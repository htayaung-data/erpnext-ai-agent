#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
LOG_DIR="${ROOT_DIR}/impl_factory/04_automation/logs"
TS="$(date -u +%Y%m%dT%H%M%SZ)"

mkdir -p "${LOG_DIR}"

COMPILE_LOG="${LOG_DIR}/${TS}_step11_compile.log"
TEST_LOG="${LOG_DIR}/${TS}_step11_contract_tests.log"
SUMMARY_LOG="${LOG_DIR}/${TS}_step11_regression_summary.md"

cd "${ROOT_DIR}"

echo "[Step11] Running compile check..."
{
  echo "[Step11] Command: python -m compileall -q apps/ai_assistant_ui/ai_assistant_ui"
  docker compose exec backend bash -lc \
    "cd /home/frappe/frappe-bench && ./env/bin/python -m compileall -q apps/ai_assistant_ui/ai_assistant_ui"
  echo "[Step11] Compile check: PASS"
} 2>&1 | tee "${COMPILE_LOG}"

echo "[Step11] Running contract regression module..."
{
  echo "[Step11] Command: python -m unittest apps.ai_assistant_ui.ai_assistant_ui.tests.test_planner_contract -v"
  docker compose exec backend bash -lc \
    "cd /home/frappe/frappe-bench && ./env/bin/python -m unittest apps.ai_assistant_ui.ai_assistant_ui.tests.test_planner_contract -v"
  echo "[Step11] Contract regression: PASS"
} 2>&1 | tee "${TEST_LOG}"

cat > "${SUMMARY_LOG}" <<EOF
# Step 11 Regression Summary

Timestamp (UTC): ${TS}

## Commands
1. \`docker compose exec backend bash -lc 'cd /home/frappe/frappe-bench && ./env/bin/python -m compileall -q apps/ai_assistant_ui/ai_assistant_ui'\`
2. \`docker compose exec backend bash -lc 'cd /home/frappe/frappe-bench && ./env/bin/python -m unittest apps.ai_assistant_ui.ai_assistant_ui.tests.test_planner_contract -v'\`

## Artifacts
1. Compile log: \`${COMPILE_LOG}\`
2. Test log: \`${TEST_LOG}\`

## Result
PASS
EOF

echo "[Step11] Done. Summary: ${SUMMARY_LOG}"
