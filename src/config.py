"""
Centralized configuration for HNSCC-RAG project.
All paths, model names, and constants live here.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# Paths
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CHROMA_DB_PATH = DATA_DIR / "chroma_db"
ABSTRACTS_PATH = DATA_DIR / "hnscc_abstracts.json"

# ============================================================
# Models
# ============================================================

EMBEDDING_MODEL = "pritamdeka/S-PubMedBert-MS-MARCO"
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash")

# ============================================================
# ChromaDB
# ============================================================

COLLECTION_NAME = "hnscc_abstracts"

# ============================================================
# Retrieval defaults
# ============================================================

DEFAULT_TOP_K = 5
MAX_TOP_K = 20  # for re-ranking later

# ============================================================
# API Keys
# ============================================================

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# ============================================================
# Production prompt variant
# ============================================================

# Selected from Phase 5 evaluation (composite score 0.928)
DEFAULT_PROMPT_VARIANT = "few_shot"

# ============================================================
# API Keys (works for both local .env and Streamlit Cloud secrets)
# ============================================================

def _get_secret(key: str, default: str = "") -> str:
    """
    Try Streamlit secrets first (production), fall back to env (local dev).
    """
    # Try Streamlit secrets if running under Streamlit
    try:
        import streamlit as st
        if key in st.secrets:
            return st.secrets[key]
    except (ImportError, FileNotFoundError, Exception):
        pass
    # Fall back to environment variable
    return os.getenv(key, default)


GOOGLE_API_KEY = _get_secret("GOOGLE_API_KEY")
NCBI_API_KEY = _get_secret("NCBI_API_KEY")
NCBI_EMAIL = _get_secret("NCBI_EMAIL")
LLM_MODEL = _get_secret("LLM_MODEL", "gemini-2.5-flash")