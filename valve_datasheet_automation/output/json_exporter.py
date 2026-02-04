"""
JSON Exporter.

Exports valve datasheets to JSON format with configurable output options.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

from ..models.datasheet import ValveDatasheet


class JSONExporter:
    """
    Exports valve datasheets to JSON format.

    Supports various output configurations including:
    - Full export with all traceability
    - Compact export with values only
    - Flat export for simple key-value pairs

    Example:
        >>> exporter = JSONExporter()
        >>> exporter.export(datasheet, Path("output.json"))
    """

    def __init__(
        self,
        indent: int = 2,
        include_traceability: bool = True,
        include_metadata: bool = True,
    ):
        """
        Initialize exporter with configuration.

        Args:
            indent: JSON indentation level
            include_traceability: Include field traceability info
            include_metadata: Include generation metadata
        """
        self.indent = indent
        self.include_traceability = include_traceability
        self.include_metadata = include_metadata

    def export(
        self,
        datasheet: ValveDatasheet,
        output_path: Optional[Path] = None,
    ) -> str:
        """
        Export datasheet to JSON.

        Args:
            datasheet: ValveDatasheet to export
            output_path: Optional path to write JSON file

        Returns:
            JSON string
        """
        data = self._prepare_data(datasheet)
        json_str = json.dumps(data, indent=self.indent, ensure_ascii=False, default=str)

        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(json_str)

        return json_str

    def _prepare_data(self, datasheet: ValveDatasheet) -> dict:
        """Prepare datasheet data for JSON export."""
        data = {}

        # Add metadata
        if self.include_metadata:
            data["metadata"] = {
                "generated_at": datasheet.generated_at.isoformat(),
                "generation_version": datasheet.generation_version,
                "validation_status": datasheet.validation_status,
                "completion": {
                    "populated": datasheet.populated_count,
                    "total": datasheet.total_count,
                    "percentage": round(datasheet.completion_percentage, 1),
                },
            }

            if datasheet.validation_errors:
                data["metadata"]["validation_errors"] = datasheet.validation_errors

            if datasheet.warnings:
                data["metadata"]["warnings"] = datasheet.warnings

        # Add fields by section
        data["sections"] = {}
        for section, fields in datasheet.fields_by_section.items():
            section_data = []
            for field in fields:
                field_data = {
                    "field_name": field.field_name,
                    "display_name": field.display_name,
                    "value": field.value,
                }

                if self.include_traceability:
                    field_data["traceability"] = field.traceability.to_dict()

                section_data.append(field_data)

            data["sections"][section] = section_data

        return data

    def export_flat(
        self,
        datasheet: ValveDatasheet,
        output_path: Optional[Path] = None,
    ) -> str:
        """
        Export datasheet as flat key-value pairs.

        Args:
            datasheet: ValveDatasheet to export
            output_path: Optional path to write JSON file

        Returns:
            JSON string with flat structure
        """
        data = datasheet.to_flat_dict()

        if self.include_metadata:
            data["_metadata"] = {
                "vds_no": datasheet.vds_no.value,
                "generated_at": datasheet.generated_at.isoformat(),
                "validation_status": datasheet.validation_status,
            }

        json_str = json.dumps(data, indent=self.indent, ensure_ascii=False, default=str)

        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(json_str)

        return json_str

    def export_batch(
        self,
        datasheets: list[ValveDatasheet],
        output_dir: Path,
    ) -> list[Path]:
        """
        Export multiple datasheets to separate files.

        Args:
            datasheets: List of datasheets to export
            output_dir: Directory for output files

        Returns:
            List of output file paths
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        output_paths = []

        for ds in datasheets:
            vds_no = ds.vds_no.value or "unknown"
            filename = f"{vds_no}_datasheet.json"
            output_path = output_dir / filename

            self.export(ds, output_path)
            output_paths.append(output_path)

        return output_paths

    def export_summary(
        self,
        datasheets: list[ValveDatasheet],
        output_path: Optional[Path] = None,
    ) -> str:
        """
        Export summary of multiple datasheets.

        Args:
            datasheets: List of datasheets
            output_path: Optional path for output file

        Returns:
            JSON summary string
        """
        summary = {
            "total_datasheets": len(datasheets),
            "generated_at": datetime.utcnow().isoformat(),
            "datasheets": [],
            "statistics": {
                "valid": 0,
                "invalid": 0,
                "avg_completion": 0.0,
            }
        }

        total_completion = 0.0
        for ds in datasheets:
            entry = {
                "vds_no": ds.vds_no.value,
                "piping_class": ds.piping_class.value,
                "valve_type": ds.valve_type.value,
                "validation_status": ds.validation_status,
                "completion_percentage": round(ds.completion_percentage, 1),
                "error_count": len(ds.validation_errors),
            }
            summary["datasheets"].append(entry)

            if ds.validation_status == "valid":
                summary["statistics"]["valid"] += 1
            else:
                summary["statistics"]["invalid"] += 1

            total_completion += ds.completion_percentage

        if datasheets:
            summary["statistics"]["avg_completion"] = round(
                total_completion / len(datasheets), 1
            )

        json_str = json.dumps(summary, indent=self.indent, ensure_ascii=False)

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(json_str)

        return json_str
