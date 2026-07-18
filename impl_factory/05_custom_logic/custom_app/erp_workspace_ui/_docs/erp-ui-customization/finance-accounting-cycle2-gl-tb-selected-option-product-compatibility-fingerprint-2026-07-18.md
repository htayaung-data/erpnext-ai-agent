# Finance & Accounting Cycle 2 GL / Trial Balance Selected-Option Product and Compatibility Fingerprint

Date: 2026-07-18
Authority: Main Control v2
Document class: canonical read-only product and compatibility fingerprint stop receipt
Repository: `/home/deploy/erp-projects/erpai_project1_erpnext_ui_design`
Branch: `feature/erpnext-ui-design`
Starting source and upstream: `dae7256a4c23531e0f4bfbcf0b5f1a6ebcd2410c`
Cycle posture: Finance Cycle 2 C2B evidence planning only
Controlling Owner selection: S2/J2/K1/R1/P1-W1/D1
Decision: `stopped_for_selected_option_fingerprint_gap`

## 1. Outcome and authority

This gate narrows the products, source seams, permissions and orchestration facts needed by the Owner-selected S2/J2/K1/R1/P1-W1/D1 package. It does not reopen the Four-File Source-Authoring Gate.

The selected package remains conditionally feasible within the four approved future source paths, but it is not ready for source authoring. Exact backend identity, Python runtime behavior, supported JUnit injection, Docker/Compose host facts, immutable MariaDB behavior, least-privilege Frappe bootstrap reads and two controller-owned protocol bindings remain unresolved.

No MariaDB digest is selected or approved. No complete execution schema or numeric workload limit is published. No source, product-materialization, infrastructure, secret, execution, HTTP, CORS, Finance-to-AI, live, permission, migration, protected-gate or accounting authority is created.

## 2. Controlling baseline

| Item | Verified value |
| --- | --- |
| Repository root | `/home/deploy/erp-projects/erpai_project1_erpnext_ui_design` |
| Branch | `feature/erpnext-ui-design` |
| Local HEAD at gate start | `dae7256a4c23531e0f4bfbcf0b5f1a6ebcd2410c` |
| Configured upstream | `origin/feature/erpnext-ui-design` |
| Upstream revision at gate start | `dae7256a4c23531e0f4bfbcf0b5f1a6ebcd2410c` |
| Ahead/behind at gate start | `0/0` |
| Index at gate start | empty |
| Published resolution amendment SHA-256 | `f6c36358e76febff6bd2bd8835f21e97d95439c13049288a3873142a5540a33e` |
| README SHA-256 at gate start | `d337e5dd101408c03c2cf7938e1a4ab8288277a192587f2001c8a761d1b175ca` |
| Unchanged harness SHA-256 | `c8d0bb0556f9abb04e1be69c1d67a7f92c4ed37a64d8270d84339ad590e9cea5` |
| Future controller | absent |
| Future runner Dockerfile | absent |
| Future initializer | absent |

The only worktree items at gate start were the unchanged harness candidate and the four protected exclusions. The source candidate files were not edited.

## 3. Controlling documents and evidence order

Later accepted documents supersede incompatible earlier assumptions. The controlling order used by this receipt is:

1. [Synthetic Evidence Execution Package](finance-accounting-cycle2-gl-tb-synthetic-evidence-execution-package-2026-07-17.md);
2. [Runtime Evidence Design Amendment](finance-accounting-cycle2-gl-tb-runtime-evidence-design-amendment-2026-07-18.md);
3. [Controller-Runner Control Plane and Source Delivery Amendment](finance-accounting-cycle2-gl-tb-controller-runner-control-plane-source-delivery-amendment-2026-07-18.md);
4. [Read-Only Compatibility and Protocol/Schema Freeze Gate](finance-accounting-cycle2-gl-tb-read-only-compatibility-protocol-schema-freeze-gate-2026-07-18.md);
5. [Compatibility Gap Resolution Amendment](finance-accounting-cycle2-gl-tb-compatibility-gap-resolution-amendment-2026-07-18.md);
6. [C2B1 Exact Installed-Source Fingerprint Receipt](finance-accounting-cycle2-c2b1-exact-installed-source-fingerprint-receipt-2026-07-17.md);
7. [C2B2-C2B6 Installed-Source Semantic Proof and Stop Receipt](finance-accounting-cycle2-c2b2-c2b6-installed-source-semantic-proof-2026-07-17.md);
8. [C2BG1 Targeted Gap Source Fingerprint Receipt](finance-accounting-cycle2-c2bg1-targeted-gap-source-fingerprint-receipt-2026-07-17.md); and
9. [C2BG2-C2BG5 Static Semantic Read and Stop Receipt](finance-accounting-cycle2-c2bg2-c2bg5-static-semantic-read-stop-receipt-2026-07-17.md).

Repository and installed-source receipts remain authoritative for what was actually observed. Exact pinned upstream source controls source behavior. Generic current documentation identifies candidates and proof obligations but does not establish version-bound runtime compatibility.

## 4. Evidence classification

| Class | Meaning in this receipt |
| --- | --- |
| Proven repository fact | Exact committed receipt, path, hash or unchanged harness evidence. |
| Proven registry/config fact | Fixed manifest/config metadata read from the registry without a layer download; this is not product approval. |
| Source-derived candidate fact | Exact pinned source states an implementation or signature; runtime behavior remains unproven. |
| Unproven runtime fact | Requires later image, host or controlled compatibility evidence. It cannot be inferred from a tag, name, field or generic document. |
| Later read-only gate fact | A bounded future command, registry, file or fixed-output inspection is identified but was not executed here. |
| Owner decision | A policy or seam choice required before source authoring can be reconsidered. |

Prohibited inference includes treating `Config.User=frappe` as a numeric identity, assuming `1000:1000`, treating a Python version range as an installed interpreter build, treating a mutable tag as an immutable product, copying the harness table inventory as the final grant list, or treating internal networking as authentication.

## 5. Pinned source evidence

### 5.1 Frappe and Python-facing source

Pinned Frappe: v16.5.0, commit `4dfcc56090eb3101d18ddb03750391511f163fcf`.

| Source | SHA-256 | Relevant proven source fact |
| --- | --- | --- |
| [`pyproject.toml`](https://github.com/frappe/frappe/blob/4dfcc56090eb3101d18ddb03750391511f163fcf/pyproject.toml) | `b2c8ca6b44d1c9a67a7f67a3d6394b138e429e1402c164d6f95c72a1f3d0773d` | Requires Python `>=3.14,<3.15`; it does not identify the installed patch/build/ABI. |
| [`frappe/__init__.py`](https://github.com/frappe/frappe/blob/4dfcc56090eb3101d18ddb03750391511f163fcf/frappe/__init__.py) | `3e70b6fd55b5a2947bc8961ea6ec47a41dd0f4a0e287c3c9eabed21a3c894340` | Import ends with optimization then fault-handler registration. |
| [`frappe/_optimizations.py`](https://github.com/frappe/frappe/blob/4dfcc56090eb3101d18ddb03750391511f163fcf/frappe/_optimizations.py#L56-L60) | `4b35c21d06acfb7dc454164cacb94f0501c081f3239c88f13f28e010be5569fd` | When `sys.__stderr__` is an `io.TextIOWrapper`, calls `faulthandler.enable()` and registers `SIGUSR1` with default `chain=False`. The condition means registration cannot be assumed from import alone. |
| [`frappe/utils/bench_helper.py`](https://github.com/frappe/frappe/blob/4dfcc56090eb3101d18ddb03750391511f163fcf/frappe/utils/bench_helper.py) | `77557c0b4c78de486e28f80c02b57599cc1e8f8e7ffa691a076257f96435c6e9` | Imports Frappe at module load and dispatches Click in-process. |
| [`frappe/commands/testing.py`](https://github.com/frappe/frappe/blob/4dfcc56090eb3101d18ddb03750391511f163fcf/frappe/commands/testing.py) | `3a87363eb432b8ef9379d7e6d0a8f7ba5028525de412a0a4762933da707cdb8e` | Owns test environment setup, discovery dispatch, runner construction, result aggregation, nonzero exit and ordinary cleanup. |
| [`frappe/testing/runner.py`](https://github.com/frappe/frappe/blob/4dfcc56090eb3101d18ddb03750391511f163fcf/frappe/testing/runner.py#L48-L92) | `e4c3a77eb4dd5c41f0474f26fa05b07edb6847e56ea030cbae3b9f7961aaeb6c` | Actual runner subclasses `unittest.TextTestRunner`; its public constructor can accept `resultclass`, but the pinned CLI does not pass one. |
| [`frappe/testing/result.py`](https://github.com/frappe/frappe/blob/4dfcc56090eb3101d18ddb03750391511f163fcf/frappe/testing/result.py) | `c17e1e6e12f81567ec3297af6745e4cb8dbfc928fbb3bdcc2fccc36b85399ba1` | Actual `TestResult` subclasses `unittest.TextTestResult` and owns the ordinary result callbacks. |
| `frappe/testing/discovery.py` | `db63ca823e8d611884d57b3d6d8403134f32e97979850a5cbbfb169ae8603a8b` | Imports the requested module and uses `unittest.TestLoader().loadTestsFromModule`; the current plain harness is in the unspecified category. |
| `frappe/testing/environment.py` | `b9035e54f1821cc81736c69347075428ca2328bee033ad1338efa4c2d81bd7bb` | Owns `frappe.init/connect`, scheduler posture, cache clear and test flags; ordinary cleanup may enable the scheduler, commit and clear cache. |
| `frappe/testing/config.py` | `5cf8813c74d1c121b7b489bf8eeb4685d6387c0c8c80c9e81a0c6e70f5613e9a` | Pins the configuration object consumed by the runner path. |

Authoritative Python references are [`signal`](https://docs.python.org/3.14/library/signal.html), [`unittest`](https://docs.python.org/3.14/library/unittest.html) and POSIX [`pthread_sigmask(3)`](https://man7.org/linux/man-pages/man3/pthread_sigmask.3.html). These sources define candidate semantics; the exact backend CPython patch, compiler, libc, ABI and kernel behavior remain unproven.

### 5.2 Installed product evidence

The accepted C2B1 receipt binds the configured backend tag to image ID/repository digest `sha256:4c8b6fb188d81f5a355008730a1122658af88799ec759029c2dbd297dfc8e257` and proves the selected installed Frappe v16.5.0 and ERPNext v16.4.1 file bytes. It deliberately did not inspect full image configuration, environment, labels, commands, mounts, networking or host configuration. C2BG1 proves the configured user name `frappe`, not a numeric UID/GID.

Anonymous registry authentication for the existing private GHCR repository was denied. No backend config blob, numeric identity, filesystem or Python binary fact was inferred from that denial.

## 6. S2 bootstrap compatibility

### 6.1 Source-derived compatible sequence

The narrowest source-derived S2 sequence is:

1. The runner Dockerfile eventually uses an exec-form Python command so the harness-bearing process is intended to be PID 1.
2. Importing the inert `erp_workspace_ui` package may precede the target module; the target module's first operational import is the standard-library `signal` module.
3. Before `threading`, `ThreadPoolExecutor`, Frappe, Bench or application imports, call `signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGUSR1})` on the main thread.
4. Keep `SIGUSR1` blocked through ordinary disposable-process exit; do not restore it in-process.
5. Verify PID 1, main-thread ownership, an exact allowed thread inventory, blocked mask and no pending `SIGUSR1` before Frappe import.
6. Import pinned Frappe while the signal remains blocked. Verify the mask, pending set and thread inventory again; do not claim its conditional fault-handler registration always ran.
7. Install the separately accepted J2 seam before the pinned runner is constructed.
8. At each release barrier, commit the marker and state first, verify no pending signal, synchronously consume exactly `SIGUSR1` with `sigwait`, then verify the pending set is empty.
9. Preserve the block through final ordinary exit. `SIGKILL` bypasses finalization and makes all partial material discard-only.

POSIX thread mask inheritance makes pre-thread blocking a valid source candidate, but runtime thread inventory and inheritance still require a later controlled canary. The accepted consequence remains explicit: Frappe's `SIGUSR1` diagnostic action is unavailable only inside this disposable runner.

### 6.2 Duplicate and pending-release boundary

Standard `SIGUSR1` is not a queued, nonce-carrying transport. Duplicate signals may coalesce, and `sigwait` cannot identify a manifest nonce. Therefore the controller remains the exclusive sender and must bind exactly one send to a validated marker/full-container-ID/nonce/sequence ledger. A pending signal before release, an unledgered send, controller restart after intent, target mismatch or duplicate ambiguity discards the complete subrun without resend.

### 6.3 Unresolved S2 facts

- exact CPython 3.14 patch, binary hash, build flags, compiler, SOABI, libc and kernel;
- actual `pthread_sigmask`, `sigwait`, pending-set and conditional Frappe `faulthandler` behavior in the final image;
- actual PID 1 command and `Config.Entrypoint`/`Cmd`/`StopSignal`;
- initial and post-Frappe thread inventories;
- exec-path resolution, ownership and modes; and
- ordinary cleanup versus killed-process evidence under the exact final process.

**S2 status:** source-compatible candidate, runtime-unproven; source authoring remains stopped.

## 7. J2 adapter compatibility

### 7.1 Pinned lifecycle

The pinned `frappe.commands.testing.main` signature is:

```text
main(site=None, app=None, module=None, doctype=None, module_def=None,
     verbose=False, tests=(), force=False, profile=False,
     junit_xml_output=None, doctype_list_path=None, failfast=False,
     case=None, skip_before_tests=False, debug=False,
     debug_exceptions=None, selected_categories=None, lightmode=False) -> None
```

The source call sequence is: clear log; create `TestConfig`; initialize the test environment; configure the optional XML output; construct `TestRunner`; perform selected discovery; iterate `runner.iterRun()` and execute each suite; derive success from every returned result; call `sys.exit(1)` on failure; and, inside the ordinary `finally`, clean up the test environment, close any configured XML object and emit timing. Environment initialization occurs before that `try`, so an initializer failure does not receive the same Frappe cleanup.

The configured global XML runner is not the runner that actually executes the suite. J2 must omit the pinned CLI JUnit option and own sanitized JUnit production from the actual result callbacks.

### 7.2 Actual runner, result and adapter seam

`frappe.testing.runner.TestRunner.__init__(stream=None, descriptions=True, verbosity=1, failfast=False, buffer=True, resultclass=None, warnings="module", *, tb_locals=False, cfg: TestConfig)` passes `resultclass or TestResult` to `unittest.TextTestRunner`. The pinned CLI never supplies `resultclass`.

There is no supported result-adapter injection hook on the accepted CLI path. The narrowest four-file-compatible seam is a source-controlled adapter subclass of the pinned Frappe `TestResult`, bound to `frappe.testing.runner.TestResult` after blocked Frappe import and before `commands.testing.main` constructs `TestRunner`.

This preserves pinned discovery, environment setup, actual suite execution, cleanup and exit behavior. It is a private module-global seam, not a supported Frappe API. Directly constructing `TestRunner(resultclass=...)` would reproduce or bypass accepted Frappe orchestration and is rejected.

### 7.3 Required callback and ID surface

The future adapter must preserve and delegate exactly once to the pinned superclass for:

- `startTestRun`, `stopTestRun`, `startTest`, `stopTest` and `stop`/`shouldStop`;
- `addSuccess`, `addError`, `addFailure`, `addSkip`, `addExpectedFailure` and `addUnexpectedSuccess`;
- `addSubTest`; and
- `addDuration` only if the exact installed CPython source supports it.

Canonical top-level IDs come only from the TestLoader-created object's `test.id()`. Subtest IDs come only from `subtest.id()`. The current harness uses subtests in five source locations, so subtest mapping is mandatory. Setup/class/module failures represented by nonordinary holders are generic, nonpromotable failures unless a later exact schema accepts them.

### 7.4 Leakage-safe finalization order

Each callback may append only fixed ID, outcome and count/hash facts to a `.partial` canonical stream. Tracebacks, exception text, SQL, paths, identities, financial values and buffered stdout/stderr are not evidence.

After successful return from the pinned test command and its ordinary cleanup, the bootstrap must reject zero tests, unexpected categories, unexpected IDs, count mismatch or duplicate callbacks; close and hash canonical outcomes; serialize sanitized JUnit to `.partial`; fsync, close and hash it; atomically promote canonical outcomes then JUnit; and only then permit `harness-complete.json`. Failure, `SystemExit(1)`, cleanup error, serialization error, killed process or incomplete file remains discard-only.

**J2 status:** lifecycle and narrow seam identified, but compatibility is stopped until the Owner explicitly accepts the private exact-source seam and later exact CPython/callback evidence closes it.

## 8. K1 backend identity and secret readability

### 8.1 Proven facts

- The backend image ID/repository digest is pinned by the installed-source receipt.
- The configured image user name was observed as `frappe` in C2BG1.
- The selected Frappe/ERPNext source bytes were proved for the accepted file set.
- Docker Compose documentation states that file-backed secret sources are bind mounts and requested `uid`, `gid` and `mode` values are not implemented for those file sources.

### 8.2 Facts not proven

No accepted evidence establishes:

- backend platform manifest/config digest or `Config.User`, `WorkingDir`, entrypoint, command and stop signal;
- effective numeric UID, primary GID, supplementary groups or exact passwd/group rows;
- rootless or user-namespace mappings;
- exact Python, Bench, Frappe, ERPNext and app runtime paths and binary hashes;
- proposed harness/initializer destinations, parent traversal, symlink/hardlink posture, owners or modes;
- PID 1 exec resolution; or
- whether an owner-only host-RAM secret file pre-owned for the container's mapped identity is readable only by the intended service.

Anonymous access to the pinned GHCR manifest/config was denied. These facts require a separately authorized backend registry and image/filesystem read-only fingerprint. Image materialization, layer download and runtime canaries remain separate later gates.

### 8.3 K1 contract preserved

The later controller may create one point-scoped RAM-backed secret directory, with an owner-only parent and one regular, no-follow, size-bounded file per consuming role. Each file must already have the proven host-side ownership after user-namespace translation and owner-read-only mode before Compose mounts it read-only at an exact service-specific `/run/secrets/<approved-name>` destination. Compose ownership remapping, shared role secrets, environment values, argv, logs, evidence hashes of secrets and copied live configuration remain rejected.

**K1 status:** stopped on backend identity, path, ownership and user-namespace proof.

## 9. R1 official MariaDB candidate fingerprint

### 9.1 Registry method

Only public registry authentication, tag/index metadata, the exact Linux/amd64 platform manifest and its referenced config blob were read. No layer blob was requested or downloaded. No Docker or Compose command, pull, build, inspect or materialization occurred.

Registry observations are date-bound to this 2026-07-18 gate, not digest approval. The config `created` values below are image-build metadata, not observation timestamps. Mutable tags may move.

### 9.2 Bounded Ubuntu/Debian candidate set

| Candidate | Observed repository/index digest | Linux/amd64 manifest | Config/image identity | Config facts |
| --- | --- | --- | --- | --- |
| MariaDB 10.11.18 Jammy (`10.11`) | `sha256:be981e4113326ada8d6004174dd09eeaefc03094037f811182a52d4f2e737350` | `sha256:9bd53e60ca32fceda2dce247d4791a1964ed05ceeea73b28e151ff9d5983b3a1` | `sha256:37b9f8bf6fe12f7d493c8aa55e97dd0205367e7b29445166e661a2739fdbae02` | created `2026-07-02T02:30:44.891113353Z`; Linux/amd64; no configured user/workdir/stop signal; entrypoint `docker-entrypoint.sh`; command `mariadbd` |
| MariaDB 11.4.12 Noble (`11.4`) | `sha256:a794d9eb009e20de605858a11f32f63b4075cbd197c650436f0e3b457e4caed7` | `sha256:a6ee0e234c527de59d6a1924703e5512e7a762c74616a443ec9c729b3a9c5154` | `sha256:5eb84d23187c27447ef6ddfec3f0332bbbc12c09fd5818b7d6b5bbef1da35772` | created `2026-07-02T02:30:39.941349958Z`; Linux/amd64; no configured user/workdir/stop signal; entrypoint `docker-entrypoint.sh`; command `mariadbd` |
| MariaDB 10.6.27 Jammy (`10.6`) legacy comparator | `sha256:114d40be36852d0a019afd8458f7e1cc63fd300403b115b1f32e31130d5f671b` | `sha256:b5e45ee3bbf582fb91e4b9447cc3f020fbab2dbcf22970e482df04d6d8ac4e44` | `sha256:27e8ebbe7dde20c1ec66c864629109cfcad003843315929ee25b262bc11fbef3` | Linux/amd64; no configured user/workdir/stop signal; entrypoint `docker-entrypoint.sh`; command `mariadbd` |

The [Docker Official Images](https://github.com/docker-library/official-images) record was fixed at commit `978734a887cff2ee0950939a12654c0072da226c`; `library/mariadb` SHA-256 was `e8c5724215fe4b6844d3cf9707e71311dae078d5a7a5221059fe5262f640a383`. It binds these version directories to [`MariaDB/mariadb-docker`](https://github.com/MariaDB/mariadb-docker) commit `53935c78b82bff912b361357d59db11d7246ea96`.

| Candidate source | Dockerfile SHA-256 | Entrypoint SHA-256 | Healthcheck SHA-256 | Exact server package in Dockerfile |
| --- | --- | --- | --- | --- |
| `10.11/` | `db7977c0be6d44ab63afba5d27b45f3f4d17c781d11f97b4e67fda475471acbd` | `72fd2da1b86f8d0518e4a88b99e70b65bad9b23c3335654a58f30041a55402f3` | `80e2a5dc9e0a50c24842d9f093659a7f2417e9399554d8b13bd294575e15a626` | `1:10.11.18+maria~ubu2204` |
| `11.4/` | `2aba3a3311263f7eb395ce90b11e8ac360c9ed952d4c3a3ec1fa1167f76a7ef0` | `8729e8de7383cede8b99956471ba9840705dd56f30072e0eec2f281371dbd153` | `592f89cb39308f8425693221b0476932918e2f3e451cad39b822e23ea0103ef0` | `1:11.4.12+maria~ubu2404` |
| `10.6/` | `ee123331738bdce1b612664064d79fdb781e0cb8c2dbed4f96922a8c4bb0e3ec` | `329ef75babe2bfa4e1252fe412f6746a3f84a99315dc06973d25ba06228b2d6f` | `80e2a5dc9e0a50c24842d9f093659a7f2417e9399554d8b13bd294575e15a626` | `1:10.6.27+maria~ubu2204` |

### 9.3 Source-derived entrypoint facts

The exact candidate entrypoints and [official MariaDB image environment documentation](https://mariadb.com/docs/server/server-management/automated-mariadb-deployment-and-administration/docker-and-mariadb/mariadb-server-docker-official-image-environment-variables) implement `file_env`/`_mariadb_file_env`, accept MariaDB and compatibility `MYSQL_*` names, require one approved root-password mode for an empty data directory, and process `/docker-entrypoint-initdb.d/*`. The generated-random-root mode emits the generated password and remains rejected. The generic application-user path grants broad authority on the named database and cannot implement D1. An existing initialized data directory causes most initialization variables to be ignored, so credential rotation cannot be inferred from restarting with new secret files.

These source facts do not prove that registry config bytes equal in-image entrypoint bytes, actual server build output, privilege behavior, internal-network behavior or restart behavior. Those require later product materialization and controlled evidence.

### 9.4 Candidate ranking — recommendation, not selection

1. **10.11.18 Jammy:** best next compatibility candidate because it remains in the [MariaDB long-term maintenance window](https://mariadb.org/about/#maintenance-policy) and is a smaller version step from the accepted 10.6 deployment lineage than 11.4.
2. **11.4.12 Noble:** strong longer-horizon candidate under the same maintenance schedule, but it has a larger server/base-OS compatibility distance that requires additional Frappe, transaction, privilege and collation evidence.
3. **10.6.27 Jammy:** retain only as the exact continuity comparator. The maintenance schedule records MariaDB Community maintenance for 10.6 ending on 2026-07-06, so it is not recommended as the new long-lived proof authority.

The UBI variants are excluded from this minimal candidate set because they change base-image and configured-user obligations without evidence that the Ubuntu candidates are unsuitable. They remain unapproved alternatives.

### 9.5 R1 gaps

No candidate is yet bound end-to-end to in-image entrypoint bytes, exact server build output, final Compose/Engine provenance, internal unpublished network, empty/existing-datadir behavior, D1 privileges, collation/Decimal behavior or Frappe compatibility. No digest is approved.

**R1 status:** candidate set and evidence ranking ready; product selection and compatibility remain stopped.

## 10. Compose and Docker Engine facts

Committed receipts do not prove the future Compose semantic/build version, Docker Engine/API build, OCI runtime, cgroup v2, storage driver, rootless/user-namespace posture, fixed-IP allocation, rendered internal-network membership, absence of published ports or exact inspection-field availability.

Authoritative [Compose service-secret documentation](https://docs.docker.com/reference/compose-file/services/#secrets) and [secret usage guidance](https://docs.docker.com/compose/how-tos/use-secrets/) establish only candidate secret semantics: file-backed sources behave as bind mounts and their requested `uid`, `gid` and `mode` are not implemented. The [network specification](https://docs.docker.com/reference/compose-file/networks/) defines `internal: true` and IPAM candidates. Future rendered/runtime evidence is still required.

**Compose/Engine status:** stopped for a separately authorized, fixed-output, read-only host fingerprint. No command was run here.

## 11. P1/W1 product compatibility

### 11.1 Required role ownership

| Role | Required authority | Explicit denial |
| --- | --- | --- |
| Static preparer | Temporary exact synthetic fixture DML before sealing | No measurement, promotion or retained setup authority |
| Credential finalizer | Create/rotate exact disposable principals, write reader-only site configuration, revoke/drop broad setup authority | No accounting adjudication or measured evidence |
| Seal verifier | Exact schema/fixture/account/denial checks after setup credentials are removed | No mutation or topology authority |
| Measured reader | Approved read-only workload and accounting/permission assertions | No root, DML, DDL, grant, topology, process or evidence promotion |
| Topology reader | Version-bound primary/replica posture only | No site-data grants, schema enumeration, process list or mutation |
| S01-S08 writer | One case-specific exact DML allowlist in one isolated semantic stack | No root, broad table union, schema discovery, measured evidence or workload-cap contribution |
| Controller | Full-ID lifecycle, release ledger, receipts, promotion, recovery and teardown | No accounting-value adjudication |

### 11.2 Current harness incompatibility

The unchanged harness reads `SYNTH_DB_ROOT_PASSWORD`; topology mode selects root; topology/reconnect helpers use root and issue connection termination; `setUpClass` seeds fixtures; permission cases mutate; and S01-S08 perform dynamic writes around the reader snapshot. It cannot be treated as the future measured reader without an explicit mode and credential split.

The current dynamic writer also derives schema columns and accepts a broad mutation-table union. That conflicts with D1. Each S case requires source-bound, case-specific columns and a distinct writer credential/evidence target.

### 11.3 Reader/writer release contradiction

The accepted marker-copy plus payload-free `SIGUSR1` transport cannot tell the reader the runtime hash of `snapshot-writer-complete.json`. That writer marker includes runtime-specific commitments. A shared control/evidence mount, environment/argv payload, `docker exec`, broker or fifth source is not authorized.

The four-file-compatible correction boundary is:

- the reader acknowledges only a fixed `released_after_controller_validation` state and precommitted S-case identity;
- the controller validates the writer terminal marker and binds its actual hash, the reader request hash, release intent and reader-observed marker in a controller-owned receipt; and
- no writer hash is transported into the reader.

This is a required later protocol decision, not a complete schema.

### 11.4 Nonterminal cold versus terminal envelope

The successful cold request may prime only the approved read-only workload request. The current full suite cannot be a primer because it seeds and mutates.

Each workload-point envelope retains one complete disposable database, site, Redis namespace, internal network, isolated volumes, controller-owned resource manifest and exact teardown boundary. Each mutating S case retains its own complete isolated semantic stack and separate writer evidence target. A writer cannot mount, read or write measured-reader evidence; the controller validates and copies the two evidence branches independently.

Before an eligible cold workload subrun, the controller owns the accepted fresh-state sequence: remove the prior runner/cgroup, reset and verify the point Redis namespace empty, reset the MariaDB process/buffer state over the unchanged sealed fixture volume using exact later R1 behavior, and bind those reset receipts into the cold manifest. No Redis or MariaDB reset occurs between an accepted cold subrun and its fresh-process/fresh-cgroup warm successor.

After a successful cold subrun, the controller must own a distinct nonterminal acceptance receipt binding the cold harness outcome, marker chain, JUnit/canonical hashes, memory facts, fixture/reset seals and `prime_eligible=true`. It must also state, by later frozen fields, that it is not envelope-terminal and has no promotion or teardown authority. The fresh warm runner binds that receipt; Redis/MariaDB are not reset between accepted cold and warm.

Only one later controller-owned envelope-terminal `point-complete.json`, after every required cold, warm and concurrent successor branch and terminal check, may authorize atomic promotion and deterministic teardown. The exact nonterminal basename and complete schemas remain deliberately unfrozen.

Any failed, killed, incomplete, ambiguous, stale, mismatched or partially finalized branch discards the full envelope. The controller alone owns exact-full-ID recovery and teardown under the approved project/point labels; no branch is repaired, resumed, promoted, reused or reset in place after failure.

**P1/W1 status:** role topology is feasible, but the current harness, writer handoff and nonterminal cold receipt prevent source authoring.

## 12. D1 database compatibility

### 12.1 Current harness source inventory is not a grant list

The unchanged harness declares this 19-table source inventory:

| Table | Declared columns |
| --- | --- |
| `tabCompany` | `name`, `default_currency`, `default_finance_book` |
| `tabCurrency` | `name`, `fraction_units`, `smallest_currency_fraction_value` |
| `tabFinance Book` | `name`, `finance_book_name` |
| `tabFiscal Year` | `name`, `year_start_date`, `year_end_date`, `disabled` |
| `tabFiscal Year Company` | `parent`, `company` |
| `tabAccount` | `name`, `company`, `parent_account`, `is_group`, `root_type`, `lft`, `rgt`, `account_currency`, `disabled` |
| `tabGL Entry` | `name`, `company`, `posting_date`, `account`, `debit`, `credit`, `is_cancelled`, `is_opening`, `finance_book` |
| `tabUser` | `name`, `enabled`, `user_type` |
| `tabHas Role` | `name`, `parent`, `parenttype`, `role` |
| `tabUser Permission` | `name`, `user`, `allow`, `for_value`, `apply_to_all_doctypes`, `applicable_for`, `hide_descendants` |
| `tabDocPerm` | `parent`, `role`, `permlevel`, `read`, `report`, `if_owner`, `mask` |
| `tabCustom DocPerm` | `name`, `parent`, `role`, `permlevel`, `read`, `report`, `if_owner`, `mask` |
| `tabDocField` | `parent`, `fieldname`, `permlevel` |
| `tabCustom Field` | `dt`, `fieldname`, `permlevel` |
| `tabDocShare` | `name`, `user`, `share_doctype`, `share_name`, `read`, `everyone` |
| `tabCustom Role` | `name`, `report`, `ref_doctype` |
| `tabProperty Setter` | `name`, `doc_type`, `field_name`, `property`, `value` |
| `tabSingles` | `doctype`, `field`, `value` |
| `tabAccounting Dimension` | `name`, `document_type`, `fieldname`, `disabled` |

This list is broader than some measured queries and omits other lifecycle/query surfaces. The final reader grant list must come from a post-split, mode-specific static SQL and pinned Frappe bootstrap trace, including every column used in output, filters, joins, grouping and ordering.

### 12.2 Additional current query surfaces

Current connection logic uses repeatable-read and read-only consistent-snapshot statements; `DATABASE()` and selected `@@` variables; `INFORMATION_SCHEMA.INNODB_TRX`; session status such as `Rows_read`; statement timeout; `EXPLAIN`; and optional controlled delay. Current topology/schema logic reads global read-only posture, replica status, table engines and columns. Current reconnect logic reads process-list tuples and issues `KILL CONNECTION` through root.

Pinned Frappe initialization, hooks, cache/scheduler/test setup and cleanup may add queries or writes before and after harness cases. Those exact operations have not been traced under a column-grant account.

### 12.3 D1 candidate behavior and unresolved proof

Current MariaDB documentation identifies `user@host`, table/column grants, `REPLICA MONITOR`, account-scoped process visibility and same-account connection termination as candidates. It does not close the behavior for any proposed immutable R1 source.

Same-user reconnect is account-scoped, not connection-scoped. It can proceed only if one exact reader account is bound to one exact service IP, exactly two expected sessions exist, the full target tuple is validated, zero unrelated same-account sessions exist and raw user/host values are suppressed from evidence. Any ambiguity discards. Normal readers still receive neither `PROCESS` nor `CONNECTION ADMIN`.

The topology account must be separated from schema/seal verification. It receives only `USAGE` plus the exact version-bound replica-monitor privilege and no site-data grants. Schema and grant verification belongs to the read-only seal verifier.

### 12.4 Case-specific writer boundary

The later exact source trace must freeze only these case families:

- S01/S06/S08: exact `tabGL Entry` insert columns; S08 rolls back;
- S02: exact `tabAccount` insert columns;
- S03: exact `tabUser Permission` insert columns;
- S04: `UPDATE(default_finance_book)` plus `SELECT(name)` on `tabCompany`;
- S05: exact inserts on `tabFiscal Year` and `tabFiscal Year Company`; and
- S07: source-bound minimal insert columns for the two poison-canary tables.

No broad DML union, `INFORMATION_SCHEMA` column discovery, database-wide `SELECT`, root, DDL, grant option, `PROCESS`, `CONNECTION ADMIN` or topology privilege is permitted in a measured reader or case writer.

**D1 status:** architecture preserved, but exact version-bound grants, Frappe lifecycle compatibility, transaction visibility, topology privilege, fixed-IP runtime proof and reconnect exclusivity remain stopped.

## 13. Four-file feasibility and ownership locks

| Future path | Sole responsibility | Must not own |
| --- | --- | --- |
| `erp_workspace_ui/tests/test_finance_gl_trial_balance_source_proof.py` | S2 bootstrap, closed J2 adapter, mode-specific preparer/verifier/reader/writer/topology/reconnect behavior, accounting/permission/snapshot adjudication | Container lifecycle, cross-branch promotion, teardown or secret creation |
| `erp_workspace_ui/tests/finance_gl_trial_balance_evidence_controller.py` | Manifest generation, exclusive release ledger, host watchdog, cgroup evidence, controller receipts, cross-branch hash binding, promotion, recovery and teardown | Accounting values, case success invention or fixture semantics |
| `erp_workspace_ui/tests/finance_gl_trial_balance_runner.Dockerfile` | Immutable runner base, exact numeric identity after fingerprint, fixed copies/owners/modes and exec-form entrypoint | Runtime decisions, secret generation or database image derivation |
| `erp_workspace_ui/tests/finance_gl_trial_balance_site_initializer.py` | Disposable site creation, fixture/account/credential transition and exact revocation/drop sequence | Evidence promotion, accounting adjudication or measured-reader execution |

The package remains conditionally four-file feasible only if the harness holds every closed mode, the controller generates schema-frozen Compose/manifests as execution inputs, R1 uses the official database image directly and J2 uses the accepted in-harness seam.

A committed Compose file, external schema/helper, broker, database wrapper Dockerfile, separate reconnect source, JUnit adapter file or other fifth runtime surface stops for a new Owner-approved architecture and allowlist gate.

## 14. Findings by severity

### 14.1 Blocker

| Finding | Concrete evidence | Disposition |
| --- | --- | --- |
| Exact backend identity and filesystem contract are unavailable. | C2B1 deliberately omitted config/runtime fields; C2BG1 proves only user name; anonymous GHCR config access was denied. | Accepted. K1 and runner Dockerfile identity cannot freeze. |
| Exact CPython/runtime signal behavior is unavailable. | Pinned Frappe requires Python 3.14 but no patch/build/ABI/libc/kernel fingerprint exists. | Accepted. S2 remains runtime-unproven. |
| J2 has no supported injection hook on the pinned CLI path. | `commands.testing.main` constructs `TestRunner` without `resultclass`; public constructor seam is unreachable without bypass. | Accepted. Private exact-source seam needs Owner acceptance. |
| Compose/Engine/runtime facts are absent. | No accepted receipt contains exact Compose, Engine/API, OCI, cgroup, storage, userns or rendered network facts. | Accepted. Later fixed-output host gate required. |
| No R1 candidate has complete product-to-runtime binding. | Registry/config and upstream source are known, but in-image bytes, server build, datadir, D1 and host behavior are not. | Accepted. No digest approved. |
| Frappe lifecycle under exact column grants is unproven. | Harness source table map omits Frappe bootstrap/cache/scheduler/cleanup SQL and is not a final grant trace. | Accepted. No database-wide fallback. |
| Current harness violates selected role separation. | Root secret/topology/reconnect, preparation and S-case mutation remain in one source/process design. | Accepted. Mode/credential split is mandatory before authoring can close. |
| P1/W1 release ownership is incomplete. | Payload-free signal cannot carry writer hash; no distinct controller-owned nonterminal cold receipt is frozen. | Accepted. Later protocol decision required. |

### 14.2 High

| Finding | Concrete evidence | Disposition |
| --- | --- | --- |
| Standard signal releases can coalesce and carry no nonce. | Python/POSIX signal semantics. | Accepted. Exclusive controller send ledger and discard-on-ambiguity required. |
| Raw Frappe result material can leak identities, paths, SQL and output. | `TextTestResult` captures formatted errors and buffered streams. | Accepted. Fixed enums/IDs/hashes only; partial failures never promote. |
| Test environment initialization precedes the pinned cleanup `try`. | Pinned `commands/testing.py` call order. | Accepted. Controller teardown owns pre-try failures. |
| Same-account reconnect can target the wrong session. | Current MariaDB behavior is account-scoped; current harness uses root. | Accepted. Exact session exclusivity and full tuple validation required. |
| Compose secret ownership fields cannot enforce K1. | Authoritative Compose secret documentation. | Accepted. Host-side mapped ownership is mandatory. |
| Topology plus schema verification would overgrant the topology account. | Current helper combines replica posture and schema reads. | Accepted. Move schema/grant checks to seal verifier. |
| Dynamic writer authority is broad and schema-discovered. | Current harness mutation-table union and `INFORMATION_SCHEMA.COLUMNS` behavior. | Accepted. Case-specific source-bound DML only. |
| Full-suite cold priming would mutate state. | Current `setUpClass`, permission and S fixtures write. | Accepted. Only approved read-only workload request can prime warm state. |

### 14.3 Medium

- Exact CPython 3.14 callback additions, duration/color behavior and constructor details remain patch-dependent.
- Mutable registry tags may change after the observation; only a later Owner-approved immutable reference may become proof authority.
- MariaDB 11.4 has a larger base-OS/server compatibility distance; 10.6 is out of Community maintenance; 10.11 still requires full Frappe compatibility evidence.

No new accounting-equation defect was found. Synthetic direct DML remains fixture-only and cannot submit, cancel, close, reopen or post an ERPNext document.

## 15. Independent review and Main Control synthesis

### 15.1 Accounting-preservation review

Accepted: existing raw-GL equations, exact A/P/S catalogs, one-company/base-currency/default-book-plus-blank-or-NULL/zero-dimension posture and no-execution boundary remain unchanged. Direct DML is isolated synthetic fixture construction only. No formula, ranking or accounting authority changed.

### 15.2 Security, permission and leakage review

Accepted: stop on backend identity; reject database-wide `SELECT`; split topology from seal verification; replace broad dynamic-writer authority with case-specific grants; suppress raw connection, traceback, path, SQL and identity material; preserve exact service-IP and same-account exclusivity requirements.

### 15.3 Database/runtime review

Accepted: three-candidate Ubuntu/Debian R1 set; no digest approval; exact upstream source binding; later in-image/server/host behavior gate; S2 runtime canary; exact Frappe SQL/grant trace; W1 and writer-handoff corrections.

### 15.4 Release/governance review

Accepted: four-file boundary remains conditional; controller alone owns cross-branch binding, promotion, recovery and teardown; any fifth source or derived database image stops; publication, source authoring, product materialization and execution remain distinct Owner gates.

### 15.5 Rejected and deferred reviewer directions

Rejected: direct `TestRunner` construction; alternate signal/transport; XML runner substitution; broad/shared secrets; UBI expansion without need; database-wide reads; root/PROCESS/CONNECTION ADMIN in measured roles; shared reader/writer evidence mounts; writer hash in env/argv/`docker exec`; full-suite primer; per-cold promotion/teardown; silent fifth file.

Deferred: VM isolation, host page-cache coldness, numeric limits, image materialization, actual signal/JUnit/database canaries, HTTP/CORS, Finance-to-AI, live alignment and accounting execution.

One Main Control synthesis was performed. No open-ended review loop was started.

## 16. Exact future read-only evidence allowlists

These allowlists describe later gates only. None was executed except the public manifest/config and upstream-source reads explicitly recorded in Section 9.

### 16.1 Registry metadata

The exact permitted repositories and references are:

- backend: `ghcr.io/htayaung-data/erpnext-factory` at existing digest `sha256:4c8b6fb188d81f5a355008730a1122658af88799ec759029c2dbd297dfc8e257` only, using an Owner-approved read-only package token;
- MariaDB 10.11 candidate: `registry-1.docker.io/library/mariadb` at `sha256:be981e4113326ada8d6004174dd09eeaefc03094037f811182a52d4f2e737350` and its referenced Linux/amd64 manifest `sha256:9bd53e60ca32fceda2dce247d4791a1964ed05ceeea73b28e151ff9d5983b3a1` only;
- MariaDB 11.4 candidate: the same repository at `sha256:a794d9eb009e20de605858a11f32f63b4075cbd197c650436f0e3b457e4caed7` and Linux/amd64 manifest `sha256:a6ee0e234c527de59d6a1924703e5512e7a762c74616a443ec9c729b3a9c5154` only; and
- MariaDB 10.6 legacy comparator: the same repository at `sha256:114d40be36852d0a019afd8458f7e1cc63fd300403b115b1f32e31130d5f671b` and Linux/amd64 manifest `sha256:b5e45ee3bbf582fb91e4b9447cc3f020fbab2dbcf22970e482df04d6d8ac4e44` only.

Permitted requests for each literal reference:

1. registry authentication token request for one exact repository;
2. `HEAD`/`GET` one tag or approved immutable manifest reference;
3. `GET` the exact Linux/amd64 platform manifest referenced by the index; and
4. `GET` only that manifest's referenced config blob.

Permitted output fields:

- HTTP `Docker-Content-Digest` and content media type;
- schema version;
- platform manifest digest, OS, architecture and variant;
- config digest, created time, OS and architecture; and
- `Config.User`, `WorkingDir`, `Entrypoint`, `Cmd` and `StopSignal`.

The config-blob request is permitted only for the config digest named by the accepted platform manifest. Layer blob requests, history, environment values, labels, secret values, tag enumeration and image pulls remain prohibited.

### 16.2 Upstream and in-image file binding

Permitted upstream files are literal:

- `https://github.com/docker-library/official-images.git` at `978734a887cff2ee0950939a12654c0072da226c`: `library/mariadb`;
- `https://github.com/MariaDB/mariadb-docker.git` at `53935c78b82bff912b361357d59db11d7246ea96`: `10.6/Dockerfile`, `10.6/docker-entrypoint.sh`, `10.6/healthcheck.sh`, `10.11/Dockerfile`, `10.11/docker-entrypoint.sh`, `10.11/healthcheck.sh`, `11.4/Dockerfile`, `11.4/docker-entrypoint.sh` and `11.4/healthcheck.sh`; and
- `https://github.com/frappe/frappe.git` at `4dfcc56090eb3101d18ddb03750391511f163fcf`: `pyproject.toml`, `frappe/__init__.py`, `frappe/_optimizations.py`, `frappe/utils/bench_helper.py`, `frappe/commands/testing.py`, `frappe/testing/__init__.py`, `frappe/testing/config.py`, `frappe/testing/discovery.py`, `frappe/testing/environment.py`, `frappe/testing/result.py` and `frappe/testing/runner.py`.

The exact MariaDB server implementation-file allowlist is not frozen and no server-source content read is preapproved. A separate source-path discovery gate may run only these exact commands and retain only the returned reference SHA pairs:

```text
git ls-remote https://github.com/MariaDB/server.git refs/tags/mariadb-10.6.27 refs/tags/mariadb-10.6.27^{}
git ls-remote https://github.com/MariaDB/server.git refs/tags/mariadb-10.11.18 refs/tags/mariadb-10.11.18^{}
git ls-remote https://github.com/MariaDB/server.git refs/tags/mariadb-11.4.12 refs/tags/mariadb-11.4.12^{}
```

That discovery gate stops after tag/peeled-commit binding. Any MariaDB server file-content allowlist requires a new exact-path Owner decision; broad clone, tree dump, code search and inferred implementation paths are not authorized by this receipt.

Permitted later in-image file paths are literal: `/usr/local/bin/docker-entrypoint.sh`, `/usr/local/bin/healthcheck.sh`, `/etc/os-release`, `/etc/passwd`, `/etc/group`, `/proc/1/exe`, `/home/frappe/frappe-bench/env/bin/python`, `/home/frappe/frappe-bench/env/bin/python3`, `/home/frappe/frappe-bench/env/bin/python3.14`, `/home/frappe/frappe-bench/apps/frappe/frappe/__init__.py`, `/home/frappe/frappe-bench/apps/frappe/frappe/_optimizations.py`, `/home/frappe/frappe-bench/apps/frappe/frappe/utils/bench_helper.py`, `/home/frappe/frappe-bench/apps/frappe/frappe/commands/testing.py`, `/home/frappe/frappe-bench/apps/frappe/frappe/testing/config.py`, `/home/frappe/frappe-bench/apps/frappe/frappe/testing/discovery.py`, `/home/frappe/frappe-bench/apps/frappe/frappe/testing/environment.py`, `/home/frappe/frappe-bench/apps/frappe/frappe/testing/result.py` and `/home/frappe/frappe-bench/apps/frappe/frappe/testing/runner.py`.

The proposed destination traversal check is limited to `/home`, `/home/frappe`, `/home/frappe/frappe-bench`, `/home/frappe/frappe-bench/apps`, `/home/frappe/frappe-bench/apps/erp_workspace_ui`, `/home/frappe/frappe-bench/apps/erp_workspace_ui/erp_workspace_ui`, `/home/frappe/frappe-bench/apps/erp_workspace_ui/erp_workspace_ui/tests` and `/run/secrets`. A missing path is recorded as absent and stops that candidate; it is not discovered by listing siblings. Output is limited to literal path, absent/present, regular-file/symlink/directory type, resolved target for the three Python candidates and `/proc/1/exe`, owner UID/GID, mode, size, link count and SHA-256 for regular files. For `/etc/passwd` and `/etc/group`, retain only the single row resolving the already observed configured user and its primary/supplementary groups. No broad listing, environment, site configuration, secret, log or operational data is permitted.

### 16.3 Backend identity and Python fingerprint

Fixed outputs only:

- PID/PPID, executable path and SHA-256;
- effective UID, primary GID, supplementary GIDs and only the resolving passwd/group rows;
- exact `sys.version`, `version_info`, implementation/cache tag, compiler/build, ABI/SOABI/MULTIARCH/config args and libc/platform/machine;
- availability and numeric identity of `SIGUSR1`, `pthread_sigmask`, `sigwait` and `sigpending`;
- main-thread boolean and exact thread count;
- `readlink -f` plus fixed `stat` fields for every proposed copy destination, parent and `/run/secrets`; and
- rootless/user-namespace mapping fields.

A later controlled compatibility canary may prove pre/post-Frappe mask, pending and thread state plus one ledgered barrier only after a separate execution approval.

### 16.4 Future host product commands — not executed

The smallest initial host command allowlist is:

```text
docker version --format '{{json .Client.Version}}|{{json .Client.APIVersion}}|{{json .Client.GitCommit}}|{{json .Client.GoVersion}}|{{json .Client.Os}}|{{json .Client.Arch}}|{{json .Client.BuildTime}}|{{json .Server.Version}}|{{json .Server.APIVersion}}|{{json .Server.MinAPIVersion}}|{{json .Server.GitCommit}}|{{json .Server.GoVersion}}|{{json .Server.Os}}|{{json .Server.Arch}}|{{json .Server.BuildTime}}|{{json .Server.Experimental}}'
docker compose version --format json
docker info --format '{{json .ServerVersion}}|{{json .Driver}}|{{json .CgroupDriver}}|{{json .CgroupVersion}}|{{json .Runtimes}}|{{json .DefaultRuntime}}|{{json .SecurityOptions}}|{{json .OSType}}|{{json .OperatingSystem}}|{{json .Architecture}}|{{json .KernelVersion}}'
docker info --format '{{range .ClientInfo.Plugins}}{{if eq .Name "compose"}}{{json .Name}}|{{json .Version}}|{{json .Path}}{{end}}{{end}}'
```

The Compose-version JSON parser may retain only its version field and any exact build/commit field actually emitted by that pinned implementation; absence is a stop, not permission to broaden output. The Compose plugin record may retain only name `compose`, version and its absolute binary path. A later checksum command must use that already accepted literal path, and `sha256sum -- <accepted-literal-compose-path>` is the only permitted plugin-binary read. The Docker CLI checksum is limited to the already resolved literal CLI path; no shell-wide path or environment dump is permitted.

After those versions prove the exact template fields, a separately approved second step may use only the following fixed formats against one manifest-listed disposable full ID. `<manifest-bound-full-id>` is replaced by the literal ID already accepted in the execution manifest; it is never a name, tag, prefix or discovery expression.

```text
docker image inspect --format '{{json .Id}}|{{json .RepoDigests}}|{{json .Os}}|{{json .Architecture}}|{{json .Config.User}}|{{json .Config.WorkingDir}}|{{json .Config.Entrypoint}}|{{json .Config.Cmd}}|{{json .Config.StopSignal}}|{{json .RootFS.Type}}|{{json .RootFS.Layers}}' <manifest-bound-image-full-id>
docker inspect --type container --format '{{json .Id}}|{{json .Image}}|{{json .Config.Image}}|{{json .Config.User}}|{{json .Config.WorkingDir}}|{{json .Config.Entrypoint}}|{{json .Config.Cmd}}|{{json .Config.StopSignal}}|{{json .Path}}|{{json .Args}}|{{json .State.Pid}}|{{json .HostConfig.NetworkMode}}|{{json .HostConfig.UsernsMode}}|{{json .HostConfig.ReadonlyRootfs}}|{{json .HostConfig.Privileged}}|{{json .HostConfig.CapAdd}}|{{json .HostConfig.CapDrop}}|{{json .HostConfig.SecurityOpt}}|{{len .HostConfig.PortBindings}}|{{range .Mounts}}{{json .Type}},{{json .Destination}},{{json .Mode}},{{json .RW}},{{json .Propagation}};{{end}}|{{range $name,$network := .NetworkSettings.Networks}}{{json $name}},{{json $network.NetworkID}},{{json $network.IPAddress}},{{json $network.Gateway}},{{json $network.MacAddress}};{{end}}' <manifest-bound-container-full-id>
docker network inspect --format '{{json .Id}}|{{json .Name}}|{{json .Driver}}|{{json .Scope}}|{{json .Internal}}|{{json .IPAM.Driver}}|{{json .IPAM.Config}}|{{range $id,$container := .Containers}}{{json $id}},{{json $container.Name}},{{json $container.IPv4Address}};{{end}}' <manifest-bound-network-full-id>
```

Permitted fields are:

- image/container: `Id`, `Image`, configured image reference, user, working directory, entrypoint, command, stop signal, executable path/args and PID;
- host security: network mode, userns mode, read-only-rootfs, privileged flag, capabilities and security options;
- mounts: type, destination, mode, read/write and propagation, never host source;
- network: ID/name/driver/scope/internal flag, IPAM driver/config, member container full IDs/names and assigned address; and
- ports: exact empty published-port assertion.

Full raw inspect/config, mount source, environment values, labels beyond approved project/point labels, logs and secret metadata are prohibited. Docker/Compose binary path and SHA-256 may be added only after the first version command identifies the installed delivery layout.

### 16.5 D1 source and later controlled denial evidence

Future source trace output must enumerate every mode-specific SQL statement and Frappe bootstrap/cleanup operation, then derive exact table/column/system-object/session privileges. Later controlled evidence, if separately approved, may retain only normalized/hashes of:

- `CURRENT_USER()`, `USER()`, `DATABASE()` and connection identity classifications;
- exact `SHOW GRANTS` allow/deny inventory;
- own-row transaction visibility and read-only/isolation enums;
- zero-row replica posture under the topology-only account;
- exactly two same-account reconnect sessions and one validated target result; and
- synthetic-prefix account inventory with host values hashed.

No accounting row, raw identity, root credential or broad grant output may be retained.

## 17. Proven facts versus unresolved prerequisites

| Area | Proven now | Still required before source authoring reconsideration |
| --- | --- | --- |
| S2 | Exact Frappe import/fault-handler source and source-compatible block-before-import sequence | Exact backend Python/runtime/process/thread/signal proof and Owner acceptance of exclusive-send boundary |
| J2 | Actual Frappe runner/result/lifecycle and narrow private seam | Owner seam decision, exact CPython callbacks, ID/subtest/setup-error mapping and later finalization canary |
| K1 | Backend digest, configured user name and Compose file-secret limitation | Numeric identity, userns, paths, owners, modes, traversal and secret readability |
| R1 | Bounded official registry/config candidates and exact upstream build-source hashes | Candidate/digest Owner choice, in-image byte binding, server/build/datadir and host/runtime behavior |
| P1/W1 | Required role split and one-stack envelope design | Harness mode split, controller writer binding, nonterminal cold receipt and terminal envelope ownership |
| D1 | Candidate account/host/grant/topology/reconnect model and harness SQL inventory | Exact immutable-source semantics, Frappe SQL trace, grants/denials, fixed-IP runtime and session exclusivity |
| Four files | Conditional ownership allocation | Close all blockers without a fifth source/runtime surface |

## 18. Owner decisions required before source-authoring reconsideration

1. Accept or reject the private exact-source J2 seam that binds an adapter to `frappe.testing.runner.TestResult`; rejection keeps authoring stopped unless a separately governed alternative or fifth surface is approved.
2. Accept the canonical parent/subtest ID policy, generic nonpromotable setup-error treatment and sanitized JUnit finalization order.
3. Authorize a later private-backend registry/image/Python read-only fingerprint and, separately, a controlled one-barrier S2 compatibility canary; reaffirm the controller as exclusive signal sender.
4. Select which R1 candidate should receive the next immutable product proof. The recommendation is 10.11.18 first, 11.4.12 second and 10.6.27 only as a legacy comparator. This is not digest approval.
5. Authorize the fixed-output Compose/Engine/OCI/cgroup/storage/user-namespace/network fingerprint before any generated execution manifest is accepted.
6. Accept the controller-owned writer-terminal hash binding while the reader acknowledges only a fixed validated-release state and case commitment.
7. Accept a distinct controller-owned nonterminal cold-subrun receipt and reserve `point-complete.json` for the one envelope-terminal promotion/teardown decision.
8. Accept the D1 split: topology-only account, seal-verifier schema/grant checks, case-specific writers and same-account reconnect only under exact session exclusivity; no database-wide fallback.
9. After those evidence decisions close, explicitly authorize a new Four-File Source-Authoring Gate. Nothing in this receipt grants it.

## 19. Validation and future documentation staging allowlist

Validation for this documentation-only gate requires:

- repository root, branch, local/upstream HEAD and `0/0` parity;
- empty index;
- candidate scope exactly this receipt plus README, in addition to the unchanged harness and four protected exclusions;
- `git diff --check HEAD`;
- Markdown trailing-whitespace and local-reference resolution;
- unchanged harness hash and absent controller/Dockerfile/initializer;
- unchanged protected-exclusion hashes and statuses;
- no selected MariaDB digest, complete executable schema or numeric workload limit; and
- no source or execution authority.

If the Owner later authorizes documentation publication, the exact staging allowlist is only:

1. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/finance-accounting-cycle2-gl-tb-selected-option-product-compatibility-fingerprint-2026-07-18.md`; and
2. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/README.md`.

## 20. Final control statement

**Decision:** `stopped_for_selected_option_fingerprint_gap`

The harness and all four future source candidates remain unchanged. The four protected exclusions remain untouched and unstaged. No source authoring, Docker/Compose command, image pull or layer download, infrastructure, secret, test, Bench, SQL, fixture, benchmark, synthetic execution, HTTP/CORS inspection, live access, staging, commit, push, migration, permission change, protected gate or accounting action occurred.
