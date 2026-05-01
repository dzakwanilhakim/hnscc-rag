"""
Phase 5 — Run full evaluation across all queries and prompt variants.

Outputs eval_results.json with per-query, per-variant results.
"""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.rag_chain import HNSCCRAGChain
from src.config import BASE_DIR

TEST_QUERIES_PATH = BASE_DIR / "experiments" / "test_queries.json"
RESULTS_PATH = BASE_DIR / "experiments" / "eval_results.json"

VARIANTS = ["zero_shot", "few_shot", "chain_of_thought"]
TOP_K = 5
SLEEP_BETWEEN_CALLS = 1


def main():
    # Load queries
    with TEST_QUERIES_PATH.open() as f:
        queries = json.load(f)
    print(f"Loaded {len(queries)} test queries")

    # Init chain (reuses retriever, single instance for all queries)
    chain = HNSCCRAGChain()

    # Storage
    # Resume from checkpoint if exists
    if RESULTS_PATH.exists():
        with RESULTS_PATH.open() as f:
            results = json.load(f)
        completed = {(r["query_id"], r["variant"]) for r in results}
        print(f"📂 Resuming from checkpoint: {len(results)} results already done")
    else:
        results = []
        completed = set()

    total_calls = len(queries) * len(VARIANTS)
    call_idx = 0

    for q in queries:
        for variant in VARIANTS:
            # Skip if already done
            if (q["id"], variant) in completed:
                continue

            call_idx += 1
            print(f"\n[{call_idx}/{total_calls}] {q['id']} — {variant}")
            print(f"  Query: {q['query'][:80]}...")

            response = chain.run(q["query"], variant=variant, k=TOP_K)

            row = {
                "query_id": q["id"],
                "category": q["category"],
                "expected_refusal": q.get("expected_refusal", False),
                "variant": variant,
                **response.to_dict(),
            }

            results.append(row)

            # Print quick status
            if response.error:
                print(f"   Error: {response.error}")
            else:
                print(f"   {response.validation.summary()}")
                print(f"     Latency: {response.latency_seconds:.2f}s")

            # Rate-limit pause
            if call_idx < total_calls:
                time.sleep(SLEEP_BETWEEN_CALLS)
                # Checkpoint every 10 calls
                if call_idx % 10 == 0:
                    with RESULTS_PATH.open("w") as f:
                        json.dump(results, f, indent=2)
                    print(f"     Checkpoint saved ({len(results)} results)")

    # Save raw results
    with RESULTS_PATH.open("w") as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*70}")
    print(f"Saved {len(results)} results to {RESULTS_PATH}")


if __name__ == "__main__":
    main()