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
SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64
IMAGE_A = f"registry.example/erpai/runner@sha256:{SHA_A}"
IMAGE_B = f"registry.example/library/mariadb@sha256:{SHA_B}"
IMAGE_C = f"registry.example/library/redis@sha256:{SHA_C}"


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
        "schema": "erpai.gl_tb.runtime_compat.execution.v1",
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
        },
        "artifacts": {
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
            "os": "linux",
            "architecture": "amd64",
        },
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
    class _Cursor:
        def __init__(self, row: tuple[object, ...]) -> None:
            self.row = row
            self.calls = 0
            self.statement = None
            self.closed = False

        def execute(self, statement: str) -> None:
            self.statement = statement

        def fetchone(self) -> object:
            self.calls += 1
            return self.row if self.calls == 1 else None

        def close(self) -> None:
            self.closed = True

    @staticmethod
    def _frappe(row: tuple[object, ...] = ("10.11.18-MariaDB-disposable", 731, 0, "REPEATABLE-READ", 0)) -> tuple[object, object, object]:
        cursor = ProbeBoundaryTests._Cursor(row)
        raw_type = type("Connection", (), {"__module__": "pymysql.connections"})
        raw = raw_type()
        raw.cursor = lambda: cursor
        raw.open = True
        wrapper_type = type("MariaDBDatabase", (), {"__module__": "frappe.database.mariadb.database"})
        wrapper = wrapper_type()
        wrapper._conn = raw
        local = types.SimpleNamespace(db=wrapper, primary_db=None, replica_db=None, conf={}, session={"user": "Guest"})
        frappe = types.SimpleNamespace(local=local)
        return frappe, raw, cursor

    def test_observation_is_runtime_free_and_sanitized(self) -> None:
        frappe, _raw, cursor = self._frappe()
        manifest = _manifest("observe")
        with (
            mock.patch.object(probe, "_connect_site", return_value=frappe),
            mock.patch.object(probe, "_destroy_site") as destroy,
            mock.patch.object(probe.metadata, "version", return_value="1.1.2") as version,
            mock.patch.object(probe, "_connection_commitment", return_value=SHA_A),
            mock.patch.object(probe, "_runtime_objects", side_effect=AssertionError("runtime forbidden")),
        ):
            result = probe.observe(manifest)
        self.assertEqual(cursor.statement, probe._STATE_SQL)
        self.assertEqual(version.call_args.args, ("PyMySQL",))
        destroy.assert_called_once_with(frappe)
        self.assertEqual(result["driver"], "pymysql")
        self.assertEqual(result["connection_id_commitment"], SHA_A)
        rendered = repr(result)
        self.assertNotIn("731", rendered)
        self.assertNotIn("Guest", rendered)
        self.assertNotIn("policy", rendered.lower())

    def test_observation_denies_replica_and_active_transaction(self) -> None:
        for mutation in ("replica", "transaction"):
            frappe, _raw, _cursor = self._frappe(
                ("10.11.18-MariaDB-disposable", 731, 1 if mutation == "transaction" else 0, "REPEATABLE-READ", 0)
            )
            if mutation == "replica":
                frappe.local.replica_db = object()
            with (
                mock.patch.object(probe, "_connect_site", return_value=frappe),
                mock.patch.object(probe, "_destroy_site"),
                mock.patch.object(probe.metadata, "version", return_value="1.1.2"),
            ):
                with self.subTest(mutation=mutation), self.assertRaises(probe.ProbeRejected):
                    probe.observe(_manifest("observe"))

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
        with mock.patch.object(probe, "_load_manifest", side_effect=RuntimeError("COMPANY SECRET SQL")), mock.patch.object(sys, "stderr", stderr):
            code = probe.main(valid_observe)
        self.assertEqual(code, 70)
        self.assertEqual(stderr.getvalue(), "runtime_compatibility_unavailable\n")


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
            "schema": "erpai.gl_tb.runtime_compat.observation.v1",
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
            "transaction_state": {
                "active": 0,
                "isolation": "REPEATABLE-READ",
                "read_only": 0,
            },
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
        leaked = dict(record)
        leaked["company"] = "LEAK"
        with self.assertRaises(controller.ControllerRejected):
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
        inspect_body = (
            f"{SHA_A}\tsha256:{SHA_A}\t/{PROJECT}_probe_{case_id}"
            f"\texited\tfalse\t0\tfalse\t{PROJECT}_internal"
            f"\tfalse\t{RUN_ID}\t{PROJECT}\truntime-probe\n"
        ).encode()
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
        self.assertRegex(text, r"(?m)^ARG BASE_IMAGE\s*$")
        self.assertIn("FROM ${BASE_IMAGE}", text)
        self.assertIn("USER 1000:1000", text)
        self.assertIn('ENTRYPOINT ["/opt/erpai/finance_gl_trial_balance_runtime_compatibility_probe.py"]', text)
        self.assertIn("--chown=1000:1000", text)
        self.assertIn("--chmod=0555", text)
        self.assertIn("os.chown(p,1000,1000)", text)
        self.assertIn("os.chmod(p,0o700)", text)
        self.assertIn("tuple(p.iterdir())", text)
        for forbidden in ("apt-get", "apk add", "pip install", "curl ", "wget ", "git clone", "latest"):
            self.assertNotIn(forbidden, text)

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
