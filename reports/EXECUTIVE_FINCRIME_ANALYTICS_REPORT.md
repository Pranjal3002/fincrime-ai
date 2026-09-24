# Executive Financial Crime Analytics Report

## Executive Summary
FinCrimeAI processed 100,000 entirely synthetic payments and generated 21,998 review alerts (22.00%). These are investigation signals, not findings of crime. Human review remains final.

## Dataset Overview
Seed 42 is the default; this run's seed is recorded in run_manifest.json. There are 2,000 observed customers across 90 simulated days, all amounts in GBP. Customer/account and counterparty identifiers are fictional. XZ and QZ are fictional risk geographies. Controlled injected patterns and probabilistic labels support evaluation but cannot establish real-world effectiveness.

## Screening Performance
Transaction-weighted precision 0.9240; recall 1.0000; F1 0.9605; false-positive rate 0.0074; false-negative rate 0.0000. Repeated counterparties are not independent tests. See screening_metrics.json for unique-entity results. Near-name hard negatives deliberately test ambiguity.

## Transaction Risk Trends
Average rule score: 18.27/100. Median payment: GBP 794.25; 99th percentile: GBP 9,982.74. Screening, rule and model alerts are combined using OR, so operational workload is higher than any single component.

## Key Statistical Findings
Geography/alert chi-square = 1211.54, p = 1.89e-265, Cramer's V = 0.110; minimum expected cell = 5671.1.
Mann-Whitney p = 0, rank-biserial effect = 0.511. Alerted/nonalerted median amounts: GBP 2224.15 / 676.68.
Amount/rule-score Spearman rho = 0.329. Approximate Wilson 95% alert-rate interval: [21.74%, 22.26%]. A serialized p-value of zero indicates floating-point underflow, not impossibility.
Exploratory synthetic associations. Alerts directly use geography and amount, so association is partly designed into the system. Repeated customer payments violate independence; p-values and Wilson intervals are descriptive approximations, not population inference. Large samples can produce small p-values without large effects. Amount skew supports a rank test; it tests distributions, not necessarily medians.

## Model Performance
Chronological train/validation/test rows: 60,000/20,000/20,000. Three expanding-window CV folds use training data only. Selection and thresholds minimize validation cost 5*FN + FP, an illustrative preference rather than an approved policy. PR-AUC is reported as average precision (AP), not trapezoidal area.

| model | precision | recall | f1 | roc_auc | pr_auc_ap | threshold |
|---|---|---|---|---|---|---|
| LogisticRegression | 0.6274 | 0.7162 | 0.6689 | 0.8664 | 0.6864 | 0.5000 |
| RandomForest | 0.6138 | 0.7463 | 0.6736 | 0.8779 | 0.7274 | 0.4000 |
| XGBoost | 0.6964 | 0.7487 | 0.7216 | 0.8850 | 0.7471 | 0.4500 |

## False Positive / False Negative Tradeoff
The selected XGBoost has 1,204 false positives and 927 false negatives on held-out payments. Lowering thresholds increases review capacity demands; missed positives remain possible. Costs must be determined by human stakeholders. Inspect threshold_analysis.csv before adopting any operating point.

## Operational Findings
Cases begin OPEN; no investigator dispositions are fabricated. Actual reviewed false-positive rates are unavailable until reviewers close cases. Ground-truth FPR is distinct from the fraction of reviews that are false positives (1 - precision). Warehouse status is a pipeline snapshot; the API reads the live SQLite case store.

## Recommendations
1. Review ambiguous entity matches with country and alias evidence.
2. Assess daily queue capacity alongside missed-positive counts before threshold changes.
3. Require temporal and customer-separated external validation before any generalization claim.
4. Investigate label construction and dependency effects before interpreting statistical significance.

## Limitations
Synthetic patterns, probabilistic labels, 90-day horizon, simplified customer baselines and no real payment connections. Model features can identify injected patterns; measured accuracy is simulation-specific. Whole-dataset dashboard predictions include training rows; only the model page reports held-out metrics. A [native Power BI semantic model](../dashboards/powerbi/README.md) and real model-view evidence are included; report rendering remains incomplete. Tableau remains specifications only.

## Governance / Human Review
This is an educational portfolio simulation and is not intended for production compliance, AML, sanctions, or financial-crime decisioning.
Rules and model versions are recorded; human review transitions produce transactional audit records. Summaries cite evidence fields and cannot change case state.
