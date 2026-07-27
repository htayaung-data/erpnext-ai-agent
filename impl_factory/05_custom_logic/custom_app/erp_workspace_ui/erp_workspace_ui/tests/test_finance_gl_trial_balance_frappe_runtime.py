from __future__ import annotations

import builtins
import importlib.util
import io
import os
import socket
import sys
import types
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

from erp_workspace_ui.finance_accounting.gl_trial_balance_adapter import (
    GLTrialBalanceAdapterError,
)
from erp_workspace_ui.finance_accounting.gl_trial_balance_frappe_runtime import (
    FrappeGLTrialBalanceRuntime,
    GLTrialBalanceRuntimePolicy,
)


USER = "accounts.manager@example.test"
COMPANY = "COMPANY_A"
SERVER = "10.11.18-MariaDB-test"
CONNECTION_ID = 731


class _Cursor:
    def __init__(self, raw: "_RawBase") -> None:
        self.raw = raw
        self.row: tuple[object, ...] | None = None
        self.consumed = False
        self.closed = False
        self.statement: str | None = None
        self.occurrence = 0

    def execute(self, statement: str, parameters: object = None) -> None:
        self.statement = statement
        self.row, self.occurrence = self.raw.execute(statement, parameters)

    def fetchone(self) -> tuple[object, ...] | None:
        if self.consumed:
            return None
        self.consumed = True
        return self.row

    def close(self) -> None:
        if (self.statement, self.occurrence) == self.raw.fail_cursor_close:
            raise RuntimeError("LEAK_CURSOR_CLOSE COMPANY_A")
        self.closed = True


class _RawBase:
    def __init__(self) -> None:
        self.server = SERVER
        self.connection_id = CONNECTION_ID
        self.active: object = False
        self.closed = False
        self.fail_statement: str | None = None
        self.fail_execute: tuple[str | None, int] = (None, 0)
        self.fail_cursor_close: tuple[str | None, int] = (None, 0)
        self.statement_counts: dict[str, int] = {}
        self.after_statement: dict[str, object] = {}
        self.statements: list[tuple[str, object]] = []
        self.account_count: object = 2
        self.gl_count: object = 1
        self.fiscal_states: dict[str, tuple[object, object]] = {
            "FY_GLOBAL": (0, 0)
        }
        self.state_override: tuple[object, ...] | None = None
        self.state_overrides: dict[int, tuple[object, ...]] = {}

    def cursor(self) -> _Cursor:
        return _Cursor(self)

    def execute(
        self, statement: str, parameters: object
    ) -> tuple[tuple[object, ...] | None, int]:
        self.statements.append((statement, parameters))
        occurrence = self.statement_counts.get(statement, 0) + 1
        self.statement_counts[statement] = occurrence
        if (statement, occurrence) == self.fail_execute:
            raise RuntimeError("LEAK_OCCURRENCE SELECT COMPANY_A FY_GLOBAL ROOT GL1 731")
        if statement == self.fail_statement:
            raise RuntimeError("LEAK_SQL company=COMPANY_A")
        row: tuple[object, ...] | None
        if statement.startswith("SELECT VERSION()"):
            row = self.state_overrides.get(occurrence)
            if row is None:
                row = self.state_override or (
                    self.server,
                    self.connection_id,
                    int(self.active)
                    if type(self.active) is bool
                    else self.active,
                )
        elif statement == "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ":
            row = None
        elif statement == "START TRANSACTION READ ONLY, WITH CONSISTENT SNAPSHOT":
            self.active = True
            row = None
        elif statement == "ROLLBACK AND NO CHAIN":
            self.active = False
            row = None
        elif "FROM `tabAccount`" in statement:
            row = (self.account_count,)
        elif "FROM `tabGL Entry`" in statement:
            row = (self.gl_count,)
        elif "FROM `tabFiscal Year Company`" in statement:
            assert isinstance(parameters, dict)
            row = self.fiscal_states[parameters["fiscal_year"]]
        else:
            raise AssertionError("unexpected statement")
        callback = self.after_statement.get(statement)
        if callable(callback):
            callback()
        return row, occurrence

    def close(self) -> None:
        self.closed = True
        self.active = False


def _driver_types(driver: str) -> tuple[type, type]:
    if driver == "pymysql":
        wrapper_module = "frappe.database.mariadb.database"
        raw_module = "pymysql.connections"
    else:
        wrapper_module = "frappe.database.mariadb.mysqlclient"
        raw_module = "MySQLdb.connections"
    raw_type = type("Connection", (_RawBase,), {"__module__": raw_module})
    wrapper_type = type("MariaDBDatabase", (), {"__module__": wrapper_module})
    return wrapper_type, raw_type


class _Frappe:
    def __init__(self, driver: str = "pymysql") -> None:
        wrapper_type, raw_type = _driver_types(driver)
        self.raw = raw_type()
        wrapper = wrapper_type()
        wrapper._conn = self.raw
        self.local = types.SimpleNamespace(
            db=wrapper,
            session={"user": USER},
            conf={},
            primary_db=None,
            replica_db=None,
        )
        self.roles: list[str] = ["Accounts Manager"]
        self.permission_result: object = True
        self.permission_calls: list[dict[str, object]] = []
        self.list_calls: list[tuple[str, dict[str, object]]] = []
        self.return_rows_verbatim = False
        self.distribution_calls: list[str] = []
        self.rows: dict[str, list[dict[str, object]]] = {
            "Company": [{"name": COMPANY, "default_currency": "MMK", "default_finance_book": "BOOK"}],
            "Finance Book": [{"name": "BOOK", "finance_book_name": "Default"}],
            "Accounting Dimension": [],
            "Fiscal Year": [
                {
                    "name": "FY_GLOBAL",
                    "year_start_date": date(2026, 1, 1),
                    "year_end_date": date(2026, 12, 31),
                    "disabled": 0,
                }
            ],
            "Fiscal Year Company": [],
            "Account": [
                {
                    "name": "ROOT",
                    "company": COMPANY,
                    "parent_account": None,
                    "is_group": 1,
                    "root_type": "Asset",
                    "lft": 1,
                    "rgt": 4,
                    "account_currency": "MMK",
                    "disabled": 0,
                },
                {
                    "name": "CASH",
                    "company": COMPANY,
                    "parent_account": "ROOT",
                    "is_group": 0,
                    "root_type": "Asset",
                    "lft": 2,
                    "rgt": 3,
                    "account_currency": "MMK",
                    "disabled": 0,
                },
            ],
            "GL Entry": [
                {
                    "name": "GL1",
                    "company": COMPANY,
                    "posting_date": date(2026, 1, 31),
                    "account": "CASH",
                    "debit": 1,
                    "credit": 0,
                    "is_cancelled": 0,
                    "is_opening": "No",
                    "finance_book": "BOOK",
                }
            ],
        }

    def get_roles(self, user: str) -> list[str]:
        self.raw.connection_id += 0
        return list(self.roles)

    def has_permission(self, **kwargs: object) -> object:
        self.permission_calls.append(dict(kwargs))
        return self.permission_result

    def get_list(self, doctype: str, **kwargs: object) -> list[dict[str, object]]:
        self.list_calls.append((doctype, dict(kwargs)))
        fields = tuple(kwargs["fields"])
        result = []
        for source in self.rows.get(doctype, []):
            if self.return_rows_verbatim:
                result.append(dict(source))
            else:
                result.append({field: source[field] for field in fields})
        return result[: int(kwargs["limit"])]


class _Permissions:
    def __init__(self) -> None:
        self.value: object = {
            "Company": [
                {
                    "doc": COMPANY,
                    "applicable_for": None,
                    "is_default": 1,
                    "hide_descendants": 0,
                }
            ]
        }

    def get_user_permissions(self, user: str) -> object:
        return self.value


def _runtime(
    driver: str = "pymysql",
    *,
    server: str = SERVER,
    actual_distribution: str | None = None,
) -> tuple[FrappeGLTrialBalanceRuntime, _Frappe, _Permissions]:
    frappe = _Frappe(driver)
    permissions = _Permissions()
    version = "1.1.2" if driver == "pymysql" else "2.2.7"
    installed_version = actual_distribution or version
    runtime = FrappeGLTrialBalanceRuntime(
        frappe_module=frappe,
        permissions_module=permissions,
        policy=GLTrialBalanceRuntimePolicy(
            expected_driver=driver,
            expected_driver_version=version,
            expected_server_version=server,
        ),
        distribution_version=lambda name: (frappe.distribution_calls.append(name), installed_version)[1],
    )
    return runtime, frappe, permissions


def _begin(runtime: FrappeGLTrialBalanceRuntime):
    return runtime.begin_read_snapshot(USER, COMPANY)


class FrappeRuntimeTests(unittest.TestCase):
    def assertUnavailable(self, call) -> GLTrialBalanceAdapterError:
        with self.assertRaises(GLTrialBalanceAdapterError) as caught:
            call()
        self.assertEqual(str(caught.exception), "finance_read_unavailable")
        self.assertEqual(caught.exception.args, ("finance_read_unavailable",))
        self.assertEqual(
            repr(caught.exception),
            "GLTrialBalanceAdapterError('finance_read_unavailable')",
        )
        self.assertIsNone(caught.exception.__cause__)
        self.assertIsNone(caught.exception.__context__)
        rendered = str(caught.exception)
        for leakage in (
            "COMPANY",
            "SELECT",
            USER,
            "FY_GLOBAL",
            "ROOT",
            "GL1",
            str(CONNECTION_ID),
            "LEAK",
        ):
            self.assertNotIn(leakage, rendered)
        return caught.exception

    def test_both_supported_driver_branches_and_exact_statement_order(self) -> None:
        for driver in ("pymysql", "mysqlclient"):
            with self.subTest(driver=driver):
                runtime, frappe, _ = _runtime(driver)
                snapshot = _begin(runtime)
                self.assertEqual(snapshot.transaction_isolation, "REPEATABLE READ")
                runtime.close_read_snapshot(snapshot)
                probe = "SELECT VERSION(), CONNECTION_ID(), @@in_transaction"
                self.assertEqual(
                    frappe.raw.statements,
                    [
                        (probe, None),
                        (
                            "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ",
                            None,
                        ),
                        (
                            "START TRANSACTION READ ONLY, "
                            "WITH CONSISTENT SNAPSHOT",
                            None,
                        ),
                        (probe, None),
                        (probe, None),
                        ("ROLLBACK AND NO CHAIN", None),
                        (probe, None),
                    ],
                )
                self.assertFalse(frappe.raw.active)
                self.assertFalse(frappe.raw.closed)

    def test_unknown_driver_and_environment_mismatches_fail_closed(self) -> None:
        for mutation in ("unknown", "driver-version", "server", "preexisting"):
            with self.subTest(mutation=mutation):
                if mutation == "unknown":
                    with self.assertRaises(GLTrialBalanceAdapterError):
                        GLTrialBalanceRuntimePolicy("other", "1", SERVER)
                        FrappeGLTrialBalanceRuntime(
                            frappe_module=object(),
                            permissions_module=object(),
                            policy=GLTrialBalanceRuntimePolicy("other", "1", SERVER),
                        )
                    continue
                runtime, frappe, _ = _runtime(
                    actual_distribution="0.0" if mutation == "driver-version" else None
                )
                if mutation == "server":
                    frappe.raw.server = "wrong"
                if mutation == "preexisting":
                    frappe.raw.active = True
                self.assertUnavailable(lambda: _begin(runtime))

    def test_transaction_statement_failures_discard_and_close(self) -> None:
        for statement in (
            "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ",
            "START TRANSACTION READ ONLY, WITH CONSISTENT SNAPSHOT",
        ):
            with self.subTest(statement=statement):
                runtime, frappe, _ = _runtime()
                frappe.raw.fail_statement = statement
                self.assertUnavailable(lambda: _begin(runtime))
                self.assertTrue(frappe.raw.closed)

    def test_roles_user_permissions_and_all_nine_permission_calls(self) -> None:
        runtime, frappe, _ = _runtime()
        snapshot = _begin(runtime)
        evidence = runtime.effective_permission_evidence(snapshot)
        self.assertEqual(evidence.roles, ("Accounts Manager",))
        self.assertEqual(evidence.user_permissions[0].for_value, COMPANY)
        requirements = (
            ("Company", "read"),
            ("Fiscal Year", "read"),
            ("Fiscal Year Company", "read"),
            ("Finance Book", "read"),
            ("Accounting Dimension", "read"),
            ("Account", "read"),
            ("Account", "report"),
            ("GL Entry", "read"),
            ("GL Entry", "report"),
        )
        for doctype, permission_type in requirements:
            self.assertTrue(
                runtime.has_permission(
                    snapshot, USER, doctype, permission_type
                )
            )
        self.assertEqual(
            frappe.permission_calls,
            [
                {
                    "doctype": doctype,
                    "ptype": permission_type,
                    "user": USER,
                    "throw": False,
                    "parent_doctype": (
                        "Fiscal Year"
                        if doctype == "Fiscal Year Company"
                        else None
                    ),
                }
                for doctype, permission_type in requirements
            ],
        )

    def test_account_manifest_completeness_and_hidden_account_denial(self) -> None:
        runtime, frappe, _ = _runtime()
        snapshot = _begin(runtime)
        manifest = runtime.complete_account_manifest(snapshot, COMPANY, 4)
        self.assertEqual(manifest.account_ids, ("ROOT", "CASH"))
        self.assertEqual(manifest.root_account_ids, ("ROOT",))
        frappe.raw.account_count = 3
        self.assertUnavailable(
            lambda: runtime.complete_account_manifest(snapshot, COMPANY, 4)
        )

    def test_gl_query_shape_and_hidden_gl_denial(self) -> None:
        runtime, frappe, _ = _runtime()
        snapshot = _begin(runtime)
        rows = runtime.get_list(
            snapshot,
            "GL Entry",
            (
                "name", "company", "posting_date", "account", "debit", "credit",
                "is_cancelled", "is_opening", "finance_book",
            ),
            (("company", "=", COMPANY), ("posting_date", "<=", date(2026, 12, 31)), ("is_cancelled", "=", 0)),
            (("finance_book", "=", "BOOK"), ("finance_book", "=", ""), ("finance_book", "is", "not set")),
            "posting_date asc, name asc",
            3,
        )
        self.assertEqual(len(rows), 1)
        aggregate = next(item for item in frappe.raw.statements if "tabGL Entry" in item[0])
        self.assertEqual(
            aggregate[1],
            {"company": COMPANY, "to_date": date(2026, 12, 31), "finance_book": "BOOK"},
        )
        frappe.raw.gl_count = 2
        self.assertUnavailable(
            lambda: runtime.get_list(
                snapshot,
                "GL Entry",
                ("name", "company", "posting_date", "account", "debit", "credit", "is_cancelled", "is_opening", "finance_book"),
                (("company", "=", COMPANY), ("posting_date", "<=", date(2026, 12, 31)), ("is_cancelled", "=", 0)),
                (("finance_book", "=", "BOOK"), ("finance_book", "=", ""), ("finance_book", "is", "not set")),
                "posting_date asc, name asc",
                3,
            )
        )

    def test_fiscal_states_do_not_expose_other_company_identity(self) -> None:
        for fiscal, aggregate, expected in (
            ("FY_GLOBAL", (0, 0), "global"),
            ("FY_SELECTED", (1, 1), "selected_company"),
            ("FY_EXCLUDED", (1, 0), "excluded"),
        ):
            with self.subTest(fiscal=fiscal):
                runtime, frappe, _ = _runtime()
                frappe.rows["Fiscal Year"] = [{"name": fiscal}]
                frappe.raw.fiscal_states = {fiscal: aggregate}
                snapshot = _begin(runtime)
                result = runtime.complete_fiscal_year_applicability(
                    snapshot, COMPANY, 2
                )
                self.assertEqual(result.fiscal_year_applicability, ((fiscal, expected),))
                self.assertNotIn("OTHER", repr(frappe.raw.statements))

    def test_fiscal_child_query_adds_exact_parent_authority(self) -> None:
        runtime, frappe, _ = _runtime()
        snapshot = _begin(runtime)
        runtime.get_list(
            snapshot,
            "Fiscal Year Company",
            ("parent", "company"),
            (("parent", "in", ("FY_GLOBAL",)), ("company", "=", COMPANY)),
            (),
            "parent asc, company asc",
            2,
        )
        kwargs = frappe.list_calls[-1][1]
        self.assertEqual(kwargs["parent_doctype"], "Fiscal Year")
        self.assertIn(["parenttype", "=", "Fiscal Year"], kwargs["filters"])
        self.assertIn(["parentfield", "=", "companies"], kwargs["filters"])
        self.assertFalse(kwargs["ignore_permissions"])
        self.assertNotIn("ignore_user_permissions", kwargs)

    def test_wrapper_raw_connection_id_and_transaction_loss_are_rejected(self) -> None:
        for mutation in ("wrapper", "raw", "connection-id", "transaction"):
            with self.subTest(mutation=mutation):
                runtime, frappe, _ = _runtime()
                snapshot = _begin(runtime)
                if mutation == "wrapper":
                    frappe.local.db = object()
                elif mutation == "raw":
                    frappe.local.db._conn = _driver_types("pymysql")[1]()
                elif mutation == "connection-id":
                    frappe.raw.connection_id += 1
                else:
                    frappe.raw.active = False
                self.assertUnavailable(lambda: runtime.final_snapshot_evidence(snapshot))

    def test_permission_and_manifest_drift_are_observable(self) -> None:
        runtime, frappe, permissions = _runtime()
        snapshot = _begin(runtime)
        initial = runtime.effective_permission_evidence(snapshot)
        frappe.roles.append("System Manager")
        final = runtime.effective_permission_evidence(snapshot)
        self.assertNotEqual(initial, final)
        permissions.value = {"Company": []}
        changed = runtime.effective_permission_evidence(snapshot)
        self.assertNotEqual(final, changed)

    def test_cleanup_is_idempotent_and_rollback_failure_closes_raw(self) -> None:
        runtime, frappe, _ = _runtime()
        snapshot = _begin(runtime)
        runtime.close_read_snapshot(snapshot)
        runtime.close_read_snapshot(snapshot)
        self.assertFalse(frappe.raw.closed)

        runtime, frappe, _ = _runtime()
        snapshot = _begin(runtime)
        frappe.raw.fail_statement = "ROLLBACK AND NO CHAIN"
        self.assertUnavailable(lambda: runtime.close_read_snapshot(snapshot))
        self.assertTrue(frappe.raw.closed)
        runtime.close_read_snapshot(snapshot)

    def test_replica_and_cross_company_rows_fail_closed(self) -> None:
        runtime, frappe, _ = _runtime()
        frappe.local.conf["read_from_replica"] = True
        self.assertUnavailable(lambda: _begin(runtime))

        runtime, frappe, _ = _runtime()
        snapshot = _begin(runtime)
        frappe.rows["Account"][0]["company"] = "COMPANY_B"
        self.assertUnavailable(
            lambda: runtime.get_list(
                snapshot,
                "Account",
                ("name", "company", "parent_account", "is_group", "root_type", "lft", "rgt", "account_currency", "disabled"),
                (("company", "=", COMPANY),),
                (),
                "lft asc, name asc",
                4,
            )
        )

    def test_malformed_permission_and_sql_error_never_leak(self) -> None:
        runtime, frappe, permissions = _runtime()
        snapshot = _begin(runtime)
        permissions.value = {"Company": [{"doc": "LEAK", "bad": 1}]}
        self.assertUnavailable(lambda: runtime.effective_permission_evidence(snapshot))
        frappe.raw.fail_statement = "SELECT COUNT(DISTINCT `name`) FROM `tabAccount` WHERE `company` = %(company)s"
        self.assertUnavailable(
            lambda: runtime.complete_account_manifest(snapshot, COMPANY, 4)
        )

    def test_module_has_no_frappe_import_or_default_runtime(self) -> None:
        module = __import__(
            "erp_workspace_ui.finance_accounting.gl_trial_balance_frappe_runtime",
            fromlist=["FrappeGLTrialBalanceRuntime"],
        )
        self.assertNotIn("frappe", module.__dict__)
        self.assertFalse(hasattr(module, "runtime"))


    def test_session_and_transaction_continuity_drift_close_exceptionally(self) -> None:
        for mutation in ("session", "transaction"):
            with self.subTest(mutation=mutation):
                runtime, frappe, _ = _runtime()
                snapshot = _begin(runtime)
                if mutation == "session":
                    frappe.local.session["user"] = "other@example.test"
                else:
                    frappe.raw.active = False
                self.assertUnavailable(
                    lambda: runtime.final_snapshot_evidence(snapshot)
                )
                self.assertTrue(frappe.raw.closed)

    def test_close_window_replacement_and_class_drift_are_rejected(self) -> None:
        for mutation in (
            "close-wrapper",
            "wrapper-class",
            "raw-class",
            "close-transaction",
        ):
            with self.subTest(mutation=mutation):
                runtime, frappe, _ = _runtime()
                snapshot = _begin(runtime)
                if mutation == "close-wrapper":
                    wrapper_type, raw_type = _driver_types("pymysql")
                    replacement = wrapper_type()
                    replacement._conn = raw_type()
                    frappe.raw.after_statement["ROLLBACK AND NO CHAIN"] = (
                        lambda: setattr(frappe.local, "db", replacement)
                    )
                elif mutation == "wrapper-class":
                    type(frappe.local.db).__module__ = "unapproved.wrapper"
                elif mutation == "raw-class":
                    type(frappe.raw).__module__ = "unapproved.raw"
                else:
                    frappe.raw.active = False
                self.assertUnavailable(
                    lambda: runtime.close_read_snapshot(snapshot)
                )
                self.assertTrue(frappe.raw.closed)

    def test_strict_db_permission_and_user_permission_flags(self) -> None:
        runtime, frappe, _ = _runtime()
        frappe.raw.active = 0
        frappe.raw.state_override = (SERVER, CONNECTION_ID, False)
        self.assertUnavailable(lambda: _begin(runtime))
        self.assertTrue(frappe.raw.closed)

        runtime, frappe, permissions = _runtime()
        snapshot = _begin(runtime)
        permissions.value["Company"][0]["is_default"] = True
        self.assertUnavailable(
            lambda: runtime.effective_permission_evidence(snapshot)
        )

        runtime, frappe, _ = _runtime()
        snapshot = _begin(runtime)
        frappe.permission_result = 1
        self.assertUnavailable(
            lambda: runtime.has_permission(
                snapshot, USER, "Company", "read"
            )
        )

        runtime, frappe, _ = _runtime()
        snapshot = _begin(runtime)
        frappe.raw.fiscal_states["FY_GLOBAL"] = (False, False)
        self.assertUnavailable(
            lambda: runtime.complete_fiscal_year_applicability(
                snapshot, COMPANY, 2
            )
        )

    def test_cursor_close_failures_are_discarded_and_physically_closed(self) -> None:
        probe = "SELECT VERSION(), CONNECTION_ID(), @@in_transaction"
        account_sql = "SELECT COUNT(DISTINCT `name`) FROM `tabAccount` WHERE `company` = %(company)s"
        cases = (
            (probe, 1, "begin"),
            ("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ", 1, "begin"),
            (probe, 2, "begin"),
            (account_sql, 1, "aggregate"),
        )
        for statement, occurrence, phase in cases:
            with self.subTest(statement=statement, occurrence=occurrence):
                runtime, frappe, _ = _runtime()
                frappe.raw.fail_cursor_close = (statement, occurrence)
                if phase == "begin":
                    self.assertUnavailable(lambda: _begin(runtime))
                else:
                    snapshot = _begin(runtime)
                    self.assertUnavailable(
                        lambda: runtime.complete_account_manifest(
                            snapshot, COMPANY, 4
                        )
                    )
                self.assertTrue(frappe.raw.closed)

    def test_exact_distribution_lookup_and_policy_state_rejections(self) -> None:
        for driver, package in (("pymysql", "PyMySQL"), ("mysqlclient", "mysqlclient")):
            with self.subTest(driver=driver):
                runtime, frappe, _ = _runtime(driver)
                _begin(runtime)
                self.assertEqual(frappe.distribution_calls, [package])

        for policy in (
            None,
            GLTrialBalanceRuntimePolicy("pymysql", "1.1.2", ""),
            GLTrialBalanceRuntimePolicy("pymysql", "2.2.7", SERVER),
        ):
            with self.subTest(policy=policy):
                self.assertUnavailable(
                    lambda policy=policy: FrappeGLTrialBalanceRuntime(
                        frappe_module=object(),
                        permissions_module=object(),
                        policy=policy,
                    )
                )

        for malformed in (
            (SERVER, CONNECTION_ID),
            (SERVER, CONNECTION_ID, 0, "extra"),
            (SERVER, "731", 0),
        ):
            with self.subTest(malformed=malformed):
                runtime, frappe, _ = _runtime()
                frappe.raw.state_override = malformed
                self.assertUnavailable(lambda: _begin(runtime))
                self.assertTrue(frappe.raw.closed)

    def test_exact_permission_preserving_list_query_matrix(self) -> None:
        runtime, frappe, _ = _runtime()
        snapshot = _begin(runtime)
        calls = (
            ("Company", ("name", "default_currency", "default_finance_book"), (("name", "=", COMPANY),), (), "name asc"),
            ("Fiscal Year", ("name", "year_start_date", "year_end_date", "disabled"), (("disabled", "=", 0),), (), "year_start_date asc, name asc"),
            ("Fiscal Year Company", ("parent", "company"), (("parent", "in", ("FY_GLOBAL",)), ("company", "=", COMPANY)), (), "parent asc, company asc"),
            ("Finance Book", ("name", "finance_book_name"), (("name", "=", "BOOK"),), (), "name asc"),
            ("Accounting Dimension", ("name", "document_type", "fieldname", "disabled"), (("disabled", "=", 0),), (), "name asc"),
            ("Account", ("name", "company", "parent_account", "is_group", "root_type", "lft", "rgt", "account_currency", "disabled"), (("company", "=", COMPANY),), (), "lft asc, name asc"),
            ("GL Entry", ("name", "company", "posting_date", "account", "debit", "credit", "is_cancelled", "is_opening", "finance_book"), (("company", "=", COMPANY), ("posting_date", "<=", date(2026, 12, 31)), ("is_cancelled", "=", 0)), (("finance_book", "=", "BOOK"), ("finance_book", "=", ""), ("finance_book", "is", "not set")), "posting_date asc, name asc"),
        )
        for doctype, fields, filters, or_filters, order_by in calls:
            runtime.get_list(snapshot, doctype, fields, filters, or_filters, order_by, 4)
            name, kwargs = frappe.list_calls[-1]
            self.assertEqual(name, doctype)
            self.assertEqual(kwargs["fields"], list(fields))
            expected_filters = [list(item) for item in filters]
            if doctype == "Fiscal Year Company":
                expected_filters += [["parenttype", "=", "Fiscal Year"], ["parentfield", "=", "companies"]]
            self.assertEqual(kwargs["filters"], expected_filters)
            self.assertEqual(kwargs["or_filters"], [list(item) for item in or_filters])
            self.assertEqual(kwargs["order_by"], order_by)
            self.assertEqual(kwargs["limit"], 4)
            self.assertFalse(kwargs["ignore_permissions"])
            self.assertFalse(kwargs["as_list"])
            self.assertNotIn("ignore_user_permissions", kwargs)

    def test_multi_company_permission_and_company_isolation(self) -> None:
        runtime, frappe, permissions = _runtime()
        permissions.value["Company"].append(
            {"doc": "COMPANY_B", "applicable_for": None, "is_default": 0, "hide_descendants": 0}
        )
        snapshot = _begin(runtime)
        evidence = runtime.effective_permission_evidence(snapshot)
        self.assertEqual(
            {rule.for_value for rule in evidence.user_permissions},
            {COMPANY, "COMPANY_B"},
        )
        frappe.rows["Company"][0]["name"] = "COMPANY_B"
        self.assertUnavailable(
            lambda: runtime.get_list(
                snapshot,
                "Company",
                ("name", "default_currency", "default_finance_book"),
                (("name", "=", COMPANY),),
                (),
                "name asc",
                2,
            )
        )

    def test_malformed_masked_unknown_rows_and_cap_plus_one(self) -> None:
        for malformed in (
            {"name": COMPANY, "default_currency": "MMK"},
            {"name": COMPANY, "default_currency": "MMK", "default_finance_book": "BOOK", "owner": "LEAK"},
        ):
            with self.subTest(malformed=malformed):
                runtime, frappe, _ = _runtime()
                snapshot = _begin(runtime)
                frappe.return_rows_verbatim = True
                frappe.rows["Company"] = [malformed]
                self.assertUnavailable(
                    lambda: runtime.get_list(
                        snapshot,
                        "Company",
                        ("name", "default_currency", "default_finance_book"),
                        (("name", "=", COMPANY),),
                        (),
                        "name asc",
                        2,
                    )
                )

        runtime, frappe, _ = _runtime()
        snapshot = _begin(runtime)
        self.assertUnavailable(
            lambda: runtime.complete_account_manifest(snapshot, COMPANY, 1)
        )

        runtime, frappe, _ = _runtime()
        snapshot = _begin(runtime)
        frappe.rows["GL Entry"].append(dict(frappe.rows["GL Entry"][0], name="GL2"))
        frappe.raw.gl_count = 2
        self.assertUnavailable(
            lambda: runtime.get_list(
                snapshot,
                "GL Entry",
                ("name", "company", "posting_date", "account", "debit", "credit", "is_cancelled", "is_opening", "finance_book"),
                (("company", "=", COMPANY), ("posting_date", "<=", date(2026, 12, 31)), ("is_cancelled", "=", 0)),
                (("finance_book", "=", "BOOK"), ("finance_book", "=", ""), ("finance_book", "is", "not set")),
                "posting_date asc, name asc",
                2,
            )
        )

    def test_aggregate_failure_returns_no_partial_and_closes(self) -> None:
        runtime, frappe, _ = _runtime()
        snapshot = _begin(runtime)
        frappe.raw.fail_statement = "SELECT COUNT(DISTINCT `name`) FROM `tabAccount` WHERE `company` = %(company)s"
        self.assertUnavailable(
            lambda: runtime.complete_account_manifest(snapshot, COMPANY, 4)
        )
        self.assertTrue(frappe.raw.closed)



    def test_alternate_name_import_has_no_runtime_side_effect(self) -> None:
        source_module = sys.modules[FrappeGLTrialBalanceRuntime.__module__]
        alternate_name = (
            "erp_workspace_ui.finance_accounting._gl_tb_runtime_import_probe"
        )
        spec = importlib.util.spec_from_file_location(
            alternate_name, source_module.__file__
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        alternate = importlib.util.module_from_spec(spec)
        original_import = builtins.__import__

        def guarded_import(name, *args, **kwargs):
            if name.split(".", 1)[0] in {"frappe", "pymysql", "MySQLdb"}:
                raise AssertionError("forbidden runtime import")
            return original_import(name, *args, **kwargs)

        sys.modules[alternate_name] = alternate
        try:
            with (
                mock.patch(
                    "builtins.__import__", side_effect=guarded_import
                ),
                mock.patch(
                    "importlib.metadata.version",
                    side_effect=AssertionError("metadata lookup"),
                ) as version_lookup,
                mock.patch(
                    "builtins.open", side_effect=AssertionError("filesystem")
                ),
                mock.patch(
                    "io.open", side_effect=AssertionError("filesystem")
                ),
                mock.patch(
                    "os.open", side_effect=AssertionError("filesystem")
                ),
                mock.patch.object(
                    Path, "open", side_effect=AssertionError("filesystem")
                ),
                mock.patch(
                    "socket.socket", side_effect=AssertionError("network")
                ),
            ):
                spec.loader.exec_module(alternate)
            version_lookup.assert_not_called()
        finally:
            sys.modules.pop(alternate_name, None)
        self.assertNotIn("frappe", alternate.__dict__)
        self.assertFalse(hasattr(alternate, "runtime"))
        self.assertFalse(hasattr(alternate, "default_runtime"))

    def test_fiscal_exact_limit_and_limit_plus_one_before_aggregates(self) -> None:
        runtime, frappe, _ = _runtime()
        frappe.rows["Fiscal Year"] = [
            {"name": "FY_GLOBAL"},
            {"name": "FY_SELECTED"},
        ]
        frappe.raw.fiscal_states = {
            "FY_GLOBAL": (0, 0),
            "FY_SELECTED": (1, 1),
        }
        snapshot = _begin(runtime)
        result = runtime.complete_fiscal_year_applicability(
            snapshot, COMPANY, 2
        )
        self.assertEqual(
            result.fiscal_year_applicability,
            (("FY_GLOBAL", "global"), ("FY_SELECTED", "selected_company")),
        )
        fiscal_calls = [
            item
            for item in frappe.raw.statements
            if "FROM `tabFiscal Year Company`" in item[0]
        ]
        self.assertEqual(len(fiscal_calls), 2)

        runtime, frappe, _ = _runtime()
        frappe.rows["Fiscal Year"] = [
            {"name": "FY_GLOBAL"},
            {"name": "FY_SELECTED"},
            {"name": "FY_EXCLUDED"},
        ]
        snapshot = _begin(runtime)
        self.assertUnavailable(
            lambda: runtime.complete_fiscal_year_applicability(
                snapshot, COMPANY, 2
            )
        )
        self.assertFalse(
            any(
                "FROM `tabFiscal Year Company`" in statement
                for statement, _ in frappe.raw.statements
            )
        )

    def test_literal_aggregate_sql_bindings_and_call_counts(self) -> None:
        account_sql = (
            "SELECT COUNT(DISTINCT `name`) FROM `tabAccount` "
            "WHERE `company` = %(company)s"
        )
        gl_sql = (
            "SELECT COUNT(DISTINCT `name`) FROM `tabGL Entry` "
            "WHERE `company` = %(company)s "
            "AND `posting_date` <= %(to_date)s "
            "AND `is_cancelled` = 0 "
            "AND (`finance_book` = %(finance_book)s "
            "OR `finance_book` = '' OR `finance_book` IS NULL)"
        )
        fiscal_sql = (
            "SELECT EXISTS(SELECT 1 FROM `tabFiscal Year Company` "
            "WHERE `parenttype` = 'Fiscal Year' "
            "AND `parentfield` = 'companies' "
            "AND `parent` = %(fiscal_year)s) AS `any_link`, "
            "EXISTS(SELECT 1 FROM `tabFiscal Year Company` "
            "WHERE `parenttype` = 'Fiscal Year' "
            "AND `parentfield` = 'companies' "
            "AND `parent` = %(fiscal_year)s "
            "AND `company` = %(company)s) AS `selected_link`"
        )

        runtime, frappe, _ = _runtime()
        snapshot = _begin(runtime)
        runtime.complete_account_manifest(snapshot, COMPANY, 4)
        self.assertEqual(
            [item for item in frappe.raw.statements if item[0] == account_sql],
            [(account_sql, {"company": COMPANY})],
        )

        runtime, frappe, _ = _runtime()
        snapshot = _begin(runtime)
        to_date = date(2026, 12, 31)
        runtime.get_list(
            snapshot,
            "GL Entry",
            (
                "name", "company", "posting_date", "account", "debit",
                "credit", "is_cancelled", "is_opening", "finance_book",
            ),
            (
                ("company", "=", COMPANY),
                ("posting_date", "<=", to_date),
                ("is_cancelled", "=", 0),
            ),
            (
                ("finance_book", "=", "BOOK"),
                ("finance_book", "=", ""),
                ("finance_book", "is", "not set"),
            ),
            "posting_date asc, name asc",
            3,
        )
        self.assertEqual(
            [item for item in frappe.raw.statements if item[0] == gl_sql],
            [
                (
                    gl_sql,
                    {
                        "company": COMPANY,
                        "to_date": to_date,
                        "finance_book": "BOOK",
                    },
                )
            ],
        )

        runtime, frappe, _ = _runtime()
        snapshot = _begin(runtime)
        runtime.complete_fiscal_year_applicability(snapshot, COMPANY, 2)
        self.assertEqual(
            [item for item in frappe.raw.statements if item[0] == fiscal_sql],
            [
                (
                    fiscal_sql,
                    {"fiscal_year": "FY_GLOBAL", "company": COMPANY},
                )
            ],
        )

    def test_occurrence_specific_probe_failures_close_without_leakage(self) -> None:
        probe = "SELECT VERSION(), CONNECTION_ID(), @@in_transaction"
        set_isolation = "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ"
        start = "START TRANSACTION READ ONLY, WITH CONSISTENT SNAPSHOT"
        rollback = "ROLLBACK AND NO CHAIN"
        expected_paths = {
            2: [probe, set_isolation, start, probe, rollback, probe],
            3: [probe, set_isolation, start, probe, probe],
            4: [probe, set_isolation, start, probe, probe, rollback, probe],
        }
        expected_rollbacks = {2: 1, 3: 0, 4: 1}
        for occurrence, phase in (
            (2, "post-start"),
            (3, "pre-rollback"),
            (4, "post-rollback"),
        ):
            with self.subTest(phase=phase):
                runtime, frappe, _ = _runtime()
                snapshot = None
                if occurrence == 2:
                    frappe.raw.fail_execute = (probe, occurrence)
                    self.assertUnavailable(lambda: _begin(runtime))
                else:
                    snapshot = _begin(runtime)
                    frappe.raw.fail_execute = (probe, occurrence)
                    self.assertUnavailable(
                        lambda: runtime.close_read_snapshot(snapshot)
                    )
                    self.assertUnavailable(
                        lambda: runtime.final_snapshot_evidence(snapshot)
                    )
                    runtime.close_read_snapshot(snapshot)
                statements = [item[0] for item in frappe.raw.statements]
                self.assertEqual(statements, expected_paths[occurrence])
                self.assertEqual(
                    statements.count(rollback), expected_rollbacks[occurrence]
                )
                self.assertFalse(
                    any(
                        marker in statement
                        for statement in statements
                        for marker in (
                            "FROM `tabAccount`",
                            "FROM `tabGL Entry`",
                            "FROM `tabFiscal Year Company`",
                        )
                    )
                )
                self.assertTrue(frappe.raw.closed)
                self.assertFalse(frappe.raw.active)

    def test_snapshot_construction_and_current_state_contract(self) -> None:
        module = __import__(
            "erp_workspace_ui.finance_accounting.gl_trial_balance_frappe_runtime",
            fromlist=["FrappeGLTrialBalanceRuntime"],
        )
        probe = "SELECT VERSION(), CONNECTION_ID(), @@in_transaction"
        set_isolation = "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ"
        start_snapshot = (
            "START TRANSACTION READ ONLY, WITH CONSISTENT SNAPSHOT"
        )
        self.assertEqual(module._PREFLIGHT_SQL, probe)
        self.assertEqual(module._STATE_SQL, probe)
        self.assertEqual(module._SET_ISOLATION_SQL, set_isolation)
        self.assertEqual(module._START_SNAPSHOT_SQL, start_snapshot)
        self.assertNotIn("@@tx_isolation", probe)
        self.assertNotIn("@@tx_read_only", probe)
        self.assertNotIn("READ WRITE", start_snapshot)
        self.assertNotIn("READ COMMITTED", set_isolation)

        for label, conflicting_state in (
            ("missing", (SERVER, CONNECTION_ID)),
            ("malformed", (SERVER, CONNECTION_ID, "1")),
            ("inactive", (SERVER, CONNECTION_ID, 0)),
            ("wrong-server", ("wrong", CONNECTION_ID, 1)),
        ):
            with self.subTest(label=label):
                runtime, frappe, _ = _runtime()
                frappe.raw.state_overrides[2] = conflicting_state
                self.assertUnavailable(lambda: _begin(runtime))
                statements = [item[0] for item in frappe.raw.statements]
                self.assertEqual(
                    statements[:4],
                    [probe, set_isolation, start_snapshot, probe],
                )
                self.assertEqual(
                    statements[-2:],
                    ["ROLLBACK AND NO CHAIN", probe],
                )
                self.assertTrue(frappe.raw.closed)
                self.assertFalse(frappe.raw.active)



if __name__ == "__main__":
    unittest.main()
