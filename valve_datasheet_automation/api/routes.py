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
    ValveTypeTemplatesResponse,
    ValveTypeTemplate,
    TemplateFieldInfo,
    MLPredictionResponse,
    MLPredictionFieldResponse,
    MLFlatPredictionResponse,
    MLModelInfoResponse,
    HybridPredictionResponse,
    HybridPredictionFieldResponse,
    HybridFlatPredictionResponse,
    ComparisonFieldResponse,
    MLComparisonResponse,
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


@router.get("/metadata/valve-type-templates", response_model=ValveTypeTemplatesResponse, tags=["Metadata"])
async def get_valve_type_templates():
    """
    Get valve type field templates for dynamic UI rendering.

    Returns construction and material field lists for each valve type,
    used by the frontend to render the correct fields based on valve type.
    """
    engine = get_engine()
    raw_templates = engine.get_valve_type_templates()
    default_key = engine.get_default_template_key()

    templates = {}
    for key, tmpl in raw_templates.items():
        templates[key] = ValveTypeTemplate(
            display_name=tmpl.get('display_name', key),
            prefixes=tmpl.get('prefixes', []),
            construction_fields=[
                TemplateFieldInfo(key=f['key'], label=f['label'])
                for f in tmpl.get('construction_fields', [])
            ],
            material_fields=[
                TemplateFieldInfo(key=f['key'], label=f['label'])
                for f in tmpl.get('material_fields', [])
            ],
        )

    return ValveTypeTemplatesResponse(
        templates=templates,
        default_template=default_key,
    )


# === ML Prediction Endpoints ===

# Lazy-loaded predictor singletons
_predictor = None
_pure_ml_predictor = None


def _get_predictor():
    """Get or initialize the HYBRID predictor (default for production)."""
    global _predictor
    if _predictor is None:
        from ..ml.hybrid_predictor import HybridPredictor
        _predictor = HybridPredictor()
        if _predictor.is_available:
            _predictor.load()
    return _predictor


def _get_pure_ml_predictor():
    """Get or initialize the pure ML predictor (for comparison only)."""
    global _pure_ml_predictor
    if _pure_ml_predictor is None:
        from ..ml.predictor import ValvePredictor
        _pure_ml_predictor = ValvePredictor()
        if _pure_ml_predictor.is_available:
            _pure_ml_predictor.load()
    return _pure_ml_predictor


@router.get("/ml/info", response_model=MLModelInfoResponse, tags=["ML"])
async def ml_model_info():
    """Get information about the trained ML model."""
    predictor = _get_predictor()
    if not predictor.is_available:
        return MLModelInfoResponse(is_available=False)

    report = predictor.get_evaluation_report()
    return MLModelInfoResponse(
        is_available=True,
        train_samples=report.get("train_samples"),
        test_accuracy=report.get("test", {}).get("overall_accuracy"),
        exact_match_rate=report.get("test", {}).get("exact_match_rate"),
        target_fields=list(report.get("test", {}).get("per_field", {}).keys()),
    )


@router.get("/ml/predict/{vds_no}", response_model=HybridPredictionResponse, tags=["ML"])
async def ml_predict(vds_no: str):
    """
    Predict all datasheet fields for a VDS number using HYBRID approach.

    Uses rule-based extraction for piping_class and sour_service (100% accurate),
    and ML prediction for other fields. This is the production-recommended endpoint.

    Returns predictions with per-field confidence scores and source info.
    """
    predictor = _get_predictor()
    if not predictor.is_available:
        raise HTTPException(
            status_code=503,
            detail="ML model not trained. Run: python -m valve_datasheet_automation.ml.train"
        )

    try:
        result = predictor.predict_with_confidence(vds_no)
        predictions = {
            field: HybridPredictionFieldResponse(
                value=info["value"],
                confidence=info["confidence"],
                source=info["source"],
            )
            for field, info in result.items()
        }
        return HybridPredictionResponse(
            vds_no=vds_no,
            predictions=predictions,
            rule_based_fields=list(predictor.get_rule_based_fields()),
            ml_predicted_fields=list(predictor.get_ml_fields()),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/ml/predict/{vds_no}/flat", response_model=HybridFlatPredictionResponse, tags=["ML"])
async def ml_predict_flat(vds_no: str):
    """
    Predict datasheet fields (flat format, values only) using HYBRID approach.

    Production-recommended endpoint with rule-based piping_class extraction.
    """
    predictor = _get_predictor()
    if not predictor.is_available:
        raise HTTPException(
            status_code=503,
            detail="ML model not trained. Run: python -m valve_datasheet_automation.ml.train"
        )

    try:
        result = predictor.predict(vds_no)
        return HybridFlatPredictionResponse(
            vds_no=vds_no,
            data=result,
            rule_based_fields=list(predictor.get_rule_based_fields()),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# === Pure ML Endpoints (for comparison only) ===

@router.get("/ml/pure/predict/{vds_no}", response_model=MLPredictionResponse, tags=["ML Pure"])
async def ml_pure_predict(vds_no: str):
    """
    Predict using PURE ML only (no rule-based extraction).

    WARNING: This endpoint has lower accuracy for piping_class (~81%).
    Use /ml/predict/{vds_no} for production.
    """
    predictor = _get_pure_ml_predictor()
    if not predictor.is_available:
        raise HTTPException(
            status_code=503,
            detail="ML model not trained. Run: python -m valve_datasheet_automation.ml.train"
        )

    try:
        result = predictor.predict_with_confidence(vds_no)
        predictions = {
            field: MLPredictionFieldResponse(
                value=info["value"],
                confidence=info["confidence"],
            )
            for field, info in result.items()
        }
        return MLPredictionResponse(
            vds_no=vds_no,
            source="pure_ml",
            predictions=predictions,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# === Legacy Hybrid Endpoints (aliases to main endpoints) ===

@router.get("/ml/hybrid/predict/{vds_no}", response_model=HybridPredictionResponse, tags=["ML"], include_in_schema=False)
async def hybrid_predict(vds_no: str):
    """Alias to /ml/predict/{vds_no} - kept for backward compatibility."""
    return await ml_predict(vds_no)


@router.get("/ml/hybrid/predict/{vds_no}/flat", response_model=HybridFlatPredictionResponse, tags=["ML"], include_in_schema=False)
async def hybrid_predict_flat(vds_no: str):
    """Alias to /ml/predict/{vds_no}/flat - kept for backward compatibility."""
    return await ml_predict_flat(vds_no)


@router.get("/ml/compare/{vds_no}", response_model=MLComparisonResponse, tags=["ML Hybrid"])
async def compare_ml_vs_hybrid(vds_no: str):
    """
    Compare Pure ML vs Hybrid predictions for a VDS number.

    Shows which fields differ and why. Use this to understand the
    improvement from using rule-based extraction for deterministic fields.
    """
    pure_ml = _get_predictor()
    hybrid = _get_hybrid_predictor()

    if not pure_ml.is_available or not hybrid.is_available:
        raise HTTPException(
            status_code=503,
            detail="ML model not trained. Run: python -m valve_datasheet_automation.ml.train"
        )

    try:
        pure_ml_result = pure_ml.predict_with_confidence(vds_no)
        hybrid_result = hybrid.predict_with_confidence(vds_no)

        fields = {}
        matches = 0
        mismatches = 0
        rule_based_fields = hybrid.get_rule_based_fields()

        for field in pure_ml_result:
            pure_val = pure_ml_result[field]["value"]
            hybrid_val = hybrid_result[field]["value"]
            is_match = pure_val == hybrid_val

            if is_match:
                matches += 1
            else:
                mismatches += 1

            fields[field] = ComparisonFieldResponse(
                pure_ml_value=pure_val,
                pure_ml_confidence=pure_ml_result[field]["confidence"],
                hybrid_value=hybrid_val,
                hybrid_confidence=hybrid_result[field]["confidence"],
                source=hybrid_result[field]["source"],
                match=is_match,
            )

        summary = {
            "total_fields": len(fields),
            "matches": matches,
            "mismatches": mismatches,
            "rule_based_count": len(rule_based_fields),
            "ml_predicted_count": len(fields) - len(rule_based_fields),
            "mismatched_fields": [
                f for f, info in fields.items() if not info.match
            ],
        }

        return MLComparisonResponse(
            vds_no=vds_no,
            summary=summary,
            fields=fields,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


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
