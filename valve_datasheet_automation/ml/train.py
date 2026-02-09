"""
Training script for the Valve Datasheet ML model.

Usage:
    python -m valve_datasheet_automation.ml.train

Loads data from unstructured/all_valve_vds_index.json,
trains multi-output classifiers, evaluates, and saves artifacts.
"""

import json
import sys
import time
from pathlib import Path

import joblib
import numpy as np

from .data_preparation import DatasetBuilder, TARGET_FIELDS
from .model import ValveDatasheetModel


def main():
    project_root = Path(__file__).parent.parent.parent
    data_path = project_root / "unstructured" / "all_valve_vds_index.json"
    model_dir = Path(__file__).parent / "trained_model"

    print("=" * 70)
    print("  VALVE DATASHEET ML MODEL - TRAINING")
    print("=" * 70)

    # --- Data preparation ---
    print("\n[1/4] Loading and preparing data...")
    builder = DatasetBuilder(data_path)
    splits = builder.prepare(test_size=0.15, val_size=0.15, random_state=42)

    X_train = splits["X_train"]
    y_train = splits["y_train"]
    X_val = splits["X_val"]
    y_val = splits["y_val"]
    X_test = splits["X_test"]
    y_test = splits["y_test"]

    print(f"  Training samples:   {X_train.shape[0]}")
    print(f"  Validation samples: {X_val.shape[0]}")
    print(f"  Test samples:       {X_test.shape[0]}")
    print(f"  Input features:     {X_train.shape[1]}")
    print(f"  Target fields:      {len(TARGET_FIELDS)}")

    # --- Training ---
    print(f"\n[2/4] Training model ({len(TARGET_FIELDS)} classifiers)...")
    model = ValveDatasheetModel(n_estimators=200, max_depth=5, learning_rate=0.1)
    start = time.time()
    train_acc = model.fit(X_train, y_train, verbose=True)
    elapsed = time.time() - start
    print(f"\n  Training completed in {elapsed:.1f}s")

    # --- Evaluation ---
    print("\n[3/4] Evaluating model...")

    print("\n  --- Validation Set ---")
    val_results = model.evaluate(X_val, y_val, builder)
    print(f"  Overall accuracy:  {val_results['overall_accuracy']:.4f}")
    print(f"  Exact match rate:  {val_results['exact_match_rate']:.4f}")

    print("\n  --- Test Set ---")
    test_results = model.evaluate(X_test, y_test, builder)
    print(f"  Overall accuracy:  {test_results['overall_accuracy']:.4f}")
    print(f"  Exact match rate:  {test_results['exact_match_rate']:.4f}")

    # Per-field breakdown
    print(f"\n  {'Field':<32s} {'Val Acc':>8s} {'Test Acc':>8s} {'F1':>8s} {'Classes':>8s}")
    print("  " + "-" * 66)
    for field in TARGET_FIELDS:
        v = val_results["per_field"][field]
        t = test_results["per_field"][field]
        print(f"  {field:<32s} {v['accuracy']:>8.3f} {t['accuracy']:>8.3f} {t['f1_weighted']:>8.3f} {t['n_classes']:>8d}")

    # --- Save ---
    print(f"\n[4/4] Saving model to {model_dir}...")
    model.save(model_dir)

    # Save encoders
    joblib.dump(builder.input_encoders, model_dir / "input_encoders.joblib")
    joblib.dump(builder.label_encoders, model_dir / "label_encoders.joblib")

    # Save evaluation report
    report = {
        "train_samples": int(X_train.shape[0]),
        "val_samples": int(X_val.shape[0]),
        "test_samples": int(X_test.shape[0]),
        "training_time_seconds": round(elapsed, 1),
        "validation": val_results,
        "test": test_results,
    }
    with open(model_dir / "evaluation_report.json", "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n  Model artifacts saved to: {model_dir}")
    print(f"  Evaluation report: {model_dir / 'evaluation_report.json'}")

    # --- Sample predictions ---
    print("\n" + "=" * 70)
    print("  SAMPLE PREDICTIONS (Test Set)")
    print("=" * 70)

    sample_indices = np.random.RandomState(42).choice(len(splits["vds_test"]), size=min(3, len(splits["vds_test"])), replace=False)
    y_pred_test = model.predict(X_test)
    pred_df = builder.decode_targets(y_pred_test)
    true_df = builder.decode_targets(y_test)

    for idx in sample_indices:
        vds = splits["vds_test"][idx]
        print(f"\n  VDS: {vds}")
        print(f"  {'Field':<30s} {'Predicted':<40s} {'Actual':<40s} {'Match'}")
        print("  " + "-" * 115)
        for field in TARGET_FIELDS:  # Show ALL fields
            pred_val = str(pred_df.iloc[idx][field])[:38]
            true_val = str(true_df.iloc[idx][field])[:38]
            match = "OK" if pred_df.iloc[idx][field] == true_df.iloc[idx][field] else "MISS"
            print(f"  {field:<30s} {pred_val:<40s} {true_val:<40s} {match}")

    print("\n" + "=" * 70)
    print("  TRAINING COMPLETE")
    print("=" * 70)

    return test_results


if __name__ == "__main__":
    main()
