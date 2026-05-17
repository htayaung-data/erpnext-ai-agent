#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_PYTHONPATH="impl_factory/05_custom_logic/custom_app/ai_assistant_ui"
MODE="${1:-full}"

SEMANTIC_MODULES=(
	"ai_assistant_ui.tests.test_semantic_resolution_registry"
	"ai_assistant_ui.tests.test_financial_summary_resolution_registry"
	"ai_assistant_ui.tests.test_semantic_financial_resolution"
)

POST_CONTRACT_MODULES=(
	"ai_assistant_ui.tests.test_post_contract_guard_probes"
	"ai_assistant_ui.tests.test_post_contract_state_integrity"
	"ai_assistant_ui.tests.test_post_contract_observability"
	"ai_assistant_ui.tests.test_post_contract_regression"
	"ai_assistant_ui.tests.test_post_contract_release_gates"
	"ai_assistant_ui.tests.test_post_contract_state_live"
	"ai_assistant_ui.tests.test_post_contract_observability_live"
	"ai_assistant_ui.tests.test_post_contract_adversarial"
)

usage() {
	cat <<'EOF'
Usage: scripts/qwen_verify_enterprise_matrix.sh [semantic|post-contract|full]

Modes:
  semantic       Run local semantic/registry verification only.
  post-contract  Run the container-backed post-contract verification matrix only.
  full           Run guardrails, semantic verification, and the post-contract matrix.
EOF
}

run_guardrails() {
	echo
	echo "==> Guardrail audit"
	python3 scripts/check_qwen_enterprise_guardrails.py
}

run_semantic_modules() {
	local module

	echo
	echo "==> Local semantic verification"
	for module in "${SEMANTIC_MODULES[@]}"; do
		echo "--> ${module}"
		PYTHONPATH="${APP_PYTHONPATH}" python3 -m unittest "${module}"
	done
}

run_post_contract_modules() {
	local module

	echo
	echo "==> Container-backed post-contract verification"
	for module in "${POST_CONTRACT_MODULES[@]}"; do
		echo "--> ${module}"
		scripts/qwen_site_run_tests.sh "${module}"
	done
}

cd "${ROOT_DIR}"

case "${MODE}" in
	semantic)
		run_guardrails
		run_semantic_modules
		;;
	post-contract)
		run_guardrails
		run_post_contract_modules
		;;
	full)
		run_guardrails
		run_semantic_modules
		run_post_contract_modules
		;;
	-h|--help|help)
		usage
		;;
	*)
		echo "Unknown mode: ${MODE}" >&2
		usage >&2
		exit 1
		;;
esac
