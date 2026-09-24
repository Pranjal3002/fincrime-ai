# Power BI evidence

| Skill | Repository evidence | What is supported |
|---|---|---|
| Native project structure | [PBIP](FinCrimeAI_Financial_Crime_Analytics.pbip), [report reference](FinCrimeAI_Financial_Crime_Analytics.Report/definition.pbir), [semantic model reference](FinCrimeAI_Financial_Crime_Analytics.SemanticModel/definition.pbism) | Real local project source |
| Data / semantic modeling | [model.bim](FinCrimeAI_Financial_Crime_Analytics.SemanticModel/model.bim) | 15 tables with types, CSV partitions and a local folder parameter |
| Fact / dimension design | [inventory](model_inventory.json), [design](DATA_MODEL.md) | Two facts, seven conformed dimensions, rule bridge and five evaluation tables |
| Cardinality and filter direction | model.bim relationships; [real model view](../../docs/images/powerbi_model.png) | 15 active many-to-one definitions with one-direction filtering |
| DAX | [measure definitions](DAX_MEASURES.md) and model.bim | 38 source definitions; full execution validation pending |
| Data export / reconciliation | [exporter](../../scripts/export_powerbi_data.py), [recorded validation](../../reports/powerbi_export_validation.json) | Local CSVs reconcile to the pipeline snapshot |
| Screenshot provenance | [capture manifest](../../reports/powerbi_evidence_manifest.json) | Cropped actual Desktop model view; no account details or synthetic overlays |
| Source validation | [recorded checks](../../reports/powerbi_source_validation.json) | Project paths and relationship endpoints resolve; 15 tables, 15 relationships, 38 measures |

The screenshot demonstrates native model structure. It does **not** prove report-page rendering, all 15 relationships simultaneously visible, DAX correctness, report totals, refresh behavior or PBIX completion. Page definitions are experimental; no report screenshot or Power BI Service deployment is claimed.
