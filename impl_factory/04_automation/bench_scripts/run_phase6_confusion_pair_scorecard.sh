#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/deploy/erp-projects/erpai_project1"
cd "$ROOT"

BASELINE_PATH="${1:-}"
CURRENT_PATH="${2:-}"

if [[ -z "$BASELINE_PATH" ]]; then
  BASELINE_PATH="$(ls -1t impl_factory/04_automation/logs/*phase1_first_run_baseline.json 2>/dev/null | head -n 1 || true)"
fi
if [[ -z "$CURRENT_PATH" ]]; then
  CURRENT_PATH="$(ls -1t impl_factory/04_automation/logs/*phase6_canary_uat_raw_v3.json 2>/dev/null | head -n 1 || true)"
fi

if [[ -z "$BASELINE_PATH" || ! -f "$BASELINE_PATH" ]]; then
  echo "ERROR: baseline artifact not found. Provide as arg1 or generate phase1 baseline first." >&2
  exit 2
fi
if [[ -z "$CURRENT_PATH" || ! -f "$CURRENT_PATH" ]]; then
  echo "ERROR: current phase6 raw artifact not found. Provide as arg2 or run phase6 canary first." >&2
  exit 2
fi

python3 impl_factory/04_automation/bench_scripts/phase6_confusion_pair_scorecard.py \
  --baseline "$BASELINE_PATH" \
  --current "$CURRENT_PATH"
