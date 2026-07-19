# Finance & Accounting Cycle 2 GL / Trial Balance Corrected E1 and E2-B1 Wire-Contract Freeze Gate

Date: 2026-07-19

Repository: `/home/deploy/erp-projects/erpai_project1_erpnext_ui_design`

Branch: `feature/erpnext-ui-design`

Controlling baseline: `53cee0d91ce268b8188ccdfe1e556a62ce30b797`

Authority: Main Control v2; planning and documentation only

Decision: `stopped_for_wire_contract_gap`

## 1. Outcome and controlling effect

This gate freezes the narrowest safe planning contract for a corrected E1 Docker-CLI/image-metadata read and an E2-B1 public GitHub commit/tree metadata acquisition. It does not execute either contract, acquire a Git tree, read MariaDB source content, approve a product digest, establish image or database compatibility, start E2-B, E3-B or E4, or reopen the Four-File Source-Authoring Gate.

The request and response shapes, evidence projections, failure rules and dependency order are frozen below. The gate nevertheless stops because a future executable package still lacks concrete prerequisites that cannot safely be inferred:

1. installed provenance for `/usr/bin/env`, `/bin/bash`, `/usr/bin/realpath`, `/usr/bin/stat` and `/usr/bin/sha256sum`;
2. an exact Docker daemon/context/config boundary for the supplied image-inspection argument vector;
3. an accepted non-null value allowlist for Docker image positions 5-9;
4. a fixed curl path, file identity, libcurl/TLS feature set and CA trust-source provenance;
5. Owner-approved connect, request and external-watchdog ceilings derived under a later acquisition preflight; and
6. source-controlled parser/controller provenance capable of enforcing the frozen wire schemas and atomic discard rules.

No placeholder-bearing command in this document is executable. Closing a planning gap does not authorize execution. Each future acquisition still requires a separate Owner gate.

## 2. Published baseline and evidence classification

The controlling documents are:

- [E1/E2-A/E3-A Read-Only Evidence Acquisition](finance-accounting-cycle2-gl-tb-e1-e2a-e3a-read-only-evidence-acquisition-2026-07-18.md), whose factual decision remains `stopped_for_read_only_evidence_gap`;
- [E1 Fixed-Output Correction and E2-B/E3-B Prerequisite Freeze Amendment](finance-accounting-cycle2-gl-tb-e1-fixed-output-e2b-e3b-prerequisite-freeze-amendment-2026-07-19.md), whose later accepted planning decisions supersede the prior failed output assumptions;
- [Selected-Option Product and Compatibility Fingerprint](finance-accounting-cycle2-gl-tb-selected-option-product-compatibility-fingerprint-2026-07-18.md); and
- [Selected-Option Evidence Closure Decisions](finance-accounting-cycle2-gl-tb-selected-option-evidence-closure-decisions-2026-07-18.md).

The evidence classes remain non-convertible:

| Package | May establish later | Must not establish |
| --- | --- | --- |
| corrected E1 | one Docker CLI literal and eleven bounded local image metadata fields | daemon compatibility, image digest approval, layer contents, database behavior, grants, GL/TB semantics or accounting correctness |
| E2-B1 | public commit, root-tree, path, Git mode/type and Git object identity | source semantics, image equality, build equality, grants, runtime behavior, digest approval or accounting authority |
| E2-B2 | only facts directly supported by later Owner-approved source bytes | runtime behavior, effective permissions, deployment equality or accounting authority |
| E3-B | static lifecycle, schema and least-privilege candidates under its own allowlists | execution, effective grants or runtime proof |
| E4 | later separately approved synthetic compatibility evidence | live or operational-data authority |

MariaDB 10.11.18 remains a proof candidate only. No registry, platform, config or image digest is selected or approved. E2-A remains provenance-only and E3-A remains static-inventory-only. The harness remains an untracked, unchanged candidate. The controller, runner Dockerfile and initializer remain absent.

## 3. Corrected E1-A — exact Docker CLI path helper

### 3.1 Frozen future command

The future evidence owner may use this command only after the five helper-binary literals and their expected GNU/Bash behavior have been separately fingerprinted and approved. It was not executed by this gate.

```bash
/usr/bin/env -i PATH=/usr/local/bin:/usr/bin LC_ALL=C BASH_ENV=/dev/null ENV=/dev/null /bin/bash --noprofile --norc -p -c '
exec 2>/dev/null
kind=$(builtin type -t docker) || exit 41
[[ "$kind" == file ]] || exit 42
hits=()
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

`/usr/local/bin:/usr/bin` is the complete search path. It has no empty component, relative component or current-directory fallback and avoids the common `/bin`/`/usr/bin` usrmerge alias duplication. A Docker executable visible only outside those two directories causes a stop; it does not authorize search expansion.

The clean environment contains exactly `PATH`, `LC_ALL`, `BASH_ENV` and `ENV`. The privileged, profile-free Bash rejects startup files and imported shell functions. `type -t` must return `file`; alias, function, builtin, keyword or missing results stop. `type -ap` must produce exactly one lexical result. Multiple results stop even when they later resolve to the same inode.

The lexical result may itself be a symlink, but it is never retained. GNU `realpath --canonicalize-existing --physical` must resolve it to one existing canonical absolute target. The retained target must match the conservative ASCII path grammar and be a regular executable file. A symlink loop, missing component, relative result, whitespace/control byte, metacharacter, zero result or ambiguity stops.

### 3.2 Exit, stdout, stderr and retained fields

| Exit | Meaning | Disposition |
| --- | --- | --- |
| `0` | exactly one canonical path was emitted | path may enter the separate literal-acceptance step |
| `41` | `docker` not found | stop and discard |
| `42` | visible name is not a disk file | stop and discard |
| `43` | Bash path collection failed | stop and discard |
| `44` | result count is not exactly one | stop and discard |
| `45` | lexical path is relative or violates the frozen grammar | stop and discard |
| `46` | lexical path is not a regular executable file | stop and discard |
| `47` | canonicalization failed | stop and discard |
| `48` | canonical result violates the frozen grammar | stop and discard |
| `49` | canonical target is not a regular executable file | stop and discard |
| `50` | fixed output could not be written | stop and discard |
| any other nonzero | unsupported helper or host behavior | stop and discard |

Success stdout is exactly one LF-terminated path and contains no other byte. Success stderr is empty. Any stdout from a nonzero run is discard-only. No PATH, environment, alias, function, directory or adjacent-file inventory is retained.

The path record may retain only the command-text SHA-256, exit `0`, `stderr_empty=true`, canonical literal path, stdout SHA-256, evidence owner and UTC attempt time. The literal must be textually substituted into every later command. A shell variable, command substitution, bare `docker`, alternate symlink spelling or later PATH lookup is prohibited.

The command is based on the [GNU Bash `type` contract](https://www.gnu.org/software/bash/manual/html_node/Bash-Builtins.html) and [GNU Coreutils `realpath` contract](https://www.gnu.org/software/coreutils/manual/html_node/realpath-invocation.html). Those upstream descriptions do not prove the installed helper bytes; their missing provenance is a concrete execution blocker.

## 4. Corrected E1-B — binary identity and drift binding

After the literal `<ACCEPTED_DOCKER_LITERAL>` is accepted, the future owner must replace the placeholder with those exact safe ASCII path bytes and run the following two commands immediately before and immediately after image inspection. These commands were not executed.

```bash
LC_ALL=C /usr/bin/stat --dereference --printf='%d|%i|%f|%a|%u|%g|%s|%Y|%Z\n' -- '<ACCEPTED_DOCKER_LITERAL>'
LC_ALL=C /usr/bin/sha256sum --binary -- '<ACCEPTED_DOCKER_LITERAL>'
```

The stat record contains exactly nine pipe-delimited fields in order:

1. decimal device number;
2. decimal inode;
3. lowercase hexadecimal raw file mode;
4. octal permission bits;
5. decimal owner UID;
6. decimal group GID;
7. decimal byte size;
8. signed decimal modification time in whole epoch seconds; and
9. signed decimal status-change time in whole epoch seconds.

The controller must validate from the raw mode that the target is a regular file and from the permission bits that at least one execute bit is present. The SHA-256 line is exactly 64 lowercase hexadecimal characters, one space, `*`, the accepted literal and LF. Each command must exit `0`, produce exactly one complete line and produce empty stderr.

The literal path, stat line and SHA-256 line must be byte-identical before and after inspection. Any drift, disappearance, parse failure, malformed line, nonregular or nonexecutable state, stderr byte or command failure discards the image output and every dependent record. Later reuse requires a new pre/use/post binding.

This detects observed pre/post drift only. It does not prove that an executable was never transiently exchanged and restored between checks. An immutable mount, file-descriptor execution design or equivalent atomic binding remains a High residual if stronger assurance is later required. GNU [`stat`](https://www.gnu.org/software/coreutils/manual/html_node/stat-invocation.html) and [`sha256sum`](https://www.gnu.org/software/coreutils/manual/html_node/sha2-utilities.html) define the proposed fields, but the installed binary identities remain unproven.

## 5. Corrected E1-C — key-safe eleven-field image inspection

### 5.1 Frozen argument vector

Only the accepted Docker literal may occupy the first argument. The exact future command is:

```text
<ACCEPTED_DOCKER_LITERAL> image inspect --format '[{{json .Id}},{{json .RepoDigests}},{{json .Os}},{{json .Architecture}},{{json (index .Config "User")}},{{json (index .Config "WorkingDir")}},{{json (index .Config "Entrypoint")}},{{json (index .Config "Cmd")}},{{json (index .Config "StopSignal")}},{{json .RootFS.Type}},{{json .RootFS.Layers}}]' sha256:4c8b6fb188d81f5a355008730a1122658af88799ec759029c2dbd297dfc8e257
```

The placeholder must be textually replaced before execution. The argument vector must not gain a global host/context flag, environment override, alternate format, fallback selector or additional image reference without a later Owner amendment. That exactness exposes a blocker: the controlling documents do not yet bind the Docker endpoint/context/config used by this vector. Ambient `DOCKER_HOST`, `DOCKER_CONTEXT`, `DOCKER_CONFIG` or current-context state would change evidence meaning. The command therefore remains non-executable until the Owner selects an explicit endpoint/config posture or separately approves a fixed context fingerprint.

### 5.2 Eleven-position schema

The only success value is one JSON array of exactly eleven positions:

| Position | Field | Permitted JSON value | Acceptance rule |
| --- | --- | --- | --- |
| 1 | image ID | string | exactly `sha256:4c8b6fb188d81f5a355008730a1122658af88799ec759029c2dbd297dfc8e257` |
| 2 | repository digests | `null` or array of strings | each string has one final `@sha256:` plus 64 lowercase hex; prefix is nonempty printable ASCII without whitespace, controls, DEL or `@`; `null` is schema-valid but nonclosing |
| 3 | OS | string | exactly `linux` |
| 4 | architecture | string | exactly `amd64` |
| 5 | configured user | `null` or string | `null` is normalized; any non-null value requires a preapproved exact value |
| 6 | working directory | `null` or string | same rule |
| 7 | entrypoint | `null` or array of strings | same rule; every array member is a string |
| 8 | command | `null` or array of strings | same rule; every array member is a string |
| 9 | stop signal | `null` or string | same rule |
| 10 | RootFS type | string | exactly `layers` |
| 11 | RootFS diff IDs | nonempty array of strings | each value is exactly `sha256:` plus 64 lowercase hexadecimal characters; order is retained |

Absent and explicit-null optional keys at positions 5-9 intentionally normalize to JSON `null`; the evidence may say only `optional_absent_or_null_normalized_to_null`. Empty string and empty array are non-null values and therefore require preapproval. The previous failed E1 promoted no value allowlist, so the exact accepted non-null values remain unresolved. Execution with an unexpected non-null value must stop for Owner adjudication; it may not silently broaden the allowlist.

Repository-digest strings and RootFS diff IDs are identifiers only. They do not approve a product digest, establish a registry binding or authorize a layer read. The conservative repository-prefix rule is a leakage-safe accepted subset, not a claim that the complete Docker reference grammar has been proven.

### 5.3 Process and retention rules

Success requires exit `0`, empty stderr and stdout containing exactly one LF-terminated JSON array with no leading/trailing text or second line. Blank, partial, multiple, invalid, wrong-length, wrong-type or wrong-value output stops. `<no value>`, a template error, an inspect error, an implicit pull request, raw-object fallback, pre/post binary drift or an unapproved optional value stops and discards all output.

The E1 receipt may retain only:

- immutable command-text SHA-256;
- accepted Docker literal and its pre/post stat and SHA-256 binding;
- exit and empty-stderr facts;
- exact output-byte SHA-256;
- the decoded eleven positions;
- fixed type/value assertions and null-normalization disposition;
- evidence owner, UTC attempt time and stop/result enum.

Raw inspect JSON, `Config` objects, environment, labels, history, mounts, container lists, layer contents, adjacent fields and daemon-wide output are prohibited. [Docker formatting](https://docs.docker.com/engine/cli/formatting/), [Go `text/template` index](https://go.dev/src/text/template/funcs.go#L195) and [Go JSON encoding](https://pkg.go.dev/encoding/json) are design authorities only. Exact installed Docker behavior remains subject to the binary and endpoint binding.

## 6. E2-B1 public HTTP policy

Official GitHub documentation was observed on 2026-07-19:

- [Get a commit object](https://docs.github.com/en/rest/git/commits?apiVersion=2026-03-10#get-a-commit-object);
- [Get a tree](https://docs.github.com/en/rest/git/trees?apiVersion=2026-03-10#get-a-tree);
- [REST API request guidance](https://docs.github.com/en/rest/using-the-rest-api/getting-started-with-the-rest-api?apiVersion=2026-03-10);
- [REST API versions](https://docs.github.com/en/rest/about-the-rest-api/api-versions);
- [REST API pagination](https://docs.github.com/en/rest/using-the-rest-api/using-pagination-in-the-rest-api?apiVersion=2026-03-10); and
- [official REST OpenAPI description](https://github.com/github/rest-api-description/blob/main/descriptions/api.github.com/api.github.com.2026-03-10.json).

The OpenAPI link above is a current discovery reference, not immutable evidence. A later acquisition/compatibility gate that relies on that file must bind it to an exact upstream commit and file SHA-256 before use. The complete JSON allowlists in this document are independently frozen as the 2026-07-19 observation-date contract.

The fixed request policy is:

| Field | Exact future value |
| --- | --- |
| repository | public `MariaDB/server` only |
| peeled commit | `197f92bee02d8e836f529f37625be69b83e7acbd` |
| method | `GET` |
| scheme/host | `https://api.github.com` |
| API version | `2026-03-10` |
| media type | `application/vnd.github+json` |
| User-Agent | `erpai-gl-tb-e2b1-readonly/1.0` |
| authentication | none; no Authorization, cookies, credentials, netrc, client certificate, proxy credential or private-resource fallback |
| redirect | prohibited; zero followed redirects |
| success | exactly HTTP `200` |

Exactly two requests are permitted: the literal commit-object request and, only after validation, one recursive tree request using the returned root `tree.sha`. No tag, branch, ref, organization, repository or code-search enumeration; no clone, fetch, archive, Contents API, blob request, returned-URL follow, nonrecursive fallback, pagination or alternate API version is allowed.

## 7. E2-B1 transport binary provenance prerequisite

The future transport literal is written as `<ACCEPTED_CURL_LITERAL>` because no installed curl binary was inspected in this gate. Before either GET can be authorized, one separate read-only fixed-output preflight must establish:

- exactly one canonical absolute regular executable path, with the same no-alias/no-function/no-ambiguity posture as E1;
- pre/post file stat identity and SHA-256;
- curl and libcurl versions, TLS backend/version, supported protocols and feature list;
- support for every selected option and every `--write-out` variable below;
- the system/native CA trust source, or exact CA-bundle literal, ownership, mode and SHA-256;
- no curl configuration file, netrc, proxy, credential helper or ambient credential input;
- the exact command-manifest SHA-256; and
- the source-controlled parser/controller source identity and runtime needed to validate duplicate JSON keys, schemas, hashes and atomic promotion.

The [curl command-line manual](https://curl.se/docs/manpage.html) is the upstream design authority. It does not prove the installed binary, compiled features or CA store. `--disable` must be the first curl option so no curl configuration is loaded. `--fail-with-body` and the selected write-out variables are not assumed supported until the preflight proves them. Curl failure behavior is never the sole validator; the controller must independently require curl exit `0`, exact HTTP status, TLS verification, URL, redirect and schema facts.

## 8. E2-B1 exact future transport command candidates

### 8.1 Fixed request headers

Each request sends exactly these application headers in addition to the HTTP/1.1 `Host: api.github.com` generated from the literal URL:

```http
Accept: application/vnd.github+json
Accept-Encoding: identity
Cache-Control: no-cache
Pragma: no-cache
X-GitHub-Api-Version: 2026-03-10
User-Agent: erpai-gl-tb-e2b1-readonly/1.0
```

There is no request body. `Authorization`, `Cookie`, `Proxy-Authorization`, `If-None-Match`, `If-Modified-Since`, client-certificate and private-resource headers are prohibited. The empty header overrides in the candidate command are defensive removals and must result in those headers being absent on the wire.

### 8.2 Commit-object command candidate

The future controller creates a fresh private attempt directory before invoking this candidate. `<CONNECT_TIMEOUT_SECONDS>` and `<TOTAL_TIMEOUT_SECONDS>` are deliberately unresolved and make the command non-executable until later Owner approval.

```bash
/usr/bin/env -i LC_ALL=C TZ=UTC '<ACCEPTED_CURL_LITERAL>' --disable --silent --show-error --fail-with-body --request GET --http1.1 --proto '=https' --tlsv1.2 --proxy '' --no-netrc --disallow-username-in-url --max-redirs 0 --connect-timeout '<CONNECT_TIMEOUT_SECONDS>' --max-time '<TOTAL_TIMEOUT_SECONDS>' --header 'Authorization:' --header 'Cookie:' --header 'Proxy-Authorization:' --header 'Accept: application/vnd.github+json' --header 'Accept-Encoding: identity' --header 'Cache-Control: no-cache' --header 'Pragma: no-cache' --header 'X-GitHub-Api-Version: 2026-03-10' --user-agent 'erpai-gl-tb-e2b1-readonly/1.0' --dump-header '<ATTEMPT_DIR>/commit.headers.part' --output '<ATTEMPT_DIR>/commit.body.part' --write-out 'exitcode=%{exitcode}\nresponse_code=%{response_code}\nmethod=%{method}\nscheme=%{scheme}\nurl_effective=%{url_effective}\nnum_redirects=%{num_redirects}\nredirect_url=%{redirect_url}\nhttp_version=%{http_version}\nssl_verify_result=%{ssl_verify_result}\nsize_download=%{size_download}\ncontent_type=%{content_type}\n' --url 'https://api.github.com/repos/MariaDB/server/git/commits/197f92bee02d8e836f529f37625be69b83e7acbd'
```

### 8.3 Recursive-tree command candidate

Only a root SHA that passed the commit schema and equality checks may replace `<ACCEPTED_ROOT_TREE_SHA>`. It is not taken from a response URL.

```bash
/usr/bin/env -i LC_ALL=C TZ=UTC '<ACCEPTED_CURL_LITERAL>' --disable --silent --show-error --fail-with-body --request GET --http1.1 --proto '=https' --tlsv1.2 --proxy '' --no-netrc --disallow-username-in-url --max-redirs 0 --connect-timeout '<CONNECT_TIMEOUT_SECONDS>' --max-time '<TOTAL_TIMEOUT_SECONDS>' --header 'Authorization:' --header 'Cookie:' --header 'Proxy-Authorization:' --header 'Accept: application/vnd.github+json' --header 'Accept-Encoding: identity' --header 'Cache-Control: no-cache' --header 'Pragma: no-cache' --header 'X-GitHub-Api-Version: 2026-03-10' --user-agent 'erpai-gl-tb-e2b1-readonly/1.0' --dump-header '<ATTEMPT_DIR>/tree.headers.part' --output '<ATTEMPT_DIR>/tree.body.part' --write-out 'exitcode=%{exitcode}\nresponse_code=%{response_code}\nmethod=%{method}\nscheme=%{scheme}\nurl_effective=%{url_effective}\nnum_redirects=%{num_redirects}\nredirect_url=%{redirect_url}\nhttp_version=%{http_version}\nssl_verify_result=%{ssl_verify_result}\nsize_download=%{size_download}\ncontent_type=%{content_type}\n' --url 'https://api.github.com/repos/MariaDB/server/git/trees/<ACCEPTED_ROOT_TREE_SHA>?recursive=1'
```

The transport stdout contract is exactly the eleven labeled LF-terminated write-out lines, in the shown order, with no other byte. Success stderr is empty. The body is never written to stdout. A write-out error, malformed/duplicate label, missing line, extra line, nonzero process exit, stderr byte or mismatch between `size_download` and saved body bytes stops.

The controller must validate `exitcode=0`, `response_code=200`, `method=GET`, `scheme=https`, the exact literal effective URL, `num_redirects=0`, empty `redirect_url`, `http_version=1.1`, `ssl_verify_result=0`, matching byte count and accepted content type. `--fail-with-body` may leave an error body; any such file remains quarantine-only and is discarded.

## 9. Response-header policy

Header names are compared case-insensitively. Critical header duplicates or comma-joining ambiguity stop. The header file is quarantine-only and is not promoted.

### 9.1 Required and validated

- exactly one final HTTP response block with status `200`;
- `Content-Type` with base media type exactly `application/json`; the only permitted parameter is an optional case-insensitive `charset=utf-8`;
- exactly one `X-GitHub-Api-Version-Selected: 2026-03-10`; absence is an API-selection ambiguity and stops;
- `Content-Encoding` absent or exactly `identity`;
- `Content-Length`, when present, a nonnegative decimal equal to saved entity-body bytes;
- effective URL, scheme, method, redirect count and TLS verification matching the write-out contract; and
- no `Link` or cursor/pagination behavior.

The required selected-version header is deliberately fail-closed even though GitHub documentation does not promise a complete raw header set. If GitHub omits it, acquisition stops for a new evidence decision rather than inferring version selection.

### 9.2 Retained

Only normalized classification facts are retained: request kind (`commit` or `recursive_tree`), method, exact status, exact effective URL classification without credentials, zero redirects, normalized content type, selected API version, response-body byte count, response-body SHA-256, transport-binary binding, attempt ID, owner and UTC time. Raw header values are not promoted.

### 9.3 Permitted but not retained

Normal unrelated GitHub/CDN infrastructure headers may be validated syntactically and then discarded, including `Date`, `Server`, `ETag`, `Last-Modified`, `Cache-Control`, `Expires`, `Age`, `Vary`, `Accept-Ranges`, `Transfer-Encoding`, `X-GitHub-Media-Type`, `X-GitHub-Request-Id`, `X-RateLimit-*`, `X-Accepted-OAuth-Scopes`, CORS headers and browser-security headers. A cache hit does not change evidence meaning because the request is bound to immutable Git object IDs, sends no conditional validator and must return a complete `200` entity body whose bytes are hashed.

GitHub's official OpenAPI repository states that not every response header is described, and its versioning policy permits additive headers. Therefore an otherwise unrelated unknown header is safely ignored and not retained; the raw JSON body remains subject to strict unknown-field rejection.

### 9.4 Prohibited

Any of the following stops and discards the attempt:

- `Location`, `Link`, `Content-Range`, `Retry-After`, `Warning`, `Deprecation` or `Sunset`;
- `Set-Cookie`, `WWW-Authenticate`, `Proxy-Authenticate`, `X-OAuth-Scopes`, `X-OAuth-Client-Id` or `X-GitHub-SSO`;
- nonidentity content encoding;
- a redirect response, conditional `304`, authentication challenge, rate-limit response, partial-content response or non-`200` status; or
- any URL userinfo, credential, token, cookie or request-ID promotion.

## 10. Commit-response raw JSON schema

The exact observation-date allowlist for the commit response is one UTF-8 JSON object with these required top-level members and no others:

| Member | Type | Nested contract |
| --- | --- | --- |
| `sha` | string | exactly the requested 40-character lowercase hexadecimal commit ID |
| `node_id` | string | parsed, not retained |
| `url` | string | credential-free HTTPS URL; parsed, not followed or retained |
| `html_url` | string | credential-free HTTPS URL; parsed, not followed or retained |
| `author` | object | exactly `date`, `name`, `email`, each string |
| `committer` | object | exactly `date`, `name`, `email`, each string |
| `message` | string | parsed, not retained |
| `tree` | object | exactly `url` string and `sha` string |
| `parents` | array | each element exactly `url`, `sha`, `html_url`, all strings |
| `verification` | object | exact schema below |

`author.date` and `committer.date` must be valid RFC 3339 date-time strings. Every parent SHA and `tree.sha` is exactly 40 lowercase hexadecimal characters. The returned top-level SHA must equal `197f92bee02d8e836f529f37625be69b83e7acbd`. Exactly one non-null `tree.sha` is extracted.

The `verification` object has exactly:

- `verified`: Boolean;
- `reason`: one of `expired_key`, `not_signing_key`, `gpgverify_error`, `gpgverify_unavailable`, `unsigned`, `unknown_signature_type`, `no_user`, `unverified_email`, `bad_email`, `unknown_key`, `malformed_signature`, `invalid`, `valid`;
- `signature`: string or JSON `null`;
- `payload`: string or JSON `null`; and
- `verified_at`: RFC 3339 date-time string or JSON `null`.

The parser rejects a BOM, invalid UTF-8, duplicate JSON keys at any depth, trailing bytes after the single JSON value, a missing member, unknown member, null where not permitted, wrong type, malformed SHA/date/URL, credential-bearing URL or equality mismatch. GitHub's API-version policy permits additive response fields, so a legitimate future additive field will intentionally cause this observation-date contract to stop for review.

The commit response projection retains only `commit_sha` and `root_tree_sha` plus its classification and response-body SHA-256. Author/committer names and emails, message, signatures, payload, parents, node ID, URLs and GitHub request ID are parsed only for schema/transport safety and discarded.

## 11. Recursive-tree raw JSON schema

The exact observation-date allowlist is one UTF-8 JSON object with these required top-level members and no others:

| Member | Type | Rule |
| --- | --- | --- |
| `sha` | string | exactly the accepted root-tree SHA |
| `url` | string | credential-free HTTPS; parsed, not followed or retained |
| `tree` | array | complete entry array governed below |
| `truncated` | Boolean | required and exactly `false` |

Every `tree` entry contains exactly these members, except that `size` is optional:

| Member | Type | Rule |
| --- | --- | --- |
| `path` | string | safe relative ASCII path contract below |
| `mode` | string enum | `100644`, `100755`, `040000`, `160000` or `120000` |
| `type` | string enum | `blob`, `tree` or `commit` |
| `size` | nonnegative integer, optional | permitted only for `blob`; parsed and discarded |
| `sha` | string | 40 lowercase hexadecimal Git object ID |
| `url` | string | credential-free HTTPS; parsed, not followed or retained |

Permitted mode/type pairs are:

- `100644` + `blob`;
- `100755` + `blob`;
- `120000` + `blob` for a symlink object;
- `040000` + `tree`; and
- `160000` + `commit` for a submodule entry.

Candidate source paths may use only `100644` or `100755` regular blobs. Symlinks, trees and submodules remain in the hashed inventory but cannot become E2-B2 candidates.

### 11.1 Path encoding and ambiguity rejection

Each path must be nonempty and match this complete portable ASCII grammar:

```text
[A-Za-z0-9._+@%=-]+(?:/[A-Za-z0-9._+@%=-]+)*
```

No decoding, Unicode normalization, case folding, percent decoding or separator conversion is performed. The grammar itself rejects absolute paths, leading/trailing/repeated slash, backslash, NUL/control/DEL, whitespace, drive letters, empty segments and non-ASCII normalization ambiguity. A segment equal to `.` or `..` is separately rejected. Exact duplicate paths, ASCII-lowercase collisions, conflicting mode/type/object identities or duplicate complete sort tuples stop the whole acquisition.

The top-level SHA must equal the accepted root-tree SHA. `truncated` missing, null, non-Boolean or true stops. `Link`, cursor, pagination, partial array or error envelope stops. GitHub's documented recursive-tree truncation advice does not authorize a nonrecursive fallback here.

## 12. Candidate-path extraction and output boundary

Candidate classification is deterministic and path-only. It does not infer MariaDB semantics. An entry is eligible only when all are true:

1. mode/type is `100644`/`blob` or `100755`/`blob`;
2. the path starts with `sql/`, `include/`, `storage/innobase/` or `storage/perfschema/`;
3. the final name ends with `.c`, `.cc`, `.cpp`, `.h`, `.hh`, `.hpp`, `.ic`, `.l`, `.y`, `.yy` or `.sql`; and
4. the ASCII-lowercased path contains at least one category token below.

| Category | Exact case-insensitive path tokens |
| --- | --- |
| `Q1_ACCOUNT_HOST_MATCH` | `sql_acl`, `acl`, `auth`, `privilege`, `grant` |
| `Q2_TABLE_COLUMN_GRANT` | `column_priv`, `table_priv`, `grant`, `privilege` |
| `Q3_PROCESS_VISIBILITY` | `processlist` |
| `Q4_EXACT_CONNECTION_TERMINATION` | `sql_kill`, `kill`, `connection` |
| `Q5_INNODB_TRX_VISIBILITY` | `innodb_trx`, `trx0trx` |
| `Q6_ISOLATION_READ_ONLY_SNAPSHOT` | `isolation`, `consistent_snapshot`, `read_only` |
| `Q7_REPLICA_TOPOLOGY_PRIVILEGE` | `replica`, `replication`, `slave`, `master_info` |
| `Q8_STATEMENT_TIMEOUT` | `max_statement_time`, `statement_timeout` |

A candidate receives every matching category in Q1-Q8 order. Multiple matches are not semantic proof and are not resolved automatically. Only a path satisfying every eligibility predicate may be promoted with its identity. A strong-token match with an ineligible prefix, suffix, mode or type remains controlled inventory; the sanitized receipt may retain only aggregate counts by `prefix_rejected`, `suffix_rejected` or `nonregular_blob_rejected` and a SHA-256 over the controlled rejected-tuple set. It must not expose those rejected paths or object IDs. Any path ambiguity governed by Section 11.1 stops the entire acquisition and may produce only the stop enum `path_ambiguous_rejected`, never a path identity or partial candidate receipt. Paths with no strong token are unrelated and are not promoted individually.

The future E2-B1 receipt may promote only:

- exact commit SHA and root-tree SHA;
- request/response classifications;
- commit and tree response-body SHA-256 values;
- `truncated=false`;
- projected-inventory SHA-256;
- candidate paths with mode, type, Git object SHA and assigned category list; and
- aggregate rejection counts/reasons and an ambiguity stop enum as allowed above, without rejected or ambiguous path identities.

It must not promote source bytes, repository-wide path lists, author or committer identity, emails, commit message, signatures, parent metadata, unrelated paths, URLs with credentials, tokens, cookies, GitHub request IDs, runtime conclusions, permission/grant conclusions or accounting semantics. If any Q category has no candidate, or the metadata-only candidate set cannot be justified for Owner review, E2-B1 stops without a content request.

E2-B2 remains a new Owner decision for each literal candidate path and object SHA. It may not follow a returned blob URL automatically.

## 13. Canonical projections and hashing

The two response-body hashes are SHA-256 over the exact entity-body bytes written by curl to `*.body.part` after HTTP transfer framing is removed. Because `Accept-Encoding: identity` is required and nonidentity response encoding stops, no content decompression boundary is admitted. These values are named `commit_response_body_sha256` and `tree_response_body_sha256`; they are not called raw HTTP wire hashes.

The commit projection is compact UTF-8 JSON with keys in this exact order and no additional member:

```json
{"commit_sha":"197f92bee02d8e836f529f37625be69b83e7acbd","root_tree_sha":"<ACCEPTED_ROOT_TREE_SHA>"}
```

The inventory projection is one compact UTF-8 JSON object with keys in exact order `commit_sha`, `root_tree_sha`, `truncated`, `entries`. Every entry has keys in exact order `path`, `mode`, `type`, `object_sha`. Entries include every valid tree entry and are sorted by unsigned UTF-8 bytes of `path`, then `mode`, `type` and `object_sha`.

```json
{"commit_sha":"197f92bee02d8e836f529f37625be69b83e7acbd","root_tree_sha":"<ACCEPTED_ROOT_TREE_SHA>","truncated":false,"entries":[{"path":"<PATH>","mode":"<MODE>","type":"<TYPE>","object_sha":"<GIT_OBJECT_SHA>"}]}
```

Serialization rules are:

- UTF-8 only, no BOM;
- no insignificant whitespace and no trailing newline;
- quotation mark and reverse solidus escaped as `\"` and `\\`;
- standard two-character escapes for backspace, tab, LF, form feed and carriage return;
- remaining U+0000-U+001F controls, if ever present outside the path contract, escaped as lowercase `\u00xx`;
- solidus not escaped;
- no Unicode normalization; and
- duplicate keys, duplicate paths or non-I-JSON values rejected before serialization.

`commit_projection_sha256` and `projected_inventory_sha256` are SHA-256 over exactly those canonical bytes. The controller must hash each saved body immediately after close, rehash before projection promotion and require equality. The parser/canonicalizer source and runtime identity are prerequisites; an ad hoc local script or unbound JSON tool is prohibited.

## 14. Temporary files, atomic promotion and discard

The future controller, if separately authored and approved, owns all acquisition state. It must create one fresh, private, symlink-free attempt directory under an Owner-approved disposable evidence root with directory mode `0700`, file mode `0600`, same evidence-owner UID and exclusive-create/no-follow semantics.

The only temporary basenames are:

- `commit.headers.part`;
- `commit.body.part`;
- `commit.stdout.part`;
- `commit.stderr.part`;
- `tree.headers.part`;
- `tree.body.part`;
- `tree.stdout.part`;
- `tree.stderr.part`;
- `commit.projection.part`;
- `inventory.projection.part`; and
- `receipt.part`.

The commit response is nonterminal. No evidence is promoted until both requests, all header/body/schema/equality/path checks, both body hashes, both canonical projections and candidate classification succeed. Promotion is one atomic rename of a sanitized receipt and its projection hashes inside the same filesystem. Raw headers, response bodies and transport stdout/stderr remain quarantine-only. They may be removed only by a later frozen exact-ID teardown protocol after accepted projection or failure. Because the retention window, removal operation and recovery behavior are not frozen here, this document makes no teardown proof and no acquisition may begin until the controller gate closes that prerequisite. No author identity, message, signature or request ID survives promotion.

A killed, timed-out, interrupted, partial or otherwise incomplete attempt is discard-only. A retry never resumes a response and never reuses a part file or attempt directory. It requires a fresh attempt ID and a separately recorded approval/disposition. There is no automatic retry, changed parameter, authentication fallback, redirect follow, nonrecursive traversal or alternate endpoint.

## 15. Failure and recovery matrix

| Failure | Required result |
| --- | --- |
| helper, Docker, curl, CA, parser or controller provenance missing/drifted | stop before request/use; discard dependents |
| DNS, TCP, TLS or certificate validation failure | stop; no insecure or alternate-host fallback |
| curl nonzero, stderr byte or malformed sidecar | discard whole attempt |
| redirect, wrong URL, method, scheme, status or content type | discard whole attempt |
| API selected-version absent/mismatch | discard; new planning decision required |
| authentication/cookie/proxy credential indication | discard and security review; no token fallback |
| response schema/duplicate-key/type drift | discard; observation-date schema review required |
| commit or root-tree mismatch | discard; do not change commit/ref |
| missing/true `truncated`, `Link`, cursor or partial response | discard; no traversal fallback |
| invalid, duplicate, conflicting or ambiguous path | discard whole tree projection |
| parser, canonicalization, body/projection hash mismatch | discard whole attempt |
| timeout or external watchdog kill | discard all parts; exact-ID teardown only |
| interruption or controller recovery | treat all `.part` files as invalid; never promote |
| any need for source/blob content | stop for E2-B2 Owner allowlist |

No failure may be converted into partial evidence. The only recovery action is exact-attempt quarantine removal by the future evidence owner. It grants no general cleanup authority.

## 16. Later timeout, retry and byte-ceiling derivation

No numeric timeout, retry, response-byte or workload limit is selected here. This document authorizes zero calibration requests. Before acquisition, a separately approved preflight must:

1. bind curl, TLS backend, CA source, parser/controller and host-watchdog provenance;
2. have the Owner choose either non-request derivation from already accepted host/network service objectives and authoritative product response constraints, or a separate calibration amendment;
3. if calibration traffic is chosen, enumerate and approve every URL, method and request count as a distinct metadata-acquisition package that explicitly supersedes the two-request boundary for calibration only; no calibration GET may occur under this document;
4. capture only DNS/connect/TLS, time-to-first-byte, total-transfer and entity-byte observations in discard-only quarantine, without promoting Git metadata or semantic evidence;
5. have the Owner select the statistic, safety multiplier, minimum/maximum ceiling and watchdog margin;
6. derive separate connect, total-request and external-watchdog values and a response-byte ceiling;
7. freeze the derived literals and their evidence/hash in a new command manifest; and
8. obtain explicit Owner approval before the actual E2-B1 acquisition, which remains exactly the two GETs in Section 8.

Retry count remains zero unless a later Owner decision selects a bounded value and failure classes. Even then, every retry is a new attempt with no partial reuse. This methodology is approved only as a derivation path; no number is approved by this document.

## 17. Preserved dependency graph

- Corrected E1 and E2-B1 may later run independently and in parallel only after their distinct prerequisites and Owner execution gates close.
- E3-B1 may proceed separately using only already approved static inputs and its own future Owner gate.
- E2-B2 waits for an accepted E2-B1 receipt and Owner approval of every literal path, object SHA and Q1-Q8 mapping.
- E3-B2 waits for installed-Python identity and exact CPython source approval.
- E3-B4 waits for the S07 source/schema allowlist.
- E3-B5 waits for accepted E2-B2 semantic evidence.
- E3-B3 remains the final static synthesis after all required predecessor receipts.
- E4 and Four-File Source Authoring remain later Owner decisions; neither may be inferred from this wire-contract document.

No package may broaden another package's files, runtime ownership, permissions or evidence meaning.

## 18. Bounded review and Main Control synthesis

One bounded review pass was used; no open-ended review loop was started.

### 18.1 Accounting-boundary preservation

Accepted: E1 is image metadata only and E2-B1 is Git metadata only. Neither can make a GL/TB, accounting equation, cancellation, close/reopen, frozen-period, audit, grant, company/currency/book/dimension, runtime or execution claim. `gl_reconstructed` remains the sole synthetic proof candidate, and Finance Cycle 2 runtime work remains unstarted.

### 18.2 Security and leakage

Accepted: the commands use literal binaries, clean inputs, no credentials, exact endpoints, no redirect/fallback, body quarantine, identity suppression and sanitized promotion. Strict JSON drift rejection and path ambiguity rejection are fail-closed. Commit identity, email, message, signature and request ID are never promoted.

Accepted with stop: Docker endpoint/context, optional-value acceptance, curl/CA identity, parser/controller identity and transport ceilings are not inferred. Their absence prevents execution.

### 18.3 HTTP/database evidence classification

Accepted: E2-B1 uses public GitHub metadata and is not MariaDB source-semantic, database, grant or runtime evidence. E1 uses local Docker image metadata and is not image-digest, database or runtime proof. No SQL, database connection, topology, transaction, snapshot, reconnect or permission evidence is acquired. This public GitHub policy is unrelated to the deferred Finance HTTP endpoint and global CORS gate.

### 18.4 Release/governance containment

Accepted: this gate changes only its canonical document and README. It authorizes no command, API request, source read, runtime source, harness/controller/Dockerfile/initializer edit, image/container action, infrastructure, secret, test, SQL, live action, stage, commit, push, migration, permission change, protected gate or accounting action.

### 18.5 Main Control synthesis

The schemas, projections and safe failure posture are coherent, but the exact executable wire package is not closed. Main Control accepts the conservative contracts and records the concrete prerequisites as Blockers rather than making unsupported host, Docker or curl assumptions. The decision is therefore `stopped_for_wire_contract_gap`.

Reviewer disposition after the single synthesis:

- accepted and incorporated: only fully eligible candidate path identities may be promoted; rejected path identities remain controlled; ambiguous paths stop; calibration traffic requires a separate Owner amendment; README now names helper and parser/controller provenance; quarantine teardown and immutable OpenAPI binding remain explicit prerequisites;
- rejected as active High: additive GitHub fields, unrelated infrastructure headers and corrected entity-body naming are availability/classification matters under fail-closed controls, not current security defects; and
- deferred: helper/curl/CA fingerprinting, Docker endpoint/config choice, optional-value allowlist, parser/controller source and runtime, numeric ceilings, stronger atomic executable binding, acquisition, E2-B2, E3-B, E4, source authoring and runtime/accounting actions.

## 19. Findings by severity and disposition

### 19.1 Blocker — accepted

| Finding | Concrete evidence | Disposition |
| --- | --- | --- |
| helper behavior is cited but installed helper provenance is absent | the controlling prerequisite amendment expressly says `/bin/bash` and `/usr/bin/realpath` were not proven; this gate did not execute or inspect them | bind exact helper paths/stat/SHA/version before E1 |
| supplied Docker image command does not bind daemon/context/config | Docker CLI context and environment can select the daemon; no controlling receipt freezes that selection | Owner must approve an explicit endpoint/config posture or context fingerprint |
| curl/TLS/CA and selected option support are unproven | no curl path/version/feature/CA preflight exists; official curl docs do not prove installed behavior | separate read-only fixed-output provenance gate |
| no approved transport ceilings exist | the Owner prohibits invented numeric limits and no derived values are published | later calibration methodology plus Owner literals required |
| parser/controller provenance is absent | the future controller source remains absent and no approved parser runtime exists | later source-authoring/compatibility gate before acquisition |

### 19.2 High — accepted containment

- Positions 5-9 lack an approved non-null value allowlist. Any non-null result stops; it cannot silently enter evidence.
- Pre/post stat and SHA checks do not prove atomic no-swap immutability. No stronger claim is made.

### 19.3 Medium — deferred

- The conservative repository-digest prefix rule is not a complete Docker-reference parser. A valid value outside it stops for review.
- Path-only category tokens may be incomplete or overinclusive. They create candidates only; missing Q coverage stops and no semantic fact is inferred.
- The ASCII path grammar is intentionally narrower than Git. A valid non-ASCII upstream path would stop rather than be normalized.
- GitHub may add response fields under a supported API version. Strict unknown-field rejection may stop on legitimate additive drift; this is intentional availability containment rather than a current security defect.
- GitHub does not publish a complete response-header schema. Critical headers are frozen; unrelated headers are ignored and not retained.
- Curl output hashes entity-body bytes, not HTTP transfer framing. The corrected evidence names resolve that classification issue.
- The current OpenAPI discovery link is mutable. Any later use as compatibility evidence requires an immutable upstream commit and file hash.
- Exact quarantine retention, removal and recovery remain part of the deferred controller/teardown contract; private mode alone is not teardown proof.

### 19.4 Rejected

Rejected: ambient Docker context acceptance; guessed helper/curl path; inherited curl configuration or proxy; authentication fallback; redirects; alternate API versions; pagination; nonrecursive fallback; repository/branch/search enumeration; blob or source reads; raw image objects; partial evidence promotion; Git object IDs labeled as SHA-256; path names treated as semantics; automatic retry; invented timeouts; digest approval; runtime, grant or accounting conclusions; and automatic progression to E2-B2, E3-B, E4 or source authoring.

## 20. Owner decisions needed to close the stop

A later planning gate must decide, without implying execution:

1. the Docker daemon/context/config binding compatible with the exact image command, or an amended exact argument vector;
2. exact accepted non-null values for positions 5-9, or confirmation that every non-null result must remain a stop;
3. the helper and curl provenance acquisition allowlists, including CA trust-source proof;
4. the parser/controller authoring and runtime identity needed to enforce these schemas;
5. the calibration inputs and later derived connect/request/watchdog/byte ceilings; and
6. whether the frozen lexical candidate predicates are accepted for E2-B1 Owner-review output.

Only after those decisions are documented may the Owner consider a corrected E1/E2-B1 read-only acquisition gate. E2-B2 remains separately approved after candidate identities exist.

## 21. Validation and future documentation staging allowlist

The documentation gate validates:

- source root `/home/deploy/erp-projects/erpai_project1_erpnext_ui_design`;
- branch `feature/erpnext-ui-design`;
- local HEAD and configured upstream both `53cee0d91ce268b8188ccdfe1e556a62ce30b797` at gate start;
- ahead/behind `0/0` and empty index at gate start;
- worktree candidates limited to this document and README, alongside the unchanged harness and four protected exclusions;
- `git diff --check HEAD` and Markdown whitespace/reference checks after writing;
- exactly one README link to this document;
- unchanged harness SHA-256 `c8d0bb0556f9abb04e1be69c1d67a7f92c4ed37a64d8270d84339ad590e9cea5`;
- absent controller, runner Dockerfile and initializer;
- unchanged protected exclusions; and
- no command/API/source/runtime/live/staging authority created.

The exact future documentation staging allowlist, if separately authorized, is:

1. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/finance-accounting-cycle2-gl-tb-corrected-e1-e2b1-wire-contract-freeze-2026-07-19.md`
2. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/README.md`

This document does not authorize staging, commit or push.

## 22. Final control statement

**Decision:** `stopped_for_wire_contract_gap`

The corrected E1 path, identity and eleven-field schemas and the E2-B1 request, response, projection and failure contracts are frozen as planning candidates. The exact executable package remains stopped on the concrete helper, Docker endpoint, optional-value, curl/CA, timeout and parser/controller prerequisites listed above.

No corrected E1 command, GitHub API request, MariaDB source-content read, E2-B1, E2-B2, E3-B or E4 execution occurred. No source authoring, image/container action, infrastructure, secret, test, Frappe, Bench, SQL, synthetic execution, live access, staging, commit, push, migration, permission change, protected gate or accounting action occurred.
