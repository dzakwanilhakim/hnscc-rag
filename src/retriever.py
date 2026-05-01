"""
HNSCC-RAG Retriever Module.

Wraps embedding model + ChromaDB into a clean retrieval interface.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any

import chromadb
from sentence_transformers import SentenceTransformer

from src.config import (
    CHROMA_DB_PATH,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    DEFAULT_TOP_K,
)


# ============================================================
# Result schema
# ============================================================

@dataclass
class RetrievalResult:
    """Single retrieved document with metadata and similarity."""
    pmid: str
    title: str
    abstract: str
    year: int
    journal: str
    doi: str
    url: str
    source_queries: List[str]
    similarity: float  # cosine similarity, 0..1 (higher = more relevant)
    distance: float    # cosine distance, 0..2 (lower = more relevant)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pmid": self.pmid,
            "title": self.title,
            "abstract": self.abstract,
            "year": self.year,
            "journal": self.journal,
            "doi": self.doi,
            "url": self.url,
            "source_queries": self.source_queries,
            "similarity": self.similarity,
            "distance": self.distance,
        }


# ============================================================
# Retriever
# ============================================================

class HNSCCRetriever:
    """
    Dense retrieval over HNSCC abstracts using S-PubMedBert + ChromaDB.

    Usage:
        retriever = HNSCCRetriever()
        results = retriever.retrieve("HPV in oropharyngeal cancer", k=5)
    """

    def __init__(
        self,
        embedding_model: str = EMBEDDING_MODEL,
        chroma_path: str = str(CHROMA_DB_PATH),
        collection_name: str = COLLECTION_NAME,
        device: str = "cpu",
    ):
        self.embedding_model_name = embedding_model
        self.device = device

        print(f"Loading embedding model: {embedding_model} on {device}")
        self.model = SentenceTransformer(embedding_model, device=device)
        print(f"  Embedding dim: {self.model.get_sentence_embedding_dimension()}")

        print(f"Connecting to ChromaDB at: {chroma_path}")
        self.client = chromadb.PersistentClient(path=chroma_path)
        self.collection = self.client.get_collection(name=collection_name)
        print(f"  Collection size: {self.collection.count()}")

    # --------------------------------------------------------
    # Internal helpers
    # --------------------------------------------------------

    def _encode_query(self, query: str) -> List[float]:
        """Encode a single query string into a normalized embedding."""
        emb = self.model.encode(
            [query],
            normalize_embeddings=True,
            show_progress_bar=False,
        )[0]
        return emb.tolist()

    def _parse_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Parse stored metadata back into Python types."""
        # source_queries was stored as comma-separated string in Phase 2
        source_queries_raw = metadata.get("source_queries", "")
        source_queries = (
            [s.strip() for s in source_queries_raw.split(",") if s.strip()]
            if source_queries_raw
            else []
        )

        return {
            "pmid": metadata.get("pmid", ""),
            "title": metadata.get("title", ""),
            "abstract": metadata.get("abstract", ""),
            "year": int(metadata.get("year", 0) or 0),
            "journal": metadata.get("journal", ""),
            "doi": metadata.get("doi", ""),
            "url": metadata.get("url", ""),
            "source_queries": source_queries,
        }

    # --------------------------------------------------------
    # Public API
    # --------------------------------------------------------

    def retrieve(
        self,
        query: str,
        k: int = DEFAULT_TOP_K,
        filter_year_min: Optional[int] = None,
        filter_year_max: Optional[int] = None,
        filter_source: Optional[str] = None,
    ) -> List[RetrievalResult]:
        """
        Retrieve top-k abstracts for a query.

        Args:
            query: User question or topic.
            k: Number of results to return.
            filter_year_min: Only include abstracts from this year onward.
            filter_year_max: Only include abstracts up to this year.
            filter_source: Only include abstracts from this query source
                           (e.g., "core", "omics", "mechanistic").

        Returns:
            List of RetrievalResult, sorted by similarity descending.
        """
        # Build metadata filter (ChromaDB "where" clause)
        where_filter = self._build_where_filter(
            filter_year_min, filter_year_max, filter_source
        )

        # Encode query
        query_embedding = self._encode_query(query)

        # Query ChromaDB
        chroma_results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=where_filter,
        )

        # Parse into structured results
        results = []
        for i in range(len(chroma_results["ids"][0])):
            metadata = chroma_results["metadatas"][0][i]
            distance = float(chroma_results["distances"][0][i])
            similarity = 1.0 - distance

            parsed = self._parse_metadata(metadata)
            results.append(RetrievalResult(
                **parsed,
                similarity=similarity,
                distance=distance,
            ))

        return results

    def retrieve_pmids(
        self,
        query: str,
        k: int = DEFAULT_TOP_K,
    ) -> List[str]:
        """Convenience method: return only the top-k PMIDs."""
        results = self.retrieve(query, k=k)
        return [r.pmid for r in results]

    def _build_where_filter(
        self,
        year_min: Optional[int],
        year_max: Optional[int],
        source: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        """Construct ChromaDB metadata filter."""
        conditions = []

        if year_min is not None:
            conditions.append({"year": {"$gte": year_min}})
        if year_max is not None:
            conditions.append({"year": {"$lte": year_max}})
        if source is not None:
            # source_queries is stored as comma-separated string;
            # exact match works for single-source queries
            conditions.append({"source_queries": {"$contains": source}})

        if not conditions:
            return None
        if len(conditions) == 1:
            return conditions[0]
        return {"$and": conditions}

