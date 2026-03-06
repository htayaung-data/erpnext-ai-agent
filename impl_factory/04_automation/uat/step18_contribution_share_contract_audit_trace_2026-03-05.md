# Contribution Share Contract Audit Trace

Date: 2026-03-05  
Owner: AI Runtime Engineering  
Scope: strict contract audit of contribution-share-era runtime changes (with current mixed worktree context)

## Governing References

1. `step13_behavioral_class_development_contract.md`
2. `step14_phase3_regression_discipline_contract.md`
3. `step16_phase3_baseline_freeze_2026-03-04.md`
4. `step17_contribution_share_approval_review_2026-03-04.md`
5. `step18_contribution_share_implementation_plan_2026-03-04.md`

## Audit Method

1. Enumerated changed runtime files under `ai_core` and `ai_core/v7`.
2. Reviewed each changed hunk against Step18 implementation steps.
3. Checked non-negotiable boundaries:
   - no prompt-to-report maps
   - no case-ID hacks
   - no keyword-driven business routing in runtime modules
   - no hidden behavior overrides outside contract/ontology/metadata/state

## Approval-To-Runtime Trace

### Step18 Step 1-2: Ontology + Capability Metadata

Status: `compliant`

Runtime/data surfaces:

1. `ai_core/ontology_normalization.py`
2. `ai_core/v7/contracts_data/ontology_base_v1.json`
3. `ai_core/v7/contracts_data/capability_registry_overrides_v1.json`

Assessment:

1. contribution/threshold semantics are represented in governed ontology/metadata surfaces.
2. no case-ID or prompt-ID logic found in these files.

### Step18 Step 3: Class Contract Representation

Status: `compliant`

Runtime/data surfaces:

1. `ai_core/v7/contracts_data/spec_contract_v1.json`
2. `ai_core/v7/contracts_data/clarification_contract_v1.json`
3. `ai_core/v7/contract_registry.py`
4. `ai_core/v7/spec_schema.py`

Assessment:

1. class identity and clarification kinds are represented as contract data.
2. clarification copy is centralized, not tied to replay case IDs.

### Step18 Step 4: Resolver Support

Status: `mostly_compliant`

Runtime surfaces:

1. `ai_core/v7/constraint_engine.py`
2. `ai_core/v7/semantic_resolver.py`
3. `ai_core/v7/entity_resolution.py`

Assessment:

1. resolver changes are predominantly metadata/contract driven.
2. `extract_entity_filters_from_message` in `entity_resolution.py` uses alias matching from candidate lists; this is deterministic entity extraction, not prompt-to-report routing.

### Step18 Step 5: Deterministic Contribution/Threshold Execution

Status: `compliant`

Runtime surfaces:

1. `ai_core/v7/contribution_share_policy.py`
2. `ai_core/v7/threshold_exception_policy.py`
3. `ai_core/v7/read_engine.py` integration points

Assessment:

1. execution is table/column-contract based and deterministic.
2. derived share/threshold behavior is computed from payload rows, not hardcoded to specific prompt text.

### Step18 Step 6-7: Follow-up + Quality

Status: `mostly_compliant`

Runtime surfaces:

1. `ai_core/v7/memory.py`
2. `ai_core/v7/shaping_policy.py`
3. `ai_core/v7/quality_gate.py`
4. `ai_core/v7/transform_followup_policy.py`
5. `ai_core/v7/resume_policy.py`

Assessment:

1. follow-up and quality checks are mostly structural and class-based.
2. resume follow-up gating is now task-class based in planner clarification resume path.

## Contract-Risk Findings

### CR-1 (Medium): Keyword-heavy class/unsupported gating in `spec_pipeline.py`

Location family:

1. `_extract_threshold_signal`
2. `_threshold_unsupported_reason`
3. `_extract_contribution_signal`
4. `_contribution_unsupported_reason`

Evidence examples:

1. token checks for `"grouped by"`, `"territory"`, `"compare"`, `"vs"`, `"pareto"`, `"running share"`.
2. direct lexical fallbacks like `"stock balance"` and `"invoice"`-based metric coercion.

Why this is risk:

1. these are runtime keyword gates for business behavior in a module explicitly listed as high-risk for this anti-pattern by contract.
2. behavior becomes fragile as class breadth grows.

### CR-2 (Closed): Resume fallback lexical gate removed

Location:

1. `resume_policy.py` planner-clarify record-type gate

Resolution:

1. removed the lexical `invoice` fallback.
2. gate now relies on structured `task_class == list_latest_records`.

## Explicit Non-Findings

1. no replay case-ID routing found in runtime modules.
2. no prompt-to-report mapping table found in runtime modules.
3. no tenant-ID or customer-ID hardcoded path found in runtime modules.

## Required Remediation Order

1. Refactor contribution/threshold unsupported detection in `spec_pipeline.py` into ontology/contract-backed inference utilities.
2. Keep unsupported reason codes and user-safe error envelopes in `read_engine.py`, but only consume structured reason outputs from step 1.
3. Add regression guard tests that fail if business-class selection depends on ad-hoc message-token checks in `spec_pipeline.py`.

## Current Gate Decision

Decision: `provisionally_in_contract_with_open_contract_debt`

Reason:

1. deterministic behavior and replay outcomes are strong.
2. contract debt remains in parser-level keyword gating in `spec_pipeline.py`.
3. this should be treated as required hardening before calling this enterprise-clean long-term architecture.
