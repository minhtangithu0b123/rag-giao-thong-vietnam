FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV EMBEDDING_PROVIDER=local
ENV LOCAL_EMBEDDING_MODEL=BAAI/bge-m3

COPY requirements-render.txt ./
RUN python -m pip install --upgrade pip \
    && pip install -r requirements-render.txt

RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-m3')"

COPY app ./app
COPY scripts ./scripts
COPY data/processed ./data/processed
COPY data/chroma ./data/chroma
COPY docker-entrypoint.sh ./docker-entrypoint.sh

RUN chmod +x docker-entrypoint.sh \
    && mkdir -p data/raw data/chroma

EXPOSE 8000

CMD ["./docker-entrypoint.sh"]
