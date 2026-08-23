FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV EMBEDDING_PROVIDER=openai
ENV OPENAI_EMBEDDING_MODEL=text-embedding-3-small

COPY requirements-render.txt ./
RUN python -m pip install --upgrade pip \
    && pip install -r requirements-render.txt

COPY app ./app
COPY scripts ./scripts
COPY data/processed ./data/processed
COPY docker-entrypoint.sh ./docker-entrypoint.sh

RUN chmod +x docker-entrypoint.sh \
    && mkdir -p data/raw data/chroma

EXPOSE 8000

CMD ["./docker-entrypoint.sh"]
