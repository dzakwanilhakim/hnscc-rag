"""
Corpus coverage + balance analysis.

Usage:
    python scripts/check.py
"""

import json
import re
from pathlib import Path
from collections import Counter
from itertools import combinations

# ============================================================
# Config
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_FILE = BASE_DIR / "data" / "hnscc_abstracts.json"

# ============================================================
# Topics
# ============================================================

TOPICS = {
    "HPV": ["HPV", "human papillomavirus"],
    "Immunotherapy": ["immunotherapy", "checkpoint", "PD-1", "PD-L1"],
    "Targeted therapy": ["targeted therapy", "EGFR", "cetuximab"],
    "Transcriptomics": ["RNA-seq", "transcriptomic", "single-cell", "scRNA"],
    "Tumor microenvironment": ["microenvironment", "TME", "immune infiltration"],
    "Machine learning/AI": ["machine learning", "deep learning"],
    "Prognosis/Survival": ["prognosis", "survival", "overall survival"],
    "Biomarker": ["biomarker"],
}

OMICS_TOPICS = {
    "Genomics": ["genomic", "WGS", "WES"],
    "Mutations": ["mutation", "variant", "somatic"],
    "CNV": ["copy number", "CNV"],
    "Proteomics": ["proteomic"],
    "Metabolomics": ["metabolomic"],
    "Multi-omics": ["multi-omics"],
    "Spatial": ["spatial transcriptomic", "Visium"],
    "Single-cell": ["single-cell", "scRNA"],
    "Liquid biopsy": ["ctDNA", "cfDNA"],
}

# ============================================================
# Helpers
# ============================================================

def contains_any(text: str, keywords: list[str]) -> bool:
    for kw in keywords:
        pattern = r"\b" + re.escape(kw.lower()) + r"\b"
        if re.search(pattern, text):
            return True
    return False


def analyze_topics(records, topic_dict, title):
    print(f"\n{title} in {len(records)} abstracts:\n")

    counts = {}

    for topic, kws in topic_dict.items():
        count = 0
        for r in records:
            text = (r.get("title", "") + " " + r.get("abstract", "")).lower()
            if contains_any(text, kws):
                count += 1

        pct = 100 * count / len(records) if records else 0
        bar = "█" * int(pct / 2)
        flag = " ⚠️" if pct < 5 else ""

        print(f" {topic:25s} {count:4d} ({pct:5.1f}%) {bar}{flag}")
        counts[topic] = count

    return counts


def analyze_sources(records):
    print("\n📊 Source distribution:\n")

    counter = Counter()

    for r in records:
        for s in r.get("source_queries", []):
            counter[s] += 1

    total = len(records)

    for k, v in counter.items():
        pct = 100 * v / total
        bar = "█" * int(pct / 2)
        print(f" {k:15s} {v:4d} ({pct:5.1f}%) {bar}")

    if not counter:
        print("⚠️ No source metadata found")


def analyze_cooccurrence(records):
    print("\n🔗 Top topic co-occurrences:\n")

    pair_counts = Counter()

    for r in records:
        text = (r.get("title", "") + " " + r.get("abstract", "")).lower()

        present = [
            topic for topic, kws in TOPICS.items()
            if contains_any(text, kws)
        ]

        for a, b in combinations(present, 2):
            pair_counts[(a, b)] += 1

    for (a, b), count in pair_counts.most_common(10):
        print(f"  {a} + {b}: {count}")


# ============================================================
# Main
# ============================================================

def main():
    if not INPUT_FILE.exists():
        print(f"❌ File not found: {INPUT_FILE}")
        return

    with INPUT_FILE.open() as f:
        records = json.load(f)

    print(f"📥 Loaded {len(records)} records")

    analyze_sources(records)

    analyze_topics(records, TOPICS, "Topic coverage")
    analyze_topics(records, OMICS_TOPICS, "Omics coverage")

    analyze_cooccurrence(records)

    print("\n✅ Done")


if __name__ == "__main__":
    main()