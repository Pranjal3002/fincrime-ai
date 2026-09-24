# GitHub publication preparation

Suggested repository name: `fincrime-ai`

Suggested description:

> End-to-end synthetic financial crime screening and payment-risk analytics platform with Python, PySpark, XGBoost, DuckDB, FastAPI, Streamlit and Power BI.

The repository is prepared for a public code/evidence review. No remote repository is created and nothing is pushed automatically. Apply the description when creating the repository; remote CI status should only be advertised after an actual run.

Before pushing, inspect the [README](../README.md), [evidence index](EVIDENCE.md), [Power BI status](../dashboards/powerbi/README.md), [Power BI model screenshot](images/powerbi_model.png), [synthetic samples](../data/samples/), [MIT license](../LICENSE) and [repository scan](../reports/repository_checks.json). Review the staged file list and local commit author identity as well.

Full generated datasets, fitted model binaries, case stores, `.pbi` caches and local session state remain ignored. The source, small recorded metrics, curated samples and real evidence images are publishable content. Retained experimental Power BI definitions are explicitly marked incomplete.
