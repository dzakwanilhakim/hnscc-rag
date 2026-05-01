# Phase 3 — Retrieval Evaluation Report

**Test queries:** 20
**Top-K:** 5

## Aggregate Metrics

- **Coverage@5** (≥1 relevant in top-5): 20/20 = 100.0%
- **Avg Topic Recall@5**: 0.910
- **Avg Similarity**: 0.951

## Source Distribution of Retrieved Papers

- `core`: 66 (48.5%)
- `omics`: 55 (40.4%)
- `mechanistic`: 15 (11.0%)

## Per-Query Results

| ID | Category | Coverage | Recall@5 | Avg Sim | Query |
|----|----------|----------|----------|---------|-------|
| Q01 | HPV | ✅ | 1.00 | 0.959 | What is the prognostic significance of HPV status in orophar... |
| Q02 | Immunotherapy | ✅ | 1.00 | 0.960 | How does PD-L1 expression affect immunotherapy response in h... |
| Q03 | TME | ✅ | 0.60 | 0.948 | What role do tumor-infiltrating lymphocytes play in HNSCC tu... |
| Q04 | Targeted therapy | ✅ | 1.00 | 0.961 | What are the latest developments in EGFR-targeted therapy fo... |
| Q05 | Epigenetics | ✅ | 0.80 | 0.957 | How is DNA methylation used as a biomarker for oral squamous... |
| Q06 | Single-cell | ✅ | 1.00 | 0.941 | What single-cell RNA sequencing studies have characterized H... |
| Q07 | Molecular subtype | ✅ | 0.40 | 0.945 | What molecular subtypes have been identified in HNSCC?... |
| Q08 | HPV | ✅ | 1.00 | 0.947 | How does HPV-positive HNSCC differ molecularly from HPV-nega... |
| Q09 | Mutations | ✅ | 0.80 | 0.952 | What are common somatic mutations in HNSCC and their clinica... |
| Q10 | Biomarker | ✅ | 1.00 | 0.943 | What prognostic biomarkers have been validated for HNSCC pat... |
| Q11 | Immunotherapy | ✅ | 1.00 | 0.954 | How effective is pembrolizumab and nivolumab for recurrent o... |
| Q12 | Mechanism | ✅ | 0.80 | 0.941 | What signaling pathways are dysregulated in HNSCC progressio... |
| Q13 | TME | ✅ | 1.00 | 0.949 | How does the immune microenvironment differ between HPV+ and... |
| Q14 | ML/AI | ✅ | 1.00 | 0.940 | What machine learning approaches have been applied to HNSCC ... |
| Q15 | Mutations | ✅ | 1.00 | 0.958 | What is the role of TP53 mutations in head and neck cancer p... |
| Q16 | Liquid biopsy | ✅ | 1.00 | 0.961 | How is liquid biopsy or ctDNA used in HNSCC monitoring?... |
| Q17 | Transcriptomics | ✅ | 1.00 | 0.957 | What are the prognostic gene expression signatures developed... |
| Q18 | Targeted therapy | ✅ | 1.00 | 0.946 | What treatment options exist for cetuximab-resistant HNSCC?... |
| Q19 | Immunotherapy | ✅ | 1.00 | 0.949 | How do immune checkpoint combinations improve HNSCC outcomes... |
| Q20 | TME | ✅ | 0.80 | 0.954 | What is the role of cancer-associated fibroblasts in HNSCC p... |

## Failure Cases

_No queries failed coverage@5._