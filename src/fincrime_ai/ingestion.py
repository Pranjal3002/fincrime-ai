"""Seeded, entirely fictional entities and payments; labels never enter features."""

import numpy as np
import pandas as pd

COUNTRIES = np.array(["GB", "IN", "US", "DE", "SG", "XZ", "QZ"])


def generate(n=100_000, seed=42, customer_count=2000, counterparty_count=600):
    if n < 100 or customer_count < 10 or counterparty_count < 60:
        raise ValueError(
            "Use >=100 transactions, >=10 customers and >=60 counterparties"
        )
    rng = np.random.default_rng(seed)
    customers = pd.DataFrame(
        {
            "customer_id": np.arange(customer_count),
            "account_id": [f"SYN-ACCOUNT-{i:05}" for i in range(customer_count)],
            "account_age_days": rng.integers(10, 3000, customer_count),
            "customer_type": rng.choice(["PERSON", "BUSINESS"], customer_count),
            "residence_country": rng.choice(COUNTRIES[:5], customer_count),
            "industry": rng.choice(
                ["RETAIL", "SERVICES", "TECHNOLOGY"], customer_count
            ),
            "risk_segment": rng.choice(["LOW", "MEDIUM", "HIGH"], customer_count),
            "kyc_status": rng.choice(
                ["COMPLETE", "PENDING"], customer_count, p=[0.96, 0.04]
            ),
            "pep_flag": rng.random(customer_count) < 0.02,
            "expected_monthly_volume": rng.integers(10, 100, customer_count),
            "expected_amount": rng.uniform(150, 1800, customer_count),
        }
    )
    customers["expected_min"] = customers.expected_amount * 0.2
    customers["expected_max"] = customers.expected_amount * 3
    watchlist = pd.DataFrame(
        [
            {
                "entity_id": i,
                "canonical_name": f"Fictional Zorvex {word} Trading",
                "aliases": f"Zorvex {word} Holdings",
                "country": COUNTRIES[i % 7],
                "entity_type": "BUSINESS",
                "sanctions_program": "SYNTHETIC-DEMO",
                "source": "GENERATED",
                "active": True,
            }
            for i, word in enumerate(
                [
                    "Amber",
                    "Birch",
                    "Cobalt",
                    "Delta",
                    "Ember",
                    "Flint",
                    "Garnet",
                    "Harbor",
                    "Indigo",
                    "Juniper",
                    "Kestrel",
                    "Linden",
                    "Marble",
                    "Nimbus",
                    "Opal",
                    "Pine",
                    "Quartz",
                    "Russet",
                    "Saffron",
                    "Topaz",
                ]
            )
        ]
    )
    counterparties = pd.DataFrame(
        {
            "counterparty_id": np.arange(counterparty_count),
            "counterparty_name": [
                f"Synthetic Merchant {i:04} Services" for i in range(counterparty_count)
            ],
            "aliases": "",
            "country": rng.choice(COUNTRIES, counterparty_count),
            "counterparty_type": "BUSINESS",
            "baseline_risk": rng.choice(["LOW", "MEDIUM"], counterparty_count),
            "synthetic_sanctions_flag": False,
        }
    )
    for i in range(50):
        w = watchlist.iloc[i % 20]
        name = (
            w.canonical_name
            if i < 20
            else w.aliases if i < 40 else w.canonical_name.replace("Trading", "Trding")
        )
        counterparties.loc[
            i, ["counterparty_name", "country", "synthetic_sanctions_flag"]
        ] = [name, w.country, True]
    # Hard negatives: similar names are not ground-truth reference entities.
    for i in range(50, 60):
        counterparties.loc[i, "counterparty_name"] = (
            watchlist.iloc[i % 20].canonical_name + " Services"
        )
    cid = rng.integers(0, customer_count, n)
    cp = rng.integers(0, counterparty_count, n)
    times = np.sort(rng.integers(0, 90 * 86400, n))
    pattern = rng.choice(
        [
            "ordinary",
            "deviation",
            "velocity",
            "geography",
            "new_beneficiary",
            "night",
            "threshold",
            "change",
        ],
        n,
        p=[0.9, 0.02, 0.01, 0.015, 0.015, 0.015, 0.015, 0.01],
    )
    baseline = customers.expected_amount.to_numpy()[cid]
    amount = baseline * rng.lognormal(-0.2, 0.75, n)
    amount[np.isin(pattern, ["deviation", "new_beneficiary", "change"])] *= rng.uniform(
        3, 8, np.isin(pattern, ["deviation", "new_beneficiary", "change"]).sum()
    )
    amount[pattern == "threshold"] = rng.uniform(
        9500, 9999, (pattern == "threshold").sum()
    )
    destination = counterparties.country.to_numpy()[cp].copy()
    destination[pattern == "geography"] = "XZ"
    times[pattern == "night"] = (times[pattern == "night"] // 86400) * 86400 + 3600
    # Real sequences, not independent velocity flags. Preserve existing labels on neighbors.
    for i in np.flatnonzero(np.isin(pattern, ["velocity", "threshold", "change"]))[::4]:
        stop = min(i + 5, n)
        cid[i:stop] = cid[i]
        times[i:stop] = times[i] + np.arange(stop - i) * 60
        pattern[i:stop] = pattern[i]
        if pattern[i] == "threshold":
            amount[i:stop] = rng.uniform(9500, 9999, stop - i)
        if pattern[i] == "change":
            amount[i:stop] = customers.expected_amount.iloc[cid[i]] * rng.uniform(
                4, 8, stop - i
            )
    tx = pd.DataFrame(
        {
            "transaction_id": [f"SYN-TX-{i:07}" for i in range(n)],
            "customer_id": cid,
            "counterparty_id": cp,
            "timestamp": pd.Timestamp("2026-01-01", tz="UTC")
            + pd.to_timedelta(times, unit="s"),
            "amount": amount.round(2),
            "currency": "GBP",
            "origin_country": customers.residence_country.to_numpy()[cid],
            "destination_country": destination,
            "payment_channel": rng.choice(["MOBILE", "WEB", "BRANCH", "API"], n),
            "payment_type": rng.choice(["TRANSFER", "CARD", "WIRE"], n),
            "payment_category": rng.choice(["RETAIL", "SERVICES", "REMITTANCE"], n),
            "device_id": [f"SYN-DEVICE-{x}" for x in cid],
            "originating_bank": "SYNTHETIC ORIGIN BANK",
            "network": "SIMULATED NETWORK",
            "beneficiary_bank": "SYNTHETIC RECEIVING BANK",
            "status": rng.choice(
                ["SETTLED", "PENDING", "FAILED"], n, p=[0.94, 0.04, 0.02]
            ),
            "injected_pattern": pattern,
        }
    )
    tx["screening_truth"] = counterparties.synthetic_sanctions_flag.to_numpy()[
        cp
    ].astype(int)
    # Probabilistic labels avoid claiming that heuristic replication is real crime detection.
    probability = np.where(pattern != "ordinary", 0.78, 0.025)
    probability = np.where(tx.screening_truth == 1, 0.9, probability)
    tx["investigation_label"] = (rng.random(n) < probability).astype(int)
    tx = tx.sort_values(["timestamp", "transaction_id"]).reset_index(drop=True)
    return customers, counterparties, tx, watchlist
