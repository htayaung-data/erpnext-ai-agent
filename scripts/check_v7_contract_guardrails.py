#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path
from typing import Dict, List, Sequence, Tuple


REPO_REL_CORE = Path("impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core")
ALLOWED_ALIAS_MODULES = {
    REPO_REL_CORE / "ontology_normalization.py",
}
SCAN_DIRS = [
    REPO_REL_CORE / "v7",
    REPO_REL_CORE / "llm",
]

DISALLOWED_CONST_NAMES = {
    "_DOMAIN_KEYWORDS",
    "_INTENT_HINTS",
    "_MINIMAL_COLUMN_ALIASES",
    "GREETING_ONLY",
    "greeting_only",
    "WRITE_VERBS",
    "write_verbs",
    "CAPABILITY_CUES",
    "capability_cues",
    "SHORTHAND_FOLLOWUPS",
    "shorthand_followups",
    "CORRECTION_CUES",
    "correction_cues",
    "PER_DIM_CUES",
    "per_dim_cues",
    "PHRASE_BONUS",
    "phrase_bonus",
}

LEGACY_IMPORT_PATTERNS: Sequence[Tuple[str, str]] = (
    (r"\bai_assistant_ui\.ai_core\.v2\b", "legacy v2 import is forbidden"),
    (r"\bai_assistant_ui\.ai_core\.v3\b", "legacy v3 import is forbidden"),
    (r"\bai_assistant_ui\.ai_core\.tools\.report_qa\b", "legacy report_qa import is forbidden"),
    (r"\bai_assistant_ui\.ai_core\.v7\.engine_mode\b", "engine_mode import is forbidden"),
)


def _iter_python_files(root: Path) -> List[Path]:
    out: List[Path] = []
    for d in SCAN_DIRS:
        base = root / d
        if not base.exists():
            continue
        out.extend(sorted(p for p in base.rglob("*.py") if p.is_file()))
    return out


def _relative(root: Path, path: Path) -> Path:
    try:
        return path.relative_to(root)
    except Exception:
        return path


def _line_text(src: str, lineno: int) -> str:
    lines = src.splitlines()
    if 1 <= lineno <= len(lines):
        return lines[lineno - 1].strip()
    return ""


def _target_names(node: ast.AST) -> List[str]:
    names: List[str] = []
    if isinstance(node, ast.Name):
        names.append(node.id)
    elif isinstance(node, (ast.Tuple, ast.List)):
        for elt in node.elts:
            names.extend(_target_names(elt))
    return names


def _is_container_literal(node: ast.AST | None) -> bool:
    return isinstance(node, (ast.Dict, ast.List, ast.Tuple, ast.Set))


def _check_ast_constants(root: Path, path: Path, src: str) -> List[str]:
    rel = _relative(root, path)
    msgs: List[str] = []
    try:
        tree = ast.parse(src)
    except Exception as ex:
        return [f"{rel}:1: parse_error: {ex}"]

    # Guard only module-level constant declarations, not local variables.
    for node in list(tree.body):
        value = None
        targets: List[str] = []
        lineno = getattr(node, "lineno", 1)

        if isinstance(node, ast.Assign):
            value = node.value
            for t in node.targets:
                targets.extend(_target_names(t))
        elif isinstance(node, ast.AnnAssign):
            value = node.value
            targets.extend(_target_names(node.target))
        else:
            continue

        if not _is_container_literal(value):
            continue

        for name in targets:
            if not name:
                continue
            name_u = name.upper()
            is_constant_like = bool(name and (name == name_u or name.startswith("_")))
            if not is_constant_like:
                continue
            if name in DISALLOWED_CONST_NAMES:
                msgs.append(f"{rel}:{lineno}: banned_constant_name '{name}'")
                continue

            if "KEYWORD" in name_u or "HINT" in name_u or ("CUE" in name_u and name_u.endswith("CUES")):
                msgs.append(f"{rel}:{lineno}: banned_keyword_routing_constant '{name}'")
                continue

            if "ALIAS" in name_u:
                if rel not in ALLOWED_ALIAS_MODULES:
                    msgs.append(
                        f"{rel}:{lineno}: alias_constant_not_allowed_in_core '{name}' "
                        "(aliases allowed only in ontology_normalization module)"
                    )

    return msgs


def _check_legacy_imports(root: Path, path: Path, src: str) -> List[str]:
    rel = _relative(root, path)
    msgs: List[str] = []
    for rx, reason in LEGACY_IMPORT_PATTERNS:
        for m in re.finditer(rx, src):
            lineno = src.count("\n", 0, m.start()) + 1
            snippet = _line_text(src, lineno)
            msgs.append(f"{rel}:{lineno}: {reason}: {snippet}")
    return msgs


def _check_forbidden_paths(root: Path) -> List[str]:
    msgs: List[str] = []
    forbidden_paths = [
        REPO_REL_CORE / "v2",
        REPO_REL_CORE / "v3",
        REPO_REL_CORE / "tools" / "report_qa.py",
        REPO_REL_CORE / "v7" / "engine_mode.py",
    ]
    for p in forbidden_paths:
        abs_p = root / p
        if abs_p.exists():
            msgs.append(f"{_relative(root, abs_p)}: forbidden_legacy_path_exists")

    for p in root.rglob("*.bak"):
        msgs.append(f"{_relative(root, p)}: backup_file_forbidden")
    for p in root.rglob("*.bak.*"):
        msgs.append(f"{_relative(root, p)}: backup_file_forbidden")

    return msgs


def _check_registry_route(root: Path) -> List[str]:
    msgs: List[str] = []
    reg = root / REPO_REL_CORE / "tools" / "registry.py"
    if not reg.exists():
        msgs.append(f"{_relative(root, reg)}: registry_file_missing")
        return msgs
    src = reg.read_text(encoding="utf-8")
    required = "from ai_assistant_ui.ai_core.v7.dispatcher import dispatch_report_qa, is_report_qa_tool"
    if required not in src:
        msgs.append(f"{_relative(root, reg)}: registry_not_pinned_to_v7_dispatcher")
    return msgs


def run(root: Path) -> int:
    failures: List[str] = []

    files = _iter_python_files(root)
    for path in files:
        src = path.read_text(encoding="utf-8")
        failures.extend(_check_ast_constants(root, path, src))
        failures.extend(_check_legacy_imports(root, path, src))

    failures.extend(_check_forbidden_paths(root))
    failures.extend(_check_registry_route(root))

    if failures:
        print("V7 contract guardrails: FAILED")
        for msg in failures:
            print(f" - {msg}")
        return 1

    print("V7 contract guardrails: PASS")
    print(f"scanned_python_files={len(files)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Check v7 contract guardrails.")
    parser.add_argument("--root", default=".", help="repository root")
    args = parser.parse_args()
    return run(Path(args.root).resolve())


if __name__ == "__main__":
    sys.exit(main())
