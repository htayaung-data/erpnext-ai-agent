# Finance & Accounting Cycle 2 GL / Trial Balance Read-Only Compatibility and Protocol/Schema Freeze Gate

**Date:** 2026-07-18

**Authority:** Main Control v2

**Repository:** `/home/deploy/erp-projects/erpai_project1_erpnext_ui_design`

**Branch:** `feature/erpnext-ui-design`

**Verified baseline:** `43bf3424cfa29e2fde9cd1fbae2805e95cb61d22`

**Decision:** `stopped_for_compatibility_schema_gap`

**Posture:** Read-only product/source compatibility analysis and documentation only. This gate authorizes no source authoring, image action, secret creation, synthetic infrastructure or execution, numeric-limit selection, HTTP/CORS inspection, Finance-to-AI access, runtime/live action, staging, commit, push, migration, permission change, protected gate or accounting execution.

## 1. Purpose and controlling authority

The Owner accepted the Four-File Source-Authoring Gate receipt and its safe-stop decision, then authorized only this GL/TB read-only compatibility and protocol/schema freeze gate. The controlling planning sources are:

1. [GL / Trial Balance Synthetic Evidence Execution Package](finance-accounting-cycle2-gl-tb-synthetic-evidence-execution-package-2026-07-17.md);
2. [GL / Trial Balance Runtime Evidence Design Amendment](finance-accounting-cycle2-gl-tb-runtime-evidence-design-amendment-2026-07-18.md);
3. [GL / Trial Balance Controller-Runner Control Plane and Source Delivery Amendment](finance-accounting-cycle2-gl-tb-controller-runner-control-plane-source-delivery-amendment-2026-07-18.md); and
4. this gate, which is authoritative only for the evidence-backed compatibility findings and the exact partial contracts expressly marked frozen below.

Later accepted documents supersede incompatible older assumptions. No historical implementation phase was re-audited because current repository evidence did not contradict its accepted accounting or workspace-protection closure.

The four future source candidates remain unchanged and unapproved:

1. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/tests/test_finance_gl_trial_balance_source_proof.py`;
2. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/tests/finance_gl_trial_balance_evidence_controller.py`;
3. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/tests/finance_gl_trial_balance_runner.Dockerfile`; and
4. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/tests/finance_gl_trial_balance_site_initializer.py`.

Only the harness exists. Its verified SHA-256 remains `c8d0bb0556f9abb04e1be69c1d67a7f92c4ed37a64d8270d84339ad590e9cea5`; the controller, Dockerfile and initializer remain absent.

## 2. Main Control result

This gate stops because a complete compatibility/protocol/schema contract cannot be frozen from the accepted design and pinned evidence without inventing behavior. The decisive gaps are:

1. Pinned Frappe v16.5.0 registers `SIGUSR1` during `import frappe`, before the selected Bench/Frappe invocation can import the harness or block the signal.
2. The pinned Frappe command accepts a JUnit path, but its selected `frappe.testing.TestRunner` path does not consume the XML runner configured by `_setup_xml_output`; a valid finalized JUnit artifact cannot be claimed.
3. The immutable backend image's configured user and numeric UID/GID were not fingerprinted. Compose file-backed secrets ignore requested `uid`, `gid` and `mode`, so exact non-root secret readability, copy ownership/modes and the Dockerfile `USER` cannot be proven.
4. No immutable MariaDB digest, exact Compose version or Engine version is approved. Password-file behavior and version-sensitive database privileges are therefore unpinned.
5. Controlled priming and fixture-preparation subruns have no accepted mode enum, marker chain, evidence owner or terminal state. A complete marker table and execution-manifest schema cannot be frozen without inventing protocol.

The pinned Frappe initializer API, four-file ownership boundary, schema-validation rules, measured-branch marker rows, inspection-field allowlists and intended database-principal separation are documented below. They create no execution authority.

## 3. Pinned evidence

### 3.1 Repository evidence

| Evidence | Verified value |
| --- | --- |
| Repository | `/home/deploy/erp-projects/erpai_project1_erpnext_ui_design` |
| Branch | `feature/erpnext-ui-design` |
| Local HEAD | `43bf3424cfa29e2fde9cd1fbae2805e95cb61d22` |
| Configured upstream | `origin/feature/erpnext-ui-design` |
| Upstream revision | `43bf3424cfa29e2fde9cd1fbae2805e95cb61d22` |
| Ahead/behind | `0/0` |
| Git index before documentation work | empty |
| Pinned Frappe | v16.5.0, commit `4dfcc56090eb3101d18ddb03750391511f163fcf`, tree `725e06e6319cef5a671884cba1b8b8841f40f99e` |
| Pinned backend image | `ghcr.io/htayaung-data/erpnext-factory@sha256:4c8b6fb188d81f5a355008730a1122658af88799ec759029c2dbd297dfc8e257` |
| MariaDB image | unresolved `<MARIADB_IMAGE>` in the canonical package; committed generic Compose uses mutable `mariadb:10.6` and is not synthetic evidence authority |

The installed-source fingerprint receipts prove selected Frappe source equality but explicitly do not contain sanitized image configuration or `/etc/passwd` and `/etc/group` evidence. The canonical package retains an unresolved MariaDB image placeholder. Neither gap may be filled from convention.

### 3.2 Pinned and authoritative upstream evidence

Frappe sources at commit `4dfcc56090eb3101d18ddb03750391511f163fcf`:

- [`frappe/__init__.py`](https://github.com/frappe/frappe/blob/4dfcc56090eb3101d18ddb03750391511f163fcf/frappe/__init__.py#L1597-L1598) invokes optimization and fault-handler registration during Frappe import.
- [`frappe/_optimizations.py`](https://github.com/frappe/frappe/blob/4dfcc56090eb3101d18ddb03750391511f163fcf/frappe/_optimizations.py#L56-L60) registers `SIGUSR1` through Python `faulthandler`.
- [`frappe/utils/bench_helper.py`](https://github.com/frappe/frappe/blob/4dfcc56090eb3101d18ddb03750391511f163fcf/frappe/utils/bench_helper.py#L12-L15) imports Frappe before dispatch; its main path dispatches Click in-process at lines 74-77.
- [`frappe/commands/testing.py`](https://github.com/frappe/frappe/blob/4dfcc56090eb3101d18ddb03750391511f163fcf/frappe/commands/testing.py#L18-L37) defines the selected test main. Lines 137-177 initialize, construct the runner, run suites and execute cleanup/XML-file close in `finally`.
- [`frappe/commands/testing.py`](https://github.com/frappe/frappe/blob/4dfcc56090eb3101d18ddb03750391511f163fcf/frappe/commands/testing.py#L207-L224) opens the JUnit path and assigns a global XML runner, while the actual suite path invokes `frappe.testing.TestRunner`.
- [`frappe/testing/runner.py`](https://github.com/frappe/frappe/blob/4dfcc56090eb3101d18ddb03750391511f163fcf/frappe/testing/runner.py#L48-L92) defines that runner as a `unittest.TextTestRunner`; the pinned tree contains no consumer that connects the global XML runner to this execution path.
- [`pyproject.toml`](https://github.com/frappe/frappe/blob/4dfcc56090eb3101d18ddb03750391511f163fcf/pyproject.toml#L128-L134) lists `unittest-xml-reporting` only in the test dependency group, not as a frozen installed runtime fact for the derived image.
- [`frappe/installer.py`](https://github.com/frappe/frappe/blob/4dfcc56090eb3101d18ddb03750391511f163fcf/frappe/installer.py#L39-L115) defines the private site initializer and its database/app/commit sequence.
- [`frappe/commands/site.py`](https://github.com/frappe/frappe/blob/4dfcc56090eb3101d18ddb03750391511f163fcf/frappe/commands/site.py) supplies the official `new_site` setup and keyword mapping.
- [`frappe/database/mariadb/setup_db.py`](https://github.com/frappe/frappe/blob/4dfcc56090eb3101d18ddb03750391511f163fcf/frappe/database/mariadb/setup_db.py) creates the site database/user and grants the generated site user all database privileges.

Container and database behavior:

- [Compose secrets](https://docs.docker.com/compose/how-tos/use-secrets/) documents service-specific file exposure under `/run/secrets`.
- [Compose service secret syntax](https://docs.docker.com/reference/compose-file/services/#secrets) documents that `uid`, `gid` and `mode` are not implemented for file-backed secrets because Compose uses bind mounts.
- [MariaDB official-image variables](https://mariadb.com/docs/server/server-management/automated-mariadb-deployment-and-administration/docker-and-mariadb/mariadb-server-docker-official-image-environment-variables) documents the generic `*_FILE` convention and that random-root-password mode prints the generated password.
- [MariaDB replica-status authority](https://mariadb.com/docs/server/reference/sql-statements/administrative-sql-statements/show/show-replica-status), [process visibility](https://mariadb.com/docs/server/reference/sql-statements/administrative-sql-statements/show/show-processlist) and [connection termination](https://mariadb.com/docs/server/reference/sql-statements/administrative-sql-statements/kill) describe version-sensitive privileges that must be bound to the future immutable image.
- [Docker inspection formatting](https://docs.docker.com/reference/cli/docker/inspect/) supports fixed Go templates; unfiltered object/config output remains prohibited.

## 4. Frappe invocation, PID 1, signal, thread, JUnit and finalization

### 4.1 Exact candidate found in pinned source

The direct same-process Frappe command candidate is:

~~~text
/home/frappe/frappe-bench/env/bin/python -I -m frappe.utils.bench_helper frappe --site <EXACT_SYNTHETIC_SITE> run-tests --app erp_workspace_ui --module erp_workspace_ui.tests.test_finance_gl_trial_balance_source_proof --junit-xml-output <EXACT_POINT_STAGING>/junit.xml
~~~

The outer `bench` executable and shell wrappers are rejected because they do not prove that the harness-bearing process is exec-form PID 1. The direct module form can keep dispatch in one Python process, but it is **not frozen for execution**:

| Contract | Pinned behavior | Result |
| --- | --- | --- |
| PID 1 | Direct exec-form Python can be PID 1 and `bench_helper.main()` dispatches in-process. | Candidate only; final entrypoint awaits image path/user and signal-bootstrap decisions. |
| `SIGUSR1` | `bench_helper` imports Frappe; Frappe import registers its fault handler on `SIGUSR1`. | Blocker. The accepted release signal is already owned before harness import. |
| Thread start | Current harness imports `threading`, `ThreadPoolExecutor` and Frappe at module import. The accepted boundary requires blocking the release signal before worker-thread creation. | Blocker. No accepted pre-Frappe bootstrap exists. |
| JUnit | `testing.main` executes `frappe.testing.TestRunner`, while `_setup_xml_output` assigns an otherwise unused XML runner and closes the requested file in `finally`. | Blocker. File creation/close is not proof of XML test records. |
| Finalization | Ordinary failure crosses the pinned `finally`; `SIGKILL` cannot. Harness evidence and controller terminal evidence have separate owners. | Compatible only with discard-only killed/incomplete runs; successful JUnit closure remains unproven. |
| Exit | Frappe exits nonzero when its actual selected runner reports failure. | Known but insufficient to cure signal/JUnit gaps. |

One later Owner amendment must select a bounded signal/bootstrap direction and a JUnit producer. A harness-as-bootstrap could theoretically block a signal before importing Frappe, but explicitly replacing Frappe fault-handler ownership and invoking a different runner would supersede the accepted Bench invocation and is not selected here. No command is approved.

## 5. Exact pinned Frappe initializer API

The pinned private module/function is `frappe.installer._new_site` with this exact signature:

~~~text
_new_site(
    db_name,
    site,
    db_root_username=None,
    db_root_password=None,
    admin_password=None,
    verbose=False,
    install_apps=None,
    source_sql=None,
    force=False,
    db_password=None,
    db_type=None,
    db_socket=None,
    db_host=None,
    db_port=None,
    db_user=None,
    setup_db=True,
    rollback_callback=None,
    mariadb_user_host_login_scope=None,
)
~~~

The source-review call sequence that can be frozen from the pinned source is:

1. set `umask(0o077)` before site or secret handling;
2. read only later-approved fixed secret files using no-follow, regular-file, owner, link-count and bounded-size checks;
3. call `frappe.init(site, new_site=True)`;
4. reject an app-name/site-name collision;
5. create `frappe.utils.scheduler.CallbackManager()`;
6. call `_new_site` with exact database name/user, `db_root_username="root"`, in-memory credentials, `db_type="mariadb"`, `db_host="db-primary"`, `db_port=3306`, `setup_db=True`, `force=False`, `source_sql=None`, `verbose=False`, `install_apps=()`, the callback manager and the later approved MariaDB host scope;
7. apply only separately frozen disposable controls and database-credential rotation;
8. set `allow_tests=1`, `pause_scheduler=1`, `mute_emails=1` and `developer_mode=0` using pinned `update_site_config`;
9. reconnect under the controlled site context and call `install_app("erpnext", verbose=False, set_as_patched=True, force=False)`;
10. call `install_app("erp_workspace_ui", verbose=False, set_as_patched=True, force=False)`;
11. commit and verify the exact installed-app set, site-config owner/mode, scheduler posture and unexpected-file absence; and
12. emit only a generic fixed-schema initializer result, destroy the context and remove the initializer before measured work.

Passing both apps directly to `_new_site(install_apps=...)` is rejected because it leaves no control point between Frappe creation, disposable controls and app installation. Direct CLI passwords, prompts, environment secret values and traceback output remain prohibited.

The API and call order are source-freezeable. Delivery is still blocked by the unresolved user/UID/GID, secret readability, MariaDB digest, host-scope and account-rotation contracts.

## 6. Dockerfile and Compose/MariaDB status

### 6.1 Dockerfile contract

| Field | Evidence-backed status |
| --- | --- |
| `FROM` | Candidate base digest is fixed: `ghcr.io/htayaung-data/erpnext-factory@sha256:4c8b6fb188d81f5a355008730a1122658af88799ec759029c2dbd297dfc8e257`. Materialization remains unapproved. |
| User name and numeric UID/GID | Unresolved; no sanitized image-config or passwd/group fingerprint. Do not infer `frappe` or `1000:1000`. |
| Harness and initializer copy destinations | Unresolved pending exact image filesystem and import-path evidence. No destination is invented. |
| Ownership and modes | Unresolved because numeric ownership and destination traversal/readability are unproven. |
| Exec-form entrypoint | Unresolved because the selected Frappe command conflicts with pinned `SIGUSR1` and JUnit behavior. |
| `RUN`, `ADD`, wildcard copy, package/network action | Remain prohibited. |

An exact Dockerfile cannot be frozen, so source authoring remains stopped.

### 6.2 Compose secrets and MariaDB password files

The following generic behavior is proven but not pinned to the future stack:

- a service may be granted a Compose secret at `/run/secrets/<secret-name>`;
- file-backed secret sources are bind mounts and ignore requested `uid`, `gid` and `mode`;
- the generic MariaDB official-image contract documents `MARIADB_ROOT_PASSWORD_FILE=/run/secrets/<secret-name>`; and
- `MARIADB_ROOT_PASSWORD`, simultaneous `VAR`/`VAR_FILE`, random-root mode, secret values in environment/argv, `.env` and copied live configuration remain prohibited.

Exact secret basenames, host RAM source paths, mounts, service grants and file ownership **are not frozen**. Naming them would invent an unaccepted protocol while numeric user compatibility is unresolved. They must be chosen only after the immutable MariaDB digest, Compose/Engine versions, backend UID/GID and exact point-network membership are fingerprinted.

## 7. Execution-manifest schema freeze status

No complete execution-manifest JSON Schema is published by this stop receipt. Publishing one would falsely resolve missing primer/fixture transitions, secret names, image paths, JUnit ownership and database-principal behavior.

The following schema rules are frozen for the later resolution gate:

- JSON Schema draft 2020-12;
- canonical UTF-8 JSON with final LF, duplicate-key rejection and no substitutions/defaults;
- `additionalProperties: false` recursively, every field explicitly required, and unknown-field rejection;
- booleans rejected where integers are required; finite canonical numbers only;
- dates are canonical `YYYY-MM-DD`; timestamps are UTC seconds with `Z` unless a field explicitly uses monotonic nanoseconds;
- lowercase SHA-256 and exact Git/image identity patterns;
- explicit units in field names or closed `{value, unit}` objects;
- `gate=finance_gl_tb_internal_v1` and `candidate=gl_reconstructed` constants;
- exact A01-A22, P01-P28 and S01-S08 ordered catalogs;
- one company, company base currency, one inclusive period inside one fiscal year, company-default Finance Book plus blank/NULL cohort, zero active dimensions, no account/book filter and no consolidation;
- exact planned resource membership in the manifest, separated from actual Docker full IDs in controller state/receipts;
- exact source hashes for harness, controller, Dockerfile, initializer, Compose, workload plan and image-materialization receipt;
- required later-approved numeric fields with explicit units and no values/defaults in planning documents; and
- no raw secret, secret hash, SQL, exception, identity or financial value in controller/teardown evidence.

### 7.1 Missing fields that prevent a complete schema

| Missing contract | Why it is schema-defining |
| --- | --- |
| Controlled priming subrun mode, predecessor and terminal owner | Determines point/subrun enums, resource membership, markers and promotability. |
| Fixture-preparation subrun mode and handoff | Determines database principal, mutable-to-sealed transition, mutation sentinel and terminal evidence. |
| Signal/bootstrap and JUnit owner | Determines runner command, artifact ownership, success/failure and finalization fields. |
| Exact Dockerfile user, paths and image identity | Determines product/source fields and inspect assertions. |
| Exact secret names/mounts/grants | Determines resource membership and service capability fields. |
| Immutable MariaDB/Compose/Engine versions | Determines topology, transaction and credential fields. |
| Exact database grants/host scopes | Determines per-subrun principal enum and denial assertions. |

The future complete schema must define, at minimum, closed top-level objects for schema/gate/candidate, run identity, source hashes, product provenance, Finance context, fixture catalogs, full resource membership, points/subruns, numeric inputs with units, fixed command/inspection hashes and Owner/reviewer approvals. This inventory is not a schema and does not authorize values.

## 8. Partial marker transition table

The accepted measured/fault branches support the exact rows below. This is deliberately a **partial, non-executable table** because controlled priming and fixture preparation have no accepted rows.

Every listed marker uses the accepted closed key order: `schema`, `event`, `sequence`, `run_id_sha256`, `point_id_sha256`, `subrun_id_sha256`, `mode`, `phase`, `session_nonce_sha256`, `container_hostname_sha256`, `manifest_sha256`, `workload_plan_sha256`, `compose_sha256`, `harness_sha256`, `controller_sha256`, `runner_image_sha256`, `previous_marker_sha256`, `monotonic_ns`. Unknown keys and noncanonical values are rejected. `sequence` and `monotonic_ns` are integers; predecessor is exact SHA-256 or `genesis`.

| Basename | Event | Mode | Phase | Sequence | Predecessor | Release owner/action | Terminal state |
| --- | --- | --- | --- | ---: | --- | --- | --- |
| `measurement-ready.json` | `measurement_ready` | measured cold/warm/concurrent subrun | `measurement_boundary` | 1 | `genesis` | controller captures baseline, records intent, sends exact accepted release | no |
| `measurement-released.json` | `measurement_released` | same measured subrun | `measurement_boundary` | 2 | `measurement-ready.json` hash | harness acknowledgment | no |
| `telemetry-ready.json` | `telemetry_ready` | same measured subrun | `finalization` | 3 | `measurement-released.json` hash | controller seals measured-window cgroup evidence, records intent, sends release | no |
| `normal-exit-released.json` | `normal_exit_released` | same measured subrun | `finalization` | 4 | `telemetry-ready.json` hash | harness acknowledgment then normal exit | runner terminal acknowledgment; controller seal still required |
| `pre-connect-ready.json` | `pre_connect_ready` | `initial_connection_stall` | `pre_connect` | 1 | `genesis` | controller pauses exact DB, verifies pause, records intent, sends release | no |
| `connection-attempt-released.json` | `connection_attempt_released` | `initial_connection_stall` | `connection_attempt` | 2 | `pre-connect-ready.json` hash | harness acknowledgment; controller watchdog owns kill/unpause | discard-only after external kill |
| `request-block-entered.json` | `request_block_entered` | `request_watchdog` | `request` | 1 | `genesis` | no release; controller owns deadline and exact kill | discard-only after external kill |
| `finalization-block-entered.json` | `finalization_block_entered` | `finalization_watchdog` | `finalization` | 1 | `genesis` | no release; controller owns deadline and exact kill | discard-only after external kill |

Missing rows that block completeness:

| Subrun | Missing exact contract |
| --- | --- |
| Controlled warm priming | basename/event/mode/phase, predecessor/genesis rule, evidence carried forward, reset boundary, release owner and terminal result |
| Fixture preparation/sealing | basename/event/mode/phase, mutable credential owner, fixture seal, handoff to read-only runner, mutation-sentinel predecessor and terminal result |

No branch may mix markers. Duplicate, rewritten, stale, missing, reordered, extra or contradictory markers invalidate the subrun. Controller restart after release intent is discard-only and never resumes or resends.

## 9. Evidence-schema freeze status

The accepted ownership split remains:

| Artifact | Sole owner | Must prove | Must not claim | Current blocker to exact schema |
| --- | --- | --- | --- | --- |
| `harness-complete.json` | harness | exact harness-owned artifact hashes/counts, A/P/S catalogs, mutation sentinel, zero identity canaries, harness finalization | JUnit, cgroup, container ID, exit/OOM, promotion, teardown | fixture-preparation/primer transition and future harness basename changes are not frozen |
| `point-complete.json` | controller, written last | harness seal, valid nonempty JUnit, measured-window memory, exact image/container, exit zero, no OOM, allowlist/canaries/links, promotability | accounting adjudication or financial values | JUnit producer and complete subrun/resource schema unresolved |
| `controller-receipt.json` | controller | source/product/command/inspection/resource/point-index hashes and closed result enum | raw IDs, secrets, SQL, figures or free text | complete point/subrun and resource membership unresolved |
| `recovery-state.json` | controller, transient owner-only | exact manifest resource IDs/names, validated action sequence, DB pause state, discard-only outcome | proof promotion or resumed release | complete resource schema/secret sources unresolved |
| `memory-receipt.json` | controller | cgroup-v2 `memory.current`, `memory.peak`, `memory.events.local`, `memory.max`, sample vector, populated state, measured-window bounds, zero OOM delta | through-exit or same-process authority | point/subrun mode and exact kernel event-key fingerprint unresolved |
| `teardown-receipt.json` | controller | exact resource absence, unpaused DB, secret-source/sites-volume absence, unknown/survivor emptiness, retained derived image | broad discovery as cleanup authority | resource/secret membership and exact names unresolved |

All future schemas must use closed ordered keys, fixed enums/hashes/counts, exact units and generic result classes. Killed or incomplete harness artifacts can never be promoted. `junit.xml` remains external to `harness-complete.json` and required by `point-complete.json`; it must contain at least one executed test record. The pinned Frappe path cannot currently produce that evidence.

Because the missing contracts affect fields, nesting, enums, predecessors, resource membership and terminal states, exact schemas for these artifacts are not frozen by this receipt.

## 10. Fixed Docker inspection formats

The following field allowlists are frozen for a future compatible controller. They are planning strings, not command approval. Each parser requires exact positional JSON tokens, exact field counts and no stderr, extra output, control characters or `<no value>`. Exact manifest-bound full IDs or approved-label filters are mandatory.

### 10.1 Runner pre-marker identity and containment

~~~text
{{json .Id}}\t{{json .Image}}\t{{json .State.Status}}\t{{json .State.Running}}\t{{json .State.Paused}}\t{{json .State.Pid}}\t{{json .State.StartedAt}}\t{{json .Config.Hostname}}\t{{json .Config.User}}\t{{json (index .Config.Labels "com.erpai.finance.project")}}\t{{json (index .Config.Labels "com.erpai.finance.service")}}\t{{json (index .Config.Labels "com.erpai.finance.run")}}\t{{json (index .Config.Labels "com.erpai.finance.point")}}\t{{json (index .Config.Labels "com.erpai.finance.subrun")}}\t{{json .HostConfig.Privileged}}\t{{json .HostConfig.NetworkMode}}\t{{json .HostConfig.PidMode}}\t{{json .HostConfig.ReadonlyRootfs}}\t{{json .HostConfig.AutoRemove}}\t{{json .HostConfig.RestartPolicy.Name}}\t{{json .HostConfig.LogConfig.Type}}
~~~

### 10.2 Runner terminal state

~~~text
{{json .Id}}\t{{json .State.Status}}\t{{json .State.Running}}\t{{json .State.Paused}}\t{{json .State.Dead}}\t{{json .State.ExitCode}}\t{{json .State.OOMKilled}}\t{{json .State.StartedAt}}\t{{json .State.FinishedAt}}\t{{json .RestartCount}}
~~~

### 10.3 Database pause state

~~~text
{{json .Id}}\t{{json .Image}}\t{{json .State.Running}}\t{{json .State.Paused}}\t{{json (index .Config.Labels "com.erpai.finance.project")}}\t{{json (index .Config.Labels "com.erpai.finance.service")}}\t{{json (index .Config.Labels "com.erpai.finance.run")}}\t{{json (index .Config.Labels "com.erpai.finance.point")}}
~~~

### 10.4 Mount verification

~~~text
{{range .Mounts}}{{json .Type}}\t{{json .Source}}\t{{json .Destination}}\t{{json .RW}}\t{{json .Propagation}}{{println}}{{end}}
~~~

`Source` is compared transiently against the exact manifest and never retained raw. Only its commitment may enter evidence.

### 10.5 Image identity/configuration

~~~text
{{json .Id}}\t{{json .RepoDigests}}\t{{json .Config.User}}\t{{json .Config.Entrypoint}}\t{{json .Config.Cmd}}\t{{json .Config.WorkingDir}}\t{{json .Config.StopSignal}}\t{{json (index .Config.Labels "com.erpai.finance.source")}}\t{{json (index .Config.Labels "com.erpai.finance.dockerfile")}}
~~~

`.Config.Env`, `.Path`, `.Args`, `.LogPath`, whole `.Config`/`.HostConfig`, network addresses, graph-driver data, commands and secret values are prohibited.

### 10.6 Exact resource discovery fields

~~~text
docker container ls --all --no-trunc --filter label=com.erpai.finance.run=<RUN_COMMITMENT> --format '{{json .ID}}\t{{json .Names}}\t{{json .Image}}\t{{json .Status}}'
docker network ls --no-trunc --filter label=com.erpai.finance.run=<RUN_COMMITMENT> --format '{{json .ID}}\t{{json .Name}}\t{{json .Driver}}\t{{json .Scope}}'
docker volume ls --filter label=com.erpai.finance.run=<RUN_COMMITMENT> --format '{{json .Name}}\t{{json .Driver}}'
~~~

Discovery never grants removal authority. Every result must match complete frozen membership and exact labels before an exact-ID/name action.

## 11. Least-privilege database contract status

The role separation is accepted; exact grants, host scopes and secret delivery remain blocked pending immutable MariaDB evidence.

| Principal | Intended future scope | Forbidden authority | Current blocker |
| --- | --- | --- | --- |
| transient site owner | Initializer/fixture setup only; Frappe-generated full rights during creation, then exact revoke/drop after reader rotation | Never reaches measured runner | Rotation/revocation sequence, account name, host scope and secret channel unproven |
| normal GL/TB reader | Exact read access only to harness-enumerated source tables/columns; primary snapshot checks under its own connection; sole credential in disposable `site_config.json` after rotation | No global privilege, mutation, DDL, `EXECUTE`, `FILE`, `PROCESS`, `REPLICA MONITOR`, `CONNECTION ADMIN` or grant option | Column/table grants, Frappe read behavior and `INFORMATION_SCHEMA.INNODB_TRX` own-row visibility require pinned proof |
| topology reader | Topology-only subrun, no default database/data grants; candidate `USAGE` plus version-pinned `REPLICA MONITOR` | No accounting rows, `PROCESS`, kill or write authority | MariaDB digest/version and exact replica-status behavior unpinned |
| reconnect fixture | Prefer two connections under the same disposable normal-reader account so one may observe/kill only its own thread; no separate elevated credential | No root, `PROCESS` or `CONNECTION ADMIN` unless a later proof demonstrates no safe same-user path | Own-thread visibility/kill and transaction behavior require selected MariaDB source proof |
| root | `db-primary` bootstrap and initializer only | Never reaches fixture, normal, topology or reconnect runner | Current harness still reads `SYNTH_DB_ROOT_PASSWORD` and selects root for topology/reconnect paths |

The later gate must freeze exact account names, host scopes, grants, create/rotate/revoke/drop order and service-specific secret delivery. `%` host scope is not approved. A broader scope would require a separate Owner risk acceptance tied to one internal unpublished network with exact membership.

## 12. Accounting and protection preservation

This gate does not change:

- `gl_reconstructed` as the sole internal synthetic candidate;
- one company, company base currency, one inclusive period inside one fiscal year, company-default Finance Book plus blank/NULL entries, zero dimensions, no consolidation and no account/book filter;
- raw-GL opening, movement, closing, hierarchy, exact balancing, fiscal-boundary, cancellation-canary and Finance Book equations;
- exact A01-A22 accounting, P01-P28 permission and S01-S08 snapshot catalogs;
- complete-chart authority, Accounts Manager positive authority, company scope, User Permission, dimension, Custom DocPerm, share, mask and custom-report-role denials;
- aggregate-only, identity-suppressed, generic fail-closed output and no-execution boundary;
- Sales, Procurement, Warehouse, Finance Cycle 1, Shared UI, routing, registries, governance and AI Assistant protection boundaries; or
- deferred HTTP/CORS, Finance-to-AI access, cancellation, close/reopen, posting, report, export, notification, mutation and accounting execution.

The controller, Dockerfile and initializer remain outside the accounting data plane. They may not implement, duplicate or reinterpret accounting or permission semantics.

## 13. Bounded review and Main Control synthesis

One bounded accounting-preservation, security/leakage, database/runtime and release-containment review was performed, followed by this one Main Control synthesis. No open-ended review loop was started.

### Blocker

| Finding | Concrete evidence | Disposition |
| --- | --- | --- |
| Accepted `SIGUSR1` transport conflicts with pinned Frappe import behavior. | Pinned `frappe/__init__.py`, `_optimizations.py`, `bench_helper.py`; current harness imports Frappe after ordinary imports. | Accepted. Source authoring remains stopped pending Owner-approved signal/bootstrap amendment. |
| Selected Frappe test path cannot prove JUnit records. | Pinned `testing.py` configures a global XML runner but executes `frappe.testing.TestRunner`; pinned runner inherits `TextTestRunner`; no consumer connects them. | Accepted. Exact JUnit producer/finalizer required. |
| Exact non-root Dockerfile and secret ownership cannot be frozen. | Backend user/UID/GID absent from receipts; Compose file-secret `uid`/`gid`/`mode` are ignored. | Accepted. Require sanitized image-user/filesystem fingerprint or Owner-approved secret redesign. |
| MariaDB/Compose behavior is not immutable. | Canonical `<MARIADB_IMAGE>` unresolved; committed mutable `mariadb:10.6` is not evidence authority; exact Compose/Engine versions absent. | Accepted. Require immutable product/source fingerprints. |
| Complete protocol/schema cannot be frozen. | Controlled primer and fixture-preparation subruns lack accepted mode/marker/owner/terminal semantics. | Accepted. No complete schema is published. |

### High

| Finding | Concrete evidence | Disposition |
| --- | --- | --- |
| Current harness exposes root credential to topology/reconnect logic through environment. | `SyntheticEnvironment.load` reads `SYNTH_DB_ROOT_PASSWORD`; `StrictMariaDBConnection(topology=True)` selects root. | Accepted. Harness remains unchanged; later design should prove scoped topology plus same-user reconnect. |
| Frappe-generated site user receives all database privileges. | Pinned MariaDB setup source creates the site account and grants all database privileges. | Accepted. It cannot be the measured reader without exact rotation. |
| Normal transaction proof may require unacceptable process visibility. | Harness checks `INFORMATION_SCHEMA.INNODB_TRX`; own-row visibility is not pinned. | Accepted. No `PROCESS` grant to normal runner. |
| MariaDB account host scope/network membership unproven. | Separate containers require remote account access; `%` would broaden all network members. | Accepted. Exact host/network proof required. |

### Medium

- Secret mount metadata is observable; retained evidence may contain only approved names/path commitments, never values or secret hashes.
- Current harness evidence basenames predate `harness-complete.json` and the controller-owned point seal; any later change requires exact review.
- `expected-actual-diff.jsonl` contains synthetic aggregate expectations/actuals; controller evidence may bind only its hash.
- Full-lifetime memory through process exit remains deferred; the accepted authority is measured-window cgroup evidence.

### Reviewer disposition

| Review | Result |
| --- | --- |
| Accounting preservation | Accepted with Section 12 conditions. No new accounting Blocker/High. |
| Security, permissions and leakage | Stop supported on secret ownership, immutable MariaDB, root exposure, account rotation, transaction visibility and host scope. |
| Database/runtime | Stop supported on Frappe `SIGUSR1`, pre-thread bootstrap, JUnit and incomplete subrun protocol. |
| Release containment | Stop supported because Dockerfile identity/paths/modes/entrypoint and complete artifact/resource schemas cannot be exact. Fixed inspect-field allowlists are acceptable planning constraints. |

## 14. Unresolved prerequisites and next bounded gate

Before source authoring can reopen, the Owner must separately approve a bounded resolution package supplying:

1. a signal/bootstrap decision resolving Frappe's pinned `SIGUSR1` ownership;
2. a JUnit producer/finalizer tied to the actual runner;
3. exact controlled-primer and fixture-preparation marker/owner/terminal semantics;
4. a sanitized read-only fingerprint for backend `Config.User`, numeric UID/GID, passwd/group mapping, Python/Frappe paths and proposed copy destinations;
5. one immutable MariaDB repository digest/image ID and pinned entrypoint `*_FILE` behavior;
6. exact Compose and Engine versions;
7. an exact owner-only secret-source readability mechanism plus basenames/mounts/service grants;
8. exact point-network membership and MariaDB account host scopes;
9. exact create/grant/rotate/revoke/drop sequence for transient site owner, normal reader, topology reader and reconnect fixture;
10. pinned transaction/topology/reconnect behavior without root or excess normal-reader privileges; and
11. one complete JSON Schema/marker/evidence artifact review after the preceding facts close.

No numeric limits are selected. Host page-cache coldness remains unproven, VM isolation remains deferred, killed/incomplete artifacts remain discard-only, and synthetic execution remains unapproved.

## 15. Validation and future documentation allowlist

Required validation for this documentation-only gate:

- repository, branch, local HEAD, configured upstream and `0/0`;
- empty index;
- candidate scope exactly this document and README plus the pre-existing untracked harness and four protected exclusions;
- `git diff --check HEAD`;
- Markdown trailing-whitespace and local-reference resolution;
- exact decision token;
- no numeric workload/runtime value selected;
- harness SHA-256 unchanged and controller/Dockerfile/initializer absent;
- protected exclusion status and SHA-256 unchanged; and
- no source edit, test, Docker/Compose command, image action, secret, infrastructure, SQL, HTTP/CORS inspection, live access, staging, commit, push, migration, permission change, protected gate or accounting action.

If the Owner later authorizes documentation staging, the exact allowlist is only:

1. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/finance-accounting-cycle2-gl-tb-read-only-compatibility-protocol-schema-freeze-gate-2026-07-18.md`; and
2. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/README.md`.

## 16. Main Control decision

**Decision:** `stopped_for_compatibility_schema_gap`

The pinned initializer API and partial read-only contracts are documented. The executable invocation, Dockerfile identity/entrypoint, Compose secret ownership, immutable MariaDB behavior, complete database-privilege contract, primer/fixture transitions and complete JSON schemas cannot be frozen without inventing behavior. The Four-File Source-Authoring Gate remains stopped. No code or execution authority is created by this document.
