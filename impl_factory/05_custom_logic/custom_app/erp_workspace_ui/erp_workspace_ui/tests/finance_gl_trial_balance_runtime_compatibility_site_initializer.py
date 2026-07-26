#!/usr/bin/python3.14
"""Create only the disposable Frappe site needed by the GL/TB probe.

The module is inert on import.  It deliberately installs no business app and
creates no fixture, accounting, external-service, or background-job data.
"""

from __future__ import annotations

import contextlib
import importlib
import io
import json
import os
import re
import stat
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Final


_GENERIC_FAILURE: Final = "runtime_compatibility_unavailable"
_SCHEMA: Final = "erpai.gl_tb.runtime_compat.site_init.v1"
_RUN_ID_RE: Final = re.compile(r"[0-9a-f]{12}")
_MANIFEST_PATH: Final = "/run/secrets/site-init-manifest.json"
_ROOT_PASSWORD_PATH: Final = "/run/secrets/db-root-password"
_ADMIN_PASSWORD_PATH: Final = "/run/secrets/site-admin-password"
_DB_PASSWORD_PATH: Final = "/run/secrets/site-db-password"
_TOP_KEYS: Final = ("schema", "run_id", "site", "secrets")
_SITE_KEYS: Final = (
    "site_name",
    "database_name",
    "database_user",
    "db_host",
    "db_port",
    "sites_path",
    "mariadb_user_host_scope",
    "synthetic_user",
    "synthetic_company",
)
_SECRET_KEYS: Final = (
    "db_root_password",
    "site_admin_password",
    "site_db_password",
)


class InitializerRejected(Exception):
    """Controlled rejection without source exception detail."""


class _DiscardText(io.TextIOBase):
    """Accept installer chatter without retaining credentials or unbounded text."""

    def writable(self) -> bool:
        return True

    def write(self, value: str) -> int:
        if type(value) is not str:
            _reject()
        return len(value)


def _reject() -> None:
    raise InitializerRejected()


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            _reject()
        result[key] = value
    return result


def _reject_number(_value: str) -> object:
    _reject()


def _decode_json(body: bytes) -> object:
    if type(body) is not bytes or body.startswith(b"\xef\xbb\xbf"):
        _reject()
    try:
        return json.loads(
            body.decode("utf-8", errors="strict"),
            object_pairs_hook=_unique_object,
            parse_float=_reject_number,
            parse_constant=_reject_number,
        )
    except InitializerRejected:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError, ValueError):
        raise InitializerRejected() from None


def _closed(value: object, keys: tuple[str, ...]) -> dict[str, object]:
    if (
        type(value) is not dict
        or len(value) != len(keys)
        or frozenset(value) != frozenset(keys)
    ):
        _reject()
    return value


def _read_regular(path: str, maximum: int) -> bytes:
    try:
        stat_result = os.lstat(path)
        if os.path.islink(path) or not os.path.isfile(path):
            _reject()
        if stat_result.st_size <= 0 or stat_result.st_size > maximum:
            _reject()
        with open(path, "rb", buffering=0) as handle:
            body = handle.read(maximum + 1)
        if len(body) != stat_result.st_size:
            _reject()
        return body
    except InitializerRejected:
        raise
    except OSError:
        raise InitializerRejected() from None


def _secret(path: str) -> str:
    body = _read_regular(path, 512)
    if len(body) < 32 or b"\n" in body or b"\r" in body or b"\x00" in body:
        _reject()
    try:
        value = body.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        raise InitializerRejected() from None
    if value != value.strip() or any(ord(character) < 33 for character in value):
        _reject()
    return value


def load_and_validate_manifest(path: str) -> dict[str, object]:
    """Load the sole initializer schema and reject every unknown field."""

    if path != _MANIFEST_PATH:
        _reject()
    document = _closed(_decode_json(_read_regular(path, 65_536)), _TOP_KEYS)
    if document["schema"] != _SCHEMA:
        _reject()
    run_id = document["run_id"]
    if type(run_id) is not str or _RUN_ID_RE.fullmatch(run_id) is None:
        _reject()
    site = _closed(document["site"], _SITE_KEYS)
    if (
        site["site_name"] != f"gl-tb-rt-{run_id}.local"
        or site["database_name"] != f"gl_tb_rt_{run_id}"
        or site["database_user"] != f"gl_tb_rt_{run_id}"
        or site["db_host"] != "db-primary"
        or site["db_port"] != 3306
        or site["sites_path"] != "/home/frappe/frappe-bench/sites"
        or site["mariadb_user_host_scope"] != "%"
        or site["synthetic_user"] != "Guest"
        or site["synthetic_company"] != f"GL_TB_RT_{run_id.upper()}"
    ):
        _reject()
    secrets = _closed(document["secrets"], _SECRET_KEYS)
    if (
        secrets["db_root_password"] != _ROOT_PASSWORD_PATH
        or secrets["site_admin_password"] != _ADMIN_PASSWORD_PATH
        or secrets["site_db_password"] != _DB_PASSWORD_PATH
    ):
        _reject()
    return document


def initialize(document: dict[str, object]) -> None:
    """Create one Frappe-only disposable site using the pinned initializer."""

    site = _closed(document["site"], _SITE_KEYS)
    sites_path = Path(str(site["sites_path"]))
    site_path = sites_path / str(site["site_name"])
    try:
        if (
            not sites_path.is_absolute()
            or sites_path.is_symlink()
            or not sites_path.is_dir()
            or site_path.exists()
            or site_path.is_symlink()
        ):
            _reject()
        sites_status = sites_path.stat()
        if (
            sites_status.st_uid != 1000
            or sites_status.st_gid != 1000
            or stat.S_IMODE(sites_status.st_mode) != 0o700
            or not os.access(sites_path, os.W_OK | os.X_OK)
        ):
            _reject()
        root_password = _secret(_ROOT_PASSWORD_PATH)
        admin_password = _secret(_ADMIN_PASSWORD_PATH)
        database_password = _secret(_DB_PASSWORD_PATH)
        os.chdir(sites_path)
        installer = importlib.import_module("frappe.installer")
        output = _DiscardText()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            getattr(installer, "_new_site")(
                db_name=str(site["database_name"]),
                site=str(site["site_name"]),
                db_root_username="root",
                db_root_password=root_password,
                admin_password=admin_password,
                verbose=False,
                install_apps=(),
                source_sql=None,
                force=False,
                db_password=database_password,
                db_type="mariadb",
                db_socket=None,
                db_host=str(site["db_host"]),
                db_port=int(site["db_port"]),
                db_user=str(site["database_user"]),
                setup_db=True,
                rollback_callback=None,
                mariadb_user_host_login_scope=str(site["mariadb_user_host_scope"]),
            )
        if not site_path.is_dir() or site_path.is_symlink():
            _reject()
        config_path = site_path / "site_config.json"
        if not config_path.is_file() or config_path.is_symlink():
            _reject()
    except InitializerRejected:
        raise
    except BaseException:
        raise InitializerRejected() from None


def _parse_cli(arguments: Sequence[str]) -> str:
    values = tuple(arguments)
    if values != ("initialize", "--manifest", _MANIFEST_PATH):
        _reject()
    return _MANIFEST_PATH


def main(argv: Sequence[str] | None = None) -> int:
    arguments = tuple(sys.argv[1:] if argv is None else argv)
    try:
        path = _parse_cli(arguments)
        initialize(load_and_validate_manifest(path))
        sys.stdout.write("initialized\n")
        return 0
    except InitializerRejected:
        try:
            sys.stderr.write(_GENERIC_FAILURE + "\n")
        except Exception:
            pass
        return 70
    except BaseException:
        try:
            sys.stderr.write(_GENERIC_FAILURE + "\n")
        except Exception:
            pass
        return 70


if __name__ == "__main__":
    raise SystemExit(main())
