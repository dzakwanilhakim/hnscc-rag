"""
Phase 5 — Analyze eval_results.json and produce evaluation_report.md.

Computes per-variant aggregates and identifies winning variant.
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
from statistics import mean

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import BASE_DIR
from src.oos_detector import is_refusal

# Use ragas-enhanced results if available, otherwise raw
RAGAS_PATH = BASE_DIR / "experiments" / "eval_results_with_ragas.json"
RAW_PATH = BASE_DIR / "experiments" / "eval_results.json"
RESULTS_PATH = RAGAS_PATH if RAGAS_PATH.exists() else RAW_PATH

REPORT_PATH = BASE_DIR / "experiments" / "evaluation_report.md"


def main():
    with RESULTS_PATH.open() as f:
        results = json.load(f)

    has_ragas = "faithfulness" in results[0]
    print(f"Loaded {len(results)} results (RAGAS: {has_ragas})")

    # Group by variant
    by_variant = defaultdict(list)
    for r in results:
        by_variant[r["variant"]].append(r)

    # Compute metrics per variant
    summary = {}
    for variant, rows in by_variant.items():
        in_scope = [r for r in rows if r["category"] != "out_of_scope" and not r["error"]]
        oos = [r for r in rows if r["category"] == "out_of_scope" and not r["error"]]

        # Citation metrics (in-scope only)
        clean_citation_rate = mean([1 if r["is_clean"] else 0 for r in in_scope]) if in_scope else 0
        avg_valid_ratio = mean([r["valid_ratio"] for r in in_scope]) if in_scope else 0
        no_citation_rate = mean([1 if not r["cited_pmids"] else 0 for r in in_scope]) if in_scope else 0

        # OOS handling
        oos_correct_refusals = sum(1 for r in oos if is_refusal(r["response_text"]))
        oos_refusal_rate = oos_correct_refusals / len(oos) if oos else 0

        # Latency
        avg_latency = mean([r["latency_seconds"] for r in rows if not r["error"]])

        # Response length (proxy for verbosity)
        avg_length = mean([len(r["response_text"].split()) for r in in_scope]) if in_scope else 0

        # RAGAS (if available)
        avg_faithfulness = None
        avg_relevancy = None
        if has_ragas:
            with_scores = [r for r in in_scope if "faithfulness" in r]
            if with_scores:
                avg_faithfulness = mean([r["faithfulness"] for r in with_scores])
                avg_relevancy = mean([r["answer_relevancy"] for r in with_scores])

        summary[variant] = {
            "n_in_scope": len(in_scope),
            "n_oos": len(oos),
            "clean_citation_rate": clean_citation_rate,
            "avg_valid_ratio": avg_valid_ratio,
            "no_citation_rate": no_citation_rate,
            "oos_refusal_rate": oos_refusal_rate,
            "avg_latency_s": avg_latency,
            "avg_response_words": avg_length,
            "avg_faithfulness": avg_faithfulness,
            "avg_relevancy": avg_relevancy,
        }

    # Build report
    lines = []
    lines.append("# Phase 5 — Evaluation Report\n")
    lines.append(f"**Test queries:** {len(results) // 3} ({sum(1 for r in results if r['variant']=='zero_shot' and r['category']!='out_of_scope')} in-scope + {sum(1 for r in results if r['variant']=='zero_shot' and r['category']=='out_of_scope')} out-of-scope)")
    lines.append(f"**Variants:** zero-shot, few-shot, chain-of-thought")
    lines.append(f"**LLM:** Gemini 2.5 Flash")
    lines.append(f"**Total LLM calls:** {len(results)}\n")

    lines.append("## Aggregate Results by Variant\n")
    lines.append("| Metric | Zero-shot | Few-shot | Chain-of-Thought |")
    lines.append("|--------|-----------|----------|------------------|")

    metrics_to_show = [
        ("Clean citation rate", "clean_citation_rate", "{:.1%}"),
        ("Avg valid PMID ratio", "avg_valid_ratio", "{:.3f}"),
        ("No-citation rate", "no_citation_rate", "{:.1%}"),
        ("Out-of-scope refusal rate", "oos_refusal_rate", "{:.1%}"),
        ("Avg latency (s)", "avg_latency_s", "{:.2f}"),
        ("Avg response length (words)", "avg_response_words", "{:.0f}"),
    ]
    if has_ragas:
        metrics_to_show.append(("RAGAS Faithfulness", "avg_faithfulness", "{:.3f}"))
        metrics_to_show.append(("RAGAS Answer Relevancy", "avg_relevancy", "{:.3f}"))

    for name, key, fmt in metrics_to_show:
        zs = summary["zero_shot"].get(key)
        fs = summary["few_shot"].get(key)
        cot = summary["chain_of_thought"].get(key)
        lines.append(f"| {name} | {fmt.format(zs) if zs is not None else 'N/A'} | "
                     f"{fmt.format(fs) if fs is not None else 'N/A'} | "
                     f"{fmt.format(cot) if cot is not None else 'N/A'} |")

    # Verdict
    lines.append("\n## Variant Comparison Verdict\n")
    lines.append("Trade-offs observed:")
    lines.append("- **Zero-shot**: fastest, most concise, sometimes inconsistent format.")
    lines.append("- **Few-shot**: most format-consistent, citation discipline strong.")
    lines.append("- **Chain-of-Thought**: most verbose, explicit reasoning visible.")

    # Pick winner heuristically: highest clean citation × lowest hallucination × good OOS handling
    def composite_score(s):
        # Weights chosen based on what matters most for medical RAG:
        # citation accuracy >> OOS refusal >> latency
        score = (
            s["clean_citation_rate"] * 0.40
            + s["oos_refusal_rate"] * 0.30
            + s["avg_valid_ratio"] * 0.20
            + (1 - min(s["avg_latency_s"] / 10, 1.0)) * 0.10  # faster is better, capped at 10s
        )
        return score

    scored = {v: composite_score(s) for v, s in summary.items()}
    winner = max(scored, key=scored.get)

    lines.append(f"\n**Composite scores** (40% citation + 30% OOS + 20% valid PMID ratio + 10% speed):\n")
    for v, s in sorted(scored.items(), key=lambda x: x[1], reverse=True):
        lines.append(f"- `{v}`: {s:.3f}")

    lines.append(f"\n**Winning variant:** `{winner}`")

    # Failure analysis
    lines.append("\n## Failure Cases\n")

    for variant in ["zero_shot", "few_shot", "chain_of_thought"]:
        failures = [r for r in by_variant[variant] if r["category"] != "out_of_scope" and not r["is_clean"]]
        if failures:
            lines.append(f"\n### {variant} — citation issues ({len(failures)} cases)")
            for r in failures[:3]:  # show first 3
                lines.append(f"- **{r['query_id']}** ({r['category']}): "
                            f"invalid PMIDs {r['invalid_pmids']}")

    # OOS failures
    lines.append("\n### Out-of-scope handling")
    for variant in ["zero_shot", "few_shot", "chain_of_thought"]:
        oos_rows = [r for r in by_variant[variant] if r["category"] == "out_of_scope"]
        misses = [r for r in oos_rows if not is_refusal(r["response_text"])]
        if misses:
            lines.append(f"\n#### {variant} — answered when should have refused ({len(misses)} cases)")
            for r in misses[:2]:
                lines.append(f"- **{r['query_id']}**: {r['question'][:80]}...")
                lines.append(f"  Response start: _{r['response_text'][:120]}..._")

    # Save
    REPORT_PATH.write_text("\n".join(lines))
    print(f"Report saved to {REPORT_PATH}")
    print(f"\nWinning variant: {winner}")


if __name__ == "__main__":
    main()