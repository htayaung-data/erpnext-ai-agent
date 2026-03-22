# Qwen ERP Phase 4 Slice 6 Audit and Observability Note (2026-03-22)

Status: completed  
Scope: compiled first-turn audit contract and latency observability for Phase 4 governed execution

## Purpose

Slice 6 completes the non-live Phase 4 governance path by making the compiled first-turn pipeline auditable as a single governed unit.

Before this slice, we had:

- compiler contracts
- compiled runtime execution
- semantic validation

But we did not yet have one dedicated enterprise audit record that summarized:

- what the compiler decided
- what the runtime executed
- whether grounding passed
- whether semantic validation passed
- where the latency was spent

## What Was Implemented

### 1. Dedicated compiled execution audit contract

Added a new contract for the compiled first-turn pipeline:

- `CompiledExecutionAuditContract`

This contract records:

1. compiler decision
2. compiler reason
3. capability and selected report
4. whether a compiled request existed
5. whether runtime execution was invoked
6. runtime success status
7. grounded validation status
8. semantic validation status
9. semantic validation errors and warnings
10. tool count and tool names
11. latency breakdown

### 2. Latency breakdown across the whole compiled pipeline

The Phase 4 helper now captures:

1. proposal generation latency
2. compilation latency
3. runtime execution latency
4. semantic validation latency
5. total pipeline latency

### 3. Unified compiled execution helper output

The compiled first-turn helper now returns:

1. pipeline contracts
2. runtime payload
3. semantic validation payload
4. compiled execution audit payload
5. latency breakdown payload

This makes the compiled path observable before it is promoted into the live chat path.

## Why This Matters

This slice preserves the enterprise direction:

- `Qwen-Agent proposes`
- `compiler enforces`
- `validator confirms`
- `audit explains`

That last part matters operationally.

Without Slice 6, we could tell whether the compiled path worked.

With Slice 6, we can also tell:

- why it worked
- why it clarified
- why it rejected
- and where the time was spent

## Verification

### Deterministic selftest

Passed:

- compiled execution audit contract selftest

### Real compiled observability smoke

Passed:

- payable first-turn request
- accepted fresh-query interpretation
- compiler `execute`
- compiled runtime execution
- grounded validation `pass`
- semantic validation `pass`
- audit payload generated with stage latency breakdown

## Current Position After Slice 6

Phase 4 is now implemented through:

1. Slice 1 contract and metadata foundation
2. Slice 2 compiler core
3. Slice 3 model proposal integration
4. Slice 4 compiled execution
5. Slice 5 semantic validation
6. Slice 6 audit and observability

This means the remaining decision is no longer implementation completeness inside the Phase 4 helper path.

The remaining decision is rollout policy.

## Next Step

Choose one:

1. promote compiled first-turn execution directly into the live chat path
2. gate compiled first-turn execution behind a rollout flag

The safer enterprise option is usually:

- rollout flag first

because the compiled path is now governed enough to test incrementally without reopening architecture drift.

## Rollout Gate Update

A gated rollout path is now implemented in the ERP chat service.

Current rollout posture:

1. compiled first-turn execution is available behind:
   - `qwen_enable_compiled_first_turn`
   - optional `qwen_compiled_first_turn_rollout_percentage`
   - optional `qwen_compiled_first_turn_rollout_users`
2. the live default remains unchanged unless the master flag is enabled
3. when the master flag is enabled:
   - allowlisted users can be forced into the compiled path
   - all other sessions can be admitted by a deterministic canary percentage
   - the canary bucket is stable for the same site, user, and session
   - operational proposal failures can fall back to the legacy read path, but only with explicit persisted rollout-fallback audit
4. a live-service smoke confirmed that when rollout admits the session:
   - the compiled first-turn path is used
   - semantic validation must pass before grounded context is persisted
   - or, if proposal generation fails operationally, the live path can fall back explicitly and audibly instead of failing silently
    - the session records:
      - fresh-query interpretation
      - compiler contract
      - compiled query request
      - runtime trace
     - semantic validation
     - compiled execution audit
     - grounded turn context
     - audit envelope
5. a rollout governance helper is also available:
   - `get_compiled_first_turn_rollout_status`
6. a rollout governance selftest is available:
   - `run_phase4_compiled_rollout_governance_selftests`
7. a monitoring helper is also available for controlled rollout review:
   - `summarize_compiled_first_turn_audits`
8. a rollout-monitoring smoke is available to verify that the summary path observes real compiled audit traffic:
   - `run_phase4_compiled_rollout_monitoring_smoke`

## Monitoring Observation

The rollout-monitoring smoke now passes.

The first monitored compiled sample showed:

1. compiler decision:
   - `execute`
2. grounded validation:
   - `pass`
3. semantic validation:
   - `pass`
4. latency shape:
   - proposal generation dominated total latency
   - runtime execution was materially smaller than proposal generation

This means the rollout gate is working, but latency monitoring should focus first on:

1. proposal generation duration
2. total first-turn pipeline duration
3. semantic pass rate under live traffic

## Proposal Cache Update

A runtime-side cache now exists for governed fresh-query proposal generation.

Scope:

1. repeated first-turn requests with the same message and interpretation context
2. cache remains advisory only
3. compiler enforcement is unchanged

Observed result from the cache smoke:

1. cold proposal generation remained slow
2. immediate repeated proposal generation dropped to near-zero model latency
3. compiled audit monitoring now exposes:
   - `proposal_cache_hit`
   - `proposal_cache_hit_rate`
4. rollout monitoring now also exposes:
   - current rollout status
   - proposal shared-inflight hit state and rate
   - rollout fallback count and rate

This means rollout review can now distinguish:

1. cold-path proposal latency
2. warmed repeated-request latency
3. runtime execution latency after proposal latency is removed from the critical path
4. rollout admission policy from actual pipeline outcomes
5. explicit operational fallback behavior during canary rollout

## Cold-Path Tuning Lever

The runtime now also supports a dedicated semantic proposal model and token budget for the fresh-query interpreter.

Available levers:

1. `SEMANTIC_FRESH_QUERY_MODEL`
2. `SEMANTIC_FRESH_QUERY_MAX_TOKENS`

Enterprise rule:

1. use these to tune cold-path proposal latency
2. do not relax compiler enforcement or semantic validation just to reduce latency

## Single-Model Production Posture

The current production-oriented posture remains:

1. one hosted Qwen model for both:
   - semantic proposal generation
   - grounded runtime/tool use
2. keep `SEMANTIC_FRESH_QUERY_MODEL` unset by default
3. only enable a separate proposal model later if measured cold-path latency justifies the extra operational complexity
