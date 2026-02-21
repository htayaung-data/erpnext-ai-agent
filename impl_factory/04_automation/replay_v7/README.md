# V7 Replay Packs (Phase 1 Baseline)

This folder contains deterministic, machine-readable golden replay packs for first-run scoring.

## File format
Each `*.jsonl` file contains one case per line:

```json
{
  "case_id": "CR-001",
  "suite": "core_read",
  "role": "ai.reader",
  "turns": [{"role": "user", "text": "Top 5 customers by revenue last month"}],
  "expected": {
    "intent": "READ",
    "task_type": "ranking",
    "metric": "revenue",
    "group_by": ["customer"],
    "output_mode": "top_n",
    "top_n": 5,
    "time_scope": "last_month"
  },
  "tags": ["sales", "ranking", "first_run"]
}
```

## Packs
- `core_read.jsonl`: single-turn read reliability baseline.
- `multiturn_context.jsonl`: 3-turn and 4-turn context/reference chains.
- `transform_followup.jsonl`: transform-last stability and idempotency.
- `no_data_unsupported.jsonl`: unsupported and no-data envelope behavior.
- `write_safety.jsonl`: write safety expectations (disabled or confirm-gated).

## Scoring
Use `impl_factory/04_automation/bench_scripts/phase1_first_run_score.py` with raw replay result artifacts.

Example:

```bash
python3 impl_factory/04_automation/bench_scripts/phase1_first_run_score.py \
  --raw impl_factory/04_automation/logs/20260221T000000Z_replay_raw.json \
  --label phase1_baseline
```

Output artifacts are written to `impl_factory/04_automation/logs/`.
