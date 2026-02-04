#!/usr/bin/env python3
"""
VDS-Driven Valve Datasheet Automation System

CLI interface for generating valve datasheets from VDS numbers.

Usage:
    python main.py generate BSFA1R
    python main.py generate BSFA1R --output datasheet.json
    python main.py batch vds_list.txt --output-dir ./datasheets/
    python main.py decode BSFA1R
    python main.py validate BSFA1R
"""

import argparse
import json
import sys
from pathlib import Path

# Add parent to path for package imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from valve_datasheet_automation.core.datasheet_engine import DatasheetEngine, DatasheetGenerationError
from valve_datasheet_automation.core.vds_decoder import VDSDecodingError
from valve_datasheet_automation.output.json_exporter import JSONExporter
from valve_datasheet_automation.output.traceability_report import TraceabilityReport


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="VDS-Driven Valve Datasheet Automation System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Generate datasheet:
    python main.py generate BSFA1R
    python main.py generate BSFA1R --output datasheet.json
    python main.py generate BSFA1R --traceability

  Batch generation:
    python main.py batch vds_list.txt --output-dir ./datasheets/

  Decode VDS number:
    python main.py decode BSFA1R

  Validate VDS number:
    python main.py validate BSFA1R
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate datasheet from VDS")
    gen_parser.add_argument("vds_no", help="VDS number (e.g., BSFA1R)")
    gen_parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Output JSON file path"
    )
    gen_parser.add_argument(
        "-t", "--traceability",
        action="store_true",
        help="Generate traceability report"
    )
    gen_parser.add_argument(
        "--flat",
        action="store_true",
        help="Output flat JSON (values only)"
    )
    gen_parser.add_argument(
        "--data-dir",
        type=Path,
        help="Directory containing data files"
    )

    # Batch command
    batch_parser = subparsers.add_parser("batch", help="Generate multiple datasheets")
    batch_parser.add_argument(
        "input_file",
        type=Path,
        help="File containing VDS numbers (one per line)"
    )
    batch_parser.add_argument(
        "-o", "--output-dir",
        type=Path,
        default=Path("./datasheets"),
        help="Output directory for generated files"
    )
    batch_parser.add_argument(
        "--summary",
        action="store_true",
        help="Generate summary report"
    )
    batch_parser.add_argument(
        "--data-dir",
        type=Path,
        help="Directory containing data files"
    )

    # Decode command
    decode_parser = subparsers.add_parser("decode", help="Decode VDS number")
    decode_parser.add_argument("vds_no", help="VDS number to decode")

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate VDS number")
    validate_parser.add_argument("vds_no", help="VDS number to validate")

    # List command
    list_parser = subparsers.add_parser("list", help="List available data")
    list_parser.add_argument(
        "what",
        choices=["prefixes", "classes", "vds"],
        help="What to list"
    )
    list_parser.add_argument(
        "--data-dir",
        type=Path,
        help="Directory containing data files"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        if args.command == "generate":
            return cmd_generate(args)
        elif args.command == "batch":
            return cmd_batch(args)
        elif args.command == "decode":
            return cmd_decode(args)
        elif args.command == "validate":
            return cmd_validate(args)
        elif args.command == "list":
            return cmd_list(args)
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


def cmd_generate(args) -> int:
    """Handle generate command."""
    print(f"Generating datasheet for VDS: {args.vds_no}")

    # Get data directory
    data_dir = args.data_dir
    if not data_dir:
        # Try to find unstructured folder
        possible_paths = [
            Path(__file__).parent.parent / "unstructured",
            Path.cwd() / "unstructured",
            Path.cwd().parent / "unstructured",
        ]
        for p in possible_paths:
            if p.exists():
                data_dir = p
                break

    # Initialize engine
    config_dir = Path(__file__).parent / "config"
    engine = DatasheetEngine(config_dir=config_dir, data_dir=data_dir)

    # Generate datasheet
    try:
        datasheet = engine.generate(args.vds_no)
    except (VDSDecodingError, DatasheetGenerationError) as e:
        print(f"Generation failed: {e}", file=sys.stderr)
        return 1

    # Output results
    exporter = JSONExporter(
        include_traceability=not args.flat,
        include_metadata=True,
    )

    if args.output:
        if args.flat:
            exporter.export_flat(datasheet, args.output)
        else:
            exporter.export(datasheet, args.output)
        print(f"Datasheet saved to: {args.output}")
    else:
        # Print to stdout
        if args.flat:
            json_str = exporter.export_flat(datasheet)
        else:
            json_str = exporter.export(datasheet)
        print(json_str)

    # Generate traceability report if requested
    if args.traceability:
        report = TraceabilityReport()
        trace_output = args.output.with_suffix(".trace.txt") if args.output else None

        if trace_output:
            report.generate(datasheet, trace_output)
            print(f"Traceability report saved to: {trace_output}")
        else:
            print("\n" + report.generate(datasheet))

    # Print summary
    print(f"\nStatus: {datasheet.validation_status.upper()}")
    print(f"Completion: {datasheet.completion_percentage:.1f}%")

    if datasheet.validation_errors:
        print(f"Errors: {len(datasheet.validation_errors)}")
        for err in datasheet.validation_errors[:3]:
            print(f"  - {err}")

    return 0 if datasheet.validation_status == "valid" else 1


def cmd_batch(args) -> int:
    """Handle batch command."""
    input_file = args.input_file

    if not input_file.exists():
        print(f"Input file not found: {input_file}", file=sys.stderr)
        return 1

    # Read VDS numbers
    with open(input_file, 'r') as f:
        vds_numbers = [line.strip() for line in f if line.strip()]

    if not vds_numbers:
        print("No VDS numbers found in input file", file=sys.stderr)
        return 1

    print(f"Processing {len(vds_numbers)} VDS numbers...")

    # Get data directory
    data_dir = args.data_dir
    if not data_dir:
        possible_paths = [
            Path(__file__).parent.parent / "unstructured",
            Path.cwd() / "unstructured",
        ]
        for p in possible_paths:
            if p.exists():
                data_dir = p
                break

    # Initialize engine
    config_dir = Path(__file__).parent / "config"
    engine = DatasheetEngine(config_dir=config_dir, data_dir=data_dir)

    # Generate datasheets
    datasheets = engine.generate_batch(vds_numbers)

    # Export
    exporter = JSONExporter()
    output_paths = exporter.export_batch(datasheets, args.output_dir)

    print(f"Generated {len(output_paths)} datasheets in: {args.output_dir}")

    # Generate summary if requested
    if args.summary:
        summary_path = args.output_dir / "batch_summary.json"
        exporter.export_summary(datasheets, summary_path)
        print(f"Summary saved to: {summary_path}")

    # Print statistics
    valid = sum(1 for ds in datasheets if ds.validation_status == "valid")
    invalid = len(datasheets) - valid
    print(f"\nResults: {valid} valid, {invalid} invalid")

    return 0 if invalid == 0 else 1


def cmd_decode(args) -> int:
    """Handle decode command."""
    from valve_datasheet_automation.core.vds_decoder import VDSDecoder

    # Load rules from config file
    config_dir = Path(__file__).parent / "config"
    rules_path = config_dir / "vds_rules.yaml"
    decoder = VDSDecoder(rules_path=rules_path if rules_path.exists() else None)

    try:
        decoded = decoder.decode(args.vds_no)
    except VDSDecodingError as e:
        print(f"Decoding failed: {e}", file=sys.stderr)
        return 1

    print(f"VDS Number: {decoded.raw_vds}")
    print(f"Valve Type: {decoded.valve_type_full}")
    print(f"Valve Prefix: {decoded.valve_type_prefix.value} ({decoded.valve_type_prefix.full_name})")
    print(f"Bore Type: {decoded.bore_type.value} ({decoded.bore_type.full_name})")
    print(f"Piping Class: {decoded.piping_class}")
    print(f"End Connection: {decoded.end_connection.value} ({decoded.end_connection.full_name})")
    print(f"NACE Compliant: {decoded.is_nace_compliant}")
    print(f"Low Temperature: {decoded.is_low_temp}")
    print(f"Metal Seated: {decoded.is_metal_seated}")
    print(f"Primary Standard: {decoded.primary_standard}")

    return 0


def cmd_validate(args) -> int:
    """Handle validate command."""
    from valve_datasheet_automation.core.vds_decoder import VDSDecoder

    # Load rules from config file
    config_dir = Path(__file__).parent / "config"
    rules_path = config_dir / "vds_rules.yaml"
    decoder = VDSDecoder(rules_path=rules_path if rules_path.exists() else None)
    is_valid, error = decoder.validate(args.vds_no)

    if is_valid:
        print(f"VDS '{args.vds_no}' is VALID")
        return 0
    else:
        print(f"VDS '{args.vds_no}' is INVALID")
        print(f"Error: {error}")
        return 1


def cmd_list(args) -> int:
    """Handle list command."""
    data_dir = args.data_dir
    if not data_dir:
        possible_paths = [
            Path(__file__).parent.parent / "unstructured",
            Path.cwd() / "unstructured",
        ]
        for p in possible_paths:
            if p.exists():
                data_dir = p
                break

    config_dir = Path(__file__).parent / "config"
    engine = DatasheetEngine(config_dir=config_dir, data_dir=data_dir)

    if args.what == "prefixes":
        print("Supported valve type prefixes:")
        for prefix in engine.supported_valve_types:
            print(f"  {prefix}")

    elif args.what == "classes":
        print("Available piping classes:")
        classes = engine.available_piping_classes
        for cls in classes:
            print(f"  {cls}")
        print(f"\nTotal: {len(classes)} classes")

    elif args.what == "vds":
        print("Indexed VDS numbers:")
        vds_list = engine.indexed_vds_numbers
        for vds in vds_list[:20]:  # Show first 20
            print(f"  {vds}")
        if len(vds_list) > 20:
            print(f"  ... and {len(vds_list) - 20} more")
        print(f"\nTotal: {len(vds_list)} VDS numbers")

    return 0


if __name__ == "__main__":
    sys.exit(main())
