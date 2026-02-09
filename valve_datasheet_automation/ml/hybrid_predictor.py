"""
Hybrid Predictor: VDS Index Lookup + Rule-based + ML for 100% accuracy.

PRIORITY ORDER:
1. VDS_INDEX: If VDS exists in training data, return exact values (100% match)
2. RULE-BASED: For unknown VDS, extract piping_class/sour_service from VDS string
3. ML-BASED: For other fields of unknown VDS, use ML prediction

This achieves 100% match with training data for known VDS numbers.
"""

import json
import numpy as np
import joblib
from pathlib import Path
from typing import Optional, Dict, Any

from .data_preparation import (
    parse_vds_features,
    INPUT_FEATURES_CAT,
    INPUT_FEATURES_NUM,
    TARGET_FIELDS,
    DatasetBuilder,
)
from .model import ValveDatasheetModel


# ============================================================================
# RULE-BASED MAPPINGS (100% Deterministic)
# ============================================================================

# Piping class letter -> Pressure class (ASME B16.34)
PRESSURE_CLASS_MAP = {
    "A": "ASME B16.34 Class 150",
    "B": "ASME B16.34 Class 300",
    "C": "ASME B16.34 Class 400",
    "D": "ASME B16.34 Class 600",
    "E": "ASME B16.34 Class 900",
    "F": "ASME B16.34 Class 1500",
    "G": "ASME B16.34 Class 2500",
    "T": "ASME B16.34 Class 600",  # Instrumentation default
}

# Pressure class letter -> Design pressure (barg @ temp)
DESIGN_PRESSURE_MAP = {
    "A": "19.6 @ -29°C, 13.8 @ 200°C",      # 150#
    "B": "51.1 @ -29°C, 43.8 @ 200°C",      # 300#
    "C": "68.2 @ -29°C, 58.4 @ 200°C",      # 400#
    "D": "102.1 @ -29°C, 87.5 @ 200°C",     # 600#
    "E": "153.2 @ -29°C, 131.3 @ 200°C",    # 900#
    "F": "255.3 @ -29°C, 218.8 @ 200°C",    # 1500#
    "G": "425.5 @ -29°C, 364.6 @ 200°C",    # 2500#
    "T": "102.1 @ -29°C, 87.5 @ 200°C",     # Instrumentation (600#)
}

# NACE variant design pressures (slightly different for sour service)
DESIGN_PRESSURE_NACE_MAP = {
    "A": "19.6 @ -29°C, 12.4 @ 200°C",
    "B": "51.1 @ -29°C, 39.3 @ 200°C",
    "D": "102.1 @ -29°C, 78.6 @ 200°C",
    "E": "153.2 @ -29°C, 117.9 @ 200°C",
    "F": "255.3 @ -29°C, 196.5 @ 200°C",
    "G": "425.5 @ -29°C, 327.5 @ 200°C",
}

# End connection char -> Full end connection description
# Format depends on pressure class (RF vs RTJ threshold)
END_CONNECTION_MAP = {
    "R": {  # RF - Raised Face
        "default": "Flanged ASME B16.5 RF",
        "high_pressure": "Flanged ASME B16.5 RF",  # 900# and above still RF by default
    },
    "J": {  # RTJ - Ring Type Joint
        "default": "Flanged ASME B16.5 RTJ",
        "high_pressure": "Flanged ASME B16.5 RTJ",
    },
    "F": {  # FF - Flat Face
        "default": "Flanged ASME B16.5 FF",
    },
    "W": {  # BW - Butt Weld
        "default": "Butt Weld ASME B16.25",
    },
    "S": {  # SW - Socket Weld
        "default": "Socket Weld ASME B16.11",
    },
}

# Sour service based on NACE flag (using exact format from training data)
SOUR_SERVICE_MAP = {
    True: "NACE MR0175 /ISO 15156-1/2/3, SSC Region 3, Non-exposed, internal only",
    False: "-",
}


# ============================================================================
# FIELDS THAT ARE RULE-BASED (100% Deterministic)
# ============================================================================

# Fields that are 100% deterministic from VDS string (rule-based)
# IMPORTANT: Only include fields where the VDS string FULLY determines the value.
#
# EXCLUDED from rule-based:
# - design_pressure: Varies based on low_temp, specific configs, piping class number
# - end_connections: Depends on valve type too (butterfly gets "Wafer Lugged"), not just end char
# - pressure_class: While mostly deterministic, has some variations in training data
#
# ML handles these better because it considers multiple features (prefix, bore, etc.)
RULE_BASED_FIELDS = {
    "piping_class",        # Reconstructed from piping_class_letter + number + modifiers (100% deterministic)
    "sour_service",        # Directly from is_nace flag (100% deterministic)
}


def reconstruct_piping_class(features: dict) -> str:
    """
    Reconstruct the full piping class string from parsed features.

    Examples:
        A, 1, nace=0, low_temp=0 -> "A1"
        B, 1, nace=1, low_temp=0 -> "B1N"
        G, 20, nace=1, low_temp=1 -> "G20LN"
        D, 10, nace=1, low_temp=0 -> "D10N"
    """
    letter = features.get("piping_class_letter", "")
    number = features.get("piping_class_number", 0)
    is_nace = features.get("is_nace", 0)
    is_low_temp = features.get("is_low_temp", 0)

    if letter == "UNK" or letter == "":
        return "Unknown"

    # Build: Letter + Number + L? + N?
    result = f"{letter}{number}"
    if is_low_temp:
        result += "L"
    if is_nace:
        result += "N"

    return result


def derive_sour_service(features: dict) -> str:
    """Derive sour service from NACE flag."""
    is_nace = bool(features.get("is_nace", 0))
    return SOUR_SERVICE_MAP[is_nace]


def derive_pressure_class(features: dict) -> str:
    """Derive pressure class from piping class letter."""
    letter = features.get("piping_class_letter", "A")
    if letter == "UNK":
        letter = "A"
    return PRESSURE_CLASS_MAP.get(letter, PRESSURE_CLASS_MAP["A"])


def derive_design_pressure(features: dict) -> str:
    """Derive design pressure from piping class letter and NACE flag."""
    letter = features.get("piping_class_letter", "A")
    is_nace = bool(features.get("is_nace", 0))

    if letter == "UNK":
        letter = "A"

    if is_nace and letter in DESIGN_PRESSURE_NACE_MAP:
        return DESIGN_PRESSURE_NACE_MAP[letter]
    return DESIGN_PRESSURE_MAP.get(letter, DESIGN_PRESSURE_MAP["A"])


def derive_end_connections(features: dict) -> str:
    """Derive end connections from end connection character."""
    end_char = features.get("end_connection", "R")
    if end_char == "UNK":
        end_char = "R"

    mapping = END_CONNECTION_MAP.get(end_char, END_CONNECTION_MAP["R"])
    return mapping.get("default", "Flanged ASME B16.5 RF")


# ============================================================================
# HYBRID PREDICTOR CLASS
# ============================================================================

class HybridPredictor:
    """
    Hybrid predictor with VDS Index lookup + Rule-based + ML prediction.

    PRIORITY ORDER:
    1. VDS_INDEX: If VDS exists in training data, return exact values (100% match)
    2. RULE-BASED: For unknown VDS, extract piping_class/sour_service from VDS string
    3. ML-BASED: For other fields of unknown VDS, use ML prediction

    Usage:
        predictor = HybridPredictor()
        predictor.load()
        result = predictor.predict("BFDA30WF")
        # If in index: returns exact training data values
        # If not in index: uses rule-based + ML fallback
    """

    def __init__(self, model_dir: Path = None, data_dir: Path = None):
        if model_dir is None:
            model_dir = Path(__file__).parent / "trained_model"
        if data_dir is None:
            data_dir = Path(__file__).parent.parent.parent / "unstructured"

        self.model_dir = model_dir
        self.data_dir = data_dir
        self.model: ValveDatasheetModel = None
        self.input_encoders: dict = None
        self.label_encoders: dict = None
        self.vds_index: Dict[str, Dict[str, Any]] = {}
        self._loaded = False

    @property
    def is_available(self) -> bool:
        """Check if a trained model exists."""
        return (self.model_dir / "model_meta.json").exists()

    def load(self) -> None:
        """Load trained model, encoders, and VDS index."""
        if not self.is_available:
            raise FileNotFoundError(
                f"No trained model found at {self.model_dir}. "
                "Run: python -m valve_datasheet_automation.ml.train"
            )

        # Load ML model
        self.model = ValveDatasheetModel()
        self.model.load(self.model_dir)

        self.input_encoders = joblib.load(self.model_dir / "input_encoders.joblib")
        self.label_encoders = joblib.load(self.model_dir / "label_encoders.joblib")

        # Load VDS Index for exact lookups
        index_path = self.data_dir / "all_valve_vds_index.json"
        if index_path.exists():
            with open(index_path, "r", encoding="utf-8") as f:
                self.vds_index = json.load(f)

        self._loaded = True

    def _encode_vds(self, vds_no: str) -> np.ndarray:
        """Parse and encode a single VDS number into feature vector for ML."""
        features = parse_vds_features(vds_no)

        encoded_parts = []
        for col in INPUT_FEATURES_CAT:
            val = str(features[col])
            enc = self.input_encoders[col]
            known = set(enc.classes_)
            if val not in known:
                val = enc.classes_[0]  # fallback to first known class
            encoded_parts.append(enc.transform([val]))

        for col in INPUT_FEATURES_NUM:
            encoded_parts.append(np.array([float(features[col])]))

        return np.array(encoded_parts).reshape(1, -1)

    def _apply_rule_based(self, features: dict) -> dict:
        """
        Apply rule-based extraction for deterministic fields.
        Returns dict of field_name -> value for rule-based fields.

        Only piping_class and sour_service are truly 100% deterministic from VDS.
        Other fields like end_connections and pressure_class depend on multiple
        factors (valve type, etc.) so ML handles them better.
        """
        return {
            "piping_class": reconstruct_piping_class(features),
            "sour_service": derive_sour_service(features),
        }

    def _lookup_vds_index(self, vds_no: str) -> Optional[Dict[str, Any]]:
        """Look up VDS in index. Returns exact data if found, None otherwise."""
        vds_upper = vds_no.upper().strip()
        return self.vds_index.get(vds_upper)

    def _filter_empty_fields(self, data: dict) -> dict:
        """Remove fields with empty or '-' values (not applicable for this valve type)."""
        return {
            k: v for k, v in data.items()
            if v and v.strip() and v.strip() != "-"
        }

    def predict(self, vds_no: str, include_empty: bool = False) -> dict:
        """
        Predict all datasheet fields.

        PRIORITY:
        1. If VDS exists in index: Return exact values from training data
        2. If not in index: Use rule-based + ML fallback

        Args:
            vds_no: VDS number string (e.g., "BFDA30WF")
            include_empty: If False, excludes empty/non-applicable fields

        Returns:
            dict of field_name -> predicted value string
        """
        if not self._loaded:
            self.load()

        # Step 1: Try VDS Index lookup first (100% match with training data)
        index_data = self._lookup_vds_index(vds_no)
        if index_data:
            # Return ALL fields from index (not just TARGET_FIELDS)
            # This ensures valve-type-specific fields like disc_construction are included
            result = {}
            exclude_fields = {'source_file'}  # Internal fields to exclude
            for field, value in index_data.items():
                if field not in exclude_fields:
                    result[field] = value
            return result if include_empty else self._filter_empty_fields(result)

        # Step 2: VDS not in index - use rule-based + ML fallback
        features = parse_vds_features(vds_no)
        rule_based_values = self._apply_rule_based(features)

        # Step 3: Get ML predictions for other fields
        X = self._encode_vds(vds_no)
        y_pred = self.model.predict(X)

        # Step 4: Combine results
        result = {}
        for i, field in enumerate(TARGET_FIELDS):
            if field in RULE_BASED_FIELDS:
                # Use rule-based value
                result[field] = rule_based_values[field]
            else:
                # Use ML prediction
                enc = self.label_encoders[field]
                val = enc.inverse_transform([int(y_pred[0, i])])[0]
                if val == DatasetBuilder.MISSING_LABEL:
                    val = ""
                result[field] = val

        return result if include_empty else self._filter_empty_fields(result)

    def predict_with_confidence(self, vds_no: str, include_empty: bool = False) -> dict:
        """
        Predict fields with confidence scores.

        PRIORITY:
        1. VDS_INDEX: confidence = 1.0, source = "vds_index"
        2. RULE_BASED: confidence = 1.0, source = "rule_based"
        3. ML_PREDICTED: confidence from model, source = "ml_predicted"

        Args:
            vds_no: VDS number string
            include_empty: If False, excludes empty/non-applicable fields

        Returns dict of field_name -> {"value": str, "confidence": float, "source": str}
        """
        if not self._loaded:
            self.load()

        # Step 1: Try VDS Index lookup first
        index_data = self._lookup_vds_index(vds_no)
        if index_data:
            # Return ALL fields from index (not just TARGET_FIELDS)
            # This ensures valve-type-specific fields like disc_construction are included
            result = {}
            exclude_fields = {'source_file'}  # Internal fields to exclude
            for field, val in index_data.items():
                if field in exclude_fields:
                    continue
                # Skip empty fields if include_empty is False
                if not include_empty and (not val or not str(val).strip() or str(val).strip() == "-"):
                    continue
                result[field] = {
                    "value": val,
                    "confidence": 1.0,
                    "source": "vds_index",
                }
            return result

        # Step 2: VDS not in index - use rule-based + ML fallback
        features = parse_vds_features(vds_no)
        rule_based_values = self._apply_rule_based(features)

        # Get ML predictions with probabilities
        X = self._encode_vds(vds_no)
        y_pred = self.model.predict(X)
        probas = self.model.predict_proba(X)

        result = {}
        for i, field in enumerate(TARGET_FIELDS):
            if field in RULE_BASED_FIELDS:
                val = rule_based_values[field]
                # Skip empty fields if include_empty is False
                if not include_empty and (not val or not val.strip() or val.strip() == "-"):
                    continue
                result[field] = {
                    "value": val,
                    "confidence": 1.0,
                    "source": "rule_based",
                }
            else:
                enc = self.label_encoders[field]
                pred_label = int(y_pred[0, i])
                val = enc.inverse_transform([pred_label])[0]
                if val == DatasetBuilder.MISSING_LABEL:
                    val = ""

                # Skip empty fields if include_empty is False
                if not include_empty and (not val or not val.strip() or val.strip() == "-"):
                    continue

                # Get confidence
                if probas.get(field) is not None and probas[field] is not None:
                    confidence = float(np.max(probas[field][0]))
                else:
                    confidence = 1.0  # constant predictor

                result[field] = {
                    "value": val,
                    "confidence": round(confidence, 4),
                    "source": "ml_predicted",
                }

        return result

    def get_rule_based_fields(self) -> set:
        """Return set of fields that are rule-based (100% accurate)."""
        return RULE_BASED_FIELDS.copy()

    def get_ml_fields(self) -> set:
        """Return set of fields that use ML prediction."""
        return set(TARGET_FIELDS) - RULE_BASED_FIELDS


# ============================================================================
# SINGLETON FOR API USE
# ============================================================================

_hybrid_predictor: Optional[HybridPredictor] = None


def get_hybrid_predictor(model_dir: Path = None) -> HybridPredictor:
    """Get or create the singleton hybrid predictor."""
    global _hybrid_predictor
    if _hybrid_predictor is None:
        _hybrid_predictor = HybridPredictor(model_dir)
        if _hybrid_predictor.is_available:
            _hybrid_predictor.load()
    return _hybrid_predictor
