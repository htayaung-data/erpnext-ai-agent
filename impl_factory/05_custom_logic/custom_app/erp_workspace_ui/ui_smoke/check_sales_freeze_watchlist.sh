#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BASE_REF="${1:-HEAD}"

cd "$APP_ROOT"

GIT_ROOT="$(git rev-parse --show-toplevel)"
APP_RELATIVE_ROOT="$(realpath --relative-to "$GIT_ROOT" "$APP_ROOT")"

changed_files="$(
	{
		git diff --name-only "$BASE_REF" -- 2>/dev/null || true
		git diff --name-only --cached -- 2>/dev/null || true
		git ls-files --others --exclude-standard 2>/dev/null || true
	} | sort -u
)"

watchlist_matches=()
while IFS= read -r file; do
	[ -n "$file" ] || continue
	case "$file" in
		"$APP_RELATIVE_ROOT"/*)
			file="${file#"$APP_RELATIVE_ROOT"/}"
			;;
	esac
	case "$file" in
		erp_workspace_ui/public/css/erp_workspace_ui.css|\
		erp_workspace_ui/public/js/erp_workspace_ui_boot.js|\
		erp_workspace_ui/public/js/runtime/console/*|\
		erp_workspace_ui/public/js/runtime/list_page/list_page_shell.js|\
		erp_workspace_ui/public/js/runtime/report_page/report_page_shell.js|\
		erp_workspace_ui/public/js/runtime/child_page/*|\
		erp_workspace_ui/workspace_registry.py|\
		erp_workspace_ui/public/js/runtime/console/workspace_registry.js|\
		erp_workspace_ui/workspace_governance_manifest.py|\
		erp_workspace_ui/sales_console/*|\
		erp_workspace_ui/erp_workspace_ui/page/sales_console*/*|\
		erp_workspace_ui/public/js/quotation_form.js|\
		erp_workspace_ui/public/js/sales_order_form.js|\
		erp_workspace_ui/public/js/delivery_note_form.js|\
		erp_workspace_ui/public/js/sales_invoice_form.js)
			watchlist_matches+=("$file")
			;;
	esac
done <<< "$changed_files"

if [ "${#watchlist_matches[@]}" -eq 0 ]; then
	echo "No Sales freeze watchlist files changed relative to $BASE_REF."
	exit 0
fi

echo "Sales freeze watchlist files changed relative to $BASE_REF:"
printf " - %s\n" "${watchlist_matches[@]}"
echo
echo "Run the mandatory gate before accepting this change:"
echo "  npm --prefix ui_smoke run test:sales-freeze-protection"
