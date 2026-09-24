"""Atomic warehouse rebuild, enforced foreign keys, stable surrogate keys."""

import os

import duckdb
import pandas as pd

from fincrime_ai.settings import ROOT


def build_warehouse(path, customers, counterparties, frame, cases, config):
    path = path.resolve()
    temporary = path.with_suffix(".building.duckdb")
    if temporary.exists():
        temporary.unlink()
    con = duckdb.connect(str(temporary))
    tables = {}
    customer = customers.copy()
    customer.insert(0, "customer_key", customer.customer_id + 1)
    order = [
        "customer_key",
        "customer_id",
        "account_id",
        "customer_type",
        "residence_country",
        "account_age_days",
        "industry",
        "risk_segment",
        "kyc_status",
        "pep_flag",
        "expected_monthly_volume",
        "expected_amount",
        "expected_min",
        "expected_max",
    ]
    tables["dim_customer"] = customer[order]
    cp = counterparties[
        ["counterparty_id", "counterparty_name", "country", "counterparty_type"]
    ].copy()
    cp.insert(0, "counterparty_key", cp.counterparty_id + 1)
    tables["dim_counterparty"] = cp
    dates = pd.DatetimeIndex(frame.timestamp.dt.normalize().unique()).sort_values()
    tables["dim_date"] = pd.DataFrame(
        {
            "date_key": dates.strftime("%Y%m%d").astype(int),
            "calendar_date": dates.date,
            "year": dates.year,
            "month": dates.month,
            "day": dates.day,
        }
    )
    countries = sorted(set(frame.origin_country) | set(frame.destination_country))
    geo = {country: i + 1 for i, country in enumerate(countries)}
    tables["dim_geography"] = pd.DataFrame(
        {
            "geography_key": list(geo.values()),
            "country_code": countries,
            "fictional_high_risk": [
                c in config["high_risk_countries"] for c in countries
            ],
        }
    )
    channels = sorted(frame.payment_channel.unique())
    channel = {name: i + 1 for i, name in enumerate(channels)}
    tables["dim_payment_channel"] = pd.DataFrame(
        {"channel_key": list(channel.values()), "payment_channel": channels}
    )
    tables["dim_risk_category"] = pd.DataFrame(
        {"risk_key": [1, 2, 3], "risk_category": ["LOW", "MEDIUM", "HIGH"]}
    )
    fact = frame.copy()
    fact["customer_key"] = fact.customer_id + 1
    fact["counterparty_key"] = fact.counterparty_id + 1
    fact["date_key"] = fact.timestamp.dt.strftime("%Y%m%d").astype(int)
    fact["origin_geography_key"] = fact.origin_country.map(geo)
    fact["destination_geography_key"] = fact.destination_country.map(geo)
    fact["channel_key"] = fact.payment_channel.map(channel)
    fact["risk_key"] = pd.cut(
        fact.risk_score, [-1, 39, 69, 100], labels=[1, 2, 3]
    ).astype(int)
    tables["fact_transactions"] = fact[
        [
            "transaction_id",
            "customer_key",
            "counterparty_key",
            "date_key",
            "origin_geography_key",
            "destination_geography_key",
            "channel_key",
            "risk_key",
            "timestamp",
            "amount",
            "currency",
            "payment_type",
            "payment_category",
            "originating_bank",
            "network",
            "beneficiary_bank",
            "status",
            "risk_score",
            "model_probability",
            "screening_score",
            "alert_flag",
            "rule_reasons",
            "investigation_label",
            "screening_truth",
        ]
    ]
    alerts = pd.DataFrame(cases)
    alerts["customer_key"] = alerts.customer_id + 1
    alerts["counterparty_key"] = alerts.counterparty_id + 1
    alerts["date_key"] = (
        pd.to_datetime(alerts.created_at).dt.strftime("%Y%m%d").astype(int)
    )
    tables["fact_screening_alerts"] = alerts[
        [
            "alert_id",
            "transaction_id",
            "customer_key",
            "counterparty_key",
            "date_key",
            "alert_type",
            "risk_score",
            "rules_triggered",
            "model_version",
            "screening_version",
            "created_at",
            "status",
            "investigator_notes",
            "disposition",
            "reason_code",
            "reviewed_at",
        ]
    ]
    try:
        con.execute("BEGIN")
        con.execute((ROOT / "sql/schema/star.sql").read_text())
        for name, table in tables.items():
            con.register("incoming", table)
            con.execute(f"INSERT INTO {name} SELECT * FROM incoming")
            con.unregister("incoming")
        count, total = con.execute(
            "SELECT COUNT(*),SUM(amount) FROM fact_transactions"
        ).fetchone()
        if count != len(frame) or abs(float(total) - float(frame.amount.sum())) > 0.01:
            raise ValueError("Warehouse reconciliation failed")
        con.execute("COMMIT")
        summary = (
            con.execute((ROOT / "sql/analytics/operations.sql").read_text())
            .df()
            .iloc[0]
            .to_dict()
        )
        daily = con.execute((ROOT / "sql/transformations/daily.sql").read_text()).df()
    finally:
        con.close()
    os.replace(temporary, path)
    return tables, summary, daily
