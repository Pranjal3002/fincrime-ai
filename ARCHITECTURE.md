# Architecture

FinCrimeAI is an educational local batch system. The pipeline processes synthetic GBP
payments; no bank, payment network, cloud account or public sanctions service is connected.

```mermaid
flowchart LR
  A[Synthetic payments] --> B[Raw Parquet]
  B --> C[Validate / ETL]
  C --> D[Past-only features]
  D --> E[DuckDB star schema]
  D --> F[Synthetic entity screening]
  F --> G[Rules and risk models]
  G --> H[Review alerts]
  H --> I[SQLite cases and audit]
  I --> J[FastAPI]
  E --> K[Streamlit / Power BI semantic model]
  E --> M[Statistical analysis]
  C --> N[Local PySpark transformation and parity checks]
  J --> L[Human investigation]
```

The logical diagram separates capabilities. Actual batch order is generation → validation
→ counterparty screening → feature generation → rules → model fitting/scoring → cases
→ warehouse → exports/reports. This makes scored facts available in one atomic rebuild.

## Conceptual payment flow

```mermaid
flowchart LR
  A[Payer / customer] --> B[Originating institution]
  B --> C[Payment network / intermediary]
  C --> D[Receiving institution]
  D --> E[Beneficiary / counterparty]
```

`account_id`, `customer_id`, originating_bank, network, beneficiary_bank and counterparty_id
represent each stage. Currency is GBP throughout; there is no FX netting or settlement engine.
Status is simulated payment metadata, independent of investigation disposition.

## Dimensional warehouse

```mermaid
erDiagram
  dim_customer ||--o{ fact_transactions : customer_key
  dim_counterparty ||--o{ fact_transactions : counterparty_key
  dim_date ||--o{ fact_transactions : date_key
  dim_geography ||--o{ fact_transactions : origin_geography_key
  dim_geography ||--o{ fact_transactions : destination_geography_key
  dim_payment_channel ||--o{ fact_transactions : channel_key
  dim_risk_category ||--o{ fact_transactions : risk_key
  fact_transactions ||--o{ fact_screening_alerts : transaction_id
  dim_customer ||--o{ fact_screening_alerts : customer_key
  dim_counterparty ||--o{ fact_screening_alerts : counterparty_key
  dim_date ||--o{ fact_screening_alerts : date_key
```

## Investigation workflow

```mermaid
stateDiagram-v2
  [*] --> OPEN: pipeline creates review alert
  OPEN --> IN_REVIEW: human accepts case
  IN_REVIEW --> ESCALATED: human requests further review
  ESCALATED --> IN_REVIEW: human resumes investigation
  IN_REVIEW --> CLOSED: human disposition and reason
  ESCALATED --> CLOSED: human disposition and reason
  CLOSED --> [*]
```

Each transition records actor, action, UTC timestamp, complete before/after state in the
same SQLite transaction. Closed cases cannot be silently reopened. Actor names are
self-asserted in this local demo; they are not authenticated identities.

## Storage, lineage and incremental concept

Raw Parquet is deterministic for a seed and environment. Processed data includes observable
features and separated truth/evaluation fields. The run manifest records input hash,
control hash, versions, seed, record count and maximum event-time watermark. Warehouse
rebuilds validate row/amount reconciliation before atomic replacement. Primary keys reject
duplicates. Case inserts are idempotent and preserve previous human review states for an
identical run key. This is an incremental-style case pattern, not a streaming ETL claim.

## Spark and Pandas

The default, fully exercised path uses Pandas. `spark_pipeline.py` is a dedicated optional
local Spark transformation (read Parquet, validate positive amounts, derive date/log amount,
deduplicate transaction IDs). It executed on 100000 rows in local[2] mode. Native Windows
Hadoop export failed without winutils; a bounded 10000-row PyArrow writer exported the
Spark results. ID, amount, log-amount, date and count parity checks passed. See
reports/spark_validation.json. It does not substitute Spark for model training or the entire pipeline.

## Zero-charge AWS mapping

| Local layer | Conceptual AWS equivalent |
|---|---|
| data/raw | S3 raw prefix |
| data/processed | S3 processed prefix |
| data/curated | S3 curated prefix / Athena tables |
| local transform | Glue Spark job |
| DuckDB analytics | Athena or Redshift analytical model |
| API and local audit | Private service and access-controlled database |

`storage.s3_uri` only maps logical locations. It performs no uploads, credential discovery
or network requests. Cloud deployment is documented, not implemented or validated.

## Operational boundaries

Bind both servers to loopback. Restart servers after pipeline regeneration to invalidate
model/data caches. Stop readers before rebuilding the warehouse on Windows. Warehouse
case statuses are snapshots from the last run; Streamlit investigation and API use live
SQLite state. Do not edit controls under a running server. No PostgreSQL integration,
production authentication, scheduling, distributed locks or real compliance controls are claimed.
