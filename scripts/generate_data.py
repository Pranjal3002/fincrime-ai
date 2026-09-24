"""Generate deterministic raw sources without model training."""

import argparse

from fincrime_ai.ingestion import generate
from fincrime_ai.settings import DATA, prepare
from fincrime_ai.validation import validate

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--transactions", type=int, default=100000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    prepare()
    customers, counterparties, tx, watch = generate(args.transactions, args.seed)
    print(validate(customers, counterparties, tx))
    for name, frame in [
        ("customers", customers),
        ("counterparties", counterparties),
        ("transactions", tx),
    ]:
        frame.to_parquet(DATA / f"raw/{name}.parquet", index=False)
    watch.to_csv(DATA / "reference/watchlist.csv", index=False)
