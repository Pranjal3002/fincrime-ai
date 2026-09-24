"""Export a small, deterministic synthetic sample with referentially complete entities."""

import json

import pandas as pd

from fincrime_ai.settings import ROOT


def main():
    raw = ROOT / "data" / "raw"
    target = ROOT / "data" / "samples"
    target.mkdir(parents=True, exist_ok=True)
    transactions = pd.read_parquet(raw / "transactions.parquet")
    # Deliberately oversample patterns for inspection; not an evaluation dataset.
    samples = [
        group.sample(n=min(20, len(group)), random_state=42)
        for _, group in transactions.groupby("injected_pattern", dropna=False)
    ]
    payments = pd.concat(samples).sort_values("transaction_id")
    frames = {"transactions": payments}
    for name, key in (
        ("customers", "customer_id"),
        ("counterparties", "counterparty_id"),
    ):
        frame = pd.read_parquet(raw / f"{name}.parquet")
        frames[name] = frame[frame[key].isin(payments[key])].sort_values(key)
        assert set(payments[key]) <= set(frames[name][key])
    frames["watchlist"] = pd.read_csv(ROOT / "data/reference/watchlist.csv")
    for name, frame in frames.items():
        frame.to_csv(target / f"{name}.csv", index=False, lineterminator="\n")
    counts = {name: len(frame) for name, frame in frames.items()}
    rows = "\n".join(f"| [{n}.csv]({n}.csv) | {v} |" for n, v in counts.items())
    (target / "README.md").write_text(
        "# Small synthetic samples\n\n"
        "Fictional examples from the recorded seed-42 dataset. No real PII or live "
        "watchlist data is included. Customer and counterparty references are complete "
        "for the sampled payments.\n\n"
        "| File | Rows |\n|---|---:|\n" + rows + "\n\n"
        "Sampling takes up to 20 payments per injected pattern with random state 42. "
        "Patterns are intentionally overrepresented: these files do not reproduce "
        "population rates or published performance metrics. Evaluation truth fields "
        "are included for inspection, never as model features.\n\n"
        "Regenerate the full dataset using the [root instructions](../../README.md#how-to-run), "
        "then run `python scripts/export_samples.py` from the repository root.\n",
        encoding="utf-8",
    )
    print(json.dumps(counts, indent=2))


if __name__ == "__main__":
    main()
