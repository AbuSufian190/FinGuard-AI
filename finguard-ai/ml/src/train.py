"""
FinGuard AI – model training entry point.

Pipeline:
  1. Load data (synthetic dev data by default; pass --data for real PaySim CSV).
  2. Run lightweight EDA and persist a summary.
  3. Engineer features (pure, row-wise).
  4. Stratified train / validation / test split BEFORE any preprocessing fit
     (prevents data leakage).
  5. Train Logistic Regression, Random Forest, and XGBoost, each handling class
     imbalance via class weights / scale_pos_weight.
  6. Select the best model on the VALIDATION PR-AUC (documented metric).
  7. Tune the decision threshold on validation (max F1).
  8. Report FINAL metrics on the untouched TEST split.
  9. Serialise the winning pipeline, feature metadata, evaluation report and a
     model card; copy artifacts into the backend.

Run:  python -m src.train          (from the ml/ directory)
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

try:
    from . import config
    from .features import engineer_features
    from .preprocessing import make_pipeline
    from .evaluate import (compute_metrics, roc_curve_points, pr_curve_points,
                           best_f1_threshold)
    from .eda import run_eda
except ImportError:  # running as a script
    import config
    from features import engineer_features
    from preprocessing import make_pipeline
    from evaluate import (compute_metrics, roc_curve_points, pr_curve_points,
                          best_f1_threshold)
    from eda import run_eda

HERE = os.path.dirname(os.path.abspath(__file__))
ML_DIR = os.path.abspath(os.path.join(HERE, ".."))
ARTIFACTS = os.path.join(ML_DIR, "artifacts")
REPORTS = os.path.join(ML_DIR, "reports")
BACKEND_ARTIFACTS = os.path.abspath(
    os.path.join(ML_DIR, "..", "backend", "app", "ml", "artifacts")
)


def _build_models(y_train: np.ndarray) -> dict:
    n_pos = int((y_train == 1).sum())
    n_neg = int((y_train == 0).sum())
    scale_pos_weight = n_neg / max(n_pos, 1)
    return {
        "logistic_regression": LogisticRegression(
            max_iter=2000, class_weight="balanced",
            random_state=config.RANDOM_STATE, n_jobs=-1,
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=200, max_depth=16, min_samples_leaf=5,
            class_weight="balanced_subsample", n_jobs=-1,
            random_state=config.RANDOM_STATE,
        ),
        "xgboost": XGBClassifier(
            n_estimators=300, max_depth=6, learning_rate=0.1,
            subsample=0.9, colsample_bytree=0.9,
            scale_pos_weight=scale_pos_weight,
            eval_metric="aucpr", tree_method="hist",
            random_state=config.RANDOM_STATE, n_jobs=-1,
        ),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", default=None,
                    help="Path to a transactions CSV (PaySim schema). "
                         "Defaults to generating synthetic dev data.")
    ap.add_argument("--rows", type=int, default=120_000,
                    help="Synthetic rows if no --data given.")
    args = ap.parse_args()

    os.makedirs(ARTIFACTS, exist_ok=True)
    os.makedirs(REPORTS, exist_ok=True)
    os.makedirs(BACKEND_ARTIFACTS, exist_ok=True)

    # ---- 1. Load data -----------------------------------------------------
    synthetic = args.data is None
    if synthetic:
        try:
            from .generate_synthetic_data import generate
        except ImportError:
            from generate_synthetic_data import generate
        print(f"[data] generating {args.rows:,} SYNTHETIC rows (dev only)")
        df = generate(args.rows)
        data_source = "SYNTHETIC development data (not real PaySim)"
    else:
        print(f"[data] loading {args.data}")
        df = pd.read_csv(args.data)
        data_source = os.path.basename(args.data)

    # ---- 2. EDA -----------------------------------------------------------
    eda = run_eda(df)
    with open(os.path.join(REPORTS, "eda_summary.json"), "w") as f:
        json.dump(eda, f, indent=2)
    print(f"[eda] rows={eda['n_rows']:,} fraud_rate={eda['fraud_rate']:.4%}")

    # ---- 3. Features ------------------------------------------------------
    X = engineer_features(df)
    y = df[config.TARGET_COLUMN].astype(int).values

    # ---- 4. Stratified split (before any preprocessing fit) --------------
    X_tmp, X_test, y_tmp, y_test = train_test_split(
        X, y, test_size=0.20, stratify=y, random_state=config.RANDOM_STATE)
    X_train, X_val, y_train, y_val = train_test_split(
        X_tmp, y_tmp, test_size=0.20, stratify=y_tmp,
        random_state=config.RANDOM_STATE)
    print(f"[split] train={len(X_train):,} val={len(X_val):,} "
          f"test={len(X_test):,}")

    # ---- 5. Train + 6. select on validation PR-AUC -----------------------
    models = _build_models(y_train)
    report = {"models": {}, "selection_metric": config.SELECTION_METRIC,
              "data_source": data_source, "synthetic": synthetic}
    best_name, best_val, best_pipe = None, -1.0, None

    for name, est in models.items():
        print(f"[train] {name} ...")
        pipe = make_pipeline(est)
        pipe.fit(X_train, y_train)
        val_proba = pipe.predict_proba(X_val)[:, 1]
        val_metrics = compute_metrics(y_val, val_proba)
        report["models"][name] = {"validation": val_metrics}
        score = val_metrics[config.SELECTION_METRIC]
        print(f"        val {config.SELECTION_METRIC}={score:.4f} "
              f"roc_auc={val_metrics['roc_auc']:.4f}")
        if score > best_val:
            best_name, best_val, best_pipe = name, score, pipe

    # ---- 7. Threshold tuning on validation -------------------------------
    best_val_proba = best_pipe.predict_proba(X_val)[:, 1]
    threshold = best_f1_threshold(y_val, best_val_proba)
    print(f"[select] best={best_name} (val {config.SELECTION_METRIC}="
          f"{best_val:.4f}); tuned threshold={threshold:.4f}")

    # ---- 8. Final TEST evaluation for ALL models (for comparison UI) -----
    for name in models:
        pipe = make_pipeline(models[name]) if name != best_name else best_pipe
        if name != best_name:
            pipe.fit(X_train, y_train)  # refit for an honest test comparison
        test_proba = pipe.predict_proba(X_test)[:, 1]
        report["models"][name]["test"] = compute_metrics(
            y_test, test_proba, threshold)
        if name == best_name:
            sel_test_proba = test_proba

    report["selected_model"] = best_name
    report["decision_threshold"] = threshold
    report["test_roc_curve"] = roc_curve_points(y_test, sel_test_proba)
    report["test_pr_curve"] = pr_curve_points(y_test, sel_test_proba)
    report["generated_at"] = datetime.now(timezone.utc).isoformat()

    sel_test = report["models"][best_name]["test"]
    print(f"[test] {best_name}: pr_auc={sel_test['pr_auc']:.4f} "
          f"roc_auc={sel_test['roc_auc']:.4f} f1={sel_test['f1']:.4f} "
          f"precision={sel_test['precision']:.4f} "
          f"recall={sel_test['recall']:.4f}")

    # ---- 9. Persist artifacts --------------------------------------------
    model_path = os.path.join(ARTIFACTS, "model.joblib")
    joblib.dump(best_pipe, model_path)

    feature_metadata = {
        "model_features": config.MODEL_FEATURES,
        "numeric_features": config.NUMERIC_FEATURES,
        "categorical_features": config.CATEGORICAL_FEATURES,
        "raw_input_columns": config.RAW_COLUMNS,
        "transaction_types": config.TRANSACTION_TYPES,
        "decision_threshold": threshold,
    }
    with open(os.path.join(ARTIFACTS, "feature_metadata.json"), "w") as f:
        json.dump(feature_metadata, f, indent=2)

    model_card = {
        "model_name": best_name,
        "model_version": datetime.now(timezone.utc).strftime("v%Y.%m.%d"),
        "trained_at": report["generated_at"],
        "selection_metric": config.SELECTION_METRIC,
        "validation_score": best_val,
        "decision_threshold": threshold,
        "data_source": data_source,
        "synthetic_data": synthetic,
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "note": ("Metrics computed on SYNTHETIC development data; NOT real "
                 "PaySim benchmark results." if synthetic else
                 "Metrics computed on provided dataset."),
    }
    with open(os.path.join(ARTIFACTS, "model_card.json"), "w") as f:
        json.dump(model_card, f, indent=2)

    with open(os.path.join(REPORTS, "evaluation_report.json"), "w") as f:
        json.dump(report, f, indent=2)

    # ship artifacts to the backend (best-effort: the backend tree may not be
    # present, e.g. inside a standalone training container).
    try:
        for fn in ("model.joblib", "feature_metadata.json", "model_card.json"):
            shutil.copy2(os.path.join(ARTIFACTS, fn),
                         os.path.join(BACKEND_ARTIFACTS, fn))
        shutil.copy2(os.path.join(REPORTS, "evaluation_report.json"),
                     os.path.join(BACKEND_ARTIFACTS, "evaluation_report.json"))
        print(f"[done] copied artifacts -> {BACKEND_ARTIFACTS}")
    except (FileNotFoundError, OSError) as exc:
        print(f"[warn] could not copy to backend tree ({exc}); "
              f"artifacts remain in {ARTIFACTS}")

    print(f"[done] saved model -> {model_path}")


if __name__ == "__main__":
    main()
