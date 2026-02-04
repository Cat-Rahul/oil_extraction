# VDS-Driven Valve Datasheet Automation System

## Technical Documentation

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture & Project Structure](#2-architecture--project-structure)
3. [Data Flow](#3-data-flow)
4. [VDS Number Decoding](#4-vds-number-decoding)
5. [Data Extraction from Excel (PMS)](#5-data-extraction-from-excel-pms)
6. [Data Extraction from PDF (Standards)](#6-data-extraction-from-pdf-standards)
7. [Data Mapping Process](#7-data-mapping-process)
8. [Field Resolution Logic](#8-field-resolution-logic)
9. [Output Generation](#9-output-generation)
10. [Configuration Files](#10-configuration-files)
11. [Example Walkthrough](#11-example-walkthrough)

---

## 1. System Overview

### Purpose

This system automatically generates complete **Valve Datasheets** from a single user input: a **VDS (Valve Data Sheet) Number**. The system is:

- **Rule-driven**: All logic is configurable via YAML files
- **Deterministic**: Same input always produces same output
- **Traceable**: Every field value includes its source reference
- **Extensible**: New valve types, classes, and standards can be added without code changes

### Key Capabilities

| Capability | Description |
|------------|-------------|
| VDS Decoding | Parse VDS numbers into structured components |
| PMS Lookup | Fetch piping class specifications from Excel data |
| Standards Reference | Apply valve standards (API 6D, ASME B16.34, etc.) |
| Material Selection | Determine materials based on base material + modifiers |
| Calculated Fields | Compute hydrotest pressures and other derived values |
| Traceability | Full audit trail for every field value |

---

## 2. Architecture & Project Structure

```
valve_backend/
├── valve_datasheet_automation/          # Main application package
│   ├── main.py                          # CLI entry point
│   ├── demo.py                          # Demo/example script
│   │
│   ├── core/                            # Core orchestration engines
│   │   ├── vds_decoder.py              # VDS number parsing
│   │   ├── datasheet_engine.py         # Main generation orchestrator
│   │   └── field_resolver.py           # Individual field value resolution
│   │
│   ├── models/                          # Data models (Pydantic)
│   │   ├── vds.py                      # VDS-related models & enums
│   │   ├── datasheet.py                # Output datasheet models
│   │   └── pms.py                      # PMS data models
│   │
│   ├── repositories/                    # Data access layers
│   │   ├── pms_repository.py           # PMS Excel data access
│   │   ├── standards_repository.py     # Valve standards access
│   │   └── vds_index_repository.py     # VDS index lookup
│   │
│   ├── output/                          # Output formatting
│   │   ├── json_exporter.py            # JSON export functionality
│   │   └── traceability_report.py      # Traceability reporting
│   │
│   ├── validators/                      # Validation logic
│   │   ├── conflict_detector.py        # Data conflict detection
│   │   └── datasheet_validator.py      # Datasheet validation
│   │
│   └── config/                          # Configuration files
│       ├── vds_rules.yaml              # VDS decoding patterns
│       ├── field_mappings.yaml         # Field-to-source mappings
│       └── material_mappings.yaml      # Material specifications
│
├── unstructured/                        # Extracted data files
│   ├── Pipping specification_extracted.json    # PMS data (from Excel)
│   ├── BALL-With Metalic Valve-*.json          # VDS Index (from Excel)
│   └── output_no_footer_clauses.json           # Standards clauses (from PDF)
│
├── verify_datasheet.py                  # Verification script
└── FIELD_SOURCE_MAP.md                  # Complete field mapping documentation
```

### Component Responsibilities

| Component | Responsibility |
|-----------|----------------|
| **DatasheetEngine** | Orchestrates the entire generation process |
| **VDSDecoder** | Parses VDS strings into structured components |
| **FieldResolver** | Resolves individual field values from multiple sources |
| **PMSRepository** | Provides access to piping class specifications |
| **StandardsRepository** | Provides access to valve standard clauses |
| **VDSIndexRepository** | Provides direct VDS-to-specification lookups |
| **JSONExporter** | Exports datasheets to JSON format |

---

## 3. Data Flow

### High-Level Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           USER INPUT: VDS No. (e.g., "BSFA1R")              │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              VDS DECODER                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Input: "BSFA1R"                                                      │    │
│  │ Output: DecodedVDS {                                                 │    │
│  │   valve_type_prefix: BALL ("BS")                                     │    │
│  │   bore_type: FULL ("F")                                              │    │
│  │   piping_class: "A1"                                                 │    │
│  │   end_connection: RF ("R")                                           │    │
│  │   is_nace_compliant: false                                           │    │
│  │   is_low_temp: false                                                 │    │
│  │   is_metal_seated: false                                             │    │
│  │ }                                                                    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FIELD RESOLVER                                     │
│                                                                              │
│   For each of 40 datasheet fields, determine source and resolve value:      │
│                                                                              │
│   ┌──────────────────┬──────────────────────────────────────────────────┐   │
│   │ Source Type      │ Action                                           │   │
│   ├──────────────────┼──────────────────────────────────────────────────┤   │
│   │ VDS              │ Extract from DecodedVDS                          │   │
│   │ PMS              │ Lookup in PMSRepository by piping_class          │   │
│   │ VALVE_STANDARD   │ Lookup in StandardsRepository                    │   │
│   │ PMS_AND_STANDARD │ Combine PMS base material + material mappings    │   │
│   │ VDS_INDEX        │ Lookup in VDSIndexRepository by VDS no           │   │
│   │ CALCULATED       │ Apply formula (e.g., 1.5 × design_pressure)      │   │
│   │ FIXED            │ Use configured constant value                    │   │
│   └──────────────────┴──────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
          ┌─────────────────────────────┼─────────────────────────────┐
          │                             │                             │
          ▼                             ▼                             ▼
┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐
│   PMS REPOSITORY    │   │ STANDARDS REPOSITORY│   │ VDS INDEX REPOSITORY│
│                     │   │                     │   │                     │
│ Source:             │   │ Source:             │   │ Source:             │
│ Pipping             │   │ output_no_footer_   │   │ BALL-With Metalic   │
│ specification_      │   │ clauses.json        │   │ Valve-*.json        │
│ extracted.json      │   │                     │   │                     │
│                     │   │ Provides:           │   │ Provides:           │
│ Provides:           │   │ - Standard clauses  │   │ - Pre-computed      │
│ - Pressure ratings  │   │ - Testing rules     │   │   material specs    │
│ - Base materials    │   │ - Fixed values      │   │ - Size ranges       │
│ - Corrosion allow.  │   │ - Clause references │   │ - Direct lookups    │
│ - Design pressures  │   │                     │   │                     │
│ - Service types     │   │                     │   │                     │
└─────────────────────┘   └─────────────────────┘   └─────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATASHEET BUILDER                                  │
│                                                                              │
│   Combine all resolved fields into ValveDatasheet:                          │
│   - 40 DatasheetField objects                                               │
│   - Each with value + traceability information                              │
│   - Metadata (generated_at, version, completion %)                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              VALIDATION                                      │
│   - Check required fields are populated                                      │
│   - Detect conflicts between sources                                         │
│   - Calculate completion percentage                                          │
│   - Set validation_status                                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           JSON EXPORTER                                      │
│   - Full JSON (with traceability)                                           │
│   - Flat JSON (values only)                                                 │
│   - Batch export capability                                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           OUTPUT: Valve Datasheet (JSON)                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. VDS Number Decoding

### VDS Format Structure

A VDS number is a compressed code where each segment represents a valve attribute:

```
{Prefix}{BoreType}[MetalSeated]{PipingClass}[Modifiers]{EndConnection}
```

### Segment Definitions

| Segment | Position | Values | Description |
|---------|----------|--------|-------------|
| **Prefix** | 1-2 | BS, GS, CS, PS | Valve type (Ball, Gate, Check, Plug) |
| **Bore Type** | 3 | F, R, M | Full, Reduced, Metal-seated |
| **Piping Class** | 4+ | A1, B1, D1, G1, etc. | Pressure class + sequence |
| **Modifiers** | Variable | N, L | NACE compliant, Low Temperature |
| **End Connection** | Last | R, J, F, W, S | RF, RTJ, FF, BW, SW |

### Valve Type Prefixes

| Code | Valve Type | Governing Standard |
|------|------------|-------------------|
| BS | Ball Valve | API 6D / ISO 17292 |
| GS | Gate Valve | API 6D / API 600 |
| CS | Check Valve | API 6D / API 594 |
| PS | Plug Valve | API 6D / API 599 |

### Bore Types

| Code | Type | Description |
|------|------|-------------|
| F | Full Bore | Full opening diameter |
| R | Reduced Bore | Reduced opening diameter |
| M | Metal-Seated | Metal-to-metal seating (typically full bore) |

### Piping Class Codes

| Letter | Pressure Rating |
|--------|-----------------|
| A | 150# |
| B | 300# |
| C | 400# |
| D | 600# |
| E | 900# |
| F | 1500# |
| G | 2500# |

### Modifiers

| Code | Modifier | Effect |
|------|----------|--------|
| N | NACE Compliant | Triggers NACE-specific material selection |
| L | Low Temperature | Triggers low-temp material selection |

### End Connections

| Code | Type | Standard |
|------|------|----------|
| R | Raised Face (RF) | ASME B16.5 |
| J | Ring Type Joint (RTJ) | ASME B16.5 |
| F | Flat Face (FF) | ASME B16.5 |
| W | Butt Weld (BW) | ASME B16.25 |
| S | Socket Weld (SW) | ASME B16.11 |

### Decoding Examples

| VDS No. | Breakdown | Result |
|---------|-----------|--------|
| `BSFA1R` | BS + F + A1 + R | Ball, Full Bore, Class A1 (150#), RF |
| `BSFB1NR` | BS + F + B1 + N + R | Ball, Full Bore, Class B1 (300#), NACE, RF |
| `BSFMG1LNJ` | BS + F + M + G1 + L + N + J | Ball, Full Bore, Metal-seated, Class G1 (2500#), Low-temp, NACE, RTJ |
| `GSRD1W` | GS + R + D1 + W | Gate, Reduced Bore, Class D1 (600#), BW |

### Decoder Output Model

```python
class DecodedVDS:
    raw_vds: str              # Original input (e.g., "BSFA1R")
    valve_type_prefix: Enum   # BALL, GATE, CHECK, PLUG
    bore_type: Enum           # FULL, REDUCED, METAL_SEATED
    piping_class: str         # e.g., "A1", "B1N"
    is_nace_compliant: bool   # True if "N" modifier present
    is_low_temp: bool         # True if "L" modifier present
    is_metal_seated: bool     # True if bore_type is "M"
    end_connection: Enum      # RF, RTJ, FF, BW, SW
```

---

## 5. Data Extraction from Excel (PMS)

### Source File

**Original**: Excel PMS (Piping Material Specification) file
**Extracted to**: `unstructured/Pipping specification_extracted.json`

### Extraction Process

```
┌───────────────────┐       ┌───────────────────┐       ┌───────────────────┐
│                   │       │                   │       │                   │
│   Excel PMS File  │──────►│  JSON Extraction  │──────►│  JSON Data File   │
│                   │       │     Process       │       │                   │
│ - Multiple sheets │       │                   │       │ - Tables array    │
│ - Tables with     │       │ - Preserve        │       │ - Headers         │
│   headers & rows  │       │   structure       │       │ - Row data        │
│                   │       │ - Extract all     │       │                   │
│                   │       │   cells          │       │                   │
└───────────────────┘       └───────────────────┘       └───────────────────┘
```

### JSON Structure

```json
{
  "sheets": [
    {
      "sheet_name": "PMS",
      "tables": [
        {
          "headers": [
            "Piping Class",
            "Rating",
            "Material",
            "Material Group",
            "Corrosion Allowance",
            "Service",
            "Design Pressure",
            "Design Temperature"
          ],
          "rows": [
            {
              "Piping Class": "A1",
              "Rating": "150#",
              "Material": "CS",
              "Material Group": "1.1",
              "Corrosion Allowance": "3 mm",
              "Service": "Cooling Water, Steam, Diesel",
              "Design Pressure": "19.6 barg @ 38°C",
              "Design Temperature": "-29°C to 200°C"
            }
          ]
        }
      ]
    }
  ]
}
```

### PMS Repository Processing

```python
# pms_repository.py - Key operations

1. Load JSON file
2. Find tables containing "Piping Class" header
3. For each row:
   a. Extract piping_class (e.g., "A1")
   b. Parse pressure_rating (e.g., "150#" → 150)
   c. Extract base_material (e.g., "CS")
   d. Extract corrosion_allowance
   e. Parse design_pressure (numeric + units)
   f. Parse design_temperature (min/max)
   g. Determine is_nace_class (contains "N")
   h. Determine is_low_temp_class (contains "L")
4. Build lookup index: piping_class → PMSClass object
```

### Data Provided by PMS Repository

| Field | Example | Used For |
|-------|---------|----------|
| `pressure_rating` | "150#" | Derive pressure_class |
| `base_material` | "CS" | Material selection key |
| `material_group` | "1.1" | Material classification |
| `corrosion_allowance` | "3 mm" | Direct output field |
| `service` | "Cooling Water, Steam" | Direct output field |
| `design_pressure_max` | "19.6 barg" | Output + calculations |
| `design_temp_min/max` | "-29°C / 200°C" | Output fields |
| `is_nace_class` | true/false | Material selection |
| `is_low_temp_class` | true/false | Material selection |

---

## 6. Data Extraction from PDF (Standards)

### Source Files

**Original**: Valve standard PDFs (API 6D, ASME B16.34, API 598, etc.)
**Extracted to**: `unstructured/output_no_footer_clauses.json`

### Extraction Process

```
┌───────────────────┐       ┌───────────────────┐       ┌───────────────────┐
│                   │       │                   │       │                   │
│   PDF Standards   │──────►│  Clause Extraction│──────►│  JSON Clauses     │
│                   │       │     Process       │       │     File          │
│ - API 6D          │       │                   │       │                   │
│ - ASME B16.34     │       │ - Parse sections  │       │ - Structured      │
│ - API 598         │       │ - Extract clauses │       │   clauses         │
│ - MSS-SP-25       │       │ - Tag rule types  │       │ - Field mappings  │
│                   │       │ - Map to fields   │       │ - References      │
└───────────────────┘       └───────────────────┘       └───────────────────┘
```

### JSON Structure

```json
{
  "clauses": [
    {
      "standard": "API 6D",
      "section": "5",
      "clause": "5.2.1",
      "title": "Hydrostatic Shell Test",
      "text": "The shell test pressure shall be at least 1.5 times...",
      "page": 42,
      "rule_type": "mandatory",
      "applies_to": ["Ball Valve", "Gate Valve", "Check Valve"],
      "datasheet_field": "hydrotest_shell"
    },
    {
      "standard": "API 598",
      "section": "4",
      "clause": "4.1",
      "title": "Leakage Rate",
      "text": "Zero leakage for soft-seated valves...",
      "page": 15,
      "rule_type": "mandatory",
      "applies_to": ["Ball Valve"],
      "datasheet_field": "leakage_rate"
    }
  ]
}
```

### Standards Repository Processing

```python
# standards_repository.py - Key operations

1. Load JSON clauses file
2. Build multiple indexes:
   a. By datasheet_field → list[StandardClause]
   b. By valve_type → list[StandardClause]
   c. By standard_name → list[StandardClause]
3. Provide lookup methods:
   - get_clauses_for_field(field_name)
   - get_clauses_for_valve_type(valve_type)
   - get_standard_value(field_name, valve_type)
```

### Rule Types

| Type | Description | Example |
|------|-------------|---------|
| `mandatory` | Must be followed | Shell test pressure requirements |
| `recommendation` | Should be followed | Preferred marking locations |
| `informational` | Reference information | Material compatibility notes |
| `formula` | Calculation rule | 1.5 × design pressure |
| `definition` | Term definition | "Bore" definition |

### Data Provided by Standards Repository

| Field | Standard | Value |
|-------|----------|-------|
| `valve_standard` | Config-based | "API 6D / ISO 17292" |
| `face_to_face` | ASME B16.10 | "Long pattern, quarter turn" |
| `operation` | API 6D | "Lever / Gear operated" |
| `inspection_testing` | Multiple | "ASME B16.34, API 598" |
| `leakage_rate` | API 598 | "As per API 598" |
| `marking_manufacturer` | MSS-SP-25 | "MSS-SP-25" |
| `fire_rating` | API 607 | "API 607 / ISO 10497" |

---

## 7. Data Mapping Process

### Field Source Types

Each of the 40 datasheet fields has a defined source type:

| Source Type | Count | Description |
|-------------|-------|-------------|
| VDS | 5 | Derived from decoded VDS number |
| PMS | 5 | Fetched from PMS repository |
| VALVE_STANDARD | 8 | From standards or fixed config |
| PMS_AND_STANDARD | 10 | Combined PMS material + mappings |
| VDS_INDEX | 3 | Direct lookup from VDS index |
| CALCULATED | 2 | Computed from other values |
| FIXED | 7 | Constant configuration values |

### Complete Field Mapping Table

#### Header Section (5 fields)

| Field | Source | Resolution |
|-------|--------|------------|
| vds_no | VDS | Direct from input |
| piping_class | VDS | Extracted from VDS |
| size_range | PMS/VDS_INDEX | From PMS class or index |
| valve_type | VDS | Prefix + bore type combined |
| service | PMS | From piping class lookup |

#### Design Section (5 fields)

| Field | Source | Resolution |
|-------|--------|------------|
| valve_standard | VALVE_STANDARD | Based on valve type |
| pressure_class | PMS | "ASME B16.34 Class " + rating |
| design_pressure | PMS | From piping class data |
| corrosion_allowance | PMS | From piping class data |
| sour_service | VDS | "NACE MR0175 / ISO 15156" if NACE, else "-" |

#### Configuration Section (3 fields)

| Field | Source | Resolution |
|-------|--------|------------|
| end_connections | VDS | Based on end connection code |
| face_to_face | VALVE_STANDARD | Fixed: "ASME B16.10 Long pattern" |
| operation | VALVE_STANDARD | Fixed: "Lever / Gear operated" |

#### Construction Section (5 fields)

| Field | Source | Resolution |
|-------|--------|------------|
| body_construction | VALVE_STANDARD | Rule-based by valve type |
| ball_construction | VALVE_STANDARD | Rule-based by pressure class |
| stem_construction | VALVE_STANDARD | Fixed: "Anti-static, Anti blowout" |
| seat_construction | VALVE_STANDARD | Based on metal-seated flag |
| locks | VALVE_STANDARD | Fixed: "Integral" |

#### Material Section (12 fields)

| Field | Source | Resolution |
|-------|--------|------------|
| body_material | VDS_INDEX | Direct lookup |
| ball_material | VDS_INDEX | Direct lookup |
| seat_material | VDS_INDEX | Direct lookup |
| seal_material | PMS_AND_STANDARD | Material mapping |
| stem_material | PMS_AND_STANDARD | Material mapping |
| gland_material | PMS_AND_STANDARD | Material mapping |
| gland_packing | PMS_AND_STANDARD | Material mapping |
| lever_handwheel | PMS_AND_STANDARD | Material mapping |
| spring_material | PMS_AND_STANDARD | Material mapping |
| gaskets | PMS_AND_STANDARD | By material + end connection |
| bolts | PMS_AND_STANDARD | By material + NACE flag |
| nuts | PMS_AND_STANDARD | By material + NACE flag |

#### Testing Section (10 fields)

| Field | Source | Resolution |
|-------|--------|------------|
| marking_purchaser | FIXED | Config value |
| marking_manufacturer | FIXED | "MSS-SP-25" |
| inspection_testing | FIXED | "ASME B16.34, API 598" |
| leakage_rate | FIXED | "As per API 598" |
| hydrotest_shell | CALCULATED | 1.5 × design_pressure |
| hydrotest_closure | CALCULATED | 1.1 × design_pressure |
| pneumatic_test | FIXED | "5.5 barg" |
| material_certification | FIXED | Config value |
| fire_rating | FIXED | "API 607 / ISO 10497" |
| finish | FIXED | Config value |

---

## 8. Field Resolution Logic

### Material Selection Algorithm

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MATERIAL SELECTION FLOW                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Step 1: Get Base Material from PMS                                          │
│         Example: piping_class "A1" → base_material "CS" (Carbon Steel)      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Step 2: Determine Material Key based on Modifiers                           │
│                                                                              │
│   ┌──────────────────┬──────────────────┬─────────────────────────────────┐ │
│   │ NACE Compliant?  │ Low Temperature? │ Material Key                    │ │
│   ├──────────────────┼──────────────────┼─────────────────────────────────┤ │
│   │ No               │ No               │ CS (base)                       │ │
│   │ Yes              │ No               │ CS_NACE                         │ │
│   │ No               │ Yes              │ LTCS                            │ │
│   │ Yes              │ Yes              │ LTCS_NACE                       │ │
│   └──────────────────┴──────────────────┴─────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Step 3: Look up Material Configuration                                       │
│                                                                              │
│   From material_mappings.yaml:                                               │
│   CS:                                                                        │
│     body: "ASTM A216 Gr. WCB" / "ASTM A105N"                                │
│     stem: "ASTM A182 F316"                                                  │
│     bolts: "ASTM A193 Gr. B7"                                               │
│     nuts: "ASTM A194 Gr. 2H"                                                │
│                                                                              │
│   CS_NACE (inherits from CS, overrides):                                    │
│     bolts: "ASTM A193 Gr. B7M"                                              │
│     nuts: "ASTM A194 Gr. 2HM"                                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Step 4: Apply Component-Specific Rules                                       │
│                                                                              │
│   For gaskets (depends on end connection):                                   │
│   - RF → "SS316/SS316L Spiral Wound with F.G. filler"                       │
│   - RTJ → "SS316L Ring Joint"                                               │
│                                                                              │
│   For body (depends on size):                                               │
│   - ≤1.5" → Forged specification                                            │
│   - >1.5" → Cast specification                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Output: Component Material Specification                                     │
│         Example: bolts = "ASTM A193 Gr. B7M" (for NACE)                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Construction Rules

#### Body Construction

```
Valve Type = Ball Valve:
  Size ≤ 1.5"  → "Forged, Two Piece"
  Size > 1.5"  → "Cast, Two/Three Piece"

Full Rule: 'Forged, Two Piece (≤1.5"), Cast, Two/Three Piece (>1.5")'
```

#### Ball Construction

```
Pressure Class ≤ 150:
  "Floating (8" and below), Trunnion mounted (10" and above)"

Pressure Class ≥ 300:
  "Floating (4" and below), Trunnion mounted (6" and above)"
```

#### Seat Construction

```
is_metal_seated = true:
  "Metal seated, hard faced, Renewable"

is_metal_seated = false:
  "Soft seated, Renewable"
```

### Calculated Fields

#### Hydrotest Pressures

Based on API 598 requirements:

```python
design_pressure = extract_from_pms(piping_class)  # e.g., 19.6 barg

hydrotest_shell = design_pressure × 1.5
# Example: 19.6 × 1.5 = 29.4 barg

hydrotest_closure = design_pressure × 1.1
# Example: 19.6 × 1.1 = 21.6 barg
```

---

## 9. Output Generation

### Output Model Structure

```python
class ValveDatasheet:
    metadata: DatasheetMetadata
    fields: dict[str, DatasheetField]
    validation_status: str
    validation_errors: list[str]

class DatasheetMetadata:
    generated_at: datetime
    generation_version: str
    vds_no: str
    completion_percentage: float

class DatasheetField:
    field_name: str
    display_name: str
    section: str
    value: str
    traceability: FieldTraceability
    is_required: bool

class FieldTraceability:
    source_type: FieldSource
    source_document: str
    source_value: str
    derivation_rule: str
    clause_reference: str
    confidence: float
    notes: str
```

### Full JSON Output Format

```json
{
  "metadata": {
    "generated_at": "2025-01-31T15:30:00",
    "generation_version": "1.0.0",
    "vds_no": "BSFA1R",
    "completion_percentage": 97.5,
    "validation_status": "valid"
  },
  "sections": {
    "Header": {
      "vds_no": {
        "display_name": "VDS No.",
        "value": "BSFA1R",
        "traceability": {
          "source_type": "Selected based on VDS No",
          "source_document": "VDS No: BSFA1R",
          "confidence": 1.0
        }
      },
      "piping_class": {
        "display_name": "Piping Class",
        "value": "A1",
        "traceability": {
          "source_type": "Selected based on VDS No",
          "source_document": "VDS No: BSFA1R",
          "derivation_rule": "Extracted from VDS position 3-4"
        }
      }
    },
    "Material": {
      "bolts": {
        "display_name": "Bolts",
        "value": "ASTM A193 Gr. B7",
        "traceability": {
          "source_type": "As per PMS Base material and Valve Standard",
          "source_document": "PMS Class A1, Material Mappings",
          "source_value": "CS → bolts",
          "derivation_rule": "Material lookup: base=CS, nace=false",
          "confidence": 1.0
        }
      }
    },
    "Testing": {
      "hydrotest_shell": {
        "display_name": "Hydrotest Shell",
        "value": "29.4 barg",
        "traceability": {
          "source_type": "Calculated",
          "source_document": "API 598",
          "source_value": "19.6 barg",
          "derivation_rule": "1.5 × Max Design Pressure",
          "clause_reference": "API 598 Section 5.2"
        }
      }
    }
  }
}
```

### Flat JSON Output Format

```json
{
  "vds_no": "BSFA1R",
  "piping_class": "A1",
  "size_range": "1/2\" - 24\"",
  "valve_type": "Ball Valve, Full Bore",
  "service": "Cooling Water, Steam, Diesel",
  "valve_standard": "API 6D / ISO 17292",
  "pressure_class": "ASME B16.34 Class 150",
  "design_pressure": "19.6 barg @ 38°C",
  "corrosion_allowance": "3 mm",
  "sour_service": "-",
  "end_connections": "Flanged ASME B16.5 RF",
  "body_material": "Forged - ASTM A105N",
  "ball_material": "Forged - ASTM A182-F316",
  "seat_material": "Reinforced PTFE",
  "bolts": "ASTM A193 Gr. B7",
  "nuts": "ASTM A194 Gr. 2H",
  "hydrotest_shell": "29.4 barg",
  "hydrotest_closure": "21.6 barg"
}
```

---

## 10. Configuration Files

### vds_rules.yaml

Defines VDS parsing patterns:

```yaml
valve_type_prefixes:
  BS:
    name: "Ball Valve"
    standard: "API 6D / ISO 17292"
  GS:
    name: "Gate Valve"
    standard: "API 6D / API 600"

bore_types:
  F: "Full Bore"
  R: "Reduced Bore"
  M: "Metal Seated"

modifiers:
  N: "NACE Compliant"
  L: "Low Temperature"

end_connections:
  R:
    type: "RF"
    standard: "ASME B16.5"
  J:
    type: "RTJ"
    standard: "ASME B16.5"

piping_class_pattern: "[A-G][0-9]+"

parsing_sequence:
  - segment: "prefix"
    position: "1-2"
    required: true
  - segment: "bore_type"
    position: "3"
    required: true
  - segment: "piping_class"
    position: "4+"
    required: true
  - segment: "end_connection"
    position: "last"
    required: true
```

### field_mappings.yaml

Defines all 40 fields and their sources:

```yaml
sections:
  Header:
    vds_no:
      display_name: "VDS No."
      source_type: VDS
      required: true

    piping_class:
      display_name: "Piping Class"
      source_type: VDS
      required: true

  Design:
    pressure_class:
      display_name: "Pressure Class"
      source_type: PMS
      derivation: "ASME B16.34 Class {rating}"
      required: true

    sour_service:
      display_name: "Sour Service"
      source_type: VDS
      rules:
        - condition: "is_nace_compliant == true"
          value: "NACE MR0175 / ISO 15156"
        - condition: "default"
          value: "-"

  Material:
    bolts:
      display_name: "Bolts"
      source_type: PMS_AND_STANDARD
      material_component: "bolts"
      required: true

  Testing:
    hydrotest_shell:
      display_name: "Hydrotest Shell"
      source_type: CALCULATED
      formula: "design_pressure * 1.5"
      units: "barg"
      reference: "API 598"
```

### material_mappings.yaml

Defines material specifications:

```yaml
base_materials:
  CS:
    description: "Carbon Steel"
    body:
      forged: "ASTM A105N"
      cast: "ASTM A216 Gr. WCB"
      size_threshold: 1.5
    stem: "ASTM A182 F316"
    gland: "ASTM A182 F6A CL 2"
    gland_packing: "Graphite / PTFE"
    spring: "Inconel 750"
    bolts: "ASTM A193 Gr. B7"
    nuts: "ASTM A194 Gr. 2H"
    gaskets:
      RF: "SS316/SS316L Spiral Wound with F.G. filler"
      RTJ: "SS316L Ring Joint"

  CS_NACE:
    inherits: CS
    description: "Carbon Steel - NACE Compliant"
    overrides:
      bolts: "ASTM A193 Gr. B7M"
      nuts: "ASTM A194 Gr. 2HM"

  LTCS:
    description: "Low Temperature Carbon Steel"
    body:
      forged: "ASTM A350 LF2"
      cast: "ASTM A352 LCB"
    # ... other components

  SS316L:
    description: "Stainless Steel 316L"
    body:
      forged: "ASTM A182 F316L"
      cast: "ASTM A351 CF3M"
    # ... other components
```

---

## 11. Example Walkthrough

### Input: VDS No. = "BSFB1NR"

### Step 1: VDS Decoding

```
Input:  "BSFB1NR"

Parsing:
  Position 1-2: "BS" → Ball Valve
  Position 3:   "F"  → Full Bore
  Position 4-5: "B1" → Piping Class B1 (300#)
  Position 6:   "N"  → NACE Compliant
  Position 7:   "R"  → RF End Connection

Output DecodedVDS:
  valve_type_prefix: BALL
  bore_type: FULL
  piping_class: "B1"
  is_nace_compliant: true
  is_low_temp: false
  is_metal_seated: false
  end_connection: RF
```

### Step 2: PMS Lookup

```
Query: PMSRepository.get_class("B1")

Result PMSClass:
  piping_class: "B1"
  pressure_rating: "300#"
  base_material: "CS"
  corrosion_allowance: "3 mm"
  service: "Process fluids"
  design_pressure_max: "50 barg @ 38°C"
  design_temp_min: "-29°C"
  design_temp_max: "200°C"
```

### Step 3: Field Resolution

| Field | Source | Resolution | Value |
|-------|--------|------------|-------|
| vds_no | VDS | Direct | "BSFB1NR" |
| piping_class | VDS | Decoded | "B1" |
| valve_type | VDS | Prefix + bore | "Ball Valve, Full Bore" |
| service | PMS | Lookup | "Process fluids" |
| valve_standard | Config | Ball Valve | "API 6D / ISO 17292" |
| pressure_class | PMS | "300#" → | "ASME B16.34 Class 300" |
| design_pressure | PMS | Lookup | "50 barg @ 38°C" |
| sour_service | VDS | is_nace=true | "NACE MR0175 / ISO 15156" |
| end_connections | VDS | RF | "Flanged ASME B16.5 RF" |
| bolts | Material | CS + NACE | "ASTM A193 Gr. B7M" |
| nuts | Material | CS + NACE | "ASTM A194 Gr. 2HM" |
| hydrotest_shell | Calculated | 50 × 1.5 | "75 barg" |
| hydrotest_closure | Calculated | 50 × 1.1 | "55 barg" |

### Step 4: Output

```json
{
  "metadata": {
    "vds_no": "BSFB1NR",
    "completion_percentage": 100.0,
    "validation_status": "valid"
  },
  "sections": {
    "Header": {
      "vds_no": {"value": "BSFB1NR"},
      "piping_class": {"value": "B1"},
      "valve_type": {"value": "Ball Valve, Full Bore"}
    },
    "Design": {
      "pressure_class": {"value": "ASME B16.34 Class 300"},
      "design_pressure": {"value": "50 barg @ 38°C"},
      "sour_service": {"value": "NACE MR0175 / ISO 15156"}
    },
    "Material": {
      "bolts": {"value": "ASTM A193 Gr. B7M"},
      "nuts": {"value": "ASTM A194 Gr. 2HM"}
    },
    "Testing": {
      "hydrotest_shell": {"value": "75 barg"},
      "hydrotest_closure": {"value": "55 barg"}
    }
  }
}
```

---

## Summary

This system provides:

1. **Single-input automation**: VDS No. → Complete Datasheet
2. **Multi-source integration**: Excel PMS + PDF Standards + VDS Index
3. **Rule-based logic**: All business rules in YAML configuration
4. **Full traceability**: Every field value includes its source
5. **Extensibility**: Add new valve types, classes, or standards without code changes
6. **Validation**: Automatic completeness and consistency checking
7. **Multiple output formats**: Full JSON with traceability or flat values only

The architecture ensures **deterministic, reproducible, and auditable** valve datasheet generation.
