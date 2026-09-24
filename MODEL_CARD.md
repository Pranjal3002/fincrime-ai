# Model card — synthetic-risk-1.0

## Intended and excluded uses
Rank synthetic payments for educational human investigation. Not for AML, sanctions,
customer acceptance, legal advice or production compliance. This is an educational portfolio simulation and is not intended for production compliance, AML, sanctions, or financial-crime decisioning.

## Data and target
Seeded synthetic customers, counterparties and 90-day GBP payments. Probabilistic
investigation labels are influenced by injected scenarios and synthetic reference membership.
This is scenario recognition, not learning real financial crime. Labels/tags/IDs and review
outcomes are excluded from model features. Customers can repeat across temporal splits;
customer-generalization is not evaluated.

## Features and preprocessing
Amount / expected baseline, fictional risk geography, night flag, prior 1h velocity,
first observed beneficiary with high value, prior 24h threshold-adjacent count, observable
name similarity, account age, synthetic PEP flag, channel, payment type and KYC status.
Median/mode imputation, numeric scaling and one-hot encoding fit on training data only.
No target encoding, future counts or truth flags are used. Baselines are generated expected
amounts, not historical medians. Simultaneous transactions are excluded from each other's windows.

## Training, imbalance and evaluation
Train/validation/test 60000/20000/20000 by timestamp; train end 2026-02-23 23:40:09+00:00,
test starts 2026-03-13 20:51:14+00:00. Three temporal CV folds operate inside training.
Logistic/forest use balanced class weights; XGBoost weights negative/positive training counts.
Validation threshold tuning minimizes 5*FN + FP, an illustrative cost preference. Test data
is used only for final metrics. No SMOTE or repeated hyperparameter search is used.

| Model | Precision | Recall | F1 | ROC-AUC | PR-AUC (AP) | Threshold |
|---|---:|---:|---:|---:|---:|---:|
| Logistic Regression | 0.6274 | 0.7162 | 0.6689 | 0.8664 | 0.6864 | 0.5000 |
| Random Forest | 0.6138 | 0.7463 | 0.6736 | 0.8779 | 0.7274 | 0.4000 |
| **XGBoost** | 0.6964 | 0.7487 | 0.7216 | 0.8850 | 0.7471 | 0.4500 |

Full precision and confusion counts: [recorded metrics](reports/model_metrics.json). PR-AUC is AP. Selected
XGBoost at 0.45; test FN 927,
FP 1204. False negatives miss review-worthy synthetic labels; false positives
consume review capacity. Neither is evidence of a real compliance outcome.

## Explainability
Global tree importance (or absolute standardized coefficient) and rule contributions.
XGBoost native pred_contribs produces additive SHAP-style log-odds contributions, including
a bias term. Every analytical row stores its three largest absolute contributions. Maximum
additivity error: 5.2452087e-06.
Contributors describe XGBoost, not another selected estimator; this distinction is exposed.
Isolation Forest provides a separate unsupervised score, trained on the training period;
it does not drive case decisions and has no supervised performance claim.

## Bias, limitations and governance
Country, PEP/KYC flags and synthetic population assumptions can encode bias. No fairness
certification or subgroup validation is claimed. Geography association is partly built into
controls. Evaluate subgroup errors and independently sourced labels before any generalization.
Exact/near name synthetic matching is easier than multilingual real-world matching.
Human review remains final. Persisted joblib is a local trusted artifact only: never load
untrusted serialized models. Versions, seeds, input/control hashes and validation metrics are
recorded. Restart services after retraining. No drift monitoring or automated retraining is implemented.
