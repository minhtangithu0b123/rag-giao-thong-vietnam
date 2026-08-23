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

RUN mkdir -p data/raw data/chroma \
    && python scripts/ingest_chroma.py

EXPOSE 8000

CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
