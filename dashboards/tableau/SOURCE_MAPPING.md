# Source mapping and grain

| Source | Grain | Use |
|---|---|---|
| fact_transactions.csv | Payment | Full volume, amount, scores, alerts and benchmark truth |
| dim_customer.csv | Customer | Customer type, synthetic KYC and baseline |
| dim_counterparty.csv | Counterparty | Beneficiary name, country and type |
| dim_date.csv | UTC day | Calendar hierarchy |
| dim_geography.csv | Country | Two logical roles: origin and destination |
| dim_payment_channel.csv | Channel | Payment channel filters |
| dim_risk_category.csv | Rule-score band | Risk grouping |
| fact_screening_alerts.csv | Combined alert | Status/disposition snapshot and review age |
| transaction_explorer_sample.csv | Sampled payment | Easy flat 5000-row preview only |
| reports/model_comparison.csv | Model on held-out test | Evaluation, separate data source |

Relationships use matching surrogate keys. Aggregate independently at fact grain before
combining operational sheets. The sample's counts are sample counts, not full-run counts.
No Hyper extract or TWB/TWBX is represented as complete.
