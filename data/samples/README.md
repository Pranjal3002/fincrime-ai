# Small synthetic samples

Fictional examples from the recorded seed-42 dataset. No real PII or live watchlist data is included. Customer and counterparty references are complete for the sampled payments.

| File | Rows |
|---|---:|
| [transactions.csv](transactions.csv) | 160 |
| [customers.csv](customers.csv) | 154 |
| [counterparties.csv](counterparties.csv) | 138 |
| [watchlist.csv](watchlist.csv) | 20 |

Sampling takes up to 20 payments per injected pattern with random state 42. Patterns are intentionally overrepresented: these files do not reproduce population rates or published performance metrics. Evaluation truth fields are included for inspection, never as model features.

Regenerate the full dataset using the [root instructions](../../README.md#how-to-run), then run `python scripts/export_samples.py` from the repository root.
