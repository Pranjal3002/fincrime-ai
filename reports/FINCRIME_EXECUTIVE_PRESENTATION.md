# FinCrimeAI | Executive Presentation

## 1. Problem / objective

Prioritize synthetic payment reviews with reproducible evidence, without making compliance decisions.

---

## 2. Payment and data architecture

Payer → originating bank → network → receiving bank → beneficiary. Synthetic data → validation → features → DuckDB → screening/models → case store → API and BI.

---

## 3. Screening approach

Exact, alias and fuzzy comparison with country/entity context. Precision 0.924; recall 1.000. Human review required.

---

## 4. Statistical findings

Cramer's V 0.110; rank-biserial 0.511. Association is partly designed into rules; repeated payments limit inferential validity.

---

## 5. ML model comparison

| model | precision | recall | f1 | roc_auc | pr_auc_ap | threshold |
|---|---|---|---|---|---|---|
| LogisticRegression | 0.6274 | 0.7162 | 0.6689 | 0.8664 | 0.6864 | 0.5000 |
| RandomForest | 0.6138 | 0.7463 | 0.6736 | 0.8779 | 0.7274 | 0.4000 |
| XGBoost | 0.6964 | 0.7487 | 0.7216 | 0.8850 | 0.7471 | 0.4500 |

---

## 6. Dashboard / operational insights

100,000 payments; 21,998 alerts. Distinguish ground-truth error rates from reviewer dispositions.

---

## 7. Explainability / investigation

Versioned rule evidence, global importance and native XGBoost additive log-odds contributors. Evidence-backed deterministic summaries; no autonomous decisions.

---

## 8. Controls and governance

Synthetic data only, chronological validation, enforced foreign keys, human workflow and transactional audit trail. Local demonstration without authentication; bind to loopback.

---

## 9. Business recommendations

Tune against reviewer capacity; inspect misses; obtain independent labels and validate on future populations before drawing broader conclusions.