#!/usr/bin/env bash
set -euo pipefail

# Enterprise batch runner:
# - Executes manifest replay in suite chunks (better failure isolation).
# - Produces combined first-run score + strict phase8 gate.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT_DIR"

MANIFEST="${1:-impl_factory/04_automation/replay_v7_expanded/manifest.json}"
STAGE="${2:-10}"
MIN_FIRST_RUN_SAMPLE="${MIN_FIRST_RUN_SAMPLE:-300}"
MIN_TARGET_CLASS_SAMPLE="${MIN_TARGET_CLASS_SAMPLE:-20}"

SUITES=(
  "core_read"
  "multiturn_context"
  "transform_followup"
  "no_data_unsupported"
  "write_safety"
)

RAW_ARGS=()

for SUITE in "${SUITES[@]}"; do
  echo "==> Running suite: ${SUITE}"
  OUT="$(python3 impl_factory/04_automation/bench_scripts/run_phase6_manifest_uat.py --manifest "$MANIFEST" --suite "$SUITE")"
  echo "$OUT"
  RAW_PATH="$(echo "$OUT" | awk -F= '/^OUT=/{print $2}' | tail -n1)"
  if [[ -z "${RAW_PATH}" ]]; then
    echo "ERROR: could not detect OUT= path for suite ${SUITE}" >&2
    exit 1
  fi
  RAW_ARGS+=(--raw "$RAW_PATH")
done

echo "==> Running first-run score across suite artifacts"
python3 impl_factory/04_automation/bench_scripts/phase1_first_run_score.py \
  "${RAW_ARGS[@]}" \
  --manifest "$MANIFEST" \
  --label "phase6_manifest_full"

echo "==> Running strict phase8 release gate"
python3 impl_factory/04_automation/bench_scripts/phase8_release_gate.py \
  "${RAW_ARGS[@]}" \
  --stage "$STAGE" \
  --manifest "$MANIFEST" \
  --min-first-run-sample-size "$MIN_FIRST_RUN_SAMPLE" \
  --min-target-class-sample-size "$MIN_TARGET_CLASS_SAMPLE" \
  --label "phase6_manifest_full"

echo "DONE: manifest full replay + strict gate completed."
