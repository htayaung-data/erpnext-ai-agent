# EC-7I-D Execution-Ready Setup Architecture

Decision: ec_7i_d_blocked_setup_commands_not_execution_ready

Date: 2026-05-21
Generated: 2026-05-21T09:05:00+00:00
Base: `main` post-PR #4 verification worktree
Head: `1504158`
Runtime effect: `none`
Strict enforcement enabled: `false`
Live trace collection performed: `false`
Environment setup performed: `false`
Site/user/dataset/archive creation performed: `false`
Production deployment performed: `false`
Staging/commit/push performed: `false`

## Purpose

EC-7I-C was accepted as a high-level setup plan, but execution was not approved because several command/spec gaps remained. EC-7I-D attempts to make the setup architecture execution-ready. It remains report-only and performs no setup actions.

## Execution-Readiness Verdict

EC-7I-D is not execution-ready yet.

Blocking reasons:

- `ai_assistant_ui.qwen_chat.service.ping_runtime_metadata_readiness` does not exist and must be replaced.
- `scripts/validate_ec7h_synthetic_dataset.py` does not exist and must be created later or replaced with an existing validation path.
- `ai_assistant_ui.qwen_chat.live_trace_collection` does not exist; live trace collection commands must not reference it until separately designed.
- exact Frappe/ERPNext app sources for bench installation are not specified.
- site admin/password handling is not specified.
- QA user creation is command-shaped but not role-complete or secret-safe.
- archive owner/group/custodian and retention policy remain owner decisions.

Therefore EC-7I-D closes as `ec_7i_d_blocked_setup_commands_not_execution_ready`.

## Source Verification

Source scan results:

| Symbol / script | Result |
|---|---|
| `ping_runtime_metadata_readiness` | Not found. |
| `validate_ec7h_synthetic_dataset` | Not found. |
| `live_trace_collection` | Not found. |
| Existing dataset validation script | Only generic `scripts/validate_seed_csvs.py` found; not suitable for EC-7H synthetic manifest validation. |
| App metadata | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/pyproject.toml` and `ai_assistant_ui/hooks.py` exist. |

## Replacements For Fictional Commands

### Runtime Readiness

Remove `ping_runtime_metadata_readiness` from executable setup instructions.

Use existing import and inventory checks until a tiny readiness helper is separately approved:

```bash
cd /tmp/erpai_pr4_postmerge_verify

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

Future bench/site verification can use:

```bash
cd TBD_CONTROLLED_BENCH_PATH
bench --site TBD_SITE_NAME execute frappe.get_installed_apps
bench --site TBD_SITE_NAME execute frappe.db.exists --args '["User", "qa_ec7h_trace_user@example.invalid"]'
```

If a runtime metadata readiness endpoint is still desired, it must be proposed as a separate tiny helper/harness slice before execution.

### Synthetic Dataset Validation

No existing EC-7H-specific dataset validator exists.

Execution-ready options:

1. Add a tiny `scripts/validate_ec7h_synthetic_dataset.py` in a later owner-approved setup-support slice.
2. Use a one-off Python validation command embedded in the future setup slice, reviewed before execution.

Recommended future validator requirements:

- parse JSON manifest;
- require `dataset_id == "EC7H_LIGHT_SEMANTIC_SYNTHETIC_SET_001"`;
- require `data_classification == "synthetic_only"`;
- require lane coverage for the five light-semantic lanes;
- reject production-like forbidden strings;
- require expected metadata/redaction fields per scenario;
- emit deterministic PASS/FAIL summary.

EC-7I-D does not create this validator.

## Exact App / Source Path Requirements

Current source checkout path:

`/tmp/erpai_pr4_postmerge_verify`

AI Assistant app source in that checkout:

`/tmp/erpai_pr4_postmerge_verify/impl_factory/05_custom_logic/custom_app/ai_assistant_ui`

Execution-ready app-source decision still needed:

| App | Required source decision |
|---|---|
| Frappe | Existing bench-managed baseline or explicit source/version. |
| ERPNext | Existing bench-managed baseline or explicit source/version. |
| `ai_assistant_ui` | Owner-approved source path or git URL/tag/commit. Recommended local source path is the accepted main checkout app path above, but install procedure must be verified against bench conventions. |

Do not use broad old feature branches or unreviewed PR #2 history.

## Secret / Password Handling

Execution must not expose secrets in repo, shell history, governance docs, or command logs.

Recommended policy:

- site admin password supplied interactively or via an owner-controlled secret file outside repo;
- QA user password reset via Frappe UI or one-time secret outside repo;
- no passwords in JSON manifests;
- no passwords in governance reports;
- no secrets under `/tmp/erpai_pr4_postmerge_verify`;
- if environment variables are used, they must be set only in the execution shell and not printed.

Future setup commands should use placeholders such as `TBD_SECRET_SOURCE` and require owner-provided secret handling before execution.

## QA User Creation Method

Preferred user identity:

- email/login: `qa_ec7h_trace_user@example.invalid`
- display name: `QA EC7H Trace`

Recommended creation path: manual UI or bench console under owner/QA supervision, not a raw command with secrets.

If bench command is approved later, use a reviewed Python method that creates and saves the user, then assigns only owner-approved roles. Example shape, not approved for execution:

```bash
bench --site TBD_SITE_NAME execute path.to.owner_approved_setup_helper.create_ec7h_qa_user
```

Open blocker: no setup helper currently exists. A future EC-7I-E setup-support slice may need to add a tiny helper or choose manual UI creation.

Roles must be chosen by owner/QA based on the synthetic scenario requirements. EC-7I-D does not assume Administrator role.

## Synthetic Dataset Manifest

Recommended manifest path outside repo for controlled site setup:

`/home/deploy/erp-projects/ec7h_controlled_bench/ec7h_synthetic_datasets/EC7H_LIGHT_SEMANTIC_SYNTHETIC_SET_001.json`

Optional repo candidate path after owner/QA approval:

`impl_factory/00_governance/current_docs/generated/ec_7i_synthetic_datasets/EC7H_LIGHT_SEMANTIC_SYNTHETIC_SET_001.json`

Manifest format:

```json
{
  "dataset_id": "EC7H_LIGHT_SEMANTIC_SYNTHETIC_SET_001",
  "data_classification": "synthetic_only",
  "schema_version": "1",
  "qa_owner": "TBD_QA_OWNER",
  "scenarios": [
    {
      "scenario_id": "ec7h_frontdoor_success_001",
      "lane_id": "frontdoor_semantic_classification",
      "scenario_type": "accepted_success",
      "synthetic_prompt": "Classify this synthetic ERP request: show the dashboard for EC7H Synthetic Customer Alpha.",
      "synthetic_record_reference": "EC7H_SYNTH_CUSTOMER_ALPHA",
      "expected_metadata_status": "covered",
      "expected_strict_readiness_status": "strict_ready",
      "expected_fallback_used": false,
      "expected_fallback_reason": "",
      "expected_authority_status": "not_applicable",
      "redaction_expectation": "no_raw_sensitive_values"
    }
  ]
}
```

Sample synthetic records:

| Synthetic id | Type | Notes |
|---|---|---|
| `EC7H_SYNTH_CUSTOMER_ALPHA` | Customer-like synthetic fixture | Must not map to real customer. |
| `EC7H_SYNTH_VENDOR_BETA` | Vendor-like synthetic fixture | Must not map to real vendor. |
| `EC7H_SYNTH_SALES_INVOICE_001` | Invoice-like synthetic fixture | Synthetic only, no real invoice number. |
| `EC7H_SYNTH_LOW_CONFIDENCE_PROMPT_001` | Prompt fixture | Designed to produce degraded semantic status if safely triggerable. |

Open blocker: manifest is not created and validator is not available.

## Archive Owner / Group / Permissions

Proposed raw archive path:

`/home/deploy/erp-projects/_cleanup_archives/ec7h_live_trace_raw_20260521/`

Required policy:

- owner: `TBD_OWNER_APPROVED_USER`
- group: `TBD_QA_OWNER_GROUP`
- mode: `750` or stricter
- raw trace custodian: `TBD_QA_OR_OWNER_CUSTODIAN`
- retention: `TBD_RETENTION_PERIOD`

Proposed activation commands for future approval:

```bash
mkdir -p /home/deploy/erp-projects/_cleanup_archives/ec7h_live_trace_raw_20260521
chown TBD_OWNER_APPROVED_USER:TBD_QA_OWNER_GROUP /home/deploy/erp-projects/_cleanup_archives/ec7h_live_trace_raw_20260521
chmod 750 /home/deploy/erp-projects/_cleanup_archives/ec7h_live_trace_raw_20260521
```

Open blocker: owner/group/custodian/retention values are not provided.

## Cleanup / Rollback Commands

Cleanup commands are not approved for EC-7I-D execution. Future setup must include owner-reviewed rollback:

```bash
# Disable QA user after trace window if required.
bench --site TBD_SITE_NAME set-user-password qa_ec7h_trace_user@example.invalid TBD_ROTATED_SECRET
bench --site TBD_SITE_NAME execute frappe.db.set_value --args '["User", "qa_ec7h_trace_user@example.invalid", "enabled", 0]'

# Remove synthetic dataset manifest outside repo if required.
rm -f /home/deploy/erp-projects/ec7h_controlled_bench/ec7h_synthetic_datasets/EC7H_LIGHT_SEMANTIC_SYNTHETIC_SET_001.json

# Raw archive cleanup only under custodian approval.
# Do not delete raw trace archives without QA/Owner retention decision.
```

Do not clean production data, ERP UI, seed/data, temp/probe/cache streams, or unrelated governance evidence inside EC-7I.

## Post-Setup Verification Commands

These are execution-ready only after missing values/helpers are resolved:

```bash
cd TBD_CONTROLLED_BENCH_PATH
bench --site TBD_SITE_NAME list-apps
bench --site TBD_SITE_NAME execute frappe.get_installed_apps
bench --site TBD_SITE_NAME execute frappe.db.exists --args '["User", "qa_ec7h_trace_user@example.invalid"]'

test -f /home/deploy/erp-projects/ec7h_controlled_bench/ec7h_synthetic_datasets/EC7H_LIGHT_SEMANTIC_SYNTHETIC_SET_001.json
test -d /home/deploy/erp-projects/_cleanup_archives/ec7h_live_trace_raw_20260521
test -w /home/deploy/erp-projects/_cleanup_archives/ec7h_live_trace_raw_20260521

python3 scripts/check_qwen_enterprise_guardrails.py
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m unittest -q \
  ai_assistant_ui.tests.test_live_trace_evidence_protocol
```

Missing before execution:

- actual bench/site;
- exact app source/install process;
- secret handling method;
- user creation method/roles;
- dataset validator or approved one-off validation command;
- archive owner/group/custodian/retention;
- safe trace collection command/harness, if collection later becomes approved.

## Passive Verification Results

EC-7I-D source/passive checks:

- `ping_runtime_metadata_readiness`: not found
- `validate_ec7h_synthetic_dataset`: not found
- `live_trace_collection`: not found
- Existing dataset validator found: `scripts/validate_seed_csvs.py` only, not suitable for EC-7H
- App metadata found: `pyproject.toml`, `ai_assistant_ui/hooks.py`
- Guardrail: PASS
- Fake-Frappe service import: PASS
- Direct assistant inventory: `0 / 1 / 27`
- Formal raw append scan: `authorized_emission.py:271`, `authorized_emission.py:327`
- EC-7H-B protocol tests: `17 passed`
- Scoped report diff check: PASS
- Excluded status scan: clean
- Staged files: `0`
- Environment setup: not performed
- Live trace collection: not performed
- Staging/commit/push: not performed

## Non-Goals

- `no_site_creation`
- `no_user_creation`
- `no_dataset_creation_or_seeding`
- `no_archive_activation`
- `no_live_trace_collection`
- `no_deployment`
- `no_instrumentation`
- `no_runtime_behavior_change`
- `no_strict_enforcement`
- `no_staging_commit_push`
- `no_cleanup`
- `no_ux_filter_mi_family_expansion`

## Final Recommendation

`ec_7i_d_blocked_setup_commands_not_execution_ready`

Do not approve setup execution yet. The next safe slice should be either:

1. EC-7I-E setup-support harness plan, to define tiny validated helpers for readiness, dataset validation, and QA user setup; or
2. owner-provided architecture decisions for app sources, secrets, roles, custodian, archive ownership, and manual UI setup path.

Only after those gaps close should EC-7I return to execution approval.
