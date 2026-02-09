"""
Multi-output classification model for valve datasheet prediction.

Uses a separate gradient-boosting classifier per target field,
wrapped in a unified API for training, prediction, and evaluation.
"""

import json
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, classification_report

from .data_preparation import TARGET_FIELDS, DatasetBuilder


class ValveDatasheetModel:
    """
    Multi-output model that predicts all datasheet fields from VDS features.

    Each target field gets its own GradientBoostingClassifier.
    Fields with only one unique value in training data get a constant predictor.
    """

    def __init__(self, n_estimators: int = 200, max_depth: int = 5, learning_rate: float = 0.1):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.models: dict[str, object] = {}
        self.constant_values: dict[str, int] = {}
        self._is_trained = False

    def fit(self, X: np.ndarray, y: np.ndarray, verbose: bool = True) -> dict:
        """
        Train a separate classifier for each target field.

        Args:
            X: Input features (n_samples, n_features)
            y: Target labels (n_samples, n_fields)
            verbose: Print progress

        Returns:
            dict of field_name -> training accuracy
        """
        train_acc = {}

        for i, field in enumerate(TARGET_FIELDS):
            y_col = y[:, i]
            n_classes = len(np.unique(y_col))

            if n_classes <= 1:
                # Only one class -> constant predictor
                self.constant_values[field] = int(y_col[0])
                train_acc[field] = 1.0
                if verbose:
                    print(f"  [{i+1:2d}/{len(TARGET_FIELDS)}] {field:30s} -> constant (1 class)")
                continue

            # Use RandomForest for fields with many classes, GBM for fewer
            if n_classes > 20:
                clf = RandomForestClassifier(
                    n_estimators=self.n_estimators,
                    max_depth=self.max_depth,
                    random_state=42,
                    n_jobs=-1,
                )
            else:
                clf = GradientBoostingClassifier(
                    n_estimators=self.n_estimators,
                    max_depth=self.max_depth,
                    learning_rate=self.learning_rate,
                    random_state=42,
                )

            clf.fit(X, y_col)
            self.models[field] = clf

            acc = accuracy_score(y_col, clf.predict(X))
            train_acc[field] = acc

            if verbose:
                print(f"  [{i+1:2d}/{len(TARGET_FIELDS)}] {field:30s} -> {n_classes:3d} classes, train_acc={acc:.3f}")

        self._is_trained = True
        return train_acc

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict all target fields.

        Args:
            X: Input features (n_samples, n_features)

        Returns:
            2D numpy array (n_samples, n_fields) of encoded labels
        """
        if not self._is_trained:
            raise RuntimeError("Model not trained. Call fit() first.")

        n_samples = X.shape[0]
        predictions = np.zeros((n_samples, len(TARGET_FIELDS)), dtype=int)

        for i, field in enumerate(TARGET_FIELDS):
            if field in self.constant_values:
                predictions[:, i] = self.constant_values[field]
            else:
                predictions[:, i] = self.models[field].predict(X)

        return predictions

    def predict_proba(self, X: np.ndarray) -> dict[str, np.ndarray]:
        """
        Get prediction probabilities per field.

        Returns dict of field_name -> (n_samples, n_classes) probability array.
        """
        if not self._is_trained:
            raise RuntimeError("Model not trained. Call fit() first.")

        probas = {}
        for field in TARGET_FIELDS:
            if field in self.constant_values:
                probas[field] = np.ones((X.shape[0], 1))
            elif hasattr(self.models[field], "predict_proba"):
                probas[field] = self.models[field].predict_proba(X)
            else:
                probas[field] = None
        return probas

    def evaluate(self, X: np.ndarray, y: np.ndarray, dataset_builder: DatasetBuilder) -> dict:
        """
        Evaluate model on a dataset.

        Returns dict with:
            per_field: {field: {accuracy, f1, n_classes}}
            overall_accuracy: mean accuracy across fields
            exact_match_rate: fraction of samples with ALL fields correct
        """
        y_pred = self.predict(X)

        per_field = {}
        accuracies = []

        for i, field in enumerate(TARGET_FIELDS):
            y_true_col = y[:, i]
            y_pred_col = y_pred[:, i]

            acc = accuracy_score(y_true_col, y_pred_col)
            n_classes = len(np.unique(y_true_col))

            # Weighted F1 for multi-class
            f1 = f1_score(y_true_col, y_pred_col, average="weighted", zero_division=0)

            per_field[field] = {
                "accuracy": round(acc, 4),
                "f1_weighted": round(f1, 4),
                "n_classes": n_classes,
            }
            accuracies.append(acc)

        # Exact match: all fields correct for a sample
        exact_matches = np.all(y_pred == y, axis=1)
        exact_match_rate = float(np.mean(exact_matches))

        return {
            "per_field": per_field,
            "overall_accuracy": round(float(np.mean(accuracies)), 4),
            "exact_match_rate": round(exact_match_rate, 4),
            "n_samples": X.shape[0],
        }

    def save(self, path: Path) -> None:
        """Save model artifacts to directory."""
        path.mkdir(parents=True, exist_ok=True)

        # Save classifiers
        for field, clf in self.models.items():
            joblib.dump(clf, path / f"clf_{field}.joblib")

        # Save constants and metadata
        meta = {
            "constant_values": self.constant_values,
            "target_fields": TARGET_FIELDS,
            "n_estimators": self.n_estimators,
            "max_depth": self.max_depth,
            "learning_rate": self.learning_rate,
        }
        with open(path / "model_meta.json", "w") as f:
            json.dump(meta, f, indent=2)

    def load(self, path: Path) -> None:
        """Load model artifacts from directory."""
        with open(path / "model_meta.json", "r") as f:
            meta = json.load(f)

        self.constant_values = meta["constant_values"]
        self.n_estimators = meta["n_estimators"]
        self.max_depth = meta["max_depth"]
        self.learning_rate = meta["learning_rate"]

        # Load classifiers
        self.models = {}
        for field in TARGET_FIELDS:
            clf_path = path / f"clf_{field}.joblib"
            if clf_path.exists():
                self.models[field] = joblib.load(clf_path)

        self._is_trained = True
