"""Independently repeat entity screening from existing synthetic sources."""

import pandas as pd

from fincrime_ai.screening import EntityMatcher
from fincrime_ai.settings import DATA, controls

if __name__ == "__main__":
    watch = pd.read_csv(DATA / "reference/watchlist.csv").fillna("")
    counterparties = pd.read_parquet(DATA / "raw/counterparties.parquet")
    matcher = EntityMatcher(watch, controls()["screening_threshold"])
    results = pd.DataFrame(
        [
            {
                "counterparty_id": int(row.counterparty_id),
                **matcher.screen(row.counterparty_name, row.country),
            }
            for row in counterparties.itertuples()
        ]
    )
    results.to_csv(DATA / "curated/entity_screening.csv", index=False)
    print(f"Screened {len(results)} unique counterparties")
