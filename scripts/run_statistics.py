"""Recompute statistical report data from existing scored payments."""

import pandas as pd

from fincrime_ai.pipeline import write_json
from fincrime_ai.settings import DATA, REPORTS
from fincrime_ai.statistics import analyze

if __name__ == "__main__":
    stats = analyze(pd.read_parquet(DATA / "processed/analytical_transactions.parquet"))
    write_json(REPORTS / "statistics.json", stats)
    print("Wrote reports/statistics.json")
