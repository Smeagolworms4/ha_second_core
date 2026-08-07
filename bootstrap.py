"""Prepare the second core config directory before Home Assistant starts.

Home Assistant 2026.8 changed how the HTTP server port is resolved:

* the port now lives in ``.storage/http`` and ``configuration.yaml`` is only
  read once, to be migrated into that store;
* the default port became 80 when the ``SUPERVISOR`` environment variable is
  set, which is the case when this image runs as an add-on.

Both would move the second core off the port the container publishes, and a
YAML ``http:`` block is migrated as a *pending* config, which Home Assistant
reverts (and restarts) five minutes later unless it is confirmed in the UI.

So the port is pinned here instead:

* ``SETUP_PORT`` (exported by the entrypoint) pins the default port, whatever
  the Home Assistant version and install type;
* ``.storage/http`` is seeded on a fresh install and, unless ``FORCE_PORT`` is
  disabled, realigned on every start so an already installed second core keeps
  behaving like a new one.

Home Assistant versions without the HTTP store keep using the ``http:`` block
in ``configuration.yaml``.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CONFIG_DIR = Path("/config")
CONFIG_FILE = CONFIG_DIR / "configuration.yaml"
STORAGE_DIR = CONFIG_DIR / ".storage"

DEFAULT_PORT = 8124
TRUSTED_PROXIES = ["10.0.0.0/8", "192.0.0.0/8", "172.0.0.0/8", "127.0.0.0/24"]


def log(message: str) -> None:
    """Print a bootstrap message to the container logs."""
    print(f"[second-core] {message}", flush=True)


def wanted_port() -> int:
    """Return the port the second core must listen on."""
    raw = os.environ.get("PORT", "")
    try:
        port = int(raw)
    except ValueError:
        if raw:
            log(f"invalid PORT {raw!r}, falling back to {DEFAULT_PORT}")
        return DEFAULT_PORT
    if not 1 <= port <= 65535:
        log(f"out of range PORT {raw!r}, falling back to {DEFAULT_PORT}")
        return DEFAULT_PORT
    return port


def force_port() -> bool:
    """Return whether the port is realigned on every start."""
    return os.environ.get("FORCE_PORT", "true").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def load_http_store_module() -> Any | None:
    """Return the HTTP config store module, or None on older cores."""
    try:
        from homeassistant.components.http import config as http_config
    except ImportError:
        return None
    # Everything below is built from the store's own schema and constants, so
    # only treat the store as usable when they are all there.
    required = ("HTTP_STORAGE_SCHEMA", "STORAGE_KEY", "STORAGE_VERSION")
    if not all(hasattr(http_config, name) for name in required):
        return None
    return http_config


def write_configuration_yaml(port: int, with_http_block: bool) -> None:
    """Generate configuration.yaml for a fresh install."""
    content = "default_config:\n"
    if with_http_block:
        # Cores without the HTTP store read the port from here on every start.
        proxies = "".join(f"    - {proxy}\n" for proxy in TRUSTED_PROXIES)
        content += (
            "\nhttp:\n"
            f"  server_port: {port}\n"
            "  use_x_forwarded_for: true\n"
            "  trusted_proxies:\n"
            f"{proxies}"
        )
    CONFIG_FILE.write_text(content)
    log("configuration.yaml generated")


def read_yaml_http_section() -> dict[str, Any] | None:
    """Return the http: section of configuration.yaml, if it has one.

    Home Assistant's own loader is used so !include and !secret tags keep
    working. Anything unexpected yields None: the caller then leaves the
    migration to Home Assistant rather than seeding a config it cannot read.
    """
    try:
        from homeassistant.util.yaml import load_yaml_dict
    except ImportError:
        return None
    try:
        config = load_yaml_dict(str(CONFIG_FILE))
    except Exception as err:  # noqa: BLE001 - any parse error means "unknown"
        log(f"could not read configuration.yaml ({err})")
        return None
    section = config.get("http")
    return section if isinstance(section, dict) else {}


def build_stable_config(http_config: Any, port: int) -> dict[str, Any] | None:
    """Return the config to seed the store with, or None to skip seeding."""
    section = read_yaml_http_section()
    if section is None:
        return None
    if not section:
        # Fresh install: the defaults this image has always shipped, so a
        # second core behind the main core's reverse proxy keeps working.
        section = {"use_x_forwarded_for": True, "trusted_proxies": TRUSTED_PROXIES}
    try:
        stable = dict(http_config.HTTP_STORAGE_SCHEMA({**section, "server_port": port}))
    except Exception as err:  # noqa: BLE001 - voluptuous raises Invalid subclasses
        log(
            f"http: section of configuration.yaml is not usable as is ({err}); "
            "leaving the migration to Home Assistant. Configure HTTP from the "
            "second core UI (Settings > System > Network) if needed."
        )
        return None
    stable[getattr(http_config, "HTTP_CONFIG_CREATED_AT", "created_at")] = datetime.now(
        timezone.utc
    ).isoformat()
    stable[getattr(http_config, "HTTP_CONFIG_ERROR", "error")] = None
    stable[getattr(http_config, "HTTP_CONFIG_ERROR_MESSAGE", "error_message")] = None
    return stable


def seed_store(http_config: Any, store_file: Path, port: int) -> None:
    """Create .storage/http so the first start already uses the right port."""
    stable = build_stable_config(http_config, port)
    if stable is None:
        return
    key_stable = getattr(http_config, "KEY_STABLE", "stable")
    key_pending = getattr(http_config, "KEY_PENDING", "pending")
    data = {key_stable: stable, key_pending: None}
    if key_migration := getattr(http_config, "KEY_YAML_MIGRATION_DONE", None):
        # The store is the source of truth from now on; without this the
        # http: block would be staged as a pending config and reverted.
        data[key_migration] = True
    payload: dict[str, Any] = {
        "version": http_config.STORAGE_VERSION,
        "key": http_config.STORAGE_KEY,
        "data": data,
    }
    if minor := getattr(http_config, "STORAGE_MINOR_VERSION", None):
        payload["minor_version"] = minor
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    store_file.write_text(json.dumps(payload, indent=2))
    store_file.chmod(0o600)
    log(f"HTTP config store created on port {port}")


def realign_store(http_config: Any, store_file: Path, port: int) -> None:
    """Put an existing store back on the wanted port."""
    try:
        payload = json.loads(store_file.read_text())
        data = payload["data"]
    except Exception as err:  # noqa: BLE001 - a broken store is Home Assistant's problem
        log(f"could not read {store_file} ({err}), leaving it untouched")
        return

    key_stable = getattr(http_config, "KEY_STABLE", "stable")
    key_pending = getattr(http_config, "KEY_PENDING", "pending")
    conf_port = getattr(http_config, "CONF_SERVER_PORT", "server_port")

    changed = False
    stable = data.get(key_stable)
    if isinstance(stable, dict) and stable.get(conf_port) != port:
        log(f"HTTP config store on port {stable.get(conf_port)}, forcing {port}")
        stable[conf_port] = port
        changed = True
    pending = data.get(key_pending)
    if isinstance(pending, dict) and pending.get(conf_port) != port:
        # A pending config is applied before stable on the next start, so it
        # would win over the port forced above.
        log("dropping pending HTTP config that uses another port")
        data[key_pending] = None
        changed = True

    if not changed:
        return
    store_file.write_text(json.dumps(payload, indent=2))


def main() -> None:
    """Pin the port before Home Assistant reads its config."""
    port = wanted_port()
    http_config = load_http_store_module()

    if not CONFIG_FILE.exists():
        write_configuration_yaml(port, with_http_block=http_config is None)
    else:
        log("configuration.yaml already exists")

    if http_config is None:
        log(f"core without HTTP config store, port {port} set in configuration.yaml")
        return

    store_file = STORAGE_DIR / http_config.STORAGE_KEY
    if not store_file.exists():
        seed_store(http_config, store_file, port)
    elif force_port():
        realign_store(http_config, store_file, port)
    else:
        log("FORCE_PORT disabled, keeping the port stored by Home Assistant")


if __name__ == "__main__":
    main()
