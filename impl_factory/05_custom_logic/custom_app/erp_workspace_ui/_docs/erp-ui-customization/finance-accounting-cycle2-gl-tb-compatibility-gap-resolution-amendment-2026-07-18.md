# Finance & Accounting Cycle 2 GL / Trial Balance Compatibility Gap Resolution Amendment

Date: 2026-07-18
Authority: Main Control v2
Document class: canonical planning-only Owner decision package
Repository: `/home/deploy/erp-projects/erpai_project1_erpnext_ui_design`
Branch: `feature/erpnext-ui-design`
Starting source and upstream: `3456d04e1b34ba24d73beb9f1550874d91287c96`
Controlling stop: `stopped_for_compatibility_schema_gap`
Four-File Source-Authoring Gate: stopped
Original planning result: `compatibility_gap_resolution_options_ready_for_owner_decision`
Owner selection status: accepted for the next read-only evidence-planning gate only

## 1. Purpose and authority

This amendment presents bounded, evidence-backed choices for the six gaps that stopped the GL/TB Read-Only Compatibility and Protocol/Schema Freeze Gate and now records the Owner's planning selections. Those selections do not establish compatibility, reopen source authoring, publish an executable schema, create execution authority or claim that any candidate works.

The controlling order is:

1. the accepted synthetic evidence execution package;
2. the later accepted runtime evidence design amendment;
3. the later accepted controller-runner control-plane amendment;
4. the published compatibility/protocol/schema stop receipt; and
5. this planning-only options amendment after explicit Owner acceptance.

Later accepted documents supersede incompatible earlier assumptions. The Owner has chosen the bounded planning directions recorded in Section 12, but the published decision remains `stopped_for_compatibility_schema_gap` until later evidence closes every prerequisite. The Four-File Source-Authoring Gate remains stopped.

## 2. Verified planning baseline

| Item | Verified planning value |
| --- | --- |
| Repository | `/home/deploy/erp-projects/erpai_project1_erpnext_ui_design` |
| Branch | `feature/erpnext-ui-design` |
| Local HEAD at start | `3456d04e1b34ba24d73beb9f1550874d91287c96` |
| Configured upstream | `origin/feature/erpnext-ui-design` |
| Upstream revision at start | `3456d04e1b34ba24d73beb9f1550874d91287c96` |
| Ahead/behind at start | `0/0` |
| Index at start | empty |
| Compatibility receipt SHA-256 | `85bdd8781892fd738395e9c438bac95a91e0a1da3f3469d9dc8e11ce83714f9e` |
| README SHA-256 at start | `606cee7e697453ae3da0a381997cd025f5cbc94c1137cd7adfd82f35c2ea687a` |
| Unchanged harness SHA-256 | `c8d0bb0556f9abb04e1be69c1d67a7f92c4ed37a64d8270d84339ad590e9cea5` |
| Future controller | absent |
| Future runner Dockerfile | absent |
| Future initializer | absent |

The pinned product facts remain Frappe v16.5.0 at commit `4dfcc56090eb3101d18ddb03750391511f163fcf` and the backend base image digest already recorded in the compatibility receipt. No MariaDB image digest, Compose version or Engine version is selected by this amendment.

## 3. Preserved accounting and workspace boundaries

Every option in this document must preserve, without reinterpretation:

- `gl_reconstructed` as the sole internal synthetic candidate;
- the accepted raw-GL opening, movement, closing, hierarchy, exact-balance, fiscal-boundary, cancellation-canary and Finance Book equations;
- exact A01-A22 accounting, P01-P28 permission and S01-S08 snapshot catalogs;
- one company, company base currency, one inclusive period inside one fiscal year, company-default Finance Book plus blank/NULL cohort, zero active dimensions, no consolidation and no account/book filter;
- complete-chart authority, aggregate-only identity-suppressed output and generic fail-closed behavior;
- normal measured runners with no root, mutation, DDL, grant, `PROCESS` or `CONNECTION ADMIN` authority;
- no HTTP endpoint, CORS inspection, native-report passthrough, ACB/cache mode, silent fallback or Finance-to-AI access;
- no cancellation, close/reopen, frozen-period-control, posting, payment, mutation or accounting-execution claim;
- Sales, Procurement, Warehouse, Finance Cycle 1, Shared UI, routing, registries, governance and AI Assistant protection boundaries; and
- source/live separation and exact allowlists for every later external-state gate.

Host page-cache coldness remains unproven. VM-level isolation and all numeric workload limits remain deferred. Killed, incomplete, ambiguous or partially finalized runs remain discard-only.

## 4. Evidence basis and interpretation rules

### 4.1 Pinned Frappe evidence

The following pinned sources are authoritative for the current incompatibility:

- [`frappe/__init__.py`](https://github.com/frappe/frappe/blob/4dfcc56090eb3101d18ddb03750391511f163fcf/frappe/__init__.py#L1597-L1598) performs fault-handler registration during Frappe import.
- [`frappe/_optimizations.py`](https://github.com/frappe/frappe/blob/4dfcc56090eb3101d18ddb03750391511f163fcf/frappe/_optimizations.py#L56-L60) registers `SIGUSR1` through `faulthandler`.
- [`frappe/utils/bench_helper.py`](https://github.com/frappe/frappe/blob/4dfcc56090eb3101d18ddb03750391511f163fcf/frappe/utils/bench_helper.py#L12-L15) imports Frappe before command dispatch and dispatches in-process.
- [`frappe/commands/testing.py`](https://github.com/frappe/frappe/blob/4dfcc56090eb3101d18ddb03750391511f163fcf/frappe/commands/testing.py#L137-L177) initializes, runs and finalizes the selected suite path.
- [`frappe/commands/testing.py`](https://github.com/frappe/frappe/blob/4dfcc56090eb3101d18ddb03750391511f163fcf/frappe/commands/testing.py#L207-L224) opens the requested XML file and assigns a global XML runner.
- [`frappe/testing/runner.py`](https://github.com/frappe/frappe/blob/4dfcc56090eb3101d18ddb03750391511f163fcf/frappe/testing/runner.py#L48-L92) defines the runner actually used by that path as `unittest.TextTestRunner`.
- [`frappe/installer.py`](https://github.com/frappe/frappe/blob/4dfcc56090eb3101d18ddb03750391511f163fcf/frappe/installer.py#L39-L115) and [`frappe/commands/site.py`](https://github.com/frappe/frappe/blob/4dfcc56090eb3101d18ddb03750391511f163fcf/frappe/commands/site.py) freeze the current initializer candidate and call mapping.
- [`frappe/database/mariadb/setup_db.py`](https://github.com/frappe/frappe/blob/4dfcc56090eb3101d18ddb03750391511f163fcf/frappe/database/mariadb/setup_db.py) shows that Frappe's generated site user receives broad database authority during site creation.

### 4.2 Authoritative platform evidence

- [Python signal handling](https://docs.python.org/3/library/signal.html) establishes main-thread handler rules and the available mask/wait primitives; it does not prove that an arbitrary signal is unused in this image.
- [Compose service secrets](https://docs.docker.com/reference/compose-file/services/#secrets) establishes that file-backed secret sources are bind mounts and their requested `uid`, `gid` and `mode` are not implemented.
- [Docker Compose secrets](https://docs.docker.com/compose/how-tos/use-secrets/) establishes service-specific `/run/secrets` exposure and the generic `*_FILE` convention; it does not pin a future MariaDB image.
- [Docker inspect formatting](https://docs.docker.com/reference/cli/docker/inspect/) supports fixed field templates; full raw object/config capture remains prohibited.
- [MariaDB CREATE USER](https://mariadb.com/docs/server/reference/sql-statements/account-management-sql-statements/create-user) defines `user@host`, wildcard and exact-host matching concepts.
- [MariaDB SHOW REPLICA STATUS](https://mariadb.com/docs/server/reference/sql-statements/administrative-sql-statements/show/show-replica-status), [SHOW PROCESSLIST](https://mariadb.com/docs/server/reference/sql-statements/administrative-sql-statements/show/show-processlist) and [KILL](https://mariadb.com/docs/server/reference/sql-statements/administrative-sql-statements/kill) document current privilege behavior.
- [MariaDB START TRANSACTION](https://mariadb.com/docs/server/reference/sql-statements/transactions/start-transaction) documents `READ ONLY` and `WITH CONSISTENT SNAPSHOT` semantics.

Generic current documentation is candidate-design evidence only. Version-sensitive behavior must later bind to one immutable MariaDB image, exact upstream entrypoint source, exact Docker Engine and exact Compose implementation before it becomes proof authority.

### 4.3 New repository contradiction that every option must resolve

Read-only inspection of the unchanged harness shows that the current process is not merely a reader:

- `SyntheticEnvironment.load` reads `SYNTH_DB_ROOT_PASSWORD`, and `StrictMariaDBConnection(topology=True)` selects root;
- topology and reconnect helpers use root, inspect process state and issue `KILL CONNECTION`;
- `setUpClass` creates a mutation connection and seeds fixtures;
- permission cases commit synthetic mutations; and
- S01-S08 perform committed or rolled-back writes while a snapshot reader remains active.

Consequently, static pre-seeding followed by one read-only process cannot preserve all accepted fixtures. A viable future design must separate at least static preparation, measured reading, topology observation and dynamic snapshot writing. No measured runner may retain a privileged secret, connection or callable mutation authority.

## 5. Gap 1 — signal and bootstrap ownership

### 5.1 Common non-negotiable contract

Whichever option the Owner later selects must prove all of the following before source authoring:

- the harness-bearing process is exec-form PID 1, or an explicitly approved minimal init owns PID 1 and the exact signal-forwarding/reaping contract is frozen;
- the control mechanism is established before any worker thread can receive or act on it;
- Frappe's diagnostic signal ownership is preserved or deliberately superseded with exact restoration and failure semantics;
- the controller revalidates exact full container ID, approved labels, point/subrun identity and expected marker immediately before every release;
- each release is single-use, nonce-bound and sequence-bound;
- controller restart, duplicate delivery, stale marker, pending signal ambiguity or target mismatch discards the subrun without resume; and
- the transport cannot choose test cases, alter accounting inputs or decide accounting success.

### 5.2 Option S1 — another signal, only after pinned unused-signal proof

| Assessment | Planning result |
| --- | --- |
| Authoritative evidence | Requires the exact Python/platform valid-signal set, pinned Frappe/Bench/all-installed-Python-source scan, base-image entrypoint and `Config.StopSignal`, Compose `stop_signal`, pre-import and post-import handler/mask fingerprints, and a controlled thread-start canary. Absence of a text match is insufficient. |
| PID 1/topology | Direct exec-form Python remains PID 1. A tiny source-controlled pre-import bootstrap blocks the selected signal, then imports and invokes the pinned Frappe test path in the same process. |
| Import/thread order | Bootstrap imports only the Python standard-library modules needed to block and synchronously wait; it blocks before Frappe, harness, logging, executor or application imports and proves no thread exists beyond the main thread. |
| Ownership/restoration | Frappe retains `SIGUSR1`. The selected control signal remains blocked and synchronously consumed for the process lifetime; pending-signal count and final drain policy must be exact. No arbitrary handler replacement is allowed. |
| Controller compatibility | Existing full-ID validation, marker copy-out, intent receipt and one-shot release model can remain, with the signal constant and fingerprints changed. |
| Failure/recovery | Invalid handler/mask/thread state stops before the first ready marker. Duplicate/pending release, controller restart or wrong target discards the subrun. Recovery never resends. |
| Accounting effect | Neutral if releases cannot select fixtures and incomplete runs remain discard-only. |
| Permission/leakage risk | Lowest of the signal choices if the signal is truly unused; no additional writable IPC surface. Handler/mask evidence must contain only enums/hashes. |
| Runtime determinism | High only after image-bound proof; otherwise unproven. Signal delivery is still asynchronous at the kernel boundary but synchronous consumption must be deterministic. |
| Source impact | Future harness/bootstrap and controller constants; possibly runner Dockerfile entrypoint. Initializer unchanged. |
| Resource/secret impact | No new service or secret. |
| Cost/reversibility | Moderate evidence cost; small source delta and readily reversible to the prior constant. |
| Residual risk | An imported native extension or runtime component may claim the signal without a source-name trace; runtime fingerprints remain mandatory. |
| Exact Owner decision | Choose `signal_option_s1_conditional` and authorize a separate read-only unused-signal fingerprint gate; do not name the signal until that gate returns exact evidence. |

### 5.3 Option S2 — harness-as-bootstrap while retaining the accepted signal name

| Assessment | Planning result |
| --- | --- |
| Authoritative evidence | Requires pinned Python `pthread_sigmask`/`sigwait` semantics, Frappe `faulthandler` registration source, exact pre/post-import handler and mask behavior, pending-signal behavior and installed thread-start inventory. |
| PID 1/topology | The source-controlled harness/bootstrap is exec-form PID 1 and owns suite construction and process exit. No shell or outer Bench wrapper is allowed. |
| Import/thread order | The bootstrap's first operational action blocks `SIGUSR1` before importing Frappe. It proves main-thread-only state, imports Frappe while the signal remains blocked, then reconciles Frappe's registration before any executor starts. |
| Ownership/restoration | Owner-selected policy: keep `SIGUSR1` blocked and synchronously consumed through disposable-process exit. Frappe's diagnostic action is unavailable only inside this runner; in-process restoration is not selected. Pending-signal ambiguity must cause discard. |
| Controller compatibility | Retains the accepted signal and marker-release interface, but changes the invocation owner from `bench_helper` to the bootstrap and therefore supersedes the prior invocation candidate. |
| Failure/recovery | Any bootstrap exception, unexpected handler, thread or pending-signal ambiguity stops before promotion. The process does not attempt restoration; `SIGKILL` remains discard-only. |
| Accounting effect | Neutral only if bootstrap executes the exact canonical suite once and cannot filter or retry cases. |
| Permission/leakage risk | No new IPC mount, but the bootstrap gains process-lifecycle authority and could suppress diagnostics if incorrectly designed. Generic errors and sealed hashes only. |
| Runtime determinism | Potentially high, but pre-import masking, synchronous consumption, pending-signal handling and thread behavior still require exact evidence. No restoration behavior is claimed. |
| Source impact | Largest harness/bootstrap change; controller command; Dockerfile exec-form entrypoint. Initializer unchanged. |
| Resource/secret impact | No new service or secret. |
| Cost/reversibility | High source and review cost; reversible by removing bootstrap only after another invocation is approved. |
| Residual risk | Divergence from Frappe's supported Bench path, diagnostic-signal loss and subtle pending-signal behavior. |
| Exact Owner decision | The Owner selected `signal_option_s2_bootstrap` for the next read-only evidence-planning gate. That gate must prove the blocked-through-exit policy; it is not source authoring. |

### 5.4 Option S3 — dedicated authenticated local control transport

| Assessment | Planning result |
| --- | --- |
| Authoritative evidence | Requires exact transport semantics from the selected runtime, filesystem/socket ownership, atomicity, blocking/wakeup, nonce/replay, mount and teardown behavior. Docker socket, Redis, SQL, HTTP, `docker exec` and broad shared mounts remain prohibited. |
| PID 1/topology | Direct pinned Frappe process may remain PID 1. A narrowly scoped local control primitive is opened before worker threads, or a reviewed bootstrap owns only the primitive then execs the runner. |
| Import/thread order | Transport endpoint and permissions must exist before import/thread start; no listener thread is allowed unless separately frozen and shown not to alter accounting execution. |
| Ownership/restoration | Frappe retains all signals. Controller owns the write end; one runner owns the read end. Exact close/unlink behavior replaces signal restoration. |
| Controller compatibility | Requires new controller transport logic, nonce protocol and exact resource membership. Marker intent/full-ID checks remain. |
| Failure/recovery | EOF, replay, extra writer, stale nonce, partial frame or controller restart discards. Recovery removes only exact-ID project resources and the exact point endpoint. |
| Accounting effect | Neutral only if releases remain sequencing-only. |
| Permission/leakage risk | Highest: adds a writable control surface. The endpoint must carry only fixed release tokens, never financial data or commands. |
| Runtime determinism | Can be high with a blocking framed protocol, but adds kernel/filesystem/runtime dependencies. |
| Source impact | Controller, harness/bootstrap, Dockerfile and Compose resource definitions. Initializer normally unchanged. |
| Resource/secret impact | Adds a point-scoped endpoint or private tmpfs object; no credential or reusable token may persist. |
| Cost/reversibility | Highest design, schema, containment and teardown cost; reversible after endpoint removal and manifest contraction. |
| Residual risk | Replay, unauthorized writer, stale endpoint, mount leakage and recovery ambiguity. |
| Exact Owner decision | Choose `signal_option_s3_transport` only after separate evidence shows both S1 and S2 unsuitable, then authorize a transport-design amendment before any source gate. |

### 5.5 Signal recommendation ranking — recommendation only

1. S2 with `SIGUSR1` blocked and synchronously consumed through disposable-process exit, subject to explicit Owner acceptance that Frappe's `SIGUSR1` diagnostic action is unavailable inside that runner.
2. S1 if the Owner prefers to preserve Frappe diagnostics and first authorizes an exact image-bound unused-signal proof.
3. S3 only if both bounded signal approaches fail.

S2 retains `SIGUSR1` and is selected for the next read-only evidence-planning gate only. No alternate signal, including `SIGUSR2`, is selected.

## 6. Gap 2 — JUnit production and finalization

### 6.1 Common JUnit acceptance contract

If JUnit remains required, exactly one producer must bind every XML test record to an actually executed canonical test ID. The controller must reject empty, merely opened, fallback-text, malformed, incomplete, duplicated or invented XML; reject DTDs, entities and external/network resolution; reject unexpected `system-out`/`system-err`; scan canaries; verify exact counts and IDs; and treat all killed or incomplete-run XML as transient discard material. For J1/J2, final promotion order is canonical test-result finalization, JUnit finalization, `harness-complete.json`, measured-window memory seal, exit/OOM checks, `point-complete.json` and atomic promotion. J3 intentionally requires a different, separately accepted ownership order as stated below.

### 6.2 Option J1 — pinned XML-capable runner executes the actual suite

| Assessment | Planning result |
| --- | --- |
| Authoritative evidence | Exact package/version/hash/source and dependency closure; exact Frappe suite-discovery contract; exact XML schema/output/finalization/exit semantics; pinned runtime installation evidence. `unittest-xml-reporting` being listed in a test dependency group is not enough. |
| Ownership/provenance | The XML-capable runner owns `junit.xml` and consumes the exact suite returned by the pinned Frappe discovery path once. Test IDs originate from the suite, not the controller. |
| Failure/exit | Any test error/failure, discovery mismatch, write/flush/close error or count mismatch yields nonzero and no promotable JUnit. |
| Killed runs | XML is never promoted; controller discards point staging after exact-ID teardown. |
| Finalization | Runner closes XML before harness/process ordinary exit; controller validates only after the file is immutable and the runner has reached the accepted finalization marker. |
| Accounting effect | Strongest independent one-to-one traceability for A/P/S case execution; no selective retry or suppression. |
| Permission/leakage | XML may expose exception paths/text unless the runner is configured or adapted to generic sealed failure records; raw failed XML is transient. |
| Determinism | High after exact dependency and ordering proof. |
| Source impact | Harness/bootstrap invocation and Dockerfile dependency/materialization; controller XML parser/validator. Initializer unchanged. |
| Resource/secret impact | No new service or secret; one exact staging file. |
| Cost/reversibility | Moderate-to-high dependency and supply-chain review; removable if policy changes. |
| Residual risk | Third-party runner behavior may diverge from Frappe cleanup or subtest handling. |
| Exact Owner decision | Choose `junit_option_j1_runner` and authorize a pinned dependency/source compatibility gate. |

### 6.3 Option J2 — reviewed adapter around the actual Frappe suite

| Assessment | Planning result |
| --- | --- |
| Authoritative evidence | Exact pinned Frappe discovery/setup/cleanup path, Python `unittest.TestResult` behavior, adapter schema and a proof that the suite executes exactly once with unchanged IDs and exit semantics. |
| Ownership/provenance | Source-controlled bootstrap/adapter owns canonical per-test outcomes and serializes JUnit directly from the actual result callbacks. Controller never invents cases. |
| Failure/exit | Adapter-internal, serialization or finalization failure forces nonzero and discard even when tests passed. Frappe cleanup remains in an exact `finally`. |
| Killed runs | Partial event log/XML is invalid and destroyed. |
| Finalization | Complete suite result -> closed canonical event seal -> closed JUnit -> harness-complete -> finalization marker -> ordinary exit. |
| Accounting effect | Strong if exact IDs map one-to-one; more custom code than J1 could suppress or misclassify a case. |
| Permission/leakage | Adapter must store fixed result classes and hashes, never traceback, SQL, identities or financial values. |
| Determinism | High if callbacks and subtest mapping are closed and ordered. |
| Source impact | Harness/bootstrap and controller; Dockerfile only for entrypoint/copy, not a third-party runtime dependency. Initializer unchanged. |
| Resource/secret impact | One canonical test-event artifact plus JUnit in point staging. |
| Cost/reversibility | High custom review cost; source-controlled and reversible. |
| Residual risk | Reimplementing runner semantics and future Frappe drift. |
| Exact Owner decision | Choose `junit_option_j2_adapter` and authorize a pinned Frappe/Python adapter-design gate. |

### 6.4 Option J3 — controller formats JUnit from sealed canonical outcomes

| Assessment | Planning result |
| --- | --- |
| Authoritative evidence | A harness-owned, append-only, hash-chained per-test outcome schema with exact canonical IDs, start/final events and result enums; proof that the harness cannot seal without one final event for every expected case. |
| Ownership/provenance | Harness owns truth; controller is a deterministic serializer only. Controller may not derive success from exit code, totals or missing records. |
| Failure/exit | Missing, duplicate, reordered, malformed or nonfinal record stops. Formatting failure stops. XML and source event seal must cross-hash. |
| Killed runs | Unsealed event records and XML are discard-only. |
| Finalization | Harness seals canonical outcomes and `harness-complete`; controller validates and formats JUnit; controller then performs terminal point sealing. This intentionally changes the prior JUnit-before-harness ownership model and would require an accepted amendment. |
| Accounting effect | Acceptable only with exact one-to-one A/P/S IDs; weaker independence because harness supplies both test truth and accounting evidence. |
| Permission/leakage | Fixed hashes/enums can be safer than third-party tracebacks. Controller must never receive raw expected/actual figures. |
| Determinism | High for formatting; provenance independence is lower. |
| Source impact | Harness event schema and controller serializer/validator; Dockerfile/initializer usually unchanged. |
| Resource/secret impact | Adds one sealed event artifact, no service or secret. |
| Cost/reversibility | High schema and governance cost; removable if a runner later owns XML. |
| Residual risk | Correlated producer failure and accidental controller adjudication. |
| Exact Owner decision | Choose `junit_option_j3_formatter` and explicitly accept reduced producer independence plus a control-plane ownership amendment. |

### 6.5 Option J4 — remove JUnit by policy

| Assessment | Planning result |
| --- | --- |
| Authoritative evidence | Explicit Owner policy plus revised closure criteria that identify the replacement independent evidence and explain the loss of JUnit/CI interoperability. |
| Ownership/provenance | Harness-owned canonical test record and controller-owned point seal become the only case-level evidence. |
| Failure/exit | Empty/missing canonical records, nonzero exit, failed case or incomplete finalization still stops. |
| Killed runs | Discard-only. |
| Finalization | Canonical record seal -> harness seal -> memory/exit/OOM validation -> point seal. |
| Accounting effect | Reduces independent evidence that every A/P/S case executed. Requires explicit risk acceptance. |
| Permission/leakage | Removes an XML leakage surface. |
| Determinism | Potentially high but less portable and independently consumable. |
| Source impact | Harness/controller schema and all documents that currently require JUnit; Dockerfile may be simpler. |
| Resource/secret impact | Removes `junit.xml`; no secret change. |
| Cost/reversibility | Lowest runtime cost but highest governance impact; reversible only with a new evidence amendment. |
| Residual risk | Reduced release-tool compatibility and correlated evidence ownership. |
| Exact Owner decision | Choose `junit_option_j4_remove` and explicitly accept the named evidence reduction; silence or convenience cannot select it. |

### 6.6 JUnit recommendation ranking — recommendation only

1. J2 because it retains the actual pinned Frappe suite/setup/cleanup path while making result and XML ownership explicit.
2. J1 if an exact XML-runner dependency proves full compatibility with Frappe IDs, subtests, cleanup and exit behavior.
3. J3 only with explicit acceptance of lower producer independence.
4. J4 only as an explicit evidence-policy change.

## 7. Gap 3 — backend UID/GID and secret readability

### 7.1 Minimum read-only fingerprint

No Dockerfile user, copy destination, ownership, mode or secret mount can be frozen until one separately approved read-only image fingerprint returns all of these facts for the exact platform manifest:

| Evidence group | Exact future evidence |
| --- | --- |
| Image identity | Repository digest, platform manifest digest, config digest/full image ID, OS, architecture, rootfs diff IDs and approved source receipt. |
| Image process config | `Config.User`, `WorkingDir`, exec-form entrypoint array, command array and stop signal as fixed fields; never full raw config or `Config.Env`. |
| Effective identity | Numeric effective UID, primary GID, supplementary GIDs, user namespace/rootless posture and the exact `/etc/passwd` and `/etc/group` rows that resolve them. |
| Runtime paths | Exact regular-file paths and SHA-256 for Python, Bench helper, Frappe, ERPNext and `erp_workspace_ui`; Python build/ABI and import resolution. |
| Proposed destinations | Every parent component plus proposed harness/initializer destination: type, device/inode or equivalent identity, owner UID/GID, mode, symlink/hardlink count, traversal rights and mount read-only state. |
| Entrypoint feasibility | Effective user can traverse, read and execute only the intended files; PID 1 command resolves without shell search or writable-path precedence. |
| Secret feasibility | Exact service UID can read the proposed owner-only mounted file and unrelated service UIDs cannot; source ownership is observed, not inferred from Compose `uid`/`gid`/`mode`. |
| Evidence sanitation | Fixed fields and hashes only; no environment dump, credential, secret hash, source secret path, live configuration or broad filesystem listing. |

The fingerprint is evidence acquisition only. It may identify candidate destinations but may not create a Dockerfile, image, container or secret.

### 7.2 Option K1 — owner-only host-RAM file-backed Compose secrets

| Assessment | Planning result |
| --- | --- |
| Authoritative evidence | Pinned Compose/Engine file-secret behavior plus the exact UID/GID/path fingerprint. The controller must prove host-RAM backing, owner-only parent, regular file, no-follow, link count, fixed maximum size and service-specific read-only mount. |
| Delivery | Controller later creates an exact point-scoped RAM directory and one secret file per consuming service, pre-owned by that service's proven UID/GID with owner-read-only mode. Compose mounts it read-only under one exact `/run/secrets/<approved-name>` target. |
| Accounting effect | Neutral if reader receives only the reader credential and preparer/writer/topology credentials are segregated. |
| Permission/leakage | Lowest bounded option. Do not rely on ignored Compose long-syntax ownership fields. No shared secret between roles. No environment, argv, logs or evidence values. |
| Determinism | High after pinned file-mount and user-namespace proof. |
| Source impact | Controller secret lifecycle, Compose service grants, initializer fixed secret reader and Dockerfile user/path. Harness reads no root secret. |
| Resource impact | Point-scoped RAM secret directory is manifest membership; exact source is transient and absent after teardown. |
| Cost/reversibility | Moderate; no new service. Reversible by removing exact mount and controller lifecycle. |
| Residual risk | Host ownership mismatch under user namespaces, source-path metadata exposure and incomplete source erasure. |
| Exact Owner decision | Choose `secret_option_k1_host_ram_files` after the UID/GID and pinned Compose/Engine fingerprint passes. |

### 7.3 Option K2 — one-shot secret staging broker into private tmpfs

| Assessment | Planning result |
| --- | --- |
| Authoritative evidence | Exact Compose tmpfs/volume ownership, broker user/privilege-drop behavior, atomic file creation/rename, mount propagation and consumer denial proof under pinned versions. |
| Delivery | A point-scoped one-shot broker receives narrowly granted host-RAM files, writes role-specific owner-only files into separate private tmpfs mounts, closes input, destroys source and exits before consumers start. Consumers mount only their role file read-only. |
| Accounting effect | Neutral if broker cannot access accounting data or evidence. |
| Permission/leakage | More isolation flexibility but introduces a privileged material-handling process. Broker logs/stdout/stderr must be empty or generic; no reusable credential remains in its image or environment. |
| Determinism | Moderate-to-high after exact mount and startup ordering proof. |
| Source impact | Controller, Compose, broker source or initializer mode, Dockerfile(s) and resource schema. Harness unchanged for delivery. |
| Resource impact | Additional one-shot container and private tmpfs objects; all require exact-ID recovery and teardown membership. |
| Cost/reversibility | High source/topology/review cost; reversible only after resource/schema contraction. |
| Residual risk | Broker privilege, cross-service mount leakage, partial staging and recovery complexity. |
| Exact Owner decision | Choose `secret_option_k2_broker` only if K1 fails the exact UID/readability proof, then authorize a separate broker-design gate. |

### 7.4 Option K3 — privileged PID 1 reads then drops identity

| Assessment | Planning result |
| --- | --- |
| Authoritative evidence | Exact kernel/container privilege-drop behavior, supplementary-group clearing, capabilities, no-new-privileges, process memory/FD closure and all child inheritance under the pinned image/runtime. |
| Delivery | Runner starts privileged, reads a narrowly mounted secret, closes/unmounts where possible, clears groups/capabilities, changes UID/GID and then imports application code. |
| Accounting effect | Formula-neutral, but measured-process trust is materially broader. |
| Permission/leakage | Highest: the same process once held elevated identity and secret bytes. Irreversible erasure from memory is difficult to prove. |
| Determinism | Platform-sensitive. |
| Source impact | Bootstrap, Dockerfile entrypoint, controller/Compose security options; initializer may share logic. |
| Resource impact | No extra service, but privileged container posture expands containment evidence. |
| Cost/reversibility | High proof cost; source is reversible, historical process exposure is not. |
| Residual risk | Surviving secret memory, file descriptors, capabilities or supplementary groups. |
| Exact Owner decision | Choose `secret_option_k3_privilege_drop` only with explicit High-risk acceptance after K1 and K2 are shown unsuitable. |

### 7.5 Secret recommendation ranking — recommendation only

1. K1 after exact UID/GID and user-namespace proof.
2. K2 if K1 cannot make service-specific owner-only files readable without broadening access.
3. K3 only as an explicitly accepted higher-risk fallback.

Environment-sourced Compose secrets are rejected for this package because the value originates in environment state. World-readable files, broad mounts, copied live configuration and Docker socket access remain rejected.

The disposable measurement `site_config.json` must contain only the eventual reader credential, be owner-readable/writable only by the exact runner identity, live on the exact per-point site volume, be mounted read-only to measured runners if pinned Frappe behavior allows it, and be destroyed without export. Its hash is sensitive and must not be retained as a credential oracle; evidence binds only an approved redacted structural receipt.

## 8. Gap 4 — immutable runtime provenance

### 8.1 Required future chain of custody

The future evidence gate must produce one non-circular chain:

1. approved MariaDB repository reference by immutable digest;
2. resolved platform manifest digest;
3. image config digest and full local image ID;
4. rootfs diff IDs and exact OS/architecture;
5. exact official-image manifest/library record;
6. exact `MariaDB/mariadb-docker` source revision, Dockerfile/entrypoint paths and SHA-256;
7. entrypoint bytes in the image equal the pinned source bytes;
8. exact server version/build and client protocol facts;
9. exact `MARIADB_ROOT_PASSWORD_FILE` and application-password-file success and fail-closed behavior;
10. exact empty-datadir initialization and existing-datadir restart behavior;
11. exact Compose plugin semantic version, source/build identity and binary checksum;
12. exact Docker Engine semantic/API version, source/build identity and binary checksum;
13. OCI runtime, cgroup v2, storage driver, rootless/user-namespace and relevant daemon security posture;
14. canonical rendered Compose hash without secret values;
15. exact internal-network flag, no published ports, no host/external network and complete service membership; and
16. fixed-field image/container/mount/secret inspection receipts with prohibited fields absent.

No pull, build or container action is authorized by this planning document. The eventual provenance fingerprint, image materialization and synthetic execution remain separate Owner gates.

### 8.2 Option R1 — official MariaDB image by repository digest

| Assessment | Planning result |
| --- | --- |
| Authoritative evidence | One official repository digest tied to its platform manifest, config/image ID, official-images record and exact [`MariaDB/mariadb-docker`](https://github.com/MariaDB/mariadb-docker) source/entrypoint bytes. |
| Accounting effect | Strongest low-customization basis for Decimal, collation, snapshot, timeout and privilege proof, while still requiring exact behavior tests later. |
| Permission/leakage | Official entrypoint may expose generated-password or environment behavior unless forbidden modes and output checks are exact. Only `*_FILE` paths may be considered. |
| Determinism | High when digest, platform, source and Engine/Compose are all fixed. |
| Source impact | Compose digest/reference and controller provenance validator; no extra database Dockerfile. Initializer binds exact behavior. |
| Resource/secret impact | Standard database service and exact role secrets. |
| Cost/reversibility | Lowest supply-chain expansion; reversible by an separately reviewed digest update. |
| Residual risk | Registry/source mapping and future host-kernel behavior remain distinct evidence layers. |
| Exact Owner decision | Choose `runtime_option_r1_official_digest` and later approve one read-only/product fingerprint gate; do not choose the digest in this amendment. |

### 8.3 Option R2 — minimal derived database wrapper over an official digest

| Assessment | Planning result |
| --- | --- |
| Authoritative evidence | Everything in R1 plus exact wrapper Dockerfile/source, build inputs, builder provenance, output image ID/digest and proof that server/entrypoint semantics are unchanged except the accepted normalization. |
| Accounting effect | Can normalize secret/startup behavior but adds code that may change initialization or server configuration. |
| Permission/leakage | Wrapper may reduce entrypoint ambiguity or create a new secret/logging surface. |
| Determinism | High only with reproducible local materialization and no network/package action. |
| Source impact | Expands the accepted future source scope beyond the four files and therefore requires a separate architecture/source-allowlist amendment. |
| Resource/secret impact | Same service shape; adds a retained derived image. |
| Cost/reversibility | High supply-chain and release cost; reversible to R1 after new evidence. |
| Residual risk | Wrapper drift and loss of direct official-image equivalence. |
| Exact Owner decision | Choose `runtime_option_r2_derived_db` only if R1's pinned entrypoint cannot satisfy accepted secret/fail-closed behavior, then authorize a separate image-design gate. |

### 8.4 Option R3 — source-built MariaDB image

| Assessment | Planning result |
| --- | --- |
| Authoritative evidence | Exact MariaDB source tag/commit/tree, compiler/toolchain/base digests, build flags, dependency closure, reproducible build and server test provenance. |
| Accounting effect | Maximum version control but largest risk of configuration divergence from supported official binaries. |
| Permission/leakage | Full supply-chain and build-secret review required. |
| Determinism | Potentially high but expensive to establish. |
| Source impact | Major expansion beyond the current project and four-file scope. |
| Resource/secret impact | New build/materialization resources and retained image. |
| Cost/reversibility | Highest; reversal requires complete product re-fingerprint. |
| Residual risk | Toolchain and dependency provenance. |
| Exact Owner decision | Choose `runtime_option_r3_source_build` only after R1 and R2 are concretely unsuitable and a separate architecture approval expands scope. |

### 8.5 Runtime recommendation ranking — recommendation only

1. R1.
2. R2 only to cure a proven official-entrypoint incompatibility.
3. R3 only as an exceptional separately governed product-build outcome.

The committed mutable `mariadb:10.6` configuration is not evidence authority. A tag, version string or unbound local image ID cannot close this gap.

## 9. Gap 5 — controlled primer and fixture-preparation protocol

### 9.1 Common protocol rules

All options below retain one complete disposable stack per workload-point envelope and use separate fault envelopes. Every subrun has its own nonce, sequence begins at one, and its first marker predecessor is `genesis`. Cross-subrun dependencies are hashes in the next subrun manifest and controller receipt, never a reused nonce or cross-branch marker predecessor.

Every marker retains the accepted common closed fields and canonical encoding. The tables below add planning rows but do not publish the complete JSON Schema. Exact schemas remain blocked until the Owner chooses one option in every gap.

Common failure rules:

- duplicate, missing, extra, stale, rewritten, reordered or contradictory marker: discard the complete envelope;
- controller restart after release intent: no resend, discard the complete envelope;
- unexpected connection, account, service, mount, secret, mutation or fixture state: discard the complete envelope;
- preparer/writer failure, partial credential rotation, failed seal, failed reset or predecessor mismatch: discard the complete envelope;
- no silent repair, restore-in-place or reuse of mutated state; and
- recovery/teardown acts only on manifest full IDs plus approved project/point labels and proves absence.

### 9.2 Required role split discovered from the unchanged harness

Static preparation alone cannot support S01-S08. Every viable protocol must provide:

- a static fixture preparer with temporary exact DML authority;
- a credential finalizer that creates/scopes reader, topology and writer accounts and removes setup authority;
- a read-only seal verifier;
- ordinary read-only accounting/permission/workload runners;
- a separate narrowly scoped dynamic writer for S01-S08, with no access to measured evidence;
- a topology-only one-shot runner; and
- an isolated reconnect arrangement with no root in a measured runner.

Dynamic snapshot cases are semantic proof, not workload-cap derivation. They run in isolated semantic envelopes or verified clones and never contaminate cold/warm workload points.

### 9.3 Protocol P1 — fresh full stack per workload point and per mutating semantic case

#### Static preparation marker branch

| Basename | Event | Mode | Phase | Seq. | Predecessor | Release owner/action | Evidence owner | Terminal state |
| --- | --- | --- | --- | ---: | --- | --- | --- | --- |
| `fixture-preparation-ready.json` | `fixture_preparation_ready` | `fixture_preparation` | `pre_mutation` | 1 | `genesis` | controller validates preparer ID, exact writer principal and empty evidence target, records intent, releases once | preparer | no |
| `fixture-preparation-released.json` | `fixture_preparation_released` | `fixture_preparation` | `mutation` | 2 | prior marker hash | preparer acknowledgment | preparer | no |
| `fixture-prepared.json` | `fixture_prepared` | `fixture_preparation` | `prepared_unsealed` | 3 | prior marker hash | no release; preparer closes mutation connection, seals fixed fixture receipt and exits | preparer | `prepared_unsealed` |

The controller then validates the preparer terminal receipt, removes the preparer, performs the separately selected account/secret rotation through initializer-only authority, removes root/setup secret grants and writes `credential-transition-receipt.json`. This controller-owned receipt contains hashes/counts/enums only and is not an accounting seal.

#### Seal-verification marker branch

| Basename | Event | Mode | Phase | Seq. | Predecessor | Release owner/action | Evidence owner | Terminal state |
| --- | --- | --- | --- | ---: | --- | --- | --- | --- |
| `fixture-seal-ready.json` | `fixture_seal_ready` | `fixture_seal_verification` | `pre_verify` | 1 | `genesis` | controller binds preparation and credential-transition hashes, verifies reader-only identity, records intent and releases | seal verifier | no |
| `fixture-seal-released.json` | `fixture_seal_released` | `fixture_seal_verification` | `verify` | 2 | prior marker hash | verifier acknowledgment | seal verifier | no |
| `fixture-sealed.json` | `fixture_sealed` | `fixture_seal_verification` | `sealed` | 3 | prior marker hash | no release; verifier seals normalized fixture manifest, mutation sentinel and denial results, then exits | seal verifier | `fixture_sealed` |

The seal must bind company, currency, fiscal year/period, default Finance Book and blank/NULL cohort, zero dimensions, A/P/S catalogs, exact source table counts/hashes, mutation sentinel, account/grant fingerprint and unexpected-object emptiness without retaining identities or financial values.

#### Warm-state choice P1-W1 — successful cold measurement is the primer

No new primer marker is introduced. The existing cold measured branch remains:

`measurement-ready.json` -> `measurement-released.json` -> `telemetry-ready.json` -> `normal-exit-released.json`.

After the controller validates the cold subrun, the warm subrun manifest must bind an exact nonterminal predecessor receipt. That cold-subrun receipt must not authorize envelope teardown. The later protocol/schema gate must distinguish the cold-subrun seal from the envelope-terminal `point-complete.json`, or freeze another exact nonterminal predecessor receipt; the exact basename and schema are not selected here. The envelope-terminal seal may be written only after all required successor subruns and terminal checks complete. The warm runner and cgroup are fresh; Redis/MariaDB are not reset between cold and warm; fixtures remain unchanged. If cold fails, warm does not run. Same-process warm evidence remains diagnostic only. No complete executable schema is claimed while this ownership and terminal-state distinction remains unresolved.

#### Warm-state choice P1-W2 — dedicated read-only primer

This choice is only for an explicitly approved warm-only rerun or if the Owner does not permit cold evidence to serve as the prime.

| Basename | Event | Mode | Phase | Seq. | Predecessor | Release owner/action | Evidence owner | Terminal state |
| --- | --- | --- | --- | ---: | --- | --- | --- | --- |
| `primer-ready.json` | `primer_ready` | `controlled_primer` | `pre_prime` | 1 | `genesis` | controller validates sealed/reset state and read-only principal, records intent and releases | primer | no |
| `primer-released.json` | `primer_released` | `controlled_primer` | `prime` | 2 | prior marker hash | primer acknowledgment | primer | no |
| `primer-complete.json` | `primer_complete` | `controlled_primer` | `post_prime` | 3 | prior marker hash | no release; primer seals request/result-class and mutation-denial hashes and exits | primer | `primed_unpromotable` |

The primer performs exactly one approved aggregate read, produces no promotable accounting/JUnit result and cannot run the full current suite because that suite mutates fixtures. The warm runner is a fresh process/cgroup. No Redis/MariaDB reset occurs between primer completion and warm start.

#### Dynamic S01-S08 reader/writer branch

Each mutating S case receives its own disposable semantic stack under P1.

Reader branch:

| Basename | Event | Mode | Phase | Seq. | Predecessor | Release owner/action | Evidence owner | Terminal state |
| --- | --- | --- | --- | ---: | --- | --- | --- | --- |
| `snapshot-reader-ready.json` | `snapshot_reader_ready` | `snapshot_semantic_reader` | `pre_snapshot` | 1 | `genesis` | controller validates read-only principal and sealed fixture, releases once | reader | no |
| `snapshot-reader-released.json` | `snapshot_reader_released` | `snapshot_semantic_reader` | `snapshot_open` | 2 | prior hash | reader acknowledgment and snapshot establishment | reader | no |
| `snapshot-writer-requested.json` | `snapshot_writer_requested` | `snapshot_semantic_reader` | `writer_boundary` | 3 | prior hash | controller validates exact S-case ID/hash and launches/releases only its writer subrun | reader | no |
| `snapshot-writer-observed.json` | `snapshot_writer_observed` | `snapshot_semantic_reader` | `post_writer_read` | 4 | prior hash | controller releases only after valid writer terminal seal; reader acknowledges its hash | reader | no |
| `snapshot-telemetry-ready.json` | `snapshot_telemetry_ready` | `snapshot_semantic_reader` | `finalization` | 5 | prior hash | controller seals reader-window memory and releases | reader | no |
| `snapshot-normal-exit-released.json` | `snapshot_normal_exit_released` | `snapshot_semantic_reader` | `finalization` | 6 | prior hash | reader acknowledgment then normal exit | reader | reader terminal acknowledgment |

Writer branch:

| Basename | Event | Mode | Phase | Seq. | Predecessor | Release owner/action | Evidence owner | Terminal state |
| --- | --- | --- | --- | ---: | --- | --- | --- | --- |
| `snapshot-writer-ready.json` | `snapshot_writer_ready` | `snapshot_semantic_writer` | `pre_mutation` | 1 | `genesis` | controller binds reader request hash, exact S-case, writer ID/principal and separate evidence target, then releases | writer | no |
| `snapshot-writer-released.json` | `snapshot_writer_released` | `snapshot_semantic_writer` | `mutation` | 2 | prior hash | writer acknowledgment | writer | no |
| `snapshot-writer-complete.json` | `snapshot_writer_complete` | `snapshot_semantic_writer` | `post_mutation` | 3 | prior hash | no release; writer closes connection and seals fixed commit/rollback result enum plus mutation hash | writer | `writer_complete` |

The writer cannot read or write reader evidence, cannot select a different S case and receives no root/DDL/grant/topology authority. S08 records the expected rollback result class, not raw values. Writer failure, extra connection or terminal mismatch discards the full semantic stack.

#### Reset and integration under P1

- After fixture seal and before a cold workload run, Redis state is recreated/reset and verified empty; MariaDB process/buffer state is reset over the same sealed fixture volume with any buffer dump/load behavior explicitly controlled by the selected image. Host page-cache coldness remains unproven.
- No reset occurs between accepted cold evidence and its fresh warm successor, or between a dedicated primer and warm successor.
- Initial-connection-stall, request-watchdog and finalization-watchdog branches use separate disposable fault envelopes. Their accepted existing marker chains remain unchanged and are always discard-only after an external kill or incomplete finalization.
- Dynamic semantic stacks never feed workload-cap evidence.

### 9.4 Protocol P2 — one sealed template plus verified clone per point/case

P2 uses the P1 preparer, credential transition, seal verifier, primer choices, measured branches and dynamic writer branches, but creates one sealed template and an independently verified clone for every workload point or S-case stack.

Additional template/clone planning rows:

| Basename/receipt | Event or result | Mode/phase | Seq./predecessor | Release/evidence owner | Terminal/use |
| --- | --- | --- | --- | --- | --- |
| `fixture-template-ready.json` | `fixture_template_ready` | `fixture_template` / `pre_seal` | 1 / `genesis` | controller records intent and releases; template verifier owns marker | no |
| `fixture-template-released.json` | `fixture_template_released` | `fixture_template` / `verify` | 2 / prior marker hash | verifier acknowledgment | no |
| `fixture-template-sealed.json` | `fixture_template_sealed` | `fixture_template` / `sealed` | 3 / prior marker hash | verifier owns normalized seal and exits | `template_sealed` |
| `fixture-clone-receipt.json` | `fixture_clone_verified` | controller receipt, not a runner marker | binds template seal, exact destination volume ID, byte/logical copy method, ownership/mode and post-copy DB verification | controller | required predecessor receipt for each point/case manifest |

The exact snapshot/clone mechanism, database clean-shutdown boundary, copy atomicity, volume driver behavior and post-clone recovery behavior must bind to the pinned Engine/storage driver and MariaDB source. A clone is not accepted merely because its files or volume name exist.

| Assessment | P1 | P2 |
| --- | --- | --- |
| Accounting preservation | Strong isolation through complete fresh preparation per envelope/case. | Strong if template and every clone are logically identical and S cases remain per-clone. |
| Permission/leakage | Fewer shared artifacts; repeated privileged preparation. | Template becomes a sensitive shared source and clone controller gains broader storage authority. |
| Runtime determinism | High, with higher setup variance. | Potentially higher fixture identity, but storage snapshot semantics are an added dependency. |
| Source impact | Controller, harness, Dockerfile, initializer within the current future four-file boundary. | Same plus possible source/Compose/storage tooling expansion; may exceed four files. |
| Resource/secret impact | Most containers/sites/databases; no reusable template. | Adds template volume/site and clone receipts; strict destruction and no cross-project mounts. |
| Evidence/review cost | High repeated setup evidence. | Highest provenance/atomicity/recovery evidence. |
| Reversibility | Straightforward teardown per envelope. | Requires template/clone schema contraction and complete retained-resource audit. |
| Residual risk | Preparation drift across envelopes. | Hidden copy-on-write sharing, stale database recovery and template leakage. |
| Exact Owner decision | `protocol_option_p1_fresh_stack`. | `protocol_option_p2_verified_clones` plus a separate storage-semantic evidence gate. |

### 9.5 Rejected protocol P3 — same process prepares, drops privilege and measures

P3 is not a viable Owner option on current evidence. The process would retain privileged secret bytes, connection objects and mutation code; the current suite also performs writes during permission and S fixtures. Same-process privilege drop cannot establish the accepted fresh application process or reader-only authority boundary. Static pre-seeding without a dynamic writer also cannot preserve S01-S08. Silent repair or reuse of a mutated database remains prohibited.

### 9.6 Protocol recommendation ranking — recommendation only

1. P1 with separate preparer, credential finalizer, seal verifier, ordinary reader, topology runner and dynamic S writer.
2. Within P1, P1-W1 (successful cold result as the prime) for normal cold/warm envelopes; P1-W2 only for a separately approved warm-only rerun.
3. P2 only if repeated preparation variance or cost is later proven unacceptable and storage semantics can be frozen.

## 10. Gap 6 — least-privilege database authority

### 10.1 Common principal contract

The immutable MariaDB source must prove exact syntax, privilege names, account host matching and denial behavior. Proposed principal names below are roles, not approved SQL identifiers.

| Role | Intended authority | Forbidden authority and exposure |
| --- | --- | --- |
| database root/bootstrap | Empty-datadir bootstrap and one-shot initializer only | Never mounted into preparer, verifier, reader, topology, reconnect, writer or evidence service |
| transient site owner | Frappe site creation and static fixture preparation on the disposable site DB | No global/grant option if source permits; closed and revoked/dropped before seal verification |
| static fixture preparer | Exact SELECT/DML on approved synthetic fixture tables during preparation | No DDL, grant, global, topology, process or kill authority after site creation |
| normal GL/TB reader | Exact approved reads and its own transaction assertions | No mutation, DDL, grant option, `FILE`, `PROCESS`, replica privilege or `CONNECTION ADMIN` |
| topology reader | One-shot replica/primary posture only | No site default DB, accounting-table grant, process list, kill or mutation |
| dynamic snapshot writer | Exact S-case SELECT/DML allowlist within its isolated semantic stack | No DDL, grant, topology, process, kill or access to measured evidence |
| reconnect fixture | Prefer same normal-reader account in an isolated reconnect subrun | No elevated authority unless a later source-bound proof rejects same-user termination and Owner accepts a separate fallback |

### 10.2 Option D1 — separated roles with same-user reconnect and exact service IP host scopes

| Assessment | Planning result |
| --- | --- |
| Authoritative evidence | Selected MariaDB source must prove exact account matching, table/column grants, own-thread visibility/kill, transaction assertions, replica privilege and revoke/drop behavior. Pinned Compose/Engine must prove fixed service addresses and exact network membership. |
| Host/network | One internal unpublished point network, no ports/external/host network. Each role account is bound to the exact address of only its service/subrun. Address reuse across simultaneous principals is prohibited. |
| Rotation order | root bootstrap -> site owner/install -> static seed -> create scoped readers/topology/writer -> create fresh reader-only site config -> close setup connections -> revoke/drop site owner/preparer -> restart/reset to eliminate sessions -> verify exact accounts/grants/connections -> remove privileged secrets/services -> seal verification -> measurement. |
| Reader | Exact column/table `SELECT` allowlist if pinned Frappe/raw SQL proves it sufficient. Database-wide `SELECT` is a separately accepted higher-leakage fallback, never implicit. |
| Snapshot assertion | Prove `INFORMATION_SCHEMA.INNODB_TRX` own-row visibility without `PROCESS`, or replace it with an exact connection-local transaction assertion after Owner review. `PROCESS` is not granted to the reader. |
| Topology | Separate one-shot account with `USAGE` plus the exact version-bound replica-monitor privilege and no site-data grants. Raw host/user/channel/SQL fields are never retained. |
| Reconnect | Two connections use the same disposable reader account; exact topology proves no unrelated same-account session. One connection observes/kills only its own account's target ID. No `PROCESS` or `CONNECTION ADMIN`. |
| Accounting effect | Strongest least-privilege preservation; S writer remains isolated and cannot influence other fixtures. |
| Permission/leakage | Lowest bounded DB option; fixed addresses add orchestration complexity. |
| Determinism | High if exact address allocation and source behavior are pinned. |
| Source impact | Controller, harness split, Compose/Dockerfile and initializer rotation logic. |
| Resource/secret impact | Separate service-specific credentials and one-shot topology/writer services. |
| Cost/reversibility | High initial evidence cost; small least-privilege grants are reversible within disposable teardown. |
| Residual risk | Own-row/own-thread behavior and fixed-IP portability. |
| Exact Owner decision | Choose `db_option_d1_exact_ip_same_user_reconnect` and authorize source-bound grant/host/reconnect proof. |

### 10.3 Option D2 — separated roles with point-network netmask host scopes

This option is identical to D1 except each account is bound to the exact point-network netmask rather than one service IP.

| Assessment | Planning result |
| --- | --- |
| Evidence | Selected MariaDB source must prove netmask matching; pinned Compose/Engine must prove the non-overlapping subnet and complete membership. |
| Accounting effect | Unchanged. |
| Permission/leakage | Broader: any service in the point subnet possessing a credential can use it. Service-specific secret grants and exact membership become critical. |
| Determinism | Simpler address allocation than D1. |
| Source/controller impact | Less fixed-IP logic; same harness/Dockerfile/initializer split. |
| Resource/secret impact | Same role secrets; subnet becomes a security boundary but not authentication. |
| Cost/reversibility | Moderate; reversible to D1 after account recreation. |
| Residual risk | Credential misuse from another point service. `%` remains prohibited. |
| Exact Owner decision | Choose `db_option_d2_netmask_same_user_reconnect` with explicit acceptance of the wider host scope. |

### 10.4 Option D3 — separate elevated reconnect actor

D3 retains D1 or D2 role separation but replaces same-user reconnect termination with a one-shot reconnect-only account/container holding only the exact selected-source privilege needed to terminate the named reader connection.

| Assessment | Planning result |
| --- | --- |
| Authoritative evidence | Concrete selected-source proof that same-user termination cannot meet the fixture, plus exact minimum privilege and target validation for the fallback account. |
| Accounting effect | Reconnect actor remains outside accounting adjudication and cannot retry/fallback. |
| Permission/leakage | Higher: an administrative termination privilege can affect more connections. Actor must validate full connection tuple and exact point before action, retain hashes/counts only and exit. |
| Determinism | High if one-shot and no unrelated eligible sessions exist. |
| Source impact | Controller, reconnect helper path in harness/actor, Compose/Dockerfile and initializer account creation. May exceed the four-file scope if a distinct actor file is required. |
| Resource/secret impact | Adds an elevated service-specific credential and one-shot container. |
| Cost/reversibility | High security/release review; credential disappears with disposable stack. |
| Residual risk | Overbroad kill target or process metadata leakage. |
| Exact Owner decision | Choose `db_option_d3_elevated_reconnect_fallback` only after a failed source-bound D1/D2 proof and explicit High-risk acceptance. |

### 10.5 Option D4 — controller-induced reconnect fault

D4 replaces SQL connection termination with an exact controller-owned network or database-process fault that forces the reader connection to fail. It is not equivalent by assumption.

| Assessment | Planning result |
| --- | --- |
| Authoritative evidence | Exact Engine/Compose network-disconnect or database-fault semantics, affected connections, recovery, timing, marker integration and proof that the failure represents the intended reconnect boundary. |
| Accounting effect | Could prove fail-closed handling but may no longer prove same-connection termination semantics. Closure criteria would need an accepted amendment. |
| Permission/leakage | Removes elevated DB credentials but grants controller additional runtime fault authority. |
| Determinism | Platform-sensitive and potentially broader than one connection. |
| Source impact | Controller and schemas; harness boundary expectations; Docker/Compose runtime surface. |
| Resource/secret impact | No reconnect DB secret; more controller authority. |
| Cost/reversibility | High semantic/release evidence cost. |
| Residual risk | Fault affects unrelated services or proves a different failure mode. |
| Exact Owner decision | Choose `db_option_d4_controller_fault` only with an explicit amendment to the reconnect proof objective after D1/D2 are unsuitable. |

### 10.6 Database recommendation ranking — recommendation only

1. D1, with table/column reads and same-user reconnect if exact source proof passes.
2. D2 if pinned Compose/Engine cannot make D1 address allocation deterministic and the Owner accepts point-subnet scope.
3. D3 only if same-user termination is concretely unavailable.
4. D4 only if the Owner intentionally changes the reconnect proof objective.

DNS host scopes require separate name-resolution proof and are not recommended. `%` is rejected absent a future explicit High-risk exception. Internal networking is containment, not authentication.

## 11. Cross-option source, ownership and release impact

The currently accepted future source-authoring boundary remains exactly these four paths, none of which is authorized for editing by this amendment:

1. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/tests/test_finance_gl_trial_balance_source_proof.py`;
2. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/tests/finance_gl_trial_balance_evidence_controller.py`;
3. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/tests/finance_gl_trial_balance_runner.Dockerfile`; and
4. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/tests/finance_gl_trial_balance_site_initializer.py`.

| Option family | Harness/bootstrap owner | Controller owner | Dockerfile owner | Initializer owner | Scope consequence |
| --- | --- | --- | --- | --- | --- |
| S1/S2 | pre-import mask/wait, suite entry, marker acknowledgments | exact full-ID release and recovery | exec-form PID 1 command/copies | none | stays within four files |
| S3 | control endpoint reader and nonce checks | endpoint writer/lifecycle | endpoint path/mount user | normally none | may stay within four files, but Compose/runtime resource schema expands |
| J1/J2 | actual suite, result ownership and finalization | bounded XML validation and point seal | exact dependency/copies/entrypoint | none | stays within four files if dependency materialization is Dockerfile-only |
| J3 | canonical per-test event truth | deterministic XML formatting | copies/entrypoint | none | stays within four files but changes evidence ownership |
| J4 | canonical result only | point seal without XML | simpler runner | none | stays within four files but requires broad documentation/schema policy amendment |
| K1/K3 | fixed secret reader or privilege-drop bootstrap | source creation/removal and grants | user, paths, modes and entrypoint | exact file reads/rotation | stays within four files after fingerprint |
| K2 | consumer only | broker lifecycle and exact membership | broker/consumer delivery | may stage role files | likely needs an extra broker source and therefore a new allowlist gate |
| R1 | no database-image logic | provenance validation | runner only | version-bound calls | stays within four files; Compose document remains a separately frozen execution input |
| R2/R3 | no database-image logic | build/provenance validation | new database build source | version-bound calls | exceeds current four-file boundary and requires separate architecture approval |
| P1 | split reader/preparer/verifier/writer modes and evidence | lifecycle, receipts, release, reset and teardown | one-shot mode entrypoints | account/secret transition | stays within four files if one source file implements closed modes without mixed authority |
| P2 | P1 modes plus clone verification inputs | template/clone lifecycle | same as P1 | same as P1 | may require extra storage tooling and source-scope amendment |
| D1/D2 | reader/topology/writer/reconnect denial and behavior | service/account membership validation | role-specific entrypoints | exact create/grant/rotate/revoke/drop | stays within four files |
| D3 | reconnect actor path | elevated actor lifecycle | actor entrypoint | fallback account | may exceed four files if distinct actor source is required |
| D4 | reconnect boundary expectations | runtime fault ownership | no extra DB credential | no reconnect account | stays within four files but changes accepted proof semantics |

Ownership locks for a later source gate:

- one writer owns each of the four files;
- the harness may adjudicate accounting/permission/snapshot results but not container lifecycle or promotion;
- the controller may adjudicate lifecycle/provenance/promotion but not accounting values or permission success;
- the initializer may create/rotate disposable accounts but cannot adjudicate proof results;
- the Dockerfile may layer exact files and define identity/entrypoint but cannot contain runtime decision logic; and
- any option requiring a fifth source file stops for a new exact allowlist and review rather than being folded into the four-file gate.

## 12. Main Control recommendation set and Owner planning selection

The Owner accepts the following ranked package as the selected direction for the next read-only evidence-planning gate only. The selection creates no compatibility finding, source-authoring authority, product-materialization authority, infrastructure authority or execution authority:

1. **Signal:** S2, harness-as-bootstrap with `SIGUSR1` blocked and synchronously consumed until disposable-process exit; explicitly accept the loss of Frappe's `SIGUSR1` diagnostic action only inside this runner. S1 is the lower-diagnostic-impact alternative if the Owner first wants the more expensive unused-signal fingerprint.
2. **JUnit:** J2, a source-controlled adapter around the actual pinned Frappe suite/result lifecycle. J1 is second if one exact XML runner proves complete compatibility.
3. **Identity/secrets:** K1, exact-UID pre-owned host-RAM file secrets with service-specific read-only mounts and no reliance on Compose ownership remapping.
4. **Runtime provenance:** R1, one official MariaDB repository digest bound to the exact official entrypoint source, with exact Compose/Engine provenance.
5. **Protocol:** P1, a fresh stack per workload-point envelope and isolated S case; separate preparer, credential finalizer, seal verifier, read-only runner, topology reader and dynamic writer. Use P1-W1 for normal cold/warm envelopes and P1-W2 only for an approved warm-only rerun.
6. **Database:** D1, exact service-IP host scopes, separate principals, no `PROCESS`/`CONNECTION ADMIN` for readers and source-proven same-user reconnect. D2 is the bounded host-scope fallback.

The selected planning receipt is exactly S2/J2/K1/R1/P1-W1/D1, with these controlling qualifications:

- S2 blocks `SIGUSR1` before Frappe import, consumes it synchronously and keeps it blocked through disposable-process exit. Frappe's `SIGUSR1` diagnostic action is unavailable only inside that disposable runner; in-process restoration is not selected.
- J2 must preserve the actual pinned Frappe suite, test IDs, setup, cleanup, result and exit behavior. The controller may not invent tests or success.
- K1 uses exact-UID, owner-only host-RAM secret files and service-specific read-only mounts without relying on Compose file-secret `uid`, `gid` or `mode` remapping.
- R1 requires one later repository digest bound to its exact platform manifest, image/config identity and matching official entrypoint source. No digest is approved now.
- P1-W1 separates the static preparer, credential finalizer, seal verifier, measured reader, topology reader and dynamic writer. Each S01-S08 case uses an isolated semantic stack or a later-approved verified clone; the full suite is never a primer. Section 9.3's nonterminal cold-subrun clarification controls W1.
- D1 targets exact table/column read grants and exact service-IP host scopes. Database-wide `SELECT` is not approved, and normal measured runners receive no root, mutation, DDL, grant, `PROCESS`, `CONNECTION ADMIN` or topology authority.

S1, S3, J1, J3, J4, K2, K3, R2, R3, P2, W2 and D2-D4 remain unapproved fallbacks.

Why this package ranks first:

- it keeps accounting adjudication in the harness and lifecycle adjudication in the controller;
- it does not require a fifth source file on current planning assumptions;
- it removes root and mutation authority from normal measured runners;
- it preserves exact case-level evidence without relying on the pinned broken Frappe XML path;
- it uses official immutable database provenance before custom database-image work; and
- it maximizes reversibility because every privileged resource is disposable and point-scoped.

The ranking does not establish feasibility. Each recommended choice remains conditional on the exact evidence gates in Section 16.

## 13. Owner-decision dependencies

### 13.1 Decisions that may safely be made independently

- Whether JUnit remains mandatory (J1/J2/J3 versus J4) can be decided independently from the MariaDB image family, although final schemas depend on both.
- S2 versus an S1 fingerprint can be chosen independently from D1 versus D2 host scopes.
- R1 versus a later derived-image exception can be decided independently from P1-W1 versus P1-W2.
- P1-W1 versus P1-W2 can be decided independently from the JUnit producer, provided the primer is read-only and unpromotable.
- The policy invariant that measured runners never possess root, writer, topology or elevated reconnect credentials may be affirmed independently of all implementation choices.
- Continued deferral of VM isolation, host page-cache proof, CORS, HTTP and numeric limits does not prevent these planning decisions.

### 13.2 Decisions and evidence that must remain sequential

1. Record the Owner-selected policy directions for signal, JUnit, secret delivery, runtime provenance, protocol and DB authority (completed by this reconciliation).
2. Fingerprint immutable backend/Python and MariaDB/Compose/Engine products without creating execution authority.
3. Use those fingerprints to freeze numeric UID/GID, exact paths, secret readability, signal ownership and database privilege/host behavior.
4. Freeze the chosen static-preparation, credential-transition, seal, cold/primer/warm, dynamic-writer, topology and reconnect subruns.
5. Freeze the final invocation, Dockerfile identity/entrypoint, initializer call/rotation order and controller ownership.
6. Publish complete execution-manifest, marker, evidence, recovery, memory, teardown and JUnit/canonical-result schemas only after steps 1-5 close.
7. Run one bounded combined accounting/security/runtime/release review over those exact contracts.
8. Only then may the Owner consider reopening a four-file source-authoring gate.

Source authoring, image materialization, synthetic infrastructure creation, synthetic execution, evidence promotion and any later runtime/live activity remain separate approvals even after all planning choices are made.

## 14. Findings by severity

### Blocker

| Finding | Concrete evidence | Main Control disposition |
| --- | --- | --- |
| Accepted `SIGUSR1` release ownership conflicts with pinned Frappe import. | Pinned `frappe/__init__.py`, `_optimizations.py` and `bench_helper.py`; current harness imports Frappe at module load. | Accepted. The Owner selected S2's pre-import, blocked-through-exit direction; no invocation is executable until exact evidence closes the conflict. |
| Pinned Frappe path cannot prove JUnit records. | Pinned `testing.py` opens/configures one XML runner but executes `frappe.testing.TestRunner`, a `TextTestRunner`. | Accepted. The Owner selected J2; exact adapter/source evidence remains required. |
| Exact non-root identity and secret readability are unknown. | Backend `Config.User`, numeric UID/GID, passwd/group and user-namespace posture are absent; Docker documents ignored file-secret `uid`/`gid`/`mode`. | Accepted. K1 is the selected direction and remains conditional on a read-only fingerprint. |
| Database/runtime behavior is not immutable. | Canonical MariaDB image remains unresolved; mutable `mariadb:10.6` is not evidence authority; exact Compose/Engine are absent. | Accepted. R1 is the selected direction; no digest or compatible product evidence is approved yet. |
| Current harness violates the planned measured-reader boundary. | Root environment/topology/reconnect use; mutation connection and static seeding in `setUpClass`; committed permission writes; dynamic S01-S08 writes. | Accepted. Protocol and role separation are mandatory before source authoring. |
| Complete protocol/schema remains impossible before selected evidence and W1 ownership close. | Product/source identity, JUnit, DB principal behavior and the cold-subrun versus envelope-terminal predecessor contract still determine fields, ownership and terminal states. | Accepted. This amendment deliberately publishes no complete executable schema. |

### High

| Finding | Concrete evidence | Main Control disposition |
| --- | --- | --- |
| Full-suite warm priming would mutate the sealed fixture. | Current suite seeds/mutates in setup, permission cases and S cases. | Accepted. Primer is one approved aggregate read only; complete suite is prohibited as primer. |
| Frappe-generated site user is too broad for measurement. | Pinned MariaDB setup source grants the generated site user broad database rights. | Accepted. Post-install rotation and reader-only fresh site config are mandatory. |
| Static pre-seeding cannot preserve S01-S08. | S01-S08 require concurrent committed/rolled-back writer actions during an open snapshot. | Accepted. Separate dynamic writer and isolated semantic envelope/clone required. |
| Normal transaction proof may tempt excess process authority. | Current harness checks `INFORMATION_SCHEMA.INNODB_TRX`; own-row visibility is not source-bound. | Accepted. No `PROCESS` grant; prove own-row visibility or approve an equivalent local assertion. |
| Same-user reconnect can target unintended sessions if account isolation fails. | MariaDB current docs scope visibility/kill to own account without elevated privilege, not necessarily one connection. | Accepted. Require no unrelated same-account session and exact target tuple. |
| Raw topology, process, JUnit or exception material can leak identity/SQL/path data. | Documented MariaDB fields and ordinary unittest/XML failure behavior. | Accepted. Retain only fixed enums/hashes/counts; failed raw material is transient. |
| Broad host scopes or environment secrets expand credential reach. | MariaDB omitted host becomes `%`; environment values are process state. | Accepted. Exact IP preferred; `%` and environment secret values rejected. |

### Medium

- Controller evidence may bind hashes of accounting artifacts but may not retain their expected/actual figures.
- Initializer, preparer, writer, verifier and measured evidence targets require separate write permissions and exact ownership.
- Template/clone P2 adds storage-driver, copy-on-write and retained-template risks.
- Secret source-path metadata may be compared transiently but not retained raw.
- Full-lifetime memory through process exit remains unproven; accepted authority remains the measured window under cgroup v2.
- Same-process warm results remain diagnostic only.

### No new accounting-semantic defect

The bounded accounting review found no contradiction in the accepted `gl_reconstructed` equations, exact balance, Finance Book cohort, fiscal posture, complete-chart authority, aggregate-only output or fail-closed/no-execution boundary. This amendment does not reopen those closed semantics.

## 15. Independent review and Main Control synthesis

One bounded review was run for each required discipline, followed by this single synthesis. No open-ended loop was started.

| Review | Findings accepted | Findings rejected or constrained | Deferred |
| --- | --- | --- | --- |
| Accounting preservation | Root/mutation authority conflicts with read-only measurement; JUnit must bind exact A/P/S cases; full-suite primer mutates; separate S writer required. | No new accounting equation or source-candidate defect accepted. Signal choice has no accounting preference beyond sequencing-only control. | Cancellation/close/reopen/execution remain reporting-only deferrals. |
| Security, permission and leakage | Exact UID/GID first; K1 preferred; root never reaches measurement; separate writer/topology roles; exact host scopes; raw JUnit/process/topology outputs prohibited. | Automatic `SIGUSR2`, `%` host scope, environment secret values, same-process privilege drop and static-only preparation rejected. | Higher-risk broker/elevated reconnect options remain conditional Owner choices. |
| Database/runtime | Pinned signal and JUnit conflicts; immutable product gap; fresh-process boundary; source-bound transaction/topology/reconnect proof. | Mutable tag/version-only evidence, unbound generic privilege assumptions and empty XML rejected. | Exact signal, MariaDB digest, Engine/Compose versions and numeric identity await later read-only gates. |
| Release/governance | Four-file ownership locks, exact-ID lifecycle, discard-only ambiguity, separate source/materialization/execution gates and no complete schema yet. | Incidental fifth file, broad source allowlist, runtime action during planning and combined external-state approval rejected. | Image materialization, synthetic execution, HTTP/CORS, live action and numeric limits remain separate. |

Reviewer recommendation differences were not treated as findings. Security favored S1 if an unused signal can be proven; runtime favored S2 for a smaller absence-proof burden. Main Control ranks S2 first with explicit diagnostic-loss acceptance and retains S1 as a fully bounded alternative. Accounting/security favored J1 for independent runner ownership; runtime favored J2 to preserve the actual pinned Frappe lifecycle. Main Control ranks J2 first because it retains that lifecycle, while J1 remains the preferred dependency-based alternative if exact compatibility is proven.

## 16. Exact evidence required before source authoring may be reconsidered

All items below are required; no one item reopens authoring by itself.

1. **Owner option receipt:** explicit tokens selecting one signal direction, one JUnit policy/producer, one secret mechanism, one runtime-provenance direction, one protocol/primer direction and one DB authority/host-scope direction.
2. **Backend identity fingerprint:** exact platform image/config identity, Python build/ABI, `Config.User`, numeric UID/GID/groups, passwd/group mapping, paths, parent traversal, ownership/modes, entrypoint/command/stop signal and userns/rootless posture.
3. **Signal/bootstrap proof:** for S2, pinned mask/handler/import/thread/pending-signal and diagnostic-loss contract; for S1, the full unused-signal source plus disposable behavior proof; for S3, an accepted transport amendment.
4. **JUnit proof:** exact actual-suite discovery, expected test-ID catalog and one producer's source/dependency, result, subtest, failure, cleanup, finalization, XML safety, count and exit contracts.
5. **MariaDB provenance:** repository/platform/config/image IDs, official-image record, exact upstream entrypoint revision/bytes, server version/build and selected platform.
6. **Compose/Engine provenance:** exact versions/build/source/checksums/API, runtime/storage/userns/cgroup/security posture, canonical Compose rendering and secret/network behavior.
7. **Non-secret secret-readability proof:** fixed service identity can read only its proposed non-secret canary file; unrelated roles cannot; file-backed ownership/mode behavior and teardown are exact. No real secret is created in this evidence gate.
8. **Initialization proof contract:** pinned `frappe.installer._new_site` signature/call order retained or explicitly amended; exact site-owner host scope, app install/control sequence and fail-closed finalization.
9. **Database authority proof:** exact account names/host scopes, table/column grants, create/grant/rotate/revoke/drop order, reader DML/DDL/global denials, topology privilege, no unexpected accounts/connections and no `%` unless separately accepted.
10. **Snapshot proof:** own-row transaction visibility without `PROCESS` or an accepted connection-local substitute; exact `READ ONLY, WITH CONSISTENT SNAPSHOT`, reconnect target and no-retry/fallback behavior under the selected source.
11. **Fixture/protocol freeze:** final static preparer, credential transition, seal, reset, cold/primer/warm, dynamic writer, topology, reconnect and fault marker tables with every owner, sequence, predecessor, terminal state, failure and teardown rule.
12. **Complete closed schemas:** execution manifest, all markers, canonical test/JUnit evidence, harness complete, point complete, controller receipt, memory, recovery, credential transition, fixture/clone and teardown. Unknown fields rejected recursively.
13. **Exact command and inspection allowlists:** fixed exec-form commands and fixed-field parsers only; no command is executed by the authoring gate.
14. **Final four-file feasibility check:** selected options fit the exact four paths. If not, stop for a new architecture and source-allowlist approval.
15. **One combined bounded review and Main Control synthesis:** accounting, security, database/runtime and release findings tied to exact source/product evidence.

Only after all evidence is accepted may the Owner consider a new **Four-File Source-Authoring Gate**. That later gate remains code authoring and review only, not execution.

## 17. Owner selections and next-gate boundary

The Owner selects, for the next read-only evidence-planning gate only:

1. `signal_option_s2_bootstrap`, blocked through disposable-process exit with no in-process restoration;
2. `junit_option_j2_adapter` around the actual pinned Frappe suite;
3. `secret_option_k1_host_ram_files`;
4. `runtime_option_r1_official_digest`, with no digest selected yet;
5. `protocol_option_p1_fresh_stack` plus `primer_option_p1_w1_cold_as_prime`, subject to the unresolved nonterminal predecessor contract in Section 9.3; and
6. `db_option_d1_exact_ip_same_user_reconnect`, targeting exact table/column read grants.

The next possible task is **GL/TB Selected-Option Product and Compatibility Fingerprint Gate**, read-only planning/evidence only. It may fingerprint the selected products and compatibility facts but may not author source, select a digest, materialize an image, create infrastructure or secrets, or execute any proof.

## 18. Validation and future documentation staging allowlist

Validation required for this planning-only amendment:

- repository root, branch, local HEAD, configured upstream and ahead/behind;
- empty Git index;
- candidate scope exactly this amendment plus README, in addition to the unchanged untracked harness and four protected exclusions;
- `git diff --check HEAD`;
- Markdown trailing-whitespace and local-reference resolution;
- original planning result `compatibility_gap_resolution_options_ready_for_owner_decision`, exact Owner selections and next-gate boundary retained;
- compatibility stop and four-file authoring stop retained;
- no complete executable schema claimed;
- no numeric workload/runtime limit selected;
- harness SHA-256 unchanged;
- future controller, Dockerfile and initializer absent;
- four protected exclusions unchanged and unstaged; and
- before the authorized documentation publication, no source edit, test, Bench, Docker/Compose action, image, site, database, network, volume, secret, SQL, HTTP/CORS inspection, live access, staging, commit, push, migration, permission change, protected gate or accounting action.

The Owner authorizes this controlled documentation publication. The exact staging allowlist is only:

1. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/finance-accounting-cycle2-gl-tb-compatibility-gap-resolution-amendment-2026-07-18.md`; and
2. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/README.md`.

## 19. Main Control status after Owner selection

**Original planning result:** `compatibility_gap_resolution_options_ready_for_owner_decision`

**Current controlling decision:** `stopped_for_compatibility_schema_gap`

The Owner-selected S2/J2/K1/R1/P1-W1/D1 directions are planning inputs for the next read-only evidence gate only. The W1 cold-subrun versus envelope-terminal distinction remains unresolved for the later protocol/schema gate. The Four-File Source-Authoring Gate remains stopped, and no implementation, product materialization, infrastructure, secret or execution authority is created.
