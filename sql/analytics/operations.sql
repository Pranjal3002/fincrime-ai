-- Transaction-grain metrics: never count a joined alert fact as transaction volume.
SELECT COUNT(*) AS transactions_screened,
       SUM(CAST(alert_flag AS INTEGER)) AS alerts,
       AVG(CAST(alert_flag AS INTEGER)) AS alert_rate,
       AVG(risk_score) AS average_risk_score,
       SUM(CASE WHEN alert_flag AND risk_score >= 70 THEN 1 ELSE 0 END) AS high_risk_alerts
FROM fact_transactions;
