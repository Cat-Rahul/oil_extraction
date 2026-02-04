"""
Traceability Report Generator.

Generates detailed traceability reports showing the source
of every field value in a datasheet.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from ..models.datasheet import ValveDatasheet, FieldSource


class TraceabilityReport:
    """
    Generates traceability reports for valve datasheets.

    Shows the source of every field value, enabling verification
    and audit of generated datasheets.

    Example:
        >>> report = TraceabilityReport()
        >>> text = report.generate(datasheet)
        >>> print(text)
    """

    def __init__(self):
        """Initialize report generator."""
        pass

    def generate(
        self,
        datasheet: ValveDatasheet,
        output_path: Optional[Path] = None,
        format: str = "text"
    ) -> str:
        """
        Generate traceability report.

        Args:
            datasheet: ValveDatasheet to report on
            output_path: Optional path to write report
            format: Output format ("text" or "markdown")

        Returns:
            Report string
        """
        if format == "markdown":
            report = self._generate_markdown(datasheet)
        else:
            report = self._generate_text(datasheet)

        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)

        return report

    def _generate_text(self, datasheet: ValveDatasheet) -> str:
        """Generate plain text report."""
        lines = []

        # Header
        lines.append("=" * 70)
        lines.append("VALVE DATASHEET TRACEABILITY REPORT")
        lines.append("=" * 70)
        lines.append("")
        lines.append(f"VDS No: {datasheet.vds_no.value}")
        lines.append(f"Generated: {datasheet.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        lines.append(f"Version: {datasheet.generation_version}")
        lines.append(f"Status: {datasheet.validation_status.upper()}")
        lines.append(f"Completion: {datasheet.completion_percentage:.1f}%")
        lines.append("")

        # Source distribution
        lines.append("-" * 70)
        lines.append("SOURCE DISTRIBUTION")
        lines.append("-" * 70)
        distribution = self._calculate_source_distribution(datasheet)
        for source, count in distribution.items():
            lines.append(f"  {source}: {count} fields")
        lines.append("")

        # Field details by section
        lines.append("-" * 70)
        lines.append("FIELD TRACEABILITY")
        lines.append("-" * 70)

        for section, fields in datasheet.fields_by_section.items():
            lines.append("")
            lines.append(f"[{section}]")
            lines.append("")

            for field in fields:
                trace = field.traceability
                lines.append(f"  {field.display_name}:")
                lines.append(f"    Value: {field.value or '(empty)'}")
                lines.append(f"    Source: {trace.source_type.value}")
                if trace.source_document:
                    lines.append(f"    Document: {trace.source_document}")
                if trace.derivation_rule:
                    lines.append(f"    Rule: {trace.derivation_rule}")
                if trace.clause_reference:
                    lines.append(f"    Clause: {trace.clause_reference}")
                if trace.notes:
                    lines.append(f"    Notes: {trace.notes}")
                lines.append("")

        # Errors and warnings
        if datasheet.validation_errors:
            lines.append("-" * 70)
            lines.append("VALIDATION ERRORS")
            lines.append("-" * 70)
            for error in datasheet.validation_errors:
                lines.append(f"  - {error}")
            lines.append("")

        if datasheet.warnings:
            lines.append("-" * 70)
            lines.append("WARNINGS")
            lines.append("-" * 70)
            for warning in datasheet.warnings:
                lines.append(f"  - {warning}")
            lines.append("")

        lines.append("=" * 70)
        lines.append("END OF REPORT")
        lines.append("=" * 70)

        return "\n".join(lines)

    def _generate_markdown(self, datasheet: ValveDatasheet) -> str:
        """Generate Markdown report."""
        lines = []

        # Header
        lines.append("# Valve Datasheet Traceability Report")
        lines.append("")
        lines.append("## Summary")
        lines.append("")
        lines.append(f"| Property | Value |")
        lines.append(f"|----------|-------|")
        lines.append(f"| VDS No | {datasheet.vds_no.value} |")
        lines.append(f"| Generated | {datasheet.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')} |")
        lines.append(f"| Version | {datasheet.generation_version} |")
        lines.append(f"| Status | **{datasheet.validation_status.upper()}** |")
        lines.append(f"| Completion | {datasheet.completion_percentage:.1f}% |")
        lines.append("")

        # Source distribution
        lines.append("## Source Distribution")
        lines.append("")
        distribution = self._calculate_source_distribution(datasheet)
        lines.append("| Source Type | Count |")
        lines.append("|-------------|-------|")
        for source, count in distribution.items():
            lines.append(f"| {source} | {count} |")
        lines.append("")

        # Field details by section
        lines.append("## Field Traceability")
        lines.append("")

        for section, fields in datasheet.fields_by_section.items():
            lines.append(f"### {section}")
            lines.append("")
            lines.append("| Field | Value | Source | Document |")
            lines.append("|-------|-------|--------|----------|")

            for field in fields:
                trace = field.traceability
                value = str(field.value or "-")[:50]  # Truncate long values
                source = trace.source_type.value[:30]
                doc = (trace.source_document or "-")[:30]
                lines.append(f"| {field.display_name} | {value} | {source} | {doc} |")

            lines.append("")

        # Errors
        if datasheet.validation_errors:
            lines.append("## Validation Errors")
            lines.append("")
            for error in datasheet.validation_errors:
                lines.append(f"- {error}")
            lines.append("")

        # Warnings
        if datasheet.warnings:
            lines.append("## Warnings")
            lines.append("")
            for warning in datasheet.warnings:
                lines.append(f"- {warning}")
            lines.append("")

        return "\n".join(lines)

    def _calculate_source_distribution(
        self,
        datasheet: ValveDatasheet
    ) -> dict[str, int]:
        """Calculate distribution of field sources."""
        distribution = {}

        for field in datasheet.all_fields:
            source = field.traceability.source_type.value
            distribution[source] = distribution.get(source, 0) + 1

        # Sort by count descending
        return dict(sorted(distribution.items(), key=lambda x: -x[1]))

    def generate_audit_trail(
        self,
        datasheet: ValveDatasheet
    ) -> list[dict]:
        """
        Generate audit trail for all field values.

        Returns:
            List of audit entries with full traceability
        """
        audit = []

        for field in datasheet.all_fields:
            trace = field.traceability
            entry = {
                "field_name": field.field_name,
                "display_name": field.display_name,
                "section": field.section,
                "value": field.value,
                "is_populated": field.is_populated,
                "source_type": trace.source_type.value,
                "source_document": trace.source_document,
                "source_value": trace.source_value,
                "derivation_rule": trace.derivation_rule,
                "clause_reference": trace.clause_reference,
                "confidence": trace.confidence,
                "notes": trace.notes,
            }
            audit.append(entry)

        return audit
