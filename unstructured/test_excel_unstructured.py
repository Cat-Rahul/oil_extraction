"""Excel to structured JSON for LLM training.

This script detects tables as contiguous non-empty rectangular regions
in each sheet and emits a clear schema with:
- headers, rows (as dicts), ranges (start/end row & column), and counts.

It also optionally includes `unstructured` partition output if that
package is installed.
"""
import argparse
import json
import os
import re
import sys
from typing import List, Dict, Any, Tuple


def try_import_unstructured():
	try:
		from unstructured.partition.auto import partition

		return partition
	except Exception:
		return None


def col_idx_to_letter(idx: int) -> str:
	# 0-based idx to Excel column (A, B, ..., Z, AA...)
	result = ""
	n = idx + 1
	while n > 0:
		n, rem = divmod(n - 1, 26)
		result = chr(65 + rem) + result
	return result


def _cell_value(v):
	# Convert numpy/pandas types to plain Python types
	try:
		import pandas as pd

		if pd.isna(v):
			return None
	except Exception:
		pass
	return v


def normalize_embedded_kv(v: str) -> Tuple[str, str] | None:
	# Detect patterns like "Piping Class is A1, 150#" or "Material: CS"
	if not isinstance(v, str):
		return None
	s = v.strip()
	if not s:
		return None
	m = re.match(r"^([^:]+?)\s*(?:is|:)\s*(.+)$", s, flags=re.IGNORECASE)
	if m:
		key = m.group(1).strip()
		val = m.group(2).strip()
		return key, val
	return None


def clean_data(obj: Any) -> Any:
	# Recursively remove None / empty-string / empty-list / empty-dict
	if isinstance(obj, dict):
		out = {}
		for k, v in obj.items():
			cv = clean_data(v)
			if cv is None:
				continue
			if cv == "":
				continue
			if cv == []:
				continue
			if cv == {}:
				continue
			out[k] = cv
		return out if out else None
	if isinstance(obj, list):
		out_list = []
		for item in obj:
			cv = clean_data(item)
			if cv is None:
				continue
			if cv == "":
				continue
			if cv == []:
				continue
			if cv == {}:
				continue
			out_list.append(cv)
		return out_list if out_list else None
	if isinstance(obj, str):
		s = obj.strip()
		return s if s != "" else None
	return obj


def detect_tables_in_df(df) -> List[Dict[str, Any]]:
	# df: pandas DataFrame read with header=None (raw grid)
	import pandas as pd

	# Normalize whitespace-only strings to NaN for detection
	mask = df.applymap(lambda x: False if (pd.isna(x) or (isinstance(x, str) and x.strip() == "")) else True)

	row_has = mask.any(axis=1).tolist()
	col_has_full = mask.any(axis=0).tolist()

	tables = []

	# find contiguous row segments
	r = 0
	table_count = 0
	while r < len(row_has):
		if not row_has[r]:
			r += 1
			continue
		r0 = r
		while r + 1 < len(row_has) and row_has[r + 1]:
			r += 1
		r1 = r

		# within these rows, find contiguous column segments that have any data
		sub = mask.iloc[r0 : r1 + 1, :]
		col_has = sub.any(axis=0).tolist()
		c = 0
		while c < len(col_has):
			if not col_has[c]:
				c += 1
				continue
			c0 = c
			while c + 1 < len(col_has) and col_has[c + 1]:
				c += 1
			c1 = c

			table_count += 1
			table_sub = df.iloc[r0 : r1 + 1, c0 : c1 + 1]

			# Heuristic: decide whether first row is header
			first_row = table_sub.iloc[0]
			non_null = first_row.notna().sum()
			string_like = first_row.apply(lambda x: isinstance(x, str)).sum()
			has_header = (string_like >= max(1, non_null // 2))

			headers = []
			data_rows = []
			if has_header:
				for i, v in enumerate(first_row.tolist()):
					if pd.isna(v) or (isinstance(v, str) and v.strip() == ""):
						headers.append(f"column_{i+1}")
					else:
						headers.append(str(v).strip())
				raw_data = table_sub.iloc[1:]
			else:
				headers = [f"column_{i+1}" for i in range(table_sub.shape[1])]
				raw_data = table_sub

			for _, row in raw_data.iterrows():
				obj = {}
				for i, h in enumerate(headers):
					raw = row.iat[i]
					# try to extract embedded key:value patterns
					embedded = None
					if isinstance(raw, str):
						embedded = normalize_embedded_kv(raw)
					if embedded:
						k2, v2 = embedded
						if v2:
							obj[k2] = v2
					else:
						clean_val = _cell_value(raw)
						if isinstance(clean_val, str):
							clean_val = clean_val.strip()
						if clean_val is not None and clean_val != "":
							obj[h] = clean_val

				# remove empty/null keys from the row
				cleaned_row = clean_data(obj)
				if cleaned_row is None:
					cleaned_row = {}
				data_rows.append(cleaned_row)

			# remove rows that are empty
			data_rows = [r for r in data_rows if r]

			table = {
				"table_id": f"table_{table_count}",
				"range": {
					"start_row": int(r0 + 1),
					"end_row": int(r1 + 1),
					"start_col": int(c0 + 1),
					"end_col": int(c1 + 1),
					"start_col_letter": col_idx_to_letter(c0),
					"end_col_letter": col_idx_to_letter(c1),
				},
				"num_rows": len(data_rows),
				"num_columns": len(headers),
				"headers": headers,
				"rows": data_rows,
			}
			tables.append(table)
			c += 1

		r += 1

	return tables


def process_file(path: str, sheet_name: str = None) -> Dict[str, Any]:
	import pandas as pd

	result = {"file": os.path.basename(path), "sheets": []}

	to_partition = try_import_unstructured()

	if sheet_name is None:
		sheets = pd.read_excel(path, sheet_name=None, header=None, dtype=object)
	else:
		sheets = {sheet_name: pd.read_excel(path, sheet_name=sheet_name, header=None, dtype=object)}

	for name, df in sheets.items():
		sheet_info = {
			"sheet_name": str(name),
			"n_rows": int(df.shape[0]),
			"n_columns": int(df.shape[1]),
			"tables": [],
		}

		tables = detect_tables_in_df(df)
		sheet_info["tables"] = tables

		result["sheets"].append(sheet_info)

	if to_partition is not None:
		try:
			# best-effort include unstructured partition text
			elements = to_partition(filename=path)
			result["unstructured_elements"] = [
				{"type": el.__class__.__name__, "text": getattr(el, "text", None)} for el in elements
			]
		except Exception as e:
			result["unstructured_error"] = str(e)

	# Clean top-level structure to remove null/empty entries
	cleaned = clean_data(result)
	return cleaned or {}


def main():
	parser = argparse.ArgumentParser(description="Extract Excel into structured JSON for LLM training")
	parser.add_argument("input", help="Input Excel file (.xlsx)")
	parser.add_argument("--sheet", help="Sheet name or index to read (optional)")
	parser.add_argument("--output", "-o", help="Output JSON file (default: stdout)")

	args = parser.parse_args()

	input_path = args.input
	if not os.path.exists(input_path):
		print(f"Input file not found: {input_path}", file=sys.stderr)
		sys.exit(2)

	try:
		out = process_file(input_path, sheet_name=args.sheet)
	except Exception as e:
		print(f"Failed to process file: {e}", file=sys.stderr)
		sys.exit(3)

	out_json = json.dumps(out, ensure_ascii=False, indent=2)

	output_path = args.output
	if not output_path:
		output_path = os.path.splitext(input_path)[0] + ".json"

	with open(output_path, "w", encoding="utf-8") as f:
		f.write(out_json)
	
	print(f"✅ Wrote structured JSON to: {output_path}")


if __name__ == "__main__":
	main()

