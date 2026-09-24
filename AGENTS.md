# Project instructions

Use Python 3.11 and local free tooling. All entities and payments must be synthetic.
Never label a person or business as sanctioned or criminal. CLEAR/REVIEW are screening
recommendations; human review is final. Keep truth labels out of model features.
Maintain chronological splits and past-only rolling features. Run pytest, ruff check .,
and black --check . after changes. Regenerate reports when analytical logic changes.
Do not claim native BI completion or Spark execution without recorded validation.
Do not commit data volumes, SQLite/DuckDB files, model binaries, environments or secrets.

The Streamlit UI and API are local demonstrations, not authenticated production services.
All review updates must pass through CaseStore and write an audit event atomically.
