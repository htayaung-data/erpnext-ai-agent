# EC-7I-G-C Safe Site Name Validation Fix

Decision target: `ec_7i_g_c_safe_site_name_validation_fix_ready_for_counterpart_qa_review`

## Scope

EC-7I-G-C is passive readiness-helper hardening only. It does not create a site, user, dataset, archive, or live trace. It does not deploy, instrument runtime, enable strict enforcement, stage files, commit, or push.

## Worktree

- Worktree: `/tmp/erpai_pr4_postmerge_verify`
- HEAD: `1504158`
- Runtime effect: none
- Staged files: 0

## Fix Summary

`scripts/check_ec7h_environment_readiness.py` now validates `site_name` before using it to build `bench / "sites" / site_name`.

The readiness helper now rejects:

- empty `site_name`
- `.`
- `..`
- path separators `/` and `\`
- path traversal or normalized paths outside `bench/sites`
- site names outside the strict allowed form: alphanumeric parts separated by `.`, with `_` and `-` allowed inside each non-empty part
- empty `sites/{site_name}` directories without `site_config.json`

Strong controlled-bench evidence now requires:

- `sites/`
- `apps/`
- valid non-traversing `site_name`
- `sites/{site_name}/site_config.json`
- no source-checkout markers

## Tests Added

Focused adversarial tests cover:

- `site_name="."`
- `site_name=".."`
- `site_name="../apps"`
- `site_name="foo/bar"`
- `site_name="foo\\bar"`
- empty `site_name`
- empty `sites/{site_name}` directory without `site_config.json`

The existing positive synthetic readiness case uses:

- `apps/`
- `sites/`
- valid `site_name="ec7h-test.local"`
- `sites/ec7h-test.local/site_config.json`

## Verification

EC-7I-G-C verification reproduced:

- Guardrail: PASS
- Fake-Frappe service import: PASS
- EC-7H-B protocol + EC-7I harness tests: PASS
- Site-name adversarial probes: PASS
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

`ec_7i_g_c_safe_site_name_validation_fix_ready_for_counterpart_qa_review`
