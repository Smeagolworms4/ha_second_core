ARG HA_TAG=stable
FROM ghcr.io/home-assistant/home-assistant:${HA_TAG}

ENV BASE_CONFIG_PATH=second-core

CMD bash -c 'mkdir -p /share/${BASE_CONFIG_PATH} && rm -rf /config && ln -s /share/${BASE_CONFIG_PATH} /config && cd /config && python3 -m homeassistant --ignore-os-check --config /config'

