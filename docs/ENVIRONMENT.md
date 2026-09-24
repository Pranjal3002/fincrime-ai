# Reproduction environment

- Verified development run: Windows, Python 3.11.9, CPU-only, local ignored virtual environment.
- Exact core versions: [requirements-lock.txt](../requirements-lock.txt). Optional PySpark and Playwright: [requirements-optional.txt](../requirements-optional.txt).
- PySpark 3.5.5 with Java 8 executed local transformations on 100,000 rows. Native Hadoop file output required unavailable Windows utilities; a bounded 10,000-row PyArrow writer exported computed Spark results. [Parity checks](../reports/spark_validation.json) passed.
- Actual Streamlit/FastAPI evidence was captured using local Playwright. No login or external account was used.
- Power BI Desktop opened the native project model. Report rendering is incomplete because of local WebView2 behavior; see [Power BI status](../dashboards/powerbi/README.md).
- Tableau specifications, AWS architecture mapping and deterministic investigation templates require no cloud accounts. No Tableau workbook, cloud deployment or LLM inference is claimed.
- Services bind to loopback. Stop them before regenerating warehouse data on Windows and restart to invalidate cached models/data.

## Validation

Run pytest, Ruff, Black, `python -m pip check` and the repository checker after installation. [Recorded local outputs](../reports/validation_results.json) are distinct from [hosted GitHub Actions results](https://github.com/Pranjal3002/fincrime-ai/actions/workflows/ci.yml). Tests require neither Spark nor Desktop BI tools.

## Correctness note

A past-only feature test identified a timestamp-unit assumption during development. The implementation explicitly normalizes timestamps to nanoseconds before window arithmetic. Published results and application evidence were regenerated from the corrected pipeline.
