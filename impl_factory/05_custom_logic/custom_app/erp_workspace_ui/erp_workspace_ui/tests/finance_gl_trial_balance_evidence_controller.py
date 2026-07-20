"""Private GL/TB evidence-controller parsing boundaries.

This source-authoring gate intentionally contains only the pure E2-B1 response
parser.  Acquisition, orchestration, process exits, and evidence promotion are
owned by later gates.
"""

import datetime
import hashlib
import json
import re
import urllib.parse


_E2B1_SHA_PATTERN = r"[0-9a-f]{40}"
_E2B1_PATH_PATTERN = r"[A-Za-z0-9._+@%=-]+(?:/[A-Za-z0-9._+@%=-]+)*"
_E2B1_RFC3339_PATTERN = (
    r"([0-9]{4})-([0-9]{2})-([0-9]{2})"
    r"[Tt]([0-9]{2}):([0-9]{2}):([0-9]{2})"
    r"(?:\.([0-9]+))?([Zz]|[+-][0-9]{2}:[0-9]{2})"
)

_E2B1_COMMIT_MEMBERS = (
    "sha",
    "node_id",
    "url",
    "html_url",
    "author",
    "committer",
    "message",
    "tree",
    "parents",
    "verification",
)
_E2B1_PERSON_MEMBERS = ("date", "name", "email")
_E2B1_TREE_REFERENCE_MEMBERS = ("url", "sha")
_E2B1_PARENT_MEMBERS = ("url", "sha", "html_url")
_E2B1_VERIFICATION_MEMBERS = (
    "verified",
    "reason",
    "signature",
    "payload",
    "verified_at",
)
_E2B1_TREE_MEMBERS = ("sha", "url", "tree", "truncated")
_E2B1_TREE_ENTRY_MEMBERS = ("path", "mode", "type", "sha", "url")

_E2B1_VERIFICATION_REASONS = frozenset(
    (
        "expired_key",
        "not_signing_key",
        "gpgverify_error",
        "gpgverify_unavailable",
        "unsigned",
        "unknown_signature_type",
        "no_user",
        "unverified_email",
        "bad_email",
        "unknown_key",
        "malformed_signature",
        "invalid",
        "valid",
    )
)
_E2B1_MODE_TYPE_PAIRS = frozenset(
    (
        ("100644", "blob"),
        ("100755", "blob"),
        ("120000", "blob"),
        ("040000", "tree"),
        ("160000", "commit"),
    )
)
_E2B1_REGULAR_BLOB_PAIRS = frozenset(
    (
        ("100644", "blob"),
        ("100755", "blob"),
    )
)
_E2B1_CANDIDATE_PREFIXES = (
    "sql/",
    "include/",
    "storage/innobase/",
    "storage/perfschema/",
)
_E2B1_CANDIDATE_SUFFIXES = (
    ".c",
    ".cc",
    ".cpp",
    ".h",
    ".hh",
    ".hpp",
    ".ic",
    ".l",
    ".y",
    ".yy",
    ".sql",
)
_E2B1_CATEGORIES = (
    ("Q1_ACCOUNT_HOST_MATCH", ("sql_acl", "acl", "auth", "privilege", "grant")),
    ("Q2_TABLE_COLUMN_GRANT", ("column_priv", "table_priv", "grant", "privilege")),
    ("Q3_PROCESS_VISIBILITY", ("processlist",)),
    ("Q4_EXACT_CONNECTION_TERMINATION", ("sql_kill", "kill", "connection")),
    ("Q5_INNODB_TRX_VISIBILITY", ("innodb_trx", "trx0trx")),
    (
        "Q6_ISOLATION_READ_ONLY_SNAPSHOT",
        ("isolation", "consistent_snapshot", "read_only"),
    ),
    (
        "Q7_REPLICA_TOPOLOGY_PRIVILEGE",
        ("replica", "replication", "slave", "master_info"),
    ),
    ("Q8_STATEMENT_TIMEOUT", ("max_statement_time", "statement_timeout")),
)
_E2B1_REJECTION_REASONS = (
    "prefix_rejected",
    "suffix_rejected",
    "nonregular_blob_rejected",
)


class _E2B1ParseRejected(Exception):
    """Controlled body, schema, or identity rejection with no untrusted message."""


class _E2B1ParserInternal(Exception):
    """Controller/configuration or parser-invariant failure with no untrusted message."""


def _e2b1_reject() -> None:
    raise _E2B1ParseRejected()


def _e2b1_internal() -> None:
    raise _E2B1ParserInternal()


def _e2b1_unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            _e2b1_reject()
        result[key] = value
    return result


def _e2b1_reject_constant(_value: str) -> object:
    _e2b1_reject()


def _e2b1_parse_float(value: str) -> float:
    parsed = float(value)
    if parsed != parsed or parsed == float("inf") or parsed == float("-inf"):
        _e2b1_reject()
    return parsed


def _e2b1_contains_surrogate(value: str) -> bool:
    return any(0xD800 <= ord(character) <= 0xDFFF for character in value)


def _e2b1_validate_complete_json(value: object) -> None:
    pending = [value]
    while pending:
        current = pending.pop()
        if type(current) is str:
            if _e2b1_contains_surrogate(current):
                _e2b1_reject()
        elif type(current) is dict:
            for key, nested in current.items():
                if type(key) is not str:
                    _e2b1_internal()
                if _e2b1_contains_surrogate(key):
                    _e2b1_reject()
                pending.append(nested)
        elif type(current) is list:
            pending.extend(current)
        elif current is None or type(current) in (bool, int, float):
            continue
        else:
            _e2b1_internal()


def _e2b1_decode_json_object(body: bytes) -> dict[str, object]:
    try:
        text = body.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        raise _E2B1ParseRejected() from None
    if text.startswith("\ufeff"):
        _e2b1_reject()
    try:
        value = json.loads(
            text,
            object_pairs_hook=_e2b1_unique_object,
            parse_constant=_e2b1_reject_constant,
            parse_float=_e2b1_parse_float,
        )
    except _E2B1ParseRejected:
        raise
    except (json.JSONDecodeError, RecursionError, ValueError):
        raise _E2B1ParseRejected() from None
    _e2b1_validate_complete_json(value)
    if type(value) is not dict:
        _e2b1_reject()
    return value


def _e2b1_require_members(
    value: object,
    members: tuple[str, ...],
) -> dict[str, object]:
    if type(value) is not dict:
        _e2b1_reject()
    for member in members:
        if member not in value:
            _e2b1_reject()
    return value


def _e2b1_require_string(value: dict[str, object], member: str) -> str:
    result = value[member]
    if type(result) is not str:
        _e2b1_reject()
    return result


def _e2b1_require_boolean(value: dict[str, object], member: str) -> bool:
    result = value[member]
    if type(result) is not bool:
        _e2b1_reject()
    return result


def _e2b1_require_array(value: dict[str, object], member: str) -> list[object]:
    result = value[member]
    if type(result) is not list:
        _e2b1_reject()
    return result


def _e2b1_validate_sha(value: str) -> None:
    if re.fullmatch(_E2B1_SHA_PATTERN, value) is None:
        _e2b1_reject()


def _e2b1_validate_https_url(value: str) -> None:
    if (
        not value
        or "\\" in value
        or any(ord(character) <= 0x20 or ord(character) == 0x7F for character in value)
        or re.search(r"%(?![0-9A-Fa-f]{2})", value) is not None
    ):
        _e2b1_reject()
    try:
        parsed = urllib.parse.urlsplit(value)
        port = parsed.port
    except ValueError:
        raise _E2B1ParseRejected() from None
    if (
        parsed.scheme != "https"
        or not parsed.netloc
        or parsed.hostname is None
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.netloc.endswith(":")
    ):
        _e2b1_reject()
    if port is not None and not 0 <= port <= 65535:
        _e2b1_reject()


def _e2b1_validate_rfc3339(value: str) -> None:
    match = re.fullmatch(_E2B1_RFC3339_PATTERN, value)
    if match is None:
        _e2b1_reject()
    year, month, day, hour, minute, second = (
        int(match.group(index)) for index in range(1, 7)
    )
    zone = match.group(8)
    if hour > 23 or minute > 59 or second > 60:
        _e2b1_reject()
    if zone in ("Z", "z"):
        offset = datetime.timedelta(0)
    else:
        offset_hour = int(zone[1:3])
        offset_minute = int(zone[4:6])
        if offset_hour > 23 or offset_minute > 59:
            _e2b1_reject()
        offset = datetime.timedelta(hours=offset_hour, minutes=offset_minute)
        if zone[0] == "-":
            offset = -offset
    try:
        timezone = datetime.timezone(offset)
        moment = datetime.datetime(
            year,
            month,
            day,
            hour,
            minute,
            min(second, 59),
            tzinfo=timezone,
        )
    except ValueError:
        raise _E2B1ParseRejected() from None
    if second == 60:
        try:
            utc_moment = moment.astimezone(datetime.timezone.utc)
        except (OverflowError, ValueError):
            raise _E2B1ParseRejected() from None
        is_leap_boundary = (
            (utc_moment.month == 6 and utc_moment.day == 30)
            or (utc_moment.month == 12 and utc_moment.day == 31)
        ) and utc_moment.hour == 23 and utc_moment.minute == 59
        if not is_leap_boundary:
            _e2b1_reject()


def _e2b1_canonical_bytes(value: object) -> bytes:
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        ).encode("utf-8", errors="strict")
    except (TypeError, UnicodeEncodeError, ValueError):
        raise _E2B1ParserInternal() from None
    if encoded.startswith(b"\xef\xbb\xbf") or b"\n" in encoded or b"\r" in encoded:
        _e2b1_internal()
    return encoded


def _e2b1_validate_person(value: object) -> None:
    person = _e2b1_require_members(value, _E2B1_PERSON_MEMBERS)
    _e2b1_validate_rfc3339(_e2b1_require_string(person, "date"))
    _e2b1_require_string(person, "name")
    _e2b1_require_string(person, "email")


def _e2b1_validate_commit(
    document: dict[str, object],
    expected_commit_sha: str,
) -> dict[str, object]:
    commit = _e2b1_require_members(document, _E2B1_COMMIT_MEMBERS)
    commit_sha = _e2b1_require_string(commit, "sha")
    _e2b1_validate_sha(commit_sha)
    if commit_sha != expected_commit_sha:
        _e2b1_reject()

    _e2b1_require_string(commit, "node_id")
    _e2b1_validate_https_url(_e2b1_require_string(commit, "url"))
    _e2b1_validate_https_url(_e2b1_require_string(commit, "html_url"))
    _e2b1_validate_person(commit["author"])
    _e2b1_validate_person(commit["committer"])
    _e2b1_require_string(commit, "message")

    tree = _e2b1_require_members(commit["tree"], _E2B1_TREE_REFERENCE_MEMBERS)
    _e2b1_validate_https_url(_e2b1_require_string(tree, "url"))
    root_tree_sha = _e2b1_require_string(tree, "sha")
    _e2b1_validate_sha(root_tree_sha)

    parents = _e2b1_require_array(commit, "parents")
    for parent_value in parents:
        parent = _e2b1_require_members(parent_value, _E2B1_PARENT_MEMBERS)
        _e2b1_validate_https_url(_e2b1_require_string(parent, "url"))
        parent_sha = _e2b1_require_string(parent, "sha")
        _e2b1_validate_sha(parent_sha)
        _e2b1_validate_https_url(_e2b1_require_string(parent, "html_url"))

    verification = _e2b1_require_members(
        commit["verification"],
        _E2B1_VERIFICATION_MEMBERS,
    )
    _e2b1_require_boolean(verification, "verified")
    reason = _e2b1_require_string(verification, "reason")
    if reason not in _E2B1_VERIFICATION_REASONS:
        _e2b1_reject()
    for nullable_member in ("signature", "payload"):
        nullable_value = verification[nullable_member]
        if nullable_value is not None and type(nullable_value) is not str:
            _e2b1_reject()
    verified_at = verification["verified_at"]
    if verified_at is not None:
        if type(verified_at) is not str:
            _e2b1_reject()
        _e2b1_validate_rfc3339(verified_at)

    projection_bytes = _e2b1_canonical_bytes(
        {
            "commit_sha": commit_sha,
            "root_tree_sha": root_tree_sha,
        }
    )
    return {
        "mode": "commit",
        "commit_sha": commit_sha,
        "root_tree_sha": root_tree_sha,
        "projection_bytes": projection_bytes,
        "projection_sha256": hashlib.sha256(projection_bytes).hexdigest(),
    }


def _e2b1_validate_tree_entry(value: object) -> tuple[str, str, str, str]:
    entry = _e2b1_require_members(value, _E2B1_TREE_ENTRY_MEMBERS)
    path = _e2b1_require_string(entry, "path")
    if re.fullmatch(_E2B1_PATH_PATTERN, path) is None:
        _e2b1_reject()
    if any(segment in (".", "..") for segment in path.split("/")):
        _e2b1_reject()

    mode = _e2b1_require_string(entry, "mode")
    object_type = _e2b1_require_string(entry, "type")
    if (mode, object_type) not in _E2B1_MODE_TYPE_PAIRS:
        _e2b1_reject()

    object_sha = _e2b1_require_string(entry, "sha")
    _e2b1_validate_sha(object_sha)
    _e2b1_validate_https_url(_e2b1_require_string(entry, "url"))

    if "size" in entry:
        size = entry["size"]
        if object_type != "blob" or type(size) is not int or size < 0:
            _e2b1_reject()
    return path, mode, object_type, object_sha


def _e2b1_entry_sort_key(
    entry: tuple[str, str, str, str],
) -> tuple[bytes, bytes, bytes, bytes]:
    return tuple(part.encode("utf-8") for part in entry)


def _e2b1_matching_categories(path: str) -> tuple[str, ...]:
    lowered_path = path.lower()
    return tuple(
        category
        for category, tokens in _E2B1_CATEGORIES
        if any(token in lowered_path for token in tokens)
    )


def _e2b1_rejected_sort_key(
    entry: tuple[str, str, str, str, str],
) -> tuple[int, bytes, bytes, bytes, bytes]:
    reason, path, mode, object_type, object_sha = entry
    try:
        reason_index = _E2B1_REJECTION_REASONS.index(reason)
    except ValueError:
        raise _E2B1ParserInternal() from None
    return (
        reason_index,
        path.encode("utf-8"),
        mode.encode("utf-8"),
        object_type.encode("utf-8"),
        object_sha.encode("utf-8"),
    )


def _e2b1_classify_candidates(
    entries: tuple[tuple[str, str, str, str], ...],
) -> tuple[
    tuple[tuple[str, str, str, str, tuple[str, ...]], ...],
    tuple[int, int, int],
    str,
]:
    candidates: list[tuple[str, str, str, str, tuple[str, ...]]] = []
    rejection_counts = [0, 0, 0]
    rejected_entries: list[tuple[str, str, str, str, str]] = []
    covered_categories: set[str] = set()

    for path, mode, object_type, object_sha in entries:
        categories = _e2b1_matching_categories(path)
        if not categories:
            continue
        if len(categories) > 1:
            _e2b1_reject()
        if not path.startswith(_E2B1_CANDIDATE_PREFIXES):
            reason_index = 0
        elif not path.endswith(_E2B1_CANDIDATE_SUFFIXES):
            reason_index = 1
        elif (mode, object_type) not in _E2B1_REGULAR_BLOB_PAIRS:
            reason_index = 2
        else:
            candidates.append((path, mode, object_type, object_sha, categories))
            covered_categories.update(categories)
            continue
        rejection_counts[reason_index] += 1
        rejected_entries.append(
            (
                _E2B1_REJECTION_REASONS[reason_index],
                path,
                mode,
                object_type,
                object_sha,
            )
        )

    required_categories = frozenset(category for category, _tokens in _E2B1_CATEGORIES)
    if covered_categories != required_categories:
        _e2b1_reject()

    rejected_entries.sort(key=_e2b1_rejected_sort_key)
    rejected_projection = [list(entry) for entry in rejected_entries]
    rejected_bytes = _e2b1_canonical_bytes(rejected_projection)
    return (
        tuple(candidates),
        tuple(rejection_counts),
        hashlib.sha256(rejected_bytes).hexdigest(),
    )


def _e2b1_validate_tree(
    document: dict[str, object],
    expected_commit_sha: str,
    expected_root_tree_sha: str,
) -> dict[str, object]:
    tree_document = _e2b1_require_members(document, _E2B1_TREE_MEMBERS)
    root_tree_sha = _e2b1_require_string(tree_document, "sha")
    _e2b1_validate_sha(root_tree_sha)
    if root_tree_sha != expected_root_tree_sha:
        _e2b1_reject()
    _e2b1_validate_https_url(_e2b1_require_string(tree_document, "url"))
    truncated = _e2b1_require_boolean(tree_document, "truncated")
    if truncated:
        _e2b1_reject()

    entry_values = _e2b1_require_array(tree_document, "tree")
    entries_list: list[tuple[str, str, str, str]] = []
    seen_paths: set[str] = set()
    seen_lower_paths: set[str] = set()
    seen_tuples: set[tuple[str, str, str, str]] = set()
    for entry_value in entry_values:
        entry = _e2b1_validate_tree_entry(entry_value)
        path = entry[0]
        lowered_path = path.lower()
        if path in seen_paths or lowered_path in seen_lower_paths or entry in seen_tuples:
            _e2b1_reject()
        seen_paths.add(path)
        seen_lower_paths.add(lowered_path)
        seen_tuples.add(entry)
        entries_list.append(entry)

    entries_list.sort(key=_e2b1_entry_sort_key)
    entries = tuple(entries_list)
    candidates, rejection_counts, rejected_tuple_sha256 = _e2b1_classify_candidates(entries)
    projection_entries = [
        {
            "path": path,
            "mode": mode,
            "type": object_type,
            "object_sha": object_sha,
        }
        for path, mode, object_type, object_sha in entries
    ]
    projection_bytes = _e2b1_canonical_bytes(
        {
            "commit_sha": expected_commit_sha,
            "root_tree_sha": root_tree_sha,
            "truncated": False,
            "entries": projection_entries,
        }
    )
    return {
        "mode": "tree",
        "commit_sha": expected_commit_sha,
        "root_tree_sha": root_tree_sha,
        "truncated": False,
        "entries": entries,
        "projection_bytes": projection_bytes,
        "projected_inventory_sha256": hashlib.sha256(projection_bytes).hexdigest(),
        "candidates": candidates,
        "rejection_counts": rejection_counts,
        "rejected_tuple_sha256": rejected_tuple_sha256,
    }


def _e2b1_parse_response_impl(
    *,
    mode: str,
    body: bytes,
    expected_commit_sha: str,
    expected_root_tree_sha: str | None,
) -> dict[str, object]:
    if type(mode) is not str or mode not in ("commit", "tree"):
        _e2b1_internal()
    if type(body) is not bytes:
        _e2b1_internal()
    if type(expected_commit_sha) is not str:
        _e2b1_internal()
    try:
        _e2b1_validate_sha(expected_commit_sha)
    except _E2B1ParseRejected:
        _e2b1_internal()

    if mode == "commit":
        if expected_root_tree_sha is not None:
            _e2b1_internal()
    else:
        if type(expected_root_tree_sha) is not str:
            _e2b1_internal()
        try:
            _e2b1_validate_sha(expected_root_tree_sha)
        except _E2B1ParseRejected:
            _e2b1_internal()

    # No response-byte ceiling is introduced here; that authority remains deferred.
    document = _e2b1_decode_json_object(body)
    if mode == "commit":
        return _e2b1_validate_commit(document, expected_commit_sha)
    return _e2b1_validate_tree(document, expected_commit_sha, expected_root_tree_sha)


def _parse_e2b1_response(
    *,
    mode: str,
    body: bytes,
    expected_commit_sha: str,
    expected_root_tree_sha: str | None = None,
) -> dict[str, object]:
    """Validate one sealed E2-B1 body and return only the frozen sanitized result."""

    try:
        return _e2b1_parse_response_impl(
            mode=mode,
            body=body,
            expected_commit_sha=expected_commit_sha,
            expected_root_tree_sha=expected_root_tree_sha,
        )
    except (_E2B1ParseRejected, _E2B1ParserInternal):
        raise
    except Exception:
        raise _E2B1ParserInternal() from None
