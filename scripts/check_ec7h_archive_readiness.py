#!/usr/bin/env python3
"""Check EC-7H raw trace archive readiness without writing trace data."""

from __future__ import annotations

import argparse
import grp
import json
import os
from pathlib import Path
import pwd
import stat
import sys
from typing import Any, Dict, Iterable


def _mode_to_int(value: str | int) -> int:
	if isinstance(value, int):
		return value
	return int(str(value), 8)


def _name_for_uid(uid: int) -> str:
	try:
		return pwd.getpwuid(uid).pw_name
	except KeyError:
		return str(uid)


def _name_for_gid(gid: int) -> str:
	try:
		return grp.getgrgid(gid).gr_name
	except KeyError:
		return str(gid)


def _is_relative_to(path: Path, parent: Path) -> bool:
	try:
		path.resolve().relative_to(parent.resolve())
		return True
	except ValueError:
		return False


def _is_lexically_relative_to(path: Path, parent: Path) -> bool:
	try:
		path.absolute().relative_to(parent.absolute())
		return True
	except ValueError:
		return False


def check_archive_readiness(
	*,
	path: str | Path,
	expected_owner: str | None = None,
	expected_group: str | None = None,
	max_mode: str | int = "750",
	retention_marker: str | Path | None = None,
	repo_root: str | Path | None = None,
) -> Dict[str, Any]:
	archive_path = Path(path)
	repo_root_path = Path(repo_root or Path.cwd())
	max_mode_int = _mode_to_int(max_mode)
	violations: list[str] = []

	archive_exists = archive_path.exists()
	archive_is_dir = archive_path.is_dir()
	archive_is_symlink = archive_path.is_symlink()
	if not archive_exists:
		violations.append("archive_path_missing")
	if archive_exists and not archive_is_dir:
		violations.append("archive_path_not_directory")
	if archive_is_symlink:
		violations.append("archive_path_is_symlink")

	outside_repo = not _is_relative_to(archive_path, repo_root_path)
	if not outside_repo:
		violations.append("archive_path_inside_repo")
	lexically_outside_repo = not _is_lexically_relative_to(archive_path, repo_root_path)
	if not lexically_outside_repo:
		violations.append("archive_path_lexically_inside_repo")

	owner = None
	group = None
	mode = None
	owner_ok = expected_owner is None
	group_ok = expected_group is None
	permissions_ok = False
	no_git_directory = False
	retention_marker_ok = retention_marker is None

	if archive_exists:
		stat_result = archive_path.stat()
		owner = _name_for_uid(stat_result.st_uid)
		group = _name_for_gid(stat_result.st_gid)
		mode = stat.S_IMODE(stat_result.st_mode)
		owner_ok = expected_owner is None or owner == expected_owner
		group_ok = expected_group is None or group == expected_group
		permissions_ok = (mode & ~max_mode_int) == 0
		no_git_directory = not (archive_path / ".git").exists()

		if not owner_ok:
			violations.append(f"owner_mismatch:{owner!r}")
		if not group_ok:
			violations.append(f"group_mismatch:{group!r}")
		if not permissions_ok:
			violations.append(f"permissions_too_broad:{oct(mode)}")
		if not no_git_directory:
			violations.append("archive_contains_git_directory")

		if retention_marker is not None:
			marker_path = Path(retention_marker)
			if not marker_path.is_absolute():
				marker_path = archive_path / marker_path
			retention_marker_ok = marker_path.exists() and marker_path.is_file()
			if not retention_marker_ok:
				violations.append(f"retention_marker_missing:{marker_path}")

	valid = not violations
	return {
		"runtime_effect": "none",
		"valid": valid,
		"archive_path": str(archive_path),
		"archive_exists": archive_exists,
		"archive_is_dir": archive_is_dir,
		"archive_is_symlink": archive_is_symlink,
		"outside_repo": outside_repo,
		"lexically_outside_repo": lexically_outside_repo,
		"owner": owner,
		"expected_owner": expected_owner,
		"owner_ok": owner_ok,
		"group": group,
		"expected_group": expected_group,
		"group_ok": group_ok,
		"mode": oct(mode) if mode is not None else None,
		"max_mode": oct(max_mode_int),
		"permissions_ok": permissions_ok,
		"retention_marker_ok": retention_marker_ok,
		"no_git_directory": no_git_directory,
		"violations": violations,
	}


def main(argv: Iterable[str] | None = None) -> int:
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("--path", required=True, help="External raw trace archive path to verify.")
	parser.add_argument("--expected-owner", default=None)
	parser.add_argument("--expected-group", default=None)
	parser.add_argument("--max-mode", default="750")
	parser.add_argument("--retention-marker", default=None)
	parser.add_argument("--repo-root", default=".")
	args = parser.parse_args(list(argv) if argv is not None else None)

	report = check_archive_readiness(
		path=args.path,
		expected_owner=args.expected_owner,
		expected_group=args.expected_group,
		max_mode=args.max_mode,
		retention_marker=args.retention_marker,
		repo_root=args.repo_root,
	)
	print(json.dumps(report, indent=2, sort_keys=True))
	return 0 if report["valid"] else 1


if __name__ == "__main__":
	sys.exit(main())
