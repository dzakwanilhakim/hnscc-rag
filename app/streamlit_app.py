"""
HNSCC-RAG — Streamlit UI

A citation-aware research assistant for head and neck squamous cell carcinoma,
powered by retrieval-augmented generation over PubMed literature.
"""

import sys
from pathlib import Path

# Make src importable when running with `streamlit run`
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from src.rag_chain import HNSCCRAGChain
from src.config import DEFAULT_PROMPT_VARIANT, DEFAULT_TOP_K
from app.components import (
    render_response_with_citations,
    render_retrieved_abstracts,
    render_validation_badge,
    render_metrics_row,
)


# ============================================================
# Page config (must be first Streamlit call)
# ============================================================

st.set_page_config(
    page_title="HNSCC-RAG | Clinical Research Assistant",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# Initialize RAG chain (cached so it loads only once)
# ============================================================

@st.cache_resource
def load_chain():
    """Load the RAG chain once and cache it."""
    return HNSCCRAGChain()


# ============================================================
# Header
# ============================================================

st.title(" HNSCC-RAG")
st.markdown(
    "**A citation-aware research assistant for head and neck squamous cell carcinoma, focused in clinical, therapy, omics, and pathways. (May 2026)**  \n"
    "_Built with LangChain, ChromaDB, S-PubMedBert embeddings, and Gemini._  \n"
    "github: https://github.com/dzakwanilhakim/hnscc-rag/  "
)
st.divider()


# ============================================================
# Sidebar — settings and info
# ============================================================

with st.sidebar:
    st.markdown("## ⚙️ Settings")

    variant = st.selectbox(
        "Prompt strategy",
        options=["few_shot", "zero_shot", "chain_of_thought"],
        index=["few_shot", "zero_shot", "chain_of_thought"].index(DEFAULT_PROMPT_VARIANT),
        help=(
            "**Few-shot** (default): example-driven, format-consistent.  \n"
            "**Zero-shot**: direct instruction, fastest.  \n"
            "**Chain-of-Thought**: explicit reasoning, most thorough."
        ),
    )

    k = st.slider(
        "Number of sources to retrieve",
        min_value=3,
        max_value=10,
        value=DEFAULT_TOP_K,
        help="More sources = broader evidence but longer response."
    )

    st.divider()

    st.markdown("## 📖 About")
    st.markdown(
        "This system retrieves from **~3,000 PubMed abstracts** focused on HNSCC "
        "research published 2018–2026, covering biomarkers, immunotherapy, "
        "molecular subtyping, and treatment.  \n\n"
        "**Scope:** HNSCC clinical and molecular research only.  \n"
        "**Disclaimer:** Research tool, not for clinical decision-making."
    )

    st.divider()
    st.caption("Built by Dzakwanil Hakim — HNSCC-RAG MVP")


# ============================================================
# Main interaction
# ============================================================

# Example queries
example_queries = [
    "What is the prognostic significance of HPV status in OPSCC?",
    "How does PD-L1 expression affect immunotherapy response?",
    "What single-cell studies have characterized HNSCC heterogeneity?",
    "What are common somatic mutations in HNSCC?",
]

st.markdown("### 💬 IS THAT REAL CHAT?!?!?! (Ask a research question about HNSCC)\n")
st.markdown("**at the left panel, you can configure the number of source of citation (default: 5) and the promp strategy (best: few_shot)")

# Quick-pick examples
# Initialize session state for the query text
if "query_text" not in st.session_state:
    st.session_state.query_text = ""

# Example query buttons — clicking sets the query text in session state
cols = st.columns(len(example_queries))
for i, ex in enumerate(example_queries):
    with cols[i]:
        if st.button(f"📌 {ex[:35]}...", key=f"example_{i}", use_container_width=True):
            st.session_state.query_text = ex

# Text area bound to session state via key
query = st.text_area(
    "Your question:",
    height=100,
    placeholder="e.g., What is the role of MGMT methylation in HNSCC prognosis?",
    key="query_text",
)
submit = st.button("🔍 Search literature", type="primary", use_container_width=True)


# ============================================================
# Run RAG pipeline
# ============================================================

if submit and query.strip():
    chain = load_chain()
    status_placeholder = st.empty()

    try:
        with status_placeholder.container():
            with st.spinner("🔎 Searching PubMed literature..."):
                # In production you might separate retrieval & generation
                response = chain.run(query.strip(), variant=variant, k=k)

        status_placeholder.empty()

    except Exception as e:
        st.error(f"❌ Error: {e}")
        st.stop()

    if response.error:
        st.error(f"❌ Pipeline error: {response.error}")
        st.stop()

    # ------------------------------------------------------------
    # Layout: response on left, sources on right
    # ------------------------------------------------------------

    col_main, col_sources = st.columns([2, 1])

    with col_main:
        st.markdown("### 📄 Response")
        render_metrics_row(response)
        render_validation_badge(response.validation)
        st.divider()
        render_response_with_citations(response.response_text, response.retrieved)

        # Optional: show prompt for transparency
        with st.expander("🔬 View prompt sent to LLM (for transparency)"):
            st.code(response.prompt, language="markdown")

    with col_sources:
        render_retrieved_abstracts(response.retrieved)


elif submit and not query.strip():
    st.warning("Please enter a question.")

else:
    st.info(
        "💡 Tip: Try one of the example queries above, or ask your own HNSCC research question. "
        "The system will retrieve from PubMed literature and answer with citations."
    )