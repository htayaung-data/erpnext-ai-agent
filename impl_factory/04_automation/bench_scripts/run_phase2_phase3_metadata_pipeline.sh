#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT_DIR"

python3 scripts/check_v7_contract_guardrails.py --root .

python3 impl_factory/04_automation/bench_scripts/phase2_capability_platform_refresh.py

python3 impl_factory/04_automation/bench_scripts/phase2_validate_capability_platform.py \
  --path impl_factory/04_automation/capability_v7/latest_capability_platform.json

python3 impl_factory/04_automation/bench_scripts/phase3_contract_overrides_refresh.py \
  --input-json impl_factory/04_automation/capability_v7/latest_capability_platform.json \
  --out-json impl_factory/04_automation/capability_v7/latest_contract_overrides.json

python3 impl_factory/04_automation/bench_scripts/phase3_validate_contract_overrides.py \
  --capability-json impl_factory/04_automation/capability_v7/latest_capability_platform.json \
  --overrides-json impl_factory/04_automation/capability_v7/latest_contract_overrides.json \
  --base-clarification-json impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/contracts_data/clarification_contract_v1.json

python3 -m unittest \
  impl_factory/04_automation/bench_scripts/test_v7_constraint_engine.py \
  impl_factory/04_automation/bench_scripts/test_v7_semantic_resolver_constraints.py \
  impl_factory/04_automation/bench_scripts/test_v7_contract_registry.py \
  impl_factory/04_automation/bench_scripts/test_phase3_contract_overrides_refresh.py \
  impl_factory/04_automation/bench_scripts/test_phase3_validate_contract_overrides.py

echo "Phase2+Phase3 metadata pipeline: PASS"
