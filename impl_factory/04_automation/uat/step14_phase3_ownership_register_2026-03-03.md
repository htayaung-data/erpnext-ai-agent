# Phase 3 Ownership Register

Date: 2026-03-03  
Owner: AI Runtime Engineering  
Scope: initial ownership register for current Tier 1 and Tier 2 quality assets  
Status: active Phase 3 baseline ownership register

## Purpose
This document assigns default ownership for the current important quality assets.

The purpose is not bureaucracy. The purpose is:

1. every critical asset has a clear owner
2. incidents know which evidence assets they belong to
3. no important suite or browser pack is “everyone’s job” and therefore nobody’s job

Until broader product/QA/operations roles are formalized, ownership remains with AI Runtime Engineering.

## Owner Definitions

### Primary Owner
The team or function responsible for:

1. keeping the asset current
2. deciding whether reruns are required
3. attaching evidence for change closure

### Supporting Owner
The team or function that may help validate, review, or execute the asset when broader operating roles are formalized.

## Current Ownership Table

| Asset | Type | Tier | Primary Owner | Supporting Owner | Notes |
|---|---|---|---|---|---|
| `core_read` | Replay suite | Tier 1 | AI Runtime Engineering | Pending formal QA owner | Core analytical read protection |
| `multiturn_context` | Replay suite | Tier 1 | AI Runtime Engineering | Pending formal QA owner | State, correction, latest-record protection |
| `write_safety` | Replay suite | Tier 1 | AI Runtime Engineering | Pending formal QA owner | Safety-critical write behavior |
| `no_data_unsupported` | Replay suite | Tier 1 | AI Runtime Engineering | Pending formal QA owner | Safe error/no-data envelope |
| `transform_followup` | Replay suite | Tier 2 | AI Runtime Engineering | Pending formal QA owner | Transform-last behavior |
| Standing browser smoke pack | Browser/manual pack | Tier 1 | AI Runtime Engineering | Pending Product QA owner | Shared-runtime browser parity |
| Customer ranking + scale | Browser/manual pack | Tier 1 | AI Runtime Engineering | Pending Product QA owner | Finance/sales ranking parity |
| Supplier ranking + scale | Browser/manual pack | Tier 1 | AI Runtime Engineering | Pending Product QA owner | Supplier ranking parity |
| Product ranking + projection | Browser/manual pack | Tier 2 | AI Runtime Engineering | Pending Product QA owner | Projection behavior protection |
| Warehouse correction + scale | Browser/manual pack | Tier 1 | AI Runtime Engineering | Pending Product QA owner | Correction authority protection |
| Latest-record clarification | Browser/manual pack | Tier 1 | AI Runtime Engineering | Pending Product QA owner | Latest-record resume protection |
| Finance parity smoke | Browser/manual pack | Tier 1 | AI Runtime Engineering | Pending Product QA owner | Receivable/payable parity |
| Write confirm/cancel smoke | Browser/manual pack | Tier 1 | AI Runtime Engineering | Pending Product QA owner | Browser-visible write safety |
| `test_v7_read_engine_clarification.py` | Module regression | Tier 1 | AI Runtime Engineering | None | Resume/latest-record/correction contract |
| `test_v7_memory_context.py` | Module regression | Tier 1 | AI Runtime Engineering | None | Topic state and follow-up control |
| `test_v7_spec_pipeline.py` | Module regression | Tier 1 | AI Runtime Engineering | None | Spec generation and latest-record pinning |
| `test_v7_semantic_resolver_constraints.py` | Module regression | Tier 1 | AI Runtime Engineering | None | Deterministic resolver semantics |
| `test_v7_response_shaper.py` | Module regression | Tier 2 | AI Runtime Engineering | None | Projection and shaping correctness |
| `test_v7_transform_last.py` | Module regression | Tier 2 | AI Runtime Engineering | None | Transform-last behavior |
| `test_v7_read_execution_runner.py` | Module regression | Tier 2 | AI Runtime Engineering | None | Bounded execution loop behavior |

## Ownership Rules

1. The primary owner must decide rerun obligations when a shared-runtime change touches the asset.
2. A Tier 1 asset cannot be treated as optional evidence.
3. When an incident is opened, it must link to at least one owned asset from this register.
4. When broader organizational roles are created in later phases, this register must be updated rather than assumed.

## Immediate Use
Until later phases formalize broader operations:

1. AI Runtime Engineering owns the evidence pack
2. browser/manual execution may still be performed by the product owner or engineer on duty
3. closure evidence must still be attached to the owned asset

## Next Update
Update this register when:

1. a new behavioral class becomes approved and gets new assets
2. a new browser/manual pack is formalized
3. Product QA or Operations ownership is formally introduced
