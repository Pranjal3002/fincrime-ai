# Compliance boundaries

This is an educational portfolio simulation and is not intended for production compliance, AML, sanctions, or financial-crime decisioning.

This project does **not** provide legal compliance advice, AML decisions, sanctions
determinations, customer risk decisions or regulatory certification. It is not affiliated
with or endorsed by any bank and does not reproduce proprietary detection policies.

It demonstrates data science, screening analytics, explainable risk signals, operational
analytics, traceability, auditability and human-in-the-loop workflows. All customers,
accounts, counterparties and payments are synthetic. The watchlist is generated locally.
Real country codes do not denote actual sanctions status; XZ/QZ are fictional risk regions.

CLEAR means that this simulation's screening threshold was not reached; it is not a legal
clearance. REVIEW means evidence should be inspected by a human. A synthetic truth flag
is a benchmark label, not a designation about a real entity. A closed case is a simulated
human disposition and says nothing about regulatory obligations.

The assistant can only summarize structured evidence. It cannot update case status or
decide legal/compliance outcomes. The default mode is deterministic, with strict fallback
when supplied prose does not match the evidence-backed template. No paid LLM API is used.

Run services only on 127.0.0.1. This demonstration lacks production authentication,
authorization, tamper-proof audit storage, retention enforcement, security monitoring and
independent model validation. Do not ingest real PII, customer data or confidential lists.
