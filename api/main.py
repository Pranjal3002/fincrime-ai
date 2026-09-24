"""Loopback-only portfolio API; no production identity or authorization layer."""

import json
from functools import lru_cache
from typing import Literal

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from fincrime_ai.features import FEATURES
from fincrime_ai.investigation import CaseStore, summarize
from fincrime_ai.rules import rule_details
from fincrime_ai.screening import EntityMatcher
from fincrime_ai.settings import ARTIFACTS, DATA, REPORTS, controls

app = FastAPI(
    title="FinCrimeAI | Synthetic Screening Lab",
    version="0.1.0",
    description="Educational simulation. Human review required. Bind to 127.0.0.1 only.",
)


def read_report(name):
    path = REPORTS / name
    if not path.exists():
        raise HTTPException(503, "Run python scripts/run_all.py first")
    return json.loads(path.read_text())


def cases():
    manifest = read_report("run_manifest.json")
    return CaseStore(ARTIFACTS / manifest["cases_file"])


@lru_cache
def matcher():
    path = DATA / "reference/watchlist.csv"
    if not path.exists():
        raise HTTPException(503, "Reference data not generated")
    return EntityMatcher(
        pd.read_csv(path).fillna(""), controls()["screening_threshold"]
    )


@lru_cache
def analytical():
    path = DATA / "processed/analytical_transactions.parquet"
    if not path.exists():
        raise HTTPException(503, "Analytical data not generated")
    return pd.read_parquet(path).set_index("transaction_id")


@lru_cache
def model():
    path = ARTIFACTS / "risk_model.joblib"
    if not path.exists():
        raise HTTPException(503, "Model not trained")
    return joblib.load(path)


class EntityRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=200)
    country: str = Field(pattern="^[A-Z]{2}$")
    entity_type: Literal["PERSON", "BUSINESS"] = "BUSINESS"


class TransactionRequest(BaseModel):
    """Score an ingested payment using trusted point-in-time features."""

    model_config = ConfigDict(extra="forbid")
    transaction_id: str = Field(pattern="^SYN-TX-[0-9]{7,}$")


class ReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    status: Literal["IN_REVIEW", "ESCALATED", "CLOSED"]
    actor: str = Field(min_length=1, max_length=80)
    investigator_notes: str = Field(min_length=1, max_length=2000)
    disposition: Literal["FALSE_POSITIVE", "FURTHER_REVIEW", "CLEARED"] | None = None
    reason_code: str | None = Field(default=None, min_length=1, max_length=80)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "simulation": True,
        "pipeline_ready": (REPORTS / "run_manifest.json").exists(),
    }


@app.post("/screen/entity")
def screen_entity(request: EntityRequest):
    try:
        return matcher().screen(request.name, request.country, request.entity_type)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.post("/score/transaction")
def score_transaction(request: TransactionRequest):
    frame = analytical()
    if request.transaction_id not in frame.index:
        raise HTTPException(
            404, "Transaction not found; ingest it through the batch pipeline"
        )
    row = frame.loc[request.transaction_id]
    probability = float(
        model().predict_proba(frame.loc[[request.transaction_id], FEATURES])[0, 1]
    )
    split = read_report("model_metrics.json")["split"]
    details = rule_details(row, controls())
    review = (
        probability >= split["threshold"]
        or bool(row.rule_review)
        or row.recommendation == "REVIEW"
    )
    return {
        "transaction_id": request.transaction_id,
        "probability": probability,
        "model_threshold": split["threshold"],
        "risk_score": int(row.risk_score),
        "recommendation": "REVIEW" if review else "CLEAR",
        "rules": details,
        "model_version": split["model_version"],
        "xgboost_top_contributors": row.xgboost_top_contributors,
        "explanation_model": "XGBoost (may differ from selected scoring model)",
        "human_review_required": review,
    }


@app.get("/alerts")
def list_alerts(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    status: Literal["OPEN", "IN_REVIEW", "ESCALATED", "CLOSED"] | None = None,
):
    return cases().list(limit, offset, status)


@app.get("/alerts/{alert_id}")
def get_alert(alert_id: str):
    try:
        return cases().get(alert_id)
    except KeyError as exc:
        raise HTTPException(404, "Alert not found") from exc


@app.patch("/alerts/{alert_id}")
def update_alert(alert_id: str, request: ReviewRequest):
    try:
        return cases().update(
            alert_id,
            request.status,
            request.actor,
            request.investigator_notes,
            request.disposition,
            request.reason_code,
        )
    except KeyError as exc:
        raise HTTPException(404, "Alert not found") from exc
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@app.get("/analytics/summary")
def analytics_summary():
    return read_report("analytics_summary.json")


@app.get("/model/metrics")
def model_metrics():
    return read_report("model_metrics.json")


@app.post("/investigation/{alert_id}/summary")
def investigation_summary(alert_id: str):
    return summarize(get_alert(alert_id))
