"""
Unit tests for VDS Decoder.
"""

import pytest
import sys
from pathlib import Path

# Add parent to path for package imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from valve_datasheet_automation.core.vds_decoder import VDSDecoder, VDSDecodingError
from valve_datasheet_automation.models.vds import ValveTypePrefix, BoreType, EndConnection


class TestVDSDecoder:
    """Test suite for VDS decoder."""

    @pytest.fixture
    def decoder(self):
        """Create decoder with default rules."""
        return VDSDecoder()

    # === Happy Path Tests ===

    @pytest.mark.parametrize("vds,expected_prefix,expected_bore,expected_class,expected_end", [
        ("BSFA1R", ValveTypePrefix.BALL, BoreType.FULL, "A1", EndConnection.RF),
        ("BSRA1R", ValveTypePrefix.BALL, BoreType.REDUCED, "A1", EndConnection.RF),
        ("BSFB1R", ValveTypePrefix.BALL, BoreType.FULL, "B1", EndConnection.RF),
        ("BSFE1J", ValveTypePrefix.BALL, BoreType.FULL, "E1", EndConnection.RTJ),
        ("BSFG1J", ValveTypePrefix.BALL, BoreType.FULL, "G1", EndConnection.RTJ),
    ])
    def test_decode_basic_patterns(self, decoder, vds, expected_prefix, expected_bore, expected_class, expected_end):
        """Test decoding basic VDS patterns."""
        result = decoder.decode(vds)

        assert result.valve_type_prefix == expected_prefix
        assert result.bore_type == expected_bore
        assert result.piping_class == expected_class
        assert result.end_connection == expected_end

    @pytest.mark.parametrize("vds,is_nace", [
        ("BSFA1R", False),
        ("BSFA1NR", True),
        ("BSFB1NR", True),
        ("BSFG1LNJ", True),
    ])
    def test_nace_compliance_detection(self, decoder, vds, is_nace):
        """Test NACE compliance flag extraction."""
        result = decoder.decode(vds)
        assert result.is_nace_compliant == is_nace

    @pytest.mark.parametrize("vds,is_low_temp", [
        ("BSFA1R", False),
        ("BSFA1LR", True),
        ("BSFG1LNJ", True),
        ("BSFA1LNR", True),
    ])
    def test_low_temp_detection(self, decoder, vds, is_low_temp):
        """Test low temperature flag extraction."""
        result = decoder.decode(vds)
        assert result.is_low_temp == is_low_temp

    def test_decode_with_modifiers(self, decoder):
        """Test decoding VDS with multiple modifiers."""
        result = decoder.decode("BSFG1LNJ")

        assert result.piping_class == "G1LN"
        assert result.is_nace_compliant == True
        assert result.is_low_temp == True
        assert result.end_connection == EndConnection.RTJ

    def test_valve_type_full_property(self, decoder):
        """Test valve_type_full property."""
        result = decoder.decode("BSFA1R")
        assert result.valve_type_full == "Ball Valve, Full Bore"

        result = decoder.decode("BSRA1R")
        assert result.valve_type_full == "Ball Valve, Reduced Bore"

    # === Error Cases ===

    @pytest.mark.parametrize("invalid_vds,expected_error", [
        ("", "cannot be empty"),
        ("XYZ", "too short"),
        ("XXFA1R", "Unknown valve type prefix"),
        ("BSXA1R", "Unknown bore type"),
        ("BSFA1X", "Unknown end connection"),
    ])
    def test_decode_invalid_vds(self, decoder, invalid_vds, expected_error):
        """Test error handling for invalid VDS numbers."""
        with pytest.raises(VDSDecodingError) as exc_info:
            decoder.decode(invalid_vds)

        assert expected_error.lower() in str(exc_info.value).lower()

    # === Validation ===

    def test_validate_valid_vds(self, decoder):
        """Test validation returns True for valid VDS."""
        is_valid, error = decoder.validate("BSFA1R")
        assert is_valid == True
        assert error is None

    def test_validate_invalid_vds(self, decoder):
        """Test validation returns False for invalid VDS."""
        is_valid, error = decoder.validate("INVALID")
        assert is_valid == False
        assert error is not None

    # === Case Insensitivity ===

    def test_case_insensitivity(self, decoder):
        """Test decoder handles case variations."""
        upper = decoder.decode("BSFA1R")
        lower = decoder.decode("bsfa1r")
        mixed = decoder.decode("BsFa1r")

        # All should normalize to uppercase
        assert upper.raw_vds == "BSFA1R"
        assert lower.raw_vds == "BSFA1R"
        assert mixed.raw_vds == "BSFA1R"

    # === To Dict ===

    def test_to_dict(self, decoder):
        """Test conversion to dictionary."""
        result = decoder.decode("BSFA1R")
        data = result.to_dict()

        assert data["raw_vds"] == "BSFA1R"
        assert data["valve_type"] == "BS"
        assert data["bore_type"] == "F"
        assert data["piping_class"] == "A1"
        assert data["end_connection"] == "R"
        assert "valve_type_full" in data


class TestDecodedVDSModel:
    """Test DecodedVDS model."""

    def test_piping_class_validation(self):
        """Test piping class format validation."""
        from valve_datasheet_automation.models.vds import DecodedVDS

        # Valid piping classes
        valid = DecodedVDS(
            raw_vds="BSFA1R",
            valve_type_prefix=ValveTypePrefix.BALL,
            bore_type=BoreType.FULL,
            piping_class="A1",
            end_connection=EndConnection.RF,
        )
        assert valid.piping_class == "A1"

        # With modifiers
        valid_mod = DecodedVDS(
            raw_vds="BSFB1NR",
            valve_type_prefix=ValveTypePrefix.BALL,
            bore_type=BoreType.FULL,
            piping_class="B1N",
            end_connection=EndConnection.RF,
        )
        assert valid_mod.piping_class == "B1N"

    def test_primary_standard_property(self):
        """Test primary standard lookup."""
        from valve_datasheet_automation.models.vds import DecodedVDS

        ball = DecodedVDS(
            raw_vds="BSFA1R",
            valve_type_prefix=ValveTypePrefix.BALL,
            bore_type=BoreType.FULL,
            piping_class="A1",
            end_connection=EndConnection.RF,
        )
        assert "API 6D" in ball.primary_standard


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
