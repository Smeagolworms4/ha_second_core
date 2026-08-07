#!/usr/bin/env bash
set -euo pipefail

BASE_CONFIG_PATH="${BASE_CONFIG_PATH:-second-core}"
PORT="${PORT:-8124}"

mkdir -p "/share/${BASE_CONFIG_PATH}"
if [ ! -L /config ]; then
  rmdir /config
  ln -s "/share/${BASE_CONFIG_PATH}" /config
fi
cd /config

# Since 2026.8 Home Assistant defaults to port 80 when SUPERVISOR is set (the
# add-on case) and no longer reads http: from configuration.yaml after the
# first start. SETUP_PORT pins the default port whatever the version, and
# bootstrap.py pins the stored one. Both are needed: the store wins at
# runtime, the default is what any fallback lands on.
export SETUP_PORT="${PORT}"

python3 /usr/src/second_core/bootstrap.py

echo "Start Home-Assistant on port ${PORT}."
exec python3 -m homeassistant --ignore-os-check --config /config
