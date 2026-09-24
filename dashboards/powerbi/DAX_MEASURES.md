# DAX measures

These definitions are generated with the semantic model. Desktop execution and validation are recorded separately in POWERBI_EVIDENCE.md.

### Transactions Screened

```dax
Transactions Screened =
COUNTROWS(fact_transactions)
```

Format: `#,0`

### Review Alerts

```dax
Review Alerts =
COUNTROWS(fact_screening_alerts)
```

Format: `#,0`

### Alert Rate

```dax
Alert Rate =
DIVIDE([Review Alerts], [Transactions Screened])
```

Format: `0.00%`

### High-Risk Alerts

```dax
High-Risk Alerts =
CALCULATE([Review Alerts], fact_screening_alerts[risk_score] >= 70)
```

Format: `#,0`

### Average Risk Score

```dax
Average Risk Score =
AVERAGE(fact_transactions[risk_score])
```

Format: `0.00`

### Total Amount GBP

```dax
Total Amount GBP =
SUM(fact_transactions[amount])
```

Format: `£#,0`

### Average Amount GBP

```dax
Average Amount GBP =
AVERAGE(fact_transactions[amount])
```

Format: `£#,0.00`

### Average Velocity

```dax
Average Velocity =
AVERAGE(fact_transactions[velocity_1h])
```

Format: `0.00`

### Velocity Spike Payments

```dax
Velocity Spike Payments =
CALCULATE([Transactions Screened], fact_transactions[velocity_1h] >= 4)
```

Format: `#,0`

### Unusual-Time Payments

```dax
Unusual-Time Payments =
CALCULATE([Transactions Screened], fact_transactions[night] = 1)
```

Format: `#,0`

### Screening Alerts

```dax
Screening Alerts =
CALCULATE([Transactions Screened], fact_transactions[screening_review] = 1)
```

Format: `#,0`

### Screening TP

```dax
Screening TP =
CALCULATE([Transactions Screened], fact_transactions[screening_review] = 1, fact_transactions[screening_truth] = 1)
```

Format: `#,0`

### Screening FP

```dax
Screening FP =
CALCULATE([Transactions Screened], fact_transactions[screening_review] = 1, fact_transactions[screening_truth] = 0)
```

Format: `#,0`

### Screening FN

```dax
Screening FN =
CALCULATE([Transactions Screened], fact_transactions[screening_review] = 0, fact_transactions[screening_truth] = 1)
```

Format: `#,0`

### Screening TN

```dax
Screening TN =
CALCULATE([Transactions Screened], fact_transactions[screening_review] = 0, fact_transactions[screening_truth] = 0)
```

Format: `#,0`

### Screening Precision

```dax
Screening Precision =
DIVIDE([Screening TP], [Screening TP] + [Screening FP])
```

Format: `0.00%`

### Screening Recall

```dax
Screening Recall =
DIVIDE([Screening TP], [Screening TP] + [Screening FN])
```

Format: `0.00%`

### Screening F1

```dax
Screening F1 =
DIVIDE(2 * [Screening Precision] * [Screening Recall], [Screening Precision] + [Screening Recall])
```

Format: `0.00%`

### Screening FPR

```dax
Screening FPR =
DIVIDE([Screening FP], [Screening FP] + [Screening TN])
```

Format: `0.00%`

### Screening FNR

```dax
Screening FNR =
DIVIDE([Screening FN], [Screening TP] + [Screening FN])
```

Format: `0.00%`

### Open Alerts

```dax
Open Alerts =
COALESCE(CALCULATE([Review Alerts], fact_screening_alerts[status] = "OPEN"), 0)
```

Format: `#,0`

### In Review Alerts

```dax
In Review Alerts =
COALESCE(CALCULATE([Review Alerts], fact_screening_alerts[status] = "IN_REVIEW"), 0)
```

Format: `#,0`

### Escalated Alerts

```dax
Escalated Alerts =
COALESCE(CALCULATE([Review Alerts], fact_screening_alerts[status] = "ESCALATED"), 0)
```

Format: `#,0`

### Closed Alerts

```dax
Closed Alerts =
COALESCE(CALCULATE([Review Alerts], fact_screening_alerts[status] = "CLOSED"), 0)
```

Format: `#,0`

### Reviewed False Positives

```dax
Reviewed False Positives =
COALESCE(CALCULATE([Review Alerts], fact_screening_alerts[disposition] = "FALSE_POSITIVE"), 0)
```

Format: `#,0`

### Reviewed FP Share

```dax
Reviewed FP Share =
DIVIDE([Reviewed False Positives], [Closed Alerts])
```

Format: `0.00%`

### Average Case Age at Cutoff

```dax
Average Case Age at Cutoff =
AVERAGE(fact_screening_alerts[age_at_data_cutoff_days])
```

Format: `0.0`

### Rule Alerts

```dax
Rule Alerts =
COUNTROWS(bridge_alert_rules)
```

Format: `#,0`

### XGBoost Threshold

```dax
XGBoost Threshold =
CALCULATE(MAX(model_comparison[threshold]), model_comparison[model] = "XGBoost")
```

Format: `0.00`

### Test TP

```dax
Test TP =
CALCULATE(MAX(model_comparison[tp]), model_comparison[model] = "XGBoost")
```

Format: `#,0`

### Test FP

```dax
Test FP =
CALCULATE(MAX(model_comparison[fp]), model_comparison[model] = "XGBoost")
```

Format: `#,0`

### Test FN

```dax
Test FN =
CALCULATE(MAX(model_comparison[fn]), model_comparison[model] = "XGBoost")
```

Format: `#,0`

### Test TN

```dax
Test TN =
CALCULATE(MAX(model_comparison[tn]), model_comparison[model] = "XGBoost")
```

Format: `#,0`

### Cramers V

```dax
Cramers V =
MAX(statistical_findings[cramers_v])
```

Format: `0.000`

### Rank Biserial

```dax
Rank Biserial =
MAX(statistical_findings[rank_biserial])
```

Format: `0.000`

### Spearman Rho

```dax
Spearman Rho =
MAX(statistical_findings[spearman_rho])
```

Format: `0.000`

### Wilson Lower

```dax
Wilson Lower =
MAX(statistical_findings[ci_lower])
```

Format: `0.00%`

### Wilson Upper

```dax
Wilson Upper =
MAX(statistical_findings[ci_upper])
```

Format: `0.00%`

Both facts connect independently to shared dimensions with single-direction filtering. Review Alerts therefore respects date, channel, risk and both geography slicers. Screening rates use the filtered payment fact. Model/statistics benchmarks remain full-run. Age is days at the synthetic data cutoff, not current operational SLA. Blank Reviewed FP Share means no closed cases.
