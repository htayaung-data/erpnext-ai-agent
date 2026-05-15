#!/usr/bin/env bash
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"

unset npm_config_prefix NPM_CONFIG_PREFIX

DEFAULT_ARTIFACT_PARENT="$SCRIPT_DIR/artifacts"
if [ -n "${ERPW_PROTECTED_WORKSPACE_ARTIFACT_ROOT:-}" ]; then
	ARTIFACT_ROOT="$ERPW_PROTECTED_WORKSPACE_ARTIFACT_ROOT"
elif mkdir -p "$DEFAULT_ARTIFACT_PARENT" 2>/dev/null && [ -w "$DEFAULT_ARTIFACT_PARENT" ]; then
	ARTIFACT_ROOT="$DEFAULT_ARTIFACT_PARENT/protected-workspaces-$TIMESTAMP"
else
	ARTIFACT_ROOT="/tmp/protected-workspaces-$TIMESTAMP"
fi

SUMMARY_FILE="$ARTIFACT_ROOT/protected-workspace-gate-summary.json"
RESULTS_TSV="$ARTIFACT_ROOT/.protected-workspace-gate-results.tsv"
NODE_CHECK_LIST="$ARTIFACT_ROOT/node-check-files.txt"
NODE_CHECK_LOG="$ARTIFACT_ROOT/node-check.log"

mkdir -p "$ARTIFACT_ROOT"
: > "$RESULTS_TSV"
find "$ARTIFACT_ROOT" -name failure.png -type f -delete 2>/dev/null || true

if [ -n "${ERPW_BASE_URL:-}" ]; then
	BASE_URL_VALUE="$ERPW_BASE_URL"
else
	BASE_URL_VALUE="https://meet.erpbosai.com"
fi

git_branch() {
	git -C "$APP_ROOT" rev-parse --abbrev-ref HEAD 2>/dev/null || printf "unknown"
}

git_commit() {
	git -C "$APP_ROOT" rev-parse HEAD 2>/dev/null || printf "unknown"
}

record_result() {
	local name="$1"
	local command="$2"
	local status="$3"
	local exit_code="$4"
	local artifact_path="$5"
	local encoded_command
	encoded_command="$(printf "%s" "$command" | base64 -w0)"
	printf "%s\t%s\t%s\t%s\t%s\n" "$name" "$status" "$exit_code" "$artifact_path" "$encoded_command" >> "$RESULTS_TSV"
}

write_summary() {
	local overall_status="$1"
	local failed_command="${2:-}"
	python3 - "$SUMMARY_FILE" "$RESULTS_TSV" "$TIMESTAMP" "$(git_commit)" "$(git_branch)" "$overall_status" "$failed_command" "$ARTIFACT_ROOT" "$APP_ROOT" <<'PY'
import base64
import json
import subprocess
import sys
from pathlib import Path

summary_file, results_file, timestamp, commit, branch, overall_status, failed_command, artifact_root, app_root = sys.argv[1:10]
commands = []
path = Path(results_file)
if path.exists():
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        name, status, exit_code, artifact_path, encoded_command = line.split("\t", 4)
        commands.append(
            {
                "name": name,
                "command": base64.b64decode(encoded_command.encode()).decode(),
                "status": status,
                "exit_code": int(exit_code),
                "artifact_path": artifact_path or None,
                "artifact_exists": bool(artifact_path and Path(artifact_path).exists()),
            }
        )

def git_lines(*args):
    result = subprocess.run(["git", "-C", app_root, *args], check=False, capture_output=True, text=True)
    return [line for line in result.stdout.splitlines() if line.strip()]

git_status_short_branch = git_lines("status", "--short", "--branch")
git_status_short = git_lines("status", "--short")
changed_files_name_status = git_lines("diff", "--name-status", "HEAD")
untracked_files = git_lines("ls-files", "--others", "--exclude-standard")

payload = {
    "timestamp": timestamp,
    "head_commit": commit,
    "branch": branch,
    "git_status_short_branch": git_status_short_branch,
    "working_tree_dirty": bool(git_status_short),
    "changed_files_name_status": changed_files_name_status,
    "untracked_files": untracked_files,
    "overall_status": overall_status,
    "artifact_root": artifact_root,
    "failed_command": failed_command or None,
    "commands": commands,
}
Path(summary_file).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
PY
}

fail_before_command() {
	local name="$1"
	local message="$2"
	echo "$message" >&2
	record_result "$name" "$message" "fail" 1 "$ARTIFACT_ROOT"
	write_summary "fail" "$name"
	echo "Protected workspace gate summary: $SUMMARY_FILE" >&2
	exit 1
}

require_env() {
	local missing=()
	local var
	for var in \
		ERPW_SALES_MANAGER_USERNAME ERPW_SALES_MANAGER_PASSWORD \
		ERPW_SALES_USER_USERNAME ERPW_SALES_USER_PASSWORD \
		ERPW_PURCHASE_MANAGER_USERNAME ERPW_PURCHASE_MANAGER_PASSWORD \
		ERPW_PURCHASE_USER_USERNAME ERPW_PURCHASE_USER_PASSWORD; do
		if [ -z "${!var:-}" ]; then
			missing+=("$var")
		fi
	done
	if [ "${#missing[@]}" -gt 0 ]; then
		fail_before_command "required-env" "Missing required environment variables: ${missing[*]}"
	fi
}

run_step() {
	local name="$1"
	local artifact_path="$2"
	local command_label="$3"
	shift 3
	local exit_code

	echo "==> $name"
	if [[ "$artifact_path" == *.log ]]; then
		mkdir -p "$(dirname "$artifact_path")"
		("$@") > "$artifact_path" 2>&1
		exit_code=$?
		cat "$artifact_path"
	else
		("$@")
		exit_code=$?
	fi
	if [ "$exit_code" -eq 0 ]; then
		record_result "$name" "$command_label" "pass" "$exit_code" "$artifact_path"
		return 0
	fi
	record_result "$name" "$command_label" "fail" "$exit_code" "$artifact_path"
	write_summary "fail" "$name"
	echo "Protected workspace gate failed at: $name" >&2
	echo "Protected workspace gate summary: $SUMMARY_FILE" >&2
	exit "$exit_code"
}

collect_node_check_files() {
	{
		git -C "$APP_ROOT" ls-files 			"erp_workspace_ui/public/js/*.js" 			"erp_workspace_ui/public/js/runtime/**/*.js" 			"erp_workspace_ui/erp_workspace_ui/page/**/*.js"
		printf "%s
" 			"ui_smoke/procurement_phase3_smoke.js" 			"ui_smoke/procurement_phase5b_smoke.js" 			"ui_smoke/procurement_phase5c_smoke.js" 			"ui_smoke/procurement_phase5d_smoke.js" 			"ui_smoke/procurement_responsive_filter_smoke.js" 			"ui_smoke/sales_action_cards_smoke.js" 			"ui_smoke/sales_detail_boundary_smoke.js" 			"ui_smoke/sales_directory_performance_smoke.js" 			"ui_smoke/sales_native_leakage_smoke.js" 			"ui_smoke/sales_order_analysis_smoke.js" 			"ui_smoke/sales_report_family_smoke.js" 			"ui_smoke/sales_route_lifecycle_smoke.js" 			"ui_smoke/sales_visual_stability_smoke.js" 			"ui_smoke/sales_worklist_shell_smoke.js"
	} | sort -u > "$NODE_CHECK_LIST"
}
run_node_checks() {
	local name="node-check-workspace-js"
	local command_label="while read file; do node --check FILE; done < $NODE_CHECK_LIST"
	echo "==> $name"
	(cd "$APP_ROOT" && while IFS= read -r file; do node --check "$file" || exit $?; done < "$NODE_CHECK_LIST") > "$NODE_CHECK_LOG" 2>&1
	local exit_code=$?
	cat "$NODE_CHECK_LOG"
	if [ "$exit_code" -eq 0 ]; then
		record_result "$name" "$command_label" "pass" "$exit_code" "$NODE_CHECK_LOG"
		return 0
	fi
	record_result "$name" "$command_label" "fail" "$exit_code" "$NODE_CHECK_LOG"
	write_summary "fail" "$name"
	echo "Protected workspace gate failed at: $name" >&2
	echo "Protected workspace gate summary: $SUMMARY_FILE" >&2
	exit "$exit_code"
}

run_sales_freeze_gate() {
	run_step \
		"sales-freeze-protection" \
		"$ARTIFACT_ROOT/sales-freeze-protection" \
		"npm --prefix ui_smoke run test:sales-freeze-protection with Sales credentials" \
		env \
		ERPW_BASE_URL="$BASE_URL_VALUE" \
		ERPW_MANAGER_USERNAME="$ERPW_SALES_MANAGER_USERNAME" \
		ERPW_MANAGER_PASSWORD="$ERPW_SALES_MANAGER_PASSWORD" \
		ERPW_USER_USERNAME="$ERPW_SALES_USER_USERNAME" \
		ERPW_USER_PASSWORD="$ERPW_SALES_USER_PASSWORD" \
		ERPW_USERNAME="$ERPW_SALES_MANAGER_USERNAME" \
		ERPW_PASSWORD="$ERPW_SALES_MANAGER_PASSWORD" \
		ERPW_SALES_FREEZE_ARTIFACT_ROOT="$ARTIFACT_ROOT/sales-freeze-protection" \
		npm --prefix "$SCRIPT_DIR" run test:sales-freeze-protection
}

run_docker_smoke() {
	local name="$1"
	local artifact_path="$2"
	local command_label="$3"
	local npm_script="$4"
	shift 4
	run_step "$name" "$artifact_path" "$command_label" env "$@" "$SCRIPT_DIR/run_playwright_docker.sh" npm run "$npm_script"
}

run_procurement_section_for_role() {
	local role_key="$1"
	local username_var="$2"
	local password_var="$3"
	local section_key="$4"
	local out_dir="$ARTIFACT_ROOT/procurement-$section_key-$role_key"
	local manager_username=""
	local manager_password=""
	local user_username=""
	local user_password=""
	if [[ "$role_key" == *manager* ]]; then
		manager_username="$username_var"
		manager_password="$password_var"
	else
		user_username="$username_var"
		user_password="$password_var"
	fi
	run_step 		"procurement-$section_key-$role_key" 		"$out_dir" 		"run_playwright_docker.sh env ERPW_PROCUREMENT_SMOKE_SECTION=$section_key npm run test:procurement-phase3 for $role_key" 		env 		ERPW_BASE_URL="$BASE_URL_VALUE" 		ERPW_PLAYWRIGHT_ARTIFACT_ROOT="$ARTIFACT_ROOT" 		ERPW_MANAGER_USERNAME="$manager_username" 		ERPW_MANAGER_PASSWORD="$manager_password" 		ERPW_USER_USERNAME="$user_username" 		ERPW_USER_PASSWORD="$user_password" 		"$SCRIPT_DIR/run_playwright_docker.sh" 		env 		ERPW_PROCUREMENT_ARTIFACT_DIR="/freeze-artifacts/procurement-$section_key-$role_key" 		ERPW_PROCUREMENT_SMOKE_SECTION="$section_key" 		npm run test:procurement-phase3
}

run_procurement_phase4a_split_gates() {
	run_procurement_section_for_role "purchase-manager" "$ERPW_PURCHASE_MANAGER_USERNAME" "$ERPW_PURCHASE_MANAGER_PASSWORD" "core-navigation-and-chrome"
	run_procurement_section_for_role "purchase-manager" "$ERPW_PURCHASE_MANAGER_USERNAME" "$ERPW_PURCHASE_MANAGER_PASSWORD" "reports-and-filter-layout"
	run_procurement_section_for_role "purchase-manager" "$ERPW_PURCHASE_MANAGER_USERNAME" "$ERPW_PURCHASE_MANAGER_PASSWORD" "worklists-and-details"
	run_procurement_section_for_role "purchase-manager" "$ERPW_PURCHASE_MANAGER_USERNAME" "$ERPW_PURCHASE_MANAGER_PASSWORD" "autocomplete-and-link-controls"
	run_procurement_section_for_role "purchase-user" "$ERPW_PURCHASE_USER_USERNAME" "$ERPW_PURCHASE_USER_PASSWORD" "role-user-regression"
}

run_procurement_responsive_for_role() {
	local role_key="$1"
	local username_var="$2"
	local password_var="$3"
	local out_dir="$ARTIFACT_ROOT/procurement-responsive-filters-$role_key"
	run_docker_smoke \
		"procurement-responsive-filters-$role_key" \
		"$out_dir" \
		"run_playwright_docker.sh npm run test:procurement-responsive-filters for $role_key" \
		"test:procurement-responsive-filters" \
		ERPW_BASE_URL="$BASE_URL_VALUE" \
		ERPW_PLAYWRIGHT_ARTIFACT_ROOT="$ARTIFACT_ROOT" \
		ERPW_MANAGER_USERNAME="$username_var" \
		ERPW_MANAGER_PASSWORD="$password_var" \
		ERPW_USER_USERNAME= \
		ERPW_USER_PASSWORD= \
		ERPW_PROCUREMENT_ARTIFACT_DIR="/freeze-artifacts/procurement-responsive-filters-$role_key"
}

run_procurement_phase5c_for_role() {
	local role_key="$1"
	local username_var="$2"
	local password_var="$3"
	local out_dir="$ARTIFACT_ROOT/procurement-phase5c-$role_key"
	run_docker_smoke \
		"procurement-phase5c-$role_key" \
		"$out_dir" \
		"run_playwright_docker.sh npm run test:procurement-phase5c for $role_key" \
		"test:procurement-phase5c" \
		ERPW_BASE_URL="$BASE_URL_VALUE" \
		ERPW_PLAYWRIGHT_ARTIFACT_ROOT="$ARTIFACT_ROOT" \
		ERPW_MANAGER_USERNAME="$username_var" \
		ERPW_MANAGER_PASSWORD="$password_var" \
		ERPW_USER_USERNAME= \
		ERPW_USER_PASSWORD= \
		ERPW_PROCUREMENT_PHASE5C_ARTIFACT_DIR="/freeze-artifacts/procurement-phase5c-$role_key"
}

run_procurement_phase5d_for_role() {
	local role_key="$1"
	local username_var="$2"
	local password_var="$3"
	local out_dir="$ARTIFACT_ROOT/procurement-phase5d-$role_key"
	run_docker_smoke 		"procurement-phase5d-$role_key" 		"$out_dir" 		"run_playwright_docker.sh npm run test:procurement-phase5d for $role_key" 		"test:procurement-phase5d" 		ERPW_BASE_URL="$BASE_URL_VALUE" 		ERPW_PLAYWRIGHT_ARTIFACT_ROOT="$ARTIFACT_ROOT" 		ERPW_MANAGER_USERNAME="$username_var" 		ERPW_MANAGER_PASSWORD="$password_var" 		ERPW_USER_USERNAME= 		ERPW_USER_PASSWORD= 		ERPW_PROCUREMENT_PHASE5D_ARTIFACT_DIR="/freeze-artifacts/procurement-phase5d-$role_key"
}

run_sales_directory_performance() {
	run_docker_smoke \
		"sales-directory-performance" \
		"$ARTIFACT_ROOT/sales-directory-performance" \
		"run_playwright_docker.sh npm run test:sales-directory-performance" \
		"test:sales-directory-performance" \
		ERPW_BASE_URL="$BASE_URL_VALUE" \
		ERPW_PLAYWRIGHT_ARTIFACT_ROOT="$ARTIFACT_ROOT" \
		ERPW_MANAGER_USERNAME="$ERPW_SALES_MANAGER_USERNAME" \
		ERPW_MANAGER_PASSWORD="$ERPW_SALES_MANAGER_PASSWORD" \
		ERPW_USER_USERNAME="$ERPW_SALES_USER_USERNAME" \
		ERPW_USER_PASSWORD="$ERPW_SALES_USER_PASSWORD" \
		ERPW_SALES_PERFORMANCE_OUT="/freeze-artifacts/sales-directory-performance"
}

require_env
collect_node_check_files

run_step "python-compileall" "$ARTIFACT_ROOT/python-compileall.log" "python3 -m compileall erp_workspace_ui" bash -lc "cd '$APP_ROOT' && python3 -m compileall erp_workspace_ui"
run_step "python-unit-discovery" "$ARTIFACT_ROOT/python-unit-discovery.log" "PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'" bash -lc "cd '$APP_ROOT' && PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'"
run_node_checks
run_step "git-diff-check" "$ARTIFACT_ROOT/git-diff-check.log" "git diff --check HEAD" git -C "$APP_ROOT" diff --check HEAD

run_sales_freeze_gate
run_procurement_phase4a_split_gates
run_procurement_phase5c_for_role "purchase-manager" "$ERPW_PURCHASE_MANAGER_USERNAME" "$ERPW_PURCHASE_MANAGER_PASSWORD"
run_procurement_phase5c_for_role "purchase-user" "$ERPW_PURCHASE_USER_USERNAME" "$ERPW_PURCHASE_USER_PASSWORD"
run_procurement_phase5d_for_role "purchase-manager" "$ERPW_PURCHASE_MANAGER_USERNAME" "$ERPW_PURCHASE_MANAGER_PASSWORD"
run_procurement_phase5d_for_role "purchase-user" "$ERPW_PURCHASE_USER_USERNAME" "$ERPW_PURCHASE_USER_PASSWORD"
run_procurement_responsive_for_role "purchase-manager" "$ERPW_PURCHASE_MANAGER_USERNAME" "$ERPW_PURCHASE_MANAGER_PASSWORD"
run_procurement_responsive_for_role "purchase-user" "$ERPW_PURCHASE_USER_USERNAME" "$ERPW_PURCHASE_USER_PASSWORD"
run_sales_directory_performance

failure_marker="$(find "$ARTIFACT_ROOT" -name failure.png -type f -print -quit 2>/dev/null || true)"
if [ -n "$failure_marker" ]; then
	record_result "artifact-stale-failure-check" "find $ARTIFACT_ROOT -name failure.png" "fail" 1 "$failure_marker"
	write_summary "fail" "artifact-stale-failure-check"
	echo "Unexpected failure marker left inside current artifact root: $failure_marker" >&2
	echo "Protected workspace gate summary: $SUMMARY_FILE" >&2
	exit 1
fi

record_result "artifact-stale-failure-check" "find $ARTIFACT_ROOT -name failure.png" "pass" 0 "$ARTIFACT_ROOT"
write_summary "pass" ""
echo "Protected workspace gate passed."
echo "Artifact root: $ARTIFACT_ROOT"
echo "Summary: $SUMMARY_FILE"
