# Qwen Chat Enterprise Baseline

Status: active baseline  
Date: 2026-04-04  
Audience: maintainers shipping changes in `qwen_chat`

## 1. Current Baseline

The current Qwen Chat baseline is considered enterprise-ready at the verification level.

As of this checkpoint:

1. guardrail audit is green
2. scripted semantic verification is green
3. scripted post-contract verification is green
4. the full enterprise release gate `scripts/qwen_verify_enterprise_matrix.sh full` has been rerun successfully end to end
5. `financial_summary` second wave is now active in one bounded form only:
   `receivable` + `payable` + `cross_domain_health` -> `working_capital_health`
6. the approved `financial_summary` composite path is now runtime-reachable from governed semantic payloads because validated `composite_profile_context` survives extracted-slot sanitization
7. smoke-fixture setup prompts have been moved into governed metadata where they were shared and unstable
8. remaining inline smoke strings have been audited and separated into:
   - governed fixture debt already migrated
   - explicit scenario contracts that should stay inline
   - debug-only local probes
9. protected smoke-support files are now guardrailed against reintroducing shared governed fixture literals inline
10. direct site-backed smoke sessions are explicitly committed on create/delete, so live hardening runs do not depend on implicit transaction visibility
11. append-only Qwen session saves now tolerate one timestamp-mismatch retry by reloading and restoring pending local session state conservatively
12. the follow-up boundary redesign wave is now closed to its stop rule:
   - `FollowUpBoundaryContract` exists
   - the contract producer and evaluator exist
   - residual degraded fallback is explicit, bounded, and test-protected
   - the wave has been revalidated with the full enterprise gate
13. residual degraded follow-up fallback is now materially narrower:
   - blank semantic payloads fail closed on supported grounded follow-up families
   - unsupported grounded artifacts do not break out on a single disjoint raw domain when semantic follow-up is present but blank
   - explicit multi-domain asks, contradictory presentation payloads, and governed uncovered-domain routing remain the bounded fallback exceptions
14. the mixed-metric adversarial lane is aligned to the approved bounded outcomes, including safe ERP reasoning that explicitly states the grounded limitation

## 2. Release-Gate Command

Default enterprise verification command:

```bash
scripts/qwen_verify_enterprise_matrix.sh full
```

This is the current authoritative baseline gate for Qwen Chat.

## 3. When To Use Less Than Full

Use targeted verification only when the change is clearly narrower than the full baseline.

### Semantic-only changes

Examples:

1. semantic registry updates
2. financial summary semantic contract changes
3. non-live semantic unit work

Run:

```bash
scripts/qwen_verify_enterprise_matrix.sh semantic
```

### Post-contract live/hardening changes

Examples:

1. smoke-fixture metadata changes
2. live hardening/support changes
3. H3/H4/H5 scenario changes

Run:

```bash
scripts/qwen_verify_enterprise_matrix.sh post-contract
```

### Runtime or policy changes touching both planes

Examples:

1. compiler behavior
2. interpreter behavior
3. semantic-to-runtime routing
4. governed recovery behavior

Run:

```bash
scripts/qwen_verify_enterprise_matrix.sh full
```

## 4. Senior Rule For Future Work

Before making the next change, choose the work type explicitly:

1. product/runtime improvement
2. governed semantic design
3. verification architecture
4. refactor hygiene

If the change is mostly refactor hygiene and does not reduce risk materially, do not do it by default.

## 5. Service.py Rule

Do not resume `service.py` trimming just to reduce line count.

Touch `service.py` only when:

1. the change improves real runtime behavior
2. the change removes meaningful verification debt
3. the affected block is clearly harming architecture or maintainability

## 6. Fixture Rule

Move prompts into governed smoke metadata only when both are true:

1. the prompt is a shared setup seed across multiple smokes
2. the prompt is not itself the scenario contract under test

Keep prompts inline when they are:

1. explicit clarification contracts
2. explicit reasoning follow-up contracts
3. adversarial wording contracts

Protected smoke-support files should not inline shared governed setup prompts again. Use fixture helpers instead.

## 7. Recommended Next Focus

Preferred next work after this checkpoint:

1. real product/runtime hardening or capability improvement
2. design-first review before any additional `financial_summary` composite widening
3. verification burn-down only when a real red appears
4. reopen follow-up boundary work only if a new red points there directly

Avoid:

1. cosmetic refactors without architectural gain
2. new prompt migrations without reuse evidence
3. speculative cleanup while the current baseline is already green
4. adding more `financial_summary` composite paths without a new checkpoint

Active plan reference:

1. [QWEN_CHAT_NEXT_WAVE_PLAN.md](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/QWEN_CHAT_NEXT_WAVE_PLAN.md)
2. [QWEN_CHAT_FOLLOWUP_BOUNDARY_WAVE_CHECKPOINT.md](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/QWEN_CHAT_FOLLOWUP_BOUNDARY_WAVE_CHECKPOINT.md)

## 8. Out-Of-Scope Reminder

This baseline does not change the standing rule:

1. [sales_console.js](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/erp_workspace_ui/page/sales_console/sales_console.js) remains outside this task and must not be touched
