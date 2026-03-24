#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Iterable, List, Tuple


REPO_ROOT = Path(__file__).resolve().parent.parent

PYTHON_SCAN_ROOTS = [
	REPO_ROOT / "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat",
	REPO_ROOT / "experimental/qwen_agent_runtime/app",
]

JSON_SCAN_FILES = [
	REPO_ROOT / "impl_factory/03_config/qwen_enterprise_metadata/business_ontology.json",
	REPO_ROOT / "impl_factory/03_config/qwen_enterprise_metadata/intent_bias_rules_registry.json",
	REPO_ROOT / "impl_factory/03_config/qwen_enterprise_metadata/clarification_templates_registry.json",
]

BANNED_JSON_KEYS = {
	"tokens_any",
	"tokens_all",
	"tokens_any_of",
	"tokens_none",
	"tokens_optional",
	"tokens_required",
	"tokens_excluded",
}

JSON_EXAMPLE_PHRASES = {
	"include qty",
	"how about last year",
	"show me all time",
}

TEXT_VAR_NAMES = {
	"text",
	"msg",
	"message",
	"raw_message",
	"normalized_text",
	"user_message",
}

LEXICAL_IN_PATTERN = re.compile(
	r"""
	\bif\b
	[^\n]{0,200}?
	(["'])([^"'\n]{2,80})\1
	\s+in\s+
	([A-Za-z_][A-Za-z0-9_]*)
	""",
	re.VERBOSE,
)

DOMAIN_BAG_PATTERN = re.compile(
	r"""
	re\.(?:search|match|compile)\(
		r?["'][^"'\n]{0,80}
		(customer|supplier|invoice|product|stock|inventory|payable|receivable|revenue|sales|cash|balance)
		[^"'\n]{0,400}
		\|
		[^"'\n]{0,400}
		(customer|supplier|invoice|product|stock|inventory|payable|receivable|revenue|sales|cash|balance)
		[^"'\n]{0,400}
	["']
	""",
	re.VERBOSE,
)

CONFIRMATION_LOGIC_PATTERN = re.compile(
	r"""
	(?i)
	(
		\bif\b[^\n]{0,200}
		|
		\belif\b[^\n]{0,200}
		|
		=\s*[\{\[\(][^\n]{0,200}
	)
	["'](?:yes|sure|go ahead)["']
	""",
	re.VERBOSE,
)


def _iter_python_files() -> Iterable[Path]:
	for root in PYTHON_SCAN_ROOTS:
		if not root.exists():
			continue
		for path in root.rglob("*.py"):
			if path.name == "__init__.py":
				continue
			yield path


def _line_number_from_offset(text: str, offset: int) -> int:
	return text.count("\n", 0, offset) + 1


def _check_python_file(path: Path) -> List[Tuple[Path, int, str]]:
	text = path.read_text(encoding="utf-8")
	issues: List[Tuple[Path, int, str]] = []

	for match in LEXICAL_IN_PATTERN.finditer(text):
		literal = match.group(2).strip().lower()
		var_name = match.group(3).strip()
		if var_name not in TEXT_VAR_NAMES:
			continue
		if literal in {"", " ", "\n"}:
			continue
		line = _line_number_from_offset(text, match.start())
		issues.append(
			(
				path,
				line,
				f'Lexical phrase check detected: string literal "{literal}" tested directly against `{var_name}`.',
			)
		)

	for match in DOMAIN_BAG_PATTERN.finditer(text):
		line = _line_number_from_offset(text, match.start())
		issues.append(
			(
				path,
				line,
				"Domain-bag regex detected in runtime code. Business meaning should not be encoded as regex keyword bags.",
			)
		)

	for match in CONFIRMATION_LOGIC_PATTERN.finditer(text):
		line = _line_number_from_offset(text, match.start())
		issues.append(
			(
				path,
				line,
				"Confirmation logic detected from lexical examples like yes/sure/go ahead.",
			)
		)
	return issues


def _walk_json(value, path_parts: List[str], findings: List[Tuple[str, str]]) -> None:
	if isinstance(value, dict):
		for key, child in value.items():
			child_path = path_parts + [str(key)]
			if key in BANNED_JSON_KEYS:
				findings.append((".".join(child_path), f'Banned token-rule key "{key}" found.'))
			_walk_json(child, child_path, findings)
	elif isinstance(value, list):
		for idx, child in enumerate(value):
			_walk_json(child, path_parts + [str(idx)], findings)
	elif isinstance(value, str):
		lower = value.strip().lower()
		for phrase in JSON_EXAMPLE_PHRASES:
			if phrase == lower:
				findings.append((".".join(path_parts), f'Example phrase "{phrase}" found in metadata.'))


def _check_json_file(path: Path) -> List[Tuple[Path, int, str]]:
	if not path.exists():
		return []
	data = json.loads(path.read_text(encoding="utf-8"))
	findings: List[Tuple[str, str]] = []
	_walk_json(data, [], findings)
	issues: List[Tuple[Path, int, str]] = []
	for json_path, message in findings:
		issues.append((path, 1, f"{message} JSON path: {json_path}"))
	return issues


def main() -> int:
	issues: List[Tuple[Path, int, str]] = []

	for path in _iter_python_files():
		issues.extend(_check_python_file(path))

	for path in JSON_SCAN_FILES:
		issues.extend(_check_json_file(path))

	if not issues:
		print("Qwen enterprise guardrail audit: PASS")
		return 0

	print("Qwen enterprise guardrail audit: FAIL")
	for path, line, message in sorted(issues, key=lambda item: (str(item[0]), item[1], item[2])):
		rel = path.relative_to(REPO_ROOT)
		print(f"- {rel}:{line}: {message}")
	return 1


if __name__ == "__main__":
	sys.exit(main())
