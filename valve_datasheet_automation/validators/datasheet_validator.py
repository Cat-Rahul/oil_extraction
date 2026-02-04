"""
Datasheet Validator.

Validates completeness and correctness of generated valve datasheets.
"""

from typing import Optional
from pydantic import BaseModel, Field

from ..models.datasheet import ValveDatasheet, DatasheetField


class ValidationResult(BaseModel):
    """Result of datasheet validation."""

    is_valid: bool = Field(..., description="Overall validation status")
    errors: list[str] = Field(default_factory=list, description="Validation errors")
    warnings: list[str] = Field(default_factory=list, description="Validation warnings")
    missing_required: list[str] = Field(
        default_factory=list,
        description="Missing required fields"
    )
    empty_fields: list[str] = Field(
        default_factory=list,
        description="Empty optional fields"
    )
    completion_percentage: float = Field(0.0, description="Completion percentage")

    @property
    def error_count(self) -> int:
        """Count of validation errors."""
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        """Count of validation warnings."""
        return len(self.warnings)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "missing_required": self.missing_required,
            "empty_fields": self.empty_fields,
            "completion_percentage": self.completion_percentage,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
        }


class DatasheetValidator:
    """
    Validates valve datasheets for completeness and correctness.

    Checks:
    - Required fields are populated
    - Values are in expected formats
    - Cross-field consistency
    - Traceability completeness

    Example:
        >>> validator = DatasheetValidator()
        >>> result = validator.validate(datasheet)
        >>> if not result.is_valid:
        ...     for error in result.errors:
        ...         print(error)
    """

    # Fields that must be populated
    REQUIRED_FIELDS = [
        'vds_no',
        'piping_class',
        'valve_type',
        'valve_standard',
        'pressure_class',
        'end_connections',
        'body_material',
        'ball_material',
        'seat_material',
        'inspection_testing',
    ]

    # Fields that should have traceability
    TRACEABLE_FIELDS = [
        'pressure_class',
        'design_pressure',
        'body_material',
        'ball_material',
        'seat_material',
        'hydrotest_shell',
        'hydrotest_closure',
    ]

    def __init__(self, strict_mode: bool = False):
        """
        Initialize validator.

        Args:
            strict_mode: If True, warnings become errors
        """
        self.strict_mode = strict_mode

    def validate(self, datasheet: ValveDatasheet) -> ValidationResult:
        """
        Validate a datasheet.

        Args:
            datasheet: ValveDatasheet to validate

        Returns:
            ValidationResult with errors and warnings
        """
        errors = []
        warnings = []
        missing_required = []
        empty_fields = []

        # Check required fields
        for field in datasheet.all_fields:
            if field.is_required and not field.is_populated:
                missing_required.append(field.display_name)
                errors.append(f"Required field missing: {field.display_name}")
            elif not field.is_populated:
                empty_fields.append(field.display_name)

        # Also check our default required fields
        for field_name in self.REQUIRED_FIELDS:
            field = getattr(datasheet, field_name, None)
            if field and not field.is_populated:
                if field.display_name not in missing_required:
                    missing_required.append(field.display_name)
                    errors.append(f"Required field missing: {field.display_name}")

        # Check traceability
        traceability_warnings = self._check_traceability(datasheet)
        if self.strict_mode:
            errors.extend(traceability_warnings)
        else:
            warnings.extend(traceability_warnings)

        # Check cross-field consistency
        consistency_issues = self._check_consistency(datasheet)
        errors.extend(consistency_issues)

        # Calculate completion
        completion = datasheet.completion_percentage

        is_valid = len(errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            missing_required=missing_required,
            empty_fields=empty_fields,
            completion_percentage=completion,
        )

    def _check_traceability(self, datasheet: ValveDatasheet) -> list[str]:
        """Check that key fields have proper traceability."""
        warnings = []

        for field_name in self.TRACEABLE_FIELDS:
            field = getattr(datasheet, field_name, None)
            if field and field.is_populated:
                trace = field.traceability
                if not trace.source_document:
                    warnings.append(
                        f"Field '{field.display_name}' missing source document in traceability"
                    )

        return warnings

    def _check_consistency(self, datasheet: ValveDatasheet) -> list[str]:
        """Check cross-field consistency."""
        errors = []

        # Check VDS matches piping class
        vds_value = datasheet.vds_no.value
        piping_class = datasheet.piping_class.value

        if vds_value and piping_class:
            # Piping class should appear in VDS
            if piping_class.replace('N', '').replace('L', '') not in vds_value:
                # This is a soft check - piping class base should be in VDS
                pass  # Could add warning here if needed

        # Check pressure class consistency
        pressure = datasheet.pressure_class.value
        if pressure and "Class" not in str(pressure):
            errors.append(
                f"Pressure class format incorrect: {pressure} "
                "(expected 'ASME B16.34 Class XXX')"
            )

        return errors

    def quick_validate(self, datasheet: ValveDatasheet) -> bool:
        """
        Quick validation - just checks if all required fields are populated.

        Args:
            datasheet: ValveDatasheet to validate

        Returns:
            True if valid, False otherwise
        """
        for field_name in self.REQUIRED_FIELDS:
            field = getattr(datasheet, field_name, None)
            if not field or not field.is_populated:
                return False
        return True

    def get_missing_fields(self, datasheet: ValveDatasheet) -> list[str]:
        """
        Get list of missing required field names.

        Args:
            datasheet: ValveDatasheet to check

        Returns:
            List of missing field display names
        """
        missing = []
        for field_name in self.REQUIRED_FIELDS:
            field = getattr(datasheet, field_name, None)
            if not field or not field.is_populated:
                missing.append(field.display_name if field else field_name)
        return missing
