# Finance & Accounting Cycle 2 GL / Trial Balance Toolchain, Docker Endpoint and Parser Provenance Gate

Date: 2026-07-19

Repository: `/home/deploy/erp-projects/erpai_project1_erpnext_ui_design`

Branch: `feature/erpnext-ui-design`

Published baseline: `240851e804e0f119f27847be63c117f08cb89d9d`

Authority: Main Control v2; bounded read-only host/tool provenance only

Decision: `stopped_for_toolchain_provenance_gap`

## 1. Outcome and controlling effect

This gate completed bounded read-only provenance for the four Owner-authorized bootstrap binaries and direct pre/post identity checks for the observed Docker and curl literals. It also recorded the client-selected Docker context/endpoint tuple and applied the exact frozen path helper to the sole approved parser candidate. That helper observed no `jq` in `/usr/local/bin:/usr/bin`, but every helper-dependent selection remains provisional because `/usr/bin/env`, an exact helper dependency, was outside the authorized fingerprint list.

The gate therefore stops. Corrected E1 has useful Docker/tool observations but does not yet have unconditional clean-helper or daemon/socket identity provenance. E2-B1 is not ready because no parser is accepted; curl CA provenance, loaded-library identity, one negated option and the eleven write-out variables also remain unbound. No fallback parser is permitted.

The following did not occur: corrected image inspection, a curl transfer, GitHub/API traffic, MariaDB source-content access, E2-B1, E2-B2, E3-B, E4, source authoring, a Docker workload or any live/operational-data action.

## 2. Published baseline and authority

The controlling records are:

- [E1/E2-A/E3-A Read-Only Evidence Acquisition](finance-accounting-cycle2-gl-tb-e1-e2a-e3a-read-only-evidence-acquisition-2026-07-18.md);
- [E1 Fixed-Output Correction and E2-B/E3-B Prerequisite Freeze Amendment](finance-accounting-cycle2-gl-tb-e1-fixed-output-e2b-e3b-prerequisite-freeze-amendment-2026-07-19.md);
- [Corrected E1 and E2-B1 Wire-Contract Freeze](finance-accounting-cycle2-gl-tb-corrected-e1-e2b1-wire-contract-freeze-2026-07-19.md); and
- the Owner continuity direction accepted when the wire-contract stop was published.

The verified gate-start repository state was:

| Fact | Verified value |
| --- | --- |
| root | `/home/deploy/erp-projects/erpai_project1_erpnext_ui_design` |
| branch | `feature/erpnext-ui-design` |
| HEAD | `240851e804e0f119f27847be63c117f08cb89d9d` |
| upstream | `origin/feature/erpnext-ui-design` at the same revision |
| ahead/behind | `0/0` |
| index | empty |
| worktree | unchanged harness and four protected exclusions only |

This task authorized tool fingerprints and minimal current Docker endpoint metadata. It did not inherit the previous publication authority and creates no staging, commit, push, runtime, source-read, image-inspection or accounting authority.

## 3. Owner decisions incorporated

| Decision | Effect in this gate |
| --- | --- |
| residual binary-swap risk | pre/post canonical path, stat tuple and SHA-256 equality are accepted as sufficient for this read-only gate; atomic no-swap proof is not required and remains an accepted residual High |
| Docker optional values | future image positions 5-9 may be `null` or a structurally valid documented type; exact observations may be retained for later review but are not compatibility approval |
| additive GitHub fields | a future parser may ignore additive unretained members after required retained fields/types validate; missing, duplicate, changed-type or conflicting required members remain fail-closed |
| parser | `jq` is the sole candidate; absence or unsuitable provenance stops with no Python, Node, custom-parser or silent fallback |
| transport ceilings | future connection ceiling `30` seconds, total request ceiling `300` seconds and zero automatic retries; these are transport safety ceilings, not Finance workload/performance limits |
| Docker endpoint | retain only effective context, endpoint URI/scheme, TLS-skip fact, clean override absence, Docker binary identity and comparison to published product facts |
| limited controller | the later E2-B1 controller candidate remains the exact Bash/curl/jq command envelope; no new E2-B1 controller source is required or authorized |

No calibration request was made or authorized.

## 4. Exact permitted command inventory

Only the following evidence-command classes were used. Repository baseline/hash checks are documentation controls, not product evidence.

### 4.1 Bootstrap identity commands

For each fixed literal `/bin/bash`, `/usr/bin/realpath`, `/usr/bin/stat` and `/usr/bin/sha256sum`:

```text
/usr/bin/realpath --canonicalize-existing --physical -- <FIXED_LITERAL>
LC_ALL=C /usr/bin/stat --dereference --printf='%d|%i|%f|%a|%u|%g|%s|%Y|%Z\n' -- <CANONICAL_LITERAL>
LC_ALL=C /usr/bin/sha256sum --binary -- <CANONICAL_LITERAL>
```

The relevant literal version command was then run, followed by the same stat and SHA-256 commands. No directory or PATH enumeration occurred.

### 4.2 Frozen path helper

The exact published helper was used independently with the fixed command name `docker`, `curl` or `jq`:

```bash
/usr/bin/env -i PATH=/usr/local/bin:/usr/bin LC_ALL=C BASH_ENV=/dev/null ENV=/dev/null /bin/bash --noprofile --norc -p -c '
exec 2>/dev/null
kind=$(builtin type -t <FIXED_TOOL_NAME>) || exit 41
[[ "$kind" == file ]] || exit 42
hits=()
builtin mapfile -t hits < <(builtin type -ap <FIXED_TOOL_NAME>) || exit 43
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

`<FIXED_TOOL_NAME>` represents literal textual substitution before execution, not a runtime variable. Successful helper bytes were transported over stdin to the already fingerprinted `/bin/bash --noprofile --norc -p -s` only to avoid Windows SSH quoting changes. No file or custom launcher was created.

### 4.3 Docker fixed metadata commands

After `DOCKER_HOST`, `DOCKER_CONTEXT` and `DOCKER_CONFIG` were unset and their absence was verified without retaining values:

```text
/usr/bin/docker version --format '{{json .Client.Version}}|{{json .Client.APIVersion}}|{{json .Client.GitCommit}}|{{json .Client.GoVersion}}|{{json .Client.Os}}|{{json .Client.Arch}}|{{json .Client.BuildTime}}|{{json .Server.Version}}|{{json .Server.APIVersion}}|{{json .Server.MinAPIVersion}}|{{json .Server.GitCommit}}|{{json .Server.GoVersion}}|{{json .Server.Os}}|{{json .Server.Arch}}|{{json .Server.BuildTime}}|{{json .Server.Experimental}}'
/usr/bin/docker context show
/usr/bin/docker context inspect --format '{{json .Name}}|{{json .Endpoints.docker.Host}}|{{json .Endpoints.docker.SkipTLSVerify}}'
```

No context list/enumeration, image/container/network/volume inspect or Docker mutation command was run.

### 4.4 curl and jq commands

The curl evidence commands were limited to:

```text
/usr/bin/curl --version
/usr/bin/curl --help all
/usr/bin/curl --manual
```

They performed no transfer. The manual/help observations were retained only as option/variable presence classifications. The `jq` lane ended at helper exit `41`; no jq version or JSON parse command was possible.

## 5. Bootstrap tool fingerprints

The stat tuple order is `device|inode|raw_mode|permissions|uid|gid|bytes|mtime|ctime`.

| Supplied literal | Canonical literal | Pre/post stat tuple | SHA-256 | Exact version/build line | Result |
| --- | --- | --- | --- | --- | --- |
| `/bin/bash` | `/usr/bin/bash` | `64513|1559|81ed|755|0|0|1396520|1710415907|1719848457` | `59474588a312b6b6e73e5a42a59bf71e62b55416b6c9d5e4a6e1c630c2a9ecd4` | `GNU bash, version 5.1.16(1)-release (x86_64-pc-linux-gnu)` | pass |
| `/usr/bin/realpath` | `/usr/bin/realpath` | `64513|1817|81ed|755|0|0|39336|1707363999|1719848457` | `79ecae9071edc0253ba3e17cf2e9883b1ed18bba1b7f355774df231cc409fbea` | `realpath (GNU coreutils) 8.32` | pass |
| `/usr/bin/stat` | `/usr/bin/stat` | `64513|1829|81ed|755|0|0|80400|1707363999|1719848457` | `9b571b54bd2f17f5fbb841e1886c2d364f5138a02533f4ac3dbfbdaf4dddbea3` | `stat (GNU coreutils) 8.32` | pass |
| `/usr/bin/sha256sum` | `/usr/bin/sha256sum` | `64513|1822|81ed|755|0|0|51624|1707363999|1719848457` | `7645c8e76d75515ccb75c9086bdcf0d4071f2985f380f249253ead7d7c6810b3` | `sha256sum (GNU coreutils) 8.32` | pass |

Every raw mode was `81ed`, every permission mode was `755`, owner/group were numeric `0/0`, and each target was a regular executable file. Pre/post stat and SHA-256 records were byte-identical and command stderr was empty. No observed drift occurred.

The Owner accepts the remaining non-atomic swap risk as a residual High under the single-owner, read-only gate. No atomic-immutability claim is made.

## 6. Path-helper outcomes and discarded transport attempts

| Tool | Evidence attempt | Exit | Fixed stdout | Stderr | Disposition |
| --- | --- | --- | --- | --- | --- |
| `docker` | first Windows-argument transport | `0` | malformed `/usr/bin/dockern` | empty | discarded; no dependent use |
| `docker` | fresh LF-preserving exact helper | `0` | `/usr/bin/docker` plus LF | empty | provisional observed literal; helper chain incomplete |
| `curl` | first Windows-argument transport | `0` | malformed `/usr/bin/curln` | empty | discarded; no transfer/dependent use |
| `curl` | CRLF-corrupted stdin transport | `1` | no accepted path | empty | discarded; no transfer/dependent use |
| `curl` | fresh LF-preserving exact helper | `0` | `/usr/bin/curl` plus LF | empty | provisional observed literal; helper chain incomplete |
| `jq` | LF-preserving exact helper | `41` | empty | empty | observed no-result; no parser accepted |

The malformed suffixes were transport quoting artifacts, not accepted helper output. Fresh attempts reused no partial evidence and created no file. No malformed attempt made a network request or ran a Docker metadata command.

The exact helper also invokes `/usr/bin/env`. The explicit bootstrap fingerprint allowlist named only Bash, `realpath`, `stat` and `sha256sum`; `/usr/bin/env` was therefore not fingerprinted. Its observed execution was explicitly allowed as part of the published helper, but its independent pre/post identity remains unresolved. The helper chain is not provenance-complete. Docker/curl discovery and jq absence are provisional observations, not accepted executable bindings, and must be reacquired after `/usr/bin/env` is fingerprinted or the Owner approves a replacement construction.

## 7. Docker CLI identity and product facts

### 7.1 Binary identity

| Field | Observed value |
| --- | --- |
| canonical path | `/usr/bin/docker` |
| pre/post stat | `64513|19454|81ed|755|0|0|44015908|1770052629|1770978249` |
| SHA-256 | `2ed412480e0eca591783f1f81f3ccb1184749a8f6431960e77ada958c7b78db2` |
| classification | regular executable, mode `755`, owner/group `0/0` |
| drift | none observed; pre/post values byte-identical |

### 7.2 Exact fixed version output

The bounded fixed command returned exit `0`, empty stderr and:

```text
"29.2.1"|"1.53"|"a5c7197"|"go1.25.6"|"linux"|"amd64"|"Mon Feb  2 17:17:09 2026"|"29.2.1"|"1.53"|"1.44"|"6bc6209"|"go1.25.6"|"linux"|"amd64"|"2026-02-02T17:17:09.000000000+00:00"|false
```

| Field | Client | Server | Published comparison |
| --- | --- | --- | --- |
| version | `29.2.1` | `29.2.1` | equal |
| API | `1.53` | `1.53` | equal |
| minimum API | not emitted | `1.44` | equal |
| Git commit | `a5c7197` | `6bc6209` | equal |
| Go | `go1.25.6` | `go1.25.6` | equal |
| OS/architecture | `linux/amd64` | `linux/amd64` | equal |
| build time | `Mon Feb  2 17:17:09 2026` | `2026-02-02T17:17:09.000000000+00:00` | server exact; client instant/text equal except the published table collapsed the day-padding from two spaces to one |
| experimental | not emitted | `false` | equal |

The client build-time difference is a documentation-normalization gap, not evidence of a different instant or binary: every identity and product field otherwise matches and the binary SHA-256 is now fixed. Strict raw-text equality nevertheless remains unresolved until the Owner accepts parsed timestamp equivalence or directs a factual correction in a later document.

## 8. Docker context and endpoint facts

The accepted commands exited `0` with empty stderr. The retained result is:

| Field | Observed value | Classification |
| --- | --- | --- |
| effective context | `default` | exactly one client-selected current context name |
| inspected context identity | `default` | equals `context show` at observation time |
| endpoint URI | `unix:///var/run/docker.sock` | exactly one client-selected local Docker endpoint |
| endpoint scheme | `unix` | neither TCP nor SSH |
| `SkipTLSVerify` | `false` | raw context Boolean only |
| override posture | `DOCKER_HOST`, `DOCKER_CONTEXT`, `DOCKER_CONFIG` unset and verified absent | no override values retained |

The endpoint is an observed client-selected local Unix-socket posture. It does not authenticate the daemon, prove socket owner/mode/stability, prove disposable or non-live runtime ownership, or prove that a future command reaches the same daemon. TLS certificate/CA verification is not exercised by a Unix socket; `SkipTLSVerify=false` must not be rephrased as proof of a TLS certificate-verification session.

Before any future corrected image inspection, a separately approved fixed-output lane must bind the minimum daemon/socket identity and pre/post drift facts needed to show that the same controlled non-live endpoint is reached. This document does not select that future field allowlist or authorize the command.

No context description, credential, certificate, metadata path, alternate context, container, image, label, environment, network, volume or mount information was read or retained.

## 9. curl, TLS and CA provenance

### 9.1 Observed binary facts

Root Main Control completed the interrupted post-use identity check. Pre/post values are identical:

| Field | Observed value |
| --- | --- |
| canonical path | `/usr/bin/curl` |
| stat | `64513|23964|81ed|755|0|0|260328|1782753688|1782973071` |
| SHA-256 | `0ca2b923679ab186f6512c7512e131a1c5c1b43d4cb5d55933998405b39e85bf` |
| version line | `curl 7.81.0 (x86_64-pc-linux-gnu) libcurl/7.81.0 OpenSSL/3.0.2 zlib/1.2.11 brotli/1.0.9 zstd/1.4.8 libidn2/2.3.2 libpsl/0.21.0 (+libidn2/2.3.2) libssh/0.9.6/openssl/zlib nghttp2/1.43.0 librtmp/2.3 OpenLDAP/2.5.17` |
| release date | `2022-01-05` |

Supported protocol names emitted by the fixed version command:

```text
dict file ftp ftps gopher gophers http https imap imaps ldap ldaps mqtt pop3 pop3s rtmp rtsp scp sftp smb smbs smtp smtps telnet tftp
```

Supported feature names:

```text
alt-svc AsynchDNS brotli GSS-API HSTS HTTP2 HTTPS-proxy IDN IPv6 Kerberos Largefile libz NTLM NTLM_WB PSL SPNEGO SSL TLS-SRP UnixSockets zstd
```

The version banner labels the TLS backend/version as OpenSSL `3.0.2`. The linked-library version strings are emitted product labels only; their loaded file paths, stat/SHA identities and drift were not bound. No TLS connection was made.

### 9.2 Exact unresolved curl requirements

- `--help all` documented every frozen transfer option except the generated negated spelling `--no-netrc`; its support remains unproven rather than disproven.
- Presence of the exact eleven write-out variables could not be retained reliably from the bounded manual capture and remains unbound: `exitcode`, `response_code`, `method`, `scheme`, `url_effective`, `num_redirects`, `redirect_url`, `http_version`, `ssl_verify_result`, `size_download`, `content_type`.
- The compiled/effective default CA file or directory was not emitted by the fixed version output. No unrestricted config read, certificate read or network request was attempted. Effective CA provenance remains unresolved.
- The dynamically loaded libcurl/TLS/dependency files were not fingerprinted. The version banner does not authenticate those files or establish future runtime linkage.
- `/usr/bin/env` provenance remains unresolved as described above.

The transport ceilings are nevertheless frozen by Owner decision: connect `30` seconds, total `300` seconds and no automatic retry. These numbers are not Finance workload limits.

## 10. jq parser facts

The exact LF-preserving helper exited `41` with empty stdout and empty stderr. Under the frozen exit table, the incomplete helper chain observed no `jq` in `/usr/local/bin:/usr/bin`. Because `/usr/bin/env` is unbound, that result is not an execution-authoritative parser binding and must be reacquired after the helper chain is closed.

Consequences:

- no accepted jq literal exists;
- no jq stat, owner, mode, SHA-256 or version can be recorded;
- compact-output, sorted-key, raw-output, exit-status, invalid-JSON and duplicate-member semantics cannot be bound to an installed version;
- E2-B1 has no approved JSON parser; and
- Python, Node, a custom parser and silent fallback remain rejected.

This is a concrete Blocker: no parser has been accepted. The observed helper exit supports the no-result, while the `/usr/bin/env` qualification prevents overstating it as a complete toolchain proof. No directory enumeration occurred.

## 11. Evidence classification and prohibited inference

| Evidence class | What is established | What is not established |
| --- | --- | --- |
| bootstrap tools | fixed paths, canonical targets, identity, versions and observed pre/post stability | atomic immutability or general host trust |
| Docker CLI | direct literal binary identity and bounded client/server product fields | provenance-complete helper selection, image, container, filesystem, database or application compatibility |
| Docker endpoint | one client-selected default local Unix-socket endpoint under clean override absence | daemon/socket identity, daemon workload state, credentials, certificate use, container identity or live deployment state |
| curl | direct literal binary identity, version-banner labels, protocols/features and observed stability | loaded-library identities, effective CA provenance, all future option/write-out semantics or any HTTP/TLS request result |
| jq | provisional no-result from the incomplete helper chain | execution-authoritative absence, parser suitability or authority |
| transport ceilings | future safety bounds `30`/`300`/zero retry | Finance workload, response-size or performance acceptance |

Tool provenance does not approve corrected E1 execution, GitHub traffic, image compatibility, MariaDB source content, grants, E2-B, E3-B, E4, source authoring, permissions, live action or accounting execution.

## 12. Corrected E1 readiness

### Observed and directly bound

- four bootstrap tool identities and versions;
- Docker canonical path, stat/SHA and pre/post equality;
- fixed Docker client/server product fields;
- effective context `default`;
- local endpoint `unix:///var/run/docker.sock`, scheme `unix`, raw `SkipTLSVerify=false`;
- clean absence of the three Docker override variables; and
- accepted residual High for non-atomic binary swap.

### Still blocked

- `/usr/bin/env` identity is unbound even though the exact helper uses it; and
- the client-selected context/endpoint does not bind the daemon or socket identity and therefore cannot yet prove that later image inspection reaches the controlled non-live daemon; and
- strict raw client build-time equality is unresolved because the published table collapsed one padding space.

**Corrected E1 readiness:** not sufficient for a later execution decision. A bounded Owner disposition and separately authorized fixed-output daemon/socket identity lane can resolve these dependencies without another broad architecture amendment. No image inspection was run.

## 13. E2-B1 readiness

### Closed or narrowed

- curl canonical path, stat/SHA, version-banner library/TLS labels, protocols, features and pre/post equality;
- public request endpoints and header/body schemas remain frozen by the wire contract;
- additive unretained fields may be ignored after strict required-field validation;
- transport ceilings are `30`/`300` seconds with zero automatic retries; and
- no new controller source is required if the exact Bash/curl/jq envelope becomes complete.

### Blocked

- `jq` is absent and no fallback parser is approved;
- effective CA file/directory provenance is unresolved;
- dynamically loaded libcurl, TLS and supporting dependency file identities are unresolved;
- `--no-netrc` exact support remains unproven;
- the eleven write-out variables remain unbound; and
- `/usr/bin/env` identity remains unbound.

**E2-B1 readiness:** not sufficient. No curl transfer or GitHub request was made.

## 14. Next bounded parallel acquisition decision

Corrected E1, E2-B1 and E3-B1 must not yet be combined into one acquisition gate because corrected E1 and E2-B1 retain material provenance Blockers. E3-B1 remains independently eligible from already approved static inputs, but this receipt does not start or authorize it.

A later combined gate is possible only after the Owner resolves the exact dependencies in Section 18 and separately authorizes the lane command allowlists. Parallel feasibility is an architecture fact, not execution authority.

## 15. Findings by severity

### 15.1 Blocker

| Finding | Concrete evidence | Effect |
| --- | --- | --- |
| sole parser candidate absent | exact jq helper exit `41`, empty stdout/stderr, frozen path | E2-B1 cannot start; no fallback |
| effective curl CA provenance absent | fixed version output emitted no CA file/directory; no broader read/network was authorized | E2-B1 TLS trust boundary cannot close |
| exact curl command semantics incomplete | `--no-netrc` and eleven write-out variables remain unbound | future transport command cannot be accepted exactly |
| helper dependency unbound | published helper executes `/usr/bin/env`; gate fingerprint allowlist omitted it while pre/post was required for every tool | corrected E1/E2-B1 clean-environment provenance remains conditional |

### 15.2 High — unresolved

| Finding | Concrete evidence | Effect |
| --- | --- | --- |
| Docker daemon/socket identity unbound | context output retained only `default`, `unix:///var/run/docker.sock` and `SkipTLSVerify=false`; no daemon or socket identity fact was authorized | corrected E1 cannot yet prove that a later image read reaches the controlled non-live daemon |
| curl loaded dependencies unbound | `curl --version` emitted product labels but no loaded file paths, stat identities, SHA-256 values or CA source | E2-B1 cannot authenticate the future TLS/client dependency chain |

### 15.3 High — accepted residual

- Pre/post canonical path, stat and SHA-256 equality cannot exclude a transient replace-and-restore between checks. The Owner explicitly accepts this residual for the read-only, single-owner gate. Any observed drift still discards dependent evidence.

### 15.4 Medium

- Docker client build-time raw text has two day-padding spaces; the prior published table records one. All identity and parsed product facts otherwise agree. Strict textual equivalence needs a bounded Owner disposition.
- Windows SSH argument/line-ending transformations corrupted three initial helper transports. All were discarded before dependent use, and LF-preserving fresh attempts succeeded where the tool existed. Future evidence command transport must preserve exact LF bytes.
- Curl help/manual capture did not close every option/write-out variable. This is an availability/evidence-completeness issue, not evidence that the installed curl lacks those capabilities.

### 15.5 Rejected inference

Rejected: treating `SkipTLSVerify=false` on a Unix socket as proof of a TLS session; treating Docker metadata as image/runtime compatibility; installing jq or selecting a fallback parser; inferring a CA store; assuming unobserved curl variables; normalizing the Docker build-time text silently; accepting malformed helper output; starting E1/E2-B/E3-B/E4; or broadening into source/live/accounting work.

## 16. Bounded reviews and Main Control synthesis

One bounded accounting-boundary, security/leakage, host/tool/runtime-classification and release/governance review was completed, followed by this single Main Control synthesis. No second review loop was opened.

Accepted reviewer findings:

- **Blocker:** `/usr/bin/env` is an unfingerprinted dependency of the exact helper, so Docker/curl helper selection and the jq no-result are provisional and must be reacquired after the helper chain is closed;
- **Blocker:** no accepted jq parser exists, and no fallback is authorized;
- **High:** the fixed context output proves only the client-selected endpoint at the observation instant, not daemon/socket identity or controlled non-live runtime ownership;
- **High:** curl's banner labels do not bind dynamically loaded libcurl/TLS/dependency files or the effective CA source;
- **Medium:** the Docker client build-time comparison has a one-space raw-text padding mismatch; and
- **Medium:** pre/post identity is point-in-time evidence only. Its replace-and-restore residual remains explicitly Owner-accepted High.

Rejected reviewer inferences:

- treating helper success as provenance-complete while `/usr/bin/env` is unbound;
- treating the local Unix endpoint as authenticated daemon identity or runtime ownership;
- treating curl banner labels as loaded-library fingerprints;
- treating the provisional jq no-result as an execution-authoritative absence;
- silently normalizing the Docker build-time text; or
- installing or selecting a fallback parser.

Deferred to separately authorized bounded work: `/usr/bin/env` provenance, Docker daemon/socket identity and drift, curl dynamic dependencies/CA/exact command semantics, jq provisioning or parser-policy supersession, and any E1/E2-B execution. Accounting semantics remain unchanged and no accounting authority was introduced.

Main Control accepts the stop: the bounded observations are retained, but none of the incomplete chains is promoted to execution authority.

## 17. Continuity status

| Required continuity fact | Status |
| --- | --- |
| current gate | Toolchain, Docker Endpoint and Parser Provenance Gate |
| closed | four bootstrap fingerprints; direct Docker and curl literal identity/product observations; client-selected Docker context/Unix endpoint observation; transport ceilings; accepted residual-swap posture |
| narrowed | corrected E1 to env, daemon/socket and build-time disposition; E2-B1 to jq, CA, dynamic-dependency, exact option/write-out and env prerequisites |
| blocked | corrected E1 and E2-B1 readiness |
| not started | corrected image inspection, E2-B1 requests, E2-B2, E3-B, E4, source authoring, Finance UI and live alignment |
| next dependency | bounded toolchain provenance-gap Owner decision |
| next Owner decision | Section 18 choices; optionally separate E3-B1 authority |
| roadmap-checkpoint trigger | not reached; trigger remains controlled completion/failure of E2-B2 plus E3-B final static synthesis |

No canonical Finance roadmap redesign or historical cleanup is required by these facts.

## 18. Exact next Owner decisions

Before another corrected E1/E2-B1 acquisition proposal, the Owner must decide:

1. authorize a fixed `/usr/bin/env` pre/post fingerprint lane, or accept the successful exact-helper result without separate env identity;
2. authorize a minimum fixed-output daemon/socket identity and pre/post drift allowlist that can distinguish the controlled non-live daemon before any corrected image read;
3. authorize controlled provisioning and provenance of an exact jq release, or explicitly supersede the jq-only parser choice; no fallback is currently allowed;
4. select a no-network fixed-output method and literal-tool allowlist to prove curl's loaded dependency identities, effective CA source, `--no-netrc` support and the eleven write-out variables;
5. accept semantic timestamp equality for Docker client build time despite display padding, or require a later factual documentation correction; and
6. decide whether independently eligible E3-B1 may proceed while corrected E1/E2-B1 provenance gaps are resolved.

These are bounded technical/authority choices. They do not justify a broad planning amendment.

## 19. Validation and future staging allowlist

After documentation writing, Main Control validates:

- repository root, branch, HEAD/upstream `240851e804e0f119f27847be63c117f08cb89d9d` and `0/0`;
- empty index before and after;
- worktree candidate scope exactly this evidence document plus README, alongside the unchanged harness and four exclusions;
- `git diff --check HEAD`, changed-document whitespace, balanced Markdown fences and changed local references;
- exactly one README index entry;
- exact permitted command inventory and the absence of any transfer/image/source/runtime command;
- unchanged protected hashes and absent controller/Dockerfile/initializer; and
- no Finance workload limit, E1/E2-B/E3-B/E4 authority, live-tree or operational-data access.

The exact future documentation staging allowlist, if separately authorized, is:

1. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/finance-accounting-cycle2-gl-tb-toolchain-docker-endpoint-parser-provenance-2026-07-19.md`
2. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/README.md`

This gate does not authorize staging, commit or push.

## 20. Final control statement

**Decision:** `stopped_for_toolchain_provenance_gap`

The four bootstrap tools, direct Docker/curl binary facts and the client-selected current local Unix endpoint observation are recorded. The gate stops because the helper dependency is incomplete, no parser is accepted, and Docker daemon/socket identity plus curl CA, loaded-dependency and exact-command requirements remain unresolved. Corrected E1, E2-B1 and the proposed combined acquisition gate are not ready.

No corrected image inspection, curl transfer, GitHub/network request, source-content read, source authoring, image/container operation, infrastructure, secret, test, Frappe, Bench, SQL, synthetic execution, live access, staging, commit, push, migration, permission change, protected gate or accounting action occurred.
