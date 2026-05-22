# EC-7J-B Packaging Boundary Plan

Decision target: `ec_7j_b_packaging_boundary_plan_ready_for_counterpart_qa_review`

## Scope

EC-7J-B is a packaging boundary plan only for EC-7H/EC-7I passive live-trace readiness work. It does not stage, commit, push, collect live traces, create or activate a controlled environment, seed datasets, activate archives, deploy, instrument runtime, or enable strict enforcement.

## Worktree State

- Worktree: `/tmp/erpai_pr4_postmerge_verify`
- Branch: detached HEAD
- HEAD: `1504158`
- Pre-EC-7J-B dirty count: 27
- Expected post-report dirty count: 28
- Staged file count: 0
- Tracked modified file count: 0
- Package shape: full-file additions only
- Hunk-aware staging required: no

## Governance Decision

Decision: package the full EC-7H/EC-7I governance chain.

Rationale:

- The governance reports are small Markdown artifacts.
- The chain explains why live trace collection is still blocked.
- The chain records the QA-driven hardening of redaction, dataset validation, archive checks, and environment readiness checks.
- A compact subset would save little size but would make future reviewers reconstruct the safety trail from conversation history.

## Exact Source / Helper Files To Include

All source/helper files are absent from HEAD and are proposed as future full-file additions.

| Path | Future staging mode | Reason |
| --- | --- | --- |
| `scripts/validate_ec7h_synthetic_dataset.py` | full-file | Passive synthetic dataset manifest validator; no DB/Frappe connection and no seeding. |
| `scripts/check_ec7h_archive_readiness.py` | full-file | Passive raw-trace archive readiness checker; no archive creation and no raw trace writes. |
| `scripts/check_ec7h_environment_readiness.py` | full-file | Passive readiness aggregator for bench/site/user/dataset/archive/redacted-output checks; no setup or collection. |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/live_trace_evidence_protocol.py` | full-file | Trace fixture schema, redaction, and validation protocol; no runtime collection path. |

## Exact Test Files To Include

All test files are absent from HEAD and are proposed as future full-file additions.

| Path | Future staging mode | Reason |
| --- | --- | --- |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_live_trace_evidence_protocol.py` | full-file | Validates schema/redaction behavior and storage-policy output. |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_ec7i_setup_support_harnesses.py` | full-file | Validates passive dataset/archive/environment readiness helpers and adversarial false-ready cases. |

## Exact Governance Reports To Include

All governance reports are absent from HEAD and are proposed as future full-file additions.

| Path | Future staging mode | Reason |
| --- | --- | --- |
| `impl_factory/00_governance/current_docs/qwen_erp_ec_7h_a_live_runtime_trace_evidence_plan_2026-05-20.md` | full-file | EC-7H live trace evidence plan. |
| `impl_factory/00_governance/current_docs/qwen_erp_ec_7h_b_trace_fixture_redaction_protocol_2026-05-20.md` | full-file | Accepted trace fixture/redaction protocol. |
| `impl_factory/00_governance/current_docs/qwen_erp_ec_7h_c_a_first_live_trace_collection_protocol_2026-05-21.md` | full-file | First collection protocol, no collection performed. |
| `impl_factory/00_governance/current_docs/qwen_erp_ec_7h_c_b_light_semantic_live_trace_collection_approval_request_2026-05-21.md` | full-file | Owner approval request defining required collection fields. |
| `impl_factory/00_governance/current_docs/qwen_erp_ec_7h_c_c_light_semantic_live_trace_collection_preflight_2026-05-21.md` | full-file | Correctly blocked preflight due to missing environment prerequisites. |
| `impl_factory/00_governance/current_docs/qwen_erp_ec_7h_d_controlled_environment_readiness_plan_2026-05-21.md` | full-file | Controlled environment readiness plan. |
| `impl_factory/00_governance/current_docs/qwen_erp_ec_7h_e_environment_readiness_verification_2026-05-21.md` | full-file | Verification showing no usable controlled environment yet. |
| `impl_factory/00_governance/current_docs/qwen_erp_ec_7i_a_controlled_environment_preparation_plan_2026-05-21.md` | full-file | Environment preparation planning baseline. |
| `impl_factory/00_governance/current_docs/qwen_erp_ec_7i_b_environment_setup_verification_request_2026-05-21.md` | full-file | Setup verification request, blocked pending owner inputs. |
| `impl_factory/00_governance/current_docs/qwen_erp_ec_7i_c_controlled_environment_setup_plan_2026-05-21.md` | full-file | Setup plan, not execution approval. |
| `impl_factory/00_governance/current_docs/qwen_erp_ec_7i_d_execution_ready_setup_architecture_2026-05-21.md` | full-file | Execution-readiness architecture and blockers. |
| `impl_factory/00_governance/current_docs/qwen_erp_ec_7i_e_setup_support_harness_plan_2026-05-21.md` | full-file | Passive harness plan. |
| `impl_factory/00_governance/current_docs/qwen_erp_ec_7i_f_passive_setup_support_harness_2026-05-21.md` | full-file | Passive harness implementation report. |
| `impl_factory/00_governance/current_docs/qwen_erp_ec_7i_f_a_passive_harness_safety_fixes_2026-05-21.md` | full-file | Dataset/archive safety hardening report. |
| `impl_factory/00_governance/current_docs/qwen_erp_ec_7i_f_b_dataset_validator_edge_case_fix_2026-05-21.md` | full-file | Dataset validator edge-case fix report. |
| `impl_factory/00_governance/current_docs/qwen_erp_ec_7i_g_passive_environment_readiness_helper_2026-05-21.md` | full-file | Passive environment readiness helper report. |
| `impl_factory/00_governance/current_docs/qwen_erp_ec_7i_g_a_readiness_helper_hardening_2026-05-22.md` | full-file | Readiness helper false-ready hardening report. |
| `impl_factory/00_governance/current_docs/qwen_erp_ec_7i_g_b_strong_bench_evidence_fix_2026-05-22.md` | full-file | Strong bench evidence fix report. |
| `impl_factory/00_governance/current_docs/qwen_erp_ec_7i_g_c_safe_site_name_validation_fix_2026-05-22.md` | full-file | Safe site-name validation fix report. |
| `impl_factory/00_governance/current_docs/qwen_erp_ec_7i_g_d_site_config_validation_fix_2026-05-22.md` | full-file | Site config validation fix report. |
| `impl_factory/00_governance/current_docs/qwen_erp_ec_7j_a_packaging_readiness_baseline_2026-05-22.md` | full-file | Packaging readiness baseline. |
| `impl_factory/00_governance/current_docs/qwen_erp_ec_7j_b_packaging_boundary_plan_2026-05-22.md` | full-file | This exact boundary plan. |

## Exact Files To Exclude Or Defer

No current dirty EC-7H/EC-7I path is proposed for exclusion. The package excludes by policy any path outside the exact include list above.

Explicitly excluded / not present:

- raw live traces
- unredacted traces
- redacted live trace JSON fixtures
- synthetic dataset manifest JSON
- site configs
- secrets, passwords, tokens, API keys, or secret-handling files
- archive directories, retention marker files, or raw archive contents
- environment setup files
- generated scratch artifacts
- ERP UI files
- seed/data or dummy-data files
- temp/probe/cache files
- PrimeAxis owner-decision docs
- S7 generated scratch streams
- Python bytecode caches and `__pycache__`

## Package Counts

- Source/helper full-file additions: 4
- Test full-file additions: 2
- Governance full-file additions: 22
- Total proposed package files after EC-7J-B report: 28
- Hunk-aware files: 0
- Generated JSON files: 0
- Live trace artifact files: 0
- Raw trace files: 0
- Environment setup/secret files: 0

## Future Staged-Index Verification Commands

Run these only after owner/Counterpart/QA explicitly approve staging.

```bash
cd /tmp/erpai_pr4_postmerge_verify
git diff --cached --name-only | wc -l
git diff --cached --name-only
git diff --cached --stat
git diff --cached --check
git diff --check -- \
  scripts/validate_ec7h_synthetic_dataset.py \
  scripts/check_ec7h_archive_readiness.py \
  scripts/check_ec7h_environment_readiness.py \
  impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/live_trace_evidence_protocol.py \
  impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_live_trace_evidence_protocol.py \
  impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_ec7i_setup_support_harnesses.py \
  impl_factory/00_governance/current_docs/qwen_erp_ec_7h_a_live_runtime_trace_evidence_plan_2026-05-20.md \
  impl_factory/00_governance/current_docs/qwen_erp_ec_7h_b_trace_fixture_redaction_protocol_2026-05-20.md \
  impl_factory/00_governance/current_docs/qwen_erp_ec_7h_c_a_first_live_trace_collection_protocol_2026-05-21.md \
  impl_factory/00_governance/current_docs/qwen_erp_ec_7h_c_b_light_semantic_live_trace_collection_approval_request_2026-05-21.md \
  impl_factory/00_governance/current_docs/qwen_erp_ec_7h_c_c_light_semantic_live_trace_collection_preflight_2026-05-21.md \
  impl_factory/00_governance/current_docs/qwen_erp_ec_7h_d_controlled_environment_readiness_plan_2026-05-21.md \
  impl_factory/00_governance/current_docs/qwen_erp_ec_7h_e_environment_readiness_verification_2026-05-21.md \
  impl_factory/00_governance/current_docs/qwen_erp_ec_7i_a_controlled_environment_preparation_plan_2026-05-21.md \
  impl_factory/00_governance/current_docs/qwen_erp_ec_7i_b_environment_setup_verification_request_2026-05-21.md \
  impl_factory/00_governance/current_docs/qwen_erp_ec_7i_c_controlled_environment_setup_plan_2026-05-21.md \
  impl_factory/00_governance/current_docs/qwen_erp_ec_7i_d_execution_ready_setup_architecture_2026-05-21.md \
  impl_factory/00_governance/current_docs/qwen_erp_ec_7i_e_setup_support_harness_plan_2026-05-21.md \
  impl_factory/00_governance/current_docs/qwen_erp_ec_7i_f_passive_setup_support_harness_2026-05-21.md \
  impl_factory/00_governance/current_docs/qwen_erp_ec_7i_f_a_passive_harness_safety_fixes_2026-05-21.md \
  impl_factory/00_governance/current_docs/qwen_erp_ec_7i_f_b_dataset_validator_edge_case_fix_2026-05-21.md \
  impl_factory/00_governance/current_docs/qwen_erp_ec_7i_g_passive_environment_readiness_helper_2026-05-21.md \
  impl_factory/00_governance/current_docs/qwen_erp_ec_7i_g_a_readiness_helper_hardening_2026-05-22.md \
  impl_factory/00_governance/current_docs/qwen_erp_ec_7i_g_b_strong_bench_evidence_fix_2026-05-22.md \
  impl_factory/00_governance/current_docs/qwen_erp_ec_7i_g_c_safe_site_name_validation_fix_2026-05-22.md \
  impl_factory/00_governance/current_docs/qwen_erp_ec_7i_g_d_site_config_validation_fix_2026-05-22.md \
  impl_factory/00_governance/current_docs/qwen_erp_ec_7j_a_packaging_readiness_baseline_2026-05-22.md \
  impl_factory/00_governance/current_docs/qwen_erp_ec_7j_b_packaging_boundary_plan_2026-05-22.md
git diff --cached --name-only | grep -E 'erp_workspace_ui|02_seed_data|dummy_data|tmp/|\.codex_tmp|primeaxis|generated/qwen_s7_browser_batch|\.json$|\.jsonl$|raw|archive|site_config|secret|password|token' || true
python3 scripts/check_qwen_enterprise_guardrails.py
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m unittest -q \
  ai_assistant_ui.tests.test_live_trace_evidence_protocol \
  ai_assistant_ui.tests.test_ec7i_setup_support_harnesses
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m py_compile \
  scripts/validate_ec7h_synthetic_dataset.py \
  scripts/check_ec7h_archive_readiness.py \
  scripts/check_ec7h_environment_readiness.py \
  impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/live_trace_evidence_protocol.py \
  impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_live_trace_evidence_protocol.py \
  impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_ec7i_setup_support_harnesses.py
```

Also rerun:

- Fake-Frappe service import probe.
- Direct assistant append inventory, expected `0 / 1 / 27`.
- Formal raw assistant append scan, expected only:
  - `authorized_emission.py:271`
  - `authorized_emission.py:327`
- Excluded status scan.

## Current Verification

EC-7J-B verification reproduced:

- Guardrail: PASS
- Fake-Frappe service import: PASS
- EC-7H-B protocol + EC-7I harness tests: PASS
- Direct assistant inventory: `0 / 1 / 27`
- Formal raw append scan:
  - `authorized_emission.py:271`
  - `authorized_emission.py:327`
- Python compile: PASS
- Scoped diff check: PASS
- Excluded status scan: clean
- Staged files: `0`

## Final Decision

`ec_7j_b_packaging_boundary_plan_ready_for_counterpart_qa_review`

## Next Step

If Counterpart/QA accept EC-7J-B, proceed to EC-7J-C staged-index construction approval request. Do not stage until that approval is explicit.
