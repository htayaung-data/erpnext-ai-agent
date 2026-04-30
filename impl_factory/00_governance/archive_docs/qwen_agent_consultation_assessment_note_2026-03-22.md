# Qwen-Agent Consultation Assessment Note (2026-03-22)

Status: accepted architecture assessment  
Scope: governance interpretation of the Qwen-Agent consultation response

## Purpose

This note records which ideas from the Qwen-Agent consultation are being adopted into the enterprise architecture, which ideas are only partially adopted, and which ideas are intentionally deferred.

The purpose is to avoid design drift and to keep a clear boundary between:

- external architecture advice
- accepted enterprise design decisions
- deferred or rejected suggestions

## Consultation Outcome Summary

The consultation confirmed our current diagnosis in three critical areas:

1. we have invested more governance effort into follow-up interpretation than into fresh-query compilation
2. fresh first-turn business requests are now the larger reliability gap
3. grounded validation alone is not enough; semantic intent-to-result validation is required

The consultation also reinforced an important architectural rule:

- `Qwen-Agent proposes`
- `compiler enforces`

## Accepted Decisions

The following consultation ideas are accepted into the architecture.

### 1. Fresh-query compilation becomes the next primary reliability track

Accepted decision:

- `FreshQueryCompilerContract` is the next major implementation priority

Reason:

- first-turn requests are the main source of current reliability failures
- follow-up convenience improvements should not outrun first-turn correctness

### 2. Single-company handling becomes a compiler/policy invariant

Accepted decision:

- `company` is a governed invariant
- it should be injected centrally
- it should not remain a repeated user-visible failure burden

Reason:

- this ERP deployment will only ever hold one company
- treating company as a user/model burden causes unnecessary failure paths

### 3. Report selection must be compiler-governed

Accepted decision:

- Qwen-Agent may propose intent and slots
- compiler and registry layers must choose the report family / report id

Reason:

- model-selected reports drift under ambiguous business wording
- enterprise ERP reliability requires deterministic boundaries around report choice

### 4. Semantic intent-to-result validation is required

Accepted decision:

- grounded data is not sufficient by itself
- the system must also validate whether the grounded result matches the requested business intent

Reason:

- a grounded-but-wrong answer is still an enterprise failure

### 5. Response policy remains explicit and enforced

Accepted decision:

- keep the governed answer policy:
  - grounded facts first
  - supporting table or numeric breakdown next
  - concise business interpretation only when relevant and grounded
  - recommendations only on explicit request

Reason:

- this behavior is already proving valuable for business users and must remain architecture-owned

## Partially Accepted Decisions

The following consultation ideas are directionally correct, but are not being adopted literally at this moment.

### 1. Collapse the separate semantic interpretation step immediately

Partial decision:

- long-term consolidation is desirable
- immediate removal is not adopted yet

Reason:

- the current semantic follow-up layer is still providing useful governance and auditability
- removing it before the fresh-query compiler exists would increase risk

Current position:

- keep semantic interpretation bounded and explicit
- do not expand it aggressively
- revisit consolidation after Phase 4 compiler work

### 2. Replace confidence policy entirely with tool-choice confidence

Partial decision:

- the idea is useful conceptually
- but we are retaining an explicit semantic confidence policy for now

Reason:

- enterprise audit needs an explicit record of degraded interpretation and fallback decisions

## Deferred Decisions

The following consultation ideas are valid, but intentionally deferred to later phases.

### 1. Parallel tool execution

Deferred to later architecture hardening and optimization.

### 2. Write-safety architecture expansion

Deferred until read-path reliability is stronger.

### 3. Multilingual execution-layer guidance

Deferred until the multilingual phase.

## Architecture Responsibility Split

The accepted responsibility split is now:

### Qwen / Qwen-Agent

Owns:

- natural-language understanding
- intent classification
- slot extraction
- grounded summarization
- clarification proposal when missing information is truly blocking

Must not own:

- final report selection
- company invariant handling
- policy decisions
- execution authorization
- business truth

### Compiler

Owns:

- intent-to-capability resolution
- report selection
- invariant injection
- default completion
- clarify vs execute vs reject decision

### Policy / Gateway

Owns:

- tool and report allowlists
- user/service permissions
- execution budgets
- argument sanitation

### Validator

Owns:

- grounding validation
- approved-source validation
- semantic intent-to-result validation
- response-policy compliance

### UI / Runtime

Owns:

- rendering
- deterministic local transforms
- artifact presentation
- timeline and session experience

## Phase Plan Impact

The consultation changes the execution priority as follows:

1. Phase 3 stays active, but its scope is intentionally bounded
2. Phase 4 becomes the next primary engineering track
3. Phase 4 must include:
   - `FreshQueryCompilerContract`
   - single-company invariant injection
   - compiler-governed report selection
   - semantic intent-to-result validation
4. remaining Phase 3 convenience features should not outrun Phase 4 reliability work

## Governing Rule Going Forward

When receiving future architecture advice, the project should apply this rule:

- accept model-family advice when it improves compiler boundaries, validation, or operability
- reject advice that pushes enterprise correctness back into free-form model behavior

This keeps Qwen-Agent as a bounded reasoning component inside the architecture, not the architecture itself.
