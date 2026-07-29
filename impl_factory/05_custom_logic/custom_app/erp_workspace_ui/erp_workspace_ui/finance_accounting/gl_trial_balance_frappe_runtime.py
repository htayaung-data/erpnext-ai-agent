"""Fail-closed Frappe binding for the internal GL / Trial Balance adapter.

The module deliberately does not import Frappe.  A future protected service
gate must inject the active Frappe modules and an exact, deployment-approved
environment policy.  Importing this module therefore cannot open a database
connection or touch a Frappe site.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from importlib import metadata
from typing import Final

from .gl_trial_balance_adapter import (
    CompleteAccountManifest,
    CompleteFiscalYearApplicability,
    EffectivePermissionEvidence,
    GLTrialBalanceAdapterError,
    ReadSnapshotEvidence,
    UserPermissionRule,
)


__all__ = [
    "FrappeGLTrialBalanceRuntime",
    "GLTrialBalanceRuntimePolicy",
]


_GENERIC_ERROR: Final = "finance_read_unavailable"
_PYMYSQL: Final = "pymysql"
_MYSQLCLIENT: Final = "mysqlclient"
_SUPPORTED_DRIVERS: Final = {
    _PYMYSQL: (
        "1.1.2",
        "PyMySQL",
        "frappe.database.mariadb.database",
        "pymysql.connections",
    ),
    _MYSQLCLIENT: (
        "2.2.7",
        "mysqlclient",
        "frappe.database.mariadb.mysqlclient",
        "MySQLdb.connections",
    ),
}
_SNAPSHOT_PHASES: Final = frozenset(
    {
        "snapshot_runtime_construct",
        "snapshot_wrapper_bind",
        "snapshot_raw_connection",
        "snapshot_driver_identity",
        "snapshot_preflight_query",
        "snapshot_server_identity",
        "snapshot_connection_identity",
        "snapshot_transaction_idle",
        "snapshot_set_isolation",
        "snapshot_start",
        "snapshot_state",
        "snapshot_evidence_build",
    }
)

# MariaDB's @@tx_isolation and @@tx_read_only expose default/session state,
# not authoritative state for the transaction currently in progress.  The
# owned snapshot is therefore proved by successful execution of the two exact
# statements below, followed by continuous active-transaction and connection
# identity checks until the terminal rollback.
_PREFLIGHT_SQL: Final = (
    "SELECT VERSION(), CONNECTION_ID(), @@in_transaction"
)
_SET_ISOLATION_SQL: Final = (
    "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ"
)
_START_SNAPSHOT_SQL: Final = (
    "START TRANSACTION READ ONLY, WITH CONSISTENT SNAPSHOT"
)
_STATE_SQL: Final = _PREFLIGHT_SQL
_ROLLBACK_SQL: Final = "ROLLBACK AND NO CHAIN"

_ACCOUNT_COUNT_SQL: Final = (
    "SELECT COUNT(DISTINCT `name`) FROM `tabAccount` "
    "WHERE `company` = %(company)s"
)
_GL_COUNT_SQL: Final = (
    "SELECT COUNT(DISTINCT `name`) FROM `tabGL Entry` "
    "WHERE `company` = %(company)s "
    "AND `posting_date` <= %(to_date)s "
    "AND `is_cancelled` = 0 "
    "AND (`finance_book` = %(finance_book)s "
    "OR `finance_book` = '' OR `finance_book` IS NULL)"
)
_FISCAL_APPLICABILITY_SQL: Final = (
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

_COMPANY_FIELDS: Final = ("name", "default_currency", "default_finance_book")
_FISCAL_YEAR_FIELDS: Final = (
    "name",
    "year_start_date",
    "year_end_date",
    "disabled",
)
_FISCAL_YEAR_COMPANY_FIELDS: Final = ("parent", "company")
_FINANCE_BOOK_FIELDS: Final = ("name", "finance_book_name")
_DIMENSION_FIELDS: Final = ("name", "document_type", "fieldname", "disabled")
_ACCOUNT_FIELDS: Final = (
    "name",
    "company",
    "parent_account",
    "is_group",
    "root_type",
    "lft",
    "rgt",
    "account_currency",
    "disabled",
)
_GL_FIELDS: Final = (
    "name",
    "company",
    "posting_date",
    "account",
    "debit",
    "credit",
    "is_cancelled",
    "is_opening",
    "finance_book",
)


@dataclass(frozen=True, slots=True)
class GLTrialBalanceRuntimePolicy:
    """Exact environment fingerprint approved by a later execution gate."""

    expected_driver: str
    expected_driver_version: str
    expected_server_version: str


@dataclass(slots=True)
class _SnapshotContext:
    token: str
    user: str
    company: str
    wrapper: object
    raw_connection: object
    connection_id: int
    driver: str
    active: bool = True
    invalid: bool = False


def _raise_unavailable() -> None:
    raise GLTrialBalanceAdapterError()


def _text(value: object, *, allow_empty: bool = False) -> str:
    if type(value) is not str or value != value.strip():
        _raise_unavailable()
    if not allow_empty and not value:
        _raise_unavailable()
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        _raise_unavailable()
    return value


def _db_flag(value: object) -> int:
    if type(value) is int and value in (0, 1):
        return value
    _raise_unavailable()


def _mapping_value(value: object, key: str) -> object:
    if isinstance(value, Mapping):
        if key not in value:
            _raise_unavailable()
        return value[key]
    try:
        return getattr(value, key)
    except Exception:
        _raise_unavailable()


class FrappeGLTrialBalanceRuntime:
    """Concrete, internal implementation of ``PermissionedSnapshotRuntime``."""

    def __init__(
        self,
        *,
        frappe_module: object,
        permissions_module: object,
        policy: GLTrialBalanceRuntimePolicy,
        distribution_version: Callable[[str], str] = metadata.version,
        snapshot_phase_hook: Callable[[str], None] | None = None,
    ) -> None:
        if snapshot_phase_hook is not None and not callable(
            snapshot_phase_hook
        ):
            _raise_unavailable()
        self._snapshot_phase_hook = snapshot_phase_hook
        self._snapshot_phase("snapshot_runtime_construct")
        if type(policy) is not GLTrialBalanceRuntimePolicy:
            _raise_unavailable()
        driver = _text(policy.expected_driver)
        driver_version = _text(policy.expected_driver_version)
        _text(policy.expected_server_version)
        supported = _SUPPORTED_DRIVERS.get(driver)
        if supported is None or driver_version != supported[0]:
            _raise_unavailable()
        if frappe_module is None or permissions_module is None or not callable(distribution_version):
            _raise_unavailable()
        self._frappe = frappe_module
        self._permissions = permissions_module
        self._policy = policy
        self._distribution_version = distribution_version
        self._context: _SnapshotContext | None = None
        self._last_closed_token: str | None = None
        self._generation = 0

    def _snapshot_phase(self, phase: str) -> None:
        if type(phase) is not str or phase not in _SNAPSHOT_PHASES:
            _raise_unavailable()
        hook = self._snapshot_phase_hook
        if hook is None:
            return
        failed = False
        result: object = None
        try:
            result = hook(phase)
        except Exception:
            failed = True
        if failed or result is not None:
            _raise_unavailable()

    @staticmethod
    def _protected(call: Callable[[], object]) -> object:
        failed = False
        value: object = None
        try:
            value = call()
        except Exception:
            failed = True
        if failed:
            # Raise after leaving the handler so source exceptions are not chained.
            _raise_unavailable()
        return value

    def _local(self) -> object:
        return getattr(self._frappe, "local")

    def _wrapper(self) -> object:
        return getattr(self._local(), "db")

    def _raw_connection(self, wrapper: object) -> object:
        raw = getattr(wrapper, "_conn")
        if raw is None:
            _raise_unavailable()
        return raw

    def _require_approved_wrapper_identity(self, wrapper: object) -> None:
        supported = _SUPPORTED_DRIVERS.get(self._policy.expected_driver)
        if supported is None:
            _raise_unavailable()
        expected_wrapper_module = supported[2]
        if self._class_identity(wrapper) != (
            expected_wrapper_module,
            "MariaDBDatabase",
        ):
            _raise_unavailable()

    @staticmethod
    def _close_new_connection_handles(
        wrapper: object, returned: object
    ) -> None:
        candidates: list[object] = []
        if returned is not None:
            candidates.append(returned)
        try:
            bound = getattr(wrapper, "_conn")
        except Exception:
            bound = None
        if bound is not None and not any(
            bound is candidate for candidate in candidates
        ):
            candidates.append(bound)
        for candidate in candidates:
            try:
                close = getattr(candidate, "close")
                if callable(close):
                    close()
            except Exception:
                pass

    def _begin_raw_connection(self, wrapper: object) -> object:
        self._require_approved_wrapper_identity(wrapper)
        self._deny_replica(wrapper)
        raw = getattr(wrapper, "_conn")
        if raw is not None:
            return raw

        returned: object = None
        try:
            connect = getattr(wrapper, "connect")
            if not callable(connect):
                raise ValueError
            returned = connect()
            if returned is not None:
                raise ValueError
            rebound_wrapper = self._wrapper()
            if rebound_wrapper is not wrapper:
                raise ValueError
            self._require_approved_wrapper_identity(rebound_wrapper)
            self._deny_replica(rebound_wrapper)
            return self._raw_connection(rebound_wrapper)
        except Exception:
            self._close_new_connection_handles(wrapper, returned)
            _raise_unavailable()

    @staticmethod
    def _class_identity(value: object) -> tuple[str, str]:
        cls = type(value)
        return _text(cls.__module__), _text(cls.__name__)

    def _config_value(self, key: str) -> object:
        conf = getattr(self._local(), "conf")
        if isinstance(conf, Mapping):
            return conf.get(key)
        getter = getattr(conf, "get", None)
        if callable(getter):
            return getter(key)
        return getattr(conf, key, None)

    def _deny_replica(self, wrapper: object) -> None:
        local = self._local()
        if getattr(local, "primary_db", None) is not None:
            _raise_unavailable()
        if getattr(local, "replica_db", None) is not None:
            _raise_unavailable()
        if wrapper is not getattr(local, "db"):
            _raise_unavailable()
        for key in (
            "read_from_replica",
            "replica_host",
            "replica_db_name",
            "replica_db_user",
            "replica_db_password",
            "different_credentials_for_replica",
        ):
            value = self._config_value(key)
            if value not in (None, "", 0, False):
                _raise_unavailable()

    @staticmethod
    def _close_cursor(cursor: object) -> None:
        close = getattr(cursor, "close")
        close()

    def _raw_one(
        self,
        raw: object,
        statement: str,
        parameters: Mapping[str, object] | None = None,
    ) -> tuple[object, ...]:
        cursor: object | None = None
        failed = False
        row: object = None
        try:
            cursor = getattr(raw, "cursor")()
            execute = getattr(cursor, "execute")
            if parameters is None:
                execute(statement)
            else:
                execute(statement, dict(parameters))
            row = getattr(cursor, "fetchone")()
            if getattr(cursor, "fetchone")() is not None:
                raise ValueError
            self._close_cursor(cursor)
            cursor = None
        except Exception:
            failed = True
            if cursor is not None:
                try:
                    self._close_cursor(cursor)
                except Exception:
                    pass
        if failed or type(row) not in (tuple, list):
            _raise_unavailable()
        return tuple(row)

    def _raw_execute(self, raw: object, statement: str) -> None:
        cursor: object | None = None
        failed = False
        try:
            cursor = getattr(raw, "cursor")()
            getattr(cursor, "execute")(statement)
            self._close_cursor(cursor)
            cursor = None
        except Exception:
            failed = True
            if cursor is not None:
                try:
                    self._close_cursor(cursor)
                except Exception:
                    pass
        if failed:
            _raise_unavailable()

    def _detect_environment(
        self, wrapper: object, raw: object
    ) -> tuple[str, int]:
        wrapper_module, wrapper_name = self._class_identity(wrapper)
        raw_module, raw_name = self._class_identity(raw)
        if wrapper_name != "MariaDBDatabase" or raw_name != "Connection":
            _raise_unavailable()
        selected_driver: str | None = None
        for driver, (_, distribution, expected_wrapper, expected_raw) in _SUPPORTED_DRIVERS.items():
            if wrapper_module == expected_wrapper and raw_module == expected_raw:
                selected_driver = driver
                actual_distribution = self._distribution_version(distribution)
                if type(actual_distribution) is not str:
                    _raise_unavailable()
                if actual_distribution != self._policy.expected_driver_version:
                    _raise_unavailable()
                break
        if selected_driver is None or selected_driver != self._policy.expected_driver:
            _raise_unavailable()
        self._snapshot_phase("snapshot_preflight_query")
        preflight = self._raw_one(raw, _PREFLIGHT_SQL)
        if len(preflight) != 3:
            _raise_unavailable()
        self._snapshot_phase("snapshot_server_identity")
        server_version = _text(preflight[0])
        if server_version != self._policy.expected_server_version:
            _raise_unavailable()
        self._snapshot_phase("snapshot_connection_identity")
        connection_id = preflight[1]
        if type(connection_id) is not int or connection_id <= 0:
            _raise_unavailable()
        self._snapshot_phase("snapshot_transaction_idle")
        in_transaction = preflight[2]
        if _db_flag(in_transaction) != 0:
            _raise_unavailable()
        return selected_driver, connection_id

    def _state(self, context: _SnapshotContext) -> None:
        state = self._raw_one(context.raw_connection, _STATE_SQL)
        if (
            len(state) != 3
            or state[0] != self._policy.expected_server_version
            or type(state[1]) is not int
            or state[1] != context.connection_id
            or _db_flag(state[2]) != 1
        ):
            _raise_unavailable()

    def _validate_binding(
        self, context: _SnapshotContext, wrapper: object, raw: object
    ) -> None:
        supported = _SUPPORTED_DRIVERS.get(context.driver)
        if supported is None:
            _raise_unavailable()
        _, _, _expected_wrapper_module, expected_raw_module = supported
        self._require_approved_wrapper_identity(wrapper)
        if self._class_identity(raw) != (expected_raw_module, "Connection"):
            _raise_unavailable()
        if wrapper is not context.wrapper or raw is not context.raw_connection:
            _raise_unavailable()

    def _invalidate_context(self, context: _SnapshotContext) -> None:
        context.active = False
        context.invalid = True
        if self._context is context:
            self._context = None
        self._last_closed_token = context.token
        self._exceptional_teardown(
            context.raw_connection,
            context.connection_id,
            mutation_attempted=True,
        )

    def _context_for(self, snapshot: ReadSnapshotEvidence) -> _SnapshotContext:
        if type(snapshot) is not ReadSnapshotEvidence:
            _raise_unavailable()
        context = self._context
        if (
            context is None
            or not context.active
            or context.invalid
            or snapshot.token != context.token
            or snapshot.user != context.user
            or snapshot.company != context.company
        ):
            _raise_unavailable()
        failed = False
        try:
            if self._current_user() != context.user:
                raise ValueError
            wrapper = self._wrapper()
            raw = self._raw_connection(wrapper)
            self._deny_replica(wrapper)
            self._validate_binding(context, wrapper, raw)
            self._state(context)
        except Exception:
            failed = True
        if failed:
            self._invalidate_context(context)
            _raise_unavailable()
        return context

    def _snapshot_evidence(self, context: _SnapshotContext) -> ReadSnapshotEvidence:
        return ReadSnapshotEvidence(
            token=context.token,
            user=context.user,
            company=context.company,
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

    def current_user(self) -> object:
        return self._protected(self._current_user)

    def _current_user(self) -> str:
        session = getattr(self._local(), "session")
        return _text(_mapping_value(session, "user"))

    def begin_read_snapshot(self, user: str, company: str) -> object:
        return self._protected(lambda: self._begin_read_snapshot(user, company))

    def _begin_read_snapshot(self, user: str, company: str) -> ReadSnapshotEvidence:
        user = _text(user)
        company = _text(company)
        raw: object | None = None
        connection_id: int | None = None
        mutation_attempted = False
        try:
            self._snapshot_phase("snapshot_wrapper_bind")
            if user != self._current_user() or self._context is not None:
                raise ValueError
            wrapper = self._wrapper()
            self._snapshot_phase("snapshot_raw_connection")
            raw = self._begin_raw_connection(wrapper)
            self._snapshot_phase("snapshot_driver_identity")
            self._deny_replica(wrapper)
            driver, connection_id = self._detect_environment(wrapper, raw)
            # A failed SET may still have reached the server; cleanup must not
            # treat a cursor-close failure as proof that no mutation occurred.
            self._snapshot_phase("snapshot_set_isolation")
            mutation_attempted = True
            self._raw_execute(raw, _SET_ISOLATION_SQL)
            # The SET applies to the next transaction; the immediately
            # following START constructs that same transaction as read-only
            # with a consistent snapshot.  _state then proves that it remains
            # active on the same wrapper, raw connection, and server session.
            # No session-default variable is treated as current-state proof.
            self._snapshot_phase("snapshot_start")
            self._raw_execute(raw, _START_SNAPSHOT_SQL)
            self._generation += 1
            self._snapshot_phase("snapshot_state")
            context = _SnapshotContext(
                token=f"gl_tb_snapshot_{self._generation}",
                user=user,
                company=company,
                wrapper=wrapper,
                raw_connection=raw,
                connection_id=connection_id,
                driver=driver,
            )
            self._state(context)
            self._snapshot_phase("snapshot_evidence_build")
            self._context = context
            return self._snapshot_evidence(context)
        except Exception:
            if raw is not None:
                self._exceptional_teardown(
                    raw, connection_id, mutation_attempted=mutation_attempted
                )
            _raise_unavailable()

    def _exceptional_teardown(
        self,
        raw: object,
        connection_id: int | None,
        *,
        mutation_attempted: bool,
    ) -> None:
        if mutation_attempted:
            try:
                self._raw_execute(raw, _ROLLBACK_SQL)
                if connection_id is not None:
                    state = self._raw_one(raw, _STATE_SQL)
                    if (
                        len(state) != 3
                        or state[0] != self._policy.expected_server_version
                        or state[1] != connection_id
                        or _db_flag(state[2]) != 0
                    ):
                        raise ValueError
            except Exception:
                pass
        # Exceptional uncertainty must not leave a reconnectable Frappe-owned
        # raw connection available to later code in the request.
        try:
            getattr(raw, "close")()
        except Exception:
            pass

    def effective_permission_evidence(
        self, snapshot: ReadSnapshotEvidence
    ) -> object:
        return self._protected(lambda: self._effective_permissions(snapshot))

    def _effective_permissions(
        self, snapshot: ReadSnapshotEvidence
    ) -> EffectivePermissionEvidence:
        context = self._context_for(snapshot)
        roles_value = getattr(self._frappe, "get_roles")(context.user)
        self._context_for(snapshot)
        if isinstance(roles_value, (str, bytes, bytearray)) or not isinstance(
            roles_value, Sequence
        ):
            _raise_unavailable()
        roles = tuple(_text(role) for role in roles_value)
        if len(set(roles)) != len(roles):
            _raise_unavailable()
        permission_value = getattr(self._permissions, "get_user_permissions")(
            context.user
        )
        self._context_for(snapshot)
        rules = self._parse_user_permissions(permission_value)
        return EffectivePermissionEvidence(
            snapshot_token=context.token,
            user=context.user,
            company=context.company,
            roles=tuple(sorted(roles)),
            user_permissions=rules,
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

    def _parse_user_permissions(self, value: object) -> tuple[UserPermissionRule, ...]:
        if not isinstance(value, Mapping):
            _raise_unavailable()
        rules: list[UserPermissionRule] = []
        seen: set[tuple[object, ...]] = set()
        for raw_allow, entries in value.items():
            allow = _text(raw_allow)
            if isinstance(entries, (str, bytes, bytearray)) or not isinstance(
                entries, Sequence
            ):
                _raise_unavailable()
            for entry in entries:
                if not isinstance(entry, Mapping) or frozenset(entry) != frozenset(
                    {"doc", "applicable_for", "is_default", "hide_descendants"}
                ):
                    _raise_unavailable()
                for_value = _text(entry["doc"])
                applicable = entry["applicable_for"]
                if applicable is not None:
                    applicable = _text(applicable, allow_empty=True)
                _db_flag(entry["is_default"])
                hide_descendants = _db_flag(entry["hide_descendants"])
                apply_to_all = 1 if applicable in (None, "") else 0
                identity = (
                    allow,
                    for_value,
                    applicable,
                    apply_to_all,
                    hide_descendants,
                )
                if identity in seen:
                    _raise_unavailable()
                seen.add(identity)
                rules.append(
                    UserPermissionRule(
                        allow=allow,
                        for_value=for_value,
                        applicable_for=applicable,
                        apply_to_all_doctypes=apply_to_all,
                        hide_descendants=hide_descendants,
                    )
                )
        return tuple(
            sorted(
                rules,
                key=lambda item: (
                    item.allow,
                    item.for_value,
                    item.applicable_for or "",
                    item.apply_to_all_doctypes,
                    item.hide_descendants,
                ),
            )
        )

    def has_permission(
        self,
        snapshot: ReadSnapshotEvidence,
        user: str,
        doctype: str,
        permission_type: str,
    ) -> object:
        return self._protected(
            lambda: self._has_permission(
                snapshot, user, doctype, permission_type
            )
        )

    def _has_permission(
        self,
        snapshot: ReadSnapshotEvidence,
        user: str,
        doctype: str,
        permission_type: str,
    ) -> bool:
        context = self._context_for(snapshot)
        if _text(user) != context.user:
            _raise_unavailable()
        doctype = _text(doctype)
        permission_type = _text(permission_type)
        parent = "Fiscal Year" if doctype == "Fiscal Year Company" else None
        value = getattr(self._frappe, "has_permission")(
            doctype=doctype,
            ptype=permission_type,
            user=context.user,
            throw=False,
            parent_doctype=parent,
        )
        self._context_for(snapshot)
        if type(value) is not bool:
            _raise_unavailable()
        return value

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
        return self._protected(
            lambda: self._get_list(
                snapshot,
                doctype,
                fields,
                filters,
                or_filters,
                order_by,
                limit,
            )
        )

    def _get_list(
        self,
        snapshot: ReadSnapshotEvidence,
        doctype: str,
        fields: tuple[str, ...],
        filters: tuple[tuple[str, str, object], ...],
        or_filters: tuple[tuple[str, str, object], ...],
        order_by: str,
        limit: int,
    ) -> tuple[dict[str, object], ...]:
        context = self._context_for(snapshot)
        parent_doctype, actual_filters = self._validate_list_contract(
            context,
            doctype,
            fields,
            filters,
            or_filters,
            order_by,
            limit,
        )
        rows = self._permission_list(
            snapshot,
            doctype=doctype,
            fields=fields,
            filters=actual_filters,
            or_filters=or_filters,
            order_by=order_by,
            limit=limit,
            parent_doctype=parent_doctype,
        )
        self._deny_cross_company(context, doctype, rows)
        if doctype == "GL Entry":
            finance_book = or_filters[0][2]
            aggregate = self._count_gl_entries(
                snapshot,
                context.company,
                filters[1][2],
                finance_book,
            )
            if aggregate != len(rows):
                _raise_unavailable()
        return rows

    def _permission_list(
        self,
        snapshot: ReadSnapshotEvidence,
        *,
        doctype: str,
        fields: tuple[str, ...],
        filters: tuple[tuple[str, str, object], ...],
        or_filters: tuple[tuple[str, str, object], ...],
        order_by: str,
        limit: int,
        parent_doctype: str | None,
    ) -> tuple[dict[str, object], ...]:
        self._context_for(snapshot)
        value = getattr(self._frappe, "get_list")(
            doctype,
            fields=list(fields),
            filters=[list(item) for item in filters],
            or_filters=[list(item) for item in or_filters],
            order_by=order_by,
            limit=limit,
            as_list=False,
            ignore_permissions=False,
            parent_doctype=parent_doctype,
        )
        self._context_for(snapshot)
        if isinstance(value, (str, bytes, bytearray)) or not isinstance(
            value, Sequence
        ):
            _raise_unavailable()
        # The adapter supplies cap-plus-one as the query limit.  Reaching
        # that sentinel is itself a deterministic rejection.
        if len(value) >= limit:
            _raise_unavailable()
        rows: list[dict[str, object]] = []
        for item in value:
            if not isinstance(item, Mapping) or frozenset(item) != frozenset(fields):
                _raise_unavailable()
            rows.append(dict(item))
        return tuple(rows)

    @staticmethod
    def _validate_list_contract(
        context: _SnapshotContext,
        doctype: str,
        fields: tuple[str, ...],
        filters: tuple[tuple[str, str, object], ...],
        or_filters: tuple[tuple[str, str, object], ...],
        order_by: str,
        limit: int,
    ) -> tuple[str | None, tuple[tuple[str, str, object], ...]]:
        if type(limit) is not int or limit <= 0:
            _raise_unavailable()
        expected: dict[str, tuple[tuple[str, ...], str]] = {
            "Company": (_COMPANY_FIELDS, "name asc"),
            "Fiscal Year": (_FISCAL_YEAR_FIELDS, "year_start_date asc, name asc"),
            "Fiscal Year Company": (_FISCAL_YEAR_COMPANY_FIELDS, "parent asc, company asc"),
            "Finance Book": (_FINANCE_BOOK_FIELDS, "name asc"),
            "Accounting Dimension": (_DIMENSION_FIELDS, "name asc"),
            "Account": (_ACCOUNT_FIELDS, "lft asc, name asc"),
            "GL Entry": (_GL_FIELDS, "posting_date asc, name asc"),
        }
        if doctype not in expected or fields != expected[doctype][0] or order_by != expected[doctype][1]:
            _raise_unavailable()
        parent: str | None = None
        actual = filters
        if doctype == "Company":
            valid = filters == (("name", "=", context.company),) and not or_filters
        elif doctype == "Fiscal Year":
            valid = filters == (("disabled", "=", 0),) and not or_filters
        elif doctype == "Fiscal Year Company":
            valid = (
                len(filters) == 2
                and filters[0][0:2] == ("parent", "in")
                and type(filters[0][2]) is tuple
                and bool(filters[0][2])
                and all(type(item) is str and item for item in filters[0][2])
                and filters[1] == ("company", "=", context.company)
                and not or_filters
            )
            parent = "Fiscal Year"
            actual = filters + (
                ("parenttype", "=", "Fiscal Year"),
                ("parentfield", "=", "companies"),
            )
        elif doctype == "Finance Book":
            valid = (
                len(filters) == 1
                and filters[0][0:2] == ("name", "=")
                and type(filters[0][2]) is str
                and bool(filters[0][2])
                and not or_filters
            )
        elif doctype == "Accounting Dimension":
            valid = filters == (("disabled", "=", 0),) and not or_filters
        elif doctype == "Account":
            valid = filters == (("company", "=", context.company),) and not or_filters
        else:
            valid = (
                len(filters) == 3
                and filters[0] == ("company", "=", context.company)
                and filters[1][0:2] == ("posting_date", "<=")
                and filters[2] == ("is_cancelled", "=", 0)
                and len(or_filters) == 3
                and or_filters[0][0:2] == ("finance_book", "=")
                and type(or_filters[0][2]) is str
                and bool(or_filters[0][2])
                and or_filters[1] == ("finance_book", "=", "")
                and or_filters[2] == ("finance_book", "is", "not set")
            )
        if not valid:
            _raise_unavailable()
        return parent, actual

    @staticmethod
    def _deny_cross_company(
        context: _SnapshotContext,
        doctype: str,
        rows: tuple[dict[str, object], ...],
    ) -> None:
        if doctype == "Company":
            if any(row.get("name") != context.company for row in rows):
                _raise_unavailable()
        elif doctype in {"Fiscal Year Company", "Account", "GL Entry"}:
            if any(row.get("company") != context.company for row in rows):
                _raise_unavailable()

    def _aggregate_one(
        self,
        snapshot: ReadSnapshotEvidence,
        statement: str,
        parameters: Mapping[str, object],
    ) -> tuple[object, ...]:
        context = self._context_for(snapshot)
        failed = False
        result: tuple[object, ...] = ()
        try:
            result = self._raw_one(
                context.raw_connection, statement, parameters
            )
        except Exception:
            failed = True
        if failed:
            self._invalidate_context(context)
            _raise_unavailable()
        self._context_for(snapshot)
        return result

    def _count_accounts(
        self, snapshot: ReadSnapshotEvidence, company: str
    ) -> int:
        row = self._aggregate_one(snapshot, _ACCOUNT_COUNT_SQL, {"company": company})
        if len(row) != 1 or type(row[0]) is not int or row[0] < 0:
            _raise_unavailable()
        return row[0]

    def _count_gl_entries(
        self,
        snapshot: ReadSnapshotEvidence,
        company: str,
        to_date: object,
        finance_book: object,
    ) -> int:
        row = self._aggregate_one(
            snapshot,
            _GL_COUNT_SQL,
            {
                "company": company,
                "to_date": to_date,
                "finance_book": finance_book,
            },
        )
        if len(row) != 1 or type(row[0]) is not int or row[0] < 0:
            _raise_unavailable()
        return row[0]

    def complete_account_manifest(
        self,
        snapshot: ReadSnapshotEvidence,
        company: str,
        max_accounts: int,
    ) -> object:
        return self._protected(
            lambda: self._complete_account_manifest(
                snapshot, company, max_accounts
            )
        )

    def _complete_account_manifest(
        self,
        snapshot: ReadSnapshotEvidence,
        company: str,
        max_accounts: int,
    ) -> CompleteAccountManifest:
        context = self._context_for(snapshot)
        if company != context.company or type(max_accounts) is not int or max_accounts <= 0:
            _raise_unavailable()
        rows = self._permission_list(
            snapshot,
            doctype="Account",
            fields=("name", "parent_account"),
            filters=(("company", "=", company),),
            or_filters=(),
            order_by="lft asc, name asc",
            limit=max_accounts + 1,
            parent_doctype=None,
        )
        count = self._count_accounts(snapshot, company)
        if count != len(rows) or count > max_accounts:
            _raise_unavailable()
        ids: list[str] = []
        roots: list[str] = []
        for row in rows:
            name = _text(row["name"])
            parent = row["parent_account"]
            if parent is not None:
                _text(parent)
            if name in ids:
                _raise_unavailable()
            ids.append(name)
            if parent is None:
                roots.append(name)
        if not ids or not roots:
            _raise_unavailable()
        return CompleteAccountManifest(
            snapshot_token=context.token,
            company=company,
            account_ids=tuple(ids),
            root_account_ids=tuple(roots),
            complete=True,
            permission_equivalent=True,
        )

    def complete_fiscal_year_applicability(
        self,
        snapshot: ReadSnapshotEvidence,
        company: str,
        max_fiscal_years: int,
    ) -> object:
        return self._protected(
            lambda: self._complete_fiscal_applicability(
                snapshot, company, max_fiscal_years
            )
        )

    def _complete_fiscal_applicability(
        self,
        snapshot: ReadSnapshotEvidence,
        company: str,
        maximum: int,
    ) -> CompleteFiscalYearApplicability:
        context = self._context_for(snapshot)
        if company != context.company or type(maximum) is not int or maximum <= 0:
            _raise_unavailable()
        rows = self._permission_list(
            snapshot,
            doctype="Fiscal Year",
            fields=("name",),
            filters=(("disabled", "=", 0),),
            or_filters=(),
            order_by="year_start_date asc, name asc",
            limit=maximum + 1,
            parent_doctype=None,
        )
        if not rows or len(rows) > maximum:
            _raise_unavailable()
        result: list[tuple[str, str]] = []
        seen: set[str] = set()
        for row in rows:
            fiscal_year = _text(row["name"])
            if fiscal_year in seen:
                _raise_unavailable()
            seen.add(fiscal_year)
            aggregate = self._aggregate_one(
                snapshot,
                _FISCAL_APPLICABILITY_SQL,
                {"fiscal_year": fiscal_year, "company": company},
            )
            if len(aggregate) != 2:
                _raise_unavailable()
            any_link = _db_flag(aggregate[0])
            selected = _db_flag(aggregate[1])
            if selected and not any_link:
                _raise_unavailable()
            state = (
                "global"
                if not any_link
                else "selected_company"
                if selected
                else "excluded"
            )
            result.append((fiscal_year, state))
        return CompleteFiscalYearApplicability(
            snapshot_token=context.token,
            company=company,
            fiscal_year_applicability=tuple(result),
            complete=True,
            permission_equivalent=True,
        )

    def final_snapshot_evidence(self, snapshot: ReadSnapshotEvidence) -> object:
        return self._protected(
            lambda: self._snapshot_evidence(self._context_for(snapshot))
        )

    def close_read_snapshot(self, snapshot: ReadSnapshotEvidence) -> None:
        self._protected(lambda: self._close_read_snapshot(snapshot))

    def _close_read_snapshot(self, snapshot: ReadSnapshotEvidence) -> None:
        if type(snapshot) is not ReadSnapshotEvidence:
            _raise_unavailable()
        if self._context is None and snapshot.token == self._last_closed_token:
            return
        context = self._context
        if context is None or snapshot.token != context.token:
            _raise_unavailable()
        failed = context.invalid
        try:
            if self._current_user() != context.user:
                raise ValueError
            wrapper = self._wrapper()
            raw = self._raw_connection(wrapper)
            self._deny_replica(wrapper)
            self._validate_binding(context, wrapper, raw)
            self._state(context)
            self._raw_execute(context.raw_connection, _ROLLBACK_SQL)

            # Re-resolve the whole binding after rollback so a replacement in
            # the close window cannot be mistaken for a clean termination.
            if self._current_user() != context.user:
                raise ValueError
            final_wrapper = self._wrapper()
            final_raw = self._raw_connection(final_wrapper)
            self._deny_replica(final_wrapper)
            self._validate_binding(context, final_wrapper, final_raw)
            state = self._raw_one(context.raw_connection, _STATE_SQL)
            if (
                len(state) != 3
                or state[0] != self._policy.expected_server_version
                or state[1] != context.connection_id
                or _db_flag(state[2]) != 0
            ):
                raise ValueError
        except Exception:
            failed = True
        context.active = False
        context.invalid = failed
        self._context = None
        self._last_closed_token = context.token
        if failed:
            try:
                getattr(context.raw_connection, "close")()
            except Exception:
                pass
            _raise_unavailable()
