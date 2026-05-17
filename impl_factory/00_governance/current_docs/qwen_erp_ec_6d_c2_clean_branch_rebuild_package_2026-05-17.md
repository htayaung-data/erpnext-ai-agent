# EC-6D-C2 Clean Branch Rebuild Package

## Decision Context

This report documents the EC-6D-C2 clean-branch rebuild package prepared for Counterpart and QA_Risk Auditor review.

- Branch: `feature/ai-assistant-stabilization-clean-c2-rebuild`
- Base: `origin/main` / `e5ea52c`
- Candidate mode: staged index only
- PR #2 status: rejected and superseded because its branch diff includes old polluted history
- Commit status: not committed
- Push status: not pushed

## Package Boundary

- Staged file count before this report: `246`
- Staged generated evidence count before this report: `16`
- Expected staged file count after this report: `247`
- ERP UI staged: `no`
- Seed/data staged: `no`
- Temp/probe/cache staged: `no`
- PrimeAxis owner-decision docs staged: `no`
- Broad-excluded AI files staged: `no`
- `fresh_query_interpreter.py` staged: `no`

Excluded broad AI paths remain out of this package unless separately approved:

- `assistant_formatting.py`
- `context/grounded_context.py`
- `followup_interpreter.py`
- `fresh_query_interpreter.py`
- `scope_support.py`

## Authority Scans

Cached direct assistant append scan is expected to show only the centralized authorized emission helper sinks:

- `authorized_emission.py:271`
- `authorized_emission.py:327`

Source scan result from EC-6D-C2 rebuild:

- `active_runtime_direct_assistant_append_count=0`
- `inventory_count=1`
- `migrated_authorized_paths_length=27`

## Verification Summary

EC-6D-C2 verification before adding this report:

- Guardrail: `PASS`
- Final authority/emission: `47 passed`
- Visible-context suite: `78 passed`
- NBU discovery suite: `153 passed`
- Manual UAT suite: `170 passed`
- Narrow semantic runtime-gate authority test: `1 passed`
- Python compile: `PASS`
- Cached/worktree diff checks: `PASS`

## Excluded Generated Files

The following generated files remain unstaged and excluded from the clean package:

- `impl_factory/00_governance/current_docs/generated/qwen_s7_browser_batch_cli_report.json`
- `impl_factory/00_governance/current_docs/generated/qwen_s7_browser_batch_cli_report.md`
- `impl_factory/00_governance/current_docs/generated/qwen_s7_browser_batch_resilience_runner_contract.json`
- `impl_factory/00_governance/current_docs/generated/qwen_s7_browser_batch_resilience_runner_contract.md`

## Important Limitation

The narrowed `test_semantic_financial_resolution.py` is a clean PR packaging gate only. It proves the EC runtime-gate authorized-boundary behavior without staging broad excluded fresh-query changes. It is not full semantic-financial regression coverage.

## Final Recommendation

If post-report cached boundary checks and narrow verification gates remain green, this staged package is ready for Counterpart and QA_Risk Auditor final commit approval.
