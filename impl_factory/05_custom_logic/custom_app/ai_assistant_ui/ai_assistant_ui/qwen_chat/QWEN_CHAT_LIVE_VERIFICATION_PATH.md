# Qwen Chat Live Verification Path

Status: active live-site verification helper  
Date: 2026-03-30  
Audience: maintainers running site-aware Qwen smokes

## 1. Purpose

This project now has a repo-local helper for running site-aware Qwen smokes through the Docker backend container.

Use:

[`scripts/qwen_site_execute.sh`](/home/deploy/erp-projects/erpai_project1/scripts/qwen_site_execute.sh)

and

[`scripts/qwen_site_run_tests.sh`](/home/deploy/erp-projects/erpai_project1/scripts/qwen_site_run_tests.sh)

and, for the repeatable enterprise matrix,

[`scripts/qwen_verify_enterprise_matrix.sh`](/home/deploy/erp-projects/erpai_project1/scripts/qwen_verify_enterprise_matrix.sh)

This avoids depending on a shell-local `bench` binary for either `bench execute` or `bench run-tests`.

## 2. Command Pattern

Example:

```bash
scripts/qwen_site_execute.sh ai_assistant_ui.qwen_chat.service.run_phase8b_recovery_authority_smoke
```

Regression example:

```bash
scripts/qwen_site_run_tests.sh ai_assistant_ui.tests.test_post_contract_regression
```

Enterprise matrix examples:

```bash
scripts/qwen_verify_enterprise_matrix.sh semantic
scripts/qwen_verify_enterprise_matrix.sh post-contract
scripts/qwen_verify_enterprise_matrix.sh full
```

Default behavior:

1. runs against the `backend` compose service
2. resolves the site from `.env`
3. prefers `DEFAULT_SITE`
4. falls back to `SITE_NAME`

Override behavior:

```bash
QWEN_SITE=erpai_prj1 scripts/qwen_site_execute.sh ai_assistant_ui.qwen_chat.service.run_phase7d_boundary_response_live_smoke
```

## 3. Current Live Results

Validated green:

1. `run_phase55_hardening_suite`
2. `run_phase6_artifact_refinement_precedence_smoke`
3. `run_phase6_hardening_suite`
4. `run_phase7d_boundary_response_live_smoke`
5. `run_phase7_hardening_suite`
6. `run_phase8b_recovery_authority_smoke`
7. `run_phase8c_repair_handling_smoke`
8. `run_phase8_hardening_suite`
9. `ai_assistant_ui.tests.test_post_contract_regression`
10. `ai_assistant_ui.tests.test_post_contract_guard_probes`
11. `ai_assistant_ui.tests.test_post_contract_state_live`
12. `ai_assistant_ui.tests.test_post_contract_release_gates`
13. `ai_assistant_ui.tests.test_post_contract_observability_live`
14. `ai_assistant_ui.tests.test_post_contract_adversarial`
15. `ai_assistant_ui.tests.test_post_contract_state_integrity`
16. `ai_assistant_ui.tests.test_post_contract_observability`
17. `scripts/qwen_verify_enterprise_matrix.sh semantic`
18. `scripts/qwen_verify_enterprise_matrix.sh post-contract`

Latest note:

1. `run_phase7d_boundary_response_live_smoke` initially exposed a brittle wording assertion
2. the live boundary payload and user-facing answer were semantically correct
3. the smoke was hardened to check for governed scope plus coverage-gap explanation, not one stale phrase
4. `run_phase6_artifact_refinement_precedence_smoke` also needed a more deterministic seed prompt
5. the enterprise fix there was to tighten the live smoke inputs, not to patch runtime behavior around an ambiguous prompt
6. `run_phase8c_repair_handling_smoke` exposed a real governed ranking gap for `customer + quantity`
7. that issue was fixed in the semantic registry and continuation handling, then verified live through the full Phase 8 suite
8. the broader regression module also exposed under-specified live smoke seeds in Phase 5.5 and Phase 7
9. those smokes were hardened by asserting setup success and using the canonical governed ranking prompt
10. after that, the full live regression module passed cleanly
11. the state-live module then exposed three stale-state H3 smokes that were seeded against older clarification and ranking assumptions
12. those H3 smokes were updated to use current governed prompts and provenance-based assertions
13. after that, the full live state module passed cleanly
14. the observability-live module exposed one stale Phase 8 enrichment-boundary seed
15. that smoke was updated to the live-proven `include serial number column` boundary path and the full module passed cleanly
16. the adversarial module then exposed two H4 assertions that were stricter than the current bounded contract
17. those H4 smokes were updated to assert bounded non-speculative behavior, not a specific legacy boundary-only path
18. after that, the full adversarial module passed cleanly
19. the remaining container-backed post-contract modules were then closed cleanly:
20. `test_post_contract_state_integrity` passed without requiring any runtime or test-contract changes
21. `test_post_contract_observability` also passed cleanly, confirming the non-live observability shape remains stable
22. the first scripted post-contract matrix run then exposed a real Phase 6 verification fragility in the artifact-refinement precedence smoke
23. that smoke was hardened using a bounded set of live-proven row-limit prompts, because the runtime could satisfy the contract but not with one single wording shape under full-matrix load
24. a later full-matrix rerun then exposed an H3 fresh-query replacement smoke that was seeded with a weaker ranking prompt and an unnecessary override prefix
25. that H3 smoke was aligned to the stronger live-proven ranking seed plus the self-contained `give me AR insight` fresh-query path
26. after those two smoke-contract fixes, the full scripted `post-contract` enterprise matrix completed green end to end
27. the next enterprise cleanup step moved the recent Phase 6 and H3 smoke prompts into the governed [`smoke_fixture_registry.json`](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/smoke_fixture_registry.json)
28. direct live probing showed that not every semantically similar ranking prompt is stable enough for this purpose
29. the governed fixture was then corrected to the live-proven `Top 7 customers by quantity sold last month` seed, which kept both the Phase 6 refinement smoke and the H3 grounded-source replacement smoke green
30. after that metadata-backed fixture correction, the full `test_post_contract_regression` module passed green again
31. the same governed fixture was then reused for the Phase 5.5 front-door boundary smoke and the Phase 7 live boundary/orchestration smokes, removing more duplicated artifact-setup prompts from Python
32. targeted live reruns of `run_phase55_frontdoor_boundary_smoke` and `run_phase7_hardening_suite` stayed green after that reuse
33. the next cleanup step introduced a dedicated `recovery_flow` fixture shape for Phase 8 product-ranking recovery prompts
34. that moved the repeated product-ranking, enrichment, guidance, acceptance, and fresh-override prompts out of Python and into governed smoke metadata
35. `run_phase8_hardening_suite` stayed green after the Phase 8 fixture migration, confirming the metadata-backed recovery flow is stable in live verification
36. the same governed `product_recovery_flow` fixture was then reused in the H3/H4 smoke paths inside `service.py`, removing the remaining duplicate product-recovery prompt literals from that layer
37. `test_post_contract_adversarial` stayed green immediately after that reuse
38. the first `test_post_contract_state_live` rerun hit a database lock timeout during test-environment setup when live modules were running concurrently, not a behavior regression
39. rerunning `test_post_contract_state_live` alone then passed cleanly end to end, confirming the fixture migration itself was stable
40. the next cleanup split truly generic recovery-interaction prompts into their own governed `interaction_actions` fixture instead of tying them to a product-specific recovery flow
41. that let the remaining H3 mixed-state recovery prompts move out of `service.py` without abusing a product-ranking fixture for generic interaction language
42. `test_post_contract_state_live` stayed green after that split, confirming the interaction fixture contract is sound in live verification
43. after the smoke-string audit and the final governed fixture migrations, the full scripted `post-contract` enterprise matrix was rerun end to end and stayed green
44. the complementary scripted `semantic` enterprise matrix was then rerun and also stayed green
45. that gives the repo a clean checkpoint where both governed semantic validation and site-backed post-contract verification are simultaneously green
46. the next enterprise hardening step then removed the last shared `give me AR insight` and `how do I ask for qty` setup literals from the protected Phase 6, Phase 8, and H3/H4 smoke-support paths
47. the guardrail audit now enforces that those governed fixture strings do not reappear inline in `service.py`, `phase6_hardening_support.py`, `phase7_hardening_support.py`, or `phase8_hardening_support.py`
48. that migration initially exposed a smoke-session harness weakness in direct site-backed Phase 5.5 execution: newly inserted smoke sessions were not explicitly committed before later `check_if_latest` save paths
49. `smoke_session_support.py` was then hardened with explicit create/delete commits for Phase 5.5 and Phase 6 smoke sessions
50. after that harness fix, `run_phase55_hardening_suite` returned green again
51. the container-backed `test_post_contract_regression` module also returned green again
52. `test_post_contract_state_live` was then rerun sequentially and passed cleanly end to end
53. the full enterprise release gate `scripts/qwen_verify_enterprise_matrix.sh full` was then rerun end to end and completed green
54. that full pass included:
    - local semantic verification
    - post-contract guard/state/observability modules
    - live regression suites for Phases 5.5 through 8
    - release-gate, state-live, observability-live, and adversarial modules
55. the next runtime improvement made the approved `financial_summary -> working_capital_health` path actually reachable from semantic-runtime payloads by preserving governed `composite_profile_context` values during extracted-slot sanitization
56. validating that improvement against the full gate then exposed two real live verification drifts in Phase 5.5:
    - the old pending-override smoke was still using a stale free-form fresh request instead of the governed fresh-override fixture
    - direct live Phase 5.5 execution could still hit a `TimestampMismatchError` on append-only Qwen session saves
57. the pending-override smoke was aligned to the governed `fresh_override_to_ar` fixture, matching the already-green H3 pending-override path
58. `session_context.py` was then hardened with a conservative timestamp-mismatch retry that reloads and restores append-only session state before retrying save
59. the new timestamp-mismatch retry is now covered in `test_post_contract_guard_probes`
60. after those two fixes:
    - `run_phase55_hardening_suite` returned green directly again
    - the full enterprise release gate `scripts/qwen_verify_enterprise_matrix.sh full` reran green again end to end

## 4. Senior Recommendation

Treat this live verification path as the default way to validate site-aware Qwen smokes before more refactor work.

Reason:

1. the live verification path is now real
2. the old blocker is no longer “bench not found”
3. site-aware greens and reds can now be investigated with evidence instead of assumption
4. the enterprise matrix script now makes the current verification contract repeatable instead of relying on manual command recall

## 5. Out-Of-Scope Reminder

This verification path does not change the standing rule:

1. [sales_console.js](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/erp_workspace_ui/page/sales_console/sales_console.js) remains outside this task and must not be touched
