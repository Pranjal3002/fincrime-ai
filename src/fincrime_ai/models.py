"""Chronological evaluation with train-only preprocessing and validation tuning."""

import time

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBClassifier

from fincrime_ai.features import CATEGORICAL, FEATURES, NUMERIC


def metrics(y, probability, threshold):
    predicted = np.asarray(probability) >= threshold
    tn, fp, fn, tp = confusion_matrix(y, predicted, labels=[0, 1]).ravel()
    return {
        "precision": float(precision_score(y, predicted, zero_division=0)),
        "recall": float(recall_score(y, predicted, zero_division=0)),
        "f1": float(f1_score(y, predicted, zero_division=0)),
        "roc_auc": float(roc_auc_score(y, probability)) if len(set(y)) > 1 else None,
        "pr_auc_ap": float(average_precision_score(y, probability)),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
        "false_positive_rate": float(fp / max(tn + fp, 1)),
        "false_negative_rate": float(fn / max(tp + fn, 1)),
    }


def preprocessing():
    return ColumnTransformer(
        [
            (
                "numeric",
                Pipeline(
                    [
                        ("impute", SimpleImputer(strategy="median")),
                        ("scale", StandardScaler()),
                    ]
                ),
                NUMERIC,
            ),
            (
                "category",
                Pipeline(
                    [
                        ("impute", SimpleImputer(strategy="most_frequent")),
                        (
                            "encode",
                            OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                        ),
                    ]
                ),
                CATEGORICAL,
            ),
        ]
    )


def train(frame, seed=42):
    n = len(frame)
    a, b = int(n * 0.6), int(n * 0.8)
    # Move boundaries to whole timestamps, avoiding same-time train/test overlap.
    a = int(frame.timestamp.searchsorted(frame.timestamp.iloc[a], side="left"))
    b = int(frame.timestamp.searchsorted(frame.timestamp.iloc[b], side="left"))
    x, y = frame[FEATURES], frame.investigation_label
    estimators = {
        "LogisticRegression": LogisticRegression(
            max_iter=400, class_weight="balanced", random_state=seed
        ),
        "RandomForest": RandomForestClassifier(
            n_estimators=70,
            max_depth=10,
            min_samples_leaf=10,
            class_weight="balanced",
            n_jobs=2,
            random_state=seed,
        ),
        "XGBoost": XGBClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.08,
            subsample=0.85,
            colsample_bytree=0.9,
            n_jobs=2,
            random_state=seed,
            eval_metric="logloss",
            scale_pos_weight=float(
                (y.iloc[:a] == 0).sum() / max((y.iloc[:a] == 1).sum(), 1)
            ),
        ),
    }
    rows = []
    thresholds = []
    fitted = {}
    for name, estimator in estimators.items():
        model = Pipeline([("preprocess", preprocessing()), ("classifier", estimator)])
        start = time.perf_counter()
        model.fit(x.iloc[:a], y.iloc[:a])
        val = model.predict_proba(x.iloc[a:b])[:, 1]
        candidates = []
        for threshold in np.arange(0.1, 0.91, 0.05):
            score = metrics(y.iloc[a:b], val, float(threshold))
            cost = 5 * score["fn"] + score["fp"]
            candidates.append((cost, float(threshold), score))
            thresholds.append(
                {
                    "model": name,
                    "threshold": float(threshold),
                    "validation_cost_5fn_plus_fp": cost,
                    **score,
                }
            )
        _, chosen, val_metrics = min(candidates, key=lambda item: item[0])
        test = model.predict_proba(x.iloc[b:])[:, 1]
        cv = cross_val_score(
            model,
            x.iloc[:a],
            y.iloc[:a],
            cv=TimeSeriesSplit(n_splits=3),
            scoring="average_precision",
            n_jobs=1,
        )
        rows.append(
            {
                "model": name,
                "threshold": chosen,
                "validation_cost": 5 * val_metrics["fn"] + val_metrics["fp"],
                "cv_pr_auc_ap_mean": float(cv.mean()),
                "cv_pr_auc_ap_std": float(cv.std()),
                "fit_evaluation_seconds": time.perf_counter() - start,
                **metrics(y.iloc[b:], test, chosen),
            }
        )
        fitted[name] = model
    comparison = pd.DataFrame(rows)
    winner = comparison.sort_values(["validation_cost", "model"]).iloc[0]
    selected = fitted[winner.model]
    start = time.perf_counter()
    probabilities = selected.predict_proba(x)[:, 1]
    scoring_seconds = time.perf_counter() - start
    anomaly = IsolationForest(
        n_estimators=60, contamination=0.1, random_state=seed, n_jobs=2
    )
    anomaly.fit(x.iloc[:a][NUMERIC])
    anomaly_scores = -anomaly.score_samples(x[NUMERIC])
    names = selected.named_steps["preprocess"].get_feature_names_out()
    clf = selected.named_steps["classifier"]
    importance = (
        clf.feature_importances_
        if hasattr(clf, "feature_importances_")
        else abs(clf.coef_[0])
    )
    importance = pd.DataFrame({"feature": names, "importance": importance}).sort_values(
        "importance", ascending=False
    )
    # Exact additive XGBoost log-odds contributions; no optional SHAP dependency.
    import xgboost as xgb

    explanation_model = fitted["XGBoost"]
    transformed = explanation_model.named_steps["preprocess"].transform(x)
    contributions = (
        explanation_model.named_steps["classifier"]
        .get_booster()
        .predict(xgb.DMatrix(transformed), pred_contribs=True)
    )
    contribution_names = explanation_model.named_steps[
        "preprocess"
    ].get_feature_names_out()
    top = np.argsort(-np.abs(contributions[:, :-1]), axis=1)[:, :3]
    explanations = [
        "; ".join(f"{contribution_names[j]}={contributions[i,j]:+.3f}" for j in indices)
        for i, indices in enumerate(top)
    ]
    split = {
        "train_rows": a,
        "validation_rows": b - a,
        "test_rows": n - b,
        "train_end": str(frame.timestamp.iloc[a - 1]),
        "validation_start": str(frame.timestamp.iloc[a]),
        "validation_end": str(frame.timestamp.iloc[b - 1]),
        "test_start": str(frame.timestamp.iloc[b]),
        "selected_model": winner.model,
        "threshold": float(winner.threshold),
        "selection": "minimum validation 5*FN+FP; test never used for selection",
        "model_version": "synthetic-risk-1.0",
        "xgboost_contribution_additivity_max_error": float(
            np.max(
                np.abs(
                    contributions.sum(axis=1)
                    - explanation_model.named_steps["classifier"]
                    .get_booster()
                    .predict(xgb.DMatrix(transformed), output_margin=True)
                )
            )
        ),
    }
    return {
        "model": selected,
        "comparison": comparison,
        "thresholds": pd.DataFrame(thresholds),
        "probabilities": probabilities,
        "anomaly_scores": anomaly_scores,
        "importance": importance,
        "explanations": explanations,
        "split": split,
        "scoring_seconds": scoring_seconds,
    }
