"""Fail-closed controller for the disposable GL/TB runtime compatibility stack.

The module is intentionally inert when imported.  It uses only the Python
standard library, never selects a Docker endpoint or product policy by
default, and accepts only a closed manifest plus four explicit commands.
Real container execution remains a separate Owner-authorized action.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import selectors
import signal
import stat
import subprocess
import sys
import tarfile
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path, PurePosixPath
from typing import Final


__all__ = [
    "CommandSpec",
    "ControllerManifest",
    "ControllerRejected",
    "build_child_command_plan",
    "canonical_json_bytes",
    "load_and_validate_manifest",
    "main",
    "parse_and_validate_manifest",
    "validate_final_filesystem_observation",
    "validate_no_symlink_path",
]


_GENERIC_FAILURE: Final = "runtime_compatibility_unavailable"
_EXECUTION_SCHEMA: Final = "erpai.gl_tb.runtime_compat.execution.v3"
_ARTIFACT_SCHEMA: Final = "erpai.gl_tb.runtime_compat.artifact_provenance.v3"
_TEARDOWN_SCHEMA: Final = "erpai.gl_tb.runtime_compat.teardown.v1"
_DISCARD_SCHEMA: Final = "erpai.gl_tb.runtime_compat.discard.v1"
_BUILD_MANIFEST_SCHEMA: Final = "erpai.gl_tb.runtime_compat.build_context.v1"
_UNIX_SOCKET_PATH_MAX_BYTES: Final = 107
_RUN_ROOT_PARENT: Final = PurePosixPath(
    "/tmp/erpai-finance-gl-tb-runtime-compat"
)
_SECRET_ROOT_PARENT: Final = PurePosixPath(
    "/dev/shm/erpai-finance-gl-tb-runtime-compat"
)
_ROOTLESSKIT_RUNTIME_PARENT: Final = PurePosixPath("/run/user")
_SOURCE_CONTENT_SCHEMA: Final = "erpai.gl_tb.runtime_compat.source_content.v1"
_MATERIALIZATION_ATTESTATION_SCHEMA: Final = (
    "erpai.gl_tb.runtime_compat.materialization_attestation.v1"
)
_FINAL_FILESYSTEM_SCHEMA: Final = "erpai.gl_tb.runtime_compat.final_filesystem.v1"
_CONTENT_ARCHIVE_HARD_MAX_BYTES: Final = 134217728
_BASE_IMAGE_REFERENCE: Final = (
    "docker.io/frappe/erpnext@sha256:"
    "63e3db0e981a6e34e250635fa6f1d52cb96e10f66e6f34393c80b6fe4329c2d0"
)
_PINNED_FRAPPE_REVISION: Final = "4dfcc56090eb3101d18ddb03750391511f163fcf"
_PINNED_ERPNEXT_REVISION: Final = "d74a649016d8bb12ee3c5a24361171cebe860bfc"
_RUNNER_PYTHON: Final = "/usr/local/bin/python3.14"
_MODE_RE: Final = re.compile(r"[0-7]{4}")
_PYTHON_VERSION_RE: Final = re.compile(r"3\.14\.[0-9]+")
# Tree SHA-256 values use the verifier's canonical descendant projection: bytewise-sorted relative paths, types, file hashes, and sizes. Final ownership/modes are independently enforced during the same scan.
_CONTEXT_MEMBERS: Final = (
    ("frappe", "tree"),
    ("erpnext", "tree"),
    ("erp_workspace_ui/erp_workspace_ui/__init__.py", "regular"),
    ("erp_workspace_ui/erp_workspace_ui/finance_accounting/__init__.py", "regular"),
    ("erp_workspace_ui/erp_workspace_ui/finance_accounting/gl_trial_balance_core.py", "regular"),
    ("erp_workspace_ui/erp_workspace_ui/finance_accounting/gl_trial_balance_adapter.py", "regular"),
    ("erp_workspace_ui/erp_workspace_ui/finance_accounting/gl_trial_balance_frappe_runtime.py", "regular"),
    ("finance_gl_trial_balance_runtime_compatibility_probe.py", "regular"),
    ("finance_gl_trial_balance_runtime_compatibility_site_initializer.py", "regular"),
    ("runner-content-build-manifest.json", "regular"),
)
_FINAL_MEMBERS: Final = (
    (_RUNNER_PYTHON, "regular"),
    ("/home/frappe/frappe-bench/apps/frappe", "tree"),
    ("/home/frappe/frappe-bench/apps/erpnext", "tree"),
    ("/home/frappe/frappe-bench/apps/erp_workspace_ui/erp_workspace_ui/__init__.py", "regular"),
    ("/home/frappe/frappe-bench/apps/erp_workspace_ui/erp_workspace_ui/finance_accounting/__init__.py", "regular"),
    ("/home/frappe/frappe-bench/apps/erp_workspace_ui/erp_workspace_ui/finance_accounting/gl_trial_balance_core.py", "regular"),
    ("/home/frappe/frappe-bench/apps/erp_workspace_ui/erp_workspace_ui/finance_accounting/gl_trial_balance_adapter.py", "regular"),
    ("/home/frappe/frappe-bench/apps/erp_workspace_ui/erp_workspace_ui/finance_accounting/gl_trial_balance_frappe_runtime.py", "regular"),
    ("/opt/erpai/finance_gl_trial_balance_runtime_compatibility_probe.py", "regular"),
    ("/opt/erpai/finance_gl_trial_balance_runtime_compatibility_site_initializer.py", "regular"),
    ("/opt/erpai/runner-content-build-manifest.json", "regular"),
)
_FINAL_SCOPES: Final = (
    (
        "/home/frappe/frappe-bench/apps/erp_workspace_ui",
        (
            ("erp_workspace_ui", "directory"),
            ("erp_workspace_ui/__init__.py", "regular"),
            ("erp_workspace_ui/finance_accounting", "directory"),
            ("erp_workspace_ui/finance_accounting/__init__.py", "regular"),
            (
                "erp_workspace_ui/finance_accounting/"
                "gl_trial_balance_adapter.py",
                "regular",
            ),
            (
                "erp_workspace_ui/finance_accounting/"
                "gl_trial_balance_core.py",
                "regular",
            ),
            (
                "erp_workspace_ui/finance_accounting/"
                "gl_trial_balance_frappe_runtime.py",
                "regular",
            ),
        ),
    ),
    (
        "/opt/erpai",
        (
            ("finance_gl_trial_balance_runtime_compatibility_probe.py", "regular"),
            (
                "finance_gl_trial_balance_runtime_compatibility_"
                "site_initializer.py",
                "regular",
            ),
            ("runner-content-build-manifest.json", "regular"),
        ),
    ),
)
_FINAL_TOP_SCOPES: Final = (
    (
        "/home/frappe/frappe-bench/apps",
        (
            ("erp_workspace_ui", "directory"),
            ("erpnext", "directory"),
            ("frappe", "directory"),
        ),
    ),
)
_CONTEXT_TO_FINAL: Final = dict(zip(
    (path for path, _kind in _CONTEXT_MEMBERS),
    (path for path, _kind in _FINAL_MEMBERS[1:]),
    strict=True,
))
_FINAL_MODES: Final = {
    path: ("0555" if kind == "tree" or ("compatibility_" in path and path.endswith(".py")) else "0444")
    for path, kind in _FINAL_MEMBERS[1:]
}
_RUN_ID_RE: Final = re.compile(r"[0-9a-f]{12}")
_GIT_SHA_RE: Final = re.compile(r"[0-9a-f]{40}")
_SHA256_RE: Final = re.compile(r"[0-9a-f]{64}")
_IMAGE_ID_RE: Final = re.compile(r"sha256:[0-9a-f]{64}")
_SAFE_TEXT_RE: Final = re.compile(r"[A-Za-z0-9._+:/=@%-]+")
_COMMANDS: Final = frozenset(
    ("preflight", "observe", "validate", "recover-teardown")
)
_SERVICES: Final = ("db-primary", "redis-cache", "site-init", "runtime-probe")
_OBSERVATION_CANARIES: Final = ("environment_observation",)
_VALIDATION_CANARIES: Final = (
    "normal_snapshot",
    "preexisting_transaction_rejected",
    "policy_mismatch_rejected",
    "replica_ambiguity_rejected",
    "binding_stability",
    "generic_failure_and_teardown",
)
_EVIDENCE_FILES: Final = (
    "artifact-provenance.json",
    "observation-result.json",
    "validation-result.json",
    "discard-results.jsonl",
    "teardown-receipt.json",
    "evidence-manifest.sha256",
)
_DEFAULT_ENDPOINTS: Final = frozenset(
    (
        "unix:///var/run/docker.sock",
        "unix:///run/docker.sock",
        "npipe:////./pipe/docker_engine",
    )
)
_ENGINE_FORMAT: Final = (
    "{{.Client.Version}}\\t{{.Client.APIVersion}}\\t"
    "{{.Server.Version}}\\t{{.Server.APIVersion}}\\t"
    "{{.Server.Os}}\\t{{.Server.Arch}}"
)
_ENGINE_INFO_FORMAT: Final = (
    "{{.ID}}\\t{{.Name}}\\t{{.DockerRootDir}}\\t"
    "{{json .SecurityOptions}}\\t{{.CgroupDriver}}\\t{{.CgroupVersion}}"
)
_IMAGE_FORMAT: Final = (
    "{{.Id}}\\t{{json .RepoDigests}}\\t{{.Os}}\\t{{.Architecture}}\\t"
    "{{json .Config.Volumes}}\\t{{json .Config}}"
)
_CONTAINER_FORMAT: Final = (
    "{{.Id}}\\t{{.Image}}\\t{{.Name}}\\t{{.State.Status}}\\t"
    "{{.State.Running}}\\t{{.State.ExitCode}}\\t{{.State.OOMKilled}}\\t"
    "{{.HostConfig.NetworkMode}}\\t{{.HostConfig.Privileged}}\\t"
    "{{.Config.User}}\\t{{.HostConfig.ReadonlyRootfs}}\\t"
    "{{json .HostConfig.CapDrop}}\\t{{json .HostConfig.SecurityOpt}}\\t"
    "{{json .Config.Entrypoint}}\\t{{json .Config.Cmd}}\\t"
    "{{range .Mounts}}{{.Type}}={{.Destination}},{{end}}\\t"
    "{{index .Config.Labels \"com.erpai.finance.gl_tb_rtcompat.run\"}}\\t"
    "{{index .Config.Labels \"com.docker.compose.project\"}}\\t"
    "{{index .Config.Labels \"com.docker.compose.service\"}}"
)
_NETWORK_FORMAT: Final = (
    "{{.Id}}\\t{{.Name}}\\t{{.Driver}}\\t{{.Internal}}\\t"
    "{{index .Labels \"com.erpai.finance.gl_tb_rtcompat.run\"}}\\t"
    "{{index .Labels \"com.docker.compose.project\"}}"
)
_VOLUME_FORMAT: Final = (
    "{{.Name}}\\t{{.Driver}}\\t{{.Scope}}\\t"
    "{{index .Labels \"com.erpai.finance.gl_tb_rtcompat.run\"}}\\t"
    "{{index .Labels \"com.docker.compose.project\"}}"
)
_CONTAINER_LIST_FORMAT: Final = (
    "{{.ID}}\\t{{.Names}}\\t"
    "{{.Label \"com.erpai.finance.gl_tb_rtcompat.run\"}}\\t"
    "{{.Label \"com.docker.compose.project\"}}\\t"
    "{{.Label \"com.docker.compose.service\"}}"
)
_NETWORK_LIST_FORMAT: Final = (
    "{{.ID}}\\t{{.Name}}\\t{{.Driver}}\\t"
    "{{.Label \"com.erpai.finance.gl_tb_rtcompat.run\"}}\\t"
    "{{.Label \"com.docker.compose.project\"}}"
)
_VOLUME_LIST_FORMAT: Final = (
    "{{.Name}}\\t{{.Driver}}\\t{{.Scope}}\\t"
    "{{.Label \"com.erpai.finance.gl_tb_rtcompat.run\"}}\\t"
    "{{.Label \"com.docker.compose.project\"}}"
)
_IMAGE_VOLUME_DESTINATIONS: Final = {
    "base_image": frozenset(("/home/frappe/frappe-bench/sites",)),
    "runner_image": frozenset(("/home/frappe/frappe-bench/sites",)),
    "mariadb_image": frozenset(("/var/lib/mysql",)),
    "redis_image": frozenset(("/data",)),
}


class ControllerRejected(Exception):
    """Controlled manifest, evidence, or containment rejection."""


class _ControllerInternal(Exception):
    """Controller invariant failure without untrusted exception text."""


def _reject() -> None:
    raise ControllerRejected()


def _internal() -> None:
    raise _ControllerInternal()


def _closed_object(value: object, keys: tuple[str, ...]) -> dict[str, object]:
    if (
        type(value) is not dict
        or len(value) != len(keys)
        or frozenset(value) != frozenset(keys)
    ):
        _reject()
    return value


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            _reject()
        result[key] = value
    return result


def _reject_float(_value: str) -> object:
    _reject()


def _reject_constant(_value: str) -> object:
    _reject()


def _decode_json(body: bytes) -> object:
    if type(body) is not bytes or body.startswith(b"\xef\xbb\xbf"):
        _reject()
    try:
        text = body.decode("utf-8", errors="strict")
        return json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_float=_reject_float,
            parse_constant=_reject_constant,
        )
    except ControllerRejected:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError, ValueError):
        raise ControllerRejected() from None


def canonical_json_bytes(value: object) -> bytes:
    """Return the sole retained JSON encoding: UTF-8, sorted, compact, final LF."""

    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8", errors="strict")
    except (TypeError, UnicodeEncodeError, ValueError):
        raise ControllerRejected() from None
    return encoded + b"\n"


def _text(value: object, *, pattern: re.Pattern[str] | None = None) -> str:
    if type(value) is not str or not value or value != value.strip():
        _reject()
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        _reject()
    if pattern is not None and pattern.fullmatch(value) is None:
        _reject()
    return value


def _sha256(value: object) -> str:
    return _text(value, pattern=_SHA256_RE)


def _concrete_sha256(value: object) -> str:
    digest = _sha256(value)
    if len(set(digest)) == 1:
        _reject()
    return digest


def _image_id(value: object) -> str:
    identity = _text(value, pattern=_IMAGE_ID_RE)
    _concrete_sha256(identity.removeprefix("sha256:"))
    return identity


def _positive_int(value: object) -> int:
    if type(value) is not int or value <= 0:
        _reject()
    return value


def _nonnegative_int(value: object) -> int:
    if type(value) is not int or value < 0:
        _reject()
    return value


def _mode(value: object) -> str:
    return _text(value, pattern=_MODE_RE)


def _inventory_entries(
    value: object,
    expected: tuple[tuple[str, str], ...],
) -> tuple[dict[str, object], ...]:
    if type(value) is not list or len(value) != len(expected):
        _reject()
    entries: list[dict[str, object]] = []
    seen: set[str] = set()
    folded: set[str] = set()
    for raw, (expected_path, expected_type) in zip(value, expected, strict=True):
        entry = _closed_object(
            raw, ("path", "type", "sha256", "size_bytes", "uid", "gid", "mode")
        )
        path = _text(entry["path"])
        kind = _text(entry["type"])
        if path != expected_path or kind != expected_type:
            _reject()
        if path in seen or path.casefold() in folded:
            _reject()
        seen.add(path)
        folded.add(path.casefold())
        size = _nonnegative_int(entry["size_bytes"])
        if kind == "tree" and size == 0:
            _reject()
        entries.append({
            "path": path,
            "type": kind,
            "sha256": _concrete_sha256(entry["sha256"]),
            "size_bytes": size,
            "uid": _nonnegative_int(entry["uid"]),
            "gid": _nonnegative_int(entry["gid"]),
            "mode": _mode(entry["mode"]),
        })
    return tuple(entries)


def _inventory_sha256(entries: Sequence[Mapping[str, object]]) -> str:
    return hashlib.sha256(canonical_json_bytes(list(entries))).hexdigest()


def _rootlesskit_runtime_dir(run_id: str, uid: int) -> str:
    if _RUN_ID_RE.fullmatch(run_id) is None or type(uid) is not int or uid < 0:
        _reject()
    result = str(_ROOTLESSKIT_RUNTIME_PARENT / str(uid) / f"gtb-{run_id}")
    if len(result.encode("utf-8")) > 48:
        _reject()
    return result


def _expected_final_filesystem_document(
    source_content: Mapping[str, object],
) -> dict[str, object]:
    python = dict(source_content["python"])
    context = {
        str(entry["path"]): entry
        for entry in source_content["build_context"]["entries"]
    }
    entries: list[dict[str, object]] = [{
        "path": python["path"],
        "type": "regular",
        "sha256": python["executable_sha256"],
        "size_bytes": python["size_bytes"],
        "uid": python["uid"],
        "gid": python["gid"],
        "mode": python["mode"],
    }]
    for context_path, final_path in _CONTEXT_TO_FINAL.items():
        source = context[context_path]
        entries.append({
            "path": final_path,
            "type": source["type"],
            "sha256": source["sha256"],
            "size_bytes": source["size_bytes"],
            "uid": 1000,
            "gid": 1000,
            "mode": _FINAL_MODES[final_path],
        })
    return {
        "schema": _FINAL_FILESYSTEM_SCHEMA,
        "python": python,
        "entries": entries,
    }


def _exact_sequence(value: object, expected: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not list or tuple(value) != expected:
        _reject()
    return expected


def _strict_absolute_path(value: object) -> PurePosixPath:
    text = _text(value)
    path = PurePosixPath(text)
    if (
        not path.is_absolute()
        or str(path) != text
        or ".." in path.parts
        or "." in path.parts
        or "//" in text
    ):
        _reject()
    return path


def _require_under(path: PurePosixPath, root: PurePosixPath) -> None:
    try:
        path.relative_to(root)
    except ValueError:
        _reject()


def _immutable_image(value: object) -> str:
    image = _text(value)
    if image != image.lower() or image.count("@sha256:") != 1:
        _reject()
    repository, digest = image.split("@sha256:", 1)
    if (
        not repository
        or "/" not in repository
        or ":" in repository.rsplit("/", 1)[-1]
        or _SHA256_RE.fullmatch(digest) is None
        or _SAFE_TEXT_RE.fullmatch(repository) is None
    ):
        _reject()
    _concrete_sha256(digest)
    return image


def _docker_endpoint(value: object, run_root: PurePosixPath) -> str:
    endpoint = _text(value)
    if endpoint in _DEFAULT_ENDPOINTS or not endpoint.startswith("unix://"):
        _reject()
    socket_path = _strict_absolute_path(endpoint.removeprefix("unix://"))
    expected = run_root / "docker" / "docker.sock"
    if (
        socket_path != expected
        or len(str(socket_path).encode("utf-8")) > _UNIX_SOCKET_PATH_MAX_BYTES
    ):
        _reject()
    return endpoint


def validate_no_symlink_path(
    path: str,
    root: str,
    *,
    allow_missing_leaf: bool = False,
    lstat: Callable[[str], os.stat_result] = os.lstat,
) -> None:
    """Reject traversal, symlinks, and non-directory ancestors.

    ``lstat`` is injectable so isolated tests need no filesystem mutation.
    """

    candidate = _strict_absolute_path(path)
    boundary = _strict_absolute_path(root)
    _require_under(candidate, boundary)
    current = PurePosixPath("/")
    for index, component in enumerate(candidate.parts[1:]):
        current /= component
        is_leaf = index == len(candidate.parts[1:]) - 1
        try:
            status = lstat(str(current))
        except FileNotFoundError:
            if is_leaf and allow_missing_leaf:
                return
            _reject()
        except OSError:
            _reject()
        if stat.S_ISLNK(status.st_mode):
            _reject()
        if not is_leaf and not stat.S_ISDIR(status.st_mode):
            _reject()


@dataclass(frozen=True, slots=True)
class CommandSpec:
    name: str
    argv: tuple[str, ...]
    timeout_seconds: int
    stdout_max_bytes: int
    stderr_max_bytes: int


@dataclass(frozen=True, slots=True)
class ControllerManifest:
    phase: str
    run_id: str
    run_root: str
    repository: Mapping[str, str]
    artifacts: Mapping[str, str]
    docker: Mapping[str, str]
    source_content: Mapping[str, object]
    compose: Mapping[str, object]
    site: Mapping[str, object]
    secrets: Mapping[str, object]
    limits: Mapping[str, int]
    policy: Mapping[str, str] | None
    canaries: tuple[str, ...]
    evidence: Mapping[str, object]
    raw: Mapping[str, object]

    @property
    def project(self) -> str:
        return str(self.compose["project"])

    @property
    def run_label(self) -> str:
        return str(self.compose["run_label"])

    @property
    def docker_prefix(self) -> tuple[str, ...]:
        return (
            str(self.docker["executable"]),
            "--host",
            str(self.docker["endpoint"]),
        )

    @property
    def compose_prefix(self) -> tuple[str, ...]:
        return self.docker_prefix + (
            "compose",
            "--project-directory",
            self.run_root,
            "--project-name",
            self.project,
            "--file",
            str(self.compose["file"]),
        )


_TOP_KEYS: Final = (
    "schema",
    "phase",
    "run_id",
    "run_root",
    "repository",
    "artifacts",
    "docker",
    "source_content",
    "compose",
    "site",
    "secrets",
    "limits",
    "policy",
    "canaries",
    "evidence",
)
_REPOSITORY_KEYS: Final = (
    "revision",
    "controller_sha256",
    "probe_sha256",
    "initializer_sha256",
    "dockerfile_sha256",
    "compose_sha256",
    "package_initializer_sha256",
    "finance_initializer_sha256",
    "core_sha256",
    "adapter_sha256",
    "runtime_sha256",
    "frappe_tree_sha256",
    "erpnext_tree_sha256",
    "source_content_sha256",
)
_ARTIFACT_KEYS: Final = (
    "base_image",
    "base_image_id",
    "runner_image",
    "runner_image_id",
    "mariadb_image",
    "mariadb_image_id",
    "redis_image",
    "redis_image_id",
)
_DOCKER_KEYS: Final = (
    "executable",
    "executable_sha256",
    "endpoint",
    "compose_version",
    "client_version",
    "client_api_version",
    "server_version",
    "server_api_version",
    "daemon_id",
    "daemon_name",
    "docker_root_dir",
    "security_options_sha256",
    "daemon_lifecycle_owner",
    "buildkit_version",
    "frontend_capabilities_sha256",
    "rootlesskit_runtime_dir",
    "cgroup_driver",
    "cgroup_version",
    "cgroup_authority",
    "os",
    "architecture",
)
_COMPOSE_KEYS: Final = (
    "file",
    "project",
    "run_label",
    "services",
    "network",
    "volumes",
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
_SECRET_KEYS: Final = (
    "directory",
    "db_root_password",
    "site_admin_password",
    "site_db_password",
    "connection_commitment_key",
    "runtime_policy",
)
_LIMIT_KEYS: Final = (
    "setup_timeout_seconds",
    "command_timeout_seconds",
    "teardown_timeout_seconds",
    "healthcheck_interval_seconds",
    "healthcheck_timeout_seconds",
    "healthcheck_retries",
    "stdout_max_bytes",
    "stderr_max_bytes",
    "evidence_max_bytes",
)
_POLICY_KEYS: Final = (
    "expected_driver",
    "expected_driver_version",
    "expected_server_version",
    "observation_result_sha256",
    "artifact_manifest_sha256",
    "approval_sha256",
)
_EVIDENCE_KEYS: Final = (
    "directory",
    "staging_directory",
    "files",
)



_SOURCE_CONTENT_KEYS: Final = (
    "schema", "source_repository_revision", "base", "frontend", "sources",
    "python", "build_context", "gl_tb",
)
_BASE_KEYS: Final = ("reference", "image_id")
_FRONTEND_KEYS: Final = (
    "policy", "dockerfile_sha256", "engine_version", "engine_api_version",
    "buildkit_version", "frontend_capabilities_sha256",
)
_SOURCES_KEYS: Final = ("frappe", "erpnext")
_SOURCE_KEYS: Final = ("revision", "tree_sha256")
_PYTHON_KEYS: Final = (
    "path", "version", "executable_sha256", "size_bytes", "uid", "gid", "mode",
)
_INVENTORY_KEYS: Final = ("entries", "manifest_sha256", "build_manifest")
_FINAL_INVENTORY_KEYS: Final = ("entries", "manifest_sha256")
_BUILD_MANIFEST_KEYS: Final = (
    "schema", "source_repository_revision", "frappe_revision",
    "erpnext_revision", "entries", "entries_sha256",
)
_GL_TB_KEYS: Final = (
    "package_initializer_sha256", "finance_initializer_sha256", "core_sha256",
    "adapter_sha256", "runtime_sha256", "probe_sha256", "initializer_sha256",
    "build_manifest_sha256",
)
_FINAL_IMAGE_KEYS: Final = (
    "image_id", "repository_digest", "os", "platform", "architecture",
)
_IMAGE_CONFIGURATION_KEYS: Final = (
    "base_config_sha256", "config_sha256", "user", "working_directory",
    "entrypoint", "cmd", "environment_sha256", "volume_destinations",
)
_VERIFICATION_CONTAINMENT_KEYS: Final = (
    "network_mode", "privileged", "read_only_rootfs", "user", "cap_drop",
    "security_options", "tmpfs_destinations", "container_started",
    "verification_container_retired",
)
_MATERIALIZATION_KEYS: Final = (
    "schema", "source_content_sha256", "final_image", "python",
    "final_filesystem", "image_configuration", "verification_containment",
)


def _validate_source_content(
    value: object,
    repository: Mapping[str, object],
    artifacts: Mapping[str, object],
    docker: Mapping[str, object],
) -> dict[str, object]:
    source_content = _closed_object(value, _SOURCE_CONTENT_KEYS)
    if (
        source_content["schema"] != _SOURCE_CONTENT_SCHEMA
        or source_content["source_repository_revision"] != repository["revision"]
    ):
        _reject()

    base = _closed_object(source_content["base"], _BASE_KEYS)
    if (
        base["reference"] != _BASE_IMAGE_REFERENCE
        or base["reference"] != artifacts["base_image"]
        or base["image_id"] != artifacts["base_image_id"]
    ):
        _reject()
    _image_id(base["image_id"])

    frontend = _closed_object(source_content["frontend"], _FRONTEND_KEYS)
    if (
        frontend["policy"] != "engine_builtin"
        or frontend["dockerfile_sha256"] != repository["dockerfile_sha256"]
        or frontend["engine_version"] != docker["server_version"]
        or frontend["engine_api_version"] != docker["server_api_version"]
        or frontend["buildkit_version"] != docker["buildkit_version"]
        or frontend["frontend_capabilities_sha256"]
        != docker["frontend_capabilities_sha256"]
    ):
        _reject()
    _concrete_sha256(frontend["dockerfile_sha256"])
    _concrete_sha256(frontend["frontend_capabilities_sha256"])

    sources = _closed_object(source_content["sources"], _SOURCES_KEYS)
    frappe = _closed_object(sources["frappe"], _SOURCE_KEYS)
    erpnext = _closed_object(sources["erpnext"], _SOURCE_KEYS)
    if (
        frappe["revision"] != _PINNED_FRAPPE_REVISION
        or erpnext["revision"] != _PINNED_ERPNEXT_REVISION
        or frappe["tree_sha256"] != repository["frappe_tree_sha256"]
        or erpnext["tree_sha256"] != repository["erpnext_tree_sha256"]
    ):
        _reject()
    _concrete_sha256(frappe["tree_sha256"])
    _concrete_sha256(erpnext["tree_sha256"])

    python = _closed_object(source_content["python"], _PYTHON_KEYS)
    if python["path"] != _RUNNER_PYTHON:
        _reject()
    _text(python["version"], pattern=_PYTHON_VERSION_RE)
    normalized_python = {
        "path": _RUNNER_PYTHON,
        "version": str(python["version"]),
        "executable_sha256": _concrete_sha256(python["executable_sha256"]),
        "size_bytes": _positive_int(python["size_bytes"]),
        "uid": _nonnegative_int(python["uid"]),
        "gid": _nonnegative_int(python["gid"]),
        "mode": _mode(python["mode"]),
    }
    if (
        normalized_python["uid"] != 0
        or normalized_python["gid"] != 0
        or normalized_python["mode"] != "0755"
    ):
        _reject()

    build_context = _closed_object(source_content["build_context"], _INVENTORY_KEYS)
    context_entries = _inventory_entries(build_context["entries"], _CONTEXT_MEMBERS)
    if build_context["manifest_sha256"] != _inventory_sha256(context_entries):
        _reject()
    if (
        frappe["tree_sha256"] != context_entries[0]["sha256"]
        or erpnext["tree_sha256"] != context_entries[1]["sha256"]
    ):
        _reject()

    build_manifest_raw = _closed_object(
        build_context["build_manifest"], _BUILD_MANIFEST_KEYS
    )
    build_manifest_entries = _inventory_entries(
        build_manifest_raw["entries"], _CONTEXT_MEMBERS[:-1]
    )
    normalized_build_manifest = {
        "schema": _BUILD_MANIFEST_SCHEMA,
        "source_repository_revision": str(
            build_manifest_raw["source_repository_revision"]
        ),
        "frappe_revision": str(build_manifest_raw["frappe_revision"]),
        "erpnext_revision": str(build_manifest_raw["erpnext_revision"]),
        "entries": list(build_manifest_entries),
        "entries_sha256": _concrete_sha256(build_manifest_raw["entries_sha256"]),
    }
    if (
        build_manifest_raw["schema"] != _BUILD_MANIFEST_SCHEMA
        or normalized_build_manifest["source_repository_revision"]
        != repository["revision"]
        or normalized_build_manifest["frappe_revision"]
        != _PINNED_FRAPPE_REVISION
        or normalized_build_manifest["erpnext_revision"]
        != _PINNED_ERPNEXT_REVISION
        or tuple(build_manifest_entries) != tuple(context_entries[:-1])
        or normalized_build_manifest["entries_sha256"]
        != _inventory_sha256(build_manifest_entries)
    ):
        _reject()
    build_manifest_body = canonical_json_bytes(normalized_build_manifest)
    build_manifest_entry = context_entries[-1]
    if (
        build_manifest_entry["sha256"]
        != hashlib.sha256(build_manifest_body).hexdigest()
        or build_manifest_entry["size_bytes"] != len(build_manifest_body)
    ):
        _reject()

    context_by_path = {entry["path"]: entry for entry in context_entries}

    gl_tb = _closed_object(source_content["gl_tb"], _GL_TB_KEYS)
    gl_paths = {
        "package_initializer_sha256": "erp_workspace_ui/erp_workspace_ui/__init__.py",
        "finance_initializer_sha256": "erp_workspace_ui/erp_workspace_ui/finance_accounting/__init__.py",
        "core_sha256": "erp_workspace_ui/erp_workspace_ui/finance_accounting/gl_trial_balance_core.py",
        "adapter_sha256": "erp_workspace_ui/erp_workspace_ui/finance_accounting/gl_trial_balance_adapter.py",
        "runtime_sha256": "erp_workspace_ui/erp_workspace_ui/finance_accounting/gl_trial_balance_frappe_runtime.py",
        "probe_sha256": "finance_gl_trial_balance_runtime_compatibility_probe.py",
        "initializer_sha256": "finance_gl_trial_balance_runtime_compatibility_site_initializer.py",
        "build_manifest_sha256": "runner-content-build-manifest.json",
    }
    repository_gl_keys = {
        "package_initializer_sha256": "package_initializer_sha256",
        "finance_initializer_sha256": "finance_initializer_sha256",
        "core_sha256": "core_sha256",
        "adapter_sha256": "adapter_sha256",
        "runtime_sha256": "runtime_sha256",
        "probe_sha256": "probe_sha256",
        "initializer_sha256": "initializer_sha256",
    }
    for key, path in gl_paths.items():
        value = _concrete_sha256(gl_tb[key])
        if value != context_by_path[path]["sha256"]:
            _reject()
        repository_key = repository_gl_keys.get(key)
        if repository_key is not None and value != repository[repository_key]:
            _reject()
    if gl_tb["build_manifest_sha256"] != build_manifest_entry["sha256"]:
        _reject()

    normalized = {
        "schema": _SOURCE_CONTENT_SCHEMA,
        "source_repository_revision": str(source_content["source_repository_revision"]),
        "base": dict(base),
        "frontend": dict(frontend),
        "sources": {"frappe": dict(frappe), "erpnext": dict(erpnext)},
        "python": normalized_python,
        "build_context": {
            "entries": list(context_entries),
            "manifest_sha256": str(build_context["manifest_sha256"]),
            "build_manifest": normalized_build_manifest,
        },
        "gl_tb": dict(gl_tb),
    }
    if repository["source_content_sha256"] != hashlib.sha256(
        canonical_json_bytes(normalized)
    ).hexdigest():
        _reject()
    return normalized


def validate_final_filesystem_observation(
    manifest: ControllerManifest,
    body: bytes,
) -> dict[str, object]:
    document = _closed_object(
        _decode_json(body), ("schema", "python", "entries")
    )
    if document["schema"] != _FINAL_FILESYSTEM_SCHEMA:
        _reject()
    python = _closed_object(document["python"], _PYTHON_KEYS)
    normalized_python = {
        "path": _text(python["path"]),
        "version": _text(python["version"]),
        "executable_sha256": _concrete_sha256(python["executable_sha256"]),
        "size_bytes": _positive_int(python["size_bytes"]),
        "uid": _nonnegative_int(python["uid"]),
        "gid": _nonnegative_int(python["gid"]),
        "mode": _mode(python["mode"]),
    }
    entries = _inventory_entries(document["entries"], _FINAL_MEMBERS)
    normalized = {
        "schema": _FINAL_FILESYSTEM_SCHEMA,
        "python": normalized_python,
        "entries": list(entries),
    }
    expected = _expected_final_filesystem_document(manifest.source_content)
    if normalized != expected:
        _reject()
    normalized["manifest_sha256"] = _inventory_sha256(entries)
    return normalized


def parse_and_validate_manifest(body: bytes) -> ControllerManifest:
    document = _closed_object(_decode_json(body), _TOP_KEYS)
    if document["schema"] != _EXECUTION_SCHEMA:
        _reject()
    phase = _text(document["phase"])
    if phase not in ("observe", "validate"):
        _reject()
    run_id = _text(document["run_id"], pattern=_RUN_ID_RE)
    expected_root = _RUN_ROOT_PARENT / run_id
    run_root = _strict_absolute_path(document["run_root"])
    if run_root != expected_root:
        _reject()

    repository = _closed_object(document["repository"], _REPOSITORY_KEYS)
    _text(repository["revision"], pattern=_GIT_SHA_RE)
    for key in _REPOSITORY_KEYS[1:]:
        _concrete_sha256(repository[key])

    artifacts = _closed_object(document["artifacts"], _ARTIFACT_KEYS)
    if artifacts["base_image"] != _BASE_IMAGE_REFERENCE:
        _reject()
    for key in ("base_image", "runner_image", "mariadb_image", "redis_image"):
        _immutable_image(artifacts[key])
    for key in (
        "base_image_id", "runner_image_id", "mariadb_image_id", "redis_image_id"
    ):
        _image_id(artifacts[key])
    source_digest = str(repository["source_content_sha256"])
    runner_digests = {
        str(artifacts["runner_image_id"]).removeprefix("sha256:"),
        str(artifacts["runner_image"]).rsplit("@sha256:", 1)[-1],
    }
    if source_digest in runner_digests:
        _reject()

    docker = _closed_object(document["docker"], _DOCKER_KEYS)
    executable = _strict_absolute_path(docker["executable"])
    if executable.name != "docker":
        _reject()
    _sha256(docker["executable_sha256"])
    _docker_endpoint(docker["endpoint"], run_root)
    for key in (
        "compose_version", "client_version", "client_api_version",
        "server_version", "server_api_version", "buildkit_version",
        "daemon_id", "daemon_name",
    ):
        _text(docker[key], pattern=_SAFE_TEXT_RE)
    _concrete_sha256(docker["frontend_capabilities_sha256"])
    _concrete_sha256(docker["security_options_sha256"])
    if (
        docker["daemon_lifecycle_owner"]
        != "external_materialization_controller"
        or docker["daemon_name"] != f"gl_tb_rtcompat_{run_id}_rootless"
        or _strict_absolute_path(docker["docker_root_dir"])
        != run_root / "docker" / "data-root"
    ):
        _reject()
    try:
        effective_uid = os.geteuid()
    except (AttributeError, OSError):
        _reject()
    if docker["rootlesskit_runtime_dir"] != _rootlesskit_runtime_dir(run_id, effective_uid):
        _reject()
    if docker["cgroup_version"] != "2":
        _reject()
    cgroup_driver = _text(docker["cgroup_driver"])
    cgroup_authority = _text(docker["cgroup_authority"])
    if phase == "observe" and cgroup_driver == "none":
        if cgroup_authority != "compatibility_observation_only":
            _reject()
    elif (
        cgroup_driver not in ("systemd", "cgroupfs")
        or cgroup_authority != "delegated_cgroup_v2"
    ):
        _reject()
    if docker["os"] != "linux" or docker["architecture"] != "amd64":
        _reject()

    source_content = _validate_source_content(
        document["source_content"], repository, artifacts, docker
    )

    project = f"gl_tb_rtcompat_{run_id}"
    run_label = f"com.erpai.finance.gl_tb_rtcompat.run={run_id}"
    compose = _closed_object(document["compose"], _COMPOSE_KEYS)
    if (
        _strict_absolute_path(compose["file"]) != run_root / "compose.yaml"
        or compose["project"] != project
        or compose["run_label"] != run_label
        or compose["network"] != f"{project}_internal"
    ):
        _reject()
    _exact_sequence(compose["services"], _SERVICES)
    expected_volumes = (
        f"{project}_db",
        f"{project}_sites",
        f"{project}_redis",
    )
    _exact_sequence(compose["volumes"], expected_volumes)

    site = _closed_object(document["site"], _SITE_KEYS)
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
    secrets = _closed_object(document["secrets"], _SECRET_KEYS)
    secret_root = _strict_absolute_path(secrets["directory"])
    if secret_root != _SECRET_ROOT_PARENT / run_id:
        _reject()
    secret_names = (
        ("db_root_password", "db-root-password"),
        ("site_admin_password", "site-admin-password"),
        ("site_db_password", "site-db-password"),
        ("connection_commitment_key", "connection-commitment-key"),
    )
    for key, basename in secret_names:
        if _strict_absolute_path(secrets[key]) != secret_root / basename:
            _reject()
    policy_path = secrets["runtime_policy"]
    if _strict_absolute_path(policy_path) != secret_root / "runtime-policy.json":
        _reject()
    if phase == "observe":
        if document["policy"] is not None:
            _reject()
        policy = None
    else:
        policy_object = _closed_object(document["policy"], _POLICY_KEYS)
        expected_versions = {"pymysql": "1.1.2", "mysqlclient": "2.2.7"}
        if (
            policy_object["expected_driver"] not in expected_versions
            or policy_object["expected_driver_version"]
            != expected_versions[policy_object["expected_driver"]]
        ):
            _reject()
        for key in _POLICY_KEYS[:3]:
            _text(policy_object[key])
        for key in _POLICY_KEYS[3:]:
            _sha256(policy_object[key])
        policy = {key: str(policy_object[key]) for key in _POLICY_KEYS}

    limits_object = _closed_object(document["limits"], _LIMIT_KEYS)
    limits = {key: _positive_int(limits_object[key]) for key in _LIMIT_KEYS}

    expected_canaries = (
        _OBSERVATION_CANARIES if phase == "observe" else _VALIDATION_CANARIES
    )
    canaries = _exact_sequence(document["canaries"], expected_canaries)

    evidence = _closed_object(document["evidence"], _EVIDENCE_KEYS)
    if (
        _strict_absolute_path(evidence["directory"]) != run_root / "evidence"
        or _strict_absolute_path(evidence["staging_directory"])
        != run_root / "staging"
    ):
        _reject()
    _exact_sequence(evidence["files"], _EVIDENCE_FILES)

    return ControllerManifest(
        phase=phase,
        run_id=run_id,
        run_root=str(run_root),
        repository={key: str(repository[key]) for key in _REPOSITORY_KEYS},
        artifacts={key: str(artifacts[key]) for key in _ARTIFACT_KEYS},
        docker={key: str(docker[key]) for key in _DOCKER_KEYS},
        source_content=source_content,
        compose=dict(compose),
        site=dict(site),
        secrets=dict(secrets),
        limits=limits,
        policy=policy,
        canaries=canaries,
        evidence=dict(evidence),
        raw=document,
    )


def load_and_validate_manifest(path: str) -> ControllerManifest:
    manifest_path = _strict_absolute_path(path)
    if manifest_path.name != "execution-manifest.json":
        _reject()
    try:
        status = os.lstat(str(manifest_path))
        if not stat.S_ISREG(status.st_mode) or status.st_nlink != 1:
            _reject()
        with open(manifest_path, "rb", buffering=0) as stream:
            body = stream.read()
    except ControllerRejected:
        raise
    except OSError:
        raise ControllerRejected() from None
    manifest = parse_and_validate_manifest(body)
    expected = PurePosixPath(manifest.run_root) / "execution-manifest.json"
    if manifest_path != expected:
        _reject()
    validate_no_symlink_path(str(manifest_path), manifest.run_root)
    return manifest


def _spec(
    manifest: ControllerManifest,
    name: str,
    argv: tuple[str, ...],
    *,
    teardown: bool = False,
) -> CommandSpec:
    return CommandSpec(
        name=name,
        argv=argv,
        timeout_seconds=manifest.limits[
            "teardown_timeout_seconds" if teardown else "command_timeout_seconds"
        ],
        stdout_max_bytes=manifest.limits["stdout_max_bytes"],
        stderr_max_bytes=manifest.limits["stderr_max_bytes"],
    )


def _preflight_plan(manifest: ControllerManifest) -> tuple[CommandSpec, ...]:
    docker = manifest.docker_prefix
    compose = manifest.compose_prefix
    plans = [
        _spec(manifest, "engine-version", docker + ("version", "--format", _ENGINE_FORMAT)),
        _spec(manifest, "engine-info", docker + ("info", "--format", _ENGINE_INFO_FORMAT)),
        _spec(manifest, "compose-version", docker + ("compose", "version", "--short")),
    ]
    for key in ("base_image", "runner_image", "mariadb_image", "redis_image"):
        plans.append(
            _spec(
                manifest,
                f"inspect-{key}",
                docker
                + ("image", "inspect", "--format", _IMAGE_FORMAT, manifest.artifacts[key]),
            )
        )
    plans.extend(
        (
            _spec(
                manifest,
                "compose-config-json",
                compose + ("config", "--format", "json"),
            ),
            _spec(manifest, "compose-images", compose + ("config", "--images")),
        )
    )
    return tuple(plans)



_CONTENT_ARCHIVE_ROOTS: Final = {
    "apps": (
        "/home/frappe/frappe-bench/apps",
        "/home/frappe/frappe-bench/apps",
    ),
    "erpai": ("/opt/erpai", "/opt/erpai"),
    "python": (_RUNNER_PYTHON, _RUNNER_PYTHON),
}


def _content_archive_limit(
    manifest: ControllerManifest,
    archive_name: str,
) -> int:
    if archive_name not in _CONTENT_ARCHIVE_ROOTS:
        _reject()
    expected = _expected_final_filesystem_document(manifest.source_content)
    if archive_name == "apps":
        selected = [
            entry for entry in expected["entries"]
            if str(entry["path"]).startswith(
                "/home/frappe/frappe-bench/apps/"
            )
        ]
    elif archive_name == "erpai":
        selected = [
            entry for entry in expected["entries"]
            if str(entry["path"]).startswith("/opt/erpai/")
        ]
    else:
        selected = [
            entry for entry in expected["entries"]
            if entry["path"] == _RUNNER_PYTHON
        ]
    if not selected:
        _reject()
    source_bytes = sum(_nonnegative_int(entry["size_bytes"]) for entry in selected)
    derived = source_bytes * 4 + manifest.limits["evidence_max_bytes"]
    return min(
        _CONTENT_ARCHIVE_HARD_MAX_BYTES,
        max(manifest.limits["stdout_max_bytes"], derived),
    )


def _archive_member_name(value: str) -> tuple[str, ...]:
    if (
        not value
        or value.startswith("/")
        or "\\" in value
        or "\x00" in value
    ):
        _reject()
    stripped = value[:-1] if value.endswith("/") else value
    parts = stripped.split("/")
    if (
        not stripped
        or any(not part or part in (".", "..") for part in parts)
    ):
        _reject()
    return tuple(parts)


def _parse_content_archive(
    manifest: ControllerManifest,
    archive_name: str,
    body: bytes,
) -> dict[str, dict[str, object]]:
    root_path, absolute_root = _CONTENT_ARCHIVE_ROOTS.get(
        archive_name, (None, None)
    )
    if (
        root_path is None
        or len(body) == 0
        or len(body) > _content_archive_limit(manifest, archive_name)
    ):
        _reject()
    expected_root = PurePosixPath(str(root_path)).name
    records: dict[str, dict[str, object]] = {}
    folded: set[str] = set()
    try:
        with tarfile.open(fileobj=io.BytesIO(body), mode="r:") as archive:
            for member in archive:
                parts = _archive_member_name(member.name)
                if parts[0] != expected_root:
                    _reject()
                if (
                    member.issym()
                    or member.islnk()
                    or member.ischr()
                    or member.isblk()
                    or member.isfifo()
                    or not (member.isdir() or member.isreg())
                    or member.linkname
                    or getattr(member, "sparse", None)
                    or set(member.pax_headers).difference(("path",))
                    or (
                        "path" in member.pax_headers
                        and member.pax_headers["path"].rstrip("/")
                        != member.name.rstrip("/")
                    )
                ):
                    _reject()
                relative = PurePosixPath(*parts[1:])
                canonical = (
                    PurePosixPath(str(absolute_root)) / relative
                    if parts[1:]
                    else PurePosixPath(str(absolute_root))
                )
                canonical_text = str(canonical)
                if (
                    canonical_text in records
                    or canonical_text.casefold() in folded
                    or type(member.uid) is not int
                    or member.uid < 0
                    or type(member.gid) is not int
                    or member.gid < 0
                    or type(member.mode) is not int
                    or member.mode < 0
                    or member.mode > 0o7777
                ):
                    _reject()
                folded.add(canonical_text.casefold())
                if member.isdir():
                    if member.size not in (0,):
                        _reject()
                    record = {
                        "path": canonical_text,
                        "type": "directory",
                        "sha256": hashlib.sha256(b"").hexdigest(),
                        "size_bytes": 0,
                        "uid": member.uid,
                        "gid": member.gid,
                        "mode": format(member.mode, "04o"),
                    }
                else:
                    if member.size < 0:
                        _reject()
                    stream = archive.extractfile(member)
                    if stream is None:
                        _reject()
                    payload = stream.read(member.size + 1)
                    if len(payload) != member.size:
                        _reject()
                    record = {
                        "path": canonical_text,
                        "type": "regular",
                        "sha256": hashlib.sha256(payload).hexdigest(),
                        "size_bytes": member.size,
                        "uid": member.uid,
                        "gid": member.gid,
                        "mode": format(member.mode, "04o"),
                    }
                records[canonical_text] = record
    except ControllerRejected:
        raise
    except (tarfile.TarError, OSError, ValueError, UnicodeError):
        raise ControllerRejected() from None
    root_record = records.get(str(absolute_root))
    expected_root_type = "regular" if archive_name == "python" else "directory"
    if root_record is None or root_record["type"] != expected_root_type:
        _reject()
    return records


def _scope_records(
    records: Mapping[str, Mapping[str, object]],
    root: str,
    *,
    recursive: bool,
) -> list[dict[str, str]]:
    prefix = root + "/"
    result: list[dict[str, str]] = []
    for path, record in records.items():
        if not path.startswith(prefix):
            continue
        relative = path[len(prefix):]
        if not recursive and "/" in relative:
            continue
        result.append({"path": relative, "type": str(record["type"])})
    result.sort(key=lambda item: item["path"].encode("utf-8", "strict"))
    return result


def _tree_record(
    records: Mapping[str, Mapping[str, object]],
    root: str,
) -> dict[str, object]:
    root_record = records.get(root)
    if (
        root_record is None
        or root_record["type"] != "directory"
        or root_record["uid"] != 1000
        or root_record["gid"] != 1000
        or root_record["mode"] != "0555"
    ):
        _reject()
    prefix = root + "/"
    descendants: list[dict[str, object]] = []
    total = 0
    for path, record in records.items():
        if not path.startswith(prefix):
            continue
        relative = path[len(prefix):]
        if record["type"] == "directory":
            if (
                record["uid"] != 1000
                or record["gid"] != 1000
                or record["mode"] != "0555"
            ):
                _reject()
            descendants.append({
                "path": relative,
                "type": "directory",
                "sha256": hashlib.sha256(b"").hexdigest(),
                "size_bytes": 0,
            })
        elif record["type"] == "regular":
            if (
                record["uid"] != 1000
                or record["gid"] != 1000
                or record["mode"] != "0444"
            ):
                _reject()
            size = _nonnegative_int(record["size_bytes"])
            total += size
            descendants.append({
                "path": relative,
                "type": "regular",
                "sha256": _concrete_sha256(record["sha256"]),
                "size_bytes": size,
            })
        else:
            _reject()
    descendants.sort(key=lambda item: item["path"].encode("utf-8", "strict"))
    return {
        "path": root,
        "type": "tree",
        "sha256": hashlib.sha256(
            canonical_json_bytes(descendants)
        ).hexdigest(),
        "size_bytes": total,
        "uid": 1000,
        "gid": 1000,
        "mode": "0555",
    }


def _final_filesystem_from_archives(
    manifest: ControllerManifest,
    archives: Mapping[str, Mapping[str, Mapping[str, object]]],
) -> dict[str, object]:
    if set(archives) != set(_CONTENT_ARCHIVE_ROOTS):
        _reject()
    records: dict[str, Mapping[str, object]] = {}
    folded: set[str] = set()
    for archive_name in sorted(archives):
        for path, record in archives[archive_name].items():
            if path in records or path.casefold() in folded:
                _reject()
            records[path] = record
            folded.add(path.casefold())

    for root, expected in _FINAL_TOP_SCOPES:
        actual = _scope_records(records, root, recursive=False)
        expected_records = [
            {"path": path, "type": kind} for path, kind in expected
        ]
        if actual != expected_records:
            _reject()
        root_record = records.get(root)
        if root_record is None or root_record["type"] != "directory":
            _reject()

    for root, expected in _FINAL_SCOPES:
        actual = _scope_records(records, root, recursive=True)
        expected_records = [
            {"path": path, "type": kind} for path, kind in expected
        ]
        if actual != expected_records:
            _reject()
        root_record = records.get(root)
        if (
            root_record is None
            or root_record["type"] != "directory"
            or root_record["uid"] != 1000
            or root_record["gid"] != 1000
            or root_record["mode"] != "0555"
        ):
            _reject()

    entries: list[dict[str, object]] = []
    for path, kind in _FINAL_MEMBERS:
        if kind == "tree":
            entries.append(_tree_record(records, path))
            continue
        record = records.get(path)
        if record is None or record["type"] != "regular":
            _reject()
        entries.append({
            "path": path,
            "type": "regular",
            "sha256": _concrete_sha256(record["sha256"]),
            "size_bytes": _nonnegative_int(record["size_bytes"]),
            "uid": _nonnegative_int(record["uid"]),
            "gid": _nonnegative_int(record["gid"]),
            "mode": _mode(record["mode"]),
        })
    expected_python = dict(manifest.source_content["python"])
    python_record = entries[0]
    python = {
        "path": python_record["path"],
        "version": expected_python["version"],
        "executable_sha256": python_record["sha256"],
        "size_bytes": python_record["size_bytes"],
        "uid": python_record["uid"],
        "gid": python_record["gid"],
        "mode": python_record["mode"],
    }
    document = {
        "schema": _FINAL_FILESYSTEM_SCHEMA,
        "python": python,
        "entries": entries,
    }
    return validate_final_filesystem_observation(
        manifest, canonical_json_bytes(document)
    )


def _content_verification_plan(manifest: ControllerManifest) -> tuple[CommandSpec, ...]:
    container = f"{manifest.project}_content_verifier"
    placeholder = "__INSPECTED_CONTENT_ID__"
    create = manifest.docker_prefix + (
        "container", "create", "--name", container,
        "--label", manifest.run_label,
        "--label", f"com.docker.compose.project={manifest.project}",
        "--label", "com.docker.compose.service=content-verifier",
        "--pull", "never", "--network", "none", "--read-only",
        "--user", "1000:1000", "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges:true",
        "--tmpfs",
        "/home/frappe/frappe-bench/sites:"
        "rw,noexec,nosuid,nodev,size=1m,mode=0700,uid=1000,gid=1000",
        "--entrypoint", "/bin/false",
        manifest.artifacts["runner_image_id"],
    )
    plans: list[CommandSpec] = [
        _spec(manifest, "content-verify-create", create),
        _spec(
            manifest, "content-verify-container",
            manifest.docker_prefix + (
                "container", "inspect", "--format", _CONTAINER_FORMAT,
                placeholder,
            ),
        ),
    ]
    copy_sources = {
        "apps": "/home/frappe/frappe-bench/apps",
        "erpai": "/opt/erpai",
        "python": _RUNNER_PYTHON,
    }
    for name in ("apps", "erpai", "python"):
        plans.append(CommandSpec(
            name=f"content-copy-{name}",
            argv=manifest.docker_prefix + (
                "container", "cp", "--archive",
                f"{placeholder}:{copy_sources[name]}", "-",
            ),
            timeout_seconds=manifest.limits["command_timeout_seconds"],
            stdout_max_bytes=_content_archive_limit(manifest, name),
            stderr_max_bytes=manifest.limits["stderr_max_bytes"],
        ))
    plans.append(_spec(
        manifest, "content-verify-retire",
        manifest.docker_prefix + (
            "container", "rm", "--force", placeholder,
        ),
        teardown=True,
    ))
    return tuple(plans)


def _validate_content_create_result(result: _CommandResult) -> str:
    if result.returncode != 0 or result.timed_out or result.stderr:
        _reject()
    lines = _parse_fixed_lines(result.stdout)
    if len(lines) != 1 or _SHA256_RE.fullmatch(lines[0]) is None:
        _reject()
    return lines[0]


def _strict_json_string_list(value: str) -> tuple[str, ...]:
    decoded = _decode_json(value.encode("utf-8"))
    if (
        type(decoded) is not list
        or any(type(item) is not str for item in decoded)
        or len(decoded) != len(set(decoded))
    ):
        _reject()
    return tuple(decoded)


def _validate_content_container(
    manifest: ControllerManifest,
    expected_id: str,
    result: _CommandResult,
) -> tuple[str, dict[str, object]]:
    if result.returncode != 0 or result.timed_out or result.stderr:
        _reject()
    lines = _parse_fixed_lines(result.stdout)
    if len(lines) != 1:
        _reject()
    fields = lines[0].split("\t")
    expected_name = f"{manifest.project}_content_verifier"
    if (
        len(fields) != 19
        or fields[0] != expected_id
        or _SHA256_RE.fullmatch(fields[0]) is None
        or fields[1] != manifest.artifacts["runner_image_id"]
        or fields[2] != f"/{expected_name}"
        or fields[3:7] != ["created", "false", "0", "false"]
        or fields[7] != "none"
        or fields[8] != "false"
        or fields[9] != "1000:1000"
        or fields[10] != "true"
        or _strict_json_string_list(fields[11]) != ("ALL",)
        or _strict_json_string_list(fields[12])
        != ("no-new-privileges:true",)
        or _strict_json_string_list(fields[13]) != ("/bin/false",)
        or _strict_json_string_list(fields[14]) != ()
        or fields[15]
        != "tmpfs=/home/frappe/frappe-bench/sites,"
        or fields[16] != manifest.run_id
        or fields[17] != manifest.project
        or fields[18] != "content-verifier"
    ):
        _reject()
    return fields[0], {
        "network_mode": "none",
        "privileged": False,
        "read_only_rootfs": True,
        "user": "1000:1000",
        "cap_drop": ["ALL"],
        "security_options": ["no-new-privileges:true"],
        "tmpfs_destinations": ["/home/frappe/frappe-bench/sites"],
        "container_started": False,
        "verification_container_retired": False,
    }


def _probe_args(manifest: ControllerManifest, case_id: str) -> tuple[str, ...]:
    if case_id not in manifest.canaries:
        _reject()
    if manifest.phase == "observe":
        return (
            "observe",
            "--manifest",
            "/run/secrets/execution-manifest.json",
            "--output",
            "/evidence/observation-result.json",
        )
    return (
        "validate",
        "--manifest",
        "/run/secrets/execution-manifest.json",
        "--policy",
        "/run/secrets/runtime-policy.json",
        "--case",
        case_id,
        "--output",
        "/evidence/validation-result.json",
    )


def _phase_plan(manifest: ControllerManifest) -> tuple[CommandSpec, ...]:
    compose = manifest.compose_prefix
    setup_timeout = str(manifest.limits["setup_timeout_seconds"])
    plans: list[CommandSpec] = list(_content_verification_plan(manifest))
    plans.extend([
        _spec(
            manifest,
            "stack-up",
            compose
            + (
                "up",
                "--detach",
                "--pull",
                "never",
                "--wait",
                "--wait-timeout",
                setup_timeout,
                "db-primary",
                "redis-cache",
            ),
        ),
        _spec(
            manifest,
            "site-initialize",
            compose
            + (
                "run",
                "--rm",
                "--no-TTY",
                "--no-deps",
                "--pull",
                "never",
                "--name",
                f"{manifest.project}_site_init",
                "--label",
                manifest.run_label,
                "site-init",
                "initialize",
                "--manifest",
                "/run/secrets/site-init-manifest.json",
            ),
        ),
    ])
    for case_id in manifest.canaries:
        container = f"{manifest.project}_probe_{case_id}"
        probe_args = _probe_args(manifest, case_id)
        plans.append(
            _spec(
                manifest,
                f"probe-wait-{case_id}",
                compose
                + (
                    "run",
                    "--no-TTY",
                    "--no-deps",
                    "--pull",
                    "never",
                    "--name",
                    container,
                    "--label",
                    manifest.run_label,
                    "runtime-probe",
                )
                + probe_args,
            )
        )
        plans.extend(
            (
                _spec(
                    manifest,
                    f"inspect-probe-{case_id}",
                    manifest.docker_prefix
                    + ("container", "inspect", "--format", _CONTAINER_FORMAT, container),
                ),
                _spec(
                    manifest,
                    f"copy-evidence-{case_id}",
                    manifest.docker_prefix
                    + (
                        "container",
                        "cp",
                        "__INSPECTED_CONTAINER_ID__:/evidence/"
                        + (
                            "observation-result.json"
                            if manifest.phase == "observe"
                            else "validation-result.json"
                        ),
                        "-",
                    ),
                ),
                _spec(
                    manifest,
                    f"retire-probe-{case_id}",
                    manifest.docker_prefix
                    + (
                        "container",
                        "rm",
                        "--force",
                        "__INSPECTED_CONTAINER_ID__",
                    ),
                    teardown=True,
                ),
            )
        )
    return tuple(plans)


def _inventory_plan(manifest: ControllerManifest) -> tuple[CommandSpec, ...]:
    project = manifest.project
    filters = (
        ("name", f"name={project}_"),
        ("run", f"label={manifest.run_label}"),
        ("project", f"label=com.docker.compose.project={project}"),
    )
    plans: list[CommandSpec] = []
    resource_commands = (
        ("containers", ("container", "ls", "--all", "--no-trunc"), _CONTAINER_LIST_FORMAT),
        ("networks", ("network", "ls", "--no-trunc"), _NETWORK_LIST_FORMAT),
        ("volumes", ("volume", "ls"), _VOLUME_LIST_FORMAT),
    )
    for resource, command, output_format in resource_commands:
        for scope, filter_value in filters:
            plans.append(
                _spec(
                    manifest,
                    f"teardown-inspect-{resource}-{scope}",
                    manifest.docker_prefix
                    + command
                    + ("--filter", filter_value, "--format", output_format),
                    teardown=True,
                )
            )
    return tuple(plans)


def _teardown_plan(manifest: ControllerManifest) -> tuple[CommandSpec, ...]:
    # Concrete removal commands are created only after the three-scope
    # inventory returns exact daemon IDs. Names are never removal authority.
    return _inventory_plan(manifest)


def build_child_command_plan(
    manifest: ControllerManifest,
    command: str,
) -> tuple[CommandSpec, ...]:
    if command not in _COMMANDS:
        _reject()
    if command == "preflight":
        return _preflight_plan(manifest)
    if command == "observe":
        if manifest.phase != "observe":
            _reject()
        return _preflight_plan(manifest) + _phase_plan(manifest) + _teardown_plan(manifest)
    if command == "validate":
        if manifest.phase != "validate" or manifest.policy is None:
            _reject()
        return _preflight_plan(manifest) + _phase_plan(manifest) + _teardown_plan(manifest)
    return _teardown_plan(manifest)


def _execution_environment(manifest: ControllerManifest) -> dict[str, str]:
    """Closed non-secret environment consumed only by the dedicated Compose file."""

    return {
        "HOME": f"{manifest.run_root}/control-home",
        "XDG_RUNTIME_DIR": manifest.docker["rootlesskit_runtime_dir"],
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": "/usr/bin:/bin",
        "COMPOSE_DISABLE_ENV_FILE": "1",
        "COMPOSE_ANSI": "never",
        "GL_TB_RUN_ID": manifest.run_id,
        "GL_TB_PROJECT": manifest.project,
        "GL_TB_RUN_LABEL": manifest.run_label,
        "GL_TB_RUNNER_IMAGE": manifest.artifacts["runner_image"],
        "GL_TB_MARIADB_IMAGE": manifest.artifacts["mariadb_image"],
        "GL_TB_REDIS_IMAGE": manifest.artifacts["redis_image"],
        "GL_TB_DB_ROOT_SECRET_FILE": str(manifest.secrets["db_root_password"]),
        "GL_TB_SITE_ADMIN_SECRET_FILE": str(manifest.secrets["site_admin_password"]),
        "GL_TB_SITE_DB_SECRET_FILE": str(manifest.secrets["site_db_password"]),
        "GL_TB_CONNECTION_KEY_FILE": str(manifest.secrets["connection_commitment_key"]),
        "GL_TB_SITE_INIT_MANIFEST_FILE": f"{manifest.secrets['directory']}/site-init-manifest.json",
        "GL_TB_EXECUTION_MANIFEST_FILE": f"{manifest.secrets['directory']}/execution-manifest.json",
        "GL_TB_RUNTIME_POLICY_FILE": str(manifest.secrets["runtime_policy"]),
        "GL_TB_HEALTH_INTERVAL_SECONDS": str(
            manifest.limits["healthcheck_interval_seconds"]
        ),
        "GL_TB_HEALTH_TIMEOUT_SECONDS": str(
            manifest.limits["healthcheck_timeout_seconds"]
        ),
        "GL_TB_HEALTH_RETRIES": str(manifest.limits["healthcheck_retries"]),
    }


@dataclass(frozen=True, slots=True)
class _CommandResult:
    returncode: int
    stdout: bytes
    stderr: bytes
    timed_out: bool


def _terminate_process(process: subprocess.Popen[bytes]) -> None:
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except (AttributeError, OSError, TypeError):
        process.kill()


def _run_subprocess(spec: CommandSpec, environment: Mapping[str, str]) -> _CommandResult:
    """Run one exact argv and enforce byte and time ceilings while streaming."""

    process: subprocess.Popen[bytes] | None = None
    selector: selectors.BaseSelector | None = None
    stdout = bytearray()
    stderr = bytearray()
    timed_out = False
    output_exceeded = False
    try:
        process = subprocess.Popen(
            list(spec.argv),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            cwd="/",
            env=dict(environment),
            start_new_session=True,
        )
        if process.stdout is None or process.stderr is None:
            raise _ControllerInternal()
        selector = selectors.DefaultSelector()
        selector.register(process.stdout, selectors.EVENT_READ, (stdout, spec.stdout_max_bytes))
        selector.register(process.stderr, selectors.EVENT_READ, (stderr, spec.stderr_max_bytes))
        deadline = time.monotonic() + spec.timeout_seconds
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                timed_out = True
                _terminate_process(process)
                break
            events = selector.select(remaining)
            if not events:
                timed_out = True
                _terminate_process(process)
                break
            for key, _mask in events:
                retained, maximum = key.data
                chunk = os.read(
                    key.fd,
                    min(65_536, maximum + 1 - len(retained)),
                )
                if not chunk:
                    selector.unregister(key.fileobj)
                    key.fileobj.close()
                    continue
                retained.extend(chunk)
                if len(retained) > maximum:
                    output_exceeded = True
                    _terminate_process(process)
                    break
            if output_exceeded:
                break
        wait_remaining = max(0.0, deadline - time.monotonic())
        try:
            process.wait(timeout=wait_remaining)
        except subprocess.TimeoutExpired:
            timed_out = True
            _terminate_process(process)
            process.wait(timeout=spec.timeout_seconds)
    except (ControllerRejected, _ControllerInternal):
        if process is not None and process.poll() is None:
            _terminate_process(process)
        raise
    except BaseException:
        if process is not None and process.poll() is None:
            try:
                _terminate_process(process)
                process.wait(timeout=spec.timeout_seconds)
            except BaseException:
                pass
        raise _ControllerInternal() from None
    finally:
        if selector is not None:
            selector.close()
        if process is not None:
            for stream in (process.stdout, process.stderr):
                if stream is not None and not stream.closed:
                    stream.close()
    if output_exceeded:
        _reject()
    return _CommandResult(process.returncode, bytes(stdout), bytes(stderr), timed_out)


def _parse_fixed_lines(value: bytes) -> tuple[str, ...]:
    try:
        text = value.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        raise ControllerRejected() from None
    if "\x00" in text or "\r" in text:
        _reject()
    lines = tuple(line for line in text.split("\n") if line)
    if any(not line or line != line.strip() for line in lines):
        _reject()
    return lines


def _validate_resolved_compose(
    manifest: ControllerManifest, body: bytes
) -> None:
    """Reject any resolved service or mount outside the frozen one-stack graph."""

    document = _decode_json(body)
    allowed_top_keys = frozenset(("name", "services", "networks", "volumes", "secrets"))
    if (
        type(document) is not dict
        or not frozenset(document).issubset(allowed_top_keys)
        or frozenset(("services", "networks", "volumes", "secrets"))
        - frozenset(document)
        or ("name" in document and document["name"] != manifest.project)
    ):
        _reject()
    services = document.get("services")
    networks = document.get("networks")
    volumes = document.get("volumes")
    secrets = document.get("secrets")
    if (
        type(services) is not dict
        or frozenset(services) != frozenset(_SERVICES)
        or type(networks) is not dict
        or frozenset(networks) != frozenset(("internal",))
        or type(volumes) is not dict
        or frozenset(volumes) != frozenset(("db", "sites", "redis"))
        or type(secrets) is not dict
        or frozenset(secrets)
        != frozenset(
            (
                "db-root-password",
                "site-admin-password",
                "site-db-password",
                "connection-commitment-key",
                "site-init-manifest",
                "execution-manifest",
                "runtime-policy",
            )
        )
    ):
        _reject()
    network = networks["internal"]
    network_labels = network.get("labels") if type(network) is dict else None
    if (
        type(network) is not dict
        or not frozenset(network).issubset(
            frozenset(("name", "driver", "internal", "attachable", "labels"))
        )
        or network.get("internal") is not True
        or network.get("attachable") is not False
        or network.get("name") != manifest.compose["network"]
        or network.get("driver", "bridge") != "bridge"
        or type(network_labels) is not dict
        or network_labels.get(
            "com.erpai.finance.gl_tb_rtcompat.run"
        )
        != manifest.run_id
    ):
        _reject()
    expected_volume_names = dict(
        zip(("db", "sites", "redis"), manifest.compose["volumes"], strict=True)
    )
    for key, expected_name in expected_volume_names.items():
        volume = volumes[key]
        volume_labels = volume.get("labels") if type(volume) is dict else None
        if (
            type(volume) is not dict
            or not frozenset(volume).issubset(
                frozenset(("name", "driver", "labels"))
            )
            or volume.get("name") != expected_name
            or volume.get("driver", "local") != "local"
            or type(volume_labels) is not dict
            or volume_labels.get(
                "com.erpai.finance.gl_tb_rtcompat.run"
            )
            != manifest.run_id
        ):
            _reject()
    expected_secret_files = {
        "db-root-password": manifest.secrets["db_root_password"],
        "site-admin-password": manifest.secrets["site_admin_password"],
        "site-db-password": manifest.secrets["site_db_password"],
        "connection-commitment-key": manifest.secrets["connection_commitment_key"],
        "runtime-policy": manifest.secrets["runtime_policy"],
        "site-init-manifest": f"{manifest.secrets['directory']}/site-init-manifest.json",
        "execution-manifest": f"{manifest.secrets['directory']}/execution-manifest.json",
    }
    for key, expected_file in expected_secret_files.items():
        secret = secrets[key]
        if (
            type(secret) is not dict
            or not frozenset(secret).issubset(frozenset(("name", "file")))
            or secret.get("file") != expected_file
            or (
                "name" in secret
                and secret["name"] != f"{manifest.project}_{key}"
            )
        ):
            _reject()
    expected_images = {
        "db-primary": manifest.artifacts["mariadb_image"],
        "redis-cache": manifest.artifacts["redis_image"],
        "site-init": manifest.artifacts["runner_image"],
        "runtime-probe": manifest.artifacts["runner_image"],
    }
    expected_service_secrets = {
        "db-primary": frozenset(("db-root-password",)),
        "redis-cache": frozenset(),
        "site-init": frozenset(
            (
                "db-root-password",
                "site-admin-password",
                "site-db-password",
                "site-init-manifest",
            )
        ),
        "runtime-probe": frozenset(
            (
                "connection-commitment-key",
                "execution-manifest",
                "runtime-policy",
            )
        ),
    }
    allowed_service_keys = {
        "db-primary": frozenset(
            (
                "image", "container_name", "pull_policy", "restart",
                "environment", "secrets", "networks", "volumes", "labels",
                "healthcheck", "logging",
            )
        ),
        "redis-cache": frozenset(
            (
                "image", "container_name", "pull_policy", "restart", "command",
                "read_only", "tmpfs", "networks", "volumes", "labels",
                "healthcheck", "logging",
            )
        ),
        "site-init": frozenset(
            (
                "image", "pull_policy", "restart", "entrypoint", "command",
                "environment", "read_only", "cap_drop", "security_opt", "tmpfs",
                "depends_on", "networks", "volumes", "secrets", "labels",
                "logging",
            )
        ),
        "runtime-probe": frozenset(
            (
                "image", "pull_policy", "restart", "environment", "read_only", "cap_drop",
                "security_opt", "tmpfs", "depends_on", "networks", "volumes",
                "secrets", "labels", "logging",
            )
        ),
    }
    expected_volume_mounts = {
        "db-primary": ("db", "/var/lib/mysql", False, True),
        "redis-cache": ("redis", "/data", False, True),
        "site-init": (
            "sites", str(manifest.site["sites_path"]), False, False,
        ),
        "runtime-probe": (
            "sites", str(manifest.site["sites_path"]), True, False,
        ),
    }
    expected_secret_targets = {
        "db-primary": {"db-root-password": "db-root-password"},
        "redis-cache": {},
        "site-init": {
            "db-root-password": "db-root-password",
            "site-admin-password": "site-admin-password",
            "site-db-password": "site-db-password",
            "site-init-manifest": "site-init-manifest.json",
        },
        "runtime-probe": {
            "connection-commitment-key": "connection-commitment-key",
            "execution-manifest": "execution-manifest.json",
            "runtime-policy": "runtime-policy.json",
        },
    }
    forbidden_service_keys = frozenset(
        (
            "ports",
            "privileged",
            "devices",
            "extra_hosts",
            "network_mode",
            "env_file",
        )
    )
    for name, service in services.items():
        if (
            type(service) is not dict
            or not frozenset(service).issubset(allowed_service_keys[name])
            or service.get("image") != expected_images[name]
            or service.get("pull_policy") != "never"
            or service.get("restart") != "no"
        ):
            _reject()
        if forbidden_service_keys.intersection(service):
            _reject()
        labels = service.get("labels")
        if (
            type(labels) is not dict
            or labels.get("com.erpai.finance.gl_tb_rtcompat.run")
            != manifest.run_id
        ):
            _reject()
        if service.get("networks") not in (["internal"], {"internal": None}):
            if not (
                type(service.get("networks")) is dict
                and frozenset(service["networks"]) == frozenset(("internal",))
            ):
                _reject()
        mounts = service.get("volumes", ())
        if not isinstance(mounts, list) or len(mounts) != 1:
            _reject()
        mount = mounts[0]
        source, target, read_only, nocopy = expected_volume_mounts[name]
        if (
            type(mount) is not dict
            or frozenset(mount)
            != frozenset(("type", "source", "target", "read_only", "volume"))
            or mount.get("type") != "volume"
            or mount.get("source") != source
            or mount.get("target") != target
            or mount.get("read_only") is not read_only
            or mount.get("volume") != {"nocopy": nocopy}
        ):
            _reject()
        service_secrets = service.get("secrets", [])
        if not isinstance(service_secrets, list):
            _reject()
        sources: dict[str, str] = {}
        for secret_mount in service_secrets:
            if (
                type(secret_mount) is not dict
                or frozenset(secret_mount) != frozenset(("source", "target"))
                or type(secret_mount.get("source")) is not str
                or type(secret_mount.get("target")) is not str
                or secret_mount["source"] in sources
            ):
                _reject()
            sources[secret_mount["source"]] = secret_mount["target"]
        if (
            frozenset(sources) != expected_service_secrets[name]
            or sources != expected_secret_targets[name]
        ):
            _reject()
        expected_environments = {
            "db-primary": {
                "MARIADB_ROOT_PASSWORD_FILE": "/run/secrets/db-root-password",
                "MARIADB_ROOT_HOST": "%",
            },
            "site-init": {
                "FRAPPE_REDIS_CACHE": "redis://redis-cache:6379"
            },
            "runtime-probe": {
                "FRAPPE_REDIS_CACHE": "redis://redis-cache:6379"
            },
        }
        if name in expected_environments:
            if service.get("environment") != expected_environments[name]:
                _reject()
        elif "environment" in service:
            _reject()
    for name in ("site-init", "runtime-probe"):
        service = services[name]
        if (
            service.get("read_only") is not True
            or service.get("cap_drop") != ["ALL"]
            or "no-new-privileges:true" not in service.get("security_opt", ())
        ):
            _reject()
    if services["db-primary"].get("container_name") != f"{manifest.project}_db_primary":
        _reject()
    if services["redis-cache"].get("container_name") != f"{manifest.project}_redis_cache":
        _reject()
    probe_tmpfs = services["runtime-probe"].get("tmpfs")
    if not isinstance(probe_tmpfs, list) or not any(
        str(value).startswith("/evidence:") for value in probe_tmpfs
    ):
        _reject()
    rendered = canonical_json_bytes(document)
    for forbidden in (
        b"/var/run/docker.sock",
        b"/run/docker.sock",
        b"/home/deploy/erp-projects",
        b'"type":"bind"',
        b'"privileged":true',
    ):
        if forbidden in rendered:
            _reject()


def _image_environment(value: object) -> dict[str, str]:
    if (
        type(value) is not list
        or any(type(item) is not str or "=" not in item for item in value)
    ):
        _reject()
    result: dict[str, str] = {}
    for item in value:
        name, content = item.split("=", 1)
        if not name or name in result:
            _reject()
        result[name] = content
    return result


def _runner_environment_overrides(
    manifest: ControllerManifest,
) -> dict[str, str]:
    content = manifest.source_content
    return {
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1",
        "PYTHONUNBUFFERED": "1",
        "PYTHONPATH": (
            "/home/frappe/frappe-bench/apps/frappe:"
            "/home/frappe/frappe-bench/apps/erpnext:"
            "/home/frappe/frappe-bench/apps/erp_workspace_ui"
        ),
        "ERPAI_FRONTEND_POLICY": "engine_builtin",
        "ERPAI_SOURCE_REPOSITORY_REVISION": manifest.repository["revision"],
        "ERPAI_FRAPPE_REVISION": content["sources"]["frappe"]["revision"],
        "ERPAI_ERPNEXT_REVISION": content["sources"]["erpnext"]["revision"],
        "ERPAI_BUILD_CONTEXT_MANIFEST_SHA256": (
            content["build_context"]["manifest_sha256"]
        ),
        "ERPAI_BUILD_MANIFEST_SHA256": content["gl_tb"][
            "build_manifest_sha256"
        ],
        "ERPAI_SOURCE_CONTENT_SHA256": manifest.repository[
            "source_content_sha256"
        ],
        "ERPAI_DOCKERFILE_SHA256": content["frontend"]["dockerfile_sha256"],
        "ERPAI_FRAPPE_TREE_SHA256": content["sources"]["frappe"][
            "tree_sha256"
        ],
        "ERPAI_ERPNEXT_TREE_SHA256": content["sources"]["erpnext"][
            "tree_sha256"
        ],
        "ERPAI_PACKAGE_INITIALIZER_SHA256": content["gl_tb"][
            "package_initializer_sha256"
        ],
        "ERPAI_FINANCE_INITIALIZER_SHA256": content["gl_tb"][
            "finance_initializer_sha256"
        ],
        "ERPAI_CORE_SHA256": content["gl_tb"]["core_sha256"],
        "ERPAI_ADAPTER_SHA256": content["gl_tb"]["adapter_sha256"],
        "ERPAI_RUNTIME_SHA256": content["gl_tb"]["runtime_sha256"],
        "ERPAI_PROBE_SHA256": content["gl_tb"]["probe_sha256"],
        "ERPAI_INITIALIZER_SHA256": content["gl_tb"]["initializer_sha256"],
        "ERPAI_RUNNER_PYTHON_VERSION": content["python"]["version"],
        "ERPAI_RUNNER_PYTHON_SHA256": content["python"][
            "executable_sha256"
        ],
    }


def _normalized_image_config(
    config: Mapping[str, object],
    environment: Mapping[str, str],
) -> dict[str, object]:
    normalized = dict(config)
    normalized["Env"] = [
        f"{name}={environment[name]}" for name in sorted(environment)
    ]
    return normalized


def _image_config(
    value: object,
    volume_document: object,
) -> tuple[dict[str, object], dict[str, str]]:
    if type(value) is not dict or any(type(key) is not str for key in value):
        _reject()
    config = dict(value)
    required = {
        "User", "WorkingDir", "Entrypoint", "Cmd", "Env", "Volumes",
    }
    if not required.issubset(config) or config["Volumes"] != volume_document:
        _reject()
    environment = _image_environment(config["Env"])
    return config, environment


def _validate_preflight_result(
    manifest: ControllerManifest,
    spec: CommandSpec,
    result: _CommandResult,
    *,
    base_configuration: Mapping[str, object] | None = None,
) -> dict[str, object] | None:
    if result.returncode != 0 or result.timed_out or result.stderr:
        _reject()
    if spec.name == "compose-config-json":
        _validate_resolved_compose(manifest, result.stdout)
        return
    lines = _parse_fixed_lines(result.stdout)
    if spec.name == "engine-version":
        if lines != (
            "\t".join(
                (
                    manifest.docker["client_version"],
                    manifest.docker["client_api_version"],
                    manifest.docker["server_version"],
                    manifest.docker["server_api_version"],
                    manifest.docker["os"],
                    manifest.docker["architecture"],
                )
            ),
        ):
            _reject()
    elif spec.name == "engine-info":
        if len(lines) != 1:
            _reject()
        fields = lines[0].split("\t")
        if (
            len(fields) != 6
            or fields[0] != manifest.docker["daemon_id"]
            or fields[1] != manifest.docker["daemon_name"]
            or fields[2] != manifest.docker["docker_root_dir"]
            or hashlib.sha256(fields[3].encode("utf-8")).hexdigest()
            != manifest.docker["security_options_sha256"]
            or "name=rootless" not in _strict_json_string_list(fields[3])
            or fields[4] != manifest.docker["cgroup_driver"]
            or fields[5] != manifest.docker["cgroup_version"]
        ):
            _reject()
    elif spec.name == "compose-version":
        if lines != (manifest.docker["compose_version"],):
            _reject()
    elif spec.name.startswith("inspect-"):
        key = spec.name.removeprefix("inspect-")
        id_key = key.replace("_image", "_image_id")
        if len(lines) != 1:
            _reject()
        fields = lines[0].split("\t")
        volume_document = (
            _decode_json(fields[4].encode("utf-8"))
            if len(fields) == 6 else False
        )
        if volume_document is None:
            volume_destinations: frozenset[str] = frozenset()
        elif type(volume_document) is dict and all(
            type(item) is str and value in (None, {})
            for item, value in volume_document.items()
        ):
            volume_destinations = frozenset(volume_document)
        else:
            _reject()
        if (
            len(fields) != 6
            or fields[0] != manifest.artifacts[id_key]
            or _strict_json_string_list(fields[1])
            != (manifest.artifacts[key],)
            or fields[2] != manifest.docker["os"]
            or fields[3] != manifest.docker["architecture"]
            or not volume_destinations.issubset(
                _IMAGE_VOLUME_DESTINATIONS[key]
            )
        ):
            _reject()
        if key == "base_image":
            config_value = _decode_json(fields[5].encode("utf-8"))
            config, environment = _image_config(
                config_value, volume_document
            )
            return {
                "configuration": config,
                "configuration_sha256": hashlib.sha256(
                    canonical_json_bytes(
                        _normalized_image_config(config, environment)
                    )
                ).hexdigest(),
            }
        if key == "runner_image":
            if base_configuration is None:
                _reject()
            base_config, base_environment = _image_config(
                dict(base_configuration),
                base_configuration.get("Volumes"),
            )
            config_value = _decode_json(fields[5].encode("utf-8"))
            config, environment = _image_config(
                config_value, volume_document
            )
            expected_environment = dict(base_environment)
            expected_environment.update(
                _runner_environment_overrides(manifest)
            )
            expected_config = dict(base_config)
            expected_config.update({
                "User": "1000:1000",
                "WorkingDir": "/opt/erpai",
                "Entrypoint": [
                    "/opt/erpai/"
                    "finance_gl_trial_balance_runtime_compatibility_probe.py"
                ],
                "Cmd": [],
                "Env": config["Env"],
            })
            actual_without_environment = dict(config)
            actual_without_environment.pop("Env")
            expected_without_environment = dict(expected_config)
            expected_without_environment.pop("Env")
            if (
                environment != expected_environment
                or actual_without_environment != expected_without_environment
            ):
                _reject()
            normalized_base = _normalized_image_config(
                base_config, base_environment
            )
            normalized_config = _normalized_image_config(
                config, environment
            )
            return {
                "final_image": {
                    "image_id": fields[0],
                    "repository_digest": manifest.artifacts["runner_image"],
                    "os": fields[2],
                    "platform": f"{fields[2]}/{fields[3]}",
                    "architecture": fields[3],
                },
                "image_configuration": {
                    "base_config_sha256": hashlib.sha256(
                        canonical_json_bytes(normalized_base)
                    ).hexdigest(),
                    "config_sha256": hashlib.sha256(
                        canonical_json_bytes(normalized_config)
                    ).hexdigest(),
                    "user": str(config["User"]),
                    "working_directory": str(config["WorkingDir"]),
                    "entrypoint": list(config["Entrypoint"]),
                    "cmd": list(config["Cmd"]),
                    "environment_sha256": hashlib.sha256(
                        canonical_json_bytes(
                            [f"{name}={environment[name]}"
                             for name in sorted(environment)]
                        )
                    ).hexdigest(),
                    "volume_destinations": sorted(volume_destinations),
                },
            }
    elif spec.name == "compose-images":
        expected = tuple(
            sorted(
                (
                    manifest.artifacts["runner_image"],
                    manifest.artifacts["mariadb_image"],
                    manifest.artifacts["redis_image"],
                )
            )
        )
        if tuple(sorted(set(lines))) != expected:
            _reject()
    return None


def _validate_materialization_attestation(
    manifest: ControllerManifest,
    value: object,
) -> dict[str, object]:
    attestation = _closed_object(value, _MATERIALIZATION_KEYS)
    if (
        attestation["schema"] != _MATERIALIZATION_ATTESTATION_SCHEMA
        or attestation["source_content_sha256"]
        != manifest.repository["source_content_sha256"]
    ):
        _reject()
    source_digest = _concrete_sha256(attestation["source_content_sha256"])
    final_image = _closed_object(attestation["final_image"], _FINAL_IMAGE_KEYS)
    expected_image = {
        "image_id": manifest.artifacts["runner_image_id"],
        "repository_digest": manifest.artifacts["runner_image"],
        "os": manifest.docker["os"],
        "platform": f"{manifest.docker['os']}/{manifest.docker['architecture']}",
        "architecture": manifest.docker["architecture"],
    }
    if final_image != expected_image:
        _reject()
    image_id_digest = _image_id(final_image["image_id"]).removeprefix("sha256:")
    repository_digest = _immutable_image(
        final_image["repository_digest"]
    ).rsplit("@sha256:", 1)[-1]
    if source_digest in (image_id_digest, repository_digest):
        _reject()

    expected_filesystem = _expected_final_filesystem_document(
        manifest.source_content
    )
    python = _closed_object(attestation["python"], _PYTHON_KEYS)
    if python != expected_filesystem["python"]:
        _reject()
    filesystem = _closed_object(
        attestation["final_filesystem"], _FINAL_INVENTORY_KEYS
    )
    entries = _inventory_entries(filesystem["entries"], _FINAL_MEMBERS)
    normalized_filesystem = {
        "entries": list(entries),
        "manifest_sha256": _concrete_sha256(filesystem["manifest_sha256"]),
    }
    if (
        normalized_filesystem["entries"] != expected_filesystem["entries"]
        or normalized_filesystem["manifest_sha256"] != _inventory_sha256(entries)
    ):
        _reject()

    configuration = _closed_object(
        attestation["image_configuration"], _IMAGE_CONFIGURATION_KEYS
    )
    entrypoint = _exact_sequence(
        configuration["entrypoint"],
        (
            "/opt/erpai/"
            "finance_gl_trial_balance_runtime_compatibility_probe.py",
        ),
    )
    command = configuration["cmd"]
    if type(command) is not list or any(type(item) is not str for item in command):
        _reject()
    volumes = _exact_sequence(
        configuration["volume_destinations"],
        ("/home/frappe/frappe-bench/sites",),
    )
    normalized_configuration = {
        "base_config_sha256": _concrete_sha256(
            configuration["base_config_sha256"]
        ),
        "config_sha256": _concrete_sha256(configuration["config_sha256"]),
        "user": _text(configuration["user"]),
        "working_directory": _text(configuration["working_directory"]),
        "entrypoint": list(entrypoint),
        "cmd": list(command),
        "environment_sha256": _concrete_sha256(
            configuration["environment_sha256"]
        ),
        "volume_destinations": list(volumes),
    }
    if (
        normalized_configuration["user"] != "1000:1000"
        or normalized_configuration["working_directory"] != "/opt/erpai"
    ):
        _reject()

    containment = _closed_object(
        attestation["verification_containment"],
        _VERIFICATION_CONTAINMENT_KEYS,
    )
    expected_containment = {
        "network_mode": "none",
        "privileged": False,
        "read_only_rootfs": True,
        "user": "1000:1000",
        "cap_drop": ["ALL"],
        "security_options": ["no-new-privileges:true"],
        "tmpfs_destinations": ["/home/frappe/frappe-bench/sites"],
        "container_started": False,
        "verification_container_retired": True,
    }
    if containment != expected_containment:
        _reject()
    return {
        "schema": _MATERIALIZATION_ATTESTATION_SCHEMA,
        "source_content_sha256": source_digest,
        "final_image": dict(final_image),
        "python": dict(python),
        "final_filesystem": normalized_filesystem,
        "image_configuration": normalized_configuration,
        "verification_containment": expected_containment,
    }


def _build_materialization_attestation(
    manifest: ControllerManifest,
    runner_observation: Mapping[str, object],
    filesystem_observation: Mapping[str, object],
    containment_observation: Mapping[str, object],
) -> dict[str, object]:
    filesystem_entries = filesystem_observation["entries"]
    value = {
        "schema": _MATERIALIZATION_ATTESTATION_SCHEMA,
        "source_content_sha256": manifest.repository["source_content_sha256"],
        "final_image": dict(runner_observation["final_image"]),
        "python": dict(filesystem_observation["python"]),
        "final_filesystem": {
            "entries": [dict(entry) for entry in filesystem_entries],
            "manifest_sha256": filesystem_observation["manifest_sha256"],
        },
        "image_configuration": dict(
            runner_observation["image_configuration"]
        ),
        "verification_containment": dict(containment_observation),
    }
    return _validate_materialization_attestation(manifest, value)


def _artifact_provenance(
    manifest: ControllerManifest,
    materialization_attestation: Mapping[str, object],
) -> dict[str, object]:
    return {
        "schema": _ARTIFACT_SCHEMA,
        "run_id": manifest.run_id,
        "repository": dict(manifest.repository),
        "artifacts": dict(manifest.artifacts),
        "docker_runtime_verified": {
            key: manifest.docker[key]
            for key in (
                "executable_sha256", "compose_version", "client_version",
                "client_api_version", "server_version", "server_api_version",
                "daemon_id", "daemon_name", "docker_root_dir",
                "security_options_sha256", "cgroup_driver", "cgroup_version",
                "os", "architecture",
            )
        },
        "build_materialization_declarations": {
            "policy": "engine_builtin",
            "buildkit_version": manifest.docker["buildkit_version"],
            "frontend_capabilities_sha256":
                manifest.docker["frontend_capabilities_sha256"],
            "status": "external_materialization_prerequisite_bound",
            "daemon_lifecycle_owner":
                manifest.docker["daemon_lifecycle_owner"],
            "daemon_socket_runtime_teardown":
                "required_before_point_closure",
        },
        "cgroup_claim": {
            "authority": manifest.docker["cgroup_authority"],
            "status": (
                "compatibility_observation_only"
                if manifest.phase == "observe"
                and manifest.docker["cgroup_driver"] == "none"
                else "external_delegation_prerequisite_bound"
            ),
        },
        "source_content": {
            "sha256": manifest.repository["source_content_sha256"],
            "contract": dict(manifest.source_content),
        },
        "materialization_attestation": dict(materialization_attestation),
        "materialization_attestation_sha256": hashlib.sha256(
            canonical_json_bytes(materialization_attestation)
        ).hexdigest(),
        "result": "runtime_preflight_and_materialization_verified",
    }


def _read_host_regular(
    path: PurePosixPath,
    maximum: int,
    *,
    private: bool = False,
) -> bytes:
    try:
        status = os.lstat(str(path))
        if (
            not stat.S_ISREG(status.st_mode)
            or status.st_nlink != 1
            or status.st_size < 0
            or status.st_size > maximum
            or (
                private
                and (
                    status.st_uid != os.geteuid()
                    or stat.S_IMODE(status.st_mode) & 0o077
                )
            )
        ):
            _reject()
        with open(path, "rb", buffering=0) as stream:
            body = stream.read(maximum + 1)
        if len(body) != status.st_size:
            _reject()
        return body
    except ControllerRejected:
        raise
    except OSError:
        raise ControllerRejected() from None


def _file_sha256(path: PurePosixPath) -> str:
    digest = hashlib.sha256()
    try:
        status = os.lstat(str(path))
        if not stat.S_ISREG(status.st_mode) or status.st_nlink != 1:
            _reject()
        with open(path, "rb", buffering=0) as stream:
            while True:
                block = stream.read(1_048_576)
                if not block:
                    break
                digest.update(block)
    except ControllerRejected:
        raise
    except OSError:
        raise ControllerRejected() from None
    return digest.hexdigest()


def _require_private_directory(path: PurePosixPath) -> None:
    try:
        status = os.lstat(str(path))
        if (
            not stat.S_ISDIR(status.st_mode)
            or status.st_uid != os.geteuid()
            or stat.S_IMODE(status.st_mode) & 0o077
        ):
            _reject()
    except ControllerRejected:
        raise
    except OSError:
        raise ControllerRejected() from None


def _require_unix_socket(
    path: PurePosixPath,
    *,
    lstat: Callable[[str], os.stat_result] = os.lstat,
) -> None:
    try:
        status = lstat(str(path))
        if not stat.S_ISSOCK(status.st_mode) or status.st_nlink != 1:
            _reject()
    except ControllerRejected:
        raise
    except OSError:
        raise ControllerRejected() from None


def _site_initializer_document(manifest: ControllerManifest) -> dict[str, object]:
    return {
        "schema": "erpai.gl_tb.runtime_compat.site_init.v1",
        "run_id": manifest.run_id,
        "site": dict(manifest.site),
        "secrets": {
            "db_root_password": "/run/secrets/db-root-password",
            "site_admin_password": "/run/secrets/site-admin-password",
            "site_db_password": "/run/secrets/site-db-password",
        },
    }


def _validate_host_inputs(manifest: ControllerManifest) -> None:
    run_root = PurePosixPath(manifest.run_root)
    compose_path = PurePosixPath(str(manifest.compose["file"]))
    docker_path = PurePosixPath(str(manifest.docker["executable"]))
    socket_path = PurePosixPath(
        str(manifest.docker["endpoint"]).removeprefix("unix://")
    )
    for directory in (run_root, run_root / "docker", run_root / "control-home"):
        validate_no_symlink_path(str(directory), str(run_root))
        _require_private_directory(directory)
    rootless_dir = PurePosixPath(manifest.docker["rootlesskit_runtime_dir"])
    rootless_parent = _ROOTLESSKIT_RUNTIME_PARENT / str(os.geteuid())
    validate_no_symlink_path(str(rootless_dir), str(rootless_parent))
    _require_private_directory(rootless_parent)
    _require_private_directory(rootless_dir)
    validate_no_symlink_path(str(compose_path), str(run_root))
    validate_no_symlink_path(str(docker_path), str(run_root))
    validate_no_symlink_path(str(socket_path), str(run_root))
    _require_unix_socket(socket_path)
    if (
        _file_sha256(compose_path) != manifest.repository["compose_sha256"]
        or _file_sha256(docker_path) != manifest.docker["executable_sha256"]
    ):
        _reject()
    control_home = run_root / "control-home"
    try:
        if tuple(os.scandir(str(control_home))):
            _reject()
    except ControllerRejected:
        raise
    except OSError:
        raise ControllerRejected() from None
    controller_path = Path(__file__)
    if controller_path.is_symlink() or _file_sha256(PurePosixPath(str(controller_path))) != manifest.repository["controller_sha256"]:
        _reject()

    secret_root = PurePosixPath(str(manifest.secrets["directory"]))
    validate_no_symlink_path(str(secret_root), str(_SECRET_ROOT_PARENT))
    _require_private_directory(secret_root)
    secret_paths = {
        key: PurePosixPath(str(manifest.secrets[key]))
        for key in _SECRET_KEYS[1:]
    }
    for path in secret_paths.values():
        validate_no_symlink_path(str(path), str(_SECRET_ROOT_PARENT))
    site_manifest_path = secret_root / "site-init-manifest.json"
    execution_manifest_path = secret_root / "execution-manifest.json"
    for path in (site_manifest_path, execution_manifest_path):
        validate_no_symlink_path(str(path), str(_SECRET_ROOT_PARENT))
    if _read_host_regular(
        execution_manifest_path, 1_048_576, private=True
    ) != canonical_json_bytes(manifest.raw):
        _reject()
    if _read_host_regular(site_manifest_path, 65_536, private=True) != canonical_json_bytes(
        _site_initializer_document(manifest)
    ):
        _reject()
    policy_body = _read_host_regular(
        secret_paths["runtime_policy"], 16_384, private=True
    )
    if manifest.phase == "observe":
        if policy_body != b"null\n":
            _reject()
    elif policy_body != canonical_json_bytes(manifest.policy):
        _reject()
    for key in (
        "db_root_password",
        "site_admin_password",
        "site_db_password",
        "connection_commitment_key",
    ):
        body = _read_host_regular(secret_paths[key], 4_096, private=True)
        if len(body) < 32 or b"\n" in body or b"\r" in body or b"\x00" in body:
            _reject()
    for path in (
        PurePosixPath(str(manifest.evidence["directory"])),
        PurePosixPath(str(manifest.evidence["staging_directory"])),
    ):
        validate_no_symlink_path(str(path), str(run_root))
        if os.path.lexists(str(path)):
            _reject()


def _atomic_write(path: PurePosixPath, body: bytes) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor: int | None = None
    try:
        descriptor = os.open(str(temporary), flags, 0o600)
        with os.fdopen(descriptor, "wb", closefd=True) as stream:
            descriptor = None
            stream.write(body)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(str(temporary), str(path))
        directory = os.open(str(path.parent), os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except Exception:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass
        try:
            os.unlink(str(temporary))
        except OSError:
            pass
        raise _ControllerInternal() from None


def _write_discard(manifest: ControllerManifest, phase: str) -> None:
    evidence = PurePosixPath(str(manifest.evidence["directory"]))
    record = canonical_json_bytes(
        {
            "schema": _DISCARD_SCHEMA,
            "run_id": manifest.run_id,
            "phase": phase,
            "result": "discard",
            "generic_error": _GENERIC_FAILURE,
        }
    )
    path = evidence / "discard-results.jsonl"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        if os.path.lexists(str(evidence)):
            _reject()
        os.mkdir(str(evidence), 0o700)
        evidence_status = os.lstat(str(evidence))
        if not stat.S_ISDIR(evidence_status.st_mode):
            _reject()
        descriptor = os.open(str(path), flags, 0o600)
        with os.fdopen(descriptor, "wb", closefd=True) as stream:
            stream.write(record)
            stream.flush()
            os.fsync(stream.fileno())
    except OSError:
        raise _ControllerInternal() from None


def _teardown_receipt(manifest: ControllerManifest, success: bool) -> dict[str, object]:
    return {
        "schema": _TEARDOWN_SCHEMA,
        "run_id": manifest.run_id,
        "project": manifest.project,
        "run_label": manifest.run_label,
        "containers_absent": success,
        "network_absent": success,
        "volumes_absent": success,
        "secret_sources_absent": success,
        "result": "pass" if success else "fail",
    }


def _preflight(manifest: ControllerManifest) -> dict[str, object]:
    _validate_host_inputs(manifest)
    if manifest.policy is not None and (
        manifest.policy["artifact_manifest_sha256"]
        != _artifact_binding_sha256(manifest)
    ):
        _reject()
    environment = _execution_environment(manifest)
    base_configuration: dict[str, object] | None = None
    runner_observation: dict[str, object] | None = None
    for spec in _preflight_plan(manifest):
        result = _run_subprocess(spec, environment)
        observed = _validate_preflight_result(
            manifest,
            spec,
            result,
            base_configuration=base_configuration,
        )
        if spec.name == "inspect-base_image":
            if (
                observed is None
                or base_configuration is not None
                or set(observed) != {
                    "configuration", "configuration_sha256",
                }
            ):
                _reject()
            base_configuration = dict(observed["configuration"])
            _concrete_sha256(observed["configuration_sha256"])
        elif spec.name == "inspect-runner_image":
            if observed is None or runner_observation is not None:
                _reject()
            runner_observation = observed
        elif observed is not None:
            _reject()
    if base_configuration is None or runner_observation is None:
        _reject()
    return runner_observation


def _expected_container_services(manifest: ControllerManifest) -> dict[str, str]:
    expected = {
        f"{manifest.project}_db_primary": "db-primary",
        f"{manifest.project}_redis_cache": "redis-cache",
        f"{manifest.project}_site_init": "site-init",
        f"{manifest.project}_content_verifier": "content-verifier",
    }
    expected.update(
        {
            f"{manifest.project}_probe_{case_id}": "runtime-probe"
            for case_id in manifest.canaries
        }
    )
    return expected


def _inventory_resources(
    manifest: ControllerManifest,
    environment: Mapping[str, str],
) -> dict[str, tuple[tuple[str, str], ...]]:
    specs = _inventory_plan(manifest)
    results = [
        _run_subprocess(spec, environment)
        for spec in specs
    ]
    if any(
        result.returncode != 0 or result.timed_out or result.stderr
        for result in results
    ):
        _reject()
    expected_containers = _expected_container_services(manifest)
    expected_volumes = frozenset(str(value) for value in manifest.compose["volumes"])
    discovered: dict[str, dict[str, str]] = {
        "containers": {},
        "networks": {},
        "volumes": {},
    }
    for spec, result in zip(specs, results, strict=True):
        resource = spec.name.split("-")[2]
        for line in _parse_fixed_lines(result.stdout):
            fields = line.split("\t")
            if resource == "containers":
                if (
                    len(fields) != 5
                    or _SHA256_RE.fullmatch(fields[0]) is None
                    or expected_containers.get(fields[1]) != fields[4]
                    or fields[2] != manifest.run_id
                    or fields[3] != manifest.project
                ):
                    _reject()
                identifier, name = fields[0], fields[1]
            elif resource == "networks":
                if (
                    len(fields) != 5
                    or _SHA256_RE.fullmatch(fields[0]) is None
                    or fields[1] != manifest.compose["network"]
                    or fields[2] != "bridge"
                    or fields[3] != manifest.run_id
                    or fields[4] != manifest.project
                ):
                    _reject()
                identifier, name = fields[0], fields[1]
            else:
                if (
                    resource != "volumes"
                    or len(fields) != 5
                    or fields[0] not in expected_volumes
                    or fields[1] != "local"
                    or fields[2] != "local"
                    or fields[3] != manifest.run_id
                    or fields[4] != manifest.project
                ):
                    _reject()
                identifier = name = fields[0]
            previous = discovered[resource].get(identifier)
            if previous is not None and previous != name:
                _reject()
            discovered[resource][identifier] = name
    for resource in discovered.values():
        if len(set(resource.values())) != len(resource):
            _reject()
    return {
        key: tuple(sorted(values.items()))
        for key, values in discovered.items()
    }


def _remove_secret_sources(manifest: ControllerManifest) -> bool:
    directory = PurePosixPath(str(manifest.secrets["directory"]))
    expected = (
        *(PurePosixPath(str(manifest.secrets[key])) for key in _SECRET_KEYS[1:-1]),
        PurePosixPath(str(manifest.secrets["runtime_policy"])),
        directory / "site-init-manifest.json",
        directory / "execution-manifest.json",
    )
    try:
        if not os.path.exists(str(directory)):
            return True
        directory_status = os.lstat(str(directory))
        if not stat.S_ISDIR(directory_status.st_mode):
            return False
        for path in expected:
            if not os.path.exists(str(path)):
                continue
            status = os.lstat(str(path))
            if not stat.S_ISREG(status.st_mode) or status.st_nlink != 1:
                return False
            os.unlink(str(path))
        os.rmdir(str(directory))
        return True
    except OSError:
        return False


def _recover_teardown(manifest: ControllerManifest) -> bool:
    environment = _execution_environment(manifest)
    try:
        inventory = _inventory_resources(manifest, environment)
        removal_specs: list[CommandSpec] = []
        for identifier, _name in inventory["containers"]:
            removal_specs.append(
                _spec(
                    manifest,
                    "teardown-remove-container-id",
                    manifest.docker_prefix
                    + ("container", "rm", "--force", identifier),
                    teardown=True,
                )
            )
        for identifier, _name in inventory["networks"]:
            removal_specs.append(
                _spec(
                    manifest,
                    "teardown-remove-network-id",
                    manifest.docker_prefix + ("network", "rm", identifier),
                    teardown=True,
                )
            )
        for name, _display in inventory["volumes"]:
            removal_specs.append(
                _spec(
                    manifest,
                    "teardown-remove-volume-name",
                    manifest.docker_prefix + ("volume", "rm", name),
                    teardown=True,
                )
            )
        for spec in removal_specs:
            result = _run_subprocess(spec, environment)
            if result.returncode != 0 or result.timed_out or result.stderr:
                return False
        remaining = _inventory_resources(manifest, environment)
        if any(remaining.values()):
            return False
        return _remove_secret_sources(manifest)
    except (ControllerRejected, _ControllerInternal):
        return False


_OBSERVATION_RESULT_KEYS: Final = (
    "schema",
    "mode",
    "run_id",
    "result",
    "error",
    "wrapper_module",
    "wrapper_class",
    "raw_module",
    "raw_class",
    "driver",
    "driver_distribution",
    "driver_version",
    "server_version",
    "initial_transaction_inactive",
    "isolation_repeatable_read",
    "transaction_read_only",
    "consistent_snapshot_started",
    "transaction_active",
    "wrapper_stable",
    "raw_connection_stable",
    "server_connection_stable",
    "rollback_no_chain_succeeded",
    "final_transaction_inactive",
    "connection_id_commitment",
    "primary_route",
    "replica_denied",
    "partial_output",
)
_VALIDATION_RESULT_KEYS: Final = (
    "schema",
    "mode",
    "run_id",
    "case_id",
    "result",
    "error",
    "expected_outcome",
    "actual_outcome",
    "pre_state",
    "active_state",
    "post_state",
    "wrapper_stable",
    "raw_connection_stable",
    "server_connection_stable",
    "primary_route",
    "replica_denied",
    "normal_physical_close",
    "exceptional_physical_close",
    "post_failure_frappe_calls",
    "partial_output",
)


def _safe_state(value: object, *, allow_none: bool = False) -> None:
    if allow_none and value is None:
        return
    state = _closed_object(value, ("active", "isolation", "read_only"))
    if type(state["active"]) is not int or state["active"] not in (0, 1):
        _reject()
    _text(state["isolation"])
    if state["read_only"] is not None and (
        type(state["read_only"]) is not int or state["read_only"] not in (0, 1)
    ):
        _reject()


def _validate_probe_record(
    manifest: ControllerManifest,
    case_id: str,
    value: object,
) -> dict[str, object]:
    if manifest.phase == "observe":
        record = _closed_object(value, _OBSERVATION_RESULT_KEYS)
        if (
            case_id != "environment_observation"
            or record["schema"] != "erpai.gl_tb.runtime_compat.observation.v2"
            or record["mode"] != "observe"
            or record["run_id"] != manifest.run_id
            or record["result"] != "pass"
            or record["error"] != ""
            or record["driver"] not in ("pymysql", "mysqlclient")
            or record["primary_route"] is not True
            or record["replica_denied"] is not True
            or record["partial_output"] is not False
        ):
            _reject()
        for key in (
            "wrapper_module",
            "wrapper_class",
            "raw_module",
            "raw_class",
            "driver_distribution",
            "driver_version",
            "server_version",
        ):
            _text(record[key])
        expected_identity = {
            "pymysql": (
                "frappe.database.mariadb.database",
                "pymysql.connections",
                "PyMySQL",
                "1.1.2",
            ),
            "mysqlclient": (
                "frappe.database.mariadb.mysqlclient",
                "MySQLdb.connections",
                "mysqlclient",
                "2.2.7",
            ),
        }[record["driver"]]
        if (
            record["wrapper_module"],
            record["raw_module"],
            record["driver_distribution"],
            record["driver_version"],
        ) != expected_identity:
            _reject()
        for key in (
            "initial_transaction_inactive",
            "isolation_repeatable_read",
            "transaction_read_only",
            "consistent_snapshot_started",
            "transaction_active",
            "wrapper_stable",
            "raw_connection_stable",
            "server_connection_stable",
            "rollback_no_chain_succeeded",
            "final_transaction_inactive",
        ):
            if record[key] is not True:
                _reject()
        _sha256(record["connection_id_commitment"])
        return record

    record = _closed_object(value, _VALIDATION_RESULT_KEYS)
    expected_outcome = (
        "success"
        if case_id in ("normal_snapshot", "binding_stability")
        else "controlled_rejection"
    )
    if (
        record["schema"] != "erpai.gl_tb.runtime_compat.validation.v1"
        or record["mode"] != "validate"
        or record["run_id"] != manifest.run_id
        or record["case_id"] != case_id
        or record["result"] != "pass"
        or record["error"] != ""
        or record["expected_outcome"] != expected_outcome
        or record["actual_outcome"] != expected_outcome
        or record["primary_route"] is not True
        or record["replica_denied"] is not True
        or type(record["post_failure_frappe_calls"]) is not int
        or record["post_failure_frappe_calls"] != 0
        or record["partial_output"] is not False
    ):
        _reject()
    for key in (
        "wrapper_stable",
        "raw_connection_stable",
        "server_connection_stable",
        "normal_physical_close",
        "exceptional_physical_close",
    ):
        if type(record[key]) is not bool:
            _reject()
    _safe_state(record["pre_state"])
    _safe_state(record["active_state"], allow_none=True)
    _safe_state(record["post_state"], allow_none=True)
    if expected_outcome == "success":
        if not (
            record["wrapper_stable"]
            and record["raw_connection_stable"]
            and record["server_connection_stable"]
            and record["normal_physical_close"] is False
            and record["exceptional_physical_close"] is False
        ):
            _reject()
    else:
        if record["exceptional_physical_close"] is not True:
            _reject()
    return record


def _probe_tar_record(
    manifest: ControllerManifest,
    case_id: str,
    body: bytes,
) -> dict[str, object]:
    if len(body) > manifest.limits["evidence_max_bytes"]:
        _reject()
    expected = (
        "observation-result.json"
        if manifest.phase == "observe"
        else "validation-result.json"
    )
    try:
        with tarfile.open(fileobj=io.BytesIO(body), mode="r:") as archive:
            members = archive.getmembers()
            if len(members) != 1:
                _reject()
            member = members[0]
            if (
                member.name != expected
                or not member.isreg()
                or member.size <= 0
                or member.size > manifest.limits["evidence_max_bytes"]
                or member.linkname
            ):
                _reject()
            stream = archive.extractfile(member)
            if stream is None:
                _reject()
            payload = stream.read(manifest.limits["evidence_max_bytes"] + 1)
            if len(payload) != member.size:
                _reject()
    except ControllerRejected:
        raise
    except (tarfile.TarError, OSError, ValueError):
        raise ControllerRejected() from None
    return _validate_probe_record(manifest, case_id, _decode_json(payload))


def _mount_summary(value: str) -> frozenset[str]:
    if not value.endswith(",") or value == ",":
        _reject()
    records = value[:-1].split(",")
    if not records or len(records) != len(set(records)):
        _reject()
    normalized: set[str] = set()
    for record in records:
        kind, separator, destination = record.partition("=")
        if (
            not separator
            or kind not in ("bind", "tmpfs", "volume")
            or str(_strict_absolute_path(destination)) != destination
        ):
            _reject()
        normalized.add(f"{kind}={destination}")
    return frozenset(normalized)


def _validate_probe_container(
    manifest: ControllerManifest,
    case_id: str,
    result: _CommandResult,
) -> str:
    if result.returncode != 0 or result.timed_out or result.stderr:
        _reject()
    lines = _parse_fixed_lines(result.stdout)
    expected_name = f"{manifest.project}_probe_{case_id}"
    if len(lines) != 1:
        _reject()
    fields = lines[0].split("\t")
    expected_mounts = frozenset((
        "volume=/home/frappe/frappe-bench/sites",
        "tmpfs=/tmp",
        "tmpfs=/evidence",
        "bind=/run/secrets/connection-commitment-key",
        "bind=/run/secrets/execution-manifest.json",
        "bind=/run/secrets/runtime-policy.json",
    ))
    if (
        len(fields) != 19
        or _SHA256_RE.fullmatch(fields[0]) is None
        or fields[1] != manifest.artifacts["runner_image_id"]
        or fields[2] != f"/{expected_name}"
        or fields[3:7] != ["exited", "false", "0", "false"]
        or fields[7] != manifest.compose["network"]
        or fields[8] != "false"
        or fields[9] != "1000:1000"
        or fields[10] != "true"
        or _strict_json_string_list(fields[11]) != ("ALL",)
        or _strict_json_string_list(fields[12])
        != ("no-new-privileges:true",)
        or _strict_json_string_list(fields[13])
        != (
            "/opt/erpai/"
            "finance_gl_trial_balance_runtime_compatibility_probe.py",
        )
        or _strict_json_string_list(fields[14])
        != _probe_args(manifest, case_id)
        or _mount_summary(fields[15]) != expected_mounts
        or fields[16] != manifest.run_id
        or fields[17] != manifest.project
        or fields[18] != "runtime-probe"
    ):
        _reject()
    return fields[0]


def _process_receipt(spec: CommandSpec, result: _CommandResult) -> dict[str, object]:
    return {
        "name": spec.name,
        "exit_code": result.returncode,
        "timed_out": result.timed_out,
        "stdout_sha256": hashlib.sha256(result.stdout).hexdigest(),
        "stderr_sha256": hashlib.sha256(result.stderr).hexdigest(),
    }


def _artifact_binding_sha256(manifest: ControllerManifest) -> str:
    value = {
        "repository": dict(manifest.repository),
        "artifacts": dict(manifest.artifacts),
        "docker": {
            key: manifest.docker[key]
            for key in (
                "executable_sha256", "compose_version", "client_version",
                "client_api_version", "server_version", "server_api_version",
                "daemon_id", "daemon_name", "docker_root_dir",
                "security_options_sha256", "daemon_lifecycle_owner",
                "buildkit_version", "frontend_capabilities_sha256",
                "cgroup_driver", "cgroup_version", "cgroup_authority",
                "os", "architecture",
            )
        },
        "source_content": dict(manifest.source_content),
    }
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _remove_failed_staging(manifest: ControllerManifest) -> bool:
    staging = PurePosixPath(str(manifest.evidence["staging_directory"]))
    try:
        if not os.path.exists(str(staging)):
            return True
        status = os.lstat(str(staging))
        if not stat.S_ISDIR(status.st_mode):
            return False
        names = tuple(sorted(os.listdir(str(staging))))
        if any(name not in _EVIDENCE_FILES for name in names):
            return False
        paths = tuple(staging / name for name in names)
        for path in paths:
            item = os.lstat(str(path))
            if not stat.S_ISREG(item.st_mode) or item.st_nlink != 1:
                return False
        for path in paths:
            os.unlink(str(path))
        os.rmdir(str(staging))
        return True
    except OSError:
        return False


def _promote_evidence(
    manifest: ControllerManifest,
    materialization_attestation: Mapping[str, object],
    probe_records: Sequence[dict[str, object]],
    process_records: Sequence[dict[str, object]],
) -> None:
    if manifest.policy is not None and (
        manifest.policy["artifact_manifest_sha256"]
        != _artifact_binding_sha256(manifest)
    ):
        _reject()
    staging = PurePosixPath(str(manifest.evidence["staging_directory"]))
    evidence = PurePosixPath(str(manifest.evidence["directory"]))
    try:
        if os.path.exists(str(staging)) or os.path.exists(str(evidence)):
            _reject()
        os.mkdir(str(staging), 0o700)
    except ControllerRejected:
        raise
    except OSError:
        raise _ControllerInternal() from None

    artifact = canonical_json_bytes(_artifact_provenance(manifest, materialization_attestation))
    teardown = canonical_json_bytes(_teardown_receipt(manifest, True))
    if manifest.phase == "observe":
        observation = canonical_json_bytes(
            {
                "schema": "erpai.gl_tb.runtime_compat.observation_bundle.v1",
                "run_id": manifest.run_id,
                "result": "pass",
                "observation": probe_records[0],
                "processes": list(process_records),
            }
        )
        validation = canonical_json_bytes(
            {
                "schema": "erpai.gl_tb.runtime_compat.validation_reference.v1",
                "result": "not_run",
            }
        )
    else:
        observation = canonical_json_bytes(
            {
                "schema": "erpai.gl_tb.runtime_compat.observation_reference.v1",
                "sha256": manifest.policy["observation_result_sha256"],
                "result": "owner_approved_reference",
            }
        )
        validation = canonical_json_bytes(
            {
                "schema": "erpai.gl_tb.runtime_compat.validation_bundle.v1",
                "run_id": manifest.run_id,
                "result": "pass",
                "results": list(probe_records),
                "processes": list(process_records),
            }
        )
    bodies = {
        "artifact-provenance.json": artifact,
        "observation-result.json": observation,
        "validation-result.json": validation,
        "discard-results.jsonl": b"",
        "teardown-receipt.json": teardown,
    }
    for name, body in bodies.items():
        _atomic_write(staging / name, body)
    manifest_body = b"".join(
        f"{hashlib.sha256(bodies[name]).hexdigest()}  {name}\n".encode("ascii")
        for name in _EVIDENCE_FILES[:-1]
    )
    _atomic_write(staging / "evidence-manifest.sha256", manifest_body)
    try:
        os.replace(str(staging), str(evidence))
    except OSError:
        raise _ControllerInternal() from None


def _promote_or_discard(
    manifest: ControllerManifest,
    materialization_attestation: Mapping[str, object],
    probe_records: Sequence[dict[str, object]],
    process_records: Sequence[dict[str, object]],
) -> None:
    try:
        _promote_evidence(
            manifest, materialization_attestation, probe_records, process_records
        )
    except BaseException:
        staging_removed = _remove_failed_staging(manifest)
        discard_written = False
        evidence = PurePosixPath(str(manifest.evidence["directory"]))
        final_absent = not os.path.lexists(str(evidence))
        if staging_removed and final_absent:
            try:
                _write_discard(manifest, manifest.phase)
                discard_written = True
            except BaseException:
                discard_written = False
        if not staging_removed or not discard_written:
            raise _ControllerInternal() from None
        _reject()


def _execute_phase(manifest: ControllerManifest) -> None:
    """Execute one closed point; incomplete materialization is discard-only."""

    runner_observation = _preflight(manifest)
    environment = _execution_environment(manifest)
    phase_ok = True
    content_id: str | None = None
    content_archives: dict[
        str, dict[str, dict[str, object]]
    ] = {}
    filesystem_observation: dict[str, object] | None = None
    containment_observation: dict[str, object] | None = None
    probe_records: list[dict[str, object]] = []
    process_records: list[dict[str, object]] = []
    probe_ids: dict[str, str] = {}
    for spec in _phase_plan(manifest):
        try:
            actual_spec = spec
            if spec.name in (
                "content-verify-container",
                "content-copy-apps",
                "content-copy-erpai",
                "content-copy-python",
                "content-verify-retire",
            ):
                if content_id is None:
                    _reject()
                argv = tuple(
                    item.replace("__INSPECTED_CONTENT_ID__", content_id)
                    for item in spec.argv
                )
                actual_spec = replace(spec, argv=argv)
            elif spec.name.startswith(("copy-evidence-", "retire-probe-")):
                prefix = (
                    "copy-evidence-"
                    if spec.name.startswith("copy-evidence-")
                    else "retire-probe-"
                )
                case_id = spec.name.removeprefix(prefix)
                identifier = probe_ids.get(case_id)
                if identifier is None:
                    _reject()
                argv = list(spec.argv)
                if prefix == "copy-evidence-":
                    _container, separator, source = argv[-2].partition(":")
                    if not separator or not source.startswith("/evidence/"):
                        _reject()
                    argv[-2] = f"{identifier}:{source}"
                else:
                    argv[-1] = identifier
                actual_spec = replace(spec, argv=tuple(argv))
            result = _run_subprocess(actual_spec, environment)
            process_records.append(_process_receipt(actual_spec, result))
            if result.returncode != 0 or result.timed_out:
                _reject()
            if spec.name == "content-verify-create":
                content_id = _validate_content_create_result(result)
            elif spec.name == "content-verify-container":
                inspected_id, containment_observation = (
                    _validate_content_container(
                        manifest, content_id, result
                    )
                )
                if inspected_id != content_id:
                    _reject()
            elif spec.name.startswith("content-copy-"):
                if result.stderr:
                    _reject()
                archive_name = spec.name.removeprefix("content-copy-")
                if archive_name in content_archives:
                    _reject()
                content_archives[archive_name] = _parse_content_archive(
                    manifest, archive_name, result.stdout
                )
            elif spec.name == "content-verify-retire":
                if (
                    result.stderr
                    or _parse_fixed_lines(result.stdout) != (content_id,)
                    or containment_observation is None
                ):
                    _reject()
                filesystem_observation = _final_filesystem_from_archives(
                    manifest, content_archives
                )
                containment_observation[
                    "verification_container_retired"
                ] = True
            elif spec.name.startswith("inspect-probe-"):
                case_id = spec.name.removeprefix("inspect-probe-")
                probe_ids[case_id] = _validate_probe_container(
                    manifest, case_id, result
                )
            elif spec.name.startswith("copy-evidence-"):
                probe_records.append(_probe_tar_record(
                    manifest,
                    spec.name.removeprefix("copy-evidence-"),
                    result.stdout,
                ))
            elif spec.name.startswith("retire-probe-"):
                if result.stderr:
                    _reject()
            elif spec.name.startswith("probe-wait-"):
                if result.stdout or result.stderr:
                    _reject()
            elif spec.name == "site-initialize":
                if (
                    result.stderr
                    or _parse_fixed_lines(result.stdout) != ("initialized",)
                ):
                    _reject()
        except (ControllerRejected, _ControllerInternal):
            phase_ok = False
            break
        except BaseException:
            phase_ok = False
            break
    try:
        teardown_ok = _recover_teardown(manifest)
    except BaseException:
        teardown_ok = False
    if (
        not phase_ok
        or not teardown_ok
        or filesystem_observation is None
        or containment_observation is None
        or len(probe_records) != len(manifest.canaries)
    ):
        _write_discard(manifest, manifest.phase)
        _reject()
    try:
        materialization_attestation = _build_materialization_attestation(
            manifest,
            runner_observation,
            filesystem_observation,
            containment_observation,
        )
    except BaseException:
        _write_discard(manifest, manifest.phase)
        _reject()
    _promote_or_discard(
        manifest,
        materialization_attestation,
        probe_records,
        process_records,
    )


def _parse_cli(argv: Sequence[str]) -> tuple[str, str]:
    if (
        len(argv) != 3
        or argv[0] not in _COMMANDS
        or argv[1] != "--manifest"
        or type(argv[2]) is not str
    ):
        _reject()
    return argv[0], argv[2]


def main(argv: Sequence[str] | None = None) -> int:
    arguments = tuple(sys.argv[1:] if argv is None else argv)
    try:
        command, manifest_path = _parse_cli(arguments)
        manifest = load_and_validate_manifest(manifest_path)
        if command == "preflight":
            _preflight(manifest)
        elif command == "recover-teardown":
            if not _recover_teardown(manifest):
                _reject()
        else:
            if command != manifest.phase:
                _reject()
            _execute_phase(manifest)
        return 0
    except (ControllerRejected, _ControllerInternal):
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
