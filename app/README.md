# HNSCC-RAG Streamlit UI

## Run locally

```bash
conda activate hnscc-rag
streamlit run app/streamlit_app.py
```

App opens at http://localhost:8501.

## Features

- Three prompt strategies (zero-shot, few-shot, chain-of-thought)
- Adjustable retrieval depth (3-10 abstracts)
- Inline citations linked to PubMed
- Sidebar showing retrieved abstracts with similarity scores
- Citation validation (catches LLM hallucinations)
- Out-of-scope refusal when knowledge base doesn't support a query

## Architecture

UI layer → `HNSCCRAGChain` (in `src/`) → ChromaDB + Gemini API.
The UI is a thin layer; all RAG logic lives in `src/`.