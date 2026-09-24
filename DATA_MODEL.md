# Dimensional data model

The authoritative DDL is [sql/schema/star.sql](sql/schema/star.sql).
DuckDB enforces 8 primary keys and 11 foreign-key relationships.

| Table | Grain | Primary key | Key derivation |
|---|---|---|---|
| fact_transactions | One synthetic payment | transaction_id | Generator business identifier |
| fact_screening_alerts | One combined review alert per flagged payment in this version | alert_id | ALERT + transaction ID |
| dim_customer | One synthetic customer/account | customer_key | customer_id + 1 |
| dim_counterparty | One synthetic beneficiary | counterparty_key | counterparty_id + 1 |
| dim_date | One UTC calendar date | date_key | YYYYMMDD integer |
| dim_geography | One country code | geography_key | Sorted-country surrogate |
| dim_payment_channel | One channel | channel_key | Sorted-channel surrogate |
| dim_risk_category | One rule-score band | risk_key | 1 LOW, 2 MEDIUM, 3 HIGH |

Customer/counterparty natural IDs are also unique. Dimensions hold descriptive attributes;
facts hold amounts, timestamps, scores and observation outcomes. Origin and destination
are role-playing relationships to dim_geography. Geography/channel keys are deterministic
for a fixed dimension domain, not durable SCD keys across new domains. Dimensions are
Type 1 snapshots; there is no slowly changing dimension implementation.

## Source-to-target mapping

| Source | Transform | Target |
|---|---|---|
| raw/customers.parquet | Add surrogate; retain account, baseline and KYC fields | dim_customer |
| raw/counterparties.parquet | Add surrogate; omit synthetic truth flag from descriptive dimension | dim_counterparty |
| raw/transactions.parquet.timestamp | UTC date, year/month/day | dim_date |
| origin_country, destination_country | Distinct values and configurable fictional risk flag | dim_geography |
| payment_channel | Distinct domain | dim_payment_channel |
| derived risk_score | 0–39 LOW, 40–69 MEDIUM, 70–100 HIGH | dim_risk_category |
| analytical_transactions | Resolve dimension keys, decimal amount, scores and evaluation truth | fact_transactions |
| audited case store | Current case snapshot linked to payment and dimensions | fact_screening_alerts |

Truth fields in the transaction fact exist for evaluation, never as predictive inputs.
Rule risk is distinct from model probability. Every amount is GBP, stored as DECIMAL(18,2)
in the warehouse. The raw/processed Python amounts are rounded floats; reconciliation
uses a one-penny tolerance over total value.

## Relationships and BI precautions

Use one-to-many, single-direction dimension→fact filters. Use two role-playing geography
tables in BI (Origin Geography, Destination Geography). Avoid active ambiguous paths from
shared dimensions through both facts. For this one-alert-per-payment implementation,
relate alert fact to transactions only when needed; do not also activate redundant paths.
Never sum transaction amounts after an unrestricted future many-alert join.

Star modeling gives explicit grains, reusable dimensions and simple aggregate SQL.
All fact keys are NOT NULL; unknown reference keys fail the load. Validation rejects
orphan source keys before transformations; warehouse constraints provide a second check.
Rebuilds stage a separate database and replace only after reconciliation. Full import CSVs
are generated under data/curated and excluded from Git; regenerate them locally.

## Power BI semantic layer

The [Power BI semantic model](dashboards/powerbi/DATA_MODEL.md) expands the analytical export to 15 tables and 15 active one-to-many relationship definitions. It uses conformed dimensions on both facts and separate origin/destination geography roles. These BI relationships are distinct from the 11 enforced DuckDB foreign keys described above.
