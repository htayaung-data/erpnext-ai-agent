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
    "validate_no_symlink_path",
]


_GENERIC_FAILURE: Final = "runtime_compatibility_unavailable"
_EXECUTION_SCHEMA: Final = "erpai.gl_tb.runtime_compat.execution.v1"
_ARTIFACT_SCHEMA: Final = "erpai.gl_tb.runtime_compat.artifact_provenance.v1"
_TEARDOWN_SCHEMA: Final = "erpai.gl_tb.runtime_compat.teardown.v1"
_DISCARD_SCHEMA: Final = "erpai.gl_tb.runtime_compat.discard.v1"
_RUN_ROOT_PARENT: Final = PurePosixPath(
    "/tmp/erpai-finance-gl-tb-runtime-compat"
)
_SECRET_ROOT_PARENT: Final = PurePosixPath(
    "/dev/shm/erpai-finance-gl-tb-runtime-compat"
)
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
_IMAGE_FORMAT: Final = (
    "{{.Id}}\\t{{json .RepoDigests}}\\t{{.Os}}\\t{{.Architecture}}"
)
_CONTAINER_FORMAT: Final = (
    "{{.Id}}\\t{{.Image}}\\t{{.Name}}\\t{{.State.Status}}\\t"
    "{{.State.Running}}\\t{{.State.ExitCode}}\\t{{.State.OOMKilled}}\\t"
    "{{.HostConfig.NetworkMode}}\\t{{.HostConfig.Privileged}}\\t"
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


def _positive_int(value: object) -> int:
    if type(value) is not int or value <= 0:
        _reject()
    return value


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
    return image


def _docker_endpoint(value: object, run_root: PurePosixPath) -> str:
    endpoint = _text(value)
    if endpoint in _DEFAULT_ENDPOINTS or not endpoint.startswith("unix://"):
        _reject()
    socket_path = _strict_absolute_path(endpoint.removeprefix("unix://"))
    expected = run_root / "docker" / "docker.sock"
    if socket_path != expected:
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
)
_ARTIFACT_KEYS: Final = (
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
        _sha256(repository[key])

    artifacts = _closed_object(document["artifacts"], _ARTIFACT_KEYS)
    for key in ("runner_image", "mariadb_image", "redis_image"):
        _immutable_image(artifacts[key])
    for key in ("runner_image_id", "mariadb_image_id", "redis_image_id"):
        _text(artifacts[key], pattern=_IMAGE_ID_RE)

    docker = _closed_object(document["docker"], _DOCKER_KEYS)
    executable = _strict_absolute_path(docker["executable"])
    if executable.name != "docker":
        _reject()
    _sha256(docker["executable_sha256"])
    _docker_endpoint(docker["endpoint"], run_root)
    for key in (
        "compose_version",
        "client_version",
        "client_api_version",
        "server_version",
        "server_api_version",
    ):
        _text(docker[key], pattern=_SAFE_TEXT_RE)
    if docker["os"] != "linux" or docker["architecture"] not in ("amd64", "arm64"):
        _reject()

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
        _spec(manifest, "compose-version", docker + ("compose", "version", "--short")),
    ]
    for key in ("runner_image", "mariadb_image", "redis_image"):
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


def _phase_plan(manifest: ControllerManifest) -> tuple[CommandSpec, ...]:
    compose = manifest.compose_prefix
    setup_timeout = str(manifest.limits["setup_timeout_seconds"])
    plans: list[CommandSpec] = [
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
    ]
    for case_id in manifest.canaries:
        container = f"{manifest.project}_probe_{case_id}"
        if manifest.phase == "observe":
            probe_args = (
                "observe",
                "--manifest",
                "/run/secrets/execution-manifest.json",
                "--output",
                "/evidence/observation-result.json",
            )
        else:
            probe_args = (
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


def _validate_preflight_result(manifest: ControllerManifest, spec: CommandSpec, result: _CommandResult) -> None:
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
    elif spec.name == "compose-version":
        if lines != (manifest.docker["compose_version"],):
            _reject()
    elif spec.name.startswith("inspect-"):
        key = spec.name.removeprefix("inspect-")
        id_key = key.replace("_image", "_image_id")
        if len(lines) != 1:
            _reject()
        fields = lines[0].split("\t")
        if (
            len(fields) != 4
            or fields[0] != manifest.artifacts[id_key]
            or manifest.artifacts[key] not in fields[1]
            or fields[2] != manifest.docker["os"]
            or fields[3] != manifest.docker["architecture"]
        ):
            _reject()
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


def _artifact_provenance(manifest: ControllerManifest) -> dict[str, object]:
    return {
        "schema": _ARTIFACT_SCHEMA,
        "run_id": manifest.run_id,
        "repository": dict(manifest.repository),
        "artifacts": dict(manifest.artifacts),
        "docker": {
            "executable_sha256": manifest.docker["executable_sha256"],
            "compose_version": manifest.docker["compose_version"],
            "client_version": manifest.docker["client_version"],
            "client_api_version": manifest.docker["client_api_version"],
            "server_version": manifest.docker["server_version"],
            "server_api_version": manifest.docker["server_api_version"],
            "os": manifest.docker["os"],
            "architecture": manifest.docker["architecture"],
        },
        "result": "verified",
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
    flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, "O_NOFOLLOW", 0)
    try:
        if not os.path.exists(str(evidence)):
            os.mkdir(str(evidence), 0o700)
        evidence_status = os.lstat(str(evidence))
        if not stat.S_ISDIR(evidence_status.st_mode):
            _reject()
        descriptor = os.open(str(path), flags, 0o600)
        with os.fdopen(descriptor, "ab", closefd=True) as stream:
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


def _preflight(manifest: ControllerManifest) -> None:
    _validate_host_inputs(manifest)
    if manifest.policy is not None and (
        manifest.policy["artifact_manifest_sha256"]
        != _artifact_binding_sha256(manifest)
    ):
        _reject()
    environment = _execution_environment(manifest)
    for spec in _preflight_plan(manifest):
        result = _run_subprocess(spec, environment)
        _validate_preflight_result(manifest, spec, result)


def _expected_container_services(manifest: ControllerManifest) -> dict[str, str]:
    expected = {
        f"{manifest.project}_db_primary": "db-primary",
        f"{manifest.project}_redis_cache": "redis-cache",
        f"{manifest.project}_site_init": "site-init",
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
    "transaction_state",
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
            or record["schema"] != "erpai.gl_tb.runtime_compat.observation.v1"
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
        _sha256(record["connection_id_commitment"])
        _safe_state(record["transaction_state"])
        if record["transaction_state"]["active"] != 0:
            _reject()
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
    if (
        len(fields) != 12
        or _SHA256_RE.fullmatch(fields[0]) is None
        or fields[1] != manifest.artifacts["runner_image_id"]
        or fields[2] != f"/{expected_name}"
        or fields[3:7] != ["exited", "false", "0", "false"]
        or fields[7] != manifest.compose["network"]
        or fields[8] != "false"
        or fields[9] != manifest.run_id
        or fields[10] != manifest.project
        or fields[11] != "runtime-probe"
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
                "executable_sha256",
                "compose_version",
                "client_version",
                "client_api_version",
                "server_version",
                "server_api_version",
                "os",
                "architecture",
            )
        },
    }
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _promote_evidence(
    manifest: ControllerManifest,
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

    artifact = canonical_json_bytes(_artifact_provenance(manifest))
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


def _execute_phase(manifest: ControllerManifest) -> None:
    """Execute the closed phase plan; any incomplete point is discard-only.

    Probe artifacts stay in memory until exact resource teardown is proven.
    Only then is one complete point promoted atomically.
    """

    _preflight(manifest)
    environment = _execution_environment(manifest)
    phase_ok = True
    probe_records: list[dict[str, object]] = []
    process_records: list[dict[str, object]] = []
    probe_ids: dict[str, str] = {}
    for spec in _phase_plan(manifest):
        try:
            actual_spec = spec
            if spec.name.startswith(("copy-evidence-", "retire-probe-")):
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
            if spec.name.startswith("inspect-probe-"):
                case_id = spec.name.removeprefix("inspect-probe-")
                probe_ids[case_id] = _validate_probe_container(
                    manifest, case_id, result
                )
            elif spec.name.startswith("copy-evidence-"):
                probe_records.append(
                    _probe_tar_record(
                        manifest,
                        spec.name.removeprefix("copy-evidence-"),
                        result.stdout,
                    )
                )
            elif spec.name.startswith("retire-probe-"):
                if result.stderr:
                    _reject()
            elif spec.name.startswith("probe-wait-"):
                if result.stdout or result.stderr:
                    _reject()
            elif spec.name == "site-initialize":
                if result.stderr or _parse_fixed_lines(result.stdout) != ("initialized",):
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
        or len(probe_records) != len(manifest.canaries)
    ):
        _write_discard(manifest, manifest.phase)
        _reject()
    _promote_evidence(manifest, probe_records, process_records)


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
