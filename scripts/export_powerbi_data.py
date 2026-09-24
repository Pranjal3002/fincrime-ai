"""Export existing validated outputs for Power BI; never retrain or alter the core run."""

import argparse
import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

from fincrime_ai.investigation import CaseStore
from fincrime_ai.settings import ARTIFACTS, DATA, REPORTS


def export(target=None):
    target = Path(target or DATA / "powerbi")
    target.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((REPORTS / "run_manifest.json").read_text())
    metrics = json.loads((REPORTS / "model_metrics.json").read_text())
    summary = json.loads((REPORTS / "analytics_summary.json").read_text())
    stats = json.loads((REPORTS / "statistics.json").read_text())
    frame = pd.read_parquet(DATA / "processed/analytical_transactions.parquet")
    tables = {p.stem: pd.read_csv(p) for p in (DATA / "curated").glob("dim_*.csv")}
    tables["dim_origin_geography"] = tables["dim_geography"].copy()
    tables["dim_destination_geography"] = tables.pop("dim_geography")
    counterparties = pd.read_parquet(DATA / "raw/counterparties.parquet")
    screen = pd.read_csv(DATA / "curated/entity_screening.csv")
    tables["dim_counterparty"] = (
        tables["dim_counterparty"]
        .merge(
            counterparties[["counterparty_id", "baseline_risk"]],
            on="counterparty_id",
            validate="1:1",
        )
        .merge(
            screen.drop(columns=["counterparty"]), on="counterparty_id", validate="1:1"
        )
    )
    tables["dim_counterparty"]["match_method"] = np.select(
        [
            tables["dim_counterparty"].alias_match,
            tables["dim_counterparty"].name_similarity_score.eq(100),
        ],
        ["Alias", "Exact"],
        default="Fuzzy candidate",
    )
    tx = pd.read_csv(DATA / "curated/fact_transactions.csv")
    extras = frame[
        [
            "transaction_id",
            "velocity_1h",
            "amount_ratio",
            "night",
            "new_counterparty",
            "recommendation",
        ]
    ].copy()
    extras["hour_utc"] = frame.timestamp.dt.hour
    extras["screening_review"] = (frame.recommendation == "REVIEW").astype(int)
    extras["screening_score_band"] = (
        (frame.screening_score // 10 * 10).clip(upper=90).astype(int)
    )
    extras["amount_band"] = pd.cut(
        frame.amount,
        [0, 500, 1000, 2500, 5000, 10000, np.inf],
        labels=[
            "01 | <500",
            "02 | 500-999",
            "03 | 1k-2.5k",
            "04 | 2.5k-5k",
            "05 | 5k-10k",
            "06 | 10k+",
        ],
        right=False,
    ).astype(str)
    tx = tx.merge(extras, on="transaction_id", validate="1:1")
    tx["alert_flag"] = tx.alert_flag.astype(int)
    tx["timestamp"] = (
        pd.to_datetime(tx.timestamp, utc=True)
        .dt.tz_localize(None)
        .dt.strftime("%Y-%m-%dT%H:%M:%S")
    )
    tables["fact_transactions"] = tx
    store = CaseStore(ARTIFACTS / manifest["cases_file"])
    cases = pd.DataFrame(store.list(limit=len(frame)))
    cases = cases.drop(columns=["evidence"])
    keys = tx[
        [
            "transaction_id",
            "customer_key",
            "counterparty_key",
            "date_key",
            "origin_geography_key",
            "destination_geography_key",
            "channel_key",
            "risk_key",
        ]
    ]
    cases = cases.merge(keys, on="transaction_id", validate="1:1")
    cases["disposition"] = cases.disposition.fillna("NOT_REVIEWED")
    # Fixed data-as-of age is reproducible and never claimed as real elapsed service time.
    asof = frame.timestamp.max()
    cases["age_at_data_cutoff_days"] = (
        asof - pd.to_datetime(cases.created_at, utc=True)
    ).dt.total_seconds() / 86400
    for col in ["created_at", "reviewed_at"]:
        cases[col] = (
            pd.to_datetime(cases[col], utc=True)
            .dt.tz_localize(None)
            .dt.strftime("%Y-%m-%dT%H:%M:%S")
        )
    tables["fact_screening_alerts"] = cases
    rules = cases[["alert_id", "rules_triggered"]].copy()
    rules["rule_name"] = rules.rules_triggered.fillna("").str.split("|")
    rules = rules.explode("rule_name")
    tables["bridge_alert_rules"] = rules.loc[
        rules.rule_name.ne(""), ["alert_id", "rule_name"]
    ]
    tables["model_comparison"] = pd.DataFrame(metrics["models"])
    tables["threshold_analysis"] = pd.read_csv(REPORTS / "threshold_analysis.csv")
    importance = pd.read_csv(REPORTS / "feature_importance.csv")
    importance["feature"] = importance.feature.str.replace(
        "numeric__", "", regex=False
    ).str.replace("category__", "", regex=False)
    tables["feature_importance"] = importance
    tables["confusion_matrix"] = pd.DataFrame(
        [
            {
                "model": r["model"],
                "actual": actual,
                "predicted": predicted,
                "cell": cell.upper(),
                "count": r[cell],
            }
            for r in metrics["models"]
            for actual, predicted, cell in [
                ("Negative", "Clear", "tn"),
                ("Negative", "Review", "fp"),
                ("Positive", "Clear", "fn"),
                ("Positive", "Review", "tp"),
            ]
        ]
    )
    tables["statistical_findings"] = pd.DataFrame(
        [
            {
                "chi_square": stats["chi_square"]["statistic"],
                "chi_p_value": stats["chi_square"]["p_value"],
                "cramers_v": stats["chi_square"]["cramers_v"],
                "mann_whitney_u": stats["mann_whitney"]["u"],
                "rank_biserial": stats["mann_whitney"]["rank_biserial"],
                "spearman_rho": stats["spearman"]["rho"],
                "ci_lower": stats["alert_rate_wilson_95"][0],
                "ci_upper": stats["alert_rate_wilson_95"][1],
                "alerted_median": stats["mann_whitney"]["alerted_median"],
                "nonalerted_median": stats["mann_whitney"]["nonalerted_median"],
                "interpretation": "Exploratory synthetic associations; repeated payments limit independence. Rules partly define the observed relationships. Tiny p-values may underflow; significance is not business value.",
            }
        ]
    )
    assert len(tx) == int(summary["transactions_screened"]) == manifest["records"]
    assert len(cases) == int(summary["alerts"]) == int(tx.alert_flag.sum())
    assert abs(tx.risk_score.mean() - summary["average_risk_score"]) < 1e-9
    assert (tx.alert_flag.eq(1) & tx.risk_score.ge(70)).sum() == summary[
        "high_risk_alerts"
    ]
    output = {}
    for name, table in tables.items():
        path = target / f"{name}.csv"
        table.to_csv(path, index=False, date_format="%Y-%m-%d", float_format="%.15g")
        output[name] = {
            "rows": len(table),
            "columns": len(table.columns),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
    checks = {
        "transactions": len(tx),
        "alerts": len(cases),
        "alert_rate": float(tx.alert_flag.mean()),
        "high_risk_alerts": int((tx.alert_flag.eq(1) & tx.risk_score.ge(70)).sum()),
        "average_risk_score": float(tx.risk_score.mean()),
        "total_amount_gbp": round(float(tx.amount.sum()), 2),
        "status_counts": cases.status.value_counts().to_dict(),
        "source_run_key": manifest["run_key"],
        "source_watermark": manifest["watermark"],
        "tables": output,
    }
    (REPORTS / "powerbi_export_validation.json").write_text(
        json.dumps(checks, indent=2), encoding="utf-8"
    )
    return checks


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--desktop-data-dir",
        type=Path,
        help="Optional machine-neutral local CSV mirror for Power Query",
    )
    args = parser.parse_args()
    result = export()
    if args.desktop_data_dir:
        args.desktop_data_dir.mkdir(parents=True, exist_ok=True)
        for source in (DATA / "powerbi").glob("*.csv"):
            shutil.copy2(source, args.desktop_data_dir / source.name)
    print(
        json.dumps(
            {key: value for key, value in result.items() if key != "tables"}, indent=2
        )
    )
