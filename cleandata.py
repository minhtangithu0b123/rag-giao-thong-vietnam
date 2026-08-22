import json
import re
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from app.text_cleaner import clean_value

RAW_PATH = PROJECT_ROOT / "data" / "raw" / "legal_documents.json"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "legal_documents_clean.jsonl"


def slugify(value: str) -> str:
    value = clean_value(value or "")
    value = value.lower()
    value = re.sub(r"[^a-z0-9A-ZÀ-ỹ]+", "-", value)
    value = value.strip("-")
    return value or "unknown"


def build_chunk_id(item, index):
    parts = [
        slugify(item.get("so_hieu", "")),
        slugify(item.get("dieu", "")),
        slugify(item.get("khoan", "")),
        str(index),
    ]
    return "__".join(parts)


def build_citation(item):
    parts = [
        item.get("so_hieu", ""),
        item.get("dieu", ""),
        item.get("khoan", ""),
    ]
    return ", ".join(part for part in parts if part)


def main():
    if not RAW_PATH.exists():
        raise FileNotFoundError(f"Khong thay file raw: {RAW_PATH}")

    with RAW_PATH.open("r", encoding="utf-8") as file:
        raw_items = json.load(file)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    kept = 0
    skipped = 0

    with OUTPUT_PATH.open("w", encoding="utf-8") as out:
        for index, raw_item in enumerate(raw_items):
            item = {key: clean_value(value) for key, value in raw_item.items()}

            text = item.get("text", "").strip()
            if not text:
                skipped += 1
                continue

            clean_item = {
                "id": build_chunk_id(item, index),
                "source": item.get("source", ""),
                "so_hieu": item.get("so_hieu", ""),
                "ten_van_ban": item.get("ten_van_ban", ""),
                "chuong": item.get("chuong", ""),
                "dieu": item.get("dieu", ""),
                "tieu_de_dieu": item.get("tieu_de_dieu", ""),
                "khoan": item.get("khoan", ""),
                "text": text,
                "citation": build_citation(item),
            }

            out.write(json.dumps(clean_item, ensure_ascii=False) + "\n")
            kept += 1

    print("Input chunks:", len(raw_items))
    print("Kept chunks:", kept)
    print("Skipped empty:", skipped)
    print("Output:", OUTPUT_PATH)


if __name__ == "__main__":
    main()