# FinCrimeAI — Financial Crime Screening & Payment Risk Analytics Platform

**Tech:** Python | SQL | PySpark | DuckDB | XGBoost | scikit-learn | FastAPI | Streamlit | Power BI

- Built an end-to-end financial-crime screening and payment-risk analytics platform processing 100K synthetic transactions through ETL, validation, screening and feature engineering into an 8-table dimensional warehouse with 11 enforced foreign-key relationships.
- Implemented explainable entity/watchlist screening and transaction-risk analytics, achieving 92.4% precision, 100% recall and 96.1% F1 on controlled synthetic screening ground truth.
- Evaluated Logistic Regression, Random Forest and XGBoost using chronological held-out evaluation; selected XGBoost with 0.747 PR-AUC, 0.722 F1 and 0.885 ROC-AUC on synthetic test labels.
- Delivered FastAPI services, six Streamlit analytics views, a native Power BI semantic model, local PySpark processing and 29 passing automated tests.

## Interview boundaries

All data and performance claims are synthetic. Power BI evidence supports semantic modeling, 15 active relationship definitions and 38 DAX definitions; rendered dashboard pages remain incomplete. Spark is a dedicated local transformation, not a distributed production deployment. Case summaries are deterministic, not LLM inference. No Tableau workbook, cloud deployment, bank affiliation or compliance certification is claimed.

Sources: [evidence index](EVIDENCE.md), [model results](../reports/model_metrics.json), [screening results](../reports/screening_metrics.json), [Power BI evidence](../dashboards/powerbi/POWERBI_EVIDENCE.md).
