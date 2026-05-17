# Qwen ERP Phase 4 Slice 5 Semantic Validation Note (2026-03-22)

Status: completed  
Scope: deterministic semantic intent-to-result validation for compiled first-turn read execution

## Purpose

Slice 5 closes the gap between:

- grounded runtime validation
- and semantic correctness against the governed first-turn request

This slice exists because a result can be:

- grounded
- approved
- tool-valid

and still be semantically wrong for the user’s requested business intent.

## What Was Implemented

### 1. ERP-side deterministic semantic validator

Added:

- `semantic_validator.py`

Validator boundary:

- runs after compiled runtime execution
- stays in ERP/compiler governance layer
- does not rely on another model call

### 2. Metadata-driven dimension and metric support

Extended report metadata with:

- `supported_dimensions`
- `supported_metrics`

This lets semantic validation check governed support without falling back to phrase-specific logic.

### 3. Deterministic validation checks

The validator now checks:

1. schema presence
2. requested metric presence
3. requested dimension consistency
4. report-to-capability consistency
5. report-to-intent-class consistency
6. semantic tag consistency
7. compiler-filter vs runtime-filter consistency
8. time-scope consistency
9. zero-row clarify policy for governed ranked/trend cases

### 4. Explicit validation outcomes

Semantic validation now returns one of:

- `pass`
- `clarify`
- `reject_semantically_inconsistent`

### 5. Compiled execution helper integration

The compiled Phase 4 helper now runs:

1. fresh-query compilation
2. compiled runtime execution
3. semantic intent-to-result validation

without promoting the path into the live first-turn chat flow yet.

## Contracts Preserved

This slice preserves the established rule:

- `Qwen-Agent proposes`
- `compiler enforces`
- `validator confirms`

The runtime still handles:

- grounded tool use
- grounded summarization

The ERP/compiler layer now additionally owns:

- semantic result acceptance
- semantic clarification
- semantic rejection

## Verification

### Deterministic selftests

Passed:

1. governed semantic pass case
2. governed semantic rejection case
3. governed semantic clarify case

### Real compiled smoke

Passed:

- payable first-turn request
- compiled report selection
- exact governed filter execution
- runtime grounded validation pass
- semantic intent-to-result validation pass

## Current Position After Slice 5

Phase 4 status now effectively is:

1. Slice 1 complete
2. Slice 2 complete
3. Slice 3 complete
4. Slice 4 complete
5. Slice 5 complete
6. Slice 6 next

The remaining decision is not whether the compiled path works technically.

The remaining decision is:

- how to audit it fully
- and how to roll it into the live first-turn chat path safely

## Next Step

Next implementation focus:

- Slice 6 audit and observability

Then:

- rollout decision for compiled first-turn execution
