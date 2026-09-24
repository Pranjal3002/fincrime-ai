"""Generate figures and executive narratives strictly from measured results."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from fincrime_ai.settings import REPORTS, ROOT


def markdown_table(frame):
    columns = list(frame.columns)
    lines = [
        "| " + " | ".join(columns) + " |",
        "|" + "|".join(["---"] * len(columns)) + "|",
    ]
    for row in frame.itertuples(index=False, name=None):
        lines.append(
            "| "
            + " | ".join(f"{v:.4f}" if isinstance(v, float) else str(v) for v in row)
            + " |"
        )
    return "\n".join(lines)


def report(frame, result, summary, stats, screening):
    images = ROOT / "docs/images"
    images.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update(
        {
            "figure.facecolor": "#f3f6fb",
            "axes.facecolor": "white",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "font.size": 11,
        }
    )
    selected = (
        result["comparison"].set_index("model").loc[result["split"]["selected_model"]]
    )
    matrix = np.array(
        [[selected.tn, selected.fp], [selected.fn, selected.tp]], dtype=int
    )
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.imshow(matrix, cmap="Blues")
    for (i, j), value in np.ndenumerate(matrix):
        ax.text(
            j,
            i,
            f"{value:,}",
            ha="center",
            va="center",
            fontsize=22,
            color="white" if value > matrix.max() / 2 else "#112b49",
        )
    ax.set(
        xticks=[0, 1],
        yticks=[0, 1],
        xticklabels=["No review", "Review"],
        yticklabels=["Negative", "Positive"],
        xlabel="Predicted",
        ylabel="Synthetic truth",
        title=f"Held-out test | {result['split']['selected_model']}",
    )
    fig.tight_layout()
    fig.savefig(images / "05_confusion_matrix.png", dpi=160)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(10, 5))
    importance = result["importance"].head(10).sort_values("importance")
    ax.barh(importance.feature, importance.importance, color="#087e8b")
    ax.set_title(f"Global feature importance | {result['split']['selected_model']}")
    ax.set_xlabel(
        "Tree importance or absolute standardized coefficient; not causal effect"
    )
    fig.tight_layout()
    fig.savefig(images / "06_feature_importance.png", dpi=160)
    plt.close(fig)
    model_table = markdown_table(
        result["comparison"][
            ["model", "precision", "recall", "f1", "roc_auc", "pr_auc_ap", "threshold"]
        ]
    )
    metrics = screening["transaction_weighted"]
    report_text = f"""# Executive Financial Crime Analytics Report

## Executive Summary
FinCrimeAI processed {len(frame):,} entirely synthetic payments and generated {int(summary['alerts']):,} review alerts ({summary['alert_rate']:.2%}). These are investigation signals, not findings of crime. Human review remains final.

## Dataset Overview
Seed 42 is the default; this run's seed is recorded in run_manifest.json. There are {frame.customer_id.nunique():,} observed customers across 90 simulated days, all amounts in GBP. Customer/account and counterparty identifiers are fictional. XZ and QZ are fictional risk geographies. Controlled injected patterns and probabilistic labels support evaluation but cannot establish real-world effectiveness.

## Screening Performance
Transaction-weighted precision {metrics['precision']:.4f}; recall {metrics['recall']:.4f}; F1 {metrics['f1']:.4f}; false-positive rate {metrics['false_positive_rate']:.4f}; false-negative rate {metrics['false_negative_rate']:.4f}. Repeated counterparties are not independent tests. See screening_metrics.json for unique-entity results. Near-name hard negatives deliberately test ambiguity.

## Transaction Risk Trends
Average rule score: {summary['average_risk_score']:.2f}/100. Median payment: GBP {stats['amount_description']['50%']:,.2f}; 99th percentile: GBP {stats['amount_description']['99%']:,.2f}. Screening, rule and model alerts are combined using OR, so operational workload is higher than any single component.

## Key Statistical Findings
Geography/alert chi-square = {stats['chi_square']['statistic']:.2f}, p = {stats['chi_square']['p_value']:.3g}, Cramer's V = {stats['chi_square']['cramers_v']:.3f}; minimum expected cell = {stats['chi_square']['min_expected_count']:.1f}.
Mann-Whitney p = {stats['mann_whitney']['p_value']:.3g}, rank-biserial effect = {stats['mann_whitney']['rank_biserial']:.3f}. Alerted/nonalerted median amounts: GBP {stats['mann_whitney']['alerted_median']:.2f} / {stats['mann_whitney']['nonalerted_median']:.2f}.
Amount/rule-score Spearman rho = {stats['spearman']['rho']:.3f}. Approximate Wilson 95% alert-rate interval: [{stats['alert_rate_wilson_95'][0]:.2%}, {stats['alert_rate_wilson_95'][1]:.2%}]. A serialized p-value of zero indicates floating-point underflow, not impossibility.
{stats['interpretation']}

## Model Performance
Chronological train/validation/test rows: {result['split']['train_rows']:,}/{result['split']['validation_rows']:,}/{result['split']['test_rows']:,}. Three expanding-window CV folds use training data only. Selection and thresholds minimize validation cost 5*FN + FP, an illustrative preference rather than an approved policy. PR-AUC is reported as average precision (AP), not trapezoidal area.

{model_table}

## False Positive / False Negative Tradeoff
The selected {result['split']['selected_model']} has {int(selected.fp):,} false positives and {int(selected.fn):,} false negatives on held-out payments. Lowering thresholds increases review capacity demands; missed positives remain possible. Costs must be determined by human stakeholders. Inspect threshold_analysis.csv before adopting any operating point.

## Operational Findings
Cases begin OPEN; no investigator dispositions are fabricated. Actual reviewed false-positive rates are unavailable until reviewers close cases. Ground-truth FPR is distinct from the fraction of reviews that are false positives (1 - precision). Warehouse status is a pipeline snapshot; the API reads the live SQLite case store.

## Recommendations
1. Review ambiguous entity matches with country and alias evidence.
2. Assess daily queue capacity alongside missed-positive counts before threshold changes.
3. Require temporal and customer-separated external validation before any generalization claim.
4. Investigate label construction and dependency effects before interpreting statistical significance.

## Limitations
Synthetic patterns, probabilistic labels, 90-day horizon, simplified customer baselines and no real payment connections. Model features can identify injected patterns; measured accuracy is simulation-specific. Whole-dataset dashboard predictions include training rows; only the model page reports held-out metrics. No native Power BI/Tableau dashboard is claimed without validation.

## Governance / Human Review
This is an educational portfolio simulation and is not intended for production compliance, AML, sanctions, or financial-crime decisioning.
Rules and model versions are recorded; human review transitions produce transactional audit records. Summaries cite evidence fields and cannot change case state.
"""
    (REPORTS / "EXECUTIVE_FINCRIME_ANALYTICS_REPORT.md").write_text(
        report_text, encoding="utf-8"
    )
    slides = [
        (
            "Problem / objective",
            "Prioritize synthetic payment reviews with reproducible evidence, without making compliance decisions.",
        ),
        (
            "Payment and data architecture",
            "Payer → originating bank → network → receiving bank → beneficiary. Synthetic data → validation → features → DuckDB → screening/models → case store → API and BI.",
        ),
        (
            "Screening approach",
            f"Exact, alias and fuzzy comparison with country/entity context. Precision {metrics['precision']:.3f}; recall {metrics['recall']:.3f}. Human review required.",
        ),
        (
            "Statistical findings",
            f"Cramer's V {stats['chi_square']['cramers_v']:.3f}; rank-biserial {stats['mann_whitney']['rank_biserial']:.3f}. Association is partly designed into rules; repeated payments limit inferential validity.",
        ),
        ("ML model comparison", model_table),
        (
            "Dashboard / operational insights",
            f"{len(frame):,} payments; {int(summary['alerts']):,} alerts. Distinguish ground-truth error rates from reviewer dispositions.",
        ),
        (
            "Explainability / investigation",
            "Versioned rule evidence, global importance and native XGBoost additive log-odds contributors. Evidence-backed deterministic summaries; no autonomous decisions.",
        ),
        (
            "Controls and governance",
            "Synthetic data only, chronological validation, enforced foreign keys, human workflow and transactional audit trail. Local demonstration without authentication; bind to loopback.",
        ),
        (
            "Business recommendations",
            "Tune against reviewer capacity; inspect misses; obtain independent labels and validate on future populations before drawing broader conclusions.",
        ),
    ]
    (REPORTS / "FINCRIME_EXECUTIVE_PRESENTATION.md").write_text(
        "# FinCrimeAI | Executive Presentation\n\n"
        + "\n\n---\n\n".join(
            f"## {i}. {title}\n\n{body}" for i, (title, body) in enumerate(slides, 1)
        ),
        encoding="utf-8",
    )
