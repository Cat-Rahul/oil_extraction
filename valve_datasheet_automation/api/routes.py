"""
API Routes for Valve Datasheet Automation.

This module provides REST API endpoints for:
- VDS decoding and validation
- Datasheet generation
- Metadata retrieval (valve types, piping classes, etc.)
"""

from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from ..core.datasheet_engine import DatasheetEngine, DatasheetGenerationError
from ..core.vds_decoder import VDSDecoder, VDSDecodingError
from .schemas import (
    GenerateDatasheetRequest,
    BatchGenerateRequest,
    DecodedVDSResponse,
    ValidationResponse,
    DatasheetResponse,
    FlatDatasheetResponse,
    DatasheetFieldResponse,
    FieldTraceabilityResponse,
    DatasheetMetadata,
    CompletionInfo,
    MetadataResponse,
    ValveTypeInfo,
    VDSListResponse,
    HealthResponse,
)


# Create router
router = APIRouter()

# Initialize engine (will be set up by the main app)
_engine: Optional[DatasheetEngine] = None


def get_engine() -> DatasheetEngine:
    """Get the datasheet engine instance."""
    global _engine
    if _engine is None:
        # Initialize with default paths
        config_dir = Path(__file__).parent.parent / "config"
        data_dir = Path(__file__).parent.parent.parent / "unstructured"
        _engine = DatasheetEngine(config_dir=config_dir, data_dir=data_dir)
    return _engine


def init_engine(config_dir: Optional[Path] = None, data_dir: Optional[Path] = None):
    """Initialize the engine with custom paths."""
    global _engine
    _engine = DatasheetEngine(config_dir=config_dir, data_dir=data_dir)


# === Health Check ===

@router.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Check API health and data loading status."""
    engine = get_engine()
    return HealthResponse(
        status="healthy",
        version=engine.VERSION,
        data_loaded=True,
        vds_index_count=len(engine.indexed_vds_numbers),
        piping_classes_count=len(engine.available_piping_classes),
    )


# === VDS Operations ===

@router.get("/vds/{vds_no}/decode", response_model=DecodedVDSResponse, tags=["VDS"])
async def decode_vds(vds_no: str):
    """
    Decode a VDS number into its constituent parts.

    - **vds_no**: VDS number string (e.g., "BSFA1R")

    Returns decoded information including valve type, bore type, piping class, etc.
    """
    engine = get_engine()
    try:
        decoded = engine.decode_vds(vds_no)
        return DecodedVDSResponse(
            raw_vds=decoded.raw_vds,
            valve_type_prefix=decoded.valve_type_prefix.value,
            valve_type_name=decoded.valve_type_prefix.full_name,
            valve_type_full=decoded.valve_type_full,
            bore_type=decoded.bore_type.value,
            bore_type_name=decoded.bore_type.full_name,
            piping_class=decoded.piping_class,
            end_connection=decoded.end_connection.value,
            end_connection_name=decoded.end_connection.full_name,
            is_nace_compliant=decoded.is_nace_compliant,
            is_low_temp=decoded.is_low_temp,
            is_metal_seated=decoded.is_metal_seated,
            primary_standard=decoded.primary_standard,
        )
    except VDSDecodingError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/vds/{vds_no}/validate", response_model=ValidationResponse, tags=["VDS"])
async def validate_vds(vds_no: str):
    """
    Validate a VDS number without generating a datasheet.

    - **vds_no**: VDS number to validate

    Returns validation result with error message if invalid.
    """
    engine = get_engine()
    is_valid, error = engine.validate_vds(vds_no)
    return ValidationResponse(
        vds_no=vds_no,
        is_valid=is_valid,
        error=error,
    )


# === Datasheet Generation ===

@router.get("/datasheet/{vds_no}", response_model=DatasheetResponse, tags=["Datasheet"])
async def get_datasheet(
    vds_no: str,
    include_traceability: bool = Query(True, description="Include traceability info"),
):
    """
    Generate a complete datasheet from a VDS number.

    - **vds_no**: VDS number (e.g., "BSFA1R")
    - **include_traceability**: Whether to include source traceability

    Returns the complete datasheet with all fields organized by section.
    """
    engine = get_engine()
    try:
        datasheet = engine.generate(vds_no)
        return _convert_datasheet_to_response(datasheet)
    except (VDSDecodingError, DatasheetGenerationError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/datasheet/{vds_no}/flat", response_model=FlatDatasheetResponse, tags=["Datasheet"])
async def get_datasheet_flat(vds_no: str):
    """
    Generate a flat datasheet (field_name -> value only).

    - **vds_no**: VDS number (e.g., "BSFA1R")

    Returns a simplified flat structure without traceability.
    """
    engine = get_engine()
    try:
        datasheet = engine.generate(vds_no)
        return FlatDatasheetResponse(
            vds_no=vds_no,
            data=datasheet.to_flat_dict(),
            validation_status=datasheet.validation_status,
            completion_percentage=datasheet.completion_percentage,
        )
    except (VDSDecodingError, DatasheetGenerationError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/datasheet/generate", response_model=DatasheetResponse, tags=["Datasheet"])
async def generate_datasheet(request: GenerateDatasheetRequest):
    """
    Generate a datasheet from VDS number (POST method).

    Alternative to GET /datasheet/{vds_no} for clients that prefer POST.
    """
    engine = get_engine()
    try:
        datasheet = engine.generate(request.vds_no)
        return _convert_datasheet_to_response(datasheet)
    except (VDSDecodingError, DatasheetGenerationError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/datasheet/batch", tags=["Datasheet"])
async def generate_batch(request: BatchGenerateRequest):
    """
    Generate datasheets for multiple VDS numbers.

    - **vds_numbers**: List of VDS numbers

    Returns a list of results with status for each.
    """
    engine = get_engine()
    results = []

    for vds_no in request.vds_numbers:
        try:
            datasheet = engine.generate(vds_no)
            results.append({
                "vds_no": vds_no,
                "status": "success",
                "data": datasheet.to_flat_dict(),
                "validation_status": datasheet.validation_status,
                "completion_percentage": datasheet.completion_percentage,
            })
        except (VDSDecodingError, DatasheetGenerationError) as e:
            results.append({
                "vds_no": vds_no,
                "status": "error",
                "error": str(e),
            })

    return {
        "total": len(request.vds_numbers),
        "successful": sum(1 for r in results if r["status"] == "success"),
        "failed": sum(1 for r in results if r["status"] == "error"),
        "results": results,
    }


# === Metadata Endpoints ===

@router.get("/metadata", response_model=MetadataResponse, tags=["Metadata"])
async def get_all_metadata():
    """
    Get all metadata for form dropdowns.

    Returns valve types, piping classes, end connections, bore types, etc.
    """
    engine = get_engine()
    decoder = engine.decoder

    # Get valve types with info
    valve_types = []
    for prefix in decoder.get_supported_prefixes():
        prefix_info = decoder.rules.get('valve_type_prefixes', {}).get(prefix, {})
        valve_types.append(ValveTypeInfo(
            prefix=prefix,
            name=prefix_info.get('name', prefix),
            standards=prefix_info.get('standards', []),
        ))

    # Get end connections
    end_connections = [
        {"code": code, "name": info.get('name', code)}
        for code, info in decoder.rules.get('end_connections', {}).items()
    ]

    # Get bore types
    bore_types = [
        {"code": code, "name": info.get('name', code)}
        for code, info in decoder.rules.get('bore_types', {}).items()
    ]

    # Standard pressure classes
    pressure_classes = ["150", "300", "600", "900", "1500", "2500"]

    return MetadataResponse(
        valve_types=valve_types,
        piping_classes=engine.available_piping_classes,
        end_connections=end_connections,
        bore_types=bore_types,
        pressure_classes=pressure_classes,
    )


@router.get("/metadata/valve-types", tags=["Metadata"])
async def get_valve_types():
    """Get list of supported valve types."""
    engine = get_engine()
    decoder = engine.decoder

    valve_types = []
    for prefix in decoder.get_supported_prefixes():
        prefix_info = decoder.rules.get('valve_type_prefixes', {}).get(prefix, {})
        valve_types.append({
            "prefix": prefix,
            "name": prefix_info.get('name', prefix),
            "standards": prefix_info.get('standards', []),
            "bore_types": prefix_info.get('bore_types', ['F', 'R']),
        })

    return {"valve_types": valve_types}


@router.get("/metadata/piping-classes", tags=["Metadata"])
async def get_piping_classes():
    """Get list of available piping classes."""
    engine = get_engine()
    return {
        "piping_classes": engine.available_piping_classes,
        "total": len(engine.available_piping_classes),
    }


@router.get("/metadata/vds-numbers", response_model=VDSListResponse, tags=["Metadata"])
async def get_vds_numbers(
    limit: int = Query(100, ge=1, le=1000, description="Max items to return"),
    offset: int = Query(0, ge=0, description="Items to skip"),
    valve_type: Optional[str] = Query(None, description="Filter by valve type prefix"),
):
    """
    Get list of indexed VDS numbers.

    - **limit**: Maximum items to return (1-1000)
    - **offset**: Items to skip for pagination
    - **valve_type**: Optional filter by valve type prefix
    """
    engine = get_engine()
    all_vds = engine.indexed_vds_numbers

    # Filter by valve type if specified
    if valve_type:
        all_vds = [v for v in all_vds if v.upper().startswith(valve_type.upper())]

    # Apply pagination
    paginated = all_vds[offset:offset + limit]

    return VDSListResponse(
        vds_numbers=paginated,
        total=len(all_vds),
    )


@router.get("/metadata/end-connections", tags=["Metadata"])
async def get_end_connections():
    """Get list of supported end connection types."""
    engine = get_engine()
    decoder = engine.decoder

    end_connections = [
        {
            "code": code,
            "name": info.get('name', code),
            "description": info.get('description', ''),
        }
        for code, info in decoder.rules.get('end_connections', {}).items()
    ]

    return {"end_connections": end_connections}


@router.get("/metadata/bore-types", tags=["Metadata"])
async def get_bore_types():
    """Get list of supported bore types."""
    engine = get_engine()
    decoder = engine.decoder

    bore_types = [
        {
            "code": code,
            "name": info.get('name', code),
        }
        for code, info in decoder.rules.get('bore_types', {}).items()
    ]

    return {"bore_types": bore_types}


# === Helper Functions ===

def _convert_datasheet_to_response(datasheet) -> DatasheetResponse:
    """Convert a ValveDatasheet to API response format."""
    sections = {}

    for section_name, fields in datasheet.fields_by_section.items():
        sections[section_name] = [
            DatasheetFieldResponse(
                field_name=f.field_name,
                display_name=f.display_name,
                section=f.section,
                value=f.value,
                is_required=f.is_required,
                is_populated=f.is_populated,
                validation_status=f.validation_status,
                traceability=FieldTraceabilityResponse(
                    source_type=f.traceability.source_type.value,
                    source_document=f.traceability.source_document,
                    source_value=f.traceability.source_value,
                    derivation_rule=f.traceability.derivation_rule,
                    clause_reference=f.traceability.clause_reference,
                    confidence=f.traceability.confidence,
                    notes=f.traceability.notes,
                ),
            )
            for f in fields
        ]

    return DatasheetResponse(
        metadata=DatasheetMetadata(
            generated_at=datasheet.generated_at,
            generation_version=datasheet.generation_version,
            validation_status=datasheet.validation_status,
            validation_errors=datasheet.validation_errors,
            warnings=datasheet.warnings,
            completion=CompletionInfo(
                populated=datasheet.populated_count,
                total=datasheet.total_count,
                percentage=round(datasheet.completion_percentage, 1),
            ),
        ),
        sections=sections,
    )
