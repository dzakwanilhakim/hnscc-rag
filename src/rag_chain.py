"""
Full RAG pipeline: retrieval + generation + citation validation.
"""

import os
import time
from dataclasses import dataclass, field
from typing import List, Optional

from dotenv import load_dotenv
from google import genai
from google.genai import types

from src.retriever import HNSCCRetriever, RetrievalResult
from src.prompts import build_prompt
from src.validators import validate_citations, CitationValidation
from src.config import LLM_MODEL, GOOGLE_API_KEY, DEFAULT_TOP_K

load_dotenv()


# ============================================================
# Result container
# ============================================================

@dataclass
class RAGResponse:
    """End-to-end RAG output with diagnostics."""
    question: str
    variant: str
    retrieved: List[RetrievalResult]
    prompt: str
    response_text: str
    validation: CitationValidation
    latency_seconds: float
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "question": self.question,
            "variant": self.variant,
            "retrieved_pmids": [r.pmid for r in self.retrieved],
            "response_text": self.response_text,
            "cited_pmids": self.validation.cited_pmids,
            "valid_pmids": self.validation.valid_pmids,
            "invalid_pmids": self.validation.invalid_pmids,
            "valid_ratio": self.validation.valid_ratio,
            "is_clean": self.validation.is_clean,
            "latency_seconds": self.latency_seconds,
            "error": self.error,
        }


# ============================================================
# RAG Chain
# ============================================================

class HNSCCRAGChain:
    """
    End-to-end RAG pipeline.

    Usage:
        chain = HNSCCRAGChain()
        response = chain.run("What is the role of HPV in OPSCC?", variant="few_shot")
        print(response.response_text)
        print(response.validation.summary())
    """

    def __init__(
        self,
        retriever: Optional[HNSCCRetriever] = None,
        model_name: str = LLM_MODEL,
        api_key: Optional[str] = None,
        temperature: float = 0.1,
        max_output_tokens: int = 1024,
    ):
        self.retriever = retriever or HNSCCRetriever()
        self.model_name = model_name
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens

        api_key = api_key or GOOGLE_API_KEY
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not set. Check your .env file.")

        self.client = genai.Client(api_key=api_key)

    # --------------------------------------------------------
    # LLM call
    # --------------------------------------------------------

    def _call_llm(self, prompt: str) -> str:
        """Call Gemini and return response text."""
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=self.temperature,
                max_output_tokens=self.max_output_tokens,
            ),
        )
        return response.text

    # --------------------------------------------------------
    # Public API
    # --------------------------------------------------------

    def run(
        self,
        question: str,
        variant: str = "zero_shot",
        k: int = DEFAULT_TOP_K,
    ) -> RAGResponse:
        """
        Run full RAG pipeline.

        Args:
            question: User's research question.
            variant: Prompt variant ("zero_shot", "few_shot", "chain_of_thought").
            k: Number of abstracts to retrieve.

        Returns:
            RAGResponse with response text, citation validation, and diagnostics.
        """
        start = time.time()

        # 1. Retrieve
        retrieved = self.retriever.retrieve(question, k=k)

        # 2. Format abstracts for prompt
        abstracts_for_prompt = [
            {
                "pmid": r.pmid,
                "title": r.title,
                "abstract": r.abstract,
                "year": r.year,
            }
            for r in retrieved
        ]

        # 3. Build prompt
        prompt = build_prompt(variant, question, abstracts_for_prompt)

        # 4. Call LLM
        try:
            response_text = self._call_llm(prompt)
            error = None
        except Exception as e:
            response_text = ""
            error = str(e)

        # 5. Validate citations
        context_pmids = [r.pmid for r in retrieved]
        validation = validate_citations(response_text, context_pmids)

        latency = time.time() - start

        return RAGResponse(
            question=question,
            variant=variant,
            retrieved=retrieved,
            prompt=prompt,
            response_text=response_text,
            validation=validation,
            latency_seconds=latency,
            error=error,
        )