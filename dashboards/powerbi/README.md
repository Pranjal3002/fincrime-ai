# Power BI semantic model

**Delivered:** native PBIP source, imported-table definitions, conformed dimensions, active one-to-many relationships and 38 DAX measure definitions. The real Desktop model-view screenshot is [included](../../docs/images/powerbi_model.png). No Microsoft sign-in or Power BI Service publishing is needed for this local project.

**Incomplete:** report-page rendering has a local WebView2 issue. Six experimental page definitions are preserved, but no rendered dashboard, report-total reconciliation or finished PBIX is claimed. Model-source validation is not proof that every DAX measure has executed correctly.

## Source structure

```text
FinCrimeAI_Financial_Crime_Analytics.pbip
FinCrimeAI_Financial_Crime_Analytics.Report/
  definition.pbir
  definition/
FinCrimeAI_Financial_Crime_Analytics.SemanticModel/
  definition.pbism
  model.bim
```

## Tables and relationships

| Role | Tables |
|---|---|
| Facts | fact_transactions, fact_screening_alerts |
| Conformed dimensions | dim_customer, dim_counterparty, dim_date, dim_origin_geography, dim_destination_geography, dim_payment_channel, dim_risk_category |
| Bridge | bridge_alert_rules |
| Disconnected analytical outputs | model_comparison, confusion_matrix, feature_importance, statistical_findings, threshold_analysis |

All 15 relationship definitions are active, one-to-many and single-direction. Seven dimensions each filter both facts (14 relationships); alerts filter the rule bridge (one relationship). There is no direct transaction-fact-to-alert-fact relationship, avoiding a second filter path. Disconnected analytical outputs represent recorded global evaluation results and should not be interpreted as responding to payment slicers.

The [model inventory](model_inventory.json) and [model source](FinCrimeAI_Financial_Crime_Analytics.SemanticModel/model.bim) are inspectable without Desktop. This is a 15-table BI semantic model; the underlying DuckDB warehouse separately has 8 tables and 11 enforced foreign keys.

## Measures

[DAX definitions](DAX_MEASURES.md) cover payment volume/value, review rates, risk, case statuses, screening performance, selected-model evaluation and statistical results. All 38 definitions are present in model.bim. Report execution and slicer behavior remain to be validated.

## Open and refresh locally

1. Generate the source data with the root README instructions (Python 3.11, seed 42).
2. Export the BI tables from the repository root:

   ```powershell
   python scripts/export_powerbi_data.py --desktop-data-dir C:\FinCrimeAIData
   ```

3. Open `FinCrimeAI_Financial_Crime_Analytics.pbip` in Power BI Desktop. The source `DataFolder` parameter defaults to the non-personal local folder shown above. If using another location, choose **Transform data → Edit parameters → DataFolder**, then apply it.
4. Choose **Home → Refresh** to import the local CSVs. No account or cloud service is involved.
5. Use **Model view** to inspect dimensions, keys and relationships. Refer to [export validation](../../reports/powerbi_export_validation.json) for expected source totals.

Expected source totals for the recorded run: **100,000 payments; 21,998 alerts; £157,994,548.85 payment value; 6,470 high-risk alerts; average risk score 18.27335**. These reconcile in Python exports; displayed Power BI totals and end-to-end refresh behavior are not yet signed off.

Local `.pbi` caches, imported data and account/session state are excluded from Git. A fresh clone must regenerate data. Do not run the project-builder script over hand-edited Desktop source without a backup; it is a source generator, not a required refresh step.

## Remaining work

Resolve local report rendering, verify all displayed measures and filter interactions, check refresh after controlled source changes, and save/reopen a PBIX if needed. No cloud publishing is planned without explicit authorization. [Evidence mapping](POWERBI_EVIDENCE.md).
