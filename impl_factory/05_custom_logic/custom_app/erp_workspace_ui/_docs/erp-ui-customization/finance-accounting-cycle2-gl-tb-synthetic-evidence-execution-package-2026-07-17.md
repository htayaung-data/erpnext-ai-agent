# Finance & Accounting Cycle 2 GL / Trial Balance Synthetic Evidence Execution Package

**Date:** 2026-07-17

**Authority:** Main Control v2, planning only

**Decision:** synthetic_evidence_execution_package_ready_for_owner_decision

**Published evidence baseline:** 45f564a5fe3e87e2262f5c32987d0707b0b5f271

**Synthetic execution:** Not authorized

**Finance Cycle 2 posture:** C2BG2-C2BG5 remain stopped for synthetic evidence; C2B7 and C2C-C2E remain unapproved

## 1. Purpose and bounded decision

This is the canonical planning package for one future disposable synthetic proof of the Finance GL / Trial Balance source posture. It freezes the evidence boundary, environment contract, single harness candidate, accounting and authority fixtures, primary-snapshot proof, workload-cap derivation, evidence formats, review gates, teardown, and exact future command classes.

The sole candidate is **gl_reconstructed**: a custom, aggregate-only, read-only reconstruction from authoritative raw GL Entry and complete Account-chart state.

This package does not:

- authorize creation of the harness;
- authorize a site, database, cache, container, volume, fixture, test, query, benchmark, or teardown;
- approve native General Ledger, native Trial Balance, Query Report passthrough, ACB/cache mode, diagnostic dual mode, or silent fallback;
- create a Finance HTTP endpoint or inspect the deferred global CORS target;
- approve runtime code, UI, Shared UI, routing, registry, governance-manifest, AI Assistant, live, migration, permission, protected-gate, or accounting-execution work;
- claim that a result is closed, reopened, frozen-period controlled, audited, certified, a financial statement, or safe for accounting execution.

Synthetic evidence can close source-proof gaps only. It cannot substitute for later runtime tests, protected-workspace regression, source-to-live alignment, or authenticated live acceptance.

## 2. Authority reconciled

This package is subordinate to, and preserves, the later accepted project truth in:

1. [Main Control V2 Transition Handoff](main-control-v2-transition-handoff-2026-07-16.md);
2. [Codex Delivery Operating Model V1 Pilot](codex-delivery-operating-model-v1-pilot-2026-07-16.md);
3. [Finance & Accounting Capability Map and Integration Plan](finance-accounting-capability-map-integration-plan-2026-07-17.md);
4. [Finance Cycle 2 GL / Trial Balance Scope and Implementation Plan](finance-accounting-cycle2-gl-trial-balance-scope-implementation-plan-2026-07-17.md);
5. [C2A2-C2A5 Scope and Governance Profile](finance-accounting-cycle2-c2a2-c2a5-scope-governance-profile-2026-07-17.md);
6. [C2B1 Exact Installed-Source Fingerprint Receipt](finance-accounting-cycle2-c2b1-exact-installed-source-fingerprint-receipt-2026-07-17.md);
7. [C2B2-C2B6 Installed-Source Semantic Proof and Stop Receipt](finance-accounting-cycle2-c2b2-c2b6-installed-source-semantic-proof-2026-07-17.md);
8. [Targeted C2B Gap-Closure Plan](finance-accounting-cycle2-targeted-c2b-gap-closure-plan-2026-07-17.md);
9. [C2BG1 Targeted Gap Source Fingerprint Receipt](finance-accounting-cycle2-c2bg1-targeted-gap-source-fingerprint-receipt-2026-07-17.md);
10. [C2BG2-C2BG5 Static Semantic Read and Stop Receipt](finance-accounting-cycle2-c2bg2-c2bg5-static-semantic-read-stop-receipt-2026-07-17.md).

The Owner has already decided:

- the cancellation-freeze High is carried as a reporting-only deferral;
- gl_reconstructed is the only synthetic-proof candidate;
- HTTP exposure and the global CORS target are deferred to a separate fingerprint/read gate;
- only this planning package is authorized now.

Later accepted documents supersede older phase labels. No historical phase is reopened unless current evidence contradicts accepted closure.

## 3. Immutable provenance and unresolved execution prerequisites

### 3.1 Accepted application provenance

| Item | Frozen value |
| --- | --- |
| Recorded backend name | erpai_project1-backend-1 |
| Recorded container ID | d7835253b02c0176fb49d84672037c8566d6ac7d29f6b92b4e3baa7c9df20813 |
| Configured image | ghcr.io/htayaung-data/erpnext-factory:erp16.4.1-hrms16.4.0-fac2.3.1-frappe16.5.0 |
| Immutable image ID | sha256:4c8b6fb188d81f5a355008730a1122658af88799ec759029c2dbd297dfc8e257 |
| Immutable repository digest | ghcr.io/htayaung-data/erpnext-factory@sha256:4c8b6fb188d81f5a355008730a1122658af88799ec759029c2dbd297dfc8e257 |
| Frappe installed source | v16.5.0, official commit 4dfcc56090eb3101d18ddb03750391511f163fcf |
| ERPNext installed source | v16.4.1, official commit d74a649016d8bb12ee3c5a24361171cebe860bfc |
| Active-site dialect attested | mariadb |
| Build-present apps | ai_assistant_ui, erp_workspace_ui, erpnext, frappe, frappe_assistant_core, hrms |
| Semantic-read allowlist SHA-256 | 5c16ba40833ac0163ed2b3b083f9db2f28e26b7e66d05730f3366b81894cca82 |
| Active-site attestation SHA-256 | 7fd7114ecbe7053d93f9cc976cc852402301609b027caf280ebc964dfcd9fa8e |

The recorded container is provenance only. A future run must not inspect, attach to, copy from, mount, network with, or execute in that container.

### 3.2 Pre-execution blockers

No synthetic execution may be authorized until all of these are resolved in one immutable execution manifest:

1. exact MariaDB image repository digest and image ID;
2. exact Redis image repository digest and image ID;
3. exact Docker Compose version and engine version;
4. exact materialized compose.yaml SHA-256;
5. exact committed source HEAD and harness SHA-256;
6. exact environment owner, run ID, host, run root, resource ceiling, and setup timeout;
7. exact in-memory secret-injection mechanism;
8. Owner-approved workload budgets from which numeric caps may later be derived.

Tag-only images, image pulls during the run, builds, mutable base images, or unreviewed placeholder expansion stop the package.

## 4. Ownership and protection boundary

| Surface | Frozen owner and rule |
| --- | --- |
| Phase authority, manifest and final adjudication | Main Control v2 |
| Disposable environment and all synthetic state | One named environment owner; no parallel environment writers |
| Accounting equations and literal expectations | Accounting reviewer; reviewed once before execution |
| Permission, identity and error canaries | Security reviewer; reviewed once before execution |
| Primary, snapshot, reconnect and workload evidence | Database/runtime reviewer; reviewed once before execution |
| Future harness source file | One implementation/test owner under a separate Owner gate |
| Sales, Procurement and Warehouse | Protected, no touch |
| Finance Cycle 1 runtime and behavior | Protected, no touch |
| Shared UI, routing, registries and governance manifests | Protected, no touch |
| AI Assistant and Finance-to-AI | No access and no accounting authority |
| Authoritative source repository | Read-only during execution except the separately approved committed harness already present at its frozen hash |
| Live deployment tree and live environment | Prohibited |

The future synthetic site installs only Frappe, ERPNext, and erp_workspace_ui from the pinned application image. HRMS, frappe_assistant_core, and ai_assistant_ui remain build-present but are not installed on the disposable site. This avoids email, notification, integration, CORS, AI, and unrelated accounting-hook activation.

That minimal app set is deliberate containment, not production-app parity. It cannot support a runtime-release claim. Full active-app regression remains a later release gate.

## 5. Disposable environment contract

### 5.1 Exact identity rules

- RUN_ID is one Owner-recorded, lowercase hexadecimal path component matching exactly twelve characters.
- Compose project: c2bg5_<RUN_ID>.
- Site: test_finance_gl_tb_<RUN_ID>.local.
- Database: test_finance_gl_tb_<RUN_ID>.
- Run root: /tmp/erpai-finance-gl-tb-c2bg5/<RUN_ID>.
- All resources carry label com.erpai.finance.c2bg5.run=<RUN_ID>.
- Reuse of a RUN_ID, site, database, container, network, or volume is prohibited.

The twelve-character RUN_ID rule is a resource-name containment rule, not a financial or workload cap.

### 5.2 Required topology

The materialized compose file may define exactly:

- one MariaDB service named db-primary;
- one Redis service named redis-cache;
- one Redis service named redis-queue;
- one Redis service named redis-socketio;
- one non-web application service named test-runner;
- one internal bridge network with internal: true;
- new named volumes for MariaDB data, sites, logs, and evidence;
- temporary, non-persistent Redis storage.

The topology must have:

- no published port;
- no host network, external network, second network, proxy, router, replica, failover target, Docker socket, privileged mode, device, extra host, or host gateway;
- no source, live, home-directory, deployment, site, log, configuration, database, cache, backup, certificate, or operational-data bind mount;
- no web, frontend, websocket, scheduler, worker, queue consumer, mail, notification, integration, exporter, or monitoring service;
- pull_policy set to never and images referenced only by approved repository digest;
- restart disabled;
- a new sites volume over /home/frappe/frappe-bench/sites;
- a new evidence volume mounted only at /evidence in test-runner;
- no copied site_config.json, common_site_config.json, database, cache, files, private files, public files, logs, or secrets.

Docker documents that an internal Compose network is externally isolated. That topology, no second network, no published ports, and no host gateway are all mandatory; configuration flags are additional containment, not substitutes.

### 5.3 Site initialization controls

Before the proof module runs:

- create the site from zero using the new MariaDB primary;
- set the global database and Redis service names to the disposable services only;
- create the Frappe-only site, apply the test/scheduler/email/developer controls, and then install ERPNext;
- set allow_tests true, pause_scheduler true, mute_emails true, and developer_mode false;
- install erp_workspace_ui only after those controls exist;
- verify the exact site app set is frappe, erpnext, erp_workspace_ui;
- verify no CORS setting, integration credential, email account, webhook, queued job, or background worker is active and no email, notification, scheduler, or integration action is executed;
- copy no configuration from any other site.

If app installation attempts email, notification, external network, integration, background work, or an unapproved app dependency, initialization stops and the environment is torn down.

### 5.4 Deterministic teardown

The same environment owner must:

1. capture and verify all sanitized evidence hashes;
2. stop and remove only the exact Compose project;
3. remove its exact named volumes and internal network;
4. verify no resource with the run label remains;
5. remove in-memory secrets from the execution session;
6. retain only the allowlisted sanitized evidence and non-secret execution manifest;
7. produce the teardown receipt.

No system prune, wildcard removal, unrelated-container action, source cleanup, live cleanup, or four-exclusion cleanup is permitted.

## 6. Exact future file allowlists

### 6.1 Repository authoring allowlist

The only future source/test-code candidate is:

impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/tests/test_finance_gl_trial_balance_source_proof.py

No runtime module, fixture helper, second test, endpoint, page, JavaScript, registry, route, hook, manifest, Shared UI, AI Assistant, or ERPNext/Frappe source file may be created or edited.

Harness authoring, review, staging, commit, and push are separate gates. Synthetic execution requires the harness to be committed and its exact source HEAD and SHA-256 accepted first.

### 6.2 Ephemeral control-file allowlist

Only these non-repository control files may exist beneath the run root:

1. compose.yaml;
2. execution-manifest.json;
3. evidence/provenance.json;
4. evidence/topology.json;
5. evidence/site-apps.json;
6. evidence/fixture-manifest.json;
7. evidence/accounting-results.jsonl;
8. evidence/permission-results.jsonl;
9. evidence/snapshot-results.jsonl;
10. evidence/workload-results.jsonl;
11. evidence/leakage-results.jsonl;
12. evidence/expected-actual-diff.jsonl;
13. evidence/mutation-sentinel.json;
14. evidence/junit.xml;
15. evidence/evidence-manifest.sha256;
16. evidence/review-disposition.json;
17. evidence/teardown-receipt.json.

There is no helper script, Dockerfile, SQL dump, copied config, fixture JSON, shell script, Python helper, log archive, screenshot, HTTP capture, or exported report in the allowlist. Literal fixtures and literal expected results live inside the single harness and are separately reviewed.

Secret values are injected from the future approved execution controller environment. No .env file, secret file, credential artifact, or secret-bearing evidence is allowed.

## 7. Exact future command allowlist

### 7.1 Placeholder freeze

The commands below are templates, not authorization. Before execution, Main Control must replace every angle-bracket placeholder once in execution-manifest.json and publish the expanded commands and hashes for Owner approval.

| Placeholder | Frozen rule |
| --- | --- |
| <RUN_ID> | Exact twelve-character lowercase hexadecimal run ID |
| <RUN_ROOT> | /tmp/erpai-finance-gl-tb-c2bg5/<RUN_ID> |
| <PROJECT> | c2bg5_<RUN_ID> |
| <SITE> | test_finance_gl_tb_<RUN_ID>.local |
| <DB_NAME> | test_finance_gl_tb_<RUN_ID> |
| <BACKEND_IMAGE> | ghcr.io/htayaung-data/erpnext-factory@sha256:4c8b6fb188d81f5a355008730a1122658af88799ec759029c2dbd297dfc8e257 |
| <MARIADB_IMAGE> | Owner-approved immutable repository digest; unresolved now |
| <REDIS_IMAGE> | Owner-approved immutable repository digest; unresolved now |
| <SETUP_TIMEOUT_SECONDS> | Owner-approved environment setup ceiling; unresolved now |
| <SOURCE_ROOT> | /home/deploy/erp-projects/erpai_project1_erpnext_ui_design |
| <HARNESS_REL> | impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/tests/test_finance_gl_trial_balance_source_proof.py |
| <TEST_CONTAINER> | c2bg5_<RUN_ID>_test_runner |

The frozen Docker Compose prefix is:

~~~text
docker compose --project-name <PROJECT> --file <RUN_ROOT>/compose.yaml
~~~

Every occurrence of COMPOSE below means that exact prefix. It is a documentation macro only; no shell alias, arbitrary suffix, additional file, profile, environment file, or override is permitted.

### 7.2 Preflight commands

~~~text
sha256sum <SOURCE_ROOT>/<HARNESS_REL>
sha256sum <RUN_ROOT>/compose.yaml <RUN_ROOT>/execution-manifest.json
docker image inspect --format '{{json .Id}} {{json .RepoDigests}}' <BACKEND_IMAGE>
docker image inspect --format '{{json .Id}} {{json .RepoDigests}}' <MARIADB_IMAGE>
docker image inspect --format '{{json .Id}} {{json .RepoDigests}}' <REDIS_IMAGE>
COMPOSE config --quiet
COMPOSE config --images
docker container ls --all --filter label=com.erpai.finance.c2bg5.run=<RUN_ID>
docker network ls --filter label=com.erpai.finance.c2bg5.run=<RUN_ID>
docker volume ls --filter label=com.erpai.finance.c2bg5.run=<RUN_ID>
~~~

Allowed outputs are restricted to the approved image IDs/repository digests, file hashes, and quiet validation result. Unfiltered container inspection, environment output, configuration output, history, logs, or secret display is prohibited.

Preflight stops if:

- any image is absent locally;
- any pull or build would be required;
- a hash differs;
- Compose resolves a tag, build, port, external network, bind mount, extra service, extra volume, or extra app;
- any of the three preflight label-filtered resource checks returns a container, network, or volume.

### 7.3 Create isolated resources

~~~text
COMPOSE up --detach --pull never --wait --wait-timeout <SETUP_TIMEOUT_SECONDS> db-primary redis-cache redis-queue redis-socketio test-runner
COMPOSE ps --all
docker network inspect <PROJECT>_internal
docker volume inspect <PROJECT>_db_data <PROJECT>_sites <PROJECT>_logs <PROJECT>_evidence
docker container inspect --format '{{json .Name}} {{json .Image}} {{json .HostConfig.NetworkMode}} {{json .HostConfig.RestartPolicy.Name}} {{json .HostConfig.Privileged}} {{json .HostConfig.CapAdd}} {{json .HostConfig.Binds}} {{json .NetworkSettings.Ports}} {{json .Mounts}} {{json .Config.Labels}}' c2bg5_<RUN_ID>_db_primary c2bg5_<RUN_ID>_redis_cache c2bg5_<RUN_ID>_redis_queue c2bg5_<RUN_ID>_redis_socketio <TEST_CONTAINER>
~~~

The sanitized container format may output only container name, exact image ID, network name, published-port map, mount type/source/target, restart policy, privilege flag, capability additions, and labels. It must not output environment variables, commands containing secrets, host paths outside the run resources, or container logs.

### 7.4 Initialize the new site

The test-runner container receives SYNTH_DB_ROOT_PASSWORD and SYNTH_ADMIN_PASSWORD only from the future approved in-memory secret channel. The only approved fixed shell payload is the new-site command below; an interactive or general shell is prohibited.

~~~text
COMPOSE exec --no-TTY test-runner bench set-config -g db_host db-primary
COMPOSE exec --no-TTY test-runner bench set-config -g redis_cache redis://redis-cache:6379
COMPOSE exec --no-TTY test-runner bench set-config -g redis_queue redis://redis-queue:6379
COMPOSE exec --no-TTY test-runner bench set-config -g redis_socketio redis://redis-socketio:6379
COMPOSE exec --no-TTY test-runner bash -lc 'bench new-site "<SITE>" --db-type mariadb --db-name "<DB_NAME>" --db-host db-primary --db-port 3306 --db-root-username root --db-root-password "$SYNTH_DB_ROOT_PASSWORD" --admin-password "$SYNTH_ADMIN_PASSWORD" --no-mariadb-socket'
COMPOSE exec --no-TTY test-runner bench --site <SITE> set-config allow_tests true --parse
COMPOSE exec --no-TTY test-runner bench --site <SITE> set-config pause_scheduler true --parse
COMPOSE exec --no-TTY test-runner bench --site <SITE> set-config mute_emails true --parse
COMPOSE exec --no-TTY test-runner bench --site <SITE> set-config developer_mode false --parse
COMPOSE exec --no-TTY test-runner bench --site <SITE> install-app erpnext
COMPOSE exec --no-TTY test-runner bench --site <SITE> install-app erp_workspace_ui
COMPOSE exec --no-TTY test-runner bench --site <SITE> list-apps
~~~

No migrate of an existing site, restore, backup, reinstall, get-app, pull, build, scheduler, worker, console, SQL console, bench execute, HTTP server, or metadata operation is allowlisted.

### 7.5 Copy and run the sole harness

~~~text
docker cp <SOURCE_ROOT>/<HARNESS_REL> <TEST_CONTAINER>:/home/frappe/frappe-bench/apps/erp_workspace_ui/erp_workspace_ui/tests/test_finance_gl_trial_balance_source_proof.py
COMPOSE exec --no-TTY test-runner sha256sum /home/frappe/frappe-bench/apps/erp_workspace_ui/erp_workspace_ui/tests/test_finance_gl_trial_balance_source_proof.py
COMPOSE exec --no-TTY test-runner bench --site <SITE> run-tests --module erp_workspace_ui.tests.test_finance_gl_trial_balance_source_proof --skip-test-records --skip-before-tests --junit-xml-output=/evidence/junit.xml
docker cp <TEST_CONTAINER>:/evidence/. <RUN_ROOT>/evidence/
bash -lc 'cd "<RUN_ROOT>/evidence" && sha256sum --check evidence-manifest.sha256'
~~~

The test command is the only proof execution entry. No pytest discovery, app-wide tests, native report command, browser, HTTP client, RPC, WSGI request, worker, scheduler, queue, email, notification, export, print, download, or accounting document action is allowlisted.

### 7.6 Teardown and absence proof

~~~text
COMPOSE down --volumes --remove-orphans
docker container ls --all --filter label=com.erpai.finance.c2bg5.run=<RUN_ID>
docker network ls --filter label=com.erpai.finance.c2bg5.run=<RUN_ID>
docker volume ls --filter label=com.erpai.finance.c2bg5.run=<RUN_ID>
~~~

All three labeled-resource checks must return no resource. Evidence is retained only under <RUN_ROOT>/evidence. Removing the run root or retained evidence is not part of this command allowlist.

Any command not listed above requires an allowlist amendment and new Owner approval. Placeholder resolution cannot add arguments, services, mounts, paths, commands, or files.

## 8. Single internal proof harness contract

The future harness:

- is test-only and cannot be imported by runtime code;
- contains the proof-only reconstruction, literal fixture builders, literal expected results, authority matrix, snapshot instrumentation, workload generator, leakage scanner, evidence writer, and mutation sentinel in one file;
- invokes an internal Python boundary directly under synthetic user context;
- creates no whitelisted method, route, RPC, REST, GraphQL, socket, page, report, export, download, or browser contract;
- emits no response over HTTP;
- does not call native General Ledger, native Trial Balance, Query Report, Report View, ACB or Process Period Closing Voucher as candidate sources and does not call posting, cancellation, close/reopen, bank, payment, tax, email, notification, or AI paths;
- may write only deterministic fixture state to the disposable database and evidence to /evidence after the future execution gate explicitly permits those synthetic-only writes;
- must prove zero access to live/source configuration and zero write to the source repository.

The internal proof adapter is experimental evidence logic, not production architecture. Passing it authorizes no runtime extraction or reuse.

## 9. Frozen gl_reconstructed accounting contract

### 9.1 Context

One request has exactly:

- one explicitly authorized company;
- that company's base currency only;
- one exact inclusive from_date and to_date;
- one unambiguous company-applicable fiscal year;
- Finance Book cohort company_default;
- zero active accounting dimensions and no Cost Center, Project, Finance Book, currency, consolidation, or account filter;
- complete company Account chart authority;
- reconstruction identifier gl_reconstructed;
- aggregate-only, identity-free public-candidate output.

Missing, ambiguous, alternate, multi-company, multi-currency, cross-fiscal, dimensioned, or filtered context is unavailable. Dates are rejected, never clamped.

### 9.2 Eligible GL row

Every eligible row must:

- match the exact company;
- use a non-group leaf Account from the complete authorized company chart;
- have is_cancelled equal to zero;
- have posting_date no later than to_date;
- have finite, non-negative debit and credit in company base currency;
- be exactly representable at the authoritative installed currency precision;
- belong to the frozen Finance Book cohort;
- contain no unsupported active dimension;
- pass exact source schema and type checks.

Duplicate source rows are additive. The proof must not deduplicate by voucher, account, amount, date, or any heuristic.

### 9.3 Opening, movement and closing

Let FY_START be the exact fiscal-year start. Let the request period be [FROM, TO].

For Balance Sheet root types:

~~~text
OPENING_SET =
  eligible rows where posting_date < FROM
  union
  eligible rows where is_opening = "Yes" and posting_date <= TO
~~~

For Profit and Loss root types:

~~~text
OPENING_SET =
  eligible rows where FY_START <= posting_date < FROM
  and is_opening != "Yes"
~~~

A Profit and Loss row marked as opening is an integrity failure. Prior-fiscal-year Profit and Loss rows do not carry. The unclosed-prior-year Profit and Loss option is unsupported.

For every root type:

~~~text
MOVEMENT_SET =
  eligible rows where FROM <= posting_date <= TO
  and is_opening != "Yes"
~~~

The set operations prevent an opening marker from entering movement or being counted twice.

For each leaf:

~~~text
opening_debit  = exact sum of OPENING_SET debit
opening_credit = exact sum of OPENING_SET credit
period_debit   = exact sum of MOVEMENT_SET debit
period_credit  = exact sum of MOVEMENT_SET credit

closing_debit  = opening_debit  + period_debit
closing_credit = opening_credit + period_credit
closing_net    = closing_debit - closing_credit
~~~

Optional net presentation cannot replace the authoritative six gross debit/credit values. Binary float, tolerance, implicit rounding, invalid-to-zero coercion, silent omission, or unexplained residual is prohibited.

### 9.4 Hierarchy and exact balance

- Every Account appears exactly once in the internal complete-chart manifest, including zero-balance leaves and required parents.
- GL rows contribute only to leaves.
- Each parent equals the exact sum of its descendant leaves and each leaf contributes once to each ancestor.
- Parent closure derives only from the already authorized chart.
- Native permission-bypassing ancestor helpers are not used.
- Duplicate keys, malformed nested-set values, cycle, orphan, cross-company parent, group-account GL, missing root, or unknown root type fails closed.
- Balance is calculated from leaves or roots, never by double-summing displayed parent and child rows.

Required equations:

~~~text
sum(leaf opening_debit) = sum(leaf opening_credit)
sum(leaf period_debit)  = sum(leaf period_credit)
sum(leaf closing_debit) = sum(leaf closing_credit)

(opening_debit - opening_credit)
+ (period_debit - period_credit)
= (closing_debit - closing_credit)
~~~

Every equality uses exact integer minor units or canonical fixed Decimal strings. A one-minor-unit difference fails.

### 9.5 Finance Book

Let D be the one resolved company-default Finance Book and N be source Finance Book NULL or exact empty string.

The only included cohort is:

~~~text
N union {D}
~~~

Opening and movement use the identical cohort. D must exist and be unambiguous. Whitespace is not normalized to blank.

Default-only, selected alternate, blank-only, selected-plus-default toggles, implicit all-books, and fallback are unsupported. Any row from another book is a poison canary and must not affect output.

### 9.6 Fiscal, PCV and cancellation posture

- Exactly one company-applicable fiscal year must contain the full request period.
- A cross-year, missing-year, overlapping-year, inverted-date, or silently clamped request fails.
- Balance Sheet history carries through eligible raw GL.
- Profit and Loss opening resets at fiscal-year start.
- Active PCV GL rows are ordinary eligible GL rows according to date, account, cancellation and book predicates.
- No PCV status, ACB row, cache, retry state, or report result is consumed.
- ACB and Process-PCV records are poison dependencies whose accessor count must remain zero.
- Rows with is_cancelled equal to one are excluded.
- Active immutable-ledger reversal rows are included on their own posting dates and net normally.
- No fixture calls cancellation or makes a freeze-control claim.
- An unbalanced opening is unavailable; the proof never creates retained earnings, closes a year, or certifies completeness.

## 10. Accounting fixture catalog

Literal inputs and literal expected values must be separately reviewed and embedded in the harness. Expected results cannot be generated by the implementation under test.

The core Company A fixture retains the accepted planning values:

- opening Cash debit 100.00 and Equity credit 100.00;
- movement Receivable debit 60.00 and Revenue credit 60.00;
- movement Cash debit 40.00 and Receivable credit 40.00;
- expected closing Cash debit 140.00, Receivable debit 20.00, Revenue credit 60.00, Equity credit 100.00;
- expected closing debit and credit totals 160.00 each.

The future execution manifest must state the synthetic base currency and its authoritative precision. The displayed decimals above are fixture notation, not a hard-coded currency precision or workload limit.

| ID | Required fixture and expected outcome |
| --- | --- |
| A01 | Core opening, movement and closing values match exactly. |
| A02 | Prior-year balanced Balance Sheet rows carry into opening. |
| A03 | Prior-year Profit and Loss rows do not carry; current-year pre-period P&L rows enter opening. |
| A04 | FROM and TO boundary rows enter movement; adjacent rows outside do not. |
| A05 | Valid Balance Sheet opening marker enters opening and never movement. |
| A06 | Profit and Loss opening marker fails closed. |
| A07 | Two leaf branches roll to every parent/root exactly once; zero accounts remain in the internal manifest. |
| A08 | Orphan, cycle, duplicate key, cross-company parent and group-account GL each fail. |
| A09 | Duplicate-looking balanced vouchers are both counted; no semantic deduplication occurs. |
| A10 | Cancelled original and swapped rows with poison amount 777.00 are excluded. |
| A11 | Active original and later immutable reversal are visible by their own dates and net after reversal. |
| A12 | Company B balanced poison amount 999.00 never affects Company A. |
| A13 | Out-of-period poison amount 888.00 never affects the request. |
| A14 | NULL, exact blank and resolved default Finance Book rows are included once; alternate and whitespace-book poison rows are excluded. |
| A15 | Missing or ambiguous company-default Finance Book fails; opening/movement cohort divergence fails. |
| A16 | Short fiscal year succeeds at exact boundaries; multiple fiscal years, cross-year and inverted period fail. |
| A17 | One-minor-unit voucher or aggregate imbalance fails with no tolerance. |
| A18 | Negative, non-finite, excess-scale, malformed date, missing account and wrong-company rows fail. |
| A19 | Active PCV raw GL affects the appropriate period, while PCV/ACB state and cache access remain zero. |
| A20 | ACB/Process-PCV poison mutations do not alter gl_reconstructed output. |
| A21 | Exact leaf/root totals and the signed opening-plus-movement equation agree. |
| A22 | Public-candidate serialization contains aggregates only and no account row or identity. |

Fixture construction may insert deterministic synthetic rows and commit writer transactions only after the future synthetic gate. It may not submit, cancel, amend, close, reopen, post through an accounting controller, or send any external effect.

## 11. Complete-chart permission and leakage fixtures

### 11.1 Positive authority

The one positive actor is an Accounts Manager with:

- exactly one explicit Company A authority;
- complete Account and GL Entry read/field authority for the internal proof;
- no Account, Cost Center, Project, Finance Book, or custom-dimension User Permission;
- no Custom DocPerm override, owner-only rule, mask, share, Custom Role drift, privileged bypass role, or unresolved permission hook;
- zero active accounting dimensions.

Administrator, System Manager, report roles, shares, and AI authority never grant this capability.

### 11.2 Mandatory denial matrix

| ID | Synthetic state | Required result before figures |
| --- | --- | --- |
| P01 | Guest or anonymous | Deny before accounting access. |
| P02 | Accounts User, Auditor, Sales, Procurement, Warehouse, Executive, AI, or roleless user | Deny despite any native report role. |
| P03 | Administrator | Deny privileged context. |
| P04 | Accounts Manager plus System Manager or another bypass role | Deny mixed privilege. |
| P05 | Missing selected company | Deny with no fallback. |
| P06 | Missing, zero, or multiple authorized companies | Deny ambiguous scope. |
| P07 | Company A actor requests Company B | Deny without revealing Company B existence, count, or values. |
| P08 | Account User Permission on any leaf | Deny; never return a partial chart. |
| P09 | Account User Permission on a parent with descendants visible | Deny. |
| P10 | Account User Permission on a parent with descendants hidden | Deny. |
| P11 | Account permission through applicable_for | Deny when relevant to any source DocType. |
| P12 | Cost Center User Permission | Deny. |
| P13 | Project User Permission | Deny. |
| P14 | Active custom Accounting Dimension or dimension permission | Deny initial zero-dimension capability. |
| P15 | Any dimension filter | Reject unsupported scope. |
| P16 | Custom DocPerm removes Account or GL Entry read/report authority | Deny. |
| P17 | Required authority is owner-only | Deny complete-chart posture. |
| P18 | Required field is above the actor's permlevel | Deny. |
| P19 | Required field is masked without effective unmask authority | Deny. |
| P20 | Share-only or everyone-share contributes relevant authority | Deny ambiguous/additive authority. |
| P21 | Wrong-role actor receives Account or GL share | Deny at purpose gate. |
| P22 | Custom Trial Balance or General Ledger report role grants a wrong-role actor | Deny; report role is not source authority. |
| P23 | Custom report role excludes the positive actor | Internal reconstruction remains independent of native report roles. |
| P24 | Relevant permission hook or query condition is unresolved | Deny until exact equivalence is proven. |
| P25 | Selected field is silently omitted by permission handling | Deny; never treat absence as zero. |
| P26 | Unsupported book, period, currency, cross-company or consolidation request | Reject with no figures. |
| P27 | Chart, balance, snapshot, timeout, cap, schema, or canary failure | Return no partial totals. |
| P28 | Authority changes during the read snapshot | Complete old state or reject; never mix authority generations. |

For P01-P26, the accounting accessor invocation count must be zero. P27-P28 may complete internal reads, but no figure or identity may escape.

Positive controls must prove:

- exact internal chart-set equality, including zero accounts and parents;
- Company A and Company B authorized actors see only their own full internal chart;
- irrelevant User Permission and irrelevant share do not change the positive result;
- strict User Permission setting changes do not broaden or narrow the accepted explicit authority;
- native report-role removal does not affect the internal adapter;
- no share is required for positive authority.

No positive control authorizes a second company, account row, report, export, or runtime role policy.

## 12. Primary, transaction, reconnect and concurrency proof

### 12.1 Primary and replica denial

The harness must prove:

- site database host equals db-primary;
- exactly one database service and alias exist;
- no read_from_replica, replica host, proxy, router, secondary connection, failover, or alternative-host retry is configured;
- the MariaDB global read_only value is false;
- SHOW ALL REPLICAS STATUS returns no row;
- every authority, chart, opening, movement, hierarchy, validation and serialization read uses one unchanged database connection ID;
- any unexpected database host, read-only primary state, replication channel, connection pool switch, or proxy stops the case.

The global read_only value alone is not sufficient because privileged users can bypass it. Topology, configuration, replication status, and connection identity must all agree.

### 12.2 Transaction contract

The exact future reader transaction is:

~~~sql
SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;
START TRANSACTION READ ONLY, WITH CONSISTENT SNAPSHOT;
~~~

The harness verifies the pinned-version session isolation, read-only access mode, in-transaction state, storage engine, and connection ID before financial reads.

Authentication context is established before the transaction, but all effective role, company, User Permission, Custom DocPerm, mask, share, Custom Role, dimension, chart, opening and movement state used for the decision is re-resolved inside the same snapshot. Cached authority that cannot be bound to the snapshot is rejected.

### 12.3 Concurrency fixtures

Each fixture pauses the reader after a named internal boundary while a separate writer connection commits a deterministic synthetic change:

| ID | Writer change | Required reader behavior |
| --- | --- | --- |
| S01 | Balanced GL debit/credit pair | Current reader sees complete before-state; new transaction sees complete after-state. |
| S02 | Account leaf/parent change | No hybrid chart and balance generation. |
| S03 | Company/User Permission or Custom DocPerm change | No mixed authority generation. |
| S04 | Company-default Finance Book change | No opening/movement cohort mix. |
| S05 | Fiscal-year overlap or boundary change | No mixed fiscal context. |
| S06 | Active immutable reversal rows | Both rows follow snapshot visibility and posting dates. |
| S07 | PCV/ACB state-only change | No effect and zero PCV/ACB accessor calls. |
| S08 | Writer rollback instead of commit | Reader and next reader both preserve the original committed state. |

Every result is all-old, all-new on a fresh transaction, or unavailable. A hybrid is a stop.

### 12.4 Reconnect handling

The harness terminates the synthetic reader connection after each material boundary in separate cases.

Required behavior:

- auto-reconnect cannot continue the existing reconstruction;
- any connection-ID change invalidates every intermediate value;
- buffered figures and serialized bytes are discarded;
- the attempt returns generic unavailable, or restarts from authentication and the first authority read under a fresh transaction;
- a full restart is allowed only within the later benchmark-derived and Owner-approved retry cap;
- no response byte is released before the whole result validates;
- repeated connection failure never falls back to another host, cache, report, or partial output.

## 13. Benchmark-derived caps

No numeric workload limit is selected by this document.

Before execution, the Owner must approve measurable service budgets for:

- request latency;
- database statement duration;
- process memory;
- examined database rows;
- internal chart accounts;
- internal GL rows;
- serialized UTF-8 response bytes;
- concurrent readers;
- setup and fixture duration;
- reconnect/retry behavior.

The harness then benchmarks monotonically increasing synthetic envelopes for:

- Account-chart size and depth;
- period days within one fiscal year;
- eligible and poison GL row counts;
- Finance Book cohort distribution;
- zero-dimension chart shapes;
- cold and warm application/cache state;
- single-reader and approved concurrent-reader load;
- serialization size;
- failure injection and reconnect.

It captures query plans, statement count, examined rows, wall time, process memory, complete output rows, UTF-8 bytes, connection IDs, and invariant status.

The GL query plan must aggregate by authorized Account keys without loading voucher, party, remarks, owner, contact, bank, tax, payroll, or other identity rows into Python. MAX_OUTPUT_ROWS counts only aggregate objects allowed by the frozen candidate schema; it never permits Account, voucher, or party rows.

The values to derive and version are:

- MAX_ACCOUNTS;
- MAX_PERIOD_DAYS;
- MAX_OUTPUT_ROWS;
- MAX_RESPONSE_BYTES;
- STATEMENT_TIMEOUT_MS;
- REQUEST_TIMEOUT_MS;
- MAX_RETRIES;
- MAX_ACTIVE_DIMENSIONS = 0.

For every numeric limit:

1. select only an observed passing point that satisfies every approved budget in cold, warm and concurrent evidence;
2. keep it strictly within the first observed failing or unstable point;
3. apply no extrapolation, interpolation, inherited default, field-name guess, or unapproved safety margin;
4. record the raw evidence and exact derivation;
5. require a separate Owner acceptance of the derived values before runtime design.

Mandatory boundary cases:

- limit-minus-one, exact limit, and limit-plus-one;
- cap enforcement before ledger aggregation where applicable;
- limit-plus-one returns scope_exceeded and never truncates;
- statement and request timeout cases discard the connection and return no partial output;
- response byte count uses complete serialized UTF-8 bytes, not characters;
- response-size plus one returns response_too_large and never streams or truncates;
- failure after every query, roll-up, invariant and serialization stage returns zero figures;
- zero active dimensions passes; any positive active-dimension count is unsupported.

The evidence run derives limits. It does not approve them for runtime use.

## 14. Identity, error and log containment

### 14.1 Canary families

Seed unique canaries in:

- Account name and Account number;
- parent and root labels;
- party, customer, supplier and employee;
- voucher number, against voucher and reference;
- remarks, title and free text;
- owner, modified_by, user, role, email, phone and address;
- bank, tax, payroll, intercompany and sensitive account-class labels;
- Cost Center, Project and custom dimensions;
- Company B, cancelled, out-of-period and alternate-book rows.

The harness source may contain the literal synthetic canaries. Retained evidence records their hashes and match counts, not the literal values.

### 14.2 Scan targets

Expected canary matches are zero in:

- public-candidate success envelope;
- every denial, unsupported, timeout, integrity and unavailable envelope;
- exception text;
- captured synthetic logger records;
- JUnit failure text;
- expected/actual diffs;
- workload and snapshot artifacts;
- teardown receipt.

The public-candidate success envelope contains context classification, aggregate opening/period/closing debit and credit totals, exact balance indicators, source mode and integrity status only. It contains no account row, account name/number, party, voucher, source record, user, role list, permission detail, action, report route, or export target.

The generic failure envelope is exactly:

~~~json
{
  "status": "unavailable",
  "reason": "finance_context_unavailable",
  "correlation_id": "opaque-synthetic-id"
}
~~~

All authority denials are byte-equivalent after correlation-ID normalization. Errors reveal no failed stage, role, company, account, field, permission, SQL, stack, count, amount, or source path.

Synthetic logs may contain only a fixed event identifier, fixture ID, normalized result class, duration class, and opaque correlation ID. Raw SQL, bind values, user/company/account identity, exception traceback, request argument, secret, and financial amount are prohibited.

## 15. Evidence contract

### 15.1 Canonical encoding

- JSON and JSONL are UTF-8 without BOM.
- Object keys are emitted in the frozen canonical order.
- JSONL has one object per line and a final LF.
- Amounts are integer minor units or canonical fixed Decimal strings, never binary floats.
- Dates are ISO date-only values.
- Hash manifests contain sorted lowercase SHA-256, two spaces, relative path, and final LF.
- Secret values and raw canaries are never retained.

### 15.2 Per-fixture evidence

Every fixture record includes:

~~~json
{
  "fixture_id": "P01",
  "family": "permission",
  "candidate": "gl_reconstructed",
  "input_manifest_sha256": "<hash>",
  "authority_vector_sha256": "<hash-or-null>",
  "expected_decision": "deny",
  "expected_sha256": "<hash>",
  "actual_decision": "not_run",
  "actual_sha256": null,
  "accessor_calls": null,
  "connection_ids_sha256": null,
  "canary_matches": null,
  "exact_diff": "not_run",
  "result": "not_run"
}
~~~

Literal expectations are reviewed separately from the reconstruction functions. The harness must compare expected and actual values and emit an exact structured diff.

### 15.3 Mutation sentinel

The sentinel proves:

- no source repository write;
- no live-tree or operational source access;
- no native report execution;
- no ACB or Process-PCV read;
- no insert/update/delete outside the disposable fixture namespace;
- no submit, cancel, amend, post, close/reopen, queue, worker, scheduler, email, notification, integration, AI, export, download, print, network request, or HTTP response;
- no evidence file outside the allowlist.

### 15.4 Evidence manifest and closure

The evidence manifest covers every retained artifact except itself, then its SHA-256 is recorded in teardown-receipt.json.

Synthetic evidence is ready for the later one-pass closure review only when:

- application, MariaDB and Redis images match approved digests;
- source HEAD, harness, compose and execution-manifest hashes match;
- topology and site app set match exactly;
- every accounting, permission, snapshot, reconnect, workload, limit, timeout, leakage and mutation-sentinel case passes;
- every expected/actual comparison is exact;
- primary-only and one-connection snapshot proof passes;
- no partial or identity-bearing output exists;
- benchmark evidence derives every required numeric cap without invention;
- teardown leaves zero labeled container, network or volume;
- all retained artifacts hash cleanly;
- no in-scope Blocker or High remains after one bounded accounting, security, database/runtime and release review;
- Main Control performs one synthesis and returns either targeted_c2b_gap_closure_pass or stopped_for_targeted_c2b_gap.

Passing synthetic evidence does not start C2B7, C2C, runtime implementation, HTTP work, live alignment, or accounting execution.

## 16. Bounded review synthesis

One planning review pass was performed.

| Review | Accepted | Rejected or narrowed | Deferred |
| --- | --- | --- | --- |
| Accounting | Raw-GL equations, exact minor-unit balance, complete hierarchy, fiscal/cancellation canaries, literal expected results | Alternate/default-selection Finance Book branches were narrowed to the already accepted company-default plus blank/NULL cohort; fixed USD precision was not frozen | ACB/cache, native reports, close/reopen, cancellation control and execution |
| Security | Denial-first authority matrix, complete-chart unavailability, Custom DocPerm/User Permission/mask/share/Custom Role cases, generic errors and canaries | Account rows and account identifiers in a public-candidate response were rejected because the accepted Cycle 2 posture keeps them deferred | Runtime roles, multi-company, dimensions, HTTP and Finance-to-AI |
| Database/runtime | Internal network, one primary, consistent read-only snapshot, connection-ID pinning, reconnect discard, cap derivation and exact teardown | Extra helper scripts, multiple harness files, optional HTTP/web services, cache-mode and PCV/ACB runtime fixtures were rejected | Immutable MariaDB/Redis digests, resource budgets and materialized compose hash |
| Release/governance | One environment owner, no live/source mounts, exact file/command gates, separate authoring/execution/review approvals | Any source/live parity or authenticated acceptance claim from synthetic evidence was rejected | Full active-app regression, Shared UI, protected gates and live acceptance |

No second general counterpart-review loop is authorized. Future review is limited to the frozen execution artifacts and then the frozen evidence, each under its own Owner gate.

## 17. Findings by severity

### Blocker before synthetic execution

1. Immutable MariaDB and Redis image digests and image IDs are not yet supplied.
2. The single harness does not yet exist as an approved committed file with a frozen SHA-256.
3. The materialized compose file and execution manifest do not yet exist at approved hashes.

These are execution prerequisites, not a gap in this planning architecture.

### Existing Blocker to be tested

- One primary, permission-consistent accounting snapshot is not proven by static source. The synthetic package must prove it or stop.

### High

- Effective complete-chart authority remains runtime-state dependent and must pass every denial fixture.
- Finance-specific caps and no-partial timeout behavior do not exist; budgets and synthetic derivation are mandatory.
- The cancellation freeze-call mismatch remains a reporting-only deferral and blocks every cancellation, freeze-control, close/reopen, audit, certification, mutation and execution claim.
- The global Assistant CORS before-request target remains unread. No Finance HTTP endpoint may be proposed before its separate fingerprint/read gate.
- The minimal synthetic app set does not prove full production active-app interaction. Runtime/release parity remains separately gated.

### Medium

- ACB uniqueness, completeness, retry cleanup and GL parity remain unproved; cache mode stays rejected.
- Process-PCV lifecycle behavior is not a source for gl_reconstructed and remains deferred.
- Company-default Finance Book plus blank/NULL equality requires synthetic proof.
- Fiscal ambiguity, malformed hierarchy and reconnect behavior require deterministic negative evidence.

No new evidence-backed planning Blocker or High contradicts the package. The decision remains synthetic_evidence_execution_package_ready_for_owner_decision.

## 18. Stop conditions

Stop before or during the affected future gate if:

- any placeholder is unresolved or expanded differently from the approved manifest;
- any image, source, compose, harness, command, app-set or evidence hash differs;
- any existing resource, live/source mount, operational input, outbound path, port, second network, proxy, replica, worker, scheduler, email, notification or integration is present;
- an unallowlisted file, command, app, import, fixture helper, source dependency or evidence artifact is needed;
- primary identity, transaction isolation, read-only state, connection ID or replica absence cannot be proven;
- any authority state produces a partial chart;
- any amount is rounded through binary float or compared with tolerance;
- opening/movement Finance Book scope diverges;
- dates clamp, hierarchy repairs itself, rows silently disappear, or imbalance is tolerated;
- reconnect continues from prior intermediate values;
- a cap, timeout or response-size failure returns partial/truncated output;
- a canary or forbidden key appears;
- any live or protected workspace is touched;
- an in-scope Blocker or High remains after the one bounded evidence review.

Teardown still runs for the exact synthetic resources after a stopped case. Stopping does not broaden cleanup authority.

## 19. Exact Owner decisions required before synthetic execution

The Owner must separately and explicitly decide all of the following:

1. approve or reject authoring the one harness file and its exact source-code allowlist;
2. after authoring, accept its independent review, committed source HEAD and SHA-256;
3. approve immutable MariaDB and Redis repository digests and image IDs;
4. approve the exact minimal synthetic site app set and accept that it provides no full active-app runtime-parity claim;
5. name the sole environment owner and approve the host, RUN_ID, run root, resource ceilings, setup timeout and in-memory secret channel;
6. approve the materialized compose.yaml and execution-manifest.json hashes;
7. approve the exact accounting equations, literal fixtures, company/base-currency precision input, company-default Finance Book cohort, zero-dimension posture and aggregate-only schema;
8. approve the synthetic Accounts Manager/company authority fixture policy and every denial/canary case;
9. approve the service budgets and cap-derivation method, while accepting that numeric caps will be decided only from later evidence;
10. approve disposable fixture-only writes and writer commits in the new synthetic database, with no ERPNext accounting document action;
11. approve the fully expanded command allowlist, evidence-retention allowlist and deterministic teardown;
12. issue the explicit gate finance_cycle2_gl_tb_targeted_gap_synthetic_execution_authorized.

After execution, a separate Owner gate is still required for one frozen-evidence closure review. No C2B7 or runtime proposal follows automatically.

The deferred CORS fingerprint/read gate is not required for this internal-only proof and must not be bundled into synthetic authorization.

## 20. Current documentation scope and no-execution receipt

After publication commit 45f564a5fe3e87e2262f5c32987d0707b0b5f271, this planning outcome changes only:

1. impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/finance-accounting-cycle2-gl-tb-synthetic-evidence-execution-package-2026-07-17.md
2. impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/README.md

These two files are not authorized for staging, commit, or push by this package.

The four unrelated exclusions remain protected and outside scope:

- impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py
- impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/browser_supplier_payables_fixture_diagnostic.py
- impl_factory/05_custom_logic/custom_app/erp_workspace_ui/ui_smoke/sales_final_acceptance_audit.js
- impl_factory/05_custom_logic/custom_app/erp_workspace_ui/a.out

No synthetic execution, harness implementation, runtime change, HTTP endpoint, CORS inspection, live access, live alignment, restart, cache clear, metadata operation, migration, permission change, protected gate, Finance-to-AI access, or accounting execution occurred while producing this package.

## 21. Authoritative product references

- [Frappe Unit Testing](https://docs.frappe.io/framework/user/en/guides/automated-testing/unit-testing)
- [Frappe bench new-site](https://docs.frappe.io/framework/user/en/bench/reference/new-site)
- [Frappe Users and Permissions](https://docs.frappe.io/framework/user/en/basics/users-and-permissions)
- [Frappe Site Configuration](https://docs.frappe.io/framework/user/en/basics/site_config)
- [MariaDB START TRANSACTION](https://mariadb.com/docs/server/reference/sql-statements/transactions/start-transaction)
- [MariaDB SET TRANSACTION](https://mariadb.com/docs/server/reference/sql-statements/transactions/set-transaction)
- [MariaDB SHOW REPLICA STATUS](https://mariadb.com/docs/server/reference/sql-statements/administrative-sql-statements/show/show-replica-status)
- [MariaDB Read-Only Replicas](https://mariadb.com/docs/server/ha-and-performance/standard-replication/read-only-replicas)
- [Docker Compose Networks](https://docs.docker.com/reference/compose-file/networks/)
- [Docker Compose Services and pull_policy](https://docs.docker.com/reference/compose-file/services/)

Installed pinned-version behavior and accepted synthetic evidence remain authoritative over general documentation.
