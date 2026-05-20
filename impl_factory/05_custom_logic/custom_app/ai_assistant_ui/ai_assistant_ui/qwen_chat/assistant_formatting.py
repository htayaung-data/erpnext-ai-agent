from __future__ import annotations

import re
from typing import Any, Callable, Dict, List, Tuple


def extract_markdown_title(text: str) -> str:
	for raw_line in str(text or "").splitlines():
		line = raw_line.strip()
		if not line:
			continue
		if line.startswith("### "):
			return line[4:].strip()
		if line.startswith("## "):
			return line[3:].strip()
		if line.startswith("# "):
			return line[2:].strip()
		if line.startswith("**") and line.endswith("**") and len(line) > 4:
			return line[2:-2].strip()
	return ""


def is_markdown_table_separator(line: str) -> bool:
	return bool(re.match(r"^\s*\|?(?:\s*:?-{3,}:?\s*\|)+\s*:?-{3,}:?\s*\|?\s*$", str(line or "")))


def split_markdown_table_cells(line: str) -> List[str]:
	value = str(line or "").strip()
	if value.startswith("|"):
		value = value[1:]
	if value.endswith("|"):
		value = value[:-1]
	return [cell.strip() for cell in value.split("|")]


def unwrap_markdown_emphasis(value: str) -> Tuple[str, str, str]:
	text = str(value or "").strip()
	match = re.fullmatch(r"(\*{0,2})(.*?)(\*{0,2})", text)
	if not match:
		return "", text, ""
	return match.group(1), match.group(2).strip(), match.group(3)


def detect_amount_unit(value: str) -> str:
	_, inner, _ = unwrap_markdown_emphasis(value)
	lower = inner.lower().strip()
	if not lower:
		return ""
	if re.fullmatch(r"(?:mmk\s+)?-?\d[\d,]*(?:\.\d+)?\s*(?:million mmk|mmk million)", lower):
		return "million_mmk"
	if re.fullmatch(r"mmk\s*-?\d[\d,]*(?:\.\d+)?", lower):
		return "mmk"
	if re.fullmatch(r"-?\d[\d,]*(?:\.\d+)?\s*mmk", lower):
		return "mmk"
	return ""


def header_unit_mode(header: str) -> str:
	value = str(header or "").strip().lower()
	if "million mmk" in value or "mmk million" in value:
		return "million_mmk"
	if "mmk" in value:
		return "mmk"
	return ""


def normalize_amount_cell(value: str, unit_mode: str) -> str:
	if unit_mode not in {"mmk", "million_mmk"}:
		return str(value or "").strip()

	lead, inner, trail = unwrap_markdown_emphasis(value)
	text = inner
	text = re.sub(r"^\s*mmk\s+", "", text, flags=re.IGNORECASE)
	text = re.sub(r"\s+million mmk\s*$", "", text, flags=re.IGNORECASE)
	text = re.sub(r"\s+mmk\s*$", "", text, flags=re.IGNORECASE)
	text = text.strip()
	if not text:
		return str(value or "").strip()
	return f"{lead}{text}{trail}"


def normalize_table_headers_and_rows(headers: List[str], body_lines: List[str]) -> Tuple[List[str], List[str]]:
	if not headers or not body_lines:
		return headers, body_lines

	row_cells: List[List[str]] = [split_markdown_table_cells(line) for line in body_lines]
	normalized_headers = list(headers)
	normalized_rows = [list(cells) for cells in row_cells]

	for idx, header in enumerate(headers):
		header_mode = header_unit_mode(header)
		column_values = [cells[idx] for cells in row_cells if idx < len(cells) and str(cells[idx] or "").strip()]
		detected_modes = [mode for mode in (detect_amount_unit(cell) for cell in column_values) if mode]
		target_mode = header_mode
		if not target_mode and detected_modes:
			target_mode = "million_mmk" if "million_mmk" in detected_modes else "mmk"
		if target_mode not in {"mmk", "million_mmk"}:
			continue

		header_text = str(header or "").strip()
		if not header_mode:
			suffix = "(MMK Million)" if target_mode == "million_mmk" else "(MMK)"
			normalized_headers[idx] = f"{header_text} {suffix}".strip()

		for row_idx, cells in enumerate(normalized_rows):
			if idx >= len(cells):
				continue
			cells[idx] = normalize_amount_cell(cells[idx], target_mode)

	return normalized_headers, ["| " + " | ".join(cells) + " |" for cells in normalized_rows]


def normalize_inline_amount_units(line: str) -> str:
	def repl(match: re.Match[str]) -> str:
		lead = match.group(1) or ""
		number = match.group(2) or ""
		million = bool(match.group(3))
		trail = match.group(3) or ""
		if million:
			return f"{lead}{number} MMK Million{trail}"
		return f"{lead}{number} MMK{trail}"

	normalized = re.sub(
		r"(\*{0,2})MMK\s+(-?\d[\d,]*(?:\.\d+)?)(?:\s+((?:Million MMK|MMK Million)))?(\*{0,2})",
		repl,
		str(line or ""),
		flags=re.IGNORECASE,
	)
	normalized = re.sub(r"\bMMK Million\s+MMK\b", "MMK Million", normalized, flags=re.IGNORECASE)
	return re.sub(r"\bMillion MMK\b", "MMK Million", normalized, flags=re.IGNORECASE)


def normalize_markdown_units(text: str) -> str:
	lines = str(text or "").replace("\r\n", "\n").split("\n")
	out: List[str] = []
	i = 0
	while i < len(lines):
		line = str(lines[i] or "")
		next_line = str(lines[i + 1] or "") if i + 1 < len(lines) else ""
		if "|" in line and is_markdown_table_separator(next_line):
			headers = split_markdown_table_cells(line)
			body_lines: List[str] = []
			i += 2
			while i < len(lines):
				body = str(lines[i] or "")
				if not body.strip() or "|" not in body:
					break
				body_lines.append(body)
				i += 1
			normalized_headers, normalized_body_lines = normalize_table_headers_and_rows(headers, body_lines)
			out.append("| " + " | ".join(normalized_headers) + " |")
			out.append(next_line)
			out.extend(normalized_body_lines)
			continue
		out.append(normalize_inline_amount_units(line))
		i += 1
	return "\n".join(out).strip()


def extract_markdown_tables(text: str) -> List[Dict[str, Any]]:
	lines = str(text or "").replace("\r\n", "\n").split("\n")
	tables: List[Dict[str, Any]] = []
	i = 0
	while i < len(lines):
		line = str(lines[i] or "")
		next_line = str(lines[i + 1] or "") if i + 1 < len(lines) else ""
		if "|" in line and is_markdown_table_separator(next_line):
			headers = split_markdown_table_cells(line)
			rows: List[Dict[str, str]] = []
			i += 2
			while i < len(lines):
				body = str(lines[i] or "")
				if not body.strip() or "|" not in body:
					break
				cells = split_markdown_table_cells(body)
				row = {
					headers[idx] if idx < len(headers) else f"col_{idx + 1}": cells[idx] if idx < len(cells) else ""
					for idx in range(len(headers))
				}
				rows.append(row)
				i += 1
			tables.append({"headers": headers, "rows": rows})
			continue
		i += 1
	return tables


def assistant_text_payload(text: str, *, safe_json_dumps: Callable[[Any], str]) -> str:
	clean = normalize_markdown_units(str(text or "").strip())
	clean = re.sub(r"\bMMKM\b", "MMK Million", clean, flags=re.IGNORECASE)
	clean = re.sub(r"\bMillion MMK\b", "MMK Million", clean, flags=re.IGNORECASE)
	clean = re.sub(r"(\d+(?:\.\d+)?)\s*M\s*MMK\b", r"\1 MMK Million", clean, flags=re.IGNORECASE)
	clean = re.sub(r"(\d+(?:\.\d+)?)\s*million\b", r"\1 MMK Million", clean, flags=re.IGNORECASE)
	clean = re.sub(r"\bMMK\s+MMK\s+Million\b", "MMK Million", clean, flags=re.IGNORECASE)
	clean = re.sub(r"\bMMK\s+million\b", "MMK Million", clean, flags=re.IGNORECASE)
	clean = re.sub(r'[₹₩¥₮$€]\s*([\d,]+(?:\.\d+)?)\s*(?:m|mn)\b', r'\1 MMK Million', clean, flags=re.IGNORECASE)
	clean = re.sub(r'[₹₩¥₮$€]\s*([\d,]+(?:\.\d+)?)', r'\1 MMK', clean)
	clean = re.sub(r'\b(INR|USD|EUR|GBP)\b', 'MMK', clean)

	payload: Dict[str, Any] = {
		"type": "text",
		"text": clean,
		"format": "markdown",
	}
	title = extract_markdown_title(clean)
	if title:
		payload["title"] = title
	tables = extract_markdown_tables(clean)
	if tables:
		payload["tables"] = tables
	return safe_json_dumps(payload)


def build_markdown_table(headers: List[str], rows: List[Dict[str, Any]]) -> str:
	clean_headers = [str(header or "").strip() for header in headers if str(header or "").strip()]
	if not clean_headers:
		return ""
	separator = "| " + " | ".join("---" for _ in clean_headers) + " |"
	lines = ["| " + " | ".join(clean_headers) + " |", separator]
	for row in rows:
		if not isinstance(row, dict):
			continue
		cells = [str(row.get(header) or "").strip() for header in clean_headers]
		lines.append("| " + " | ".join(cells) + " |")
	return "\n".join(lines).strip()


def ensure_table_from_grounded_context(
	text: str,
	assistant_payload: Dict[str, Any],
	grounded_turn: Dict[str, Any],
) -> str:
	current = str(text or "").strip()
	if current and extract_markdown_tables(current):
		return current
	headers = grounded_turn.get("returned_schema")
	rows = grounded_turn.get("table_rows")
	if not isinstance(headers, list) or not isinstance(rows, list):
		return current
	table_block = build_markdown_table(headers, rows)
	if not table_block:
		return current
	if not current:
		title = str(assistant_payload.get("title") or grounded_turn.get("source_name") or "").strip()
		if title:
			return f"## {title}\n\n{table_block}".strip()
		return table_block
	return f"{current}\n\n{table_block}".strip()


def format_million_value(raw: str) -> str:
	negative = raw.startswith("-")
	numeric = raw[1:] if negative else raw
	value = float(numeric.replace(",", ""))
	scaled = value / 1_000_000.0
	text = f"{scaled:,.2f}".rstrip("0").rstrip(".")
	return f"-{text}" if negative else text


def currency_like_header(header: str) -> bool:
	value = str(header or "").strip().lower()
	return any(token in value for token in ("sales", "revenue", "amount", "outstanding", "value", "mmk"))


def convert_summary_line_to_million(line: str) -> str:
	text = str(line or "")
	lower = text.lower()
	if "million" in lower:
		return text
	if not any(token in lower for token in ("sales", "revenue", "amount", "outstanding", "value", "mmk")):
		return text
	pattern = re.compile(
		r"(\*{0,2})(?:MMK\s+)?(-?\d{1,3}(?:,\d{3})+(?:\.\d+)?)(?:\s+MMK)?(\*{0,2})",
		flags=re.IGNORECASE,
	)

	def _replace(match: re.Match[str]) -> str:
		scaled = format_million_value(match.group(2))
		return f"{match.group(1)}{scaled} MMK Million{match.group(3)}"

	return pattern.sub(_replace, text)


def transform_markdown_to_million(text: str) -> str:
	lines = str(text or "").replace("\r\n", "\n").split("\n")
	out: List[str] = []
	i = 0
	while i < len(lines):
		line = str(lines[i] or "")
		next_line = str(lines[i + 1] or "") if i + 1 < len(lines) else ""
		if "|" in line and is_markdown_table_separator(next_line):
			headers = split_markdown_table_cells(line)
			scaled_headers = []
			scale_cols = set()
			for idx, header in enumerate(headers):
				if currency_like_header(header):
					scale_cols.add(idx)
					if "million" not in header.lower():
						header = header.replace("(MMK)", "(MMK Million)")
						if header == headers[idx]:
							header = f"{header} (MMK Million)"
				scaled_headers.append(header)
			out.append("| " + " | ".join(scaled_headers) + " |")
			out.append(next_line)
			i += 2
			while i < len(lines):
				body = str(lines[i] or "")
				if not body.strip() or "|" not in body:
					break
				cells = split_markdown_table_cells(body)
				for idx in scale_cols:
					if idx >= len(cells):
						continue
					cell = cells[idx]
					match = re.fullmatch(r"(\*{0,2})(-?\d{1,3}(?:,\d{3})+(?:\.\d+)?)(\*{0,2})", cell.strip())
					if not match:
						continue
					cells[idx] = f"{match.group(1)}{format_million_value(match.group(2))}{match.group(3)}"
				out.append("| " + " | ".join(cells) + " |")
				i += 1
			continue
		out.append(convert_summary_line_to_million(line))
		i += 1
	return "\n".join(out).strip()
