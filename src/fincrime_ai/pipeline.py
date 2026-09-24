"""Reproducible end-to-end batch run. Generated data and models remain ignored."""

import hashlib
import json
import time

import joblib
import numpy as np
import pandas as pd

from fincrime_ai.features import build_features
from fincrime_ai.ingestion import generate
from fincrime_ai.investigation import CaseStore
from fincrime_ai.models import metrics, train
from fincrime_ai.rules import apply_rules
from fincrime_ai.screening import EntityMatcher
from fincrime_ai.settings import ARTIFACTS, DATA, REPORTS, controls, prepare
from fincrime_ai.statistics import analyze
from fincrime_ai.validation import validate
from fincrime_ai.warehouse import build_warehouse


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, default=str), encoding="utf-8")


def run(n=100_000, seed=42):
    prepare()
    config = controls()
    overall = time.perf_counter()
    started = time.perf_counter()
    customers, counterparties, tx, watchlist = generate(n, seed)
    generation = time.perf_counter() - started
    quality = validate(customers, counterparties, tx)
    for name, frame in [
        ("customers", customers),
        ("counterparties", counterparties),
        ("transactions", tx),
    ]:
        frame.to_parquet(DATA / f"raw/{name}.parquet", index=False)
    watchlist.to_csv(DATA / "reference/watchlist.csv", index=False)
    print(f"Generated and validated {n:,} synthetic transactions", flush=True)
    started = time.perf_counter()
    matcher = EntityMatcher(watchlist, config["screening_threshold"])
    screened = pd.DataFrame(
        [
            {
                "counterparty_id": int(row.counterparty_id),
                **matcher.screen(row.counterparty_name, row.country),
            }
            for row in counterparties.itertuples()
        ]
    )
    screening = time.perf_counter() - started
    started = time.perf_counter()
    frame = apply_rules(
        build_features(tx, customers, counterparties, screened, config), config
    )
    transformation = time.perf_counter() - started
    print(
        "Screening and point-in-time features complete; training three models",
        flush=True,
    )
    result = train(frame, seed)
    frame["model_probability"] = result["probabilities"]
    frame["anomaly_score"] = result["anomaly_scores"]
    frame["xgboost_top_contributors"] = result["explanations"]
    frame["model_review"] = frame.model_probability.ge(result["split"]["threshold"])
    frame["alert_flag"] = (
        frame.rule_review | frame.model_review | frame.recommendation.eq("REVIEW")
    )
    frame["evaluation_split"] = np.repeat(
        ["train", "validation", "test"],
        [
            result["split"]["train_rows"],
            result["split"]["validation_rows"],
            result["split"]["test_rows"],
        ],
    )
    cases = []
    for row in frame.loc[frame.alert_flag].itertuples():
        cases.append(
            {
                "alert_id": f"ALERT-{row.transaction_id}",
                "transaction_id": row.transaction_id,
                "customer_id": int(row.customer_id),
                "counterparty_id": int(row.counterparty_id),
                "alert_type": (
                    "SCREENING" if row.recommendation == "REVIEW" else "PAYMENT_RISK"
                ),
                "risk_score": float(row.risk_score),
                "rules_triggered": row.rule_reasons,
                "model_version": result["split"]["model_version"],
                "screening_version": config["screening_version"],
                "created_at": row.timestamp.isoformat(),
                "status": "OPEN",
                "investigator_notes": "",
                "disposition": None,
                "reason_code": None,
                "reviewed_at": None,
                "evidence": {
                    "amount_ratio": float(row.amount_ratio),
                    "screening_score": float(row.screening_score),
                    "velocity_1h": int(row.velocity_1h),
                    "xgboost_top_contributors": row.xgboost_top_contributors,
                },
            }
        )
    # Preserve human review state across identical reruns; isolate other run configurations.
    run_key = hashlib.sha256(
        f"features-v2:{n}:{seed}:{json.dumps(config,sort_keys=True)}".encode()
    ).hexdigest()[:12]
    case_path = ARTIFACTS / f"cases-{run_key}.sqlite"
    store = CaseStore(case_path)
    store.seed(cases)
    current_cases = store.list(limit=len(cases))
    tables, summary, daily = build_warehouse(
        DATA / "warehouse.duckdb",
        customers,
        counterparties,
        frame,
        current_cases,
        config,
    )
    for name, table in tables.items():
        table.to_csv(DATA / f"curated/{name}.csv", index=False)
    daily.to_csv(DATA / "curated/daily_operations.csv", index=False)
    frame.to_parquet(DATA / "processed/analytical_transactions.parquet", index=False)
    screened.to_csv(DATA / "curated/entity_screening.csv", index=False)
    # Sampling is explicit: full fact exports remain available for BI.
    frame.sample(min(5000, len(frame)), random_state=seed).to_csv(
        DATA / "curated/transaction_explorer_sample.csv", index=False
    )
    result["comparison"].to_csv(REPORTS / "model_comparison.csv", index=False)
    result["thresholds"].to_csv(REPORTS / "threshold_analysis.csv", index=False)
    result["importance"].to_csv(REPORTS / "feature_importance.csv", index=False)
    joblib.dump(result["model"], ARTIFACTS / "risk_model.joblib")
    cp_truth = (
        counterparties.set_index("counterparty_id")
        .loc[screened.counterparty_id]
        .synthetic_sanctions_flag.astype(int)
    )
    screening_metrics = {
        "transaction_weighted": metrics(
            frame.screening_truth,
            frame.screening_score / 100,
            config["screening_threshold"] / 100,
        ),
        "unique_entities": metrics(
            cp_truth,
            screened.screening_score / 100,
            config["screening_threshold"] / 100,
        ),
    }
    stats = analyze(frame)
    write_json(REPORTS / "screening_metrics.json", screening_metrics)
    write_json(REPORTS / "statistics.json", stats)
    write_json(
        REPORTS / "model_metrics.json",
        {"split": result["split"], "models": result["comparison"].to_dict("records")},
    )
    write_json(REPORTS / "data_quality.json", quality)
    write_json(REPORTS / "analytics_summary.json", summary)
    write_json(
        REPORTS / "run_manifest.json",
        {
            "seed": seed,
            "records": n,
            "run_key": run_key,
            "cases_file": case_path.name,
            "engine": "pandas",
            "rules_version": config["version"],
            "rules_sha256": hashlib.sha256(
                json.dumps(config, sort_keys=True).encode()
            ).hexdigest(),
            "data_sha256": hashlib.sha256(
                (DATA / "raw/transactions.parquet").read_bytes()
            ).hexdigest(),
            "watermark": str(frame.timestamp.max()),
            "incremental_strategy": "idempotent keyed case inserts; atomic full warehouse rebuild; watermark recorded, streaming not implemented",
        },
    )
    write_json(
        REPORTS / "performance_metrics.json",
        {
            "records_processed": n,
            "generation_seconds": generation,
            "transformation_seconds": transformation,
            "screening_unique_entities": len(counterparties),
            "screening_seconds": screening,
            "model_scoring_seconds": result["scoring_seconds"],
            "total_seconds": time.perf_counter() - overall,
            "total_timing_scope": "Through warehouse and metric export; excludes subsequent analytical plot and executive report rendering",
            "screening_timing_scope": "Unique counterparty matching; excludes join and IO; cache reuse across payments",
        },
    )
    from fincrime_ai.reporting import report

    report(frame, result, summary, stats, screening_metrics)
    print(
        json.dumps(
            {
                "records": n,
                "alerts": len(cases),
                "selected_model": result["split"]["selected_model"],
                "warehouse_tables": len(tables),
                "elapsed_seconds": round(time.perf_counter() - overall, 2),
            }
        ),
        flush=True,
    )
    return summary
