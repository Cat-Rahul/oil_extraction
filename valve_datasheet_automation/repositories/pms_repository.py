"""
PMS (Piping Material Specification) Repository.

Provides access to PMS data for valve datasheet generation,
supporting queries by piping class to retrieve material specs,
pressure ratings, and service information.
"""

import json
import re
from pathlib import Path
from typing import Optional

from ..models.pms import PMSClass


class PMSRepository:
    """
    Repository for accessing PMS (Piping Material Specification) data.

    Loads PMS data from JSON files and provides lookup methods
    for retrieving piping class information.

    Attributes:
        data_path: Path to the PMS data file
        _index: Internal index of piping classes

    Example:
        >>> repo = PMSRepository(Path("data/pms_data.json"))
        >>> pms = repo.get_class("A1")
        >>> print(pms.pressure_rating)
        '150#'
    """

    def __init__(self, data_path: Optional[Path] = None):
        """
        Initialize repository with PMS data source.

        Args:
            data_path: Path to PMS JSON file. If None, uses empty data.
        """
        self._data: dict = {}
        self._index: dict[str, PMSClass] = {}

        if data_path and data_path.exists():
            self._load_data(data_path)
            self._build_index()

    def _load_data(self, path: Path) -> None:
        """Load PMS data from JSON file."""
        with open(path, 'r', encoding='utf-8') as f:
            self._data = json.load(f)

    def _build_index(self) -> None:
        """Build lookup index from loaded data."""
        # Handle different JSON structures
        sheets = self._data.get('sheets', [])

        for sheet in sheets:
            tables = sheet.get('tables', [])

            for table in tables:
                headers = table.get('headers', [])
                rows = table.get('rows', [])

                # Look for piping class in table
                if 'Piping Class' in headers or 'piping_class' in [h.lower().replace(' ', '_') for h in headers]:
                    self._process_pms_table(headers, rows)

    def _process_pms_table(self, headers: list[str], rows: list[dict]) -> None:
        """Process a PMS table and extract piping class entries."""
        for row in rows:
            # Try different possible column names
            piping_class = (
                row.get('Piping Class') or
                row.get('piping_class') or
                row.get('column_2', '')
            )

            # Skip non-class rows (like "Design Code:", "Service:", etc.)
            if not piping_class or ':' in piping_class:
                continue

            # Extract only valid piping class codes
            piping_class = piping_class.strip()
            if not re.match(r'^[A-Z]\d+[LN]*$', piping_class):
                continue

            # Create PMSClass entry
            pms_class = PMSClass(
                piping_class=piping_class,
                pressure_rating=self._extract_value(row, ['pressure_rating', 'Rating', 'column_3']),
                material_group=self._extract_value(row, ['material_group', 'Material Group']),
                base_material=self._extract_value(row, ['Material', 'base_material', 'column_4']),
                corrosion_allowance=self._extract_value(row, ['C.A', 'corrosion_allowance', 'CA']),
                service=self._extract_value(row, ['Service', 'service', 'column_7']),
                design_pressure_min=self._extract_value(row, ['design_pressure_min', 'column_8']),
                design_pressure_max=self._extract_value(row, ['design_pressure_max', 'column_9']),
                sheet_no=str(self._extract_value(row, ['Sheet No.', 'sheet_no', 'Sheet NO', 'column_10']) or ''),
            )

            self._index[piping_class] = pms_class

    def _extract_value(self, row: dict, keys: list[str]) -> str:
        """Extract value from row trying multiple possible keys."""
        for key in keys:
            if key in row and row[key]:
                val = row[key]
                if isinstance(val, str):
                    return val.strip()
                return str(val)
        return ""

    def get_class(self, piping_class: str) -> Optional[PMSClass]:
        """
        Get PMS data for a specific piping class.

        Args:
            piping_class: Piping class code (e.g., "A1", "B1N")

        Returns:
            PMSClass or None if not found
        """
        piping_class = piping_class.upper().strip()
        return self._index.get(piping_class)

    def get_pressure_rating(self, piping_class: str) -> Optional[str]:
        """Get pressure rating for piping class."""
        pms = self.get_class(piping_class)
        return pms.pressure_rating if pms else None

    def get_pressure_class_numeric(self, piping_class: str) -> Optional[int]:
        """Get numeric pressure class (150, 300, etc.)."""
        pms = self.get_class(piping_class)
        return pms.pressure_class_numeric if pms else None

    def get_design_pressure(self, piping_class: str) -> Optional[str]:
        """Get design pressure range for piping class."""
        pms = self.get_class(piping_class)
        if pms:
            return pms.design_pressure_range
        return None

    def get_service(self, piping_class: str) -> Optional[str]:
        """Get service description for piping class."""
        pms = self.get_class(piping_class)
        return pms.service if pms else None

    def get_corrosion_allowance(self, piping_class: str) -> Optional[str]:
        """Get corrosion allowance for piping class."""
        pms = self.get_class(piping_class)
        return pms.corrosion_allowance if pms else None

    def get_base_material(self, piping_class: str) -> Optional[str]:
        """Get base material specification for piping class."""
        pms = self.get_class(piping_class)
        return pms.base_material if pms else None

    def list_all_classes(self) -> list[str]:
        """List all available piping classes."""
        return sorted(self._index.keys())

    def class_exists(self, piping_class: str) -> bool:
        """Check if a piping class exists in the repository."""
        return piping_class.upper().strip() in self._index

    def get_classes_by_rating(self, rating: int) -> list[PMSClass]:
        """Get all piping classes with a specific pressure rating."""
        return [
            pms for pms in self._index.values()
            if pms.pressure_class_numeric == rating
        ]

    def to_dict(self) -> dict:
        """Export all PMS data as dictionary."""
        return {
            code: pms.to_dict()
            for code, pms in self._index.items()
        }

    def load_from_dict(self, data: dict[str, dict]) -> None:
        """
        Load PMS data directly from dictionary.

        Useful for testing or when data comes from non-file sources.
        """
        self._index.clear()
        for code, values in data.items():
            self._index[code] = PMSClass(
                piping_class=code,
                **values
            )

    def add_default_classes(self) -> None:
        """Add default piping classes for testing/fallback."""
        # Standard ASME B16.34 pressure-temperature ratings at ambient (38°C)
        # Pressure values in barg for Carbon Steel
        defaults = {
            'A1': PMSClass(
                piping_class='A1',
                pressure_rating='150#',
                material_group='1.1',
                base_material='CS',
                corrosion_allowance='3 mm',
                service='Cooling Water, Diesel, Steam',
                design_pressure_min='-1.0 barg @ -29°C',
                design_pressure_max='19.6 barg @ 38°C',
                design_temp_min='-29°C',
                design_temp_max='200°C',
                sheet_no='24',
            ),
            'B1': PMSClass(
                piping_class='B1',
                pressure_rating='300#',
                material_group='1.1',
                base_material='CS',
                corrosion_allowance='3 mm',
                service='Cooling Water, Diesel, Steam',
                design_pressure_min='-1.0 barg @ -29°C',
                design_pressure_max='51.1 barg @ 38°C',
                design_temp_min='-29°C',
                design_temp_max='200°C',
                sheet_no='25',
            ),
            'D1': PMSClass(
                piping_class='D1',
                pressure_rating='600#',
                material_group='1.1',
                base_material='CS',
                corrosion_allowance='3 mm',
                service='Process',
                design_pressure_min='-1.0 barg @ -29°C',
                design_pressure_max='102.1 barg @ 38°C',
                design_temp_min='-29°C',
                design_temp_max='200°C',
                sheet_no='26',
            ),
            'E1': PMSClass(
                piping_class='E1',
                pressure_rating='900#',
                material_group='1.1',
                base_material='CS',
                corrosion_allowance='3 mm',
                service='High Pressure Process',
                design_pressure_min='-1.0 barg @ -29°C',
                design_pressure_max='153.2 barg @ 38°C',
                design_temp_min='-29°C',
                design_temp_max='200°C',
                sheet_no='27',
            ),
            'F1': PMSClass(
                piping_class='F1',
                pressure_rating='1500#',
                material_group='1.1',
                base_material='CS',
                corrosion_allowance='3 mm',
                service='High Pressure Process',
                design_pressure_min='-1.0 barg @ -29°C',
                design_pressure_max='255.3 barg @ 38°C',
                design_temp_min='-29°C',
                design_temp_max='200°C',
                sheet_no='28',
            ),
            'G1': PMSClass(
                piping_class='G1',
                pressure_rating='2500#',
                material_group='1.1',
                base_material='CS',
                corrosion_allowance='3 mm',
                service='High Pressure Process',
                design_pressure_min='-1.0 barg @ -29°C',
                design_pressure_max='425.5 barg @ 38°C',
                design_temp_min='-29°C',
                design_temp_max='200°C',
                sheet_no='29',
            ),
            # NACE variants
            'A1N': PMSClass(
                piping_class='A1N',
                pressure_rating='150#',
                material_group='1.1',
                base_material='CS',
                corrosion_allowance='3 mm',
                service='Sour Service - NACE',
                design_pressure_min='-1.0 barg @ -29°C',
                design_pressure_max='19.6 barg @ 38°C',
                design_temp_min='-29°C',
                design_temp_max='200°C',
                sheet_no='30',
            ),
            'B1N': PMSClass(
                piping_class='B1N',
                pressure_rating='300#',
                material_group='1.1',
                base_material='CS',
                corrosion_allowance='3 mm',
                service='Sour Service - NACE',
                design_pressure_min='-1.0 barg @ -29°C',
                design_pressure_max='51.1 barg @ 38°C',
                design_temp_min='-29°C',
                design_temp_max='200°C',
                sheet_no='31',
            ),
            # Low Temp variants
            'A1L': PMSClass(
                piping_class='A1L',
                pressure_rating='150#',
                material_group='1.1',
                base_material='CS',
                corrosion_allowance='3 mm',
                service='Low Temperature Service',
                design_pressure_min='-1.0 barg @ -46°C',
                design_pressure_max='19.6 barg @ 38°C',
                design_temp_min='-46°C',
                design_temp_max='200°C',
                sheet_no='32',
            ),
            # Combined NACE + Low Temp
            'G1LN': PMSClass(
                piping_class='G1LN',
                pressure_rating='2500#',
                material_group='1.1',
                base_material='CS',
                corrosion_allowance='3 mm',
                service='Sour Service, Low Temperature - NACE',
                design_pressure_min='-1.0 barg @ -46°C',
                design_pressure_max='425.5 barg @ 38°C',
                design_temp_min='-46°C',
                design_temp_max='200°C',
                sheet_no='33',
            ),
        }
        self._index.update(defaults)
