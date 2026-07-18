# Finance & Accounting Cycle 2 GL / Trial Balance E1 Fixed-Output Correction and E2-B/E3-B Prerequisite Freeze Amendment

Date: 2026-07-19
Authority: Main Control v2
Document class: canonical planning-only prerequisite amendment reconciled for documentation staging
Repository: `/home/deploy/erp-projects/erpai_project1_erpnext_ui_design`
Branch: `feature/erpnext-ui-design`
Starting source and upstream: `3b14e4328d554c183eab9f1acee82e0050e43c43`
Starting ahead/behind: `0/0`
Controlling evidence receipt: [E1/E2-A/E3-A Read-Only Evidence Acquisition](finance-accounting-cycle2-gl-tb-e1-e2a-e3a-read-only-evidence-acquisition-2026-07-18.md)
Controlling evidence decision retained: `stopped_for_read_only_evidence_gap`
Decision: `prerequisite_design_reconciled_for_docs_staging`

## 1. Outcome and authority

This amendment freezes the smallest planning candidates for a corrected E1 fixed-output acquisition, an E2-B path/semantic split, and five E3-B static prerequisite packages. It does not acquire evidence, approve a product digest, read a new implementation file, execute a command, start E2-B or E3-B, establish runtime compatibility, authorize E4, or reopen source authoring.

The Owner accepts the prior prerequisite-design stop and resolves its planning choices. The selected E2-B1 direction is one separately controlled, path-metadata-only recursive Git tree inventory at the exact peeled MariaDB commit. The Owner also accepts the clean privileged Bash/GNU `realpath` Docker-path posture and deterministic JSON `null` normalization for absent optional Docker configuration keys. These are documentation decisions only: corrected E1, GitHub acquisition, E2-B1, E2-B2 and E3-B remain unstarted and require later separate authority.

The E1 contract, E2-B1 metadata boundary, E2-B2 separation, E3-B decomposition and dependency graph are now reconciled for documentation staging. This is not a compatibility, evidence-acquisition or execution decision.

E2-A remains completed for provenance only. E3-A remains completed for static inventory only. MariaDB 10.11.18 remains a proof candidate only. No digest is approved. E4 and the Four-File Source-Authoring Gate remain deferred.

## 2. Evidence classes and non-conversion rules

| Class | A later approved gate may establish | It must not be converted into |
| --- | --- | --- |
| E1 command evidence | exact literal CLI path, fixed file identity, and eleven bounded image metadata fields | filesystem, UID/GID, secrets, Python, PID/thread/signal, application or runtime compatibility |
| E2-B1 path metadata | exact commit/tree/path/type/mode/blob identity | source semantics, compiled behavior, grants, runtime behavior or digest approval |
| E2-B2 source semantics | facts directly supported by exact approved source bytes and questions | build equality, deployment configuration, permission sufficiency, runtime behavior or accounting authority |
| E3-B static closure | lifecycle, callback, statement, candidate-role, schema-source and reconnect contracts | executed behavior, effective grants, physical schema, evidence validity or synthetic acceptance |
| E4 runtime evidence | only facts explicitly authorized by a later E4 gate | live or operational-data acceptance, accounting execution or source authoring |

Planning is not evidence acquisition. Source evidence is not runtime evidence. Inventory is not a grant list. A candidate permission matrix is not effective permission proof. Frappe user authority and MariaDB account authority are separate evidence planes.

## 3. Corrected E1 fixed-output contract

### 3.1 Owner-accepted future technical direction

The Owner accepts this planning method for a later separately authorized E1 evidence gate. It has two ordered substeps owned by one future E1 evidence owner:

1. establish exactly one canonical Docker CLI path in a clean evidence shell; and
2. only after that literal is accepted, use that same literal executable for fixed-field image inspection and for any permitted `stat` and SHA-256 records.

No guessed path, bare `docker` invocation, PATH re-resolution or alternate executable may intervene. Pre-inspection and post-inspection file identity must match. A changed path, file identity or hash discards the entire E1 acquisition.

The following are rejected:

- the prior dot-selector for optional `Config` keys;
- raw inspect JSON, `{{json .}}`, full objects or fallback formats;
- pipe-delimited field output, because a permitted JSON string may itself contain `|`;
- `command -v`, `which`, `whereis`, globbing, PATH/environment output or a guessed `/usr/bin/docker`;
- aliases, functions, builtins, keywords, multiple PATH hits, relative paths or ambiguous paths;
- environment values, labels, history, layer blobs or layer contents;
- automatic fallback after a template or path error; and
- any claim that absent and explicitly null optional keys have been distinguished.

### 3.2 Owner-accepted future Docker CLI path method

This exact future method is accepted for planning and was not executed:

```text
BASH_ENV=/dev/null ENV=/dev/null /bin/bash --noprofile --norc -p -c '
kind=$(builtin type -t docker) || exit 41
[[ "$kind" == "file" ]] || exit 42
builtin mapfile -t hits < <(builtin type -ap docker) || exit 43
((${#hits[@]} == 1)) || exit 44
candidate=${hits[0]}
[[ "$candidate" =~ ^/[A-Za-z0-9._+/@%=-]+$ ]] || exit 45
[[ -f "$candidate" && -x "$candidate" ]] || exit 46
resolved=$(/usr/bin/realpath --canonicalize-existing --physical -- "$candidate") || exit 47
[[ "$resolved" =~ ^/[A-Za-z0-9._+/@%=-]+$ ]] || exit 48
[[ -f "$resolved" && -x "$resolved" ]] || exit 49
printf "%s\n" "$resolved" || exit 50
' 2>/dev/null
```

The child shell is privileged and profile-free so `BASH_ENV`, `ENV`, exported functions and user profiles cannot supply the selected command. `builtin type -t` must classify the visible name as a disk file. `builtin type -ap` must return exactly one PATH executable. The conservative grammar rejects whitespace, control characters, relative results and shell metacharacters. GNU `realpath --canonicalize-existing --physical` must return one existing, symlink-free absolute target.

Permitted success output is exactly one LF-terminated canonical absolute path matching the frozen grammar, with exit `0` and empty stderr. No other value is retained.

| Exit | Fixed meaning | Evidence disposition |
| --- | --- | --- |
| `0` | one canonical regular executable path emitted | candidate path may enter the separate acceptance step |
| `41` | `docker` not found | stop and discard |
| `42` | visible name is not a disk file | stop and discard |
| `43` | path inventory could not be collected | stop and discard |
| `44` | zero, duplicate or multiple PATH hits | stop and discard |
| `45` | candidate is relative or violates the conservative grammar | stop and discard |
| `46` | candidate is not a regular executable | stop and discard |
| `47` | exact canonicalization failed or target does not exist | stop and discard |
| `48` | resolved value is not one conservative absolute path | stop and discard |
| `49` | resolved target is not a regular executable | stop and discard |
| `50` | final fixed output could not be written | stop and discard |
| any other nonzero | unsupported or unexpected host behavior | stop and discard |

No stdout from a nonzero run is evidence. A launch diagnostic is suppressed and never reclassified as evidence.

Authoritative design basis:

- the [GNU Bash `type` contract](https://www.gnu.org/software/bash/manual/html_node/Bash-Builtins.html) defines `-t`, `-a` and `-p`, and Bash privileged/profile-free startup excludes the inherited shell customizations this evidence shell rejects;
- the [GNU Coreutils `realpath` contract](https://www.gnu.org/software/coreutils/manual/html_node/realpath-invocation.html) defines canonical absolute output, physical symlink resolution and `--canonicalize-existing` failure; and
- this is still a host-command candidate, not proof that the installed `/bin/bash` and `/usr/bin/realpath` bytes are the cited GNU implementations.

The Owner accepts the clean privileged Bash plus GNU `realpath` posture. This approves the method, not the installed helper binaries or host compatibility. If either helper is missing, non-GNU, behaviorally different or outside the conservative grammar, E1 stops. The evidence shell excludes inherited functions and startup injection; it does not claim to audit aliases or functions defined only in an unrelated interactive shell.

### 3.3 Literal-path acceptance and identity binding

The path command does not itself approve the path. The future evidence owner must capture stdout bytes, stdout SHA-256, exit status and the empty-stderr assertion, then freeze the exact literal. All following command texts must substitute that literal directly; an unresolved placeholder, shell variable, command substitution, PATH lookup or symlink re-resolution is prohibited.

Only the accepted literal may be passed to the already accepted fixed `stat` field set and `sha256sum`. The future acquisition must record the same fields used for the Compose plugin—literal path, type, owner/group names, numeric UID/GID, mode and byte size—plus the file SHA-256. It must repeat both stat and SHA-256 around the later permitted use and require exact equality. A changed literal target, stat identity or SHA-256 stops and discards every dependent image record. No directory listing, adjacent-file read, bare `docker`, later PATH lookup, alternate symlink spelling or binary execution through another path is allowed.

### 3.4 Owner-accepted future image-inspection method

After literal-path acceptance, `<ACCEPTED_DOCKER_LITERAL>` must be replaced by the exact accepted absolute bytes. A command containing the placeholder is not executable and must stop. The frozen argument vector is:

```text
<ACCEPTED_DOCKER_LITERAL> image inspect --format '[{{json .Id}},{{json .RepoDigests}},{{json .Os}},{{json .Architecture}},{{json (index .Config "User")}},{{json (index .Config "WorkingDir")}},{{json (index .Config "Entrypoint")}},{{json (index .Config "Cmd")}},{{json (index .Config "StopSignal")}},{{json .RootFS.Type}},{{json .RootFS.Layers}}]' sha256:4c8b6fb188d81f5a355008730a1122658af88799ec759029c2dbd297dfc8e257
```

This is a deliberately constructed eleven-element JSON array, not raw inspect JSON. Only the five optional `Config` selectors use `index`; the required top-level and RootFS selectors remain fail-closed.

| Position | Field | Permitted JSON type and condition |
| --- | --- | --- |
| 1 | image ID | string; exactly `sha256:4c8b6fb188d81f5a355008730a1122658af88799ec759029c2dbd297dfc8e257` |
| 2 | repository digests | array of strings or `null` |
| 3 | OS | nonempty string |
| 4 | architecture | nonempty string |
| 5 | configured user | string or `null` |
| 6 | working directory | string or `null` |
| 7 | entrypoint | array of strings or `null` |
| 8 | command | array of strings or `null` |
| 9 | stop signal | string or `null` |
| 10 | RootFS type | nonempty string |
| 11 | RootFS diff IDs | array of strings or `null`; identifiers only, never layer contents |

The Owner accepts the rule that absent and explicit-null optional `Config` values are intentionally normalized to JSON `null`; present empty strings and arrays remain `""` and `[]`. The retained fact is `normalized_null`, not proof of whether the original representation was absent or explicitly null. A non-null optional value is acceptable only when it has the frozen field type and an exact value or shape approved before acquisition; an otherwise unexpected non-null value stops for Owner adjudication rather than being interpreted.

Permitted success behavior is exit `0`, empty stderr and exactly one LF-terminated valid JSON array of length eleven. Rejection is mandatory for any nonzero exit, stderr byte, blank/partial/multiple-line output, invalid JSON, unexpected length/type/order, wrong image ID, `<no value>`, unapproved object or field, unexpected non-null optional value, template parse/execute error, inspect error, implicit pull, raw fallback, or pre/post Docker binary identity mismatch. Partial output from a failed template is always discard-only.

Authoritative design basis:

- [Docker's formatting documentation](https://docs.docker.com/engine/cli/formatting/) defines Go-template formatting and the `json` helper;
- [Docker CLI v29.2.1 template helpers](https://github.com/docker/cli/blob/v29.2.1/templates/templates.go) bind the selected CLI source candidate's JSON helper;
- [Docker CLI v29.2.1 inspector](https://github.com/docker/cli/blob/v29.2.1/cli/command/inspect/inspector.go) binds the typed/raw retry and `missingkey=error` behavior that produced the prior stop;
- [Go `text/template` source](https://go.dev/src/text/template/funcs.go#L195) defines `index` and the zero value returned for an absent map key; and
- [Go `encoding/json`](https://pkg.go.dev/encoding/json) defines a nil interface as JSON `null`.

The method remains unexecuted until the accepted Docker literal is bound to the v29.2.1 behavior being cited. Unsupported `index`, parenthesized arguments, JSON encoding, typed/raw inspection or missing-key behavior is a hard stop, never permission to broaden inspection.

### 3.5 E1 evidence record and closure condition

The future E1 record may retain only:

- candidate command ID and immutable command-text hash;
- path command exit, empty-stderr boolean, literal-path bytes and path-output hash;
- accepted literal, pre/post stat fields and pre/post file SHA-256;
- image command exit, empty-stderr boolean and output SHA-256;
- the eleven parsed fields, fixed type assertions and pinned-ID equality;
- normalization disposition `optional_absent_or_null_normalized_to_null`;
- fixed rejection/stop enum; and
- evidence owner, UTC acquisition time and controlling approval reference.

E1 closes only if the helper posture is Owner-approved, the path lane succeeds unambiguously, the Docker binary identity remains stable, the exact literal invocation returns one valid record, and every rejection rule passes. It remains metadata-only evidence.

## 4. E2-B path discovery and semantic-read separation

### 4.1 Owner-selected E2-B1 metadata-only discovery

The peeled MariaDB Server commit remains:

`197f92bee02d8e836f529f37625be69b83e7acbd`

The required semantic areas remain account/host matching, table/column grant enforcement, process visibility, exact connection termination, `INFORMATION_SCHEMA.INNODB_TRX`, transaction isolation and read-only consistent snapshots, replica/topology status privilege, and statement-timeout semantics.

The Owner selects one future, separately controlled, path-metadata-only recursive Git Trees inventory of the public `MariaDB/server` repository. A trusted literal-path manifest is not selected because none is independently established. A bounded nonrecursive frontier is not selected. The recursive inventory is the sole narrow exception to the prior complete-tree prohibition; that prohibition remains controlling for source contents, other repositories or commits, general search and semantic reads.

This decision approves documentation of the future protocol only. No request, Git tree acquisition, path inventory or implementation-file read occurred.

### 4.2 Frozen GitHub API and request boundary

The future E2-B1 gate must freeze these request facts without substitution:

- repository: public `MariaDB/server` only;
- peeled commit: `197f92bee02d8e836f529f37625be69b83e7acbd`;
- API version header: `X-GitHub-Api-Version: 2026-03-10`;
- media type header: `Accept: application/vnd.github+json`;
- public unauthenticated read only; no `Authorization` header, token, credential or private-resource access; and
- one fixed nonsecret `User-Agent` before acquisition; if none is frozen in the later command gate, acquisition stops rather than inventing one during execution.

Only two future requests are permitted:

1. exact Git commit-object lookup for the literal peeled commit, solely to validate the returned commit SHA and obtain its single root `tree.sha`; and
2. `GET /repos/MariaDB/server/git/trees/{root_tree_sha}?recursive=1` for that exact returned root tree.

No tag, branch, ref, repository, organization or code-search enumeration is permitted. No blob, Contents API or file-content URL may be requested or followed. No redirect, authentication fallback, alternate API version, changed-parameter retry, nonrecursive retry, clone, fetch, archive, local index, grep or general-search fallback is permitted.

API version `2026-03-10` is selected for the future request; this documentation-only reconciliation does not prove that the later host/API interaction will accept it. A rejection is a stop.

### 4.3 Wire validation, retained projection and promotion

The future gate must validate the complete wire responses against an exact raw-response key/type allowlist frozen before execution. Documented but unretained fields may be parsed and discarded. A field outside that pinned wire schema, a missing required field, wrong type, error/message envelope or schema drift stops. The retained-field allowlist is not incorrectly treated as the complete GitHub wire schema.

The retained evidence projection is limited to:

- exact `commit_sha`;
- exact `root_tree_sha`;
- SHA-256 of the exact commit-response body bytes;
- SHA-256 of the exact recursive-tree response body bytes;
- `truncated`, present as Boolean `false`; and
- for each returned tree entry, literal `path`, `mode`, `type` and Git `object_sha`.

The Git entry `object_sha` is a Git object identifier, not a claimed SHA-256. URLs, sizes and other known wire fields are discarded after schema validation. No source bytes, excerpts, environment value, semantic fact or runtime claim may enter the projection.

The projected inventory must be canonicalized before hashing as one compact UTF-8 JSON object with keys in this exact order: `commit_sha`, `root_tree_sha`, `truncated`, `entries`. Each entry uses keys in this exact order: `path`, `mode`, `type`, `object_sha`. Entries are sorted by the UTF-8 byte sequence of `path`, then `mode`, `type` and `object_sha`; strings use JSON escaping, no insignificant whitespace or byte-order mark is permitted, and no trailing newline is included. Duplicate paths, case-collision ambiguity or duplicate sort tuples stop. `projected_inventory_sha256` is SHA-256 over exactly those canonical bytes.

Identity and completeness stops are mandatory for non-success status, redirect, returned commit mismatch, returned root-tree mismatch, `truncated` missing/null/non-Boolean/true, pagination or `Link`/cursor behavior, partial/error output, schema drift, invalid/absolute/traversal/control/backslash-ambiguous path, duplicate/conflicting path, unknown mode/type, or any content request. The response must be one complete nonpaginated tree array. There is no fallback.

Only entries with `type=blob` and regular-file mode `100644` or `100755` may be proposed as literal path candidates. Path metadata suggests candidates but proves no MariaDB semantic. No candidate is promoted automatically: Main Control must map each proposed literal path and Git object ID to one of the eight frozen E2-B2 question categories in a path-only Owner-review receipt. If a complete candidate set cannot be justified from metadata alone, the gate stops without content access. The Owner-review receipt may promote only those candidate paths, their modes/types/object IDs, question categories and `projected_inventory_sha256`; the full inventory and raw responses remain controlled evidence.

GitHub's [Git Trees API](https://docs.github.com/en/rest/git/trees) is the selected metadata surface. The [repository contents API](https://docs.github.com/en/rest/repos/contents), code search and every source-content surface remain rejected.

### 4.4 E2-B2 exact semantic source-read contract

E2-B2 is a separately approved future gate. It may start only after the Owner approves the literal E2-B1 path list and maps every path to one or more frozen question IDs:

- `Q1_ACCOUNT_HOST_MATCH`;
- `Q2_TABLE_COLUMN_GRANT`;
- `Q3_PROCESS_VISIBILITY`;
- `Q4_EXACT_CONNECTION_TERMINATION`;
- `Q5_INNODB_TRX_VISIBILITY`;
- `Q6_ISOLATION_READ_ONLY_SNAPSHOT`;
- `Q7_REPLICA_TOPOLOGY_PRIVILEGE`; and
- `Q8_STATEMENT_TIMEOUT`.

For each approved literal path, the future contract must bind:

- peeled commit and root tree SHA;
- literal path and E2-B1 blob SHA;
- raw-byte SHA-256, byte count, encoding and newline convention;
- exact question ID;
- minimum exact supporting line range and excerpt-byte hash;
- directly supported paraphrased fact, conditions and limitations;
- named adjacent dependency without opening it;
- reviewer and disposition `supported`, `not_supported`, `blocked_by_adjacent_path` or `mismatch_discard`; and
- explicit statement that the evidence is source-only and grants no runtime or digest authority.

Only the Owner-approved blob identities may be read. Full source is not retained in the amendment. E2-B2 stops on commit/path/blob/hash mismatch, decoding ambiguity, missing semantics, unpinned build condition, contradictory branch, API mismatch, or a required adjacent file/symbol outside the allowlist. An adjacent path may be named but not opened; adding it requires a new Owner allowlist decision.

Prohibited inference includes semantics from filenames, other branches/versions, neighboring files, product documentation alone, tests, compile flags, deployment configuration, image equality, digest approval, complete grant sufficiency, final role design, numeric limits, runtime behavior or accounting authority. Partial supported facts may be retained as non-closure evidence, but E2-B2 closes only if Q1-Q8 are all directly supported.

## 5. E3-B bounded prerequisite packages

The E3-B numbers are ownership labels, not automatic execution order. Every package requires separate Owner approval and consumes only accepted predecessor evidence.

### 5.1 E3-B1 — Frappe lifecycle and harness mapping

Inputs are limited to the published E3-A receipt, its already pinned Frappe paths, and the unchanged harness at SHA-256 `c8d0bb0556f9abb04e1be69c1d67a7f92c4ed37a64d8270d84339ad590e9cea5`. No adjacent source expansion is permitted.

Required outputs:

- exact initializer → discovery → runner → callback → test/module/class cleanup → Frappe cleanup → JUnit finalization → evidence-promotion graph;
- literal allowlist of the five published top-level `test.id()` values;
- mapping for the five published static subtest sites to fixed non-sensitive aliases;
- generic holder-failure policy without module/class/test/parameter/fixture identity;
- current authority-entry map and leakage register; and
- invariant that no evidence is promotable until every cleanup and JUnit finalization obligation succeeds.

Stop on a hash/path mismatch, sixth/dynamic/unexpected/duplicate test or subtest, value-bearing identity that cannot map safely, unresolved lifecycle edge, promotion-before-cleanup path, or any need to retain raw traceback, captured output, expected/actual payload or identity-bearing holder error.

### 5.2 E3-B2 — CPython/J2 callback binding

This package does not follow automatically from corrected E1. It first requires a separately approved fixed-output installed-Python identity record binding the immutable backend image, one absolute executable path and hash, implementation name, complete version tuple, cache tag, ABI/SOABI and build identity. PATH, environment, `sys.path` and package inventory remain prohibited.

Only then may the Owner approve an exact CPython tag/commit and literal path/hash allowlist covering `addSubTest`, `stop`, `shouldStop`, `addDuration`, setup/class/module holders, callback order and superclass delegation.

Required output is an exact method-owner/signature/caller/order/exception/delegation matrix, compatibility binding to the private pinned `frappe.testing.runner.TestResult` candidate, fixed sanitized outcome enums, generic holder mapping and post-cleanup JUnit finalization contract.

Stop on non-CPython or vendor-patched identity, build/source mismatch, missing or changed callback, private Frappe seam mismatch, unresolved superclass behavior, or any need for raw IDs, tracebacks or captured output. Direct `TestRunner` construction remains rejected.

### 5.3 E3-B3 — SQL and least-privilege candidate

E3-B3 is the final static synthesis package despite its number. It waits for E3-B1, E2-B2, E3-B4 and E3-B5, and for E3-B2 wherever callback/finalization behavior affects lifecycle SQL.

Its non-executable statement matrix must record statement ID, phase/case, actor, statement class/template identity, database/system object/table, exact read/write columns, row predicate, transaction state, semantic citation, candidate privilege, prohibited privilege, expected denial and sanitized retained evidence.

Actors remain separate: preparer, normal reader, seal verifier, topology account, reconnect account, one writer per S01-S08 case, and a distinct Frappe bootstrap/cleanup identity if framework lifecycle SQL cannot fit reader authority.

Two authority planes must remain visibly separate:

1. Frappe actor, role, company, User Permission, DocPerm/Custom DocPerm, mask, share and report-role denial before raw-GL query dispatch; and
2. MariaDB account, host scope, object/column privilege, session and transaction authority.

A read-only database login does not prove Frappe permission enforcement. Frappe negative tests do not prove database least privilege. The normal measured reader must have no DDL, DML, `GRANT`, `FILE` or administrative authority.

Stop on dynamic/unknown SQL, object or column; wildcard or `ALL`; broad database `SELECT`; role co-residence; root, `PROCESS` or `CONNECTION ADMIN` in measured readers/reconnect; unbound Frappe cleanup SQL; or any privilege not directly supported by E2-B2. The matrix is a candidate only, never a final `GRANT` list.

No accounting semantics may be inferred from a field or table name. Opening, movement, closing, account/company currency, hierarchy, fiscal boundaries, cancellation canaries and Finance Book cohorts remain blocked until exact approved ERPNext/Frappe product evidence and later runtime evidence support them. Cancellation, close/reopen, frozen-period controls, audit certification, mutation and accounting execution remain deferred.

### 5.4 E3-B4 — S07 exact-column closure

Prerequisites are exact installed ERPNext/Frappe commit binding, a later Owner-approved literal allowlist for the two DocType definitions and only demonstrably necessary schema-generation/migration paths, and bounded physical-schema provenance. No new path is guessed or read by this amendment.

For `tabAccount Closing Balance` and `tabProcess Period Closing Voucher`, the package must freeze the exact ordered required-column tuple, each column's source path/hash/field provenance, relevant type/null/default facts, exact S07 read/write use and fail-closed missing/extra/renamed behavior.

Dynamic runtime intersection and silent fallback are rejected. Static source closure does not prove the disposable physical schema; E4 must later verify exact equality. Stop if commits or paths are unbound, DocType sources are insufficient, Custom Fields/Property Setters/patches can change required columns, or any required column remains dynamic.

### 5.5 E3-B5 — reconnect contract

E3-B5 waits for E2-B2 account/host matching, process-visibility and exact connection-termination semantics. It must freeze:

- one unique account and service/source IP per active subrun;
- no overlapping account reuse;
- exactly two same-account, same-IP, expected-database sessions;
- ephemeral validation of account, matched host rule, source IP, database, target/survivor connection IDs and controller-assigned roles;
- zero unrelated same-account sessions;
- termination only after exact tuple/count equality;
- target absent, survivor present, reconnect on a new ID, killed ID still absent and count restored to exactly two; and
- retained evidence limited to aliases/hashes, counts, booleans and fixed enums.

Same-account self-termination may proceed only if E2-B2 proves it without root, `PROCESS`, `CONNECTION ADMIN` or database-wide `SELECT`. Otherwise this package stops for an Owner redesign/defer choice. Every mismatch, timeout, partial or cleanup-failed result is discard-only. E4 alone may prove runtime reconnect behavior.

## 6. Dependency order and safe parallel lanes

```text
corrected E1 ───────────────────────────────┐
E2-B1 ── Owner literal-path approval ── E2-B2 ── E3-B5 ─┐
E3-B1 ────────────────────────────────────────────────────┤
Python identity ── CPython allowlist ── E3-B2 ────────────┤
S07 allowlist ── E3-B4 ───────────────────────────────────┤
                                                         └─ E3-B3 final static synthesis
all accepted static packages ── one Main Control synthesis ── later Owner choices for E4/source authoring
```

Corrected E1, E2-B1 and E3-B1 are technically independent and may be separately approved in parallel. Installed-Python identity/source binding and S07 allowlist preparation are also independent planning lanes. No lane may consume provisional output from another lane.

Sequential boundaries are mandatory:

- E2-B2 waits for Owner acceptance of the E2-B1 literal paths;
- E3-B2 waits for installed-Python identity and exact CPython source binding;
- E3-B4 waits for its exact ERPNext/Frappe source/schema allowlist;
- E3-B5 waits for E2-B2;
- E3-B3 closes last after the required semantic, lifecycle, schema and reconnect inputs; and
- one Main Control synthesis follows the accepted static packages.

E4, controller/harness source authoring, image materialization, infrastructure/secrets, synthetic execution and any runtime evidence remain separate later Owner gates.

## 7. Findings and one-pass review disposition

### Resolved prerequisite-design finding

- **E2B1-REV-001 resolved for planning.** The Owner supplies the missing narrow authority for one exact-commit, recursive, path-metadata-only inventory and freezes the API version, media type, unauthenticated posture, retained projection and fail-closed truncation boundary. This resolves the documentation design choice only; E2-B1 evidence remains unacquired.

### Blocker

1. **Current authority separation is absent.** Published E3-A evidence locates reader, preparer, dynamic writer, schema, topology, root and reconnect authority in one harness/process. No candidate grant matrix may be treated as closure.
2. **J2 and post-cleanup finalization remain unbound.** Published E3-A evidence shows inherited callbacks remain unbound and harness promotion precedes outer Frappe cleanup.
3. **S07 exact columns remain dynamic.** Published E3-A evidence shows runtime schema intersection for both S07 tables.
4. **Reconnect least privilege remains unproven.** Published E3-A evidence does not prove the unique account/IP, exact-two, zero-unrelated and forbidden-privilege posture.

### High

1. Docker inspection must use the exact canonical binary it fingerprints, with matching pre/post stat and SHA-256; a later bare-PATH invocation is rejected.
2. Frappe application permission evidence and MariaDB least-privilege evidence must remain separate and both fail closed.
3. E3-B3 must close last; static inventory cannot become a grant list.
4. GL/TB semantics cannot be inferred from filenames or column names. Cancellation and execution controls remain deferred.
5. Expected/actual payloads, tracebacks, captured output, value-bearing subtest identities and raw process account/host values are concrete leakage surfaces. Only sanitized aliases/hashes/counts/booleans/enums may be promoted.
6. Static S07 closure cannot prove the physical disposable schema, and static reconnect design cannot prove runtime reconnect behavior.

### Medium

- An eleven-element JSON array is accepted instead of pipe-delimited JSON to avoid delimiter ambiguity.
- Outer `.Config` and required selectors can still fail; exit `0`, empty stderr, one complete record and discard-only partial output remain mandatory.
- E2-B path evidence must reject non-blob candidates, redirects, truncation, schema drift, ambiguous paths and adjacent-file expansion.
- Canonical test identities may be checked transiently only; persisted failure records remain identity-safe and row-free.

### Reviewer dispositions

Accepted:

- the selected one-time recursive, path-metadata-only E2-B1 inventory with fixed public unauthenticated API posture;
- separate wire-schema validation, retained projection and canonical inventory SHA-256;
- exact-literal Docker invocation with pre/post file identity;
- deterministic Docker optional-key `null` normalization as a normalized fact, not original-representation proof;
- distinct Frappe and MariaDB permission planes;
- E3-B3 as final static synthesis;
- E3-B4/E3-B5 as static contracts only;
- discard-only partial, killed, mismatched or cleanup-failed evidence; and
- continued read-only, no-execution accounting protection.

Rejected:

- treating documentation readiness as E2-B1 execution, source evidence or compatibility;
- invented MariaDB paths, general historical search or recursive access outside the exact selected repository/commit metadata exception;
- bare `docker`, raw inspect, fallback formats, PATH/environment dumps or guessed executable paths;
- semantics inferred from path/schema names;
- SQL grants as proof of Frappe permission enforcement;
- application permissions as proof of database least privilege; and
- any source-to-runtime, metadata-to-runtime or planning-to-execution conversion.

Deferred:

- installed helper/binary proof, corrected E1 acquisition and Docker CLI/image binding;
- Git tree acquisition, literal MariaDB path approval and all E2-B source reads;
- installed CPython identity and exact callback sources;
- ERPNext/Frappe S07 source/schema allowlists;
- complete role/grant candidate, physical schema and reconnect proof;
- all E4 runtime canaries, digest approval, complete schemas and numeric workload limits;
- HTTP/CORS, Finance-to-AI, source authoring, live alignment and accounting execution.

No new accounting-equation contradiction was found. No accounting correctness or runtime compatibility claim is made.

## 8. Owner decisions still required

Before any acquisition or static package starts, the Owner must separately decide:

1. whether to stage and later publish only this amendment and README;
2. the exact future E1 acquisition command gate, including installed-helper handling and exact non-null optional-value expectations;
3. the exact future E2-B1 acquisition command/schema gate, including fixed nonsecret `User-Agent` and complete raw wire-schema allowlist;
4. whether to execute corrected E1 and E2-B1 under separate approvals;
5. which exact E2-B1 candidate commit/path/object-ID list to approve for E2-B2 after reviewing the path-only receipt;
6. whether to authorize E3-B1 on only the already pinned Frappe paths and unchanged harness;
7. the fixed-output installed-Python identity fields and later exact CPython path allowlist before E3-B2;
8. the exact ERPNext/Frappe S07 source/schema allowlist before E3-B4;
9. whether to preserve same-account reconnect only if E2-B2 proves the forbidden-privilege-free path, otherwise redesign or defer it;
10. whether to authorize E2-B2 only after literal-path acceptance and then the dependent E3-B5/E3-B3 packages; and
11. later and separately, whether to authorize one static synthesis, E4, or source authoring.

None of these decisions is implicit in accepting or publishing this document.

## 9. Protected boundaries

Finance Cycle 1 aggregate/read-only protections remain controlling: role separation, company scope, aggregate-only payloads, fail-closed accounting behavior, identity suppression and no execution. `gl_reconstructed` remains the sole synthetic proof candidate. No native General Ledger, native Trial Balance, Query Report passthrough, ACB/cache mode or silent fallback is restored.

Sales, Procurement and Warehouse routes, landing behavior, role authority, request isolation, managed navigation and accepted browser behavior remain protected. Finance workspace behavior, Shared UI, routing, registries, governance manifests, AI Assistant and Finance-to-AI access remain unchanged. Landing precedence remains `Sales > Procurement > Finance > Warehouse`.

No native report/list/form/export/download/print/mutation/email/notification/execution surface is approved. Source/live separation remains controlling, and the live deployment tree and operational data remain out of scope.

The harness remains unchanged and untracked. The future controller, runner Dockerfile and initializer remain absent. The Four-File Source-Authoring Gate remains stopped.

## 10. Validation and future documentation staging allowlist

Validation for this amendment requires:

- starting amendment SHA-256 `01d4ceb33c5f39f8cd78b2bb3b706d1456a009d2846fbd3eceb991b5a04d5c3b` and starting README SHA-256 `6faf4e4992c9b0fa25d0f167f434c5ab48ded2f8dc3f2db95e7e340e583929c7`;
- exact repository root, branch and local/upstream `3b14e4328d554c183eab9f1acee82e0050e43c43` with `0/0` parity;
- empty index;
- candidate scope exactly this amendment plus README, alongside the unchanged harness and four protected exclusions;
- `git diff --check HEAD`, Markdown trailing-whitespace and local-reference checks;
- unchanged harness SHA-256 `c8d0bb0556f9abb04e1be69c1d67a7f92c4ed37a64d8270d84339ad590e9cea5`;
- unchanged exclusion statuses and hashes;
- absent controller, Dockerfile and initializer;
- no digest approval, complete executable schema or numeric workload limit;
- no E2-B/E3-B/E4 execution authority; and
- no live-tree or operational-data access.

If the Owner later authorizes documentation staging, the exact allowlist is only:

1. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/finance-accounting-cycle2-gl-tb-e1-fixed-output-e2b-e3b-prerequisite-freeze-amendment-2026-07-19.md`; and
2. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/README.md`.

## 11. Final control statement

**Decision:** `prerequisite_design_reconciled_for_docs_staging`

The Owner-selected E1 path/null posture and E2-B1 recursive metadata-only protocol are reconciled with the unchanged E2-B2/E3-B dependency graph. The published `stopped_for_read_only_evidence_gap` remains the controlling evidence decision. This documentation-readiness result does not claim compatibility, acquisition or execution. No candidate command was executed. No GitHub tree was acquired. No new MariaDB, ERPNext, Frappe or CPython implementation file was read. Corrected E1, E2-B1, E2-B2, E3-B1 through E3-B5, E4 and source authoring were not started.

No source authoring, image inspection/pull/materialization, container or Compose action, infrastructure, secret, test, Frappe, Bench, SQL, fixture, synthetic execution, HTTP/CORS inspection, live access, staging, commit, push, migration, permission change, protected gate or accounting action occurred.
