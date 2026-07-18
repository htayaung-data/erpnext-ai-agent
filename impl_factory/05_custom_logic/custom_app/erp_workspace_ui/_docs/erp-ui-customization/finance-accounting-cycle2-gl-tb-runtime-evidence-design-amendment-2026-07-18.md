# Finance & Accounting Cycle 2 GL / Trial Balance Runtime Evidence Design Amendment

**Date:** 2026-07-18

**Authority:** Main Control v2 planning only

**Decision:** `runtime_evidence_design_reconciled_for_docs_staging`

**Owner status:** accepted as the canonical runtime-evidence planning design

**Execution authority:** not granted

## 1. Purpose and controlling posture

The Single GL / Trial Balance Synthetic Harness Authoring Gate stopped at `stopped_for_harness_gap`. The accounting, permission, release-containment, and static reviews of the current harness remain accepted. The stop was caused by runtime-evidence design gaps: the current proof process cannot externally terminate a stalled initial database connection, its timeout fixtures cannot establish an exact wall-clock millisecond boundary, its cold/warm labels do not prove isolated cold state, and its memory peak is contaminated by prior work in the same process.

This document corrects those planning gaps. On 2026-07-18 the Owner accepted its runtime-evidence design choices, and the [synthetic evidence execution package](finance-accounting-cycle2-gl-tb-synthetic-evidence-execution-package-2026-07-17.md) is reconciled to those later decisions in the same documentation-only task. The [current harness](../../erp_workspace_ui/tests/test_finance_gl_trial_balance_source_proof.py) remains unchanged. Acceptance authorizes planning of a later controller-and-harness source-authoring gate only; it does not authorize code authoring, numeric values, synthetic execution, or a runtime gate.

The accepted constraints remain controlling:

- `gl_reconstructed` is the sole synthetic source-proof candidate.
- The proof remains internal, synthetic, read-only, aggregate-only, single-company, and without HTTP, CORS inspection, Finance-to-AI access, accounting authority, or accounting execution.
- Native General Ledger, native Trial Balance, Query Report passthrough, ACB/cache authority, and silent fallback remain rejected.
- Cancellation, close/reopen, frozen-period control, audit certification, mutation, and execution claims remain deferred.
- Sales, Procurement, Warehouse, Finance Cycle 1, Shared UI, routing, registries, governance, AI Assistant, and all live environments remain outside this design and protected.

## 2. Frozen source baseline

| Item | Frozen planning evidence |
|---|---|
| Repository | `/home/deploy/erp-projects/erpai_project1_erpnext_ui_design` |
| Branch | `feature/erpnext-ui-design` |
| Local `HEAD` and upstream | `33159a54477e450eb4bd9996f747c0d626d2182f` |
| Ahead/behind | `0/0` |
| Index at intake | empty |
| Current harness SHA-256 | `c8d0bb0556f9abb04e1be69c1d67a7f92c4ed37a64d8270d84339ad590e9cea5` |
| Current harness status | untracked design candidate; not executable authority |

The current hash binds this amendment's review of the stopped candidate only. Synthetic execution requires a later committed harness and controller, an Owner-accepted source `HEAD`, blob identities, and new SHA-256 values. Any source change invalidates the current binding.

## 3. Findings that require the amendment

### 3.1 Blockers before synthetic execution

1. Before this reconciliation, the accepted package used an in-container `compose exec` proof command and banned helper code. The reconciled package now requires the accepted source-controlled host controller, but the controller has not been authored or authorized.
2. Before this reconciliation, the package applied limit-minus-one, exact-limit, and limit-plus-one to every numeric limit, including millisecond timeouts. The reconciled package now keeps exact boundaries only for deterministic workload units and treats statement/request ceilings independently, but no numeric ceiling is approved.
3. The harness remains uncommitted while the package requires committed source identity before execution.

### 3.2 High findings in the current design

1. The harness constructs its strict MariaDB connection before its later request-deadline assertions; a blocked initial connection is outside its in-process checks.
2. The current database-delay and Python-delay fixtures show eventual timeout behavior, not an exact causal boundary around the configured millisecond.
3. The current cold/warm benchmark is first-read versus repeat-read inside one long-lived test process. It does not isolate application process, Redis state, database buffer state, or prior point history.
4. `ru_maxrss` and the current shared-process memory measurements are lifetime peaks; later points can inherit an earlier point's peak.
5. Harness files are finalized individually. A hard kill can leave a mixed set of partial and final files; those files cannot be promoted as one complete evidence set.
6. The package's current evidence-manifest and teardown-receipt relationship can become circular if each retained artifact is required to cover the other.

### 3.3 Medium findings and costs

- A reviewed host controller has narrow but powerful Docker lifecycle authority and requires an exact argument/resource allowlist.
- A complete disposable stack per workload-point envelope has high setup and evidence cost.
- cgroup v2 becomes a required host capability for closure-grade memory evidence.
- Failure evidence is intentionally generic; diagnosis may require a separately approved rerun.
- A fresh database container cannot prove a cold host page cache.

No new accounting-semantic, role, company-scope, identity, or execution-authority finding was introduced by the accepted design.

## 4. Accepted Main Control design

The Owner accepts a source-reviewed host controller plus one-shot proof containers. The controller is orchestration and evidence-control code, not a second accounting proof candidate. The existing harness remains the sole source of accounting, permission, snapshot, workload, and leakage assertions.

The later controller candidate is:

`impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/tests/finance_gl_trial_balance_evidence_controller.py`

It must be standard-library-only, executed on the dedicated synthetic host by one named environment owner, and kept outside every proof container and synthetic network. The Docker socket must never be mounted into a container. The controller must never import application runtime code or implement accounting logic.

An ephemeral, execution-time-only controller was considered but is not recommended: even with a hash, it would lack normal source review and committed source-to-execution traceability. A plain shell `timeout` around `compose exec` is rejected because it can terminate only the Docker client while leaving the in-container process alive. A Docker-socket sidecar is rejected because it creates a root-equivalent in-container authority surface.

## 5. External hard-timeout ownership

### 5.1 Sole owner and lifecycle

One named environment owner invokes the reviewed host controller once. The controller remains the parent lifecycle authority from preflight through final absence proof:

`preflight -> point create -> fixture seed/seal -> state reset -> runner create -> measure -> finalize -> point teardown -> absence proof -> next point -> run synthesis -> final teardown -> final absence proof`

The controller launches every child command as an exact argument array with no shell. It uses an absolute monotonic clock and manifest-defined, Owner-approved ceilings. Every Docker client call also has a bounded controller wait. Killing or timing out a Docker client is not itself accepted as proof that a runner stopped.

The controller must create the exactly named and labelled one-shot runner container before starting the harness. It then observes that container directly. Its deadline begins before the runner starts, so it covers:

- application startup and imports;
- site initialization and the first database connection;
- the complete candidate request;
- harness evidence finalization and terminal seal creation;
- runner exit and controller validation.

On deadline expiry the controller terminates the exact runner container, records only sanitized state, rejects all runner-owned evidence, and enters teardown in `finally`. Normal termination may first use an Owner-approved graceful stop; the independently enforced hard stop uses the exact container identity and `SIGKILL` if it remains running. Exit code `137` alone is never causal evidence.

### 5.2 Independent deadline classes

No value is selected in this amendment. A later execution manifest must freeze distinct Owner-approved values and units for:

- `<SETUP_CEILING>`;
- `<POINT_REQUEST_CEILING>`;
- `<EVIDENCE_FINALIZATION_CEILING>`;
- `<POINT_TOTAL_CEILING>`;
- `<PACKAGE_TOTAL_CEILING>`;
- `<TERM_TO_KILL_GRACE>`;
- `<NORMAL_TEARDOWN_CEILING>`;
- `<RECOVERY_TEARDOWN_CEILING>`;
- `<DOCKER_CLIENT_CEILING>`.

The package ceiling does not kill the controller before cleanup. It stops new work and forces the controller into its bounded teardown state. If the Docker daemon is unavailable or exact absence cannot be proven, the controller records `teardown_unverified`, retains only hashed resource identities, and stops. It never claims successful teardown or uses broad cleanup.

### 5.3 Crash recovery

Recovery may use only the same committed controller and frozen manifest. It may inspect and remove only exact resources whose names, IDs, Compose project, and run/point labels all match the manifest. Uncertain identity stops cleanup. Recovery does not resume proof execution; it only completes bounded teardown and absence evidence.

## 6. Causal timeout classifications

Timeout evidence is an intersection of independent signals, not an inference from elapsed time or an exit code.

### 6.1 Database statement timeout

A result may be classified `database_statement_timeout` only when all are true:

- the session's configured statement ceiling is set and read back exactly;
- the deterministic server-side fault is entered;
- MariaDB returns the pinned statement-timeout class/error `1969`, with its approved status counter transition;
- the runner exits normally, is not OOM-killed, and the external watchdog did not fire;
- the affected connection is discarded;
- the candidate serializer committed zero bytes and no candidate response was sealed;
- the retained record contains only the generic timeout class, hashes, counts, and timing metadata, not raw SQL or error text.

### 6.2 Initial-connection watchdog timeout

The accepted future fixture uses a controller/harness handshake and the exact synthetic database container:

1. A dedicated harness fault mode atomically emits a sanitized `pre_connect_ready` marker immediately before opening a new initial database connection, then waits on a controller gate.
2. The controller verifies the marker, pauses only the exact point-scoped synthetic `db-primary` container, and releases the gate.
3. The harness attempts the real initial connection to the now-paused database.
4. The external point deadline expires and the controller terminates the exact runner.
5. Cleanup unpauses the exact database container before normal point teardown; failure to unpause moves directly to exact-ID recovery cleanup.

This fixture is accepted only if the marker hash exists, the controller deadline expires, the controller's exact kill action succeeds, the runner is not OOM-killed, no MariaDB statement-timeout marker exists, and no candidate output or final seal exists. It proves that the external owner covers the connection boundary; it does not claim a precise driver timeout.

Alternative synthetic barriers before connection were considered. They can prove controller reach but not a stalled real connection. A network fault proxy or `NET_ADMIN` was rejected because it expands topology and privilege. The Owner accepts pausing only the exact disposable synthetic database as the bounded design; authoring and execution remain separately gated.

### 6.3 Request and finalization watchdog timeouts

Separate source-reviewed harness fault modes atomically emit `request_block_entered` or `finalization_block_entered` and then wait on an intentionally unreleased synthetic control event. The controller terminates the exact one-shot runner at the matching ceiling. Classification requires the expected marker, a controller-owned monotonic deadline event, exact termination evidence, no DB-timeout signal, no OOM, and no promoted output.

Missing, dual, contradictory, or ambiguous signals produce `timeout_evidence_invalid`. They are never silently reclassified.

### 6.4 Zero partial output

Each subrun writes only to its unique, point-local staging volume. The harness writes a terminal `point-complete.json` last, after final filenames, canonical parsing, canary scans, and hashes succeed. The controller promotes a point only after normal runner exit and validation of the terminal seal.

Any timeout, hard kill, `.partial` file, unexpected file, missing seal, symlink, hardlink, noncanonical document, forbidden key, canary match, or hash mismatch causes the entire subrun staging volume to be discarded. Only a controller-owned fixed-schema timeout record is retained. Raw stdout/stderr may exist only in bounded transient controller storage for scanning and must be discarded; Docker logs, environment, commands, SQL, errors, identities, and financial values are never retained.

## 7. Deterministic boundary amendment

### 7.1 Required replacement

The canonical package's exact millisecond limit-minus-one/exact-limit/limit-plus-one rule must be replaced for time limits. MariaDB states that statement timeouts are checked at intervals and an interrupted statement may run longer than the configured value. Process scheduling, container startup, and timer wake-up add further nondeterminism. A ±1 ms acceptance rule would create false failures; a tolerance band would invent a policy value that has no accepted accounting or runtime basis.

The Owner accepts the following replacement:

- retain exact minus-one/exact/plus-one evidence for discrete deterministic caps such as accounts, dates/days, eligible GL rows, response objects, canonical UTF-8 bytes, active dimensions, and approved retry count;
- define a deterministic workload boundary independently of time;
- freeze each timeout configuration and read it back exactly;
- prove an ordinary under-ceiling control completes without either timeout owner firing, without asserting proximity to the ceiling;
- prove a deterministic server overrun produces MariaDB error `1969` while the external watchdog does not fire;
- prove deterministic non-returning connection/request/finalization barriers are terminated by the external watchdog with no sealed output;
- record observed latency for evidence and later budget selection, but make no exact kill-latency or maximum-lateness claim.

The timeout ceiling is a safety limit, not a precision performance boundary.

### 7.2 How later numeric values are derived

No numeric timeout, retry, workload, memory, or sampling value is introduced here. A later, separately approved synthetic derivation pass must:

1. execute the accepted discrete workload coordinates across isolated cold, warm, and concurrent variants;
2. retain canonical observed distributions and resource peaks without selecting a cap;
3. compare the evidence with Owner-supplied business-response, host-resource, and evidence-cost budgets;
4. propose exact workload caps and independent ceilings with their derivation hashes;
5. obtain explicit Owner approval before freezing them in the execution manifest;
6. rerun the exact approved limit-minus-one/exact/plus-one workload cases and the causal timeout fixtures.

No automatic interpolation, percentile, hidden safety margin, or observed maximum becomes authority.

## 8. State taxonomy

| State | Exact meaning | What is not claimed |
|---|---|---|
| Fresh application process | A new one-shot runner container, PID namespace, Python/Frappe process, writable layer, and cgroup created after fixture seal; no prior candidate import or read in that process. | Not a cold Redis, database buffer, or host cache by itself. |
| Cold application/cache namespace | Fresh application process plus newly recreated point-specific Redis services/namespaces after site creation and fixture seeding; approved Redis databases have sanitized zero key counts before measurement. | No key names or values; no host page-cache claim. |
| Warm repeat state | A new measured runner process/cgroup reads the unchanged sealed fixture after an exact primer/cold read has populated the same point Redis namespaces and MariaDB process/buffer. | Not same-process Python-cache warmth. Any same-process diagnostic is qualitative and cannot derive caps. |
| New database-buffer state | After fixture seal, MariaDB is cleanly recreated over the same point volume with buffer-pool dump-at-shutdown and load-at-startup disabled; no business-table read occurs before the measured cold request. | Does not prove cold Linux host filesystem/page cache. |
| Primed database-buffer state | The same MariaDB process and unchanged sealed fixture immediately after the exact approved primer/cold request. | Does not prove application-process warmth. |
| Host page-cache state | Explicitly `unproven` in the accepted container design. | No cold-host or cold-storage claim. |

## 9. Isolation unit and cold/warm sequence

The accepted unit is one complete disposable stack per logical workload-point envelope, run sequentially. The envelope contains the discrete workload coordinate and its cold, warm, and where required concurrent variants.

For each envelope the controller must:

1. create a unique Compose project, internal network, database, site, Redis stores, volumes, and point labels from the frozen manifest;
2. deterministically seed the synthetic fixture;
3. write and seal a normalized fixture-provenance manifest and mutation sentinel;
4. recreate MariaDB over the same sealed synthetic volume with approved buffer settings;
5. recreate the Redis services/stores and record only sanitized zero key counts;
6. create a new cold runner container/cgroup and run the cold request;
7. preserve the unchanged DB/site fixture and warmed Redis/DB state;
8. create a new warm runner container/cgroup and run the warm request;
9. create a separate concurrency runner/cgroup if that variant is in the approved workload plan;
10. verify the before/after fixture hash and mutation sentinel are identical;
11. tear down the entire point stack and prove absence before the next envelope.

No database export, copied live configuration, operational data, live mount, repository mount, snapshot from live, or cross-point volume reuse is allowed. A shared stack across points is cheaper but rejected for closure-quality evidence because prior Redis, DB-buffer, and process history would contaminate causality. A complete stack per variant is unnecessary and would break the natural cold/warm pair unless a separately reviewed deterministic clone mechanism were introduced.

Host page-cache coldness remains explicitly unproven. VM-level isolation is deferred and is not required at this stage; if later evidence shows the accepted cold-state definition is insufficient, a separate Owner gate must decide whether to require a dedicated disposable VM and new block volume per point. Host-wide cache dropping, privileged cache operations, and shared-host coldness claims remain prohibited.

## 10. Fixture provenance

Cold and warm variants must bind to the same logical fixture through:

- committed harness `HEAD`, Git blob, and SHA-256;
- committed controller `HEAD`, Git blob, and SHA-256;
- immutable backend/database/Redis image digests;
- Compose and execution-manifest SHA-256;
- exact point/workload input manifest hash;
- deterministic seed identifier, company, base currency, fiscal dates, Finance Book cohort, dimensions posture, chart and GL fixture counts;
- normalized fixture-manifest SHA-256, table-count/checksum evidence, and pre/post mutation-sentinel SHA-256;
- exact DB/Redis reset-state records and container identity hashes.

Only normalized hashes, allowed counts, enums, and synthetic values may be retained. Any fixture-provenance mismatch stops the point; it is never averaged, repaired, or silently regenerated inside a measured subrun.

## 11. Per-point memory telemetry

### 11.1 Authoritative method

Every measured cold, warm, and concurrent variant gets a new one-shot runner container and new cgroup v2 hierarchy. The host controller containment-checks the exact runner's cgroup and records:

- `point_id` and `variant`;
- controller, harness, manifest, Compose, fixture, workload, and image hashes;
- hashed container ID and hashed cgroup path;
- clock source and monotonic measurement-window start/end;
- `units = bytes`;
- baseline `memory.current` and baseline `memory.peak` before the candidate;
- periodic `memory.current` samples at `<MEMORY_SAMPLE_INTERVAL>`;
- final `memory.current`, cgroup-lifetime `memory.peak`, and maximum sampled current;
- `memory.max` and the approved expected budget class;
- before/after deltas for `memory.events.local`, including `high`, `max`, `oom`, and `oom_kill`;
- optional swap current/peak only if separately supported and approved;
- sample count and SHA-256 of the canonical sample vector;
- expected/actual pass class, runner exit class, and Docker `OOMKilled` state.

The absolute peak in the new cgroup is authoritative. Delta-from-baseline is informational only. Engine statistics may corroborate the series but cannot replace `memory.peak`, because sampling can miss a short peak. `ru_maxrss`, `tracemalloc`, and process-lifetime history may remain diagnostics but cannot select or close a memory cap.

If cgroup v2 `memory.peak` and `memory.events.local` are unavailable or cannot be attributed to the exact container, the point stops. There is no silent fallback. A later Owner decision may select a different pinned telemetry provider under a new review.

### 11.2 Numeric derivation

The sampling interval, container memory ceiling, expected peak, and workload cap remain placeholders. Later isolated synthetic observations plus the Owner's resource budget produce a proposal; the Owner must approve every numeric value before it enters a materialized manifest. Killed, OOM, unsealed, or telemetry-incomplete points cannot derive a cap.

## 12. Evidence integrity and manifest graph

The future evidence graph must avoid circular hashes:

1. `proof-evidence-manifest.sha256` covers every accepted point, controller, harness, fixture, workload, permission, accounting, leakage, isolation, watchdog, and memory artifact except itself.
2. `teardown-receipt.json` references the proof-manifest hash and records exact post-run absence checks.
3. `final-evidence-manifest.sha256` covers the proof manifest, teardown receipt, and all retained artifacts except itself.
4. Main Control reports the final root SHA-256 out of band in the closure receipt.

Point evidence is promoted from same-filesystem staging by atomic directory rename only after the terminal seal validates. Controller records are append-free atomic files or hash-chained fixed-schema JSONL created without overwriting an existing run. A killed or incomplete runner contributes no harness artifact to the proof manifest.

## 13. Deterministic teardown and orphan policy

Teardown always runs in controller `finally`:

1. stop the exact runner if still present;
2. unpause the exact synthetic database if the connection-stall fixture paused it;
3. run exact-project Compose down with volumes and orphans under the approved ceiling;
4. list resources by exact run ID, point ID, Compose project, and manifest-recorded identities;
5. inspect only fixed sanitized identity/state/label fields;
6. if a verified remnant exists, remove exact IDs in dependency order: containers, then networks, then volumes;
7. repeat exact absence scans;
8. write the teardown receipt and final evidence manifest.

No prune, wildcard, image removal, global cache action, unrelated project cleanup, Git cleanup, live-tree path, or unverified resource removal is allowed. Failure to prove absence keeps execution stopped and records `teardown_unverified`.

## 14. Exact later file allowlists

These are planning allowlists, not current write authority.

### 14.1 Later repository authoring gate

Exactly these paths may be candidates only under the later separately authorized source-authoring gate:

1. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/tests/test_finance_gl_trial_balance_source_proof.py`
2. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/tests/finance_gl_trial_balance_evidence_controller.py`
3. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/finance-accounting-cycle2-gl-tb-synthetic-evidence-execution-package-2026-07-17.md`
4. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/finance-accounting-cycle2-gl-tb-runtime-evidence-design-amendment-2026-07-18.md`
5. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/README.md`

The exact code-authoring scope is the first two paths. The three documentation paths may receive factual traceability updates only. The controller is host test-support code; the existing test file remains the sole accounting proof harness. Runtime, UI, routes, registries, hooks, manifests, roles, permissions, AI Assistant, and live files are excluded.

### 14.2 Future disposable run root

The manifest must resolve every placeholder to one exact contained path before approval. The allowed top-level inputs are:

- `<RUN_ROOT>/compose.yaml`
- `<RUN_ROOT>/execution-manifest.json`
- `<RUN_ROOT>/workload-plan.json`
- `<RUN_ROOT>/control/controller-state.json`

Transient, never-retained inputs/staging are:

- `<RUN_ROOT>/control/<SUBRUN_ID>/ready.json`
- `<RUN_ROOT>/staging/<SUBRUN_ID>/`
- bounded transient stdout/stderr scan files owned by the controller

The retained evidence allowlist is:

- `<RUN_ROOT>/evidence/controller-receipt.json`
- `<RUN_ROOT>/evidence/controller-events.jsonl`
- `<RUN_ROOT>/evidence/watchdog-results.jsonl`
- `<RUN_ROOT>/evidence/isolation-results.jsonl`
- `<RUN_ROOT>/evidence/memory-results.jsonl`
- `<RUN_ROOT>/evidence/point-index.json`
- `<RUN_ROOT>/evidence/review-disposition.json`
- `<RUN_ROOT>/evidence/proof-evidence-manifest.sha256`
- `<RUN_ROOT>/evidence/teardown-receipt.json`
- `<RUN_ROOT>/evidence/final-evidence-manifest.sha256`
- `<RUN_ROOT>/evidence/points/<POINT_ID>/provenance.json`
- `<RUN_ROOT>/evidence/points/<POINT_ID>/fixture-manifest.json`
- `<RUN_ROOT>/evidence/points/<POINT_ID>/accounting-results.jsonl`
- `<RUN_ROOT>/evidence/points/<POINT_ID>/permission-results.jsonl`
- `<RUN_ROOT>/evidence/points/<POINT_ID>/snapshot-results.jsonl`
- `<RUN_ROOT>/evidence/points/<POINT_ID>/workload-results.jsonl`
- `<RUN_ROOT>/evidence/points/<POINT_ID>/leakage-results.jsonl`
- `<RUN_ROOT>/evidence/points/<POINT_ID>/expected-actual-diff.jsonl`
- `<RUN_ROOT>/evidence/points/<POINT_ID>/mutation-sentinel.json`
- `<RUN_ROOT>/evidence/points/<POINT_ID>/junit.xml`
- `<RUN_ROOT>/evidence/points/<POINT_ID>/point-complete.json`

No `.env`, SQL dump, raw log, copied site configuration, secret, identity-bearing output, financial export, or host/source/live bind mount is allowed.

## 15. Exact future command allowlists

These templates are not execution authority. Before any run, placeholders must be expanded to a materialized argument-vector manifest, hashes frozen, command compatibility proven, and the complete list approved by the Owner. No shell interpretation is permitted.

### 15.1 Sole Owner-facing controller commands

```text
/usr/bin/python3 -I <CONTROLLER_PATH> preflight --manifest <RUN_ROOT>/execution-manifest.json
/usr/bin/python3 -I <CONTROLLER_PATH> execute --manifest <RUN_ROOT>/execution-manifest.json
/usr/bin/python3 -I <CONTROLLER_PATH> recover-teardown --manifest <RUN_ROOT>/execution-manifest.json
```

`execute` owns point finalization and run finalization; no free-form command passthrough is allowed. `recover-teardown` cannot create or run a proof.

### 15.2 Controller child-command classes

Only materialized forms of these classes may be used:

```text
git -C <SOURCE_ROOT> rev-parse --show-toplevel
git -C <SOURCE_ROOT> rev-parse HEAD
git -C <SOURCE_ROOT> rev-parse @{upstream}
git -C <SOURCE_ROOT> rev-list --left-right --count HEAD...@{upstream}
git -C <SOURCE_ROOT> diff --cached --name-only
sha256sum <EXACT_ALLOWED_SOURCE_OR_RUN_ROOT_FILE> [...]
docker version --format <FIXED_SANITIZED_FORMAT>
docker image inspect --format <FIXED_SANITIZED_FORMAT> <EXACT_DIGEST>
docker compose --project-name <POINT_PROJECT> --file <RUN_ROOT>/compose.yaml config --quiet
docker compose --project-name <POINT_PROJECT> --file <RUN_ROOT>/compose.yaml config --images
docker compose --project-name <POINT_PROJECT> --file <RUN_ROOT>/compose.yaml up --detach --pull never --wait --wait-timeout <SETUP_CEILING> <EXACT_SETUP_SERVICES>
docker compose --project-name <POINT_PROJECT> --file <RUN_ROOT>/compose.yaml run --rm --no-deps <EXACT_SETUP_SERVICE> <EXACT_SETUP_ARGV>
docker compose --project-name <POINT_PROJECT> --file <RUN_ROOT>/compose.yaml stop --timeout <TERM_TO_KILL_GRACE> <EXACT_DB_OR_REDIS_SERVICE>
docker compose --project-name <POINT_PROJECT> --file <RUN_ROOT>/compose.yaml rm --force --stop <EXACT_DB_OR_REDIS_SERVICE>
docker compose --project-name <POINT_PROJECT> --file <RUN_ROOT>/compose.yaml up --detach --force-recreate --no-deps --pull never <EXACT_DB_OR_REDIS_SERVICE>
docker compose --project-name <POINT_PROJECT> --file <RUN_ROOT>/compose.yaml run --detach --no-deps --pull never --name <POINT_CONTAINER> --label <EXACT_RUN_LABEL> --label <EXACT_POINT_LABEL> <TEST_RUNNER_SERVICE> <EXACT_HARNESS_ARGV>
docker container wait <POINT_CONTAINER>
docker container inspect --format <FIXED_SANITIZED_FORMAT> <POINT_CONTAINER>
docker container stop --timeout <TERM_TO_KILL_GRACE> <POINT_CONTAINER>
docker container kill --signal KILL <POINT_CONTAINER>
docker container pause <EXACT_DB_CONTAINER>
docker container unpause <EXACT_DB_CONTAINER>
docker container cp <POINT_CONTAINER>:<EXACT_SEALED_EVIDENCE_PATH> <EXACT_CONTROLLER_STAGING_PATH>
docker container rm --force --volumes <POINT_CONTAINER>
docker compose --project-name <POINT_PROJECT> --file <RUN_ROOT>/compose.yaml exec --no-TTY <EXACT_REDIS_SERVICE> redis-cli --raw DBSIZE
docker compose --project-name <POINT_PROJECT> --file <RUN_ROOT>/compose.yaml down --volumes --remove-orphans --timeout <NORMAL_TEARDOWN_CEILING>
docker container ls --all --filter <EXACT_RUN_LABEL_FILTER> --format <FIXED_ID_FORMAT>
docker network ls --filter <EXACT_RUN_LABEL_FILTER> --format <FIXED_ID_FORMAT>
docker volume ls --filter <EXACT_RUN_LABEL_FILTER> --format <FIXED_ID_FORMAT>
docker container rm --force --volumes <EXACT_VERIFIED_CONTAINER_ID> [...]
docker network rm <EXACT_VERIFIED_NETWORK_ID> [...]
docker volume rm <EXACT_VERIFIED_VOLUME_ID> [...]
```

The materialized list must also preserve the accepted site creation, app installation, scheduler-disable, and fixture preparation commands from the canonical package. Before those commands are executable authority, a read-only compatibility gate must fingerprint the pinned Frappe `bench run-tests` implementation and prove that the selected test-record and JUnit arguments do not skip the run or lose JUnit output.

Prohibited command classes include arbitrary shell, `docker exec` into the proof runner, `docker logs`, unfiltered events/inspect, environment or command inspection, image pull/build, systemd mutation, Docker socket mounts, added external networks, network fault proxies, `NET_ADMIN`, prune, wildcard cleanup, source cleanup, live paths, SQL clients, Bench migration/cache/metadata operations, and accounting actions.

## 16. Protection boundaries

Before and after every later authoring or execution gate, Main Control must compare status and SHA-256 for the four exclusions and stop on drift:

1. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py` — `01668e175610d9d090ea51018badbde8b021103afe13ed878782a58b8ce3b224`
2. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/browser_supplier_payables_fixture_diagnostic.py` — `d9822184b26f3c1ebaf5b93663b1f6c3a495b6482f013092d955748dfdf963c5`
3. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/ui_smoke/sales_final_acceptance_audit.js` — `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
4. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/a.out` — `0063411e61152850243132aa87ef12844a8724adb671bf4f38793bcd2b1ce339`

They must remain unstaged and must never be cleaned, stashed, reset, copied, mounted, or incorporated into evidence. The repository and live tree must never be mounted into the disposable stack. All protected workspace/runtime boundaries listed in section 1 remain unchanged.

## 17. Owner acceptance record and remaining gates

On 2026-07-18 the Owner accepted the following design choices:

1. Exact wall-clock millisecond minus-one/exact/plus-one assertions are superseded by exact discrete workload-unit boundaries plus independently enforced statement and request ceilings.
2. The future external owner is a source-controlled host controller with one-shot runner, watchdog, evidence-promotion, recovery, and teardown authority limited by the exact allowlists.
3. The initial-connection stall fixture may pause only the exact disposable point-scoped synthetic database after the sanitized ready-marker handshake.
4. Every workload-point envelope receives one complete disposable stack and runs sequentially.
5. Closure-grade cold state requires a fresh runner/cgroup, reset Redis state, reset MariaDB process/buffer state, and sealed identical fixture provenance; host page-cache coldness remains explicitly unproven.
6. VM-level isolation is not required now and remains deferred unless later evidence demonstrates that the accepted cold-state definition is insufficient.
7. Authoritative warm evidence uses a fresh runner after a controlled primer against unchanged warmed Redis/DB state; same-process warm evidence is diagnostic only and cannot derive caps.
8. cgroup v2 `memory.current`, `memory.peak`, and `memory.events.local` are the authoritative per-variant memory sources, with no silent fallback.
9. Killed or incomplete subruns are discard-only; no harness-owned artifact from them may be promoted.
10. The non-circular proof-manifest, teardown-receipt, and final-manifest graph plus atomic point promotion are accepted.
11. Recovery teardown may remove only exact IDs whose project and approved run/point labels match the frozen manifest.
12. The numeric-derivation method is accepted for design only; no numeric timeout, workload, memory, retry, concurrency, or sampling value is approved.
13. Planning of the later controller-and-harness source-authoring gate is approved; code authoring and execution are not.

These decisions supersede the previously unresolved alternatives in this amendment. Shell timeouts, ephemeral-only controller authority, network fault proxies, shared point stacks, first/repeat evidence in one process as cold proof, process-lifetime memory as point authority, partial evidence promotion, circular manifests, broad cleanup, and automatic numeric inference remain rejected. HTTP/CORS inspection, Finance-to-AI access, the in-memory secret-channel implementation, live acceptance, and accounting execution remain deferred.

Owner acceptance supplies no numeric value and authorizes no code authoring, source publication, infrastructure, or synthetic execution. Remaining approvals are the later exact source-authoring gate, its bounded review and publication gates, the materialized execution inputs and numeric values, and the explicit synthetic-execution gate.

## 18. Independent review synthesis

Main Control ran one bounded review each for database/runtime determinism, security/information leakage, and release containment/teardown, followed by this single synthesis.

### Accepted

- External control must target an exact one-shot runner container, not a `compose exec` client or in-process timer.
- The millisecond ±1 rule must be replaced for time while discrete workload ±1 evidence remains.
- Statement timeout, external watchdog timeout, OOM, and ambiguous exit must be distinct outcomes.
- A complete new stack per workload-point envelope, Redis reset after fixture creation, new runner cgroup per measured variant, and an explicit `host_page_cache = unproven` claim are required.
- cgroup v2 peak/event evidence, zero-partial-output promotion, exact-ID teardown, and a non-circular final manifest are required.
- The current harness accounting, permission, release-containment, and static passes remain accepted; runtime-impacting fault/telemetry changes require only bounded targeted rereview.

### Accepted with Main Control modification

- Reviewers agreed on a hash-bound host controller but differed on storage. Main Control selects a later source-controlled test-support controller rather than an ephemeral-only helper because committed review and source-to-execution binding outweigh the one-file increase. It remains outside runtime and is not a second accounting harness.
- Reviewers described warm repeat as either the same process or a fresh process. Main Control selects a fresh authoritative warm runner for uncontaminated memory and permits a same-process warm diagnostic only if it cannot derive caps.

The Owner adopted both Main Control modifications as the canonical planning posture.

### Rejected

- Shell timeout, in-process alarm/thread as sole authority, DB timeout as request timeout, exit `137` alone, raw Docker logs, arbitrary environment/command inspection, timeout tolerance bands, current first/repeat labels as cold evidence, shared runner memory, Docker-stat sampling as peak authority, host cache dropping, socket sidecars, network proxies, broad cleanup, and open-ended review loops.

### Deferred

- Every numeric ceiling, workload cap, memory budget, retry cap, concurrency level, sampling interval, image digest, and materialized command hash.
- The exact environment owner/host identity and cgroup-v2 capability result.
- VM/new-block-volume isolation and any host page-cache coldness claim, unless later evidence demonstrates that the accepted cold-state definition is insufficient.
- The read-only Frappe test-command compatibility fingerprint.
- Source authoring, publication, synthetic infrastructure, execution, and any diagnostic rerun.
- HTTP/CORS, Finance-to-AI, secret-channel expansion, live acceptance, and accounting execution.

This documentation reconciliation creates no new accounting-semantic, permission, information-leakage, or release finding.

## 19. Exact later amendments required

The design choices in section 17 are resolved. A separate explicit Owner authorization is still required before the exact controller-and-harness source-authoring gate may begin. That later gate may:

1. add the reviewed host controller under the exact test-support path;
2. amend the sole harness with fixed-schema ready markers, deterministic fault modes, fixture prepare/measure separation, state-isolation receipts, sealed point finalization, and cgroup evidence hooks without changing accounting semantics;
3. update the canonical package, this amendment and the README only as required for factual source-authoring traceability, without changing the accepted architecture;
4. run bounded database/runtime, security/leakage, and release reviews only on those code changes;
5. publish committed source and freeze new source hashes under a separate Owner gate;
6. obtain a separate execution authorization with materialized commands, immutable images, host capability evidence, environment owner, and approved numeric budgets.

## 20. Validation and no-action receipt

This reconciliation pass verifies the repository baseline, reconciled package, README index, current harness hash, current worktree/index containment, and the four exclusion hashes. It performs documentation whitespace/reference checks and a final three-document candidate-scope check after writing.

No harness or runtime file was modified. No test, Bench command, Docker command, query, fixture, benchmark, synthetic environment, network, database, site, cache, container, volume, migration, metadata operation, permission change, protected gate, accounting action, live access, staging, commit, or push was performed.

## 21. Authoritative references

- [MariaDB statement timeout behavior](https://mariadb.com/docs/server/ha-and-performance/optimization-and-tuning/query-optimizations/aborting-statements)
- [MariaDB error 1969](https://mariadb.com/docs/server/reference/error-codes/mariadb-error-codes-1900-to-1999)
- [MariaDB InnoDB buffer pool](https://mariadb.com/docs/server/server-usage/storage-engines/innodb/innodb-buffer-pool)
- [Docker container wait](https://docs.docker.com/reference/cli/docker/container/wait/)
- [Docker container kill](https://docs.docker.com/reference/cli/docker/container/kill/)
- [Docker container stop](https://docs.docker.com/reference/cli/docker/container/stop/)
- [Docker Compose down](https://docs.docker.com/reference/cli/docker/compose/down/)
- [Docker runtime metrics](https://docs.docker.com/engine/containers/runmetrics/)
- [Linux cgroup v2 memory controller](https://docs.kernel.org/admin-guide/cgroup-v2.html)
- [GNU timeout limitations](https://www.gnu.org/software/coreutils/manual/html_node/timeout-invocation.html)
- [Redis `DBSIZE`](https://redis.io/docs/latest/commands/dbsize/)
