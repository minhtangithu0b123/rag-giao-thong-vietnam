#!/bin/sh
set -e

mkdir -p data/raw data/processed data/chroma

if [ ! -f "data/chroma/chroma.sqlite3" ]; then
  echo "Chroma index not found. Building index..."
  python scripts/ingest_chroma.py
else
  echo "Chroma index found. Skipping ingest."
fi

exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
