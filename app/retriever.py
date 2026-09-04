import json
import math
import re
import unicodedata
from pathlib import Path

import chromadb
from rank_bm25 import BM25Okapi

from app.embeddings import EmbeddingService


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHROMA_PATH = PROJECT_ROOT / "data" / "chroma"
CLEAN_PATH = PROJECT_ROOT / "data" / "processed" / "legal_documents_clean.jsonl"
COLLECTION_NAME = "traffic_law_chunks"

DENSE_TOP_K = 30
SPARSE_TOP_K = 30
RRF_K = 60
BOOST_SCALE = 0.02

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
    "quá tốc độ": [
        "điều khiển xe chạy quá tốc độ quy định",
        "chạy quá tốc độ quy định",
        "tốc độ quy định",
    ],
    "chạy quá tốc độ": [
        "điều khiển xe chạy quá tốc độ quy định",
        "chạy quá tốc độ quy định",
        "tốc độ quy định",
    ],
    "biển báo": [
        "không chấp hành hiệu lệnh chỉ dẫn của biển báo hiệu",
        "biển báo hiệu",
        "vạch kẻ đường",
    ],
    "không chấp hành biển báo": [
        "không chấp hành hiệu lệnh chỉ dẫn của biển báo hiệu",
        "biển báo hiệu",
        "vạch kẻ đường",
    ],
    "đường cao tốc": [
        "đi vào đường cao tốc",
        "đường cao tốc",
        "người đi bộ đi vào đường cao tốc",
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
    "bicycle": ("xe đạp", "xe đạp máy", "xe thô sơ"),
}

PENALTY_ARTICLE_BY_VEHICLE = {
    "car": "Điều 6",
    "motorbike": "Điều 7",
    "specialized_vehicle": "Điều 8",
    "pedestrian": "Điều 10",
    "bicycle": "Điều 9",
}


def normalize_text(text: str) -> str:
    text = str(text or "").lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    text = text.replace("đ", "d")
    return text


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", normalize_text(text))


class HybridRetriever:
    def __init__(self):
        self.embedder = EmbeddingService()
        self.client = chromadb.PersistentClient(path=str(CHROMA_PATH))
        self.collection = self.client.get_collection(COLLECTION_NAME)
        self.chunks = self.load_chunks()
        self.bm25 = self.build_bm25(self.chunks)

    def load_chunks(self) -> list[dict]:
        if not CLEAN_PATH.exists():
            raise FileNotFoundError(f"Khong tim thay file clean: {CLEAN_PATH}")

        chunks = []
        with CLEAN_PATH.open("r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if line:
                    chunks.append(json.loads(line))
        return chunks

    def build_bm25(self, chunks: list[dict]) -> BM25Okapi:
        tokenized_corpus = [tokenize(self.searchable_text(chunk)) for chunk in chunks]
        return BM25Okapi(tokenized_corpus)

    def searchable_text(self, chunk: dict) -> str:
        return " ".join(
            [
                chunk.get("text", ""),
                chunk.get("citation", ""),
                chunk.get("so_hieu", ""),
                chunk.get("ten_van_ban", ""),
                chunk.get("dieu", ""),
                chunk.get("khoan", ""),
                chunk.get("tieu_de_dieu", ""),
                chunk.get("vehicle_group", ""),
            ]
        )

    def expand_query(self, question: str) -> str:
        normalized_question = normalize_text(question)
        expansions = []

        for keyword, phrases in LEGAL_EXPANSIONS.items():
            if normalize_text(keyword) in normalized_question:
                expansions.extend(phrases)

        if not expansions:
            return question

        return question + " " + " ".join(expansions)

    def detect_vehicle(self, question: str) -> str | None:
        normalized_question = normalize_text(question)

        for vehicle, patterns in VEHICLE_PATTERNS.items():
            for pattern in patterns:
                normalized_pattern = normalize_text(pattern)
                regex = r"(?<![a-z0-9])" + re.escape(normalized_pattern) + r"(?![a-z0-9])"
                if re.search(regex, normalized_question):
                    return vehicle

        return None

    def make_chunk_from_chroma(self, doc: str, meta: dict) -> dict:
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

    def dense_retrieve(self, question: str) -> dict[str, dict]:
        query_embedding = self.embedder.embed_text(question)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=DENSE_TOP_K,
            include=["metadatas", "documents", "distances"],
        )

        candidates = {}
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        distances = results["distances"][0]

        for rank, (doc, meta, distance) in enumerate(zip(docs, metas, distances), start=1):
            chunk = self.make_chunk_from_chroma(doc, meta)
            chunk_id = chunk["id"]
            candidates[chunk_id] = {
                "chunk": chunk,
                "dense_rank": rank,
                "sparse_rank": None,
                "dense_score": 1.0 / (1.0 + float(distance)),
                "sparse_score": 0.0,
                "rrf_score": 1.0 / (RRF_K + rank),
                "boost_score": 0.0,
                "distance": float(distance),
                "from_dense": True,
                "from_sparse": False,
            }

        return candidates

    def sparse_retrieve(self, question: str) -> dict[str, dict]:
        query_tokens = tokenize(question)
        scores = self.bm25.get_scores(query_tokens)
        top_indexes = sorted(range(len(scores)), key=lambda index: scores[index], reverse=True)[:SPARSE_TOP_K]
        max_score = max((float(scores[index]) for index in top_indexes), default=0.0)

        candidates = {}
        for rank, index in enumerate(top_indexes, start=1):
            raw_score = float(scores[index])
            if raw_score <= 0:
                continue

            chunk = self.chunks[index]
            chunk_id = str(chunk.get("id") or f"sparse-{index}")
            sparse_score = raw_score / max_score if max_score > 0 else 0.0
            candidates[chunk_id] = {
                "chunk": chunk,
                "dense_rank": None,
                "sparse_rank": rank,
                "dense_score": 0.0,
                "sparse_score": sparse_score,
                "rrf_score": 1.0 / (RRF_K + rank),
                "boost_score": 0.0,
                "distance": math.inf,
                "from_dense": False,
                "from_sparse": True,
            }

        return candidates

    def metadata_boost(self, question: str, chunk: dict) -> float:
        normalized_question = normalize_text(question)
        text = normalize_text(self.searchable_text(chunk))
        score = 0.0
        vehicle = self.detect_vehicle(question)

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
        elif asks_penalty and vehicle and not chunk_vehicle and "168/2024" in chunk.get("so_hieu", ""):
            score -= 0.35

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

    def merge_candidates(self, dense_candidates: dict, sparse_candidates: dict, question: str) -> list[dict]:
        merged = dict(dense_candidates)

        for chunk_id, sparse_item in sparse_candidates.items():
            if chunk_id in merged:
                merged[chunk_id]["sparse_rank"] = sparse_item["sparse_rank"]
                merged[chunk_id]["sparse_score"] = sparse_item["sparse_score"]
                merged[chunk_id]["rrf_score"] += sparse_item["rrf_score"]
                merged[chunk_id]["from_sparse"] = True
            else:
                merged[chunk_id] = sparse_item

        ranked = []
        for item in merged.values():
            boost = self.metadata_boost(question, item["chunk"])
            item["boost_score"] = boost
            item["final_score"] = item["rrf_score"] + BOOST_SCALE * boost
            ranked.append(item)

        ranked.sort(key=lambda item: item["final_score"], reverse=True)
        return ranked

    def format_result(self, item: dict) -> dict:
        chunk = item["chunk"]
        return {
            "score": item["final_score"],
            "dense_score": item["dense_score"],
            "sparse_score": item["sparse_score"],
            "rrf_score": item["rrf_score"],
            "boost_score": item["boost_score"],
            "dense_rank": item["dense_rank"],
            "sparse_rank": item["sparse_rank"],
            "citation": chunk.get("citation", ""),
            "source": chunk.get("source", ""),
            "so_hieu": chunk.get("so_hieu", ""),
            "ten_van_ban": chunk.get("ten_van_ban", ""),
            "chuong": chunk.get("chuong", ""),
            "dieu": chunk.get("dieu", ""),
            "khoan": chunk.get("khoan", ""),
            "vehicle_group": chunk.get("vehicle_group", ""),
            "text": chunk.get("text", ""),
        }

    def retrieve(self, question: str, top_k: int = 5) -> list[dict]:
        expanded_question = self.expand_query(question)
        dense_candidates = self.dense_retrieve(expanded_question)
        sparse_candidates = self.sparse_retrieve(expanded_question)
        ranked = self.merge_candidates(dense_candidates, sparse_candidates, question)
        return [self.format_result(item) for item in ranked[:top_k]]
