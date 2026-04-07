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
15. Phase 1.1 now has its first strict governed operational checkpoint:
   - `Delivery Note List`
   - exact `last 5` scope preserved on the live compiled path
   - strict checkpoint smoke promoted into the release-gate path
   - full enterprise gate rerun green after that promotion
16. Phase 1.1 now also has a bounded governed trend checkpoint:
   - `Delivery Note Trends` is admitted through the existing `trend_analytics` family
   - both current-fiscal-year and `last_year` delivery-trend asks are release-gated
   - invoice-detail to delivery-trend breakout continuity is release-gated
   - `last_year` works through reused governed time-scope contracts, not a delivery-specific routing patch
17. the bounded Delivery correction track is now closed:
   - `latest N` Delivery Note listing behavior is browser-valid again
   - full-month Delivery Note listing no longer leaks a prior numeric limit
   - governed `Delivery Note` detail drilldown now works from the listing surface
   - the Delivery Note detail smoke is now in the release-gate module
18. the bounded invoice-to-delivery proof slice is now closed:
   - supported invoices answer delivery proof from governed evidence
   - rough delivery-date follow-ups are grounded to linked submitted delivery-note dates
   - fresh-chat explicit invoice identifiers now route through governed `entity_detail` before compiled-first-turn handling
   - both the standard and fresh-chat invoice proof smokes are release-gated
19. Phase `1.1` is now checkpoint-complete:
   - Delivery Note listing, date-scope, status, trend, detail, and invoice-to-delivery proof are release-gated
   - the next bounded operational expansion should move to `1.2` Sales Order Status

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

1. move to `1.2` Sales Order Status as the next bounded operational phase
2. keep the `1.1D` invoice-to-delivery proof slice narrow and evidence-based if it is later expanded
3. verification burn-down only when a real red appears

Avoid:

1. cosmetic refactors without architectural gain
2. new prompt migrations without reuse evidence
3. speculative cleanup while the current baseline is already green
4. adding more `financial_summary` composite paths without a new checkpoint

Active plan reference:

1. [qwen_erp_phase_implementation_roadmap_2026-04-04.md](/home/deploy/erp-projects/erpai_project1/impl_factory/00_governance/current_docs/qwen_erp_phase_implementation_roadmap_2026-04-04.md)
2. [qwen_erp_post_contract_expansion_backlog_2026-03-25.md](/home/deploy/erp-projects/erpai_project1/impl_factory/00_governance/current_docs/qwen_erp_post_contract_expansion_backlog_2026-03-25.md)
3. [QWEN_CHAT_FINANCIAL_SUMMARY_RUNTIME_BOUNDARY.md](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/docs/current/QWEN_CHAT_FINANCIAL_SUMMARY_RUNTIME_BOUNDARY.md)

## 8. Out-Of-Scope Reminder

This baseline does not change the standing rule:

1. [sales_console.js](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/erp_workspace_ui/page/sales_console/sales_console.js) remains outside this task and must not be touched
