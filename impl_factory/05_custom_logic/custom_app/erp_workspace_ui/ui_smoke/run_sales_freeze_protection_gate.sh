#!/usr/bin/env bash
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"

unset npm_config_prefix NPM_CONFIG_PREFIX

default_artifact_parent="$SCRIPT_DIR/artifacts"
if [ -n "${ERPW_SALES_FREEZE_ARTIFACT_ROOT:-}" ]; then
	ARTIFACT_ROOT="$ERPW_SALES_FREEZE_ARTIFACT_ROOT"
elif mkdir -p "$default_artifact_parent" 2>/dev/null && [ -w "$default_artifact_parent" ]; then
	ARTIFACT_ROOT="$default_artifact_parent/sales-freeze-protection-$TIMESTAMP"
else
	ARTIFACT_ROOT="/tmp/sales-freeze-protection-$TIMESTAMP"
fi
SUMMARY_FILE="$ARTIFACT_ROOT/sales-freeze-protection-summary.json"
RESULTS_TSV="$ARTIFACT_ROOT/.sales-freeze-protection-results.tsv"
NODE_CHECK_LIST="$ARTIFACT_ROOT/node-check-files.txt"
NODE_CHECK_LOG="$ARTIFACT_ROOT/node-check.log"

case "$ARTIFACT_ROOT" in
	"$SCRIPT_DIR"/*)
		CONTAINER_ARTIFACT_ROOT="/work/${ARTIFACT_ROOT#"$SCRIPT_DIR"/}"
		DOCKER_ARTIFACT_ROOT_ENV=""
		;;
	*)
		CONTAINER_ARTIFACT_ROOT="/freeze-artifacts"
		DOCKER_ARTIFACT_ROOT_ENV="ERPW_PLAYWRIGHT_ARTIFACT_ROOT=\"$ARTIFACT_ROOT\""
		;;
esac

mkdir -p "$ARTIFACT_ROOT"
: > "$RESULTS_TSV"

# If a caller reuses an explicit artifact root, remove old failure markers before
# this run starts so the final summary cannot be confused with stale evidence.
find "$ARTIFACT_ROOT" -name failure.png -type f -delete 2>/dev/null || true

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
    result = subprocess.run(
        ["git", "-C", app_root, *args],
        check=False,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line.strip()]

git_status_short_branch = git_lines("status", "--short", "--branch")
git_status_short = git_lines("status", "--short")
changed_files_name_status = git_lines("diff", "--name-status", "HEAD")
untracked_files = git_lines("ls-files", "--others", "--exclude-standard")

payload = {
    "timestamp": timestamp,
    "head_commit": commit,
    "git_commit": commit,
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
	echo "Sales freeze protection summary: $SUMMARY_FILE" >&2
	exit 1
}

require_env() {
	local missing=()
	local var
	for var in ERPW_BASE_URL ERPW_MANAGER_USERNAME ERPW_MANAGER_PASSWORD ERPW_USER_USERNAME ERPW_USER_PASSWORD; do
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
	local command="$3"
	local exit_code

	echo "==> $name"
	if [[ "$artifact_path" == *.log ]]; then
		mkdir -p "$(dirname "$artifact_path")"
		(cd "$APP_ROOT" && bash -lc "$command") > "$artifact_path" 2>&1
		exit_code=$?
		cat "$artifact_path"
	else
		(cd "$APP_ROOT" && bash -lc "$command")
		exit_code=$?
	fi
	if [ "$exit_code" -eq 0 ]; then
		record_result "$name" "$command" "pass" "$exit_code" "$artifact_path"
		return 0
	fi
	record_result "$name" "$command" "fail" "$exit_code" "$artifact_path"
	write_summary "fail" "$name"
	echo "Sales freeze protection failed at: $name" >&2
	echo "Sales freeze protection summary: $SUMMARY_FILE" >&2
	exit "$exit_code"
}

collect_node_check_files() {
	{
		printf "%s\n" \
			"erp_workspace_ui/public/js/erp_workspace_ui_boot.js" \
			"erp_workspace_ui/public/js/runtime/console/workspace_console_runtime.js" \
			"erp_workspace_ui/public/js/runtime/console/workspace_console_sidebar.js" \
			"erp_workspace_ui/public/js/runtime/list_page/list_page_shell.js" \
			"erp_workspace_ui/public/js/runtime/report_page/report_page_shell.js"
		find "$APP_ROOT/erp_workspace_ui/erp_workspace_ui/page" -maxdepth 2 -path "*/sales_console*/*.js" -type f \
			| sed "s#^$APP_ROOT/##"
		find "$APP_ROOT/erp_workspace_ui/public/js" -maxdepth 1 \
			\( -name "quotation_form.js" -o -name "sales_order_form.js" -o -name "delivery_note_form.js" -o -name "sales_invoice_form.js" \) -type f \
			| sed "s#^$APP_ROOT/##"
		git -C "$APP_ROOT" ls-files "ui_smoke/sales*_smoke.js"
	} | sort -u > "$NODE_CHECK_LIST"
}

run_node_checks() {
	local name="node-check-sales-shared-js"
	local command="while IFS= read -r file; do node --check \"\$file\"; done < \"$NODE_CHECK_LIST\""
	local exit_code

	echo "==> $name"
	(cd "$APP_ROOT" && while IFS= read -r file; do node --check "$file"; done < "$NODE_CHECK_LIST") > "$NODE_CHECK_LOG" 2>&1
	exit_code=$?
	cat "$NODE_CHECK_LOG"
	if [ "$exit_code" -eq 0 ]; then
		record_result "$name" "$command" "pass" "$exit_code" "$NODE_CHECK_LOG"
		return 0
	fi
	record_result "$name" "$command" "fail" "$exit_code" "$NODE_CHECK_LOG"
	write_summary "fail" "$name"
	echo "Sales freeze protection failed at: $name" >&2
	echo "Sales freeze protection summary: $SUMMARY_FILE" >&2
	exit "$exit_code"
}

run_smoke() {
	local name="$1"
	local out_env="$2"
	local npm_command="$3"
	local out_dir="$ARTIFACT_ROOT/$name"
	local container_out_dir="$CONTAINER_ARTIFACT_ROOT/$name"
	local command="cd \"$SCRIPT_DIR\" && env $DOCKER_ARTIFACT_ROOT_ENV $out_env=\"$container_out_dir\" ./run_playwright_docker.sh npm run $npm_command"
	run_step "$name" "$out_dir" "$command"
}

require_env
collect_node_check_files

run_step "python-compileall" "$ARTIFACT_ROOT/python-compileall.log" "python3 -m compileall erp_workspace_ui"
run_step "python-unit-discovery" "$ARTIFACT_ROOT/python-unit-discovery.log" "PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'"
run_node_checks
run_step "git-diff-check" "$ARTIFACT_ROOT/git-diff-check.log" "git diff --check HEAD"

run_smoke "sales-route-lifecycle" "ERPW_CAPTURE_ROOT" "test:sales-route-lifecycle"
run_smoke "sales-action-cards" "ERPW_SALES_ACTIONS_OUT" "test:sales-actions"
run_smoke "sales-worklists" "ERPW_SALES_WORKLISTS_OUT" "test:sales-worklists"
run_smoke "sales-detail-boundary" "ERPW_SALES_DETAIL_OUT" "test:sales-detail-boundary"
run_smoke "sales-reports" "ERPW_SALES_REPORTS_OUT" "test:sales-reports"
run_smoke "sales-native-leakage" "ERPW_SALES_LEAKAGE_OUT" "test:sales-native-leakage"
run_smoke "sales-visual-stability" "ERPW_SALES_VISUAL_OUT" "test:sales-visual-stability"
run_smoke "sales-order-analysis-manager-user" "ERPW_SALES_ORDER_ANALYSIS_OUT" "test:sales-order-analysis"

failure_marker="$(find "$ARTIFACT_ROOT" -name failure.png -type f -print -quit 2>/dev/null || true)"
if [ -n "$failure_marker" ]; then
	record_result "artifact-stale-failure-check" "find \"$ARTIFACT_ROOT\" -name failure.png" "fail" 1 "$failure_marker"
	write_summary "fail" "artifact-stale-failure-check"
	echo "Unexpected failure marker left inside current artifact root: $failure_marker" >&2
	echo "Sales freeze protection summary: $SUMMARY_FILE" >&2
	exit 1
fi

record_result "artifact-stale-failure-check" "find \"$ARTIFACT_ROOT\" -name failure.png" "pass" 0 "$ARTIFACT_ROOT"
write_summary "pass" ""
echo "Sales freeze protection gate passed."
echo "Artifact root: $ARTIFACT_ROOT"
echo "Summary: $SUMMARY_FILE"
