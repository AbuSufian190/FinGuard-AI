"""Evaluation metrics for imbalanced fraud detection."""
from __future__ import annotations

from typing import Dict

import numpy as np
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)


def compute_metrics(y_true, y_proba, threshold: float = 0.5) -> Dict:
    """Return the full metric set. accuracy is included for completeness but is
    never used as the selection criterion (see config.SELECTION_METRIC)."""
    y_pred = (np.asarray(y_proba) >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()

    return {
        "threshold": float(threshold),
        "pr_auc": float(average_precision_score(y_true, y_proba)),
        "roc_auc": float(roc_auc_score(y_true, y_proba)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "accuracy": float((tp + tn) / max(tp + tn + fp + fn, 1)),
        "confusion_matrix": {"tn": int(tn), "fp": int(fp),
                             "fn": int(fn), "tp": int(tp)},
    }


def roc_curve_points(y_true, y_proba, max_points: int = 200) -> Dict:
    fpr, tpr, _ = roc_curve(y_true, y_proba)
    idx = np.linspace(0, len(fpr) - 1, min(max_points, len(fpr))).astype(int)
    return {"fpr": fpr[idx].tolist(), "tpr": tpr[idx].tolist()}


def pr_curve_points(y_true, y_proba, max_points: int = 200) -> Dict:
    precision, recall, _ = precision_recall_curve(y_true, y_proba)
    idx = np.linspace(0, len(precision) - 1,
                      min(max_points, len(precision))).astype(int)
    return {"precision": precision[idx].tolist(),
            "recall": recall[idx].tolist()}


def best_f1_threshold(y_true, y_proba) -> float:
    """Pick the probability threshold that maximises F1 on the given data."""
    precision, recall, thresholds = precision_recall_curve(y_true, y_proba)
    f1 = 2 * precision * recall / (precision + recall + 1e-12)
    # thresholds has len = len(precision) - 1
    if len(thresholds) == 0:
        return 0.5
    return float(thresholds[int(np.argmax(f1[:-1]))])
