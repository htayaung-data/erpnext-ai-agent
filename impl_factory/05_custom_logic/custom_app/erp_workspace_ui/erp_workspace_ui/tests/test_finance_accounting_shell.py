from __future__ import annotations

import json
import re
import sys
import types
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch


class _FrappePermissionError(Exception):
    pass


def _install_frappe_stub() -> None:
    if "frappe" in sys.modules:
        return

    frappe_stub = types.ModuleType("frappe")
    frappe_stub.PermissionError = _FrappePermissionError
    frappe_stub.session = types.SimpleNamespace(user=None)
    frappe_stub.get_roles = lambda user=None: []
    frappe_stub.defaults = types.SimpleNamespace(get_user_default=lambda key: None)
    frappe_stub._ = lambda value: value
    frappe_stub.whitelist = lambda *args, **kwargs: (lambda fn: fn) if not args else args[0]

    def throw(message, exc=None):
        raise (exc or Exception)(message)

    frappe_stub.throw = throw

    utils_stub = types.ModuleType("frappe.utils")
    utils_stub.cstr = lambda value="": "" if value is None else str(value)
    utils_stub.now_datetime = lambda: datetime(2026, 7, 4, 0, 0, 0)

    sys.modules["frappe"] = frappe_stub
    sys.modules["frappe.utils"] = utils_stub


_install_frappe_stub()

import frappe  # noqa: E402

from erp_workspace_ui.finance_accounting import service


_SOURCE_ROOT = Path(__file__).resolve().parents[1]
_FRONTEND_SOURCE = _SOURCE_ROOT / "erp_workspace_ui/page/finance_control_desk/finance_control_desk.js"
_PAGE_METADATA_SOURCE = _SOURCE_ROOT / "erp_workspace_ui/page/finance_control_desk/finance_control_desk.json"
_SERVICE_SOURCE = _SOURCE_ROOT / "finance_accounting/service.py"
_SIDEBAR_SOURCE = _SOURCE_ROOT / "public/js/runtime/console/workspace_console_sidebar.js"
_F4D_DOC_SOURCE = _SOURCE_ROOT.parent / "_docs/erp-ui-customization/finance-accounting-phase-f4d-receivables-count-posture-2026-07-06.md"
_F4K1_DOC_SOURCE = _SOURCE_ROOT.parent / "_docs/erp-ui-customization/finance-accounting-phase-f4k1-ar-copy-traceability-remediation-2026-07-07.md"


def _frontend_source() -> str:
    return _FRONTEND_SOURCE.read_text(encoding="utf-8")


def _service_source() -> str:
    return _SERVICE_SOURCE.read_text(encoding="utf-8")


def _sidebar_source() -> str:
    return _SIDEBAR_SOURCE.read_text(encoding="utf-8")



_COMPANY_SCOPE = {
    "name": "Mingalar Mobile Distribution Co., Ltd.",
    "label": "Mingalar Mobile Distribution Co., Ltd.",
    "currency": "MMK",
}


def _resolver(state="scoped", role_category="manager", selected_company=None, reason="single_enabled_company_without_company_permission"):
    return {
        "state": state,
        "source": "single_company_site_fallback" if state == "scoped" else state,
        "reason": reason,
        "role_category": role_category,
        "selected_company": _COMPANY_SCOPE if selected_company is None and state == "scoped" else selected_company,
        "rows": [],
        "metrics": [],
        "amounts": [],
        "documents": [],
    }


def _permission_allowed(*args, **kwargs):
    return {
        "source": service.RECEIVABLES_COUNT_SOURCE,
        "source_permission_checked": True,
        "source_permission_verified": True,
        "reason": "source_permission_allowed",
    }


def _fake_bucket_count(filters, list_getter=None):
    due_filter = filters[-1]
    if due_filter == ["due_date", "is", "not set"]:
        return 0
    if due_filter[1] == ">=":
        return 2
    if due_filter[1] == "between" and due_filter[2][1] in {"2026-07-03", "2026-07-05"}:
        return 1
    return 0

class TestFinanceAccountingShell(unittest.TestCase):
    def test_page_metadata_allows_only_finance_desk_roles(self):
        metadata = json.loads(_PAGE_METADATA_SOURCE.read_text(encoding="utf-8"))
        roles = {entry.get("role") for entry in metadata.get("roles", [])}

        self.assertEqual(roles, {"Accounts Manager", "Accounts User"})
        self.assertNotIn("System Manager", roles)
        self.assertNotIn("Executive Approver", roles)
        self.assertNotIn("All", roles)

    def setUp(self):
        self.previous_user = getattr(frappe.session, "user", None)
        frappe.session.user = "finance@example.test"

    def tearDown(self):
        frappe.session.user = self.previous_user

    def test_shell_context_is_static_and_no_effect_for_accounts_manager(self):
        with patch.object(service.frappe, "get_roles", return_value=["Accounts Manager"]):
            payload = service.get_finance_control_desk_shell_context()

        self.assertEqual(payload["state"]["kind"], "ready")
        self.assertEqual(payload["workspace"]["workspace_id"], "finance")
        self.assertEqual(payload["scope"]["financial_data_enabled"], False)
        self.assertEqual(payload["scope"]["execution_enabled"], False)
        self.assertEqual(payload["rows"], [])
        self.assertTrue(payload["lanes"])
        self.assertTrue(all(lane["rows"] == [] for lane in payload["lanes"]))
        self.assertTrue(all(value is False for value in payload["no_effect"].values()))
        self.assertEqual(payload["no_effect"]["row_level_financial_data_returned"], False)
        self.assertNotIn("financial_rows_loaded", payload["no_effect"])
        self.assertNotIn("user", payload["context"])
        self.assertNotIn("roles", payload["context"])
        self.assertNotIn("finance@example.test", repr(payload["context"]))
        self.assertEqual(payload["context"]["role_family"], "Finance & Accounting")
        self.assertEqual(payload["context"]["role_variant"], "accounts_manager")
        self.assertEqual(payload["context"]["has_finance_shell_access"], True)

    def test_shell_context_restricts_non_finance_roles_without_rows(self):
        with patch.object(service.frappe, "get_roles", return_value=["Sales User"]):
            payload = service.get_finance_control_desk_shell_context()

        self.assertEqual(payload["state"]["kind"], "restricted")
        self.assertEqual(payload["scope"]["scope_mode"], "restricted")
        self.assertEqual(payload["lanes"], [])
        self.assertEqual(payload["rows"], [])
        self.assertTrue(all(value is False for value in payload["no_effect"].values()))

    def test_overview_context_ready_for_accounts_manager_with_f4b_resolver_scope(self):
        with patch.object(service.frappe, "get_roles", return_value=["Accounts Manager"]), patch.object(
            service,
            "resolve_finance_role_company_scope",
            return_value=_resolver(),
        ), patch.object(
            service,
            "verify_receivables_source_permission",
            side_effect=_permission_allowed,
        ), patch.object(
            service,
            "_permission_preserving_receivables_count",
            side_effect=_fake_bucket_count,
        ):
            payload = service.get_finance_control_desk_overview_context()

        self.assertEqual(payload["state"]["kind"], "ready")
        self.assertNotIn("user", payload["context"])
        self.assertNotIn("roles", payload["context"])
        self.assertNotIn("finance@example.test", repr(payload["context"]))
        self.assertEqual(payload["context"]["role_variant"], "accounts_manager")
        self.assertEqual(payload["scope"]["scope_mode"], service.FINANCE_OVERVIEW_PHASE)
        self.assertEqual(payload["scope"]["accounting_overview_enabled"], True)
        self.assertEqual(payload["scope"]["receivables_count_posture_enabled"], True)
        self.assertEqual(payload["scope"]["receivables_amount_summary_enabled"], False)
        self.assertEqual(payload["scope"]["financial_data_enabled"], False)
        self.assertEqual(payload["scope"]["financial_rows_enabled"], False)
        self.assertEqual(payload["scope"]["monetary_values_enabled"], False)
        self.assertEqual(payload["scope"]["execution_enabled"], False)
        self.assertEqual(payload["company_scope"]["company"], _COMPANY_SCOPE["name"])
        self.assertEqual(payload["company_scope"]["source"], "single_company_site_fallback")
        self.assertNotEqual(payload["company_scope"]["source"], "user_default_company")
        self.assertEqual(payload["receivables_posture"]["state"], "ready")
        self.assertEqual(payload["receivables_posture"]["bucket_counts"], {
            "current": 2,
            "overdue_1_30": 1,
            "overdue_31_60": 0,
            "overdue_61_90": 0,
            "overdue_over_90": 0,
        })
        for blocked_key in ("rows", "amounts", "documents", "metrics", "customer", "invoice", "route", "report", "export", "action"):
            self.assertNotIn(blocked_key, payload["receivables_posture"])
        self.assertEqual(payload["rows"], [])
        self.assertEqual(payload["metrics"], [])
        self.assertEqual(payload["amounts"], [])
        self.assertEqual(payload["documents"], [])
        self.assertTrue(payload["posture_cards"])
        self.assertTrue(all(card["rows"] == [] for card in payload["posture_cards"]))
        self.assertTrue(all(value is False for value in payload["no_effect"].values()))
        self.assertEqual(
            set(payload),
            {
                "workspace",
                "context",
                "scope",
                "state",
                "sidebar",
                "navigation",
                "overview",
                "receivables_posture",
                "receivables_amount_summary",
                "company_scope",
                "period_scope",
                "posture_cards",
                "lanes",
                "metrics",
                "amounts",
                "documents",
                "rows",
                "no_effect",
                "fetched_at",
            },
        )
        for card in payload["posture_cards"]:
            self.assertEqual(set(card), {"key", "title", "state", "detail", "value", "rows"})
            self.assertEqual(card["rows"], [])

    def test_user_default_company_alone_does_not_authorize_overview_or_counts(self):
        with patch.object(service.frappe, "get_roles", return_value=["Accounts Manager"]), patch.object(
            service.frappe.defaults,
            "get_user_default",
            return_value="Example Company",
        ), patch.object(
            service,
            "resolve_finance_role_company_scope",
            return_value=_resolver(state="unavailable", selected_company=None, reason="company_user_permission_required_for_multi_company"),
        ), patch.object(
            service,
            "_permission_preserving_receivables_count",
            side_effect=AssertionError("count query should not run"),
        ):
            payload = service.get_finance_control_desk_overview_context()

        self.assertEqual(payload["state"]["kind"], "unavailable")
        self.assertEqual(payload["scope"]["accounting_overview_enabled"], False)
        self.assertEqual(payload["scope"]["receivables_count_posture_enabled"], False)
        self.assertEqual(payload["scope"]["receivables_amount_summary_enabled"], False)
        self.assertEqual(payload["company_scope"]["state"], "unavailable")
        self.assertNotEqual(payload["company_scope"]["source"], "user_default_company")
        self.assertIsNone(payload["company_scope"]["company"])
        self.assertEqual(payload["receivables_posture"]["state"], "unavailable")
        self.assertEqual(payload["receivables_posture"]["bucket_counts"], {})
        self.assertEqual(payload["rows"], [])
        self.assertEqual(payload["amounts"], [])
        self.assertEqual(payload["documents"], [])

    def test_overview_context_is_unavailable_when_f4b_resolver_has_no_scope(self):
        cases = [
            _resolver(state="unavailable", selected_company=None, reason="company_user_permission_required_for_multi_company"),
            _resolver(state="selection_required", selected_company=None, reason="multiple_company_permissions_require_selection"),
            _resolver(state="restricted", selected_company=None, reason="requested_company_outside_scope"),
        ]
        for resolver in cases:
            with self.subTest(state=resolver["state"], reason=resolver["reason"]):
                with patch.object(service.frappe, "get_roles", return_value=["Accounts Manager"]), patch.object(
                    service,
                    "resolve_finance_role_company_scope",
                    return_value=resolver,
                ), patch.object(
                    service,
                    "_permission_preserving_receivables_count",
                    side_effect=AssertionError("count query should not run"),
                ):
                    payload = service.get_finance_control_desk_overview_context()

                self.assertEqual(payload["state"]["kind"], "unavailable")
                self.assertEqual(payload["scope"]["accounting_overview_enabled"], False)
                self.assertEqual(payload["scope"]["receivables_count_posture_enabled"], False)
                self.assertEqual(payload["scope"]["receivables_amount_summary_enabled"], False)
                self.assertIn(payload["company_scope"]["state"], {"unavailable", "selection_required", "restricted"})
                self.assertIsNone(payload["company_scope"]["company"])
                self.assertEqual(payload["receivables_posture"]["state"], "unavailable")
                self.assertEqual(payload["receivables_posture"]["bucket_counts"], {})
                self.assertEqual(payload["rows"], [])
                self.assertEqual(payload["amounts"], [])
                self.assertEqual(payload["documents"], [])

    def test_accounts_user_gets_no_raw_receivables_counts_from_overview(self):
        with patch.object(service.frappe, "get_roles", return_value=["Accounts User"]), patch.object(
            service,
            "resolve_finance_role_company_scope",
            return_value=_resolver(role_category="normal_finance"),
        ), patch.object(
            service,
            "_permission_preserving_receivables_count",
            side_effect=AssertionError("count query should not run"),
        ):
            payload = service.get_finance_control_desk_overview_context()

        self.assertEqual(payload["state"]["kind"], "ready")
        self.assertEqual(payload["scope"]["accounting_overview_enabled"], True)
        self.assertEqual(payload["scope"]["receivables_count_posture_enabled"], False)
        self.assertEqual(payload["scope"]["receivables_amount_summary_enabled"], False)
        self.assertEqual(payload["company_scope"]["state"], "scoped")
        self.assertEqual(payload["receivables_posture"]["state"], "unavailable")
        self.assertEqual(payload["receivables_posture"]["bucket_counts"], {})
        self.assertEqual(payload["receivables_posture"]["policy"]["reason"], "low_count_policy_not_ready")
        self.assertEqual(payload["receivables_posture"]["policy"]["accounts_user_raw_counts_enabled"], False)

    def test_overview_context_restricts_non_finance_roles_without_rows(self):
        with patch.object(service.frappe, "get_roles", return_value=["Sales User"]), patch.object(
            service.frappe.defaults,
            "get_user_default",
            return_value="Example Company",
        ):
            payload = service.get_finance_control_desk_overview_context()

        self.assertEqual(payload["state"]["kind"], "restricted")
        self.assertEqual(payload["scope"]["scope_mode"], "restricted")
        self.assertEqual(payload["scope"]["accounting_overview_enabled"], False)
        self.assertEqual(payload["company_scope"]["state"], "restricted")
        self.assertEqual(payload["posture_cards"], [])
        self.assertEqual(payload["lanes"], [])
        self.assertEqual(payload["rows"], [])

    def test_system_manager_executive_and_non_finance_get_no_receivables_counts(self):
        cases = [
            (["System Manager"], "system_admin_only"),
            (["Executive Approver"], "executive_only"),
            (["Sales Manager"], "restricted"),
        ]
        for roles, role_category in cases:
            with self.subTest(roles=roles):
                with patch.object(service.frappe, "get_roles", return_value=roles):
                    payload = service.get_finance_control_desk_overview_context()

                self.assertEqual(payload["state"]["kind"], "restricted")
                self.assertEqual(payload["scope"]["accounting_overview_enabled"], False)
                self.assertEqual(payload["scope"].get("receivables_count_posture_enabled"), False)
                self.assertEqual(payload["receivables_posture"], {})
                self.assertEqual(payload["receivables_amount_summary"], {})
                self.assertEqual(payload["rows"], [])
                self.assertEqual(payload["amounts"], [])
                self.assertEqual(payload["documents"], [])

    def test_system_manager_shell_access_does_not_grant_overview_access(self):
        with patch.object(service.frappe, "get_roles", return_value=["System Manager"]), patch.object(
            service.frappe.defaults,
            "get_user_default",
            return_value="Example Company",
        ):
            shell_payload = service.get_finance_control_desk_shell_context()
            overview_payload = service.get_finance_control_desk_overview_context()

        self.assertEqual(shell_payload["state"]["kind"], "ready")
        self.assertEqual(overview_payload["state"]["kind"], "restricted")
        self.assertEqual(overview_payload["scope"]["scope_mode"], "restricted")
        self.assertEqual(overview_payload["rows"], [])

    def test_search_is_unavailable_and_empty_for_f3(self):
        with patch.object(service.frappe, "get_roles", return_value=["Accounts User"]):
            payload = service.search_finance_control_desk_workspace("invoice")

        self.assertEqual(payload["state"], "unavailable")
        self.assertEqual(payload["groups"], [])
        self.assertEqual(payload["results"], [])
        self.assertTrue(all(value is False for value in payload["no_effect"].values()))

    def test_guest_is_rejected(self):
        frappe.session.user = "Guest"
        with self.assertRaises(frappe.PermissionError):
            service.get_finance_control_desk_shell_context()
        with self.assertRaises(frappe.PermissionError):
            service.get_finance_control_desk_overview_context()

    def test_frontend_calls_role_aware_overview_context(self):
        source = _frontend_source()

        self.assertIn(
            "erp_workspace_ui.finance_accounting.service.get_finance_control_desk_overview_context",
            source,
        )
        self.assertIn("frappe.call", source)
        self.assertIn("method: OVERVIEW_CONTEXT_METHOD", source)
        self.assertIn("payload.state", source)
        self.assertIn("payload.scope", source)
        self.assertIn("payload.posture_cards", source)
        self.assertIn("payload.overview", source)
        self.assertIn("payload.no_effect", source)

    def test_frontend_source_has_ready_restricted_loading_and_unavailable_contract(self):
        source = _frontend_source()

        for expected in (
            "renderReady",
            "renderRestricted",
            "renderLoading",
            "renderUnavailable",
            'data-finance-f3-overview="ready"',
            'data-finance-f3-overview="restricted"',
            'data-finance-f3-overview="loading"',
            'data-finance-f3-overview="unavailable"',
            "Finance Control Desk is restricted",
            "No row-level data shown",
            "Aggregate source reads only",
            "Read-only overview",
        ):
            self.assertIn(expected, source)

        self.assertIn("row-level accounting data is not returned, shown, linked, exported, or actionable", source)
        self.assertIn("Finance overview shows no row-level financial data", source)
        self.assertIn("Policy violation: row-level financial data was returned to this page", source)
        self.assertIn("renderPolicyViolation", source)
        self.assertNotIn("No financial rows loaded", source)
        self.assertNotIn("Finance overview contains no financial rows", source)
        self.assertNotIn("returned rows, but", source)
        self.assertNotIn("loads no financial rows", source)

    def test_frontend_blocks_nested_forbidden_finance_payload_shapes(self):
        source = _frontend_source()

        for expected in (
            "FORBIDDEN_COLLECTION_KEYS",
            "FORBIDDEN_IDENTITY_KEYS",
            "FORBIDDEN_SURFACE_KEYS",
            "hasForbiddenFinancePayloadShape",
            "renderPolicyViolation",
            "row_level_financial_data_returned",
            "payment_ledger_rows",
            "gl_rows",
            "voucher_no",
            "report_name",
            "download_url",
            "print_url",
            "email_sent",
            "notification_sent",
            "portal_action_performed",
            "payment_entry_created",
            "journal_entry_created",
            "reconciliation_performed",
            "tax_filing_performed",
            "period_close_performed",
            "erp_document_created",
            "native_route_opened",
            "report_run",
            "sendmail",
            "payment_reconciliation",
            "bank_reconciliation",
            "write_off",
            "customer_statement",
            "customer_reminder",
            "return renderPolicyViolation(normalized)",
        ):
            self.assertIn(expected, source)

        self.assertLess(source.index("hasFinancialRows(normalized)"), source.index('normalized.state.kind === "restricted"'))
        self.assertNotIn("financial_rows_loaded", source)

    def test_frontend_source_keeps_f3_boundary(self):
        source = _frontend_source()
        forbidden_patterns = [
            r"frappe\.get_all",
            r"frappe\.get_list\s*\(",
            r"frappe\.db\.sql",
            r"ignore_permissions",
            r"query-report",
            r"/app/",
            r"#Form/",
            r"frappe\.set_route",
            r"\.save\(",
            r"\.submit\(",
            r"\.cancel\(",
            r"insert\(",
            r"delete_doc",
            r"frappe\.set_value|set_value\s*\(",
            r"frappe\.enqueue|enqueue\s*\(",
            r"frappe\.sendmail|sendmail\s*\(",
            r"download\(",
            r"export_data",
            r"Sales Invoice",
            r"Purchase Invoice",
            r"GL Entry",
            r"Payment Entry",
            r"Journal Entry",
            r"Bank Transaction",
        ]
        for pattern in forbidden_patterns:
            self.assertIsNone(re.search(pattern, source), pattern)

        self.assertNotIn("rows.map", source)
        self.assertNotIn("rows.forEach", source)
        self.assertNotIn("renderRows", source)
        self.assertIn("hasFinancialRows", source)

    def test_backend_source_keeps_f3_boundary(self):
        source = _service_source()
        forbidden_patterns = [
            r"frappe\.get_all",
            r"frappe\.get_list\s*\(",
            r"frappe\.db\.sql",
            r"ignore_permissions",
            r"query-report",
            r"/app/",
            r"#Form/",
            r"frappe\.set_route",
            r"\.save\(",
            r"\.submit\(",
            r"\.cancel\(",
            r"insert\(",
            r"delete_doc",
            r"set_value",
            r"enqueue",
            r"sendmail",
            r"download\(",
            r"export_data",
            r"ignore_permissions",
        ]
        for pattern in forbidden_patterns:
            self.assertIsNone(re.search(pattern, source), pattern)
        self.assertIn('getattr(frappe, "get_list", None)', source)
        self.assertIn('getattr(frappe, "has_permission", None)', source)
        self.assertIn("public_context(context)", source)
        self.assertIn("Finance Control Desk is available for approved read-only posture", source)
        self.assertNotIn("F2 shell is registered", source)


    def test_f4d_doc_defines_shared_ui_future_contract_without_redesign_now(self):
        source = _F4D_DOC_SOURCE.read_text(encoding="utf-8")

        self.assertIn("Shared UI Future Contract", source)
        self.assertIn("shared workspace UI grammar", source)
        self.assertIn("stable page shell", source)
        self.assertIn("no blank first-load flashes", source)
        self.assertIn("should not copy Warehouse, Sales, or Procurement page-local classes blindly", source)
        self.assertIn("F4D does not redesign the Finance Control Desk", source)

    def test_f4k1_doc_defines_ar_copy_and_traceability_contract(self):
        source = _F4K1_DOC_SOURCE.read_text(encoding="utf-8")

        for expected in (
            "bounded aggregate source reads",
            "row-level data is not returned, shown, linked, exported, or actionable",
            "Sales Invoice aggregate count buckets",
            "Payment Ledger MMK amount buckets",
            "F4G remains the design-only Payment Ledger aggregate contract",
            "F4K1 does not approve live alignment",
        ):
            self.assertIn(expected, source)

        self.assertIn("avoid `no financial rows loaded`", source)

    def test_finance_sidebar_does_not_expose_native_notification_utility(self):
        source = _sidebar_source()

        self.assertIn('config.workspaceId === "warehouse" || config.workspaceId === "finance"', source)
        self.assertIn("openNativeNotifications", source)
        self.assertIn("data-erpw-sales-notifications-open", source)

    def test_finance_registry_targets_remain_page_only(self):
        from erp_workspace_ui.workspace_registry import get_finance_workspace_definition

        workspace = get_finance_workspace_definition()
        self.assertEqual(workspace["managed_doctypes"], {})
        self.assertEqual(workspace["directory_queues_by_doctype"], {})
        for item in workspace["fallback_items"]:
            self.assertEqual(item["target"]["kind"], "page")
            self.assertEqual(item["target"]["route"], "finance-control-desk")
            self.assertNotIn("doctype", item["target"])
            self.assertNotIn("report", item["target"])


if __name__ == "__main__":
    unittest.main()