"""
Valve Datasheet output models.

This module contains the data models for the generated valve datasheet,
including field-level traceability for every value.
"""

from enum import Enum
from typing import Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class FieldSource(str, Enum):
    """Data source types for datasheet fields."""
    VDS = "Selected based on VDS No"
    PMS = "Automated based on PMS class"
    VALVE_STANDARD = "As per valve standard"
    PMS_AND_STANDARD = "As per PMS Base material and Valve Standard"
    VDS_INDEX = "From VDS Index lookup"
    PROJECT_SPECIFIC = "Project Specific"
    CALCULATED = "Calculated"
    FIXED = "Fixed value"
    NOT_APPLICABLE = "Not Applicable for this Valve Type"
    UNKNOWN = "Unknown source"

    @property
    def is_automatic(self) -> bool:
        """Check if this source is automatic (not manual input)."""
        return self in [
            self.VDS, self.PMS, self.VALVE_STANDARD,
            self.PMS_AND_STANDARD, self.VDS_INDEX, self.CALCULATED, self.FIXED
        ]


class FieldTraceability(BaseModel):
    """
    Traceability information for a single datasheet field.

    Every field in the output datasheet has traceability information
    that documents where the value came from and how it was derived.

    Attributes:
        source_type: The type of data source used
        source_document: Specific document or reference (e.g., "PMS Class A1")
        source_value: Original value from source before any transformation
        derivation_rule: Rule or formula applied to derive the value
        clause_reference: Reference to specific clause (e.g., "API 6D 5.2")
        confidence: Confidence level (1.0 = certain, <1.0 = inferred)
        notes: Additional notes about the derivation
    """

    source_type: FieldSource = Field(
        default=FieldSource.UNKNOWN,
        description="Type of data source"
    )
    source_document: Optional[str] = Field(
        default=None,
        description="Specific source document or reference"
    )
    source_value: Optional[str] = Field(
        default=None,
        description="Original value from source"
    )
    derivation_rule: Optional[str] = Field(
        default=None,
        description="Rule or formula used for derivation"
    )
    clause_reference: Optional[str] = Field(
        default=None,
        description="Standard clause reference"
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence level (0-1)"
    )
    notes: Optional[str] = Field(
        default=None,
        description="Additional notes"
    )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "source_type": self.source_type.value,
            "source_document": self.source_document,
            "source_value": self.source_value,
            "derivation_rule": self.derivation_rule,
            "clause_reference": self.clause_reference,
            "confidence": self.confidence,
            "notes": self.notes,
        }


class DatasheetField(BaseModel):
    """
    A single field in the valve datasheet with its value and traceability.

    Attributes:
        field_name: Internal name of the field
        display_name: Human-readable display name
        section: Section of the datasheet (Header, Design, Material, etc.)
        value: The field value (can be any type)
        traceability: Source and derivation information
        is_required: Whether this field is mandatory
        is_populated: Whether the field has a non-empty value
    """

    field_name: str = Field(..., description="Internal field identifier")
    display_name: str = Field(default="", description="Human-readable name")
    section: str = Field(..., description="Datasheet section")
    value: Any = Field(default=None, description="Field value")
    traceability: FieldTraceability = Field(
        default_factory=FieldTraceability,
        description="Traceability information"
    )
    is_required: bool = Field(default=False, description="Is field required")

    def model_post_init(self, __context) -> None:
        """Set display name from field name if not provided."""
        if not self.display_name:
            # Convert snake_case to Title Case
            display = self.field_name.replace("_", " ").title()
            object.__setattr__(self, 'display_name', display)

    @property
    def is_populated(self) -> bool:
        """Check if field has a non-empty value."""
        if self.value is None:
            return False
        if isinstance(self.value, str) and not self.value.strip():
            return False
        return True

    @property
    def validation_status(self) -> str:
        """Get validation status for this field."""
        if self.is_required and not self.is_populated:
            return "MISSING"
        if not self.is_populated:
            return "EMPTY"
        if self.traceability.confidence < 0.8:
            return "LOW_CONFIDENCE"
        return "OK"

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "field_name": self.field_name,
            "display_name": self.display_name,
            "section": self.section,
            "value": self.value,
            "is_required": self.is_required,
            "is_populated": self.is_populated,
            "validation_status": self.validation_status,
            "traceability": self.traceability.to_dict(),
        }


class DatasheetSection(str, Enum):
    """Sections of the valve datasheet."""
    HEADER = "Header"
    DESIGN = "Design"
    CONFIGURATION = "Configuration"
    CONSTRUCTION = "Construction"
    MATERIAL = "Material"
    TESTING = "Testing"
    GENERAL = "General"


class ValveDatasheet(BaseModel):
    """
    Complete valve datasheet with all fields and metadata.

    This is the main output model containing all 35+ fields
    organized by section with full traceability.

    Sections:
        - Header: VDS No, Piping Class, Size Range, Valve Type, Service
        - Design: Valve Standard, Pressure Class, Design Pressure, etc.
        - Configuration: End Connections, Face-to-Face, Operation
        - Construction: Body, Ball, Stem, Seat, Locks
        - Material: All material specifications
        - Testing: Inspection, Testing, Certification
    """

    # === HEADER SECTION ===
    vds_no: DatasheetField = Field(..., description="VDS Number")
    piping_class: DatasheetField = Field(..., description="Piping Class")
    size_range: DatasheetField = Field(..., description="Size Range")
    valve_type: DatasheetField = Field(..., description="Valve Type")
    service: DatasheetField = Field(..., description="Service")

    # === DESIGN SECTION ===
    valve_standard: DatasheetField = Field(..., description="Valve Standard")
    pressure_class: DatasheetField = Field(..., description="Pressure Class")
    design_pressure: DatasheetField = Field(..., description="Design Pressure")
    corrosion_allowance: DatasheetField = Field(..., description="Corrosion Allowance")
    sour_service: DatasheetField = Field(..., description="Sour Service Requirements")

    # === CONFIGURATION SECTION ===
    end_connections: DatasheetField = Field(..., description="End Connections")
    face_to_face: DatasheetField = Field(..., description="Face-to-Face Dimension")
    operation: DatasheetField = Field(..., description="Operation")

    # === CONSTRUCTION SECTION ===
    body_construction: DatasheetField = Field(..., description="Body Construction")
    ball_construction: Optional[DatasheetField] = Field(default=None, description="Ball Construction (Ball valves)")
    disc_construction: Optional[DatasheetField] = Field(default=None, description="Disc Construction (Butterfly/Check/Globe)")
    wedge_construction: Optional[DatasheetField] = Field(default=None, description="Wedge Construction (Gate valves)")
    stem_construction: DatasheetField = Field(..., description="Stem Construction")
    shaft_construction: Optional[DatasheetField] = Field(default=None, description="Shaft Construction (Butterfly valves)")
    seat_construction: DatasheetField = Field(..., description="Seat Construction")
    locks: Optional[DatasheetField] = Field(default=None, description="Locks")
    back_seat_construction: Optional[DatasheetField] = Field(default=None, description="Back Seat Construction (Gate/Globe valves)")
    packing_construction: Optional[DatasheetField] = Field(default=None, description="Packing Construction (Gate/Globe valves)")
    bonnet_construction: Optional[DatasheetField] = Field(default=None, description="Bonnet Construction (Needle valves)")

    # === MATERIAL SECTION ===
    body_material: DatasheetField = Field(..., description="Body Material")
    ball_material: Optional[DatasheetField] = Field(default=None, description="Ball Material (Ball valves)")
    disc_material: Optional[DatasheetField] = Field(default=None, description="Disc Material (Butterfly/Check/Globe)")
    wedge_material: Optional[DatasheetField] = Field(default=None, description="Wedge Material (Gate valves)")
    trim_material: Optional[DatasheetField] = Field(default=None, description="Trim Material")
    seat_material: DatasheetField = Field(..., description="Seat Material")
    seal_material: Optional[DatasheetField] = Field(default=None, description="Seal Material")
    stem_material: DatasheetField = Field(..., description="Stem Material")
    shaft_material: Optional[DatasheetField] = Field(default=None, description="Shaft Material (Butterfly valves)")
    gland_material: Optional[DatasheetField] = Field(default=None, description="Gland Material")
    gland_packing: Optional[DatasheetField] = Field(default=None, description="Gland Packing")
    lever_handwheel: Optional[DatasheetField] = Field(default=None, description="Lever / Handwheel")
    spring_material: Optional[DatasheetField] = Field(default=None, description="Spring")
    gaskets: DatasheetField = Field(..., description="Gaskets")
    bolts: DatasheetField = Field(..., description="Bolts")
    nuts: DatasheetField = Field(..., description="Nuts")
    needle_material: Optional[DatasheetField] = Field(default=None, description="Needle Material (Needle/DBB valves)")
    hinge_pin_material: Optional[DatasheetField] = Field(default=None, description="Hinge/Hinge Pin Material (Check valves)")

    # === TESTING SECTION ===
    marking_purchaser: DatasheetField = Field(..., description="Marking - Purchaser")
    marking_manufacturer: DatasheetField = Field(..., description="Marking - Manufacturer")
    inspection_testing: DatasheetField = Field(..., description="Inspection/Testing")
    leakage_rate: DatasheetField = Field(..., description="Leakage Rate")
    hydrotest_shell: DatasheetField = Field(..., description="Hydrotest Shell")
    hydrotest_closure: DatasheetField = Field(..., description="Hydrotest Closure")
    pneumatic_test: DatasheetField = Field(..., description="Pneumatic LP Test")
    material_certification: DatasheetField = Field(..., description="Material Certification")
    fire_rating: DatasheetField = Field(..., description="Fire Rating")
    finish: DatasheetField = Field(..., description="Finish")

    # === METADATA ===
    generated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Generation timestamp"
    )
    generation_version: str = Field(
        default="1.0.0",
        description="Generator version"
    )
    validation_status: str = Field(
        default="pending",
        description="Overall validation status"
    )
    validation_errors: list[str] = Field(
        default_factory=list,
        description="Validation errors"
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Warnings"
    )

    @property
    def all_fields(self) -> list[DatasheetField]:
        """Get all datasheet fields as a list (including optional fields that are set)."""
        field_names = [
            # Header
            'vds_no', 'piping_class', 'size_range', 'valve_type', 'service',
            # Design
            'valve_standard', 'pressure_class', 'design_pressure',
            'corrosion_allowance', 'sour_service',
            # Configuration
            'end_connections', 'face_to_face', 'operation',
            # Construction (includes optional valve-type-specific fields)
            'body_construction', 'ball_construction', 'disc_construction',
            'wedge_construction', 'stem_construction', 'shaft_construction',
            'seat_construction', 'locks', 'back_seat_construction',
            'packing_construction', 'bonnet_construction',
            # Material (includes optional valve-type-specific fields)
            'body_material', 'ball_material', 'disc_material', 'wedge_material',
            'trim_material', 'seat_material', 'seal_material', 'stem_material',
            'shaft_material', 'gland_material', 'gland_packing',
            'lever_handwheel', 'spring_material', 'gaskets', 'bolts', 'nuts',
            'needle_material', 'hinge_pin_material',
            # Testing
            'marking_purchaser', 'marking_manufacturer', 'inspection_testing',
            'leakage_rate', 'hydrotest_shell', 'hydrotest_closure',
            'pneumatic_test', 'material_certification', 'fire_rating', 'finish'
        ]
        # Only return fields that are not None
        return [getattr(self, name) for name in field_names if getattr(self, name) is not None]

    @property
    def fields_by_section(self) -> dict[str, list[DatasheetField]]:
        """Get fields organized by section."""
        sections = {}
        for field in self.all_fields:
            section = field.section
            if section not in sections:
                sections[section] = []
            sections[section].append(field)
        return sections

    @property
    def populated_count(self) -> int:
        """Count of populated fields."""
        return sum(1 for f in self.all_fields if f.is_populated)

    @property
    def total_count(self) -> int:
        """Total number of fields."""
        return len(self.all_fields)

    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage."""
        if self.total_count == 0:
            return 0.0
        return (self.populated_count / self.total_count) * 100

    @property
    def is_valid(self) -> bool:
        """Check if datasheet passes validation."""
        return self.validation_status == "valid" and len(self.validation_errors) == 0

    def get_missing_required_fields(self) -> list[DatasheetField]:
        """Get list of required fields that are not populated."""
        return [f for f in self.all_fields if f.is_required and not f.is_populated]

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON export."""
        return {
            "metadata": {
                "generated_at": self.generated_at.isoformat(),
                "generation_version": self.generation_version,
                "validation_status": self.validation_status,
                "validation_errors": self.validation_errors,
                "warnings": self.warnings,
                "completion": {
                    "populated": self.populated_count,
                    "total": self.total_count,
                    "percentage": round(self.completion_percentage, 1),
                },
            },
            "sections": {
                section: [f.to_dict() for f in fields]
                for section, fields in self.fields_by_section.items()
            },
        }

    def to_flat_dict(self) -> dict:
        """Convert to flat dictionary (field_name -> value), only including populated fields."""
        return {f.field_name: f.value for f in self.all_fields if f.is_populated}


# Factory function for creating empty datasheet fields
def create_field(
    field_name: str,
    section: str,
    value: Any = None,
    source_type: FieldSource = FieldSource.UNKNOWN,
    source_document: Optional[str] = None,
    is_required: bool = False,
    **trace_kwargs
) -> DatasheetField:
    """
    Factory function to create a DatasheetField with traceability.

    Args:
        field_name: Internal field identifier
        section: Datasheet section name
        value: Field value
        source_type: Data source type
        source_document: Source document reference
        is_required: Whether field is required
        **trace_kwargs: Additional traceability kwargs

    Returns:
        DatasheetField instance
    """
    traceability = FieldTraceability(
        source_type=source_type,
        source_document=source_document,
        **trace_kwargs
    )
    return DatasheetField(
        field_name=field_name,
        section=section,
        value=value,
        traceability=traceability,
        is_required=is_required,
    )
