"""Exploratory tests on dependent synthetic payments, not causal inference."""

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, mannwhitneyu, spearmanr


def wilson(successes, n, z=1.96):
    p = successes / n
    center = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [float(center - half), float(center + half)]


def analyze(frame):
    table = pd.crosstab(frame.high_risk_geo, frame.alert_flag)
    chi, p, _, expected = chi2_contingency(table)
    yes = frame.loc[frame.alert_flag, "amount"]
    no = frame.loc[~frame.alert_flag, "amount"]
    u, up = mannwhitneyu(yes, no, alternative="two-sided")
    rho, rp = spearmanr(frame.amount, frame.risk_score)
    return {
        "amount_description": frame.amount.describe(
            percentiles=[0.5, 0.9, 0.99]
        ).to_dict(),
        "alert_rate": float(frame.alert_flag.mean()),
        "alert_rate_wilson_95": wilson(int(frame.alert_flag.sum()), len(frame)),
        "risk_score_description": frame.risk_score.describe().to_dict(),
        "geography_counts": frame.destination_country.value_counts().to_dict(),
        "channel_counts": frame.payment_channel.value_counts().to_dict(),
        "chi_square": {
            "statistic": float(chi),
            "p_value": float(p),
            "min_expected_count": float(expected.min()),
            "cramers_v": float(np.sqrt(chi / len(frame))),
            "table": table.to_dict(),
        },
        "mann_whitney": {
            "u": float(u),
            "p_value": float(up),
            "rank_biserial": float(2 * u / (len(yes) * len(no)) - 1),
            "alerted_median": float(yes.median()),
            "nonalerted_median": float(no.median()),
        },
        "spearman": {"rho": float(rho), "p_value": float(rp)},
        "interpretation": "Exploratory synthetic associations. Alerts directly use geography and amount, so association is partly designed into the system. Repeated customer payments violate independence; p-values and Wilson intervals are descriptive approximations, not population inference. Large samples can produce small p-values without large effects. Amount skew supports a rank test; it tests distributions, not necessarily medians.",
    }
