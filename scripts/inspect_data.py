import json
from collections import Counter
from pathlib import Path

Raw_dir = Path("data/raw")

def load_all_docs():
    docs = []
    for path in Raw_dir.glob("*.json"):
        with path.open("r", encoding="utf-8") as file:
            items = json.load(file)

        for item in items:
            item["_raw_file"] = path.name
            docs.append(item)

    return docs

def main():
    docs = load_all_docs()
    print("Total chunks:", len(docs))

    by_file = Counter(doc.get("_raw_file", "N/A") for doc in docs)
    print("\nChunks by file:")
    for file_name, count in by_file.most_common():
        print(f"- {file_name}: {count}")

    so_hieu_counter = Counter(doc.get("so_hieu", "N/A") for doc in docs)
    print("\nChunks by so_hieu:")
    for so_hieu, count in so_hieu_counter.most_common():
        print(f"- {so_hieu}: {count}")

    empty_text = [doc for doc in docs if not doc.get("text", "").strip()]
    print("\nEmpty text chunks:", len(empty_text))

    print("\nSample chunks:")
    for doc in docs[:5]:
        print("-" * 80)
        print("file:", doc.get("_raw_file"))
        print("so_hieu:", doc.get("so_hieu"))
        print("ten_van_ban:", doc.get("ten_van_ban"))
        print("dieu:", doc.get("dieu"))
        print("khoan:", doc.get("khoan"))
        print("text:", doc.get("text", "")[:500])


if __name__ == "__main__":
    main()
