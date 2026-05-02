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
| NBU-S1 | Pending | Shared visible artifact intent contract |
| NBU-S3 | Pending | Latest relevant artifact selection |
| NBU-S2 | Pending | Shared projection contract |
| NBU-S4 | Pending | Entity detail enrichment contract |
| NBU-S5 | Pending | Professional clarification and fallback language |
| NBU-S6 | Pending | Enterprise guardrail closure |
| NBU-S7 | Pending | Regression matrix |
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

The enterprise guardrail audit remains red with the baseline findings recorded in Section 13. That is now the main stabilization blocker before Phase 4.
