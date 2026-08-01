FROM weblate/weblate:2026.7

USER root

COPY packages/hexxy-weblate /usr/src/hexxy-weblate
RUN source /app/venv/bin/activate && uv pip install --no-cache-dir /usr/src/hexxy-weblate

USER 1000
