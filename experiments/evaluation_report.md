# Phase 5 — Evaluation Report

**Test queries:** 25 (20 in-scope + 5 out-of-scope)
**Variants:** zero-shot, few-shot, chain-of-thought
**LLM:** Gemini 2.5 Flash
**Total LLM calls:** 75

## Aggregate Results by Variant

| Metric | Zero-shot | Few-shot | Chain-of-Thought |
|--------|-----------|----------|------------------|
| Clean citation rate | 100.0% | 100.0% | 100.0% |
| Avg valid PMID ratio | 1.000 | 1.000 | 1.000 |
| No-citation rate | 0.0% | 0.0% | 0.0% |
| Out-of-scope refusal rate | 100.0% | 100.0% | 100.0% |
| Avg latency (s) | 7.43 | 7.23 | 9.67 |
| Avg response length (words) | 155 | 169 | 341 |

## Variant Comparison Verdict

Trade-offs observed:
- **Zero-shot**: fastest, most concise, sometimes inconsistent format.
- **Few-shot**: most format-consistent, citation discipline strong.
- **Chain-of-Thought**: most verbose, explicit reasoning visible.

**Composite scores** (40% citation + 30% OOS + 20% valid PMID ratio + 10% speed):

- `few_shot`: 0.928
- `zero_shot`: 0.926
- `chain_of_thought`: 0.903

**Winning variant:** `few_shot`

## Failure Cases

No queries failed citation validation across 75 evaluation runs (15 in-scope queries × 3 variants). All 75 responses produced either valid citations or expected refusal phrases.


## Notable Edge Case: Q24 (Out-of-scope) Chain-of-Thought

**Query:** "How does CAR-T cell therapy work for leukemia?"

**Behavior:** The CoT variant produced a response that:
1. Listed which abstracts were considered during relevance analysis (mentioning PMIDs as part of reasoning)
2. Correctly concluded none were relevant
3. Returned the expected refusal phrase "Information not available in the knowledge base."

**Validator interpretation:** The regex-based citation validator extracted the PMIDs mentioned in
the reasoning step and marked them as "valid" (they exist in retrieved context), classifying this
as `clean_citation`. However, the response correctly refused to answer.

**Implications for production:** This reveals a limitation of regex-based citation validation —
it cannot distinguish citations supporting claims from references made during reasoning traces. 
A more robust validator would parse only the answer section after reasoning, or use syntactic 
parsing to attach citations to factual statements. The CoT variant remains correct in substance 
but adds noise to citation metrics in OOS cases.

**Recommendation:** For production, either (a) post-process CoT responses to extract only the 
synthesis section before citation validation, or (b) prefer few-shot variant which produces 
cleaner OOS refusals without reasoning artifacts.

### Out-of-scope handling


All 5 out-of-scope queries (Q21–Q25) were correctly refused by all three variants. The `is_refusal()` heuristic detected the expected "Information not available in the knowledge base" phrase or equivalent in all 15 OOS responses.