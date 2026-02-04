#!/usr/bin/env python3
"""
Demo script for VDS-Driven Valve Datasheet Automation System.

This script demonstrates the core functionality of the system.
"""

import sys
from pathlib import Path
import json

# Add parent to path for package imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from valve_datasheet_automation.core.vds_decoder import VDSDecoder, VDSDecodingError
from valve_datasheet_automation.core.datasheet_engine import DatasheetEngine
from valve_datasheet_automation.output.json_exporter import JSONExporter
from valve_datasheet_automation.output.traceability_report import TraceabilityReport


def demo_vds_decoder():
    """Demonstrate VDS number decoding."""
    print("=" * 60)
    print("DEMO: VDS Number Decoding")
    print("=" * 60)

    decoder = VDSDecoder()

    # Test various VDS patterns
    test_vds = [
        "BSFA1R",    # Ball, Full bore, Class A1, RF
        "BSRA1R",    # Ball, Reduced bore, Class A1, RF
        "BSFB1NR",   # Ball, Full bore, Class B1N (NACE), RF
        "BSFG1LNJ",  # Ball, Full bore, Class G1LN (Low temp + NACE), RTJ
    ]

    for vds in test_vds:
        try:
            result = decoder.decode(vds)
            print(f"\n{vds}:")
            print(f"  Valve Type: {result.valve_type_full}")
            print(f"  Piping Class: {result.piping_class}")
            print(f"  End Connection: {result.end_connection.full_name}")
            print(f"  NACE: {result.is_nace_compliant}")
            print(f"  Low Temp: {result.is_low_temp}")
        except VDSDecodingError as e:
            print(f"\n{vds}: ERROR - {e}")


def demo_datasheet_generation():
    """Demonstrate full datasheet generation."""
    print("\n" + "=" * 60)
    print("DEMO: Datasheet Generation")
    print("=" * 60)

    # Initialize engine with config
    config_dir = Path(__file__).parent / "config"
    data_dir = Path(__file__).parent.parent / "unstructured"

    engine = DatasheetEngine(config_dir=config_dir, data_dir=data_dir)

    # Generate datasheet
    vds_no = "BSFA1R"
    print(f"\nGenerating datasheet for: {vds_no}")

    try:
        datasheet = engine.generate(vds_no)

        print(f"\nGeneration Results:")
        print(f"  Status: {datasheet.validation_status.upper()}")
        print(f"  Completion: {datasheet.completion_percentage:.1f}%")
        print(f"  Fields Populated: {datasheet.populated_count}/{datasheet.total_count}")

        # Show key fields
        print(f"\nKey Field Values:")
        print(f"  VDS No: {datasheet.vds_no.value}")
        print(f"  Piping Class: {datasheet.piping_class.value}")
        print(f"  Valve Type: {datasheet.valve_type.value}")
        print(f"  Valve Standard: {datasheet.valve_standard.value}")
        print(f"  Pressure Class: {datasheet.pressure_class.value}")
        print(f"  End Connections: {datasheet.end_connections.value}")
        print(f"  Body Material: {datasheet.body_material.value}")
        print(f"  Ball Material: {datasheet.ball_material.value}")
        print(f"  Seat Material: {datasheet.seat_material.value}")

        # Show traceability for one field
        print(f"\nTraceability Example (Ball Material):")
        trace = datasheet.ball_material.traceability
        print(f"  Source Type: {trace.source_type.value}")
        print(f"  Source Document: {trace.source_document}")

        if datasheet.validation_errors:
            print(f"\nValidation Errors:")
            for err in datasheet.validation_errors:
                print(f"  - {err}")

    except Exception as e:
        print(f"Error: {e}")


def demo_json_export():
    """Demonstrate JSON export."""
    print("\n" + "=" * 60)
    print("DEMO: JSON Export")
    print("=" * 60)

    config_dir = Path(__file__).parent / "config"
    data_dir = Path(__file__).parent.parent / "unstructured"

    engine = DatasheetEngine(config_dir=config_dir, data_dir=data_dir)
    datasheet = engine.generate("BSFA1R")

    # Export to JSON
    exporter = JSONExporter(include_traceability=True)
    json_str = exporter.export(datasheet)

    # Show snippet
    data = json.loads(json_str)
    print(f"\nJSON Structure:")
    print(f"  Metadata keys: {list(data.get('metadata', {}).keys())}")
    print(f"  Sections: {list(data.get('sections', {}).keys())}")

    # Show flat export
    flat_json = exporter.export_flat(datasheet)
    flat_data = json.loads(flat_json)
    print(f"\nFlat Export (first 5 fields):")
    for i, (key, value) in enumerate(flat_data.items()):
        if i >= 5:
            break
        if not key.startswith('_'):
            print(f"  {key}: {value}")


def demo_batch_generation():
    """Demonstrate batch generation."""
    print("\n" + "=" * 60)
    print("DEMO: Batch Generation")
    print("=" * 60)

    config_dir = Path(__file__).parent / "config"
    data_dir = Path(__file__).parent.parent / "unstructured"

    engine = DatasheetEngine(config_dir=config_dir, data_dir=data_dir)

    # Generate multiple datasheets
    vds_list = ["BSFA1R", "BSRA1R", "BSFB1NR", "INVALID_VDS"]
    print(f"\nProcessing {len(vds_list)} VDS numbers...")

    datasheets = engine.generate_batch(vds_list)

    print(f"\nBatch Results:")
    for ds in datasheets:
        status = "OK" if ds.validation_status == "valid" else "ERROR"
        print(f"  {ds.vds_no.value}: {status} ({ds.completion_percentage:.0f}%)")


def main():
    """Run all demos."""
    print("=" * 60)
    print("VDS-DRIVEN VALVE DATASHEET AUTOMATION SYSTEM")
    print("Demo Script")
    print("=" * 60)

    demo_vds_decoder()
    demo_datasheet_generation()
    demo_json_export()
    demo_batch_generation()

    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    print("\nTo generate a datasheet, run:")
    print("  python main.py generate BSFA1R")
    print("\nTo see all options:")
    print("  python main.py --help")


if __name__ == "__main__":
    main()
