# Qwen ERP Phase 4 Consultation Assessment Note (2026-03-22)

Status: accepted phase-level assessment  
Scope: governance interpretation of the Phase 4 Qwen review

## Purpose

This note records how the Phase 4 Qwen review changes the Fresh Query Compiler design before implementation starts.

## Accepted Decisions

### 1. Keep the compiler boundary

Accepted:

- first-turn requests should compile into governed execution requests
- `Qwen-Agent` proposes
- compiler enforces

### 2. Avoid separate interpretation and compilation service tiers

Accepted:

- do not design Phase 4 as:
  - ERP -> interpretation service -> compiler service -> runtime execution
- interpretation should be a compiler sub-step, not a separately exposed microservice boundary

### 3. Use closed-set intent classes

Accepted:

- `intent_class` must be a governed enum
- do not allow free-text intent labels to become execution keys

### 4. Allow model-ranked candidate reports only as advisory inputs

Accepted:

- the model may suggest 1-3 candidate reports
- the compiler still selects the final report

### 5. Keep semantic validation deterministic by default

Accepted:

- validation should first use:
  - schema checks
  - field presence checks
  - semantic tag checks
  - time-scope checks
- slower review logic should be optional, not default

## Partially Accepted Decisions

### 1. Compiler co-location

Accepted direction:

- compiler should be co-located with the orchestration boundary
- extra network hops should be avoided

Open implementation decision:

- whether the best enterprise location is:
  - Frappe backend
  - same runtime container
  - another tightly co-located boundary

This remains open for final implementation design, but it should not become a separate remote service tier.

## Phase 4 Design Corrections

The Phase 4 plan is now corrected to include:

1. `CompiledQueryRequestContract`
2. closed-set `intent_class`
3. `candidate_reports` as advisory-only
4. `ambiguity_reason` for clarify paths
5. compiler topology with no separate interpretation service
6. revised implementation order:
   - metadata foundation
   - compiler core
   - model proposal integration
   - compiled execution path
   - semantic validation
   - audit

## Governing Rule

The Phase 4 rule going into implementation is:

- keep semantics flexible
- keep execution deterministic
- keep topology simple

This prevents enterprise reliability from being traded away for convenience or latency hacks.
