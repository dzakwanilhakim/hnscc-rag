'''
Phase 1 — Step 1: Download HNSCC Abstract from Pubmed

output: data/hnscc_abstracts_raw.json (unfiltered)

Query design:
- Combines MeSH terms with title/abstract
- biomarker
- omics
- exlude case reports, editorials, letters, and comments, focus to primary research
- review included

'''

import os
import json
import time
import yaml
from pathlib import Path
from typing import List, Dict, Optional
from Bio import Entrez
from dotenv import load_dotenv
from tqdm import tqdm

# 0. Configuration
load_dotenv()
QUERY_FILENAME = "queries_hnscc.yaml"
Entrez.email = os.getenv("NCBI_EMAIL")
Entrez.api_key = os.getenv("NCBI_API_KEY")

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "data"
OUTPUT_FILE = OUTPUT_DIR / "hnscc_abstracts_raw.json"

MAX_RESULTS = {
    "core": 2000,
    "omics": 2500,
    "mechanistic": 2500
}
BATCH_SIZE = 100

# ============================================================
# 1. PubMed query - HNSCC focused
# ============================================================

SCRIPT_DIR = Path(__file__).resolve().parent
QUERY_PATH = SCRIPT_DIR / QUERY_FILENAME

with open(QUERY_PATH, "r") as f:
    queries = yaml.safe_load(f)["hnscc"]

print(f"Loaded queries: {list(queries.keys())}")

# ============================================================
# 2. Get PMIDs
# ============================================================

def search_pubmed(query: str, max_results: int) -> List[str]:
    """Run esearch and return list of PMIDs."""
    print(f"Searching PubMed for up to {max_results} results...")
    
    handle = Entrez.esearch(
        db="pubmed",
        term=query,
        retmax=max_results,
        sort="relevance"
    )
    record = Entrez.read(handle)
    handle.close()
    
    pmids = record["IdList"]
    total_available = int(record["Count"])
    
    print(f"Total matching in PubMed: {total_available:,}")
    print(f"Fetching: {len(pmids):,}")
    
    return pmids


# ============================================================
# 2. Get metadata for PMIDs
# ============================================================

def fetch_metadata_batch(pmids: List[str]) -> List[Dict]:
    """Fetch metadata for a batch of PMIDs with retry."""
    
    for attempt in range(3):
        try:
            handle = Entrez.efetch(
                db="pubmed",
                id=",".join(pmids),
                rettype="medline",
                retmode="xml"
            )
            records = Entrez.read(handle)
            handle.close()
            return records["PubmedArticle"]
        
        except Exception as e:
            print(f"Retry {attempt+1} failed: {e}")
            time.sleep(2)

    return []


def parse_record(record: Dict) -> Optional[Dict]:
    """Convert raw Entrez record to flat dict."""
    
    try:
        article = record["MedlineCitation"]["Article"]
        pmid = str(record["MedlineCitation"]["PMID"])

        # Title
        title = str(article.get("ArticleTitle", "")).strip()
        if not title:
            return None

        # Abstract
        abstract_data = article.get("Abstract", {}).get("AbstractText", [])
        if not abstract_data:
            return None

        if isinstance(abstract_data, list):
            parts = []
            for part in abstract_data:
                text = str(part).strip()
                label = getattr(part, "attributes", {}).get("Label")
                if label:
                    parts.append(f"{label}: {text}")
                else:
                    parts.append(text)
            abstract = " ".join(parts)
        else:
            abstract = str(abstract_data).strip()

        if not abstract:
            return None

        # Year (robust)
        year = 0
        pub_date = article.get("Journal", {}).get("JournalIssue", {}).get("PubDate", {})
        if "Year" in pub_date:
            year = int(pub_date["Year"])
        elif "MedlineDate" in pub_date:
            year = int(pub_date["MedlineDate"][:4])

        # Journal
        journal = str(article.get("Journal", {}).get("Title", "")).strip()

        # Authors
        authors = []
        for author in article.get("AuthorList", []):
            if "LastName" in author and "ForeName" in author:
                authors.append(f"{author['ForeName']} {author['LastName']}")
            elif "CollectiveName" in author:
                authors.append(str(author["CollectiveName"]))

        # Publication types
        pub_types = [str(pt) for pt in article.get("PublicationTypeList", [])]

        # MeSH terms
        mesh_terms = []
        for mesh in record["MedlineCitation"].get("MeshHeadingList", []):
            mesh_terms.append(str(mesh["DescriptorName"]))

        # DOI
        doi = ""
        for article_id in record.get("PubmedData", {}).get("ArticleIdList", []):
            if article_id.attributes.get("IdType") == "doi":
                doi = str(article_id)
                break

        return {
            "pmid": pmid,
            "title": title,
            "abstract": abstract,
            "authors": authors,
            "journal": journal,
            "year": year,
            "publication_types": pub_types,
            "mesh_terms": mesh_terms,
            "doi": doi,
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        }

    except Exception:
        return None


# ============================================================
# 3. Main
# ============================================================
def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Search (multi-query)
    all_pmids = []
    pmid_source = {}

    for name, query in queries.items():
        print(f"\n🔍 Running query: {name}")
        
        # support both int or dict MAX_RESULTS
        # max_n = MAX_RESULTS[name] if isinstance(MAX_RESULTS, dict) else MAX_RESULTS
        max_n = MAX_RESULTS.get(name, 1000)
        pmids = search_pubmed(query, max_n)
        
        for p in pmids:
            pmid_source.setdefault(p, set()).add(name)
        
        all_pmids.extend(pmids)

    # Deduplicate
    pmids = list(set(all_pmids))

    print(f"\nTotal unique PMIDs: {len(pmids)}")
    if not pmids:
        print("No results returned. Check query or API key.")
        return
    
    # 2. Fetch metadata
    print(f"\nFetching metadata in batches of {BATCH_SIZE}...")
    
    all_records = []
    failed_batches = 0
    
    for i in tqdm(range(0, len(pmids), BATCH_SIZE), desc="Batches"):
        batch = pmids[i:i + BATCH_SIZE]
        
        try:
            records = fetch_metadata_batch(batch)
            for r in records:
                parsed = parse_record(r)
                if parsed:
                    # ✅ attach source info (IMPORTANT FIX)
                    parsed["source_queries"] = sorted(list(pmid_source.get(parsed["pmid"], [])))
                    all_records.append(parsed)
        
        except Exception as e:
            failed_batches += 1
            print(f"\n⚠️ Batch {i//BATCH_SIZE} failed: {e}")
        
        time.sleep(0.15)
    
    if failed_batches:
        print(f"\n⚠️ {failed_batches} batch(es) failed")
    
    print(f"\n✅ Parsed {len(all_records)} / {len(pmids)} records")
    
    # 3. Save
    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(all_records, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Saved to: {OUTPUT_FILE}")
    print(f"File size: {OUTPUT_FILE.stat().st_size / 1024 / 1024:.2f} MB")

if __name__ == "__main__":
    main()