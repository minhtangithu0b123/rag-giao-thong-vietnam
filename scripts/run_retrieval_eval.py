import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from app.retriever import HybridRetriever
EVAL_PATH = PROJECT_ROOT / "evals" / "retrieval_eval_seed.jsonl"


def load_cases() -> list[dict]:
    cases = []
    with EVAL_PATH.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases


def is_match(result: dict, case: dict) -> bool:
    if case.get("expected_so_hieu") and case["expected_so_hieu"] not in result.get("so_hieu", ""):
        return False
    if case.get("expected_dieu") and case["expected_dieu"] != result.get("dieu", ""):
        return False
    if case.get("expected_vehicle_group") and case["expected_vehicle_group"] != result.get("vehicle_group", ""):
        return False
    return True


def main() -> None:
    retriever = HybridRetriever()
    cases = load_cases()
    recall_at_1 = 0
    recall_at_3 = 0
    reciprocal_ranks = []

    for case in cases:
        results = retriever.retrieve(case["question"], top_k=5)
        rank = None
        for index, result in enumerate(results, start=1):
            if is_match(result, case):
                rank = index
                break

        if rank == 1:
            recall_at_1 += 1
        if rank is not None and rank <= 3:
            recall_at_3 += 1
        reciprocal_ranks.append(0.0 if rank is None else 1.0 / rank)

        status = "PASS" if rank is not None else "FAIL"
        top = results[0] if results else {}
        print(f"{status} | rank={rank} | {case['question']}")
        print(f"  top1: {top.get('citation')} | vehicle={top.get('vehicle_group')} | score={top.get('score')}")

    total = len(cases)
    print("=" * 80)
    print(f"Cases: {total}")
    print(f"Recall@1: {recall_at_1 / total:.2f}")
    print(f"Recall@3: {recall_at_3 / total:.2f}")
    print(f"MRR: {sum(reciprocal_ranks) / total:.2f}")


if __name__ == "__main__":
    main()
