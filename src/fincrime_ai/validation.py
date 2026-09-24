"""Fail-fast data contracts and reconciliation."""

import numpy as np


def validate(customers, counterparties, transactions):
    for frame, key in [
        (customers, "customer_id"),
        (counterparties, "counterparty_id"),
        (transactions, "transaction_id"),
    ]:
        if frame[key].isna().any() or frame[key].duplicated().any():
            raise ValueError(f"Invalid primary key: {key}")
    for key, dimension in [
        ("customer_id", customers),
        ("counterparty_id", counterparties),
    ]:
        if not transactions[key].isin(dimension[key]).all():
            raise ValueError(f"Orphan foreign key: {key}")
    if not (np.isfinite(transactions.amount).all() and (transactions.amount > 0).all()):
        raise ValueError("Amounts must be positive and finite")
    if transactions.timestamp.isna().any():
        raise ValueError("Missing timestamp")
    if not transactions.currency.eq("GBP").all():
        raise ValueError("Simulation expects GBP; FX conversion not implemented")
    return {
        "records": len(transactions),
        "amount_total": round(float(transactions.amount.sum()), 2),
        "orphan_keys": 0,
        "duplicate_keys": 0,
    }
