# Field Source Mapping for Valve Datasheet

This document shows exactly where each field value comes from.

## Source Files

| Source Type | File Location | Description |
|-------------|---------------|-------------|
| **VDS_INDEX** | `unstructured/BALL-With Metalic Valve-*.json` | Pre-computed values from Excel |
| **PMS** | `unstructured/Pipping specification_extracted.json` | Piping Material Specification |
| **MATERIAL_MAPS** | `config/material_mappings.yaml` | Material specifications by base material |
| **FIELD_CONFIG** | `config/field_mappings.yaml` | Field definitions and rules |
| **VDS_RULES** | `config/vds_rules.yaml` | VDS decoding patterns |

---

## Complete Field Mapping (40 Fields)

### HEADER SECTION (5 fields)

| # | Field | Source | Source File | How Value is Determined |
|---|-------|--------|-------------|------------------------|
| 1 | `vds_no` | VDS | User Input | Direct from user input |
| 2 | `piping_class` | VDS | Decoded from VDS | Extract "A1" from "BSF**A1**R" |
| 3 | `size_range` | VDS_INDEX | BALL-*.json | Lookup by VDS No → "Size Range" column |
| 4 | `valve_type` | VDS | Decoded from VDS | "BS"="Ball", "F"="Full Bore" → "Ball Valve, Full Bore" |
| 5 | `service` | PMS | Pipping specification.json | Lookup by Piping Class → Service column |

### DESIGN SECTION (5 fields)

| # | Field | Source | Source File | How Value is Determined |
|---|-------|--------|-------------|------------------------|
| 6 | `valve_standard` | FIELD_CONFIG | field_mappings.yaml | defaults.Ball Valve = "API 6D / ISO 17292" |
| 7 | `pressure_class` | PMS + Derived | Derived from class prefix | A=150, B=300, D=600, E=900, F=1500, G=2500 |
| 8 | `design_pressure` | PMS | Pipping specification.json | design_pressure_max from PMS class |
| 9 | `corrosion_allowance` | PMS | Pipping specification.json | "C.A" column = "3 mm" |
| 10 | `sour_service` | VDS | Decoded from VDS | If "N" in VDS → "NACE MR0175", else "-" |

### CONFIGURATION SECTION (3 fields)

| # | Field | Source | Source File | How Value is Determined |
|---|-------|--------|-------------|------------------------|
| 11 | `end_connections` | VDS | Decoded from VDS | "R"="RF" → "Flanged ASME B16.5 RF" |
| 12 | `face_to_face` | FIELD_CONFIG | field_mappings.yaml | Fixed value from config |
| 13 | `operation` | FIELD_CONFIG | field_mappings.yaml | Fixed value from config |

### CONSTRUCTION SECTION (5 fields)

| # | Field | Source | Source File | How Value is Determined |
|---|-------|--------|-------------|------------------------|
| 14 | `body_construction` | DERIVED | field_resolver.py | Based on valve type → Forged/Cast rule |
| 15 | `ball_construction` | DERIVED | field_resolver.py | Based on pressure class: ≤150 or ≥300 rule |
| 16 | `stem_construction` | FIELD_CONFIG | field_mappings.yaml | Fixed: "Anti-static, Anti blowout proof" |
| 17 | `seat_construction` | DERIVED | field_resolver.py | Based on is_metal_seated flag from VDS |
| 18 | `locks` | FIELD_CONFIG | field_mappings.yaml | Fixed value from config |

### MATERIAL SECTION (12 fields)

| # | Field | Source | Source File | How Value is Determined |
|---|-------|--------|-------------|------------------------|
| 19 | `body_material` | MATERIAL_MAPS | material_mappings.yaml | CS.components.body.forged/cast |
| 20 | `ball_material` | VDS_INDEX | BALL-*.json | Lookup by VDS No → "Ball Material" column |
| 21 | `seat_material` | VDS_INDEX | BALL-*.json | Lookup by VDS No → "Seat Material" column |
| 22 | `seal_material` | MATERIAL_MAPS | material_mappings.yaml | Default: "PTFE" |
| 23 | `stem_material` | MATERIAL_MAPS | material_mappings.yaml | CS.components.stem |
| 24 | `gland_material` | MATERIAL_MAPS | material_mappings.yaml | CS.components.gland |
| 25 | `gland_packing` | MATERIAL_MAPS | material_mappings.yaml | CS.components.gland_packing |
| 26 | `lever_handwheel` | MATERIAL_MAPS | material_mappings.yaml | Default: "Carbon Steel, Painted" |
| 27 | `spring_material` | MATERIAL_MAPS | material_mappings.yaml | CS.components.spring |
| 28 | `gaskets` | MATERIAL_MAPS | material_mappings.yaml | CS.components.gaskets.RF or .RTJ |
| 29 | `bolts` | MATERIAL_MAPS | material_mappings.yaml | CS.components.bolts (B7 or B7M for NACE) |
| 30 | `nuts` | MATERIAL_MAPS | material_mappings.yaml | CS.components.nuts (2H or 2HM for NACE) |

### TESTING SECTION (10 fields)

| # | Field | Source | Source File | How Value is Determined |
|---|-------|--------|-------------|------------------------|
| 31 | `marking_purchaser` | FIELD_CONFIG | field_mappings.yaml | Fixed value |
| 32 | `marking_manufacturer` | FIELD_CONFIG | field_mappings.yaml | Fixed: "MSS-SP-25" |
| 33 | `inspection_testing` | FIELD_CONFIG | field_mappings.yaml | Fixed: "ASME B16.34, API 598" |
| 34 | `leakage_rate` | FIELD_CONFIG | field_mappings.yaml | Fixed: "As per API 598" |
| 35 | `hydrotest_shell` | CALCULATED | field_resolver.py | **1.5 × Design Pressure** |
| 36 | `hydrotest_closure` | CALCULATED | field_resolver.py | **1.1 × Design Pressure** |
| 37 | `pneumatic_test` | FIELD_CONFIG | field_mappings.yaml | Fixed: "5.5 barg" |
| 38 | `material_certification` | FIELD_CONFIG | field_mappings.yaml | Fixed value |
| 39 | `fire_rating` | FIELD_CONFIG | field_mappings.yaml | "API 607 / ISO 10497" |
| 40 | `finish` | FIELD_CONFIG | field_mappings.yaml | Fixed value |

---

## NACE Compliance Logic

When VDS contains "N" (e.g., BSF**B1N**R):

| Field | Non-NACE Value | NACE Value |
|-------|----------------|------------|
| sour_service | - | NACE MR0175 / ISO 15156 |
| bolts | ASTM A193 Gr. B7 | ASTM A193 Gr. B7**M** |
| nuts | ASTM A194 Gr. 2H | ASTM A194 Gr. 2H**M** |

---

## Pressure Class Derivation

| Piping Class Prefix | Pressure Rating | Design Pressure (barg @ 38°C) |
|---------------------|-----------------|------------------------------|
| A (e.g., A1) | 150# | 19.6 |
| B (e.g., B1) | 300# | 51.1 |
| C | 400# | - |
| D (e.g., D1) | 600# | 102.1 |
| E (e.g., E1) | 900# | 153.2 |
| F | 1500# | 255.3 |
| G (e.g., G1) | 2500# | 425.5 |

---

## Hydrotest Calculation

```
Hydrotest Shell    = Design Pressure × 1.5
Hydrotest Closure  = Design Pressure × 1.1

Example for Class 150 (19.6 barg):
  Shell   = 19.6 × 1.5 = 29.4 barg
  Closure = 19.6 × 1.1 = 21.6 barg
```
