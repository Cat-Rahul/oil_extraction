"""
VDS (Valve Data Sheet) Number Decoder.

This module provides configurable parsing of VDS numbers into
their constituent components using rules defined in vds_rules.yaml.

VDS Format:
    {Prefix}{BoreType}[MetalSeated]{PipingClass}[Modifiers]{EndConnection}

Examples:
    - BSFA1R    -> Ball, Full bore, Class A1, RF end
    - BSFB1NR   -> Ball, Full bore, Class B1N (NACE), RF end
    - BSFMG1LNJ -> Ball, Full bore, Metal-seated, Class G1LN, RTJ end
"""

import re
from pathlib import Path
from typing import Optional
import yaml

from ..models.vds import (
    DecodedVDS,
    ValveTypePrefix,
    BoreType,
    EndConnection,
)


class VDSDecodingError(Exception):
    """Raised when VDS decoding fails."""

    def __init__(self, message: str, vds: str = "", segment: str = ""):
        self.vds = vds
        self.segment = segment
        super().__init__(message)


class VDSDecoder:
    """
    Configurable VDS number decoder.

    Parses VDS numbers into structured DecodedVDS objects using
    rules defined in YAML configuration.

    Attributes:
        rules: Loaded VDS rules from configuration
        strict_mode: If True, unknown patterns raise errors

    Example:
        >>> decoder = VDSDecoder(Path("config/vds_rules.yaml"))
        >>> result = decoder.decode("BSFA1R")
        >>> print(result.valve_type_full)
        'Ball Valve, Full Bore'
    """

    def __init__(self, rules_path: Optional[Path] = None, strict_mode: bool = True):
        """
        Initialize decoder with rules from YAML config.

        Args:
            rules_path: Path to vds_rules.yaml. If None, uses defaults.
            strict_mode: If True, raises errors for unknown patterns.
        """
        self.strict_mode = strict_mode
        self.rules = self._load_rules(rules_path) if rules_path else self._default_rules()
        self._validate_rules()

    def _load_rules(self, path: Path) -> dict:
        """Load VDS decoding rules from YAML file."""
        if not path.exists():
            raise FileNotFoundError(f"VDS rules file not found: {path}")

        with open(path, 'r', encoding='utf-8') as f:
            rules = yaml.safe_load(f)

        return rules

    def _default_rules(self) -> dict:
        """Return default decoding rules if no config provided."""
        return {
            'valve_type_prefixes': {
                'BS': {'name': 'Ball Valve'},
                'GS': {'name': 'Gate Valve'},
                'CS': {'name': 'Check Valve'},
                'PS': {'name': 'Plug Valve'},
            },
            'bore_types': {
                'F': {'name': 'Full Bore'},
                'R': {'name': 'Reduced Bore'},
                'M': {'name': 'Metal Seated'},
            },
            'end_connections': {
                'R': {'name': 'RF'},
                'J': {'name': 'RTJ'},
                'F': {'name': 'FF'},
                'W': {'name': 'BW'},
                'S': {'name': 'SW'},
            },
            'modifiers': {
                'N': {'name': 'NACE Compliant'},
                'L': {'name': 'Low Temperature'},
            },
        }

    def _validate_rules(self) -> None:
        """Validate loaded rules have required sections."""
        required = ['valve_type_prefixes', 'bore_types', 'end_connections']
        for section in required:
            if section not in self.rules:
                raise ValueError(f"Missing required rules section: {section}")

    def decode(self, vds_no: str) -> DecodedVDS:
        """
        Decode a VDS number into its constituent parts.

        Args:
            vds_no: VDS number string (e.g., "BSFA1R", "BSFMG1LNJ", "GAWA1R")

        Returns:
            DecodedVDS with all extracted attributes

        Raises:
            VDSDecodingError: If VDS format is invalid or unknown
        """
        # Normalize input
        vds_no = vds_no.upper().strip()

        if not vds_no:
            raise VDSDecodingError("VDS number cannot be empty", vds_no)

        if len(vds_no) < 5:
            raise VDSDecodingError(
                f"VDS number too short: {vds_no} (minimum 5 characters)",
                vds_no
            )

        # Extract components in order
        valve_prefix, prefix_len = self._extract_valve_prefix(vds_no)
        bore_type, has_metal_seated = self._extract_bore_type(vds_no, prefix_len)
        piping_class, modifiers = self._extract_piping_class_and_modifiers(
            vds_no, valve_prefix, bore_type, has_metal_seated, prefix_len
        )
        end_connection = self._extract_end_connection(vds_no)

        # Determine modifier flags
        is_nace = 'N' in modifiers
        is_low_temp = 'L' in modifiers
        is_metal_seated = has_metal_seated or bore_type == BoreType.METAL_SEATED

        return DecodedVDS(
            raw_vds=vds_no,
            valve_type_prefix=valve_prefix,
            bore_type=bore_type,
            piping_class=piping_class,
            is_nace_compliant=is_nace,
            is_low_temp=is_low_temp,
            is_metal_seated=is_metal_seated,
            end_connection=end_connection,
        )

    def _extract_valve_prefix(self, vds: str) -> tuple[ValveTypePrefix, int]:
        """
        Extract valve type prefix (2 or 3 characters).

        Tries 3-character prefixes first, then falls back to 2-character.

        Args:
            vds: Normalized VDS string

        Returns:
            Tuple of (ValveTypePrefix enum, prefix_length)

        Raises:
            VDSDecodingError: If prefix is unknown
        """
        valid_prefixes = self.rules.get('valve_type_prefixes', {})

        # Try 3-character prefix first
        if len(vds) >= 3:
            prefix3 = vds[:3]
            if prefix3 in valid_prefixes:
                try:
                    return ValveTypePrefix.from_string(prefix3), 3
                except ValueError:
                    pass

        # Fall back to 2-character prefix
        prefix2 = vds[:2]
        if prefix2 in valid_prefixes:
            try:
                return ValveTypePrefix.from_string(prefix2), 2
            except ValueError as e:
                raise VDSDecodingError(str(e), vds, "valve_prefix")

        valid_list = ', '.join(valid_prefixes.keys())
        raise VDSDecodingError(
            f"Unknown valve type prefix in {vds}. "
            f"Valid prefixes: {valid_list}",
            vds,
            "valve_prefix"
        )

    def _extract_bore_type(self, vds: str, prefix_len: int = 2) -> tuple[BoreType, bool]:
        """
        Extract bore type from position after prefix.

        Handles special case where 'M' indicates metal-seated
        following a bore type.

        Args:
            vds: Normalized VDS string
            prefix_len: Length of the valve type prefix (2 or 3)

        Returns:
            Tuple of (BoreType, has_metal_seated_flag)

        Raises:
            VDSDecodingError: If bore type is unknown
        """
        # For 3-char prefixes, bore type may be embedded or after prefix
        bore_pos = prefix_len

        # Handle case where bore is not explicit (some 3-char prefixes include bore info)
        if bore_pos >= len(vds):
            # Default to Full bore if not specified
            return BoreType.FULL, False

        bore_char = vds[bore_pos]
        has_metal_seated = False

        # Check if next position is metal-seated indicator
        if len(vds) > bore_pos + 1 and vds[bore_pos + 1] == 'M':
            has_metal_seated = True

        # If bore_char itself is M, it means metal-seated full bore
        if bore_char == 'M':
            return BoreType.METAL_SEATED, True

        # Core bore types that are always recognized
        core_bore_types = {'F', 'R', 'M', 'T'}

        valid_bores = self.rules.get('bore_types', {})

        # For some VDS formats (like GAWA1R), the character after prefix may be piping class
        # Check if it looks like a piping class letter (A-G) - these are NOT bore types
        # They indicate piping class, not bore configuration
        if bore_char in 'ABCDEFG':
            # For 3-char prefixes, assume these are piping class letters
            # Return default bore type based on prefix rules
            prefix = vds[:prefix_len]
            prefix_rules = self.rules.get('valve_type_prefixes', {}).get(prefix, {})
            default_bore = prefix_rules.get('default_bore', 'F')
            try:
                return BoreType.from_string(default_bore), False
            except ValueError:
                return BoreType.FULL, False

        if bore_char not in valid_bores and bore_char not in core_bore_types:
            valid_list = ', '.join(valid_bores.keys())
            raise VDSDecodingError(
                f"Unknown bore type '{bore_char}' in {vds}. "
                f"Valid bore types: {valid_list}",
                vds,
                "bore_type"
            )

        try:
            return BoreType.from_string(bore_char), has_metal_seated
        except ValueError as e:
            raise VDSDecodingError(str(e), vds, "bore_type")

    def _extract_piping_class_and_modifiers(
        self,
        vds: str,
        prefix: ValveTypePrefix,
        bore: BoreType,
        has_metal_seated: bool,
        prefix_len: int = 2
    ) -> tuple[str, set[str]]:
        """
        Extract piping class and modifiers from VDS.

        The piping class is located after the prefix, bore type,
        and optional metal-seated indicator, before the end connection.

        Args:
            vds: Normalized VDS string
            prefix: Valve type prefix
            bore: Bore type
            has_metal_seated: Whether metal-seated flag was detected
            prefix_len: Length of the valve type prefix (2 or 3)

        Returns:
            Tuple of (full_piping_class, set of modifiers)

        Raises:
            VDSDecodingError: If piping class cannot be parsed
        """
        # Calculate start position
        # Prefix (2 or 3) + Bore (1, if present) + Optional Metal-seated (1 if present)
        start_pos = prefix_len

        # Valid bore type characters (not including A-G which are piping class letters)
        valid_bore_chars = ['F', 'R', 'M', 'T']

        # Check if there's an explicit bore type character
        if start_pos < len(vds) and vds[start_pos] in valid_bore_chars:
            start_pos += 1
            # Check for metal-seated indicator after bore type
            if has_metal_seated and start_pos < len(vds) and vds[start_pos] == 'M':
                start_pos += 1
        elif bore == BoreType.METAL_SEATED:
            # If bore is M, it was already counted
            pass

        # End position is one before the last character (end connection)
        end_pos = len(vds) - 1

        # Handle special end connections (like 'WR' for wafer RF)
        # Check if last 2 chars could be a compound end connection
        if end_pos > start_pos and vds[-2] in ['W', 'T'] and vds[-1] in ['R', 'J', 'F']:
            # Could be WR (Wafer RF), TJ (Threaded RTJ), etc.
            end_pos = len(vds) - 2

        class_portion = vds[start_pos:end_pos]

        if not class_portion:
            raise VDSDecodingError(
                f"Cannot extract piping class from {vds}",
                vds,
                "piping_class"
            )

        # Parse piping class: Multiple formats supported
        # Standard: Letter + Digits + Optional modifiers (L, N, LN)
        #   Examples: A1, B1N, G1LN, A10N, G20LN
        # Instrumentation: Digits + Letter + Optional modifiers
        #   Examples: 50A, 50B, 50C (series + class)
        match = re.match(r'^([A-Z]\d+)([LN]*)$', class_portion)

        # Try instrumentation format (digits + letter)
        if not match:
            match = re.match(r'^(\d+[A-Z])([LN]*)$', class_portion)

        if not match:
            raise VDSDecodingError(
                f"Invalid piping class format '{class_portion}' in {vds}. "
                f"Expected format: Letter + Digits (A1, B1) or Digits + Letter (50A) + optional L/N modifiers",
                vds,
                "piping_class"
            )

        base_class = match.group(1)
        modifier_str = match.group(2)

        # Full piping class includes modifiers
        full_class = base_class + modifier_str

        # Extract individual modifiers
        modifiers = set(modifier_str) if modifier_str else set()

        return full_class, modifiers

    def _extract_end_connection(self, vds: str) -> EndConnection:
        """
        Extract end connection type from last character.

        Args:
            vds: Normalized VDS string

        Returns:
            EndConnection enum

        Raises:
            VDSDecodingError: If end connection is unknown
        """
        end_char = vds[-1]
        valid_ends = self.rules.get('end_connections', {})

        if end_char not in valid_ends:
            valid_list = ', '.join(valid_ends.keys())
            raise VDSDecodingError(
                f"Unknown end connection '{end_char}' in {vds}. "
                f"Valid end connections: {valid_list}",
                vds,
                "end_connection"
            )

        try:
            return EndConnection.from_string(end_char)
        except ValueError as e:
            raise VDSDecodingError(str(e), vds, "end_connection")

    def validate(self, vds_no: str) -> tuple[bool, Optional[str]]:
        """
        Validate a VDS number without raising exceptions.

        Args:
            vds_no: VDS number to validate

        Returns:
            Tuple of (is_valid, error_message or None)
        """
        try:
            self.decode(vds_no)
            return True, None
        except VDSDecodingError as e:
            return False, str(e)

    def get_supported_prefixes(self) -> list[str]:
        """Get list of supported valve type prefixes."""
        return list(self.rules.get('valve_type_prefixes', {}).keys())

    def get_supported_bore_types(self) -> list[str]:
        """Get list of supported bore types."""
        return list(self.rules.get('bore_types', {}).keys())

    def get_supported_end_connections(self) -> list[str]:
        """Get list of supported end connections."""
        return list(self.rules.get('end_connections', {}).keys())


# Convenience function for quick decoding
def decode_vds(vds_no: str) -> DecodedVDS:
    """
    Quick decode function using default rules.

    Args:
        vds_no: VDS number string

    Returns:
        DecodedVDS object

    Example:
        >>> result = decode_vds("BSFA1R")
        >>> print(result.valve_type_full)
        'Ball Valve, Full Bore'
    """
    decoder = VDSDecoder()
    return decoder.decode(vds_no)
