#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT_DIR"

python3 scripts/check_v7_contract_guardrails.py --root .
python3 impl_factory/04_automation/bench_scripts/phase1_validate_replay_packs.py \
  --manifest impl_factory/04_automation/replay_v7/manifest.json

TMP_LOG="$(mktemp)"
trap 'rm -f "$TMP_LOG"' EXIT

python3 impl_factory/04_automation/bench_scripts/run_phase6_canary_uat.py | tee "$TMP_LOG"
RAW_PATH="$(awk -F= '/^OUT=/{print $2}' "$TMP_LOG" | tail -n1)"

if [[ -z "$RAW_PATH" ]]; then
  echo "ERROR: unable to detect raw artifact path from run_phase6_canary_uat.py output" >&2
  exit 1
fi

python3 impl_factory/04_automation/bench_scripts/phase1_first_run_score.py \
  --raw "$RAW_PATH" \
  --manifest impl_factory/04_automation/replay_v7/manifest.json \
  --label "phase1_baseline"
