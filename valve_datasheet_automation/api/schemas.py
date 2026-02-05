"""
Pydantic schemas for API request/response models.
"""

from typing import Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


# === Request Schemas ===

class GenerateDatasheetRequest(BaseModel):
    """Request body for generating a datasheet."""
    vds_no: str = Field(..., description="VDS number (e.g., BSFA1R)", min_length=5)


class BatchGenerateRequest(BaseModel):
    """Request body for batch generation."""
    vds_numbers: list[str] = Field(..., description="List of VDS numbers")


# === Response Schemas ===

class DecodedVDSResponse(BaseModel):
    """Response for VDS decoding."""
    raw_vds: str
    valve_type_prefix: str
    valve_type_name: str
    valve_type_full: str
    bore_type: str
    bore_type_name: str
    piping_class: str
    end_connection: str
    end_connection_name: str
    is_nace_compliant: bool
    is_low_temp: bool
    is_metal_seated: bool
    primary_standard: str


class ValidationResponse(BaseModel):
    """Response for VDS validation."""
    vds_no: str
    is_valid: bool
    error: Optional[str] = None


class FieldTraceabilityResponse(BaseModel):
    """Traceability information for a field."""
    source_type: str
    source_document: Optional[str] = None
    source_value: Optional[str] = None
    derivation_rule: Optional[str] = None
    clause_reference: Optional[str] = None
    confidence: float
    notes: Optional[str] = None


class DatasheetFieldResponse(BaseModel):
    """A single field in the datasheet."""
    field_name: str
    display_name: str
    section: str
    value: Any
    is_required: bool
    is_populated: bool
    validation_status: str
    traceability: FieldTraceabilityResponse


class CompletionInfo(BaseModel):
    """Completion statistics."""
    populated: int
    total: int
    percentage: float


class DatasheetMetadata(BaseModel):
    """Metadata for a generated datasheet."""
    generated_at: datetime
    generation_version: str
    validation_status: str
    validation_errors: list[str]
    warnings: list[str]
    completion: CompletionInfo


class DatasheetResponse(BaseModel):
    """Complete datasheet response."""
    metadata: DatasheetMetadata
    sections: dict[str, list[DatasheetFieldResponse]]


class FlatDatasheetResponse(BaseModel):
    """Flat datasheet response (field_name -> value)."""
    vds_no: str
    data: dict[str, Any]
    validation_status: str
    completion_percentage: float


# === Metadata Response Schemas ===

class ValveTypeInfo(BaseModel):
    """Information about a valve type."""
    prefix: str
    name: str
    standards: list[str] = []


class PipingClassInfo(BaseModel):
    """Information about a piping class."""
    class_name: str
    material: Optional[str] = None
    description: Optional[str] = None


class VDSIndexEntry(BaseModel):
    """A VDS index entry."""
    vds_no: str
    valve_type: Optional[str] = None
    piping_class: Optional[str] = None


class MetadataResponse(BaseModel):
    """General metadata response."""
    valve_types: list[ValveTypeInfo]
    piping_classes: list[str]
    end_connections: list[dict[str, str]]
    bore_types: list[dict[str, str]]
    pressure_classes: list[str]


class VDSListResponse(BaseModel):
    """Response for VDS list."""
    vds_numbers: list[str]
    total: int


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    data_loaded: bool
    vds_index_count: int
    piping_classes_count: int


# === Valve Type Template Schemas ===

class TemplateFieldInfo(BaseModel):
    """A single field in a valve type template."""
    key: str
    label: str


class ValveTypeTemplate(BaseModel):
    """Template definition for a valve type."""
    display_name: str
    prefixes: list[str]
    construction_fields: list[TemplateFieldInfo]
    material_fields: list[TemplateFieldInfo]


class ValveTypeTemplatesResponse(BaseModel):
    """Response containing all valve type templates."""
    templates: dict[str, ValveTypeTemplate]
    default_template: str
