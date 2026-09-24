"""SQLite simulated cases; validated transitions and transactional audit records."""

import json
import sqlite3
from datetime import UTC, datetime

TRANSITIONS = {
    "OPEN": {"IN_REVIEW"},
    "IN_REVIEW": {"ESCALATED", "CLOSED"},
    "ESCALATED": {"IN_REVIEW", "CLOSED"},
    "CLOSED": set(),
}
DISPOSITIONS = {"FALSE_POSITIVE", "FURTHER_REVIEW", "CLEARED"}


class CaseStore:
    def __init__(self, path):
        self.path = str(path)
        with self.connect() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS cases (alert_id TEXT PRIMARY KEY, body TEXT NOT NULL)"
            )
            conn.execute(
                "CREATE TABLE IF NOT EXISTS audit (event_id INTEGER PRIMARY KEY AUTOINCREMENT, alert_id TEXT, actor TEXT, action TEXT, timestamp TEXT, before_state TEXT, after_state TEXT)"
            )

    def connect(self):
        return sqlite3.connect(self.path, timeout=20)

    def seed(self, cases):
        with self.connect() as conn:
            for case in cases:
                body = json.dumps(case, default=str)
                cursor = conn.execute(
                    "INSERT OR IGNORE INTO cases VALUES (?,?)", (case["alert_id"], body)
                )
                if cursor.rowcount:
                    conn.execute(
                        "INSERT INTO audit (alert_id,actor,action,timestamp,before_state,after_state) VALUES (?,?,?,?,?,?)",
                        (
                            case["alert_id"],
                            "pipeline",
                            "CREATE",
                            datetime.now(UTC).isoformat(),
                            "null",
                            body,
                        ),
                    )

    def get(self, alert_id):
        with self.connect() as conn:
            row = conn.execute(
                "SELECT body FROM cases WHERE alert_id=?", (alert_id,)
            ).fetchone()
        if row is None:
            raise KeyError(alert_id)
        return json.loads(row[0])

    def list(self, limit=100, offset=0, status=None):
        with self.connect() as conn:
            if status:
                rows = conn.execute(
                    "SELECT body FROM cases WHERE json_extract(body,'$.status')=? ORDER BY alert_id LIMIT ? OFFSET ?",
                    (status, limit, offset),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT body FROM cases ORDER BY alert_id LIMIT ? OFFSET ?",
                    (limit, offset),
                ).fetchall()
        return [json.loads(row[0]) for row in rows]

    def update(
        self, alert_id, status, actor, notes, disposition=None, reason_code=None
    ):
        if not actor.strip() or not notes.strip():
            raise ValueError("A human actor and investigation notes are required")
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT body FROM cases WHERE alert_id=?", (alert_id,)
            ).fetchone()
            if not row:
                raise KeyError(alert_id)
            before = json.loads(row[0])
            if status not in TRANSITIONS[before["status"]]:
                raise ValueError("Invalid workflow transition")
            if status == "CLOSED" and (
                disposition not in DISPOSITIONS or not reason_code
            ):
                raise ValueError("Closing requires valid disposition and reason code")
            if status != "CLOSED" and disposition is not None:
                raise ValueError("Disposition is only permitted on closure")
            stamp = datetime.now(UTC).isoformat()
            after = {
                **before,
                "status": status,
                "investigator_notes": notes,
                "disposition": disposition,
                "reason_code": reason_code,
                "reviewed_at": stamp,
            }
            body = json.dumps(after)
            conn.execute("UPDATE cases SET body=? WHERE alert_id=?", (body, alert_id))
            conn.execute(
                "INSERT INTO audit (alert_id,actor,action,timestamp,before_state,after_state) VALUES (?,?,?,?,?,?)",
                (alert_id, actor, "HUMAN_REVIEW", stamp, row[0], body),
            )
        return after


def summarize(case, generated=None):
    evidence = case["evidence"]
    text = f"Transaction {case['transaction_id']} has amount / expected baseline ratio {evidence['amount_ratio']:.2f} [amount_ratio], synthetic reference similarity {evidence['screening_score']:.1f}/100 [screening_score], and {evidence['velocity_1h']} prior payments in one hour [velocity_1h]. Triggered controls: {case['rules_triggered'] or 'MODEL_THRESHOLD'} [rules_triggered]. Human review required."
    # Strict allowlist: only an exact evidence-backed template is accepted.
    return {
        "summary": text,
        "mode": "validated_template" if generated == text else "deterministic_fallback",
        "evidence_fields": [
            "amount_ratio",
            "screening_score",
            "velocity_1h",
            "rules_triggered",
        ],
        "human_review_required": True,
    }
