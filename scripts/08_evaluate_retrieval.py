"""
Phase 3 — Retrieval evaluation.

Evaluates retrieval quality on the test query set using two metrics:

1. Topic-keyword Recall@5 — does at least one of top-5 abstracts contain
   any expected_topic keyword in title or abstract? (proxy for relevance)

2. Source distribution — which query source (core/omics/mechanistic) do
   retrieved papers come from?

Outputs a markdown report at experiments/retrieval_evaluation.md.
"""

import json
import re
from collections import Counter
from pathlib import Path

from src.retriever import HNSCCRetriever
from src.config import BASE_DIR

TEST_QUERIES_PATH = BASE_DIR / "experiments" / "test_queries.json"
OUTPUT_REPORT = BASE_DIR / "experiments" / "retrieval_evaluation.md"
TOP_K = 5


def keyword_match(text: str, keywords: list[str]) -> bool:
    """Check if any keyword is in text (case-insensitive, word boundary)."""
    text_lower = text.lower()
    for kw in keywords:
        pattern = r"\b" + re.escape(kw.lower()) + r"\b"
        if re.search(pattern, text_lower):
            return True
    return False


def main():
    # Load test queries
    with TEST_QUERIES_PATH.open() as f:
        test_queries = json.load(f)

    print(f"Loaded {len(test_queries)} test queries")

    # Load retriever
    retriever = HNSCCRetriever()

    # Run all queries
    rows = []
    source_counter = Counter()

    for q in test_queries:
        results = retriever.retrieve(q["query"], k=TOP_K)

        # Topic recall: does ANY top-5 result mention any expected topic?
        all_text = " ".join(
            (r.title + " " + r.abstract).lower() for r in results
        )
        any_match = keyword_match(all_text, q["expected_topics"])

        # Per-result topic match
        per_result_matches = []
        for r in results:
            text = (r.title + " " + r.abstract).lower()
            per_result_matches.append(keyword_match(text, q["expected_topics"]))
            for src in r.source_queries:
                source_counter[src] += 1

        topic_recall_at_k = sum(per_result_matches) / TOP_K
        avg_similarity = sum(r.similarity for r in results) / len(results)

        rows.append({
            "id": q["id"],
            "query": q["query"],
            "category": q["category"],
            "any_relevant_in_top5": any_match,
            "topic_recall_at_5": topic_recall_at_k,
            "avg_similarity": avg_similarity,
            "top_pmids": [r.pmid for r in results],
            "top_titles": [r.title for r in results],
        })

    # Aggregate metrics
    n_total = len(rows)
    n_any_match = sum(1 for r in rows if r["any_relevant_in_top5"])
    avg_topic_recall = sum(r["topic_recall_at_5"] for r in rows) / n_total
    avg_sim = sum(r["avg_similarity"] for r in rows) / n_total

    # Build report
    lines = []
    lines.append("# Phase 3 — Retrieval Evaluation Report\n")
    lines.append(f"**Test queries:** {n_total}")
    lines.append(f"**Top-K:** {TOP_K}\n")

    lines.append("## Aggregate Metrics\n")
    lines.append(f"- **Coverage@5** (≥1 relevant in top-5): {n_any_match}/{n_total} = {n_any_match/n_total:.1%}")
    lines.append(f"- **Avg Topic Recall@5**: {avg_topic_recall:.3f}")
    lines.append(f"- **Avg Similarity**: {avg_sim:.3f}\n")

    lines.append("## Source Distribution of Retrieved Papers\n")
    total_retrieved = sum(source_counter.values())
    for src, count in source_counter.most_common():
        pct = 100 * count / total_retrieved if total_retrieved else 0
        lines.append(f"- `{src}`: {count} ({pct:.1f}%)")

    lines.append("\n## Per-Query Results\n")
    lines.append("| ID | Category | Coverage | Recall@5 | Avg Sim | Query |")
    lines.append("|----|----------|----------|----------|---------|-------|")
    for r in rows:
        cov = "✅" if r["any_relevant_in_top5"] else "❌"
        lines.append(
            f"| {r['id']} | {r['category']} | {cov} | "
            f"{r['topic_recall_at_5']:.2f} | {r['avg_similarity']:.3f} | "
            f"{r['query'][:60]}... |"
        )

    lines.append("\n## Failure Cases\n")
    failures = [r for r in rows if not r["any_relevant_in_top5"]]
    if not failures:
        lines.append("_No queries failed coverage@5._")
    else:
        for r in failures:
            lines.append(f"\n### {r['id']}: {r['query']}")
            lines.append(f"**Category:** {r['category']}")
            lines.append(f"**Top retrieved titles:**")
            for pmid, title in zip(r["top_pmids"], r["top_titles"]):
                lines.append(f"- [{pmid}] {title[:120]}")

    report = "\n".join(lines)

    # Save
    OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_REPORT.write_text(report)

    print(f"\n{'='*70}")
    print("AGGREGATE RESULTS")
    print(f"{'='*70}")
    print(f"Coverage@5 (≥1 relevant): {n_any_match}/{n_total} = {n_any_match/n_total:.1%}")
    print(f"Avg Topic Recall@5: {avg_topic_recall:.3f}")
    print(f"Avg Similarity: {avg_sim:.3f}")
    print(f"\nReport saved to: {OUTPUT_REPORT}")


if __name__ == "__main__":
    main()