"""
Run RAGAS evaluation on stored eval results.
Augments eval_results.json with faithfulness and answer_relevancy scores.
"""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from src.config import BASE_DIR, GOOGLE_API_KEY

RESULTS_PATH = BASE_DIR / "experiments" / "eval_results.json"
OUT_PATH = BASE_DIR / "experiments" / "eval_results_with_ragas.json"


def load_full_abstract(pmid: str, lookup: dict) -> str:
    return lookup.get(pmid, "")


def main():
    with RESULTS_PATH.open() as f:
        results = json.load(f)

    # Build PMID → abstract lookup (need full retrieved context for RAGAS)
    abstracts_path = BASE_DIR / "data" / "hnscc_abstracts.json"
    with abstracts_path.open() as f:
        abstracts = json.load(f)
    pmid_to_abstract = {a["pmid"]: a["abstract"] for a in abstracts}

    # Filter to in-scope queries only (RAGAS doesn't make sense for OOS)
    in_scope = [r for r in results if r["category"] != "out_of_scope" and not r["error"]]

    print(f"Running RAGAS on {len(in_scope)} in-scope responses...")

    # Build evaluation dataset
    data = {
        "question": [r["question"] for r in in_scope],
        "answer": [r["response_text"] for r in in_scope],
        "contexts": [
            [pmid_to_abstract.get(p, "") for p in r["retrieved_pmids"]]
            for r in in_scope
        ],
    }
    dataset = Dataset.from_dict(data)

    # Configure RAGAS to use Gemini
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=GOOGLE_API_KEY,
        temperature=0,
    )
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004",
        google_api_key=GOOGLE_API_KEY,
    )

    # Run RAGAS
    scores = evaluate(
        dataset=dataset,
        metrics=[faithfulness, answer_relevancy],
        llm=llm,
        embeddings=embeddings,
    )

    # Convert to dict and merge back
    df = scores.to_pandas()
    for i, row in enumerate(in_scope):
        row["faithfulness"] = float(df["faithfulness"].iloc[i])
        row["answer_relevancy"] = float(df["answer_relevancy"].iloc[i])

    # Re-merge with OOS results
    final = []
    in_scope_idx = 0
    for r in results:
        if r["category"] != "out_of_scope" and not r["error"]:
            final.append(in_scope[in_scope_idx])
            in_scope_idx += 1
        else:
            final.append(r)

    with OUT_PATH.open("w") as f:
        json.dump(final, f, indent=2)

    print(f"\nSaved RAGAS-enhanced results to {OUT_PATH}")


if __name__ == "__main__":
    main()