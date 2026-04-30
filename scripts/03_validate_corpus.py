"""
Phase 1 — Step 3: Validate cleaned corpus.

Input: data/hnscc_abstracts.json
Output: console report (no overwrite)
"""

import json
from pathlib import Path
from collections import Counter

# ============================================================
# Config
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_FILE = BASE_DIR / "data" / "hnscc_abstracts.json"

REQUIRED_FIELDS = ["pmid", "title", "abstract", "year"]

# ============================================================
# Helpers
# ============================================================

def word_count(text: str) -> int:
    return len(text.split()) if text else 0


# ============================================================
# Main
# ============================================================

def main():
    if not INPUT_FILE.exists():
        print(f"❌ File not found: {INPUT_FILE}")
        return

    with INPUT_FILE.open("r", encoding="utf-8") as f:
        records = json.load(f)

    print(f"📥 Loaded {len(records)} records")

    # ========================================================
    # 1. Schema validation
    # ========================================================

    missing_field_counts = Counter()

    for r in records:
        for field in REQUIRED_FIELDS:
            if not r.get(field):
                missing_field_counts[field] += 1

    print("\n🔎 Missing field check:")
    if missing_field_counts:
        for field, count in missing_field_counts.items():
            print(f"  {field}: {count}")
    else:
        print("  ✅ All required fields present")

    # ========================================================
    # 2. Duplicate check
    # ========================================================

    pmids = [r.get("pmid") for r in records if r.get("pmid")]
    unique_pmids = set(pmids)

    print("\n🔁 Duplicate check:")
    print(f"  Total PMIDs: {len(pmids)}")
    print(f"  Unique PMIDs: {len(unique_pmids)}")

    if len(pmids) != len(unique_pmids):
        print(f"  ⚠️ Duplicates detected: {len(pmids) - len(unique_pmids)}")
    else:
        print("  ✅ No duplicates")

    # ========================================================
    # 3. Length stats
    # ========================================================

    abstract_lengths = [word_count(r.get("abstract", "")) for r in records]
    title_lengths = [word_count(r.get("title", "")) for r in records]

    print("\n📏 Length statistics:")

    if abstract_lengths:
        print(f"  Avg abstract: {sum(abstract_lengths)/len(abstract_lengths):.0f}")
        print(f"  Min / Max: {min(abstract_lengths)} / {max(abstract_lengths)}")

    if title_lengths:
        print(f"  Avg title: {sum(title_lengths)/len(title_lengths):.0f}")

    # ========================================================
    # 4. Year distribution
    # ========================================================

    years = [r.get("year", 0) for r in records if r.get("year", 0) > 0]

    print("\n📅 Year distribution:")

    if years:
        print(f"  Range: {min(years)} - {max(years)}")

        year_counts = Counter(years)
        for y, c in sorted(year_counts.items(), reverse=True)[:10]:
            print(f"  {y}: {c}")
    else:
        print("  ⚠️ No valid year data")

    # ========================================================
    # 5. Source distribution (NEW - IMPORTANT)
    # ========================================================

    src_counter = Counter()

    for r in records:
        for s in r.get("source_queries", []):
            src_counter[s] += 1

    print("\n📊 Source distribution:")
    if src_counter:
        for k, v in src_counter.items():
            print(f"  {k}: {v}")
    else:
        print("  ⚠️ No source metadata found")

    # ========================================================
    # 6. Publication types (sanity check)
    # ========================================================

    pub_counter = Counter()

    for r in records:
        for pt in r.get("publication_types", []):
            pub_counter[pt] += 1

    print("\n📚 Top publication types:")
    for pt, count in pub_counter.most_common(10):
        print(f"  {pt}: {count}")

    # ========================================================
    # 7. Quality flags
    # ========================================================

    short_abstracts = sum(1 for r in records if word_count(r.get("abstract", "")) < 80)
    empty_abstracts = sum(1 for r in records if not r.get("abstract"))

    print("\n🚩 Quality checks:")
    print(f"  Abstracts 100 words: {short_abstracts}")
    print(f"  Empty abstracts: {empty_abstracts}")

    print("\n✅ Validation complete")


if __name__ == "__main__":
    main()