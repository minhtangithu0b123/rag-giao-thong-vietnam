import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.retriever import HybridRetriever


FINAL_RESULTS = 5


def main() -> None:
    question = " ".join(sys.argv[1:]).strip()
    if not question:
        question = "vuot den do phat muc bao nhieu tien?"

    retriever = HybridRetriever()
    results = retriever.retrieve(question, top_k=FINAL_RESULTS)

    print("Question:", question)
    print("Retrieval: Hybrid Dense + BM25 with RRF fusion")
    print("=" * 80)

    for index, item in enumerate(results, start=1):
        print(f"\nTop {index}")
        print("Final score:", round(item["score"], 6))
        print("RRF score:", round(item["rrf_score"], 6))
        print("Dense rank:", item["dense_rank"])
        print("Sparse rank:", item["sparse_rank"])
        print("Dense score:", round(item["dense_score"], 4))
        print("Sparse score:", round(item["sparse_score"], 4))
        print("Boost score:", round(item["boost_score"], 4))
        print("Citation:", item.get("citation"))
        print("Van ban:", item.get("ten_van_ban"))
        print("So hieu:", item.get("so_hieu"))
        print("Dieu:", item.get("dieu"))
        print("Khoan:", item.get("khoan"))
        print("Vehicle group:", item.get("vehicle_group"))
        print("Text:", item.get("text", "")[:900])


if __name__ == "__main__":
    main()
