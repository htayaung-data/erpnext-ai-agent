"""Pure, synthetic E2-B1 parser fixtures with no Finance runtime authority."""

from __future__ import annotations

import contextlib
import hashlib
import io
import os
import unittest
from typing import Callable


_E2B1_EXPECTED_COMMIT_SHA = "197f92bee02d8e836f529f37625be69b83e7acbd"
_E2B1_EXPECTED_ROOT_TREE_SHA = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
_E2B1_COMMIT_BODY_A = b'{"sha":"197f92bee02d8e836f529f37625be69b83e7acbd","node_id":"synthetic-node","url":"https://example.invalid/commit","html_url":"https://example.invalid/commit-view","author":{"date":"2026-01-01T00:00:00Z","name":"Synthetic User","email":"synthetic@example.invalid"},"committer":{"date":"2026-01-01T00:00:00Z","name":"Synthetic User","email":"synthetic@example.invalid"},"message":"Synthetic commit fixture","tree":{"url":"https://example.invalid/tree","sha":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},"parents":[],"verification":{"verified":false,"reason":"unsigned","signature":null,"payload":null,"verified_at":null}}'
_E2B1_COMMIT_BODY_B = b'{"verification":{"verified_at":null,"payload":null,"signature":null,"reason":"unsigned","verified":false},"parents":[],"tree":{"sha":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","url":"https://example.invalid/tree"},"message":"Synthetic commit fixture","committer":{"email":"synthetic@example.invalid","name":"Synthetic User","date":"2026-01-01T00:00:00Z"},"author":{"email":"synthetic@example.invalid","name":"Synthetic User","date":"2026-01-01T00:00:00Z"},"html_url":"https://example.invalid/commit-view","url":"https://example.invalid/commit","node_id":"synthetic-node","sha":"197f92bee02d8e836f529f37625be69b83e7acbd"}'
_E2B1_EXPECTED_COMMIT_PROJECTION = b'{"commit_sha":"197f92bee02d8e836f529f37625be69b83e7acbd","root_tree_sha":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}'
_E2B1_TREE_BODY_A = b'{"sha":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","url":"https://example.invalid/git/trees/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","tree":[{"path":"storage/innobase/synthetic_innodb_trx_probe.cc","mode":"100644","type":"blob","sha":"5555555555555555555555555555555555555555","url":"https://example.invalid/git/objects/5555555555555555555555555555555555555555"},{"path":"sql/synthetic_sql_kill_probe.cc","mode":"100644","type":"blob","sha":"4444444444444444444444444444444444444444","url":"https://example.invalid/git/objects/4444444444444444444444444444444444444444"},{"path":"sql/synthetic_replica_probe.cc","mode":"100644","type":"blob","sha":"7777777777777777777777777777777777777777","url":"https://example.invalid/git/objects/7777777777777777777777777777777777777777"},{"path":"sql/synthetic_processlist_probe.cc","mode":"100644","type":"blob","sha":"3333333333333333333333333333333333333333","url":"https://example.invalid/git/objects/3333333333333333333333333333333333333333"},{"path":"sql/synthetic_max_statement_time_probe.cc","mode":"100644","type":"blob","sha":"8888888888888888888888888888888888888888","url":"https://example.invalid/git/objects/8888888888888888888888888888888888888888"},{"path":"sql/synthetic_consistent_snapshot_probe.cc","mode":"100644","type":"blob","sha":"6666666666666666666666666666666666666666","url":"https://example.invalid/git/objects/6666666666666666666666666666666666666666"},{"path":"sql/synthetic_column_priv_probe.cc","mode":"100644","type":"blob","sha":"2222222222222222222222222222222222222222","url":"https://example.invalid/git/objects/2222222222222222222222222222222222222222"},{"path":"sql/synthetic_auth_probe.cc","mode":"100644","type":"blob","sha":"1111111111111111111111111111111111111111","url":"https://example.invalid/git/objects/1111111111111111111111111111111111111111"}],"truncated":false}'
_E2B1_TREE_BODY_B = b'{"truncated":false,"tree":[{"url":"https://example.invalid/git/objects/1111111111111111111111111111111111111111","sha":"1111111111111111111111111111111111111111","type":"blob","mode":"100644","path":"sql/synthetic_auth_probe.cc"},{"url":"https://example.invalid/git/objects/2222222222222222222222222222222222222222","sha":"2222222222222222222222222222222222222222","type":"blob","mode":"100644","path":"sql/synthetic_column_priv_probe.cc"},{"url":"https://example.invalid/git/objects/6666666666666666666666666666666666666666","sha":"6666666666666666666666666666666666666666","type":"blob","mode":"100644","path":"sql/synthetic_consistent_snapshot_probe.cc"},{"url":"https://example.invalid/git/objects/8888888888888888888888888888888888888888","sha":"8888888888888888888888888888888888888888","type":"blob","mode":"100644","path":"sql/synthetic_max_statement_time_probe.cc"},{"url":"https://example.invalid/git/objects/3333333333333333333333333333333333333333","sha":"3333333333333333333333333333333333333333","type":"blob","mode":"100644","path":"sql/synthetic_processlist_probe.cc"},{"url":"https://example.invalid/git/objects/7777777777777777777777777777777777777777","sha":"7777777777777777777777777777777777777777","type":"blob","mode":"100644","path":"sql/synthetic_replica_probe.cc"},{"url":"https://example.invalid/git/objects/4444444444444444444444444444444444444444","sha":"4444444444444444444444444444444444444444","type":"blob","mode":"100644","path":"sql/synthetic_sql_kill_probe.cc"},{"url":"https://example.invalid/git/objects/5555555555555555555555555555555555555555","sha":"5555555555555555555555555555555555555555","type":"blob","mode":"100644","path":"storage/innobase/synthetic_innodb_trx_probe.cc"}],"url":"https://example.invalid/git/trees/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","sha":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}'
_E2B1_EXPECTED_TREE_PROJECTION = b'{"commit_sha":"197f92bee02d8e836f529f37625be69b83e7acbd","root_tree_sha":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","truncated":false,"entries":[{"path":"sql/synthetic_auth_probe.cc","mode":"100644","type":"blob","object_sha":"1111111111111111111111111111111111111111"},{"path":"sql/synthetic_column_priv_probe.cc","mode":"100644","type":"blob","object_sha":"2222222222222222222222222222222222222222"},{"path":"sql/synthetic_consistent_snapshot_probe.cc","mode":"100644","type":"blob","object_sha":"6666666666666666666666666666666666666666"},{"path":"sql/synthetic_max_statement_time_probe.cc","mode":"100644","type":"blob","object_sha":"8888888888888888888888888888888888888888"},{"path":"sql/synthetic_processlist_probe.cc","mode":"100644","type":"blob","object_sha":"3333333333333333333333333333333333333333"},{"path":"sql/synthetic_replica_probe.cc","mode":"100644","type":"blob","object_sha":"7777777777777777777777777777777777777777"},{"path":"sql/synthetic_sql_kill_probe.cc","mode":"100644","type":"blob","object_sha":"4444444444444444444444444444444444444444"},{"path":"storage/innobase/synthetic_innodb_trx_probe.cc","mode":"100644","type":"blob","object_sha":"5555555555555555555555555555555555555555"}]}'
_E2B1_HISTORICAL_MISSING_Q_BODY = b'{"url":"https://api.github.com/tree/a","tree":[{"url":"https://api.github.com/blob/b","sha":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb","size":7,"type":"blob","mode":"100644","path":"sql/z.c","future_entry":"ignored"},{"path":"include/A.h","mode":"100755","type":"blob","sha":"cccccccccccccccccccccccccccccccccccccccc","url":"https://api.github.com/blob/c"}],"truncated":false,"sha":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","future_top":null}'
_E2B1_HISTORICAL_REJECTION_ONLY_SHA256 = "b70e3e547694bb24ac064ef12b6ad7cc15327eb4c04aea94d350912c4f7ead0b"

_E2B1_EXPECTED_TREE_ENTRIES = (
    ("sql/synthetic_auth_probe.cc", "100644", "blob", "1111111111111111111111111111111111111111"),
    ("sql/synthetic_column_priv_probe.cc", "100644", "blob", "2222222222222222222222222222222222222222"),
    ("sql/synthetic_consistent_snapshot_probe.cc", "100644", "blob", "6666666666666666666666666666666666666666"),
    ("sql/synthetic_max_statement_time_probe.cc", "100644", "blob", "8888888888888888888888888888888888888888"),
    ("sql/synthetic_processlist_probe.cc", "100644", "blob", "3333333333333333333333333333333333333333"),
    ("sql/synthetic_replica_probe.cc", "100644", "blob", "7777777777777777777777777777777777777777"),
    ("sql/synthetic_sql_kill_probe.cc", "100644", "blob", "4444444444444444444444444444444444444444"),
    ("storage/innobase/synthetic_innodb_trx_probe.cc", "100644", "blob", "5555555555555555555555555555555555555555"),
)
_E2B1_EXPECTED_TREE_CANDIDATES = (
    ("sql/synthetic_auth_probe.cc", "100644", "blob", "1111111111111111111111111111111111111111", ("Q1_ACCOUNT_HOST_MATCH",)),
    ("sql/synthetic_column_priv_probe.cc", "100644", "blob", "2222222222222222222222222222222222222222", ("Q2_TABLE_COLUMN_GRANT",)),
    ("sql/synthetic_consistent_snapshot_probe.cc", "100644", "blob", "6666666666666666666666666666666666666666", ("Q6_ISOLATION_READ_ONLY_SNAPSHOT",)),
    ("sql/synthetic_max_statement_time_probe.cc", "100644", "blob", "8888888888888888888888888888888888888888", ("Q8_STATEMENT_TIMEOUT",)),
    ("sql/synthetic_processlist_probe.cc", "100644", "blob", "3333333333333333333333333333333333333333", ("Q3_PROCESS_VISIBILITY",)),
    ("sql/synthetic_replica_probe.cc", "100644", "blob", "7777777777777777777777777777777777777777", ("Q7_REPLICA_TOPOLOGY_PRIVILEGE",)),
    ("sql/synthetic_sql_kill_probe.cc", "100644", "blob", "4444444444444444444444444444444444444444", ("Q4_EXACT_CONNECTION_TERMINATION",)),
    ("storage/innobase/synthetic_innodb_trx_probe.cc", "100644", "blob", "5555555555555555555555555555555555555555", ("Q5_INNODB_TRX_VISIBILITY",)),
)
_E2B1_TREE_B_ENTRY_FRAGMENTS = (
    b'{"url":"https://example.invalid/git/objects/1111111111111111111111111111111111111111","sha":"1111111111111111111111111111111111111111","type":"blob","mode":"100644","path":"sql/synthetic_auth_probe.cc"}',
    b'{"url":"https://example.invalid/git/objects/2222222222222222222222222222222222222222","sha":"2222222222222222222222222222222222222222","type":"blob","mode":"100644","path":"sql/synthetic_column_priv_probe.cc"}',
    b'{"url":"https://example.invalid/git/objects/6666666666666666666666666666666666666666","sha":"6666666666666666666666666666666666666666","type":"blob","mode":"100644","path":"sql/synthetic_consistent_snapshot_probe.cc"}',
    b'{"url":"https://example.invalid/git/objects/8888888888888888888888888888888888888888","sha":"8888888888888888888888888888888888888888","type":"blob","mode":"100644","path":"sql/synthetic_max_statement_time_probe.cc"}',
    b'{"url":"https://example.invalid/git/objects/3333333333333333333333333333333333333333","sha":"3333333333333333333333333333333333333333","type":"blob","mode":"100644","path":"sql/synthetic_processlist_probe.cc"}',
    b'{"url":"https://example.invalid/git/objects/7777777777777777777777777777777777777777","sha":"7777777777777777777777777777777777777777","type":"blob","mode":"100644","path":"sql/synthetic_replica_probe.cc"}',
    b'{"url":"https://example.invalid/git/objects/4444444444444444444444444444444444444444","sha":"4444444444444444444444444444444444444444","type":"blob","mode":"100644","path":"sql/synthetic_sql_kill_probe.cc"}',
    b'{"url":"https://example.invalid/git/objects/5555555555555555555555555555555555555555","sha":"5555555555555555555555555555555555555555","type":"blob","mode":"100644","path":"storage/innobase/synthetic_innodb_trx_probe.cc"}',
)
_E2B1_REJECTED_ENTRY_FRAGMENTS = (
    b'{"path":"docs/synthetic_processlist_probe.cc","mode":"100644","type":"blob","sha":"9999999999999999999999999999999999999999","url":"https://example.invalid/git/objects/9999999999999999999999999999999999999999"}',
    b'{"path":"sql/synthetic_processlist_probe.txt","mode":"100644","type":"blob","sha":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb","url":"https://example.invalid/git/objects/bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"}',
    b'{"path":"sql/synthetic_processlist_tree_probe.cc","mode":"040000","type":"tree","sha":"cccccccccccccccccccccccccccccccccccccccc","url":"https://example.invalid/git/objects/cccccccccccccccccccccccccccccccccccccccc"}',
)
_E2B1_EXPECTED_REJECTED_TUPLE_SHA256 = "8b7353752be6f67899ae65c128567afd0571324ea06c23fa74e7fc7dec879021"
_E2B1_NEUTRAL_TREE_ENTRY = b'{"path":"docs/synthetic_neutral_probe.cc","mode":"100644","type":"blob","sha":"9999999999999999999999999999999999999999","url":"https://example.invalid/git/objects/9999999999999999999999999999999999999999"}'


def _e2b1_fixture_parser_api() -> tuple[Callable[..., object], type[Exception], type[Exception]]:
    from erp_workspace_ui.tests.finance_gl_trial_balance_evidence_controller import (
        _E2B1ParseRejected,
        _E2B1ParserInternal,
        _parse_e2b1_response,
    )

    return _parse_e2b1_response, _E2B1ParseRejected, _E2B1ParserInternal


def _e2b1_fixture_splice_once(body: bytes, needle: bytes, replacement: bytes) -> bytes:
    position = body.find(needle)
    if position < 0 or body.find(needle, position + len(needle)) >= 0:
        raise AssertionError("fixture splice must match exactly once")
    return body[:position] + replacement + body[position + len(needle) :]


def _e2b1_fixture_append_member(body: bytes, member: bytes) -> bytes:
    if not body.endswith(b"}"):
        raise AssertionError("fixture body must end with one object")
    return body[:-1] + b"," + member + b"}"


def _e2b1_fixture_insert_tree_entries(body: bytes, entries: tuple[bytes, ...]) -> bytes:
    marker = b'],"truncated":false}'
    return _e2b1_fixture_splice_once(
        body,
        marker,
        b"," + b",".join(entries) + marker,
    )


def _e2b1_fixture_remove_tree_entry(body: bytes, entry: bytes) -> bytes:
    with_trailing_comma = entry + b","
    if body.find(with_trailing_comma) >= 0:
        return _e2b1_fixture_splice_once(body, with_trailing_comma, b"")
    return _e2b1_fixture_splice_once(body, b"," + entry, b"")


class TestFinanceGLTrialBalanceE2B1ParserFixtures(unittest.TestCase):
    """Sealed parser fixtures with no database, filesystem, or evidence ownership."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        if (
            os.environ.get("FINANCE_GL_TB_E2B1_PARSER_GATE")
            != "finance_gl_tb_e2b1_parser_v1"
        ):
            raise RuntimeError("parser-only fixture gate is not enabled")

    def _parse_commit(self, body: bytes) -> dict[str, object]:
        parser, _controlled, _internal = _e2b1_fixture_parser_api()
        return parser(
            mode="commit",
            body=body,
            expected_commit_sha=_E2B1_EXPECTED_COMMIT_SHA,
        )

    def _parse_tree(self, body: bytes) -> dict[str, object]:
        parser, _controlled, _internal = _e2b1_fixture_parser_api()
        return parser(
            mode="tree",
            body=body,
            expected_commit_sha=_E2B1_EXPECTED_COMMIT_SHA,
            expected_root_tree_sha=_E2B1_EXPECTED_ROOT_TREE_SHA,
        )

    def _assert_fixed_bytes(
        self,
        body: bytes,
        expected_length: int,
        expected_sha256: str,
    ) -> None:
        self.assertEqual(expected_length, len(body))
        self.assertEqual(expected_sha256, hashlib.sha256(body).hexdigest())
        self.assertFalse(body.startswith(b"\xef\xbb\xbf"))
        self.assertFalse(body.endswith(b"\n"))

    def _assert_failure(
        self,
        expected_exception: type[Exception],
        *,
        mode: object,
        body: object,
        expected_commit_sha: object,
        expected_root_tree_sha: object = None,
        leak_canaries: tuple[str, ...] = (),
    ) -> None:
        parser, _controlled, _internal = _e2b1_fixture_parser_api()
        result: object = None
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            with self.assertRaises(expected_exception) as caught:
                result = parser(
                    mode=mode,
                    body=body,
                    expected_commit_sha=expected_commit_sha,
                    expected_root_tree_sha=expected_root_tree_sha,
                )
        self.assertIsNone(result)
        self.assertEqual((), caught.exception.args)
        self.assertEqual("", str(caught.exception))
        self.assertEqual("", stdout.getvalue())
        self.assertEqual("", stderr.getvalue())
        disclosed = repr(caught.exception)
        self.assertNotIn("projection", disclosed.lower())
        self.assertNotIn("mapping", disclosed.lower())
        for canary in leak_canaries:
            self.assertNotIn(canary, disclosed)

    def _assert_controlled_rejection(
        self,
        body: bytes,
        *,
        mode: str = "tree",
        leak_canaries: tuple[str, ...] = (),
    ) -> None:
        _parser, controlled, _internal = _e2b1_fixture_parser_api()
        self._assert_failure(
            controlled,
            mode=mode,
            body=body,
            expected_commit_sha=_E2B1_EXPECTED_COMMIT_SHA,
            expected_root_tree_sha=(
                _E2B1_EXPECTED_ROOT_TREE_SHA if mode == "tree" else None
            ),
            leak_canaries=leak_canaries,
        )

    def _assert_internal_failure(
        self,
        *,
        mode: object,
        body: object,
        expected_commit_sha: object,
        expected_root_tree_sha: object = None,
        leak_canaries: tuple[str, ...] = (),
    ) -> None:
        _parser, _controlled, internal = _e2b1_fixture_parser_api()
        self._assert_failure(
            internal,
            mode=mode,
            body=body,
            expected_commit_sha=expected_commit_sha,
            expected_root_tree_sha=expected_root_tree_sha,
            leak_canaries=leak_canaries,
        )

    def test_e2b1_01_canonical_commit_bodies(self) -> None:
        self._assert_fixed_bytes(
            _E2B1_COMMIT_BODY_A,
            620,
            "2614932f825e98c3254f5ec4a80fcf18ed2227b97b29b6f7b450419142c5b4a3",
        )
        self._assert_fixed_bytes(
            _E2B1_COMMIT_BODY_B,
            620,
            "4c633f286358f68cb049b2bc4cd88cd1be55de6c9bd0020c959bf15b7653998a",
        )
        self.assertNotEqual(_E2B1_COMMIT_BODY_A, _E2B1_COMMIT_BODY_B)
        expected = {
            "mode": "commit",
            "commit_sha": _E2B1_EXPECTED_COMMIT_SHA,
            "root_tree_sha": _E2B1_EXPECTED_ROOT_TREE_SHA,
            "projection_bytes": _E2B1_EXPECTED_COMMIT_PROJECTION,
            "projection_sha256": "82465c3e106dfe3d0e75ea3cbfdc18dfe682f5fabb44bc86c4cce259979e2fe9",
        }
        results = tuple(self._parse_commit(body) for body in (_E2B1_COMMIT_BODY_A, _E2B1_COMMIT_BODY_B))
        self.assertEqual(expected, results[0])
        self.assertEqual(results[0], results[1])
        self.assertEqual(tuple(expected), tuple(results[0]))
        self._assert_fixed_bytes(
            results[0]["projection_bytes"],
            116,
            "82465c3e106dfe3d0e75ea3cbfdc18dfe682f5fabb44bc86c4cce259979e2fe9",
        )
        for omitted_key in (
            "node_id",
            "url",
            "html_url",
            "author",
            "committer",
            "message",
            "tree",
            "parents",
            "verification",
        ):
            self.assertNotIn(omitted_key, results[0])
        for omitted_value in (
            b"Synthetic User",
            b"synthetic@example.invalid",
            b"Synthetic commit fixture",
            b"https://example.invalid",
        ):
            self.assertNotIn(omitted_value, results[0]["projection_bytes"])

    def test_e2b1_02_canonical_tree_bodies(self) -> None:
        self._assert_fixed_bytes(
            _E2B1_TREE_BODY_A,
            1853,
            "778cfc6deaeb5129e16a17d444f0b3e305841bd6d22a5a09389d9fe9fe495522",
        )
        self._assert_fixed_bytes(
            _E2B1_TREE_BODY_B,
            1853,
            "578549ea05c4e4dbdd8f583be4e21b0af5483c828474048fd01bb659feda334f",
        )
        self.assertNotEqual(_E2B1_TREE_BODY_A, _E2B1_TREE_BODY_B)
        expected = {
            "mode": "tree",
            "commit_sha": _E2B1_EXPECTED_COMMIT_SHA,
            "root_tree_sha": _E2B1_EXPECTED_ROOT_TREE_SHA,
            "truncated": False,
            "entries": _E2B1_EXPECTED_TREE_ENTRIES,
            "projection_bytes": _E2B1_EXPECTED_TREE_PROJECTION,
            "projected_inventory_sha256": "45de585a728d5244dd9d6b783f1a4e8ddb84680eed5c141082c012e5b00646b6",
            "candidates": _E2B1_EXPECTED_TREE_CANDIDATES,
            "rejection_counts": (0, 0, 0),
            "rejected_tuple_sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
        }
        results = tuple(self._parse_tree(body) for body in (_E2B1_TREE_BODY_A, _E2B1_TREE_BODY_B))
        self.assertEqual(expected, results[0])
        self.assertEqual(results[0], results[1])
        self.assertEqual(tuple(expected), tuple(results[0]))
        self._assert_fixed_bytes(
            results[0]["projection_bytes"],
            1215,
            "45de585a728d5244dd9d6b783f1a4e8ddb84680eed5c141082c012e5b00646b6",
        )
        self.assertEqual(
            (
                "Q1_ACCOUNT_HOST_MATCH",
                "Q2_TABLE_COLUMN_GRANT",
                "Q6_ISOLATION_READ_ONLY_SNAPSHOT",
                "Q8_STATEMENT_TIMEOUT",
                "Q3_PROCESS_VISIBILITY",
                "Q7_REPLICA_TOPOLOGY_PRIVILEGE",
                "Q4_EXACT_CONNECTION_TERMINATION",
                "Q5_INNODB_TRX_VISIBILITY",
            ),
            tuple(candidate[4][0] for candidate in results[0]["candidates"]),
        )
        self.assertEqual(
            {
                "Q1_ACCOUNT_HOST_MATCH",
                "Q2_TABLE_COLUMN_GRANT",
                "Q3_PROCESS_VISIBILITY",
                "Q4_EXACT_CONNECTION_TERMINATION",
                "Q5_INNODB_TRX_VISIBILITY",
                "Q6_ISOLATION_READ_ONLY_SNAPSHOT",
                "Q7_REPLICA_TOPOLOGY_PRIVILEGE",
                "Q8_STATEMENT_TIMEOUT",
            },
            {candidate[4][0] for candidate in results[0]["candidates"]},
        )
        self.assertNotIn(b"https://", results[0]["projection_bytes"])

    def test_e2b1_03_missing_q_and_ambiguity_rejections(self) -> None:
        self._assert_controlled_rejection(
            _E2B1_HISTORICAL_MISSING_Q_BODY,
            leak_canaries=(
                "include/A.h",
                "sql/z.c",
                "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
                _E2B1_HISTORICAL_REJECTION_ONLY_SHA256,
            ),
        )
        required_categories = (
            "Q1_ACCOUNT_HOST_MATCH",
            "Q2_TABLE_COLUMN_GRANT",
            "Q6_ISOLATION_READ_ONLY_SNAPSHOT",
            "Q8_STATEMENT_TIMEOUT",
            "Q3_PROCESS_VISIBILITY",
            "Q7_REPLICA_TOPOLOGY_PRIVILEGE",
            "Q4_EXACT_CONNECTION_TERMINATION",
            "Q5_INNODB_TRX_VISIBILITY",
        )
        for category, fragment in zip(
            required_categories,
            _E2B1_TREE_B_ENTRY_FRAGMENTS,
            strict=True,
        ):
            body = _e2b1_fixture_remove_tree_entry(_E2B1_TREE_BODY_B, fragment)
            self._assert_controlled_rejection(
                body,
                leak_canaries=(category,),
            )

        for ambiguous_path in (
            b"sql/synthetic_grant_probe.cc",
            b"sql/synthetic_auth_column_priv_probe.cc",
        ):
            body = _e2b1_fixture_splice_once(
                _E2B1_TREE_BODY_A,
                b"sql/synthetic_auth_probe.cc",
                ambiguous_path,
            )
            self._assert_controlled_rejection(
                body,
                leak_canaries=(
                    ambiguous_path.decode("ascii"),
                    "1111111111111111111111111111111111111111",
                ),
            )

    def test_e2b1_04_json_encoding_and_complete_value_boundaries(self) -> None:
        canonical = self._parse_commit(_E2B1_COMMIT_BODY_A)
        self.assertEqual(canonical, self._parse_commit(_E2B1_COMMIT_BODY_A + b" \t\r\n"))

        malformed_bodies = (
            b"\xff",
            b"\xef\xbb\xbf" + _E2B1_COMMIT_BODY_A,
            b"",
            b'{"sha":',
            _E2B1_COMMIT_BODY_A + b"{}",
            b"[]",
            _e2b1_fixture_splice_once(
                _E2B1_COMMIT_BODY_A,
                b'{"sha":"197f92bee02d8e836f529f37625be69b83e7acbd","node_id"',
                b'{"sha":"197f92bee02d8e836f529f37625be69b83e7acbd","sha":"197f92bee02d8e836f529f37625be69b83e7acbd","node_id"',
            ),
            _e2b1_fixture_splice_once(
                _E2B1_COMMIT_BODY_A,
                b'"author":{"date":"2026-01-01T00:00:00Z","name"',
                b'"author":{"date":"2026-01-01T00:00:00Z","date":"2026-01-01T00:00:00Z","name"',
            ),
            _e2b1_fixture_append_member(
                _E2B1_COMMIT_BODY_A,
                b'"future":{"duplicate":1,"duplicate":2}',
            ),
            _e2b1_fixture_append_member(_E2B1_COMMIT_BODY_A, b'"future":NaN'),
            _e2b1_fixture_append_member(_E2B1_COMMIT_BODY_A, b'"future":Infinity'),
            _e2b1_fixture_append_member(_E2B1_COMMIT_BODY_A, b'"future":-Infinity'),
            _e2b1_fixture_append_member(_E2B1_COMMIT_BODY_A, b'"future":"\\ud800"'),
            _e2b1_fixture_append_member(_E2B1_COMMIT_BODY_A, b'"\\ud800":"value"'),
            _e2b1_fixture_append_member(_E2B1_COMMIT_BODY_A, b'"future":"bad\x01value"'),
        )
        for body in malformed_bodies:
            self._assert_controlled_rejection(
                body,
                mode="commit",
                leak_canaries=("bad", "duplicate"),
            )

    def test_e2b1_05_complete_schemas_additive_policy_and_enum(self) -> None:
        enriched_commit = _e2b1_fixture_splice_once(
            _E2B1_COMMIT_BODY_A,
            b'"author":{"date":"2026-01-01T00:00:00Z","name":"Synthetic User","email":"synthetic@example.invalid"}',
            b'"author":{"date":"2026-01-01T00:00:00Z","name":"Synthetic User","email":"synthetic@example.invalid","future_author":"ignored"}',
        )
        enriched_commit = _e2b1_fixture_splice_once(
            enriched_commit,
            b'"committer":{"date":"2026-01-01T00:00:00Z","name":"Synthetic User","email":"synthetic@example.invalid"}',
            b'"committer":{"date":"2026-01-01T00:00:00Z","name":"Synthetic User","email":"synthetic@example.invalid","future_committer":"ignored"}',
        )
        enriched_commit = _e2b1_fixture_splice_once(
            enriched_commit,
            b'"message":"Synthetic commit fixture"',
            b'"message":"Synthetic \\"quote\\" \\\\ reverse \\u0001 control"',
        )
        enriched_commit = _e2b1_fixture_splice_once(
            enriched_commit,
            b'"tree":{"url":"https://example.invalid/tree","sha":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}',
            b'"tree":{"url":"https://example.invalid/tree","sha":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","future_tree":"ignored"}',
        )
        enriched_commit = _e2b1_fixture_splice_once(
            enriched_commit,
            b'"parents":[]',
            b'"parents":[{"url":"https://example.invalid/parent","sha":"dddddddddddddddddddddddddddddddddddddddd","html_url":"https://example.invalid/parent-view","future_parent":"ignored"}]',
        )
        enriched_commit = _e2b1_fixture_splice_once(
            enriched_commit,
            b'"verification":{"verified":false,"reason":"unsigned","signature":null,"payload":null,"verified_at":null}',
            b'"verification":{"verified":false,"reason":"unsigned","signature":"synthetic-signature","payload":"synthetic-payload","verified_at":"2026-01-01T00:00:00Z","future_verification":"ignored"}',
        )
        enriched_commit = _e2b1_fixture_append_member(
            enriched_commit,
            b'"future_top":{"finite_float":1.25,"quote":"\\"","reverse":"\\\\","control":"\\u0002"}',
        )
        enriched_result = self._parse_commit(enriched_commit)
        self.assertEqual(
            self._parse_commit(_E2B1_COMMIT_BODY_A),
            enriched_result,
        )
        for omitted_canary in (
            b"future_author",
            b"future_committer",
            b"future_tree",
            b"future_parent",
            b"future_verification",
            b"future_top",
            b"synthetic-signature",
            b"synthetic-payload",
            b"quote",
            b"reverse",
            b"control",
        ):
            self.assertNotIn(omitted_canary, enriched_result["projection_bytes"])

        enriched_tree = _e2b1_fixture_splice_once(
            _E2B1_TREE_BODY_A,
            b'"path":"sql/synthetic_auth_probe.cc","mode":"100644"',
            b'"path":"sql/synthetic_auth_probe.cc","size":0,"future_entry":{"finite_float":2.5,"control":"\\u0003"},"mode":"100644"',
        )
        enriched_tree = _e2b1_fixture_append_member(
            enriched_tree,
            b'"future_top":{"finite_float":3.5}',
        )
        enriched_tree_result = self._parse_tree(enriched_tree)
        self.assertEqual(
            self._parse_tree(_E2B1_TREE_BODY_A),
            enriched_tree_result,
        )
        self.assertNotIn(b"future_entry", enriched_tree_result["projection_bytes"])
        self.assertNotIn(b"future_top", enriched_tree_result["projection_bytes"])

        for reason in (
            b"expired_key",
            b"not_signing_key",
            b"gpgverify_error",
            b"gpgverify_unavailable",
            b"unsigned",
            b"unknown_signature_type",
            b"no_user",
            b"unverified_email",
            b"bad_email",
            b"unknown_key",
            b"malformed_signature",
            b"invalid",
            b"valid",
        ):
            body = _e2b1_fixture_splice_once(
                _E2B1_COMMIT_BODY_A,
                b'"reason":"unsigned"',
                b'"reason":"' + reason + b'"',
            )
            self.assertEqual(self._parse_commit(_E2B1_COMMIT_BODY_A), self._parse_commit(body))

        invalid_commit_schema = (
            _e2b1_fixture_splice_once(
                _E2B1_COMMIT_BODY_A,
                b',"message":"Synthetic commit fixture"',
                b"",
            ),
            _e2b1_fixture_splice_once(
                _E2B1_COMMIT_BODY_A,
                b'"node_id":"synthetic-node"',
                b'"node_id":null',
            ),
            _e2b1_fixture_splice_once(
                _E2B1_COMMIT_BODY_A,
                b'"parents":[]',
                b'"parents":{}',
            ),
            _e2b1_fixture_splice_once(
                _E2B1_COMMIT_BODY_A,
                b',"email":"synthetic@example.invalid"},"committer"',
                b'},"committer"',
            ),
            _e2b1_fixture_splice_once(
                _E2B1_COMMIT_BODY_A,
                b'"committer":{"date":"2026-01-01T00:00:00Z","name":"Synthetic User","email":"synthetic@example.invalid"}',
                b'"committer":{"date":"2026-01-01T00:00:00Z","name":"Synthetic User","email":false}',
            ),
            _e2b1_fixture_splice_once(
                _E2B1_COMMIT_BODY_A,
                b'"tree":{"url":"https://example.invalid/tree","sha":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}',
                b'"tree":{"url":null,"sha":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}',
            ),
            _e2b1_fixture_splice_once(
                _E2B1_COMMIT_BODY_A,
                b'"verification":{"verified":false,"reason":"unsigned","signature":null,"payload":null,"verified_at":null}',
                b'"verification":{"verified":null,"signature":null,"payload":null,"verified_at":null}',
            ),
            _e2b1_fixture_splice_once(
                _E2B1_COMMIT_BODY_A,
                b'"reason":"unsigned"',
                b'"reason":"identity_leak_canary"',
            ),
            _e2b1_fixture_splice_once(
                _E2B1_COMMIT_BODY_A,
                b'"signature":null',
                b'"signature":7',
            ),
            _e2b1_fixture_splice_once(
                _E2B1_COMMIT_BODY_A,
                b'"payload":null',
                b'"payload":false',
            ),
            _e2b1_fixture_splice_once(
                _E2B1_COMMIT_BODY_A,
                b'"verified_at":null',
                b'"verified_at":7',
            ),
            _e2b1_fixture_splice_once(
                enriched_commit,
                b'"sha":"dddddddddddddddddddddddddddddddddddddddd","html_url"',
                b'"html_url"',
            ),
            _e2b1_fixture_splice_once(
                enriched_commit,
                b'"html_url":"https://example.invalid/parent-view"',
                b'"html_url":null',
            ),
        )
        for body in invalid_commit_schema:
            self._assert_controlled_rejection(
                body,
                mode="commit",
                leak_canaries=("identity_leak_canary", "synthetic@example.invalid"),
            )

        invalid_tree_schema = (
            _e2b1_fixture_splice_once(
                _E2B1_TREE_BODY_A,
                b'"truncated":false',
                b'"truncated":null',
            ),
            _e2b1_fixture_splice_once(
                _E2B1_TREE_BODY_A,
                b'"url":"https://example.invalid/git/trees/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"',
                b'"url":null',
            ),
            _e2b1_fixture_splice_once(
                _E2B1_TREE_BODY_A,
                b'"path":"sql/synthetic_auth_probe.cc",',
                b"",
            ),
            _e2b1_fixture_splice_once(
                _E2B1_TREE_BODY_A,
                b'"type":"blob","sha":"1111111111111111111111111111111111111111"',
                b'"type":null,"sha":"1111111111111111111111111111111111111111"',
            ),
            _e2b1_fixture_splice_once(
                _E2B1_TREE_BODY_A,
                b'"mode":"100644","type":"blob","sha":"1111111111111111111111111111111111111111"',
                b'"mode":7,"type":"blob","sha":"1111111111111111111111111111111111111111"',
            ),
        )
        for body in invalid_tree_schema:
            self._assert_controlled_rejection(body)

    def test_e2b1_06_identity_and_invocation_boundaries(self) -> None:
        alternate_root_body = _e2b1_fixture_splice_once(
            _E2B1_COMMIT_BODY_A,
            b'"tree":{"url":"https://example.invalid/tree","sha":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}',
            b'"tree":{"url":"https://example.invalid/tree","sha":"dddddddddddddddddddddddddddddddddddddddd"}',
        )
        self.assertEqual(
            {
                "mode": "commit",
                "commit_sha": _E2B1_EXPECTED_COMMIT_SHA,
                "root_tree_sha": "dddddddddddddddddddddddddddddddddddddddd",
                "projection_bytes": b'{"commit_sha":"197f92bee02d8e836f529f37625be69b83e7acbd","root_tree_sha":"dddddddddddddddddddddddddddddddddddddddd"}',
                "projection_sha256": "6db9c3688507676b3f480492c65c24b900548b66718e854ea93f90879c2cf236",
            },
            self._parse_commit(alternate_root_body),
        )
        commit_identity_bodies = (
            _e2b1_fixture_splice_once(
                _E2B1_COMMIT_BODY_A,
                b'"sha":"197f92bee02d8e836f529f37625be69b83e7acbd"',
                b'"sha":"dddddddddddddddddddddddddddddddddddddddd"',
            ),
            _e2b1_fixture_splice_once(
                _E2B1_COMMIT_BODY_A,
                b'"sha":"197f92bee02d8e836f529f37625be69b83e7acbd"',
                b'"sha":"197F92BEE02D8E836F529F37625BE69B83E7ACBD"',
            ),
            _e2b1_fixture_splice_once(
                _E2B1_COMMIT_BODY_A,
                b'"sha":"197f92bee02d8e836f529f37625be69b83e7acbd"',
                b'"sha":"197f92bee02d8e836f529f37625be69b83e7acb"',
            ),
            _e2b1_fixture_splice_once(
                _E2B1_COMMIT_BODY_A,
                b'"tree":{"url":"https://example.invalid/tree","sha":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}',
                b'"tree":{"url":"https://example.invalid/tree","sha":"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"}',
            ),
        )
        for body in commit_identity_bodies:
            self._assert_controlled_rejection(
                body,
                mode="commit",
                leak_canaries=("dddddddddddddddddddddddddddddddddddddddd",),
            )

        tree_identity_bodies = (
            _e2b1_fixture_splice_once(
                _E2B1_TREE_BODY_A,
                b'{"sha":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","url"',
                b'{"sha":"dddddddddddddddddddddddddddddddddddddddd","url"',
            ),
            _e2b1_fixture_splice_once(
                _E2B1_TREE_BODY_A,
                b'{"sha":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","url"',
                b'{"sha":"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA","url"',
            ),
            _e2b1_fixture_splice_once(
                _E2B1_TREE_BODY_A,
                b'"sha":"1111111111111111111111111111111111111111","url":"https://example.invalid/git/objects/1111111111111111111111111111111111111111"',
                b'"sha":"IDENTITY_LEAK_CANARY","url":"https://example.invalid/git/objects/1111111111111111111111111111111111111111"',
            ),
            _e2b1_fixture_splice_once(
                _E2B1_TREE_BODY_A,
                b'"sha":"1111111111111111111111111111111111111111","url":"https://example.invalid/git/objects/1111111111111111111111111111111111111111"',
                b'"sha":"111111111111111111111111111111111111111A","url":"https://example.invalid/git/objects/1111111111111111111111111111111111111111"',
            ),
        )
        for body in tree_identity_bodies:
            self._assert_controlled_rejection(
                body,
                leak_canaries=("IDENTITY_LEAK_CANARY",),
            )

        parent_body = _e2b1_fixture_splice_once(
            _E2B1_COMMIT_BODY_A,
            b'"parents":[]',
            b'"parents":[{"url":"https://example.invalid/parent","sha":"dddddddddddddddddddddddddddddddddddddddd","html_url":"https://example.invalid/parent-view"}]',
        )
        self.assertEqual(self._parse_commit(_E2B1_COMMIT_BODY_A), self._parse_commit(parent_body))
        invalid_parent_sha = _e2b1_fixture_splice_once(
            parent_body,
            b'"sha":"dddddddddddddddddddddddddddddddddddddddd"',
            b'"sha":"parent_identity_leak_canary"',
        )
        self._assert_controlled_rejection(
            invalid_parent_sha,
            mode="commit",
            leak_canaries=("parent_identity_leak_canary",),
        )

        for invalid_mode in ("Commit", "", 7):
            self._assert_internal_failure(
                mode=invalid_mode,
                body=_E2B1_COMMIT_BODY_A,
                expected_commit_sha=_E2B1_EXPECTED_COMMIT_SHA,
                leak_canaries=(str(invalid_mode),),
            )
        self._assert_internal_failure(
            mode="commit",
            body=_E2B1_COMMIT_BODY_A.decode("ascii"),
            expected_commit_sha=_E2B1_EXPECTED_COMMIT_SHA,
        )
        self._assert_internal_failure(
            mode="commit",
            body=_E2B1_COMMIT_BODY_A,
            expected_commit_sha=7,
        )
        self._assert_internal_failure(
            mode="commit",
            body=_E2B1_COMMIT_BODY_A,
            expected_commit_sha="CONFIG_IDENTITY_LEAK_CANARY",
            leak_canaries=("CONFIG_IDENTITY_LEAK_CANARY",),
        )
        self._assert_internal_failure(
            mode="commit",
            body=_E2B1_COMMIT_BODY_A,
            expected_commit_sha=_E2B1_EXPECTED_COMMIT_SHA,
            expected_root_tree_sha=_E2B1_EXPECTED_ROOT_TREE_SHA,
        )
        self._assert_internal_failure(
            mode="tree",
            body=_E2B1_TREE_BODY_A,
            expected_commit_sha=_E2B1_EXPECTED_COMMIT_SHA,
        )
        self._assert_internal_failure(
            mode="tree",
            body=_E2B1_TREE_BODY_A,
            expected_commit_sha=_E2B1_EXPECTED_COMMIT_SHA,
            expected_root_tree_sha="ROOT_CONFIG_LEAK_CANARY",
            leak_canaries=("ROOT_CONFIG_LEAK_CANARY",),
        )

    def test_e2b1_07_https_and_rfc3339_boundaries(self) -> None:
        canonical_commit = self._parse_commit(_E2B1_COMMIT_BODY_A)
        commit_url_marker = b'"url":"https://example.invalid/commit"'
        for valid_url in (
            b"https://example.invalid:0/commit",
            b"https://example.invalid:65535/commit",
            b"https://[2001:db8::1]/commit",
            b"https://example.invalid/%7Esynthetic",
        ):
            body = _e2b1_fixture_splice_once(
                _E2B1_COMMIT_BODY_A,
                commit_url_marker,
                b'"url":"' + valid_url + b'"',
            )
            self.assertEqual(canonical_commit, self._parse_commit(body))

        invalid_urls = (
            b"",
            b"http://example.invalid/identity_leak_canary",
            b"/relative/identity_leak_canary",
            b"https://user:secret@example.invalid/identity_leak_canary",
            b"https://example.invalid:",
            b"https://example.invalid:65536/identity_leak_canary",
            b"https://example.invalid:%31/identity_leak_canary",
            b"https://example.invalid/%ZZ/identity_leak_canary",
            b"https://example.invalid\\\\identity_leak_canary",
            b"https://example.invalid/\\u0001identity_leak_canary",
            b"https://example.invalid/\x7fidentity_leak_canary",
            b"https://[2001:db8::1/identity_leak_canary",
        )
        for invalid_url in invalid_urls:
            body = _e2b1_fixture_splice_once(
                _E2B1_COMMIT_BODY_A,
                commit_url_marker,
                b'"url":"' + invalid_url + b'"',
            )
            self._assert_controlled_rejection(
                body,
                mode="commit",
                leak_canaries=("identity_leak_canary", "user", "secret"),
            )

        parent_body = _e2b1_fixture_splice_once(
            _E2B1_COMMIT_BODY_A,
            b'"parents":[]',
            b'"parents":[{"url":"https://example.invalid/parent","sha":"dddddddddddddddddddddddddddddddddddddddd","html_url":"https://example.invalid/parent-view"}]',
        )
        distributed_url_failures = (
            _e2b1_fixture_splice_once(
                _E2B1_COMMIT_BODY_A,
                b'"html_url":"https://example.invalid/commit-view"',
                b'"html_url":"ftp://example.invalid/html_identity_canary"',
            ),
            _e2b1_fixture_splice_once(
                _E2B1_COMMIT_BODY_A,
                b'"url":"https://example.invalid/tree"',
                b'"url":"https://user:secret@example.invalid/tree_identity_canary"',
            ),
            _e2b1_fixture_splice_once(
                parent_body,
                b'"url":"https://example.invalid/parent"',
                b'"url":"relative_parent_identity_canary"',
            ),
            _e2b1_fixture_splice_once(
                parent_body,
                b'"html_url":"https://example.invalid/parent-view"',
                b'"html_url":"http://example.invalid/parent_html_identity_canary"',
            ),
        )
        for body in distributed_url_failures:
            self._assert_controlled_rejection(
                body,
                mode="commit",
                leak_canaries=("identity_canary", "secret"),
            )
        self._assert_controlled_rejection(
            _e2b1_fixture_splice_once(
                _E2B1_TREE_BODY_A,
                b'"url":"https://example.invalid/git/trees/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"',
                b'"url":"http://example.invalid/tree_top_identity_canary"',
            ),
            leak_canaries=("tree_top_identity_canary",),
        )
        self._assert_controlled_rejection(
            _e2b1_fixture_splice_once(
                _E2B1_TREE_BODY_A,
                b'"url":"https://example.invalid/git/objects/1111111111111111111111111111111111111111"',
                b'"url":"https://user:secret@example.invalid/entry_identity_canary"',
            ),
            leak_canaries=("entry_identity_canary", "secret"),
        )

        author_date_marker = b'"author":{"date":"2026-01-01T00:00:00Z"'
        valid_dates = (
            b"2026-01-01T00:00:00Z",
            b"2026-01-01t00:00:00z",
            b"2026-01-01T00:00:00.123456Z",
            b"2026-01-01T05:30:00+05:30",
            b"2026-01-01T04:00:00-04:00",
            b"2024-02-29T12:34:56Z",
            b"2026-06-30T23:59:60Z",
            b"2026-12-31T23:59:60Z",
            b"2026-07-01T05:29:60+05:30",
        )
        for valid_date in valid_dates:
            body = _e2b1_fixture_splice_once(
                _E2B1_COMMIT_BODY_A,
                author_date_marker,
                b'"author":{"date":"' + valid_date + b'"',
            )
            self.assertEqual(canonical_commit, self._parse_commit(body))

        verified_at_body = _e2b1_fixture_splice_once(
            _E2B1_COMMIT_BODY_A,
            b'"verified_at":null',
            b'"verified_at":"2026-12-31T23:59:60Z"',
        )
        self.assertEqual(canonical_commit, self._parse_commit(verified_at_body))
        invalid_dates = (
            b"",
            b"2026-01-01T00:00:00.Z",
            b"2026-01-01T00:00:00,1Z",
            b"2026-01-01T00:00:00",
            b"2026-01-01 00:00:00Z",
            b"2026-01-01t00:00:00x",
            b"0000-01-01T00:00:00Z",
            b"2026-13-01T00:00:00Z",
            b"2026-02-30T00:00:00Z",
            b"2023-02-29T00:00:00Z",
            b"2026-01-01T24:00:00Z",
            b"2026-01-01T00:60:00Z",
            b"2026-01-01T00:00:61Z",
            b"2026-01-01T00:00:00+24:00",
            b"2026-01-01T00:00:00+00:60",
            b"2026-01-01T00:00:60Z",
        )
        for invalid_date in invalid_dates:
            body = _e2b1_fixture_splice_once(
                _E2B1_COMMIT_BODY_A,
                author_date_marker,
                b'"author":{"date":"' + invalid_date + b'"',
            )
            self._assert_controlled_rejection(
                body,
                mode="commit",
                leak_canaries=("2026-01-01",),
            )

    def test_e2b1_08_tree_modes_sizes_paths_and_late_failure(self) -> None:
        pair_marker = b'"mode":"100644","type":"blob"'
        valid_pairs = (
            b'"mode":"100644","type":"blob"',
            b'"mode":"100755","type":"blob"',
            b'"mode":"120000","type":"blob"',
            b'"mode":"040000","type":"tree"',
            b'"mode":"160000","type":"commit"',
        )
        for pair in valid_pairs:
            entry = _e2b1_fixture_splice_once(
                _E2B1_NEUTRAL_TREE_ENTRY,
                pair_marker,
                pair,
            )
            result = self._parse_tree(
                _e2b1_fixture_insert_tree_entries(_E2B1_TREE_BODY_A, (entry,))
            )
            self.assertEqual(9, len(result["entries"]))
            self.assertEqual(_E2B1_EXPECTED_TREE_CANDIDATES, result["candidates"])

        invalid_pairs = (
            b'"mode":"100644","type":"tree"',
            b'"mode":"100644","type":"commit"',
            b'"mode":"100755","type":"tree"',
            b'"mode":"100755","type":"commit"',
            b'"mode":"120000","type":"tree"',
            b'"mode":"120000","type":"commit"',
            b'"mode":"040000","type":"blob"',
            b'"mode":"040000","type":"commit"',
            b'"mode":"160000","type":"blob"',
            b'"mode":"160000","type":"tree"',
            b'"mode":"999999","type":"blob"',
            b'"mode":"100644","type":"unknown_identity_canary"',
        )
        for pair in invalid_pairs:
            entry = _e2b1_fixture_splice_once(
                _E2B1_NEUTRAL_TREE_ENTRY,
                pair_marker,
                pair,
            )
            self._assert_controlled_rejection(
                _e2b1_fixture_insert_tree_entries(_E2B1_TREE_BODY_A, (entry,)),
                leak_canaries=("unknown_identity_canary",),
            )

        for size_literal in (b"0", b"7"):
            sized_entry = _e2b1_fixture_splice_once(
                _E2B1_NEUTRAL_TREE_ENTRY,
                b',"sha":"9999999999999999999999999999999999999999"',
                b',"size":' + size_literal + b',"sha":"9999999999999999999999999999999999999999"',
            )
            result = self._parse_tree(
                _e2b1_fixture_insert_tree_entries(
                    _E2B1_TREE_BODY_A,
                    (sized_entry,),
                )
            )
            self.assertEqual(9, len(result["entries"]))

        invalid_size_entries = tuple(
            _e2b1_fixture_splice_once(
                _E2B1_NEUTRAL_TREE_ENTRY,
                b',"sha":"9999999999999999999999999999999999999999"',
                b',"size":' + size_literal + b',"sha":"9999999999999999999999999999999999999999"',
            )
            for size_literal in (b"-1", b"1.5", b"true", b"null")
        ) + (
            _e2b1_fixture_splice_once(
                _e2b1_fixture_splice_once(
                    _E2B1_NEUTRAL_TREE_ENTRY,
                    pair_marker,
                    b'"mode":"040000","type":"tree"',
                ),
                b',"sha":"9999999999999999999999999999999999999999"',
                b',"size":0,"sha":"9999999999999999999999999999999999999999"',
            ),
        )
        for entry in invalid_size_entries:
            self._assert_controlled_rejection(
                _e2b1_fixture_insert_tree_entries(_E2B1_TREE_BODY_A, (entry,))
            )

        valid_symbol_path = _e2b1_fixture_splice_once(
            _E2B1_NEUTRAL_TREE_ENTRY,
            b"docs/synthetic_neutral_probe.cc",
            b"docs/A._+@%=-/b.cc",
        )
        self.assertEqual(
            9,
            len(
                self._parse_tree(
                    _e2b1_fixture_insert_tree_entries(
                        _E2B1_TREE_BODY_A,
                        (valid_symbol_path,),
                    )
                )["entries"]
            ),
        )
        invalid_paths = (
            b"",
            b"docs/synthetic_\xc3\xa9_probe.cc",
            b"docs/synthetic neutral_probe.cc",
            b"docs\\synthetic_neutral_probe.cc",
            b"docs/\x01synthetic_neutral_probe.cc",
            b"/docs/synthetic_neutral_probe.cc",
            b"docs/synthetic_neutral_probe.cc/",
            b"docs//synthetic_neutral_probe.cc",
            b"docs/./synthetic_neutral_probe.cc",
            b"docs/../synthetic_neutral_probe.cc",
        )
        for invalid_path in invalid_paths:
            entry = _e2b1_fixture_splice_once(
                _E2B1_NEUTRAL_TREE_ENTRY,
                b"docs/synthetic_neutral_probe.cc",
                invalid_path,
            )
            self._assert_controlled_rejection(
                _e2b1_fixture_insert_tree_entries(_E2B1_TREE_BODY_A, (entry,))
            )

        duplicate_entry = _E2B1_TREE_B_ENTRY_FRAGMENTS[0]
        conflicting_entry = _e2b1_fixture_splice_once(
            duplicate_entry,
            b'"sha":"1111111111111111111111111111111111111111"',
            b'"sha":"9999999999999999999999999999999999999999"',
        )
        case_collision_entry = _e2b1_fixture_splice_once(
            conflicting_entry,
            b"sql/synthetic_auth_probe.cc",
            b"SQL/SYNTHETIC_AUTH_PROBE.CC",
        )
        for entry in (duplicate_entry, conflicting_entry, case_collision_entry):
            self._assert_controlled_rejection(
                _e2b1_fixture_insert_tree_entries(_E2B1_TREE_BODY_A, (entry,)),
                leak_canaries=("SQL/SYNTHETIC_AUTH_PROBE.CC",),
            )

        late_invalid_entry = _e2b1_fixture_splice_once(
            _E2B1_NEUTRAL_TREE_ENTRY,
            b"docs/synthetic_neutral_probe.cc",
            b"late invalid identity canary",
        )
        self._assert_controlled_rejection(
            _e2b1_fixture_insert_tree_entries(
                _E2B1_TREE_BODY_A,
                (_E2B1_NEUTRAL_TREE_ENTRY, late_invalid_entry),
            ),
            leak_canaries=("late invalid identity canary",),
        )
        self._assert_controlled_rejection(
            _e2b1_fixture_splice_once(
                _E2B1_TREE_BODY_A,
                b'"truncated":false',
                b'"truncated":true',
            )
        )

    def test_e2b1_09_classification_rejections_and_hashing(self) -> None:
        results = tuple(
            self._parse_tree(
                _e2b1_fixture_insert_tree_entries(
                    _E2B1_TREE_BODY_A,
                    entries,
                )
            )
            for entries in (
                _E2B1_REJECTED_ENTRY_FRAGMENTS,
                tuple(reversed(_E2B1_REJECTED_ENTRY_FRAGMENTS)),
            )
        )
        self.assertEqual(results[0], results[1])
        self.assertEqual((1, 1, 1), results[0]["rejection_counts"])
        self.assertEqual(
            _E2B1_EXPECTED_REJECTED_TUPLE_SHA256,
            results[0]["rejected_tuple_sha256"],
        )
        self.assertEqual(_E2B1_EXPECTED_TREE_CANDIDATES, results[0]["candidates"])
        self.assertEqual(11, len(results[0]["entries"]))

        q4_candidate = tuple(
            candidate
            for candidate in results[0]["candidates"]
            if candidate[0] == "sql/synthetic_sql_kill_probe.cc"
        )
        self.assertEqual(
            (
                (
                    "sql/synthetic_sql_kill_probe.cc",
                    "100644",
                    "blob",
                    "4444444444444444444444444444444444444444",
                    ("Q4_EXACT_CONNECTION_TERMINATION",),
                ),
            ),
            q4_candidate,
        )
        multiple_q4_tokens = _e2b1_fixture_splice_once(
            _E2B1_TREE_BODY_A,
            b"sql/synthetic_sql_kill_probe.cc",
            b"sql/synthetic_kill_connection_probe.cc",
        )
        multiple_q4_result = self._parse_tree(multiple_q4_tokens)
        self.assertIn(
            (
                "sql/synthetic_kill_connection_probe.cc",
                "100644",
                "blob",
                "4444444444444444444444444444444444444444",
                ("Q4_EXACT_CONNECTION_TERMINATION",),
            ),
            multiple_q4_result["candidates"],
        )

        no_candidate_body = b'{"sha":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","url":"https://example.invalid/tree","tree":[],"truncated":false}'
        self._assert_controlled_rejection(no_candidate_body)

    def test_e2b1_10_controlled_and_internal_fail_closed_behavior(self) -> None:
        self._assert_controlled_rejection(
            _e2b1_fixture_splice_once(
                _E2B1_TREE_BODY_A,
                b'"path":"sql/synthetic_auth_probe.cc"',
                b'"path":"sql/late_identity_leak_canary auth.cc"',
            ),
            leak_canaries=("late_identity_leak_canary",),
        )
        self._assert_internal_failure(
            mode="unexpected_internal_mode_canary",
            body=_E2B1_TREE_BODY_A,
            expected_commit_sha=_E2B1_EXPECTED_COMMIT_SHA,
            expected_root_tree_sha=_E2B1_EXPECTED_ROOT_TREE_SHA,
            leak_canaries=("unexpected_internal_mode_canary",),
        )
        self.assertEqual(
            "8b7353752be6f67899ae65c128567afd0571324ea06c23fa74e7fc7dec879021",
            _E2B1_EXPECTED_REJECTED_TUPLE_SHA256,
        )
