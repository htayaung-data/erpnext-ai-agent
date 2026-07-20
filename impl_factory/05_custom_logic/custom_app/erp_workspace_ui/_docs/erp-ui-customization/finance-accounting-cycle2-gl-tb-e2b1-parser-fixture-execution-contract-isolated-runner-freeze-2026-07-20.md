# Finance & Accounting Cycle 2 GL / Trial Balance E2-B1 Parser Fixture Execution Contract and Isolated Runner Freeze Gate

**Date:** 2026-07-20

**Authority:** Main Control v2

**Repository:** `/home/deploy/erp-projects/erpai_project1_erpnext_ui_design`

**Branch:** `feature/erpnext-ui-design`

**Verified baseline:** `3adb869c2f59472139dd6e26a46624b71dee3f5b`

**Decision:** `stopped_for_parser_runner_gap`

**Posture:** Planning and documentation only. This gate authorizes no Python import, compilation, collection or execution; no test, Bench, Docker, acquisition, infrastructure, source, runtime, live or accounting action; and no staging, commit or push.

## 1. Purpose and authority boundary

The Owner accepted `canonical_parser_fixture_source_published` and authorized one planning gate to determine whether a future isolated runner can execute exactly the ten committed methods in `TestFinanceGLTrialBalanceE2B1ParserFixtures` without making the database-backed GL/TB test class or any runtime surface reachable.

This document records a controlled stop. The ten method selectors can be frozen, but no exact runner can be frozen from the committed and previously accepted evidence. The accepted Frappe runner performs environment initialization and module-wide discovery. The only previously fingerprinted isolated host Python is intentionally standard-library-only and cannot import the harness. A direct exact-name `unittest` runner in the backend environment remains an unproven candidate, not execution authority.

This document is authoritative only for:

1. the runner gap and its repository evidence;
2. the exact ordered ten-method target;
3. the fail-closed phases, isolation obligations and evidence/discard requirements that any later runner must satisfy; and
4. the bounded Owner choices needed before runner source or execution can be considered.

It does not reopen the accepted parser architecture, fixture design or general controller review. It does not approve E2-B1 acquisition, E3-B1, E1, GL/TB accounting proof, Finance Cycle 2 closure or any accounting authority.

## 2. Verified baseline and immutable sources

| Item | Verified value |
| --- | --- |
| Repository root | `/home/deploy/erp-projects/erpai_project1_erpnext_ui_design` |
| Branch | `feature/erpnext-ui-design` |
| Local HEAD | `3adb869c2f59472139dd6e26a46624b71dee3f5b` |
| Configured upstream | `origin/feature/erpnext-ui-design` |
| Upstream revision | `3adb869c2f59472139dd6e26a46624b71dee3f5b` |
| Ahead/behind before documentation work | `0/0` |
| Git index before documentation work | empty |
| Harness SHA-256 | `923292b532353011a0663b0b69cbfcd21e5611d61a7178d6a1add0788d60be7b` |
| Controller SHA-256 | `69e67523d893b38b6559c75152f5802f6e5acf19642fd95d82cc2631d5a485b3` |
| Canonical parser contract SHA-256 | `d86161c9f7df4836f12783fbfa30a495c79b5155e4e5ccdb985fb649803e5b1e` |

The protected worktree items were preserved exactly:

| Path | Status | SHA-256 |
| --- | --- | --- |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py` | modified, unstaged | `01668e175610d9d090ea51018badbde8b021103afe13ed878782a58b8ce3b224` |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/browser_supplier_payables_fixture_diagnostic.py` | untracked | `d9822184b26f3c1ebaf5b93663b1f6c3a495b6482f013092d955748dfdf963c5` |
| `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/ui_smoke/sales_final_acceptance_audit.js` | untracked | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/a.out` | untracked | `0063411e61152850243132aa87ef12844a8724adb671bf4f38793bcd2b1ce339` |

Read-only controlling evidence:

1. [E2-B1 Python standard-library parser provenance and contract](finance-accounting-cycle2-gl-tb-e2b1-python-stdlib-parser-provenance-contract-freeze-2026-07-19.md);
2. [read-only compatibility and protocol/schema stop](finance-accounting-cycle2-gl-tb-read-only-compatibility-protocol-schema-freeze-gate-2026-07-18.md);
3. [selected-option product and compatibility fingerprint](finance-accounting-cycle2-gl-tb-selected-option-product-compatibility-fingerprint-2026-07-18.md);
4. [E1/E2-A/E3-A read-only evidence receipt](finance-accounting-cycle2-gl-tb-e1-e2a-e3a-read-only-evidence-acquisition-2026-07-18.md);
5. [runtime evidence design amendment](finance-accounting-cycle2-gl-tb-runtime-evidence-design-amendment-2026-07-18.md);
6. [controller-runner control-plane amendment](finance-accounting-cycle2-gl-tb-controller-runner-control-plane-source-delivery-amendment-2026-07-18.md); and
7. [synthetic evidence execution package](finance-accounting-cycle2-gl-tb-synthetic-evidence-execution-package-2026-07-17.md).

The committed source surfaces were inspected read-only:

- [parser fixture harness](../../erp_workspace_ui/tests/test_finance_gl_trial_balance_source_proof.py); and
- [E2-B1 controller/parser candidate](../../erp_workspace_ui/tests/finance_gl_trial_balance_evidence_controller.py).

## 3. Main Control stop determination

### 3.1 The accepted Frappe path cannot be the parser-only runner

The previously recorded same-process Frappe command candidate is:

```text
/home/frappe/frappe-bench/env/bin/python -I -m frappe.utils.bench_helper frappe --site <EXACT_SYNTHETIC_SITE> run-tests --app erp_workspace_ui --module erp_workspace_ui.tests.test_finance_gl_trial_balance_source_proof --junit-xml-output <EXACT_POINT_STAGING>/junit.xml
```

It remains rejected for this gate and is not an invocation candidate:

1. pinned `frappe.commands.testing.main` initializes the Frappe test environment before its execution `try`;
2. pinned discovery imports the requested module and calls `unittest.TestLoader().loadTestsFromModule`;
3. the environment layer owns `frappe.init/connect`, scheduler/test posture, cache handling, commit and cleanup behavior;
4. the command targets the entire harness module, not the ten exact methods; and
5. its JUnit option does not prove records from the actual selected runner.

Those properties violate the required denial of site initialization, database access and module-wide discovery. The command cannot be narrowed by assumption from the presence of `tests` or `case` parameters in the pinned function signature; their exact source behavior was not frozen by the accepted evidence.

### 3.2 The database-backed class is reachable under module-wide discovery

The harness has these relevant source facts:

| Harness evidence | Consequence |
| --- | --- |
| H:40 imports `frappe`; H:41 imports `MariaDBDatabase`. | Loading any test name from the module executes application/database imports before a test can be selected. |
| H:3880-3884 decorates `TestFinanceGLTrialBalanceSourceProof` with `SYNTH_GL_TB_GATE == finance_gl_tb_internal_v1`. | The database class is eligible when the shared gate is enabled. |
| H:3888-3931 defines its `setUpClass`. | Setup loads the synthetic environment and workload plan, creates an evidence writer, walks the evidence root, verifies topology/schema, opens `StrictMariaDBConnection`, seeds database fixtures and writes a manifest. |
| H:3934-3974 defines its `tearDownClass`. | Finalization reads/writes evidence, performs leakage and mutation checks, closes the database connection and closes the evidence writer. |
| H:7008-7011 uses the same `SYNTH_GL_TB_GATE == finance_gl_tb_internal_v1` value for the parser class. | Enabling the parser fixture gate also removes the database class's skip barrier. |

The ten parser methods do not themselves request database, filesystem, network, thread or subprocess work. Their lazy controller import is at H:6966-6973. The Blocker is module import and runner ownership, not the committed fixture bodies.

Under the accepted Frappe module-discovery path, the database class is therefore not merely importable: it is eligible for selection and its setup can execute. The required proof that it remains unreachable fails.

### 3.3 No other exact runner is frozen

The only accepted isolated interpreter fingerprint is the parser contract's `/usr/bin/python3.10` standard-library boundary with `-I -S -B -X utf8`. Its frozen module search path excludes the repository, current directory, site-packages, Frappe and MariaDB. It cannot import this harness.

A direct backend invocation using ten fully qualified `unittest` names is the only plausible same-file candidate. It is not approved or frozen because the accepted evidence does not bind:

1. the backend Python executable's exact absolute path, stat, SHA-256, version or ABI;
2. the exact backend module-search path and complete Frappe/MariaDB import closure;
3. the installed CPython `unittest` loader, suite, case, result and command-entry source bytes;
4. `loadTestsFromNames` behavior, requested order, `_FailedTest` behavior, unsupported-name failure, duplicate handling and proof of no discovery fallback;
5. an exact pre-execution collected-suite inventory seam;
6. sanitized output, exit, timeout, signal and finalization ownership; or
7. independent DB, network, filesystem, thread and subprocess denial/counter providers active before module import.

The committed controller ends with parser functions. It has no runner argv preflight, exact suite loader, result adapter, side-effect observer, evidence promotion owner or teardown entrypoint. No exact executable, argv, working directory, environment, import path, timeout, result destination or teardown contract can therefore be truthfully frozen in this gate.

## 4. Exact ordered ten-method target

This is the sole frozen method target for a later separately approved runner. It is not a command or execution allowlist.

| Order | Harness line | Fully qualified selector |
| ---: | ---: | --- |
| 1 | 7112 | `erp_workspace_ui.tests.test_finance_gl_trial_balance_source_proof.TestFinanceGLTrialBalanceE2B1ParserFixtures.test_e2b1_01_canonical_commit_bodies` |
| 2 | 7160 | `erp_workspace_ui.tests.test_finance_gl_trial_balance_source_proof.TestFinanceGLTrialBalanceE2B1ParserFixtures.test_e2b1_02_canonical_tree_bodies` |
| 3 | 7221 | `erp_workspace_ui.tests.test_finance_gl_trial_balance_source_proof.TestFinanceGLTrialBalanceE2B1ParserFixtures.test_e2b1_03_missing_q_and_ambiguity_rejections` |
| 4 | 7269 | `erp_workspace_ui.tests.test_finance_gl_trial_balance_source_proof.TestFinanceGLTrialBalanceE2B1ParserFixtures.test_e2b1_04_json_encoding_and_complete_value_boundaries` |
| 5 | 7308 | `erp_workspace_ui.tests.test_finance_gl_trial_balance_source_proof.TestFinanceGLTrialBalanceE2B1ParserFixtures.test_e2b1_05_complete_schemas_additive_policy_and_enum` |
| 6 | 7506 | `erp_workspace_ui.tests.test_finance_gl_trial_balance_source_proof.TestFinanceGLTrialBalanceE2B1ParserFixtures.test_e2b1_06_identity_and_invocation_boundaries` |
| 7 | 7638 | `erp_workspace_ui.tests.test_finance_gl_trial_balance_source_proof.TestFinanceGLTrialBalanceE2B1ParserFixtures.test_e2b1_07_https_and_rfc3339_boundaries` |
| 8 | 7786 | `erp_workspace_ui.tests.test_finance_gl_trial_balance_source_proof.TestFinanceGLTrialBalanceE2B1ParserFixtures.test_e2b1_08_tree_modes_sizes_paths_and_late_failure` |
| 9 | 7944 | `erp_workspace_ui.tests.test_finance_gl_trial_balance_source_proof.TestFinanceGLTrialBalanceE2B1ParserFixtures.test_e2b1_09_classification_rejections_and_hashing` |
| 10 | 8003 | `erp_workspace_ui.tests.test_finance_gl_trial_balance_source_proof.TestFinanceGLTrialBalanceE2B1ParserFixtures.test_e2b1_10_controlled_and_internal_fail_closed_behavior` |

The future runner must preserve this order and reject an empty, missing, duplicate, reordered, shortened, broadened, module, class, pattern, package or application selector. A skipped method is not a completed method. Exit code zero cannot qualify evidence by itself because an inactive gate can skip all ten methods.

## 5. Invocation freeze matrix

| Required contract | Status in this gate | Required evidence before execution |
| --- | --- | --- |
| Absolute executable | unresolved; no executable approved | Exact backend or parser-only runner path from a separately approved fingerprint gate. |
| Executable stat and SHA-256 | unresolved | Fixed stat-field allowlist, raw observation and source-controlled receipt. |
| Interpreter/runtime | unresolved | Exact version, ABI, build flags and executable/source binding. |
| `argv` | unresolved; approved argv is empty | Literal argument vector with ten selectors and proof that it cannot invoke discovery. |
| Working directory | unresolved | One absolute repository or sealed runner root proven necessary and read-only. |
| Environment | unresolved; approved environment is empty | Exact name/value allowlist, including a parser-specific gate decision that does not enable the database class. |
| Locale/timezone | unresolved | Exact `LANG`, `LC_ALL` and `TZ` values plus runtime behavior evidence. |
| Import/module paths | unresolved | Exact ordered search path and hashes for every permitted import; no current-directory or ambient-site fallback. |
| Selection order | frozen at Section 4 | Loader/source evidence and a collected-ID equality check before test start. |
| Timeout/termination | unresolved | Independently enforced statement/process ceiling owner; no numeric value is approved. |
| Output/exit | unresolved | Sanitized result adapter, byte/hash capture, outcome mapping and finalization source. Exit `65/70` remains deferred. |
| Evidence destination | unresolved | Controller-owned isolated staging root and atomic promotion/discard implementation. |
| Teardown/recovery | unresolved | Exact process/cgroup and temporary-root ownership with independent completion proof. |

There is no silent default. Every unresolved row is execution-blocking.

## 6. Isolation contract for any future design

A later runner must establish the following controls before importing the harness:

1. no module-wide, class-wide, package-wide or application-wide discovery;
2. no `TestFinanceGLTrialBalanceSourceProof` ID, class setup or class teardown in the collected suite;
3. no Frappe site initialization, site selection, scheduler, queue or cache lifecycle;
4. zero database connection and SQL-query attempts;
5. zero network connection and acquisition attempts;
6. no filesystem writes, including bytecode, temporary files, logs, coverage, JUnit or harness evidence, by the runner process;
7. no Docker socket, Engine, container or infrastructure contact;
8. zero background threads, subprocesses and queue workers;
9. no email, notification or integration dispatch; and
10. no runtime, live, permission, metadata or accounting action.

Only reads necessary to load the exact approved runner, committed harness, committed controller and frozen import closure may be permitted. A provider implemented inside the imported harness alone is insufficient to prove pre-import denial. The later design must identify independent enforcement and observation providers, bind their binaries/configuration by hash, and demonstrate that they are active before module import.

The runner process must be read-only. A separately owned controller may capture sanitized result events and write evidence to a private staging destination, but that ownership is not authored or approved here.

## 7. Fail-closed future phase contract

| Phase | Required action | Stop condition |
| ---: | --- | --- |
| 1 | Verify source, executable, loader, import-closure and observer fingerprints. | Any absent, extra or mismatched identity stops before environment construction. |
| 2 | Validate the exact environment and the ordered ten-selector vector. | Any unknown variable, wrong gate, duplicate, reordering or broad selector stops before import. |
| 3 | Enter the independently denied import/collection boundary and import only the frozen closure. | Any site, DB, network, write, thread, subprocess or unexpected import attempt stops and discards. |
| 4 | Flatten the collected suite without running it and compare exact IDs, order and count with Section 4. | Any `_FailedTest`, skip holder, suite error, database-class ID, duplicate, missing or extra ID stops before test start. |
| 5 | Execute the ten methods once in frozen order. | Any skip, failure, error, expected failure, unexpected success, duplicate start, missing terminal event or side effect stops remaining work. |
| 6 | Validate sanitized result events, process exit, signal state and output counts/hashes. | Any unrecognized outcome, raw sensitive output, truncation, unsupported exit or incomplete finalization discards the run. |
| 7 | Reconcile pre/post source hashes, side-effect counters, duration, memory and evidence completeness. | Any source change, nonzero counter, missing provider or inconsistent observation discards the run. |
| 8 | Atomically promote a completion receipt or retain only a sanitized discard receipt. | Partial, killed, timed-out, broadened or side-effecting evidence is never promoted. |
| 9 | Deterministically terminate the exact process/cgroup and remove the exact controller-owned staging root. | Teardown mismatch invalidates completion and produces a discard receipt. |

A stop at any phase prevents all later phases. No partial method mapping, parser projection, raw output or partially complete evidence graph is accepted.

## 8. Future evidence schema freeze

### 8.1 Common encoding and validation

The following is a planning schema, not an executable implementation. A future authoring gate must encode it without expansion.

- Schema ID: `finance_gl_tb_e2b1_parser_fixture_execution_v1`.
- JSON artifacts use UTF-8 without BOM, one JSON value, no duplicate keys, no NaN or infinity, no unknown fields and exact JSON types; Boolean is never accepted as integer.
- JSON Lines contain one complete JSON object per line. Empty lines are forbidden.
- SHA-256 values are 64 lowercase hexadecimal characters and cover exact bytes.
- Counts and byte values are nonnegative integers. Durations use integer nanoseconds. Memory uses integer bytes.
- Selectors are exact strings from Section 4; aliases and abbreviations are forbidden.
- Raw stdout, stderr, tracebacks, fixture bodies, paths, object IDs and leakage canaries are not promotable artifacts.
- A missing required artifact, field, provider or terminal event is a discard condition.

### 8.2 `parser-fixture-execution-manifest.json`

Required top-level fields and types:

| Field | Type and content |
| --- | --- |
| `schema_id` | exact string `finance_gl_tb_e2b1_parser_fixture_execution_v1` |
| `run_id` | opaque controller-assigned string; its exact format remains to be frozen with controller ownership |
| `design_baseline` | object containing `decision: stopped_for_parser_runner_gap` and a `document_sha256`; execution requires a later superseding authority receipt |
| `execution_authority` | object containing a nonempty later Owner decision ID and receipt SHA-256; no value exists in this gate |
| `sources` | object containing exact `harness_sha256`, `controller_sha256` and `parser_contract_sha256` strings |
| `executable` | object containing `absolute_path`, fixed-stat object, `sha256`, `runtime_version` and `abi`; every value must be nonempty before execution |
| `invocation` | object containing literal `argv` array, absolute `cwd`, exact ordered `environment` array, exact `locale`, exact `timezone` and exact ordered `module_search_paths` array |
| `requested_selectors` | exact ordered ten-string array from Section 4 |
| `limits` | object with `per_method_timeout_ns`, `total_timeout_ns`, `memory_ceiling_bytes`, `stdout_ceiling_bytes`, `stderr_ceiling_bytes` and `evidence_ceiling_bytes`; all remain unapproved and must be absent from execution authority until separately approved |
| `providers` | object binding independent selection, DB, network, filesystem, process/thread, clock, memory and teardown provider identities and SHA-256 values |

The exact executable stat fields, controller `run_id` format and provider implementations remain unresolved. This artifact cannot be instantiated as promotable evidence until those gaps close.

### 8.3 `parser-fixture-selection.json`

Required fields:

- `schema_id`: exact schema ID;
- `requested_selectors`: ordered ten-string array;
- `collected_selectors`: ordered ten-string array exactly equal to requested;
- `collected_count`: integer exactly equal to the frozen selector count;
- `exact_match`: Boolean `true`;
- `module_discovery_used`, `class_discovery_used`, `package_discovery_used`, `application_discovery_used`: each Boolean `false`;
- `failed_test_ids`, `unexpected_setup_ids`, `database_class_ids`, `duplicate_ids`, `missing_ids`, `extra_ids`: each empty array; and
- `selection_provider_sha256`: hash of the independently bound selection provider.

### 8.4 `parser-fixture-method-results.jsonl`

There must be exactly one terminal row per selector in Section 4 and no other row. Each row has:

- `schema_id`: exact schema ID;
- `ordinal`: unique integer corresponding to the frozen order;
- `selector`: exact fully qualified selector;
- `start_count`: integer exactly `1`;
- `terminal_count`: integer exactly `1`;
- `outcome`: one of `success`, `failure`, `error`, `skip`, `expected_failure`, `unexpected_success`, `not_run`;
- `duration`: object containing `value_ns` and a frozen `clock_provider_sha256`;
- `memory`: object containing nonnegative byte observations and a frozen `memory_provider_sha256`; and
- `sanitized_detail_sha256`: hash of a generic result classification with no raw exception or fixture content.

Only ten `success` outcomes are promotable. Every other enum value discards the entire run.

### 8.5 `parser-fixture-process-result.json`

Required fields:

- `schema_id`;
- `exit_code`: integer or `null` when terminated by signal;
- `signal`: frozen signal-name enum or `null` on ordinary exit;
- `stdout_byte_count`, `stderr_byte_count`: nonnegative integers;
- `stdout_sha256`, `stderr_sha256`: exact stream hashes;
- `stdout_truncated`, `stderr_truncated`: each Boolean `false` for promotable evidence;
- `runner_finalized`: Boolean `true` for promotable evidence; and
- `exit_mapping_contract_sha256`: hash of the later frozen unittest result/exit mapping.

Exit `65/70` belongs to a deferred outer controller-process boundary. It is not asserted by this fixture execution schema.

### 8.6 `parser-fixture-side-effects.json`

Required fields:

- `schema_id`;
- `database_connection_attempts` and `database_query_attempts`;
- `network_connection_attempts` and `acquisition_attempts`;
- `filesystem_write_attempts` and `filesystem_bytes_written`;
- `threads_started`, `subprocesses_started`, `queues_started`, `emails_attempted`, `notifications_attempted` and `integrations_attempted`;
- `docker_contact_attempts`, `site_initialization_attempts` and `accounting_action_attempts`;
- `source_hashes_before` and `source_hashes_after`; and
- one identity/hash per independent observation provider.

Every counter must be zero, and pre/post harness and controller hashes must match their manifest values. Missing or in-process-only observation does not qualify as zero evidence.

### 8.7 Terminal receipts

Exactly one terminal receipt is retained:

1. `parser-fixture-completion.json` requires exact selection, ten once-only successes, accepted process result, zero side effects, equal pre/post source hashes, complete artifact hashes and one evidence-root hash. It can be written only after successful teardown reconciliation.
2. `parser-fixture-discard.json` contains only `schema_id`, `run_id`, failed phase, one reason enum, sanitized provider/source hashes, `partial_evidence_destroyed: true`, `raw_streams_destroyed: true` and `teardown_status`.

The discard reason enum is:

```text
fingerprint_mismatch
environment_mismatch
import_or_collection_failure
selection_mismatch
test_non_success
timeout
signal
side_effect_attempt
source_changed
output_limit_exceeded
memory_limit_exceeded
evidence_incomplete
teardown_failure
internal_error
```

Killed, timed-out, broadened, skipped, incomplete, side-effecting, source-changing or teardown-failing runs are discard-only. Their method rows, mappings, projections and raw streams are never promoted.

## 9. Numeric-limit derivation method

This gate approves no numeric value and no derivation execution.

After the runner, import closure, side-effect providers and evidence writer are separately frozen, the Owner may authorize a bounded derivation exercise under the same source hashes and selector inventory. That later exercise must:

1. predeclare the number of isolated observations and their cold/warm posture;
2. record per-method and total duration in nanoseconds, independently observed memory in bytes, stdout/stderr bytes and total evidence bytes;
3. discard incomplete, killed, side-effecting or source-mismatched observations from limit derivation;
4. publish every accepted observation, measurement resolution, variance and proposed headroom rationale;
5. propose, but not automatically approve, per-method and total time ceilings, memory ceiling, stdout/stderr ceilings and evidence-size ceiling; and
6. later prove each approved limit at pass and limit-plus-one boundaries with timeout producing no partial output.

No average, percentile, maximum, multiplier or margin becomes authoritative by convention. The Owner must separately approve each numeric limit after reviewing the evidence and reversibility.

## 10. Accounting and release claim boundary

A future successful parser-fixture run may establish only this bounded statement:

> The ten exact E2-B1 parser fixture methods completed once under the recorded harness and controller hashes, exact runner contract and zero-side-effect evidence.

It must not claim:

- GL/TB or `gl_reconstructed` accounting correctness;
- MariaDB product/source behavior;
- complete-chart, company, permission, dimension, snapshot or leakage semantics outside the parser fixtures;
- Frappe runtime compatibility;
- E2-B1 network acquisition or E2-B2 source-reading readiness;
- `harness-complete.json`, `point-complete.json` or synthetic-point closure;
- Finance Cycle 2 closure; or
- accounting execution or authority.

## 11. Review findings

### Blocker

1. **No runner proves the database-backed class unreachable.** The accepted Frappe path performs module-wide discovery, while the database and parser classes share the same gate. Database `setUpClass` performs prohibited environment, filesystem and database work.
2. **No authoritative runner satisfies both importability and exact named-test isolation.** The accepted isolated host Python cannot import the harness; the backend Python and its exact `unittest` behavior are not fingerprinted.

### High

1. **Module import is not isolated.** Even exact-name loading imports Frappe and `MariaDBDatabase` before selection. No accepted pre-import OS denial and import-side-effect closure exists.
2. **Exact selection, output and evidence ownership are absent.** The controller has parser functions only. There is no exact-suite inventory, sanitized result adapter, side-effect provider, atomic promotion or teardown implementation.
3. **Skip can masquerade as success.** The parser gate is checked in `setUp`; an inactive gate may skip all methods while a generic runner exits successfully. Completion must be based on ten exact success events, never exit code alone.

### Medium

1. Numeric time, memory, output and evidence limits remain intentionally unselected pending a separately approved derivation exercise.
2. Frappe initialization precedes its ordinary cleanup `try`, so partial initialization cannot rely on ordinary cleanup; this reinforces the rejection of that runner for this parser-only contract.

### Accounting-preservation result

No new accounting-semantic defect was found in the fixture scope. The execution stop preserves the reporting-only, no-execution and no-accounting-authority boundaries.

## 12. Bounded reviews and Main Control synthesis

| Review | Result |
| --- | --- |
| Python runner and test selection | Stop. Frappe discovery is module-wide; the stdlib-only host interpreter cannot import the module; backend exact-name behavior is unpinned. |
| Security, import and side-effect containment | Stop. Shared gate eligibility, module-level Frappe/MariaDB imports and absent independent pre-import denial prevent a zero-side-effect claim. |
| Accounting/source-proof preservation | Stop without a new accounting finding. Parser execution could prove parser fixtures only and cannot promote GL/TB accounting evidence. |
| Release and evidence integrity | Stop. No exact argv, observer, sanitized result adapter, promotion owner, numeric limits or teardown owner is frozen. |

Main Control accepts the evidence-backed Blocker and High findings. One synthesis pass was performed; no open-ended counterpart-review loop was started. The source fixture package remains accepted and unchanged, but execution authority remains empty.

## 13. Remaining prerequisites and bounded Owner choices

The Owner must select one path before any runner authoring or evidence execution:

1. **Recommended - parser-only source boundary.** Authorize a later source-design gate for a pure parser fixture module and controller-owned exact runner with an independent parser gate and no Frappe/MariaDB import closure. Then fingerprint the exact interpreter and `unittest` source before execution.
2. **Same-file direct exact-name proof.** Authorize a read-only provenance gate for the backend Python, complete `unittest` and import closure, exact-name suite behavior, pre-import OS denials, suite-inventory adapter, sanitized result mapping and side-effect providers. This path must explicitly accept investigation of the module-level Frappe/MariaDB imports and shared gate; it may still stop as infeasible.
3. **Defer execution.** Keep the current static parser source evidence only. E2-B1 fixture execution remains stopped.

If the Owner selects option 1 or 2, separate later decisions are still required for:

- the exact executable, argv, cwd, environment, locale, timezone and module-search path;
- the exact independent denial/observation providers and result/evidence owner;
- the parser-specific gate and proof that the database class cannot become eligible;
- the separately derived numeric limits; and
- source authoring, static review, execution and evidence promotion as distinct approvals.

The Frappe module runner is rejected for this isolation contract and is not a viable Owner choice without materially broadening the task to allow site/database initialization.

## 14. Future allowlists

### 14.1 Documentation staging allowlist - unapproved

If the Owner later authorizes publication, the exact documentation staging allowlist is:

1. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/finance-accounting-cycle2-gl-tb-e2b1-parser-fixture-execution-contract-isolated-runner-freeze-2026-07-20.md`;
2. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/README.md`.

No staging, commit or push is authorized by this gate.

### 14.2 Method target - frozen but not executable authority

The only future method target is the ordered ten-selector table in Section 4. It permits no module, class, pattern, package or application discovery.

### 14.3 Command and execution allowlist - unapproved and empty

```text
[]
```

There is no approved executable, argument vector, Python import, collection, test command, environment, write destination, Bench command, Docker command or evidence action.

## 15. Validation and no-action receipt

Main Control verified read-only before documentation authoring:

- repository root, branch, local HEAD and configured upstream;
- local/upstream equality and ahead/behind `0/0`;
- an empty Git index;
- exact harness, controller and canonical parser-contract SHA-256 values;
- committed harness source lines for imports, both gates, database setup/finalization and all ten method selectors;
- accepted Frappe initialization, discovery, runner, JUnit and cleanup evidence; and
- the absence of a source-controlled runner/evidence adapter in the current controller.

After documentation authoring, Main Control must reverify the exact two-document candidate scope plus the four protected exclusions, `git diff --check HEAD`, strict UTF-8, no BOM or trailing whitespace, Markdown fences/local references, one README entry, an empty index and unchanged source/protected hashes.

No source file changed. No Python was imported, compiled, collected or executed. No test, Bench, Docker, network acquisition, infrastructure, secret, database, SQL, runtime, live, migration, permission, protected-gate or accounting action occurred. No file was staged, committed or pushed.
