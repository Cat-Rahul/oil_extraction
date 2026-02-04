#!/usr/bin/env python3
"""
Manual Verification Script for Valve Datasheet Accuracy.

Run this to compare generated values against source data.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from valve_datasheet_automation.core.datasheet_engine import DatasheetEngine


def verify_bsfa1r():
    """Verify BSFA1R datasheet against known values."""

    print("=" * 70)
    print("VERIFICATION REPORT: BSFA1R")
    print("=" * 70)

    # Expected values from source documents
    expected = {
        # From VDS Index (Excel)
        "vds_no": "BSFA1R",
        "size_range": '1/2" - 24"',
        "valve_type": "Ball Valve, Full Bore",
        "end_connections": "Flanged ASME B16.5 RF",
        "ball_material": "Forged - ASTM A182-F316",
        "seat_material": "Reinforced PTFE",
        "piping_class": "A1",

        # From PMS (Excel)
        "corrosion_allowance": "3 mm",

        # From VDS Decoding
        "sour_service": "-",  # Not NACE

        # From Material Mappings (CS)
        "bolts": "ASTM A193 Gr. B7",
        "nuts": "ASTM A194 Gr. 2H",
        "stem_material": "ASTM A182 F316",
        "gland_material": "ASTM A182 F6A CL 2",
        "spring_material": "Inconel 750",
        "gland_packing": "Graphite / PTFE",

        # From Standards
        "valve_standard": "API 6D / ISO 17292",
        "inspection_testing": "ASME B16.34, API 598",
        "leakage_rate": "As per API 598",

        # Calculated (1.5x and 1.1x of 19.6 barg)
        "hydrotest_shell": "29.4 barg",
        "hydrotest_closure": "21.6 barg",
    }

    # Generate datasheet
    config_dir = Path(__file__).parent / "valve_datasheet_automation" / "config"
    data_dir = Path(__file__).parent / "unstructured"

    engine = DatasheetEngine(config_dir=config_dir, data_dir=data_dir)
    datasheet = engine.generate("BSFA1R")

    # Compare
    passed = 0
    failed = 0

    print(f"\n{'Field':<25} {'Expected':<35} {'Generated':<35} {'Status'}")
    print("-" * 110)

    for field_name, expected_value in expected.items():
        field = getattr(datasheet, field_name, None)
        if field:
            generated_value = field.value
            match = str(generated_value) == str(expected_value)
            status = "PASS" if match else "FAIL"

            if match:
                passed += 1
            else:
                failed += 1

            # Truncate long values for display
            exp_display = str(expected_value)[:33] + ".." if len(str(expected_value)) > 35 else str(expected_value)
            gen_display = str(generated_value)[:33] + ".." if len(str(generated_value)) > 35 else str(generated_value)

            print(f"{field_name:<25} {exp_display:<35} {gen_display:<35} {status}")
        else:
            print(f"{field_name:<25} {expected_value:<35} {'[FIELD NOT FOUND]':<35} FAIL")
            failed += 1

    print("-" * 110)
    print(f"\nRESULTS: {passed} passed, {failed} failed")
    print(f"ACCURACY: {(passed / (passed + failed)) * 100:.1f}%")

    if failed == 0:
        print("\n*** ALL VERIFICATIONS PASSED ***")
    else:
        print("\n*** SOME VERIFICATIONS FAILED - REVIEW REQUIRED ***")

    return failed == 0


def verify_nace_compliance():
    """Verify NACE materials are correctly selected."""

    print("\n" + "=" * 70)
    print("VERIFICATION: NACE COMPLIANCE (BSFB1NR)")
    print("=" * 70)

    # NACE-specific expected values
    expected_nace = {
        "sour_service": "NACE MR0175 / ISO 15156",
        "bolts": "ASTM A193 Gr. B7M",  # M suffix for NACE
        "nuts": "ASTM A194 Gr. 2HM",   # M suffix for NACE
    }

    config_dir = Path(__file__).parent / "valve_datasheet_automation" / "config"
    data_dir = Path(__file__).parent / "unstructured"

    engine = DatasheetEngine(config_dir=config_dir, data_dir=data_dir)
    datasheet = engine.generate("BSFB1NR")

    passed = 0
    failed = 0

    print(f"\n{'Field':<25} {'Expected (NACE)':<35} {'Generated':<35} {'Status'}")
    print("-" * 110)

    for field_name, expected_value in expected_nace.items():
        field = getattr(datasheet, field_name, None)
        if field:
            generated_value = field.value
            match = str(generated_value) == str(expected_value)
            status = "PASS" if match else "FAIL"

            if match:
                passed += 1
            else:
                failed += 1

            print(f"{field_name:<25} {str(expected_value):<35} {str(generated_value):<35} {status}")

    print("-" * 110)
    print(f"NACE COMPLIANCE: {passed}/{passed + failed} fields correct")

    return failed == 0


def verify_pressure_class_mapping():
    """Verify pressure class is correctly derived from piping class."""

    print("\n" + "=" * 70)
    print("VERIFICATION: PRESSURE CLASS MAPPING")
    print("=" * 70)

    test_cases = [
        ("BSFA1R", "ASME B16.34 Class 150"),   # A = 150#
        ("BSFB1R", "ASME B16.34 Class 300"),   # B = 300#
        ("BSFD1R", "ASME B16.34 Class 600"),   # D = 600#
        ("BSFE1J", "ASME B16.34 Class 900"),   # E = 900#
        ("BSFG1J", "ASME B16.34 Class 2500"),  # G = 2500#
    ]

    config_dir = Path(__file__).parent / "valve_datasheet_automation" / "config"
    data_dir = Path(__file__).parent / "unstructured"

    engine = DatasheetEngine(config_dir=config_dir, data_dir=data_dir)

    passed = 0
    failed = 0

    print(f"\n{'VDS No':<15} {'Expected':<30} {'Generated':<30} {'Status'}")
    print("-" * 85)

    for vds_no, expected in test_cases:
        try:
            datasheet = engine.generate(vds_no)
            generated = datasheet.pressure_class.value
            match = generated == expected
            status = "PASS" if match else "FAIL"

            if match:
                passed += 1
            else:
                failed += 1

            print(f"{vds_no:<15} {expected:<30} {generated:<30} {status}")
        except Exception as e:
            print(f"{vds_no:<15} {expected:<30} {'ERROR: ' + str(e)[:20]:<30} FAIL")
            failed += 1

    print("-" * 85)
    print(f"PRESSURE MAPPING: {passed}/{passed + failed} cases correct")

    return failed == 0


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("VALVE DATASHEET ACCURACY VERIFICATION")
    print("=" * 70)

    all_passed = True

    all_passed &= verify_bsfa1r()
    all_passed &= verify_nace_compliance()
    all_passed &= verify_pressure_class_mapping()

    print("\n" + "=" * 70)
    if all_passed:
        print("OVERALL RESULT: ALL VERIFICATIONS PASSED")
    else:
        print("OVERALL RESULT: SOME VERIFICATIONS FAILED")
    print("=" * 70)

    sys.exit(0 if all_passed else 1)
