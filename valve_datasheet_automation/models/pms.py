"""
PMS (Piping Material Specification) data models.

This module contains data models for representing piping material
specification data used in valve datasheet generation.
"""

from typing import Optional
from pydantic import BaseModel, Field


class PMSClass(BaseModel):
    """
    Piping Material Specification class data.

    Represents a single piping class with all associated specifications
    including pressure ratings, materials, and services.

    Attributes:
        piping_class: Class identifier (e.g., A1, B1N, G1LN)
        pressure_rating: Pressure class rating (e.g., "150#", "300#")
        material_group: Material group code (e.g., "1.1", "2.3")
        base_material: Base material specification (e.g., "CS", "SS316L")
        corrosion_allowance: Corrosion allowance (e.g., "3 mm")
        service: Service description (e.g., "Cooling Water, Diesel, Steam")
        design_pressure_min: Minimum design pressure with temp
        design_pressure_max: Maximum design pressure with temp
        design_temp_min: Minimum design temperature
        design_temp_max: Maximum design temperature
        sheet_no: Reference sheet number in PMS document
    """

    piping_class: str = Field(..., description="Piping class code")
    pressure_rating: str = Field(default="", description="Pressure rating")
    material_group: str = Field(default="", description="Material group code")
    base_material: str = Field(default="", description="Base material spec")
    corrosion_allowance: str = Field(default="", description="Corrosion allowance")
    service: str = Field(default="", description="Service description")
    design_pressure_min: str = Field(default="", description="Min design pressure")
    design_pressure_max: str = Field(default="", description="Max design pressure")
    design_temp_min: str = Field(default="", description="Min design temperature")
    design_temp_max: str = Field(default="", description="Max design temperature")
    sheet_no: str = Field(default="", description="PMS sheet number")

    @property
    def pressure_class_numeric(self) -> Optional[int]:
        """Extract numeric pressure class (150, 300, etc.)."""
        import re
        match = re.search(r'(\d+)', self.pressure_rating)
        if match:
            return int(match.group(1))
        return None

    @property
    def pressure_class_formatted(self) -> str:
        """Get formatted pressure class string."""
        if self.pressure_class_numeric:
            return f"Class {self.pressure_class_numeric}"
        return self.pressure_rating

    @property
    def design_pressure_range(self) -> str:
        """Get design pressure range as formatted string."""
        parts = []
        if self.design_pressure_min:
            parts.append(self.design_pressure_min)
        if self.design_pressure_max:
            parts.append(self.design_pressure_max)
        return ", ".join(parts) if parts else "-"

    @property
    def is_nace_class(self) -> bool:
        """Check if this is a NACE-compliant class (contains N suffix)."""
        return 'N' in self.piping_class.upper()

    @property
    def is_low_temp_class(self) -> bool:
        """Check if this is a low-temperature class (contains L suffix)."""
        return 'L' in self.piping_class.upper()

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "piping_class": self.piping_class,
            "pressure_rating": self.pressure_rating,
            "pressure_class_numeric": self.pressure_class_numeric,
            "pressure_class_formatted": self.pressure_class_formatted,
            "material_group": self.material_group,
            "base_material": self.base_material,
            "corrosion_allowance": self.corrosion_allowance,
            "service": self.service,
            "design_pressure_min": self.design_pressure_min,
            "design_pressure_max": self.design_pressure_max,
            "design_pressure_range": self.design_pressure_range,
            "design_temp_min": self.design_temp_min,
            "design_temp_max": self.design_temp_max,
            "sheet_no": self.sheet_no,
            "is_nace_class": self.is_nace_class,
            "is_low_temp_class": self.is_low_temp_class,
        }


class MaterialSpec(BaseModel):
    """
    Material specification for valve components.

    Represents material specifications for various valve parts
    including body, ball, seat, stem, etc.
    """

    component: str = Field(..., description="Component name (body, ball, etc.)")
    material_code: str = Field(..., description="Material code (e.g., ASTM A182-F316)")
    material_description: str = Field(default="", description="Material description")
    forged_spec: Optional[str] = Field(None, description="Forged material spec")
    cast_spec: Optional[str] = Field(None, description="Cast material spec")
    hardness_requirement: Optional[str] = Field(None, description="Hardness requirement")
    coating: Optional[str] = Field(None, description="Coating specification")
    additional_requirements: list[str] = Field(
        default_factory=list,
        description="Additional requirements (NACE, etc.)"
    )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "component": self.component,
            "material_code": self.material_code,
            "material_description": self.material_description,
            "forged_spec": self.forged_spec,
            "cast_spec": self.cast_spec,
            "hardness_requirement": self.hardness_requirement,
            "coating": self.coating,
            "additional_requirements": self.additional_requirements,
        }


class VDSIndexEntry(BaseModel):
    """
    Entry from the VDS Index containing pre-computed valve specifications.

    This represents a single row from the VDS Index table that contains
    pre-determined specifications for a specific VDS number.
    Expanded to support all valve types (Ball, Gate, Globe, Check, etc.)
    """

    vds_no: str = Field(..., description="VDS Number")
    piping_class: str = Field(default="", description="Piping Class")
    source_file: str = Field(default="", description="Source Excel file")

    # Header fields
    size_range: str = Field(default="", description="Size Range")
    valve_type: str = Field(default="", description="Valve Type")
    service: str = Field(default="", description="Service")

    # Design fields
    valve_standard: str = Field(default="", description="Valve Standard")
    pressure_class: str = Field(default="", description="Pressure Class")
    design_pressure: str = Field(default="", description="Design Pressure")
    corrosion_allowance: str = Field(default="", description="Corrosion Allowance")
    sour_service: str = Field(default="", description="Sour Service Requirements")

    # Configuration fields
    end_connections: str = Field(default="", description="End Connections")
    face_to_face: str = Field(default="", description="Face to Face Dimension")
    operation: str = Field(default="", description="Operation")

    # Construction fields
    body_construction: str = Field(default="", description="Body Construction")
    ball_construction: str = Field(default="", description="Ball Construction (Ball valves)")
    wedge_construction: str = Field(default="", description="Wedge Construction (Gate valves)")
    disc_construction: str = Field(default="", description="Disc Construction (Globe/Check)")
    stem_construction: str = Field(default="", description="Stem Construction")
    shaft_construction: str = Field(default="", description="Shaft Construction (Butterfly valves)")
    seat_construction: str = Field(default="", description="Seat Construction")
    back_seat_construction: str = Field(default="", description="Back Seat Construction")
    packing_construction: str = Field(default="", description="Packing Construction")
    locks: str = Field(default="", description="Locks")

    # Material fields
    body_material: str = Field(default="", description="Body Material")
    ball_material: str = Field(default="", description="Ball Material")
    wedge_material: str = Field(default="", description="Wedge Material")
    disc_material: str = Field(default="", description="Disc Material")
    trim_material: str = Field(default="", description="Trim Material")
    seat_material: str = Field(default="", description="Seat Material")
    seal_material: str = Field(default="", description="Seal Material")
    back_seat_material: str = Field(default="", description="Back Seat Material")
    stem_material: str = Field(default="", description="Stem Material")
    shaft_material: str = Field(default="", description="Shaft Material (Butterfly valves)")
    gland_material: str = Field(default="", description="Gland Material")
    gland_packing: str = Field(default="", description="Gland Packing")
    lever_handwheel: str = Field(default="", description="Lever / Handwheel")
    spring_material: str = Field(default="", description="Spring Material")
    gaskets: str = Field(default="", description="Gaskets")
    bolts: str = Field(default="", description="Bolts")
    nuts: str = Field(default="", description="Nuts")

    # Testing fields
    marking_purchaser: str = Field(default="", description="Marking - Purchaser")
    marking_manufacturer: str = Field(default="", description="Marking - Manufacturer")
    inspection_testing: str = Field(default="", description="Inspection - Testing")
    leakage_rate: str = Field(default="", description="Leakage Rate")
    hydrotest_shell: str = Field(default="", description="Hydrotest Shell")
    hydrotest_closure: str = Field(default="", description="Hydrotest Closure")
    pneumatic_test: str = Field(default="", description="Pneumatic Test")
    material_certification: str = Field(default="", description="Material Certification")
    fire_rating: str = Field(default="", description="Fire Rating")
    finish: str = Field(default="", description="Finish")

    # Legacy fields
    page_no: Optional[int] = Field(None, description="Page number in document")
    revision: str = Field(default="", description="Revision code")

    class Config:
        extra = "allow"  # Allow extra fields from JSON

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return self.model_dump(exclude_none=True)

    def get_field(self, field_name: str) -> Optional[str]:
        """Get a field value by name, with fallback to extra fields."""
        value = getattr(self, field_name, None)
        if value:
            return str(value)
        # Try extra fields (from Config extra="allow")
        extra = getattr(self, '__pydantic_extra__', {}) or {}
        return extra.get(field_name)
