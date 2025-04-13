ARG HA_TAG=stable
FROM ghcr.io/home-assistant/home-assistant:${HA_TAG}

ENV BASE_CONFIG_PATH=second-core

CMD bash -c 'python3 -m homeassistant \
  --config "/config/${BASE_CONFIG_PATH}/config" \
  --media-dir "/config/${BASE_CONFIG_PATH}/media" \
  --ssl "/config/${BASE_CONFIG_PATH}/ssl"'
