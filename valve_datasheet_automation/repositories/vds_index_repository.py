"""
VDS Index Repository.

Provides access to the VDS Index containing pre-computed
valve specifications for direct lookup.
"""

import json
from pathlib import Path
from typing import Optional

from ..models.pms import VDSIndexEntry


class VDSIndexRepository:
    """
    Repository for accessing VDS Index data.

    The VDS Index contains pre-computed specifications for each VDS number,
    including material selections that have already been determined.

    Attributes:
        data_path: Path to the VDS Index data file
        _index: Internal lookup by VDS number

    Example:
        >>> repo = VDSIndexRepository(Path("data/vds_index.json"))
        >>> entry = repo.get_entry("BSFA1R")
        >>> print(entry.ball_material)
        'Forged - ASTM A182-F316'
    """

    def __init__(self, data_path: Optional[Path] = None):
        """
        Initialize repository with VDS Index data source.

        Args:
            data_path: Path to VDS Index JSON file
        """
        self._data: dict = {}
        self._index: dict[str, VDSIndexEntry] = {}

        if data_path and data_path.exists():
            self._load_data(data_path)
            self._build_index()

    def _load_data(self, path: Path) -> None:
        """Load VDS Index data from JSON file."""
        with open(path, 'r', encoding='utf-8') as f:
            self._data = json.load(f)

    def _build_index(self) -> None:
        """Build lookup index from loaded data."""
        # Check if this is the new unified format (dict with VDS as keys)
        if isinstance(self._data, dict) and 'sheets' not in self._data:
            self._process_unified_format()
            return

        # Legacy format: Handle sheets-based JSON structure
        sheets = self._data.get('sheets', [])

        for sheet in sheets:
            # Look for the Index sheet
            sheet_name = sheet.get('sheet_name', '')

            if sheet_name == 'Index':
                tables = sheet.get('tables', [])
                for table in tables:
                    self._process_index_table(table)

    def _process_unified_format(self) -> None:
        """Process the new unified VDS index format."""
        for vds_no, entry_data in self._data.items():
            if not isinstance(entry_data, dict):
                continue

            # Skip if doesn't look like a VDS entry
            if not vds_no or len(vds_no) < 5:
                continue

            try:
                entry = VDSIndexEntry(
                    vds_no=vds_no,
                    **{k: v for k, v in entry_data.items() if k != 'vds_no' and v}
                )
                self._index[vds_no.upper()] = entry
            except Exception:
                # If model validation fails, try minimal entry
                entry = VDSIndexEntry(
                    vds_no=vds_no,
                    piping_class=entry_data.get('piping_class', ''),
                    valve_type=entry_data.get('valve_type', ''),
                )
                self._index[vds_no.upper()] = entry

    def _process_index_table(self, table: dict) -> None:
        """Process the VDS Index table."""
        rows = table.get('rows', [])

        for row in rows:
            vds_no = row.get('VDS', '').strip()

            # Skip header rows and non-VDS entries
            if not vds_no or vds_no in ['BALL VALVE', 'Sheet Index', 'VDS']:
                continue

            # Skip if doesn't look like a VDS number
            if len(vds_no) < 5:
                continue

            entry = VDSIndexEntry(
                vds_no=vds_no,
                piping_class=row.get('Piping Class', ''),
                size_range=row.get('Size Range', ''),
                valve_type=row.get('Valve type', ''),
                end_connections=row.get('End Connections', ''),
                ball_material=row.get('Ball Material', ''),
                seat_material=row.get('Seat Material', ''),
                body_material=row.get('Body Material', ''),
                page_no=self._parse_int(row.get('Page No')),
                revision=row.get('Rev', ''),
            )

            self._index[vds_no.upper()] = entry

    def _parse_int(self, value) -> Optional[int]:
        """Safely parse integer value."""
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    def get_entry(self, vds_no: str) -> Optional[VDSIndexEntry]:
        """
        Get VDS Index entry by VDS number.

        Args:
            vds_no: VDS number (e.g., "BSFA1R")

        Returns:
            VDSIndexEntry or None if not found
        """
        return self._index.get(vds_no.upper().strip())

    def get_field(self, vds_no: str, field_name: str) -> Optional[str]:
        """
        Get a specific field value from VDS Index.

        Args:
            vds_no: VDS number
            field_name: Field name to retrieve

        Returns:
            Field value or None
        """
        entry = self.get_entry(vds_no)
        if entry:
            return getattr(entry, field_name, None)
        return None

    def get_ball_material(self, vds_no: str) -> Optional[str]:
        """Get ball material for a VDS number."""
        entry = self.get_entry(vds_no)
        return entry.ball_material if entry else None

    def get_seat_material(self, vds_no: str) -> Optional[str]:
        """Get seat material for a VDS number."""
        entry = self.get_entry(vds_no)
        return entry.seat_material if entry else None

    def get_body_material(self, vds_no: str) -> Optional[str]:
        """Get body material for a VDS number."""
        entry = self.get_entry(vds_no)
        return entry.body_material if entry else None

    def get_end_connections(self, vds_no: str) -> Optional[str]:
        """Get end connections for a VDS number."""
        entry = self.get_entry(vds_no)
        return entry.end_connections if entry else None

    def get_valve_type(self, vds_no: str) -> Optional[str]:
        """Get valve type for a VDS number."""
        entry = self.get_entry(vds_no)
        return entry.valve_type if entry else None

    def exists(self, vds_no: str) -> bool:
        """Check if a VDS number exists in the index."""
        return vds_no.upper().strip() in self._index

    def list_all_vds(self) -> list[str]:
        """List all VDS numbers in the index."""
        return sorted(self._index.keys())

    def list_by_piping_class(self, piping_class: str) -> list[VDSIndexEntry]:
        """
        Get all VDS entries for a specific piping class.

        Args:
            piping_class: Piping class code (e.g., "A1")

        Returns:
            List of matching VDSIndexEntry objects
        """
        piping_class = piping_class.upper().strip()
        return [
            entry for entry in self._index.values()
            if entry.piping_class.upper() == piping_class
        ]

    def list_by_valve_type(self, valve_type: str) -> list[VDSIndexEntry]:
        """
        Get all VDS entries for a specific valve type.

        Args:
            valve_type: Valve type (e.g., "Ball Valve, Full Bore")

        Returns:
            List of matching VDSIndexEntry objects
        """
        valve_type_lower = valve_type.lower()
        return [
            entry for entry in self._index.values()
            if valve_type_lower in entry.valve_type.lower()
        ]

    @property
    def total_entries(self) -> int:
        """Total number of VDS entries in the index."""
        return len(self._index)

    def to_dict(self) -> dict:
        """Export all VDS Index data as dictionary."""
        return {
            vds: entry.to_dict()
            for vds, entry in self._index.items()
        }

    def add_entry(self, entry: VDSIndexEntry) -> None:
        """
        Add or update an entry in the index.

        Args:
            entry: VDSIndexEntry to add
        """
        self._index[entry.vds_no.upper()] = entry

    def load_from_dict(self, data: dict) -> None:
        """
        Load VDS Index directly from dictionary.

        Useful for testing or when data comes from non-file sources.

        Args:
            data: Dictionary of VDS number -> entry data
        """
        self._index.clear()
        for vds_no, values in data.items():
            if isinstance(values, dict):
                entry = VDSIndexEntry(vds_no=vds_no, **values)
            elif isinstance(values, VDSIndexEntry):
                entry = values
            else:
                continue
            self._index[vds_no.upper()] = entry

    def add_default_entries(self) -> None:
        """Add default VDS entries for testing/fallback."""
        defaults = [
            VDSIndexEntry(
                vds_no='BSFA1R',
                piping_class='A1',
                size_range='1/2" - 24"',
                valve_type='Ball Valve, Full Bore',
                end_connections='Flanged ASME B16.5 RF',
                ball_material='Forged - ASTM A182-F316',
                seat_material='Reinforced PTFE',
                revision='C0',
            ),
            VDSIndexEntry(
                vds_no='BSRA1R',
                piping_class='A1',
                size_range='1/2" - 24"',
                valve_type='Ball Valve, Reduced Bore',
                end_connections='Flanged ASME B16.5 RF',
                ball_material='Forged - ASTM A182-F316',
                seat_material='Reinforced PTFE',
                revision='C0',
            ),
            VDSIndexEntry(
                vds_no='BSFB1NR',
                piping_class='B1N',
                size_range='1/2" - 24"',
                valve_type='Ball Valve, Full Bore',
                end_connections='Flanged ASME B16.5 RF',
                ball_material='Forged - ASTM A182-F316L',
                seat_material='Reinforced PTFE',
                revision='C0',
            ),
        ]

        for entry in defaults:
            self._index[entry.vds_no.upper()] = entry
