import json
import math
import re
import sys
import unicodedata
from pathlib import Path

import chromadb
from rank_bm25 import BM25Okapi


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.embeddings import EmbeddingService


CHROMA_PATH = PROJECT_ROOT / "data" / "chroma"
CLEAN_PATH = PROJECT_ROOT / "data" / "processed" / "legal_documents_clean.jsonl"
COLLECTION_NAME = "traffic_law_chunks"
DENSE_TOP_K = 30
SPARSE_TOP_K = 30
FINAL_RESULTS = 5

DENSE_WEIGHT = 0.45
SPARSE_WEIGHT = 0.30
BOOST_WEIGHT = 0.25


LEGAL_EXPANSIONS = {
    "vượt đèn đỏ": [
        "không chấp hành hiệu lệnh của đèn tín hiệu giao thông",
        "đèn tín hiệu giao thông",
        "đèn đỏ",
    ],
    "đèn đỏ": [
        "không chấp hành hiệu lệnh của đèn tín hiệu giao thông",
        "đèn tín hiệu giao thông",
    ],
    "nồng độ cồn": [
        "trong máu hoặc hơi thở có nồng độ cồn",
        "điều khiển xe mà trong máu hoặc hơi thở có nồng độ cồn",
    ],
    "xe máy": [
        "người điều khiển xe mô tô",
        "người điều khiển xe gắn máy",
        "xe mô tô xe gắn máy",
    ],
    "mô tô": [
        "người điều khiển xe mô tô",
        "xe mô tô",
    ],
    "ô tô": [
        "người điều khiển xe ô tô",
        "xe ô tô",
    ],
    "không đội mũ bảo hiểm": [
        "không đội mũ bảo hiểm",
        "mũ bảo hiểm cho người đi mô tô xe máy",
    ],
    "sai làn": [
        "đi không đúng phần đường",
        "đi không đúng làn đường",
        "phần đường làn đường quy định",
    ],
    "không có bằng lái": [
        "không có giấy phép lái xe",
        "giấy phép lái xe",
    ],
}


PENALTY_HINTS = ("phạt", "bao nhiêu tiền", "mức phạt", "trừ điểm", "xử phạt")


VEHICLE_PATTERNS = {
    "specialized_vehicle": ("xe máy chuyên dùng", "máy kéo"),
    "car": ("ô tô", "oto", "xe hơi", "xe con"),
    "motorbike": ("xe máy", "mô tô", "xe gắn máy", "tay ga"),
    "pedestrian": ("người đi bộ", "đi bộ"),
}


PENALTY_ARTICLE_BY_VEHICLE = {
    "car": "Điều 6",
    "motorbike": "Điều 7",
    "specialized_vehicle": "Điều 8",
    "pedestrian": "Điều 10",
}


def normalize_text(text: str) -> str:
    text = str(text or "").lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    text = text.replace("đ", "d")
    return text


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", normalize_text(text))


def expand_query(question: str) -> str:
    normalized_question = normalize_text(question)
    expansions = []

    for keyword, phrases in LEGAL_EXPANSIONS.items():
        if normalize_text(keyword) in normalized_question:
            expansions.extend(phrases)

    if not expansions:
        return question

    return question + " " + " ".join(expansions)


def detect_vehicle(question: str) -> str | None:
    normalized_question = normalize_text(question)

    for vehicle, patterns in VEHICLE_PATTERNS.items():
        for pattern in patterns:
            if normalize_text(pattern) in normalized_question:
                return vehicle

    return None


def load_chunks() -> list[dict]:
    if not CLEAN_PATH.exists():
        raise FileNotFoundError(f"Khong tim thay file clean: {CLEAN_PATH}")

    chunks = []
    with CLEAN_PATH.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line:
                chunks.append(json.loads(line))
    return chunks


def searchable_text(chunk: dict) -> str:
    return " ".join(
        [
            chunk.get("text", ""),
            chunk.get("citation", ""),
            chunk.get("so_hieu", ""),
            chunk.get("ten_van_ban", ""),
            chunk.get("dieu", ""),
            chunk.get("khoan", ""),
            chunk.get("tieu_de_dieu", ""),
        ]
    )


def make_chunk_from_chroma(doc: str, meta: dict) -> dict:
    return {
        "id": meta.get("chunk_id") or meta.get("id") or meta.get("citation") or doc[:80],
        "text": doc,
        "source": meta.get("source", ""),
        "so_hieu": meta.get("so_hieu", ""),
        "ten_van_ban": meta.get("ten_van_ban", ""),
        "chuong": meta.get("chuong", ""),
        "dieu": meta.get("dieu", ""),
        "khoan": meta.get("khoan", ""),
        "vehicle_group": meta.get("vehicle_group", ""),
        "tieu_de_dieu": meta.get("tieu_de_dieu", ""),
        "citation": meta.get("citation", ""),
    }


def dense_retrieve(question: str) -> dict[str, dict]:
    embedder = EmbeddingService()
    query_embedding = embedder.embed_text(question)

    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    collection = client.get_collection(COLLECTION_NAME)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=DENSE_TOP_K,
        include=["metadatas", "documents", "distances"],
    )

    candidates = {}
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    distances = results["distances"][0]

    for doc, meta, distance in zip(docs, metas, distances):
        chunk = make_chunk_from_chroma(doc, meta)
        chunk_id = chunk["id"]
        candidates[chunk_id] = {
            "chunk": chunk,
            "dense_score": 1.0 / (1.0 + float(distance)),
            "sparse_score": 0.0,
            "boost_score": 0.0,
            "distance": float(distance),
            "from_dense": True,
            "from_sparse": False,
        }

    return candidates


def sparse_retrieve(question: str, chunks: list[dict]) -> dict[str, dict]:
    tokenized_corpus = [tokenize(searchable_text(chunk)) for chunk in chunks]
    bm25 = BM25Okapi(tokenized_corpus)
    query_tokens = tokenize(question)
    scores = bm25.get_scores(query_tokens)

    top_indexes = sorted(range(len(scores)), key=lambda index: scores[index], reverse=True)[:SPARSE_TOP_K]
    max_score = max((float(scores[index]) for index in top_indexes), default=0.0)

    candidates = {}
    for index in top_indexes:
        raw_score = float(scores[index])
        if raw_score <= 0:
            continue

        chunk = chunks[index]
        chunk_id = str(chunk.get("id") or f"sparse-{index}")
        sparse_score = raw_score / max_score if max_score > 0 else 0.0
        candidates[chunk_id] = {
            "chunk": chunk,
            "dense_score": 0.0,
            "sparse_score": sparse_score,
            "boost_score": 0.0,
            "distance": math.inf,
            "from_dense": False,
            "from_sparse": True,
        }

    return candidates


def metadata_boost(question: str, chunk: dict) -> float:
    normalized_question = normalize_text(question)
    text = normalize_text(searchable_text(chunk))
    score = 0.0
    vehicle = detect_vehicle(question)

    for keyword, phrases in LEGAL_EXPANSIONS.items():
        if normalize_text(keyword) in normalized_question:
            for phrase in phrases:
                if normalize_text(phrase) in text:
                    score += 0.35

    asks_penalty = any(normalize_text(hint) in normalized_question for hint in PENALTY_HINTS)
    if asks_penalty and "168/2024" in chunk.get("so_hieu", ""):
        score += 0.25

    chunk_vehicle = chunk.get("vehicle_group", "")
    if asks_penalty and vehicle and chunk_vehicle == vehicle:
        score += 1.35
    elif asks_penalty and vehicle and chunk_vehicle and chunk_vehicle != vehicle:
        score -= 1.15

    target_article = PENALTY_ARTICLE_BY_VEHICLE.get(vehicle)
    chunk_article = normalize_text(chunk.get("dieu", ""))
    if asks_penalty and target_article:
        if chunk_article == normalize_text(target_article):
            score += 0.45
        elif chunk_article in {normalize_text(article) for article in PENALTY_ARTICLE_BY_VEHICLE.values()}:
            score -= 0.30

    if vehicle == "motorbike" and "xe may chuyen dung" in normalize_text(text):
        score -= 1.10

    return max(-1.0, min(score, 1.5))


def merge_candidates(dense_candidates: dict, sparse_candidates: dict, question: str) -> list[dict]:
    merged = dict(dense_candidates)

    for chunk_id, sparse_item in sparse_candidates.items():
        if chunk_id in merged:
            merged[chunk_id]["sparse_score"] = sparse_item["sparse_score"]
            merged[chunk_id]["from_sparse"] = True
        else:
            merged[chunk_id] = sparse_item

    ranked = []
    for item in merged.values():
        boost = metadata_boost(question, item["chunk"])
        item["boost_score"] = boost
        item["final_score"] = (
            DENSE_WEIGHT * item["dense_score"]
            + SPARSE_WEIGHT * item["sparse_score"]
            + BOOST_WEIGHT * item["boost_score"]
        )
        ranked.append(item)

    ranked.sort(key=lambda item: item["final_score"], reverse=True)
    return ranked


def main() -> None:
    question = " ".join(sys.argv[1:]).strip()
    if not question:
        question = "vượt đèn đỏ phạt mức bao nhiêu tiền?"

    expanded_question = expand_query(question)
    chunks = load_chunks()

    dense_candidates = dense_retrieve(expanded_question)
    sparse_candidates = sparse_retrieve(expanded_question, chunks)
    ranked = merge_candidates(dense_candidates, sparse_candidates, question)

    print("Question:", question)
    print("Expanded:", expanded_question)
    print("Detected vehicle:", detect_vehicle(question))
    print("Dense candidates:", len(dense_candidates))
    print("Sparse candidates:", len(sparse_candidates))
    print("Merged candidates:", len(ranked))
    print("=" * 80)

    for index, item in enumerate(ranked[:FINAL_RESULTS], start=1):
        chunk = item["chunk"]

        print(f"\nTop {index}")
        print("Final score:", round(item["final_score"], 4))
        print("Dense score:", round(item["dense_score"], 4))
        print("Sparse score:", round(item["sparse_score"], 4))
        print("Boost score:", round(item["boost_score"], 4))
        print("From dense:", item["from_dense"])
        print("From sparse:", item["from_sparse"])
        print("Distance:", item["distance"])
        print("Citation:", chunk.get("citation"))
        print("Van ban:", chunk.get("ten_van_ban"))
        print("So hieu:", chunk.get("so_hieu"))
        print("Dieu:", chunk.get("dieu"))
        print("Khoan:", chunk.get("khoan"))
        print("Vehicle group:", chunk.get("vehicle_group"))
        print("Text:", chunk.get("text", "")[:900])


if __name__ == "__main__":
    main()
