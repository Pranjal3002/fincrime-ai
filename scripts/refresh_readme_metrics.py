"""Refresh only marked README metric tables, preserving editorial documentation."""

import json
import re

from fincrime_ai.settings import REPORTS, ROOT


def main():
    models = json.loads((REPORTS / "model_metrics.json").read_text())
    screening = json.loads((REPORTS / "screening_metrics.json").read_text())[
        "transaction_weighted"
    ]
    names = {
        "LogisticRegression": "Logistic Regression",
        "RandomForest": "Random Forest",
        "XGBoost": "**XGBoost**",
    }
    model_rows = [
        "| Model | Precision | Recall | F1 | ROC-AUC | PR-AUC (AP) |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in models["models"]:
        values = " | ".join(
            f"{row[key]:.6f}"
            for key in ("precision", "recall", "f1", "roc_auc", "pr_auc_ap")
        )
        model_rows.append(f"| {names[row['model']]} | {values} |")
    screen_rows = ["| Metric | Result |", "|---|---:|"]
    for label, key in (
        ("Precision", "precision"),
        ("Recall", "recall"),
        ("F1", "f1"),
        ("False Positive Rate", "false_positive_rate"),
        ("False Negative Rate", "false_negative_rate"),
    ):
        screen_rows.append(f"| {label} | {screening[key]:.4f} |")
    path = ROOT / "README.md"
    content = path.read_text(encoding="utf-8")
    for marker, rows in (
        ("MODEL_RESULTS", model_rows),
        ("SCREENING_RESULTS", screen_rows),
    ):
        start = f"<!-- {marker}_START -->"
        end = f"<!-- {marker}_END -->"
        replacement = start + "\n\n" + "\n".join(rows) + "\n\n" + end
        content, count = re.subn(
            re.escape(start) + r".*?" + re.escape(end),
            lambda _, value=replacement: value,
            content,
            flags=re.DOTALL,
        )
        if count != 1:
            raise ValueError(f"Expected one {marker} block, found {count}")
    path.write_text(content, encoding="utf-8")
    print("Refreshed README tables from recorded metrics; editorial content preserved.")


if __name__ == "__main__":
    main()
