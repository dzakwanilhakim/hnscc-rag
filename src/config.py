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