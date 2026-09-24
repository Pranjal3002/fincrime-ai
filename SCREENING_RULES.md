# Screening and review controls

Authoritative configuration: [config/rules.json](config/rules.json).
Version: synthetic-rules-1.0; name matcher: synthetic-screen-1.0.

Names undergo Unicode decomposition, ASCII transliteration where possible, punctuation
removal, lowercase conversion and whitespace normalization. Non-Latin-only names can
normalize to empty and are rejected; multilingual coverage is limited.

Each active canonical name and pipe-delimited alias is compared using RapidFuzz ratio.
Score = 0.90 × name similarity + 5 for country agreement + 5 for entity-type agreement.
An exact match naturally yields similarity 100; aliases compete with canonical candidates.
The best candidate is retained, including when below threshold. REVIEW starts at 88/100;
otherwise CLEAR. Neither output is a sanctions determination. Country mismatches reduce
confidence but do not automatically suppress a review. The list has 20 synthetic entries,
50 positive counterparties and 10 constructed near-name negatives among 600 counterparties.

| Rule | Observable condition | Contribution |
|---|---|---:|
| R01 HIGH_AMOUNT_DEVIATION | Amount / synthetic expected amount ≥ 4 | 30 |
| R02 HIGH_RISK_GEOGRAPHY | Fictional XZ or QZ destination | 20 |
| R03 UNUSUAL_TIME | UTC hour < 5 | 10 |
| R04 VELOCITY_SPIKE | At least 4 earlier payments in 1 hour | 30 |
| R05 NEW_COUNTERPARTY | First observed beneficiary and amount ratio ≥ 2 | 20 |
| R06 WATCHLIST_SIMILARITY | Screening score ≥ 88 | 50 |
| R07 REPEATED_THRESHOLD_ADJACENT | At least 2 earlier payments in [9500,10000) GBP in 24 hours | 25 |

Score contributions are capped at 100. Rule review starts at 40. An alert is created when
any of rule review, model threshold or screening review is reached. Every rule includes
an identifier, severity, score and explanation; the API adds observed feature values.
The illustrative 10000 threshold is not a regulatory threshold or institution policy.

Velocity windows exclude simultaneous timestamps and current/future payments. Baseline
amount is a generated onboarding expectation, not a claimed historical median. First
beneficiary means first in the observed 90-day window, not necessarily lifetime-first.
Screening ground truth is excluded from features. Evaluation reports both entity-level
and transaction-weighted errors. Recall 1.0 on a constructed benchmark does not establish
real-world recall. Threshold changes require a rerun and human review of capacity tradeoffs.
