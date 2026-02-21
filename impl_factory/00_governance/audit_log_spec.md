# Audit Log Spec (Implementation Factory)

Every deterministic change must produce an artifact in repo.

## Required artifacts per step
- Input: CSVs / YAML config / FAC payload JSON
- Execution: command used + timestamp
- Output: logs or exported snapshot

## Storage convention
- CSVs: impl_factory/02_seed_data/
- Config maps: impl_factory/03_config/
- Scripts: impl_factory/04_automation/bench_scripts/
- FAC payloads: impl_factory/04_automation/fac_payloads/
- Logs: impl_factory/04_automation/logs/<YYYY-MM-DD>_<step>_<purpose>.log

## Rules
- No silent changes
- No manual UI steps unless explicitly documented
