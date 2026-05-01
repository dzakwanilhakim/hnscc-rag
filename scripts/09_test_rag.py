"""
Phase 4 — Smoke test for the full RAG pipeline.

Tests all three prompt variants on a sample query.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.rag_chain import HNSCCRAGChain


def main():
    chain = HNSCCRAGChain()

    question = "What is the prognostic significance of HPV status in oropharyngeal squamous cell carcinoma?"

    for variant in ["zero_shot", "few_shot", "chain_of_thought"]:
        print(f"\n{'='*70}")
        print(f"VARIANT: {variant.upper()}")
        print(f"{'='*70}")

        response = chain.run(question, variant=variant, k=5)

        if response.error:
            print(f"❌ Error: {response.error}")
            continue

        print(f"\nRetrieved PMIDs: {[r.pmid for r in response.retrieved]}")
        print(f"\nResponse:\n{response.response_text}")
        print(f"\nValidation: {response.validation.summary()}")
        print(f"Latency: {response.latency_seconds:.2f}s")


if __name__ == "__main__":
    main()