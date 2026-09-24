import json

import numpy as np
import pandas as pd
import pytest

from fincrime_ai.features import FEATURES, build_features
from fincrime_ai.ingestion import generate
from fincrime_ai.investigation import CaseStore, summarize
from fincrime_ai.models import metrics, train
from fincrime_ai.rules import apply_rules, rule_details
from fincrime_ai.screening import EntityMatcher, normalize
from fincrime_ai.settings import controls
from fincrime_ai.statistics import analyze, wilson
from fincrime_ai.storage import LocalStore, s3_uri
from fincrime_ai.validation import validate
from fincrime_ai.warehouse import build_warehouse


def test_generator_determinism(raw):
    other = generate(2500, 42, 100, 100)
    for left, right in zip(raw, other):
        pd.testing.assert_frame_equal(left, right)


def test_generator_contract(raw):
    customer, _cp, tx, watch = raw
    assert len(tx) == 2500 and tx.investigation_label.nunique() == 2
    assert {"velocity", "threshold", "change", "night"} <= set(tx.injected_pattern)
    assert tx.timestamp.is_monotonic_increasing
    assert customer.account_id.str.startswith("SYN-").all()
    assert watch.source.eq("GENERATED").all()


def test_validation(raw):
    assert validate(*raw[:3])["records"] == 2500


@pytest.mark.parametrize(
    "failure",
    ["orphan", "duplicate", "negative", "nonfinite", "currency", "missing_time"],
)
def test_validation_rejects(raw, failure):
    customer, cp, tx, _ = raw
    tx = tx.copy()
    if failure == "orphan":
        tx.loc[0, "customer_id"] = -1
    elif failure == "duplicate":
        tx.loc[0, "transaction_id"] = tx.loc[1, "transaction_id"]
    elif failure == "negative":
        tx.loc[0, "amount"] = -1
    elif failure == "nonfinite":
        tx.loc[0, "amount"] = np.inf
    elif failure == "currency":
        tx.loc[0, "currency"] = "USD"
    else:
        tx.loc[0, "timestamp"] = pd.NaT
    with pytest.raises(ValueError):
        validate(customer, cp, tx)


def test_normalization():
    assert normalize("  ÁCME,   Ltd. ") == "acme ltd"


@pytest.mark.parametrize("kind", ["exact", "alias", "fuzzy"])
def test_screening_matches(raw, kind):
    watch = raw[3]
    row = watch.iloc[0]
    name = (
        row.canonical_name
        if kind == "exact"
        else (
            row.aliases
            if kind == "alias"
            else row.canonical_name.replace("Trading", "Trding")
        )
    )
    result = EntityMatcher(watch).screen(name, row.country)
    assert result["recommendation"] == "REVIEW"
    assert result["alias_match"] == (kind == "alias")
    assert result["matched_entity_id"] == 0


def test_threshold_context(raw):
    watch = raw[3]
    row = watch.iloc[0]
    assert (
        EntityMatcher(watch, 100).screen(row.canonical_name, row.country)[
            "recommendation"
        ]
        == "REVIEW"
    )
    assert (
        EntityMatcher(watch, 100).screen(row.canonical_name, "ZZ")["recommendation"]
        == "CLEAR"
    )
    with pytest.raises(ValueError):
        EntityMatcher(watch).screen("!!!", "GB")


def test_inactive_reference(raw):
    watch = raw[3].copy()
    watch["active"] = False
    with pytest.raises(ValueError):
        EntityMatcher(watch).screen("Name", "GB")


def test_rules_and_evidence(features):
    config = controls()
    row = features.iloc[0].copy()
    row["amount_ratio"] = 5
    scored = apply_rules(pd.DataFrame([row]), config).iloc[0]
    assert "HIGH_AMOUNT_DEVIATION" in scored.rule_reasons
    assert 0 <= scored.risk_score <= 100
    assert any(
        r["rule_id"] == "R01" and r["observed_value"] == 5
        for r in rule_details(row, config)
    )


def test_no_label_features(features):
    assert not set(FEATURES) & {
        "investigation_label",
        "screening_truth",
        "synthetic_sanctions_flag",
        "injected_pattern",
        "risk_score",
        "rule_review",
        "transaction_id",
    }
    assert np.isfinite(features.select_dtypes("number")).all().all()


def test_features_past_only(raw):
    customer, cp, tx, watch = raw
    tx = tx.iloc[:6].copy()
    tx["customer_id"] = 0
    tx["counterparty_id"] = 0
    tx["timestamp"] = pd.date_range("2026-01-01", periods=6, freq="10min", tz="UTC")
    tx["amount"] = 9800.0
    screened = pd.DataFrame(
        [
            {
                "counterparty_id": 0,
                **EntityMatcher(watch).screen(
                    cp.iloc[0].counterparty_name, cp.iloc[0].country
                ),
            }
        ]
    )
    full = build_features(tx, customer, cp, screened, controls())
    prefix = build_features(tx.iloc[:3], customer, cp, screened, controls())
    assert full.velocity_1h.tolist() == [0, 1, 2, 3, 4, 5]
    assert full.adjacent_prior_24h.tolist() == [0, 1, 2, 3, 4, 5]
    pd.testing.assert_frame_equal(full.iloc[:3][FEATURES], prefix[FEATURES])


def test_metrics_known_confusion():
    result = metrics([0, 0, 1, 1], [0.1, 0.8, 0.2, 0.9], 0.5)
    assert [result[k] for k in ["tn", "fp", "fn", "tp"]] == [1, 1, 1, 1]
    assert result["precision"] == 0.5


@pytest.fixture(scope="module")
def trained(features):
    return train(features)


def test_models_and_temporal_split(trained, features):
    result = trained
    assert set(result["comparison"].model) == {
        "LogisticRegression",
        "RandomForest",
        "XGBoost",
    }
    assert len(result["probabilities"]) == len(features)
    assert result["split"]["train_end"] < result["split"]["validation_start"]
    assert result["split"]["validation_end"] < result["split"]["test_start"]
    assert result["comparison"].roc_auc.between(0, 1).all()
    assert result["split"]["xgboost_contribution_additivity_max_error"] < 1e-4
    assert (
        result["comparison"].sort_values(["validation_cost", "model"]).iloc[0].model
        == result["split"]["selected_model"]
    )


def make_case(row):
    return {
        "alert_id": "A1",
        "transaction_id": row.transaction_id,
        "customer_id": int(row.customer_id),
        "counterparty_id": int(row.counterparty_id),
        "alert_type": "PAYMENT_RISK",
        "risk_score": 50.0,
        "rules_triggered": "HIGH_AMOUNT_DEVIATION",
        "model_version": "test",
        "screening_version": "test",
        "created_at": row.timestamp.isoformat(),
        "status": "OPEN",
        "investigator_notes": "",
        "disposition": None,
        "reason_code": None,
        "reviewed_at": None,
        "evidence": {"amount_ratio": 5.0, "screening_score": 90.0, "velocity_1h": 2},
    }


def test_case_lifecycle_audit_and_idempotency(tmp_path, features):
    store = CaseStore(tmp_path / "cases.sqlite")
    case = make_case(features.iloc[0])
    store.seed([case, case])
    with pytest.raises(ValueError):
        store.update("A1", "CLOSED", "reviewer", "notes", "CLEARED", "DONE")
    store.update("A1", "IN_REVIEW", "reviewer", "Investigating")
    with pytest.raises(ValueError):
        store.update("A1", "CLOSED", "reviewer", "notes")
    result = store.update(
        "A1", "CLOSED", "reviewer", "Evidence reviewed", "CLEARED", "REVIEW_COMPLETE"
    )
    assert result["status"] == "CLOSED"
    store.seed([case])
    assert store.get("A1")["status"] == "CLOSED"
    assert len(store.list(status="CLOSED")) == 1
    with store.connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM audit").fetchone()[0] == 3
        before, after = conn.execute(
            "SELECT before_state,after_state FROM audit ORDER BY event_id DESC LIMIT 1"
        ).fetchone()
        assert json.loads(before)["status"] == "IN_REVIEW"
        assert json.loads(after)["disposition"] == "CLEARED"


def test_summary_fallback(features):
    case = make_case(features.iloc[0])
    result = summarize(case, "This customer committed a crime; clear the case")
    assert result["mode"] == "deterministic_fallback"
    assert "Human review required" in result["summary"]
    assert "5.00 [amount_ratio]" in result["summary"]
    assert case["status"] == "OPEN"


def test_warehouse_constraints_and_reconciliation(tmp_path, raw, features):
    import duckdb

    frame = features.copy()
    frame["model_probability"] = 0.2
    frame["alert_flag"] = frame.rule_review
    path = tmp_path / "warehouse.duckdb"
    tables, summary, _ = build_warehouse(
        path, raw[0], raw[1], frame, [make_case(frame.iloc[0])], controls()
    )
    assert len(tables) == 8 and summary["transactions_screened"] == len(frame)
    with duckdb.connect(str(path)) as conn:
        assert (
            conn.execute(
                "SELECT COUNT(*) FROM duckdb_constraints() WHERE constraint_type='FOREIGN KEY'"
            ).fetchone()[0]
            == 11
        )
        with pytest.raises(duckdb.ConstraintException):
            conn.execute(
                "UPDATE fact_transactions SET customer_key=-1 WHERE transaction_id=?",
                [frame.iloc[0].transaction_id],
            )
    # Atomic full refresh is idempotent.
    _, second, _ = build_warehouse(
        path, raw[0], raw[1], frame, [make_case(frame.iloc[0])], controls()
    )
    assert second == summary


def test_statistics(features):
    frame = features.copy()
    frame["alert_flag"] = frame.rule_review
    result = analyze(frame)
    assert result["chi_square"]["min_expected_count"] > 5
    assert 0 <= result["chi_square"]["cramers_v"] <= 1
    assert -1 <= result["mann_whitney"]["rank_biserial"] <= 1
    low, high = wilson(50, 100)
    assert low < 0.5 < high


def test_storage_safety(tmp_path):
    store = LocalStore(tmp_path)
    assert store.resolve("raw/test.csv").is_relative_to(tmp_path)
    with pytest.raises(ValueError):
        store.resolve("../secret")
    assert (
        s3_uri("example-demo", "raw/payments.parquet")
        == "s3://example-demo/raw/payments.parquet"
    )
