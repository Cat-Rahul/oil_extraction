"""
Standards Repository.

Provides access to valve standard clauses (API 6D, ASME B16.34, etc.)
for resolving "As per valve standard" fields in datasheets.
"""

import json
from enum import Enum
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field


class RuleType(str, Enum):
    """Classification of standard clause rule types."""
    MANDATORY = "mandatory"
    RECOMMENDATION = "recommendation"
    INFORMATIONAL = "informational"
    EXAMPLE = "example"
    FORMULA = "formula"
    DEFINITION = "definition"


class StandardClause(BaseModel):
    """
    Represents a single clause from a valve standard.

    Attributes:
        standard: Standard name (e.g., "API 6D")
        section: Section number
        clause: Clause number (e.g., "5.2.1")
        title: Clause title
        text: Full clause text
        page: Page number in source document
        rule_type: Classification (mandatory, recommendation, etc.)
        normative_references: Referenced standards
        applies_to: Valve types this clause applies to
        datasheet_field: Mapped datasheet field name
    """
    standard: str = Field(..., description="Standard name")
    section: str = Field(default="", description="Section number")
    clause: str = Field(..., description="Clause number")
    title: str = Field(default="", description="Clause title")
    text: str = Field(default="", description="Clause text")
    page: Optional[int] = Field(None, description="Page number")
    rule_type: str = Field(default="informational", description="Rule type")
    normative_references: list[str] = Field(default_factory=list)
    applies_to: list[str] = Field(default_factory=list)
    datasheet_field: str = Field(default="General Requirement")

    @property
    def rule_type_enum(self) -> RuleType:
        """Get rule type as enum."""
        try:
            return RuleType(self.rule_type)
        except ValueError:
            return RuleType.INFORMATIONAL

    @property
    def is_mandatory(self) -> bool:
        """Check if clause is mandatory."""
        return self.rule_type_enum == RuleType.MANDATORY

    @property
    def full_reference(self) -> str:
        """Get full clause reference string."""
        return f"{self.standard} {self.clause}"


class StandardsRepository:
    """
    Repository for accessing valve standard clauses.

    Loads extracted clauses from JSON and provides lookup methods
    for resolving standard-based field values.

    Attributes:
        clauses: List of all loaded clauses
        _by_field: Index of clauses by datasheet field
        _by_valve_type: Index of clauses by valve type

    Example:
        >>> repo = StandardsRepository(Path("data/clauses.json"))
        >>> clauses = repo.get_clauses_for_field("Hydrostatic Test Pressure")
        >>> for c in clauses:
        ...     print(f"{c.standard} {c.clause}: {c.rule_type}")
    """

    def __init__(self, clauses_path: Optional[Path] = None):
        """
        Initialize repository with extracted clauses.

        Args:
            clauses_path: Path to clauses JSON file
        """
        self._clauses: list[StandardClause] = []
        self._by_field: dict[str, list[StandardClause]] = {}
        self._by_valve_type: dict[str, list[StandardClause]] = {}
        self._by_standard: dict[str, list[StandardClause]] = {}

        if clauses_path and clauses_path.exists():
            self._load_clauses(clauses_path)
            self._build_indexes()

    def _load_clauses(self, path: Path) -> None:
        """Load clauses from JSON file."""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for item in data:
            try:
                clause = StandardClause(**item)
                self._clauses.append(clause)
            except Exception:
                # Skip malformed clauses
                continue

    def _build_indexes(self) -> None:
        """Build lookup indexes for efficient queries."""
        for clause in self._clauses:
            # Index by datasheet field
            field = clause.datasheet_field
            if field not in self._by_field:
                self._by_field[field] = []
            self._by_field[field].append(clause)

            # Index by valve type
            for vt in clause.applies_to:
                if vt not in self._by_valve_type:
                    self._by_valve_type[vt] = []
                self._by_valve_type[vt].append(clause)

            # Index by standard
            std = clause.standard
            if std not in self._by_standard:
                self._by_standard[std] = []
            self._by_standard[std].append(clause)

    def get_clauses_for_field(
        self,
        field_name: str,
        valve_type: Optional[str] = None,
        rule_type: Optional[RuleType] = None
    ) -> list[StandardClause]:
        """
        Get clauses applicable to a datasheet field.

        Args:
            field_name: Datasheet field name
            valve_type: Filter by valve type (optional)
            rule_type: Filter by rule type (optional)

        Returns:
            List of matching clauses
        """
        clauses = self._by_field.get(field_name, [])

        if valve_type:
            clauses = [
                c for c in clauses
                if valve_type in c.applies_to or "All Valves" in c.applies_to
            ]

        if rule_type:
            clauses = [c for c in clauses if c.rule_type_enum == rule_type]

        return clauses

    def get_mandatory_requirements(
        self,
        valve_type: str,
        field_name: Optional[str] = None
    ) -> list[StandardClause]:
        """
        Get mandatory requirements for a valve type.

        Args:
            valve_type: Valve type (e.g., "Ball Valve")
            field_name: Optional field name filter

        Returns:
            List of mandatory clauses
        """
        if field_name:
            return self.get_clauses_for_field(
                field_name,
                valve_type=valve_type,
                rule_type=RuleType.MANDATORY
            )

        # Get all mandatory clauses for valve type
        all_clauses = self._by_valve_type.get(valve_type, [])
        all_clauses.extend(self._by_valve_type.get("All Valves", []))

        return [c for c in all_clauses if c.is_mandatory]

    def get_standard_value(
        self,
        field_name: str,
        valve_type: str
    ) -> Optional[str]:
        """
        Get standard-defined value for a field.

        Extracts values that are explicitly defined in standards.

        Args:
            field_name: Datasheet field name
            valve_type: Valve type

        Returns:
            Standard reference string or None
        """
        clauses = self.get_mandatory_requirements(valve_type, field_name)

        if clauses:
            # Return reference to the first matching clause
            clause = clauses[0]
            refs = clause.normative_references
            if refs:
                return f"As per {', '.join(refs[:2])}"
            return f"As per {clause.full_reference}"

        return None

    def get_normative_references(
        self,
        field_name: str,
        valve_type: Optional[str] = None
    ) -> list[str]:
        """
        Get all normative references for a field.

        Args:
            field_name: Datasheet field name
            valve_type: Optional valve type filter

        Returns:
            List of unique normative references
        """
        clauses = self.get_clauses_for_field(field_name, valve_type)

        refs = set()
        for clause in clauses:
            refs.update(clause.normative_references)

        return sorted(refs)

    def get_clauses_by_standard(self, standard: str) -> list[StandardClause]:
        """Get all clauses from a specific standard."""
        return self._by_standard.get(standard, [])

    def get_clause(self, standard: str, clause_no: str) -> Optional[StandardClause]:
        """
        Get a specific clause by standard and clause number.

        Args:
            standard: Standard name (e.g., "API 6D")
            clause_no: Clause number (e.g., "5.2.1")

        Returns:
            StandardClause or None
        """
        clauses = self._by_standard.get(standard, [])
        for c in clauses:
            if c.clause == clause_no:
                return c
        return None

    def search_clauses(self, keyword: str) -> list[StandardClause]:
        """
        Search clauses by keyword in title or text.

        Args:
            keyword: Search keyword (case-insensitive)

        Returns:
            List of matching clauses
        """
        keyword = keyword.lower()
        return [
            c for c in self._clauses
            if keyword in c.title.lower() or keyword in c.text.lower()
        ]

    def list_all_fields(self) -> list[str]:
        """List all datasheet fields that have associated clauses."""
        return sorted(self._by_field.keys())

    def list_all_standards(self) -> list[str]:
        """List all standards in the repository."""
        return sorted(self._by_standard.keys())

    def list_all_valve_types(self) -> list[str]:
        """List all valve types in the repository."""
        return sorted(self._by_valve_type.keys())

    @property
    def total_clauses(self) -> int:
        """Total number of clauses in repository."""
        return len(self._clauses)

    def add_default_clauses(self) -> None:
        """Add default clauses for testing/fallback."""
        defaults = [
            StandardClause(
                standard="API 6D",
                clause="1.1",
                title="General",
                rule_type="informational",
                applies_to=["Ball Valve", "Gate Valve", "Check Valve", "Plug Valve"],
                datasheet_field="Design Standard",
            ),
            StandardClause(
                standard="API 598",
                clause="4",
                title="Testing Requirements",
                rule_type="mandatory",
                applies_to=["All Valves"],
                datasheet_field="Inspection Testing",
                normative_references=["API 598", "ASME B16.34"],
            ),
            StandardClause(
                standard="ASME B16.10",
                clause="",
                title="Face-to-Face Dimensions",
                rule_type="mandatory",
                applies_to=["All Valves"],
                datasheet_field="Face to Face Dimension",
                normative_references=["ASME B16.10"],
            ),
        ]

        self._clauses.extend(defaults)
        self._build_indexes()
