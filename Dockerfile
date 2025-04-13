ARG HA_TAG=stable
FROM ghcr.io/home-assistant/home-assistant:${HA_TAG}

ENV BASE_CONFIG_PATH=second-core

CMD bash -c '\
  mkdir -p /share/${BASE_CONFIG_PATH} && \
  rmdir /config && \
  ln -s /share/${BASE_CONFIG_PATH} /config && \
  cd /config && \
  if [ ! -f /config/configuration.yaml ]; then \
    echo -e "default_config:\n\nhttp:\n  server_port: 8124\n  use_x_forwarded_for: true\n  trusted_proxies:\n    - 10.0.0.0/8\n    - 192.0.0.0/8\n    - 172.0.0.0/8\n    - 127.0.0.0/24" > /config/configuration.yaml; \
    echo "✅ configuration.yaml generated"; \
  else \
    echo "✅ configuration.yaml already exist."; \
  fi && \
  echo "Start Home-Assitant." && \
  python3 -m homeassistant --ignore-os-check --config /config\
'
