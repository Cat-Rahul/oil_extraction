"""
Conflict Detector.

Detects conflicts between different data sources (PMS vs Standards)
in generated datasheets.
"""

from typing import Optional

from ..models.vds import DecodedVDS
from ..models.datasheet import ValveDatasheet, FieldSource


class ConflictDetector:
    """
    Detects conflicts between data sources in datasheets.

    Identifies cases where:
    - PMS data conflicts with standard requirements
    - VDS attributes conflict with PMS class
    - Material selections conflict with service requirements

    Example:
        >>> detector = ConflictDetector()
        >>> conflicts = detector.detect(datasheet, decoded_vds)
        >>> for conflict in conflicts:
        ...     print(conflict)
    """

    def detect(
        self,
        datasheet: ValveDatasheet,
        decoded_vds: Optional[DecodedVDS] = None
    ) -> list[str]:
        """
        Detect conflicts in a datasheet.

        Args:
            datasheet: Generated ValveDatasheet
            decoded_vds: Optional decoded VDS for context

        Returns:
            List of conflict descriptions
        """
        conflicts = []

        # Check NACE compliance conflicts
        if decoded_vds and decoded_vds.is_nace_compliant:
            nace_conflicts = self._check_nace_compliance(datasheet)
            conflicts.extend(nace_conflicts)

        # Check low temperature conflicts
        if decoded_vds and decoded_vds.is_low_temp:
            lt_conflicts = self._check_low_temp_compliance(datasheet)
            conflicts.extend(lt_conflicts)

        # Check pressure rating consistency
        pr_conflicts = self._check_pressure_rating_consistency(datasheet)
        conflicts.extend(pr_conflicts)

        # Check material compatibility
        mat_conflicts = self._check_material_compatibility(datasheet)
        conflicts.extend(mat_conflicts)

        return conflicts

    def _check_nace_compliance(self, datasheet: ValveDatasheet) -> list[str]:
        """Check NACE compliance requirements are met."""
        conflicts = []

        # Check sour service field
        sour_service = datasheet.sour_service.value
        if sour_service and "NACE" not in str(sour_service):
            conflicts.append(
                "VDS indicates NACE compliance but sour service field "
                "does not reference NACE MR0175"
            )

        # Check bolt material for NACE
        bolts = datasheet.bolts.value
        if bolts and "B7M" not in str(bolts) and "NACE" not in str(bolts):
            conflicts.append(
                "NACE compliance required but bolt material may not be "
                "NACE compliant (expected B7M grade)"
            )

        return conflicts

    def _check_low_temp_compliance(self, datasheet: ValveDatasheet) -> list[str]:
        """Check low temperature service requirements."""
        conflicts = []

        # Check body material for low temp
        body_material = datasheet.body_material.value
        if body_material:
            body_str = str(body_material).upper()
            # Low temp typically requires LF2, LCB, or similar
            low_temp_materials = ['LF2', 'LCB', 'LF3', 'LCC', 'A350', 'A352']
            has_low_temp_material = any(
                mat in body_str for mat in low_temp_materials
            )
            if not has_low_temp_material:
                conflicts.append(
                    f"Low temperature service required but body material "
                    f"'{body_material}' may not be suitable for low temp"
                )

        return conflicts

    def _check_pressure_rating_consistency(
        self,
        datasheet: ValveDatasheet
    ) -> list[str]:
        """Check pressure rating is consistent across fields."""
        conflicts = []

        pressure_class = datasheet.pressure_class.value
        design_pressure = datasheet.design_pressure.value

        # Basic sanity check - if we have both, they should be consistent
        if pressure_class and design_pressure:
            # Extract class number
            import re
            class_match = re.search(r'(\d+)', str(pressure_class))
            if class_match:
                class_num = int(class_match.group(1))

                # Very high pressure class should have significant design pressure
                pressure_match = re.search(r'(\d+\.?\d*)', str(design_pressure))
                if pressure_match:
                    pressure_val = float(pressure_match.group(1))

                    # Rough sanity check (not exact - would need proper tables)
                    if class_num >= 900 and pressure_val < 50:
                        conflicts.append(
                            f"Pressure class {class_num} but design pressure "
                            f"seems low ({design_pressure})"
                        )

        return conflicts

    def _check_material_compatibility(self, datasheet: ValveDatasheet) -> list[str]:
        """Check material selections are compatible."""
        conflicts = []

        body_material = str(datasheet.body_material.value or "")
        ball_material = str(datasheet.ball_material.value or "")

        # Check galvanic compatibility (simplified)
        if body_material and ball_material:
            # Carbon steel body should typically have SS internals
            if "A105" in body_material or "A216" in body_material:
                if "F316" not in ball_material and "316" not in ball_material:
                    conflicts.append(
                        "Carbon steel body typically paired with SS316 ball "
                        f"but found: {ball_material}"
                    )

        return conflicts

    def get_conflict_summary(self, conflicts: list[str]) -> dict:
        """
        Get summary of detected conflicts.

        Args:
            conflicts: List of conflict descriptions

        Returns:
            Summary dictionary
        """
        return {
            "total_conflicts": len(conflicts),
            "has_conflicts": len(conflicts) > 0,
            "conflicts": conflicts,
            "categories": {
                "nace": sum(1 for c in conflicts if "NACE" in c),
                "low_temp": sum(1 for c in conflicts if "low temp" in c.lower()),
                "pressure": sum(1 for c in conflicts if "pressure" in c.lower()),
                "material": sum(1 for c in conflicts if "material" in c.lower()),
            }
        }
