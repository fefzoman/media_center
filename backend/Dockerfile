FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
RUN pip install . \
    && useradd --system --uid 10001 --create-home media-center \
    && mkdir /data \
    && chown media-center:media-center /data

USER media-center
CMD ["python", "-m", "media_center"]
