"""
Datasheet Engine.

Main orchestration engine for generating complete valve datasheets
from VDS numbers.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List

import yaml

from .vds_decoder import VDSDecoder, VDSDecodingError, ValveTypePrefix
from .field_resolver import FieldResolver
from .excel_parser import ExcelParser
from ..models.vds import DecodedVDS
from ..models.datasheet import (
    ValveDatasheet,
    DatasheetField,
    FieldTraceability,
    FieldSource,
    create_field,
)
from ..repositories.pms_repository import PMSRepository
from ..repositories.standards_repository import StandardsRepository
from ..repositories.vds_index_repository import VDSIndexRepository


class DatasheetGenerationError(Exception):
    """Raised when datasheet generation fails."""

    def __init__(self, message: str, vds_no: str = "", errors: list[str] = None):
        self.vds_no = vds_no
        self.errors = errors or []
        super().__init__(message)


class DatasheetEngine:
    """
    Main orchestration engine for generating valve datasheets.

    Coordinates VDS decoding, field resolution, validation, and
    output generation.

    Attributes:
        decoder: VDS number decoder
        resolver: Field value resolver
        config_dir: Configuration directory path

    Example:
        >>> engine = DatasheetEngine(Path("config"))
        >>> datasheet = engine.generate("BSFA1R")
        >>> print(datasheet.completion_percentage)
        95.0
    """

    VERSION = "1.0.0"

    def __init__(
        self,
        config_dir: Optional[Path] = None,
        data_dir: Optional[Path] = None,
        field_applicability_path: Optional[Path] = None,
    ):
        """
        Initialize engine with configuration directory.

        Args:
            config_dir: Path to configuration files
            data_dir: Path to data files (PMS, clauses, VDS index)
            field_applicability_path: Path to the Excel file defining field applicability
        """
        self.config_dir = config_dir or Path(__file__).parent.parent / "config"
        self.data_dir = data_dir

        # Initialize decoder
        vds_rules_path = self.config_dir / "vds_rules.yaml"
        self.decoder = VDSDecoder(
            rules_path=vds_rules_path if vds_rules_path.exists() else None
        )

        # Initialize repositories
        self.pms_repo = self._init_pms_repo()
        self.standards_repo = self._init_standards_repo()
        self.vds_index_repo = self._init_vds_index_repo()

        # Load field applicability
        self.field_applicability: Dict[str, List[str]] = {}
        if field_applicability_path and field_applicability_path.exists():
            try:
                excel_parser = ExcelParser()
                self.field_applicability = excel_parser.parse_field_applicability(field_applicability_path)
            except Exception as e:
                print(f"Warning: Could not load field applicability Excel: {e}")
        
        # Load valve type templates
        templates_path = self.config_dir / "valve_type_templates.yaml"
        self._valve_type_templates = self._load_valve_type_templates(templates_path)

        # Initialize field resolver
        field_mappings_path = self.config_dir / "field_mappings.yaml"
        self.resolver = FieldResolver(
            pms_repo=self.pms_repo,
            standards_repo=self.standards_repo,
            vds_index_repo=self.vds_index_repo,
            config_path=field_mappings_path if field_mappings_path.exists() else None,
            field_applicability=self.field_applicability,
        )

    def _init_pms_repo(self) -> PMSRepository:
        """Initialize PMS repository."""
        repo = PMSRepository()

        # Try to load from data directory
        if self.data_dir:
            pms_path = self.data_dir / "Pipping specification_extracted.json"
            if pms_path.exists():
                repo = PMSRepository(pms_path)

        # Add defaults if empty
        if not repo.list_all_classes():
            repo.add_default_classes()

        return repo

    def _init_standards_repo(self) -> StandardsRepository:
        """Initialize standards repository."""
        repo = StandardsRepository()

        # Try to load from data directory
        if self.data_dir:
            clauses_path = self.data_dir / "output_no_footer_clauses.json"
            if clauses_path.exists():
                repo = StandardsRepository(clauses_path)

        # Add defaults if empty
        if repo.total_clauses == 0:
            repo.add_default_clauses()

        return repo

    def _init_vds_index_repo(self) -> VDSIndexRepository:
        """Initialize VDS index repository."""
        repo = VDSIndexRepository()

        # Try to load from data directory
        if self.data_dir:
            # First try the new unified index (contains all valve types)
            unified_index_path = self.data_dir / "all_valve_vds_index.json"
            if unified_index_path.exists():
                repo = VDSIndexRepository(unified_index_path)
            else:
                # Fall back to legacy Ball valve index
                index_path = self.data_dir / "BALL-With Metalic Valve-for sample data sheet with reference marked.json"
                if index_path.exists():
                    repo = VDSIndexRepository(index_path)

        # Add defaults if empty
        if repo.total_entries == 0:
            repo.add_default_entries()

        return repo

    def _load_valve_type_templates(self, path: Path) -> dict:
        """Load valve type template definitions from YAML."""
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        return {}

    def get_valve_type_templates(self) -> dict:
        """Return valve type templates for API consumption."""
        return self._valve_type_templates.get('valve_type_templates', {})

    def get_default_template_key(self) -> str:
        """Return the default template key."""
        return self._valve_type_templates.get('default_template', 'BALL')

    def generate(self, vds_no: str) -> ValveDatasheet:
        """
        Generate complete datasheet from VDS number.

        Args:
            vds_no: VDS number string (e.g., "BSFA1R")

        Returns:
            Complete ValveDatasheet with all fields populated

        Raises:
            VDSDecodingError: If VDS format is invalid
            DatasheetGenerationError: If generation fails
        """
        errors = []
        warnings = []

        # Step 1: Decode VDS
        try:
            decoded_vds = self.decoder.decode(vds_no)
        except VDSDecodingError as e:
            raise DatasheetGenerationError(
                f"Failed to decode VDS: {e}",
                vds_no=vds_no,
                errors=[str(e)]
            )

        # Step 2: Resolve all fields
        fields = {}
        for field_name in self._get_all_field_names():
            try:
                fields[field_name] = self.resolver.resolve_field(field_name, decoded_vds)
            except Exception as e:
                # Create error field
                fields[field_name] = create_field(
                    field_name=field_name,
                    section="Unknown",
                    value=None,
                    source_type=FieldSource.UNKNOWN,
                    notes=f"Resolution error: {str(e)}",
                )
                errors.append(f"Field '{field_name}': {str(e)}")

        # Step 3: Build datasheet
        datasheet = self._build_datasheet(fields, decoded_vds)

        # Step 4: Validate
        validation_errors = self._validate_datasheet(datasheet)
        errors.extend(validation_errors)

        # Step 5: Set final status
        datasheet.validation_errors = errors
        datasheet.warnings = warnings
        datasheet.validation_status = "valid" if not errors else "invalid"

        return datasheet

    def generate_batch(self, vds_numbers: list[str]) -> list[ValveDatasheet]:
        """
        Generate datasheets for multiple VDS numbers.

        Args:
            vds_numbers: List of VDS number strings

        Returns:
            List of ValveDatasheet objects
        """
        results = []
        for vds_no in vds_numbers:
            try:
                datasheet = self.generate(vds_no)
                results.append(datasheet)
            except (VDSDecodingError, DatasheetGenerationError) as e:
                # Create error datasheet
                error_ds = self._create_error_datasheet(vds_no, str(e))
                results.append(error_ds)
        return results

    def _get_all_field_names(self) -> list[str]:
        """Get list of all datasheet field names (including valve-type-specific fields)."""
        return [
            # Header
            'vds_no', 'piping_class', 'size_range', 'valve_type', 'service',
            # Design
            'valve_standard', 'pressure_class', 'design_pressure',
            'corrosion_allowance', 'sour_service',
            # Configuration
            'end_connections', 'face_to_face', 'operation',
            # Construction (includes valve-type-specific fields)
            'body_construction', 'ball_construction', 'disc_construction',
            'wedge_construction', 'stem_construction', 'shaft_construction',
            'seat_construction', 'locks', 'back_seat_construction',
            'packing_construction', 'bonnet_construction',
            # Material (includes valve-type-specific fields)
            'body_material', 'ball_material', 'disc_material', 'wedge_material',
            'trim_material', 'seat_material', 'seal_material', 'stem_material',
            'shaft_material', 'gland_material', 'gland_packing',
            'lever_handwheel', 'spring_material', 'gaskets', 'bolts', 'nuts',
            'needle_material', 'hinge_pin_material',
            # Testing
            'marking_purchaser', 'marking_manufacturer', 'inspection_testing',
            'leakage_rate', 'hydrotest_shell', 'hydrotest_closure',
            'pneumatic_test', 'material_certification', 'fire_rating', 'finish',
        ]

    def _build_datasheet(
        self,
        fields: dict[str, DatasheetField],
        decoded_vds: DecodedVDS
    ) -> ValveDatasheet:
        """Construct ValveDatasheet from resolved fields."""

        def get_field(name: str) -> DatasheetField:
            """Get field or create empty placeholder."""
            if name in fields:
                return fields[name]
            return create_field(
                field_name=name,
                section="Unknown",
                value=None,
                source_type=FieldSource.UNKNOWN,
            )

        def get_optional_field(name: str) -> Optional[DatasheetField]:
            """Get optional field only if it has a value."""
            if name in fields:
                field = fields[name]
                # Only return if the field has an actual value
                if field.value and str(field.value).strip() and str(field.value).strip() != "-":
                    return field
            return None

        return ValveDatasheet(
            # Header
            vds_no=get_field('vds_no'),
            piping_class=get_field('piping_class'),
            size_range=get_field('size_range'),
            valve_type=get_field('valve_type'),
            service=get_field('service'),
            # Design
            valve_standard=get_field('valve_standard'),
            pressure_class=get_field('pressure_class'),
            design_pressure=get_field('design_pressure'),
            corrosion_allowance=get_field('corrosion_allowance'),
            sour_service=get_field('sour_service'),
            # Configuration
            end_connections=get_field('end_connections'),
            face_to_face=get_field('face_to_face'),
            operation=get_field('operation'),
            # Construction (optional fields based on valve type)
            body_construction=get_field('body_construction'),
            ball_construction=get_optional_field('ball_construction'),
            disc_construction=get_optional_field('disc_construction'),
            wedge_construction=get_optional_field('wedge_construction'),
            stem_construction=get_field('stem_construction'),
            shaft_construction=get_optional_field('shaft_construction'),
            seat_construction=get_field('seat_construction'),
            locks=get_optional_field('locks'),
            back_seat_construction=get_optional_field('back_seat_construction'),
            packing_construction=get_optional_field('packing_construction'),
            bonnet_construction=get_optional_field('bonnet_construction'),
            # Material (optional fields based on valve type)
            body_material=get_field('body_material'),
            ball_material=get_optional_field('ball_material'),
            disc_material=get_optional_field('disc_material'),
            wedge_material=get_optional_field('wedge_material'),
            trim_material=get_optional_field('trim_material'),
            seat_material=get_field('seat_material'),
            seal_material=get_optional_field('seal_material'),
            stem_material=get_field('stem_material'),
            shaft_material=get_optional_field('shaft_material'),
            gland_material=get_optional_field('gland_material'),
            gland_packing=get_optional_field('gland_packing'),
            lever_handwheel=get_optional_field('lever_handwheel'),
            spring_material=get_optional_field('spring_material'),
            gaskets=get_field('gaskets'),
            bolts=get_field('bolts'),
            nuts=get_field('nuts'),
            needle_material=get_optional_field('needle_material'),
            hinge_pin_material=get_optional_field('hinge_pin_material'),
            # Testing
            marking_purchaser=get_field('marking_purchaser'),
            marking_manufacturer=get_field('marking_manufacturer'),
            inspection_testing=get_field('inspection_testing'),
            leakage_rate=get_field('leakage_rate'),
            hydrotest_shell=get_field('hydrotest_shell'),
            hydrotest_closure=get_field('hydrotest_closure'),
            pneumatic_test=get_field('pneumatic_test'),
            material_certification=get_field('material_certification'),
            fire_rating=get_field('fire_rating'),
            finish=get_field('finish'),
            # Metadata
            generated_at=datetime.utcnow(),
            generation_version=self.VERSION,
        )

    def _validate_datasheet(self, datasheet: ValveDatasheet) -> list[str]:
        """Validate datasheet completeness."""
        errors = []

        # Check required fields
        missing = datasheet.get_missing_required_fields()
        for field in missing:
            errors.append(f"Required field missing: {field.display_name}")

        return errors

    def _create_error_datasheet(self, vds_no: str, error: str) -> ValveDatasheet:
        """Create a minimal datasheet with error information."""
        def error_field(name: str, section: str = "Unknown") -> DatasheetField:
            return create_field(
                field_name=name,
                section=section,
                value=None,
                source_type=FieldSource.UNKNOWN,
                notes=f"Generation failed: {error}",
            )

        # Create VDS field with the input
        vds_field = create_field(
            field_name='vds_no',
            section='Header',
            value=vds_no,
            source_type=FieldSource.VDS,
        )

        return ValveDatasheet(
            vds_no=vds_field,
            piping_class=error_field('piping_class', 'Header'),
            size_range=error_field('size_range', 'Header'),
            valve_type=error_field('valve_type', 'Header'),
            service=error_field('service', 'Header'),
            valve_standard=error_field('valve_standard', 'Design'),
            pressure_class=error_field('pressure_class', 'Design'),
            design_pressure=error_field('design_pressure', 'Design'),
            corrosion_allowance=error_field('corrosion_allowance', 'Design'),
            sour_service=error_field('sour_service', 'Design'),
            end_connections=error_field('end_connections', 'Configuration'),
            face_to_face=error_field('face_to_face', 'Configuration'),
            operation=error_field('operation', 'Configuration'),
            body_construction=error_field('body_construction', 'Construction'),
            # Optional construction fields are None for error datasheet
            stem_construction=error_field('stem_construction', 'Construction'),
            seat_construction=error_field('seat_construction', 'Construction'),
            body_material=error_field('body_material', 'Material'),
            # Optional material fields are None for error datasheet
            seat_material=error_field('seat_material', 'Material'),
            stem_material=error_field('stem_material', 'Material'),
            gaskets=error_field('gaskets', 'Material'),
            bolts=error_field('bolts', 'Material'),
            nuts=error_field('nuts', 'Material'),
            marking_purchaser=error_field('marking_purchaser', 'Testing'),
            marking_manufacturer=error_field('marking_manufacturer', 'Testing'),
            inspection_testing=error_field('inspection_testing', 'Testing'),
            leakage_rate=error_field('leakage_rate', 'Testing'),
            hydrotest_shell=error_field('hydrotest_shell', 'Testing'),
            hydrotest_closure=error_field('hydrotest_closure', 'Testing'),
            pneumatic_test=error_field('pneumatic_test', 'Testing'),
            material_certification=error_field('material_certification', 'Testing'),
            fire_rating=error_field('fire_rating', 'Testing'),
            finish=error_field('finish', 'Testing'),
            generated_at=datetime.utcnow(),
            generation_version=self.VERSION,
            validation_status="error",
            validation_errors=[error],
        )

    def decode_vds(self, vds_no: str) -> DecodedVDS:
        """
        Decode a VDS number without generating full datasheet.

        Useful for validation or inspection.

        Args:
            vds_no: VDS number string

        Returns:
            DecodedVDS object
        """
        return self.decoder.decode(vds_no)

    def validate_vds(self, vds_no: str) -> tuple[bool, Optional[str]]:
        """
        Validate a VDS number without generating datasheet.

        Args:
            vds_no: VDS number to validate

        Returns:
            Tuple of (is_valid, error_message or None)
        """
        return self.decoder.validate(vds_no)

    @property
    def supported_valve_types(self) -> list[str]:
        """Get list of supported valve type prefixes."""
        return self.decoder.get_supported_prefixes()

    @property
    def available_piping_classes(self) -> list[str]:
        """Get list of available piping classes from PMS."""
        return self.pms_repo.list_all_classes()

    @property
    def indexed_vds_numbers(self) -> list[str]:
        """Get list of VDS numbers in the index."""
        return self.vds_index_repo.list_all_vds()
