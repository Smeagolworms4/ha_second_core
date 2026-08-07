ARG HA_TAG=stable
FROM ghcr.io/home-assistant/home-assistant:${HA_TAG}

ENV BASE_CONFIG_PATH=second-core
# Port the second core listens on inside the container. Home Assistant 2026.8
# moved the port into .storage/http and defaults to 80 under Supervisor, so it
# is pinned instead of being left to the core's default.
ENV PORT=8124
# Realign the stored port on every start, so an already installed second core
# behaves like a new one. Set to false to manage the port from the second
# core UI (Settings > System > Network).
ENV FORCE_PORT=true

COPY entrypoint.sh bootstrap.py /usr/src/second_core/
RUN chmod +x /usr/src/second_core/entrypoint.sh

CMD ["/usr/src/second_core/entrypoint.sh"]
