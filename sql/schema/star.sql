CREATE TABLE dim_customer (
 customer_key BIGINT PRIMARY KEY, customer_id BIGINT UNIQUE NOT NULL,
 account_id VARCHAR, customer_type VARCHAR, residence_country VARCHAR,
 account_age_days INTEGER, industry VARCHAR, risk_segment VARCHAR,
 kyc_status VARCHAR, pep_flag BOOLEAN, expected_monthly_volume INTEGER,
 expected_amount DOUBLE, expected_min DOUBLE, expected_max DOUBLE
);
CREATE TABLE dim_counterparty (
 counterparty_key BIGINT PRIMARY KEY, counterparty_id BIGINT UNIQUE NOT NULL,
 counterparty_name VARCHAR, country VARCHAR, counterparty_type VARCHAR
);
CREATE TABLE dim_date (date_key INTEGER PRIMARY KEY, calendar_date DATE UNIQUE, year INTEGER, month INTEGER, day INTEGER);
CREATE TABLE dim_geography (geography_key INTEGER PRIMARY KEY, country_code VARCHAR UNIQUE, fictional_high_risk BOOLEAN);
CREATE TABLE dim_payment_channel (channel_key INTEGER PRIMARY KEY, payment_channel VARCHAR UNIQUE);
CREATE TABLE dim_risk_category (risk_key INTEGER PRIMARY KEY, risk_category VARCHAR UNIQUE);
CREATE TABLE fact_transactions (
 transaction_id VARCHAR PRIMARY KEY,
 customer_key BIGINT NOT NULL REFERENCES dim_customer(customer_key),
 counterparty_key BIGINT NOT NULL REFERENCES dim_counterparty(counterparty_key),
 date_key INTEGER NOT NULL REFERENCES dim_date(date_key),
 origin_geography_key INTEGER NOT NULL REFERENCES dim_geography(geography_key),
 destination_geography_key INTEGER NOT NULL REFERENCES dim_geography(geography_key),
 channel_key INTEGER NOT NULL REFERENCES dim_payment_channel(channel_key),
 risk_key INTEGER NOT NULL REFERENCES dim_risk_category(risk_key),
 timestamp TIMESTAMPTZ, amount DECIMAL(18,2), currency VARCHAR,
 payment_type VARCHAR, payment_category VARCHAR, originating_bank VARCHAR,
 network VARCHAR, beneficiary_bank VARCHAR, status VARCHAR,
 risk_score DOUBLE, model_probability DOUBLE, screening_score DOUBLE,
 alert_flag BOOLEAN, rule_reasons VARCHAR, investigation_label INTEGER,
 screening_truth INTEGER
);
CREATE TABLE fact_screening_alerts (
 alert_id VARCHAR PRIMARY KEY,
 transaction_id VARCHAR NOT NULL REFERENCES fact_transactions(transaction_id),
 customer_key BIGINT NOT NULL REFERENCES dim_customer(customer_key),
 counterparty_key BIGINT NOT NULL REFERENCES dim_counterparty(counterparty_key),
 date_key INTEGER NOT NULL REFERENCES dim_date(date_key),
 alert_type VARCHAR, risk_score DOUBLE, rules_triggered VARCHAR,
 model_version VARCHAR, screening_version VARCHAR, created_at TIMESTAMPTZ,
 status VARCHAR, investigator_notes VARCHAR, disposition VARCHAR,
 reason_code VARCHAR, reviewed_at TIMESTAMPTZ
);
