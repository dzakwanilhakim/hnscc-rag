"""
Out-of-scope refusal detector.

Checks whether a response contains the expected refusal phrase or equivalent.
"""

REFUSAL_KEYWORDS = [
    "not available in the knowledge base",
    "information not available",
    "cannot answer",
    "no relevant abstracts",
    "no information",
    "out of scope",
    "outside the scope",
    "do not contain",
    "do not include",
]


def is_refusal(response_text: str) -> bool:
    """
    Heuristic check: does the response refuse to answer?
    Returns True if any refusal phrase appears.
    """
    if not response_text:
        return False
    text_lower = response_text.lower()
    return any(phrase in text_lower for phrase in REFUSAL_KEYWORDS)