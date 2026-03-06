# Phase 3 Risk-Tier Inventory

Date: 2026-03-03  
Owner: AI Runtime Engineering  
Scope: initial risk-tier inventory for current replay suites, browser/manual packs, and critical module regressions  
Status: active Phase 3 baseline inventory

## Purpose
This document assigns risk tiers and rerun obligations to the current quality assets.

It exists to answer three enterprise questions clearly:

1. which assets protect the highest-risk business behavior
2. what must be rerun after a given type of change
3. who owns the evidence for each critical asset

This is a governance artifact. It is not a runtime contract.

## Tier Definitions

### Tier 1
High business, safety, or compliance impact.

Examples:

1. finance-critical reads
2. write safety
3. latest-record misrouting that can mislead users materially
4. cross-topic state defects that can produce wrong answers in production sessions

### Tier 2
Important analytical behavior with moderate business impact.

Examples:

1. ranking
2. projection
3. transform-followup
4. correction/rebind
5. browser smoke for core user flows

### Tier 3
Lower-risk presentation or developer-confidence assets.

Examples:

1. focused helper/unit tests with narrow scope
2. formatting-only regressions
3. support tests around extracted module boundaries

## Replay Suite Inventory

| Asset | Tier | Owner | Protects | Must rerun when |
|---|---|---|---|---|
| `core_read` | 1 | AI Runtime Engineering | core analytical read behavior, report selection, ranking, projection, KPI, trend, entity follow-up | resolver changes, shaping changes, memory/resume changes, capability metadata changes, structural refactor |
| `multiturn_context` | 1 | AI Runtime Engineering | correction/rebind, context topic switch, latest-record follow-up, session state carryover | memory/resume changes, follow-up policy changes, structural refactor |
| `write_safety` | 1 | AI Runtime Engineering | destructive/write-safe behavior, confirm/cancel flow, bounded write control | any write-path change, permission boundary change, safety wording/confirmation logic change |
| `no_data_unsupported` | 1 | AI Runtime Engineering | safe no-data envelope, unsupported handling, observability-safe responses | shaping changes, quality-gate changes, unsupported/no-data policy changes |
| `transform_followup` | 2 | AI Runtime Engineering | transform-last behavior, scale/projection/sort/top-n reuse on prior result | transform policy changes, response shaping changes, memory/resume changes |

## Browser / Manual Pack Inventory

| Asset | Tier | Owner | Protects | Must rerun when |
|---|---|---|---|---|
| Curated browser smoke pack | 1 | AI Runtime Engineering + Product QA | cross-topic parity, browser/runtime session correctness, real user-path safety | structural refactor, memory/resume changes, resolver changes, shaping changes, release-candidate close |
| Customer ranking + scale | 2 | AI Runtime Engineering | ranking + transform parity in finance/sales reads | ranking, transform, resolver, shaping changes |
| Product ranking + projection | 2 | AI Runtime Engineering | detail projection and restrictive `only` behavior | projection/shaping changes, memory changes |
| Warehouse correction + scale | 1 | AI Runtime Engineering | correction/rebind state authority, cross-topic carryover, aggregate-row-safe ranking | correction policy changes, memory changes, ranking changes |
| Latest-record clarification flow | 1 | AI Runtime Engineering | doctype clarification, resume pinning, latest-record execution | latest-record policy changes, resume changes, ontology/metadata changes touching doctypes |
| Finance parity smoke (`accounts receivable`, `purchase invoice latest`) | 1 | AI Runtime Engineering | finance subject disambiguation, doctype/domain pinning | semantic resolver changes, capability metadata changes, latest-record policy changes |
| Write confirm/cancel smoke | 1 | AI Runtime Engineering | browser-visible write safety | write path changes, wording changes, confirm/cancel logic changes |

## Critical Module / Unit Regression Inventory

| Asset | Tier | Owner | Protects | Must rerun when |
|---|---|---|---|---|
| `test_v7_read_engine_clarification.py` | 1 | AI Runtime Engineering | latest-record recovery, correction/rebind, state merging, clarifications | read_engine, resume_policy, memory, latest-record policy changes |
| `test_v7_memory_context.py` | 1 | AI Runtime Engineering | topic state, follow-up rebinding, correction ordering, sticky projection/scale reset | memory changes, follow-up policy changes |
| `test_v7_spec_pipeline.py` | 1 | AI Runtime Engineering | spec generation, explicit latest-record pinning, task-class normalization | spec_pipeline changes, planner/spec normalization changes |
| `test_v7_semantic_resolver_constraints.py` | 1 | AI Runtime Engineering | deterministic report selection, finance/party ledger semantics, ranking constraints | semantic_resolver changes, capability metadata changes |
| `test_v7_response_shaper.py` | 2 | AI Runtime Engineering | projection labels, restrictive `only`, aggregate-row handling, shaped output correctness | response_shaper changes, shaping policy changes |
| `test_v7_transform_last.py` | 2 | AI Runtime Engineering | transform-last mode preservation and scale/projection behavior | transform_last changes, shaping changes |
| `test_v7_read_execution_runner.py` | 2 | AI Runtime Engineering | bounded retry/switch loop, candidate progression, final fallback behavior | execution runner / loop policy changes |
| `test_v7_capability_registry.py` | 2 | AI Runtime Engineering | governed capability semantics availability | capability metadata changes |
| `test_v7_ontology_normalization.py` | 2 | AI Runtime Engineering | canonical metric/dimension/ambiguity normalization | ontology changes |

## Standing Core Packs

### Core replay pack
Always treat the following as the minimum shared-runtime replay confidence set:

1. `core_read`
2. `multiturn_context`
3. `transform_followup`

### Core browser smoke pack
Always treat the following as the minimum browser parity set after significant shared-runtime change:

1. customer ranking + scale
2. product ranking + projection
3. warehouse correction + scale
4. latest-record clarification

## Ownership Rule
Current default owner for all listed assets:

1. AI Runtime Engineering

When Product QA or Operations ownership becomes formalized in later phases, this inventory must be updated to show joint ownership where appropriate.

## Immediate Use Rule
Until a fuller incident system is operational:

1. do not merge or accept shared-runtime changes without checking this inventory
2. determine the impacted surfaces
3. rerun the assets required by those surfaces
4. attach the evidence to the change/closure note

## Next Update
This inventory must be updated when:

1. a new behavioral class is approved
2. a new browser/manual golden pack is introduced
3. a suite changes tier because business risk changed
4. ownership changes
