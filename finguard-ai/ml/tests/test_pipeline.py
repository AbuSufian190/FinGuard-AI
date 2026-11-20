"""ML pipeline tests: data gen, feature engineering, training, metrics, SHAP."""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.abspath(os.path.join(HERE, "..", "src"))
sys.path.insert(0, SRC)

from config import MODEL_FEATURES, TARGET_COLUMN  # noqa: E402
from features import engineer_features  # noqa: E402
from generate_synthetic_data import generate  # noqa: E402
from preprocessing import make_pipeline  # noqa: E402
from evaluate import compute_metrics  # noqa: E402
from sklearn.ensemble import RandomForestClassifier  # noqa: E402
from sklearn.model_selection import train_test_split  # noqa: E402


def test_generator_shape_and_fraud_only_on_eligible_types():
    df = generate(5000, fraud_rate=0.01, seed=1)
    assert len(df) == 5000
    assert df[TARGET_COLUMN].sum() > 0
    fraud_types = set(df.loc[df[TARGET_COLUMN] == 1, "type"].unique())
    assert fraud_types.issubset({"TRANSFER", "CASH_OUT"})


def test_engineer_features_columns_and_balance_error():
    df = generate(500, seed=2)
    X = engineer_features(df)
    assert list(X.columns) == MODEL_FEATURES
    assert not X.isna().any().any()
    # errorBalanceOrig = newbalanceOrig + amount - oldbalanceOrg
    expected = (df["newbalanceOrig"] + df["amount"] - df["oldbalanceOrg"]).values
    assert np.allclose(X["errorBalanceOrig"].values, expected)


def test_feature_engineering_is_deterministic():
    df = generate(300, seed=3)
    assert engineer_features(df).equals(engineer_features(df))


def test_training_and_prediction_consistency():
    df = generate(8000, fraud_rate=0.02, seed=4)
    X = engineer_features(df)
    y = df[TARGET_COLUMN].values
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3,
                                          stratify=y, random_state=0)
    pipe = make_pipeline(RandomForestClassifier(
        n_estimators=60, class_weight="balanced", random_state=0, n_jobs=-1))
    pipe.fit(Xtr, ytr)
    proba = pipe.predict_proba(Xte)[:, 1]
    m = compute_metrics(yte, proba)
    assert 0.0 <= m["pr_auc"] <= 1.0
    assert 0.0 <= m["roc_auc"] <= 1.0
    # prediction is reproducible for identical input
    assert np.allclose(proba, pipe.predict_proba(Xte)[:, 1])


def test_metrics_contains_expected_keys():
    y = np.array([0, 0, 1, 1])
    p = np.array([0.1, 0.2, 0.8, 0.9])
    m = compute_metrics(y, p)
    for k in ("pr_auc", "roc_auc", "precision", "recall", "f1",
              "confusion_matrix"):
        assert k in m


def test_shap_explainer_on_trained_model():
    df = generate(4000, fraud_rate=0.03, seed=5)
    X = engineer_features(df)
    y = df[TARGET_COLUMN].values
    pipe = make_pipeline(RandomForestClassifier(
        n_estimators=40, class_weight="balanced", random_state=0, n_jobs=-1))
    pipe.fit(X, y)
    from explain import FraudExplainer
    exp = FraudExplainer(pipe).explain(X.head(1), top_k=5)
    assert len(exp["top_features"]) == 5
    assert exp["method"] in {"shap", "importance"}
