import json
from collections import Counter
from pathlib import Path

DATA_PATH = Path("data/raw/legal_documents.json")


def main():
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Khong thay file: {DATA_PATH}")

    with DATA_PATH.open("r", encoding="utf-8") as file:
        docs = json.load(file)

    print("Total chunks:", len(docs))

    so_hieu_counter = Counter(doc.get("so_hieu", "N/A") for doc in docs)
    print("\nChunks by so_hieu:")
    for so_hieu, count in so_hieu_counter.most_common():
        print(f"- {so_hieu}: {count}")

    source_counter = Counter(doc.get("source", "N/A") for doc in docs)
    print("\nSources:")
    for source, count in source_counter.most_common():
        print(f"- {count}: {source}")

    empty_text = [doc for doc in docs if not doc.get("text", "").strip()]
    print("\nEmpty text chunks:", len(empty_text))

    print("\nSample chunks:")
    for doc in docs[:3]:
        print("-" * 80)
        print("so_hieu:", doc.get("so_hieu"))
        print("ten_van_ban:", doc.get("ten_van_ban"))
        print("dieu:", doc.get("dieu"))
        print("khoan:", doc.get("khoan"))
        print("text:", doc.get("text", "")[:700])


if __name__ == "__main__":
    main()