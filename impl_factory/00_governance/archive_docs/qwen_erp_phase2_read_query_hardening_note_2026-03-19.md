# Qwen ERP Phase 2 Read Query Hardening Note (2026-03-19)

Status: completed with known gaps  
Scope: enterprise Phase 2 from the Qwen ERP blueprint  
Phase goal: tighten the Qwen read-query path so approved reports, validation, and audit are governed explicitly instead of relying only on model behavior.

Note:
The initial Phase 2 implementation used a runtime-local registry.
That governance location was later normalized into the shared enterprise metadata foundation described in:

- `/home/deploy/erp-projects/erpai_project1/impl_factory/00_governance/qwen_erp_enterprise_metadata_foundation_note_2026-03-19.md`

## Objective

Phase 2 was defined as the first read-path hardening layer:

1. capability/report registry tightening
2. tool gateway policy refinement
3. stronger grounded validation
4. richer audit envelope

The goal was not to widen feature scope.  
The goal was to reduce implicit runtime behavior and replace it with explicit policy and audit structure.

## What Was Implemented

### 1. Governed report registry

Implemented in:

- `/home/deploy/erp-projects/erpai_project1/experimental/qwen_agent_runtime/app/report_registry.json`
- `/home/deploy/erp-projects/erpai_project1/experimental/qwen_agent_runtime/app/report_registry.py`

This registry now defines the first approved report set for the Qwen runtime, including:

- `Sales Analytics`
- `Stock Balance`
- `Warehouse Wise Stock Balance`
- `Accounts Payable Summary`
- `Accounts Payable`
- `Accounts Receivable`
- `Accounts Receivable Summary`

Each approved report now carries governed metadata such as:

- module
- report family
- required filters
- allowed follow-up modes
- chartable fields

This is intentionally a narrow first registry, not a universal catalog.

### 2. Tool gateway policy

Implemented in:

- `/home/deploy/erp-projects/erpai_project1/experimental/qwen_agent_runtime/app/tool_gateway_policy.py`
- `/home/deploy/erp-projects/erpai_project1/experimental/qwen_agent_runtime/app/qwen_agent_engine.py`

The runtime now enforces policy for key FAC report tools:

- `erp_fac-report_list`
- `erp_fac-report_requirements`
- `erp_fac-generate_report`

Policy behavior now includes:

- module restriction for `report_list`
- approved-report enforcement for `report_requirements`
- approved-report enforcement for `generate_report`
- required-filter validation for `generate_report`
- deterministic default-company injection when needed

This phase keeps the policy focused on read-report safety only.

### 3. Stronger grounded validation

Implemented in:

- `/home/deploy/erp-projects/erpai_project1/experimental/qwen_agent_runtime/app/validation.py`
- `/home/deploy/erp-projects/erpai_project1/experimental/qwen_agent_runtime/app/service.py`

The runtime now performs explicit grounded read validation before returning a final answer.

Validation currently checks:

- at least one successful grounding tool call exists for factual read answers
- report-based tool usage references only approved reports
- report-based tool usage satisfies required filters

Validation now returns structured metadata inside `agent_meta.validation`, including:

- status
- errors
- grounding tools used
- approved reports used

### 4. Richer audit envelope

Implemented in:

- `/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/contracts.py`
- `/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py`

Each Qwen turn now records a hidden `qwen_audit_envelope` with:

- request id
- session id
- follow-up mode
- execution path
- grounded status
- source kind
- source name
- runtime engine
- runtime model
- runtime latency
- tool count
- tool names
- validation status
- validation errors
- answer length

This is the first compact per-turn operational audit summary for the Qwen path.

## What Was Fixed During Phase 2

One important read-path issue was discovered and corrected during the phase:

1. `stock by warehouse` initially failed Phase 2 validation because the actual report used by the agent was `Warehouse Wise Stock Balance`, which was not yet explicitly approved in the registry

That report was then added to the governed registry rather than bypassing validation.

This is the intended behavior of the phase:

1. surface ungoverned capability usage
2. approve it explicitly if valid
3. keep policy and execution aligned

## Verification Performed

Technical verification completed:

1. Python compile checks passed for:
   - ERP-side Qwen chat modules
   - runtime-side app modules
2. Runtime rebuilt successfully
3. Backend and websocket restarted successfully
4. Runtime health check succeeded
5. Fresh session verification confirmed:
   - approved report registry enforcement is active
   - validation metadata is returned inside runtime responses
   - `qwen_audit_envelope` is persisted in session history

Verified examples:

1. `show sales last month`
   - passed validation with approved report `Sales Analytics`
2. `How much we need to pay as Payable as of now?`
   - passed validation with approved report `Accounts Payable Summary`
3. `stock by warehouse`
   - initially failed due to missing registry approval
   - passed after explicit registry update for `Warehouse Wise Stock Balance`

## What Phase 2 Does Not Yet Do

This phase intentionally does not yet provide:

1. full capability-family ontology beyond the first approved reports
2. typed artifact generation contracts
3. write proposal and confirmation safety
4. Burmese language/locale behavior
5. broader follow-up taxonomy beyond the Phase 1 baseline
6. least-privilege service-user credential replacement

## Manual Browser Sign-Off

Manual browser sign-off is useful, but not the primary closure criterion for this phase.

Reason:

1. Phase 2 is mainly runtime policy, validation, and audit hardening
2. the primary evidence is structured technical verification
3. UI behavior should still be checked, but it is not the main measure of Phase 2 completion

Recommended user check after this phase:

1. run 2-3 approved read queries in the browser
2. confirm visible answers still look correct
3. confirm no obvious regression in normal chat behavior

## Exit Decision

Phase 2 is considered:

`completed with known gaps`

Why not plain `completed`:

1. report governance and validation are now present and active
2. but the approved capability registry is still intentionally small
3. later phases are still needed before enterprise release claims are justified

## Next Phase

Phase 3: Follow-Up System

Planned focus:

1. typed follow-up classes beyond the current minimal set
2. local projection and local sort/limit paths
3. filter refinement and sibling-switch resolution from structured context
4. reduced reliance on raw model follow-up reasoning
