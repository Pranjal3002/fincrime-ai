SELECT d.calendar_date, COUNT(*) AS transactions,
       SUM(CAST(f.alert_flag AS INTEGER)) AS alerts,
       SUM(f.amount) AS payment_value_gbp, AVG(f.risk_score) AS average_risk_score
FROM fact_transactions f JOIN dim_date d USING(date_key)
GROUP BY d.calendar_date ORDER BY d.calendar_date;
