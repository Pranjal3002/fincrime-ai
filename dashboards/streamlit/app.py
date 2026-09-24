"""Six-page local analytics and investigation interface."""

import json

import pandas as pd
import plotly.express as px
import streamlit as st

from fincrime_ai.investigation import CaseStore, summarize
from fincrime_ai.settings import ARTIFACTS, DATA, REPORTS, ROOT

st.set_page_config(
    page_title="FinCrimeAI | Screening Analytics", page_icon="◈", layout="wide"
)
st.markdown(
    """<style>.stApp {background:#f4f7fb;} h1,h2,h3 {color:#102a43;} [data-testid='stMetric'] {background:white;padding:18px;border-radius:10px;border-top:3px solid #008b8b;} .block-container {padding-top:2rem;} </style>""",
    unsafe_allow_html=True,
)
st.sidebar.title("◈ FinCrimeAI")
st.sidebar.caption("FINANCIAL CRIME ANALYTICS LAB")
pages = [
    "Executive Overview",
    "Screening Analytics",
    "Payment Risk",
    "Statistical Analysis",
    "Model Performance",
    "Investigation Explorer",
]
page = st.sidebar.radio("Workspace", pages)
st.sidebar.info(
    "Synthetic data only. Educational simulation. Human review remains final."
)
if not (DATA / "processed/analytical_transactions.parquet").exists():
    st.warning("Run python scripts/run_all.py to generate the analytical dataset.")
    st.stop()


@st.cache_data
def load():
    return pd.read_parquet(DATA / "processed/analytical_transactions.parquet")


def report(name):
    return json.loads((REPORTS / name).read_text())


frame = load()
st.title(page)
st.caption("FinCrimeAI / Synthetic payments / 90-day observation window / GBP")
channels = st.sidebar.multiselect(
    "Payment channels",
    sorted(frame.payment_channel.unique()),
    default=sorted(frame.payment_channel.unique()),
)
data = frame[frame.payment_channel.isin(channels)]
if data.empty:
    st.info("Select at least one channel.")
    st.stop()
daily = (
    data.groupby(data.timestamp.dt.date)
    .agg(transactions=("transaction_id", "size"), alerts=("alert_flag", "sum"))
    .reset_index()
)

if page == "Executive Overview":
    cols = st.columns(4)
    for col, label, value in zip(
        cols,
        ["Payments screened", "Review alerts", "Alert rate", "Average rule score"],
        [
            f"{len(data):,}",
            f"{data.alert_flag.sum():,}",
            f"{data.alert_flag.mean():.1%}",
            f"{data.risk_score.mean():.1f} / 100",
        ],
    ):
        col.metric(label, value)
    st.subheader("Review demand over time")
    st.plotly_chart(
        px.area(daily, x="timestamp", y="alerts", color_discrete_sequence=["#087e8b"]),
        width="stretch",
    )
    left, right = st.columns(2)
    with left:
        st.subheader("Payment channels")
        counts = (
            data.groupby("payment_channel")
            .alert_flag.mean()
            .reset_index(name="alert_rate")
        )
        st.plotly_chart(
            px.bar(
                counts,
                x="payment_channel",
                y="alert_rate",
                color_discrete_sequence=["#214d72"],
            ),
            width="stretch",
        )
    with right:
        st.subheader("Operational context")
        st.write(
            "An alert requests investigation; it does not establish wrongdoing. Combined alerts include model, rule and synthetic name-screening signals."
        )
        st.write(
            "Reviewed false-positive rate: unavailable until human dispositions are recorded."
        )
        st.caption(
            "Whole-dataset operations include training predictions. Held-out evaluation appears on Model Performance."
        )
elif page == "Screening Analytics":
    metrics = report("screening_metrics.json")["transaction_weighted"]
    cols = st.columns(4)
    for col, key in zip(cols, ["precision", "recall", "f1", "false_positive_rate"]):
        col.metric(key.replace("_", " ").title(), f"{metrics[key]:.2%}")
    st.caption(
        "Metrics cover the full synthetic benchmark; channel filters affect charts only."
    )
    left, right = st.columns(2)
    with left:
        st.plotly_chart(
            px.histogram(
                data,
                x="screening_score",
                nbins=35,
                title="Synthetic reference similarity",
                color_discrete_sequence=["#087e8b"],
            ),
            width="stretch",
        )
    with right:
        reasons = (
            data.loc[data.alert_flag, "rule_reasons"]
            .str.split("|")
            .explode()
            .value_counts()
            .rename_axis("reason")
            .reset_index(name="alerts")
        )
        reasons = reasons[reasons.reason.ne("")]
        st.plotly_chart(
            px.bar(
                reasons,
                x="alerts",
                y="reason",
                orientation="h",
                title="Triggered controls",
                color_discrete_sequence=["#214d72"],
            ),
            width="stretch",
        )
    st.dataframe(
        data[
            [
                "transaction_id",
                "counterparty_name",
                "matched_entity",
                "screening_score",
                "recommendation",
            ]
        ].head(100),
        hide_index=True,
    )
elif page == "Payment Risk":
    geography = (
        data.groupby("destination_country")
        .agg(
            payments=("transaction_id", "size"),
            alerts=("alert_flag", "sum"),
            average_risk=("risk_score", "mean"),
        )
        .reset_index()
    )
    st.subheader("Destination geography")
    st.caption(
        "XZ and QZ are fictional risk geographies, shown in a bar chart rather than mapped to real countries."
    )
    left, right = st.columns(2)
    with left:
        st.plotly_chart(
            px.bar(
                geography,
                x="destination_country",
                y="alerts",
                color="average_risk",
                color_continuous_scale="Teal",
            ),
            width="stretch",
        )
    with right:
        st.plotly_chart(
            px.scatter(
                data.sample(min(2500, len(data)), random_state=42),
                x="amount",
                y="model_probability",
                color="alert_flag",
                log_x=True,
                title="Payment amount vs model score (sample)",
            ),
            width="stretch",
        )
    st.dataframe(geography, hide_index=True)
elif page == "Statistical Analysis":
    stats = report("statistics.json")
    st.caption(
        "Full-run statistics; channel filters do not recalculate inferential tests."
    )
    cols = st.columns(3)
    cols[0].metric(
        "Geography association / Cramer's V", f"{stats['chi_square']['cramers_v']:.3f}"
    )
    cols[1].metric(
        "Amount / rank-biserial", f"{stats['mann_whitney']['rank_biserial']:.3f}"
    )
    cols[2].metric("Amount vs rule risk / Spearman", f"{stats['spearman']['rho']:.3f}")
    st.warning(stats["interpretation"])
    st.plotly_chart(
        px.histogram(
            data,
            x="amount",
            color="alert_flag",
            nbins=80,
            range_x=[0, float(data.amount.quantile(0.99))],
            barmode="overlay",
            title="Payment distribution, display clipped at 99th percentile",
        ),
        width="stretch",
    )
    st.json(
        {k: stats[k] for k in ["chi_square", "mann_whitney", "alert_rate_wilson_95"]}
    )
elif page == "Model Performance":
    metrics = report("model_metrics.json")
    st.success(
        f"Selected model: {metrics['split']['selected_model']} | Held-out test: {metrics['split']['test_rows']:,} payments"
    )
    st.caption(
        "Full-run held-out metrics; channel filters do not change evaluation. PR-AUC is average precision."
    )
    comparison = pd.DataFrame(metrics["models"])
    st.dataframe(
        comparison[
            ["model", "precision", "recall", "f1", "roc_auc", "pr_auc_ap", "threshold"]
        ],
        hide_index=True,
    )
    left, right = st.columns(2)
    left.image(str(ROOT / "docs/images/05_confusion_matrix.png"))
    right.image(str(ROOT / "docs/images/06_feature_importance.png"))
    thresholds = pd.read_csv(REPORTS / "threshold_analysis.csv")
    st.plotly_chart(
        px.line(
            thresholds,
            x="threshold",
            y="validation_cost_5fn_plus_fp",
            color="model",
            title="Validation threshold cost: 5 × missed positives + false positives",
        ),
        width="stretch",
    )
elif page == "Investigation Explorer":
    store = CaseStore(ARTIFACTS / report("run_manifest.json")["cases_file"])
    status = st.selectbox("Case status", ["OPEN", "IN_REVIEW", "ESCALATED", "CLOSED"])
    records = store.list(limit=100, status=status)
    st.caption(
        "Live simulated workflow; first 100 cases in selected status. Channel filter does not apply to the live case store."
    )
    if not records:
        st.info("No cases in this status.")
        st.stop()
    chosen = st.selectbox("Alert", [r["alert_id"] for r in records])
    case = store.get(chosen)
    cols = st.columns(3)
    cols[0].metric("Rule risk", case["risk_score"])
    cols[1].metric("Status", case["status"])
    cols[2].metric("Alert type", case["alert_type"])
    st.info(summarize(case)["summary"])
    st.json(case["evidence"])
    st.caption(
        "XGBoost contributors are additive log-odds explanations of XGBoost, which may differ from the selected scoring model."
    )
    with st.form("human_review"):
        actor = st.text_input("Investigator identifier")
        notes = st.text_area("Evidence and review notes")
        target = st.selectbox("Next status", ["IN_REVIEW", "ESCALATED", "CLOSED"])
        disposition = st.selectbox(
            "Disposition on closure", ["CLEARED", "FALSE_POSITIVE", "FURTHER_REVIEW"]
        )
        reason = st.text_input("Closure reason code")
        if st.form_submit_button("Record human review"):
            try:
                store.update(
                    chosen,
                    target,
                    actor,
                    notes,
                    disposition if target == "CLOSED" else None,
                    reason or None,
                )
                st.success("Review and audit event recorded.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
st.caption(
    "This is an educational portfolio simulation and is not intended for production compliance, AML, sanctions, or financial-crime decisioning."
)
