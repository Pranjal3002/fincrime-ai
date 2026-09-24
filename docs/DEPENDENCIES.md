# Dependencies and technical references

The project is MIT licensed. Dependencies retain their own licenses; no third-party dataset
or real sanctions list is redistributed. Installed package versions are recorded in
`requirements-lock.txt`; optional tools are separately listed in `requirements-optional.txt`.

| Tooling | Purpose | Upstream license family |
|---|---|---|
| Python | Local runtime | PSF |
| NumPy, Pandas, SciPy, scikit-learn | Data, statistics, modeling | BSD |
| XGBoost | Gradient boosting / native additive contributions | Apache 2.0 |
| DuckDB | Embedded analytical warehouse | MIT |
| PyArrow / PySpark | Parquet / optional local Spark | Apache 2.0 |
| RapidFuzz | Entity similarity | MIT |
| FastAPI, Uvicorn, HTTPX | Local API | MIT / BSD |
| Streamlit | Local analytics UI | Apache 2.0 |
| Plotly, Matplotlib | Interactive/static analytical plots | MIT / Matplotlib license |
| Joblib | Local model persistence | BSD |
| Pytest, Ruff, Black | Tests, lint, format | MIT |
| Playwright | Optional real browser screenshots | Apache 2.0 |

Power BI includes native semantic-model source and a real Desktop model-view capture; report rendering remains incomplete. Tableau is specifications only. Neither desktop tool is required for the core pipeline or automated tests. No paid features, accounts or service deployments are used.

Implementation references:

- [DuckDB CREATE TABLE and constraints](https://duckdb.org/docs/current/sql/statements/create_table)
- [scikit-learn metric definitions](https://scikit-learn.org/stable/api/sklearn.metrics.html)
- [scikit-learn temporal cross-validation](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html)
- [XGBoost prediction contributions](https://xgboost.readthedocs.io/en/stable/python/python_api.html#xgboost.Booster.predict)

PR-AUC labels in the repository explicitly mean average precision. XGBoost contribution
values are in raw margin/log-odds space, including a bias term for additivity validation.
