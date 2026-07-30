"""Isolated source and Node tests for the premium Finance GL/TB page surface."""

from __future__ import annotations

import json
import subprocess
import unittest
from copy import deepcopy
from pathlib import Path


_SOURCE_ROOT = Path(__file__).resolve().parents[1]
_PAGE_SOURCE = (
    _SOURCE_ROOT
    / "erp_workspace_ui/page/finance_control_desk/finance_control_desk.js"
)
_QUERY = {
    "company": "COMPANY_A",
    "fiscal_year": "FY-2026",
    "from_date": "2026-01-01",
    "to_date": "2026-12-31",
}


def _amounts(*, distinct: bool = False) -> dict[str, str]:
    if distinct:
        return {
            "closing_credit": "6.00",
            "closing_debit": "5.00",
            "movement_credit": "4.00",
            "movement_debit": "3.00",
            "opening_credit": "2.00",
            "opening_debit": "1.00",
        }
    return {
        "closing_credit": "30.00",
        "closing_debit": "30.00",
        "movement_credit": "20.00",
        "movement_debit": "20.00",
        "opening_credit": "10.00",
        "opening_debit": "10.00",
    }


def _payload() -> dict[str, object]:
    return {
        "boundary": {
            "accounting_execution_enabled": False,
            "cancellation_control_claimed": False,
            "mutation_enabled": False,
            "party_identifiers_returned": False,
            "period_close_control_claimed": False,
            "read_only": True,
            "source_gl_entries_returned": False,
            "voucher_identifiers_returned": False,
        },
        "lines": [
            {
                "account_id": "1000 - Assets",
                "amounts": _amounts(distinct=True),
                "depth": 0,
                "is_group": True,
                "parent_account_id": None,
                "root_type": "Asset",
            },
            {
                "account_id": "1110 - Cash",
                "amounts": _amounts(),
                "depth": 1,
                "is_group": False,
                "parent_account_id": "1000 - Assets",
                "root_type": "Asset",
            },
        ],
        "schema_version": "finance-gl-trial-balance.internal.v2",
        "scope": {
            "active_dimensions": 0,
            "base_currency": "MMK",
            "company": "COMPANY_A",
            "currency_precision": 2,
            "default_finance_book": "DEFAULT_BOOK",
            "finance_book_scope": [
                "company_default",
                "blank_unbooked",
                "null_unbooked",
            ],
            "fiscal_year": "FY-2026",
            "fiscal_year_end": "2026-12-31",
            "fiscal_year_start": "2026-01-01",
            "from_date": "2026-01-01",
            "to_date": "2026-12-31",
        },
        "state": "ready",
        "totals": {
            "gross": _amounts(),
            "presentation": _amounts(),
        },
    }


def _node(script: str, *values: object) -> str:
    command = ["node", "-e", script, str(_PAGE_SOURCE)]
    command.extend(json.dumps(value, separators=(",", ":")) for value in values)
    result = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def _validate(payload: dict[str, object], query: dict[str, str] | None = None) -> bool:
    script = """
const ui = require(process.argv[1]);
const payload = JSON.parse(process.argv[2]);
const query = JSON.parse(process.argv[3]);
process.stdout.write(ui.validateGLTBPayload(payload, query) ? "true" : "false");
"""
    return _node(script, payload, query or _QUERY) == "true"


class FinanceGLTrialBalancePageTests(unittest.TestCase):
    def test_canonical_payload_renders_exact_accounting_column_order(self) -> None:
        script = """
const ui = require(process.argv[1]);
const payload = JSON.parse(process.argv[2]);
const query = JSON.parse(process.argv[3]);
const html = ui.renderGLTBReady(payload);
process.stdout.write(JSON.stringify({
  valid: ui.validateGLTBPayload(payload, query),
  html,
  balanced: ui.exactGLTBBalanceStatus(payload),
}));
"""
        result = json.loads(_node(script, _payload(), _QUERY))
        self.assertTrue(result["valid"])
        self.assertTrue(result["balanced"]["balanced"])
        self.assertEqual(result["balanced"]["label"], "Exactly balanced")
        html = result["html"]
        headers = [
            "Opening debit",
            "Opening credit",
            "Movement debit",
            "Movement credit",
            "Closing debit",
            "Closing credit",
        ]
        self.assertEqual([html.find(value) for value in headers], sorted(
            html.find(value) for value in headers
        ))
        expected_cells = (
            "<td>1.00</td><td>2.00</td><td>3.00</td>"
            "<td>4.00</td><td>5.00</td><td>6.00</td>"
        )
        self.assertIn(expected_cells, html)
        self.assertIn('scope="row"', html)
        self.assertIn('scope="col"', html)
        self.assertIn("<caption", html)
        for forbidden in ("<a ", "href=", "download=", "onclick=", "data-action="):
            self.assertNotIn(forbidden, html)

    def test_validator_rejects_unknown_types_scale_and_boundary_drift(self) -> None:
        cases: list[dict[str, object]] = []
        unknown = _payload()
        unknown["voucher_rows"] = []
        cases.append(unknown)
        line_unknown = _payload()
        line_unknown["lines"][0]["voucher_no"] = "JV-SECRET"  # type: ignore[index]
        cases.append(line_unknown)
        boolean_scope = _payload()
        boolean_scope["scope"]["active_dimensions"] = False  # type: ignore[index]
        cases.append(boolean_scope)
        numeric_amount = _payload()
        numeric_amount["lines"][0]["amounts"]["opening_debit"] = 1  # type: ignore[index]
        cases.append(numeric_amount)
        boundary_integer = _payload()
        boundary_integer["boundary"]["mutation_enabled"] = 0  # type: ignore[index]
        cases.append(boundary_integer)
        prior_schema = _payload()
        prior_schema["schema_version"] = "finance-gl-trial-balance.internal.v1"
        cases.append(prior_schema)
        for amount in ("-1.00", "01.00", "1e2", "1.0", "1.000", ""):
            malformed = _payload()
            malformed["lines"][0]["amounts"]["opening_debit"] = amount  # type: ignore[index]
            cases.append(malformed)
        for payload in cases:
            with self.subTest(payload=payload):
                self.assertFalse(_validate(payload))

    def test_validator_rejects_empty_and_malformed_hierarchy(self) -> None:
        cases: list[dict[str, object]] = []
        empty = _payload()
        empty["lines"] = []
        cases.append(empty)
        duplicate = _payload()
        duplicate["lines"][1]["account_id"] = "1000 - Assets"  # type: ignore[index]
        cases.append(duplicate)
        child_first = _payload()
        child_first["lines"].reverse()  # type: ignore[union-attr]
        cases.append(child_first)
        bad_depth = _payload()
        bad_depth["lines"][1]["depth"] = 2  # type: ignore[index]
        cases.append(bad_depth)
        bad_root = _payload()
        bad_root["lines"][1]["root_type"] = "Expense"  # type: ignore[index]
        cases.append(bad_root)
        bad_group = _payload()
        bad_group["lines"][0]["is_group"] = False  # type: ignore[index]
        cases.append(bad_group)
        for payload in cases:
            with self.subTest(payload=payload):
                self.assertFalse(_validate(payload))

    def test_validator_rejects_unbalanced_gross_and_presentation_totals(self) -> None:
        for cohort in ("gross", "presentation"):
            payload = _payload()
            payload["totals"][cohort]["closing_credit"] = "31.00"  # type: ignore[index]
            with self.subTest(cohort=cohort):
                self.assertFalse(_validate(payload))

    def test_validator_rejects_scope_request_and_finance_book_drift(self) -> None:
        cases: list[tuple[dict[str, object], dict[str, str]]] = []
        company = _payload()
        company["scope"]["company"] = "OTHER_COMPANY"  # type: ignore[index]
        cases.append((company, _QUERY))
        request = dict(_QUERY)
        request["from_date"] = "2026-02-01"
        cases.append((_payload(), request))
        cohort = _payload()
        cohort["scope"]["finance_book_scope"] = [  # type: ignore[index]
            "company_default",
            "null_unbooked",
            "blank_unbooked",
        ]
        cases.append((cohort, _QUERY))
        named_with_unbooked_scope = _payload()
        named_with_unbooked_scope["scope"]["finance_book_scope"] = [  # type: ignore[index]
            "blank_unbooked",
            "null_unbooked",
        ]
        cases.append((named_with_unbooked_scope, _QUERY))
        null_with_named_scope = _payload()
        null_with_named_scope["scope"]["default_finance_book"] = None  # type: ignore[index]
        cases.append((null_with_named_scope, _QUERY))
        for malformed_default in ("", " ", False):
            malformed = _payload()
            malformed["scope"]["default_finance_book"] = malformed_default  # type: ignore[index]
            cases.append((malformed, _QUERY))
        fiscal = _payload()
        fiscal["scope"]["fiscal_year_start"] = "2026-02-01"  # type: ignore[index]
        cases.append((fiscal, _QUERY))
        for payload, query in cases:
            with self.subTest(payload=payload, query=query):
                self.assertFalse(_validate(payload, query))

    def test_unbooked_only_v2_uses_fixed_non_named_label(self) -> None:
        payload = _payload()
        payload["scope"]["default_finance_book"] = None  # type: ignore[index]
        payload["scope"]["finance_book_scope"] = [  # type: ignore[index]
            "blank_unbooked",
            "null_unbooked",
        ]
        script = """
const ui = require(process.argv[1]);
const payload = JSON.parse(process.argv[2]);
const query = JSON.parse(process.argv[3]);
process.stdout.write(JSON.stringify({
  valid: ui.validateGLTBPayload(payload, query),
  html: ui.renderGLTBReady(payload),
}));
"""
        result = json.loads(_node(script, payload, _QUERY))

        self.assertTrue(result["valid"])
        self.assertIn("Unbooked only (blank or no Finance Book)", result["html"])
        self.assertNotIn("company_default", result["html"])
        self.assertNotIn("null |", result["html"])

    def test_renderer_escapes_account_and_finance_book_text(self) -> None:
        payload = _payload()
        hostile = "<img src=x onerror=alert(1)>"
        payload["lines"][0]["account_id"] = hostile  # type: ignore[index]
        payload["lines"][1]["parent_account_id"] = hostile  # type: ignore[index]
        payload["scope"]["default_finance_book"] = "<b>Book</b>"  # type: ignore[index]
        script = """
const ui = require(process.argv[1]);
const payload = JSON.parse(process.argv[2]);
const query = JSON.parse(process.argv[3]);
process.stdout.write(JSON.stringify({
  valid: ui.validateGLTBPayload(payload, query),
  html: ui.renderGLTBReady(payload),
}));
"""
        result = json.loads(_node(script, payload, _QUERY))
        self.assertTrue(result["valid"])
        self.assertNotIn("<img", result["html"])
        self.assertNotIn("<b>Book</b>", result["html"])
        self.assertIn("&lt;img", result["html"])
        self.assertIn("&lt;b&gt;Book&lt;/b&gt;", result["html"])

    def test_request_uses_exact_post_method_and_four_arguments(self) -> None:
        script = """
const ui = require(process.argv[1]);
const query = JSON.parse(process.argv[2]);
(async () => {
  let captured = null;
  const payload = await ui.createGLTrialBalanceRequest((request) => {
    captured = request;
    request.callback({ message: { marker: "canonical" } });
    return null;
  }, query);
  process.stdout.write(JSON.stringify({
    method: captured.method,
    type: captured.type,
    args: captured.args,
    keys: Object.keys(captured.args),
    payload,
  }));
})().catch(() => process.exit(2));
"""
        result = json.loads(_node(script, _QUERY))
        self.assertEqual(
            result["method"],
            "erp_workspace_ui.finance_accounting.gl_trial_balance_http."
            "get_gl_trial_balance",
        )
        self.assertEqual(result["type"], "POST")
        self.assertEqual(result["args"], _QUERY)
        self.assertEqual(
            result["keys"],
            ["company", "fiscal_year", "from_date", "to_date"],
        )
        self.assertEqual(result["payload"], {"marker": "canonical"})

    def test_invalid_query_is_rejected_without_calling_transport(self) -> None:
        query = dict(_QUERY)
        query["company"] = "OTHER\nCOMPANY"
        script = """
const ui = require(process.argv[1]);
const query = JSON.parse(process.argv[2]);
let calls = 0;
ui.createGLTrialBalanceRequest(() => { calls += 1; }, query)
  .then(() => process.exit(2))
  .catch(() => process.stdout.write(String(calls)));
"""
        self.assertEqual(_node(script, query), "0")

    def test_module_import_makes_no_automatic_gl_tb_request(self) -> None:
        script = """
let calls = 0;
global.frappe = { call() { calls += 1; } };
require(process.argv[1]);
process.stdout.write(String(calls));
"""
        self.assertEqual(_node(script), "0")

    def test_request_coordinator_discards_older_result(self) -> None:
        script = """
const ui = require(process.argv[1]);
(async () => {
  const pending = [];
  const observed = [];
  const coordinator = ui.createGLTBRequestCoordinator((query) => (
    new Promise((resolve) => pending.push({ query, resolve }))
  ));
  const first = coordinator.load({ id: 1 }, {
    onPayload(payload) { observed.push(payload.id); },
  });
  await Promise.resolve();
  const second = coordinator.load({ id: 2 }, {
    onPayload(payload) { observed.push(payload.id); },
  });
  await Promise.resolve();
  pending[0].resolve({ id: 1 });
  pending[1].resolve({ id: 2 });
  const results = await Promise.all([first, second]);
  process.stdout.write(JSON.stringify({ observed, results }));
})().catch(() => process.exit(2));
"""
        result = json.loads(_node(script))
        self.assertEqual(result["observed"], [2])
        self.assertTrue(result["results"][0]["stale"])
        self.assertFalse(result["results"][1]["stale"])

    def test_invalidation_purges_result_without_payload_cache(self) -> None:
        script = """
const ui = require(process.argv[1]);
let invalidations = 0;
const host = {
  innerHTML: "SECRET_RESULT",
  setAttribute(name, value) { this[name] = value; },
};
const live = { textContent: "" };
const submit = { disabled: false };
const form = { querySelector() { return submit; } };
const target = {
  __financeGLTBRequestCoordinator: {
    invalidate() { invalidations += 1; },
  },
  querySelector(selector) {
    if (selector === "[data-finance-gltb-state-host]") return host;
    if (selector === "[data-finance-gltb-live-status]") return live;
    if (selector === "[data-finance-gltb-form]") return form;
    return null;
  },
};
ui.invalidateGLTBResults(target, "empty");
process.stdout.write(JSON.stringify({
  invalidations,
  html: host.innerHTML,
  live: live.textContent,
  keys: Object.keys(target),
}));
"""
        result = json.loads(_node(script))
        self.assertEqual(result["invalidations"], 1)
        self.assertNotIn("SECRET_RESULT", result["html"])
        self.assertIn('data-finance-gltb-state="empty"', result["html"])
        self.assertNotIn("__financeGLTBPayload", result["keys"])

    def test_workspace_has_accessible_explicit_form_and_all_fixed_states(self) -> None:
        script = """
const ui = require(process.argv[1]);
const ready = ui.renderGLTBWorkspace("COMPANY_A", "empty", ["Accounts Manager"]);
const denied = ui.renderGLTBWorkspace("", "denied");
const states = ["empty", "loading", "denied", "unavailable", "error"]
  .map((state) => ui.renderGLTBState(state));
process.stdout.write(JSON.stringify({ ready, denied, states }));
"""
        result = json.loads(_node(script))
        ready = result["ready"]
        self.assertIn("<form", ready)
        self.assertIn('name="fiscal_year"', ready)
        self.assertIn('name="from_date" type="date"', ready)
        self.assertIn('name="to_date" type="date"', ready)
        self.assertIn("<output", ready)
        self.assertIn('type="submit"', ready)
        self.assertIn('aria-labelledby="finance-gltb-title"', ready)
        self.assertIn('data-finance-gltb-live-status="1"', ready)
        self.assertNotIn("<form", result["denied"])
        self.assertIn('data-finance-gltb-state="denied"', result["denied"])
        for state, html in zip(
            ("empty", "loading", "denied", "unavailable", "error"),
            result["states"],
            strict=True,
        ):
            self.assertIn(f'data-finance-gltb-state="{state}"', html)

    def test_workspace_role_presentation_matches_bridge_policy(self) -> None:
        script = """
const ui = require(process.argv[1]);
const roles = [
  ["Accounts Manager"],
  ["Accounts User"],
  ["Auditor"],
  ["Accounts Manager", "System Manager"],
  ["Accounts Manager", "Administrator"],
  ["Accounts Manager", "Bypass Finance Scope"],
];
process.stdout.write(JSON.stringify(roles.map((value) => ({
  allowed: ui.hasGLTBPresentationRole(value),
  html: ui.renderGLTBWorkspace("COMPANY_A", "empty", value),
}))));
"""
        results = json.loads(_node(script))
        self.assertTrue(results[0]["allowed"])
        self.assertIn("<form", results[0]["html"])
        for result in results[1:]:
            self.assertFalse(result["allowed"])
            self.assertNotIn("<form", result["html"])
            self.assertIn('data-finance-gltb-state="denied"', result["html"])

    def test_source_freezes_purge_responsive_and_containment_boundaries(self) -> None:
        source = _PAGE_SOURCE.read_text(encoding="utf-8", errors="strict")
        load_start = source.index("function loadOverviewContext")
        load_end = source.index("function bindFinancePageHide", load_start)
        load_source = source[load_start:load_end]
        self.assertLess(
            load_source.index('invalidateGLTBResults(target, "empty")'),
            load_source.index("setHtml(target, renderLoading())"),
        )
        invalidate_start = source.index("function invalidateTarget")
        invalidate_end = source.index("function hide", invalidate_start)
        self.assertIn(
            'invalidateGLTBResults(target, "empty")',
            source[invalidate_start:invalidate_end],
        )
        self.assertIn("@media (max-width: 860px)", source)
        self.assertIn("@media (max-width: 420px)", source)
        self.assertIn(".finance-gltb-input:focus-visible", source)
        self.assertIn(".finance-gltb-table-wrap", source)
        self.assertNotIn("__financeGLTBPayload", source)
        self.assertNotIn("frappe.db", source)
        self.assertNotIn("ignore_permissions", source)
        self.assertEqual(source.count("GL_TRIAL_BALANCE_METHOD"), 2)


if __name__ == "__main__":
    unittest.main()
