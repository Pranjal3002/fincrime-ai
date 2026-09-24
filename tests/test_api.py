import joblib
import pytest
from fastapi.testclient import TestClient
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from api import main
from fincrime_ai.features import FEATURES
from fincrime_ai.investigation import CaseStore
from fincrime_ai.models import preprocessing


@pytest.fixture
def client(tmp_path, monkeypatch, raw, features):
    data = tmp_path / "data"
    artifacts = tmp_path / "artifacts"
    reports = tmp_path / "reports"
    for path in [data / "reference", data / "processed", artifacts, reports]:
        path.mkdir(parents=True, exist_ok=True)
    raw[3].to_csv(data / "reference/watchlist.csv", index=False)
    frame = features.copy()
    frame["xgboost_top_contributors"] = "numeric__amount_ratio=+0.2"
    frame.to_parquet(data / "processed/analytical_transactions.parquet", index=False)
    model = Pipeline(
        [
            ("preprocess", preprocessing()),
            ("classifier", LogisticRegression(max_iter=200)),
        ]
    )
    model.fit(frame[FEATURES], frame.investigation_label)
    joblib.dump(model, artifacts / "risk_model.joblib")
    (reports / "model_metrics.json").write_text(
        '{"split":{"threshold":0.5,"model_version":"test"},"models":[]}'
    )
    (reports / "run_manifest.json").write_text('{"cases_file":"cases.sqlite"}')
    (reports / "analytics_summary.json").write_text('{"transactions_screened":2500}')
    CaseStore(artifacts / "cases.sqlite").seed(
        [
            {
                "alert_id": "A1",
                "transaction_id": "SYN-TX-0000001",
                "status": "OPEN",
                "rules_triggered": "HIGH_AMOUNT_DEVIATION",
                "evidence": {
                    "amount_ratio": 5.0,
                    "screening_score": 90.0,
                    "velocity_1h": 2,
                },
            }
        ]
    )
    monkeypatch.setattr(main, "DATA", data)
    monkeypatch.setattr(main, "REPORTS", reports)
    monkeypatch.setattr(main, "ARTIFACTS", artifacts)
    for loader in [main.matcher, main.model, main.analytical]:
        loader.cache_clear()
    yield TestClient(main.app)
    for loader in [main.matcher, main.model, main.analytical]:
        loader.cache_clear()


def test_health():
    assert TestClient(main.app).get("/health").json()["status"] == "ok"


def test_scoring(client, features):
    tx = features.iloc[0].transaction_id
    response = client.post("/score/transaction", json={"transaction_id": tx})
    assert response.status_code == 200
    assert 0 <= response.json()["probability"] <= 1
    assert response.json()["recommendation"] in {"CLEAR", "REVIEW"}
    assert (
        client.post(
            "/score/transaction", json={"transaction_id": "SYN-TX-9999999"}
        ).status_code
        == 404
    )
    assert (
        client.post(
            "/score/transaction", json={"transaction_id": tx, "investigation_label": 1}
        ).status_code
        == 422
    )


def test_screen_api(client, raw):
    row = raw[3].iloc[0]
    response = client.post(
        "/screen/entity", json={"name": row.canonical_name, "country": row.country}
    )
    assert response.status_code == 200 and response.json()["recommendation"] == "REVIEW"
    assert (
        client.post("/screen/entity", json={"name": " ", "country": "GB"}).status_code
        == 422
    )


def test_workflow_api(client):
    assert client.get("/alerts").status_code == 200
    assert client.get("/alerts/missing").status_code == 404
    assert client.get("/alerts?limit=1000").status_code == 422
    assert (
        client.patch(
            "/alerts/A1",
            json={
                "status": "CLOSED",
                "actor": "reviewer",
                "investigator_notes": "notes",
            },
        ).status_code
        == 409
    )
    assert (
        client.patch(
            "/alerts/A1",
            json={
                "status": "IN_REVIEW",
                "actor": "reviewer",
                "investigator_notes": "Checking evidence",
            },
        ).status_code
        == 200
    )
    assert client.post("/investigation/A1/summary").json()["human_review_required"]
    assert client.get("/analytics/summary").status_code == 200
    assert client.get("/model/metrics").status_code == 200
