"""
Reusable Streamlit components for HNSCC-RAG UI.
"""

from typing import List
import streamlit as st

from src.retriever import RetrievalResult


def render_response_with_citations(response_text: str, retrieved: List[RetrievalResult]):
    """Render response with PMIDs as clickable citations."""
    if not response_text:
        st.warning("No response generated.")
        return

    # Build PMID → metadata lookup for hyperlinking
    pmid_to_url = {r.pmid: r.url for r in retrieved}

    # Replace [PMID:xxxxx] with clickable links
    rendered = response_text
    for pmid, url in pmid_to_url.items():
        rendered = rendered.replace(
            f"[PMID:{pmid}]",
            f"[\\[PMID:{pmid}\\]]({url})"
        )

    st.markdown(rendered)


def render_retrieved_abstracts(retrieved: List[RetrievalResult]):
    """Render retrieved abstracts as expandable cards in sidebar."""
    if not retrieved:
        st.info("No abstracts retrieved.")
        return

    st.markdown(f"###  Retrieved Sources ({len(retrieved)})")

    for i, r in enumerate(retrieved, 1):
        # Color-code similarity
        if r.similarity >= 0.85:
            sim_emoji = "🟢"
        elif r.similarity >= 0.70:
            sim_emoji = "🟡"
        else:
            sim_emoji = "🟠"

        with st.expander(
            f"{sim_emoji} [{i}] PMID:{r.pmid} — {r.title[:80]}..."
        ):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**Title:** {r.title}")
                st.markdown(f"**Journal:** _{r.journal}_ ({r.year})")
            with col2:
                st.metric("Similarity", f"{r.similarity:.3f}")

            st.markdown("**Abstract:**")
            st.markdown(f"_{r.abstract}_")

            st.markdown(f"[🔗 View on PubMed]({r.url})")

            if r.source_queries:
                st.caption(f"Source queries: {', '.join(r.source_queries)}")


def render_validation_badge(validation):
    """Render citation validation status as a badge."""
    if validation.missing_citations:
        st.warning("⚠️  No citations found in response")
    elif validation.is_clean:
        st.success(f"✅ All {len(validation.cited_pmids)} citations valid")
    else:
        st.error(
            f"⚠️  {len(validation.invalid_pmids)}/{len(validation.cited_pmids)} citations invalid"
        )


def render_metrics_row(response):
    """Render a row of small metrics about the response."""
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Sources retrieved", len(response.retrieved))
    with col2:
        st.metric("Citations", len(response.validation.cited_pmids))
    with col3:
        st.metric("Latency", f"{response.latency_seconds:.1f}s")
    with col4:
        avg_sim = (
            sum(r.similarity for r in response.retrieved) / len(response.retrieved)
            if response.retrieved else 0
        )
        st.metric("Avg similarity", f"{avg_sim:.2f}")