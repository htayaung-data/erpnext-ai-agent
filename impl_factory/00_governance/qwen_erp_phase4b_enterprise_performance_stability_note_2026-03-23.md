# Qwen ERP Phase 4B Enterprise Performance And Stability Note (2026-03-23)

## 1. Purpose

This note records the enterprise hardening checkpoint after the Phase 4B semantic family layer implementation.

The target for this checkpoint was:

1. enterprise-grade performance across all currently governed families
2. enterprise-grade stability across all currently governed families
3. no relaxation of compiler or validator governance to achieve that result

## 2. What Changed

The main hardening change was to move compiled governed report execution onto a deterministic backend executor instead of routing every exact compiled read through the runtime model path.

Implemented boundary:

1. compiler still selects the exact governed report and completed filters
2. backend executes that exact governed report deterministically
3. family adapters normalize the result into canonical family artifacts
4. family and semantic validators still gate the response
5. canonical rendering still produces the final answer

This preserved the governing rule:

- `Qwen-Agent proposes`
- `compiler enforces`
- `validator confirms`

## 3. Key Hardening Details

### 3.1 Deterministic Governed Executor

Compiled single-family reads now prefer deterministic governed report execution in ERP backend code instead of model-mediated runtime execution.

This reduced:

1. model latency on exact compiled reads
2. runtime drift risk on compiled answers
3. unnecessary tool orchestration for already-governed report selections

### 3.2 Composite Execution Remains Governed

Composite governed reads now use the same deterministic executor for child steps.

Important runtime note:

- composite child steps remain serialized in the current safe path when direct execution is preferred
- this is intentional because Frappe runtime configuration is thread-local in worker child threads

Even with serialized execution, composite latency is now within enterprise targets for the current governed composite profile.

### 3.3 Direct Execution Retry Hardening

The deterministic executor now retries once on:

1. transient execution failure
2. transient zero-row direct result

This was added because the `Gross Profit`-based product-profitability path showed intermittent direct-execution instability under full evaluation runs.

The retry is deterministic and does not widen model freedom.

## 4. Verification Result

Full governed suite result after hardening:

1. `17/17` cases passing
2. `0` failed cases
3. `7/7` governed families marked `enterprise_green`
4. `development_green_rate = 1.0`
5. `enterprise_green_rate = 1.0`

Current governed family scope verified green:

1. `financial_statement`
2. `aging`
3. `ranking_analytics`
4. `trend_analytics`
5. `inventory_snapshot`
6. `product_profitability`
7. `working_capital_health`

## 5. Performance Posture

The biggest enterprise conclusion from this checkpoint is:

- the earlier pathological runtime bottleneck is no longer the controlling factor for the current governed family scope

Observed full-suite posture:

1. average total pipeline latency is now around `1.9s`
2. full-suite p95 total pipeline latency is about `3.3s`
3. the slowest observed full-suite case remained under the current family enterprise target
4. latency-focus family suite remained fully green after hardening

Important nuance:

- some proposal-generation stage budgets can still spike above family-specific development sub-budgets
- but end-to-end enterprise targets for the currently governed family set are now satisfied

So the current posture is:

1. enterprise-green end-to-end for current governed family scope
2. still worth continuing proposal-stage optimization later
3. no need to reopen compiler/family architecture to achieve current enterprise-read goals

## 6. Enterprise Assessment

For the currently governed family scope, Phase 4B now meets the intended enterprise bar on:

1. correctness
2. determinism
3. auditability
4. latency
5. stability

This does **not** mean the whole ERP assistant is complete.

It means:

1. the current governed read-family scope is enterprise-stable
2. the semantic family architecture has held up under hardening
3. the next work should be expansion and maintainability, not rescue redesign

## 7. Recommended Next Step

The next best step after this checkpoint is:

1. treat Phase 4B as closed for the current governed family scope
2. move into post-4B workstreams:
   - broader governed family expansion
   - larger family evaluation sets
   - maintainability refactor of oversized modules
   - multilingual and OCR-ready preparation layers later
3. keep compiler and validator boundaries unchanged while expanding breadth
