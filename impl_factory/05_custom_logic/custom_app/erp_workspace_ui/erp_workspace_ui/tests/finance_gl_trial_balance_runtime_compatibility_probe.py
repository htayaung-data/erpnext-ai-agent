#!/usr/bin/python3.14
"""One-shot observation and validation probe for the disposable GL/TB stack.

Importing this module is inert: Frappe, the published runtime, the database,
the filesystem, and the network are touched only after ``main`` accepts one
of the two exact operational command lines.
"""

from __future__ import annotations

import hashlib
import hmac
import importlib
import json
import os
import re
import sys
from collections.abc import Mapping, Sequence
from importlib import metadata
from pathlib import Path
from typing import Final


_GENERIC_FAILURE: Final = "runtime_compatibility_unavailable"
_FINANCE_FAILURE: Final = "finance_read_unavailable"
_MANIFEST_SCHEMA: Final = "erpai.gl_tb.runtime_compat.execution.v1"
_OBSERVATION_SCHEMA: Final = "erpai.gl_tb.runtime_compat.observation.v1"
_VALIDATION_SCHEMA: Final = "erpai.gl_tb.runtime_compat.validation.v1"
_RUN_ID_RE: Final = re.compile(r"[0-9a-f]{12}")
_SHA256_RE: Final = re.compile(r"[0-9a-f]{64}")
_MANIFEST_PATH: Final = "/run/secrets/execution-manifest.json"
_POLICY_PATH: Final = "/run/secrets/runtime-policy.json"
_OBSERVATION_OUTPUT: Final = "/evidence/observation-result.json"
_VALIDATION_OUTPUT: Final = "/evidence/validation-result.json"
_COMMITMENT_KEY_PATH: Final = "/run/secrets/connection-commitment-key"
_STATE_SQL: Final = (
    "SELECT VERSION(), CONNECTION_ID(), @@in_transaction, "
    "@@tx_isolation, @@tx_read_only"
)
_REPLICA_KEYS: Final = (
    "read_from_replica",
    "replica_host",
    "replica_db_name",
    "replica_db_user",
    "replica_db_password",
    "different_credentials_for_replica",
)
_TOP_KEYS: Final = (
    "schema",
    "phase",
    "run_id",
    "run_root",
    "repository",
    "artifacts",
    "docker",
    "compose",
    "site",
    "secrets",
    "limits",
    "policy",
    "canaries",
    "evidence",
)
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
_POLICY_KEYS: Final = (
    "expected_driver",
    "expected_driver_version",
    "expected_server_version",
    "observation_result_sha256",
    "artifact_manifest_sha256",
    "approval_sha256",
)
_OBSERVE_CANARIES: Final = ("environment_observation",)
_VALIDATE_CANARIES: Final = (
    "normal_snapshot",
    "preexisting_transaction_rejected",
    "policy_mismatch_rejected",
    "replica_ambiguity_rejected",
    "binding_stability",
    "generic_failure_and_teardown",
)
_DRIVERS: Final = {
    (
        "frappe.database.mariadb.database",
        "pymysql.connections",
    ): ("pymysql", "PyMySQL"),
    (
        "frappe.database.mariadb.mysqlclient",
        "MySQLdb.connections",
    ): ("mysqlclient", "mysqlclient"),
}


class ProbeRejected(Exception):
    """Controlled rejection without untrusted detail."""


def _reject() -> None:
    raise ProbeRejected()


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
    except ProbeRejected:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError, ValueError):
        raise ProbeRejected() from None


def _canonical_json(value: object) -> bytes:
    try:
        body = json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8", errors="strict")
    except (TypeError, UnicodeEncodeError, ValueError):
        raise ProbeRejected() from None
    return body + b"\n"


def _closed(value: object, keys: tuple[str, ...]) -> dict[str, object]:
    if (
        type(value) is not dict
        or len(value) != len(keys)
        or frozenset(value) != frozenset(keys)
    ):
        _reject()
    return value


def _text(value: object, *, allow_empty: bool = False) -> str:
    if type(value) is not str or value != value.strip():
        _reject()
    if not allow_empty and not value:
        _reject()
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        _reject()
    return value


def _read_regular(path: str, *, maximum: int) -> bytes:
    try:
        stat_result = os.lstat(path)
        if not os.path.isfile(path) or os.path.islink(path):
            _reject()
        if stat_result.st_size <= 0 or stat_result.st_size > maximum:
            _reject()
        with open(path, "rb", buffering=0) as handle:
            body = handle.read(maximum + 1)
        if len(body) != stat_result.st_size:
            _reject()
        return body
    except ProbeRejected:
        raise
    except OSError:
        raise ProbeRejected() from None


def _load_manifest(path: str, phase: str) -> dict[str, object]:
    if path != _MANIFEST_PATH:
        _reject()
    document = _closed(_decode_json(_read_regular(path, maximum=1_048_576)), _TOP_KEYS)
    if document["schema"] != _MANIFEST_SCHEMA or document["phase"] != phase:
        _reject()
    run_id = _text(document["run_id"])
    if _RUN_ID_RE.fullmatch(run_id) is None:
        _reject()
    if document["run_root"] != f"/tmp/erpai-finance-gl-tb-runtime-compat/{run_id}":
        _reject()
    site = _closed(document["site"], _SITE_KEYS)
    if (
        site["site_name"] != f"gl-tb-rt-{run_id}.local"
        or site["database_name"] != f"gl_tb_rt_{run_id}"
        or site["database_user"] != f"gl_tb_rt_{run_id}"
        or site["db_host"] != "db-primary"
        or site["db_port"] != 3306
        or site["sites_path"] != "/home/frappe/frappe-bench/sites"
        or site["synthetic_user"] != "Guest"
        or site["synthetic_company"] != f"GL_TB_RT_{run_id.upper()}"
    ):
        _reject()
    expected_canaries = _OBSERVE_CANARIES if phase == "observe" else _VALIDATE_CANARIES
    if type(document["canaries"]) is not list or tuple(document["canaries"]) != expected_canaries:
        _reject()
    if phase == "observe" and document["policy"] is not None:
        _reject()
    if phase == "validate":
        _closed(document["policy"], _POLICY_KEYS)
    return document


def _load_policy(path: str, manifest: Mapping[str, object]) -> dict[str, str]:
    if path != _POLICY_PATH:
        _reject()
    document = _closed(_decode_json(_read_regular(path, maximum=16_384)), _POLICY_KEYS)
    manifest_policy = _closed(manifest["policy"], _POLICY_KEYS)
    if document != manifest_policy:
        _reject()
    driver = _text(document["expected_driver"])
    expected_versions = {"pymysql": "1.1.2", "mysqlclient": "2.2.7"}
    if (
        driver not in expected_versions
        or document["expected_driver_version"] != expected_versions[driver]
    ):
        _reject()
    version = _text(document["expected_driver_version"])
    server = _text(document["expected_server_version"])
    result = {
        "expected_driver": driver,
        "expected_driver_version": version,
        "expected_server_version": server,
    }
    for key in _POLICY_KEYS[3:]:
        value = _text(document[key])
        if _SHA256_RE.fullmatch(value) is None:
            _reject()
        result[key] = value
    return result


def _atomic_output(path: str, expected: str, value: object) -> None:
    if path != expected:
        _reject()
    destination = Path(path)
    if destination.parent != Path("/evidence") or destination.name != Path(expected).name:
        _reject()
    temporary = destination.with_name(f".{destination.name}.incomplete")
    descriptor: int | None = None
    try:
        descriptor = os.open(
            temporary,
            os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0),
            0o600,
        )
        body = _canonical_json(value)
        written = os.write(descriptor, body)
        if written != len(body):
            _reject()
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = None
        os.replace(temporary, destination)
    except ProbeRejected:
        raise
    except OSError:
        raise ProbeRejected() from None
    finally:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass


def _class_identity(value: object) -> tuple[str, str]:
    cls = type(value)
    return _text(cls.__module__), _text(cls.__name__)


def _local_conf_value(local: object, key: str) -> object:
    conf = getattr(local, "conf")
    if isinstance(conf, Mapping):
        return conf.get(key)
    getter = getattr(conf, "get", None)
    if callable(getter):
        return getter(key)
    return getattr(conf, key, None)


def _replica_denied(frappe: object, wrapper: object) -> bool:
    local = getattr(frappe, "local")
    if (
        wrapper is not getattr(local, "db")
        or getattr(local, "primary_db", None) is not None
        or getattr(local, "replica_db", None) is not None
    ):
        return False
    return all(_local_conf_value(local, key) in (None, "", 0, False) for key in _REPLICA_KEYS)


def _raw_one(raw: object) -> tuple[object, ...]:
    cursor: object | None = None
    try:
        cursor = getattr(raw, "cursor")()
        getattr(cursor, "execute")(_STATE_SQL)
        row = getattr(cursor, "fetchone")()
        if getattr(cursor, "fetchone")() is not None or type(row) not in (tuple, list):
            _reject()
        return tuple(row)
    except ProbeRejected:
        raise
    except Exception:
        raise ProbeRejected() from None
    finally:
        if cursor is not None:
            try:
                getattr(cursor, "close")()
            except Exception:
                pass


def _db_flag(value: object) -> int:
    if type(value) is not int or value not in (0, 1):
        _reject()
    return value


def _state(value: tuple[object, ...]) -> dict[str, object]:
    if len(value) != 5:
        _reject()
    return {
        "active": _db_flag(value[2]),
        "isolation": _text(value[3]),
        "read_only": _db_flag(value[4]),
    }


def _read_commitment_key() -> bytes:
    key = _read_regular(_COMMITMENT_KEY_PATH, maximum=4_096)
    if len(key) < 32 or b"\n" in key or b"\r" in key:
        _reject()
    return key


def _connection_commitment(connection_id: int) -> str:
    if type(connection_id) is not int or connection_id <= 0:
        _reject()
    return hmac.new(
        _read_commitment_key(),
        str(connection_id).encode("ascii"),
        hashlib.sha256,
    ).hexdigest()


def _connect_site(manifest: Mapping[str, object]) -> object:
    site = _closed(manifest["site"], _SITE_KEYS)
    frappe = importlib.import_module("frappe")
    getattr(frappe, "init")(
        site=str(site["site_name"]),
        sites_path=str(site["sites_path"]),
        force=True,
    )
    getattr(frappe, "connect")(set_admin_as_user=False)
    getattr(frappe, "set_user")("Guest")
    return frappe


def _destroy_site(frappe: object | None) -> None:
    if frappe is not None:
        try:
            getattr(frappe, "destroy")()
        except Exception:
            pass


def _driver_identity(wrapper: object, raw: object) -> tuple[str, str, str]:
    wrapper_module, wrapper_class = _class_identity(wrapper)
    raw_module, raw_class = _class_identity(raw)
    if wrapper_class != "MariaDBDatabase" or raw_class != "Connection":
        _reject()
    selected = _DRIVERS.get((wrapper_module, raw_module))
    if selected is None:
        _reject()
    driver, distribution = selected
    try:
        version = metadata.version(distribution)
    except Exception:
        raise ProbeRejected() from None
    return driver, distribution, _text(version)


def _raw_open(raw: object) -> bool:
    value = getattr(raw, "open", None)
    if type(value) is bool:
        return value
    if type(value) is int and value in (0, 1):
        return bool(value)
    _reject()


def observe(manifest: Mapping[str, object]) -> dict[str, object]:
    frappe: object | None = None
    try:
        frappe = _connect_site(manifest)
        local = getattr(frappe, "local")
        wrapper = getattr(local, "db")
        raw = getattr(wrapper, "_conn")
        if raw is None or not _replica_denied(frappe, wrapper):
            _reject()
        driver, distribution, driver_version = _driver_identity(wrapper, raw)
        state_row = _raw_one(raw)
        if len(state_row) != 5 or _db_flag(state_row[2]) != 0:
            _reject()
        return {
            "schema": _OBSERVATION_SCHEMA,
            "mode": "observe",
            "run_id": manifest["run_id"],
            "result": "pass",
            "error": "",
            "wrapper_module": _class_identity(wrapper)[0],
            "wrapper_class": _class_identity(wrapper)[1],
            "raw_module": _class_identity(raw)[0],
            "raw_class": _class_identity(raw)[1],
            "driver": driver,
            "driver_distribution": distribution,
            "driver_version": driver_version,
            "server_version": _text(state_row[0]),
            "transaction_state": _state(state_row),
            "connection_id_commitment": _connection_commitment(state_row[1]),
            "primary_route": True,
            "replica_denied": True,
            "partial_output": False,
        }
    finally:
        _destroy_site(frappe)


def _runtime_objects(frappe: object, policy: Mapping[str, str]) -> tuple[object, type[Exception]]:
    runtime_module = importlib.import_module(
        "erp_workspace_ui.finance_accounting.gl_trial_balance_frappe_runtime"
    )
    adapter_module = importlib.import_module(
        "erp_workspace_ui.finance_accounting.gl_trial_balance_adapter"
    )
    permissions = importlib.import_module("frappe.permissions")
    policy_object = getattr(runtime_module, "GLTrialBalanceRuntimePolicy")(
        expected_driver=policy["expected_driver"],
        expected_driver_version=policy["expected_driver_version"],
        expected_server_version=policy["expected_server_version"],
    )
    runtime = getattr(runtime_module, "FrappeGLTrialBalanceRuntime")(
        frappe_module=frappe,
        permissions_module=permissions,
        policy=policy_object,
    )
    return runtime, getattr(adapter_module, "GLTrialBalanceAdapterError")


def _controlled_failure(error: BaseException, expected_type: type[Exception]) -> bool:
    return (
        type(error) is expected_type
        and str(error) == _FINANCE_FAILURE
        and error.__cause__ is None
        and error.__context__ is None
    )


def _snapshot_state(snapshot: object) -> dict[str, object]:
    if (
        getattr(snapshot, "transaction_active") is not True
        or getattr(snapshot, "transaction_read_only") is not True
        or getattr(snapshot, "transaction_isolation") != "REPEATABLE READ"
        or getattr(snapshot, "consistent_snapshot") is not True
        or getattr(snapshot, "primary_connection") is not True
        or getattr(snapshot, "replica_denied") is not True
        or getattr(snapshot, "reconnect_denied") is not True
        or getattr(snapshot, "same_connection") is not True
        or getattr(snapshot, "stable") is not True
    ):
        _reject()
    return {"active": 1, "isolation": "REPEATABLE-READ", "read_only": 1}


def _validation_base(manifest: Mapping[str, object], case_id: str) -> dict[str, object]:
    return {
        "schema": _VALIDATION_SCHEMA,
        "mode": "validate",
        "run_id": manifest["run_id"],
        "case_id": case_id,
        "result": "fail",
        "error": _GENERIC_FAILURE,
        "expected_outcome": "success",
        "actual_outcome": "unexpected_failure",
        "pre_state": None,
        "active_state": None,
        "post_state": None,
        "wrapper_stable": False,
        "raw_connection_stable": False,
        "server_connection_stable": False,
        "primary_route": False,
        "replica_denied": False,
        "normal_physical_close": False,
        "exceptional_physical_close": False,
        "post_failure_frappe_calls": 0,
        "partial_output": False,
    }


def validate_case(
    manifest: Mapping[str, object], policy: Mapping[str, str], case_id: str
) -> dict[str, object]:
    if case_id not in _VALIDATE_CANARIES:
        _reject()
    result = _validation_base(manifest, case_id)
    frappe: object | None = None
    destroy_after = True
    try:
        frappe = _connect_site(manifest)
        site = _closed(manifest["site"], _SITE_KEYS)
        user = str(site["synthetic_user"])
        company = str(site["synthetic_company"])
        local = getattr(frappe, "local")
        wrapper = getattr(local, "db")
        raw = getattr(wrapper, "_conn")
        if raw is None or not _raw_open(raw) or not _replica_denied(frappe, wrapper):
            _reject()
        result["pre_state"] = {
            "active": 0,
            "isolation": "unobserved",
            "read_only": None,
        }
        result["primary_route"] = True
        result["replica_denied"] = True

        if case_id in ("normal_snapshot", "binding_stability"):
            runtime, error_type = _runtime_objects(frappe, policy)
            snapshot = getattr(runtime, "begin_read_snapshot")(user, company)
            result["active_state"] = _snapshot_state(snapshot)
            final = getattr(runtime, "final_snapshot_evidence")(snapshot)
            if final != snapshot:
                _reject()
            getattr(runtime, "close_read_snapshot")(snapshot)
            if (
                not _raw_open(raw)
                or getattr(local, "db") is not wrapper
                or getattr(wrapper, "_conn") is not raw
            ):
                _reject()
            result.update(
                result="pass",
                error="",
                expected_outcome="success",
                actual_outcome="success",
                post_state={
                    "active": 0,
                    "isolation": "unobserved",
                    "read_only": None,
                },
                wrapper_stable=True,
                raw_connection_stable=True,
                server_connection_stable=True,
                normal_physical_close=False,
            )
            del error_type
            return result

        result["expected_outcome"] = "controlled_rejection"
        destroy_after = False
        if case_id == "policy_mismatch_rejected":
            rejected_policy = dict(policy)
            rejected_policy["expected_server_version"] = (
                policy["expected_server_version"] + "-mismatch"
            )
            runtime, error_type = _runtime_objects(frappe, rejected_policy)
            call = lambda: getattr(runtime, "begin_read_snapshot")(user, company)
        else:
            if case_id == "preexisting_transaction_rejected":
                runtime_a, error_type = _runtime_objects(frappe, policy)
                first = getattr(runtime_a, "begin_read_snapshot")(user, company)
                result["active_state"] = _snapshot_state(first)
                runtime_b, second_error_type = _runtime_objects(frappe, policy)
                if second_error_type is not error_type:
                    _reject()
                call = lambda: getattr(runtime_b, "begin_read_snapshot")(user, company)
            elif case_id == "replica_ambiguity_rejected":
                runtime, error_type = _runtime_objects(frappe, policy)
                setattr(local, "replica_db", object())
                call = lambda: getattr(runtime, "begin_read_snapshot")(user, company)
            elif case_id == "generic_failure_and_teardown":
                runtime, error_type = _runtime_objects(frappe, policy)
                first = getattr(runtime, "begin_read_snapshot")(user, company)
                result["active_state"] = _snapshot_state(first)
                session = getattr(local, "session")
                if isinstance(session, Mapping):
                    session["user"] = user + ".invalid"
                else:
                    setattr(session, "user", user + ".invalid")
                call = lambda: getattr(runtime, "final_snapshot_evidence")(first)
            else:
                _reject()
        try:
            call()
        except BaseException as error:
            if not _controlled_failure(error, error_type):
                _reject()
        else:
            _reject()

        if _raw_open(raw):
            _reject()
        result["exceptional_physical_close"] = True
        result.update(
            result="pass",
            error="",
            actual_outcome="controlled_rejection",
            wrapper_stable=False,
            raw_connection_stable=False,
            server_connection_stable=False,
        )
        return result
    finally:
        if destroy_after:
            _destroy_site(frappe)


def _parse_cli(arguments: Sequence[str]) -> tuple[str, str, str | None, str | None, str]:
    values = tuple(arguments)
    if values == (
        "observe",
        "--manifest",
        _MANIFEST_PATH,
        "--output",
        _OBSERVATION_OUTPUT,
    ):
        return "observe", _MANIFEST_PATH, None, None, _OBSERVATION_OUTPUT
    if (
        len(values) == 9
        and values[:3] == ("validate", "--manifest", _MANIFEST_PATH)
        and values[3:5] == ("--policy", _POLICY_PATH)
        and values[5] == "--case"
        and values[7:] == ("--output", _VALIDATION_OUTPUT)
        and values[6] in _VALIDATE_CANARIES
    ):
        return "validate", _MANIFEST_PATH, _POLICY_PATH, values[6], _VALIDATION_OUTPUT
    _reject()


def main(argv: Sequence[str] | None = None) -> int:
    arguments = tuple(sys.argv[1:] if argv is None else argv)
    try:
        mode, manifest_path, policy_path, case_id, output_path = _parse_cli(arguments)
        manifest = _load_manifest(manifest_path, mode)
        if mode == "observe":
            value = observe(manifest)
            _atomic_output(output_path, _OBSERVATION_OUTPUT, value)
        else:
            if policy_path is None or case_id is None:
                _reject()
            policy = _load_policy(policy_path, manifest)
            value = validate_case(manifest, policy, case_id)
            _atomic_output(output_path, _VALIDATION_OUTPUT, value)
        return 0
    except ProbeRejected:
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
