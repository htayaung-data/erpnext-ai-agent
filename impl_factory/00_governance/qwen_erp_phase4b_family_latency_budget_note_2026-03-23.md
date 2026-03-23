# Qwen ERP Phase 4B Family Latency Budget Note (2026-03-23)

Status: implemented  
Scope: family-by-family latency governance for the post-4B governed read path  
Goal: measure the governed family layer against explicit development budgets and tighter enterprise targets without relaxing compiler or validator governance.

## 1. Why This Was Added

After the core Phase 4B semantic family layer was completed, the next enterprise-safe step was:

1. broaden family evaluation coverage
2. make latency expectations explicit by business family
3. distinguish:
   - acceptable current development posture
   - still-open enterprise production targets

This note introduces latency budgets as evaluation governance, not as execution logic.

## 2. Design Rule

Latency budgets do not change compiler or validator behavior.

They are used only to answer:

1. which governed families are currently acceptable for development
2. which governed families are already meeting tighter enterprise targets
3. which heavier families still need targeted hardening

So the architecture remains:

- `Qwen-Agent proposes`
- `compiler enforces`
- `validator confirms`

## 3. What Was Implemented

### 3.1 Family Latency Budgets

Governed budgets were added for:

1. `financial_statement`
2. `aging`
3. `ranking_analytics`
4. `trend_analytics`
5. `inventory_snapshot`
6. `product_profitability`
7. `working_capital_health`

Each budget now records:

1. proposal-generation development budget
2. runtime-execution development budget
3. total-pipeline development budget
4. tighter total-pipeline enterprise target

### 3.2 Broader Evaluation Sets

The family evaluation registry was expanded with:

1. additional execute-path business cases
2. a dedicated `latency_focus_families` set for heavier governed families

### 3.3 Budget-Aware Evaluation

The evaluation layer now returns:

1. per-case latency assessment
2. per-family latency budget summary
3. development-green vs enterprise-green rates

## 4. Measured Posture

The current budget report shows:

1. latency budget summary is working
2. the governed family layer is broadly development-acceptable
3. enterprise targets are still intentionally stricter than current runtime reality

Important measured result from the full report:

1. `development_green_rate`: `0.8571`
2. `enterprise_green_rate`: `0.5714`

Meaning:

1. most governed families are within current development budgets
2. only some families are already within tighter enterprise targets

The current heavier open areas remain:

1. `working_capital_health`
2. heavier composite/runtime paths
3. some trend/runtime stages when uncached

## 5. Important Interpretation

This does **not** mean the architecture is wrong.

It means:

1. correctness/governance is strong
2. latency is now measurable by family
3. the remaining work is targeted runtime hardening, not redesign

## 6. Recommended Next Work

The next latency hardening order should be:

1. composite `working_capital_health`
2. heavier trend paths
3. remaining runtime-heavy inventory/product families
4. larger family evaluation sets and repeated warm/cold comparisons

## 7. Enterprise Conclusion

Current truthful posture:

1. the governed family layer is suitable for continued development and controlled internal use
2. it is not yet uniformly enterprise-fast across all heavier families
3. latency hardening should now proceed family-by-family, using governed budgets and evaluation sets rather than ad hoc query tuning
