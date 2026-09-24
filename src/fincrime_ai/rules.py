"""Versioned rule contributions, human-readable evidence, capped risk score."""

import numpy as np


def apply_rules(frame, config):
    result = frame.copy()
    result["risk_score"] = 0
    reasons = np.full(len(result), "", dtype=object)
    for rule in config["rules"]:
        if rule["operator"] != "ge":
            raise ValueError("Unsupported operator")
        mask = result[rule["feature"]].ge(rule["threshold"]).to_numpy()
        result[rule["rule_id"]] = mask
        result["risk_score"] += mask * rule["score"]
        reasons[mask] = [s + rule["rule_name"] + "|" for s in reasons[mask]]
    result["risk_score"] = result.risk_score.clip(upper=100)
    result["rule_reasons"] = [s.rstrip("|") for s in reasons]
    result["rule_review"] = result.risk_score.ge(config["risk_threshold"])
    return result


def rule_details(row, config):
    return [
        {**r, "observed_value": float(row[r["feature"]])}
        for r in config["rules"]
        if row[r["feature"]] >= r["threshold"]
    ]
