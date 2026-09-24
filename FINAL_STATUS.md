# Delivery status

The local synthetic platform is implemented and evidenced. Power BI delivery is semantic modeling with partial report work; this repository does not claim a finished Power BI dashboard.

| Area | Verified delivery |
|---|---|
| Data | 100,000 synthetic GBP payments, 2,000 customers, 600 counterparties, 20 watchlist entities |
| ETL / warehouse | Validated batch pipeline, lineage, reconciliation, 8 DuckDB tables and 11 enforced foreign keys |
| Spark | Actual local transformation of 100,000 rows; bounded PyArrow export and source parity checks |
| Screening | Explainable fictional-watchlist matches and transaction-risk rules; 21,998 review alerts |
| Statistics | Descriptive analysis, chi-square, Mann–Whitney U, Wilson intervals, Spearman and effect sizes |
| ML | Chronological train/validation/test evaluation of LR, RF and XGBoost; selected XGBoost threshold 0.45 |
| Services | Local FastAPI and six working Streamlit views; human case workflow with atomic audit |
| Power BI | Native PBIP, 15 semantic-model tables, 15 active relationship definitions, 38 DAX definitions, real model-view screenshot |
| Quality | 29 passing local tests, Ruff, Black, dependency and repository checks; see recorded outputs |
| Visual evidence | 12 existing real application/plot/transcript assets plus a real Power BI model capture |

## Recorded results

XGBoost test precision **0.696420**, recall **0.748712**, F1 **0.721620**, ROC-AUC **0.885037**, PR-AUC/AP **0.747059**. Confusion matrix: TP 2,762; FP 1,204; FN 927; TN 15,107.

Transaction-weighted screening precision **0.924025101**, recall **1.0**, F1 **0.960512522**, FPR **0.007389324**, FNR **0**. Controlled synthetic benchmark only; not production efficacy.

## Partial and future work

- Power BI report rendering is limited by local WebView2 behavior. Experimental page definitions are preserved; full DAX execution, displayed-total reconciliation, refresh behavior and PBIX completion remain unverified.
- Tableau deliverables are specifications only; no native workbook or screenshot is claimed.
- AWS is a conceptual architecture mapping; no cloud deployment occurred.
- Investigation summaries are deterministic templates; no LLM inference occurred.
- Hosted [GitHub Actions results](https://github.com/Pranjal3002/fincrime-ai/actions/workflows/ci.yml) are available for pushed revisions. Local checks and hosted results are recorded separately.
- The local demo has no production authentication or compliance certification.

## Review and reproduction

[README](README.md) provides setup commands. [Evidence index](docs/EVIDENCE.md) maps claims to source and outputs. [Model card](MODEL_CARD.md) and [compliance boundaries](COMPLIANCE_BOUNDARIES.md) define limitations. Generated full data, models and local session state are excluded from publication.
