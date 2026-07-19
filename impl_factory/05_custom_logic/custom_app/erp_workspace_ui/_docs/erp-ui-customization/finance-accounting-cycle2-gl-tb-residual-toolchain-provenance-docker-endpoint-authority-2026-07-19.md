# Finance & Accounting Cycle 2 GL / Trial Balance Residual Toolchain Provenance and Docker Endpoint Authority Gate

Date: 2026-07-19

Repository: `/home/deploy/erp-projects/erpai_project1_erpnext_ui_design`

Branch: `feature/erpnext-ui-design`

Published baseline: `55faea3a4c353b4aaabf12f97179cecd8891a95d`

Authority: Main Control v2; bounded local read-only provenance and planning only

Decision: `stopped_for_residual_toolchain_gap`

## 1. Outcome and controlling effect

This gate closes the previously missing `/usr/bin/env` identity, conclusively establishes that the sole approved parser candidate `jq` is absent from the frozen `/usr/local/bin:/usr/bin` path, and records bounded local curl, CA-bundle, ELF-interpreter, startup-dependency, option and write-out evidence.

The gate stops because no approved JSON parser exists. No parser semantics could be tested, and no fallback, installation or alternate parser is permitted. E2-B1 therefore remains blocked.

The Owner's endpoint decision independently keeps corrected E1 blocked. The observed `unix:///var/run/docker.sock` endpoint remains unapproved and was not contacted. A later E1 may use only a separately approved disposable and isolated Docker daemon with its own endpoint and data root, no mount/proxy/fallback to `/var/run/docker.sock`, and separately approved creation, image acquisition, use and teardown. VM-level isolation remains deferred.

E3-B1 remains independently eligible under a separate Owner gate, but it was not started or authorized here. The three lanes must not be combined into one acquisition gate.

## 2. Published authority and repository baseline

The controlling records are:

- [Corrected E1 and E2-B1 Wire-Contract Freeze](finance-accounting-cycle2-gl-tb-corrected-e1-e2b1-wire-contract-freeze-2026-07-19.md);
- [Toolchain, Docker Endpoint and Parser Provenance Gate](finance-accounting-cycle2-gl-tb-toolchain-docker-endpoint-parser-provenance-2026-07-19.md); and
- the Owner's accepted publication receipt and endpoint-authority direction for this gate.

The verified gate-start state was:

| Fact | Verified value |
| --- | --- |
| repository root | `/home/deploy/erp-projects/erpai_project1_erpnext_ui_design` |
| branch | `feature/erpnext-ui-design` |
| HEAD | `55faea3a4c353b4aaabf12f97179cecd8891a95d` |
| upstream | `origin/feature/erpnext-ui-design` at the same revision |
| ahead/behind | `0/0` |
| index | empty |
| worktree | unchanged harness plus the four protected exclusions only |

This gate did not inherit publication, execution, image, network-acquisition, source-reading or runtime authority.

## 3. `/usr/bin/env` provenance closure

The exact accepted fixed commands were:

```text
/usr/bin/realpath --canonicalize-existing --physical -- /usr/bin/env
LC_ALL=C /usr/bin/stat --dereference --printf='%d|%i|%f|%a|%u|%g|%s|%Y|%Z\n' -- /usr/bin/env
LC_ALL=C /usr/bin/sha256sum --binary -- /usr/bin/env
/usr/bin/env --version
```

The accepted run used LF-preserving standard-input transport to the already accepted `/bin/bash --noprofile --norc -p -s`. The stat tuple order is `device|inode|raw_mode|permissions|uid|gid|bytes|mtime|ctime`.

| Field | Accepted value |
| --- | --- |
| supplied literal | `/usr/bin/env` |
| canonical literal | `/usr/bin/env` |
| pre/use-post/post stat | `64513|1642|81ed|755|0|0|43976|1707363999|1719848457` |
| SHA-256 | `85036540673319c6c2f54233fd2b9e45a8a71246b51cc96c4e6ab8ee6c419eb0` |
| version line | `env (GNU coreutils) 8.32` |
| classification | regular executable, mode `755`, UID/GID `0/0` |
| drift | none; stat and SHA-256 were byte-identical before and after helper use |

The accepted commands exited `0` with empty stderr. This closes the prior helper-dependency Blocker for the observed host state. It does not create an atomic no-swap guarantee; fresh future use still requires its own pre/use/post binding.

One earlier Windows argument-transport attempt was discarded after its stat format pipes were interpreted as shell pipelines. It retained no evidence and had no dependent use. The fresh LF-preserving attempt supplied the accepted record.

## 4. Exact jq helper result

After `/usr/bin/env` was accepted, the exact published helper was rerun with literal `jq`:

```bash
/usr/bin/env -i PATH=/usr/local/bin:/usr/bin LC_ALL=C BASH_ENV=/dev/null ENV=/dev/null /bin/bash --noprofile --norc -p -c '
exec 2>/dev/null
kind=$(builtin type -t jq) || exit 41
[[ "$kind" == file ]] || exit 42
hits=()
builtin mapfile -t hits < <(builtin type -ap jq) || exit 43
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

| Result field | Exact result |
| --- | --- |
| exit | `41` |
| stdout | empty |
| stderr | empty |
| classification | conclusively absent from the complete frozen path `/usr/local/bin:/usr/bin` |

No jq literal, file identity, version or parser runtime exists to approve. The conditional sealed-standard-input tests for required fields/types, arrays/objects, nulls, projection, ordering, truncation, accepted unknown-field policy, malformed JSON and duplicate/ambiguous identity rejection were therefore not run. Their prerequisite failed.

This is the controlling Blocker. Python, Node, a custom parser, installation and silent fallback remain rejected.

## 5. Explicit CA bundle candidate

The gate inspected only the Owner-selected literal; no arbitrary CA/configuration/credential search occurred.

| Field | Accepted value |
| --- | --- |
| supplied/canonical path | `/etc/ssl/certs/ca-certificates.crt` |
| pre/post stat | `64513|841|81a4|644|0|0|182140|1781677273|1781677273` |
| SHA-256 | `69e3e35ee9f50033a7465f6293de884d570200ae8d803bc1c4e05525c1c2a7f2` |
| classification | nonempty regular file, UID/GID `0/0`, mode `644` |
| drift | none observed |

The file is accepted as the explicit future `--cacert` candidate. It is not classified as curl's implicit default, and the local-file tests below do not prove TLS certificate validation or the trust semantics of any future HTTPS session.

## 6. Curl and ELF inspection identities

The accepted curl identity remains:

| Field | Value |
| --- | --- |
| path | `/usr/bin/curl` |
| stat | `64513|23964|81ed|755|0|0|260328|1782753688|1782973071` |
| SHA-256 | `0ca2b923679ab186f6512c7512e131a1c5c1b43d4cb5d55933998405b39e85bf` |
| curl/libcurl | `7.81.0` / `7.81.0` |
| banner TLS label | OpenSSL `3.0.2` |

The exact ELF inspection tool was:

| Field | Value |
| --- | --- |
| supplied path | `/usr/bin/readelf` |
| canonical path | `/usr/bin/x86_64-linux-gnu-readelf` |
| pre/post stat | `64513|74056|81ed|755|0|0|776640|1764774481|1771050666` |
| SHA-256 | `04db0000749aff89e4af21429340b00b536fc6f80e811c872c006507881a5560` |
| version | `GNU readelf (GNU Binutils for Ubuntu) 2.38` |

`readelf --program-headers --wide /usr/bin/curl` identified interpreter `/lib64/ld-linux-x86-64.so.2`. `readelf --dynamic --wide /usr/bin/curl` identified direct `NEEDED` entries `libcurl.so.4`, `libz.so.1` and `libc.so.6`; no `RPATH` or `RUNPATH` was retained.

The interpreter binding was:

| Field | Value |
| --- | --- |
| supplied path | `/lib64/ld-linux-x86-64.so.2` |
| canonical path | `/usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2` |
| stat | `64513|3217|81ed|755|0|0|240936|1769761256|1771051039` |
| SHA-256 | `9eb34cb2da3ae2a9398cc09b3cd2d069563ec40d9858cb711af15cd23fa80abf` |
| version | `ld.so (Ubuntu GLIBC 2.35-0ubuntu3.13) stable release version 2.35` |

## 7. Clean-environment startup dependency graph

The accepted interpreter listing used only `PATH=/usr/local/bin:/usr/bin`, `LC_ALL=C` and `TZ=UTC`. Loader, proxy, authentication, HOME, curl-configuration and CA-override environment variables were absent. The file-backed startup graph resolved to:

| Canonical dependency | SHA-256 |
| --- | --- |
| `/usr/lib/x86_64-linux-gnu/libcurl.so.4.7.0` | `0b6cae5c8f3ba2e76777d4fcffebbc4baaea3d8016bca0f0606f2ff104cbd7ac` |
| `/usr/lib/x86_64-linux-gnu/libz.so.1.2.11` | `64c206f0146cc58bbddc4f22054436f4ff278f5a554aa3ce6921ddf7e9133370` |
| `/usr/lib/x86_64-linux-gnu/libc.so.6` | `c53819710b163d3f1d2541778590d58d3ef31cb0ed75adcbe059faac68c1e72d` |
| `/usr/lib/x86_64-linux-gnu/libnghttp2.so.14.20.1` | `3b9cae3346ad67fbe962fa1ed73f358e125604a3ad7bb11626fa712ccefe6ee2` |
| `/usr/lib/x86_64-linux-gnu/libidn2.so.0.3.7` | `1420c60a18189fb2e7bb4b8da1409564b0c1c46c59df5bbb0c23339bb961403a` |
| `/usr/lib/x86_64-linux-gnu/librtmp.so.1` | `2401c4fc99c7b93e79648071224a6eb230dcb800184ccacc8e1854e33fc61445` |
| `/usr/lib/x86_64-linux-gnu/libssh.so.4.8.7` | `66a3c908ba71ea89be3ddba61704cbb1d9fcbfeaa80b24f2d22174f27e41e36c` |
| `/usr/lib/x86_64-linux-gnu/libpsl.so.5.3.2` | `95ca960ec3417da3d9505c8d2c6f0e9b7caf79ab900f6099a6bd938cf91069c5` |
| `/usr/lib/x86_64-linux-gnu/libssl.so.3` | `3b3562ee6d106840e8d000300c9517ebc28269c2ed0a9b23351e71c518cd7bb8` |
| `/usr/lib/x86_64-linux-gnu/libcrypto.so.3` | `f488e5cdfaaaa816648e7287db9468ef27b78980a5327632539067c59981a2be` |
| `/usr/lib/x86_64-linux-gnu/libgssapi_krb5.so.2.2` | `74c938dcc051d96376e4a396d4694f0ce9da54c08fce18c593148ad567f93810` |
| `/usr/lib/x86_64-linux-gnu/libldap-2.5.so.0.1.12` | `c2cd9a8456ce347c8e07df96462ffc4dd0809afd246a0be23d59c47adc0d11c6` |
| `/usr/lib/x86_64-linux-gnu/liblber-2.5.so.0.1.12` | `235df8ad6af0eaabea5d1e6ae037bf130d0cadb341c4914687427e897ee2588b` |
| `/usr/lib/x86_64-linux-gnu/libzstd.so.1.4.8` | `5df4f4df42d76270bb6981fabc7c1fdccd8ad28a23d84d67f73203fb3f537667` |
| `/usr/lib/x86_64-linux-gnu/libbrotlidec.so.1.0.9` | `db9dbda709a46c3ae124433f47c4db71167db8aaba4eafdfd99c8a3a14584463` |
| `/usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2` | `9eb34cb2da3ae2a9398cc09b3cd2d069563ec40d9858cb711af15cd23fa80abf` |
| `/usr/lib/x86_64-linux-gnu/libunistring.so.2.2.0` | `9c28d59500f186fc28bf7e77e9b1a71129f66731c52ac1e974b9acd1a760911a` |
| `/usr/lib/x86_64-linux-gnu/libgnutls.so.30.31.0` | `dcadda7f0f82c54ca157b6ca0a5fdc8e1128db4d778109c8e197e2f84c2ac9ba` |
| `/usr/lib/x86_64-linux-gnu/libhogweed.so.6.4` | `47d56894948545036bd49aed718393bf6edb93fce222874dad30b59f085ad9ee` |
| `/usr/lib/x86_64-linux-gnu/libnettle.so.8.4` | `2d3bda6cfa2d477cd91b8178843d19e081b911a124f04b4be06b6e32c9fabc73` |
| `/usr/lib/x86_64-linux-gnu/libgmp.so.10.4.1` | `4dc20a901c6951e678e216e959da2534bcef7053e6efdf1492509baf142282b0` |
| `/usr/lib/x86_64-linux-gnu/libkrb5.so.3.3` | `7ccebba46ab1548e386e4884c0bc6553d4297789d53324d890fa30f0c87ee31b` |
| `/usr/lib/x86_64-linux-gnu/libk5crypto.so.3.1` | `43d6a714cda56141db7070f16c2ca4a33ed93c5af848b8ee226749fb29f3ef9d` |
| `/usr/lib/x86_64-linux-gnu/libcom_err.so.2.1` | `a2b7c9d27f5e50a7956e2327cde4fafbbe0e442187d5d3883d5a0ecfd836ddc1` |
| `/usr/lib/x86_64-linux-gnu/libkrb5support.so.0.1` | `134342eac5baf7a0c5a37be979bf8addb22d171220441478f98ba6cd2771d14d` |
| `/usr/lib/x86_64-linux-gnu/libsasl2.so.2.0.25` | `344870a9ff3cfee1df28f518e9e93073df8d0522a288f016f06fdacbfa49eed8` |
| `/usr/lib/x86_64-linux-gnu/libbrotlicommon.so.1.0.9` | `abf86ae9362dbb413c740a55b194c74adb09a7bd92d8fbd96a293c797a4a6d08` |
| `/usr/lib/x86_64-linux-gnu/libp11-kit.so.0.3.0` | `d2b01eaad185e95ef312940a3bdd4b6694f992b022a2dddb9dd494286e5a1d2c` |
| `/usr/lib/x86_64-linux-gnu/libtasn1.so.6.6.2` | `f198a1272ca6a071b313646ae65fc1942628df8caebe07e4c377b15b68903358` |
| `/usr/lib/x86_64-linux-gnu/libkeyutils.so.1.9` | `ad20d5fb89df5297073b46373c65bfbb01f33a00b4949894055d29a7fcf00900` |
| `/usr/lib/x86_64-linux-gnu/libresolv.so.2` | `0f40debbe0184c3a2b2f90ecb5aa7d499cae96e9d84e2859f866e5ed6e3018f8` |
| `/usr/lib/x86_64-linux-gnu/libffi.so.8.1.0` | `247da4d5d34a91cadcdd6282be4c4644fcb8af001334d2b8a82ecda435418cbf` |

`linux-vdso.so.1` has no file identity and was not hashed. All recorded file-backed dependency post-check hashes matched.

This proves the loader-resolved startup graph only at the observation points. It does not prove later `dlopen` activity, NSS, OpenSSL provider, engine or plugin loading, or future no-drift. GnuTLS is an indirect dependency in the graph; curl's banner identifies OpenSSL as its selected TLS backend, and GnuTLS presence must not be described otherwise.

## 8. Exact local curl option and write-out checks

The local success command used clean `LC_ALL=C` and `TZ=UTC`, `/usr/bin/curl`, `file:///dev/null`, `/dev/null` output destinations and these options:

```text
--disable
--silent
--show-error
--fail-with-body
--request GET
--http1.1
--proto '=file'
--tlsv1.2
--proxy ''
--no-netrc
--disallow-username-in-url
--max-redirs 0
--retry 0
--connect-timeout 30
--max-time 300
--cacert /etc/ssl/certs/ca-certificates.crt
--header Authorization:
--header Cookie:
--header Proxy-Authorization:
--header Accept: application/vnd.github+json
--header Accept-Encoding: identity
--header Cache-Control: no-cache
--header Pragma: no-cache
--header X-GitHub-Api-Version: 2026-03-10
--user-agent erpai-gl-tb-e2b1-readonly/1.0
--dump-header /dev/null
--output /dev/null
--write-out <exact eleven-field format>
--url file:///dev/null
```

`--disable` was the first curl option. The clean environment retained no HOME, proxy, authentication, CA override or loader override value, and no credential/configuration file was inspected. `--retry 0` made the accepted zero-automatic-retry posture explicit. The connect and total ceilings remain 30 and 300 seconds; these are transport safety ceilings, not Finance workload limits.

Two independent success runs were byte-identical:

```text
exitcode=0
response_code=000
method=GET
scheme=FILE
url_effective=file:///dev/null
num_redirects=0
redirect_url=
http_version=0
ssl_verify_result=0
size_download=0
content_type=
```

A local missing-file test produced the expected fail-closed pair:

```text
exitcode=37
response_code=000
method=GET
scheme=FILE
url_effective=file:///definitely-not-present-erpai-gl-tb-e2b1
num_redirects=0
redirect_url=
http_version=0
ssl_verify_result=0
size_download=0
content_type=
curl: (37) Couldn't open file /definitely-not-present-erpai-gl-tb-e2b1
```

The control wrapper normalized its outer nonzero report, so status `37` is bound by curl's installed write-out/error pair rather than a separately retained controller exit field.

A protocol-denial check used future restriction `--proto '=https'` with `file:///dev/null`; it made no connection and failed closed:

```text
exitcode=1
response_code=000
method=GET
scheme=
url_effective=file:///dev/null
num_redirects=0
redirect_url=
http_version=0
ssl_verify_result=0
size_download=0
content_type=
curl: (1) Protocol "file" not supported or disabled in libcurl
```

### 8.1 What the local checks establish

- every selected option was recognized;
- `--disable` can occupy the first option position;
- `--no-netrc`, empty proxy, explicit `--cacert`, zero redirects, explicit zero retry and the two transport ceilings were accepted;
- all eleven write-out variables are installed and deterministic for the local target;
- local missing-file and prohibited-protocol cases fail closed; and
- header/body destinations are distinct arguments and did not contaminate the eleven-line stdout on the zero-byte target.

### 8.2 What the local checks do not establish

- actual TLS negotiation, certificate-chain validation or use of the CA bundle in an HTTPS session;
- any HTTPS status, HTTP version, content type, header, body, redirect or effective-URL result;
- that local `ssl_verify_result=0` says anything about TLS;
- HTTPS scheme casing; the local value was uppercase `FILE`;
- semantic redirect refusal against an actual redirect;
- positive separation with nonempty HTTP headers/body;
- future dynamic-loading identities or future no-drift; or
- independent success-stderr hashing, because the control surface presented one combined output stream.

These are local tool-behavior observations, not an E2-B1 acquisition receipt. They do not authorize an HTTPS request.

## 9. Docker endpoint authority disposition

The observed endpoint `unix:///var/run/docker.sock` remains unapproved. Context name, socket path, Docker version, hostname and daemon metadata cannot establish non-live or disposable ownership. No Docker command or socket contact occurred in this gate.

The future authority boundary is frozen:

1. corrected E1 may run only against a separately Owner-approved disposable and isolated Docker daemon;
2. it must have a dedicated endpoint and data root;
3. it must not mount, proxy or fall back to `/var/run/docker.sock`;
4. daemon creation, image acquisition, inspection use and deterministic teardown require a later explicit Owner gate;
5. the existing fixed Docker inspection architecture remains controlling; registry inspection, Skopeo, OCI parsing and alternate sources remain rejected; and
6. VM-level isolation remains deferred unless later evidence shows it is required.

No endpoint, daemon or infrastructure is created or approved by this document.

## 10. Separate readiness adjudication

| Lane | Decision | Reason |
| --- | --- | --- |
| corrected E1 | blocked | only a separately approved disposable isolated Docker daemon may be used; none is approved or created |
| E2-B1 | blocked | `/usr/bin/env`, curl, CA and startup dependency facts are narrowed, but the sole approved jq parser is conclusively absent; HTTPS/TLS semantics also remain unexecuted |
| E3-B1 | independently eligible but not authorized | it may proceed under its own bounded Owner gate and need not wait for E1/E2-B1 |

E1 must remain separate. E2-B1 and independently scoped E3-B1 cannot form a later bounded parallel acquisition gate unless the Owner first selects and closes a parser path for E2-B1. This document does not make that parser decision.

## 11. Findings by severity

### 11.1 Blocker

| Finding | Concrete evidence | Disposition |
| --- | --- | --- |
| sole approved parser absent | accepted `/usr/bin/env`; exact jq helper exit `41` with empty stdout/stderr under complete frozen path | E2-B1 remains stopped; Owner parser choice required, with no fallback inferred |
| corrected E1 endpoint authority absent | Owner expressly rejects `/var/run/docker.sock` and requires a separately approved disposable isolated daemon | corrected E1 remains stopped; no Docker contact allowed |

### 11.2 High - accepted residual

- Pre/use/post path, stat and SHA-256 equality cannot exclude a transient replace-and-restore between observations. The previously accepted non-atomic residual remains; no drift was observed and any future observed drift still discards dependents.

No new evidence-supported accounting or security High was found.

### 11.3 Deferred limitations

- The local `file://` checks cannot prove future HTTPS/TLS/CA, redirect or nonempty response-separation behavior. They must not be promoted as network compatibility evidence.
- The startup dependency graph cannot bind later `dlopen`, NSS, provider, engine or plugin files. A future acquisition requires fresh identity/drift binding and an explicit disposition for dynamic loading.
- The future exact HTTPS scheme casing remains unbound; local `%{scheme}` emitted uppercase `FILE`, which must not be normalized into an unobserved HTTPS value.
- Controller-level process-exit and independently separated stderr enforcement remain deferred. Curl's installed write-out/error pair showed `37` for the missing-file case, but the outer wrapper did not independently retain those channels.

### 11.4 Medium

- The local write-out `scheme` value is uppercase `FILE`; future HTTPS casing remains unproven.
- The missing-file status `37` is supported by curl's write-out/error pair but was not independently retained by the outer control wrapper.
- Local zero-byte output/header destinations prove argument separation and stdout cleanliness, not positive separation of nonempty HTTP material.
- Failed Windows quoting, unavailable `rg` and one unusable parallel post-check were discarded; the accepted evidence was reacquired through bounded serial/fixed transport.

### 11.5 Rejected inference

Rejected: treating the selected Unix socket as non-live; contacting it; treating CA metadata as certificate-validation proof; treating `ssl_verify_result=0` on `file://` as TLS evidence; describing indirect GnuTLS as curl's selected TLS backend; treating startup dependencies as complete future dynamic-loading proof; installing jq; selecting Python, Node, a custom parser or fallback; starting E1/E2-B1/E3-B1; or broadening into source, runtime, live or accounting work.

## 12. Bounded review and Main Control synthesis

One bounded accounting-preservation, security/credential-leakage, database/runtime and release-containment review was followed by this Main Control synthesis. No general architecture or repeated counterpart-review loop was opened.

Accepted reviewer findings:

- `/usr/bin/env` provenance is closed for this observation, including matching pre/use-post/post identity;
- exact helper exit `41` with empty streams proves no `jq` in the complete frozen path, but not host-wide absence;
- the CA file is accepted only as the explicit future `--cacert` candidate, not implicit-default or TLS-validation proof;
- readelf, interpreter and startup dependency hashes materially close local startup provenance at the observation points;
- two clean local curl runs prove option recognition and deterministic eleven-field local output; and
- accounting/database and security/leakage boundaries pass because no accounting, database, permission, credential, source, operational or network-response fact was acquired.

Accepted Blocker and authority stop:

- the sole approved parser is absent, so parser/schema/duplicate/ambiguity/projection tests cannot run and E2-B1 remains blocked; and
- E1 remains blocked by Owner endpoint authority until a separately approved disposable isolated daemon exists.

Rejected reviewer inferences:

- host-wide jq absence, parser installation or fallback;
- CA hash or `file://` `ssl_verify_result=0` as TLS proof;
- startup dependency listing as complete dynamic-runtime identity;
- indirect GnuTLS as curl's selected HTTPS backend;
- `unix:///var/run/docker.sock` as disposable, non-live or approved;
- combining E1 with any E2-B1/E3-B1 acquisition; or
- describing these checks as an acquisition receipt.

Deferred: HTTPS scheme casing, controller-level process-exit/separate-stderr enforcement, TLS/redirect/nonempty-response behavior, future `dlopen` identities, fresh drift binding, the Owner parser choice, disposable Docker planning and every later acquisition or execution gate.

Main Control accepts the evidence-supported stop: `/usr/bin/env` is closed, jq is conclusively absent from the frozen path, E2-B1 is blocked, E1 remains separately blocked by endpoint authority, and E3-B1 remains separately eligible but unauthorized. Curl/CA evidence is retained only for later reuse within its explicit local-only limitations.

## 13. Continuity and roadmap checkpoint

| Continuity fact | Status |
| --- | --- |
| current gate | Residual Toolchain Provenance and Docker Endpoint Authority Gate |
| closed | `/usr/bin/env` host identity; explicit CA candidate identity; readelf/interpreter/startup graph; local curl option and eleven-variable recognition |
| blocked | corrected E1 endpoint authority; E2-B1 parser prerequisite |
| independently eligible | E3-B1, only under a separate Owner gate |
| next dependency | bounded Owner parser choice and, separately, disposable Docker endpoint planning |
| roadmap checkpoint | not reached |
| checkpoint trigger | unchanged: completion or controlled failure of E2-B2 plus E3-B final static synthesis |

This is a tooling/provenance stop, not an accounting-design failure. No broad architecture amendment is required.

## 14. Recommended next bounded gate

Because jq is conclusively absent, Main Control recommends a planning-only **GL/TB E2-B1 Parser Authority Decision Gate**. It should present bounded Owner choices without installing or executing anything. Corrected E1's disposable Docker endpoint must remain a separate later infrastructure-authority gate. E3-B1 may be authorized separately and need not wait.

No recommended gate is started by this receipt.

## 15. Validation and future documentation staging allowlist

After writing, Main Control validates:

- repository root, branch, HEAD/upstream `55faea3a4c353b4aaabf12f97179cecd8891a95d` and `0/0`;
- empty index before and after;
- worktree candidate scope exactly this document and README plus the five unchanged protected items;
- `git diff --check HEAD`, changed-document whitespace, balanced Markdown fences and local references;
- exactly one README index entry;
- unchanged protected hashes and statuses;
- no Finance workload limit, E1/E2-B1/E3-B1/E2-B2/E3-B/E4/source-authoring authority; and
- no Docker contact, outbound acquisition or prohibited state change.

The exact future documentation staging allowlist, if separately authorized, is:

1. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/finance-accounting-cycle2-gl-tb-residual-toolchain-provenance-docker-endpoint-authority-2026-07-19.md`
2. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/README.md`

This gate does not authorize staging, commit or push.

## 16. Final control statement

**Decision:** `stopped_for_residual_toolchain_gap`

The residual host-tool evidence is narrowed substantially, but E2-B1 cannot proceed without an Owner parser decision and corrected E1 cannot proceed without a separately approved disposable isolated Docker endpoint. E3-B1 remains separately eligible and unauthorized. The roadmap checkpoint remains unchanged.

No network acquisition, Docker-daemon contact, image inspection, source-content acquisition, source authoring, infrastructure, secret access, test, Frappe, Bench, SQL, synthetic execution, live access, staging, commit, push, migration, permission change, protected gate or accounting action occurred.
