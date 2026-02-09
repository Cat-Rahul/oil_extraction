"""
Extract training data from Excel valve datasheet files.
Converts Excel sheets to JSON format for ML training.

Usage:
    python extract_training_data.py
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional

# Field mapping: Excel label -> JSON field name
FIELD_MAPPING = {
    "VDS No": "vds_no",
    "Piping Class": "piping_class",
    "Size Range": "size_range",
    "Valve type": "valve_type",
    "Service": "service",
    "Valve Standard": "valve_standard",
    "Pressure Class": "pressure_class",
    "Design Pressure": "design_pressure",
    "Corrosion Allowance": "corrosion_allowance",
    "Sour Service Requirements": "sour_service",
    "End Connections": "end_connections",
    "Face to Face Dimension": "face_to_face",
    "Construction": "body_construction",
    "Operation": "operation",
    "Material": "body_material",
    "Marking - Purchaser": "marking_purchaser",
    "Marking - Purchasers Spe": "marking_purchaser",
    "Marking – Manufacturer": "marking_manufacturer",
    "Marking - Manufacturer": "marking_manufacturer",
    "Inspection - Testing": "inspection_testing",
    "Inspection – Testing": "inspection_testing",
    "Leakage Rate": "leakage_rate",
    "Hydrotest Shell Test Pres": "hydrotest_shell",
    "Hydrotest Closure Test Pr": "hydrotest_closure",
    "Pneumatic LP Test Pressur": "pneumatic_test",
    "Material Certification": "material_certification",
    "Fire Rating": "fire_rating",
    "Finish": "finish",
    "Locks": "locks",
}

# Fields that continue on subsequent rows (no label)
CONSTRUCTION_FIELDS = [
    "body_construction", "ball_construction", "stem_construction",
    "seat_construction", "disc_construction", "wedge_construction",
    "gland_construction", "locks"
]

MATERIAL_FIELDS = [
    "body_material", "ball_material", "seat_material", "seal_material",
    "stem_material", "gland_material", "gland_packing", "lever_handwheel",
    "spring_material", "gaskets", "bolts", "nuts", "disc_material",
    "wedge_material", "trim_material", "hinge_pin_material"
]


def clean_value(val: Any) -> str:
    """Clean and convert value to string."""
    if pd.isna(val):
        return ""
    val = str(val).strip()
    # Fix common encoding issues
    val = val.replace("\u2019", "'").replace("\u2013", "-")
    val = val.replace("\u00e2\u20ac\u2122", "'")
    return val


def extract_sheet_data(df: pd.DataFrame, valve_type_hint: str) -> Optional[Dict[str, Any]]:
    """Extract datasheet data from a single sheet."""
    data = {}

    # Track which multi-row fields we're in
    in_construction = False
    in_material = False
    construction_idx = 0
    material_idx = 0

    for idx, row in df.iterrows():
        label = clean_value(row[0])
        value = clean_value(row[2]) if len(row) > 2 else ""

        # Skip empty rows
        if not label and not value:
            continue

        # Check if this is a labeled field
        matched = False
        for excel_label, json_field in FIELD_MAPPING.items():
            if label and excel_label.lower() in label.lower():
                data[json_field] = value
                matched = True

                # Track if we're entering construction or material section
                if json_field == "body_construction":
                    in_construction = True
                    in_material = False
                    construction_idx = 0
                elif json_field == "body_material":
                    in_construction = False
                    in_material = True
                    material_idx = 0
                elif json_field == "operation":
                    in_construction = False
                elif json_field in ["marking_purchaser", "marking_manufacturer"]:
                    in_material = False
                break

        # Handle unlabeled continuation rows
        if not matched and value:
            if in_construction and construction_idx < len(CONSTRUCTION_FIELDS) - 1:
                construction_idx += 1
                field = CONSTRUCTION_FIELDS[construction_idx]
                data[field] = value
            elif in_material and material_idx < len(MATERIAL_FIELDS) - 1:
                material_idx += 1
                field = MATERIAL_FIELDS[material_idx]
                data[field] = value

    # Validate we got minimum required fields
    if "vds_no" in data and "valve_type" in data:
        return data
    return None


def extract_from_excel(file_path: Path) -> Dict[str, Dict]:
    """Extract all datasheets from an Excel file."""
    results = {}
    valve_type_hint = file_path.stem  # e.g., "BALL-With Metalic Valve-C0"

    print(f"Processing: {file_path.name}")

    try:
        xl = pd.ExcelFile(file_path)
    except Exception as e:
        print(f"  Error opening file: {e}")
        return results

    for sheet_name in xl.sheet_names:
        # Skip Index sheet
        if sheet_name.lower() == "index":
            continue

        try:
            df = pd.read_excel(xl, sheet_name=sheet_name, header=None, nrows=60)
            data = extract_sheet_data(df, valve_type_hint)

            if data and "vds_no" in data:
                vds_no = data["vds_no"]
                data["source_file"] = file_path.name
                results[vds_no] = data

        except Exception as e:
            print(f"  Error processing sheet {sheet_name}: {e}")

    print(f"  Extracted {len(results)} datasheets")
    return results


def main():
    # Source directory
    source_dir = Path("unstructured/VALVE DATA SHEET")

    # Output file
    output_file = Path("unstructured/extracted_valve_data.json")

    # Collect all data
    all_data = {}

    # Process each Excel file
    for excel_file in source_dir.glob("*.xls*"):
        if excel_file.name.startswith("~$"):  # Skip temp files
            continue

        extracted = extract_from_excel(excel_file)
        all_data.update(extracted)

    # Save to JSON
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*50}")
    print(f"Total extracted: {len(all_data)} datasheets")
    print(f"Saved to: {output_file}")

    # Show sample
    if all_data:
        sample_vds = list(all_data.keys())[0]
        print(f"\nSample entry ({sample_vds}):")
        for k, v in list(all_data[sample_vds].items())[:10]:
            print(f"  {k}: {str(v)[:50]}")


if __name__ == "__main__":
    main()
