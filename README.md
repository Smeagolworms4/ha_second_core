# Ha Second Core

[![pipeline status](https://github.com/Smeagolworms4/ha_second_core/actions/workflows/build_images.yml/badge.svg)](https://github.com/Smeagolworms4/ha_second_core/actions/workflows/build_images.yml)

[!["Buy Me A Coffee"](https://raw.githubusercontent.com/Smeagolworms4/donate-assets/master/coffee.png)](https://www.buymeacoffee.com/smeagolworms4)
[!["Buy Me A Coffee"](https://raw.githubusercontent.com/Smeagolworms4/donate-assets/master/paypal.png)](https://www.paypal.com/donate/?business=SURRPGEXF4YVU&no_recurring=0&item_name=Hello%2C+I%27m+SmeagolWorms4.+For+my+open+source+projects.%0AThanks+you+very+mutch+%21%21%21&currency_code=EUR)

Run a second core for HA

## Usage

Pull repository

```bash
docker pull smeagolworms4/ha_second_core
```
Run container:

```bash
docker run -ti smeagolworms4/ha_second_core
```

## Environment variables

```
ENV BASE_CONFIG_PATH=second-core
ENV PORT=8124
ENV FORCE_PORT=true
```

- `BASE_CONFIG_PATH`: directory under `/share` holding the second core config.
- `PORT`: port the second core listens on inside the container.
- `FORCE_PORT`: realign the port on every start (see below). Set to `false` to
  manage it from the second core UI instead.

## About the port

Home Assistant 2026.8 moved the HTTP configuration from `configuration.yaml`
to `.storage/http`, and made port 80 the default when the `SUPERVISOR`
environment variable is set (which is the case for the add-on). Left alone,
that would move the second core off the port the container publishes, and a
`http:` block in `configuration.yaml` would be migrated as a *pending* config
that Home Assistant reverts, and restarts for, after five minutes unless it is
confirmed in the UI.

The port is therefore pinned at startup, so an already installed second core
keeps behaving like a new one:

- `SETUP_PORT` is exported so `PORT` is the default port whatever the Home
  Assistant version and install type;
- `.storage/http` is seeded on a fresh install (reusing the `http:` settings of
  an existing `configuration.yaml`, if any) and, unless `FORCE_PORT` is
  disabled, put back on `PORT` on every start.

Older cores, which have no HTTP config store, keep using the `http:` block of
the generated `configuration.yaml`.

Existing installs keep the `http:` block Home Assistant no longer reads; it can
be removed from `configuration.yaml` to silence the repair warning about it.

## Docker hub

https://hub.docker.com/r/smeagolworms4/ha_second_core

## Github

https://github.com/Smeagolworms4/ha_second_core


## Home Assistant Addon

https://github.com/GollumDom/addon-repository
