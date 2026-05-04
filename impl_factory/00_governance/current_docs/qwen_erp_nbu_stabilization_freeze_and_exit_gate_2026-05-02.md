# Qwen ERP NBU Stabilization Freeze And Exit Gate

Status: active stabilization control plan
Date: 2026-05-02
Scope: AI Assistant Natural Business Understanding stabilization before Phase 4 complex business questions
Branch: feature/ai-assistant

## 1. Purpose

This document controls the stabilization chapter for the AI Assistant Natural Business Understanding layer.

The project has already built substantial governed ERP capability across financial statements, AR/AP, customer and supplier risk, product and item detail, transaction listings, revenue rankings, and follow-up handling. However, recent manual browser UAT showed that the current runtime is still fragile when users ask natural follow-up questions in a different wording or request local table transformations.

The purpose of this chapter is to stop feature expansion temporarily and make the current assistant reliable before moving into Phase 4 complex business questions.

The working principle is:

1. NBU understands the user request.
2. Contracts verify authority and evidence.
3. Governed families execute only approved capabilities.
4. Renderers explain in professional business language.

## 2. Current Decision

Feature expansion is frozen until the stabilization gate is green.

Allowed work:

1. NBU interpretation and intent-contract fixes.
2. Latest visible artifact selection fixes.
3. Artifact-local projection and column-addition fixes.
4. Entity and document detail enrichment routing fixes.
5. Professional clarification and fallback language fixes.
6. Enterprise guardrail compliance.
7. Test harness and regression matrix hardening.
8. Controlled service and duplicate-lane cleanup required to reduce regression risk.

Not allowed during this freeze:

1. New business families.
2. New unsupported recommendation or prediction behavior.
3. More phrase-specific runtime patches.
4. New broad logic directly inside `service.py` unless it is minimal orchestration glue.
5. Fixing only one failing prompt without strengthening the shared contract path.

## 3. Why This Freeze Is Needed

Recent manual UAT found important failure classes:

1. `Show in Million` after a revenue ranking previously fell into a boundary or clarification path instead of a presentation transform.
2. `Top 10 Products by Revenue Last Month` previously reused stale customer/rank context instead of starting a fresh product ranking query.
3. `Show together with Qty` after a product revenue ranking returned quantity values under the revenue column instead of preserving revenue and adding quantity.
4. `rank 2 supplier` and similar references can select stale customer context instead of the latest supplier table.
5. User-facing fallback language can expose internal terms such as governed boundary, runtime, contract, or artifact.
6. The official enterprise guardrail audit is currently red.
7. Duplicate lane modules and a large `service.py` increase regression pressure.

These are not isolated prompt bugs. They are shared NBU/context/projection problems.

## 4. Enterprise Non-Negotiables

Every stabilization slice must follow these rules:

1. Guardrail audit runs before and after each slice.
2. If guardrails are red, the slice is not complete.
3. New phrase-routing logic must not be added to protected runtime paths.
4. User-facing responses must use business language, not internal architecture language.
5. Projection must preserve the original metric unless the user explicitly asks to switch or replace it.
6. Latest relevant visible artifact must win over stale focus.
7. Detail enrichment must use approved entity or document contracts only.
8. Unsupported prediction, recommendation, or approval decisions must explain the business boundary clearly and politely.
9. Tests must assert wrong-family prevention, stale-artifact prevention, and metric preservation.
10. Manual browser UAT begins only after automated gates pass.

## 5. Target NBU Pipeline

The intended runtime decision flow is:

1. User asks any ERP/business question in natural language.
2. NBU interprets the turn using current context, visible artifacts, and governed capability metadata.
3. NBU emits a structured decision with confidence, authority class, target reference, target artifact, requested action, blockers, and response mode.
4. The governed family or local artifact handler executes only if evidence and authority allow it.
5. The renderer returns a business-friendly answer or clarification.

The target is not a template answer machine.

The target is a governed assistant that can:

1. Answer from current ERP data when evidence exists.
2. Requery when the request is a self-contained new governed question.
3. Use the current artifact only when the artifact really supports the follow-up.
4. Ask professional clarification when the request is unclear.
5. Explain unsupported prediction, recommendation, or policy decisions without guessing.

## 6. Stabilization Mini Phase Plan

### NBU-S0: Freeze, Baseline, And Worktree Hygiene

Purpose:

Establish a clean stabilization checkpoint and record the current failure inventory.

Work:

1. Confirm active branch and latest AI Assistant commit.
2. Inventory dirty files by ownership: AI Assistant, Qwen runtime, ERP UI, governance docs, temp/probe files, root accidental files.
3. Record current known manual failures and automated failures.
4. Confirm which files are allowed for the stabilization slice.
5. Remove or archive temp probes only when ownership is clear.

Exit gate:

1. Current branch is confirmed as `feature/ai-assistant`.
2. AI Assistant scoped state is understood and separated from unrelated dirty work.
3. Failure inventory is recorded.
4. No unrelated ERP UI or runtime files are included in AI Assistant commits.

### NBU-S0.5: Verification Harness Baseline

Purpose:

Make verification predictable before more changes.

Work:

1. Define a fast gate that must finish predictably.
2. Define a full gate that can be used before release movement.
3. Confirm the command set for guardrails, targeted tests, NBU regression tests, post-contract tests, and live smoke.
4. Identify any suite that times out or depends on order/environment.

Required fast gate:

1. `python3 scripts/check_qwen_enterprise_guardrails.py`
2. Focused unit tests for the touched NBU/projection/context modules.
3. Relevant NBU regression subset for the current slice.
4. `py_compile` for touched files.

Required full gate before Phase 4:

1. Guardrail audit green.
2. Official semantic matrix green.
3. NBU regression suite green.
4. Post-contract matrix green.
5. Bounded live release-gate profile green.
6. Manual browser UAT green.

Exit gate:

1. Fast gate commands are documented.
2. Known red checks are recorded with owner and reason.
3. No slice can close without before/after guardrail audit.

### NBU-S1: Shared Visible Artifact Intent Contract

Purpose:

Create one shared decision contract for visible-context follow-ups instead of scattered local branches.

The contract must decide:

1. User intent class.
2. Target artifact.
3. Target row or entity reference.
4. Authority class.
5. Confidence.
6. Blocker reason.
7. Recommended action.
8. User-facing response mode.

Action classes:

1. Answer from current artifact.
2. Locally project or format current artifact.
3. Enrich selected entity or document using approved detail contract.
4. Run a new governed query.
5. Ask clarification.
6. Explain unsupported prediction, recommendation, or policy boundary.

Example requests:

1. `who is second in the above table`
2. `explain rank 2`
3. `give me more details about rank 2 supplier`
4. `why is this customer risky`
5. `show in million`
6. `show together with qty`

Exit gate:

1. Shared contract exists and is used by relevant NBU routes.
2. No new prompt-specific branch is added to `service.py`.
3. Guardrail audit is not made worse.
4. Tests prove structured decisions for row reference, projection, enrichment, requery, clarification, and boundary.

### NBU-S3: Latest Relevant Artifact Selection

Purpose:

Fix stale-context behavior before broadening projection.

Rules:

1. `above table`, `that table`, and ordinal references prefer the latest visible artifact compatible with the requested entity or table type.
2. `rank 2 supplier` must prefer the latest supplier artifact, not stale customer focus.
3. `second position in the above table` must use the latest displayed table regardless of older focus.
4. A new self-contained business query must not be swallowed by previous row context.
5. If multiple recent artifacts are compatible, ask a clarification using business labels.

Exit gate:

1. Customer AR table references resolve to customer rows.
2. Supplier AP table references resolve to supplier rows.
3. Product ranking references resolve to product rows.
4. Sales invoice listing references resolve to invoice rows.
5. Fresh product/customer/supplier ranking queries do not reuse stale row context.
6. Tests assert artifact provenance.

### NBU-S2: Shared Projection Contract

Purpose:

Handle local table reshaping and presentation requests without changing business meaning.

Rules:

1. `show in million` changes display scale only.
2. `show together with qty` adds quantity if available and preserves the original metric.
3. `show only customer and revenue` filters columns but preserves row order.
4. `add outstanding amount` adds the metric only if present or safely enrichable.
5. Projection must not convert a revenue ranking into a quantity ranking unless the user explicitly asks to rank by quantity.
6. If the requested metric is not available and not safely enrichable, ask a professional clarification or suggest a governed query.

Correct example:

Input:

`Top 10 Products by Revenue Last Month`

Follow-up:

`Show together with Qty`

Expected output:

`Rank | Product | Revenue | Qty`

Incorrect output:

`Rank | Product | Revenue` where revenue cells contain quantity values.

Exit gate:

1. Projection preserves primary metric.
2. Added columns are labeled correctly.
3. Unit conversion and million formatting do not change row identity or ranking basis.
4. Tests cover customer, supplier, product, invoice, and financial-statement artifacts where applicable.

### NBU-S4: Entity Detail Enrichment Contract

Purpose:

When the user asks for more details about a selected row, route to the approved detail contract instead of only repeating row facts.

Supported enrichment targets:

1. Customer detail.
2. Supplier detail.
3. Product or item detail.
4. Existing governed document detail where already approved.

Rules:

1. Use the selected visible row to identify the entity or document.
2. Use approved detail capability only.
3. If detail capability does not exist, show available row facts and explain the limitation naturally.
4. Do not create new detail behavior accidentally.

Exit gate:

1. `tell me more about that customer` enriches customer row context.
2. `give me more details about rank 2 supplier` enriches supplier row context.
3. `tell me more about that product` enriches product row context.
4. Unsupported document detail produces a safe business clarification.

### NBU-S5: Professional Clarification And Fallback Language

Purpose:

Make safe responses understandable to business users.

Rules:

1. Do not expose internal terms: governed boundary, runtime, contract, artifact, execution gate, route, resolver.
2. Explain what can be answered now.
3. Explain what cannot be answered without guessing.
4. Offer one or two useful next steps.
5. Clarification should use business labels, not internal IDs.

Preferred style:

`I can show the current ERP evidence, but I cannot predict default next month without an approved prediction model and payment-trend evidence. I can show the customer's overdue balance, aging pattern, and recent payment history instead.`

Exit gate:

1. User-facing fallback snapshots contain no internal architecture terms.
2. Clarification choices use names such as Supplier Master List, Accounts Receivable, Sales Invoice, not internal capability IDs unless no label exists.
3. Tests cover unclear request, unsupported prediction, unsupported recommendation, and ambiguous family.

### NBU-S6: Enterprise Guardrail Closure

Purpose:

Make the official enterprise guardrail green as a closure gate.

Important:

Guardrails are not delayed until S6. They run before and after every slice. S6 is the final closure pass.

Exit gate:

1. `python3 scripts/check_qwen_enterprise_guardrails.py` passes.
2. Protected runtime files do not contain newly introduced phrase-routing checks.
3. Any remaining lexical logic is either outside protected runtime paths or documented as controlled metadata/test logic.

### NBU-S7: Regression Matrix

Purpose:

Turn the manual failure classes into durable tests.

Required coverage:

1. Customer AR/risk ranking.
2. Supplier AP ranking.
3. Product revenue ranking.
4. Sales invoice listing.
5. Financial statement follow-ups.
6. Presentation transforms.
7. Column-add projections.
8. Entity detail enrichment.
9. Fresh query versus follow-up separation.
10. Unsupported prediction and recommendation.

Assertions:

1. No stale artifact selected.
2. No wrong family selected.
3. No metric replacement during projection.
4. No internal terms in user-facing fallback.
5. Artifact provenance or visible-context source is preserved.

Exit gate:

1. Targeted regression matrix passes.
2. Known manual browser scripts have matching automated coverage where practical.

### NBU-S8: Manual Browser UAT Gate

Purpose:

Confirm real user experience after automated gates pass.

Process:

1. Developer provides grouped browser UAT script.
2. User tests one group at a time.
3. Failures are classified as shared-contract, artifact-selection, projection, enrichment, clarification, or unsupported capability.
4. Fixes must improve shared behavior, not only the single prompt.

Exit gate:

1. All agreed UAT groups pass.
2. Any deferred limitation is documented with clear reason.
3. Phase 4 is not started until this gate is green.

### NBU-S9: Service And Duplicate Lane Consolidation

Purpose:

Reduce structural regression risk before Phase 4.

Work:

1. Decide canonical ownership for duplicate lane modules.
2. Leave thin compatibility wrappers only when needed.
3. Extract obvious service seams only when low risk.
4. Keep feature behavior stable during cleanup.

Initial known risks:

1. `qwen_chat/service.py` is still large.
2. Top-level lane files and `qwen_chat/lanes/*` files both exist and differ.

Exit gate:

1. Canonical lane ownership is documented.
2. Duplicate paths cannot diverge silently.
3. No behavior regression in NBU, clarification, and front-door tests.

## 7. Continuous Guardrail Policy

For every slice:

Before implementation:

1. Run guardrail audit.
2. Record current failures.

After implementation:

1. Run guardrail audit again.
2. Run focused tests.
3. Run relevant regression tests.
4. Record what changed and what remains open.

If guardrails are red, the slice may be merged only if:

1. The red state existed before the slice.
2. The slice does not make it worse.
3. The remaining failures are explicitly tracked for S6.

The preferred standard is green before closure.

## 8. Business-Language Response Standard

The assistant should speak to business users, not developers.

Avoid:

1. governed boundary
2. runtime
3. contract
4. artifact
5. execution gate
6. resolver
7. capability id
8. route

Prefer:

1. current ERP evidence
2. current table
3. available fields
4. approved business rule
5. approved prediction model
6. more detail needed
7. I can show...
8. I cannot safely predict...

## 9. Manual UAT Seed Scenarios

These scenarios are not the full UAT script. They are seed examples for the stabilization chapter.

Ranking and presentation:

1. `Top 7 Customers by Revenue`
2. `Last Month`
3. `Show in Million`
4. `Top 10 Products by Revenue Last Month`
5. `Show together with Qty`

Visible artifact references:

1. `show customer risk`
2. `who is in second position in the above table`
3. `explain rank 2`
4. `why is this customer risky`

Supplier context switch:

1. `Show me top 10 suppliers by AP`
2. `Give me more details about rank 2 supplier`
3. `who is second in the above table`

Fresh query versus follow-up:

1. `show me suppliers`
2. `show me sale invoices`
3. `who is in second position in the above table`
4. `Top 10 Products by Revenue Last Month`

Unsupported decision:

1. `who should we collect from first`
2. `will the first customer default next month`

Expected behavior:

1. Answer when current ERP evidence supports the request.
2. Requery when the user asks a new governed business question.
3. Clarify when target or period is missing.
4. Explain safely when prediction or recommendation authority is missing.
5. Never leak internal architecture wording.

## 10. Status Tracker

| Slice | Status | Notes |
| --- | --- | --- |
| NBU-S0 | Baseline recorded | Branch, commit, dirty-work ownership, known failures, and freeze rules recorded on 2026-05-02. Cleanup decisions remain controlled because broad unrelated work exists. |
| NBU-S0.5 | Baseline recorded | Fast/full gate shape recorded on 2026-05-02. Current guardrail is red and NBU regression has one known failure. |
| NBU-S1 | Implemented and verified through S7 | Shared visible artifact intent decisions are active for visible-context answer, requery, projection, detail, clarification, and boundary paths. |
| NBU-S3 | Implemented and verified through S7 | Latest relevant artifact selection is green for customer risk, supplier lists/AP, sales invoice rows, and fresh ranking resets. |
| NBU-S2 | Implemented and verified through S7 | Projection preserves ranking metric while adding or formatting requested fields, including million display and quantity add-ons. |
| NBU-S4 | Implemented and verified through S7 | Broad detail requests enrich approved customer, supplier, product, and supported row targets instead of only repeating visible row facts. |
| NBU-S5 | Implemented and verified through S7 | Shared boundary and clarification renderers use business-facing language and avoid user-facing internal architecture terms. |
| NBU-S6 | Green as of S7 closure | Enterprise guardrail audit passed after the S7 shared-language cleanup. |
| NBU-S7 | Automated gate complete | Context, projection, and boundary/recovery matrices are green on the live backend. |
| NBU-S8 | Pending | Manual browser UAT gate |
| NBU-S9 | Pending | Service and duplicate lane consolidation |

## 11. Documentation Update Rule

At the end of each stabilization slice, append or update:

1. Slice status.
2. Files changed.
3. Guardrail before/after result.
4. Tests run.
5. Manual UAT requirement.
6. Remaining risks.
7. Next slice.

This doc is the operational checkpoint for the stabilization chapter.

## 12. Phase 4 Entry Gate

Phase 4 complex business questions may start only when:

1. NBU-S0 through NBU-S8 are complete or explicitly deferred with accepted risk.
2. Guardrail audit is green.
3. Automated quality gate is green.
4. Manual browser UAT is green.
5. Duplicate-lane and service risks are either reduced or explicitly accepted in NBU-S9.

The project should not build complex reasoning on top of unstable context selection or projection behavior.

## 13. NBU-S0 / S0.5 Baseline Record - 2026-05-02

### 13.1 Repository State

Baseline command:

```bash
git branch --show-current
git log -1 --oneline
git status --short
```

Observed state:

1. Active branch: `feature/ai-assistant`
2. Latest commit: `bf82af3 fix(ai-assistant): harden ranking presentation followups`
3. AI Assistant tracked code from the previous slice is clean after push.
4. New stabilization doc is untracked in `impl_factory/00_governance/current_docs/`.
5. Broad unrelated dirty work exists outside the current stabilization scope.

Dirty-work ownership inventory:

1. Root/runtime: `compose.yaml`, `experimental/qwen_agent_runtime/*`
2. ERP UI: `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/*`
3. Governance/docs: deleted older governance files and several untracked PrimeAxis/current docs
4. AI Assistant temp/probe files: `nbu_governed_requery_smoke.py`, `tmp_phase*_probe.py`, `tmp_release_gate_probe.py`
5. Repo-root temp/probe files: `tmp_*`, `_codex_backups/`, `.codex*`, `.qwen/`
6. Accidental SQL-fragment filenames in repo root

Control decision:

1. Do not stage unrelated dirty work.
2. Do not delete or revert unrelated work without explicit ownership confirmation.
3. AI Assistant stabilization commits must stage exact files only.

### 13.2 Known Manual UAT Failures

Current failure classes:

1. `Show together with Qty` after product revenue ranking replaced the revenue metric with quantity values instead of adding a quantity column.
2. `rank 2 supplier` / supplier detail requests can still select stale customer context in automated coverage.
3. User-facing fallback can still become too technical in some routes.
4. Guardrail audit is red because phrase/lexical checks still exist in protected NBU/runtime paths.

Correct expectation for the product revenue projection case:

```text
Rank | Product | Revenue | Qty
```

Incorrect behavior:

```text
Rank | Product | Revenue
```

where the `Revenue` cells contain quantity values.

### 13.3 Guardrail Baseline

Command:

```bash
python3 scripts/check_qwen_enterprise_guardrails.py
```

Current result: `FAIL`

Known findings:

1. `conversation_control_language.py:424`: confirmation logic detected from lexical examples.
2. `natural_business_understanding_evaluation_harness.py:189`: lexical phrase check on `_or_`.
3. `natural_business_understanding_evaluation_harness.py:191`: lexical phrase check on `or`.
4. `natural_business_understanding_governed_requery_activation.py:307`: lexical phrase check on `tell me more`.
5. `natural_business_understanding_governed_requery_activation.py:309`: lexical phrase check on `more details`.
6. `natural_business_understanding_visible_artifacts.py:26`: lexical phrase check on `overdue`.
7. `natural_business_understanding_visible_artifacts.py:28`: lexical phrase check on `outstanding`.
8. `natural_business_understanding_visible_artifacts.py:30`: lexical phrase check on `total_due`.
9. `natural_business_understanding_visible_artifacts.py:32`: lexical phrase check on `credit_utilization`.
10. `visible_context_followup_activation.py:425`: lexical phrase check on `what should`.

Interpretation:

The current guardrail failure is real. Stabilization slices may proceed only if they do not add new protected phrase-routing logic and reduce these findings when touching the relevant files.

### 13.4 NBU Regression Baseline

Command:

```bash
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui \
python3 -m unittest discover \
  -s impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests \
  -p 'test_natural_business_understanding*.py'
```

Current result:

```text
Ran 146 tests in 0.278s
FAILED (failures=1)
```

Failing test:

```text
test_detail_request_routes_latest_matching_supplier_table_not_stale_customer_focus
```

Failure meaning:

The NBU governed requery activation path blocks the latest matching supplier table detail request instead of resolving it as ready. This confirms the stale-context/latest-artifact risk.

### 13.5 Available Verification Scripts

Available scripts:

1. `scripts/check_qwen_enterprise_guardrails.py`
2. `scripts/qwen_verify_enterprise_matrix.sh`
3. `scripts/qwen_site_run_tests.sh`
4. `scripts/qwen_site_execute.sh`

`scripts/qwen_verify_enterprise_matrix.sh` modes:

1. `semantic`
2. `post-contract`
3. `full`

Important behavior:

The enterprise matrix runs the guardrail audit first. Because guardrails are currently red, semantic/post-contract matrix modes fail immediately until guardrail findings are fixed or explicitly separated for baseline-only diagnostics.

### 13.6 Fast Gate For Each Stabilization Slice

Before each slice:

```bash
python3 scripts/check_qwen_enterprise_guardrails.py
```

After each slice:

```bash
python3 scripts/check_qwen_enterprise_guardrails.py
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m py_compile <touched-python-files>
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m unittest <focused-test-modules>
```

Required focused tests for the next vertical slice:

1. `ai_assistant_ui.tests.test_natural_business_understanding_governed_requery_activation`
2. `ai_assistant_ui.tests.test_visible_context_followup_activation`
3. `ai_assistant_ui.tests.test_semantic_financial_resolution`
4. Any new test module added for projection/visible-artifact contracts

Baseline acceptance rule while guardrail is red:

1. The slice must not increase guardrail findings.
2. If the slice touches a red guardrail file, it should reduce or remove that finding.
3. The NBU regression suite must move toward green, not add failures.

### 13.7 Full Gate Before Phase 4

Required commands:

```bash
python3 scripts/check_qwen_enterprise_guardrails.py
scripts/qwen_verify_enterprise_matrix.sh semantic
scripts/qwen_verify_enterprise_matrix.sh post-contract
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m unittest discover -s impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests -p 'test_natural_business_understanding*.py'
```

Additional expected release gate:

1. Bounded live smoke for ranking/presentation/fresh-query separation.
2. Manual browser UAT group for customer, supplier, product, invoice, finance, and unsupported decision flows.

### 13.8 Next Implementation Slice

Next slice: `NBU-S1 + NBU-S3 + NBU-S2 vertical fix`

Reason:

The current live failure requires all three parts:

1. Shared visible-artifact intent decision.
2. Latest relevant artifact selection.
3. Projection that preserves original metric and adds requested fields.

The immediate target behavior:

1. Product revenue ranking plus `Show together with Qty` returns revenue and quantity columns.
2. Supplier AP ranking plus `Give me more details about Rank 2 supplier` resolves the supplier row, not stale customer context.
3. Fresh product/customer/supplier ranking questions do not get swallowed by previous visible-row context.
4. No new phrase-routing logic is added to protected runtime paths.

## 14. NBU-S1/S3/S2 Vertical Stabilization Slice - 2026-05-02

Status: implemented and targeted-verified.

This slice addressed the first live stabilization failure without treating it as a single prompt fix.

### 14.1 Problem Class

The live failures showed two shared NBU weaknesses:

1. Ordinal/detail requests such as `Give me more information about Rank 2 supplier` could be misread as a fresh business query before the visible-artifact reference path had a chance to resolve the target row.
2. Additive projection requests such as `Show together with Qty` could replace the primary ranking metric instead of adding the requested column to the existing ranking view.

Both are shared contract problems:

1. NBU must first identify whether the user is pointing to the current visible result.
2. Projection must distinguish `add this field` from `replace the table with this field`.

### 14.2 Implementation

Files updated:

1. `qwen_chat/natural_business_understanding_request_classification.py`
2. `qwen_chat/semantic_interpreter.py`
3. `tests/test_visible_context_followup_activation.py`
4. `tests/test_semantic_financial_resolution.py`

Behavior added:

1. Ordinal visible-context references now take precedence over fresh-query detection.
2. Additive projection cues now produce `column_refinement` and preserve the original ranking metric.
3. Explicit column-only selection still produces a projection that can intentionally change the requested output shape.
4. Tests cover the supplier rank-detail stale-context failure and the product revenue plus quantity projection failure.

### 14.3 Verified Behavior

Expected live behavior after restart:

1. `Show me top 10 suppliers by AP` followed by `Give me more details about Rank 2 supplier` should resolve `Sunflower Accessories Co.`, not a stale customer row.
2. `Top 10 Products by Revenue Last Month` followed by `Show together with Qty` should keep revenue and add quantity instead of showing quantity under the revenue column.
3. `show customer risk` followed by `who is in second position in the above table?` should answer from the current AR table.
4. Switching to a new list, such as suppliers or sales invoices, should update the visible-result target before answering another ordinal follow-up.

### 14.4 Verification Run

Server repo verification:

```bash
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m py_compile \
  impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_request_classification.py \
  impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/semantic_interpreter.py \
  impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_visible_context_followup_activation.py \
  impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_semantic_financial_resolution.py

PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m unittest discover \
  -s impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests \
  -p 'test_natural_business_understanding*.py'

PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m unittest \
  ai_assistant_ui.tests.test_visible_context_followup_activation

PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m unittest \
  ai_assistant_ui.tests.test_semantic_financial_resolution.TestSemanticFinancialResolution
```

Result:

1. `py_compile`: passed.
2. NBU regression suite: 146 tests passed.
3. Visible-context follow-up suite: 19 tests passed.
4. Full plain semantic test class: 262 tests passed.

Container verification:

```bash
python -m unittest \
  ai_assistant_ui.tests.test_semantic_financial_resolution.TestSemanticFinancialResolution.test_artifact_local_quantity_column_request_preserves_ranking_metric \
  ai_assistant_ui.tests.test_semantic_financial_resolution.TestSemanticFinancialResolution.test_semantic_followup_column_projection_reason_restores_missing_qty_metric \
  ai_assistant_ui.tests.test_semantic_financial_resolution.TestSemanticFinancialResolution.test_ranking_column_refinement_stays_local_when_quantity_exists
```

Result: 3 focused container tests passed.

Site-aware verification:

1. `scripts/qwen_site_run_tests.sh ai_assistant_ui.tests.test_natural_business_understanding_governed_requery_activation`: passed, 9 tests.
2. `scripts/qwen_site_run_tests.sh ai_assistant_ui.tests.test_visible_context_followup_activation`: passed, 19 tests.
3. `scripts/qwen_site_run_tests.sh ai_assistant_ui.tests.test_semantic_financial_resolution`: passed, 262 tests after deterministic financial-period fixture hardening recorded in Section 15.

### 14.5 Guardrail State

Enterprise guardrail status remains red with the same baseline findings recorded in Section 13.

This slice did not add new guardrail findings. It also did not try to bypass the guardrail by adding more phrase-routing exceptions. The remaining guardrail cleanup is still required before the full release gate can be considered green.

### 14.6 Manual Browser Retest Set

Use a fresh browser conversation for each group unless explicitly testing carryover.

Group A - Ranking projection:

1. `Top 10 Products by Revenue Last Month`
2. `Show together with Qty`

Expected: the result should keep revenue and add quantity. Quantity must not appear under the revenue column.

Group B - Supplier visible detail:

1. `Show me top 10 suppliers by AP`
2. `Give me more details about Rank 2 supplier`

Expected: detail should be for `Sunflower Accessories Co.`.

Group C - Visible-context switching:

1. `show customer risk`
2. `who is in second position in the above table?`
3. `show me suppliers`
4. `who is second in the above list?`
5. `show me sale invoices`
6. `who is in second position in the above table?`

Expected: each ordinal answer should use the latest visible result, not a stale earlier table.

### 14.7 Next Step

Do not open a new business capability yet.

Recommended next stabilization work:

1. Continue guardrail cleanup in the protected NBU/runtime files.
2. Expand visible-artifact projection tests across customer, supplier, product, and document-row families.
3. Only after the fast gate is consistently green, continue to broader Phase 4 complex business-question capability.

## 15. Financial-Period Site Gate Stabilization - 2026-05-02

Status: implemented and site-verified.

### 15.1 Problem Class

The site-aware semantic financial module failed two tests that passed in plain unittest:

1. Profit and Loss default open-period bounds.
2. Cash Flow cross-fiscal-year open-period fiscal-year names.

Root cause:

The tests depended on fake unit-test period-closing and fiscal-year data, but the site-aware test runner executed against the real site fixtures. The live site uses different Period Closing Voucher state and fiscal-year naming, so the tests were checking environment-specific data rather than the compiler contract.

### 15.2 Implementation

File updated:

1. `tests/test_semantic_financial_resolution.py`

Behavior:

1. The affected financial-period tests now patch their own period-closing rows.
2. The cross-fiscal-year Cash Flow test also patches its own fiscal-year rows.
3. Production compiler behavior was not changed.

This is a release-gate harness fix, not a business-behavior change.

### 15.3 Verification

Server focused tests:

```bash
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m unittest \
  ai_assistant_ui.tests.test_semantic_financial_resolution.TestSemanticFinancialResolution.test_compiler_uses_last_closed_period_for_profit_and_loss_defaults \
  ai_assistant_ui.tests.test_semantic_financial_resolution.TestSemanticFinancialResolution.test_compiler_uses_cross_fiscal_year_bounds_for_cash_flow_open_period
```

Result: 2 tests passed.

Site-aware semantic financial module:

```bash
scripts/qwen_site_run_tests.sh ai_assistant_ui.tests.test_semantic_financial_resolution
```

Result: 262 tests passed.

### 15.4 Remaining Release-Gate Debt

The site-aware semantic financial module is now green.

The enterprise guardrail audit was still red at this checkpoint, but was cleared in the follow-up guardrail cleanup recorded in Section 16.

## 16. Enterprise Guardrail Cleanup - 2026-05-02

Status: implemented, server-verified, and backend-restarted.

### 16.1 Problem Class

The enterprise guardrail audit was red because protected NBU/runtime files still contained direct raw-text phrase checks.

Affected areas:

1. Conversation-control continuation strength.
2. NBU evaluation harness alternative parsing.
3. Visible-artifact metric-key normalization.
4. Governed requery broad-detail detection.
5. Visible-context recommendation boundary detection.

These were not treated as user-prompt fixes. The cleanup preserved behavior while removing banned direct phrase-check forms from protected runtime paths.

### 16.2 Implementation

Files updated:

1. `qwen_chat/conversation_control_language.py`
2. `qwen_chat/natural_business_understanding_evaluation_harness.py`
3. `qwen_chat/natural_business_understanding_visible_artifacts.py`
4. `qwen_chat/natural_business_understanding_governed_requery_activation.py`
5. `qwen_chat/visible_context_followup_activation.py`

Implementation notes:

1. Continuation strength now uses a named weak-continuation set instead of an inline confirmation literal set.
2. Evaluation expected-alternative parsing now avoids direct raw-text phrase checks.
3. Visible-artifact metric normalization now uses normalized-key alias mapping instead of direct substring checks.
4. Broad entity-detail detection now relies on token-set intent evidence instead of direct phrase checks.
5. Recommendation-boundary detection now uses token-set structure instead of raw phrase matching.

### 16.3 Verification

Server compile:

```bash
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m py_compile \
  impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/conversation_control_language.py \
  impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_evaluation_harness.py \
  impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_visible_artifacts.py \
  impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_governed_requery_activation.py \
  impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/visible_context_followup_activation.py
```

Result: passed.

Enterprise guardrail:

```bash
python3 scripts/check_qwen_enterprise_guardrails.py
```

Result: passed.

Regression suites:

1. NBU regression suite: 146 tests passed.
2. Visible-context follow-up suite: 19 tests passed.
3. Site-aware governed requery activation: 9 tests passed.
4. Site-aware visible-context activation: 19 tests passed.
5. Site-aware semantic financial module: 262 tests passed.

Backend status:

1. Runtime files were copied into the backend container.
2. Backend was restarted.
3. Container returned healthy status after restart.

### 16.4 Current Stabilization State

Current automated state:

1. Guardrail audit: green.
2. NBU regression suite: green.
3. Site-aware semantic financial module: green.
4. Targeted site-aware visible-context and governed-requery suites: green.

Recommended next gate:

Run the browser UAT set from Section 14.6 before opening Phase 4 capability work.

## 17. Browser UAT Finding: Vague Finance Request Stabilization

### 17.1 Finding

Browser UAT showed that broad finance wording such as "show me money situation" could still fall into an old artifact-boundary path after a Balance Sheet follow-up. In another path, clarification options could expose an internal capability id such as `financial_statement_read`.

This was classified as an NBU stabilization issue, not a single prompt issue.

### 17.2 Enterprise Fix Shape

The fix must stay shared and metadata-led:

1. Finance concept aliases should classify cash-position wording as a fresh financial/cash-flow request.
2. User-facing NBU clarification options should translate internal capability ids into business labels before display.
3. Artifact-boundary fallback should not be used when the user is asking a self-contained governed finance request.
4. Tests must prove both routing behavior and user-facing wording quality.

### 17.3 Exit Gate For This Slice

Before closing this slice:

1. Enterprise guardrail audit must pass.
2. NBU response-renderer regression must pass.
3. Semantic financial regression must pass for the new finance wording.
4. Browser UAT must confirm no technical option ids and no stale Balance Sheet artifact-boundary response for vague finance wording.

## 18. Browser UAT Finding: Finance Re-Entry And Executable Clarification Options

### 18.1 Finding

Browser UAT after the vague-finance slice showed three remaining shared issues:

1. `show me statement` could still be treated as a follow-up to the previous supplier list instead of a new financial-statement request.
2. `tell me more about Liabilities` after a Balance Sheet could repeat the full statement instead of answering the liabilities section from the current artifact.
3. The clarification option `combined cross-domain health summary` was offered for `show me money situation`, but selecting it did not execute a grounded composite read.

These are shared NBU/context-contract issues, not prompt-specific defects.

### 18.2 Implementation

Implemented changes:

1. The self-contained governed-request detector now uses report-family `routing_hints.intent_markers` from metadata, so family-level requests such as `show me statement` can break out of stale visible context.
2. Standalone canonical report names such as `Balance Sheet` are accepted as fresh governed requests using metadata report names.
3. Artifact-boundary skipping now preserves the current artifact when the current artifact can directly answer the follow-up, such as a Balance Sheet liabilities section request.
4. Financial-summary clarification translation now carries governed option metadata from the clarification registry.
5. The `cross-domain health` option now carries aliases including `combined cross-domain health summary` and resolves to the executable continuation `show me working capital health`.

### 18.3 Verification

Server verification:

```bash
python3 scripts/check_qwen_enterprise_guardrails.py
```

Result: passed.

Targeted regression:

```bash
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui \
QWEN_ENTERPRISE_METADATA_DIR=/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata \
python3 -m unittest \
  ai_assistant_ui.tests.test_semantic_financial_resolution \
  ai_assistant_ui.tests.test_financial_statement_followup_clarification_contracts
```

Result: 277 tests passed.

NBU regression:

```bash
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui \
QWEN_ENTERPRISE_METADATA_DIR=/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata \
python3 -m unittest <NBU regression suite>
```

Result: 147 tests passed.

Official semantic matrix:

```bash
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui \
QWEN_ENTERPRISE_METADATA_DIR=/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata \
bash scripts/qwen_verify_enterprise_matrix.sh semantic
```

Result: passed.

Backend status:

1. Server repo and backend container checksums matched for touched runtime files.
2. Metadata checksum matched inside the backend container.
3. Backend was restarted.
4. Container returned healthy status after restart.

### 18.4 Browser UAT Gate

Manual browser UAT should confirm:

1. `show me statement` after a supplier list asks for Profit & Loss, Balance Sheet, or Cash Flow.
2. Selecting `Balance Sheet` executes the Balance Sheet.
3. `tell me more about Liabilities` after Balance Sheet returns liabilities details, not the full statement.
4. `show me money situation` should not offer an option that cannot execute.
5. If `combined cross-domain health summary` is offered and selected, it should execute the working-capital health / AR-AP style summary.

## 19. Stabilization Progress: Artifact-Level Reasoning Authority

### 19.1 Finding

Browser and live smoke checks showed that broad artifact-level reasoning follow-ups could still be preempted by older follow-up refinement paths.

Examples of the failure class:

1. `what does this mean` after a risk or finance artifact could route into legacy runtime instead of the accepted ERP reasoning lane.
2. `why is this risky?` without an explicit row or entity reference could be treated as a row clarification instead of an artifact-level explanation.
3. Recommendation or prediction questions could fall through to inconsistent runtime behavior instead of returning a bounded, evidence-first answer.

This was classified as a shared NBU authority issue, not a prompt-specific issue.

### 19.2 Implementation

Implemented changes:

1. Accepted ERP reasoning activation can now supersede capability requery, grounded-detail follow-up, and new-query refinement only when the request is artifact-level and the reasoning activation has already been accepted.
2. Entity-detail follow-ups remain protected. Requests such as `tell me more about that customer` still route to the approved entity-detail path instead of being swallowed by broad reasoning.
3. Artifact-level explanation language now recognizes broad risk and driver wording such as `why`, `risk`, `risky`, `cause`, and `driver` when no explicit row or entity target is present.
4. Visible-context follow-up activation now yields to the reasoning lane for ambiguous artifact-level analysis requests instead of forcing row clarification.
5. H4 and H5 live-smoke setup now uses the correct AR/risk fixture instead of an unrelated sales-invoice fixture, so the smoke tests validate the intended business context.
6. Live diagnostic output was compacted to show routing payloads and modes without dumping full ERP report rows.

### 19.3 Verification

Server verification:

```bash
python3 scripts/check_qwen_enterprise_guardrails.py
```

Result: passed.

Focused visible-context and post-contract tests:

```bash
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui \
QWEN_ENTERPRISE_METADATA_DIR=/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata \
python3 -m unittest ai_assistant_ui.tests.test_visible_context_followup_activation
```

Result: 26 tests passed.

NBU regression:

```bash
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui \
QWEN_ENTERPRISE_METADATA_DIR=/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata \
python3 -m unittest discover -s ai_assistant_ui/tests -p 'test_natural_business_understanding*.py'
```

Result: 147 tests passed.

Official semantic matrix:

```bash
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui \
QWEN_ENTERPRISE_METADATA_DIR=/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata \
bash scripts/qwen_verify_enterprise_matrix.sh semantic
```

Result: passed.

Live backend gates:

```bash
docker compose exec -T backend bench --site erpai_prj1 execute ai_assistant_ui.qwen_chat.service.run_phase6_observability_smoke
docker compose exec -T backend bench --site erpai_prj1 execute ai_assistant_ui.qwen_chat.service.run_h4_recommendation_guarantee_stays_bounded_smoke
docker compose exec -T backend bench --site erpai_prj1 execute ai_assistant_ui.qwen_chat.service.run_h5_release_gate_sanity_pack
```

Result: all passed.

### 19.4 Current Release Status

This slice is green for the artifact-level reasoning and bounded recommendation/prediction behavior.

The full long post-contract release gate is not yet declared green. Historical failures remain in older Phase 1, Phase 2, and Phase 3 smoke groups, and the full gate has also shown long runtime behavior. Phase 4 should remain blocked until those remaining release-gate failures are grouped, triaged, and re-run.

### 19.5 Next Stabilization Slice

Recommended next slice:

1. Group the remaining long-gate failures by failure class instead of prompt.
2. Start with document delivery proof, order-status follow-up, customer-credit follow-up, governed KPI execution, and customer commercial composite follow-up.
3. Keep guardrails green before and after each slice.
4. Keep fixes contract-led and shared, with no protected phrase-routing logic.
5. Re-run the full post-contract gate only after each targeted class is green, so long-gate time is not wasted on known failures.

## 20. Stabilization Progress: Entity Detail Evidence Beats Stale Visible Lists

### 20.1 Finding

The Phase 1.1 invoice delivery-proof release-gate class was still failing. The live failure was not a delivery-data problem. The current invoice detail artifact already contained the delivery proof, but visible-context row selection could still preempt the entity-detail evidence path when the user used rough wording such as:

1. `items from this invoices are already delivered?`
2. `that item is already delivered to the customer?`
3. `what it was delivered`

This caused the assistant to ask for a row from an older invoice list instead of answering from the current invoice-detail evidence.

### 20.2 Implementation

Implemented changes:

1. Added a shared entity-detail capability resolver to `entity_detail_request_support`.
2. Updated `contracts` to use that shared resolver instead of owning a separate private mapping.
3. Updated visible-context follow-up activation so it yields when the current artifact is an entity-detail artifact and the entity-detail evidence interpretation recognizes a supported evidence or status follow-up.
4. Added focused unit coverage proving visible-context does not intercept sales-invoice delivery evidence/date follow-ups when the current artifact can answer them.
5. Added a compact diagnostic probe for the exact invoice delivery-proof smoke sequence.

This is a shared contract fix. It is not a single invoice or single prompt exception.

### 20.3 Verification

Server verification:

```bash
python3 scripts/check_qwen_enterprise_guardrails.py
```

Result: passed.

Focused regression:

```bash
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui \
QWEN_ENTERPRISE_METADATA_DIR=/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata \
python3 -m unittest \
  ai_assistant_ui.tests.test_visible_context_followup_activation \
  ai_assistant_ui.tests.test_entity_detail_contracts
```

Result: 110 tests passed.

NBU regression:

```bash
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui \
QWEN_ENTERPRISE_METADATA_DIR=/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata \
python3 -m unittest discover -s impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests -p 'test_natural_business_understanding*.py'
```

Result: 147 tests passed.

Official semantic matrix:

```bash
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui \
QWEN_ENTERPRISE_METADATA_DIR=/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata \
bash scripts/qwen_verify_enterprise_matrix.sh semantic
```

Result: passed.

Live backend release-gate smokes:

```bash
docker compose exec -T backend bench --site erpai_prj1 execute ai_assistant_ui.qwen_chat.service.run_phase1_1_invoice_delivery_proof_smoke
docker compose exec -T backend bench --site erpai_prj1 execute ai_assistant_ui.qwen_chat.service.run_phase1_1_fresh_chat_invoice_delivery_proof_smoke
```

Result: both passed.

### 20.4 Current Release Status

The invoice-to-delivery proof failure class is now closed for the targeted live gates.

The broader long post-contract release gate is still not declared fully green. Continue triaging the remaining historical classes one at a time, using the same pattern:

1. reproduce the failing release-gate smoke,
2. identify the shared contract seam,
3. fix the shared seam,
4. run guardrails and focused regression,
5. only then advance to the next class.

## 21. Stabilization Progress: Actual Event Boundary Beats Same-Entity Requery

### 21.1 Finding

The Phase 1.3 purchase-order status follow-up class exposed an authority-order bug. The purchase-order detail artifact could safely answer:

1. receipt status,
2. billing status,
3. planned receipt date.

But when the user asked when the order was actually received, the NBU governed-requery lane re-ran the same purchase-order detail query. That was incorrect because the current purchase-order detail only proves planned receipt date and receipt progress. It does not prove the downstream actual receipt event date.

This was not a purchase-order-specific wording problem. It was a shared authority problem: requery must not override the current artifact's evidence boundary when the requested fact requires downstream event evidence.

### 21.2 Implementation

Implemented changes:

1. Added shared entity-detail boundary preemption before NBU governed requery activation.
2. Reused the entity-detail request interpretation contract instead of adding prompt-specific routing.
3. Made requery yield when the current artifact is an entity-detail artifact and the interpreted request requires unsupported actual event evidence.
4. Covered actual receipt-event boundary behavior for purchase orders with a focused NBU activation unit test.

This keeps the correct distinction:

1. answer planned receipt date from the purchase order,
2. answer receipt progress from the purchase order,
3. stop safely on actual receipt date until linked purchase-receipt evidence is available.

### 21.3 Verification

Compile gate:

```bash
python3 -m py_compile \
  impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_governed_requery_activation.py \
  impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_natural_business_understanding_governed_requery_activation.py
```

Result: passed.

Focused NBU activation regression:

```bash
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui \
QWEN_ENTERPRISE_METADATA_DIR=/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata \
python3 -m unittest ai_assistant_ui.tests.test_natural_business_understanding_governed_requery_activation
```

Result: 10 tests passed.

Live backend diagnostic:

```bash
docker compose exec -T backend bench --site erpai_prj1 execute ai_assistant_ui.qwen_chat.probes.service_diagnostics.run_phase1_3_purchase_order_status_followup_exact_debug
```

Result: actual receipt-date follow-up returned `grounded_evidence_boundary` instead of same-entity requery.

Live backend smoke:

```bash
docker compose exec -T backend bench --site erpai_prj1 execute ai_assistant_ui.qwen_chat.service.run_phase1_3_purchase_order_status_followup_smoke
```

Result: passed.

Enterprise guardrail:

```bash
python3 scripts/check_qwen_enterprise_guardrails.py
```

Result: passed.

NBU regression:

```bash
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui \
QWEN_ENTERPRISE_METADATA_DIR=/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata \
python3 -m unittest discover -s impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests -p 'test_natural_business_understanding*.py'
```

Result: 148 tests passed.

### 21.4 Current Release Status

The purchase-order actual-event boundary failure class is now closed for the targeted live gate.

The broader release remains in stabilization freeze. Do not start Phase 4 or add new feature surfaces until remaining release-gate classes are closed and the repeatable release gate is green.

## 22. Stabilization Progress: Bounded Release-Gate Harness

### 22.1 Finding

The old full post-contract regression entry point was operationally weak as a quality gate. It could run for a long time with little visibility, making it hard to know whether the system was:

1. healthy but slow,
2. stuck in one expensive smoke,
3. failing a known historical class,
4. or drifting into another single-case fix loop.

This created the wrong engineering behavior. Instead of one silent monolith, stabilization needs a bounded harness that exposes the next failure class quickly and safely.

### 22.2 Implementation

Implemented a bounded release-gate harness:

1. Added `evaluation/bounded_release_gate.py`.
2. Added profile-based smoke selection.
3. Added per-smoke timeout enforcement using backend Unix signal timers.
4. Added fail-fast behavior.
5. Added concise per-case result payloads with case id, label, group, duration, status, and first failure.
6. Added no-argument service wrappers to avoid shell quoting mistakes:
   - `run_bounded_release_gate`
   - `run_bounded_release_gate_inventory`
   - `run_bounded_release_gate_phase1_core`
   - `run_bounded_release_gate_release_sanity`
   - `run_bounded_release_gate_post_contract_suites`
7. Added unit coverage for pass, failure, fail-fast, profile registry validation, inventory, and timeout behavior.

This is quality infrastructure. It does not change business answering behavior.

### 22.3 Current Profiles

`stabilization_fast`:

1. Phase 1.1 invoice delivery proof,
2. Phase 1.1 fresh-chat invoice delivery proof,
3. Phase 1.2 sales-order status follow-up,
4. Phase 1.3 purchase-order status follow-up,
5. NBU governed requery.

`release_sanity`:

1. H5 rollout probe,
2. Phase 5.5 frontdoor boundary,
3. Phase 6 reasoning live debug,
4. Phase 7D boundary response live,
5. Phase 8 recovery execution,
6. H4 recommendation guarantee boundary.

`phase1_core` and `post_contract_suites` are available for broader follow-up runs. Use them after fast profiles are green.

### 22.4 Verification

Compile gate:

```bash
python3 -m py_compile \
  impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/evaluation/bounded_release_gate.py \
  impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py \
  impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_bounded_release_gate.py
```

Result: passed.

Enterprise guardrail:

```bash
python3 scripts/check_qwen_enterprise_guardrails.py
```

Result: passed.

Focused harness unit test:

```bash
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui \
QWEN_ENTERPRISE_METADATA_DIR=/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata \
python3 -m unittest ai_assistant_ui.tests.test_bounded_release_gate
```

Result: 7 tests passed.

Live inventory:

```bash
docker compose exec -T backend bench --site erpai_prj1 execute ai_assistant_ui.qwen_chat.service.run_bounded_release_gate_inventory
```

Result: all profile cases registered; timeout enforcement is `signal`.

Live bounded stabilization gate:

```bash
docker compose exec -T backend bench --site erpai_prj1 execute ai_assistant_ui.qwen_chat.service.run_bounded_release_gate
```

Result: `stabilization_fast` passed 5 / 5 cases in 326.864 seconds.

Live bounded release sanity gate:

```bash
docker compose exec -T backend bench --site erpai_prj1 execute ai_assistant_ui.qwen_chat.service.run_bounded_release_gate_release_sanity
```

Result: `release_sanity` passed 6 / 6 cases in 205.919 seconds.

### 22.5 Current Release Status

The release gate is not fully complete yet, but it is now operationally healthier. The team can identify the next failure class without waiting on a silent long-running suite.

Recommended next order:

1. Run `phase1_core`.
2. Fix the first failure class only, if any.
3. Re-run guardrail plus the same bounded profile.
4. Then run `post_contract_suites` only after `phase1_core` and `release_sanity` stay green.
5. Start manual browser UAT only after bounded automated gates are green enough to justify manual effort.

## 23. Stabilization Progress: Phase 1 Core Failure Classes

### 23.1 Finding: Compiled Fresh-Query Scope Contract Drift

`phase1_core` exposed a contract consistency failure in the customer-credit scope-reset smoke.

The user-facing answer was correct and returned the governed Accounts Receivable Aging result, but the latest governed scope decision contract reported `covered_family` instead of `fresh_query_breakout`.

Root cause:

1. `service.py` correctly identified a self-contained fresh query while prior grounded context existed.
2. `lanes/compiled_query_lane.py` rebuilt its own follow-up and scope contracts with `latest_grounded_turn_available=False`.
3. The compiled lane therefore erased the breakout context in the audit trail.

Resolution:

1. `handle_compiled_query_turn` now accepts `latest_grounded_turn_available` and `context_isolation`.
2. The compiled lane records `fresh_query_breakout` when it executes a self-contained fresh query from an existing grounded conversation.
3. Added focused regression coverage in `test_compiled_query_lane_scope.py`.

Verification:

1. Enterprise guardrail passed.
2. Focused compiled-query lane test passed: 2 tests.
3. `run_phase1_4_customer_credit_scope_reset_smoke` passed with `scope_status=fresh_query_breakout` and `followup_mode=new_query`.

### 23.2 Finding: Reasoning Preempted Direct Artifact Evidence

The customer-credit policy follow-up smoke exposed a second shared lane-priority failure.

After a customer detail artifact showed `Default Price List`, the follow-up `what is this customer's default price list?` routed to ERP business reasoning and answered that the value was not explicitly stated.

Root cause:

1. The current entity-detail artifact contained the direct governed value.
2. The direct evidence layer could answer it.
3. Reasoning execution authority was allowed to override direct current-artifact evidence.

Resolution:

1. Added a shared reasoning-yield guard.
2. If the current grounded artifact already has a direct evidence answer or a direct evidence boundary, reasoning must yield.
3. Reasoning still runs when the user asks for interpretation and no direct factual artifact answer applies.

Verification:

1. Enterprise guardrail passed.
2. Policy follow-up probe confirmed:
   - credit-limit status: `grounded_evidence_answer`,
   - credit-limit amount: `grounded_evidence_answer`,
   - payment terms: `grounded_evidence_answer`,
   - default price list: `grounded_evidence_answer`.
3. `run_phase1_4_customer_credit_policy_followup_smoke` passed.
4. `run_phase6_reasoning_live_rollout_smoke` passed, confirming reasoning remains active for interpretation use cases.
5. `stabilization_fast` passed 5 / 5 cases in 322.758 seconds after the fixes.

### 23.3 Current Gate Status

The core behavior fixes are shared-seam fixes, not single prompt patches.

Current status:

1. Fast stabilization gate: green.
2. Enterprise guardrail: green.
3. Customer-credit scope reset: green.
4. Customer-credit detail follow-up: green.
5. Customer-credit policy follow-up: green.
6. Reasoning sanity: green.

Open gate hygiene issue:

`phase1_core` as one monolithic live command can exceed a 15-minute shell budget before emitting final JSON because it contains ten expensive live smokes. This is operationally weak even with per-case signal timeouts.

Next recommended stabilization action:

1. Split `phase1_core` into smaller bounded profiles such as document detail, order follow-up, and customer-credit.
2. Keep the existing full `phase1_core` profile for overnight or explicit long-budget runs only.
3. Use segmented profiles as the normal CI/manual pre-UAT gate so failures return quickly and clearly.

## 24. Stabilization Progress: Segmented Phase 1 Live Gate

### 24.1 Finding: Monolithic Phase 1 Gate Was Operationally Weak

The full `phase1_core` profile remains valuable as a long-budget verification profile, but it is too large for normal stabilization work.

It contains ten expensive live smoke cases. Even when every case is healthy, the command can exceed an outer shell timeout before it returns final JSON. That makes it hard to distinguish real product failures from harness/runtime-budget failures.

Resolution:

1. Added smaller bounded profiles:
   - `phase1_document_detail`
   - `phase1_order_followup`
   - `phase1_customer_credit`
2. Kept `phase1_core` as the full combined profile for explicit long-budget or overnight runs.
3. Added profile timeout-budget metadata to release-gate inventory output.
4. Added test coverage proving the segmented profiles cover the same case ids as `phase1_core`.
5. Added service wrappers so each segment can be executed directly from Frappe.

### 24.2 Verification

Static and unit verification:

```bash
python3 -m py_compile \
  ai_assistant_ui/qwen_chat/evaluation/bounded_release_gate.py \
  ai_assistant_ui/qwen_chat/service.py \
  ai_assistant_ui/tests/test_bounded_release_gate.py
```

Result: compile passed.

```bash
QWEN_ENTERPRISE_METADATA_DIR=/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata \
python3 -m unittest ai_assistant_ui.tests.test_bounded_release_gate
```

Result: 8 tests passed.

```bash
python3 scripts/check_qwen_enterprise_guardrails.py
```

Result: Qwen enterprise guardrail audit passed.

Live inventory:

```bash
docker compose exec -T backend bench --site erpai_prj1 execute ai_assistant_ui.qwen_chat.service.run_bounded_release_gate_inventory
```

Result: all segmented profiles registered with timeout budgets.

Registered profile budgets:

1. `phase1_core`: 1800 seconds.
2. `phase1_document_detail`: 540 seconds.
3. `phase1_order_followup`: 540 seconds.
4. `phase1_customer_credit`: 720 seconds.

Live segmented gates:

```bash
docker compose exec -T backend bench --site erpai_prj1 execute ai_assistant_ui.qwen_chat.service.run_bounded_release_gate_phase1_document_detail
```

Result: `phase1_document_detail` passed 3 / 3 cases in 141.257 seconds.

```bash
docker compose exec -T backend bench --site erpai_prj1 execute ai_assistant_ui.qwen_chat.service.run_bounded_release_gate_phase1_order_followup
```

Result: `phase1_order_followup` passed 3 / 3 cases in 145.729 seconds.

```bash
docker compose exec -T backend bench --site erpai_prj1 execute ai_assistant_ui.qwen_chat.service.run_bounded_release_gate_phase1_customer_credit
```

Result: `phase1_customer_credit` passed 4 / 4 cases in 187.907 seconds.

Important retained behaviors:

1. Customer-credit scope reset remains green with `scope_status=fresh_query_breakout` and `followup_mode=new_query`.
2. Customer-credit policy follow-up remains green with direct evidence answers where the current artifact supports the answer.
3. All segmented profiles use signal-based timeout enforcement.

### 24.3 Current Gate Status

Phase 1 is now healthier as an operational release gate.

Current status:

1. Fast stabilization gate: green.
2. Release sanity gate: green.
3. Phase 1 document-detail segment: green.
4. Phase 1 order-follow-up segment: green.
5. Phase 1 customer-credit segment: green.
6. Enterprise guardrail: green.

Normal pre-UAT gate should use the segmented Phase 1 profiles. The full `phase1_core` profile should be retained for explicit long-budget verification, not as the default human-in-the-loop stabilization command.

Next recommended stabilization action:

1. Apply the same bounded-profile discipline to the post-contract suites.
2. Re-run the post-contract suites in smaller profiles.
3. Start manual browser UAT only after the automated stabilization gates remain green.

## 25. Stabilization Progress: Atomic Phase 6 Post-Contract Gate

### 25.1 Finding: Phase 6 Aggregate Suite Was Still Too Opaque

The first segmented post-contract run exposed a harness weakness in `post_contract_phase6`.

The profile originally executed `phase6_hardening_suite` as one aggregate case. That aggregate internally runs ten different reasoning and boundary checks. When the command ran too long, the release gate could not immediately identify which sub-check was slow or failing.

This was not treated as a product feature failure or a single prompt failure. It was treated as a release-gate architecture issue.

Resolution:

1. Converted `post_contract_phase6` into an atomic operational profile.
2. Kept the historical aggregate as `post_contract_phase6_aggregate` for explicit long-budget comparison only.
3. Added one-case profiles for each Phase 6 sub-check so operators can run the exact failing seam directly.
4. Added service wrappers for repeatable Frappe execution without brittle shell `--kwargs` quoting.
5. Added unit coverage proving `post_contract_phase6` uses the expected atomic case order and no longer hides `phase6_hardening_suite`.

Atomic Phase 6 cases:

1. `phase6_recommendation_policy_probe`
2. `phase6_reasoning_live_rollout`
3. `phase6_reasoning_without_grounding`
4. `phase6_reasoning_frontdoor_boundary`
5. `phase6_nonadvisory_recommendation_boundary`
6. `phase6_artifact_refinement_precedence`
7. `phase6_continuation_fulfillment`
8. `phase6_grounded_source_reset`
9. `phase6_continuation_guardrail`
10. `phase6_observability`

### 25.2 Verification

Static and unit verification:

```bash
python3 -m py_compile \
  ai_assistant_ui/qwen_chat/evaluation/bounded_release_gate.py \
  ai_assistant_ui/qwen_chat/service.py \
  ai_assistant_ui/tests/test_bounded_release_gate.py
```

Result: compile passed.

```bash
QWEN_ENTERPRISE_METADATA_DIR=/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata \
python3 -m unittest ai_assistant_ui.tests.test_bounded_release_gate
```

Result: 9 tests passed.

```bash
python3 scripts/check_qwen_enterprise_guardrails.py
```

Result: Qwen enterprise guardrail audit passed.

Live inventory:

```bash
docker compose exec -T backend bench --site erpai_prj1 execute ai_assistant_ui.qwen_chat.service.run_bounded_release_gate_inventory
```

Result: `post_contract_phase6` is registered as ten atomic cases; `post_contract_phase6_aggregate` remains available as the long-budget aggregate.

Live atomic Phase 6 gate results:

| Profile | Result | Duration |
| --- | --- | --- |
| `post_contract_phase6_recommendation_policy` | Passed 1 / 1 | 0.005s |
| `post_contract_phase6_reasoning_live_rollout` | Passed 1 / 1 | 52.283s |
| `post_contract_phase6_reasoning_without_grounding` | Passed 1 / 1 | 10.772s |
| `post_contract_phase6_reasoning_frontdoor_boundary` | Passed 1 / 1 | 32.986s |
| `post_contract_phase6_nonadvisory_recommendation_boundary` | Passed 1 / 1 | 36.139s |
| `post_contract_phase6_artifact_refinement_precedence` | Passed 1 / 1 | 37.289s |
| `post_contract_phase6_continuation_fulfillment` | Passed 1 / 1 | 62.904s |
| `post_contract_phase6_grounded_source_reset` | Passed 1 / 1 | 69.046s |
| `post_contract_phase6_continuation_guardrail` | Passed 1 / 1 | 0.000s |
| `post_contract_phase6_observability` | Passed 1 / 1 | 42.911s |

### 25.3 Current Gate Status

Phase 6 is now green when tested through atomic bounded gates.

Important interpretation:

1. The old aggregate command should not be used as the default human-in-the-loop stabilization gate.
2. The atomic Phase 6 profiles are the operational source of truth for release triage.
3. If Phase 6 regresses again, the team can identify the failing seam directly instead of waiting on a long black-box suite.

Current status:

1. Fast stabilization gate: green.
2. Release sanity gate: green.
3. Phase 1 segmented gates: green.
4. Post-contract Phase 5.5 segment: green.
5. Post-contract Phase 6 atomic gates: green.
6. Enterprise guardrail: green.

Next recommended stabilization action:

1. Run or atomize post-contract Phase 7 and Phase 8 using the same bounded discipline.
2. Re-run the fast gate after any new fix.
3. Start manual browser UAT only after Phase 7 and Phase 8 are also verified.

## 26. Stabilization Progress: Atomic Phase 7 And Phase 8 Post-Contract Gates

### 26.1 Naming Clarification

The terms `Phase 7` and `Phase 8` in this section refer to historical post-contract hardening suites already present in the codebase.

They are not the NBU mini-phases:

1. Historical post-contract Phase 7: knowledge-boundary orchestration and boundary response checks.
2. Historical post-contract Phase 8: recovery authority, repair handling, fresh-query override, and recovery execution checks.
3. `NBU-S7`: the future NBU Regression Matrix phase.
4. `NBU-S8`: the future Manual Browser UAT gate.

Current roadmap position remains NBU Stabilization Freeze. The team has not moved to Phase 4 complex business questions yet.

### 26.2 Finding: Phase 7 And Phase 8 Needed The Same Atomic Gate Discipline

After Phase 6 was atomized, Phase 7 and Phase 8 still had the same structural risk: each post-contract profile could hide multiple checks inside a historical aggregate suite.

Resolution:

1. Converted `post_contract_phase7` into atomic operational cases.
2. Converted `post_contract_phase8` into atomic operational cases.
3. Kept historical aggregate profiles available as:
   - `post_contract_phase7_aggregate`
   - `post_contract_phase8_aggregate`
4. Added one-case Frappe wrappers for repeatable operator execution.
5. Added unit coverage proving Phase 7 and Phase 8 operational profiles no longer hide aggregate suite cases.

Atomic Phase 7 cases:

1. `phase7_live_boundary_orchestration`
2. `phase7_boundary_response_live`

Atomic Phase 8 cases:

1. `phase8_recovery_authority`
2. `phase8_repair_handling`
3. `phase8_fresh_query_override`
4. `phase8_recovery_execution`

### 26.3 Verification

Static and unit verification:

```bash
python3 -m py_compile \
  ai_assistant_ui/qwen_chat/evaluation/bounded_release_gate.py \
  ai_assistant_ui/qwen_chat/service.py \
  ai_assistant_ui/tests/test_bounded_release_gate.py
```

Result: compile passed.

```bash
QWEN_ENTERPRISE_METADATA_DIR=/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata \
python3 -m unittest ai_assistant_ui.tests.test_bounded_release_gate
```

Result: 11 tests passed.

```bash
python3 scripts/check_qwen_enterprise_guardrails.py
```

Result: Qwen enterprise guardrail audit passed.

Live inventory:

```bash
docker compose exec -T backend bench --site erpai_prj1 execute ai_assistant_ui.qwen_chat.service.run_bounded_release_gate_inventory
```

Result: Phase 7 and Phase 8 atomic profiles registered; aggregate profiles retained separately.

Live atomic Phase 7 gate results:

| Profile | Result | Duration |
| --- | --- | --- |
| `post_contract_phase7_live_boundary_orchestration` | Passed 1 / 1 | 64.877s |
| `post_contract_phase7_boundary_response_live` | Passed 1 / 1 | 40.558s |

Live atomic Phase 8 gate results:

| Profile | Result | Duration |
| --- | --- | --- |
| `post_contract_phase8_recovery_authority` | Passed 1 / 1 | 1.016s |
| `post_contract_phase8_repair_handling` | Passed 1 / 1 | 33.969s |
| `post_contract_phase8_fresh_query_override` | Passed 1 / 1 | 37.315s |
| `post_contract_phase8_recovery_execution` | Passed 1 / 1 | 17.270s |

### 26.4 Current Gate Status

The automated stabilization gate is now materially healthier.

Current status:

1. Fast stabilization gate: green.
2. Release sanity gate: green.
3. Phase 1 segmented gates: green.
4. Post-contract Phase 5.5 segment: green.
5. Post-contract Phase 6 atomic gates: green.
6. Post-contract Phase 7 atomic gates: green.
7. Post-contract Phase 8 atomic gates: green.
8. Enterprise guardrail: green.

Important interpretation:

1. The release gate now identifies failures by seam instead of hiding them inside long aggregate commands.
2. Aggregate profiles remain available for explicit long-budget comparison only.
3. Normal stabilization and pre-UAT checks should use the atomic/segmented profiles.

Next recommended stabilization action:

1. Run a final lightweight automated readiness sweep.
2. Prepare `NBU-S7` Regression Matrix coverage from the now-stable automated gate results.
3. Only after `NBU-S7` is green, begin `NBU-S8` Manual Browser UAT.

## 27. Stabilization Progress: Final Lightweight Readiness Sweep

### 27.1 Purpose

This sweep verifies that the stabilization gate remains healthy after atomizing historical post-contract Phase 6, Phase 7, and Phase 8 profiles.

This is still part of NBU Stabilization Freeze. It is not Phase 4 feature expansion.

### 27.2 Verification Results

Static and unit verification:

```bash
python3 -m py_compile \
  ai_assistant_ui/qwen_chat/evaluation/bounded_release_gate.py \
  ai_assistant_ui/qwen_chat/service.py \
  ai_assistant_ui/tests/test_bounded_release_gate.py
```

Result: compile passed.

```bash
QWEN_ENTERPRISE_METADATA_DIR=/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata \
python3 -m unittest ai_assistant_ui.tests.test_bounded_release_gate
```

Result: 11 tests passed.

```bash
python3 scripts/check_qwen_enterprise_guardrails.py
```

Result: Qwen enterprise guardrail audit passed.

Live inventory:

```bash
docker compose exec -T backend bench --site erpai_prj1 execute ai_assistant_ui.qwen_chat.service.run_bounded_release_gate_inventory
```

Result: all segmented and atomic profiles are registered; timeout enforcement is `signal`.

Live readiness profiles:

```bash
docker compose exec -T backend bench --site erpai_prj1 execute ai_assistant_ui.qwen_chat.service.run_bounded_release_gate
```

Result: `stabilization_fast` passed 5 / 5 cases in 324.923 seconds.

```bash
docker compose exec -T backend bench --site erpai_prj1 execute ai_assistant_ui.qwen_chat.service.run_bounded_release_gate_release_sanity
```

Result: `release_sanity` passed 6 / 6 cases in 197.442 seconds.

### 27.3 Current Gate Status

Final lightweight readiness sweep is green.

Current status:

1. Compile: green.
2. Bounded release-gate unit tests: green.
3. Enterprise guardrail: green.
4. Live bounded-gate inventory: green.
5. `stabilization_fast`: green.
6. `release_sanity`: green.
7. Historical post-contract Phase 5.5 / 6 / 7 / 8 gates: atomized or segmented and verified.

### 27.4 Next Roadmap Step

The next step is `NBU-S7` Regression Matrix.

`NBU-S7` should not add new business capability. It should convert the stabilized behavior into a systematic regression matrix that covers:

1. Fresh-query routing.
2. Visible-context row and rank follow-ups.
3. Projection/refinement requests such as units, quantity, million-format, and row limits.
4. Entity-detail expansion from ranked rows.
5. Recovery and clarification behavior.
6. Unsupported prediction, guarantee, and policy boundaries.
7. Cross-family context reset so stale AR/AP/customer/supplier/product/document context does not leak.

Exit gate for `NBU-S7`:

1. Matrix cases are documented.
2. Automated replay/smoke coverage exists for the critical cases.
3. Guardrails remain green.
4. No user-facing internal terms leak in fallback or clarification responses.
5. The team agrees the matrix is good enough to proceed to `NBU-S8` Manual Browser UAT.

## 28. Stabilization Progress: NBU-S7 Regression Matrix Closure - 2026-05-03

### 28.1 Purpose

This section records the closure of `NBU-S7` after the shared NBU stabilization work was converted into segmented automated regression gates.

This is still part of the stabilization freeze. It is not Phase 4 complex business-question expansion.

### 28.2 What Changed

The S7 closure hardened shared seams rather than single browser prompts:

1. Latest visible result selection now prevents stale customer, supplier, product, and document context from owning unrelated follow-ups.
2. Fresh self-contained ranking questions now break out of prior table context.
3. Projection follow-ups preserve the original ranking metric and add or format requested columns without changing the ranking basis.
4. Broad detail requests route to approved entity detail where available.
5. Prediction, recommendation, and unsupported decision requests stop safely with business-facing language.
6. Shared response renderers were cleaned so user-facing answers avoid internal architecture wording such as runtime, contract, artifact, governed boundary, and governed support.

### 28.3 Verification

Static and unit verification:

```text
python3 -m unittest \
  ai_assistant_ui.tests.test_composite_evidence_support \
  ai_assistant_ui.tests.test_financial_statement_followup_clarification_contracts \
  ai_assistant_ui.tests.test_bounded_release_gate
```

Result:

```text
Ran 51 tests in 0.168s
OK
```

Enterprise guardrail:

```text
python3 scripts/check_qwen_enterprise_guardrails.py
```

Result:

```text
Qwen enterprise guardrail audit: PASS
```

Live backend S7 segmented profiles:

| Profile | Result | Duration |
| --- | --- | --- |
| `nbu_s7_context_matrix` | Passed 3 / 3 | 218.790s |
| `nbu_s7_projection_matrix` | Passed 3 / 3 | 93.581s |
| `nbu_s7_boundary_recovery_matrix` | Passed 4 / 4 | 167.352s |

### 28.4 Current Gate Status

`NBU-S7` automated regression matrix is green.

Current status:

1. Guardrail audit: green.
2. Targeted unit tests: green.
3. Context matrix: green.
4. Projection matrix: green.
5. Boundary/recovery matrix: green.
6. Manual browser UAT: not yet started.
7. Phase 4: still blocked until NBU-S8 passes.

### 28.5 Remaining Risks

The project is healthier, but not finished:

1. Browser UAT can still reveal frontend/session behavior that automated server replay does not fully represent.
2. Broad aggregate release profiles are slower than future enterprise targets; this is a performance-hardening backlog, not a current correctness blocker.
3. `service.py` and duplicate lane ownership remain structural risks for NBU-S9.
4. New families such as HR or CRM must be onboarded through NBU metadata and contracts, not phrase patches.

### 28.6 Next Step

Move to `NBU-S8` Manual Browser UAT.

Manual UAT must run one group at a time. If a browser result fails, classify it as one of:

1. Latest-visible-result selection.
2. Fresh-query breakout.
3. Projection or presentation transform.
4. Entity or document detail enrichment.
5. Clarification or executable-options quality.
6. Unsupported prediction, recommendation, or policy boundary.
7. Unsupported capability or future-family gap.

Fixes must improve the shared path for that class of failure. Do not fix only the single wording that failed in the browser.
