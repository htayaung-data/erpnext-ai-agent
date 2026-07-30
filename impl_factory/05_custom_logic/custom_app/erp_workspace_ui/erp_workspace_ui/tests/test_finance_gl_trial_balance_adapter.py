from __future__ import annotations

import unittest
from dataclasses import replace
from datetime import date
from decimal import Decimal

from erp_workspace_ui.finance_accounting.gl_trial_balance_adapter import (
    CompleteAccountManifest,
    CompleteFiscalYearApplicability,
    EffectivePermissionEvidence,
    GLTrialBalanceAdapterError,
    GLTrialBalanceReadRequest,
    ReadSnapshotEvidence,
    UserPermissionRule,
    read_gl_trial_balance,
)


COMPANY = "COMPANY_A"
OTHER_COMPANY = "COMPANY_B"
CURRENCY = "MMK"
DEFAULT_BOOK = "BOOK_DEFAULT"
FISCAL_YEAR = "FY2026"
USER = "accounts.manager@example.test"
SNAPSHOT_TOKEN = "SYNTHETIC_SNAPSHOT_1"
UNAUTHORIZED_COMPANY = "COMPANY_C"
# Proof-only fixture caps.  They are not production limits.
SYNTHETIC_MAX_ACCOUNTS = 17
SYNTHETIC_MAX_GL_ENTRIES = 23


def _request(**changes: object) -> GLTrialBalanceReadRequest:
    value = GLTrialBalanceReadRequest(
        company=COMPANY,
        fiscal_year=FISCAL_YEAR,
        from_date=date(2026, 4, 1),
        to_date=date(2026, 6, 30),
        currency_precision=2,
        max_accounts=SYNTHETIC_MAX_ACCOUNTS,
        max_gl_entries=SYNTHETIC_MAX_GL_ENTRIES,
    )
    return replace(value, **changes)


def _account(
    name: str,
    parent: str | None,
    is_group: int,
    root_type: str,
    lft: int,
    rgt: int,
    **changes: object,
) -> dict[str, object]:
    value: dict[str, object] = {
        "name": name,
        "company": COMPANY,
        "parent_account": parent,
        "is_group": is_group,
        "root_type": root_type,
        "lft": lft,
        "rgt": rgt,
        "account_currency": CURRENCY,
        "disabled": 0,
    }
    value.update(changes)
    return value


ACCOUNT_ROWS = [
    _account("ASSET_ROOT", None, 1, "Asset", 1, 4),
    _account("CASH", "ASSET_ROOT", 0, "Asset", 2, 3),
    _account("LIABILITY_ROOT", None, 1, "Liability", 5, 8),
    _account("PAYABLE", "LIABILITY_ROOT", 0, "Liability", 6, 7),
    _account("EQUITY_ROOT", None, 1, "Equity", 9, 12),
    _account("EQUITY", "EQUITY_ROOT", 0, "Equity", 10, 11),
    _account("INCOME_ROOT", None, 1, "Income", 13, 16),
    _account("REVENUE", "INCOME_ROOT", 0, "Income", 14, 15),
    _account("EXPENSE_ROOT", None, 1, "Expense", 17, 20),
    _account("EXPENSE", "EXPENSE_ROOT", 0, "Expense", 18, 19),
]
ACCOUNT_IDS = tuple(row["name"] for row in ACCOUNT_ROWS)
ROOT_IDS = (
    "ASSET_ROOT",
    "LIABILITY_ROOT",
    "EQUITY_ROOT",
    "INCOME_ROOT",
    "EXPENSE_ROOT",
)


def _gl_entry(
    name: str,
    account: str,
    posting_date: date,
    debit: str,
    credit: str,
    *,
    finance_book: str | None = DEFAULT_BOOK,
    is_opening: str = "No",
    **changes: object,
) -> dict[str, object]:
    value: dict[str, object] = {
        "name": name,
        "company": COMPANY,
        "posting_date": posting_date,
        "account": account,
        "debit": Decimal(debit),
        "credit": Decimal(credit),
        "is_cancelled": 0,
        "is_opening": is_opening,
        "finance_book": finance_book,
    }
    value.update(changes)
    return value


GL_ROWS = [
    _gl_entry("GL_SOURCE_OPEN_D", "CASH", date(2025, 12, 31), "100", "0"),
    _gl_entry("GL_SOURCE_OPEN_C", "EQUITY", date(2025, 12, 31), "0", "100"),
    _gl_entry("GL_SOURCE_OLD_PNL_D", "EXPENSE", date(2025, 12, 31), "900", "0"),
    _gl_entry("GL_SOURCE_OLD_PNL_C", "REVENUE", date(2025, 12, 31), "0", "900"),
    _gl_entry("GL_SOURCE_FY_OPEN_D", "EXPENSE", date(2026, 1, 1), "20", "0"),
    _gl_entry("GL_SOURCE_FY_OPEN_C", "REVENUE", date(2026, 1, 1), "0", "20"),
    _gl_entry(
        "GL_SOURCE_FROM_D",
        "EXPENSE",
        date(2026, 4, 1),
        "10",
        "0",
        finance_book="",
    ),
    _gl_entry("GL_SOURCE_FROM_C", "REVENUE", date(2026, 4, 1), "0", "10", finance_book=""),
    _gl_entry(
        "GL_SOURCE_TO_D",
        "EXPENSE",
        date(2026, 6, 30),
        "5",
        "0",
        finance_book=None,
    ),
    _gl_entry("GL_SOURCE_TO_C", "REVENUE", date(2026, 6, 30), "0", "5", finance_book=None),
]


def _account_limit_rows() -> list[dict[str, object]]:
    return [
        _account("ASSET_ROOT", None, 1, "Asset", 1, 10),
        _account("CASH", "ASSET_ROOT", 0, "Asset", 2, 3),
        _account("RECEIVABLE", "ASSET_ROOT", 0, "Asset", 4, 5),
        _account("BANK", "ASSET_ROOT", 0, "Asset", 6, 7),
        _account("INVENTORY", "ASSET_ROOT", 0, "Asset", 8, 9),
        _account("LIABILITY_ROOT", None, 1, "Liability", 11, 20),
        _account("PAYABLE", "LIABILITY_ROOT", 0, "Liability", 12, 13),
        _account("TAX_PAYABLE", "LIABILITY_ROOT", 0, "Liability", 14, 15),
        _account("LOAN_PAYABLE", "LIABILITY_ROOT", 0, "Liability", 16, 17),
        _account("ACCRUAL", "LIABILITY_ROOT", 0, "Liability", 18, 19),
        _account("EQUITY_ROOT", None, 1, "Equity", 21, 26),
        _account("EQUITY", "EQUITY_ROOT", 0, "Equity", 22, 23),
        _account("RETAINED_EARNINGS", "EQUITY_ROOT", 0, "Equity", 24, 25),
        _account("INCOME_ROOT", None, 1, "Income", 27, 30),
        _account("REVENUE", "INCOME_ROOT", 0, "Income", 28, 29),
        _account("EXPENSE_ROOT", None, 1, "Expense", 31, 36),
        _account("EXPENSE", "EXPENSE_ROOT", 0, "Expense", 32, 33),
        _account("OTHER_EXPENSE", "EXPENSE_ROOT", 0, "Expense", 34, 35),
    ]


def _gl_limit_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index in range(12):
        rows.extend(
            (
                _gl_entry(
                    f"GL_LIMIT_{index:02d}_D",
                    "EXPENSE",
                    date(2026, 5, 1),
                    "1",
                    "0",
                ),
                _gl_entry(
                    f"GL_LIMIT_{index:02d}_C",
                    "REVENUE",
                    date(2026, 5, 1),
                    "0",
                    "1",
                ),
            )
        )
    return rows


def _rows() -> dict[str, list[dict[str, object]]]:
    return {
        "Company": [
            {
                "name": COMPANY,
                "default_currency": CURRENCY,
                "default_finance_book": DEFAULT_BOOK,
            }
        ],
        "Fiscal Year": [
            {
                "name": FISCAL_YEAR,
                "year_start_date": date(2026, 1, 1),
                "year_end_date": date(2026, 12, 31),
                "disabled": 0,
            }
        ],
        "Fiscal Year Company": [{"parent": FISCAL_YEAR, "company": COMPANY}],
        "Finance Book": [
            {"name": DEFAULT_BOOK, "finance_book_name": "Default Finance Book"}
        ],
        "Accounting Dimension": [],
        "Account": [dict(row) for row in ACCOUNT_ROWS],
        "GL Entry": [dict(row) for row in GL_ROWS],
    }


def _company_rule(**changes: object) -> UserPermissionRule:
    value = UserPermissionRule(
        allow="Company",
        for_value=COMPANY,
        applicable_for=None,
        apply_to_all_doctypes=1,
        hide_descendants=0,
    )
    return replace(value, **changes)


def _snapshot(**changes: object) -> ReadSnapshotEvidence:
    value = ReadSnapshotEvidence(
        token=SNAPSHOT_TOKEN,
        user=USER,
        company=COMPANY,
        primary_connection=True,
        replica_denied=True,
        transaction_isolation="REPEATABLE READ",
        transaction_read_only=True,
        transaction_active=True,
        consistent_snapshot=True,
        reconnect_denied=True,
        same_connection=True,
        stable=True,
    )
    return replace(value, **changes)


def _permissions(**changes: object) -> EffectivePermissionEvidence:
    value = EffectivePermissionEvidence(
        snapshot_token=SNAPSHOT_TOKEN,
        user=USER,
        company=COMPANY,
        roles=("Accounts Manager",),
        user_permissions=(_company_rule(),),
        complete=True,
        permission_equivalent=True,
        unresolved_relevant_hooks=False,
        custom_docperm_drift=False,
        property_setter_drift=False,
        owner_only_drift=False,
        elevated_permlevel_drift=False,
        field_mask_drift=False,
        share_drift=False,
        custom_report_role_drift=False,
    )
    return replace(value, **changes)


def _manifest(**changes: object) -> CompleteAccountManifest:
    value = CompleteAccountManifest(
        snapshot_token=SNAPSHOT_TOKEN,
        company=COMPANY,
        account_ids=ACCOUNT_IDS,
        root_account_ids=ROOT_IDS,
        complete=True,
        permission_equivalent=True,
    )
    return replace(value, **changes)


def _fiscal_manifest(**changes: object) -> CompleteFiscalYearApplicability:
    value = CompleteFiscalYearApplicability(
        snapshot_token=SNAPSHOT_TOKEN,
        company=COMPANY,
        fiscal_year_applicability=((FISCAL_YEAR, "selected_company"),),
        complete=True,
        permission_equivalent=True,
    )
    return replace(value, **changes)


class SyntheticPermissionedRuntime:
    def __init__(self) -> None:
        self.user: object = USER
        self.snapshot: object = _snapshot()
        self.permission_evidence: object = _permissions()
        self.final_permission_evidence: object = self.permission_evidence
        self.manifests: list[object] = [_manifest(), _manifest()]
        self.fiscal_manifests: list[object] = [_fiscal_manifest(), _fiscal_manifest()]
        self.rows = _rows()
        self.permission_denials: set[tuple[str, str]] = set()
        self.final_permission_denials: set[tuple[str, str]] = set()
        self.final_snapshot: object = _snapshot()
        self.fail_operation: str | None = None
        self.fail_doctype: str | None = None
        self.close_failure = False
        self.respect_gl_or_filters = False
        self.calls: list[tuple[object, ...]] = []
        self.closed: list[ReadSnapshotEvidence] = []
        self._manifest_index = 0
        self._fiscal_manifest_index = 0
        self._permission_evidence_index = 0

    def current_user(self) -> object:
        self.calls.append(("current_user",))
        if self.fail_operation == "current_user":
            raise RuntimeError("LEAK_CURRENT_USER")
        return self.user

    def begin_read_snapshot(self, user: str, company: str) -> object:
        self.calls.append(("begin_read_snapshot", user, company))
        if self.fail_operation == "begin_read_snapshot":
            raise RuntimeError("LEAK_BEGIN_SNAPSHOT")
        return self.snapshot

    def effective_permission_evidence(self, snapshot: ReadSnapshotEvidence) -> object:
        self.calls.append(("effective_permission_evidence", snapshot.token))
        if self.fail_operation == "effective_permission_evidence":
            raise RuntimeError("LEAK_EFFECTIVE_PERMISSION")
        evidence = (
            self.permission_evidence
            if self._permission_evidence_index == 0
            else self.final_permission_evidence
        )
        self._permission_evidence_index += 1
        return evidence

    def has_permission(
        self,
        snapshot: ReadSnapshotEvidence,
        user: str,
        doctype: str,
        permission_type: str,
    ) -> object:
        self.calls.append(
            ("has_permission", snapshot.token, user, doctype, permission_type)
        )
        if self.fail_operation == "has_permission":
            raise RuntimeError("LEAK_PERMISSION_CHECK")
        final_pass = any(
            call[0] == "final_snapshot_evidence" for call in self.calls
        )
        denials = (
            self.final_permission_denials if final_pass else self.permission_denials
        )
        return (doctype, permission_type) not in denials

    def get_list(
        self,
        snapshot: ReadSnapshotEvidence,
        doctype: str,
        fields: tuple[str, ...],
        filters: tuple[tuple[str, str, object], ...],
        or_filters: tuple[tuple[str, str, object], ...],
        order_by: str,
        limit: int,
    ) -> object:
        self.calls.append(
            (
                "get_list",
                snapshot.token,
                doctype,
                fields,
                filters,
                or_filters,
                order_by,
                limit,
            )
        )
        if self.fail_operation == "get_list" or self.fail_doctype == doctype:
            raise RuntimeError(f"LEAK_DATABASE_{doctype}_{COMPANY}")
        rows = [dict(row) for row in self.rows[doctype]]
        if doctype == "GL Entry" and self.respect_gl_or_filters:
            allowed_books = (
                ("", None)
                if len(or_filters) == 2
                else (or_filters[0][2], "", None)
            )
            rows = [row for row in rows if row["finance_book"] in allowed_books]
        return rows

    def complete_account_manifest(
        self,
        snapshot: ReadSnapshotEvidence,
        company: str,
        max_accounts: int,
    ) -> object:
        self.calls.append(
            ("complete_account_manifest", snapshot.token, company, max_accounts)
        )
        if self.fail_operation == "complete_account_manifest":
            raise RuntimeError("LEAK_ACCOUNT_MANIFEST")
        index = min(self._manifest_index, len(self.manifests) - 1)
        self._manifest_index += 1
        return self.manifests[index]

    def complete_fiscal_year_applicability(
        self,
        snapshot: ReadSnapshotEvidence,
        company: str,
        max_fiscal_years: int,
    ) -> object:
        self.calls.append(
            ("complete_fiscal_year_applicability", snapshot.token, company, max_fiscal_years)
        )
        if self.fail_operation == "complete_fiscal_year_applicability":
            raise RuntimeError("LEAK_FISCAL_MANIFEST")
        index = min(self._fiscal_manifest_index, len(self.fiscal_manifests) - 1)
        self._fiscal_manifest_index += 1
        return self.fiscal_manifests[index]

    def final_snapshot_evidence(self, snapshot: ReadSnapshotEvidence) -> object:
        self.calls.append(("final_snapshot_evidence", snapshot.token))
        if self.fail_operation == "final_snapshot_evidence":
            raise RuntimeError("LEAK_SNAPSHOT_STATUS")
        return self.final_snapshot

    def close_read_snapshot(self, snapshot: ReadSnapshotEvidence) -> None:
        self.calls.append(("close_read_snapshot", snapshot.token))
        self.closed.append(snapshot)
        if self.close_failure:
            raise RuntimeError("LEAK_CLOSE_SNAPSHOT")


def _runtime_for_company(
    company: str,
    user_permissions: tuple[UserPermissionRule, ...],
) -> SyntheticPermissionedRuntime:
    runtime = SyntheticPermissionedRuntime()
    runtime.snapshot = _snapshot(company=company)
    runtime.final_snapshot = _snapshot(company=company)
    runtime.permission_evidence = _permissions(
        company=company,
        user_permissions=user_permissions,
    )
    runtime.final_permission_evidence = runtime.permission_evidence
    runtime.manifests = [_manifest(company=company), _manifest(company=company)]
    runtime.fiscal_manifests = [
        _fiscal_manifest(
            company=company,
            fiscal_year_applicability=((FISCAL_YEAR, "selected_company"),),
        ),
        _fiscal_manifest(
            company=company,
            fiscal_year_applicability=((FISCAL_YEAR, "selected_company"),),
        ),
    ]
    runtime.rows["Company"][0]["name"] = company
    runtime.rows["Fiscal Year Company"][0]["company"] = company
    for row in runtime.rows["Account"]:
        row["company"] = company
    for row in runtime.rows["GL Entry"]:
        row["company"] = company
    return runtime


def _read(runtime: SyntheticPermissionedRuntime, **request_changes: object):
    return read_gl_trial_balance(
        request=_request(**request_changes),
        runtime=runtime,
    )


def _assert_unavailable(
    case: unittest.TestCase,
    runtime: SyntheticPermissionedRuntime,
    **request_changes: object,
) -> GLTrialBalanceAdapterError:
    with case.assertRaises(GLTrialBalanceAdapterError) as raised:
        _read(runtime, **request_changes)
    error = raised.exception
    case.assertEqual(error.code, "finance_read_unavailable")
    case.assertEqual(str(error), "finance_read_unavailable")
    case.assertNotIn("LEAK", repr(error))
    case.assertIsNone(error.__cause__)
    case.assertIsNone(error.__context__)
    return error


class TestFinanceGLTrialBalancePermissionedAdapter(unittest.TestCase):
    def test_authorized_read_applies_accounting_boundaries_and_closes_snapshot(self):
        runtime = SyntheticPermissionedRuntime()

        result = _read(runtime)

        self.assertEqual(result.scope.company, COMPANY)
        self.assertEqual(result.scope.base_currency, CURRENCY)
        self.assertEqual(result.scope.default_finance_book, DEFAULT_BOOK)
        self.assertEqual(
            result.scope.finance_book_cohort,
            ("company_default", "blank_unbooked", "null_unbooked"),
        )
        self.assertEqual(result.gross_totals.opening_debit, Decimal("120.00"))
        self.assertEqual(result.gross_totals.opening_credit, Decimal("120.00"))
        self.assertEqual(result.gross_totals.movement_debit, Decimal("15.00"))
        self.assertEqual(result.gross_totals.movement_credit, Decimal("15.00"))
        self.assertEqual(result.gross_totals.closing_debit, Decimal("135.00"))
        self.assertEqual(result.gross_totals.closing_credit, Decimal("135.00"))
        self.assertEqual(runtime.closed, [_snapshot()])
        self.assertEqual(
            [call[0] for call in runtime.calls][-14:],
            [
                "complete_account_manifest",
                "complete_fiscal_year_applicability",
                "final_snapshot_evidence",
                "effective_permission_evidence",
                *(["has_permission"] * 9),
                "close_read_snapshot",
            ],
        )

    def test_exact_permission_requirements_and_query_contract(self):
        runtime = SyntheticPermissionedRuntime()

        _read(runtime)

        permission_calls = [call for call in runtime.calls if call[0] == "has_permission"]
        expected_permissions = [
            ("Company", "read"),
            ("Fiscal Year", "read"),
            ("Fiscal Year Company", "read"),
            ("Finance Book", "read"),
            ("Accounting Dimension", "read"),
            ("Account", "read"),
            ("Account", "report"),
            ("GL Entry", "read"),
            ("GL Entry", "report"),
        ]
        self.assertEqual(
            [(call[3], call[4]) for call in permission_calls],
            expected_permissions * 2,
        )
        queries = {call[2]: call for call in runtime.calls if call[0] == "get_list"}
        self.assertEqual(
            queries["Company"][3],
            ("name", "default_currency", "default_finance_book"),
        )
        self.assertEqual(queries["Company"][4], (("name", "=", COMPANY),))
        self.assertEqual(
            queries["Fiscal Year"][3],
            ("name", "year_start_date", "year_end_date", "disabled"),
        )
        self.assertEqual(queries["Fiscal Year"][4], (("disabled", "=", 0),))
        self.assertEqual(
            queries["Fiscal Year Company"][4],
            (
                ("parent", "in", (FISCAL_YEAR,)),
                ("company", "=", COMPANY),
            ),
        )
        self.assertEqual(
            queries["Account"][3],
            (
                "name",
                "company",
                "parent_account",
                "is_group",
                "root_type",
                "lft",
                "rgt",
                "account_currency",
                "disabled",
            ),
        )
        self.assertEqual(queries["Account"][4], (("company", "=", COMPANY),))
        self.assertEqual(queries["Account"][6], "lft asc, name asc")
        self.assertEqual(
            queries["GL Entry"][3],
            (
                "name",
                "company",
                "posting_date",
                "account",
                "debit",
                "credit",
                "is_cancelled",
                "is_opening",
                "finance_book",
            ),
        )
        self.assertEqual(
            queries["GL Entry"][4],
            (
                ("company", "=", COMPANY),
                ("posting_date", "<=", date(2026, 6, 30)),
                ("is_cancelled", "=", 0),
            ),
        )
        self.assertEqual(
            queries["GL Entry"][5],
            (
                ("finance_book", "=", DEFAULT_BOOK),
                ("finance_book", "=", ""),
                ("finance_book", "is", "not set"),
            ),
        )
        self.assertEqual(queries["GL Entry"][6], "posting_date asc, name asc")
        self.assertEqual(queries["GL Entry"][7], SYNTHETIC_MAX_GL_ENTRIES + 1)
        self.assertTrue(
            all(
                call[7] == SYNTHETIC_MAX_ACCOUNTS + 1
                for doctype, call in queries.items()
                if doctype != "GL Entry"
            )
        )
        for operation in (
            "complete_account_manifest",
            "complete_fiscal_year_applicability",
        ):
            calls = [call for call in runtime.calls if call[0] == operation]
            self.assertTrue(calls)
            self.assertTrue(all(call[3] == SYNTHETIC_MAX_ACCOUNTS for call in calls))
        self.assertNotIn("debit_in_account_currency", queries["GL Entry"][3])
        self.assertNotIn("credit_in_account_currency", queries["GL Entry"][3])
        self.assertNotIn("voucher_no", queries["GL Entry"][3])
        self.assertNotIn("party", queries["GL Entry"][3])

    def test_guest_and_administrator_stop_before_snapshot(self):
        for user in ("Guest", "Administrator", "", None):
            with self.subTest(user=user):
                runtime = SyntheticPermissionedRuntime()
                runtime.user = user

                _assert_unavailable(self, runtime)

                self.assertEqual(runtime.calls, [("current_user",)])
                self.assertEqual(runtime.closed, [])

    def test_wrong_role_and_privileged_role_mixture_are_denied_before_source_reads(self):
        role_sets = (
            ("Accounts User",),
            ("Auditor",),
            ("System Manager",),
            ("Accounts Manager", "System Manager"),
            ("Accounts Manager", "Bypass Finance Scope"),
        )
        for roles in role_sets:
            with self.subTest(roles=roles):
                runtime = SyntheticPermissionedRuntime()
                runtime.permission_evidence = _permissions(roles=roles)

                _assert_unavailable(self, runtime)

                self.assertFalse(any(call[0] == "get_list" for call in runtime.calls))
                self.assertEqual(runtime.closed, [_snapshot()])

    def test_company_user_permissions_allow_one_explicit_selected_company(self):
        company_a_rule = _company_rule()
        company_b_rule = _company_rule(for_value=OTHER_COMPANY)
        cases = (
            (COMPANY, (company_a_rule,)),
            (COMPANY, (company_a_rule, company_b_rule)),
            (OTHER_COMPANY, (company_a_rule, company_b_rule)),
        )
        for selected_company, rules in cases:
            with self.subTest(selected_company=selected_company, rules=rules):
                runtime = _runtime_for_company(selected_company, rules)

                result = _read(runtime, company=selected_company)

                self.assertEqual(result.scope.company, selected_company)
                self.assertEqual(
                    [call for call in runtime.calls if call[0] == "begin_read_snapshot"],
                    [("begin_read_snapshot", USER, selected_company)],
                )
                queries = {
                    call[2]: call for call in runtime.calls if call[0] == "get_list"
                }
                self.assertEqual(
                    queries["Company"][4],
                    (("name", "=", selected_company),),
                )
                self.assertEqual(
                    queries["Account"][4],
                    (("company", "=", selected_company),),
                )
                self.assertEqual(
                    queries["GL Entry"][4][0],
                    ("company", "=", selected_company),
                )
                for operation in (
                    "complete_account_manifest",
                    "complete_fiscal_year_applicability",
                ):
                    self.assertTrue(
                        all(
                            call[2] == selected_company
                            for call in runtime.calls
                            if call[0] == operation
                        )
                    )

    def test_company_user_permission_rejections_are_exact_and_fail_closed(self):
        relevant = UserPermissionRule(
            allow="Account",
            for_value="ASSET_ROOT",
            applicable_for=None,
            apply_to_all_doctypes=1,
            hide_descendants=0,
        )
        cases = (
            (),
            (_company_rule(), _company_rule()),
            (_company_rule(for_value=""),),
            (_company_rule(apply_to_all_doctypes=0),),
            (_company_rule(applicable_for="GL Entry"),),
            (_company_rule(hide_descendants=1),),
            (_company_rule(), relevant),
        )
        for rules in cases:
            with self.subTest(rules=rules):
                runtime = SyntheticPermissionedRuntime()
                runtime.permission_evidence = _permissions(user_permissions=rules)

                _assert_unavailable(self, runtime)

                self.assertFalse(any(call[0] == "get_list" for call in runtime.calls))

    def test_unauthorized_missing_and_blank_company_selection_fail_closed(self):
        rules = (
            _company_rule(),
            _company_rule(for_value=OTHER_COMPANY),
        )
        unauthorized = _runtime_for_company(UNAUTHORIZED_COMPANY, rules)
        _assert_unavailable(self, unauthorized, company=UNAUTHORIZED_COMPANY)
        self.assertFalse(any(call[0] == "get_list" for call in unauthorized.calls))

        for selected_company in (None, "", " "):
            with self.subTest(selected_company=selected_company):
                runtime = SyntheticPermissionedRuntime()
                _assert_unavailable(self, runtime, company=selected_company)
                self.assertEqual(runtime.calls, [])

    def test_multiple_company_permissions_never_accept_cross_company_rows(self):
        rules = (
            _company_rule(),
            _company_rule(for_value=OTHER_COMPANY),
        )
        runtime = _runtime_for_company(COMPANY, rules)
        runtime.rows["GL Entry"][0]["company"] = OTHER_COMPANY
        _assert_unavailable(self, runtime)
        self.assertEqual(runtime.closed, [_snapshot()])

        fiscal_runtime = _runtime_for_company(COMPANY, rules)
        fiscal_runtime.rows["Fiscal Year Company"].append(
            {"parent": FISCAL_YEAR, "company": OTHER_COMPANY}
        )
        _assert_unavailable(self, fiscal_runtime)
        self.assertEqual(fiscal_runtime.closed, [_snapshot()])

    def test_company_permission_set_drift_fails_closed(self):
        rules = (
            _company_rule(),
            _company_rule(for_value=OTHER_COMPANY),
        )
        runtime = _runtime_for_company(COMPANY, rules)
        runtime.final_permission_evidence = _permissions(
            user_permissions=(_company_rule(),),
        )

        _assert_unavailable(self, runtime)

        self.assertTrue(any(call[0] == "get_list" for call in runtime.calls))
        self.assertEqual(runtime.closed, [_snapshot()])

    def test_final_doctype_permission_drift_fails_closed(self):
        runtime = SyntheticPermissionedRuntime()
        runtime.final_permission_denials.add(("GL Entry", "report"))

        _assert_unavailable(self, runtime)

        gl_report_checks = [
            call
            for call in runtime.calls
            if call[0] == "has_permission"
            and call[3:] == ("GL Entry", "report")
        ]
        self.assertEqual(len(gl_report_checks), 2)
        self.assertTrue(any(call[0] == "get_list" for call in runtime.calls))
        self.assertEqual(runtime.closed, [_snapshot()])

    def test_effective_permission_drift_and_incomplete_evidence_fail_closed(self):
        changes = (
            {"complete": False},
            {"permission_equivalent": False},
            {"unresolved_relevant_hooks": True},
            {"custom_docperm_drift": True},
            {"property_setter_drift": True},
            {"owner_only_drift": True},
            {"elevated_permlevel_drift": True},
            {"field_mask_drift": True},
            {"share_drift": True},
            {"custom_report_role_drift": True},
        )
        for change in changes:
            with self.subTest(change=change):
                runtime = SyntheticPermissionedRuntime()
                runtime.permission_evidence = _permissions(**change)

                _assert_unavailable(self, runtime)

                self.assertFalse(any(call[0] == "get_list" for call in runtime.calls))

    def test_each_missing_read_or_report_permission_stops_before_configuration_read(self):
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
        for requirement in requirements:
            with self.subTest(requirement=requirement):
                runtime = SyntheticPermissionedRuntime()
                runtime.permission_denials.add(requirement)

                _assert_unavailable(self, runtime)

                self.assertFalse(any(call[0] == "get_list" for call in runtime.calls))

    def test_wrong_company_and_wrong_currency_rows_fail_closed(self):
        mutations = (
            ("Company", 0, "name", OTHER_COMPANY),
            ("Account", 1, "company", OTHER_COMPANY),
            ("Account", 1, "account_currency", "USD"),
            ("GL Entry", 0, "company", OTHER_COMPANY),
        )
        for doctype, index, field, value in mutations:
            with self.subTest(doctype=doctype, field=field):
                runtime = SyntheticPermissionedRuntime()
                runtime.rows[doctype][index][field] = value

                _assert_unavailable(self, runtime)

                self.assertEqual(runtime.closed, [_snapshot()])

    def test_cancelled_entry_is_filtered_in_query_and_rejected_if_returned(self):
        runtime = SyntheticPermissionedRuntime()
        runtime.rows["GL Entry"].append(
            _gl_entry(
                "GL_CANCELLED_DEBIT_SECRET",
                "CASH",
                date(2026, 6, 1),
                "1",
                "0",
                is_cancelled=1,
            )
        )
        runtime.rows["GL Entry"].append(
            _gl_entry(
                "GL_CANCELLED_CREDIT_SECRET",
                "PAYABLE",
                date(2026, 6, 1),
                "0",
                "1",
                is_cancelled=1,
            )
        )

        _assert_unavailable(self, runtime)

        query = next(
            call
            for call in runtime.calls
            if call[0] == "get_list" and call[2] == "GL Entry"
        )
        self.assertIn(("is_cancelled", "=", 0), query[4])

    def test_finance_book_default_blank_and_null_are_accepted_but_unknown_is_rejected(self):
        runtime = SyntheticPermissionedRuntime()
        result = _read(runtime)
        self.assertEqual(result.gross_totals.movement_debit, Decimal("15.00"))

        unknown = SyntheticPermissionedRuntime()
        unknown.rows["GL Entry"][0]["finance_book"] = "BOOK_UNKNOWN_SECRET"
        error = _assert_unavailable(self, unknown)
        self.assertNotIn("BOOK_UNKNOWN_SECRET", str(error))

    def test_blank_and_null_company_defaults_use_only_unbooked_rows(self):
        for raw_default in ("", None):
            with self.subTest(raw_default=raw_default):
                runtime = SyntheticPermissionedRuntime()
                runtime.respect_gl_or_filters = True
                runtime.rows["Company"][0]["default_finance_book"] = raw_default
                runtime.rows["GL Entry"].extend(
                    (
                        _gl_entry(
                            "OTHER_BOOK_DEBIT",
                            "CASH",
                            date(2026, 5, 1),
                            "999",
                            "0",
                            finance_book="BOOK_OTHER",
                        ),
                        _gl_entry(
                            "OTHER_BOOK_CREDIT",
                            "EQUITY",
                            date(2026, 5, 1),
                            "0",
                            "999",
                            finance_book="BOOK_OTHER",
                        ),
                    )
                )

                result = _read(runtime)

                self.assertIsNone(result.scope.default_finance_book)
                self.assertEqual(
                    result.scope.finance_book_cohort,
                    ("blank_unbooked", "null_unbooked"),
                )
                self.assertEqual(result.gross_totals.opening_debit, Decimal("0.00"))
                self.assertEqual(result.gross_totals.opening_credit, Decimal("0.00"))
                self.assertEqual(result.gross_totals.movement_debit, Decimal("15.00"))
                self.assertEqual(result.gross_totals.movement_credit, Decimal("15.00"))

                finance_book_reads = [
                    call
                    for call in runtime.calls
                    if call[0] == "get_list" and call[2] == "Finance Book"
                ]
                self.assertEqual(finance_book_reads, [])
                gl_query = next(
                    call
                    for call in runtime.calls
                    if call[0] == "get_list" and call[2] == "GL Entry"
                )
                self.assertEqual(
                    gl_query[5],
                    (
                        ("finance_book", "=", ""),
                        ("finance_book", "is", "not set"),
                    ),
                )
                permission_calls = [
                    call
                    for call in runtime.calls
                    if call[0] == "has_permission"
                    and call[3:5] == ("Finance Book", "read")
                ]
                self.assertEqual(len(permission_calls), 2)

    def test_malformed_company_default_finance_book_fails_closed(self):
        for raw_default in (" ", " BOOK_DEFAULT", 7, False, ("BOOK_DEFAULT",)):
            with self.subTest(raw_default=raw_default):
                runtime = SyntheticPermissionedRuntime()
                runtime.rows["Company"][0]["default_finance_book"] = raw_default
                _assert_unavailable(self, runtime)

    def test_fiscal_year_company_and_requested_date_contracts(self):
        runtime = SyntheticPermissionedRuntime()
        result = _read(runtime)
        self.assertEqual(result.scope.fiscal_year_start, date(2026, 1, 1))
        self.assertEqual(result.scope.fiscal_year_end, date(2026, 12, 31))
        self.assertEqual(result.scope.from_date, date(2026, 4, 1))
        self.assertEqual(result.scope.to_date, date(2026, 6, 30))

        cases = (
            {"fiscal_year": "FY2027"},
            {"from_date": date(2025, 12, 31)},
            {"to_date": date(2027, 1, 1)},
        )
        for change in cases:
            with self.subTest(change=change):
                _assert_unavailable(self, SyntheticPermissionedRuntime(), **change)

        wrong_company = SyntheticPermissionedRuntime()
        wrong_company.rows["Fiscal Year Company"] = [
            {"parent": FISCAL_YEAR, "company": OTHER_COMPANY}
        ]
        _assert_unavailable(self, wrong_company)

    def test_balance_sheet_history_is_retained_and_pre_fiscal_pnl_is_excluded(self):
        runtime = SyntheticPermissionedRuntime()

        result = _read(runtime)
        lines = {line.account_id: line for line in result.lines}

        self.assertEqual(lines["CASH"].amounts.opening_debit, Decimal("100.00"))
        self.assertEqual(lines["EQUITY"].amounts.opening_credit, Decimal("100.00"))
        self.assertEqual(lines["EXPENSE"].amounts.opening_debit, Decimal("20.00"))
        self.assertEqual(lines["REVENUE"].amounts.opening_credit, Decimal("20.00"))

    def test_complete_manifest_is_independent_exact_and_stable(self):
        cases = (
            _manifest(account_ids=ACCOUNT_IDS + ("HIDDEN_ACCOUNT",)),
            _manifest(account_ids=ACCOUNT_IDS[:-1]),
            _manifest(complete=False),
            _manifest(permission_equivalent=False),
            _manifest(company=OTHER_COMPANY),
            _manifest(snapshot_token="OTHER_SNAPSHOT"),
        )
        for manifest in cases:
            with self.subTest(manifest=manifest):
                runtime = SyntheticPermissionedRuntime()
                runtime.manifests = [manifest, manifest]

                _assert_unavailable(self, runtime)

        changed = SyntheticPermissionedRuntime()
        changed.manifests = [
            _manifest(),
            _manifest(account_ids=tuple(reversed(ACCOUNT_IDS))),
        ]
        _assert_unavailable(self, changed)
        self.assertEqual(
            len([call for call in changed.calls if call[0] == "complete_account_manifest"]),
            2,
        )


    def test_fiscal_applicability_manifest_is_complete_exact_and_stable(self):
        invalid_manifests = (
            _fiscal_manifest(complete=False),
            _fiscal_manifest(permission_equivalent=False),
            _fiscal_manifest(company=OTHER_COMPANY),
            _fiscal_manifest(snapshot_token="OTHER_SNAPSHOT"),
            _fiscal_manifest(fiscal_year_applicability=()),
            _fiscal_manifest(
                fiscal_year_applicability=(("FY2027", "selected_company"),)
            ),
            _fiscal_manifest(fiscal_year_applicability=((FISCAL_YEAR, "other"),)),
        )
        for manifest in invalid_manifests:
            with self.subTest(manifest=manifest):
                runtime = SyntheticPermissionedRuntime()
                runtime.fiscal_manifests = [manifest, manifest]
                _assert_unavailable(self, runtime)

        excluded = SyntheticPermissionedRuntime()
        excluded.rows["Fiscal Year Company"] = []
        excluded_manifest = _fiscal_manifest(
            fiscal_year_applicability=((FISCAL_YEAR, "excluded"),)
        )
        excluded.fiscal_manifests = [excluded_manifest, excluded_manifest]
        _assert_unavailable(self, excluded)

        proven_global = SyntheticPermissionedRuntime()
        proven_global.rows["Fiscal Year Company"] = []
        global_manifest = _fiscal_manifest(
            fiscal_year_applicability=((FISCAL_YEAR, "global"),)
        )
        proven_global.fiscal_manifests = [global_manifest, global_manifest]
        result = _read(proven_global)
        self.assertEqual(result.scope.fiscal_year_start, date(2026, 1, 1))

        changed = SyntheticPermissionedRuntime()
        changed.fiscal_manifests = [_fiscal_manifest(), global_manifest]
        _assert_unavailable(self, changed)
        self.assertEqual(
            len(
                [
                    call
                    for call in changed.calls
                    if call[0] == "complete_fiscal_year_applicability"
                ]
            ),
            2,
        )

    def test_missing_parent_orphan_and_cycle_are_propagated_as_generic_failure(self):
        def without_asset_root(runtime: SyntheticPermissionedRuntime) -> None:
            runtime.rows["Account"] = [
                row for row in runtime.rows["Account"] if row["name"] != "ASSET_ROOT"
            ]
            ids = tuple(name for name in ACCOUNT_IDS if name != "ASSET_ROOT")
            roots = tuple(name for name in ROOT_IDS if name != "ASSET_ROOT")
            runtime.manifests = [
                _manifest(account_ids=ids, root_account_ids=roots),
                _manifest(account_ids=ids, root_account_ids=roots),
            ]

        def orphan_root(runtime: SyntheticPermissionedRuntime) -> None:
            runtime.rows["Account"][1]["parent_account"] = None

        def cycle(runtime: SyntheticPermissionedRuntime) -> None:
            runtime.rows["Account"][0]["parent_account"] = "CASH"

        for mutation in (without_asset_root, orphan_root, cycle):
            with self.subTest(mutation=mutation.__name__):
                runtime = SyntheticPermissionedRuntime()
                mutation(runtime)

                _assert_unavailable(self, runtime)

                self.assertEqual(runtime.closed, [_snapshot()])

    def test_active_dimensions_and_malformed_dimension_rows_are_rejected(self):
        active = {
            "name": "DIMENSION_SECRET",
            "document_type": "Cost Center",
            "fieldname": "cost_center",
            "disabled": 0,
        }
        for row in (active, {"name": "DIMENSION_SECRET"}):
            with self.subTest(row=row):
                runtime = SyntheticPermissionedRuntime()
                runtime.rows["Accounting Dimension"] = [row]

                error = _assert_unavailable(self, runtime)
                self.assertNotIn("DIMENSION_SECRET", str(error))
                self.assertFalse(
                    any(
                        call[0] in {"complete_account_manifest", "final_snapshot_evidence"}
                        for call in runtime.calls
                    )
                )

    def test_disabled_historical_account_is_retained_but_flag_must_be_strict(self):
        retained = SyntheticPermissionedRuntime()
        retained.rows["Account"][1]["disabled"] = 1
        result = _read(retained)
        self.assertIn("CASH", {line.account_id for line in result.lines})

        malformed = SyntheticPermissionedRuntime()
        malformed.rows["Account"][1]["disabled"] = True
        _assert_unavailable(self, malformed)

    def test_malformed_rows_types_and_exact_key_drift_fail_closed(self):
        mutations = (
            ("GL Entry", 0, "debit", 100.0),
            ("GL Entry", 0, "posting_date", "2025-12-31"),
            ("GL Entry", 0, "is_opening", 0),
            ("Account", 0, "lft", True),
            ("Fiscal Year", 0, "disabled", False),
        )
        for doctype, index, field, value in mutations:
            with self.subTest(doctype=doctype, field=field):
                runtime = SyntheticPermissionedRuntime()
                runtime.rows[doctype][index][field] = value
                _assert_unavailable(self, runtime)

        missing = SyntheticPermissionedRuntime()
        del missing.rows["GL Entry"][0]["credit"]
        _assert_unavailable(self, missing)

        extra = SyntheticPermissionedRuntime()
        extra.rows["GL Entry"][0]["voucher_no"] = "VOUCHER_SECRET"
        error = _assert_unavailable(self, extra)
        self.assertNotIn("VOUCHER_SECRET", str(error))

    def test_limits_are_explicit_and_limit_plus_one_is_rejected(self):
        runtime = SyntheticPermissionedRuntime()
        _read(runtime)
        queries = {call[2]: call for call in runtime.calls if call[0] == "get_list"}
        self.assertEqual(
            queries["Account"][7],
            SYNTHETIC_MAX_ACCOUNTS + 1,
        )
        self.assertEqual(
            queries["GL Entry"][7],
            SYNTHETIC_MAX_GL_ENTRIES + 1,
        )

        account_rows = _account_limit_rows()
        self.assertEqual(len(account_rows), SYNTHETIC_MAX_ACCOUNTS + 1)
        account_ids = tuple(row["name"] for row in account_rows)
        too_many_accounts = SyntheticPermissionedRuntime()
        too_many_accounts.rows["Account"] = [dict(row) for row in account_rows]
        _assert_unavailable(self, too_many_accounts)
        account_query = next(
            call
            for call in too_many_accounts.calls
            if call[0] == "get_list" and call[2] == "Account"
        )
        self.assertEqual(account_query[7], SYNTHETIC_MAX_ACCOUNTS + 1)

        accounts_control = SyntheticPermissionedRuntime()
        accounts_control.rows["Account"] = [dict(row) for row in account_rows]
        account_manifest = _manifest(account_ids=account_ids)
        accounts_control.manifests = [account_manifest, account_manifest]
        self.assertEqual(
            _read(accounts_control, max_accounts=SYNTHETIC_MAX_ACCOUNTS + 1).scope.company,
            COMPANY,
        )

        gl_rows = _gl_limit_rows()
        self.assertEqual(len(gl_rows), SYNTHETIC_MAX_GL_ENTRIES + 1)
        self.assertEqual(len({row["name"] for row in gl_rows}), len(gl_rows))
        self.assertTrue(all(row["is_cancelled"] == 0 for row in gl_rows))
        self.assertEqual(
            sum((row["debit"] for row in gl_rows), Decimal("0")),
            sum((row["credit"] for row in gl_rows), Decimal("0")),
        )
        too_many_gl = SyntheticPermissionedRuntime()
        too_many_gl.rows["GL Entry"] = [dict(row) for row in gl_rows]
        _assert_unavailable(self, too_many_gl)
        gl_query = next(
            call
            for call in too_many_gl.calls
            if call[0] == "get_list" and call[2] == "GL Entry"
        )
        self.assertEqual(gl_query[7], SYNTHETIC_MAX_GL_ENTRIES + 1)

        gl_control = SyntheticPermissionedRuntime()
        gl_control.rows["GL Entry"] = [dict(row) for row in gl_rows]
        self.assertEqual(
            _read(
                gl_control,
                max_gl_entries=SYNTHETIC_MAX_GL_ENTRIES + 1,
            ).scope.company,
            COMPANY,
        )

        for change in (
            {"max_accounts": 0},
            {"max_gl_entries": 0},
            {"max_accounts": True},
            {"max_gl_entries": True},
        ):
            with self.subTest(change=change):
                runtime = SyntheticPermissionedRuntime()
                _assert_unavailable(self, runtime, **change)
                self.assertEqual(runtime.calls, [])

    def test_snapshot_authority_change_and_close_failure_return_no_partial_result(self):
        invalid_snapshots = (
            _snapshot(primary_connection=False),
            _snapshot(replica_denied=False),
            _snapshot(transaction_read_only=False),
            _snapshot(transaction_active=False),
            _snapshot(consistent_snapshot=False),
            _snapshot(reconnect_denied=False),
            _snapshot(same_connection=False),
            _snapshot(transaction_isolation="READ COMMITTED"),
            _snapshot(stable=False),
            _snapshot(user="other@example.test"),
            _snapshot(company=OTHER_COMPANY),
        )
        for snapshot in invalid_snapshots:
            with self.subTest(snapshot=snapshot):
                runtime = SyntheticPermissionedRuntime()
                runtime.snapshot = snapshot
                _assert_unavailable(self, runtime)
                self.assertEqual(runtime.closed, [snapshot])

        stale = SyntheticPermissionedRuntime()
        stale.final_snapshot = _snapshot(stable=False)
        _assert_unavailable(self, stale)
        self.assertEqual(stale.closed, [_snapshot()])

        close_failure = SyntheticPermissionedRuntime()
        close_failure.close_failure = True
        _assert_unavailable(self, close_failure)
        self.assertEqual(close_failure.closed, [_snapshot()])

    def test_source_and_database_failures_are_generic_non_leaking_and_cleaned_up(self):
        operations = (
            "begin_read_snapshot",
            "effective_permission_evidence",
            "has_permission",
            "complete_account_manifest",
            "complete_fiscal_year_applicability",
            "final_snapshot_evidence",
        )
        for operation in operations:
            with self.subTest(operation=operation):
                runtime = SyntheticPermissionedRuntime()
                runtime.fail_operation = operation
                error = _assert_unavailable(self, runtime)
                self.assertNotIn("LEAK", str(error))
                if operation == "begin_read_snapshot":
                    self.assertEqual(runtime.closed, [])
                else:
                    self.assertEqual(runtime.closed, [_snapshot()])

        for doctype in ("Company", "Fiscal Year", "Account", "GL Entry"):
            with self.subTest(doctype=doctype):
                runtime = SyntheticPermissionedRuntime()
                runtime.fail_doctype = doctype
                error = _assert_unavailable(self, runtime)
                self.assertEqual(str(error), "finance_read_unavailable")
                self.assertNotIn(COMPANY, str(error))
                self.assertNotIn(doctype, str(error))
                self.assertEqual(runtime.closed, [_snapshot()])

    def test_deterministic_normalization_under_reordered_owned_source_rows(self):
        forward_runtime = SyntheticPermissionedRuntime()
        reverse_runtime = SyntheticPermissionedRuntime()
        for rows in reverse_runtime.rows.values():
            rows.reverse()
        reverse_runtime.manifests = [
            _manifest(
                account_ids=tuple(reversed(ACCOUNT_IDS)),
                root_account_ids=tuple(reversed(ROOT_IDS)),
            ),
            _manifest(
                account_ids=tuple(reversed(ACCOUNT_IDS)),
                root_account_ids=tuple(reversed(ROOT_IDS)),
            ),
        ]

        forward = _read(forward_runtime)
        reverse = _read(reverse_runtime)

        self.assertEqual(forward, reverse)

    def test_final_result_contains_no_gl_source_or_voucher_identity(self):
        runtime = SyntheticPermissionedRuntime()

        result = _read(runtime)
        rendered = repr(result)

        for row in GL_ROWS:
            self.assertNotIn(str(row["name"]), rendered)
        for forbidden in (
            "voucher_no",
            "voucher_type",
            "party",
            "LEAK_DATABASE",
            "BOOK_UNKNOWN_SECRET",
        ):
            self.assertNotIn(forbidden, rendered)


if __name__ == "__main__":
    raise SystemExit("direct execution is not authorized")
