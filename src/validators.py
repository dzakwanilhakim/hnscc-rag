"""
Citation validator for RAG responses.

Verifies that PMIDs cited in the LLM output exist in the retrieved context.
This catches the common failure mode of hallucinated citations.
"""

import re
from dataclasses import dataclass
from typing import List, Set


@dataclass
class CitationValidation:
    """Result of validating citations in a generated response."""
    cited_pmids: List[str]      # PMIDs found in the response
    valid_pmids: List[str]      # cited PMIDs that exist in context
    invalid_pmids: List[str]    # cited PMIDs NOT in context (hallucinated)
    missing_citations: bool     # True if response has zero citations
    valid_ratio: float          # valid / total cited
    is_clean: bool              # True if all citations are valid

    def summary(self) -> str:
        if self.missing_citations:
            return "⚠️  No citations found in response."
        if self.is_clean:
            return f"✅ All {len(self.cited_pmids)} citations valid."
        return (
            f"⚠️  {len(self.invalid_pmids)}/{len(self.cited_pmids)} citations invalid: "
            f"{self.invalid_pmids}"
        )

PMID_PATTERN = re.compile(r"\bPMID[:\s]*(\d{7,9})\b", re.IGNORECASE)


def extract_pmids(text: str) -> List[str]:
    """Extract all PMIDs mentioned in text."""
    matches = PMID_PATTERN.findall(text)
    # Deduplicate while preserving order
    seen = set()
    out = []
    for pmid in matches:
        if pmid not in seen:
            seen.add(pmid)
            out.append(pmid)
    return out


def validate_citations(
    response_text: str,
    context_pmids: List[str],
) -> CitationValidation:
    """
    Validate citations in a response against the retrieved context.

    Args:
        response_text: The LLM's generated answer.
        context_pmids: List of PMIDs that were actually in the retrieved context.

    Returns:
        CitationValidation with diagnostic info.
    """
    cited = extract_pmids(response_text)
    context_set: Set[str] = set(context_pmids)

    valid = [p for p in cited if p in context_set]
    invalid = [p for p in cited if p not in context_set]

    missing = len(cited) == 0
    valid_ratio = len(valid) / len(cited) if cited else 0.0

    return CitationValidation(
        cited_pmids=cited,
        valid_pmids=valid,
        invalid_pmids=invalid,
        missing_citations=missing,
        valid_ratio=valid_ratio,
        is_clean=(not missing) and (len(invalid) == 0),
    )