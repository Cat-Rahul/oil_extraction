import os
import json
import re
from typing import List, Dict, Any, Tuple, Optional, Set
from bs4 import BeautifulSoup
from collections import Counter
from unstructured.partition.pdf import partition_pdf
from unstructured.documents.elements import Table


# ============================================================
# CONFIG
# ============================================================

COMMON_SUFFIXES = {"no", "number", "code", "id", "date", "qty", "name", "description", "type", "seq"}
MIN_TABLE_ROWS = 2
MIN_COLUMN_ALIGNMENT = 0.5
MAX_HEADER_LENGTH = 60  # Increased to allow legitimate long headers
MAX_HEADER_SPECIAL_CHARS_RATIO = 0.5  # More lenient


# ============================================================
# TEXT CLEANING (MINIMAL - PRESERVES CONTENT)
# ============================================================

def clean_text(text: str) -> str:
    """Minimal cleaning - only remove excessive whitespace."""
    if not text:
        return ""
    
    # Replace multiple spaces/newlines with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Remove control characters but keep normal punctuation
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    
    return text.strip()


def is_garbage_header(header: str) -> bool:
    """
    Only detect truly garbage headers - be very conservative.
    Preserve legitimate technical headers.
    """
    if not header or len(header) < 1:
        return True
    
    # Too long to be a header
    if len(header) > MAX_HEADER_LENGTH:
        return True
    
    # Excessive special characters (but allow technical notation)
    special_chars = sum(1 for c in header if not c.isalnum() and c not in ' -_./()[]')
    if len(header) > 0 and special_chars / len(header) > MAX_HEADER_SPECIAL_CHARS_RATIO:
        return True
    
    # Repetitive patterns like "=====" or "-----"
    if re.search(r'(.)\1{6,}', header):
        return True
    
    # Only pipes or underscores
    if re.match(r'^[|_\s]+$', header):
        return True
    
    return False


def clean_header(header: str) -> str:
    """
    Minimal header cleaning - preserve technical terms and legitimate headers.
    Only remove obvious artifacts.
    """
    header = clean_text(header)
    
    # Remove ONLY obvious document artifacts that appear in header rows
    # But be very careful not to remove legitimate column names
    
    # Remove excessive pipes/underscores used as separators
    header = re.sub(r'[|_]{3,}', ' ', header)
    
    # Remove standalone page markers like "Page 5 of 127" but keep "Page" as a column name
    header = re.sub(r'\bPage\s+\d+\s+of\s+\d+\b', '', header, flags=re.IGNORECASE)
    
    header = clean_text(header)
    
    return header if header and not is_garbage_header(header) else ""


# ============================================================
# PAGE HEADER/FOOTER DETECTION
# ============================================================

def detect_page_headers_footers(pages_data: Dict[int, List[str]]) -> Dict[int, Dict[str, Any]]:
    """
    Detect recurring text across pages that appears in same position.
    This identifies headers/footers.
    """
    if len(pages_data) < 2:
        return {}
    
    # Find text that appears on multiple pages
    text_frequency = Counter()
    text_to_pages = {}
    
    for page_num, texts in pages_data.items():
        for text in texts:
            cleaned = clean_text(text)
            if len(cleaned) < 5:  # Skip very short text
                continue
            
            text_frequency[cleaned] += 1
            text_to_pages.setdefault(cleaned, set()).add(page_num)
    
    # Find recurring text (appears on 50%+ of pages)
    min_occurrences = max(2, len(pages_data) // 2)
    recurring_texts = {
        text for text, count in text_frequency.items() 
        if count >= min_occurrences
    }
    
    # Classify recurring text by position and content
    headers_footers = {}
    
    for page_num, texts in pages_data.items():
        page_header = []
        page_footer = []
        
        for i, text in enumerate(texts):
            cleaned = clean_text(text)
            
            if cleaned in recurring_texts:
                # First few texts are likely headers
                if i < len(texts) // 3:
                    page_header.append(cleaned)
                # Last few texts are likely footers
                elif i > 2 * len(texts) // 3:
                    page_footer.append(cleaned)
        
        headers_footers[page_num] = {
            "header": " | ".join(page_header) if page_header else "",
            "footer": " | ".join(page_footer) if page_footer else "",
            "recurring_texts": list(recurring_texts & set(clean_text(t) for t in texts))
        }
    
    return headers_footers


# ============================================================
# HEADER DETECTION IN TABLES
# ============================================================

def detect_header_row(rows: List[List[str]]) -> int:
    """
    Intelligently detect which row is the actual header.
    """
    if not rows or len(rows) < 2:
        return 0
    
    scores = []
    
    for i, row in enumerate(rows[:3]):
        score = 0
        
        # Prefer rows with shorter text
        avg_length = sum(len(cell) for cell in row) / len(row) if row else 0
        if 3 <= avg_length <= 40:
            score += 2
        
        # Prefer rows with proper capitalization
        capitalized = sum(1 for cell in row if cell and cell[0].isupper())
        score += capitalized
        
        # Prefer rows with common header keywords
        header_keywords = [
            'no', 'number', 'name', 'code', 'type', 'description', 
            'date', 'qty', 'id', 'rev', 'seq', 'class', 'spec',
            'material', 'size', 'rating', 'pressure', 'temp'
        ]
        keyword_matches = sum(1 for cell in row if any(
            kw in cell.lower() for kw in header_keywords
        ))
        score += keyword_matches * 3
        
        # Penalize rows that are mostly numeric
        numeric_cells = sum(1 for cell in row if cell and cell.replace('.', '').replace('-', '').isdigit())
        if numeric_cells > len(row) * 0.5:
            score -= 3
        
        scores.append(score)
    
    return scores.index(max(scores)) if scores else 0


# ============================================================
# HEADER MERGING (CONSERVATIVE)
# ============================================================

def should_merge_headers(a: str, b: str) -> bool:
    """
    Conservative merging - only merge obvious split headers.
    """
    if not a or not b:
        return False
    
    a_clean = clean_text(a.lower())
    b_clean = clean_text(b.lower())
    
    # Don't merge if either is garbage
    if is_garbage_header(a) or is_garbage_header(b):
        return False
    
    # Merge if second part is common suffix
    if b_clean in COMMON_SUFFIXES and len(a_clean) <= 20:
        return True
    
    # Merge very short fragments (likely split words)
    if len(a_clean) <= 3 and len(b_clean) <= 3 and not b_clean.isdigit():
        return True
    
    # Merge if first part ends with separator
    if a_clean and a_clean[-1] in '-,/':
        return True
    
    return False


def merge_headers(raw_headers: List[str]) -> Tuple[List[str], Dict[int, List[int]]]:
    """
    Merge split headers while preserving legitimate separate columns.
    """
    # Clean headers minimally
    cleaned = [clean_header(h) for h in raw_headers]
    
    merged: List[str] = []
    header_map: Dict[int, List[int]] = {}
    merged_idx = 0
    i = 0
    
    while i < len(cleaned):
        current = cleaned[i]
        
        # Skip completely empty
        if not current:
            i += 1
            continue
        
        merge_group = [i]
        
        # Look ahead for potential merges
        j = i + 1
        while j < len(cleaned):
            nxt = cleaned[j]
            if nxt and should_merge_headers(current, nxt):
                merge_group.append(j)
                current = f"{current} {nxt}".strip()
                j += 1
            else:
                break
        
        # Add merged header
        merged.append(current)
        header_map[merged_idx] = merge_group
        merged_idx += 1
        
        i = j if j > i else i + 1
    
    # Fallback to generic names if all headers are garbage
    if not merged or all(is_garbage_header(h) for h in merged):
        merged = [f"Column_{i}" for i in range(len(raw_headers))]
        header_map = {i: [i] for i in range(len(raw_headers))}
    
    return merged, header_map


# ============================================================
# TABLE PARSING
# ============================================================

def parse_html_table(html: str) -> List[List[str]]:
    """Parse HTML table carefully."""
    try:
        soup = BeautifulSoup(html, "html.parser")
        rows = []
        
        for tr in soup.find_all("tr"):
            cells = []
            for cell in tr.find_all(["td", "th"]):
                text = clean_text(cell.get_text())
                colspan = int(cell.get("colspan", 1))
                cells.extend([text] * colspan)
            
            if cells:
                rows.append(cells)
        
        return rows
    except Exception as e:
        print(f"⚠️  Error parsing table: {e}")
        return []


def normalize_table_rows(rows: List[List[str]]) -> List[List[str]]:
    """Normalize column counts."""
    if not rows:
        return rows
    
    col_counts = [len(row) for row in rows]
    most_common_cols = max(set(col_counts), key=col_counts.count)
    
    normalized = []
    for row in rows:
        if len(row) < most_common_cols:
            row = row + [""] * (most_common_cols - len(row))
        elif len(row) > most_common_cols:
            row = row[:most_common_cols]
        normalized.append(row)
    
    return normalized


def is_valid_table(rows: List[List[str]], headers: List[str]) -> bool:
    """Validate table structure."""
    if len(rows) < MIN_TABLE_ROWS:
        return False
    
    # Need at least some valid headers
    valid_headers = sum(1 for h in headers if h and not h.startswith("Column_"))
    if valid_headers == 0:
        return False
    
    # Check alignment
    header_len = len(headers)
    aligned = sum(1 for r in rows[1:] if abs(len(r) - header_len) <= 2)
    alignment_ratio = aligned / len(rows[1:]) if len(rows) > 1 else 0
    
    if alignment_ratio < MIN_COLUMN_ALIGNMENT:
        return False
    
    # Need actual content
    has_content = any(
        any(cell and len(cell) > 1 for cell in row) 
        for row in rows[1:]
    )
    
    return has_content


def extract_table_rows(
    headers: List[str],
    header_map: Dict[int, List[int]],
    rows: List[List[str]]
) -> List[Dict[str, str]]:
    """Extract data rows as dictionaries."""
    data = []
    
    for row in rows[1:]:
        if not any(cell.strip() for cell in row):
            continue
        
        row_dict: Dict[str, str] = {}
        
        for idx, header in enumerate(headers):
            if not header:
                continue
            
            values = []
            for orig_idx in header_map.get(idx, [idx]):
                if orig_idx < len(row):
                    cell_value = clean_text(row[orig_idx])
                    if cell_value:
                        values.append(cell_value)
            
            row_dict[header] = " ".join(values) if values else ""
        
        if any(v for v in row_dict.values()):
            data.append(row_dict)
    
    return data


# ============================================================
# MAIN EXTRACTION
# ============================================================

def extract_pdf(
    pdf_path: str,
    output_json: str = "extraction_output.json",
    strategy: str = "hi_res"
) -> Dict[str, Any]:
    """
    Extract PDF with separate header/footer detection.
    """
    
    print(f"📄 Extracting: {pdf_path}")
    print(f"⚙️  Strategy: {strategy}")
    
    # Partition PDF
    elements = partition_pdf(
        filename=pdf_path,
        strategy=strategy,
        infer_table_structure=True,
        languages=["eng"],
        extract_images_in_pdf=False
    )
    
    print(f"✓ Found {len(elements)} elements")
    
    # First pass: collect all text by page for header/footer detection
    page_texts: Dict[int, List[str]] = {}
    
    for el in elements:
        if not isinstance(el, Table) and hasattr(el, 'text') and el.text:
            page = getattr(el.metadata, "page_number", 1) or 1
            text = clean_text(el.text)
            if text:
                page_texts.setdefault(page, []).append(text)
    
    # Detect recurring headers/footers
    print("🔍 Detecting page headers/footers...")
    headers_footers = detect_page_headers_footers(page_texts)
    
    # Second pass: organize content
    pages: Dict[int, Dict[str, Any]] = {}
    
    for el in elements:
        page = getattr(el.metadata, "page_number", 1) or 1
        
        pages.setdefault(page, {
            "tables": [],
            "text": []
        })
        
        # TABLE PROCESSING
        if isinstance(el, Table):
            html = getattr(el.metadata, "text_as_html", None)
            if not html:
                continue
            
            rows = parse_html_table(html)
            if not rows:
                continue
            
            # Detect header row
            header_idx = detect_header_row(rows)
            table_data = rows[header_idx:]
            table_data = normalize_table_rows(table_data)
            
            if len(table_data) < MIN_TABLE_ROWS:
                continue
            
            # Merge headers
            raw_headers = table_data[0]
            headers, header_map = merge_headers(raw_headers)
            
            # Validate
            if not is_valid_table(table_data, headers):
                continue
            
            # Extract data
            data_rows = extract_table_rows(headers, header_map, table_data)
            
            if data_rows:
                pages[page]["tables"].append({
                    "headers": headers,
                    "rows": data_rows,
                    "row_count": len(data_rows),
                    "column_count": len(headers),
                    "raw_headers": raw_headers  # Preserve original headers for reference
                })
        
        # TEXT PROCESSING (exclude recurring headers/footers)
        elif hasattr(el, 'text') and el.text:
            text = clean_text(el.text)
            if not text:
                continue
            
            # Skip if this text is a recurring header/footer
            hf = headers_footers.get(page, {})
            if text in hf.get("recurring_texts", []):
                continue
            
            pages[page]["text"].append({
                "type": getattr(el, "category", "Unknown"),
                "text": text
            })
    
    # Build result with separate header/footer info
    result = {
        "file": os.path.basename(pdf_path),
        "extraction_strategy": strategy,
        "total_pages": len(pages),
        "pages": []
    }
    
    for page_num in sorted(pages):
        page_data = pages[page_num]
        hf = headers_footers.get(page_num, {})
        
        result["pages"].append({
            "page_number": page_num,
            "page_header": hf.get("header", ""),
            "page_footer": hf.get("footer", ""),
            "tables": page_data["tables"],
            "table_count": len(page_data["tables"]),
            "text_blocks": page_data["text"],
            "text_block_count": len(page_data["text"])
        })
    
    # Write output
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    # Summary
    total_tables = sum(len(p["tables"]) for p in result["pages"])
    total_rows = sum(t["row_count"] for p in result["pages"] for t in p["tables"])
    pages_with_headers = sum(1 for p in result["pages"] if p["page_header"])
    
    print(f"\n📊 Extraction Complete:")
    print(f"   Pages: {len(result['pages'])}")
    print(f"   Tables: {total_tables}")
    print(f"   Table rows: {total_rows}")
    print(f"   Pages with detected headers: {pages_with_headers}")
    print(f"\n✅ Saved to: {output_json}")
    
    return result


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    pdf_file = "output_no_footer.pdf"
    
    if os.path.exists(pdf_file):
        output_name = os.path.splitext(pdf_file)[0] + ".json"
        extract_pdf(pdf_file, output_name)
    else:
        print(f"❌ PDF not found: {pdf_file}")