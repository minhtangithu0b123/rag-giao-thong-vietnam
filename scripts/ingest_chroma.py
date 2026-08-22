import json
import sys
from pathlib import Path

import chromadb
from tqdm import tqdm


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.embeddings import EmbeddingService


CLEAN_PATH = PROJECT_ROOT / "data" / "processed" / "legal_documents_clean.jsonl"
CHROMA_PATH = PROJECT_ROOT / "data" / "chroma"
COLLECTION_NAME = "traffic_law_chunks"
BATCH_SIZE = 32


def load_chunks() -> list[dict]:
    if not CLEAN_PATH.exists():
        raise FileNotFoundError(
            f"Khong tim thay file: {CLEAN_PATH}. Hay chay python scripts\\clean_data.py truoc."
        )

    chunks = []
    with CLEAN_PATH.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line:
                chunks.append(json.loads(line))

    return chunks


def ensure_unique_ids(chunks: list[dict]) -> list[dict]:
    seen = set()
    fixed_chunks = []

    for index, chunk in enumerate(chunks):
        chunk_id = str(chunk.get("id") or f"chunk-{index}")
        if chunk_id in seen:
            chunk_id = f"{chunk_id}__dup-{index}"
        seen.add(chunk_id)

        fixed_chunk = dict(chunk)
        fixed_chunk["id"] = chunk_id
        fixed_chunks.append(fixed_chunk)

    return fixed_chunks


def build_embedding_text(chunk: dict) -> str:
    return "\n".join(
        [
            f"Van ban: {chunk.get('ten_van_ban', '')}",
            f"So hieu: {chunk.get('so_hieu', '')}",
            f"Vi tri: {chunk.get('chuong', '')}, {chunk.get('dieu', '')}, {chunk.get('khoan', '')}",
            f"Tieu de dieu: {chunk.get('tieu_de_dieu', '')}",
            f"Noi dung: {chunk.get('text', '')}",
        ]
    )


def build_metadata(chunk: dict) -> dict:
    return {
        "chunk_id": str(chunk.get("id", "")),
        "source": str(chunk.get("source", "")),
        "so_hieu": str(chunk.get("so_hieu", "")),
        "ten_van_ban": str(chunk.get("ten_van_ban", "")),
        "chuong": str(chunk.get("chuong", "")),
        "dieu": str(chunk.get("dieu", "")),
        "khoan": str(chunk.get("khoan", "")),
        "vehicle_group": str(chunk.get("vehicle_group", "")),
        "tieu_de_dieu": str(chunk.get("tieu_de_dieu", "")),
        "citation": str(chunk.get("citation", "")),
    }


def recreate_collection(client):
    try:
        client.delete_collection(name=COLLECTION_NAME)
    except Exception:
        pass

    return client.create_collection(name=COLLECTION_NAME)


def main() -> None:
    chunks = load_chunks()
    chunks = ensure_unique_ids(chunks)
    print("Loaded chunks:", len(chunks))

    if not chunks:
        raise ValueError("Khong co chunk nao de ingest.")

    CHROMA_PATH.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    collection = recreate_collection(client)
    embedder = EmbeddingService()

    for start in tqdm(range(0, len(chunks), BATCH_SIZE), desc="Ingesting"):
        batch = chunks[start : start + BATCH_SIZE]

        ids = [str(chunk["id"]) for chunk in batch]
        documents = [str(chunk.get("text", "")) for chunk in batch]
        embedding_texts = [build_embedding_text(chunk) for chunk in batch]
        embeddings = embedder.embed_batch(embedding_texts)
        metadatas = [build_metadata(chunk) for chunk in batch]

        collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    print("Done ingesting chunks into ChromaDB")
    print("Path:", CHROMA_PATH)
    print("Collection:", COLLECTION_NAME)
    print("Count:", collection.count())


if __name__ == "__main__":
    main()
