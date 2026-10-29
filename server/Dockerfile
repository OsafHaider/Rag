FROM python:3.14-slim

# Copy the pinned uv package manager into the image.
COPY --from=ghcr.io/astral-sh/uv:0.11.8 /uv /bin/uv

WORKDIR /code

# Copy dependency files first to improve Docker layer caching.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

RUN useradd --create-home --uid 10001 appuser
COPY --chown=appuser:appuser app ./app
RUN mkdir -p /home/appuser/.cache/fastembed \
    && chown -R appuser:appuser /home/appuser/.cache

ENV PATH="/code/.venv/bin:$PATH" \
    APP_ENV=production \
    FASTEMBED_CACHE_PATH="/home/appuser/.cache/fastembed" \
    PYTHONUNBUFFERED=1

USER appuser

EXPOSE 8000
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]