# Claude Project Instructions (claude.md)

## Project Title

**VDS‑Driven Valve Datasheet Automation System**

## Objective

Build a system that automatically generates a complete **Valve Datasheet (Output File)** based on a single user input: **VDS No.**

The system must fetch, derive, and map required data from:

* **PMS Data File (Excel)**
* **Valve Standards (PDF)**
* **Derived logic from VDS No.**

The output must strictly follow the structure and fields defined in the **Output Datasheet Template**, especially the **"Input / Selection"** column logic.

---

## Inputs

### 1. PMS Data File (Excel)

* Contains piping class–wise and material‑wise data
* Used for:

  * Material specifications
  * Pressure / temperature ratings
  * Flange, rating, and standard‑based selections

### 2. Valve Standards (PDF)

* Governing standards such as:

  * API 6D
  * ASME B16.34
  * Face‑to‑face dimensions
  * Testing, inspection, and marking requirements
* Used where the Output Datasheet specifies **"As per valve standard"**

### 3. Output Datasheet Template

* Defines:

  * Required output fields
  * Source of each field via **Input / Selection** column

    * PMS
    * Valve Standard
    * Derived from VDS No.
    * Calculated

### 4. VDS No. (User Input)

Example:

```
BSFA1R
```

The VDS No. is a **compressed code** that drives valve configuration.

---

## VDS No. Decoding Logic

Each character (or group) in the VDS No. represents a valve attribute.

### Example: `BSFA1R`

| Segment | Meaning                  | Description                     |
| ------- | ------------------------ | ------------------------------- |
| BS      | Valve Type               | Ball Valve Datasheet            |
| F       | Bore Type                | Full Bore                       |
| A1      | Piping Class             | As per PMS – Class A1           |
| R       | Variant / End / Operator | Variant logic (to be confirmed) |

> ⚠️ The decoding rules must be **configurable**, not hard‑coded.

---

## Core System Flow

### Step 1: User Input

* User provides **VDS No.**

### Step 2: Decode VDS No.

* Parse VDS string into:

  * Valve type
  * Bore type
  * Piping class
  * Variant / operation logic

### Step 3: Determine Data Source Per Field

For each field in the Output Datasheet:

| Input / Selection Value | Action                                 |
| ----------------------- | -------------------------------------- |
| PMS                     | Fetch from Excel based on piping class |
| Valve Standard          | Fetch from PDF standard                |
| As per VDS              | Use decoded VDS logic                  |
| Calculated              | Compute based on rules                 |

### Step 4: Fetch Data

* Query PMS Excel using:

  * Piping class (e.g., A1)
  * Valve type
* Extract standard values from PDF (rule‑based, not free text)

### Step 5: Populate Output Datasheet

* Fill **all required fields**
* Maintain original wording where specified (e.g., *As per API 6D*)

### Step 6: Validation

* Ensure:

  * No required fields are blank
  * PMS + Standard conflicts are flagged

---

## Mapping Rules (Critical)

1. **The Output Datasheet is the source of truth**
2. The **Input / Selection** column dictates logic
3. No assumptions outside PMS, Standards, or VDS rules
4. If data is unavailable → flag explicitly

---

## Functional Requirements

* Single VDS No. input → full datasheet output
* Deterministic output (same input = same result)
* Modular decoding logic
* Extensible for:

  * New valve types
  * New piping classes
  * New standards

---

## Non‑Functional Requirements

* Traceability: every output field must reference its source
* Explainability: system should explain *why* a value was selected
* Maintainability: VDS decoding rules stored as config

---

## Assumptions

* PMS Excel is structured and consistent
* Valve standards are fixed and approved
* VDS format is standardized across projects

---

## Out of Scope (For Now)

* UI / Frontend
* AI‑based interpretation of vague standards
* Free‑text PDF parsing without rules

---

## Expected Outcome

A reliable, rule‑driven engine where:

> **VDS No. + PMS + Standards → Complete Valve Datasheet**

with zero manual intervention.

---

## Notes for Claude

* Do not invent values
* Always prefer explicit mappings
* Ask for clarification only when decoding rules are undefined
