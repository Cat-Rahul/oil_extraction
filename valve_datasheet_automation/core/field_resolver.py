"""
Field Resolver.

Resolves individual datasheet field values from multiple data sources
based on configured mappings.
"""

import re
import yaml
from pathlib import Path
from typing import Any, Optional

from ..models.vds import DecodedVDS
from ..models.datasheet import (
    DatasheetField,
    FieldTraceability,
    FieldSource,
    DatasheetSection,
    create_field,
)
from ..repositories.pms_repository import PMSRepository
from ..repositories.standards_repository import StandardsRepository
from ..repositories.vds_index_repository import VDSIndexRepository


class FieldResolutionError(Exception):
    """Raised when field resolution fails."""

    def __init__(self, message: str, field_name: str = ""):
        self.field_name = field_name
        super().__init__(message)


class FieldResolver:
    """
    Resolves individual datasheet field values from multiple sources.

    Routes each field to its appropriate data source based on
    configuration in field_mappings.yaml.

    Attributes:
        pms: PMS data repository
        standards: Standards/clauses repository
        vds_index: VDS index repository
        field_configs: Field configuration from YAML
        material_mappings: Material mappings from YAML

    Example:
        >>> resolver = FieldResolver(pms_repo, std_repo, vds_repo, config)
        >>> field = resolver.resolve_field("pressure_class", decoded_vds)
        >>> print(field.value)
        'ASME B16.34 Class 150'
    """

    def __init__(
        self,
        pms_repo: PMSRepository,
        standards_repo: StandardsRepository,
        vds_index_repo: VDSIndexRepository,
        config_path: Optional[Path] = None,
        field_applicability: Optional[Dict[str, List[str]]] = None,
    ):
        """
        Initialize resolver with data sources and configuration.

        Args:
            pms_repo: PMS data repository
            standards_repo: Standards/clauses repository
            vds_index_repo: VDS index repository
            config_path: Path to field_mappings.yaml
            field_applicability: Dictionary mapping template names to applicable field lists
        """
        self.pms = pms_repo
        self.standards = standards_repo
        self.vds_index = vds_index_repo
        self.field_configs = self._load_config(config_path) if config_path else {}
        self.field_applicability = field_applicability or {}

        # Load material mappings
        self.material_mappings = {}
        if config_path:
            material_path = config_path.parent / "material_mappings.yaml"
            if material_path.exists():
                self.material_mappings = self._load_material_mappings(material_path)

    def _load_material_mappings(self, path: Path) -> dict:
        """Load material mappings configuration."""
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}

    def _load_config(self, path: Path) -> dict:
        """Load field mappings configuration."""
        if not path.exists():
            return {}

        with open(path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # Flatten sections into field configs
        flat_config = {}
        sections = config.get('sections', {})

        for section_name, section_data in sections.items():
            fields = section_data.get('fields', {})
            for field_name, field_config in fields.items():
                field_config['section'] = section_name
                flat_config[field_name] = field_config

        return flat_config

    def resolve_field(
        self,
        field_name: str,
        decoded_vds: DecodedVDS
    ) -> DatasheetField:
        """
        Resolve a single field value.

        Args:
            field_name: Name of field to resolve
            decoded_vds: Decoded VDS information

        Returns:
            DatasheetField with value and traceability
        """
        config = self.field_configs.get(field_name, {})
        source_type = config.get('source', 'UNKNOWN')
        section = config.get('section', 'General')
        is_required = config.get('is_required', False)
        display_name = config.get('display_name', field_name.replace('_', ' ').title())

        # Check if field is applicable for this valve type
        valve_type_full_name = decoded_vds.valve_type_prefix.full_name
        if self.field_applicability and valve_type_full_name in self.field_applicability:
            if field_name not in self.field_applicability[valve_type_full_name]:
                return create_field(
                    field_name=field_name,
                    section=section,
                    value=None,
                    source_type=FieldSource.NOT_APPLICABLE,
                    notes=f"Not applicable for {valve_type_full_name}",
                )

        # Map string source to enum
        source_enum = self._map_source_type(source_type)

        # Resolve value based on source type
        value, traceability = self._resolve_by_source(
            source_enum,
            field_name,
            decoded_vds,
            config
        )

        return DatasheetField(
            field_name=field_name,
            display_name=display_name,
            section=section,
            value=value,
            traceability=traceability,
            is_required=is_required,
        )

    def _map_source_type(self, source_str: str) -> FieldSource:
        """Map string source type to FieldSource enum."""
        mapping = {
            'VDS': FieldSource.VDS,
            'PMS': FieldSource.PMS,
            'VALVE_STANDARD': FieldSource.VALVE_STANDARD,
            'PMS_AND_STANDARD': FieldSource.PMS_AND_STANDARD,
            'VDS_INDEX': FieldSource.VDS_INDEX,
            'CALCULATED': FieldSource.CALCULATED,
            'FIXED': FieldSource.FIXED,
            'PROJECT_SPECIFIC': FieldSource.PROJECT_SPECIFIC,
        }
        return mapping.get(source_str, FieldSource.UNKNOWN)

    def _resolve_by_source(
        self,
        source: FieldSource,
        field_name: str,
        vds: DecodedVDS,
        config: dict
    ) -> tuple[Any, FieldTraceability]:
        """Resolve field value from a specific source."""

        if source == FieldSource.VDS:
            return self._resolve_from_vds(field_name, vds, config)

        elif source == FieldSource.PMS:
            return self._resolve_from_pms(field_name, vds, config)

        elif source == FieldSource.VALVE_STANDARD:
            return self._resolve_from_standard(field_name, vds, config)

        elif source == FieldSource.PMS_AND_STANDARD:
            return self._resolve_from_pms_and_standard(field_name, vds, config)

        elif source == FieldSource.VDS_INDEX:
            return self._resolve_from_vds_index(field_name, vds, config)

        elif source == FieldSource.CALCULATED:
            return self._resolve_calculated(field_name, vds, config)

        elif source == FieldSource.FIXED:
            return self._resolve_fixed(field_name, config)

        elif source == FieldSource.PROJECT_SPECIFIC:
            return self._resolve_fixed(field_name, config)

        # Unknown source - return empty with traceability
        return (None, FieldTraceability(
            source_type=FieldSource.UNKNOWN,
            notes=f"Unknown source type for field: {field_name}"
        ))

    def _resolve_from_vds(
        self,
        field_name: str,
        vds: DecodedVDS,
        config: dict
    ) -> tuple[Any, FieldTraceability]:
        """Resolve field from VDS decoding."""

        # Map field names to VDS attributes
        vds_mappings = {
            'vds_no': lambda v: v.raw_vds,
            'piping_class': lambda v: v.piping_class,
            'valve_type': lambda v: v.valve_type_full,
            'sour_service': lambda v: (
                "NACE MR0175 / ISO 15156" if v.is_nace_compliant else "-"
            ),
            'end_connections': lambda v: v.end_connection_description,
        }

        resolver_func = vds_mappings.get(field_name)
        if resolver_func:
            value = resolver_func(vds)
        else:
            # Try to get from rules in config
            rules = config.get('rules', [])
            value = self._evaluate_rules(rules, vds)

        return (value, FieldTraceability(
            source_type=FieldSource.VDS,
            source_document=f"VDS No: {vds.raw_vds}",
            source_value=str(value) if value else None,
        ))

    def _resolve_from_pms(
        self,
        field_name: str,
        vds: DecodedVDS,
        config: dict
    ) -> tuple[Any, FieldTraceability]:
        """Resolve field from PMS data."""

        # Strip modifiers (N, L, LN) from piping class for lookup
        base_class = vds.piping_class.rstrip('NL')
        if base_class.endswith('L'):
            base_class = base_class[:-1]

        # Try with full class first, then base class
        pms_class = self.pms.get_class(vds.piping_class)
        if not pms_class:
            pms_class = self.pms.get_class(base_class)

        if not pms_class:
            return (config.get('default'), FieldTraceability(
                source_type=FieldSource.PMS,
                source_document=f"PMS Class {vds.piping_class} not found",
                notes="Using default value - piping class not found in PMS",
            ))

        # Derive pressure class from piping class prefix if not in PMS
        def get_pressure_class_str(p, v):
            if p.pressure_class_numeric:
                return f"ASME B16.34 Class {p.pressure_class_numeric}"
            # Derive from piping class prefix
            class_prefix = v.piping_class[0].upper() if v.piping_class else 'A'
            class_to_rating = {'A': 150, 'B': 300, 'C': 400, 'D': 600, 'E': 900, 'F': 1500, 'G': 2500}
            derived_class = class_to_rating.get(class_prefix, 150)
            return f"ASME B16.34 Class {derived_class}"

        # Map field names to PMS attributes
        pms_mappings = {
            'size_range': lambda p, v: config.get('default', '1/2" - 24"'),
            'service': lambda p, v: p.service or "-",
            'pressure_class': get_pressure_class_str,
            'design_pressure': lambda p, v: p.design_pressure_range if p.design_pressure_range != "-" else f"{p.design_pressure_max or 'As per ASME B16.34'}",
            'corrosion_allowance': lambda p, v: p.corrosion_allowance or "3 mm",
        }

        resolver_func = pms_mappings.get(field_name)
        if resolver_func:
            value = resolver_func(pms_class, vds)
        else:
            value = config.get('default')

        return (value, FieldTraceability(
            source_type=FieldSource.PMS,
            source_document=f"PMS Class {vds.piping_class} ({pms_class.pressure_rating})",
            source_value=str(value) if value else None,
        ))

    def _resolve_from_standard(
        self,
        field_name: str,
        vds: DecodedVDS,
        config: dict
    ) -> tuple[Any, FieldTraceability]:
        """Resolve field from valve standards."""

        # Check for fixed value in config
        fixed_value = config.get('value')
        if fixed_value:
            return (fixed_value, FieldTraceability(
                source_type=FieldSource.VALVE_STANDARD,
                source_document="Configuration",
                source_value=fixed_value,
            ))

        # Check for defaults by valve type
        defaults = config.get('defaults', {})
        valve_type_name = vds.valve_type_prefix.full_name
        valve_type_full = vds.valve_type_full  # Includes bore type

        # Try full valve type first (e.g., "Gate Valve, Outside Screw and Yoke, Full Bore")
        if valve_type_full in defaults:
            value = defaults[valve_type_full]
            return (value, FieldTraceability(
                source_type=FieldSource.VALVE_STANDARD,
                source_document=f"Default for {valve_type_full}",
                source_value=value,
            ))

        # Then try prefix name only (e.g., "Gate Valve, Outside Screw and Yoke")
        if valve_type_name in defaults:
            value = defaults[valve_type_name]
            return (value, FieldTraceability(
                source_type=FieldSource.VALVE_STANDARD,
                source_document=f"Default for {valve_type_name}",
                source_value=value,
            ))

        # Also try generic valve type (e.g., "Gate Valve")
        generic_type = valve_type_name.split(',')[0].strip()
        if generic_type in defaults:
            value = defaults[generic_type]
            return (value, FieldTraceability(
                source_type=FieldSource.VALVE_STANDARD,
                source_document=f"Default for {generic_type}",
                source_value=value,
            ))

        # Try to get from standards repository
        value = self.standards.get_standard_value(field_name, valve_type_name)

        if value:
            return (value, FieldTraceability(
                source_type=FieldSource.VALVE_STANDARD,
                source_document="Valve Standard",
                source_value=value,
            ))

        # Handle construction fields with smart defaults
        value = self._resolve_construction_field(field_name, vds, config)
        if value:
            return (value, FieldTraceability(
                source_type=FieldSource.VALVE_STANDARD,
                source_document="Valve Standard (derived)",
                source_value=value,
            ))

        # Evaluate rules with PMS context for pressure_class
        pms_class = self.pms.get_class(vds.piping_class)
        pressure_class = pms_class.pressure_class_numeric if pms_class else 150

        rules = config.get('rules', [])
        value = self._evaluate_rules(rules, vds, pressure_class=pressure_class)

        return (value or config.get('default'), FieldTraceability(
            source_type=FieldSource.VALVE_STANDARD,
            source_document="Valve Standard",
        ))

    def _resolve_construction_field(
        self,
        field_name: str,
        vds: DecodedVDS,
        config: dict
    ) -> Optional[str]:
        """Resolve construction fields with intelligent defaults."""

        # Get pressure class from PMS (with fallback for None)
        pms_class = self.pms.get_class(vds.piping_class)
        pressure_class = (pms_class.pressure_class_numeric if pms_class and pms_class.pressure_class_numeric else None)

        # If no pressure class from PMS, derive from piping class naming convention
        if pressure_class is None:
            # Standard mapping: A=150, B=300, D=600, E=900, F=1500, G=2500
            class_prefix = vds.piping_class[0].upper() if vds.piping_class else 'A'
            class_to_rating = {'A': 150, 'B': 300, 'C': 400, 'D': 600, 'E': 900, 'F': 1500, 'G': 2500}
            pressure_class = class_to_rating.get(class_prefix, 150)

        if field_name == 'body_construction':
            # Body construction depends on valve type and general practice
            if vds.valve_type_prefix.full_name == "Ball Valve":
                return 'Forged, Two Piece (<=1.5"), Cast, Two/Three Piece (>1.5")'
            return config.get('default', 'Forged/Cast per API 6D')

        elif field_name == 'ball_construction':
            # Ball construction depends on pressure class
            if pressure_class <= 150:
                return 'Floating (8" and below), Trunnion mounted (10" and above)'
            elif pressure_class >= 300:
                return 'Floating (4" and below), Trunnion mounted (6" and above)'
            return config.get('default', 'Floating/Trunnion per API 6D')

        elif field_name == 'seat_construction':
            # Seat construction depends on metal-seated flag
            if vds.is_metal_seated:
                return "Metal seated, hard faced, Renewable"
            return "Soft seated, Renewable"

        return None

    def _resolve_from_pms_and_standard(
        self,
        field_name: str,
        vds: DecodedVDS,
        config: dict
    ) -> tuple[Any, FieldTraceability]:
        """Resolve field combining PMS and standard data."""

        # First try VDS index for pre-computed values
        vds_entry = self.vds_index.get_entry(vds.raw_vds)

        if vds_entry:
            # Try to get value directly from VDS index entry
            # Use getattr for direct field access, then try get_field for extras
            value = getattr(vds_entry, field_name, None)
            if not value:
                value = vds_entry.get_field(field_name) if hasattr(vds_entry, 'get_field') else None

            if value:
                return (value, FieldTraceability(
                    source_type=FieldSource.PMS_AND_STANDARD,
                    source_document=f"VDS Index: {vds.raw_vds}",
                    source_value=value,
                ))

        # Get base material from PMS
        pms_class = self.pms.get_class(vds.piping_class)
        base_material = pms_class.base_material if pms_class else "CS"

        # Determine material key based on NACE/LowTemp compliance
        material_key = base_material
        if vds.is_low_temp and vds.is_nace_compliant:
            material_key = f"LTCS_NACE" if base_material == "CS" else f"{base_material}_NACE"
        elif vds.is_low_temp:
            material_key = "LTCS" if base_material == "CS" else base_material
        elif vds.is_nace_compliant:
            material_key = f"{base_material}_NACE"

        # Try to derive from material mappings
        value = self._get_material_from_mappings(field_name, material_key, vds)

        if not value:
            # Evaluate rules based on conditions
            rules = config.get('rules', [])
            value = self._evaluate_rules(rules, vds, base_material=base_material)

        if not value:
            value = config.get('default')

        source_doc = f"Material Mappings ({material_key})" if value else f"PMS {vds.piping_class} + Valve Standard"

        return (value, FieldTraceability(
            source_type=FieldSource.PMS_AND_STANDARD,
            source_document=source_doc,
            source_value=str(value) if value else None,
            notes=f"Base material: {base_material}, Material key: {material_key}" if base_material else None,
        ))

    def _get_material_from_mappings(
        self,
        field_name: str,
        material_key: str,
        vds: DecodedVDS
    ) -> Optional[str]:
        """Get material specification from material_mappings.yaml."""
        base_materials = self.material_mappings.get('base_materials', {})

        # Map field names to component keys
        component_map = {
            'body_material': 'body',
            'ball_material': 'ball',
            'stem_material': 'stem',
            'gland_material': 'gland',
            'bolts': 'bolts',
            'nuts': 'nuts',
            'gaskets': 'gaskets',
            'spring_material': 'spring',
            'gland_packing': 'gland_packing',
        }

        component_key = component_map.get(field_name)
        if not component_key:
            return None

        # Try to get material spec
        material_config = base_materials.get(material_key)

        # Handle inheritance
        if material_config and 'inherits' in material_config:
            parent_key = material_config['inherits']
            parent_config = base_materials.get(parent_key, {})
            parent_components = parent_config.get('components', {})

            # Check for overrides first
            overrides = material_config.get('component_overrides', {})
            if component_key in overrides:
                return overrides[component_key]

            # Fall back to parent
            material_config = parent_config

        if not material_config:
            # Fall back to base material without suffix
            base_key = material_key.replace('_NACE', '').replace('LTCS', 'CS')
            material_config = base_materials.get(base_key, base_materials.get('CS', {}))

        components = material_config.get('components', {})
        component_spec = components.get(component_key)

        if not component_spec:
            return None

        # Handle nested body spec (forged vs cast)
        if isinstance(component_spec, dict):
            if component_key == 'body':
                # Use forged as default (most common for ball valves)
                return f"Forged - {component_spec.get('forged', '')} / Cast - {component_spec.get('cast', '')}"
            elif component_key == 'gaskets':
                # Use end connection to determine gasket type
                end_conn = vds.end_connection.name if vds.end_connection else 'RF'
                return component_spec.get(end_conn, component_spec.get('RF', ''))
            else:
                return str(component_spec)

        return component_spec

    def _resolve_from_vds_index(
        self,
        field_name: str,
        vds: DecodedVDS,
        config: dict
    ) -> tuple[Any, FieldTraceability]:
        """Resolve field from VDS index lookup."""

        vds_entry = self.vds_index.get_entry(vds.raw_vds)

        if vds_entry:
            # Try to get the field value directly
            value = getattr(vds_entry, field_name, None)

            # Also try get_field method for extra fields
            if not value and hasattr(vds_entry, 'get_field'):
                value = vds_entry.get_field(field_name)

            if value:
                return (value, FieldTraceability(
                    source_type=FieldSource.VDS_INDEX,
                    source_document=f"VDS Index: {vds.raw_vds}",
                    source_value=value,
                ))

        # Try valve_type_defaults
        valve_type_defaults = config.get('valve_type_defaults', {})
        valve_type_full = vds.valve_type_full
        valve_type_name = vds.valve_type_prefix.full_name
        generic_type = valve_type_name.split(',')[0].strip()

        # Try in order: full type, prefix name, generic type
        for type_name in [valve_type_full, valve_type_name, generic_type]:
            if type_name in valve_type_defaults:
                value = valve_type_defaults[type_name]
                return (value, FieldTraceability(
                    source_type=FieldSource.VDS_INDEX,
                    source_document=f"Valve type default for {type_name}",
                    source_value=value,
                    notes="Using valve type default",
                ))

        # Fallback to general default
        value = config.get('default')
        return (value, FieldTraceability(
            source_type=FieldSource.VDS_INDEX,
            source_document=f"VDS Index lookup failed for {vds.raw_vds}",
            notes="Using default value",
        ))

    def _resolve_calculated(
        self,
        field_name: str,
        vds: DecodedVDS,
        config: dict
    ) -> tuple[Any, FieldTraceability]:
        """Resolve calculated fields."""

        formula = config.get('formula', '')
        unit = config.get('unit', 'barg')

        # Get PMS data for calculations
        pms_class = self.pms.get_class(vds.piping_class)

        # Standard pressure ratings for ASME B16.34 (barg @ 38°C for CS)
        standard_pressures = {
            150: 19.6,
            300: 51.1,
            600: 102.1,
            900: 153.2,
            1500: 255.3,
            2500: 425.5,
        }

        # Get design pressure from PMS or use standard based on pressure class
        pressure = None
        pressure_source = "Standard ASME B16.34"

        if pms_class and pms_class.design_pressure_max:
            pressure = self._extract_pressure_value(pms_class.design_pressure_max)
            pressure_source = f"PMS {vds.piping_class}"

        if not pressure and pms_class:
            # Fallback to standard pressure based on rating
            pressure_class = pms_class.pressure_class_numeric
            if pressure_class:
                pressure = standard_pressures.get(pressure_class)
                pressure_source = f"ASME B16.34 Class {pressure_class}"

        if not pressure:
            # Ultimate fallback - assume 150# class
            pressure = standard_pressures[150]
            pressure_source = "ASME B16.34 Class 150 (default)"

        if field_name == 'hydrotest_shell':
            # Shell test = 1.5 x max design pressure (per API 598)
            shell_test = pressure * 1.5
            value = f"{shell_test:.1f} {unit}"
            return (value, FieldTraceability(
                source_type=FieldSource.CALCULATED,
                source_document=pressure_source,
                derivation_rule="1.5 x Max Design Pressure (API 598)",
                source_value=f"{pressure} {unit}",
            ))

        elif field_name == 'hydrotest_closure':
            # Closure test = 1.1 x max design pressure (per API 598)
            closure_test = pressure * 1.1
            value = f"{closure_test:.1f} {unit}"
            return (value, FieldTraceability(
                source_type=FieldSource.CALCULATED,
                source_document=pressure_source,
                derivation_rule="1.1 x Max Design Pressure (API 598)",
                source_value=f"{pressure} {unit}",
            ))

        # Return default if calculation fails
        return (config.get('default'), FieldTraceability(
            source_type=FieldSource.CALCULATED,
            notes="Calculation not applicable for this field",
        ))

    def _resolve_fixed(
        self,
        field_name: str,
        config: dict
    ) -> tuple[Any, FieldTraceability]:
        """Resolve fixed/constant value fields."""

        value = config.get('value', config.get('default'))

        return (value, FieldTraceability(
            source_type=FieldSource.FIXED,
            source_document="Configuration",
            source_value=str(value) if value else None,
        ))

    def _evaluate_rules(
        self,
        rules: list[dict],
        vds: DecodedVDS,
        **context
    ) -> Optional[str]:
        """
        Evaluate conditional rules to determine field value.

        Args:
            rules: List of rule dictionaries with condition and value
            vds: Decoded VDS for context
            **context: Additional context variables

        Returns:
            Matching rule value or None
        """
        for rule in rules:
            condition = rule.get('condition', '')
            value = rule.get('value')

            if self._evaluate_condition(condition, vds, **context):
                return value

        return None

    def _evaluate_condition(
        self,
        condition: str,
        vds: DecodedVDS,
        **context
    ) -> bool:
        """
        Evaluate a condition string against VDS and context.

        Args:
            condition: Condition string (e.g., "is_nace_compliant == true")
            vds: Decoded VDS
            **context: Additional context

        Returns:
            True if condition matches
        """
        if not condition:
            return True

        # Get pressure class from context or PMS
        pressure_class_val = context.get('pressure_class')
        if pressure_class_val is None:
            pms_class = self.pms.get_class(vds.piping_class)
            pressure_class_val = pms_class.pressure_class_numeric if pms_class else 150

        # Build evaluation context
        eval_context = {
            'is_nace_compliant': vds.is_nace_compliant,
            'is_low_temp': vds.is_low_temp,
            'is_metal_seated': vds.is_metal_seated,
            'valve_type': vds.valve_type_prefix.full_name,
            'bore_type': vds.bore_type.full_name,
            'piping_class': vds.piping_class,
            'end_connection': vds.end_connection.name,
            'pressure_class': pressure_class_val,
            **context
        }

        # Simple condition evaluation
        condition = condition.lower().strip()

        # Handle comparison operators (<=, >=, <, >, ==)
        for op in ['<=', '>=', '<', '>', '==']:
            if op in condition:
                parts = condition.split(op)
                if len(parts) == 2:
                    var_name = parts[0].strip()
                    expected_str = parts[1].strip().strip('"\'')

                    actual = eval_context.get(var_name)
                    if actual is None:
                        return False

                    # Try numeric comparison
                    try:
                        expected_num = float(expected_str)
                        actual_num = float(actual) if not isinstance(actual, (int, float)) else actual

                        if op == '<=':
                            return actual_num <= expected_num
                        elif op == '>=':
                            return actual_num >= expected_num
                        elif op == '<':
                            return actual_num < expected_num
                        elif op == '>':
                            return actual_num > expected_num
                        elif op == '==':
                            return actual_num == expected_num
                    except (ValueError, TypeError):
                        pass

                    # Boolean comparison for ==
                    if op == '==':
                        if expected_str in ['true', 'false']:
                            return actual == (expected_str == 'true')
                        # String comparison
                        return str(actual).lower() == expected_str.lower()

                break

        # Handle contains checks
        if 'contains' in condition:
            match = re.match(r'(\w+)\s+contains\s+["\']?(.+?)["\']?$', condition)
            if match:
                var_name = match.group(1)
                search_term = match.group(2)
                actual = str(eval_context.get(var_name, ''))
                return search_term.lower() in actual.lower()

        return False

    def _extract_pressure_value(self, pressure_str: str) -> Optional[float]:
        """Extract numeric pressure value from string like '19.6 @ -29°C'."""
        if not pressure_str:
            return None

        match = re.search(r'([\d.]+)', pressure_str)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        return None

    def resolve_all_fields(self, decoded_vds: DecodedVDS) -> dict[str, DatasheetField]:
        """
        Resolve all configured fields.

        Args:
            decoded_vds: Decoded VDS

        Returns:
            Dictionary of field_name -> DatasheetField
        """
        fields = {}
        for field_name in self.field_configs.keys():
            fields[field_name] = self.resolve_field(field_name, decoded_vds)
        return fields
