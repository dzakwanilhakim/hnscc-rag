"""
Phase 3 — Smoke test for HNSCCRetriever.

Verifies retrieval works through the new module API.
"""

from src.retriever import HNSCCRetriever


def main():
    retriever = HNSCCRetriever()

    test_queries = [
        "HPV positive oropharyngeal cancer prognosis",
        "PD-L1 immunotherapy response in HNSCC",
        "tumor microenvironment immune infiltration",
        "EGFR targeted therapy laryngeal cancer",
        "DNA methylation biomarker oral cancer",
    ]

    for q in test_queries:
        print(f"\n{'='*70}")
        print(f"Query: {q}")
        print(f"{'='*70}")

        results = retriever.retrieve(q, k=3)

        for i, r in enumerate(results, 1):
            print(f"\n[{i}] PMID: {r.pmid} | Similarity: {r.similarity:.3f} | Year: {r.year}")
            print(f"    Title: {r.title[:100]}...")

    # Test filter
    print(f"\n{'='*70}")
    print("Filter test: year >= 2024, query about HPV")
    print(f"{'='*70}")
    results = retriever.retrieve(
        "HPV positive oropharyngeal cancer",
        k=3,
        filter_year_min=2024,
    )
    for r in results:
        print(f"  PMID: {r.pmid} | Year: {r.year} | Sim: {r.similarity:.3f}")
        print(f"    {r.title[:90]}...")


if __name__ == "__main__":
    main()