# EC-7I-G-D Site Config Validation Fix

Decision target: `ec_7i_g_d_site_config_validation_fix_ready_for_counterpart_qa_review`

## Scope

EC-7I-G-D is passive readiness-helper hardening only. It does not create a site, user, dataset, archive, or live trace. It does not deploy, instrument runtime, enable strict enforcement, stage files, commit, or push.

## Worktree

- Worktree: `/tmp/erpai_pr4_postmerge_verify`
- HEAD: `1504158`
- Runtime effect: none
- Staged files: 0

## Fix Summary

`scripts/check_ec7h_environment_readiness.py` now validates `sites/{site_name}/site_config.json` before treating it as controlled site evidence.

The readiness helper now rejects:

- missing `site_config.json`
- symlinked `site_config.json`
- empty `site_config.json`
- invalid JSON
- JSON values that are not objects
- JSON objects with no expected Frappe-like config key

The current expected Frappe-like keys include:

- `db_name`
- `db_password`
- `db_type`
- `db_host`
- `db_port`
- `developer_mode`
- `encryption_key`
- `redis_cache`
- `redis_queue`
- `redis_socketio`
- `socketio_port`

Strong controlled-bench evidence now requires:

- `sites/`
- `apps/`
- valid non-traversing `site_name`
- non-symlink `sites/{site_name}/site_config.json`
- valid JSON object with at least one expected Frappe-like config key
- no source-checkout markers

## Tests Added

Focused adversarial tests cover:

- empty `site_config.json`
- `site_config.json` containing `not json`
- `site_config.json` containing `[]`
- symlinked `site_config.json`
- JSON object with no expected Frappe config keys

The positive synthetic readiness case uses:

- `apps/`
- `sites/`
- valid `site_name="ec7h-test.local"`
- non-symlink `sites/ec7h-test.local/site_config.json`
- valid JSON object containing `db_name`

## Verification

EC-7I-G-D verification reproduced:

- Guardrail: PASS
- Fake-Frappe service import: PASS
- EC-7H-B protocol + EC-7I harness tests: PASS
- Site-config adversarial probes: PASS
- Direct assistant inventory: `0 / 1 / 27`
- Formal raw append scan:
  - `authorized_emission.py:271`
  - `authorized_emission.py:327`
- Python compile: PASS
- Scoped diff check: PASS
- Excluded status scan: clean
- Staged files: `0`

## Boundary

This remains passive readiness-helper hardening only. EC-7H live trace collection remains blocked until a real controlled non-production bench/site, QA user, synthetic dataset, archive custody, and redacted output policy are owner/QA approved.

## Final Decision

`ec_7i_g_d_site_config_validation_fix_ready_for_counterpart_qa_review`
