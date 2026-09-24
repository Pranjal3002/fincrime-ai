"""Point-in-time features; every rolling window excludes the current row."""

import numpy as np

NUMERIC = [
    "amount_ratio",
    "high_risk_geo",
    "night",
    "velocity_1h",
    "new_counterparty_high_value",
    "adjacent_prior_24h",
    "screening_score",
    "account_age_days",
    "pep_flag",
]
CATEGORICAL = ["payment_channel", "payment_type", "kyc_status"]
FEATURES = NUMERIC + CATEGORICAL


def build_features(tx, customers, counterparties, screened, config):
    frame = (
        tx.merge(customers, on="customer_id", validate="many_to_one")
        .merge(
            counterparties[["counterparty_id", "counterparty_name"]],
            on="counterparty_id",
            validate="many_to_one",
        )
        .merge(screened, on="counterparty_id", validate="many_to_one")
    )
    frame = frame.sort_values(["timestamp", "transaction_id"]).reset_index(drop=True)
    frame["amount_ratio"] = frame.amount / frame.expected_amount
    frame["high_risk_geo"] = frame.destination_country.isin(
        config["high_risk_countries"]
    ).astype(int)
    frame["night"] = (frame.timestamp.dt.hour < 5).astype(int)
    frame["new_counterparty"] = (
        frame.groupby(["customer_id", "counterparty_id"]).cumcount() == 0
    ).astype(int)
    frame["new_counterparty_high_value"] = (
        frame.new_counterparty.eq(1) & frame.amount_ratio.ge(2)
    ).astype(int)
    frame["velocity_1h"] = 0
    frame["adjacent_prior_24h"] = 0
    for _, group in frame.groupby("customer_id", sort=False):
        seconds = group.timestamp.dt.as_unit("ns").astype("int64").to_numpy() // 10**9
        # searchsorted(side=left) excludes all simultaneous payments to avoid order artifacts.
        end = np.searchsorted(seconds, seconds, side="left")
        start = np.searchsorted(seconds, seconds - 3600, side="left")
        frame.loc[group.index, "velocity_1h"] = end - start
        adjacent = (
            group.amount.between(9500, 10000, inclusive="left").astype(int).to_numpy()
        )
        cumulative = np.r_[0, np.cumsum(adjacent)]
        start_day = np.searchsorted(seconds, seconds - 86400, side="left")
        frame.loc[group.index, "adjacent_prior_24h"] = (
            cumulative[end] - cumulative[start_day]
        )
    return frame
