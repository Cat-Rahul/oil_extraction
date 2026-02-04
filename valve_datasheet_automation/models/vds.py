"""
VDS (Valve Data Sheet) data models.

This module contains the data models for parsing and representing
VDS numbers and their decoded components.

VDS Format Examples:
    - BSFA1R: Ball valve, Full bore, Class A1, RF end
    - BSFMG1LNJ: Ball valve, Full bore, Metal-seated, Class G1LN, RTJ end
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator
import re


class ValveTypePrefix(str, Enum):
    """Valve type prefixes in VDS numbering system."""
    # 2-character prefixes (legacy)
    BALL = "BS"      # Ball valve dataSheet
    GATE = "GS"      # Gate valve dataSheet
    CHECK = "CS"     # Check valve dataSheet
    PLUG = "PS"      # Plug valve dataSheet

    # 3-character prefixes (new format)
    BALL_FULL = "BSF"       # Ball valve, Full bore
    BALL_REDUCED = "BSR"    # Ball valve, Reduced bore
    GATE_OSY = "GAW"        # Gate valve, Outside Screw & Yoke (Wedge)
    GLOBE = "GLS"           # Globe valve, Outside Screw
    CHECK_PISTON = "CHP"    # Check valve, Piston type
    CHECK_SWING = "CSW"     # Check valve, Swing type
    CHECK_DUAL = "CDP"      # Check valve, Dual Plate
    BUTTERFLY = "BFD"       # Butterfly valve
    DBB = "DSR"             # Double Block and Bleed valve (Reduced)
    DBB_FULL = "DSF"        # Double Block and Bleed valve (Full)
    NEEDLE = "NEE"          # Needle valve

    @classmethod
    def from_string(cls, value: str) -> "ValveTypePrefix":
        """Get enum from string value."""
        value = value.upper()
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"Unknown valve type prefix: {value}")

    @property
    def full_name(self) -> str:
        """Get full valve type name."""
        names = {
            self.BALL: "Ball Valve",
            self.GATE: "Gate Valve",
            self.CHECK: "Check Valve",
            self.PLUG: "Plug Valve",
            self.BALL_FULL: "Ball Valve, Full Bore",
            self.BALL_REDUCED: "Ball Valve, Reduced Bore",
            self.GATE_OSY: "Gate Valve, Outside Screw and Yoke",
            self.GLOBE: "Globe Valve, Outside Screw and Yoke",
            self.CHECK_PISTON: "Check Valve, Piston Type",
            self.CHECK_SWING: "Check Valve, Swing Type",
            self.CHECK_DUAL: "Check Valve, Dual Plate",
            self.BUTTERFLY: "Butterfly Valve",
            self.DBB: "Double Block and Bleed Valve",
            self.DBB_FULL: "Double Block and Bleed Valve",
            self.NEEDLE: "Needle Valve",
        }
        return names[self]

    @property
    def primary_standard(self) -> str:
        """Get primary design standard for this valve type."""
        standards = {
            self.BALL: "API 6D / ISO 17292",
            self.GATE: "API 6D / API 600",
            self.CHECK: "API 6D / API 594",
            self.PLUG: "API 6D / API 599",
            self.BALL_FULL: "API 6D / ISO 17292",
            self.BALL_REDUCED: "API 6D / ISO 17292",
            self.GATE_OSY: "API 600 / API 6D",
            self.GLOBE: "API 602 / BS 1873",
            self.CHECK_PISTON: "API 602 / BS 1868",
            self.CHECK_SWING: "API 6D / API 594",
            self.CHECK_DUAL: "API 594",
            self.BUTTERFLY: "API 609 / MSS SP-68",
            self.DBB: "API 6D",
            self.DBB_FULL: "API 6D",
            self.NEEDLE: "ASME B16.34",
        }
        return standards[self]


class BoreType(str, Enum):
    """Valve bore type classifications."""
    FULL = "F"           # Full bore / Full opening
    REDUCED = "R"        # Reduced bore / Reduced opening
    METAL_SEATED = "M"   # Metal-seated (typically full bore)
    TUBE = "T"           # Tube connection (for instrumentation valves)

    @classmethod
    def from_string(cls, value: str) -> "BoreType":
        """Get enum from string value."""
        value = value.upper()
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"Unknown bore type: {value}")

    @property
    def full_name(self) -> str:
        """Get full bore type description."""
        names = {
            self.FULL: "Full Bore",
            self.REDUCED: "Reduced Bore",
            self.METAL_SEATED: "Full Bore",  # Metal-seated is typically full bore
            self.TUBE: "Tube Connection",
        }
        return names[self]

    @property
    def is_metal_seated(self) -> bool:
        """Check if this is a metal-seated configuration."""
        return self == self.METAL_SEATED


class EndConnection(str, Enum):
    """End connection types for valves."""
    RF = "R"    # Raised Face
    RTJ = "J"   # Ring Type Joint
    FF = "F"    # Flat Face
    BW = "W"    # Butt Weld
    SW = "S"    # Socket Weld

    @classmethod
    def from_string(cls, value: str) -> "EndConnection":
        """Get enum from string value."""
        value = value.upper()
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"Unknown end connection: {value}")

    @property
    def full_name(self) -> str:
        """Get full end connection name."""
        names = {
            self.RF: "Raised Face",
            self.RTJ: "Ring Type Joint",
            self.FF: "Flat Face",
            self.BW: "Butt Weld",
            self.SW: "Socket Weld",
        }
        return names[self]

    @property
    def standard(self) -> str:
        """Get applicable standard for this end connection."""
        return "ASME B16.5"

    def get_flange_description(self) -> str:
        """Get full flange description string."""
        return f"Flanged {self.standard} {self.name}"


class DecodedVDS(BaseModel):
    """
    Decoded VDS Number with all extracted attributes.

    This model represents the fully parsed VDS number with
    all its constituent parts extracted and validated.

    Attributes:
        raw_vds: Original VDS string (normalized to uppercase)
        valve_type_prefix: Valve type (BS, GS, CS, PS)
        bore_type: Bore configuration (F, R, M)
        piping_class: Piping class code (e.g., A1, B1N, G1LN)
        piping_class_base: Base piping class without modifiers (e.g., A1)
        is_nace_compliant: Whether NACE MR0175 compliance is required
        is_low_temp: Whether low temperature service is required
        is_metal_seated: Whether metal-seated construction is required
        end_connection: End connection type (R, J, F, etc.)
        valve_type_full: Full valve type description

    Example:
        >>> vds = DecodedVDS(
        ...     raw_vds="BSFA1R",
        ...     valve_type_prefix=ValveTypePrefix.BALL,
        ...     bore_type=BoreType.FULL,
        ...     piping_class="A1",
        ...     end_connection=EndConnection.RF
        ... )
        >>> vds.valve_type_full
        'Ball Valve, Full Bore'
    """

    raw_vds: str = Field(..., description="Original VDS string")
    valve_type_prefix: ValveTypePrefix = Field(..., description="Valve type code")
    bore_type: BoreType = Field(..., description="Bore type code")
    piping_class: str = Field(..., description="Full piping class (e.g., A1, B1N)")
    piping_class_base: str = Field(default="", description="Base class without modifiers")
    is_nace_compliant: bool = Field(default=False, description="NACE MR0175 compliance")
    is_low_temp: bool = Field(default=False, description="Low temperature service")
    is_metal_seated: bool = Field(default=False, description="Metal-seated construction")
    end_connection: EndConnection = Field(..., description="End connection type")

    class Config:
        """Pydantic configuration."""
        frozen = False  # Allow mutation for post-processing

    def model_post_init(self, __context) -> None:
        """Post-initialization processing."""
        # Normalize raw VDS
        object.__setattr__(self, 'raw_vds', self.raw_vds.upper().strip())

        # Extract base piping class if not set
        if not self.piping_class_base:
            match = re.match(r'^([A-Z]\d+)', self.piping_class)
            if match:
                object.__setattr__(self, 'piping_class_base', match.group(1))
            else:
                object.__setattr__(self, 'piping_class_base', self.piping_class)

        # Set metal-seated flag from bore type
        if self.bore_type == BoreType.METAL_SEATED:
            object.__setattr__(self, 'is_metal_seated', True)

    @field_validator('piping_class')
    @classmethod
    def validate_piping_class(cls, v: str) -> str:
        """Validate piping class format."""
        v = v.upper().strip()
        # Standard pattern: Letter + digits + optional modifiers (L, N, LN)
        # Examples: A1, B1N, G1LN
        # Instrumentation pattern: Digits + letter + optional modifiers
        # Examples: 50A, 50B, 50C
        if not re.match(r'^([A-Z]\d+[LN]*|\d+[A-Z][LN]*)$', v):
            raise ValueError(f'Invalid piping class format: {v}')
        return v

    @property
    def valve_type_full(self) -> str:
        """Get full valve type description (e.g., 'Ball Valve, Full Bore')."""
        valve_name = self.valve_type_prefix.full_name
        bore_name = self.bore_type.full_name
        return f"{valve_name}, {bore_name}"

    @property
    def end_connection_description(self) -> str:
        """Get full end connection description."""
        return self.end_connection.get_flange_description()

    @property
    def primary_standard(self) -> str:
        """Get primary design standard for this valve."""
        return self.valve_type_prefix.primary_standard

    @property
    def modifiers(self) -> list[str]:
        """Get list of active modifiers."""
        mods = []
        if self.is_nace_compliant:
            mods.append("NACE")
        if self.is_low_temp:
            mods.append("Low Temp")
        if self.is_metal_seated:
            mods.append("Metal Seated")
        return mods

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "raw_vds": self.raw_vds,
            "valve_type": self.valve_type_prefix.value,
            "valve_type_name": self.valve_type_prefix.full_name,
            "bore_type": self.bore_type.value,
            "bore_type_name": self.bore_type.full_name,
            "piping_class": self.piping_class,
            "piping_class_base": self.piping_class_base,
            "is_nace_compliant": self.is_nace_compliant,
            "is_low_temp": self.is_low_temp,
            "is_metal_seated": self.is_metal_seated,
            "end_connection": self.end_connection.value,
            "end_connection_name": self.end_connection.full_name,
            "valve_type_full": self.valve_type_full,
            "primary_standard": self.primary_standard,
            "modifiers": self.modifiers,
        }


class VDSPattern(BaseModel):
    """
    Pattern definition for VDS parsing rules.

    Used in configuration to define how VDS segments are extracted.
    """
    segment_name: str = Field(..., description="Name of the segment")
    position: Optional[int] = Field(None, description="Fixed position in string")
    length: Optional[int] = Field(None, description="Fixed length of segment")
    pattern: Optional[str] = Field(None, description="Regex pattern for extraction")
    required: bool = Field(default=True, description="Whether segment is required")
    mapping: dict[str, str] = Field(default_factory=dict, description="Value mappings")
