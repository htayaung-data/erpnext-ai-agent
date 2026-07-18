# Finance & Accounting Cycle 2 GL / Trial Balance E1/E2-A/E3-A Read-Only Evidence Acquisition

Date: 2026-07-18
Authority: Main Control v2
Document class: canonical read-only evidence receipt and controlled stop
Repository: `/home/deploy/erp-projects/erpai_project1_erpnext_ui_design`
Branch: `feature/erpnext-ui-design`
Starting source and upstream: `644fdfeb1337a46107e1ef6dc1db655ff8893d6e`
Ahead/behind at gate start: `0/0`
Controlling fingerprint: [Selected-Option Product and Compatibility Fingerprint](finance-accounting-cycle2-gl-tb-selected-option-product-compatibility-fingerprint-2026-07-18.md)
Controlling Owner decisions: [Selected-Option Evidence Closure Decisions](finance-accounting-cycle2-gl-tb-selected-option-evidence-closure-decisions-2026-07-18.md)
Fingerprint decision retained: `stopped_for_selected_option_fingerprint_gap`
Decision: `stopped_for_read_only_evidence_gap`

## 1. Outcome and authority

This receipt records exactly three bounded read-only acquisition lanes:

1. E1 host/backend fixed-field metadata;
2. E2-A MariaDB 10.11 immutable provenance binding; and
3. E3-A pinned Frappe and unchanged-harness static inventory.

E2-A completed its provenance-only objective. E3-A completed its static-inventory objective. E1 established the permitted host and Compose facts but stopped because the published fixed image-inspection template could not render an absent `Config.Entrypoint` key and the frozen command set did not establish the Docker CLI literal path. No alternate template, raw inspection or assumed path was used.

The complete gate therefore stops at `stopped_for_read_only_evidence_gap`. The successful lane evidence remains valid and may be cited by a later exact gate, but it does not approve a digest, establish compatibility, close K1/S2/J2/P1/W1/D1, authorize E2-B/E3-B/E4, reopen source authoring or advance Finance Cycle 2 beyond the current C2B evidence posture.

## 2. Evidence classification and prohibited inference

| Evidence class | Authority in this receipt | It does not prove |
| --- | --- | --- |
| Repository facts | Git identity, committed documents, unchanged harness hash and static source bytes | runtime behavior, product behavior or live state |
| Host-command facts | only the literal fixed fields emitted by the approved E1 commands | image filesystem, numeric identity, PID/signal/thread behavior, secrets or application runtime |
| Registry/config facts | exact digest-addressed OCI index, Linux/amd64 manifest and referenced config fields | layer bytes, installed server behavior, digest approval or Frappe compatibility |
| Pinned-source facts | exact upstream commit/file hashes and source relationships | in-image equality unless separately bound, runtime execution or effective permissions |
| Static inventory facts | source locations, declared operations, control flow, test sites and candidate authority surfaces | executed query set, grants, denial behavior, concurrency, cleanup success or leakage resistance |
| Unproven runtime facts | explicitly assigned to a later gate | no inference is permitted |

Metadata is not runtime proof. Source is not runtime proof. Inventory is not a grant list. A successful digest comparison is not digest approval. Absence or failure under a fixed output template is a stop, not permission to broaden inspection.

## 3. Repository and protected-state baseline

| Item | Verified value |
| --- | --- |
| Repository root | `/home/deploy/erp-projects/erpai_project1_erpnext_ui_design` |
| Branch | `feature/erpnext-ui-design` |
| Local HEAD | `644fdfeb1337a46107e1ef6dc1db655ff8893d6e` |
| Upstream | `origin/feature/erpnext-ui-design` at the same revision |
| Ahead/behind | `0/0` |
| Index | empty |
| Fingerprint SHA-256 | `b0908b4a34534b7c1b9cebac194130a102fc063244ff517c57428280a7c1ea4c` |
| Evidence-closure decisions SHA-256 | `2833673bcab1376c7181bbef91bc5f00a2d1347f91be06bf919b177e87e62de4` |
| Harness SHA-256 | `c8d0bb0556f9abb04e1be69c1d67a7f92c4ed37a64d8270d84339ad590e9cea5` |

The harness remained untracked. The future controller, runner Dockerfile and initializer were absent. The four protected exclusions retained their pre-existing statuses and hashes. The live deployment tree and operational data were not accessed.

## 4. Lane disposition summary

| Lane | Evidence acquired | Lane disposition | Whole-gate effect |
| --- | --- | --- | --- |
| E1 | Docker/Compose fixed product fields, host drivers/security facts, exact Compose plugin path/stat/hash | partial evidence; stopped on fixed image template and missing Docker CLI path | Blocker; whole gate stops |
| E2-A | exact OCI digest chain, safe config fields, Official Images and MariaDB Docker source hashes, server tag/peeled commit | completed for provenance only | narrows R1; no digest approval |
| E3-A | exact Frappe lifecycle/J2, test/subtest, credential, connection, SQL, mutation, evidence and leakage inventories | completed for static inventory only | narrows J2/P1/W1/D1; no compatibility/grants |

## 5. E1 host and backend metadata evidence

### 5.1 Exact Docker client/server facts

The published fixed `docker version --format` command emitted:

| Field | Client | Server |
| --- | --- | --- |
| Version | `29.2.1` | `29.2.1` |
| API | `1.53` | `1.53` |
| Minimum API | not a client field | `1.44` |
| Git commit | `a5c7197` | `6bc6209` |
| Go version | `go1.25.6` | `go1.25.6` |
| OS/architecture | `linux` / `amd64` | `linux` / `amd64` |
| Build time | `Mon Feb 2 17:17:09 2026` | `2026-02-02T17:17:09.000000000+00:00` |
| Experimental | not a client field | `false` |

The command was exactly:

```text
docker version --format '{{json .Client.Version}}|{{json .Client.APIVersion}}|{{json .Client.GitCommit}}|{{json .Client.GoVersion}}|{{json .Client.Os}}|{{json .Client.Arch}}|{{json .Client.BuildTime}}|{{json .Server.Version}}|{{json .Server.APIVersion}}|{{json .Server.MinAPIVersion}}|{{json .Server.GitCommit}}|{{json .Server.GoVersion}}|{{json .Server.Os}}|{{json .Server.Arch}}|{{json .Server.BuildTime}}|{{json .Server.Experimental}}'
```

### 5.2 Compose and host product facts

`docker compose version --format json` emitted only `{"version":"v5.0.2"}`.

The fixed Compose-plugin record emitted:

```text
"compose"|"v5.0.2"|"/usr/libexec/docker/cli-plugins/docker-compose"
```

Because that literal path was proven, only that file was read with fixed `stat` fields and SHA-256:

| Field | Observed value |
| --- | --- |
| Type | regular file |
| Owner/group | `root` / `root` |
| Numeric owner/group | `0` / `0` |
| Mode | `755` |
| Size | `31327024` bytes |
| SHA-256 | `2d880f723d3da7c779c54fdaea91a842fca8af55d1397f1ed8d7cbab3dd7af67` |

The fixed `docker info --format` commands established:

| Host product field | Observed value |
| --- | --- |
| Server version | `29.2.1` |
| Storage driver | `overlayfs` |
| Cgroup driver/version | `systemd` / `2` |
| Available OCI runtimes | `io.containerd.runc.v2`, `runc` |
| Default runtime | `runc` |
| Security options | AppArmor, built-in seccomp profile, cgroup namespaces |
| OS type/system | `linux`, `Ubuntu 22.04.4 LTS` |
| Architecture | `x86_64` |
| Kernel | `5.15.0-177-generic` |

No frozen command established the Docker CLI literal binary path. Its stat and checksum were therefore not attempted.

### 5.3 Exact backend-image inspection stop

The exact authorized image metadata command was attempted against only the already pinned image ID:

```text
docker image inspect --format '{{json .Id}}|{{json .RepoDigests}}|{{json .Os}}|{{json .Architecture}}|{{json .Config.User}}|{{json .Config.WorkingDir}}|{{json .Config.Entrypoint}}|{{json .Config.Cmd}}|{{json .Config.StopSignal}}|{{json .RootFS.Type}}|{{json .RootFS.Layers}}' sha256:4c8b6fb188d81f5a355008730a1122658af88799ec759029c2dbd297dfc8e257
```

It exited `1` and emitted no formatted evidence:

```text
template parsing error: template: :1:135: executing "" at <.Config.Entrypoint>: map has no entry for key "Entrypoint"
```

The template was not altered and raw inspection was not used. Consequently this receipt does not newly establish the image ID/repository digests, platform, configured user, working directory, entrypoint, command, stop signal, rootfs type or diff IDs. The previously accepted installed-source/image identity receipt remains historical authority for only the facts it already proved.

### 5.4 E1 facts still unproven

- Docker CLI literal path, stat and checksum;
- backend image fields blocked by the fixed template;
- numeric UID/GID, supplementary groups and passwd/group mapping;
- rootless/user-namespace translation;
- path traversal, ownership, modes and secret readability;
- exact Python patch/build/compiler/ABI/SOABI/libc facts;
- PID 1, main-thread/thread inventory and signal mask/pending behavior;
- K1 owner-only secret behavior; and
- runtime or Frappe compatibility.

**E1 disposition:** host facts retained; E1 stopped. A later Owner-approved corrected fixed-output acquisition gate is required. The failure is not evidence that the image itself is incompatible.

## 6. E2-A MariaDB 10.11 immutable provenance evidence

### 6.1 Registry request boundary and digest chain

Only repository-scoped authentication, the exact digest-addressed index, its exact Linux/amd64 manifest and that manifest's referenced config blob were requested. No tag enumeration, layer blob or image pull occurred.

| Object | Requested identity | Response/proof |
| --- | --- | --- |
| OCI index | `sha256:be981e4113326ada8d6004174dd09eeaefc03094037f811182a52d4f2e737350` | response digest matched; `application/vnd.oci.image.index.v1+json`; schema `2` |
| Linux/amd64 manifest | `sha256:9bd53e60ca32fceda2dce247d4791a1964ed05ceeea73b28e151ff9d5983b3a1` | exact index entry; response digest matched; `application/vnd.oci.image.manifest.v1+json`; schema `2` |
| Config | `sha256:37b9f8bf6fe12f7d493c8aa55e97dd0205367e7b29445166e661a2739fdbae02` | referenced by manifest; in-memory payload SHA-256 matched |

The config response used `application/octet-stream` and supplied no `Docker-Content-Digest` header. Integrity is therefore recorded from the manifest reference plus the independently computed payload SHA-256, not from a nonexistent response header.

Safe retained config fields:

- created: `2026-07-02T02:30:44.891113353Z`;
- entrypoint: `["docker-entrypoint.sh"]`;
- command: `["mariadbd"]`; and
- user, working directory and stop signal: absent/null.

No environment values, labels, history or layer descriptors were retained.

### 6.2 Pinned build-source hashes

| Source | Pinned revision | Raw SHA-256 |
| --- | --- | --- |
| [`library/mariadb`](https://github.com/docker-library/official-images/blob/978734a887cff2ee0950939a12654c0072da226c/library/mariadb) | `docker-library/official-images` `978734a887cff2ee0950939a12654c0072da226c` | `e8c5724215fe4b6844d3cf9707e71311dae078d5a7a5221059fe5262f640a383` |
| [`10.11/Dockerfile`](https://github.com/MariaDB/mariadb-docker/blob/53935c78b82bff912b361357d59db11d7246ea96/10.11/Dockerfile) | `MariaDB/mariadb-docker` `53935c78b82bff912b361357d59db11d7246ea96` | `db7977c0be6d44ab63afba5d27b45f3f4d17c781d11f97b4e67fda475471acbd` |
| [`10.11/docker-entrypoint.sh`](https://github.com/MariaDB/mariadb-docker/blob/53935c78b82bff912b361357d59db11d7246ea96/10.11/docker-entrypoint.sh) | same | `72fd2da1b86f8d0518e4a88b99e70b65bad9b23c3335654a58f30041a55402f3` |
| [`10.11/healthcheck.sh`](https://github.com/MariaDB/mariadb-docker/blob/53935c78b82bff912b361357d59db11d7246ea96/10.11/healthcheck.sh) | same | `80e2a5dc9e0a50c24842d9f093659a7f2417e9399554d8b13bd294575e15a626` |

The exact Official Images stanza binds:

- tags `10.11.18-jammy`, `10.11-jammy`, `10-jammy`, `10.11.18`, `10.11` and `10`;
- architectures `amd64`, `arm64v8`, `ppc64le` and `s390x`;
- `GitCommit` `53935c78b82bff912b361357d59db11d7246ea96`;
- directory `10.11`; and
- the default Dockerfile in that directory.

The Dockerfile uses `ubuntu:jammy`, copies the entrypoint/healthcheck scripts, and its entrypoint/command declarations agree with the safe registry config fields. This is source-to-registry provenance evidence; it is not in-image byte equality or runtime proof.

### 6.3 MariaDB Server tag binding

The only server-repository command was:

```text
git ls-remote https://github.com/MariaDB/server.git refs/tags/mariadb-10.11.18 refs/tags/mariadb-10.11.18^{}
```

It returned:

| Reference | SHA |
| --- | --- |
| tag object | `51002ba60131e307b550dfaca41dd1e15ba81085` |
| peeled commit | `197f92bee02d8e836f529f37625be69b83e7acbd` |

No clone, tree dump, search or MariaDB Server implementation-file read occurred.

### 6.4 E2-A conclusion and limits

The digest-addressed index/manifest/config chain, Official Images mapping, pinned Docker source and server tag binding are internally consistent. The tag-to-index association remains the previously frozen candidate/fingerprint fact because this gate did not authorize a fresh mutable-tag dereference.

**E2-A disposition:** completed for immutable provenance evidence. MariaDB 10.11.18 Jammy remains the first proof candidate only. No repository, manifest, config or image digest is approved. Datadir initialization, password-file behavior, effective identity, server build, transaction, grants, reconnect, collation, Decimal, containment and Frappe compatibility remain unproven.

## 7. E3-A pinned Frappe/J2/D1 static inventory

### 7.1 Source and harness authority

`H` below means the unchanged 6,911-line harness:

`impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/tests/test_finance_gl_trial_balance_source_proof.py`

Its SHA-256 remained `c8d0bb0556f9abb04e1be69c1d67a7f92c4ed37a64d8270d84339ad590e9cea5`.

The accepted installed-source receipt binds Frappe v16.5.0 to commit `4dfcc56090eb3101d18ddb03750391511f163fcf`, tree `725e06e6319cef5a671884cba1b8b8841f40f99e`, with selected installed/source equality `26/26`.

| Pinned Frappe file | SHA-256 |
| --- | --- |
| `frappe/commands/testing.py` | `3a87363eb432b8ef9379d7e6d0a8f7ba5028525de412a0a4762933da707cdb8e` |
| `frappe/testing/runner.py` | `e4c3a77eb4dd5c41f0474f26fa05b07edb6847e56ea030cbae3b9f7961aaeb6c` |
| `frappe/testing/result.py` | `c17e1e6e12f81567ec3297af6745e4cb8dbfc928fbb3bdcc2fccc36b85399ba1` |
| `frappe/testing/discovery.py` | `db63ca823e8d611884d57b3d6d8403134f32e97979850a5cbbfb169ae8603a8b` |
| `frappe/testing/environment.py` | `b9035e54f1821cc81736c69347075428ca2328bee033ad1338efa4c2d81bd7bb` |
| `frappe/testing/config.py` | `5cf8813c74d1c121b7b489bf8eeb4685d6387c0c8c80c9e81a0c6e70f5613e9a` |
| `frappe/testing/__init__.py` | `914e98750eab9512f4456c048a57ca4cf8022000928394104007571e712d3f0d` |

### 7.2 Frappe initialization, discovery, execution and cleanup

Pinned [`frappe/commands/testing.py`](https://github.com/frappe/frappe/blob/4dfcc56090eb3101d18ddb03750391511f163fcf/frappe/commands/testing.py#L18-L177) performs this static sequence:

1. import `TestConfig`, `TestRunner` and discovery functions;
2. clear the test log;
3. construct `TestConfig`;
4. initialize the test environment before the execution `try`;
5. configure optional XML output;
6. construct `TestRunner` without a `resultclass` argument;
7. discover the selected module;
8. iterate `runner.iterRun()` and execute each suite through `runner.run(suite)`;
9. call `sys.exit(1)` when any returned result is unsuccessful; and
10. in the ordinary `finally`, clean up the environment, close optional XML output and record timing.

An initialization failure therefore does not enter the same ordinary cleanup. Discovery imports the requested module and uses `unittest.TestLoader().loadTestsFromModule`; this plain `unittest.TestCase` harness enters the unspecified category.

Pinned `TestRunner` imports module-global `TestResult` and passes `resultclass or TestResult` to `unittest.TextTestRunner`. The CLI does not pass `resultclass`. The selected J2 direction therefore remains a private exact-source binding to `frappe.testing.runner.TestResult` after blocked Frappe import and before CLI runner construction. It is not implemented or runtime-compatible evidence. Direct `TestRunner` construction remains rejected.

The current harness promotes its artifacts inside `tearDownClass` at H:3932-3966. Pinned Frappe outer cleanup occurs only after `runner.run()` returns. Current harness promotion can therefore precede Frappe cleanup and cannot satisfy the accepted post-cleanup/discard-only finalization contract.

### 7.3 Exact top-level tests and static subtest sites

Exact top-level IDs:

1. `erp_workspace_ui.tests.test_finance_gl_trial_balance_source_proof.TestFinanceGLTrialBalanceSourceProof.test_10_accounting_fixture_catalog` - H:4726;
2. `erp_workspace_ui.tests.test_finance_gl_trial_balance_source_proof.TestFinanceGLTrialBalanceSourceProof.test_20_permission_company_and_leakage_catalog` - H:4074;
3. `erp_workspace_ui.tests.test_finance_gl_trial_balance_source_proof.TestFinanceGLTrialBalanceSourceProof.test_25_installed_permission_extraction_controls` - H:4295;
4. `erp_workspace_ui.tests.test_finance_gl_trial_balance_source_proof.TestFinanceGLTrialBalanceSourceProof.test_30_primary_snapshot_concurrency_and_reconnect_catalog` - H:5697; and
5. `erp_workspace_ui.tests.test_finance_gl_trial_balance_source_proof.TestFinanceGLTrialBalanceSourceProof.test_40_workload_caps_timeouts_and_no_partial_contract` - H:6300.

Static subtest call sites:

| Harness line | Static parameter names only |
| --- | --- |
| H:4248 | `fixture_id`, `variant` |
| H:4744 | `fixture_id`, `variant` |
| H:6113 | `fixture_id` |
| H:6251 | `reconnect_boundary` |
| H:6308 | `workload_point` |

Runtime parameter values and value-bearing `subtest.id()` strings were not retained. E3-A does not freeze the complete safe ID allowlist.

### 7.4 Result callback surface

Pinned `frappe.testing.result.TestResult` overrides:

- `startTestRun`, `stopTestRun`, `startTest`, `stopTest`;
- `addSuccess`, `addError`, `addFailure`, `addSkip`;
- `addExpectedFailure`, `addUnexpectedSuccess`; and
- error printing and captured-output formatting.

It does not override `addSubTest`; that remains inherited from the installed `unittest.TextTestResult`. `stop`/`shouldStop` are inherited. `addDuration` depends on the exact installed CPython build. Setup/class/module holders and inherited callback behavior remain unproven.

### 7.5 Credential and environment references

H:1319 and H:1479-1529 reference:

- `SYNTH_WORKLOAD_PLAN_JSON`;
- `SYNTH_RUN_ID`;
- `SYNTH_EXPECTED_SITE`;
- `SYNTH_DB_ROOT_PASSWORD`;
- `SYNTH_CURRENCY_CODE` and `SYNTH_CURRENCY_PRECISION`;
- `SYNTH_FY_START`, `SYNTH_FY_END`, `SYNTH_FROM_DATE`, `SYNTH_TO_DATE`;
- `SYNTH_EVIDENCE_DIR`;
- `SYNTH_EXPECTED_HARNESS_SHA256`; and
- `SYNTH_GL_TB_GATE` at H:3879.

Database name, host, port, site user and site password are read from `frappe.conf` at H:1485-1511. The root password is currently an environment value, not a file-backed mode-specific secret.

### 7.6 Connection and authority modes

| Mode | Static source location and authority |
| --- | --- |
| Normal reader | site credential at H:2828-2835; read-only repeatable-read snapshot |
| Preparation | site credential at H:3908-3911; seeds base fixtures |
| Dynamic writer | same preparation connection and `FixtureMutationGate`; permission mutations H:4300-4724 and S-case mutations H:5732-6091 |
| Topology/schema | `topology=True` selects root at H:1567-1568; topology/schema queries H:2956-3022 |
| Reconnect fault | another root topology connection validates a process row and issues `KILL CONNECTION`, H:3025-3049 and H:6255-6259 |
| Concurrent readers | additional normal site-user readers; no distinct measured-reader credential |

Preparation, mutation, measured reading, schema verification, topology, root and reconnect authority are co-resident in the current module/process. This is source inventory evidence of incompatibility with the selected role separation; it is not permission to execute or broaden authority.

### 7.7 Static SQL and data-surface inventory

Session/transaction surfaces at H:1602-1719 include:

- `SET SESSION max_statement_time`;
- `SHOW SESSION STATUS LIKE 'Rows_read'`;
- `SELECT CONNECTION_ID()`;
- `SET TRANSACTION ISOLATION LEVEL REPEATABLE READ`;
- `START TRANSACTION READ ONLY, WITH CONSISTENT SNAPSHOT`;
- `DATABASE()`, `@@hostname`, `@@port`, `@@server_id`, `@@in_transaction`;
- `INFORMATION_SCHEMA.INNODB_TRX` fields `TRX_MYSQL_THREAD_ID`, `TRX_ISOLATION_LEVEL`, `TRX_IS_READ_ONLY`; and
- adapter commit and rollback calls.

Declared application-table inventory at H:258-315:

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

Reader-query families at H:2298-2811 include:

- company, currency and Finance Book lookups;
- user, role, User Permission and standard/custom DocPerm reads;
- `tabDocField UNION ALL tabCustom Field`;
- DocShare filters for Account/GL Entry and actor/everyone;
- `tabCustom Role INNER JOIN tabHas Role`;
- Property Setter, strict-permission Single and active-dimension reads;
- `tabFiscal Year LEFT JOIN tabFiscal Year Company`, ordered by fiscal year/company;
- complete Account chart ordered by `lft,name`;
- GL validation through `LEFT JOIN tabAccount` with company/book/date and malformed/cancelled/opening/scale/account-scope filters;
- aggregate GL through `INNER JOIN tabAccount`, conditional opening/movement sums, `GROUP BY gle.account`, `ORDER BY gle.account`; and
- optional `EXPLAIN FORMAT=JSON` and `SELECT SLEEP`.

Schema/topology/process surfaces at H:2956-3047 include `@@GLOBAL.read_only`, server identity, `SHOW ALL REPLICAS STATUS`, `INFORMATION_SCHEMA.TABLES`, `INFORMATION_SCHEMA.COLUMNS`, `INFORMATION_SCHEMA.PROCESSLIST` fields `ID`, `DB`, `USER`, `HOST`, and `KILL CONNECTION`.

Mutation helpers at H:1964-2045 use dynamic `INFORMATION_SCHEMA.COLUMNS` discovery, parameterized dynamic `INSERT`, parameterized dynamic `UPDATE ... WHERE BINARY name ...`, commit and rollback. This inventory is not a final statement list or grant list.

### 7.8 S01-S08 mutation inventory

Every insert currently adds common metadata fields `name`, `owner`, `creation`, `modified`, `modified_by`, `docstatus`, `idx`.

| Case | Static mutation inventory |
| --- | --- |
| S01 | two `tabGL Entry` inserts then commit; GL/date/account/debit-credit/currency/voucher/company/book/opening/cancelled/remarks fields; H:5802-5811 and helper H:3420-3486 |
| S02 | group and leaf `tabAccount` inserts with account/company/hierarchy/report/currency/range/disabled fields; H:5837-5874 |
| S03 | one `tabUser Permission` insert with user/allow/value/default/apply-all/applicable-for/hide-descendants; H:5894-5908 |
| S04 | update `tabCompany.default_finance_book` by exact name, then commit; H:5924-5930 |
| S05 | insert `tabFiscal Year` and `tabFiscal Year Company` with year/date/company/parent metadata; H:5956-5980 |
| S06 | four `tabGL Entry` inserts for original balanced pair and reversal pair, then commit; H:5996-6025 |
| S07 | insert `tabAccount Closing Balance` and `tabProcess Period Closing Voucher`, then commit; H:6051-6062 |
| S08 | two `tabGL Entry` inserts followed by rollback; H:6082-6091 |

S07 exact columns are not statically frozen: current code intersects runtime schema-discovered columns with common base fields and optional company. Every case is preceded by broader scope seeding. `FIXTURE_MUTATION_TABLES` contains 17 tables at H:317-336, so current authority is broader than the selected case-specific writer contract.

### 7.9 Evidence, JUnit and leakage inventory

Harness-owned `/evidence` outputs at H:138-149 and H:1167-1258 are:

- `fixture-manifest.json`;
- `accounting-results.jsonl`;
- `permission-results.jsonl`;
- `snapshot-results.jsonl`;
- `workload-results.jsonl`;
- `leakage-results.jsonl`;
- `expected-actual-diff.jsonl`; and
- `mutation-sentinel.json`.

External basenames include `junit.xml`, provenance, topology, site-apps, manifest, review and teardown receipts at H:151-161. The current harness does not produce JUnit.

Concrete leakage-bearing source surfaces are:

- `expected-actual-diff.jsonl` stores complete synthetic expected/actual payloads at H:4009-4020;
- fixture records retain fixture/family, decisions, accessor counts and hashes at H:1266-1305;
- pinned Frappe result formatting can emit test identities, formatted errors, tracebacks and captured stdout/stderr;
- assertion failures and dynamic subtest IDs can enter result/JUnit text;
- in-memory log records include fixture ID, outcome, duration class and correlation ID at H:1142-1164;
- the root password is present in process environment; and
- raw process-list account/host values are read before being omitted from retained evidence.

No runtime value, identity, traceback, process-list row, dynamic subtest ID or financial value was collected by this gate.

## 8. Main Control synthesis

### 8.1 Blocker status

| Area | Evidence effect | Status after this gate |
| --- | --- | --- |
| E1 host product | Docker/Compose/cgroup/storage/runtime/security/kernel facts established | narrowed, not closed |
| E1 backend image | exact template emitted no formatted evidence; Docker CLI path also absent | Blocker carried; corrected exact read required |
| R1/E2-A | immutable provenance chain and server tag binding completed | E2-A closed only; digest/compatibility still stopped |
| S2/K1 | host prerequisites narrowed; no Python/image identity/filesystem/signal/secret proof | Blockers carried |
| J2 | exact Frappe lifecycle, private seam, tests/subtests and callback surface inventoried | narrowed; adapter/finalization/runtime behavior blocked |
| P1/W1 | current promotion and authority co-residence identified | blockers carried; selected controller ownership not implemented |
| D1 | statement/data/mutation/topology/reconnect surfaces inventoried | narrowed; exact semantics/grants/role split blocked |
| Four-file authoring | incompatibilities and required splits identified | remains stopped |

E2-A is sufficient to request a separate E2-B exact source-path approval. E3-A is sufficient to define a bounded E3-B static work package. The combined static compatibility closure gate is not ready to start automatically: the Owner must first resolve the E1 fixed-output gap and separately approve E2-B and E3-B inputs. E4 remains the only place for runtime behavior, denial and isolation proof.

### 8.2 Findings by severity

#### Blocker

1. **E1 acquisition contract incomplete.** The exact image template failed at absent `Config.Entrypoint`, and no frozen command established the Docker CLI literal path/hash. Repository evidence: published E1 stop rules; command evidence: exit `1` with the recorded template error.
2. **Authority separation absent in current harness.** Reader, preparation, dynamic mutation, schema, topology, root and reconnect authority co-reside at H:1567-1568, H:2828-2835, H:2956-3049, H:3908-3911, H:4300-4724 and H:5732-6091.
3. **J2/JUnit and finalization not closed.** The private seam is not implemented, inherited callbacks remain unbound, and harness promotion at H:3932-3966 precedes pinned Frappe outer cleanup.
4. **Least-privilege contract cannot be frozen.** Frappe bootstrap/cleanup SQL is untraced, S07 columns are runtime-discovered, and the current mutation authority spans 17 tables.
5. **S2 bootstrap is absent from current harness.** H:38 imports Frappe before any future pre-Frappe signal block.

#### High

1. `SYNTH_DB_ROOT_PASSWORD` is environment-backed while root combines schema, topology, process and reconnect operations.
2. Reconnect validates one process row rather than the selected one-account/IP, exactly-two-session, zero-unrelated-session contract.
3. Topology, schema verification and reconnect are concentrated under root.
4. Dynamic mutation performs schema discovery and uses a broad table union; S07 remains dynamic.
5. Expected/actual payloads, result identities, tracebacks, captured streams, value-bearing subtest IDs and raw process account/host values are concrete leakage surfaces.
6. Full-suite setup and tests mutate state and cannot serve as a read-only cold primer.

#### Medium

- The config blob supplied no digest header, but its referenced identity was independently verified by payload SHA-256; record both facts without treating the missing header as mismatch.
- The tag-to-index relation is inherited from the frozen candidate record; this gate did not dereference a mutable tag.
- The Compose plugin binary is proven, but no assumption is allowed for the Docker CLI path.
- No new accounting-equation contradiction was found.

### 8.3 Reviewer dispositions

Accepted:

- the concrete E1 fixed-template/path stop;
- E2-A only as immutable provenance evidence;
- E3-A only as static inventory;
- the authority, finalization, S07/grant, reconnect and leakage findings above; and
- continued Finance Cycle 1 aggregate/read-only accounting protection.

Rejected:

- metadata-as-runtime or source-as-runtime claims;
- interpreting the image-template failure as image incompatibility;
- digest approval, final grants, complete schema or numeric-limit selection;
- direct `TestRunner`, broad/root measured authority, database-wide `SELECT` or silent role fallback;
- claiming an actual credential/identity/financial-value leak from this gate, because no runtime value was acquired; and
- automatic E2-B, E3-B, E4 or source-authoring progression.

Deferred:

- corrected E1 image/CLI-path evidence;
- numeric identity, filesystem, Python, K1 and S2 proof;
- E2-B MariaDB Server semantic reads;
- E3-B J2/D1 static closure;
- image materialization and E4 runtime canaries;
- complete schemas and numeric workload limits;
- HTTP/CORS, Finance-to-AI, live alignment and accounting execution.

## 9. Exact next prerequisites

### 9.1 Corrected E1 prerequisite

Before a combined compatibility closure gate, the Owner must approve a new exact read-only E1 amendment containing:

1. a key-safe fixed image-inspection template that returns the same permitted fields while representing absent/null keys without raw JSON or output broadening;
2. one exact fixed-output method to establish the Docker CLI literal binary path; and
3. `stat`/`sha256sum` only against that proven literal path.

The amendment must retain the same pinned image ID and all existing prohibitions. Image filesystem, container creation/execution, environment/labels/history/layers and operational data remain outside that correction.

### 9.2 E2-B prerequisite

E2-B cannot begin until the Owner approves a literal MariaDB Server file-path allowlist at peeled commit `197f92bee02d8e836f529f37625be69b83e7acbd`. The path proposal must be limited to exact implementation questions for:

- account/host matching and column/table grants;
- process visibility and exact connection termination authority;
- `INFORMATION_SCHEMA.INNODB_TRX` visibility;
- transaction isolation, read-only consistent snapshots and transaction state;
- replica/topology status privilege; and
- statement/request timeout semantics relevant to the static harness inventory.

E2-B must hash every approved file, stop on absent/different paths and retain source semantics only. Clone, tree dump, general search, adjacent-file expansion, image action, SQL and runtime claims remain prohibited.

### 9.3 E3-B prerequisite

E3-B requires separate approval of an exact static input allowlist and must:

1. consume only the accepted pinned Frappe paths, unchanged harness and accepted receipts;
2. add exact pinned CPython source/build evidence for inherited `unittest` callbacks only after its version/source identity is separately established and allowlisted;
3. freeze the five top-level IDs, safe subtest/holder mapping, superclass delegation and fixed sanitized outcomes;
4. reject unexpected, duplicate or value-bearing IDs and all raw error/trace/output/payload/account/host evidence;
5. map initialization, discovery, runner construction, cleanup, nonzero exit and post-cleanup promotion ordering;
6. trace every mode-specific Frappe bootstrap/cleanup SQL operation;
7. map each static SQL/session/topology/process/mutation operation to one exact role and table/column/system-object candidate;
8. split preparer, normal reader, seal verifier, topology, reconnect and each S01-S08 writer contract;
9. freeze exact S07 insert columns or stop for an exact schema/source approval;
10. freeze unique reconnect account/service-IP, exactly two expected sessions, full target tuple and zero unrelated-session obligations; and
11. classify every runtime-only assertion for E4 without treating a candidate grant matrix as proof.

If E3-B requires an unapproved source path, a fifth source/runtime surface, runtime observation, image/filesystem access or broader privilege, it stops for a new Owner decision.

## 10. Remaining approvals and protected boundaries

The following approvals remain distinct:

1. documentation staging of this receipt;
2. documentation commit;
3. documentation push;
4. corrected E1 fixed-output acquisition;
5. E2-B exact-path source read;
6. E3-B exact static closure;
7. image-filesystem/numeric-identity/Python proof;
8. E4 materialization and controlled canaries;
9. source authoring;
10. image/infrastructure/secret materialization and synthetic execution; and
11. live alignment, migration, metadata, permission, protected-gate and accounting execution.

Finance Cycle 1; Sales, Procurement and Warehouse behavior; Finance workspace boundaries; Shared UI and common runtime; routing; registries; governance manifests; AI Assistant and Finance-to-AI access; the harness/source candidates; source/live separation; and live environments remain protected and unchanged.

`gl_reconstructed` remains the sole synthetic candidate. Aggregate-only, one-company, company-base-currency, default-Finance-Book-plus-blank/NULL, zero-active-dimension, identity-suppressed, fail-closed and no-accounting-execution boundaries remain controlling.

## 11. Validation and future documentation staging allowlist

Validation for this gate requires:

- repository root, branch, local/upstream revision and `0/0` parity;
- empty index;
- candidate scope exactly this evidence receipt plus README, alongside the unchanged harness and four protected exclusions;
- `git diff --check HEAD` and Markdown trailing-whitespace checks;
- resolution of every local Markdown reference;
- unchanged harness hash and absent controller/Dockerfile/initializer;
- unchanged exclusion statuses and hashes;
- E2-A digests described only as proof candidates;
- no complete executable schema or numeric workload limit;
- no E4, source-authoring, runtime or live authority; and
- no operational-data or live-tree access.

If the Owner later authorizes documentation staging, the exact allowlist is only:

1. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/finance-accounting-cycle2-gl-tb-e1-e2a-e3a-read-only-evidence-acquisition-2026-07-18.md`; and
2. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/README.md`.

## 12. Final control statement

**Decision:** `stopped_for_read_only_evidence_gap`

E1 host facts, E2-A provenance and E3-A static inventory are recorded. E1 did not complete its exact image/CLI-path evidence contract, and E3-A confirms material J2/D1/source-role gaps. E2-B, E3-B, E4 and source authoring were not started.

No image pull or layer read, container creation/execution/export/copy, source authoring, infrastructure, secret creation/read, test, Frappe, Bench, SQL, fixture, synthetic execution, HTTP/CORS inspection, live-tree access, staging, commit, push, migration, permission change, protected gate or accounting action occurred.
