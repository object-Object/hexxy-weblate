# Keep in sync with packages/hexxy-weblate/pyproject.toml
FROM weblate/weblate:2026.10

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libx11-dev \
    && rm -rf /var/lib/apt/lists/*

# Keep in sync with packages/hexxy-weblate/pyproject.toml
RUN source /app/venv/bin/activate \
    && uv pip install --no-cache-dir hexdoc~=2.0rc1 \
    && apt-get purge -y build-essential libx11-dev \
    && apt-get autoremove -y

COPY packages/hexxy-weblate /usr/src/hexxy-weblate
RUN source /app/venv/bin/activate \
    && uv pip install --no-cache-dir /usr/src/hexxy-weblate

USER 1000
