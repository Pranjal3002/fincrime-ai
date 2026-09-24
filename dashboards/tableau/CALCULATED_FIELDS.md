# Tableau calculations (authored, not executed in Tableau)

For the denormalized explorer CSV:

```text
Alert Indicator = INT([alert_flag])
Alert Rate = SUM([Alert Indicator]) / COUNT([transaction_id])
Risk Band = IF [risk_score] >= 70 THEN "HIGH" ELSEIF [risk_score] >= 40 THEN "MEDIUM" ELSE "LOW" END
Benchmark False Positive = INT([alert_flag] AND [investigation_label] = 0)
Benchmark Negative = INT([investigation_label] = 0)
Benchmark FPR = SUM([Benchmark False Positive]) / SUM([Benchmark Negative])
Review False Positive Share = SUM([Benchmark False Positive]) / SUM([Alert Indicator])
Payment Day = DATETRUNC('day', [timestamp])
Fictional Risk Geography = [destination_country] = "XZ" OR [destination_country] = "QZ"
```

For full fact imports use `destination_geography_key` through the destination dimension,
not the absent `destination_country` field. Add null/zero-denominator handling where needed.
On the alert fact, closed disposition is a human outcome; do not substitute synthetic truth.
Calculated-field syntax and display typing need verification in Desktop before claiming use.
