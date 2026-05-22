# EC-7I-F Passive Setup-Support Harness Implementation

Decision: ec_7i_f_passive_setup_support_harness_ready_for_counterpart_qa_review

Date: 2026-05-21
Generated: 2026-05-21T14:20:00+00:00
Base: `main` post-PR #4 verification worktree
Head: `1504158`
Runtime effect: `none`
Strict enforcement enabled: `false`
Live trace collection performed: `false`
Environment setup performed: `false`
Site/user/dataset/archive creation performed: `false`
Dataset seeding performed: `false`
Archive activation performed: `false`
Production deployment performed: `false`
Staging/commit/push performed: `false`

## Purpose

EC-7I-F implements the first two passive setup-support harnesses approved by Owner/Counterpart:

- `scripts/validate_ec7h_synthetic_dataset.py`
- `scripts/check_ec7h_archive_readiness.py`

Both scripts are evidence validators only. They do not connect to Frappe, do not read or write a database, do not seed records, do not create archives, do not collect traces, and do not change runtime behavior.

## Files Added

| File | Purpose |
|---|---|
| `scripts/validate_ec7h_synthetic_dataset.py` | Validates the EC-7H synthetic dataset manifest and emits a pass/fail JSON report. |
| `scripts/check_ec7h_archive_readiness.py` | Verifies raw trace archive readiness and emits a pass/fail JSON report. |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_ec7i_setup_support_harnesses.py` | Focused unit tests for both passive harness scripts. |
| `impl_factory/00_governance/current_docs/qwen_erp_ec_7i_f_passive_setup_support_harness_2026-05-21.md` | EC-7I-F governance report. |

## Synthetic Dataset Validator

Script:

`scripts/validate_ec7h_synthetic_dataset.py`

Behavior:

- requires `dataset_id == "EC7H_LIGHT_SEMANTIC_SYNTHETIC_SET_001"`;
- requires `data_classification == "synthetic_only"`;
- validates required manifest and scenario fields;
- validates lane coverage for the five light-semantic lanes;
- validates allowed scenario types;
- requires synthetic markers in prompt or record reference;
- rejects raw business/customer/vendor/supplier/entity/invoice-like identifiers;
- prints JSON pass/fail output;
- exits `0` only when valid;
- exits nonzero when invalid;
- does not import Frappe;
- does not connect to any DB;
- does not seed records.

Required lanes:

- `frontdoor_semantic_classification`
- `fresh_query_interpretation`
- `followup_interpretation`
- `semantic_reasoning_activation`
- `semantic_repair_intent`

Allowed scenario types:

- `accepted_success`
- `degraded_low_confidence`
- `runtime_error_fallback`
- `missing_metadata`
- `not_applicable`
- `rejected`

Command shape:

```bash
python3 scripts/validate_ec7h_synthetic_dataset.py \
  /path/to/EC7H_LIGHT_SEMANTIC_SYNTHETIC_SET_001.json
```

## Archive Readiness Checker

Script:

`scripts/check_ec7h_archive_readiness.py`

Behavior:

- verifies archive path exists and is a directory;
- verifies path is outside the provided repo root;
- verifies owner/group when expected values are provided;
- verifies permissions are no broader than the requested maximum mode, default `750`;
- verifies optional retention marker file when specified;
- verifies no `.git` directory exists inside the archive path;
- prints JSON pass/fail output;
- exits `0` only when valid;
- exits nonzero when invalid;
- writes no raw traces;
- creates no directories;
- changes no permissions.

Command shape:

```bash
python3 scripts/check_ec7h_archive_readiness.py \
  --path /home/deploy/erp-projects/_cleanup_archives/ec7h_live_trace_raw_20260521 \
  --expected-owner TBD_OWNER_APPROVED_USER \
  --expected-group TBD_QA_OWNER_GROUP \
  --max-mode 750 \
  --retention-marker RETENTION.md \
  --repo-root /tmp/erpai_pr4_postmerge_verify
```

## Focused Test Coverage

New focused tests cover:

- valid synthetic manifest passes;
- wrong dataset name fails;
- missing lane coverage fails;
- raw business identifiers such as `Yoma Bank` and `SINV-0001` fail;
- dataset CLI emits pass/fail output without DB access;
- external restricted archive directory passes;
- missing archive path fails;
- archive path inside repo fails;
- overly broad permissions fail;
- missing retention marker fails.

Test command:

```bash
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m unittest -q \
  ai_assistant_ui.tests.test_ec7i_setup_support_harnesses
```

Expected result: `7 passed`.

## Non-Goals Preserved

- `no_site_creation`
- `no_user_creation`
- `no_dataset_seeding`
- `no_archive_activation`
- `no_live_trace_collection`
- `no_deployment`
- `no_instrumentation`
- `no_runtime_behavior_change`
- `no_strict_enforcement`
- `no_staging_commit_push`
- `no_cleanup`
- `no_ux_filter_mi_family_expansion`

## Verification Results

EC-7I-F verification reproduced:

- Guardrail: PASS
- Fake-Frappe service import: PASS
- Direct assistant inventory: `0 / 1 / 27`
- Formal raw append scan: `authorized_emission.py:271`, `authorized_emission.py:327`
- EC-7H-B protocol tests: `17 passed`
- EC-7I-F harness tests: `7 passed`
- Combined protocol/harness command: `24 passed`
- Python compile: PASS
- Scoped diff check: PASS
- Excluded status scan: clean
- Staged files: `0`

## Final Recommendation

`ec_7i_f_passive_setup_support_harness_ready_for_counterpart_qa_review`

If accepted, the next slice should remain narrow: either implement the passive environment readiness helper or request owner decisions for the manual QA-user/environment setup path. Environment setup and live trace collection remain paused.
