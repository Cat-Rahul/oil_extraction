import json
import re
import sys
import os

# ============================================================
# INPUT
# ============================================================

if len(sys.argv) < 2:
    print("❌ Usage: python clause_builder.py <extracted_json_file>")
    sys.exit(1)

input_json = sys.argv[1]

RULES_DIR = "rules"
FIELD_RULES = json.load(open(os.path.join(RULES_DIR, "datasheet_fields.json")))
VALVE_RULES = json.load(open(os.path.join(RULES_DIR, "valve_applicability.json")))

extracted = json.load(open(input_json, encoding="utf-8"))

# ============================================================
# REGEX
# ============================================================

SECTION_RE = re.compile(r'^(\d+)\.?[\s]+(.+)$')
CLAUSE_RE  = re.compile(r'^(\d+(?:\.\d+)+)[\s:]+(.+)$')
DEF_SPLIT_RE = re.compile(r'(\d+\.\d+\.\d+)\s+')

NORMATIVE_RE = re.compile(
    r'\b(API\s?[A-Z0-9.\-]+|ASME\s?[A-Z0-9.\-]+|ISO\s?\d+|EN\s?\d+|ASTM\s?[A-Z0-9]+|NACE\s?[A-Z0-9]+|MSS\s?[A-Z0-9\-]+)\b',
    re.IGNORECASE
)

# ============================================================
# HELPERS
# ============================================================

def is_toc_line(text: str) -> bool:
    # Dot leaders
    if re.search(r'\.{3,}\s*\d+$', text):
        return True

    # Clause + title + page number
    if re.match(r'^\d+(\.\d+)*\s+.+\s+\d+$', text):
        return True

    # Section-only TOC lines
    if re.match(r'^(Normative References|Terms, Definitions|Symbols and Units)', text):
        return True

    return False

def recover_section(clause):
    return clause.split('.')[0]


def classify_rule_type(text):
    t = text.lower()
    if "shall" in t:
        return "mandatory"
    if "should" in t:
        return "recommendation"
    if "example" in t:
        return "example"
    if "times" in t or "×" in t:
        return "formula"
    return "informational"


def extract_normative_refs(text):
    return sorted(set(m.upper() for m in NORMATIVE_RE.findall(text)))


def infer_valves(title, text):
    content = f"{title} {text}".lower()
    matches = set()

    for rule in VALVE_RULES:
        for kw in rule["keywords"]:
            # word-boundary safe match (handles plural lists correctly)
            if re.search(rf'\b{re.escape(kw)}\b', content):
                matches.add(rule["valve_type"])

    return sorted(matches) if matches else ["All Valves"]


def infer_datasheet_field(title, text):
    content = f"{title} {text}".lower()

    for rule in FIELD_RULES:
        if any(k in content for k in rule["include"]) and not any(
            x in content for x in rule["exclude"]
        ):
            return rule["field"]

    return "General Requirement"

# ============================================================
# BUILD CLAUSES
# ============================================================

clauses = []
current_clause = None

for page in extracted["pages"]:
    page_no = page["page_number"]

    for block in page["text_blocks"]:
        text = block["text"].strip()

        if not text or is_toc_line(text):
            continue

        # Normative References Section Isolation
        if text.lower().startswith("the following referenced documents"):
            current_clause = {
                "standard": "API 6D",
                "section": "NR",
                "clause": "NR",
                "title": "Normative References",
                "text": "",
                "page": page_no
            }
            clauses.append(current_clause)
            continue

        cl = CLAUSE_RE.match(text)
        if cl:
            clause_no, title = cl.groups()
            current_clause = {
                "standard": "API 6D",
                "section": recover_section(clause_no),
                "clause": clause_no,
                "title": title.strip(),
                "text": "",
                "page": page_no
            }
            clauses.append(current_clause)
            continue

        # Definition split
        defs = DEF_SPLIT_RE.split(text)
        if len(defs) > 3:
            for i in range(1, len(defs), 2):
                clauses.append({
                    "standard": "API 6D",
                    "section": recover_section(defs[i]),
                    "clause": defs[i],
                    "title": "Definition",
                    "text": defs[i+1].strip(),
                    "page": page_no,
                    "rule_type": "definition",
                    "applies_to": ["All Valves"],
                    "normative_references": [],
                    "datasheet_field": "Definitions"
                })
            current_clause = None
            continue

        if current_clause:
            current_clause["text"] += " " + text

# ============================================================
# ENRICH
# ============================================================

final = []

for c in clauses:
    if not c["text"].strip():
        continue

    c["rule_type"] = classify_rule_type(c["text"])
    c["normative_references"] = extract_normative_refs(c["text"])
    c["applies_to"] = infer_valves(c["title"], c["text"])
    c["datasheet_field"] = infer_datasheet_field(c["title"], c["text"])

    final.append(c)

# ============================================================
# OUTPUT
# ============================================================

out = os.path.splitext(os.path.basename(input_json))[0] + "_clauses.json"
json.dump(final, open(out, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

print(f"✅ Clauses generated: {len(final)}")
print(f"📄 Output file: {out}")
