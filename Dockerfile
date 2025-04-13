ARG HA_TAG=stable
FROM ghcr.io/home-assistant/home-assistant:${HA_TAG}

ENV BASE_CONFIG_PATH=second-core

CMD bash -c 'mkdir -p /config/${BASE_CONFIG_PATH} && python3 -m homeassistant \
  --config "/config/${BASE_CONFIG_PATH}" \
  --ignore-os-check'

