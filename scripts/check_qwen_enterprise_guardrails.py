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
	REPO_ROOT / "impl_factory/03_config/qwen_enterprise_metadata/semantic_resolution_registry.json",
	REPO_ROOT / "impl_factory/03_config/qwen_enterprise_metadata/financial_summary_resolution_registry.json",
	REPO_ROOT / "impl_factory/03_config/qwen_enterprise_metadata/smoke_fixture_registry.json",
]

SMOKE_FIXTURE_INLINE_SCAN_FILES = [
	REPO_ROOT / "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py",
	REPO_ROOT / "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/phase6_hardening_support.py",
	REPO_ROOT / "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/phase7_hardening_support.py",
	REPO_ROOT / "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/phase8_hardening_support.py",
]

FRESH_QUERY_INTERPRETER_GUARDRAIL_FILE = (
	REPO_ROOT
	/ "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/fresh_query_interpreter.py"
)
FAMILY_ADAPTERS_GUARDRAIL_FILE = (
	REPO_ROOT
	/ "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/family_adapters.py"
)
GOVERNED_REPORT_EXECUTOR_GUARDRAIL_FILE = (
	REPO_ROOT
	/ "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/governed_report_executor.py"
)
LEGACY_RUNTIME_LANE_GUARDRAIL_FILE = (
	REPO_ROOT
	/ "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/legacy_runtime_lane.py"
)
FAMILY_TOOL_SURFACE_GUARDRAIL_FILE = (
	REPO_ROOT
	/ "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/family_tool_surface.py"
)

FRESH_QUERY_INTERPRETER_BANNED_SUBSTRINGS = {
	"_repair_governed_interpretation_from_message(": "Semantic-governed interpreter must not repair routing from raw message text.",
	"def _message_ranking_subject(": "Semantic-governed interpreter must not infer ranking subject from raw message text.",
	"def _message_ranking_metric(": "Semantic-governed interpreter must not infer ranking metric from raw message text.",
	"apply_intent_rules(message, interpretation)": "Semantic-governed interpreter must not mutate intent class from raw message text during validation.",
	'ontology_query_slot_aliases("requested_time_scope")': "Semantic-governed interpreter must not derive requested time scope from raw message text during validation.",
	"build_family_tool_surface_for_message(": "Fresh-query interpreter must not route from raw-message family tool surface fallback.",
}
FAMILY_ADAPTERS_BANNED_SUBSTRINGS = {
	"def _requested_top_n(": "Family adapters must not infer rank limits from raw message text.",
	"def _requested_metric_hint(": "Family adapters must not infer metric choice from raw message text.",
	"def _requested_output_columns(": "Family adapters must not infer requested columns from raw message text.",
	"def _requested_transaction_columns(message:": "Transaction listing adapters must not infer columns from raw message text.",
}
GOVERNED_REPORT_EXECUTOR_BANNED_SUBSTRINGS = {
	"def _requested_limit(": "Governed report executor must not derive direct-query limits from raw message text.",
}
LEGACY_RUNTIME_LANE_BANNED_SUBSTRINGS = {
	"build_family_tool_surface_for_message(": "Legacy runtime lane must not route from raw-message family tool surface.",
}
FAMILY_TOOL_SURFACE_BANNED_SUBSTRINGS = {
	"report_family_transitional_surface_markers(": "Family tool surface must not route from transitional phrase markers.",
	"def _matched_phrases(": "Family tool surface must not match raw report/marker phrases from message text.",
}
FOLLOWUP_INTERPRETER_GUARDRAIL_FILE = (
	REPO_ROOT
	/ "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/followup_interpreter.py"
)
FOLLOWUP_INTERPRETER_BANNED_SUBSTRINGS = {
	"ontology_detect_followup_modes(": "Follow-up interpreter must not parse raw follow-up modes from message text.",
	"def is_million_transform_intent(": "Follow-up interpreter must not keep lexical million-transform parser seams.",
	"ontology_followup_slot_aliases(": "Follow-up interpreter must not derive time-scope breakout from raw message aliases.",
	"ontology_self_contained_prefixes(": "Follow-up interpreter must not derive fresh-query breakout from self-contained prefix lists.",
}

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


def _check_inline_smoke_fixture_literals() -> List[Tuple[Path, int, str]]:
	try:
		smoke_registry = json.loads(
			(
				REPO_ROOT
				/ "impl_factory/03_config/qwen_enterprise_metadata/smoke_fixture_registry.json"
			).read_text(encoding="utf-8")
		)
	except Exception as exc:
		return [
			(
				REPO_ROOT / "impl_factory/03_config/qwen_enterprise_metadata/smoke_fixture_registry.json",
				1,
				f"Smoke fixture registry inline-literal scan failed to load: {exc}",
			)
		]

	fixture_literals = {
		"give me AR insight",
		"how do I ask for qty",
		"forget that, give me AR insight",
		"forget that, show me AR insight",
		"include qty column",
		"include serial number column",
		"yes please run the governed alternative",
		"yes, run that",
	}
	for fixture in smoke_registry.get("fixtures") or []:
		if not isinstance(fixture, dict):
			continue
		replacement_message = str(fixture.get("replacement_message") or "").strip()
		if replacement_message:
			fixture_literals.add(replacement_message)
		action_messages = fixture.get("action_messages") if isinstance(fixture.get("action_messages"), dict) else {}
		for value in action_messages.values():
			normalized = str(value or "").strip()
			if normalized:
				fixture_literals.add(normalized)

	issues: List[Tuple[Path, int, str]] = []
	for path in SMOKE_FIXTURE_INLINE_SCAN_FILES:
		if not path.exists():
			continue
		text = path.read_text(encoding="utf-8")
		for literal in sorted(fixture_literals):
			pattern = f'"{literal}"'
			offset = text.find(pattern)
			if offset == -1:
				continue
			line = _line_number_from_offset(text, offset)
			issues.append(
				(
					path,
					line,
					f'Shared smoke fixture literal "{literal}" detected inline. Use smoke fixture helpers instead.',
				)
			)
	return issues


def _check_fresh_query_interpreter_semantic_boundaries() -> List[Tuple[Path, int, str]]:
	path = FRESH_QUERY_INTERPRETER_GUARDRAIL_FILE
	if not path.exists():
		return []
	text = path.read_text(encoding="utf-8")
	issues: List[Tuple[Path, int, str]] = []
	for needle, message in FRESH_QUERY_INTERPRETER_BANNED_SUBSTRINGS.items():
		offset = text.find(needle)
		if offset == -1:
			continue
		line = _line_number_from_offset(text, offset)
		issues.append((path, line, message))
	return issues


def _check_banned_substrings(
	path: Path,
	banned_substrings: dict[str, str],
) -> List[Tuple[Path, int, str]]:
	if not path.exists():
		return []
	text = path.read_text(encoding="utf-8")
	issues: List[Tuple[Path, int, str]] = []
	for needle, message in banned_substrings.items():
		offset = text.find(needle)
		if offset == -1:
			continue
		line = _line_number_from_offset(text, offset)
		issues.append((path, line, message))
	return issues


def _check_followup_interpreter_concept_detection_scope() -> List[Tuple[Path, int, str]]:
	path = FOLLOWUP_INTERPRETER_GUARDRAIL_FILE
	if not path.exists():
		return []
	issues: List[Tuple[Path, int, str]] = []
	for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
		if "ontology_detect_concepts(" not in line:
			continue
		if "include_extended=False" in line:
			continue
		issues.append(
			(
				path,
				line_number,
				"Follow-up interpreter must not use extended ontology alias detection in runtime boundary logic.",
			)
		)
	return issues


def main() -> int:
	issues: List[Tuple[Path, int, str]] = []

	for path in _iter_python_files():
		issues.extend(_check_python_file(path))

	for path in JSON_SCAN_FILES:
		issues.extend(_check_json_file(path))

	issues.extend(_check_inline_smoke_fixture_literals())
	issues.extend(_check_fresh_query_interpreter_semantic_boundaries())
	issues.extend(_check_banned_substrings(FAMILY_ADAPTERS_GUARDRAIL_FILE, FAMILY_ADAPTERS_BANNED_SUBSTRINGS))
	issues.extend(
		_check_banned_substrings(
			GOVERNED_REPORT_EXECUTOR_GUARDRAIL_FILE,
			GOVERNED_REPORT_EXECUTOR_BANNED_SUBSTRINGS,
		)
	)
	issues.extend(
		_check_banned_substrings(
			LEGACY_RUNTIME_LANE_GUARDRAIL_FILE,
			LEGACY_RUNTIME_LANE_BANNED_SUBSTRINGS,
		)
	)
	issues.extend(
		_check_banned_substrings(
			FAMILY_TOOL_SURFACE_GUARDRAIL_FILE,
			FAMILY_TOOL_SURFACE_BANNED_SUBSTRINGS,
		)
	)
	issues.extend(
		_check_banned_substrings(
			FOLLOWUP_INTERPRETER_GUARDRAIL_FILE,
			FOLLOWUP_INTERPRETER_BANNED_SUBSTRINGS,
		)
	)
	issues.extend(_check_followup_interpreter_concept_detection_scope())

	custom_app_root = REPO_ROOT / "impl_factory/05_custom_logic/custom_app/ai_assistant_ui"
	if str(custom_app_root) not in sys.path:
		sys.path.insert(0, str(custom_app_root))
	try:
		from ai_assistant_ui.qwen_chat.semantic_resolution_registry import (
			validate_semantic_resolution_registry,
		)
		from ai_assistant_ui.qwen_chat.financial_summary_resolution_registry import (
			validate_financial_summary_resolution_registry,
		)
		from ai_assistant_ui.qwen_chat.smoke_fixture_registry import (
			validate_smoke_fixture_registry,
		)

		registry_result = validate_semantic_resolution_registry()
		for message in registry_result.errors:
			issues.append(
				(
					REPO_ROOT / "impl_factory/03_config/qwen_enterprise_metadata/semantic_resolution_registry.json",
					1,
					f"Semantic resolution registry invalid: {message}",
				)
			)
		financial_summary_registry_result = validate_financial_summary_resolution_registry()
		for message in financial_summary_registry_result.errors:
			issues.append(
				(
					REPO_ROOT / "impl_factory/03_config/qwen_enterprise_metadata/financial_summary_resolution_registry.json",
					1,
					f"Financial summary resolution registry invalid: {message}",
				)
			)
		smoke_fixture_registry_result = validate_smoke_fixture_registry()
		for message in smoke_fixture_registry_result.errors:
			issues.append(
				(
					REPO_ROOT / "impl_factory/03_config/qwen_enterprise_metadata/smoke_fixture_registry.json",
					1,
					f"Smoke fixture registry invalid: {message}",
				)
			)
	except Exception as exc:
		issues.append(
			(
				REPO_ROOT / "impl_factory/03_config/qwen_enterprise_metadata/semantic_resolution_registry.json",
				1,
				f"Semantic resolution registry validation import failed: {exc}",
			)
		)

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
