"""
Data preparation for VDS ML model.

Loads the all_valve_vds_index.json, parses VDS numbers into features,
encodes categorical variables, and prepares train/val/test splits.
"""

import json
import re
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder


# ---------- VDS feature extraction ----------

# Known 3-char prefixes (must check before 2-char)
THREE_CHAR_PREFIXES = {"BSF", "BSR", "GAW", "GLS", "CHP", "CSW", "CDP", "BFD", "DSR", "DSF", "NEE"}
TWO_CHAR_PREFIXES = {"BS", "GS", "CS", "PS"}
BORE_CHARS = {"F", "R", "M", "T"}
END_CHARS = {"R", "J", "F", "W", "S"}

# For 3-char prefixes, bore type is implicit in the prefix itself
PREFIX_BORE_MAP = {
    "BSF": "F",   # Ball Full
    "BSR": "R",   # Ball Reduced
    "GAW": "F",   # Gate (default full)
    "GLS": "F",   # Globe (default full)
    "CHP": "F",   # Check Piston (default full)
    "CSW": "F",   # Check Swing (default full)
    "CDP": "F",   # Check Dual Plate (default full)
    "BFD": "F",   # Butterfly (default full)
    "DSR": "R",   # DBB Reduced
    "DSF": "F",   # DBB Full
    "NEE": "F",   # Needle (default full)
}


def parse_vds_features(vds: str) -> dict:
    """
    Parse a VDS number string into ML-ready feature dict.

    Returns dict with keys:
        prefix, bore_type, piping_class_letter, piping_class_number,
        is_nace, is_low_temp, is_metal_seated, end_connection
    """
    vds = vds.upper().strip()
    features = {
        "prefix": "UNK",
        "bore_type": "UNK",
        "piping_class_letter": "UNK",
        "piping_class_number": 0,
        "is_nace": 0,
        "is_low_temp": 0,
        "is_metal_seated": 0,
        "end_connection": "UNK",
    }

    if len(vds) < 5:
        return features

    # 1. Extract prefix (3-char then 2-char)
    prefix_len = 0
    if len(vds) >= 3 and vds[:3] in THREE_CHAR_PREFIXES:
        features["prefix"] = vds[:3]
        prefix_len = 3
    elif vds[:2] in TWO_CHAR_PREFIXES:
        features["prefix"] = vds[:2]
        prefix_len = 2
    else:
        return features

    # 2. End connection (always last char)
    if vds[-1] in END_CHARS:
        features["end_connection"] = vds[-1]

    # 3. Extract bore type and determine where piping class starts
    pos = prefix_len

    if prefix_len == 3:
        # For 3-char prefixes, bore type is implicit in the prefix.
        # Do NOT consume the next character as bore type.
        features["bore_type"] = PREFIX_BORE_MAP.get(features["prefix"], "F")
        # Check for metal-seated indicator 'M' right after 3-char prefix
        if pos < len(vds) and vds[pos] == "M":
            features["is_metal_seated"] = 1
            pos += 1
        # Middle = everything between prefix (+ optional M) and end connection
        middle = vds[pos:-1]
    else:
        # For 2-char prefixes, bore type is explicitly at position 2
        if pos < len(vds) and vds[pos] in BORE_CHARS:
            features["bore_type"] = vds[pos]
            if vds[pos] == "M":
                features["is_metal_seated"] = 1
            pos += 1
        # Check for metal-seated indicator after bore
        if pos < len(vds) and vds[pos] == "M" and features["bore_type"] != "M":
            features["is_metal_seated"] = 1
            pos += 1
        middle = vds[pos:-1]

    # 4. Parse piping class + modifiers from middle portion
    if middle:
        # Standard format: Letter + Digits + optional L/N modifiers
        # Examples: A1, B1N, F1LN, G20
        m = re.match(r"([A-GT])(\d+)(L?)(N?)", middle)
        if m:
            features["piping_class_letter"] = m.group(1)
            features["piping_class_number"] = int(m.group(2))
            if m.group(3):
                features["is_low_temp"] = 1
            if m.group(4):
                features["is_nace"] = 1
        else:
            # Try instrumentation format: T + digits + letter (T50A, T60B)
            m2 = re.match(r"T(\d+)([A-Z])(L?)(N?)", middle)
            if m2:
                features["piping_class_letter"] = "T"
                features["piping_class_number"] = int(m2.group(1))
                if m2.group(3):
                    features["is_low_temp"] = 1
                if m2.group(4):
                    features["is_nace"] = 1
            else:
                # Fallback: try digits + letter
                m3 = re.match(r"(\d+)([A-Z])(L?)(N?)", middle)
                if m3:
                    features["piping_class_number"] = int(m3.group(1))
                    features["piping_class_letter"] = m3.group(2)
                    if m3.group(3):
                        features["is_low_temp"] = 1
                    if m3.group(4):
                        features["is_nace"] = 1

    return features


# ---------- Target fields ----------

# Fields we predict (exclude identifiers and source_file)
TARGET_FIELDS = [
    "valve_type",
    "piping_class",
    "size_range",
    "service",
    "valve_standard",
    "pressure_class",
    "design_pressure",
    "corrosion_allowance",
    "sour_service",
    "end_connections",
    "face_to_face",
    "body_construction",
    "ball_construction",
    "stem_construction",
    "seat_construction",
    "locks",
    "operation",
    "body_material",
    "ball_material",
    "seat_material",
    "seal_material",
    "stem_material",
    "gland_material",
    "gland_packing",
    "lever_handwheel",
    "spring_material",
    "gaskets",
    "bolts",
    "nuts",
    "marking_purchaser",
    "marking_manufacturer",
    "inspection_testing",
    "leakage_rate",
    "hydrotest_shell",
    "hydrotest_closure",
    "pneumatic_test",
    "material_certification",
    "fire_rating",
    "finish",
]

# Categorical input features
INPUT_FEATURES_CAT = ["prefix", "bore_type", "piping_class_letter", "end_connection"]
INPUT_FEATURES_NUM = ["piping_class_number", "is_nace", "is_low_temp", "is_metal_seated"]


class DatasetBuilder:
    """
    Builds ML-ready datasets from the VDS index JSON.

    Attributes:
        data_path: Path to all_valve_vds_index.json
        label_encoders: dict of field_name -> LabelEncoder (for targets)
        input_encoders: dict of feature_name -> LabelEncoder (for categorical inputs)
    """

    MISSING_LABEL = "__MISSING__"

    def __init__(self, data_path: Path):
        self.data_path = data_path
        self.label_encoders: dict[str, LabelEncoder] = {}
        self.input_encoders: dict[str, LabelEncoder] = {}
        self._raw: Optional[dict] = None

    def load(self) -> pd.DataFrame:
        """Load JSON and return raw DataFrame."""
        with open(self.data_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        self._raw = raw
        return pd.DataFrame.from_dict(raw, orient="index")

    def build_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Parse VDS numbers into feature columns."""
        feat_rows = []
        for vds in df["vds_no"]:
            feat_rows.append(parse_vds_features(vds))
        feat_df = pd.DataFrame(feat_rows, index=df.index)
        return feat_df

    def encode_inputs(self, feat_df: pd.DataFrame, fit: bool = True) -> np.ndarray:
        """
        Encode categorical input features + numeric features into numpy array.

        Args:
            feat_df: DataFrame from build_features()
            fit: If True, fit encoders (training). If False, transform only.

        Returns:
            2D numpy array of shape (n_samples, n_features)
        """
        encoded_parts = []

        for col in INPUT_FEATURES_CAT:
            vals = feat_df[col].astype(str).values
            if fit:
                enc = LabelEncoder()
                enc.fit(vals)
                self.input_encoders[col] = enc
            else:
                enc = self.input_encoders[col]
                # Handle unseen labels
                known = set(enc.classes_)
                vals = np.array([v if v in known else enc.classes_[0] for v in vals])
            encoded_parts.append(enc.transform(vals).reshape(-1, 1))

        for col in INPUT_FEATURES_NUM:
            encoded_parts.append(feat_df[col].values.reshape(-1, 1).astype(float))

        return np.hstack(encoded_parts)

    def encode_targets(self, df: pd.DataFrame, fit: bool = True) -> np.ndarray:
        """
        Encode all target fields into a 2D numpy array.

        Missing/empty values are mapped to MISSING_LABEL.

        Returns:
            2D numpy array of shape (n_samples, n_target_fields)
        """
        encoded_parts = []

        for field in TARGET_FIELDS:
            vals = df[field].fillna("").astype(str).values
            # Treat empty and "-" as missing
            vals = np.array([
                self.MISSING_LABEL if (v.strip() == "" or v.strip() == "-") else v
                for v in vals
            ])
            if fit:
                enc = LabelEncoder()
                enc.fit(vals)
                self.label_encoders[field] = enc
            else:
                enc = self.label_encoders[field]
                known = set(enc.classes_)
                vals = np.array([v if v in known else self.MISSING_LABEL for v in vals])
            encoded_parts.append(enc.transform(vals).reshape(-1, 1))

        return np.hstack(encoded_parts)

    def decode_targets(self, y: np.ndarray) -> pd.DataFrame:
        """
        Decode numeric target array back to string values.

        Args:
            y: 2D numpy array (n_samples, n_fields)

        Returns:
            DataFrame with decoded field values.
        """
        result = {}
        for i, field in enumerate(TARGET_FIELDS):
            enc = self.label_encoders[field]
            decoded = enc.inverse_transform(y[:, i].astype(int))
            # Replace MISSING_LABEL back with empty string
            decoded = [("" if v == self.MISSING_LABEL else v) for v in decoded]
            result[field] = decoded
        return pd.DataFrame(result)

    def prepare(
        self,
        test_size: float = 0.15,
        val_size: float = 0.15,
        random_state: int = 42,
    ) -> dict:
        """
        Full pipeline: load -> feature extraction -> encoding -> split.

        Returns dict with keys:
            X_train, X_val, X_test, y_train, y_val, y_test,
            vds_train, vds_val, vds_test (VDS number strings),
            feature_names, target_names
        """
        df = self.load()
        feat_df = self.build_features(df)

        X = self.encode_inputs(feat_df, fit=True)
        y = self.encode_targets(df, fit=True)

        vds_numbers = df["vds_no"].values

        # First split: train+val vs test
        X_temp, X_test, y_temp, y_test, vds_temp, vds_test = train_test_split(
            X, y, vds_numbers,
            test_size=test_size,
            random_state=random_state,
            stratify=df["valve_type"].values,
        )

        # Second split: train vs val
        val_ratio = val_size / (1 - test_size)
        # Get valve types for stratification
        vt_temp = df.loc[df["vds_no"].isin(vds_temp), "valve_type"].values
        # Reorder to match vds_temp
        vt_map = dict(zip(df["vds_no"].values, df["valve_type"].values))
        vt_temp_ordered = np.array([vt_map[v] for v in vds_temp])

        X_train, X_val, y_train, y_val, vds_train, vds_val = train_test_split(
            X_temp, y_temp, vds_temp,
            test_size=val_ratio,
            random_state=random_state,
            stratify=vt_temp_ordered,
        )

        return {
            "X_train": X_train,
            "X_val": X_val,
            "X_test": X_test,
            "y_train": y_train,
            "y_val": y_val,
            "y_test": y_test,
            "vds_train": vds_train,
            "vds_val": vds_val,
            "vds_test": vds_test,
            "feature_names": INPUT_FEATURES_CAT + INPUT_FEATURES_NUM,
            "target_names": TARGET_FIELDS,
        }
