# Evidence index

Every claim below refers to a locally executed synthetic project. See [delivery status](../FINAL_STATUS.md) for partial work and [model card](../MODEL_CARD.md) for evaluation limitations.

| Skill | Implementation | Execution / evidence |
|---|---|---|
| Python, Pandas, NumPy | [Core package](../src/fincrime_ai/) | [Pipeline transcript](../reports/pipeline_output.txt), [tests](../tests/) |
| ETL and validation | [Pipeline](../src/fincrime_ai/pipeline.py), [validation](../src/fincrime_ai/validation.py) | [Data quality](../reports/data_quality.json), [run manifest](../reports/run_manifest.json) |
| SQL / warehousing | [SQL](../sql/), [warehouse](../src/fincrime_ai/warehouse.py), [design](../DATA_MODEL.md) | [Actual schema evidence](images/12_warehouse_schema.png): 8 tables, 11 enforced foreign keys |
| PySpark | [Local transformation](../src/fincrime_ai/spark_pipeline.py) | [100K-row execution and parity](../reports/spark_validation.json); bounded PyArrow export on Windows |
| Financial crime screening | [Entity screening](../src/fincrime_ai/screening.py), [rules](../src/fincrime_ai/rules.py) | [Screening metrics](../reports/screening_metrics.json), [Streamlit view](images/02_screening_dashboard.png) |
| Statistics | [Analysis module](../src/fincrime_ai/statistics.py), [write-up](../STATISTICAL_ANALYSIS.md) | [Recorded statistics](../reports/statistics.json), [real view](images/07_statistical_analysis.png) |
| ML and temporal validation | [Models](../src/fincrime_ai/models.py), [features](../src/fincrime_ai/features.py) | [Comparison](../reports/model_comparison.csv), [split/threshold/confusion metrics](../reports/model_metrics.json) |
| Explainability | [Model contributions](../src/fincrime_ai/models.py) | [Importance](../reports/feature_importance.csv), [investigation view](images/08_alert_investigation.png) |
| Investigation workflow | [Case store and audit](../src/fincrime_ai/investigation.py) | [Tests](../tests/), [actual investigation UI](images/08_alert_investigation.png); local self-asserted identities |
| FastAPI | [API implementation](../api/main.py) | [Real Swagger UI](images/09_fastapi_docs.png), [local smoke validation](../reports/validation_results.json) |
| Streamlit | [Six-view app](../dashboards/streamlit/app.py) | Actual application screenshots 01–04 and 07–08 below |
| Power BI | [PBIP and semantic source](../dashboards/powerbi/), [detailed mapping](../dashboards/powerbi/POWERBI_EVIDENCE.md) | [Real Desktop model view](images/powerbi_model.png); report rendering incomplete |
| Testing / quality | [Tests](../tests/), [GitHub Actions](../.github/workflows/ci.yml) | [Local output](../reports/validation_results.json), [test transcript image](images/10_tests_passed.png); remote CI not run |
| Executive communication | [Analytics report](../reports/EXECUTIVE_FINCRIME_ANALYTICS_REPORT.md) | [Presentation narrative](../reports/FINCRIME_EXECUTIVE_PRESENTATION.md); Markdown, not PDF/PPTX |
| Repository hygiene | [Checker](../scripts/check_repository.py), [ignore rules](../.gitignore) | [Scan results](../reports/repository_checks.json); heuristic, not a security certification |

## Visual provenance

| Asset | Actual source |
|---|---|
| [01 Executive](images/01_executive_dashboard.png) | Live Streamlit executive view |
| [02 Screening](images/02_screening_dashboard.png) | Live Streamlit screening view |
| [03 Geographic risk](images/03_geographic_risk.png) | Live Streamlit payment-risk view |
| [04 Model performance](images/04_model_performance.png) | Live Streamlit model view |
| [05 Confusion matrix](images/05_confusion_matrix.png) | Matplotlib plot from evaluated model output |
| [06 Feature importance](images/06_feature_importance.png) | Matplotlib plot from recorded importance |
| [07 Statistics](images/07_statistical_analysis.png) | Live Streamlit statistical view |
| [08 Investigation](images/08_alert_investigation.png) | Live Streamlit investigation view |
| [09 API](images/09_fastapi_docs.png) | Live FastAPI Swagger UI |
| [10 Tests](images/10_tests_passed.png) | Browser-rendered transcript of actual test output |
| [11 Pipeline](images/11_pipeline_run.png) | Browser-rendered transcript of actual pipeline output |
| [12 Warehouse](images/12_warehouse_schema.png) | Browser-rendered actual DuckDB table/constraint introspection |
| [Power BI model](images/powerbi_model.png) | Cropped native Desktop model view; no report-page claim |

Source descriptions and SHA-256 hashes: [original 12 assets](../reports/screenshot_manifest.json) and [Power BI capture](../reports/powerbi_evidence_manifest.json). Cropping removes application chrome; it does not add model elements. No screenshot contains personal account information.

## Claims deliberately excluded

No real-world detection efficacy, completed Power BI dashboard/PBIX, Tableau workbook, cloud deployment, production authentication or compliance certification. AWS mapping and Tableau specifications are concepts. Investigation summary assistance is deterministic; no LLM ran. Isolation Forest produces an auxiliary score, not an independently validated anomaly detector.

## Reproducibility

Use Python 3.11, the dependency lock and seed 42 as documented in the [README](../README.md#how-to-run). Full generated data and model binaries are ignored; small [synthetic samples](../data/samples/) support inspection without running the pipeline. BI exports and case statuses are snapshots, so later human actions can change refreshed status counts.
