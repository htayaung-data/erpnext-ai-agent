from __future__ import annotations

import builtins
import copy
import hashlib
import importlib.util
import io
import json
import os
import socket
import stat
import subprocess
import sys
import tarfile
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock


STAGE = Path(__file__).resolve().parent
CONTROLLER_PATH = STAGE / "finance_gl_trial_balance_runtime_compatibility_controller.py"
PROBE_PATH = STAGE / "finance_gl_trial_balance_runtime_compatibility_probe.py"
INITIALIZER_PATH = STAGE / "finance_gl_trial_balance_runtime_compatibility_site_initializer.py"
DOCKERFILE_PATH = STAGE / "finance_gl_trial_balance_runtime_compatibility_runner.Dockerfile"
COMPOSE_PATH = STAGE / "finance_gl_trial_balance_runtime_compatibility.compose.yaml"

RUN_ID = "0123456789ab"
RUN_ROOT = f"/tmp/erpai-finance-gl-tb-runtime-compat/{RUN_ID}"
SECRET_ROOT = f"/dev/shm/erpai-finance-gl-tb-runtime-compat/{RUN_ID}"
PROJECT = f"gl_tb_rtcompat_{RUN_ID}"
RUN_LABEL = f"com.erpai.finance.gl_tb_rtcompat.run={RUN_ID}"
REVISION = "e40201b2266604f7a85065d0be8525a59f0ab605"
SHA_A = hashlib.sha256(b"route-b-fixture-a").hexdigest()
SHA_B = hashlib.sha256(b"route-b-fixture-b").hexdigest()
SHA_C = hashlib.sha256(b"route-b-fixture-c").hexdigest()
IMAGE_A = f"registry.example/erpai/runner@sha256:{SHA_A}"
IMAGE_B = f"registry.example/library/mariadb@sha256:{SHA_B}"
IMAGE_C = f"registry.example/library/redis@sha256:{SHA_C}"
BASE_IMAGE = "docker.io/frappe/erpnext@sha256:63e3db0e981a6e34e250635fa6f1d52cb96e10f66e6f34393c80b6fe4329c2d0"
FRAPPE_REVISION = "4dfcc56090eb3101d18ddb03750391511f163fcf"
ERPNEXT_REVISION = "d74a649016d8bb12ee3c5a24361171cebe860bfc"
PYTHON_PATH = "/usr/local/bin/python3.14"
SECURITY_OPTIONS_JSON = '["name=rootless","name=seccomp,profile=builtin"]'


def _fixture_hash(value: object) -> str:
    body = json.dumps(
        value, allow_nan=False, ensure_ascii=False,
        separators=(",", ":"), sort_keys=True,
    ).encode() + b"\n"
    return hashlib.sha256(body).hexdigest()


def _entry(
    path: str, kind: str, sha: str, *, size: int,
    uid: int = 7, gid: int = 8, mode: str = "0644",
) -> dict[str, object]:
    return {
        "path": path, "type": kind, "sha256": sha, "size_bytes": size,
        "uid": uid, "gid": gid, "mode": mode,
    }


def _source_content() -> dict[str, object]:
    source_context = [
        _entry("frappe", "tree", SHA_A, size=101),
        _entry("erpnext", "tree", SHA_B, size=102),
        _entry("erp_workspace_ui/erp_workspace_ui/__init__.py", "regular", SHA_C, size=0),
        _entry("erp_workspace_ui/erp_workspace_ui/finance_accounting/__init__.py", "regular", SHA_A, size=1),
        _entry("erp_workspace_ui/erp_workspace_ui/finance_accounting/gl_trial_balance_core.py", "regular", SHA_B, size=201),
        _entry("erp_workspace_ui/erp_workspace_ui/finance_accounting/gl_trial_balance_adapter.py", "regular", SHA_C, size=202),
        _entry("erp_workspace_ui/erp_workspace_ui/finance_accounting/gl_trial_balance_frappe_runtime.py", "regular", SHA_A, size=203),
        _entry("finance_gl_trial_balance_runtime_compatibility_probe.py", "regular", SHA_B, size=204),
        _entry("finance_gl_trial_balance_runtime_compatibility_site_initializer.py", "regular", SHA_C, size=205),
    ]
    build_manifest = {
        "schema": "erpai.gl_tb.runtime_compat.build_context.v1",
        "source_repository_revision": REVISION,
        "frappe_revision": FRAPPE_REVISION,
        "erpnext_revision": ERPNEXT_REVISION,
        "entries": copy.deepcopy(source_context),
        "entries_sha256": _fixture_hash(source_context),
    }
    build_manifest_body = json.dumps(
        build_manifest, allow_nan=False, ensure_ascii=False,
        separators=(",", ":"), sort_keys=True,
    ).encode() + b"\n"
    build_manifest_sha = hashlib.sha256(build_manifest_body).hexdigest()
    context = source_context + [
        _entry(
            "runner-content-build-manifest.json", "regular",
            build_manifest_sha, size=len(build_manifest_body),
        )
    ]
    return {
        "schema": "erpai.gl_tb.runtime_compat.source_content.v1",
        "source_repository_revision": REVISION,
        "base": {"reference": BASE_IMAGE, "image_id": f"sha256:{SHA_B}"},
        "frontend": {
            "policy": "engine_builtin", "dockerfile_sha256": SHA_A,
            "engine_version": "28.5.2", "engine_api_version": "1.51",
            "buildkit_version": "v0.25.1",
            "frontend_capabilities_sha256": SHA_B,
        },
        "sources": {
            "frappe": {"revision": FRAPPE_REVISION, "tree_sha256": SHA_A},
            "erpnext": {"revision": ERPNEXT_REVISION, "tree_sha256": SHA_B},
        },
        "python": {
            "path": PYTHON_PATH, "version": "3.14.2",
            "executable_sha256": SHA_C, "size_bytes": 999,
            "uid": 0, "gid": 0, "mode": "0755",
        },
        "build_context": {
            "entries": context,
            "manifest_sha256": _fixture_hash(context),
            "build_manifest": build_manifest,
        },
        "gl_tb": {
            "package_initializer_sha256": SHA_C,
            "finance_initializer_sha256": SHA_A,
            "core_sha256": SHA_B,
            "adapter_sha256": SHA_C,
            "runtime_sha256": SHA_A,
            "probe_sha256": SHA_B,
            "initializer_sha256": SHA_C,
            "build_manifest_sha256": build_manifest_sha,
        },
    }


def _load_exact(path: Path, name: str) -> types.ModuleType:
    if not path.is_file() or path.is_symlink():
        raise AssertionError(f"missing or substituted staged source: {path.name}")
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot load staged source: {path.name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return module


controller = _load_exact(CONTROLLER_PATH, "_gl_tb_runtime_compat_controller_test")
probe = _load_exact(PROBE_PATH, "_gl_tb_runtime_compat_probe_test")
initializer = _load_exact(INITIALIZER_PATH, "_gl_tb_runtime_compat_initializer_test")


def _policy() -> dict[str, object]:
    values: dict[str, object] = {}
    for key in controller._POLICY_KEYS:
        if key == "expected_driver":
            values[key] = "pymysql"
        elif key == "expected_driver_version":
            values[key] = "1.1.2"
        elif key == "expected_server_version":
            values[key] = "10.11.18-MariaDB-disposable"
        else:
            values[key] = SHA_A
    return values


def _manifest(phase: str = "observe") -> dict[str, object]:
    policy = None if phase == "observe" else _policy()
    runtime_policy = f"{SECRET_ROOT}/runtime-policy.json"
    canaries = (
        ["environment_observation"]
        if phase == "observe"
        else [
            "normal_snapshot",
            "preexisting_transaction_rejected",
            "policy_mismatch_rejected",
            "replica_ambiguity_rejected",
            "binding_stability",
            "generic_failure_and_teardown",
        ]
    )
    document: dict[str, object] = {
        "schema": "erpai.gl_tb.runtime_compat.execution.v3",
        "phase": phase,
        "run_id": RUN_ID,
        "run_root": RUN_ROOT,
        "repository": {
            "revision": REVISION,
            "controller_sha256": SHA_A,
            "probe_sha256": SHA_B,
            "initializer_sha256": SHA_C,
            "dockerfile_sha256": SHA_A,
            "compose_sha256": SHA_B,
            "package_initializer_sha256": SHA_C,
            "finance_initializer_sha256": SHA_A,
            "core_sha256": SHA_B,
            "adapter_sha256": SHA_C,
            "runtime_sha256": SHA_A,
            "frappe_tree_sha256": SHA_A,
            "erpnext_tree_sha256": SHA_B,
            "source_content_sha256": _fixture_hash(_source_content()),
        },
        "artifacts": {
            "base_image": BASE_IMAGE,
            "base_image_id": f"sha256:{SHA_B}",
            "runner_image": IMAGE_A,
            "runner_image_id": f"sha256:{SHA_A}",
            "mariadb_image": IMAGE_B,
            "mariadb_image_id": f"sha256:{SHA_B}",
            "redis_image": IMAGE_C,
            "redis_image_id": f"sha256:{SHA_C}",
        },
        "docker": {
            "executable": f"{RUN_ROOT}/tools/docker",
            "executable_sha256": SHA_C,
            "endpoint": f"unix://{RUN_ROOT}/docker/docker.sock",
            "compose_version": "v2.40.3",
            "client_version": "28.5.2",
            "client_api_version": "1.51",
            "server_version": "28.5.2",
            "server_api_version": "1.51",
            "daemon_id": "ROOTLESS:DAEMON:0123456789AB",
            "daemon_name": f"gl_tb_rtcompat_{RUN_ID}_rootless",
            "docker_root_dir": f"{RUN_ROOT}/docker/data-root",
            "security_options_sha256": hashlib.sha256(
                SECURITY_OPTIONS_JSON.encode()
            ).hexdigest(),
            "daemon_lifecycle_owner": "external_materialization_controller",
            "buildkit_version": "v0.25.1",
            "frontend_capabilities_sha256": SHA_B,
            "rootlesskit_runtime_dir": f"/run/user/{os.geteuid()}/gtb-{RUN_ID}",
            "cgroup_driver": "none" if phase == "observe" else "systemd",
            "cgroup_version": "2",
            "cgroup_authority": (
                "compatibility_observation_only"
                if phase == "observe" else "delegated_cgroup_v2"
            ),
            "os": "linux",
            "architecture": "amd64",
        },
        "source_content": _source_content(),
        "compose": {
            "file": f"{RUN_ROOT}/compose.yaml",
            "project": PROJECT,
            "run_label": RUN_LABEL,
            "services": ["db-primary", "redis-cache", "site-init", "runtime-probe"],
            "network": f"{PROJECT}_internal",
            "volumes": [f"{PROJECT}_db", f"{PROJECT}_sites", f"{PROJECT}_redis"],
        },
        "site": {
            "site_name": f"gl-tb-rt-{RUN_ID}.local",
            "database_name": f"gl_tb_rt_{RUN_ID}",
            "database_user": f"gl_tb_rt_{RUN_ID}",
            "db_host": "db-primary",
            "db_port": 3306,
            "sites_path": "/home/frappe/frappe-bench/sites",
            "mariadb_user_host_scope": "%",
            "synthetic_user": "Guest",
            "synthetic_company": f"GL_TB_RT_{RUN_ID.upper()}",
        },
        "secrets": {
            "directory": SECRET_ROOT,
            "db_root_password": f"{SECRET_ROOT}/db-root-password",
            "site_admin_password": f"{SECRET_ROOT}/site-admin-password",
            "site_db_password": f"{SECRET_ROOT}/site-db-password",
            "connection_commitment_key": f"{SECRET_ROOT}/connection-commitment-key",
            "runtime_policy": runtime_policy,
        },
        "limits": {
            "setup_timeout_seconds": 30,
            "command_timeout_seconds": 20,
            "teardown_timeout_seconds": 15,
            "healthcheck_interval_seconds": 2,
            "healthcheck_timeout_seconds": 2,
            "healthcheck_retries": 30,
            "stdout_max_bytes": 8192,
            "stderr_max_bytes": 4096,
            "evidence_max_bytes": 65536,
        },
        "policy": policy,
        "canaries": canaries,
        "evidence": {
            "directory": f"{RUN_ROOT}/evidence",
            "staging_directory": f"{RUN_ROOT}/staging",
            "files": [
                "artifact-provenance.json",
                "observation-result.json",
                "validation-result.json",
                "discard-results.jsonl",
                "teardown-receipt.json",
                "evidence-manifest.sha256",
            ],
        },
    }
    return document


def _encoded(document: object, *, sort_keys: bool = False) -> bytes:
    return json.dumps(document, separators=(",", ":"), sort_keys=sort_keys).encode() + b"\n"


def _refresh_source_hash(document: dict[str, object]) -> None:
    document["repository"]["source_content_sha256"] = _fixture_hash(
        document["source_content"]
    )


def _refresh_context_hash(document: dict[str, object]) -> None:
    content = document["source_content"]
    content["build_context"]["manifest_sha256"] = _fixture_hash(
        content["build_context"]["entries"]
    )
    _refresh_source_hash(document)


def _base_image_config() -> dict[str, object]:
    return {
        "User": "frappe",
        "WorkingDir": "/home/frappe/frappe-bench",
        "Entrypoint": ["/home/frappe/frappe-bench/env/bin/gunicorn"],
        "Cmd": ["--bind=0.0.0.0:8000"],
        "Env": [
            "PATH=/usr/local/bin:/usr/bin",
            "BASE_ONLY=pinned",
        ],
        "Volumes": {"/home/frappe/frappe-bench/sites": {}},
        "Labels": {"org.opencontainers.image.title": "pinned-base"},
        "ExposedPorts": {"8000/tcp": {}},
    }


def _runner_image_config(
    manifest: controller.ControllerManifest,
) -> dict[str, object]:
    config = copy.deepcopy(_base_image_config())
    environment = {
        item.split("=", 1)[0]: item.split("=", 1)[1]
        for item in config["Env"]
    }
    environment.update(controller._runner_environment_overrides(manifest))
    config.update({
        "User": "1000:1000",
        "WorkingDir": "/opt/erpai",
        "Entrypoint": [
            "/opt/erpai/finance_gl_trial_balance_runtime_compatibility_probe.py"
        ],
        "Cmd": [],
        "Env": [
            f"{name}={environment[name]}" for name in sorted(environment)
        ],
    })
    return config


def _image_inspect(
    manifest: controller.ControllerManifest,
    key: str,
    *,
    config: dict[str, object] | None = None,
) -> bytes:
    volumes = {
        "base_image": {"/home/frappe/frappe-bench/sites": {}},
        "runner_image": {"/home/frappe/frappe-bench/sites": {}},
        "mariadb_image": {"/var/lib/mysql": {}},
        "redis_image": {"/data": {}},
    }[key]
    fields = (
        manifest.artifacts[key.replace("_image", "_image_id")],
        json.dumps([manifest.artifacts[key]], separators=(",", ":")),
        "linux",
        "amd64",
        json.dumps(volumes, separators=(",", ":"), sort_keys=True),
        json.dumps(
            (
                config
                if config is not None
                else (_base_image_config() if key == "base_image" else {})
            ),
            separators=(",", ":"),
            sort_keys=True,
        ),
    )
    return ("\t".join(fields) + "\n").encode()


def _runner_observation(
    manifest: controller.ControllerManifest,
) -> dict[str, object]:
    plans = controller._preflight_plan(manifest)
    base_spec = next(
        item for item in plans if item.name == "inspect-base_image"
    )
    base = controller._validate_preflight_result(
        manifest,
        base_spec,
        controller._CommandResult(
            0, _image_inspect(manifest, "base_image"), b"", False
        ),
    )
    if base is None:
        raise AssertionError("base configuration was not observed")
    runner_spec = next(
        item for item in plans if item.name == "inspect-runner_image"
    )
    observed = controller._validate_preflight_result(
        manifest,
        runner_spec,
        controller._CommandResult(
            0,
            _image_inspect(
                manifest,
                "runner_image",
                config=_runner_image_config(manifest),
            ),
            b"",
            False,
        ),
        base_configuration=base["configuration"],
    )
    if observed is None:
        raise AssertionError("runner materialization was not observed")
    return observed


def _filesystem_observation(
    manifest: controller.ControllerManifest,
) -> dict[str, object]:
    expected = controller._expected_final_filesystem_document(
        manifest.source_content
    )
    return controller.validate_final_filesystem_observation(
        manifest, _encoded(expected)
    )


def _materialization_attestation(
    manifest: controller.ControllerManifest,
) -> dict[str, object]:
    return controller._build_materialization_attestation(
        manifest,
        _runner_observation(manifest),
        _filesystem_observation(manifest),
        {
            "network_mode": "none",
            "privileged": False,
            "read_only_rootfs": True,
            "user": "1000:1000",
            "cap_drop": ["ALL"],
            "security_options": ["no-new-privileges:true"],
            "tmpfs_destinations": ["/home/frappe/frappe-bench/sites"],
            "container_started": False,
            "verification_container_retired": True,
        },
    )


def _content_container_inspect(
    manifest: object, replacements: dict[int, str] | None = None,
) -> bytes:
    fields = [
        SHA_A,
        manifest.artifacts["runner_image_id"],
        f"/{PROJECT}_content_verifier",
        "created", "false", "0", "false", "none", "false",
        "1000:1000", "true",
        json.dumps(["ALL"], separators=(",", ":")),
        json.dumps(["no-new-privileges:true"], separators=(",", ":")),
        json.dumps(["/bin/false"], separators=(",", ":")),
        json.dumps([], separators=(",", ":")),
        "tmpfs=/home/frappe/frappe-bench/sites,",
        RUN_ID, PROJECT, "content-verifier",
    ]
    for index, value in (replacements or {}).items():
        fields[index] = value
    return ("\t".join(fields) + "\n").encode()


def _probe_container_inspect(
    manifest: object, case_id: str,
    replacements: dict[int, str] | None = None,
) -> bytes:
    mounts = (
        "volume=/home/frappe/frappe-bench/sites,"
        "tmpfs=/tmp,tmpfs=/evidence,"
        "bind=/run/secrets/connection-commitment-key,"
        "bind=/run/secrets/execution-manifest.json,"
        "bind=/run/secrets/runtime-policy.json,"
    )
    fields = [
        SHA_A,
        manifest.artifacts["runner_image_id"],
        f"/{PROJECT}_probe_{case_id}",
        "exited", "false", "0", "false", manifest.compose["network"],
        "false", "1000:1000", "true",
        json.dumps(["ALL"], separators=(",", ":")),
        json.dumps(["no-new-privileges:true"], separators=(",", ":")),
        json.dumps(
            ["/opt/erpai/finance_gl_trial_balance_runtime_compatibility_probe.py"],
            separators=(",", ":"),
        ),
        json.dumps(list(controller._probe_args(manifest, case_id)), separators=(",", ":")),
        mounts, RUN_ID, PROJECT, "runtime-probe",
    ]
    for index, value in (replacements or {}).items():
        fields[index] = value
    return ("\t".join(fields) + "\n").encode()


def _resolved_compose() -> dict[str, object]:
    labels = {"com.erpai.finance.gl_tb_rtcompat.run": RUN_ID}

    def volume(
        source: str, target: str, *, read_only: bool, nocopy: bool
    ) -> list[dict[str, object]]:
        return [{
            "type": "volume",
            "source": source,
            "target": target,
            "read_only": read_only,
            "volume": {"nocopy": nocopy},
        }]

    def secrets(values: dict[str, str]) -> list[dict[str, str]]:
        return [
            {"source": source, "target": target}
            for source, target in values.items()
        ]

    return {
        "name": PROJECT,
        "services": {
            "db-primary": {
                "image": IMAGE_B,
                "container_name": f"{PROJECT}_db_primary",
                "pull_policy": "never",
                "restart": "no",
                "environment": {
                    "MARIADB_ROOT_PASSWORD_FILE": "/run/secrets/db-root-password",
                    "MARIADB_ROOT_HOST": "%",
                },
                "secrets": secrets({"db-root-password": "db-root-password"}),
                "networks": ["internal"],
                "volumes": volume(
                    "db", "/var/lib/mysql", read_only=False, nocopy=True
                ),
                "labels": labels,
            },
            "redis-cache": {
                "image": IMAGE_C,
                "container_name": f"{PROJECT}_redis_cache",
                "pull_policy": "never",
                "restart": "no",
                "networks": ["internal"],
                "volumes": volume(
                    "redis", "/data", read_only=False, nocopy=True
                ),
                "labels": labels,
            },
            "site-init": {
                "image": IMAGE_A,
                "pull_policy": "never",
                "restart": "no",
                "environment": {
                    "FRAPPE_REDIS_CACHE": "redis://redis-cache:6379"
                },
                "read_only": True,
                "cap_drop": ["ALL"],
                "security_opt": ["no-new-privileges:true"],
                "tmpfs": ["/tmp:rw,noexec,nosuid,nodev"],
                "networks": ["internal"],
                "volumes": volume(
                    "sites",
                    "/home/frappe/frappe-bench/sites",
                    read_only=False,
                    nocopy=False,
                ),
                "secrets": secrets({
                    "db-root-password": "db-root-password",
                    "site-admin-password": "site-admin-password",
                    "site-db-password": "site-db-password",
                    "site-init-manifest": "site-init-manifest.json",
                }),
                "labels": labels,
            },
            "runtime-probe": {
                "image": IMAGE_A,
                "pull_policy": "never",
                "restart": "no",
                "environment": {
                    "FRAPPE_REDIS_CACHE": "redis://redis-cache:6379"
                },
                "read_only": True,
                "cap_drop": ["ALL"],
                "security_opt": ["no-new-privileges:true"],
                "tmpfs": [
                    "/tmp:rw,noexec,nosuid,nodev",
                    "/evidence:rw,noexec,nosuid,nodev",
                ],
                "networks": ["internal"],
                "volumes": volume(
                    "sites",
                    "/home/frappe/frappe-bench/sites",
                    read_only=True,
                    nocopy=False,
                ),
                "secrets": secrets({
                    "connection-commitment-key": "connection-commitment-key",
                    "execution-manifest": "execution-manifest.json",
                    "runtime-policy": "runtime-policy.json",
                }),
                "labels": labels,
            },
        },
        "networks": {
            "internal": {
                "name": f"{PROJECT}_internal",
                "driver": "bridge",
                "internal": True,
                "attachable": False,
                "labels": labels,
            }
        },
        "volumes": {
            key: {
                "name": f"{PROJECT}_{key}",
                "driver": "local",
                "labels": labels,
            }
            for key in ("db", "sites", "redis")
        },
        "secrets": {
            "db-root-password": {
                "file": f"{SECRET_ROOT}/db-root-password"
            },
            "site-admin-password": {
                "file": f"{SECRET_ROOT}/site-admin-password"
            },
            "site-db-password": {
                "file": f"{SECRET_ROOT}/site-db-password"
            },
            "connection-commitment-key": {
                "file": f"{SECRET_ROOT}/connection-commitment-key"
            },
            "site-init-manifest": {
                "file": f"{SECRET_ROOT}/site-init-manifest.json"
            },
            "execution-manifest": {
                "file": f"{SECRET_ROOT}/execution-manifest.json"
            },
            "runtime-policy": {
                "file": f"{SECRET_ROOT}/runtime-policy.json"
            },
        },
    }


class ManifestSchemaTests(unittest.TestCase):
    def test_valid_observe_and_validate_manifests(self) -> None:
        observed = controller.parse_and_validate_manifest(_encoded(_manifest("observe"), sort_keys=True))
        validated = controller.parse_and_validate_manifest(_encoded(_manifest("validate"), sort_keys=True))
        self.assertEqual(observed.phase, "observe")
        self.assertIsNone(observed.policy)
        self.assertEqual(validated.phase, "validate")
        self.assertEqual(validated.policy["expected_driver"], "pymysql")
        self.assertEqual(validated.repository["revision"], REVISION)

    def test_json_objects_are_order_independent_but_closed(self) -> None:
        document = _manifest()
        reversed_document = dict(reversed(tuple(document.items())))
        controller.parse_and_validate_manifest(_encoded(reversed_document))
        for mutation in ("unknown", "missing"):
            changed = copy.deepcopy(document)
            if mutation == "unknown":
                changed["unexpected"] = "LEAK"
            else:
                changed.pop("evidence")
            with self.subTest(mutation=mutation), self.assertRaises(controller.ControllerRejected):
                controller.parse_and_validate_manifest(_encoded(changed))

    def test_duplicate_bom_utf8_trailing_float_and_constant_rejection(self) -> None:
        valid = _encoded(_manifest())
        bodies = (
            b'{"schema":"x","schema":"y"}',
            b"\xef\xbb\xbf" + valid,
            b"\xff",
            valid + b"{}",
            valid.replace(b'"db_port":3306', b'"db_port":3306.0'),
            valid.replace(b'"db_port":3306', b'"db_port":NaN'),
        )
        for body in bodies:
            with self.subTest(body=body[:24]), self.assertRaises(controller.ControllerRejected):
                controller.parse_and_validate_manifest(body)

    def test_missing_null_wrong_type_unknown_nested_and_bool_integer(self) -> None:
        cases: list[dict[str, object]] = []
        missing = _manifest()
        missing["docker"].pop("endpoint")
        cases.append(missing)
        null_value = _manifest()
        null_value["compose"]["network"] = None
        cases.append(null_value)
        wrong_type = _manifest()
        wrong_type["canaries"] = "environment_observation"
        cases.append(wrong_type)
        nested_unknown = _manifest()
        nested_unknown["artifacts"]["tag"] = "latest"
        cases.append(nested_unknown)
        bool_int = _manifest()
        bool_int["limits"]["command_timeout_seconds"] = True
        cases.append(bool_int)
        for index, document in enumerate(cases):
            with self.subTest(index=index), self.assertRaises(controller.ControllerRejected):
                controller.parse_and_validate_manifest(_encoded(document))

    def test_run_root_path_endpoint_and_image_are_exact(self) -> None:
        mutations = []
        traversal = _manifest()
        traversal["run_root"] = f"{RUN_ROOT}/../{RUN_ID}"
        mutations.append(traversal)
        prefix_escape = _manifest()
        prefix_escape["compose"]["file"] = f"{RUN_ROOT}-evil/compose.yaml"
        mutations.append(prefix_escape)
        default_socket = _manifest()
        default_socket["docker"]["endpoint"] = "unix:///var/run/docker.sock"
        mutations.append(default_socket)
        remote_socket = _manifest()
        remote_socket["docker"]["endpoint"] = "tcp://127.0.0.1:2375"
        mutations.append(remote_socket)
        mutable_image = _manifest()
        mutable_image["artifacts"]["runner_image"] = "registry.example/erpai/runner:latest"
        mutations.append(mutable_image)
        for index, document in enumerate(mutations):
            with self.subTest(index=index), self.assertRaises(controller.ControllerRejected):
                controller.parse_and_validate_manifest(_encoded(document))

    def test_one_stack_and_exact_resources_only(self) -> None:
        for key, value in (
            ("services", ["db-primary", "redis-cache", "site-init", "runtime-probe", "worker"]),
            ("volumes", [f"{PROJECT}_db", f"{PROJECT}_sites"]),
            ("network", f"{PROJECT}_external"),
        ):
            document = _manifest()
            document["compose"][key] = value
            with self.subTest(key=key), self.assertRaises(controller.ControllerRejected):
                controller.parse_and_validate_manifest(_encoded(document))

    def test_host_scope_and_driver_versions_are_exact(self) -> None:
        for driver, version in (
            ("pymysql", "2.0.0"),
            ("mysqlclient", "1.1.2"),
        ):
            document = _manifest("validate")
            document["policy"]["expected_driver"] = driver
            document["policy"]["expected_driver_version"] = version
            with self.subTest(driver=driver), self.assertRaises(
                controller.ControllerRejected
            ):
                controller.parse_and_validate_manifest(_encoded(document))
        document = _manifest()
        document["site"]["mariadb_user_host_scope"] = "localhost"
        with self.assertRaises(controller.ControllerRejected):
            controller.parse_and_validate_manifest(_encoded(document))

    def test_resolved_compose_is_closed_and_mounts_are_exact(self) -> None:
        manifest = controller.parse_and_validate_manifest(_encoded(_manifest()))
        valid = _resolved_compose()
        controller._validate_resolved_compose(manifest, _encoded(valid))
        mutations: list[dict[str, object]] = []
        top_config = copy.deepcopy(valid)
        top_config["configs"] = {"host": {"file": "/etc/passwd"}}
        mutations.append(top_config)
        service_config = copy.deepcopy(valid)
        service_config["services"]["runtime-probe"]["configs"] = [
            {"source": "host", "target": "/run/config"}
        ]
        mutations.append(service_config)
        bind_mount = copy.deepcopy(valid)
        bind_mount["services"]["runtime-probe"]["volumes"][0] = {
            "type": "bind",
            "source": "/",
            "target": "/host",
            "read_only": True,
            "volume": {"nocopy": False},
        }
        mutations.append(bind_mount)
        wrong_secret_target = copy.deepcopy(valid)
        wrong_secret_target["services"]["runtime-probe"]["secrets"][0][
            "target"
        ] = "other"
        mutations.append(wrong_secret_target)
        for index, document in enumerate(mutations):
            with self.subTest(index=index), self.assertRaises(
                controller.ControllerRejected
            ):
                controller._validate_resolved_compose(
                    manifest, _encoded(document)
                )

    def test_observation_and_validation_policy_separation(self) -> None:
        self.assertIn("approval_sha256", controller._POLICY_KEYS)
        self.assertTrue(
            any("observation" in key for key in controller._POLICY_KEYS),
            "validation policy must bind the approved observation result",
        )
        observe = _manifest("observe")
        observe["policy"] = _policy()
        with self.assertRaises(controller.ControllerRejected):
            controller.parse_and_validate_manifest(_encoded(observe))
        validate = _manifest("validate")
        validate["policy"] = None
        with self.assertRaises(controller.ControllerRejected):
            controller.parse_and_validate_manifest(_encoded(validate))


class PathAndCommandTests(unittest.TestCase):
    @staticmethod
    def _status(mode: int, *, links: int = 1) -> object:
        return types.SimpleNamespace(st_mode=mode, st_nlink=links)

    def test_component_symlink_and_non_directory_rejection(self) -> None:
        target = f"{RUN_ROOT}/evidence/result.json"

        def clean(path: str) -> object:
            return self._status(stat.S_IFREG | 0o600) if path == target else self._status(stat.S_IFDIR | 0o700)

        controller.validate_no_symlink_path(target, RUN_ROOT, lstat=clean)
        for bad_path, bad_mode in (
            ("/tmp/erpai-finance-gl-tb-runtime-compat", stat.S_IFLNK | 0o777),
            (RUN_ROOT, stat.S_IFLNK | 0o777),
            (f"{RUN_ROOT}/evidence", stat.S_IFREG | 0o600),
            (target, stat.S_IFLNK | 0o777),
        ):
            def bad(path: str, bad_path: str = bad_path, bad_mode: int = bad_mode) -> object:
                if path == bad_path:
                    return self._status(bad_mode)
                return clean(path)

            with self.subTest(path=bad_path), self.assertRaises(controller.ControllerRejected):
                controller.validate_no_symlink_path(target, RUN_ROOT, lstat=bad)

    def test_missing_leaf_is_explicit_and_traversal_never_allowed(self) -> None:
        target = f"{RUN_ROOT}/evidence/new.json"

        def missing(path: str) -> object:
            if path == target:
                raise FileNotFoundError
            return self._status(stat.S_IFDIR | 0o700)

        controller.validate_no_symlink_path(target, RUN_ROOT, allow_missing_leaf=True, lstat=missing)
        with self.assertRaises(controller.ControllerRejected):
            controller.validate_no_symlink_path(target, RUN_ROOT, lstat=missing)
        with self.assertRaises(controller.ControllerRejected):
            controller.validate_no_symlink_path(f"{RUN_ROOT}/../escape", RUN_ROOT, lstat=missing)

    def test_docker_endpoint_leaf_must_be_a_single_unix_socket(self) -> None:
        path = Path(f"{RUN_ROOT}/docker/docker.sock")

        def status(mode: int, links: int = 1) -> object:
            return types.SimpleNamespace(st_mode=mode, st_nlink=links)

        controller._require_unix_socket(
            path, lstat=lambda _path: status(stat.S_IFSOCK | 0o660)
        )
        for value in (
            status(stat.S_IFLNK | 0o777),
            status(stat.S_IFREG | 0o600),
            status(stat.S_IFSOCK | 0o660, 2),
        ):
            with self.subTest(mode=value.st_mode), self.assertRaises(
                controller.ControllerRejected
            ):
                controller._require_unix_socket(
                    path, lstat=lambda _path, value=value: value
                )

    def test_host_secret_source_requires_private_owner_mode(self) -> None:
        path = Path("/synthetic/secret")
        body = b"x" * 32
        good = types.SimpleNamespace(
            st_mode=stat.S_IFREG | 0o600,
            st_nlink=1,
            st_size=len(body),
            st_uid=1000,
        )
        with (
            mock.patch.object(controller.os, "lstat", return_value=good),
            mock.patch.object(controller.os, "geteuid", return_value=1000),
            mock.patch("builtins.open", return_value=io.BytesIO(body)),
        ):
            self.assertEqual(
                controller._read_host_regular(path, 64, private=True),
                body,
            )
        bad = types.SimpleNamespace(
            st_mode=stat.S_IFREG | 0o644,
            st_nlink=1,
            st_size=len(body),
            st_uid=1000,
        )
        with (
            mock.patch.object(controller.os, "lstat", return_value=bad),
            mock.patch.object(controller.os, "geteuid", return_value=1000),
        ):
            with self.assertRaises(controller.ControllerRejected):
                controller._read_host_regular(path, 64, private=True)

    def test_exact_subcommands_and_phase_mismatch(self) -> None:
        observe = controller.parse_and_validate_manifest(_encoded(_manifest("observe")))
        validate = controller.parse_and_validate_manifest(_encoded(_manifest("validate")))
        for command in ("preflight", "observe", "recover-teardown"):
            self.assertTrue(controller.build_child_command_plan(observe, command))
        self.assertTrue(controller.build_child_command_plan(validate, "validate"))
        for manifest, command in ((observe, "validate"), (validate, "observe"), (observe, "exec")):
            with self.subTest(command=command), self.assertRaises(controller.ControllerRejected):
                controller.build_child_command_plan(manifest, command)

    def test_all_docker_argv_are_endpoint_pinned_and_closed(self) -> None:
        manifest = controller.parse_and_validate_manifest(_encoded(_manifest("validate")))
        forbidden = {"prune", "logs", "exec", "build"}
        for command in ("preflight", "validate", "recover-teardown"):
            for spec in controller.build_child_command_plan(manifest, command):
                self.assertEqual(spec.argv[:3], (f"{RUN_ROOT}/tools/docker", "--host", f"unix://{RUN_ROOT}/docker/docker.sock"))
                self.assertFalse(forbidden.intersection(spec.argv))
                self.assertNotIn("--remove-orphans", spec.argv)
                self.assertNotIn("shell", spec.argv)
                if "--pull" in spec.argv:
                    self.assertEqual(spec.argv[spec.argv.index("--pull") + 1], "never")

    def test_phase_plan_waits_for_completion_before_teardown(self) -> None:
        manifest = controller.parse_and_validate_manifest(_encoded(_manifest("validate")))
        names = [spec.name for spec in controller.build_child_command_plan(manifest, "validate")]
        probe_positions = [index for index, name in enumerate(names) if name.startswith("probe-")]
        self.assertTrue(probe_positions)
        self.assertTrue(any("wait" in name for name in names), names)
        self.assertTrue(any("result" in name or "evidence" in name for name in names), names)
        teardown_first = min(
            index
            for index, name in enumerate(names)
            if name.startswith("teardown-")
        )
        self.assertGreater(teardown_first, max(probe_positions))

    def test_subprocess_is_shell_free_closed_and_bounded(self) -> None:
        spec = controller.CommandSpec(
            "x",
            (sys.executable, "-I", "-c", "import sys;sys.stdout.write('ok')"),
            3,
            8,
            8,
        )
        real_popen = subprocess.Popen
        with mock.patch.object(
            controller.subprocess, "Popen", wraps=real_popen
        ) as popen:
            result = controller._run_subprocess(
                spec, {"LANG": "C", "PATH": "/usr/bin:/bin"}
            )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"ok")
        kwargs = popen.call_args.kwargs
        self.assertIs(kwargs["shell"], False)
        self.assertEqual(kwargs["cwd"], "/")
        self.assertEqual(
            kwargs["env"], {"LANG": "C", "PATH": "/usr/bin:/bin"}
        )
        self.assertTrue(kwargs["start_new_session"])
        overflow = controller.CommandSpec(
            "overflow",
            (sys.executable, "-I", "-c", "import sys;sys.stdout.write('123456789')"),
            3,
            8,
            8,
        )
        with self.assertRaises(controller.ControllerRejected):
            controller._run_subprocess(
                overflow, {"LANG": "C", "PATH": "/usr/bin:/bin"}
            )

    def test_environment_contains_paths_not_secret_values_or_host_overrides(self) -> None:
        manifest = controller.parse_and_validate_manifest(_encoded(_manifest("validate")))
        environment = controller._execution_environment(manifest)
        for forbidden in ("DOCKER_HOST", "DOCKER_CONTEXT", "COMPOSE_PROJECT_NAME", "HTTP_PROXY", "HTTPS_PROXY"):
            self.assertNotIn(forbidden, environment)
        self.assertEqual(environment["COMPOSE_DISABLE_ENV_FILE"], "1")
        self.assertEqual(environment["COMPOSE_ANSI"], "never")
        rendered = repr(environment)
        self.assertNotIn("root-password-value", rendered)
        self.assertIn("db-root-password", rendered)


class ProbeBoundaryTests(unittest.TestCase):
    _INITIAL = (
        "10.11.18-MariaDB-disposable",
        731,
        0,
        "REPEATABLE-READ",
        0,
    )
    _ACTIVE = (
        "10.11.18-MariaDB-disposable",
        731,
        1,
        "REPEATABLE-READ",
        1,
    )
    _FINAL = (
        "10.11.18-MariaDB-disposable",
        731,
        0,
        "REPEATABLE-READ",
        0,
    )

    class _Cursor:
        def __init__(self, raw: object) -> None:
            self.raw = raw
            self.row: tuple[object, ...] | None = None
            self.calls = 0
            self.statement = None
            self.closed = False

        def execute(self, statement: str) -> None:
            self.statement = statement
            self.raw.statements.append(statement)
            ordinal = len(self.raw.statements)
            if ordinal in self.raw.fail_at or statement in self.raw.fail_statements:
                raise RuntimeError("LEAK COMPANY SQL CONNECTION 731")
            if statement == probe._STATE_SQL:
                if not self.raw.rows:
                    raise RuntimeError("LEAK EMPTY STATE")
                self.row = self.raw.rows.pop(0)
            elif statement not in probe._TRANSACTION_CONTROL_SQL:
                raise AssertionError("unexpected statement")
            callback = self.raw.after_execute.get(ordinal)
            if callback is not None:
                callback()

        def fetchone(self) -> object:
            self.calls += 1
            return self.row if self.calls == 1 else None

        def close(self) -> None:
            self.raw.cursor_close_calls += 1
            self.closed = True
            if self.raw.cursor_close_calls in self.raw.fail_cursor_close_at:
                raise RuntimeError("LEAK CURSOR CLOSE COMPANY SQL CONNECTION 731")

    class _Raw:
        def __init__(
            self,
            rows: tuple[tuple[object, ...], ...],
            *,
            fail_at: frozenset[int],
            fail_statements: frozenset[str],
            fail_cursor_close_at: frozenset[int],
        ) -> None:
            self.rows = list(rows)
            self.fail_at = set(fail_at)
            self.fail_statements = set(fail_statements)
            self.fail_cursor_close_at = set(fail_cursor_close_at)
            self.after_execute: dict[int, object] = {}
            self.statements: list[str] = []
            self.cursor_close_calls = 0
            self.open = True
            self.close_calls = 0

        def cursor(self) -> object:
            return ProbeBoundaryTests._Cursor(self)

        def close(self) -> None:
            self.close_calls += 1
            self.open = False

    @staticmethod
    def _frappe(
        rows: tuple[tuple[object, ...], ...] | None = None,
        *,
        fail_at: frozenset[int] = frozenset(),
        fail_statements: frozenset[str] = frozenset(),
        fail_cursor_close_at: frozenset[int] = frozenset(),
        driver: str = "pymysql",
    ) -> tuple[object, object, object]:
        wrapper_module, raw_module = {
            "pymysql": (
                "frappe.database.mariadb.database",
                "pymysql.connections",
            ),
            "mysqlclient": (
                "frappe.database.mariadb.mysqlclient",
                "MySQLdb.connections",
            ),
        }[driver]
        raw_type = type(
            "Connection",
            (ProbeBoundaryTests._Raw,),
            {"__module__": raw_module},
        )
        raw = raw_type(
            rows
            if rows is not None
            else (
                ProbeBoundaryTests._INITIAL,
                ProbeBoundaryTests._ACTIVE,
                ProbeBoundaryTests._FINAL,
            ),
            fail_at=fail_at,
            fail_statements=fail_statements,
            fail_cursor_close_at=fail_cursor_close_at,
        )
        wrapper_type = type(
            "MariaDBDatabase",
            (),
            {"__module__": wrapper_module},
        )
        wrapper = wrapper_type()
        wrapper._conn = raw
        local = types.SimpleNamespace(db=wrapper, primary_db=None, replica_db=None, conf={}, session={"user": "Guest"})
        frappe = types.SimpleNamespace(local=local)
        return frappe, raw, raw

    def _assert_observation_rejected(self, frappe: object) -> None:
        with (
            mock.patch.object(probe, "_connect_site", return_value=frappe),
            mock.patch.object(probe, "_destroy_site"),
            mock.patch.object(probe.metadata, "version", return_value="1.1.2"),
            mock.patch.object(probe, "_connection_commitment", return_value=SHA_A),
        ):
            with self.assertRaises(probe.ProbeRejected) as raised:
                probe.observe(_manifest("observe"))
        self.assertEqual(str(raised.exception), "")
        self.assertIsNone(raised.exception.__cause__)
        self.assertIsNone(raised.exception.__context__)

    def test_observation_is_runtime_free_and_sanitized(self) -> None:
        frappe, raw, _script = self._frappe()
        manifest = _manifest("observe")
        with (
            mock.patch.object(probe, "_connect_site", return_value=frappe),
            mock.patch.object(probe, "_destroy_site") as destroy,
            mock.patch.object(probe.metadata, "version", return_value="1.1.2") as version,
            mock.patch.object(probe, "_connection_commitment", return_value=SHA_A),
            mock.patch.object(probe, "_runtime_objects", side_effect=AssertionError("runtime forbidden")),
        ):
            result = probe.observe(manifest)
        self.assertEqual(
            raw.statements,
            [
                probe._STATE_SQL,
                probe._SET_ISOLATION_SQL,
                probe._START_SNAPSHOT_SQL,
                probe._STATE_SQL,
                probe._ROLLBACK_SQL,
                probe._STATE_SQL,
            ],
        )
        self.assertEqual(version.call_args.args, ("PyMySQL",))
        destroy.assert_called_once_with(frappe)
        self.assertEqual(result["schema"], "erpai.gl_tb.runtime_compat.observation.v2")
        self.assertEqual(result["driver"], "pymysql")
        self.assertEqual(result["connection_id_commitment"], SHA_A)
        self.assertEqual(set(result), set(controller._OBSERVATION_RESULT_KEYS))
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
            "primary_route",
            "replica_denied",
        ):
            self.assertIs(result[key], True)
        self.assertIs(result["partial_output"], False)
        self.assertNotIn("transaction_state", result)
        self.assertNotIn("connection_id", result)
        rendered = repr(result)
        self.assertNotIn("731", rendered)
        self.assertNotIn("Guest", rendered)
        self.assertNotIn("policy", rendered.lower())
        source = PROBE_PATH.read_text(encoding="utf-8")
        observation_boundary = source[
            source.index("def _raw_one"):source.index("def _runtime_objects")
        ]
        for forbidden in (
            "tabGL Entry",
            "tabAccount",
            "synthetic_company",
            "get_list",
            "gl_trial_balance_core",
            "gl_trial_balance_adapter",
        ):
            self.assertNotIn(forbidden, observation_boundary)

    def test_mysqlclient_observation_uses_the_same_closed_lifecycle(self) -> None:
        frappe, raw, _script = self._frappe(driver="mysqlclient")
        with (
            mock.patch.object(probe, "_connect_site", return_value=frappe),
            mock.patch.object(probe, "_destroy_site") as destroy,
            mock.patch.object(
                probe.metadata, "version", return_value="2.2.7"
            ) as version,
            mock.patch.object(probe, "_connection_commitment", return_value=SHA_A),
            mock.patch.object(
                probe,
                "_runtime_objects",
                side_effect=AssertionError("runtime forbidden"),
            ),
        ):
            result = probe.observe(_manifest("observe"))
        self.assertEqual(
            raw.statements,
            [
                probe._STATE_SQL,
                probe._SET_ISOLATION_SQL,
                probe._START_SNAPSHOT_SQL,
                probe._STATE_SQL,
                probe._ROLLBACK_SQL,
                probe._STATE_SQL,
            ],
        )
        self.assertEqual(version.call_args.args, ("mysqlclient",))
        destroy.assert_called_once_with(frappe)
        self.assertEqual(result["driver"], "mysqlclient")
        self.assertEqual(result["driver_distribution"], "mysqlclient")
        self.assertEqual(result["driver_version"], "2.2.7")
        self.assertEqual(result["connection_id_commitment"], SHA_A)
        self.assertNotIn("connection_id", result)

    def test_observation_denies_replica_and_initial_active_transaction(self) -> None:
        for mutation in ("replica", "transaction"):
            rows = (
                (
                    "10.11.18-MariaDB-disposable",
                    731,
                    1,
                    "REPEATABLE-READ",
                    0,
                ),
            ) if mutation == "transaction" else None
            frappe, _raw, _script = self._frappe(rows)
            if mutation == "replica":
                frappe.local.replica_db = object()
            with self.subTest(mutation=mutation):
                self._assert_observation_rejected(frappe)

    def test_observation_rejects_each_transaction_statement_failure(self) -> None:
        for statement in (
            probe._SET_ISOLATION_SQL,
            probe._START_SNAPSHOT_SQL,
            probe._ROLLBACK_SQL,
        ):
            rows = (
                self._INITIAL,
                self._FINAL,
            ) if statement != probe._ROLLBACK_SQL else (
                self._INITIAL,
                self._ACTIVE,
            )
            frappe, raw, _script = self._frappe(
                rows,
                fail_statements=frozenset((statement,)),
            )
            with self.subTest(statement=statement):
                self._assert_observation_rejected(frappe)
            self.assertIn(statement, raw.statements)
            if statement == probe._ROLLBACK_SQL:
                self.assertFalse(raw.open)
                self.assertEqual(raw.close_calls, 1)

    def test_observation_rejects_cursor_close_failure_and_discards(self) -> None:
        for close_ordinal in range(1, 7):
            frappe, raw, _script = self._frappe(
                fail_cursor_close_at=frozenset((close_ordinal,))
            )
            with self.subTest(close_ordinal=close_ordinal):
                self._assert_observation_rejected(frappe)
            if close_ordinal == 1:
                self.assertEqual(raw.close_calls, 0)
            else:
                self.assertFalse(raw.open)
                self.assertEqual(raw.close_calls, 1)

    def test_observation_rejects_binding_and_server_identity_drift(self) -> None:
        for mutation in (
            "wrapper-active",
            "raw-active",
            "wrapper-final",
            "raw-final",
            "server-active",
            "server-final",
        ):
            rows = [self._INITIAL, self._ACTIVE, self._FINAL]
            if mutation == "server-active":
                rows[1] = (
                    "10.11.18-MariaDB-disposable",
                    732,
                    1,
                    "REPEATABLE-READ",
                    1,
                )
            elif mutation == "server-final":
                rows[2] = (
                    "10.11.18-MariaDB-disposable",
                    732,
                    0,
                    "REPEATABLE-READ",
                    0,
                )
            frappe, raw, _script = self._frappe(tuple(rows))
            if mutation.startswith("wrapper"):
                ordinal = 3 if mutation.endswith("active") else 5
                raw.after_execute[ordinal] = lambda: setattr(
                    frappe.local, "db", types.SimpleNamespace(_conn=raw)
                )
            elif mutation.startswith("raw"):
                ordinal = 3 if mutation.endswith("active") else 5
                replacement = types.SimpleNamespace(open=True)
                raw.after_execute[ordinal] = lambda: setattr(
                    frappe.local.db, "_conn", replacement
                )
            with self.subTest(mutation=mutation):
                self._assert_observation_rejected(frappe)

    def test_observation_rejects_lost_or_final_active_transaction(self) -> None:
        cases = {
            "lost-active": (731, 0, "REPEATABLE-READ", 1),
            "wrong-isolation": (731, 1, "READ-COMMITTED", 1),
            "not-read-only": (731, 1, "REPEATABLE-READ", 0),
        }
        for name, (connection_id, active, isolation, read_only) in cases.items():
            rows = (
                self._INITIAL,
                (
                    "10.11.18-MariaDB-disposable",
                    connection_id,
                    active,
                    isolation,
                    read_only,
                ),
            )
            frappe, _raw, _script = self._frappe(rows)
            with self.subTest(name=name):
                self._assert_observation_rejected(frappe)
        final_active = (
            self._INITIAL,
            self._ACTIVE,
            (
                "10.11.18-MariaDB-disposable",
                731,
                1,
                "REPEATABLE-READ",
                1,
            ),
        )
        frappe, _raw, _script = self._frappe(final_active)
        self._assert_observation_rejected(frappe)

    def test_observation_rejects_replica_ambiguity_at_each_checkpoint(self) -> None:
        for checkpoint in ("initial", "active", "final"):
            frappe, raw, _script = self._frappe()
            if checkpoint == "initial":
                frappe.local.replica_db = object()
            else:
                ordinal = 3 if checkpoint == "active" else 5
                raw.after_execute[ordinal] = lambda: setattr(
                    frappe.local, "replica_db", object()
                )
            with self.subTest(checkpoint=checkpoint):
                self._assert_observation_rejected(frappe)

    def test_normal_validation_calls_only_begin_final_close(self) -> None:
        frappe, raw, _cursor = self._frappe()
        snapshot = types.SimpleNamespace(
            transaction_active=True,
            transaction_read_only=True,
            transaction_isolation="REPEATABLE READ",
            consistent_snapshot=True,
            primary_connection=True,
            replica_denied=True,
            reconnect_denied=True,
            same_connection=True,
            stable=True,
        )

        class Runtime:
            def __init__(self) -> None:
                self.calls: list[str] = []

            def begin_read_snapshot(self, user: str, company: str) -> object:
                self.calls.append("begin")
                self.user = user
                self.company = company
                return snapshot

            def final_snapshot_evidence(self, value: object) -> object:
                self.calls.append("final")
                return value

            def close_read_snapshot(self, value: object) -> None:
                self.calls.append("close")

            def __getattr__(self, name: str) -> object:
                if name in {"effective_permission_evidence", "has_permission", "get_list", "complete_account_manifest", "complete_fiscal_year_applicability"}:
                    raise AssertionError(f"forbidden runtime method: {name}")
                raise AttributeError(name)

        runtime = Runtime()
        with (
            mock.patch.object(probe, "_connect_site", return_value=frappe),
            mock.patch.object(probe, "_destroy_site"),
            mock.patch.object(probe, "_runtime_objects", return_value=(runtime, RuntimeError)),
        ):
            result = probe.validate_case(_manifest("validate"), _policy(), "normal_snapshot")
        self.assertEqual(runtime.calls, ["begin", "final", "close"])
        self.assertEqual(runtime.user, "Guest")
        self.assertEqual(runtime.company, f"GL_TB_RT_{RUN_ID.upper()}")
        self.assertEqual(result["result"], "pass")
        self.assertFalse(result["normal_physical_close"])
        self.assertTrue(raw.open)

    def test_preexisting_transaction_uses_two_runtime_instances(self) -> None:
        frappe, _raw, _cursor = self._frappe()
        snapshot = types.SimpleNamespace(
            transaction_active=True,
            transaction_read_only=True,
            transaction_isolation="REPEATABLE READ",
            consistent_snapshot=True,
            primary_connection=True,
            replica_denied=True,
            reconnect_denied=True,
            same_connection=True,
            stable=True,
        )

        class FinanceError(Exception):
            pass

        first = mock.Mock()
        first.begin_read_snapshot.return_value = snapshot
        first.close_read_snapshot.return_value = None
        second = mock.Mock()
        error = FinanceError("finance_read_unavailable")
        error.__cause__ = None
        error.__context__ = None
        def reject_and_close(*_args: object) -> object:
            _raw.open = False
            raise error

        second.begin_read_snapshot.side_effect = reject_and_close
        with (
            mock.patch.object(probe, "_connect_site", return_value=frappe),
            mock.patch.object(probe, "_destroy_site"),
            mock.patch.object(probe, "_runtime_objects", side_effect=((first, FinanceError), (second, FinanceError))) as factory,
        ):
            result = probe.validate_case(_manifest("validate"), _policy(), "preexisting_transaction_rejected")
        self.assertEqual(factory.call_count, 2)
        first.begin_read_snapshot.assert_called_once()
        second.begin_read_snapshot.assert_called_once()
        first.close_read_snapshot.assert_not_called()
        self.assertEqual(result["actual_outcome"], "controlled_rejection")

    def test_policy_replica_and_generic_canaries_close_and_never_destroy(self) -> None:
        class FinanceError(Exception):
            pass

        def snapshot() -> object:
            return types.SimpleNamespace(
                transaction_active=True,
                transaction_read_only=True,
                transaction_isolation="REPEATABLE READ",
                consistent_snapshot=True,
                primary_connection=True,
                replica_denied=True,
                reconnect_denied=True,
                same_connection=True,
                stable=True,
            )

        for case_id in (
            "policy_mismatch_rejected",
            "replica_ambiguity_rejected",
            "generic_failure_and_teardown",
        ):
            frappe, raw, _cursor = self._frappe()
            runtime = mock.Mock()
            error = FinanceError("finance_read_unavailable")
            error.__cause__ = None
            error.__context__ = None

            def reject(*_args: object) -> object:
                raw.open = False
                raise error

            if case_id == "generic_failure_and_teardown":
                runtime.begin_read_snapshot.return_value = snapshot()
                runtime.final_snapshot_evidence.side_effect = reject
            else:
                runtime.begin_read_snapshot.side_effect = reject
            with (
                self.subTest(case_id=case_id),
                mock.patch.object(probe, "_connect_site", return_value=frappe),
                mock.patch.object(probe, "_destroy_site") as destroy,
                mock.patch.object(
                    probe,
                    "_runtime_objects",
                    return_value=(runtime, FinanceError),
                ),
            ):
                result = probe.validate_case(
                    _manifest("validate"), _policy(), case_id
                )
            self.assertEqual(result["actual_outcome"], "controlled_rejection")
            self.assertTrue(result["exceptional_physical_close"])
            self.assertEqual(result["post_failure_frappe_calls"], 0)
            destroy.assert_not_called()

    def test_unknown_wrapper_driver_is_rejected_before_compatibility_claim(self) -> None:
        frappe, raw, _cursor = self._frappe()
        type(raw).__module__ = "unknown.driver"
        with (
            mock.patch.object(probe, "_connect_site", return_value=frappe),
            mock.patch.object(probe, "_destroy_site"),
        ):
            with self.assertRaises(probe.ProbeRejected):
                probe.observe(_manifest("observe"))

    def test_probe_cli_and_generic_failure_do_not_leak(self) -> None:
        valid_observe = (
            "observe",
            "--manifest",
            "/run/secrets/execution-manifest.json",
            "--output",
            "/evidence/observation-result.json",
        )
        self.assertEqual(probe._parse_cli(valid_observe)[0], "observe")
        for argv in ((), ("obs",), valid_observe + ("LEAK",)):
            with self.subTest(argv=argv), self.assertRaises(probe.ProbeRejected):
                probe._parse_cli(argv)
        stderr = io.StringIO()
        with (
            mock.patch.object(
                probe,
                "_load_manifest",
                side_effect=RuntimeError("COMPANY SECRET SQL"),
            ),
            mock.patch.object(probe, "_atomic_output") as output,
            mock.patch.object(sys, "stderr", stderr),
        ):
            code = probe.main(valid_observe)
        self.assertEqual(code, 70)
        self.assertEqual(stderr.getvalue(), "runtime_compatibility_unavailable\n")
        output.assert_not_called()


class EvidenceAndTeardownTests(unittest.TestCase):
    def test_snapshot_identity_is_not_permitted_in_retained_schema(self) -> None:
        forbidden = {"user", "company", "token", "connection_id", "container_id", "exception", "traceback", "sql"}
        source = PROBE_PATH.read_text(encoding="utf-8")
        self.assertNotIn("asdict(", source)
        sample = {
            "schema": "erpai.gl_tb.runtime_compat.validation.v1",
            "result": "pass",
            "wrapper_stable": True,
        }
        self.assertFalse(forbidden.intersection(sample))

    def test_incomplete_or_teardown_failure_is_discard_only(self) -> None:
        manifest = controller.parse_and_validate_manifest(_encoded(_manifest("observe")))
        failed = controller._CommandResult(1, b"", b"LEAK SECRET", False)
        ok = controller._CommandResult(0, b"", b"", False)
        writes: list[tuple[object, bytes]] = []
        with (
            mock.patch.object(controller, "_preflight"),
            mock.patch.object(controller, "_phase_plan", return_value=(controller.CommandSpec("probe", ("x",), 1, 8, 8),)),
            mock.patch.object(controller, "_run_subprocess", return_value=failed),
            mock.patch.object(controller, "_recover_teardown", return_value=False),
            mock.patch.object(controller, "_write_discard") as discard,
            mock.patch.object(controller, "_atomic_write", side_effect=lambda path, body: writes.append((path, body))),
        ):
            with self.assertRaises(controller.ControllerRejected):
                controller._execute_phase(manifest)
        discard.assert_called_once()
        rendered = b"".join(body for _path, body in writes)
        self.assertNotIn(b"artifact-provenance", rendered)
        self.assertNotIn(b"LEAK", rendered)
        self.assertFalse(any(str(path).endswith("evidence-manifest.sha256") for path, _body in writes))
        del ok

    def test_internal_phase_exception_still_runs_teardown(self) -> None:
        manifest = controller.parse_and_validate_manifest(
            _encoded(_manifest("observe"))
        )
        spec = controller.CommandSpec("stack-up", ("x",), 1, 8, 8)
        with (
            mock.patch.object(controller, "_preflight"),
            mock.patch.object(controller, "_phase_plan", return_value=(spec,)),
            mock.patch.object(
                controller,
                "_run_subprocess",
                side_effect=controller._ControllerInternal(),
            ),
            mock.patch.object(
                controller, "_recover_teardown", return_value=True
            ) as teardown,
            mock.patch.object(controller, "_write_discard"),
        ):
            with self.assertRaises(controller.ControllerRejected):
                controller._execute_phase(manifest)
        teardown.assert_called_once_with(manifest)

    def test_teardown_plan_is_inventory_only_before_exact_id_removal(self) -> None:
        manifest = controller.parse_and_validate_manifest(_encoded(_manifest("observe")))
        plan = controller.build_child_command_plan(manifest, "recover-teardown")
        names = [spec.name for spec in plan]
        self.assertTrue(names)
        self.assertTrue(all("inspect" in name for name in names), names)
        for spec in plan:
            self.assertNotIn("prune", spec.argv)
            self.assertNotIn("--remove-orphans", spec.argv)
            self.assertNotIn("rm", spec.argv)
        inventory = controller._inventory_plan(manifest)
        self.assertEqual(len(inventory), 9)
        filters = {
            spec.argv[spec.argv.index("--filter") + 1]
            for spec in inventory
        }
        self.assertEqual(
            filters,
            {
                f"name={PROJECT}_",
                f"label={RUN_LABEL}",
                f"label=com.docker.compose.project={PROJECT}",
            },
        )

    def test_canonical_evidence_is_deterministic_and_no_nan(self) -> None:
        first = controller.canonical_json_bytes({"b": 2, "a": 1})
        second = controller.canonical_json_bytes({"a": 1, "b": 2})
        self.assertEqual(first, b'{"a":1,"b":2}\n')
        self.assertEqual(first, second)
        with self.assertRaises(controller.ControllerRejected):
            controller.canonical_json_bytes({"value": float("nan")})

    def test_probe_tar_is_single_file_strict_and_leakage_closed(self) -> None:
        manifest = controller.parse_and_validate_manifest(
            _encoded(_manifest("observe"))
        )
        record = {
            "schema": "erpai.gl_tb.runtime_compat.observation.v2",
            "mode": "observe",
            "run_id": RUN_ID,
            "result": "pass",
            "error": "",
            "wrapper_module": "frappe.database.mariadb.database",
            "wrapper_class": "MariaDBDatabase",
            "raw_module": "pymysql.connections",
            "raw_class": "Connection",
            "driver": "pymysql",
            "driver_distribution": "PyMySQL",
            "driver_version": "1.1.2",
            "server_version": "10.11.18-MariaDB-disposable",
            "initial_transaction_inactive": True,
            "isolation_repeatable_read": True,
            "transaction_read_only": True,
            "consistent_snapshot_started": True,
            "transaction_active": True,
            "wrapper_stable": True,
            "raw_connection_stable": True,
            "server_connection_stable": True,
            "rollback_no_chain_succeeded": True,
            "final_transaction_inactive": True,
            "connection_id_commitment": SHA_A,
            "primary_route": True,
            "replica_denied": True,
            "partial_output": False,
        }

        def archive(value: object) -> bytes:
            payload = controller.canonical_json_bytes(value)
            output = io.BytesIO()
            with tarfile.open(fileobj=output, mode="w:") as stream:
                member = tarfile.TarInfo("observation-result.json")
                member.size = len(payload)
                member.mode = 0o600
                stream.addfile(member, io.BytesIO(payload))
            return output.getvalue()

        accepted = controller._probe_tar_record(
            manifest, "environment_observation", archive(record)
        )
        self.assertEqual(accepted["driver"], "pymysql")
        for proof in (
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
            changed = dict(record)
            changed[proof] = False
            with self.subTest(proof=proof), self.assertRaises(
                controller.ControllerRejected
            ):
                controller._probe_tar_record(
                    manifest, "environment_observation", archive(changed)
                )
        for leaked_key in ("company", "connection_id"):
            leaked = dict(record)
            leaked[leaked_key] = "LEAK"
            with self.subTest(leaked_key=leaked_key), self.assertRaises(
                controller.ControllerRejected
            ):
                controller._probe_tar_record(
                    manifest, "environment_observation", archive(leaked)
                )

    def test_recovery_uses_observed_ids_and_rejects_unknown_inventory(self) -> None:
        manifest = controller.parse_and_validate_manifest(
            _encoded(_manifest("observe"))
        )
        populated = {
            "containers": ((SHA_A, f"{PROJECT}_db_primary"),),
            "networks": ((SHA_B, f"{PROJECT}_internal"),),
            "volumes": ((f"{PROJECT}_db", f"{PROJECT}_db"),),
        }
        empty = {"containers": (), "networks": (), "volumes": ()}
        calls: list[tuple[str, ...]] = []
        with (
            mock.patch.object(
                controller,
                "_inventory_resources",
                side_effect=(populated, empty),
            ),
            mock.patch.object(
                controller,
                "_run_subprocess",
                side_effect=lambda spec, _env: (
                    calls.append(spec.argv)
                    or controller._CommandResult(0, b"", b"", False)
                ),
            ),
            mock.patch.object(
                controller, "_remove_secret_sources", return_value=True
            ),
        ):
            self.assertTrue(controller._recover_teardown(manifest))
        rendered = repr(calls)
        self.assertIn(SHA_A, rendered)
        self.assertIn(SHA_B, rendered)
        self.assertNotIn("--remove-orphans", rendered)

        unknown = controller._CommandResult(
            0,
            (
                f"{SHA_A}\tunexpected\t{RUN_ID}\t{PROJECT}"
                "\truntime-probe\n"
            ).encode(),
            b"",
            False,
        )
        clear = controller._CommandResult(0, b"", b"", False)
        with mock.patch.object(
            controller,
            "_run_subprocess",
            side_effect=(unknown,) + (clear,) * 8,
        ):
            with self.assertRaises(controller.ControllerRejected):
                controller._inventory_resources(
                    manifest, controller._execution_environment(manifest)
                )

    def test_probe_retirement_uses_the_inspected_container_id(self) -> None:
        manifest = controller.parse_and_validate_manifest(
            _encoded(_manifest("observe"))
        )
        case_id = "environment_observation"
        inspect = controller.CommandSpec(
            f"inspect-probe-{case_id}", ("docker", "inspect", "name"), 1, 8_192, 8
        )
        retire = controller.CommandSpec(
            f"retire-probe-{case_id}",
            ("docker", "container", "rm", "--force", "name"),
            1,
            8,
            8,
        )
        inspect_body = _probe_container_inspect(manifest, case_id)
        self.assertEqual(
            controller._validate_probe_container(
                manifest,
                case_id,
                controller._CommandResult(0, inspect_body, b"", False),
            ),
            SHA_A,
        )
        for index, value in (
            (9, "0:0"), (10, "false"), (11, "[]"), (12, "[]"),
            (13, '["/bin/sh"]'), (14, "[]"), (15, "tmpfs=/tmp,"),
        ):
            with self.subTest(index=index), self.assertRaises(
                controller.ControllerRejected
            ):
                controller._validate_probe_container(
                    manifest,
                    case_id,
                    controller._CommandResult(
                        0,
                        _probe_container_inspect(manifest, case_id, {index: value}),
                        b"",
                        False,
                    ),
                )
        calls: list[tuple[str, ...]] = []

        def run(spec: controller.CommandSpec, _environment: object) -> object:
            calls.append(spec.argv)
            if spec.name.startswith("inspect-probe-"):
                return controller._CommandResult(0, inspect_body, b"", False)
            return controller._CommandResult(0, b"", b"", False)

        with (
            mock.patch.object(controller, "_preflight"),
            mock.patch.object(
                controller, "_phase_plan", return_value=(inspect, retire)
            ),
            mock.patch.object(controller, "_run_subprocess", side_effect=run),
            mock.patch.object(
                controller, "_recover_teardown", return_value=True
            ),
            mock.patch.object(controller, "_write_discard"),
        ):
            with self.assertRaises(controller.ControllerRejected):
                controller._execute_phase(manifest)
        self.assertEqual(calls[-1][-1], SHA_A)



class RouteBDerivativeRunnerManifestTests(unittest.TestCase):
    def test_source_content_contract_is_prebuild_only_closed_and_hashed(self) -> None:
        accepted = controller.parse_and_validate_manifest(_encoded(_manifest()))
        self.assertEqual(
            accepted.source_content["schema"],
            "erpai.gl_tb.runtime_compat.source_content.v1",
        )
        self.assertEqual(
            set(accepted.source_content),
            {
                "schema", "source_repository_revision", "base", "frontend",
                "sources", "python", "build_context", "gl_tb",
            },
        )
        self.assertTrue(
            {"final_image", "final_filesystem", "independent_verification_sha256"}
            .isdisjoint(accepted.source_content)
        )
        self.assertEqual(
            accepted.repository["source_content_sha256"],
            _fixture_hash(accepted.source_content),
        )

    def test_source_content_rejects_postbuild_or_unknown_claims(self) -> None:
        for key, value in (
            ("final_image", {"image_id": f"sha256:{SHA_A}"}),
            ("final_filesystem", {"entries": []}),
            ("materialization_attestation", {}),
            ("independent_verification_sha256", SHA_A),
        ):
            changed = _manifest()
            changed["source_content"][key] = value
            _refresh_source_hash(changed)
            with self.subTest(key=key), self.assertRaises(
                controller.ControllerRejected
            ):
                controller.parse_and_validate_manifest(_encoded(changed))

    def test_source_content_rejects_placeholder_and_circular_identity(self) -> None:
        repeated = _manifest()
        repeated["repository"]["source_content_sha256"] = "a" * 64
        with self.assertRaises(controller.ControllerRejected):
            controller.parse_and_validate_manifest(_encoded(repeated))

        for value in (
            _manifest()["artifacts"]["runner_image_id"].removeprefix("sha256:"),
            _manifest()["artifacts"]["runner_image"].rsplit("@sha256:", 1)[-1],
        ):
            changed = _manifest()
            changed["repository"]["source_content_sha256"] = value
            with self.subTest(value=value), self.assertRaises(
                controller.ControllerRejected
            ):
                controller.parse_and_validate_manifest(_encoded(changed))

    def test_source_content_pins_sources_python_and_build_context(self) -> None:
        accepted = controller.parse_and_validate_manifest(_encoded(_manifest()))
        entries = accepted.source_content["build_context"]["entries"]
        self.assertEqual(
            tuple((entry["path"], entry["type"]) for entry in entries),
            controller._CONTEXT_MEMBERS,
        )
        self.assertEqual(
            accepted.source_content["build_context"]["manifest_sha256"],
            _fixture_hash(entries),
        )
        mutations = (
            (("base", "reference"), "docker.io/frappe/erpnext:latest"),
            (("sources", "frappe", "revision"), "0" * 40),
            (("sources", "erpnext", "revision"), "0" * 40),
            (("python", "path"), "/usr/bin/python3.14"),
        )
        for path, value in mutations:
            changed = _manifest()
            target = changed["source_content"]
            for component in path[:-1]:
                target = target[component]
            target[path[-1]] = value
            _refresh_source_hash(changed)
            with self.subTest(path=path), self.assertRaises(
                controller.ControllerRejected
            ):
                controller.parse_and_validate_manifest(_encoded(changed))

    def test_source_content_rejects_context_drift_and_malformed_fields(self) -> None:
        cases = []
        unexpected = _manifest()
        unexpected["source_content"]["build_context"]["entries"][0]["path"] = "other"
        cases.append(unexpected)
        duplicate = _manifest()
        duplicate["source_content"]["build_context"]["entries"][1]["path"] = "frappe"
        cases.append(duplicate)
        symlink = _manifest()
        symlink["source_content"]["build_context"]["entries"][0]["type"] = "symlink"
        cases.append(symlink)
        boolean = _manifest()
        boolean["source_content"]["python"]["size_bytes"] = True
        cases.append(boolean)
        for index, changed in enumerate(cases):
            _refresh_context_hash(changed)
            with self.subTest(index=index), self.assertRaises(
                controller.ControllerRejected
            ):
                controller.parse_and_validate_manifest(_encoded(changed))


class RouteBDerivativeRunnerBoundaryTests(unittest.TestCase):
    def test_final_filesystem_is_derived_and_independently_observed(self) -> None:
        manifest = controller.parse_and_validate_manifest(_encoded(_manifest()))
        expected = controller._expected_final_filesystem_document(
            manifest.source_content
        )
        observed = controller.validate_final_filesystem_observation(
            manifest, _encoded(expected)
        )
        self.assertEqual(observed["entries"], expected["entries"])
        self.assertEqual(
            observed["manifest_sha256"],
            _fixture_hash(expected["entries"]),
        )
        for mutation in ("missing", "unexpected", "hash"):
            changed = copy.deepcopy(expected)
            if mutation == "missing":
                changed["entries"].pop()
            elif mutation == "unexpected":
                changed["entries"].append(copy.deepcopy(changed["entries"][-1]))
            else:
                changed["entries"][4]["sha256"] = hashlib.sha256(
                    b"unexpected materialization"
                ).hexdigest()
            with self.subTest(mutation=mutation), self.assertRaises(
                controller.ControllerRejected
            ):
                controller.validate_final_filesystem_observation(
                    manifest, _encoded(changed)
                )

    def test_materialization_attestation_is_controller_owned_closed_and_bound(self) -> None:
        manifest = controller.parse_and_validate_manifest(_encoded(_manifest()))
        attestation = _materialization_attestation(manifest)
        self.assertEqual(
            set(attestation),
            set(controller._MATERIALIZATION_KEYS),
        )
        self.assertEqual(
            attestation["source_content_sha256"],
            manifest.repository["source_content_sha256"],
        )
        self.assertEqual(
            attestation["final_image"]["repository_digest"],
            manifest.artifacts["runner_image"],
        )
        self.assertTrue(
            attestation["verification_containment"][
                "verification_container_retired"
            ]
        )
        for section, key, value in (
            ("final_image", "image_id", f"sha256:{SHA_B}"),
            (
                "final_filesystem", "manifest_sha256",
                manifest.repository["source_content_sha256"],
            ),
            ("verification_containment", "extra", True),
        ):
            changed = copy.deepcopy(attestation)
            changed[section][key] = value
            with self.subTest(section=section, key=key), self.assertRaises(
                controller.ControllerRejected
            ):
                controller._validate_materialization_attestation(
                    manifest, changed
                )

    def test_runner_inspection_binds_identity_configuration_and_source_hash(self) -> None:
        manifest = controller.parse_and_validate_manifest(_encoded(_manifest()))
        observed = _runner_observation(manifest)
        self.assertEqual(
            observed["final_image"]["image_id"],
            manifest.artifacts["runner_image_id"],
        )
        self.assertEqual(
            observed["final_image"]["repository_digest"],
            manifest.artifacts["runner_image"],
        )
        self.assertEqual(
            set(controller._runner_environment_overrides(manifest)),
            {
                "PYTHONDONTWRITEBYTECODE", "PYTHONNOUSERSITE",
                "PYTHONUNBUFFERED", "PYTHONPATH", "ERPAI_FRONTEND_POLICY",
                "ERPAI_SOURCE_REPOSITORY_REVISION", "ERPAI_FRAPPE_REVISION",
                "ERPAI_ERPNEXT_REVISION",
                "ERPAI_BUILD_CONTEXT_MANIFEST_SHA256",
                "ERPAI_BUILD_MANIFEST_SHA256", "ERPAI_SOURCE_CONTENT_SHA256",
                "ERPAI_DOCKERFILE_SHA256", "ERPAI_FRAPPE_TREE_SHA256",
                "ERPAI_ERPNEXT_TREE_SHA256",
                "ERPAI_PACKAGE_INITIALIZER_SHA256",
                "ERPAI_FINANCE_INITIALIZER_SHA256", "ERPAI_CORE_SHA256",
                "ERPAI_ADAPTER_SHA256", "ERPAI_RUNTIME_SHA256",
                "ERPAI_PROBE_SHA256", "ERPAI_INITIALIZER_SHA256",
                "ERPAI_RUNNER_PYTHON_VERSION", "ERPAI_RUNNER_PYTHON_SHA256",
            },
        )
        plans = controller._preflight_plan(manifest)
        base_spec = next(
            item for item in plans if item.name == "inspect-base_image"
        )
        base = controller._validate_preflight_result(
            manifest,
            base_spec,
            controller._CommandResult(
                0, _image_inspect(manifest, "base_image"), b"", False
            ),
        )
        self.assertIsNotNone(base)
        runner_spec = next(
            item for item in plans if item.name == "inspect-runner_image"
        )
        mutations = []
        wrong_source = _runner_image_config(manifest)
        wrong_source["Env"] = [
            item if not item.startswith("ERPAI_SOURCE_CONTENT_SHA256=")
            else "ERPAI_SOURCE_CONTENT_SHA256=" + SHA_C
            for item in wrong_source["Env"]
        ]
        mutations.append(wrong_source)
        extra_environment = _runner_image_config(manifest)
        extra_environment["Env"].append("UNAPPROVED=value")
        mutations.append(extra_environment)
        changed_label = _runner_image_config(manifest)
        changed_label["Labels"] = {"unexpected": "drift"}
        mutations.append(changed_label)
        changed_command = _runner_image_config(manifest)
        changed_command["Cmd"] = None
        mutations.append(changed_command)
        for index, config in enumerate(mutations):
            with self.subTest(index=index), self.assertRaises(
                controller.ControllerRejected
            ):
                controller._validate_preflight_result(
                    manifest,
                    runner_spec,
                    controller._CommandResult(
                        0,
                        _image_inspect(
                            manifest, "runner_image", config=config
                        ),
                        b"",
                        False,
                    ),
                    base_configuration=base["configuration"],
                )

    def test_content_verifier_attests_containment_before_retirement(self) -> None:
        manifest = controller.parse_and_validate_manifest(_encoded(_manifest()))
        created = controller._validate_content_create_result(
            controller._CommandResult(
                0, (SHA_A + "\n").encode(), b"", False
            )
        )
        identifier, containment = controller._validate_content_container(
            manifest,
            created,
            controller._CommandResult(
                0, _content_container_inspect(manifest), b"", False
            ),
        )
        self.assertEqual(identifier, SHA_A)
        self.assertEqual(containment["network_mode"], "none")
        self.assertFalse(containment["container_started"])
        self.assertFalse(containment["verification_container_retired"])
        plan = controller._content_verification_plan(manifest)
        names = [item.name for item in plan]
        self.assertEqual(
            names,
            [
                "content-verify-create", "content-verify-container",
                "content-copy-apps", "content-copy-erpai",
                "content-copy-python", "content-verify-retire",
            ],
        )
        self.assertNotIn("run", plan[0].argv)
        self.assertEqual(plan[0].argv[-2:], ("/bin/false", manifest.artifacts["runner_image_id"]))
        for spec in plan:
            self.assertNotIn("-c", spec.argv)
            self.assertNotIn(controller._RUNNER_PYTHON, spec.argv)

    def test_route_b_rootlesskit_paths_are_short_deterministic_and_run_scoped(self) -> None:
        first = controller._rootlesskit_runtime_dir(RUN_ID, 1000)
        self.assertEqual(first, f"/run/user/1000/gtb-{RUN_ID}")
        self.assertEqual(
            first, controller._rootlesskit_runtime_dir(RUN_ID, 1000)
        )
        self.assertNotEqual(
            first, controller._rootlesskit_runtime_dir("f" * 12, 1000)
        )
        self.assertLess(len(first), len(RUN_ROOT))
        self.assertLessEqual(len(first.encode("utf-8")), 48)
        socket_path = f"{RUN_ROOT}/docker/docker.sock"
        self.assertLessEqual(
            len(socket_path.encode("utf-8")),
            controller._UNIX_SOCKET_PATH_MAX_BYTES,
        )
        with self.assertRaises(controller.ControllerRejected):
            controller._rootlesskit_runtime_dir(RUN_ID, 10 ** 40)

    def test_route_b_cgroup_claim_boundary(self) -> None:
        observed = controller.parse_and_validate_manifest(
            _encoded(_manifest("observe"))
        )
        self.assertEqual(
            observed.docker["cgroup_authority"],
            "compatibility_observation_only",
        )
        invalid = _manifest("validate")
        invalid["docker"]["cgroup_driver"] = "none"
        invalid["docker"]["cgroup_authority"] = "compatibility_observation_only"
        with self.assertRaises(controller.ControllerRejected):
            controller.parse_and_validate_manifest(_encoded(invalid))
        observed_artifact = controller._artifact_provenance(
            observed, _materialization_attestation(observed)
        )
        self.assertEqual(
            observed_artifact["cgroup_claim"]["status"],
            "compatibility_observation_only",
        )
        self.assertEqual(
            set(observed_artifact["source_content"]),
            {"sha256", "contract"},
        )
        self.assertIn("materialization_attestation", observed_artifact)
        self.assertNotIn("runner_content", observed_artifact)
        validated = controller.parse_and_validate_manifest(
            _encoded(_manifest("validate"))
        )
        validation_artifact = controller._artifact_provenance(
            validated, _materialization_attestation(validated)
        )
        self.assertEqual(
            validation_artifact["cgroup_claim"]["status"],
            "external_delegation_prerequisite_bound",
        )
        self.assertNotEqual(
            validation_artifact["result"], "delegated_cgroup_v2_verified"
        )

    def test_route_b_materialization_failures_are_generic_discard_only(self) -> None:
        manifest = controller.parse_and_validate_manifest(_encoded(_manifest()))
        leaked = {
            "schema": "erpai.gl_tb.runtime_compat.final_filesystem.v1",
            "python": manifest.source_content["python"],
            "entries": controller._expected_final_filesystem_document(
                manifest.source_content
            )["entries"],
            "company": "LEAK",
        }
        with self.assertRaises(controller.ControllerRejected) as raised:
            controller.validate_final_filesystem_observation(
                manifest, _encoded(leaked)
            )
        self.assertEqual(raised.exception.args, ())
        self.assertNotIn("LEAK", repr(raised.exception))

        plan = controller._content_verification_plan(manifest)
        create_ok = controller._CommandResult(
            0, (SHA_A + "\n").encode(), b"", False
        )
        inspect_ok = controller._CommandResult(
            0, _content_container_inspect(manifest), b"", False
        )
        archive_ok = controller._CommandResult(0, b"archive", b"", False)
        retire_ok = controller._CommandResult(
            0, (SHA_A + "\n").encode(), b"", False
        )
        failure_sets = (
            (controller._CommandResult(1, b"", b"LEAK", False),),
            (
                create_ok,
                controller._CommandResult(0, b"bad\n", b"", False),
            ),
            (
                create_ok, inspect_ok,
                controller._CommandResult(1, b"", b"LEAK", False),
            ),
            (
                create_ok, inspect_ok, archive_ok, archive_ok, archive_ok,
                controller._CommandResult(0, b"wrong\n", b"", False),
            ),
        )
        for index, results in enumerate(failure_sets):
            with (
                self.subTest(index=index),
                mock.patch.object(controller, "_preflight"),
                mock.patch.object(controller, "_phase_plan", return_value=plan),
                mock.patch.object(
                    controller, "_run_subprocess", side_effect=results
                ),
                mock.patch.object(
                    controller, "_parse_content_archive",
                    return_value={"/synthetic": {}},
                ),
                mock.patch.object(
                    controller, "_recover_teardown", return_value=True
                ) as teardown,
                mock.patch.object(controller, "_write_discard") as discard,
                mock.patch.object(controller, "_promote_evidence") as promote,
            ):
                with self.assertRaises(controller.ControllerRejected):
                    controller._execute_phase(manifest)
                teardown.assert_called_once_with(manifest)
                discard.assert_called_once_with(manifest, "observe")
                promote.assert_not_called()

    def test_route_b_observe_validate_binding_and_promotion_are_separate(self) -> None:
        observe = controller.parse_and_validate_manifest(
            _encoded(_manifest("observe"))
        )
        validate = controller.parse_and_validate_manifest(
            _encoded(_manifest("validate"))
        )
        for manifest, command in ((observe, "observe"), (validate, "validate")):
            names = [
                spec.name
                for spec in controller.build_child_command_plan(manifest, command)
            ]
            self.assertLess(
                names.index("content-verify-create"), names.index("stack-up")
            )
            content_plan = controller._content_verification_plan(manifest)
            create = next(
                spec for spec in content_plan
                if spec.name == "content-verify-create"
            )
            self.assertIn("--network", create.argv)
            self.assertIn("none", create.argv)
            self.assertIn("--read-only", create.argv)
            self.assertIn("--cap-drop", create.argv)
            self.assertNotIn("/usr/bin/python3.14", create.argv)
            self.assertNotIn("run", create.argv)
            for spec in content_plan:
                self.assertTrue(
                    spec.argv[:3] == manifest.docker_prefix
                )
                self.assertNotIn("-c", spec.argv)

    def test_execute_phase_promotes_only_after_stopped_image_proof_and_teardown(
        self,
    ) -> None:
        manifest = controller.parse_and_validate_manifest(
            _encoded(_manifest("observe"))
        )
        plan = controller._phase_plan(manifest)
        events: list[str] = []
        observation = {
            "schema": "erpai.gl_tb.runtime_compat.observation.v2",
            "mode": "observe",
            "run_id": RUN_ID,
            "result": "pass",
            "error": "",
            "wrapper_module": "frappe.database.mariadb.database",
            "wrapper_class": "MariaDBDatabase",
            "raw_module": "pymysql.connections",
            "raw_class": "Connection",
            "driver": "pymysql",
            "driver_distribution": "PyMySQL",
            "driver_version": "1.1.2",
            "server_version": "10.11.18-MariaDB-disposable",
            "initial_transaction_inactive": True,
            "isolation_repeatable_read": True,
            "transaction_read_only": True,
            "consistent_snapshot_started": True,
            "transaction_active": True,
            "wrapper_stable": True,
            "raw_connection_stable": True,
            "server_connection_stable": True,
            "rollback_no_chain_succeeded": True,
            "final_transaction_inactive": True,
            "connection_id_commitment": SHA_A,
            "primary_route": True,
            "replica_denied": True,
            "partial_output": False,
        }
        payload = controller.canonical_json_bytes(observation)
        tar_output = io.BytesIO()
        with tarfile.open(fileobj=tar_output, mode="w:") as archive:
            member = tarfile.TarInfo("observation-result.json")
            member.size = len(payload)
            member.mode = 0o600
            archive.addfile(member, io.BytesIO(payload))
        probe_tar = tar_output.getvalue()

        def run(spec: object, _environment: object) -> object:
            events.append(spec.name)
            if spec.name == "content-verify-create":
                return controller._CommandResult(
                    0, (SHA_A + "\n").encode(), b"", False
                )
            if spec.name == "content-verify-container":
                self.assertEqual(spec.argv[-1], SHA_A)
                return controller._CommandResult(
                    0, _content_container_inspect(manifest), b"", False
                )
            if spec.name.startswith("content-copy-"):
                self.assertTrue(spec.argv[-2].startswith(SHA_A + ":"))
                return controller._CommandResult(0, b"archive", b"", False)
            if spec.name == "content-verify-retire":
                self.assertEqual(spec.argv[-1], SHA_A)
                return controller._CommandResult(
                    0, (SHA_A + "\n").encode(), b"", False
                )
            if spec.name == "site-initialize":
                return controller._CommandResult(
                    0, b"initialized\n", b"", False
                )
            if spec.name.startswith("inspect-probe-"):
                return controller._CommandResult(
                    0,
                    _probe_container_inspect(
                        manifest, "environment_observation",
                        {0: SHA_C},
                    ),
                    b"",
                    False,
                )
            if spec.name.startswith("copy-evidence-"):
                self.assertTrue(spec.argv[-2].startswith(SHA_C + ":"))
                return controller._CommandResult(0, probe_tar, b"", False)
            return controller._CommandResult(0, b"", b"", False)

        promoted: list[tuple[object, object, object, object]] = []
        with (
            mock.patch.object(
                controller, "_preflight",
                return_value=_runner_observation(manifest),
            ),
            mock.patch.object(controller, "_phase_plan", return_value=plan),
            mock.patch.object(controller, "_run_subprocess", side_effect=run),
            mock.patch.object(
                controller, "_parse_content_archive",
                side_effect=lambda _manifest, name, _body: {
                    f"/{name}": {"type": "synthetic"}
                },
            ),
            mock.patch.object(
                controller, "_final_filesystem_from_archives",
                return_value=_filesystem_observation(manifest),
            ),
            mock.patch.object(
                controller, "_recover_teardown",
                side_effect=lambda _manifest: events.append("teardown") or True,
            ),
            mock.patch.object(
                controller, "_promote_or_discard",
                side_effect=lambda *args: (
                    events.append("promote"), promoted.append(args)
                ),
            ),
            mock.patch.object(controller, "_write_discard") as discard,
        ):
            controller._execute_phase(manifest)
        self.assertEqual(
            events,
            [item.name for item in plan] + ["teardown", "promote"],
        )
        discard.assert_not_called()
        self.assertEqual(len(promoted), 1)
        attestation = promoted[0][1]
        self.assertEqual(
            attestation["source_content_sha256"],
            manifest.repository["source_content_sha256"],
        )
        self.assertFalse(
            attestation["verification_containment"]["container_started"]
        )
        self.assertTrue(
            attestation["verification_containment"][
                "verification_container_retired"
            ]
        )



    def test_route_b_promotion_schema_hashes_and_atomic_directory_rename(self) -> None:
        for phase in ("observe", "validate"):
            manifest = controller.parse_and_validate_manifest(
                _encoded(_manifest(phase))
            )
            if manifest.policy is not None:
                with self.assertRaises(controller.ControllerRejected):
                    controller._promote_evidence(
                        manifest,
                        _materialization_attestation(manifest),
                        [{"case_id": case_id} for case_id in manifest.canaries],
                        [{"name": "bounded-process"}],
                    )
                manifest.policy["artifact_manifest_sha256"] = (
                    controller._artifact_binding_sha256(manifest)
                )
            writes: dict[str, bytes] = {}

            def capture(path: object, body: bytes) -> None:
                writes[Path(str(path)).name] = body

            with (
                self.subTest(phase=phase),
                mock.patch.object(controller.os.path, "exists", return_value=False),
                mock.patch.object(controller.os, "mkdir") as mkdir,
                mock.patch.object(controller, "_atomic_write", side_effect=capture),
                mock.patch.object(controller.os, "replace") as replace,
            ):
                controller._promote_evidence(
                    manifest,
                    _materialization_attestation(manifest),
                    [{"case_id": case_id} for case_id in manifest.canaries],
                    [{"name": "bounded-process"}],
                )
            staging = str(manifest.evidence["staging_directory"])
            evidence = str(manifest.evidence["directory"])
            mkdir.assert_called_once_with(staging, 0o700)
            replace.assert_called_once_with(staging, evidence)
            self.assertEqual(set(writes), set(controller._EVIDENCE_FILES))
            artifact = json.loads(writes["artifact-provenance.json"])
            self.assertEqual(
                artifact["schema"],
                "erpai.gl_tb.runtime_compat.artifact_provenance.v3",
            )
            self.assertEqual(
                artifact["source_content"]["sha256"],
                manifest.repository["source_content_sha256"],
            )
            self.assertEqual(
                artifact["materialization_attestation"]["final_image"][
                    "repository_digest"
                ],
                manifest.artifacts["runner_image"],
            )
            observation = json.loads(writes["observation-result.json"])
            validation = json.loads(writes["validation-result.json"])
            if phase == "observe":
                self.assertEqual(
                    observation["schema"],
                    "erpai.gl_tb.runtime_compat.observation_bundle.v1",
                )
                self.assertEqual(validation["result"], "not_run")
            else:
                self.assertEqual(
                    validation["schema"],
                    "erpai.gl_tb.runtime_compat.validation_bundle.v1",
                )
                self.assertEqual(
                    observation["sha256"],
                    manifest.policy["observation_result_sha256"],
                )
            lines = writes["evidence-manifest.sha256"].decode("ascii").splitlines()
            self.assertEqual(len(lines), len(controller._EVIDENCE_FILES) - 1)
            for line, name in zip(lines, controller._EVIDENCE_FILES[:-1], strict=True):
                digest, separator, recorded_name = line.partition("  ")
                self.assertEqual(separator, "  ")
                self.assertEqual(recorded_name, name)
                self.assertEqual(digest, hashlib.sha256(writes[name]).hexdigest())

    def test_route_b_promotion_failure_cleans_staging_and_records_discard(self) -> None:
        manifest = controller.parse_and_validate_manifest(_encoded(_manifest("observe")))
        with (
            mock.patch.object(
                controller, "_promote_evidence", side_effect=OSError("LEAK")
            ),
            mock.patch.object(
                controller, "_remove_failed_staging", return_value=True
            ) as cleanup,
            mock.patch.object(controller.os.path, "lexists", return_value=False),
            mock.patch.object(controller, "_write_discard") as discard,
        ):
            with self.assertRaises(controller.ControllerRejected):
                controller._promote_or_discard(
                    manifest,
                    {},
                    [{"case_id": "environment_observation"}],
                    [],
                )
        cleanup.assert_called_once_with(manifest)
        discard.assert_called_once_with(manifest, "observe")

    def test_route_b_completed_evidence_is_immutable_on_duplicate_failure(self) -> None:
        manifest = controller.parse_and_validate_manifest(_encoded(_manifest("observe")))
        with (
            mock.patch.object(
                controller, "_promote_evidence", side_effect=controller.ControllerRejected()
            ),
            mock.patch.object(
                controller, "_remove_failed_staging", return_value=True
            ) as cleanup,
            mock.patch.object(controller.os.path, "lexists", return_value=True),
            mock.patch.object(controller, "_write_discard") as discard,
        ):
            with self.assertRaises(controller._ControllerInternal):
                controller._promote_or_discard(manifest, {}, [], [])
        cleanup.assert_called_once_with(manifest)
        discard.assert_not_called()

        with (
            mock.patch.object(controller.os.path, "lexists", return_value=True),
            mock.patch.object(controller.os, "mkdir") as mkdir,
            mock.patch.object(controller.os, "open") as open_file,
        ):
            with self.assertRaises(controller.ControllerRejected):
                controller._write_discard(manifest, "observe")
        mkdir.assert_not_called()
        open_file.assert_not_called()

    def test_route_b_host_owned_archive_scanner_semantics(self) -> None:
        manifest = controller.parse_and_validate_manifest(_encoded(_manifest()))

        def archive(members: list[tuple[str, str, bytes]]) -> bytes:
            output = io.BytesIO()
            with tarfile.open(fileobj=output, mode="w:") as stream:
                for name, kind, payload in members:
                    member = tarfile.TarInfo(name)
                    member.uid = 1000
                    member.gid = 1000
                    member.mode = 0o555 if kind == "directory" else 0o444
                    if kind == "directory":
                        member.type = tarfile.DIRTYPE
                        member.size = 0
                        stream.addfile(member)
                    elif kind == "regular":
                        member.size = len(payload)
                        stream.addfile(member, io.BytesIO(payload))
                    elif kind == "symlink":
                        member.type = tarfile.SYMTYPE
                        member.linkname = "target"
                        stream.addfile(member)
                    else:
                        raise AssertionError(kind)
            return output.getvalue()

        valid = archive([
            ("apps", "directory", b""),
            ("apps/frappe", "directory", b""),
            ("apps/frappe/A.py", "regular", b"alpha\n"),
        ])
        records = controller._parse_content_archive(
            manifest, "apps", valid
        )
        self.assertEqual(
            records[
                "/home/frappe/frappe-bench/apps/frappe/A.py"
            ]["sha256"],
            hashlib.sha256(b"alpha\n").hexdigest(),
        )
        cases = (
            archive([
                ("apps", "directory", b""),
                ("apps/link", "symlink", b""),
            ]),
            archive([
                ("apps", "directory", b""),
                ("apps/A.py", "regular", b"a"),
                ("apps/a.py", "regular", b"b"),
            ]),
            archive([
                ("other", "directory", b""),
            ]),
            archive([
                ("apps", "directory", b""),
                ("apps/../escape", "regular", b"x"),
            ]),
        )
        for index, body in enumerate(cases):
            with self.subTest(index=index), self.assertRaises(
                controller.ControllerRejected
            ):
                controller._parse_content_archive(
                    manifest, "apps", body
                )



class InitializerAndStaticContractTests(unittest.TestCase):
    def test_initializer_cli_is_exact_and_generic(self) -> None:
        expected = ("initialize", "--manifest", "/run/secrets/site-init-manifest.json")
        self.assertEqual(initializer._parse_cli(expected), expected[2])
        for argv in ((), expected + ("extra",), ("init", "--manifest", expected[2])):
            with self.subTest(argv=argv), self.assertRaises(initializer.InitializerRejected):
                initializer._parse_cli(argv)
        stderr = io.StringIO()
        with mock.patch.object(initializer, "load_and_validate_manifest", side_effect=RuntimeError("ROOT PASSWORD LEAK")), mock.patch.object(sys, "stderr", stderr):
            code = initializer.main(expected)
        self.assertEqual(code, 70)
        self.assertEqual(stderr.getvalue(), "runtime_compatibility_unavailable\n")

    def test_initializer_creates_no_business_or_accounting_fixture(self) -> None:
        source = INITIALIZER_PATH.read_text(encoding="utf-8")
        for forbidden in (
            "GL Entry",
            "tabAccount",
            "Company(",
            "install_apps=(\"erpnext\"",
            "sendmail",
            "scheduler",
            "notification",
        ):
            self.assertNotIn(forbidden, source)
        self.assertIn("install_apps=()", source)
        self.assertNotIn("shell=True", source)
        self.assertNotIn("io.StringIO()", source)
        self.assertIn("class _DiscardText", source)
        self.assertIn("sites_status.st_uid != 1000", source)
        self.assertIn("sites_status.st_gid != 1000", source)

    def test_dockerfile_has_immutable_non_root_offline_contract(self) -> None:
        text = DOCKERFILE_PATH.read_text(encoding="utf-8")
        self.assertNotIn("# syntax=", text)
        self.assertIn(f"FROM {BASE_IMAGE}", text)
        self.assertIn("engine_builtin", text)
        self.assertIn(PYTHON_PATH, text)
        self.assertNotIn("/usr/bin/python3.14", text)
        self.assertIn(FRAPPE_REVISION, text)
        self.assertIn(ERPNEXT_REVISION, text)
        self.assertIn("USER 1000:1000", text)
        self.assertIn(
            'ENTRYPOINT ["/opt/erpai/finance_gl_trial_balance_runtime_compatibility_probe.py"]',
            text,
        )
        self.assertIn("CMD []", text)
        self.assertIn("/home/frappe/frappe-bench/apps/frappe/", text)
        self.assertIn("/home/frappe/frappe-bench/apps/erpnext/", text)
        self.assertNotIn("COPY .", text)
        self.assertIn("--chown=1000:1000", text)
        self.assertIn("--chmod=0555", text)
        self.assertNotIn("CONTENT_MANIFEST_SHA256", text)
        self.assertIn(
            "ERPAI_SOURCE_CONTENT_SHA256=${SOURCE_CONTENT_SHA256}", text
        )
        for argument in (
            "BUILD_CONTEXT_MANIFEST_SHA256", "BUILD_MANIFEST_SHA256",
            "SOURCE_CONTENT_SHA256", "FRAPPE_TREE_SHA256",
            "ERPNEXT_TREE_SHA256", "CORE_SHA256", "ADAPTER_SHA256",
            "RUNTIME_SHA256", "PROBE_SHA256", "INITIALIZER_SHA256",
            "RUNNER_PYTHON_VERSION", "RUNNER_PYTHON_SHA256",
        ):
            self.assertEqual(text.count(f"ARG {argument}"), 1)
        self.assertIn("erpai.gl_tb.runtime_compat.build_context.v1", text)
        self.assertIn("set(by_path)==set(expected_hashes)", text)
        self.assertIn("opt.iterdir()", text)
        self.assertIn("tuple(apps.iterdir())", text)
        self.assertIn("os.chmod(apps,0o555)", text)
        for forbidden in (
            "apt-get", "apk add", "pip install", "curl ", "wget ",
            "git clone", "latest",
        ):
            self.assertNotIn(forbidden, text)
        self.assertEqual(
            PROBE_PATH.read_text(encoding="utf-8").splitlines()[0],
            f"#!{PYTHON_PATH}",
        )
        self.assertEqual(
            INITIALIZER_PATH.read_text(encoding="utf-8").splitlines()[0],
            f"#!{PYTHON_PATH}",
        )
        self.assertEqual(
            probe._MANIFEST_SCHEMA,
            controller._EXECUTION_SCHEMA,
        )
        self.assertIn("source_content", probe._TOP_KEYS)
        self.assertNotIn("content_manifest", probe._TOP_KEYS)

    def test_compose_is_internal_immutable_and_narrow(self) -> None:
        text = COMPOSE_PATH.read_text(encoding="utf-8")
        for variable in ("GL_TB_RUNNER_IMAGE", "GL_TB_MARIADB_IMAGE", "GL_TB_REDIS_IMAGE"):
            self.assertIn(variable, text)
        self.assertGreaterEqual(text.count("pull_policy: never"), 4)
        self.assertIn("internal: true", text)
        self.assertIn("no-new-privileges:true", text)
        self.assertIn("cap_drop:", text)
        for forbidden in (
            "ports:",
            "privileged: true",
            "docker.sock",
            "network_mode: host",
            "host-gateway",
            "restart: always",
            "image: mariadb:latest",
            "worker:",
            "scheduler:",
            "websocket:",
            "type: bind",
            "/run/config",
        ):
            self.assertNotIn(forbidden, text)
        self.assertIn("/run/secrets/site-init-manifest.json", text)
        self.assertIn("target: execution-manifest.json", text)
        self.assertIn("target: runtime-policy.json", text)
        self.assertIn("/evidence:rw,noexec,nosuid,nodev", text)
        self.assertEqual(
            text.count("FRAPPE_REDIS_CACHE: redis://redis-cache:6379"), 2
        )
        self.assertNotIn("MARIADB_DATABASE:", text)
        self.assertNotIn("MARIADB_USER:", text)
        self.assertNotIn("MARIADB_PASSWORD_FILE:", text)
        self.assertEqual(
            text.split("redis-cache:", 1)[0].count("site-db-password"), 0
        )
        sites_mounts = text.split("source: sites")[1:]
        self.assertEqual(len(sites_mounts), 2)
        self.assertTrue(all("nocopy: false" in value for value in sites_mounts))

    def test_all_staged_modules_are_import_inert(self) -> None:
        sources = (
            (CONTROLLER_PATH, "_controller_inert_probe"),
            (PROBE_PATH, "_probe_inert_probe"),
            (INITIALIZER_PATH, "_initializer_inert_probe"),
        )
        original_import = builtins.__import__

        def guarded_import(name: str, *args: object, **kwargs: object) -> object:
            if name.split(".", 1)[0] in {"frappe", "pymysql", "MySQLdb", "erp_workspace_ui"}:
                raise AssertionError(f"forbidden import: {name}")
            return original_import(name, *args, **kwargs)

        for path, name in sources:
            code = compile(path.read_bytes(), str(path), "exec")
            module = types.ModuleType(name)
            module.__file__ = str(path)
            module.__package__ = ""
            sys.modules[name] = module
            try:
                with (
                    mock.patch("builtins.__import__", side_effect=guarded_import),
                    mock.patch("builtins.open", side_effect=AssertionError("filesystem")),
                    mock.patch("os.open", side_effect=AssertionError("filesystem")),
                    mock.patch("os.lstat", side_effect=AssertionError("filesystem")),
                    mock.patch("subprocess.Popen", side_effect=AssertionError("process")),
                    mock.patch("socket.socket", side_effect=AssertionError("network")),
                ):
                    exec(code, module.__dict__)
            finally:
                sys.modules.pop(name, None)


if __name__ == "__main__":
    unittest.main()
