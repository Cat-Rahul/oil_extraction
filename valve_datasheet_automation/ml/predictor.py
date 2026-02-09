"""
Prediction service for the trained ML model.

Provides a high-level API: VDS number in -> predicted datasheet fields out.
"""

import json
import numpy as np
import joblib
from pathlib import Path

from .data_preparation import (
    parse_vds_features,
    INPUT_FEATURES_CAT,
    INPUT_FEATURES_NUM,
    TARGET_FIELDS,
    DatasetBuilder,
)
from .model import ValveDatasheetModel


class ValvePredictor:
    """
    High-level predictor: takes a VDS number, returns predicted field values.

    Usage:
        predictor = ValvePredictor()
        predictor.load()
        result = predictor.predict("BSFA1R")
        # result = {"valve_type": "Ball Valve, Full Bore", "body_material": "...", ...}
    """

    def __init__(self, model_dir: Path = None):
        if model_dir is None:
            model_dir = Path(__file__).parent / "trained_model"
        self.model_dir = model_dir
        self.model: ValveDatasheetModel = None
        self.input_encoders: dict = None
        self.label_encoders: dict = None
        self._loaded = False

    @property
    def is_available(self) -> bool:
        """Check if a trained model exists."""
        return (self.model_dir / "model_meta.json").exists()

    def load(self) -> None:
        """Load trained model and encoders."""
        if not self.is_available:
            raise FileNotFoundError(
                f"No trained model found at {self.model_dir}. "
                "Run: python -m valve_datasheet_automation.ml.train"
            )

        self.model = ValveDatasheetModel()
        self.model.load(self.model_dir)

        self.input_encoders = joblib.load(self.model_dir / "input_encoders.joblib")
        self.label_encoders = joblib.load(self.model_dir / "label_encoders.joblib")
        self._loaded = True

    def _encode_vds(self, vds_no: str) -> np.ndarray:
        """Parse and encode a single VDS number into feature vector."""
        features = parse_vds_features(vds_no)

        encoded_parts = []
        for col in INPUT_FEATURES_CAT:
            val = str(features[col])
            enc = self.input_encoders[col]
            known = set(enc.classes_)
            if val not in known:
                val = enc.classes_[0]  # fallback
            encoded_parts.append(enc.transform([val]))

        for col in INPUT_FEATURES_NUM:
            encoded_parts.append(np.array([float(features[col])]))

        return np.array(encoded_parts).reshape(1, -1)

    def predict(self, vds_no: str) -> dict:
        """
        Predict all datasheet fields for a VDS number.

        Args:
            vds_no: VDS number string (e.g., "BSFA1R")

        Returns:
            dict of field_name -> predicted value string
        """
        if not self._loaded:
            self.load()

        X = self._encode_vds(vds_no)
        y_pred = self.model.predict(X)

        # Decode predictions back to string values
        result = {}
        for i, field in enumerate(TARGET_FIELDS):
            enc = self.label_encoders[field]
            val = enc.inverse_transform([int(y_pred[0, i])])[0]
            if val == DatasetBuilder.MISSING_LABEL:
                val = ""
            result[field] = val

        return result

    def predict_with_confidence(self, vds_no: str) -> dict:
        """
        Predict fields with confidence scores.

        Returns dict of field_name -> {"value": str, "confidence": float}
        """
        if not self._loaded:
            self.load()

        X = self._encode_vds(vds_no)
        y_pred = self.model.predict(X)
        probas = self.model.predict_proba(X)

        result = {}
        for i, field in enumerate(TARGET_FIELDS):
            enc = self.label_encoders[field]
            pred_label = int(y_pred[0, i])
            val = enc.inverse_transform([pred_label])[0]
            if val == DatasetBuilder.MISSING_LABEL:
                val = ""

            # Get confidence
            if probas.get(field) is not None and probas[field] is not None:
                confidence = float(np.max(probas[field][0]))
            else:
                confidence = 1.0  # constant predictor

            result[field] = {
                "value": val,
                "confidence": round(confidence, 4),
            }

        return result

    def get_evaluation_report(self) -> dict:
        """Load and return the evaluation report from training."""
        report_path = self.model_dir / "evaluation_report.json"
        if report_path.exists():
            with open(report_path, "r") as f:
                return json.load(f)
        return {}
