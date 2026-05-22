# EC-7J-C Staged-Index Construction Approval Request

Decision target: `ec_7j_c_staged_index_construction_request_ready_for_counterpart_qa_owner_review`

## Scope

EC-7J-C is a staging approval request only. It does not stage, commit, push, collect live traces, create or activate a controlled environment, seed datasets, activate archives, deploy, instrument runtime, or enable strict enforcement.

## Current State

- Worktree: `/tmp/erpai_pr4_postmerge_verify`
- HEAD: `1504158`
- Staged files: 0
- Approved EC-7J-B package boundary: 28 full-file untracked additions
- Hunk-aware staging required: no
- EC-7J-C report status: not included in the 28-file EC-7J-B package unless owner/QA explicitly add it later

## Approved 28-File Include List

The EC-7J-B include list is the authority. Broad grep scans are secondary warning signals only.

```text
scripts/validate_ec7h_synthetic_dataset.py
scripts/check_ec7h_archive_readiness.py
scripts/check_ec7h_environment_readiness.py
impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/live_trace_evidence_protocol.py
impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_live_trace_evidence_protocol.py
impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_ec7i_setup_support_harnesses.py
impl_factory/00_governance/current_docs/qwen_erp_ec_7h_a_live_runtime_trace_evidence_plan_2026-05-20.md
impl_factory/00_governance/current_docs/qwen_erp_ec_7h_b_trace_fixture_redaction_protocol_2026-05-20.md
impl_factory/00_governance/current_docs/qwen_erp_ec_7h_c_a_first_live_trace_collection_protocol_2026-05-21.md
impl_factory/00_governance/current_docs/qwen_erp_ec_7h_c_b_light_semantic_live_trace_collection_approval_request_2026-05-21.md
impl_factory/00_governance/current_docs/qwen_erp_ec_7h_c_c_light_semantic_live_trace_collection_preflight_2026-05-21.md
impl_factory/00_governance/current_docs/qwen_erp_ec_7h_d_controlled_environment_readiness_plan_2026-05-21.md
impl_factory/00_governance/current_docs/qwen_erp_ec_7h_e_environment_readiness_verification_2026-05-21.md
impl_factory/00_governance/current_docs/qwen_erp_ec_7i_a_controlled_environment_preparation_plan_2026-05-21.md
impl_factory/00_governance/current_docs/qwen_erp_ec_7i_b_environment_setup_verification_request_2026-05-21.md
impl_factory/00_governance/current_docs/qwen_erp_ec_7i_c_controlled_environment_setup_plan_2026-05-21.md
impl_factory/00_governance/current_docs/qwen_erp_ec_7i_d_execution_ready_setup_architecture_2026-05-21.md
impl_factory/00_governance/current_docs/qwen_erp_ec_7i_e_setup_support_harness_plan_2026-05-21.md
impl_factory/00_governance/current_docs/qwen_erp_ec_7i_f_passive_setup_support_harness_2026-05-21.md
impl_factory/00_governance/current_docs/qwen_erp_ec_7i_f_a_passive_harness_safety_fixes_2026-05-21.md
impl_factory/00_governance/current_docs/qwen_erp_ec_7i_f_b_dataset_validator_edge_case_fix_2026-05-21.md
impl_factory/00_governance/current_docs/qwen_erp_ec_7i_g_passive_environment_readiness_helper_2026-05-21.md
impl_factory/00_governance/current_docs/qwen_erp_ec_7i_g_a_readiness_helper_hardening_2026-05-22.md
impl_factory/00_governance/current_docs/qwen_erp_ec_7i_g_b_strong_bench_evidence_fix_2026-05-22.md
impl_factory/00_governance/current_docs/qwen_erp_ec_7i_g_c_safe_site_name_validation_fix_2026-05-22.md
impl_factory/00_governance/current_docs/qwen_erp_ec_7i_g_d_site_config_validation_fix_2026-05-22.md
impl_factory/00_governance/current_docs/qwen_erp_ec_7j_a_packaging_readiness_baseline_2026-05-22.md
impl_factory/00_governance/current_docs/qwen_erp_ec_7j_b_packaging_boundary_plan_2026-05-22.md
```

## Exact Future Staging Procedure

Run only after explicit owner/Counterpart/QA approval.

```bash
cd /tmp/erpai_pr4_postmerge_verify
git add -- \
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
```

## Authoritative Staged Boundary Check

After staging, this check must show `STAGED_COUNT=28`, `MISSING=[]`, and `EXTRA=[]`.

```bash
python3 - <<'PY'
import subprocess

approved = {
    "scripts/validate_ec7h_synthetic_dataset.py",
    "scripts/check_ec7h_archive_readiness.py",
    "scripts/check_ec7h_environment_readiness.py",
    "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/live_trace_evidence_protocol.py",
    "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_live_trace_evidence_protocol.py",
    "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_ec7i_setup_support_harnesses.py",
    "impl_factory/00_governance/current_docs/qwen_erp_ec_7h_a_live_runtime_trace_evidence_plan_2026-05-20.md",
    "impl_factory/00_governance/current_docs/qwen_erp_ec_7h_b_trace_fixture_redaction_protocol_2026-05-20.md",
    "impl_factory/00_governance/current_docs/qwen_erp_ec_7h_c_a_first_live_trace_collection_protocol_2026-05-21.md",
    "impl_factory/00_governance/current_docs/qwen_erp_ec_7h_c_b_light_semantic_live_trace_collection_approval_request_2026-05-21.md",
    "impl_factory/00_governance/current_docs/qwen_erp_ec_7h_c_c_light_semantic_live_trace_collection_preflight_2026-05-21.md",
    "impl_factory/00_governance/current_docs/qwen_erp_ec_7h_d_controlled_environment_readiness_plan_2026-05-21.md",
    "impl_factory/00_governance/current_docs/qwen_erp_ec_7h_e_environment_readiness_verification_2026-05-21.md",
    "impl_factory/00_governance/current_docs/qwen_erp_ec_7i_a_controlled_environment_preparation_plan_2026-05-21.md",
    "impl_factory/00_governance/current_docs/qwen_erp_ec_7i_b_environment_setup_verification_request_2026-05-21.md",
    "impl_factory/00_governance/current_docs/qwen_erp_ec_7i_c_controlled_environment_setup_plan_2026-05-21.md",
    "impl_factory/00_governance/current_docs/qwen_erp_ec_7i_d_execution_ready_setup_architecture_2026-05-21.md",
    "impl_factory/00_governance/current_docs/qwen_erp_ec_7i_e_setup_support_harness_plan_2026-05-21.md",
    "impl_factory/00_governance/current_docs/qwen_erp_ec_7i_f_passive_setup_support_harness_2026-05-21.md",
    "impl_factory/00_governance/current_docs/qwen_erp_ec_7i_f_a_passive_harness_safety_fixes_2026-05-21.md",
    "impl_factory/00_governance/current_docs/qwen_erp_ec_7i_f_b_dataset_validator_edge_case_fix_2026-05-21.md",
    "impl_factory/00_governance/current_docs/qwen_erp_ec_7i_g_passive_environment_readiness_helper_2026-05-21.md",
    "impl_factory/00_governance/current_docs/qwen_erp_ec_7i_g_a_readiness_helper_hardening_2026-05-22.md",
    "impl_factory/00_governance/current_docs/qwen_erp_ec_7i_g_b_strong_bench_evidence_fix_2026-05-22.md",
    "impl_factory/00_governance/current_docs/qwen_erp_ec_7i_g_c_safe_site_name_validation_fix_2026-05-22.md",
    "impl_factory/00_governance/current_docs/qwen_erp_ec_7i_g_d_site_config_validation_fix_2026-05-22.md",
    "impl_factory/00_governance/current_docs/qwen_erp_ec_7j_a_packaging_readiness_baseline_2026-05-22.md",
    "impl_factory/00_governance/current_docs/qwen_erp_ec_7j_b_packaging_boundary_plan_2026-05-22.md",
}
staged = set(
    line.strip()
    for line in subprocess.check_output(["git", "diff", "--cached", "--name-only"], text=True).splitlines()
    if line.strip()
)
print("STAGED_COUNT=", len(staged))
print("MISSING=", sorted(approved - staged))
print("EXTRA=", sorted(staged - approved))
raise SystemExit(0 if staged == approved else 1)
PY
```

## Excluded-Stream And Artifact Warning Scans

These scans are secondary warnings. A match is not automatically a failure if the file is in the approved include list and uses the term only in validation/report context. Any match outside the approved include list is a blocker.

```bash
git diff --cached --name-only | grep -E 'erp_workspace_ui|02_seed_data|dummy_data|tmp/|\.codex_tmp|primeaxis|generated/qwen_s7_browser_batch' || true
git diff --cached --name-only | grep -E '\.json$|\.jsonl$|\.log$|\.csv$|raw_trace|live_trace_raw|unredacted|site_config\.json|secret|password|token|archive/' || true
```

Expected:

- No ERP UI / seed / temp / probe / cache / PrimeAxis / S7 generated scratch files.
- No staged `.json`, `.jsonl`, `.log`, `.csv`, raw-trace, live-trace-raw, unredacted trace, actual `site_config.json`, secret, password, token, or archive content files.
- It is acceptable for approved validation scripts and governance reports to contain terms such as `archive`, `site_config`, `raw trace`, or `password` as policy/test text.

## Direct Assistant Append Scan

```bash
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 - <<'PY'
from ai_assistant_ui.qwen_chat.final_answer_emission_dry_run import build_final_answer_emission_dry_run_report
from ai_assistant_ui.qwen_chat.strict_readiness_soft_gate import raw_assistant_append_scan

report = build_final_answer_emission_dry_run_report(reviewer="ec7j_staged_index_review")
print("ACTIVE_RUNTIME_DIRECT_ASSISTANT_APPEND_COUNT=", report.get("active_runtime_direct_assistant_append_count"))
print("INVENTORY_COUNT=", report.get("inventory_count"))
print("MIGRATED_AUTHORIZED_PATHS_LENGTH=", len(report.get("migrated_authorized_paths") or []))
print("FORMAL_RAW_SCAN=", [(row["relative_file_path"], row["line"]) for row in raw_assistant_append_scan(root_path=".")])
PY
```

Expected:

- `ACTIVE_RUNTIME_DIRECT_ASSISTANT_APPEND_COUNT=0`
- `INVENTORY_COUNT=1`
- `MIGRATED_AUTHORIZED_PATHS_LENGTH=27`
- Formal raw scan only:
  - `authorized_emission.py:271`
  - `authorized_emission.py:327`

## Protocol / Harness Test Command

```bash
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m unittest -q \
  ai_assistant_ui.tests.test_live_trace_evidence_protocol \
  ai_assistant_ui.tests.test_ec7i_setup_support_harnesses
```

Expected: 36 passed.

## Compile / Diff Checks

```bash
python3 -m py_compile \
  scripts/validate_ec7h_synthetic_dataset.py \
  scripts/check_ec7h_archive_readiness.py \
  scripts/check_ec7h_environment_readiness.py \
  impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/live_trace_evidence_protocol.py \
  impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_live_trace_evidence_protocol.py \
  impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_ec7i_setup_support_harnesses.py

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
```

## Guardrail And Service Import

```bash
python3 scripts/check_qwen_enterprise_guardrails.py
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 - <<'PY'
import sys, types
fake_frappe = types.ModuleType("frappe")
fake_frappe.get_all = lambda *args, **kwargs: []
fake_frappe.get_doc = lambda *args, **kwargs: None
fake_frappe.get_meta = lambda *args, **kwargs: types.SimpleNamespace(fields=[])
fake_frappe.get_traceback = lambda: ""
fake_frappe.log_error = lambda *args, **kwargs: None
fake_frappe.throw = lambda *args, **kwargs: (_ for _ in ()).throw(Exception(args[0] if args else "frappe.throw"))
fake_frappe.conf = {}
fake_frappe.local = types.SimpleNamespace(site="")
fake_frappe.session = types.SimpleNamespace(user="Administrator")
fake_frappe.db = types.SimpleNamespace(exists=lambda *a, **k: False, get_value=lambda *a, **k: None, get_all=lambda *a, **k: [], sql=lambda *a, **k: [], count=lambda *a, **k: 0)
fake_frappe.DoesNotExistError = type("DoesNotExistError", (Exception,), {})
fake_frappe.ValidationError = type("ValidationError", (Exception,), {})
sys.modules["frappe"] = fake_frappe
import ai_assistant_ui.qwen_chat.service
print("FAKE_FRAPPE_SERVICE_IMPORT=PASS")
PY
```

## Current Verification

EC-7J-C current-state verification reproduced:

- Staged files: 0
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

## Final Decision

`ec_7j_c_staged_index_construction_request_ready_for_counterpart_qa_owner_review`

## Next Step

If Counterpart/QA/Owner approve EC-7J-C, proceed to EC-7J-D staged-index package construction using only the exact `git add -- <28 files>` procedure above. No commit or push should happen during EC-7J-D.
