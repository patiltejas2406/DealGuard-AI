"""Machine Learning Evaluation Metrics & Baseline Comparison Engine."""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
)


class ModelEvaluator:
    """Evaluates candidate ML models on held-out test splits against statistical baselines."""

    @staticmethod
    def evaluate_regression(
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_baseline: Optional[np.ndarray] = None,
    ) -> Dict[str, float]:
        """Compute comprehensive regression evaluation metrics."""
        y_true = np.asarray(y_true)
        y_pred = np.asarray(y_pred)

        mae = float(mean_absolute_error(y_true, y_pred))
        mse = float(mean_squared_error(y_true, y_pred))
        rmse = float(np.sqrt(mse))
        r2 = float(r2_score(y_true, y_pred))

        # Safe MAPE calculation avoiding zero division
        non_zeros = np.abs(y_true) > 1e-6
        if np.any(non_zeros):
            mape = float(np.mean(np.abs((y_true[non_zeros] - y_pred[non_zeros]) / y_true[non_zeros])))
        else:
            mape = 0.0

        metrics: Dict[str, float] = {
            "mae": round(mae, 4),
            "rmse": round(rmse, 4),
            "r2": round(r2, 4),
            "mape": round(mape, 4),
        }

        if y_baseline is not None:
            y_base = np.asarray(y_baseline)
            base_rmse = float(np.sqrt(mean_squared_error(y_true, y_base)))
            metrics["baseline_rmse"] = round(base_rmse, 4)
            if base_rmse > 1e-6:
                lift = max(0.0, (base_rmse - rmse) / base_rmse) * 100.0
                metrics["lift_over_baseline_pct"] = round(lift, 2)

        return metrics

    @staticmethod
    def evaluate_binary_classification(
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_prob: Optional[np.ndarray] = None,
        y_baseline: Optional[np.ndarray] = None,
    ) -> Dict[str, Any]:
        """Compute comprehensive binary classification evaluation metrics."""
        y_true = np.asarray(y_true)
        y_pred = np.asarray(y_pred)

        acc = float(accuracy_score(y_true, y_pred))
        prec = float(precision_score(y_true, y_pred, zero_division=0))
        rec = float(recall_score(y_true, y_pred, zero_division=0))
        f1 = float(f1_score(y_true, y_pred, zero_division=0))

        cm = confusion_matrix(y_true, y_pred)
        tn, fp, fn, tp = (int(cm[0, 0]), int(cm[0, 1]), int(cm[1, 0]), int(cm[1, 1])) if cm.shape == (2, 2) else (0, 0, 0, 0)

        metrics: Dict[str, Any] = {
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "true_negatives": tn,
            "false_positives": fp,
            "false_negatives": fn,
            "true_positives": tp,
        }

        if y_prob is not None:
            try:
                # If 2D probability matrix passed, select positive class probability
                if y_prob.ndim == 2:
                    prob_pos = y_prob[:, 1]
                else:
                    prob_pos = y_prob
                roc_auc = float(roc_auc_score(y_true, prob_pos))
                pr_auc = float(average_precision_score(y_true, prob_pos))
                brier = float(brier_score_loss(y_true, prob_pos))
                metrics["auc_roc"] = round(roc_auc, 4)
                metrics["pr_auc"] = round(pr_auc, 4)
                metrics["brier_score"] = round(brier, 4)
            except Exception:
                metrics["auc_roc"] = 0.5
                metrics["pr_auc"] = 0.0
                metrics["brier_score"] = 0.5

        if y_baseline is not None:
            y_base = np.asarray(y_baseline)
            base_acc = float(accuracy_score(y_true, y_base))
            metrics["baseline_accuracy"] = round(base_acc, 4)
            if base_acc > 0.0:
                lift = max(0.0, (acc - base_acc) / base_acc) * 100.0
                metrics["lift_over_baseline_pct"] = round(lift, 2)

        return metrics
