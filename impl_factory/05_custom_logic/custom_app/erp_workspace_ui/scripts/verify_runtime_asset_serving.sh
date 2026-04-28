#!/usr/bin/env bash

set -euo pipefail

BASE_URL="${1:-${ERPW_BASE_URL:-http://127.0.0.1:8083}}"
FRONTEND_CONTAINER="${FRONTEND_CONTAINER:-erpai_project1-frontend-1}"

required_assets=(
  "/assets/erp_workspace_ui/js/erp_workspace_ui_boot.js"
  "/assets/erp_workspace_ui/js/sales_order_form.js"
  "/assets/erp_workspace_ui/js/quotation_form.js"
  "/assets/erp_workspace_ui/js/delivery_note_form.js"
  "/assets/erp_workspace_ui/js/runtime/console/workspace_console_runtime.js"
  "/assets/erp_workspace_ui/js/runtime/child_page/child_page_helpers.js"
  "/assets/erp_workspace_ui/js/runtime/child_page/child_page_sections.js"
  "/assets/erp_workspace_ui/js/runtime/child_page/child_page_details.js"
  "/assets/erp_workspace_ui/js/runtime/child_page/child_page_terms.js"
  "/assets/erp_workspace_ui/js/runtime/child_page/child_page_summaries.js"
  "/assets/erp_workspace_ui/js/runtime/child_page/child_page_observability.js"
  "/assets/erp_workspace_ui/js/runtime/child_page/child_page_shell.js"
  "/assets/erp_workspace_ui/js/runtime/child_page/child_page_shell_content.js"
  "/assets/erp_workspace_ui/js/runtime/child_page/child_page_runtime.js"
  "/assets/erp_workspace_ui/js/runtime/child_page/child_page_connections.js"
  "/assets/erp_workspace_ui/js/runtime/child_page/child_page_support.js"
  "/assets/erp_workspace_ui/js/runtime/child_page/child_page_sidebar.js"
)

echo "Verifying ERP Workspace UI runtime assets from ${BASE_URL}"

for asset in "${required_assets[@]}"; do
  status="$(curl -sS -o /dev/null -w '%{http_code}' "${BASE_URL}${asset}")"
  if [[ "${status}" != "200" ]]; then
    echo "FAIL ${asset} -> HTTP ${status}" >&2
    exit 1
  fi
  echo "OK   ${asset}"
done

if docker ps --format '{{.Names}}' | grep -qx "${FRONTEND_CONTAINER}"; then
  echo
  echo "Verifying runtime directory inside ${FRONTEND_CONTAINER}"
  docker exec "${FRONTEND_CONTAINER}" bash -lc '
    set -euo pipefail
    test -d /home/frappe/frappe-bench/apps/erp_workspace_ui/erp_workspace_ui/public/js/runtime/console
    test -f /home/frappe/frappe-bench/apps/erp_workspace_ui/erp_workspace_ui/public/js/runtime/console/workspace_console_runtime.js
    test -d /home/frappe/frappe-bench/apps/erp_workspace_ui/erp_workspace_ui/public/js/runtime/child_page
    test -f /home/frappe/frappe-bench/apps/erp_workspace_ui/erp_workspace_ui/public/js/runtime/child_page/child_page_observability.js
    test -f /home/frappe/frappe-bench/apps/erp_workspace_ui/erp_workspace_ui/public/js/runtime/child_page/child_page_sections.js
    test -f /home/frappe/frappe-bench/apps/erp_workspace_ui/erp_workspace_ui/public/js/runtime/child_page/child_page_details.js
    test -f /home/frappe/frappe-bench/apps/erp_workspace_ui/erp_workspace_ui/public/js/runtime/child_page/child_page_terms.js
    test -f /home/frappe/frappe-bench/apps/erp_workspace_ui/erp_workspace_ui/public/js/runtime/child_page/child_page_summaries.js
    test -f /home/frappe/frappe-bench/apps/erp_workspace_ui/erp_workspace_ui/public/js/runtime/child_page/child_page_shell.js
    test -f /home/frappe/frappe-bench/apps/erp_workspace_ui/erp_workspace_ui/public/js/runtime/child_page/child_page_shell_content.js
    test -f /home/frappe/frappe-bench/apps/erp_workspace_ui/erp_workspace_ui/public/js/runtime/child_page/child_page_connections.js
  '
  echo "OK   frontend container sees child-page runtime assets"
else
  echo
  echo "Skip frontend container check; ${FRONTEND_CONTAINER} is not running"
fi

echo
echo "Runtime asset serving verification passed"
