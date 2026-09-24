# Semantic-model design

The authoritative definition is [model.bim](FinCrimeAI_Financial_Crime_Analytics.SemanticModel/model.bim).

- `fact_transactions`: one payment per transaction ID.
- `fact_screening_alerts`: one review alert per alert ID in the exported case snapshot.
- Customer, counterparty, date, origin geography, destination geography, payment channel and risk category are conformed dimensions. Each filters both facts through active single-direction one-to-many relationships.
- Geography is role-playing: origin and destination use separate dimensions.
- `bridge_alert_rules`: one row per alert/rule combination, filtered by the alert fact.
- Model comparison, confusion matrix, feature importance, statistical findings and threshold analysis are disconnected recorded outputs, not transaction-grain facts.

There are 15 tables and 15 relationships. Facts do not directly filter each other. This differs deliberately from the [physical DuckDB model](../../DATA_MODEL.md), whose 8 tables enforce 11 foreign keys.

Measures and key visibility are included in source. Report filter behavior remains unvalidated. See [current status and refresh instructions](README.md).
