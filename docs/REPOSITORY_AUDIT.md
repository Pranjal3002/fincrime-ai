# Publication audit

The existing core implementation was preserved. Cleanup focused on presentation, truthful evidence, reproducibility and Git hygiene; it did not rerun model training or author Power BI report pages.

## Disposition

| Item | Action |
|---|---|
| Valid code, tests, analytical outputs and original 12 images | Preserved |
| Root package layout and imports | Preserved; no risky directory reorganization |
| Large generated datasets, warehouse, fitted models and case databases | Kept locally and excluded from Git |
| Virtual environments, caches, logs, scratch automation and original documentation-generator backup | Kept locally under ignored locations |
| Power BI project/report/semantic-model source | Preserved as Git-visible text; six report definitions labeled experimental |
| Power BI local caches and session state | Excluded through `.pbi` and temporary-workspace rules |
| Power BI screenshot | Added an actual Desktop model-view capture, cropped without overlays |
| Synthetic samples | Added 160 payments with 154 referenced customers, 138 counterparties and 20 fictional watchlist rows |
| Editorial documentation | Rebuilt README and evidence/status/resume docs; polished supporting material |
| Documentation generator | Changed to update only marked metric tables, protecting reviewed prose |
| MIT license | Existing license retained; dependency licenses remain separate |

**No project files were deleted. No core directories were moved.** Uncertain and potentially useful local outputs were preserved rather than removed for appearance.

## Validation and boundaries

- [Local quality results](../reports/validation_results.json): pytest, Ruff, Black and dependency validation.
- [Repository checks](../reports/repository_checks.json): Git-visible size/junk/secret-pattern scan, JSON parsing, local Markdown file links and screenshot hashes.
- [Documentation checks](../reports/documentation_validation.json): nine Mermaid diagrams parsed and rendered to SVG; README visually reviewed locally.
- [Power BI source checks](../reports/powerbi_source_validation.json): project references and relationship endpoints resolve; counts checked against actual source. This does not validate report rendering or DAX execution.
- [Read-only publication audit](../reports/publication_audit.json): source dataset counts, actual DuckDB totals/constraints and local Markdown anchors verified.
- All 13 evidence images were visually reviewed. The original application/plot/transcript images retain their original hashes; the native Power BI capture has a separate manifest.

The secret scan is heuristic and is not a comprehensive security audit. Local file-link checks do not certify external websites. Hosted CI has not run. Power BI report rendering and completed PBIX validation remain incomplete; Tableau is specifications only.

## Git preparation

The repository had no commits and no remote at audit time. The requested initial commit contains source, documentation, small samples, metrics and genuine evidence. No remote creation, push, Power BI Service publishing or account login is part of this cleanup. See [publication preparation](GITHUB_PUBLICATION.md) for the suggested repository name and description.
