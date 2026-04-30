"""
Phase 1 — Step 2: Filter and clean raw abstracts.

Input: data/hnscc_abstracts_raw.json
Output: data/hnscc_abstracts.json (cleaned, deduplicated)
"""

import json
import re
from pathlib import Path
from collections import Counter
from typing import Tuple

# ============================================================
# Configuration
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data" / "hnscc_abstracts_raw.json"
OUTPUT_FILE = BASE_DIR / "data" / "hnscc_abstracts.json"

MIN_ABSTRACT_WORDS = 100
MIN_TITLE_WORDS = 4
TARGET_SIZE = 3000

# ============================================================
# Helpers
# ============================================================

def word_count(text: str) -> int:
    return len(text.split()) if text else 0


def clean_text(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


# ============================================================
# Filters
# ============================================================

def is_valid_abstract(record: dict) -> Tuple[bool, str]:
    abstract = record.get("abstract", "")
    title = record.get("title", "")

    if word_count(abstract) < MIN_ABSTRACT_WORDS:
        return False, "abstract_too_short"

    if word_count(title) < MIN_TITLE_WORDS:
        return False, "title_too_short"

    pub_types = record.get("publication_types", [])
    bad_types = {"Erratum", "Retraction of Publication", "Comment"}

    if any(pt in bad_types for pt in pub_types):
        return False, "bad_publication_type"

    if "Letter" in pub_types and word_count(abstract) < 200:
        return False, "letter_too_short"

    return True, ""


# ============================================================
# Main
# ============================================================

def main():
    if not INPUT_FILE.exists():
        print(f"Input file not found: {INPUT_FILE}")
        return

    with INPUT_FILE.open("r", encoding="utf-8") as f:
        records = json.load(f)

    print(f"Loaded {len(records)} raw records")

    # ========================================================
    # Deduplicate + merge source_queries
    # ========================================================

    pmid_map = {}

    for r in records:
        pmid = r.get("pmid")
        if not pmid:
            continue

        if pmid not in pmid_map:
            pmid_map[pmid] = r
        else:
            # merge source_queries if exists
            existing = pmid_map[pmid]
            existing_sources = set(existing.get("source_queries", []))
            new_sources = set(r.get("source_queries", []))
            existing["source_queries"] = sorted(existing_sources | new_sources)

    unique_records = list(pmid_map.values())

    print(f"After deduplication: {len(unique_records)}")

    # ========================================================
    # Filter
    # ========================================================

    filtered = []
    rejection_reasons = Counter()

    for r in unique_records:
        valid, reason = is_valid_abstract(r)

        if valid:
            # copy to avoid mutating original
            cleaned = dict(r)
            cleaned["title"] = clean_text(r.get("title", ""))
            cleaned["abstract"] = clean_text(r.get("abstract", ""))
            filtered.append(cleaned)
        else:
            rejection_reasons[reason] += 1

    print("\nRejection breakdown:")
    for reason, count in rejection_reasons.most_common():
        print(f"  {reason}: {count}")

    print(f"\nFiltered records: {len(filtered)}")

    # ========================================================
    # Sort + cap
    # ========================================================

    filtered.sort(key=lambda r: r.get("year", 0) or 0, reverse=True)
    final = filtered[:TARGET_SIZE]

    print(f"Final corpus size: {len(final)}")

    # ========================================================
    # Stats
    # ========================================================

    years = [r.get("year", 0) for r in final if r.get("year", 0) > 0]
    word_counts = [word_count(r.get("abstract", "")) for r in final]

    print("\nCorpus statistics:")

    if years:
        print(f"  Year range: {min(years)} - {max(years)}")
    else:
        print("  Year range: N/A")

    if word_counts:
        avg_len = sum(word_counts) / len(word_counts)
        print(f"  Avg abstract length: {avg_len:.0f} words")
        print(f"  Min / Max length: {min(word_counts)} / {max(word_counts)} words")
    else:
        print("  No valid word count stats")

    # ========================================================
    # Save
    # ========================================================

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(final, f, indent=2, ensure_ascii=False)

    size_mb = OUTPUT_FILE.stat().st_size / 1024 / 1024
    print(f"\nSaved cleaned corpus to: {OUTPUT_FILE}")
    print(f"  File size: {size_mb:.2f} MB")


if __name__ == "__main__":
    main()