# Finance GL / Trial Balance Implementation Direction Counterpart Review

Date: 2026-07-22
Authority: Main Control v2
Document class: canonical architecture, delivery, assurance-proportionality and roadmap review
Repository: /home/deploy/erp-projects/erpai_project1_erpnext_ui_design
Branch: feature/erpnext-ui-design
Starting HEAD and upstream: 3a0873650aa5f73117eef8947725bbc8b6a75a5c
Starting ahead/behind: 0/0
Starting index: empty
Decision: gl_tb_direction_review_reconciled_for_owner_decision

## 1. Executive decision

The GL/TB track has made material source-level progress, but it has not delivered a usable Finance runtime capability. The completed work selected and bounded one defensible accounting direction, rejected unsafe native adapters, defined a strict aggregate contract, and authored substantial static evidence code. No GL/TB service, endpoint, page, route, report, scheduled job, authenticated runtime result, synthetic execution result or live acceptance exists.

The track is now at a governance-loop boundary. From the canonical capability-map decision through this starting HEAD, 30 relevant commits comprise 27 documentation-only commits and three source/test commits. The recent parser, runner, provenance and provider sequence did reduce real unknowns until it proved that the fixed provider set cannot supply a complete D1/O1 execution boundary. Continuing general provider or parser prerequisite work without a new Owner-funded infrastructure outcome would repeat that conclusion and would make the assurance mechanism the de facto Finance roadmap.

Main Control recommends the following combined direction, as a recommendation only:

1. select Option 1, STATIC-HOLD-1, for parser execution;
2. select Option 3 and move provider/isolation work to an inactive, separately owned evidence-platform track;
3. recommend one later, separately Owner-approved, bounded Level-A E2 path-identity and source-semantic attempt using exact literal paths, object/source identities, Q1-Q8 scope and fail-closed rules;
4. use terminal E2-B2 controlled failure only if that single bounded Level-A attempt cannot close;
5. group E3-B1, E3-B4, only the necessary E3-B2 work, E3-B5 and the E3-B3 synthesis into one Static Compatibility Closure Package; and
6. stop again for Owner review at completion or controlled failure of E2-B2 plus the grouped E3 final static synthesis.

This recommendation preserves gl_reconstructed as the sole source direction. It does not select native General Ledger, native Trial Balance, Query Report passthrough, ACB/cache mode or silent fallback. It does not approve diagnostic execution, controlled synthetic execution, source authoring, runtime implementation or release.

STATIC-HOLD-1 restores strategic control; it does not deliver GL/TB. The bounded Level-A E2 attempt may restore the static product/source path. The grouped E3 package completes the architecture checkpoint. Only a later Owner-approved product-authoring decision can begin delivery of a usable GL/TB capability.

The current accepted dependency graph still requires an E2-B1 path receipt before successful E2-B2. The future Level-A attempt therefore requires an explicit Owner-approved, claim-proportionate replacement or supersession of the parser-execution prerequisite. It may not bypass that prerequisite silently. Parser execution, D1/O1 provider work and Level-C promotion remain prohibited for the static E2 claim.

### 1.1 Independent-evaluation reconciliation

Main Control performed one evidence reconciliation only. No second counterpart-review cycle was opened.

| Independent-evaluation finding | Disposition | Reconciled effect |
| --- | --- | --- |
| Do not default immediately to terminal E2-B2 controlled failure | accepted | one bounded Level-A path-identity/source-semantic attempt becomes the preferred future recommendation; controlled failure is the one-attempt fallback |
| Consolidate E3 work into one grouped static outcome | accepted | E3-B1, B4, necessary B2, B5 and B3 become one Static Compatibility Closure Package with bounded parallel lanes and one synthesis |
| Clarify what delivery restored means | accepted_with_calibration | STATIC-HOLD-1 restores control, the E2 attempt may restore the static source path, grouped E3 closes architecture, and only later product authoring begins usable delivery |
| Identify the post-checkpoint product decision | accepted | the next Owner choice is FND-01, FND-02 and a Finance-owned gl_reconstructed adapter behind the existing Finance Control Desk |
| Preserve evidence-platform containment | accepted | current artifacts remain physically coupled under the app tests tree; independence requires later separate ownership and artifact boundaries |
| Calibrate the test-discovery finding | accepted_with_calibration | repository discoverability/import order is proven, but no protected CI/release discovery path is proven here; risk is conditional Medium pending an exact runner-path review |
| Keep the commit-ratio conclusion proportionate | accepted | the 27:3 ratio is evidence of imbalance only with zero product/runtime delivery and repeated provider findings; documentation volume alone is not failure |

No evaluation finding is rejected. Authority for the future Level-A E2 attempt, grouped E3 package, evidence-platform separation and post-checkpoint product authoring remains deferred_to_owner.

## 2. Authority, baseline and evidence rules

This review reconciles the latest accepted truth in:

- [Main Control v2 Transition Handoff](main-control-v2-transition-handoff-2026-07-16.md);
- [Codex Delivery Operating Model V1 Pilot](codex-delivery-operating-model-v1-pilot-2026-07-16.md);
- [Finance Capability Map and Integration Plan](finance-accounting-capability-map-integration-plan-2026-07-17.md);
- [GL / Trial Balance Scope and Implementation Plan](finance-accounting-cycle2-gl-trial-balance-scope-implementation-plan-2026-07-17.md);
- [C2B2-C2B6 Installed-Source Semantic Proof](finance-accounting-cycle2-c2b2-c2b6-installed-source-semantic-proof-2026-07-17.md);
- [Targeted C2B Gap-Closure Plan](finance-accounting-cycle2-targeted-c2b-gap-closure-plan-2026-07-17.md);
- [C2BG1 Source Fingerprint Receipt](finance-accounting-cycle2-c2bg1-targeted-gap-source-fingerprint-receipt-2026-07-17.md);
- [C2BG2-C2BG5 Static Semantic Read and Stop Receipt](finance-accounting-cycle2-c2bg2-c2bg5-static-semantic-read-stop-receipt-2026-07-17.md);
- [Synthetic Evidence Execution Package](finance-accounting-cycle2-gl-tb-synthetic-evidence-execution-package-2026-07-17.md);
- [Runtime Evidence Design Amendment](finance-accounting-cycle2-gl-tb-runtime-evidence-design-amendment-2026-07-18.md);
- [Controller-Runner Control Plane Amendment](finance-accounting-cycle2-gl-tb-controller-runner-control-plane-source-delivery-amendment-2026-07-18.md);
- [Compatibility and Protocol/Schema Stop](finance-accounting-cycle2-gl-tb-read-only-compatibility-protocol-schema-freeze-gate-2026-07-18.md);
- [Compatibility Gap Resolution Amendment](finance-accounting-cycle2-gl-tb-compatibility-gap-resolution-amendment-2026-07-18.md);
- [E1/E2-A/E3-A Evidence Receipt](finance-accounting-cycle2-gl-tb-e1-e2a-e3a-read-only-evidence-acquisition-2026-07-18.md);
- [E1 Fixed-Output and E2-B/E3-B Prerequisite Amendment](finance-accounting-cycle2-gl-tb-e1-fixed-output-e2b-e3b-prerequisite-freeze-amendment-2026-07-19.md);
- [Python Parser Contract](finance-accounting-cycle2-gl-tb-e2b1-python-stdlib-parser-provenance-contract-freeze-2026-07-19.md);
- [Parser Runner Provenance Stop](finance-accounting-cycle2-gl-tb-e2b1-parser-only-python-unittest-runner-provenance-invocation-freeze-2026-07-21.md);
- [Residual Import and Isolation Authority Amendment](finance-accounting-cycle2-gl-tb-e2b1-parser-runner-residual-import-isolation-authority-amendment-2026-07-22.md);
- [Provider Fingerprint Stop](finance-accounting-cycle2-gl-tb-e2b1-parser-sandbox-observer-bootstrap-provider-fingerprint-2026-07-22.md); and
- [Parser Provider Gap Resolution Amendment](finance-accounting-cycle2-gl-tb-e2b1-parser-provider-gap-resolution-amendment-2026-07-22.md).

Later accepted records supersede older labels and assumptions. This review does not reopen every historical phase. It uses older evidence only to explain current accepted truth or a current dependency.

Evidence must not be converted across these boundaries:

| Evidence | Maximum claim |
| --- | --- |
| Static source, documents, literal fixtures and hashes | source design, static semantics and fail-closed reasoning only |
| Diagnostic execution | non-promotable engineering feedback only |
| Controlled synthetic execution | only the exact observed synthetic facts under the approved envelope |
| Authenticated environment or live evidence | separately authorized environment-specific acceptance only |
| Controlled failure | one explicit unresolved dependency; never a pass |

No source test, fixture, source proof, synthetic result or representative smoke check can be called authenticated live acceptance.

## 3. Verified repository and protected state

At review start:

| Item | Verified state |
| --- | --- |
| Repository root | /home/deploy/erp-projects/erpai_project1_erpnext_ui_design |
| Branch | feature/erpnext-ui-design |
| Local HEAD | 3a0873650aa5f73117eef8947725bbc8b6a75a5c |
| Configured upstream | origin/feature/erpnext-ui-design |
| Upstream revision | 3a0873650aa5f73117eef8947725bbc8b6a75a5c |
| Ahead/behind | 0/0 |
| Index | empty |
| Existing dirty scope | exactly the four accepted unrelated exclusions |

Protected committed source identities:

| Source | SHA-256 | Review status |
| --- | --- | --- |
| [finance_gl_trial_balance_evidence_controller.py](../../erp_workspace_ui/tests/finance_gl_trial_balance_evidence_controller.py) | 69e67523d893b38b6559c75152f5802f6e5acf19642fd95d82cc2631d5a485b3 | read-only and unchanged |
| [test_finance_gl_trial_balance_e2b1_parser_fixtures.py](../../erp_workspace_ui/tests/test_finance_gl_trial_balance_e2b1_parser_fixtures.py) | b46dc6b02db57b0611346abad8665567fecf91456ce1db6fd488af9cbfea3afb | read-only and unchanged |
| [test_finance_gl_trial_balance_source_proof.py](../../erp_workspace_ui/tests/test_finance_gl_trial_balance_source_proof.py) | c8d0bb0556f9abb04e1be69c1d67a7f92c4ed37a64d8270d84339ad590e9cea5 | read-only and unchanged |

Protected unrelated exclusions:

| Path | Required state | SHA-256 |
| --- | --- | --- |
| impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py | modified, unstaged | 01668e175610d9d090ea51018badbde8b021103afe13ed878782a58b8ce3b224 |
| impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/browser_supplier_payables_fixture_diagnostic.py | untracked, unstaged | d9822184b26f3c1ebaf5b93663b1f6c3a495b6482f013092d955748dfdf963c5 |
| impl_factory/05_custom_logic/custom_app/erp_workspace_ui/ui_smoke/sales_final_acceptance_audit.js | untracked, unstaged | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| impl_factory/05_custom_logic/custom_app/erp_workspace_ui/a.out | untracked, unstaged | 0063411e61152850243132aa87ef12844a8724adb671bf4f38793bcd2b1ce339 |

The live deployment tree was not accessed.

## 4. Current-state truth matrix

| Area | Current evidence-supported determination | State and claim level |
| --- | --- | --- |
| Accounting semantics | Installed-source work proves a bounded algorithm narrative for opening, movement, closing, hierarchy and root totals. The sole candidate is aggregate raw-GL reconstruction. No result has executed. | materially advanced static design; Level A only |
| Permissions and leakage | Native reports are rejected; complete-chart authority, runtime User Permission, Custom DocPerm, masks, shares, strict settings and custom roles remain unresolved. The harness contains a strong static denial design and identity suppression, but it has not run. | static design and fixtures; no effective permission proof |
| Controller | The 633-line file is a pure E2-B1 response parser. Its header defers acquisition, orchestration, exits and promotion. It has no CLI, parent/child control plane, IPC, watchdog, evidence writer, recovery or teardown. | committed source; not an executable controller |
| Parser fixtures | Ten literal synthetic unittest methods cover commit/tree projections, Q1-Q8 classification, schema and encoding boundaries, identity suppression and fail-closed classifications. They have never been imported or executed under an approved gate. | strong static fixture package; Level A only |
| Database harness | The 6,911-line experimental test surface targets gl_reconstructed with A01-A22, P01-P28 and S01-S08 fixtures. It imports Frappe/MariaDB at module load, needs site and database credentials, creates synthetic database mutations and threaded workload readers, and remains unexecuted. | substantial evidence code; inaccessible without Frappe/site/database infrastructure |
| Synthetic environment | Disposable database/site/cache/network/volume, cgroup, marker, secret, discard and teardown contracts are extensively designed. The runner Dockerfile and initializer are absent; the current parser has no control plane; no environment was materialized. | Level C design only |
| Provider/isolation track | bwrap is absent. unshare and setpriv are partial primitives; strace is a leakage-bearing observer candidate; timeout is only an outer ceiling. No sealed root, inherited-FD closure, Unix-socket denial, process/thread denial, complete observer or teardown composition exists. | conclusive provider stop for the fixed set |
| E1 | Initial fixed-output evidence was incomplete. Later documents corrected the planning contract, but the default Docker socket remains unapproved and no disposable isolated endpoint exists. | blocked formal infrastructure evidence; not on the static accounting path |
| E2-B1 | Parser and fixtures exist. Formal public metadata acquisition remains unapproved and blocked by the chosen D1/O1/bootstrap/control-plane standard. | current formal claim requires execution; accounting semantics do not |
| E2-B2 | Successful source reading is currently ineligible because no accepted real E2-B1 literal-path/object-ID receipt exists. Q1-Q8 remain important to least privilege, snapshot and reconnect design. | prefer one later Owner-approved bounded Level-A path/source attempt; controlled failure only if it cannot close |
| E3-B1 | Fixed-hash Frappe lifecycle and harness mapping remains an eligible bounded lane. | included in one grouped Static Compatibility Closure Package |
| E3-B2 | Waits for a fixed installed-Python identity and exact CPython source binding; include only what is necessary where callback/finalization behavior affects lifecycle SQL and synthesis. | conditional lane inside the grouped package |
| E3-B3 | Numbering is not execution order. It remains the one final Main Control synthesis after the applicable grouped lanes and E2-B2 result. | terminal step of the grouped package |
| E3-B4 and E3-B5 | B4 retains an exact S07 ERPNext/Frappe source/schema allowlist. B5 derives its disposition from the E2-B2 account/host/process/termination result. | bounded lanes in one grouped package; B5 remains sequential on E2 |
| E3-B final synthesis | It must retain every unsupported or controlled-failure fact and may not invent grants, callback behavior, physical schema or reconnect proof. | one grouped architecture checkpoint, not serial amendments |
| E4 | Controlled runtime canaries remain deferred and unapproved. E4 is required before runtime compatibility, physical-schema, permission, snapshot and reconnect claims, but not before source-direction selection or this static checkpoint. | deferred Level C |
| Runtime Finance capability | No GL/TB runtime capability exists. The committed Finance service still returns ledger posture unavailable and states that account balances, ledger rows, statements and trial-balance figures remain blocked at finance_accounting/service.py:2776-2781. | no executable business capability |
| Finance Cycle 2 status | The pre-implementation/source-proof track has advanced materially through static semantics, contracts and evidence code. Under the accepted governance vocabulary, Finance Cycle 2 runtime implementation has not started. | pre-implementation; do not describe as a started runtime cycle |

## 5. Accounting capability matrix

| Facet | Completed static outcome | Planned or unexecuted boundary |
| --- | --- | --- |
| Opening | Raw-GL candidate separates eligible pre-period and opening-entry treatment; native formula sources are mapped. | No permission-equivalent or executed opening; no production PCV tie-out. |
| Movement | Inclusive from-date through to-date movement, cancelled-row exclusion and opening-row treatment are statically defined. | No authenticated database result or same-population proof with opening. |
| Closing | Exact equation closing debit/credit equals opening plus movement, with net debit minus credit. | No synthetic or runtime execution. |
| Exact balancing | Decimal and minor-unit fail-closed rules are authored; visible-subset balance is prohibited. | No executed exact equality or complete-chart permission proof. |
| Hierarchy | Authorized full-chart set, parent/group integrity, zero-account completion and recursive aggregation are authored. | Effective complete-chart authority remains unresolved. |
| Fiscal boundaries | Exactly one containing fiscal year and strict invalid/cross-year rejection are designed; native silent date clamping is rejected. | Active fiscal settings, PCV state and closed-period behavior remain untested. |
| Cancellation | Candidate excludes is_cancelled rows and the Owner accepted reporting-only deferral. | Freeze/cancellation caller mismatch remains High for cancellation, freeze, close, certification or audit claims. |
| Finance Books | Bounded posture is company default book plus blank/NULL unbooked rows with one identical opening/movement rule. | Cohort parity is unexecuted and remains High. Non-default/all-book modes are unsupported. |
| Company and currency | Exactly one company, matching account company and company base currency are statically enforced. | Effective company/User Permission behavior, other currencies, intercompany and consolidation are deferred. |
| Dimensions | Zero active dimensions and no slice is the only candidate. Dimension filters or positive active-dimension state fail closed. | Cost Center, Project and custom-dimension slices are unsupported. |
| PCV/ACB cache | Native source behavior is understood enough to reject it. | Completed-state selection, key normalization, uniqueness, completeness, retry safety, parity and snapshot equality remain unproved; cache mode stays rejected. |
| Output and identity | Aggregate-only, identity-free success and generic no-partial failures are designed. | No runtime leakage, logs or response evidence. |
| Accounting execution | Explicitly excluded. | Cancellation, close/reopen, frozen-period control, audit certification, journals, payments and every mutation remain deferred. |

Completed business capability is therefore zero executable GL/TB functionality. Completed architecture value is substantial: unsafe adapters were removed from consideration, a single bounded source direction survived, and its accounting limits are explicit.

## 6. Current source and execution truth

### 6.1 Controller

Committed-source evidence at finance_gl_trial_balance_evidence_controller.py:1-12 and 578-633 shows:

- a parser-only purpose;
- five standard-library imports;
- validation and canonical projection logic;
- one parser entry function; and
- no acquisition, network, database, runner, supervisor, process control, signal, IPC, watchdog, JUnit, evidence promotion, recovery or teardown implementation.

The filename must not be interpreted as proof that a controller exists. A response-size authority also remains deferred.

### 6.2 Ten parser fixtures

The ten static methods cover:

1. canonical commit bodies, reordered equivalence and identity suppression;
2. canonical tree bodies, Q1-Q8 classification and deterministic projection;
3. missing-category and cross-category ambiguity rejection;
4. UTF-8, BOM, malformed JSON, duplicate-key, nonfinite and surrogate boundaries;
5. required schema, unknown/additive fields and verification enums;
6. commit/tree identity and invocation-argument failures;
7. HTTPS URL and RFC3339 timestamp boundaries;
8. tree modes, types, sizes, paths, collisions, duplicates, truncation and late failure;
9. deterministic rejected-entry counts and tuple hash; and
10. controlled parser rejection versus internal fail-closed error.

They use synthetic values and lazy parser loading. The suite is conventionally discoverable and raises a gate error when its explicit environment authority is absent. No import, collection or execution has occurred. Static fixture review proves expected source intent, not interpreter compatibility, side-effect denial, acquisition correctness or accounting.

### 6.3 Database harness

The database harness is a different risk surface:

- it imports Frappe and MariaDBDatabase at lines 38-39 before the class-level skip gate;
- it loads site/application and synthetic database credentials;
- it constructs network database connections;
- it creates preparer, reader, verifier, topology, reconnect and writer behavior;
- it contains accounting, permission/leakage and snapshot/concurrency fixture catalogs; and
- it remains experimental evidence code under the tests directory, not production runtime.

Import alone does not establish a database connection, and the class requires its exact synthetic gate before setup. Ordinary repository-root discovery exposes the Frappe/MariaDB module import surface before the skip. Repository-level discoverability and import ordering are proven; an actual protected CI or release-runner path that performs this discovery is not proven and was not inspected. The current finding is therefore a conditional Medium release-containment risk pending a separately approved exact runner-path review. It is not evidence of a leak or execution.

### 6.4 Synthetic environment

The accepted Level-C design specifies isolation, provenance, one stack per workload point, primary-connection pinning, replica denial, repeatable-read snapshot checks, cgroup memory evidence, discard-only incomplete runs, atomic point promotion, sanitized manifests and exact teardown. None was materialized.

The current source set does not implement that environment:

- no runner Dockerfile exists;
- no site initializer exists;
- the parser file contains no host control plane;
- the database harness still contains an environment-backed root-secret reference that later design intended to replace with service-scoped RAM-backed secret files; and
- no image, site, database, cache, network, volume, secret, marker, cgroup or evidence directory was created.

## 7. Delivery chronology and loop analysis

### 7.1 Bounded history

The chronology begins with the canonical capability-map commit cfdfe80 on 2026-07-17 and ends at starting HEAD 3a08736 on 2026-07-22:

| Period | Commits and outcome | Delivery value |
| --- | --- | --- |
| Capability and source direction | Capability map, five-phase plan, inventory, governance, source fingerprint, C2B proof and targeted semantic receipt | high: ranked GL/TB, rejected unsafe native paths and selected sole raw-GL candidate |
| Synthetic architecture | Synthetic package, runtime amendment, controller-runner design, compatibility stop and resolution | high for future formal evidence: exposed snapshot, permission, secret, lifecycle and teardown requirements |
| Static product prerequisites | E1/E2-A/E3-A receipt, prerequisite and wire/toolchain/parser contracts | mixed: E2-A and E3-A materially narrowed facts; later toolchain work increasingly served acquisition machinery |
| Source authoring | 0867867 parser correction/controller source, 3adb869 canonical fixtures/harness source, d639d49 parser-fixture isolation and harness update | real source delivery, but all three commits changed evidence/test surfaces only |
| Runner and provider sequence | runner stop, provenance stop, residual import/isolation amendment, provider fingerprint stop and provider resolution | initially useful; conclusively proved the fixed set cannot close D1/O1; another general pass would be duplicative |

Exact bounded totals:

- 30 relevant commits;
- 27 documentation-only commits;
- three source/test commits;
- zero product/runtime implementation commits;
- zero approved parser, fixture, harness, accounting or synthetic executions; and
- zero live acceptance or deployment actions.

The 27:3 ratio is not by itself a quality verdict. Several documents changed architecture and prevented an unsafe implementation. It is evidence of a delivery imbalance only when combined with the absence of product code and the repeated provider conclusion.

### 7.2 Findings that materially changed architecture

- native General Ledger, native Trial Balance, Query Report passthrough and ACB/cache reuse were rejected;
- gl_reconstructed became the sole candidate;
- cancellation was bounded to a reporting-only deferral;
- one-company, company-base-currency, default-book-plus-unbooked and zero-dimension posture was frozen;
- complete-chart permission equivalence and coherent primary snapshot became explicit runtime Blockers;
- incomplete/killed evidence became discard-only;
- workload bounds changed from artificial exact milliseconds to evidence-derived workload and causal ceilings;
- controller-owned isolation, promotion and teardown were separated from the harness;
- parser and database fixtures were separated; and
- the fixed provider set was conclusively shown insufficient for D1/O1.

### 7.3 Repeated or diminishing-yield findings

The following facts recur across the runner-provenance, residual-import, provider-fingerprint and provider-resolution records:

- no sealed source root;
- no inherited-FD closure;
- no complete network/Unix-socket denial;
- no process/thread denial;
- no independent complete observer;
- no pre-import bootstrap/control plane;
- no deterministic recovery and teardown; and
- no execution authority.

The fingerprint gate established these facts. The provider-resolution amendment usefully converted them into an Owner choice. A further general provider, parser, architecture or provenance gate without a named new provider and funded outcome would restate an accepted limit.

### 7.4 Loop conclusion

The project has not been a pure documentation loop: early source and evidence work materially improved accounting and security architecture. It has now reached a loop boundary because the assurance platform has started determining the roadmap for a Level-A static checkpoint.

Assurance cost is disproportionate when a ten-case metadata parser must first acquire a new sandbox/provider/control-plane platform before independently eligible source analysis can continue. That platform may be justified later for credential-bearing controlled synthetic evidence shared across suites. It is not proportionate as an active GL/TB parser prerequisite today.

Opportunity cost is concrete. GL/TB was ranked first in the Finance roadmap and is a foundation for statements, close, cash/liquidity and consolidation. Payment Schedule/aging work and other Finance domains also remain deferred while evidence-platform prerequisites consume the active sequence.

## 8. Assurance proportionality

| Level | Definition | Current state | Proper next use |
| --- | --- | --- | --- |
| A - static source evidence | reviewed source, literal fixtures, hashes, schemas and static reasoning | current maximum attained level | one bounded E2 path/source attempt and one grouped E3 Static Compatibility Closure Package |
| B - diagnostic parser execution | synthetic fixtures executed for engineering feedback only | absent and unapproved | not recommended now |
| C - controlled synthetic evidence | approved isolation, observation, provenance, discard and teardown | extensively designed but unavailable | later formal runtime/source-proof claim only |
| D - runtime or live acceptance | authenticated, permission-aware, company-scoped and environment-specific | absent and deferred | later runtime/live release gate |

### 8.1 Level required next

The canonical checkpoint - completion or controlled failure of E2-B2 plus E3-B final static synthesis - is a Level-A product/source checkpoint. The preferred route is one later bounded Level-A attempt that first binds exact E2 path/object identities and then reads only the approved source semantics for Q1-Q8. It requires a new Owner-approved replacement or supersession of the current parser-execution prerequisite. E3-B1 and E3-B4 are explicitly static, necessary E3-B2 work is source binding only, and E3-B3 remains a static synthesis.

Level C is legitimate before promoting zero-side-effect, harness-unreachability, snapshot, permission, reconnect or controlled synthetic claims. It was allowed to become an implicit prerequisite for unrelated Level-A progress because the current E2-B1 acquisition contract requires formal parser execution before path promotion. That is an assurance-policy dependency, not an accounting equation or Finance permission dependency.

### 8.2 Diagnostic Level B

Level B has modest engineering value: it could reveal syntax, interpreter, import-alias and fixture/runtime defects. It could never prove:

- E2-B1 acquisition closure;
- E2-B2 source semantics;
- E3-B closure;
- GL/TB accounting correctness;
- database-harness unreachability;
- zero side effects;
- runtime compatibility;
- release readiness; or
- live acceptance.

Under the current repository structure, a simple on-host Level-B lane is not cleanly supportable under the accepted requirement that it must not expose the database harness. Exact-file loading narrows ordinary imports but does not deny direct reads, ambient credentials or file descriptors, Unix sockets or network. Ordinary test discovery can import the Frappe/MariaDB harness before its class skip. Default unittest failures can also retain repository paths and fixture values.

A conceptually safer Level-B lane would need a new clean offline runner containing only exact controller and fixture blobs, with no repository mount, database harness, credentials, inherited descriptors or network, plus sanitized discard-only output. That creates a new runner/provider/source surface whose cost is not materially lower than the ten parser fixtures justify.

Main Control therefore rejects Option 4 now. Static-only evidence is more honest and efficient. Reconsider Level B only after a concrete parser change creates a real debugging need and the Owner explicitly accepts that its result is non-promotable.

## 9. Dependency classification and critical-path reconstruction

| Dependency | Classification | Current critical-path effect |
| --- | --- | --- |
| raw-GL opening/movement/closing, Decimal, hierarchy and fiscal contract | mandatory accounting dependency | preserve; static contract exists, later execution required for runtime claim |
| complete authorized chart, exact company, identical opening/movement book and permission scope | mandatory permission/security dependency | blocks balanced runtime claim, not static direction |
| one coherent primary snapshot and fail-closed reconnect | mandatory accounting and security dependency for runtime | Level C/E4 later; not needed for static checkpoint |
| E2-B1/E2-B2 path identities and Q1-Q8 MariaDB source semantics | mandatory product/source compatibility for direct database least privilege and reconnect design | prefer one Owner-approved bounded Level-A attempt; controlled failure only if that attempt cannot close |
| E3-B1 Frappe lifecycle/leakage mapping | mandatory product/source compatibility | bounded parallel lane inside one grouped closure package |
| E3-B2 CPython/Frappe callback binding | mandatory product/source compatibility where finalization affects lifecycle SQL | include only necessary source binding inside the grouped package |
| E3-B4 S07 schema-source closure | mandatory product/source compatibility | bounded parallel lane inside the grouped package |
| E3-B5 reconnect contract | mandatory security dependency only if E2-B2 supports it | grouped package lane, sequential on the E2 result |
| E3-B3 final synthesis | mandatory governance/architecture checkpoint | one terminal synthesis for the grouped package; must preserve failures |
| E1 Docker endpoint and image metadata | formal synthetic-evidence dependency | remove from immediate static critical path |
| D1/O1, sealed root, import ledger, supervisor/runner, IPC, watchdog, recovery and teardown | formal synthetic-evidence dependencies | freeze and move to inactive infrastructure track |
| ten-fixture Level-B execution | optional diagnostic dependency | reject/defer |
| E4 controlled canaries | deferred release/runtime dependency | required before runtime compatibility, not before static checkpoint |
| CORS/HTTP fingerprint | deferred endpoint/release dependency | not on internal/static path |
| cancellation freeze remediation | deferred accounting dependency for cancellation, close/freeze/audit claims | reporting-only scope excludes those claims |
| repeated general provider/provenance amendments | self-imposed or duplicative governance dependency after fixed-set conclusion | freeze |

### 9.1 Shortest evidence-supported path

~~~text
Owner selects STATIC-HOLD-1 + dormant infrastructure separation
and explicitly approves a claim-proportionate Level-A E2 prerequisite replacement
        |
        +--> one bounded E2 path-identity/source-semantic attempt
        |       |
        |       +--> E2-B2 completion
        |       |
        |       +--> terminal controlled failure if the attempt cannot close
        |
        +--> one GL/TB Static Compatibility Closure Package
                |
                +--> parallel: E3-B1 + E3-B4 + necessary E3-B2
                |
                +--> sequential: E3-B5 from the E2 result
                |
                +--> one E3-B3 Main Control synthesis
                        |
                        +--> mandatory Owner checkpoint
                                |
                                +--> separate FND-01/FND-02/product-authoring decision
~~~

STATIC-HOLD-1 cannot be silently treated as an E2-B1 pass. The Owner must explicitly approve the claim-proportionate Level-A replacement or supersession before the single E2 attempt. Parser execution, D1/O1 work and Level-C promotion remain outside that attempt. If exact literal paths, object/source identities or Q1-Q8 semantics cannot close under its frozen rules, the lane ends in controlled failure without another search.

### 9.2 Parallel, sequential and frozen work

May proceed as bounded parallel lanes inside one later Owner-approved GL/TB Static Compatibility Closure Package:

- E3-B1 using the accepted E3-A inputs and fixed harness hash;
- E3-B4 using its exact ERPNext/Frappe S07 path allowlist; and
- only the necessary E3-B2 installed-Python/source binding required for final synthesis.

Each lane retains its exact path authority and specialist owner. An unsupported material fact is recorded once in the final synthesis and does not automatically create a new prerequisite search or amendment.

Must remain sequential:

- the E2 source-semantic step after exact path/object identities are accepted under the later Owner-approved Level-A replacement;
- E3-B5 after E2-B2;
- the single E3-B3 synthesis after the grouped B1/necessary-B2/B4/B5 and E2-B2 dispositions; and
- any E4 or source-authoring decision after the final static Owner checkpoint.

Must be frozen:

- parser fixture execution;
- E1;
- provider nomination/acquisition;
- controller control-plane authoring;
- Docker, image, secret and synthetic environment work;
- general parser/provider/provenance review; and
- runtime Finance implementation.

Must move to a separate inactive track:

- reusable provider/isolation, observer, sealed-root, supervisor/runner, IPC, watchdog, evidence promotion, recovery and teardown capability.

The exact future trigger for that track is all of:

1. a named Level-C claim that cannot close by static evidence or controlled failure;
2. demonstrated reuse beyond the ten parser fixtures or necessity for the credential-bearing database harness;
3. an Owner-nominated immutable provider/composition;
4. a named infrastructure owner and bounded budget;
5. an exact source/artifact/environment boundary; and
6. explicit supply-chain, privilege, leakage and teardown authority.

Without all six, the track remains inactive.

### 9.3 Ownership locks

| Surface | Owner/lock |
| --- | --- |
| Controller, parser fixture and database harness | frozen at the verified hashes; no edits or execution |
| E2-B path identities and Q1-Q8 | one future exact source-evidence owner only; literal paths/object identities and fail-closed rules; no provider team inference |
| Grouped E3 package | one coherent outcome with separate Frappe lifecycle, Python/callback and S07 schema specialist locks |
| E3-B1 lifecycle/leakage | Frappe static specialist; no source edits or runtime |
| Necessary E3-B2 Python/callback | Python/Frappe source specialist; exact identity/path allowlist |
| E3-B4 S07 schema | ERPNext/Frappe schema specialist; exact paths only |
| E3-B5 and E3-B3 | B5 consumes only the accepted E2 result; Main Control owns the one final synthesis |
| Provider infrastructure | separate inactive owner and artifact boundary; no Finance repository or live authority |
| Finance runtime, Shared UI, routing, registries and workspace behavior | remain protected and outside this review |

## 10. Strategic option assessment

### 10.1 Option 1 - STATIC-HOLD-1

- Business value: honestly preserves the static parser and fixture work and stops sunk-cost escalation.
- Accounting risk: lowest; makes no new accounting claim.
- Permission/leakage risk: lowest while nothing executes.
- Engineering complexity: minimal.
- Infrastructure impact: none.
- Source/runtime overlap: none if the three protected sources stay frozen.
- Evidence credibility: high for the static/no-execution claim.
- Time/evidence cost: low.
- Reversibility: complete.
- Effect on roadmap: positive only when paired with the one Owner-approved Level-A E2 attempt and its terminal fallback; alone it leaves E2-B2 blocked.
- Owner authority required: explicit selection of STATIC-HOLD-1 and rejection of automatic provider progression.
- Exit/stop condition: parser/provider lane stays stopped until a new named Level-C trigger is approved.

### 10.2 Option 2 - E-PURSUE + D-NOMINATE

- Business value: could eventually support formal parser and wider controlled-synthetic evidence.
- Accounting risk: neutral to equations, but high opportunity cost delays actual accounting work.
- Permission/leakage risk: medium/high due to provider supply chain, privileges, tracing, raw observer data and new runtime surfaces.
- Engineering complexity: very high; provider provenance, sealed root, syscall/process/network denial, observer, bootstrap, IPC, watchdog, recovery and teardown all remain.
- Infrastructure impact: substantial and likely broader than the current repository boundary.
- Source/runtime overlap: may force new artifacts or scope beyond the controller-only boundary.
- Evidence credibility: potentially high only after complete Level-C closure; currently zero execution authority.
- Time/evidence cost: highest and not proportionate to a ten-case metadata parser.
- Reversibility: good before acquisition; lower after provider/runtime surface creation.
- Effect on roadmap: keeps the assurance platform on the Finance critical path and delays E3 and wider Finance work.
- Owner authority required: exact provider/composition nomination, provenance/read authority, infrastructure owner/budget, later activation and execution gates.
- Exit/stop condition: stop immediately on missing immutable identity, privilege, sealed-root, observation, source-scope or teardown proof.

### 10.3 Option 3 - separate provider/isolation infrastructure track

- Business value: preserves future reusable assurance capability without blocking GL/TB static progress.
- Accounting risk: low if the track is inactive and cannot change Finance.
- Permission/leakage risk: low while inactive; future risk must be separately approved.
- Engineering complexity: isolated from the Finance outcome and funded only when justified.
- Infrastructure impact: none now; later explicit artifact/environment scope.
- Source/runtime overlap: prohibited unless a later Owner allowlist names it.
- Evidence credibility: prevents weak provider evidence from being mistaken for Finance closure.
- Time/evidence cost: low now; later charged to a reusable platform outcome.
- Reversibility: complete while inactive.
- Effect on roadmap: removes E1/D1/O1/controller machinery from the immediate static critical path.
- Owner authority required: decision to separate and the six-part future trigger; no implementation authority.
- Exit/stop condition: no work starts until every trigger condition exists.

### 10.4 Option 4 - diagnostic-only parser execution

- Business value: limited engineering feedback on syntax/import/fixture behavior.
- Accounting risk: no legitimate accounting value; promotion risk is significant.
- Permission/leakage risk: unacceptable on the current host under the no-harness-exposure rule; a clean offline artifact-only runner would be needed.
- Engineering complexity: moderate/high once isolation, loading and sanitization are handled honestly.
- Infrastructure impact: a new runner or source surface.
- Source/runtime overlap: risks exposing the database harness or repository paths.
- Evidence credibility: Level B only and permanently non-promotable.
- Time/evidence cost: greater than current value.
- Reversibility: high before creating the runner.
- Effect on roadmap: likely opens another design series without advancing E2-B2 accounting semantics.
- Owner authority required: explicit diagnostic-only decision and exact two-file/offline runner boundary.
- Exit/stop condition: reject now; reconsider only after a concrete parser defect creates a material debugging need.

### 10.5 Option 5 - stop or redesign the proof approach

- Business value: highest when limited to claim-proportionate proof and the accepted static checkpoint.
- Accounting risk: low only if gl_reconstructed and every fail-closed boundary remain unchanged.
- Permission/leakage risk: controlled by retaining complete-chart, identity suppression and no-partial rules.
- Engineering complexity: lower than building an evidence platform solely for the parser.
- Infrastructure impact: no provider or Level-C infrastructure; the future Level-A attempt is bounded read-only path/source evidence only.
- Source/runtime overlap: none at this review stage.
- Evidence credibility: high if exact path/object/source identities and Q1-Q8 facts close under frozen rules, or remain explicit controlled failures after the single attempt.
- Time/evidence cost: bounded.
- Reversibility: high.
- Effect on roadmap: gives one proportionate chance to restore the static product/source path before falling back to the canonical controlled-failure checkpoint.
- Owner authority required: separately approve the exact Level-A replacement/supersession, literal path/object/source boundaries, Q1-Q8 scope and fail-closed rules.
- Exit/stop condition: one attempt only; no parser execution, provider work, new accounting source or native/fallback resurrection; failure closes the lane and is retained by the grouped E3 synthesis.

### 10.6 Ranking

1. Option 1 + Option 3 + the bounded Level-A E2 attempt and controlled-failure fallback from Option 5 - recommended.
2. Immediate terminal controlled failure - honest fallback only after the single Level-A attempt cannot close; not the preferred default.
3. Option 4 - technically conceivable in a clean offline runner, but rejected/deferred as disproportionate.
4. Option 2 - credible only as a separately funded reusable evidence-platform outcome; not recommended for the current GL/TB critical path.

## 11. Independent reviews and Main Control disposition

Exactly one bounded review was performed for each required perspective, followed by this single synthesis.

| Perspective | Independent challenge and finding | Main Control disposition |
| --- | --- | --- |
| Accounting and ERP semantics | Provider/parser isolation does not change opening, movement, closing, hierarchy, fiscal, book or balance truth. Complete chart, same population and coherent snapshot block runtime claims, not static source selection. | accepted; no new accounting Blocker from provider work |
| Security, permissions and leakage | On-host diagnostic execution cannot prove the database harness unreachable; Level C remains valid for formal zero-side-effect claims. Native adapters remain permission-unsafe. | accepted; reject Level B now and retain native rejection |
| Platform and test architecture | The controller is parser-only; the environment is unmaterialized; fixed tools cannot provide D1/O1. Option 1+3 with controlled failure is proportionate containment. | accepted_with_calibration; one bounded Level-A E2 attempt precedes the fallback |
| Enterprise architecture and integration | GL/TB remains a Finance-owned internal aggregate direction with no Shared UI, routing, registry or protected-workspace dependency at the static checkpoint. Evidence-platform concerns should have separate ownership and must not become a cross-workspace runtime. | accepted, subject to inactive-track and ownership-lock rules |
| Delivery, roadmap and governance | STATIC-HOLD-1 alone cannot bridge E2-B1 to E2-B2. A terminal failure or explicit protocol reset is required. Thirty commits, zero product runtime and repeated provider conclusions show assurance has become the de facto roadmap. | accepted_with_calibration; recommend one explicit Level-A reset/attempt before terminal failure |
| Release containment | No runtime release is possible; conventional test discovery can expose/import test surfaces before gates; source/live and exact staging boundaries must remain hard. | accepted_with_calibration; repository exposure is proven, but actual CI/release discovery is not, so risk is conditional Medium |

No reviewer recommended weakening Level C for a formal claim. No reviewer found evidence that gl_reconstructed should be replaced. No Blocker or High was accepted without exact committed-source or controlling-document evidence.

## 12. Findings by severity

### 12.1 Blockers

1. Runtime balanced-GL/TB claim: complete authorized chart and permission-equivalent opening/movement are unproved. Native Trial Balance remains rejected.
2. Runtime coherent result: one primary consistent snapshot, replica exclusion and reconnect behavior are unproved.
3. Formal Level-C parser execution: no complete D1 provider, independent O1, pre-import bootstrap or executable controller/control plane exists.
4. Formal GL/TB synthetic execution: the accepted disposable environment is not materialized and current source does not implement the complete design.
5. GL/TB release: no runtime/product implementation, E4 evidence, Level-D acceptance or source-to-live approval exists.

These Blockers do not block this documentation review or the Level-A static checkpoint. They block the specifically named execution, runtime or release claims.

### 12.2 High

1. E2-B2 successful closure has no bridge while STATIC-HOLD-1 is selected; the current accepted graph still requires an E2-B1 literal-path receipt.
2. Effective User Permission, Custom DocPerm, masks, shares, strict settings, custom roles and complete-chart authority remain unresolved for runtime.
3. Finance Book opening/movement cohort parity remains unexecuted.
4. Cancellation freeze-call mismatch remains material to cancellation, freeze, close, audit or certification claims and is accepted only as reporting-only deferral.
5. A new provider would create supply-chain, privilege, leakage, source-scope and teardown risk without advancing accounting semantics.
6. Keeping provider work on the Finance critical path delays the bounded E2 source path, grouped E3 closure and wider Finance outcomes.
7. Broad staging or cleanup could contaminate the exact documentation scope with four protected exclusions.
8. Assurance promotion could turn extensive documentation into an unsupported impression of runtime readiness.
9. Option 3 is not physically separated at HEAD: all three evidence sources remain under the production app tests tree. A future platform cannot be called independent until a separate repository/package or explicit non-importable artifact boundary, owner, CI boundary and deployment boundary are approved.

### 12.3 Medium

1. The controller filename overstates implemented orchestration.
2. The parser response-size authority remains deferred.
3. The last provider-resolution document mainly packaged a conclusion already established by the fingerprint stop; another general pass would have no new decision yield.
4. Level-B feedback has real but small value and does not justify a new runner today.
5. Minimal synthetic app coverage would not prove future production active-app parity.
6. Repository-level test discovery exposure is concrete: the parser fixture is conventionally discoverable and errors without its gate, while the database harness imports Frappe/MariaDB before its class skip. No protected CI or release-runner path performing that discovery is proven or inspected, so the release risk remains conditional Medium.

### 12.4 Rejected findings or conclusions

- No actual credential, network, database, accounting or identity leak occurred.
- Provider failure is not an accounting-design failure.
- Static fixtures are not executed evidence.
- Controlled failure is not a pass.
- The database harness is not production runtime.
- Source proof is not release readiness.
- No current evidence supports native GL/TB, Query Report, ACB/cache or fallback resurrection.
- Documentation volume alone is not treated as proof of failure; decision yield and delivery impact are the test.

## 13. Main Control synthesis and work disposition

### Stop

- all parser execution and diagnostic-runner design;
- E-PURSUE + D-NOMINATE on the Finance critical path;
- E1 and Docker endpoint work;
- controller control-plane authoring;
- general provider, parser, architecture and provenance review;
- synthetic environment creation or execution;
- runtime GL/TB implementation;
- HTTP/CORS and Finance-to-AI work; and
- any release, staging, commit, push or live action.

### Resume only after separate Owner approval

- one bounded Level-A E2 path-identity/source-semantic attempt under an explicitly superseding claim-proportionate protocol;
- terminal E2-B2 controlled failure only if that one attempt cannot close; and
- one GL/TB Static Compatibility Closure Package containing E3-B1, E3-B4, necessary E3-B2, E3-B5 and the E3-B3 synthesis.

### Grouped static closure

Inside the single grouped package, E3-B1 and E3-B4 may proceed as bounded parallel lanes because their authority, inputs and files do not overlap. Only necessary E3-B2 source binding may join them after its exact identity/path authority. E3-B5 remains sequential on the E2 result, and Main Control performs one E3-B3 synthesis. Specialist ownership and exact path allowlists remain distinct, but there are no serial lane-by-lane amendments.

### Separate inactive track

Provider/isolation infrastructure moves off the Finance critical path but does not become an automatically active parallel stream. It receives no source, provider, package, Docker, secret, runtime or network authority. It may resume only under the six-part trigger in Section 9.2.

### Protected integrations

Sales, Procurement and Warehouse routes, landing behavior, role authority, request isolation, managed navigation and accepted browser behavior remain unchanged. Finance Cycle 1 remains bounded aggregate/read-only. Shared UI, boot routing, child-page helpers, registries, governance manifests, landing precedence and AI Assistant remain unchanged.

No future GL/TB source task may modify Shared UI or another workspace incidentally. A later runtime endpoint or UI requires separate impact analysis, cross-workspace regression evidence, exact file allowlists, Finance permission gates and separate live approval. Finance-to-AI remains prohibited until an independent authority, company-scope, identity-leakage and no-accounting-authority decision is approved.

The enterprise ownership boundary is:

- Sales remains the owner of Sales workspace behavior; GL/TB consumes only lifecycle-proven accounting facts, never Sales UI payloads or Sales role authority.
- Procurement remains the owner of Procurement workspace behavior; Procurement access cannot become AP or GL authority.
- Warehouse custom workflow state is not Stock Ledger, valuation or GL truth. Initial aggregate GL/TB needs no Warehouse change; later inventory accounting requires a separate SLE-to-GL reconciliation and Warehouse regression gate.
- Shared UI owns domain-neutral presentation and lifecycle only. It must receive an already-authorized public schema and may not derive accounting semantics.
- Routing, registry, boot and governance surfaces remain Main Control or shared-runtime locks. Landing precedence remains Sales > Procurement > Finance > Warehouse.
- AI Assistant is neither an accounting source, approved GL/TB consumer nor accounting actor. Existing Finance-to-AI access remains a deferred High stop.

The current evidence artifacts are not yet an independent platform because they remain committed below erp_workspace_ui/tests. Separation in this recommendation is a dormant ownership and future-artifact decision, not a claim that physical separation already exists. Any future platform must use a separate repository/package or explicitly non-importable artifact boundary and must have no automatic app-test discovery, boot, hook, route, registry, deployment, credential or CI coupling.

After the mandatory static checkpoint, and only after a new Owner decision, the shortest product architecture remains a Finance-owned controlled-reconstruction adapter behind the existing Finance Control Desk boundary. FND-01 financial context and FND-02 source-adapter contracts must precede any totals. No new route, sidebar item, registry target, Shared UI change or landing change is required by default. This post-checkpoint direction is not source-authoring authority.

## 14. Next bounded outcomes

| Order | Bounded outcome | Required evidence | Owner approval before work | Closure/stop |
| --- | --- | --- | --- | --- |
| 1 | Strategic dependency reset | explicit selection of STATIC-HOLD-1, dormant provider track, one-attempt Level-A E2 posture and grouped E3 outcome | Owner accepts the strategy and later separately approves the technical read boundaries | stop if the current parser prerequisite is neither satisfied nor explicitly superseded |
| 2 | One bounded Level-A E2 path/source attempt | exact MariaDB commit/root, literal paths, object/source identities, Q1-Q8 mapping, hashes, source-supported facts and fail-closed result; no parser or provider execution | one exact path-identity/source-read authority that explicitly replaces or supersedes the current parser-execution prerequisite for this static claim | E2-B2 completes, or one terminal controlled failure records every unsupported Q fact; no second search |
| 3 | One GL/TB Static Compatibility Closure Package | parallel B1 lifecycle/identity/leakage, B4 S07 schema and necessary B2 callback lanes; B5 from E2; one B3 synthesis preserving every unsupported fact | one grouped package authority with exact per-lane path allowlists and specialist locks; no execution | one coherent closure or controlled-failure synthesis; unsupported facts do not spawn new micro-gates |
| 4 | Mandatory post-checkpoint Owner decision | E2 completion/controlled failure plus grouped E3 synthesis and exact remaining runtime risks | separate product-authoring decision | choose whether to authorize FND-01, FND-02 and a Finance-owned gl_reconstructed adapter; no automatic source work |

No outcome starts automatically from this document.

## 15. Anti-loop controls

1. This document is the one canonical strategic decision record.
2. One bounded independent review per perspective and one Main Control synthesis are complete; no second general cycle is permitted.
3. No repeated general provider, parser, architecture or provenance review.
4. No new micro-gate unless it removes one specifically named critical-path Blocker.
5. Every proposed gate must name the business or closure decision it enables.
6. A gate that cannot enable that decision is rejected or merged.
7. Accepted evidence is not reacquired without concrete source, dependency, provider or environment drift.
8. Later accepted documents supersede obsolete phase labels and assumptions.
9. Blocker and High findings require exact repository, committed-document, installed-source or authoritative primary-product evidence.
10. Diagnostic evidence is never promoted into controlled synthetic, accounting, runtime, release or live acceptance.
11. Provider infrastructure cannot silently become the Finance roadmap.
12. Main Control must report whenever assurance cost exceeds the value of the claim.
13. The mandatory next decision checkpoint is after the single E2 attempt reaches completion/controlled failure and the grouped E3 package reaches its final synthesis; no automatic amendment follows.
14. Minor documentation defects are consolidated into one correction, not serial one-field gates.
15. Two consecutive gates that produce no new source/product fact trigger an immediate Owner stop review.
16. A controlled failure terminates its lane; it cannot automatically spawn an adjacent search.
17. The Level-A E2 path permits one bounded attempt only; path or source expansion requires Owner adjudication, not an automatic search.
18. The E3 lanes close in one grouped package; an unsupported fact is recorded once in the final synthesis rather than generating a serial amendment.

## 16. Deferred scope

Deferred and unapproved:

- successful E2-B1 acquisition;
- the recommended future Level-A E2 path-identity/source-semantic attempt and its prerequisite-supersession decision;
- E1 and Docker endpoint/image evidence;
- provider acquisition or activation;
- parser or harness execution;
- controller/control-plane authoring;
- runner Dockerfile and initializer authoring;
- synthetic environment materialization;
- numeric workload or response limits;
- E4;
- GL/TB service, endpoint, page, route, registry, Shared UI or governance changes;
- HTTP/CORS;
- Finance-to-AI;
- active dimensions and dimension slices;
- non-default Finance Books;
- currencies beyond company base currency;
- multi-company, intercompany and consolidation;
- cancellation, close/reopen, frozen-period controls and audit certification;
- accounting mutation or execution;
- source-to-live alignment, migration, metadata, roles, permissions or protected gates; and
- authenticated live acceptance and production readiness.

Before any broad future application release, repository-level discoverability and import ordering justify a separately approved exact runner-path review. No current protected CI or release discovery path is proven here, so this remains a conditional Medium risk. This review does not inspect the runner or authorize a containment change.

## 17. Exact Owner decisions required

The Owner must decide:

1. whether to select STATIC-HOLD-1 and keep provider/isolation dormant and off the Finance critical path;
2. whether the provider track remains inactive until the six-part Level-C trigger is satisfied;
3. whether to approve, in a later separate task, one exact claim-proportionate Level-A replacement or supersession of the parser-execution prerequisite and one bounded E2 path-identity/source-semantic attempt;
4. whether terminal E2-B2 controlled failure is accepted only if that single attempt cannot close;
5. whether to authorize one GL/TB Static Compatibility Closure Package with exact specialist/path locks for E3-B1, E3-B4, necessary E3-B2, E3-B5 and one E3-B3 synthesis;
6. whether the project must stop again at the grouped static checkpoint before any C2B7, C2C-C2E, source-authoring, E4 or runtime decision;
7. at that checkpoint, whether to authorize FND-01 financial-context closure, FND-02 accounting-source adapter closure and a bounded Finance-owned gl_reconstructed adapter behind the existing Finance Control Desk; and
8. later, before any broad release, whether an exact protected runner path proves test discovery and requires a containment change.

Accepting this review is not approval for any listed future work.

## 18. Validation and future documentation staging allowlist

Required static validation:

- repository root, branch, HEAD and upstream;
- ahead/behind 0/0;
- empty index;
- candidate scope exactly this document plus README and the four pre-existing exclusions;
- protected source and exclusion hashes/statuses;
- git diff --check HEAD;
- strict UTF-8 without BOM, replacement characters or mojibake;
- no trailing whitespace;
- balanced Markdown fences;
- valid local references;
- exactly one README entry for this document;
- no recommendation described as Owner approval; and
- no runtime, execution, provider, acquisition, Docker, live or accounting authority.

If the Owner later authorizes documentation staging, the exact future allowlist is only:

1. impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/finance-accounting-cycle2-gl-tb-implementation-direction-counterpart-review-2026-07-22.md
2. impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/README.md

No source, test, fixture, provider, runtime, Shared UI, route, registry, manifest or exclusion may be staged.

## 19. Final control statement

Decision: gl_tb_direction_review_reconciled_for_owner_decision

The GL/TB accounting/source direction is materially advanced but still pre-implementation and non-executable. The parser/provider path has reached a conclusive fixed-set stop and should not remain the Finance critical path. The reconciled recommendation is STATIC-HOLD-1 plus dormant infrastructure separation, one later Owner-approved bounded Level-A E2 path-identity/source-semantic attempt, terminal controlled failure only if that attempt cannot close, and one grouped E3 Static Compatibility Closure Package followed by the mandatory Owner checkpoint.

STATIC-HOLD-1 restores strategic control, the E2 attempt may restore the static product path, and grouped E3 closure completes the architecture checkpoint. Only the later Owner decision on FND-01, FND-02 and a Finance-owned gl_reconstructed adapter can begin product delivery. No new route, sidebar item, Shared UI behavior, registry target, landing change, HTTP endpoint or AI integration is required by default.

Finance Cycle 2 runtime implementation was not started. No code authoring, import, compilation, collection, test, acquisition, provider action, Docker/Compose action, infrastructure, secret, SQL, Frappe, Bench, synthetic execution, runtime action, live access, migration, metadata change, permission change, protected gate, staging, commit, push or accounting action occurred.
