# Finance & Accounting Cycle 2 GL / Trial Balance Controller-Runner Control Plane and Source Delivery Amendment

**Date:** 2026-07-18

**Authority:** Main Control v2

**Repository:** `/home/deploy/erp-projects/erpai_project1_erpnext_ui_design`

**Branch:** `feature/erpnext-ui-design`

**Planning baseline:** `ca9c14e00c0fecee81aa35004bdfa5c07caf393e`

**Decision:** `controller_runner_control_plane_design_reconciled_for_docs_staging`

**Owner status:** all control-plane, terminal-seal, measured-window, immutable-delivery, image-identity, secret-channel and exact-ID teardown decisions in this amendment are accepted as the canonical planning posture

**Posture:** Planning and documentation only. Source authoring, image materialization, synthetic execution, numeric-limit selection, staging, commit, push, runtime work, HTTP, Finance-to-AI access, live action and accounting execution remain unapproved.

## 1. Purpose and authority

The controlled GL / Trial Balance controller-and-harness source-authoring gate stopped safely as `stopped_for_source_authoring_gap` without changing source. The accepted runtime design required deterministic runner barriers, but the then-current topology, command allowlist and two-file authoring scope did not define:

- an authenticated-enough, fail-closed controller-to-runner release path;
- a pre-exit telemetry hold that the controller can release without losing terminal evidence;
- immutable and hash-verifiable harness delivery to one-shot runners; or
- secret-safe creation of the disposable Frappe site.

This amendment resolves those questions at architecture level only. The Owner accepts its one control transport, one terminal-seal owner, one immutable image-delivery method, one secret-injection design and exact four-file future source scope. The canonical package, prior runtime amendment and README are reconciled to those decisions in this documentation-only task. Source authoring still requires a separate explicit gate.

This amendment does not:

- authorize a controller, harness, Dockerfile or initializer edit;
- authorize an image build, pull, tag, registry push or cleanup;
- authorize a container, site, database, cache, network, volume, secret, fixture, benchmark or proof run;
- approve any numeric workload, row, byte, memory, timing, retry or concurrency limit;
- start C2B7, C2C, Finance Cycle 2 runtime work or any accounting execution;
- change `gl_reconstructed`, accounting equations, literal expectations, permissions, company authority, complete-chart authority, snapshot semantics, aggregate-only output, identity suppression or no-execution posture; or
- alter Sales, Procurement, Warehouse, Finance Cycle 1, Shared UI, routing, registries, governance, AI Assistant or live boundaries.

## 2. Controlling evidence and baseline

This amendment was synthesized from complete read-only inspection of:

1. [GL / Trial Balance Synthetic Evidence Execution Package](finance-accounting-cycle2-gl-tb-synthetic-evidence-execution-package-2026-07-17.md);
2. [GL / Trial Balance Runtime Evidence Design Amendment](finance-accounting-cycle2-gl-tb-runtime-evidence-design-amendment-2026-07-18.md);
3. [ERP UI customization documentation index](README.md); and
4. the current uncommitted harness candidate, read-only:
   `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/tests/test_finance_gl_trial_balance_source_proof.py`.

The verified planning baseline was:

| Evidence | Verified value |
| --- | --- |
| Branch | `feature/erpnext-ui-design` |
| Local HEAD | `ca9c14e00c0fecee81aa35004bdfa5c07caf393e` |
| Configured upstream | `origin/feature/erpnext-ui-design` |
| Upstream revision | `ca9c14e00c0fecee81aa35004bdfa5c07caf393e` |
| Ahead/behind | `0/0` |
| Git index | empty |
| Synthetic package pre-reconciliation SHA-256 | `e64ea82f6bafb47564f0067f6dd7d916cda895c4eb9f5f05ed58b46d41a9ed45` |
| Runtime amendment pre-reconciliation SHA-256 | `0362e0c91d421b4a0ad5dd4673ccbee4d7f52eabc86168aaf4b47b65f82296cb` |
| Control-plane amendment pre-reconciliation SHA-256 | `4332fb9eea8f0dcb9b16b98efe6f7ffac7071eb3ec07907138162c18fe8ac013` |
| README pre-reconciliation SHA-256 | `122487898771c55dce218734049c8e4de7150778bf15220c96515d935e6e6c35` |
| Harness SHA-256 | `c8d0bb0556f9abb04e1be69c1d67a7f92c4ed37a64d8270d84339ad590e9cea5` |
| Future controller, runner Dockerfile and site initializer | absent |

Current harness evidence relevant to this amendment:

- it contains no control-marker or signal-wait implementation;
- its evidence writer can finalize harness-owned files but cannot certify external cgroup telemetry, Docker exit/OOM state, controller validation or atomic promotion;
- its current workload memory observations are same-process diagnostics, not the accepted cgroup-v2 authority; and
- its current disposable-topology contract obtains a database-root credential from an environment value, which is incompatible with the required future secret boundary.

This task reconciles the canonical package, runtime amendment, this amendment and README to the accepted later decisions. The hashes above are pre-reconciliation fingerprints. Source authoring, image materialization and execution remain separately unapproved.

## 3. Preserved accounting, authority and protection boundaries

The control plane is outside the accounting data plane. It may coordinate only synthetic runner lifecycle, fixed barriers, exact database pause/unpause, controller deadlines, cgroup capture, evidence validation, promotion, recovery and teardown.

The following remain frozen:

- `gl_reconstructed` is the sole synthetic accounting-proof candidate.
- Raw-GL opening, movement, closing, hierarchy, balancing, fiscal-boundary, cancellation-canary and Finance Book cohort semantics remain unchanged.
- The complete-chart permission matrix, role separation, company scope, User Permission, dimension, Custom DocPerm, share, mask and custom-report-role denials remain unchanged.
- The harness remains the sole owner of accounting fixtures, literal expectations, permission fixtures, snapshot checks, workload generation, leakage canaries and mutation sentinels.
- Output remains internal, aggregate-only, identity-suppressed, read-only and fail-closed.
- No endpoint, report passthrough, list, form, export, download, print, email, notification, approval, mutation, close/reopen, cancellation, frozen-period action or accounting execution is introduced.
- HTTP and the deferred global CORS fingerprint remain outside scope.
- Finance-to-AI access and accounting authority remain unapproved.
- Host page-cache coldness remains explicitly unproven.
- VM-level and new-block-volume isolation remain deferred unless later evidence shows the accepted cold-state definition is inadequate.
- No workload or runtime numeric limit is selected here.

## 4. Main Control synthesis

The Owner-accepted bounded design is:

1. The runner writes a canonical, immutable, nonce-bound phase marker in its own disposable writable layer.
2. The host controller copies out exactly that marker from the exact full runner container ID and validates it as hostile tar input.
3. The controller durably records the intended external action and release transition.
4. The controller performs only the state-specific external action.
5. The controller sends `SIGUSR1` to the exact full runner ID.
6. The harness-bearing Python process, running as exec-form PID 1, synchronously consumes the signal with a blocked-signal `sigwait` boundary.
7. The runner acknowledges the release with the next immutable hash-chained marker.
8. For successful measured subruns, the runner blocks at `telemetry-ready.json` after sealing harness evidence.
9. The controller captures authoritative measured-window cgroup evidence, releases normal exit, verifies exit and OOM state, validates harness artifacts, writes `point-complete.json` last and promotes the point atomically.
10. Any killed, timed-out, OOM, incomplete, ambiguous, telemetry-unavailable or unsealed subrun is discard-only.

This design preserves no HTTP, no Redis/SQL control, no extra external network, no sidecar, no Docker socket mount, no general `docker exec`, no arbitrary copy-in and no shared mutable control volume.

The design has an explicit trust boundary: Unix signals carry no nonce or authenticated payload. Exact marker copy-out plus signal is acceptable only while one named environment owner has exclusive Docker-host mutation authority for the disposable project. Within that boundary, causal evidence is the combination of exact full-ID validation, one-use runner nonce commitment, immutable marker hash chain, durable controller state and the expected next marker or exit. If another Docker-authorized host process must be treated as hostile, this option is insufficient and a separately designed cryptographically authenticated control service would be required.

## 5. Controller-to-runner transport alternatives

| Option | Ownership and direction | Topology, files and commands | Authentication, replay and PID behavior | Permission, leakage, failure and teardown | Evidence cost, reversibility and boundary result |
| --- | --- | --- | --- | --- | --- |
| Exact marker copy-out plus exact Unix signal | Runner owns immutable marker; controller reads it. Controller owns action and one release signal to the exact runner. | No mount or extra service. Exact `docker container cp ... -` and `docker container kill --signal SIGUSR1` only. | Marker has one-use nonce commitment and hash chain. Controller binds it to the exact full ID. Runner must be exec-form PID 1 and use synchronous blocked-signal waiting. Signal itself is not authenticated. | No secret/data-plane channel. Host Docker authority remains powerful. Missing, stale, duplicate, reordered or ambiguous state discards. Runner writable layer and transient host marker copies are removed during exact teardown. | Lowest added topology and evidence cost. Fully removable. Preserves no HTTP/no extra network/no shared control mount. **Accepted for planning**, subject to the later read-only compatibility fingerprint. |
| Point-scoped control volume or named pipe | Controller writes release token; runner reads. Runner may write readiness into the same point-scoped surface. | Adds a shared mount and path contract. Requires file/pipe creation, permissions and mount inspection. | Can carry a nonce, but mutable shared state creates stale-file, replacement and replay surfaces. No PID signal requirement. | Expands host-file and mount authority; needs link/race containment and exact volume teardown. A controller crash may leave an apparently releasable token. | Deterministic fallback with higher review and evidence cost. Reversible after volume removal, but does not preserve the accepted no-control-mount boundary. |
| Dedicated control service or sidecar | Service owns authenticated request/release protocol. | Adds image, service, port or socket, health lifecycle and usually a network. | Can provide cryptographic authentication and ordered nonces. Does not require PID signal forwarding. | Adds credentials, protocol parser, logs, availability and teardown surfaces. It can contaminate workload isolation. | Highest source, topology and evidence cost. Reversible but broadens no-extra-service/no-extra-network boundaries. Rejected for the present threat model; reconsider only if exclusive Docker-host authority is unacceptable. |
| Container stdin | Controller holds an attached client and writes a release token; runner reads. | Requires long-lived attach plumbing and one-shot stdin ownership. | Token can bind a nonce. Attach reconnect and EOF semantics are ambiguous after controller failure. PID 1 must own or forward stdin. | Risks secret/control mixing and unbounded client output. Recovery cannot safely infer whether input was consumed. | Low file footprint but poor crash evidence and replay containment. Rejected. |
| Docker exec release | Controller starts an in-container process. | Adds `docker exec` process and command authority. | Exact argv can carry a nonce, but creates a second process outside the harness's control boundary. | Broad command-injection and environment-inspection surface; changes measured state; complicates teardown and provenance. | High containment cost and easy authority expansion. Rejected. |
| Docker copy-in release | Controller mutates the runner filesystem after creation. | Requires exact destination, tar/copy validation and a runner poller. | Can carry a nonce, but replay and replacement rules resemble a shared file. | Expands copy-in and mutation authority. A crash between copy and durable state is ambiguous. | Technically reversible with container removal, but inferior to a signal and rejected for release control. Reconsideration requires a separate redesign gate. |
| Redis or SQL channel | Controller writes data-plane state; runner reads. | Reuses or expands database/cache credentials, commands and connections. | Could bind a nonce but makes proof control dependent on the systems being paused/reset and measured. | Secret, permission, persistence, transaction and leakage risks; SQL cannot release the initial-connect fixture while the database is paused. | High contamination and reconciliation cost. Rejected. |
| HTTP or other network channel | Controller calls runner/service over a port. | Adds listener, route, port, network and authentication. | Can authenticate and order requests, but creates endpoint authority. | Conflicts with deferred HTTP/CORS and expands attack, logging and live-confusion surfaces. | High review and regression cost. Rejected. |
| Evidence-volume release file | Controller writes a token into the harness evidence mount. | Reuses a shared writable evidence surface. | Nonce is possible, but release state and proof state become mutually mutable. | Stale/replay, tampering and promotion-integrity risks. | Low apparent cost but breaks evidence ownership and no-shared-control-state boundaries. Rejected. |

Authoritative behavior supporting the accepted design:

- Docker sends a selected signal to the container's main process; shell-form wrappers do not automatically forward it. [Docker container kill](https://docs.docker.com/reference/cli/docker/container/kill/)
- `docker container cp ... -` produces a tar stream and can copy from running or stopped containers; therefore the controller must validate the archive and independently prove the runner is running. [Docker container cp](https://docs.docker.com/reference/cli/docker/container/cp/)
- Python delivers ordinary handlers on the main thread at later interpreter checkpoints, while POSIX signal masks and synchronous waiting are exposed through `pthread_sigmask` and `sigwait`. [Python signal documentation](https://docs.python.org/3/library/signal.html)

## 6. Exact transport trust and process contract

### 6.1 Exclusive-host authority

The marker/signal design is valid only when:

- one named environment owner is the sole process permitted to mutate the approved disposable Docker project;
- the controller is the only process permitted to send release or kill signals to its runners;
- no unreviewed Docker client, daemon plugin, socket-mounted container or host automation acts on the project;
- the controller validates full resource IDs, exact names, image IDs, creation/start identity and labels immediately around each marker copy and signal; and
- a signal without a matching validated marker and durable controller state never counts as evidence.

This is phase correlation and lifecycle containment, not cryptographic defense against a hostile Docker administrator.

### 6.2 PID and signal contract

The future derived image must use an exec-form entrypoint that makes the harness-bearing Python/Frappe test process PID 1. No shell wrapper is allowed.

Before source authoring, a pinned installed-source compatibility fingerprint must prove:

- the selected Frappe test invocation executes the harness in that same PID rather than spawning an unobserved child;
- the pinned base image and Frappe/Bench code do not reserve or depend on `SIGUSR1`;
- no thread is created before the harness blocks `SIGUSR1`; and
- JUnit and harness finalization remain available with the selected one-shot invocation.

The future harness must:

1. block `SIGUSR1` before any worker thread exists;
2. reject a pre-pending release signal before each ready marker;
3. permit only one outstanding release;
4. wait synchronously on the main test thread with `signal.sigwait`;
5. write the release-consumed acknowledgment marker before moving to the next phase; and
6. fail closed on unsupported platform behavior, wrong PID topology, unexpected signal, duplicate release or phase mismatch.

An asynchronous Python handler plus a threading event is not accepted because handler execution can be delayed by C-level work and does not provide the required barrier determinism.

### 6.3 Full container identity correction

Docker assigns the authoritative full container ID during creation. Under the preferred no-copy-in/no-control-mount design, the runner cannot portably know that future ID before it starts. Hostname or a private cgroup view is not an authoritative full-ID source.

Owner-accepted correction:

- the controller creates the runner for one manifest-enumerated run/point/subrun identity tuple and does not override Docker's default container hostname;
- every runner marker carries `container_hostname_sha256` and the one-use run/point/subrun commitments, not a claimed full container-ID hash;
- the controller proves that the observed hostname/short identifier is a prefix of the exact inspected full ID;
- the controller copies the marker from that exact full ID; and
- the controller's receipt binds `container_id_sha256` to `marker_sha256`.

Runner-local full-ID injection remains rejected. Reopening it would require a separately approved create-then-descriptor-copy-in or equivalent pre-start inbound-channel redesign with expanded copy-in, file, command and replay authority.

## 7. Marker and nonce contract

### 7.1 Exact runner-local path and basenames

The future harness may create only this control directory inside the disposable runner's writable layer:

`/tmp/erpai-finance-gl-tb-control/markers/`

It is not a mount or retained evidence volume. The harness creates it with owner-only access before any marker and verifies that it is a real directory, not a link.

The exact transient marker basenames are:

1. `measurement-ready.json`;
2. `measurement-released.json`;
3. `pre-connect-ready.json`;
4. `connection-attempt-released.json`;
5. `request-block-entered.json`;
6. `finalization-block-entered.json`;
7. `telemetry-ready.json`; and
8. `normal-exit-released.json`.

`harness-complete.json` is a sealed harness evidence artifact, not a transient control marker. `point-complete.json` is controller-owned final evidence.

### 7.2 Canonical marker schema

Every control marker has exactly these ordered keys and no others:

~~~json
{
  "schema": "erpai.finance.gl_tb.control_marker",
  "event": "<approved-enum>",
  "sequence": "<manifest-enumerated-sequence>",
  "run_id_sha256": "<lowercase-sha256>",
  "point_id_sha256": "<lowercase-sha256>",
  "subrun_id_sha256": "<lowercase-sha256>",
  "mode": "<approved-enum>",
  "phase": "<approved-enum>",
  "session_nonce_sha256": "<lowercase-sha256>",
  "container_hostname_sha256": "<lowercase-sha256>",
  "manifest_sha256": "<lowercase-sha256>",
  "workload_plan_sha256": "<lowercase-sha256>",
  "compose_sha256": "<lowercase-sha256>",
  "harness_sha256": "<lowercase-sha256>",
  "controller_sha256": "<lowercase-sha256>",
  "runner_image_sha256": "<lowercase-sha256>",
  "previous_marker_sha256": "<lowercase-sha256-or-genesis-enum>",
  "monotonic_ns": "<integer-observation-not-a-limit>"
}
~~~

The schema contains no raw nonce, raw run/point/subrun identifier, username, role, company, account, dimension, amount, SQL, exception, path, secret, credential, financial value or free-form message.

The controller computes and records the exact marker-file SHA-256 after canonical validation. Retained evidence may contain only approved enums and hashes; it may not retain raw control marker contents.

### 7.3 Nonce lifecycle

- The runner obtains a fresh cryptographically secure random nonce for each subrun.
- The raw nonce exists only in runner memory and is never written, copied, logged or retained.
- Markers contain only `session_nonce_sha256`.
- A subrun cannot reuse a nonce commitment.
- The nonce commitment, exact subrun state, previous-marker hash and controller full-ID binding jointly prevent stale or cross-subrun acceptance within the exclusive-host threat model.
- Controller restart never resumes an evidence subrun, even if the marker and nonce commitment appear valid.

### 7.4 Atomic marker creation

For each exact marker, the harness must:

1. open a same-directory partial with exclusive creation and no-follow semantics;
2. verify regular-file type, expected owner and a single link;
3. write canonical UTF-8 JSON with final LF;
4. flush and fsync the file;
5. atomically rename it to the exact final basename;
6. fsync the parent directory; and
7. never overwrite, unlink or rewrite that basename during the runner lifetime.

The controller must treat `docker container cp ... -` as hostile tar input. It may accept exactly one regular member with the exact expected basename, no link, device, traversal, duplicate, extra member or unexpected metadata, and no bytes beyond the later manifest-approved evidence ceiling. It must parse the member without a general extraction command.

Copy success is insufficient because Docker can copy from stopped containers. Fixed-field inspection must prove the exact full ID is running immediately before and after every ready-marker copy except the explicitly stopped-container read of `normal-exit-released.json`.

### 7.5 Invalid and recovery behavior

Any duplicate, changed, stale, missing, unexpected, contradictory, out-of-order or noncanonical marker invalidates that subrun. No release signal is sent from an invalid state.

A repeated controller read of the same immutable marker is idempotent only before the next transition and only if its full hash and all binding fields are unchanged.

The controller durably writes release intent before signal delivery. A crash between release intent, signal delivery and acknowledgment is inherently ambiguous; recovery must not infer completion or resend. The subrun becomes discard-only.

Controller recovery may:

- inspect only manifest-bound exact IDs and approved labels;
- kill a blocked exact runner;
- unpause and verify the exact disposable database if required;
- destroy transient marker copies and exact disposable resources; and
- write a sanitized teardown/recovery classification.

Recovery may not resume a proof, send a normal release, promote evidence or create replacement resources.

## 8. Fail-closed handshake state machine

Each subrun follows one mutually exclusive branch. A runner never traverses multiple fault branches.

### 8.1 Common prefix

~~~text
manifest_verified
-> runner_created
-> exact_full_id_image_labels_hostname_verified
-> runner_started
-> cgroup_attributed
-> sampling_started
~~~

If a measurement boundary is required by the workload mode:

~~~text
measurement_ready
-> marker_copied_and_validated
-> baseline_cgroup_captured
-> release_intent_durable
-> SIGUSR1_sent_to_exact_full_id
-> measurement_released_acknowledged
~~~

### 8.2 Initial-connection-stall branch

~~~text
pre_connect_ready
-> marker_copied_and_validated
-> database_pause_intent_durable
-> exact_database_container_paused
-> Paused_true_verified
-> connection_release_intent_durable
-> SIGUSR1_sent_to_exact_runner
-> connection_attempt_released_acknowledged
-> connection_attempt_observed_stalled
-> external_deadline_reached
-> exact_runner_SIGKILL
-> exit_and_OOM_state_inspected
-> exact_database_unpaused
-> Paused_false_verified
-> discard_only_receipt
-> teardown
~~~

If database pause is uncertain, times out or cannot be confirmed, the runner is not released. If unpause cannot be verified, teardown is `teardown_unverified` and never broadens cleanup authority.

### 8.3 Request-watchdog branch

~~~text
request_block_entered
-> marker_copied_and_validated
-> no_release_by_design
-> external_request_ceiling_reached
-> exact_runner_SIGKILL
-> exit_and_OOM_state_inspected
-> discard_only_receipt
-> teardown
~~~

### 8.4 Finalization-watchdog branch

~~~text
finalization_block_entered
-> marker_copied_and_validated
-> no_release_by_design
-> external_finalization_ceiling_reached
-> exact_runner_SIGKILL
-> exit_and_OOM_state_inspected
-> discard_only_receipt
-> teardown
~~~

### 8.5 Successful measured branch

~~~text
harness_artifacts_finalized_in_point_staging
-> harness_complete_written
-> telemetry_ready_written
-> telemetry_ready_marker_validated
-> exact_runner_identity_and_cgroup_revalidated
-> final_measured_window_cgroup_capture
-> controller_memory_receipt_sealed
-> normal_exit_release_intent_durable
-> SIGUSR1_sent_to_exact_runner
-> normal_exit_released_acknowledged
-> runner_exit_zero_and_OOMKilled_false_verified
-> sealed_harness_artifacts_copied
-> exact_allowlist_hash_format_canary_and_link_validation
-> controller_writes_point_complete_last
-> same_filesystem_atomic_point_promotion
~~~

Killed, timed-out, OOM, incomplete, prematurely exited, telemetry-unavailable, cgroup-drifted, unsealed or ambiguous runs remain discard-only and cannot produce or promote a valid `point-complete.json`.

## 9. Pre-exit cgroup telemetry and terminal seal

The exact owner sequence is accepted as the recommendation:

1. The harness completes only its own artifacts.
2. The harness writes `harness-complete.json`.
3. The harness writes `telemetry-ready.json` and blocks in synchronous signal wait.
4. The controller revalidates exact full container ID, PID, start identity, labels, running state and cgroup attribution.
5. The controller reads only the resolved exact cgroup-v2 paths and captures:
   - `memory.current`;
   - `memory.peak`;
   - `memory.events.local`;
   - `memory.max`;
   - OOM and OOM-kill deltas;
   - the canonical sample-vector hash;
   - the final monotonic observation; and
   - measurement-window start and end observations.
6. The controller requires `cgroup.events` to prove the runner cgroup remains populated while final capture occurs.
7. The controller seals its memory receipt.
8. The controller sends the normal-exit release to the exact full runner ID.
9. The runner writes `normal-exit-released.json` and exits normally.
10. The controller verifies exit success and `OOMKilled=false`, validates copied harness evidence, writes `point-complete.json` last and atomically promotes the point.

The controller reads cgroup files directly with standard-library file operations after containment validation. Docker stats, a general shell, `cat`, fallback providers and host-wide cgroup inspection are not allowlisted.

### 9.1 Exact evidence claim

The authoritative claim is **measured-window cgroup peak**, beginning at the approved fresh-runner measurement boundary and ending while the runner is blocked at `telemetry-ready.json`. It is not a claim over post-release acknowledgment, JUnit wrapper activity or interpreter shutdown.

The Owner accepts the measured-window claim because it covers the candidate workload and keeps the accepted containment boundary. A literal full-cgroup-lifetime peak through process exit remains deferred unless a separately approved controller-owned parent-cgroup or reviewed launcher/holder design expands the host privileges, source, commands and evidence.

### 9.2 Terminal seal ownership

The controller is the sole owner of final `point-complete.json` because only it can certify:

- exact container and image identity;
- final cgroup evidence;
- Docker exit and OOM state;
- copy-out validation;
- complete harness-artifact hashes;
- absence of canaries and links;
- manifest dependency correctness; and
- successful same-filesystem atomic promotion.

The harness is the sole owner of `harness-complete.json`. This supersedes the older assumption that the harness writes the terminal point seal.

## 10. Immutable harness delivery

### 10.1 Alternatives

| Method | Binding and supply-chain evidence | Permission, leakage and runtime impact | Teardown, cost and recommendation |
| --- | --- | --- | --- |
| Separately built immutable derived runner image | Exact base image ID/digest, source HEAD/blob, harness and initializer hashes, Dockerfile hash, canonical context hash, build metadata, resulting full image ID/config/rootfs/layer identities and copy-out verification. | No source or live mount at execution. No build/pull during proof. Build is a separate high-authority gate. | Retain exact image through closure; exact cleanup is a later gate. Highest initial planning evidence but strongest runtime immutability. **Accepted for planning.** |
| Pre-start copy into exact created container | Controller copies harness after create and before start; receipt binds source and container ID. | Adds copy-in authority, mutable writable layer and tar-path validation. Full-ID descriptor could also be injected but expands control surface. | Container removal is reversible, but source binding is weaker and execution manifest more complex. Rejected unless derived-image materialization proves unavailable. |
| Read-only source mount | Bind or volume mount exposes source to runner; inspect can prove read-only type/source. | Violates no source mount, risks repository leakage and host-path confusion, and couples proof to mutable checkout state. | Easy cleanup but unacceptable source/live containment. Rejected. |
| Runtime copy into waiting runner | Copy occurs after start. | Adds a waiting process, copy-in race, mutable code after identity check and broader injection surface. | Poor provenance and determinism. Rejected. |
| OCI artifact or image-layer injection | Can be immutable and signed, but requires artifact tooling, registry/media-type decisions and import logic. | Adds supply-chain components, credentials or network unless fully local. | Potential future alternative for cross-host distribution; excessive for same-host proof. Deferred. |

### 10.2 Owner-accepted image-materialization posture

The derived synthetic runner image must be created only in a separately approved image-materialization gate. The exact build context contains only:

1. `finance_gl_trial_balance_runner.Dockerfile`;
2. `test_finance_gl_trial_balance_source_proof.py`; and
3. `finance_gl_trial_balance_site_initializer.py`.

The host controller is not included in the image.

The Dockerfile may contain only:

- the exact approved backend digest or verified local base image identity;
- exact non-wildcard copy operations for the harness and initializer;
- fixed ownership and modes;
- the fixed non-root execution user; and
- an exec-form entrypoint.

It may not use `RUN`, `ADD`, remote URL syntax, wildcard copy, package installation, network download, unpinned base, build secret, argument/environment secret, controller inclusion, repository directory, live configuration or protected path.

The controller constructs a canonical tar context from exact source files rather than passing the repository directory as build context. Image materialization uses no pull and no build-step network. [Docker build-context behavior](https://docs.docker.com/build/concepts/context/) and [Buildx build options](https://docs.docker.com/reference/cli/docker/buildx/build/) are the authoritative future behavior references.

### 10.3 Source-to-image verification

The future materialization receipt must freeze:

- source branch, HEAD and exact Git blob identities;
- base repository digest and verified local full image ID;
- harness, initializer and Dockerfile SHA-256 values;
- canonical build-context manifest and tar-stream SHA-256;
- exact build argument-vector SHA-256;
- Docker Engine and Buildx versions;
- sanitized build metadata;
- resulting derived full image ID, config digest, rootfs/layer identities and exact local tag;
- sanitized image configuration, user, entrypoint, command, mounts, ports, environment-key allowlist and labels; and
- a create-never-start verification container receipt proving the copied-out harness and initializer bytes, modes and owners match source.

The derived image is executed later only by exact local full image ID with pull disabled. No registry publication is required for same-host synthetic evidence. Docker's default local Engine image store does not make registry-retained provenance attestations available in the same way as an attestation-capable registry, so the controller-owned materialization receipt is the evidence authority for this stage.

Cross-host distribution, private registry publication, push credentials, registry retention and attestation validation require a separate network and release gate.

### 10.4 Image retention and cleanup

The exact derived image remains present through synthetic-evidence closure. Recovery teardown must never remove it.

A later cleanup gate may remove only the exact verified local tag and full image ID after confirming no approved or unrelated container references it. It may not use force, prune, wildcard, dangling-image cleanup or registry action. Cleanup is reversible only by a newly approved identical materialization; therefore materialization evidence must be retained after image removal.

## 11. Secret-injection design

### 11.1 Alternatives

| Mechanism | Arguments, inspect and files | Bench/Frappe compatibility and source impact | Persistence, leakage, teardown and recommendation |
| --- | --- | --- | --- |
| Compose secrets backed by controller-created host RAM files plus reviewed initializer | Secret values are not container environment values or command arguments. Compose mounts exact secret files under `/run/secrets`. Docker inspect reveals mount metadata and secret names, not retained values. | Frappe's documented `bench new-site` exposes password options or prompts, so a reviewed initializer is required to read exact secret files and call the pinned installation API in-process. Adds one bounded source file. | Host source files are transient RAM-backed files; site database credential necessarily persists in disposable `site_config.json` until exact sites-volume teardown. Strongest bounded option. **Accepted for planning**, with the explicit narrow secret-bind exception. |
| Container environment values | Values appear in container configuration and inspect. | Bench can consume environment only through additional wrapper logic; current harness reads root credential this way. | Persists in inspectable config until container removal and may enter diagnostics. Rejected. |
| Compose environment-sourced secrets | Source value originates in environment even when exposed as a secret file. | Still requires environment handling and initializer. | Host/controller environment inspection risk remains; provenance is weaker. Rejected. |
| Anonymous stdin or pipe | Value can avoid arguments and files if the consumer reads stdin exactly. | Documented Bench prompting is interactive; deterministic prompt automation or a wrapper is required. Compose one-shot lifecycle and error recovery are fragile. | Controller crash and partial input are ambiguous; output may echo prompts. Rejected for this stage. |
| RAM-backed temporary file without Compose secret mount | Secret stays in volatile host storage but must be bind-mounted or copied. | Requires explicit file path handling. | Similar host lifecycle but weaker service-scoped semantics and easier accidental mount broadening. Use only as the exact source behind Compose secrets. |
| Reviewed initialization shim | Can read fixed secret files and invoke pinned Frappe code without secret argv/env. | Required by the recommended mechanism. Must be a separately reviewed, tightly bounded source file. | Safe only with strict logging, exception and teardown rules. Accepted as a required scope expansion, not hidden implementation detail. |
| Command-line arguments | Values are visible in process arguments and may enter controller receipts or diagnostics. | Directly supported by documented Bench options. | Explicitly prohibited. |
| Shell interpolation or copied live config | Values may appear in shell history, command strings, logs or persistent copied files. | Broad, unreviewed behavior. | Explicitly prohibited. |
| External secret manager or Swarm secret | Can provide stronger centralized lifecycle. | Adds service/platform/network/credential dependencies not present in this disposable stack. | Deferred unless same-host Compose secrets prove inadequate. |

Primary behavior references:

- Compose grants secrets to services as files under `/run/secrets`. [Docker Compose secrets](https://docs.docker.com/compose/how-tos/use-secrets/)
- Compose service secret sources are implemented as narrowly scoped mounts and require explicit grants. [Compose service secrets](https://docs.docker.com/reference/compose-file/services/)
- Frappe documents password command options for new-site creation, so direct CLI use would place values in process arguments. [Frappe Bench new-site](https://docs.frappe.io/framework/user/en/bench/reference/new-site)
- Frappe site configuration stores database connection data required by the disposable site. [Frappe site configuration](https://docs.frappe.io/framework/user/en/basics/site_config)
- MariaDB's official image supports password-file conventions; random-root-password mode is rejected because it can print the generated password. [MariaDB container environment variables](https://mariadb.com/docs/server/server-management/automated-mariadb-deployment-and-administration/docker-and-mariadb/mariadb-server-docker-official-image-environment-variables)

### 11.2 Owner-accepted secret lifecycle

The future controller:

1. generates disposable root, site-database and site-administrator credentials in memory;
2. creates exact, exclusive, no-follow, single-link, owner-only files beneath an Owner-approved host RAM-backed filesystem;
3. creates no `.env` file and records no secret value or secret hash;
4. grants each Compose secret only to the service that requires it:
   - database-root secret to MariaDB and the one-shot initializer;
   - site-database and site-administrator secrets only to the initializer;
   - no root secret to normal accounting/workload runners;
   - a separately scoped least-privilege topology/reconnect credential only if a pinned privilege fingerprint proves it sufficient;
5. configures MariaDB to consume its documented password-file input;
6. lets the initializer read only the exact files under `/run/secrets` and call a pinned, fingerprinted Frappe installation API in-process;
7. forbids the initializer from emitting values in argv, environment, stdout, stderr, exception messages or evidence;
8. removes the initializer before measured work;
9. destroys exact host secret-source files in normal and recovery teardown; and
10. destroys the disposable sites volume containing `site_config.json` during exact point teardown.

All synthetic services must use a disabled Docker logging driver and the controller must verify the fixed sanitized inspect field. Docker otherwise uses a persistent default logging driver in common installations. [Docker logging configuration](https://docs.docker.com/engine/logging/configure/)

Bounded stdout/stderr needed for process status is controller-owned transient state, scanned for secret and identity canaries, then destroyed. `docker logs` is not allowlisted.

Teardown evidence records only fixed lifecycle outcomes and path/identity hashes. It records neither secret values nor hashes of secret values.

### 11.3 Required source and mount decision

The former two-file source scope was insufficient. The Owner now accepts:

- expansion of the repository source allowlist to include the Dockerfile and initializer listed in Section 12;
- a narrow exception to the no-host-bind rule solely for Compose's read-only, service-scoped mounts from exact controller-created RAM-backed secret-source files; and
- the generated site database credential existing inside only the point's disposable `site_config.json` until exact sites-volume destruction.

These accepted planning decisions do not authorize source authoring, secret creation, image materialization or execution. A later compatibility gate must prove the pinned Compose secret behavior, MariaDB password-file support, Frappe initializer API/signatures, file ownership/mode, non-disclosure and teardown absence.

## 12. Exact future file allowlists

These are planning allowlists only. They do not authorize creation or modification.

### 12.1 Repository source candidates

Exactly:

1. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/tests/test_finance_gl_trial_balance_source_proof.py`;
2. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/tests/finance_gl_trial_balance_evidence_controller.py`;
3. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/tests/finance_gl_trial_balance_runner.Dockerfile`; and
4. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/tests/finance_gl_trial_balance_site_initializer.py`.

Ownership:

- harness: sole accounting, permission, snapshot, workload, leakage and harness-evidence owner;
- controller: host orchestration, watchdog, Docker lifecycle, cgroup telemetry, controller evidence, promotion, recovery and teardown only;
- Dockerfile: immutable runner layering and exec-form entrypoint only; and
- initializer: disposable-site creation plus exact secret-file consumption only.

The initializer may not contain accounting, permission, reporting, evidence-adjudication, workload, UI, endpoint or production-runtime logic. The controller may not import application runtime code or implement accounting semantics.

### 12.2 Documentation candidates

Current documentation reconciliation:

1. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/finance-accounting-cycle2-gl-tb-controller-runner-control-plane-source-delivery-amendment-2026-07-18.md`;
2. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/finance-accounting-cycle2-gl-tb-synthetic-evidence-execution-package-2026-07-17.md`;
3. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/finance-accounting-cycle2-gl-tb-runtime-evidence-design-amendment-2026-07-18.md`; and
4. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/README.md`.

This task authorizes only factual documentation reconciliation across those four paths. It does not authorize staging, publication or source work.

### 12.3 Image-materialization context

Exactly:

1. `<MATERIALIZATION_ROOT>/context/finance_gl_trial_balance_runner.Dockerfile`;
2. `<MATERIALIZATION_ROOT>/context/test_finance_gl_trial_balance_source_proof.py`;
3. `<MATERIALIZATION_ROOT>/context/finance_gl_trial_balance_site_initializer.py`; and
4. `<MATERIALIZATION_ROOT>/context/build-context-manifest.sha256`.

The canonical tar build stream contains the first three exact files. The context manifest is controller evidence and is not copied into the image.

Retained sanitized image evidence:

1. `<MATERIALIZATION_ROOT>/evidence/image-materialization-manifest.json`;
2. `<MATERIALIZATION_ROOT>/evidence/build-context-manifest.json`;
3. `<MATERIALIZATION_ROOT>/evidence/build-metadata.json`;
4. `<MATERIALIZATION_ROOT>/evidence/image-verification.json`; and
5. `<MATERIALIZATION_ROOT>/evidence/image-materialization-receipt.json`.

No controller, repository directory, protected exclusion, live path, application configuration, site data, secret, log or unrelated file may enter the context or retained materialization evidence.

### 12.4 Transient control and controller state

Runner-local markers are the eight exact basenames in Section 7 under:

`/tmp/erpai-finance-gl-tb-control/markers/`

Host raw copies are transient under:

`<RUN_ROOT>/control/<SUBRUN_ID>/markers/<EXACT_MARKER_BASENAME>`

Controller state is limited to:

1. `<RUN_ROOT>/control/controller-state.json`;
2. `<RUN_ROOT>/control/<SUBRUN_ID>/subrun-state.json`;
3. `<RUN_ROOT>/control/<SUBRUN_ID>/release-intent.json`;
4. `<RUN_ROOT>/control/<SUBRUN_ID>/recovery-state.json`; and
5. bounded transient stdout/stderr scan files for exact child processes.

Raw marker copies and scan files are destroyed after validated teardown. If teardown identity cannot be verified, only minimal owner-only recovery identifiers may remain; none counts as proof.

### 12.5 Harness staging and point evidence

The canonical package's existing point basenames remain unchanged except for terminal-seal ownership. Point-local staging may contain exactly:

1. `provenance.json`;
2. `topology.json`;
3. `site-apps.json`;
4. `fixture-manifest.json`;
5. `accounting-results.jsonl`;
6. `permission-results.jsonl`;
7. `snapshot-results.jsonl`;
8. `workload-results.jsonl`;
9. `leakage-results.jsonl`;
10. `expected-actual-diff.jsonl`;
11. `mutation-sentinel.json`;
12. `junit.xml`; and
13. `harness-complete.json`.

The controller adds only:

14. `memory-receipt.json`; and
15. `point-complete.json`, written last.

The promoted point directory remains:

`<RUN_ROOT>/evidence/points/<POINT_ID>/`

### 12.6 Retained controller, proof and teardown evidence

Exactly:

1. `<RUN_ROOT>/evidence/controller-receipt.json`;
2. `<RUN_ROOT>/evidence/controller-events.jsonl`;
3. `<RUN_ROOT>/evidence/watchdog-results.jsonl`;
4. `<RUN_ROOT>/evidence/isolation-results.jsonl`;
5. `<RUN_ROOT>/evidence/memory-results.jsonl`;
6. `<RUN_ROOT>/evidence/point-index.json`;
7. `<RUN_ROOT>/evidence/review-disposition.json`;
8. `<RUN_ROOT>/evidence/proof-evidence-manifest.sha256`;
9. `<RUN_ROOT>/evidence/teardown-receipt.json`; and
10. `<RUN_ROOT>/evidence/final-evidence-manifest.sha256`.

Discard-only runs retain only their sanitized fixed-class controller/watchdog/teardown records. No killed or incomplete harness artifact may be promoted or included as valid proof.

## 13. Exact future command classes

These templates are architecture only. No command in this section was executed or is authorized for execution.

### 13.1 Owner-facing controller entrypoints

~~~text
/usr/bin/python3 -I <SOURCE_ROOT>/<CONTROLLER_REL> materialize-image --manifest <IMAGE_MATERIALIZATION_MANIFEST>
/usr/bin/python3 -I <SOURCE_ROOT>/<CONTROLLER_REL> preflight --manifest <RUN_ROOT>/execution-manifest.json
/usr/bin/python3 -I <SOURCE_ROOT>/<CONTROLLER_REL> execute --manifest <RUN_ROOT>/execution-manifest.json
/usr/bin/python3 -I <SOURCE_ROOT>/<CONTROLLER_REL> recover-teardown --manifest <RUN_ROOT>/execution-manifest.json
~~~

Adding `materialize-image` supersedes the prior assumption that only the other three Owner-facing entrypoints exist. Image materialization remains a separate future approval gate; it cannot be invoked by `execute`.

### 13.2 Marker copy-out and exact release

~~~text
docker container inspect --format <FIXED_ID_IMAGE_RUNNING_PID_LABEL_HOSTNAME_FORMAT> <EXACT_FULL_RUNNER_ID>
docker container cp <EXACT_FULL_RUNNER_ID>:/tmp/erpai-finance-gl-tb-control/markers/<EXACT_MARKER_BASENAME> -
docker container kill --signal SIGUSR1 <EXACT_FULL_RUNNER_ID>
docker container wait <EXACT_FULL_RUNNER_ID>
docker container inspect --format <FIXED_RUNNER_EXIT_OOM_FORMAT> <EXACT_FULL_RUNNER_ID>
docker container stop --timeout <OWNER_APPROVED_GRACE> <EXACT_FULL_RUNNER_ID>
docker container kill --signal KILL <EXACT_FULL_RUNNER_ID>
docker container cp <EXACT_FULL_RUNNER_ID>:<EXACT_SEALED_HARNESS_STAGING_PATH> -
~~~

Copy-out parsers accept only exact regular members and never invoke a general tar extractor.

### 13.3 Database pause and recovery

~~~text
docker container inspect --format <FIXED_DB_ID_RUNNING_PAUSED_LABEL_FORMAT> <EXACT_FULL_DB_ID>
docker container pause <EXACT_FULL_DB_ID>
docker container inspect --format <FIXED_DB_PAUSED_FORMAT> <EXACT_FULL_DB_ID>
docker container unpause <EXACT_FULL_DB_ID>
docker container inspect --format <FIXED_DB_PAUSED_FORMAT> <EXACT_FULL_DB_ID>
~~~

### 13.4 Cgroup capture

The controller uses standard-library, no-follow reads of the exact resolved runner cgroup paths under:

~~~text
/proc/<EXACT_RUNNER_PID>/cgroup
/sys/fs/cgroup/<CONTAINMENT_VALIDATED_RUNNER_CGROUP>/cgroup.events
/sys/fs/cgroup/<CONTAINMENT_VALIDATED_RUNNER_CGROUP>/memory.current
/sys/fs/cgroup/<CONTAINMENT_VALIDATED_RUNNER_CGROUP>/memory.peak
/sys/fs/cgroup/<CONTAINMENT_VALIDATED_RUNNER_CGROUP>/memory.events.local
/sys/fs/cgroup/<CONTAINMENT_VALIDATED_RUNNER_CGROUP>/memory.max
~~~

No shell command, Docker stats, host-wide cgroup traversal or fallback collector is allowlisted.

### 13.5 Image materialization and verification

~~~text
docker buildx version
docker image inspect --format <FIXED_IMAGE_FORMAT> <EXACT_BASE_DIGEST_OR_VERIFIED_LOCAL_BASE_ID>
docker image tag <VERIFIED_BASE_ID> <EXACT_TRANSIENT_LOCAL_BASE_TAG>
docker buildx build --file finance_gl_trial_balance_runner.Dockerfile --network none --pull=false --no-cache --load --metadata-file <EXACT_METADATA_FILE> --tag <EXACT_DERIVED_TAG> -
docker image inspect --format <FIXED_IMAGE_FORMAT> <EXACT_DERIVED_TAG>
docker container create --name <EXACT_VERIFY_NAME> --label <EXACT_VERIFICATION_LABELS> <EXACT_DERIVED_IMAGE_ID>
docker container cp <EXACT_VERIFY_ID>:<EXACT_HARNESS_PATH> -
docker container cp <EXACT_VERIFY_ID>:<EXACT_INITIALIZER_PATH> -
docker container rm --volumes <EXACT_VERIFY_ID>
docker image rm <EXACT_TRANSIENT_LOCAL_BASE_TAG>
~~~

The verification container is created but never started. No build or pull occurs during synthetic execution.

### 13.6 Exact teardown and later image cleanup

Before any Compose or exact-ID removal, the controller validates every manifest-enumerated resource's full ID, exact name, image and approved project/run/point labels. Any unknown or additional project resource produces `teardown_unverified` and stops broad cleanup.

Planning classes:

~~~text
docker container ls --all --filter <EXACT_APPROVED_LABEL_FILTER> --format <FIXED_ID_FORMAT>
docker network ls --filter <EXACT_APPROVED_LABEL_FILTER> --format <FIXED_ID_FORMAT>
docker volume ls --filter <EXACT_APPROVED_LABEL_FILTER> --format <FIXED_ID_FORMAT>
docker container rm --force --volumes <EXACT_VERIFIED_CONTAINER_ID>
docker network rm <EXACT_VERIFIED_NETWORK_ID>
docker volume rm <EXACT_VERIFIED_VOLUME_ID>
~~~

Only after a separate image-cleanup approval:

~~~text
docker container ls --all --filter ancestor=<EXACT_FULL_IMAGE_ID> --format <FIXED_ID_FORMAT>
docker image inspect --format <FIXED_IMAGE_FORMAT> <EXACT_DERIVED_TAG>
docker image rm <EXACT_DERIVED_TAG>
docker image rm --no-prune <EXACT_FULL_IMAGE_ID>
~~~

Exact-ID fallback teardown order is containers, networks, then volumes. Recovery never removes the derived image.

### 13.7 Command prohibitions

Not allowlisted:

- arbitrary or control-plane `docker exec`;
- `docker logs`;
- shell passthrough, shell interpolation or general command suffixes;
- free-form copy-in or directory extraction;
- unfiltered inspect, events or daemon-wide state dumps;
- Docker socket mounts;
- extra external networks;
- Redis, SQL or HTTP control channels;
- image pull, registry login/push or live image deployment;
- force image removal, prune, wildcard or unrelated-resource cleanup; and
- any runtime, endpoint, UI, routing, registry, governance, permission, live or accounting command.

Any inherited exact diagnostic command in the canonical package is subordinate to the accepted control-plane restrictions and cannot be repurposed as a controller-to-runner channel.

## 14. Superseded assumptions

The Owner accepts, and this documentation reconciliation records:

1. **Two-file authoring scope:** superseded by an exact four-file source candidate scope because immutable delivery and secret-safe initialization require a Dockerfile and reviewed initializer.
2. **Harness-owned terminal seal:** superseded. Harness owns `harness-complete.json`; controller owns final `point-complete.json`.
3. **Runner marker contains full container-ID hash:** corrected. The runner carries a pre-created identity/hostname commitment; the controller binds the copied marker to the exact full ID in its receipt.
4. **Only three controller entrypoints:** expanded by a separately gated `materialize-image` entrypoint.
5. **Unspecified in-memory secret channel with no secret file:** superseded by service-scoped Compose secret files sourced from exact controller-created host RAM files plus a reviewed initializer.
6. **No host bind mounts without exception:** narrowed to allow only exact read-only Compose secret mounts from approved RAM-backed source files.
7. **Harness writes `point-complete.json` before exit:** superseded by the pre-exit telemetry hold, normal-exit release, exit/OOM validation and controller-owned seal.
8. **Full-cgroup-lifetime memory claim:** clarified as authoritative measured-window cgroup evidence ending at the pre-exit telemetry barrier. A literal through-exit claim remains unapproved.
9. **Copy-out implies live runner:** rejected; fixed-field running-state inspection is required because Docker can copy from stopped containers.

No accounting equation, authority fixture, permission boundary, company scope, snapshot posture, workload derivation method, protected-workspace boundary or deferred runtime capability is superseded.

## 15. Findings and review disposition

### 15.1 Blocker

| Finding | Concrete evidence | Disposition |
| --- | --- | --- |
| Current two-file source scope cannot provide both immutable image delivery and secret-safe Frappe site initialization. | The current harness reads a root credential from environment. Frappe's documented new-site interface exposes password CLI options/prompts, while Compose secrets provide files. A reviewed file-consuming initializer and Dockerfile are absent. | **Accepted and resolved at planning level.** The exact four-file scope is canonical. Source authoring remains separately gated and unapproved. |
| The runner cannot know Docker's post-create full ID inside its own marker without an inbound channel. | Docker assigns container identity at create time; the accepted topology prohibits post-create copy-in/control mounts, and hostname/cgroup views are not authoritative full IDs. | **Accepted and resolved at planning level.** Controller-owned full-ID binding is canonical; runner-local injection remains rejected. Source authoring still requires a separate gate and compatibility proof. |

### 15.2 High

| Finding | Concrete evidence | Disposition |
| --- | --- | --- |
| Async Python handlers do not provide a deterministic barrier, and Docker targets only the main container process. | Authoritative Docker/Python behavior; pinned Bench PID boundary is not yet fingerprinted. | **Accepted.** Require exec-form PID 1, pre-thread signal blocking and synchronous `sigwait`, subject to a read-only compatibility gate. |
| Harness cannot certify external terminal evidence. | Current harness finalizes before controller cgroup capture, Docker exit/OOM validation and promotion. | **Accepted.** Controller becomes sole `point-complete.json` owner. |
| Docker copy-out is a tar stream and works on stopped containers. | Authoritative Docker copy behavior. | **Accepted.** Strict single-member parser plus fixed-field running checks. |
| Literal full-lifetime cgroup peak cannot be sealed before releasing the runner. | Acknowledgment/interpreter exit happens after pre-exit capture. | **Accepted with clarification.** Use measured-window authority; full-lifetime design is a separate Owner option. |
| Teardown can affect unrelated resources if project discovery is trusted before identity validation. | Compose project operations can include resources not present in the frozen manifest. | **Accepted.** Pre-validate every exact resource; unknown extras yield `teardown_unverified`. |

### 15.3 Medium

| Finding | Disposition |
| --- | --- |
| Signals carry no nonce and can coalesce. | Accept one outstanding release only, exact state, hash-chained markers and an exclusive-host threat boundary. |
| Crash after release intent is ambiguous. | Discard-only; never retry or resume. |
| Default Docker logs can persist output on the host. | Require disabled logging for synthetic services and scan/destroy only bounded controller-owned process streams. |
| Default local image-store metadata is not a registry attestation. | Accept controller-owned same-host materialization receipts; defer registry publication. |
| Derived-image cleanup is not reversible without rebuilding. | Retain through closure and use a separate exact-ID cleanup gate. |

### 15.4 Rejected and deferred reviewer proposals

- A sidecar, HTTP service, Redis/SQL channel, stdin attach, shared evidence-volume release and general Docker exec/copy-in were rejected because their topology, authority, leakage or recovery costs exceed the accepted threat model.
- A cryptographically authenticated control service is deferred unless the Owner rejects exclusive Docker-host authority.
- A private registry is deferred because the proposed proof is same-host; cross-host delivery requires its own gate.
- A controller-owned parent cgroup or launcher remains deferred unless a later gate reopens literal through-exit lifetime evidence.
- VM-level isolation and host page-cache proof remain deferred under the accepted runtime design.
- Accounting and permission review was not reopened because the control-plane proposal does not change their accepted semantics.

## 16. Owner-accepted decisions and remaining gates

On 2026-07-18 the Owner accepted:

1. **Transport:** exact marker copy-out plus exact `SIGUSR1` under one named environment owner with exclusive Docker-host mutation authority.
2. **Process boundary:** exec-form harness-bearing Python/Frappe PID 1 and synchronous blocked-signal `sigwait`, subject to a later pinned read-only Bench/Frappe signal/PID compatibility gate.
3. **Full-ID binding:** controller-owned full-ID binding in the controller receipt while the runner marker carries the manifest identity commitments and observed hostname commitment.
4. **Terminal seal:** the controller as sole `point-complete.json` owner and the harness as `harness-complete.json` owner.
5. **Memory claim:** authoritative measured-window cgroup evidence ending while the runner is blocked at `telemetry-ready`; through-exit lifetime proof remains deferred.
6. **Source scope:** the exact four-file future source allowlist in Section 12.
7. **Image gate:** a separate `materialize-image` controller entrypoint and separately approved derived-image materialization gate.
8. **Artifact identity:** same-host exact local derived image ID plus controller-owned materialization receipts, with registry publication deferred.
9. **Image lifecycle:** retention of the derived image through evidence closure and separate exact-ID cleanup approval.
10. **Secret channel:** controller-generated credentials, exact host-RAM-backed Compose secret sources, service-scoped read-only secret mounts and the reviewed initializer.
11. **Site credential persistence:** the generated point database credential may exist only in the disposable site's `site_config.json` until exact sites-volume destruction.
12. **Logging:** disabled Docker container logging plus bounded transient controller-stream scanning and destruction.
13. **Teardown:** full identity validation of every project resource before Compose or exact-ID teardown; unknown extras stop with `teardown_unverified`.
14. **Documentation reconciliation:** factual reconciliation of the canonical package, runtime amendment, this amendment and README in this four-file documentation-only task.

These acceptances authorize no source authoring, image materialization, infrastructure, secret creation, numeric selection or synthetic execution. Remaining gates are the read-only runtime/Compose/MariaDB/Frappe compatibility gate; exact four-file source authoring and bounded review; source publication; image materialization; materialized execution inputs and numeric values; synthetic execution; evidence closure; and any later image cleanup.

## 17. Validation and closure

The bounded review set was:

- database/runtime determinism;
- security and information leakage; and
- release containment, source delivery and teardown.

Main Control performed one synthesis pass. Accounting and permission review were not reopened because the proposed control plane does not change accepted accounting or authority semantics.

Validation for this documentation task must prove:

- repository path, branch, local HEAD, upstream and `0/0`;
- empty index;
- candidate scope exactly the canonical package, runtime amendment, this amendment and README, alongside the unchanged untracked harness and four protected exclusions;
- `git diff --check HEAD`;
- Markdown whitespace and local-reference resolution;
- the four supplied pre-reconciliation documentation hashes matched before editing and the harness hash remains unchanged;
- absent controller, Dockerfile and initializer;
- no approved numeric workload/runtime limit;
- explicit continued deferral of host page-cache coldness, VM isolation, HTTP/CORS, Finance-to-AI access and accounting execution; and
- no code authoring, execution, infrastructure, image build, staging, commit, push or live action.

### 17.1 Future documentation staging allowlist

If and only if the Owner later authorizes documentation staging, the exact staging allowlist is:

1. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/finance-accounting-cycle2-gl-tb-controller-runner-control-plane-source-delivery-amendment-2026-07-18.md`;
2. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/finance-accounting-cycle2-gl-tb-synthetic-evidence-execution-package-2026-07-17.md`;
3. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/finance-accounting-cycle2-gl-tb-runtime-evidence-design-amendment-2026-07-18.md`; and
4. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/README.md`.

No source path is included.

## 18. Main Control decision

**Decision:** `controller_runner_control_plane_design_reconciled_for_docs_staging`

The Owner accepts the bounded control transport, terminal telemetry hold, immutable harness delivery, exact four-file future source scope, secret channel and teardown architecture. The four controlling documents are reconciled for a later documentation-staging decision. Source authoring, image materialization and synthetic execution remain unapproved.
