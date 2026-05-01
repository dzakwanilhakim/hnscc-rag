"""
Prompt templates for HNSCC-RAG generation.

Three variants for systematic comparison:
- VARIANT_A: Zero-shot with citation enforcement
- VARIANT_B: Few-shot with formatted examples
- VARIANT_C: Chain-of-Thought reasoning
"""

from typing import List


# ============================================================
# Shared system instructions
# ============================================================

SYSTEM_INSTRUCTION = """You are a biomedical research assistant specialized in head and neck \
squamous cell carcinoma (HNSCC). Your role is to answer research questions using only the \
provided abstracts as evidence.

CRITICAL RULES:
1. EVERY sentence containing a factual claim MUST end with a citation in the format [PMID:xxxxxxxx], \
where xxxxxxxx is the exact PMID from one of the provided abstracts. No exceptions.
2. Use ONLY the PMIDs that appear in the provided abstracts. Do NOT invent, modify, shorten, \
or paraphrase any PMID.
3. PMIDs are 7 to 9 digit numbers. Always copy them in full.
4. If you cannot answer the question using the provided abstracts, respond with EXACTLY this \
text and nothing else: "Information not available in the knowledge base."
5. Do not use external knowledge. Do not make treatment recommendations.
6. Be concise and evidence-grounded.

Required output format:
- Main answer with inline [PMID:xxxxxxxx] citations.
- A "References" section listing each cited PMID on its own line."""


# ============================================================
# Context formatting helper
# ============================================================

def format_context(abstracts: List[dict]) -> str:
    """
    Format retrieved abstracts as numbered context block.

    Each abstract is shown with index, PMID, year, title, and abstract text.
    """
    blocks = []
    for i, a in enumerate(abstracts, 1):
        block = (
            f"[Abstract {i}] PMID:{a['pmid']} | Year:{a.get('year', 'N/A')}\n"
            f"Title: {a['title']}\n"
            f"Abstract: {a['abstract']}"
        )
        blocks.append(block)
    return "\n\n".join(blocks)


# ============================================================
# VARIANT A — Zero-shot with citation enforcement
# ============================================================

VARIANT_A_TEMPLATE = """{system}

Below are {n} abstracts retrieved from the HNSCC literature. Use them to answer the question.

CONTEXT:
{context}

QUESTION:
{question}

Provide a concise answer with inline citations of the form [PMID:xxxxx]. \
End with a "References" section listing the cited PMIDs."""


def build_variant_a(question: str, abstracts: List[dict]) -> str:
    return VARIANT_A_TEMPLATE.format(
        system=SYSTEM_INSTRUCTION,
        n=len(abstracts),
        context=format_context(abstracts),
        question=question,
    )


# ============================================================
# VARIANT B — Few-shot with formatted examples
# ============================================================

FEW_SHOT_EXAMPLES = """EXAMPLE 1:
Question: What is the role of HPV in oropharyngeal cancer?
Answer: HPV-positive oropharyngeal cancer is associated with better prognosis compared to \
HPV-negative tumors [PMID:12345678]. The improved outcomes are linked to distinct molecular \
features and stronger immune response [PMID:23456789].

References:
- PMID:12345678
- PMID:23456789

---

EXAMPLE 2:
Question: How does PD-L1 expression affect immunotherapy response?
Answer: Higher PD-L1 expression generally correlates with better response to checkpoint inhibitors \
in HNSCC [PMID:34567890]. However, response is not universal, as PD-L1-low tumors can still benefit \
from combination strategies [PMID:45678901].

References:
- PMID:34567890
- PMID:45678901

---
"""


VARIANT_B_TEMPLATE = """{system}

Below are example responses showing the required format, followed by {n} abstracts to use.

{examples}

CONTEXT:
{context}

QUESTION:
{question}

Provide your answer in the same format as the examples above. Use only the PMIDs from \
the provided abstracts."""


def build_variant_b(question: str, abstracts: List[dict]) -> str:
    return VARIANT_B_TEMPLATE.format(
        system=SYSTEM_INSTRUCTION,
        n=len(abstracts),
        examples=FEW_SHOT_EXAMPLES,
        context=format_context(abstracts),
        question=question,
    )


# ============================================================
# VARIANT C — Chain-of-Thought reasoning
# ============================================================

VARIANT_C_TEMPLATE = """{system}

Below are {n} abstracts from HNSCC literature. Answer the question using a structured \
reasoning approach.

CONTEXT:
{context}

QUESTION:
{question}

Follow this process exactly:

STEP 1 — RELEVANCE ANALYSIS:
List which abstracts (by Abstract number) are relevant to the question and briefly \
explain why each one is relevant.

STEP 2 — SYNTHESIS:
Synthesize the relevant evidence into a coherent answer with inline [PMID:xxxxx] citations.

STEP 3 — REFERENCES:
List all cited PMIDs."""


def build_variant_c(question: str, abstracts: List[dict]) -> str:
    return VARIANT_C_TEMPLATE.format(
        system=SYSTEM_INSTRUCTION,
        n=len(abstracts),
        context=format_context(abstracts),
        question=question,
    )


# ============================================================
# Public API
# ============================================================

PROMPT_BUILDERS = {
    "zero_shot": build_variant_a,
    "few_shot": build_variant_b,
    "chain_of_thought": build_variant_c,
}


def build_prompt(variant: str, question: str, abstracts: List[dict]) -> str:
    """Build prompt for a given variant."""
    if variant not in PROMPT_BUILDERS:
        raise ValueError(f"Unknown variant: {variant}. Choose from {list(PROMPT_BUILDERS)}")
    return PROMPT_BUILDERS[variant](question, abstracts)