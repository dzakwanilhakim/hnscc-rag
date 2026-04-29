#!/bin/bash
set -e
#conda create -n hnscc-rag python=3.11 -y
#conda activate hnscc-rag

echo "01. Core RAG Framework ================================"
pip install -U langchain langchain-community langchain-google-genai

echo "02. Vector Database ==================================="
pip install -U chromadb

echo "03. Embeddings ========================================"
pip install -U sentence-transformers

echo "04. PubMed API ========================================"
pip install -U biopython

echo "05. LLM API ==========================================="
pip install -U google-generativeai

echo "06. UI ================================================"
pip install -U streamlit

echo "07. Utilities ========================================="
pip install python-dotenv tqdm ragas ipykernel jupyterlab

echo "DONE! ========================================="
