# Finance & Accounting Cycle 2 GL / Trial Balance E2-B1 Parser Sandbox, Observer and Bootstrap Provider Selection/Fingerprint Gate

Date: 2026-07-22

Repository: `/home/deploy/erp-projects/erpai_project1_erpnext_ui_design`

Branch: `feature/erpnext-ui-design`

Verified baseline: `c13a2d5972e6ef8131ad8239359fee3e9e89dde2`

Authority: Main Control v2; planning and read-only provider fingerprinting only

Decision: `stopped_for_parser_provider_gap`

## 1. Outcome and controlling effect

The published [Parser Runner Residual Import and Isolation Authority Amendment](finance-accounting-cycle2-gl-tb-e2b1-parser-runner-residual-import-isolation-authority-amendment-2026-07-22.md) remains controlling. Its `I1+C1+A1+D1+O1+S1+R1+P1` package is recommendation-only.

This gate fingerprints only the five Owner-fixed candidates and the exact kernel prerequisites. It finds:

1. `/usr/bin/bwrap` is absent;
2. `/usr/bin/unshare` and `/usr/bin/setpriv` are present but are partial D1 building blocks, not a complete denial provider;
3. `/usr/bin/strace` is a conditional O1 observation candidate, but its raw output, ptrace effects, completion and placement are unresolved;
4. `/usr/bin/timeout` is a conditional external ceiling candidate, not a complete process-tree, observer, evidence or teardown owner; and
5. the requested bootstrap order cannot apply C1 source-only enforcement retroactively to interpreter-startup modules or to the controller's current imports at lines 8-12.

The fixed candidate set cannot presently freeze the required D1 denial boundary. In particular, no present fixed candidate denies runner-created processes/threads, supplies an exact read-only sealed source view, closes inherited descriptors, or denies socket syscalls. A seccomp policy, delegated `pids.max` envelope, sealed-root preparation mechanism or another enforcement surface would be required, but none is authored, selected or approved.

This is a provider/bootstrap tooling stop, not an accounting-design failure. It does not approve a provider, source work, Python, an import ledger, a namespace, a sandbox, tracing, a timeout, numeric limits or evidence promotion.

## 2. Verified baseline and protected state

| Item | Verified value |
| --- | --- |
| repository root | `/home/deploy/erp-projects/erpai_project1_erpnext_ui_design` |
| branch | `feature/erpnext-ui-design` |
| HEAD/upstream | `c13a2d5972e6ef8131ad8239359fee3e9e89dde2` |
| configured upstream | `origin/feature/erpnext-ui-design` |
| ahead/behind | `0/0` |
| Git index | empty |
| worktree before documentation | four unchanged protected exclusions only |

Protected committed sources remain:

| Surface | SHA-256 |
| --- | --- |
| [parser fixture](../../erp_workspace_ui/tests/test_finance_gl_trial_balance_e2b1_parser_fixtures.py) | `b46dc6b02db57b0611346abad8665567fecf91456ce1db6fd488af9cbfea3afb` |
| [controller](../../erp_workspace_ui/tests/finance_gl_trial_balance_evidence_controller.py) | `69e67523d893b38b6559c75152f5802f6e5acf19642fd95d82cc2631d5a485b3` |
| [database harness](../../erp_workspace_ui/tests/test_finance_gl_trial_balance_source_proof.py) | `c8d0bb0556f9abb04e1be69c1d67a7f92c4ed37a64d8270d84339ad590e9cea5` |

The controller still imports `datetime`, `hashlib`, `json`, `re` and `urllib.parse` at lines 8-12 and ends at line 633 with parser-only behavior. It contains no supervisor, runner, denial, observer, suite, result, watchdog, evidence, discard or teardown implementation.

The fixture still lazily requests the canonical controller name at lines 63-70, gates its class at lines 105-112 and defines exactly ten methods at lines 213, 261, 322, 370, 409, 607, 739, 887, 1045 and 1104. The database harness still imports `frappe` and `MariaDBDatabase` unconditionally at lines 38-39; it remains forbidden and must be absent from the future child view.

## 3. Preserved non-negotiable boundary

Every future choice must preserve:

- exactly ten literal direct `TestCase(methodName)` instances in the frozen order;
- one flat explicit ordered `unittest.TestSuite`;
- no loader, discovery, `unittest.main`, `TextTestRunner`, JUnit or default traceback result;
- controller-only future source scope unless concrete evidence forces an Owner stop;
- a current Python observation/execution allowlist of `[]`;
- no database-harness visibility, import, access or unreachability claim without independent enforcement evidence;
- deferred exit `65/70`, watchdog duration, kill grace and every other numeric limit;
- no Frappe, Bench, ERPNext, MariaDB, Docker, E2-B1 acquisition, Finance runtime or accounting authority; and
- distinct future read, source-authoring, provider-activation, Python-observation, fixture-execution and evidence-promotion approvals.

## 4. Exact evidence scope and command record

### 4.1 Fixed provider operands

Only these candidate paths were tested for presence:

```text
/usr/bin/bwrap
/usr/bin/unshare
/usr/bin/setpriv
/usr/bin/strace
/usr/bin/timeout
```

No PATH search, alternate-tool enumeration, package installation or fallback selection occurred.

### 4.2 Candidate identity commands

For the literal list above, Main Control used only:

```text
LC_ALL=C /usr/bin/test -e <ONE_LITERAL_CANDIDATE>
/usr/bin/realpath --canonicalize-existing --physical -- <ONE_PRESENT_LITERAL>
LC_ALL=C /usr/bin/stat --dereference --printf='%d|%i|%f|%a|%u|%g|%U|%G|%s|%Y|%Z\n' -- <ONE_PRESENT_LITERAL>
LC_ALL=C /usr/bin/sha256sum --binary -- <ONE_PRESENT_LITERAL>
/usr/bin/unshare --version
/usr/bin/unshare --help
/usr/bin/setpriv --version
/usr/bin/setpriv --help
/usr/bin/strace --version
/usr/bin/strace --help
/usr/bin/timeout --version
/usr/bin/timeout --help
```

The identity tuple is `device|inode|hex mode|octal mode|uid|gid|owner|group|bytes|mtime epoch|ctime epoch`.

A first composite stat attempt had shell-quoting errors. Its stat output was rejected in full; it activated no provider and changed no state. The byte-preserved command forms above were then run successfully. Only the successful records enter this document.

### 4.3 Package, ELF, library and manual commands

```text
/usr/bin/dpkg-query -S /usr/bin/unshare /usr/bin/setpriv /usr/bin/strace /usr/bin/timeout
/usr/bin/dpkg-query -W -f='${binary:Package}|${Version}|${Architecture}|${db:Status-Abbrev}|${source:Package}|${source:Version}\n' util-linux strace coreutils
/usr/bin/readelf --program-headers --wide <ONE_PRESENT_LITERAL>
/usr/bin/readelf --dynamic --wide <ONE_PRESENT_LITERAL>
/usr/bin/readelf --notes --wide <ONE_PRESENT_LITERAL>
/usr/bin/ldd <ONE_PRESENT_LITERAL>
/usr/sbin/getcap -n /usr/bin/unshare /usr/bin/setpriv /usr/bin/strace /usr/bin/timeout
```

Exact installed manual paths were fingerprinted and read selectively with `/usr/bin/zgrep`, `/usr/bin/zcat` and `/usr/bin/sed`:

```text
/usr/share/man/man1/unshare.1.gz
/usr/share/man/man1/setpriv.1.gz
/usr/share/man/man1/strace.1.gz
/usr/share/man/man1/timeout.1.gz
/usr/share/man/man2/ptrace.2.gz
/usr/share/info/coreutils.info.gz
```

### 4.4 Fixed kernel prerequisite commands and paths

```text
/usr/bin/uname --kernel-release
/usr/bin/uname --machine
/usr/bin/cat /proc/sys/kernel/unprivileged_userns_clone
/usr/bin/cat /proc/sys/user/max_user_namespaces
/usr/bin/grep -E '^(CapEff|NoNewPrivs):' /proc/self/status
/usr/bin/cat /sys/fs/cgroup/cgroup.controllers
/usr/bin/test -e /sys/fs/cgroup/cgroup.type
/usr/bin/cat /proc/self/cgroup
/usr/bin/readlink /proc/self/ns/cgroup
/usr/bin/readlink /proc/self/ns/ipc
/usr/bin/readlink /proc/self/ns/mnt
/usr/bin/readlink /proc/self/ns/net
/usr/bin/readlink /proc/self/ns/pid
/usr/bin/readlink /proc/self/ns/pid_for_children
/usr/bin/readlink /proc/self/ns/time
/usr/bin/readlink /proc/self/ns/time_for_children
/usr/bin/readlink /proc/self/ns/user
/usr/bin/readlink /proc/self/ns/uts
```

The `/proc/self` and namespace values describe only each short-lived read-only inspection process. They do not identify or approve a future runner namespace.

### 4.5 Upstream interpretation references

Installed version-matched manuals are primary for local option behavior. The interpretation is also bounded by:

- [Linux kernel seccomp-filter documentation](https://docs.kernel.org/userspace-api/seccomp_filter.html), which states that syscall filtering is one sandbox component rather than a complete sandbox;
- [Linux kernel no-new-privileges documentation](https://docs.kernel.org/userspace-api/no_new_privs.html), which states that the bit is inherited and cannot be unset but does not prevent non-`execve` privilege changes;
- [Linux kernel Yama documentation](https://docs.kernel.org/admin-guide/LSM/Yama.html), which documents ptrace policy as a runtime prerequisite and preserves direct parent/child tracing only under some modes;
- [Python 3.10 import-system documentation](https://docs.python.org/3.10/reference/import.html), which distinguishes already initialized `__main__`, built-in, frozen and path-loaded modules; and
- [GNU `timeout` documentation](https://www.gnu.org/software/coreutils/manual/html_node/timeout-invocation.html), which documents process-group, foreground, kill and ambiguous `137` behavior.

These references do not substitute for future installed activation evidence.

## 5. Fixed kernel and process facts

| Fact | Observed value | Controlling interpretation |
| --- | --- | --- |
| kernel release | `5.15.0-177-generic` | product fact only; no feature was activated |
| architecture | `x86_64` | sole inspected architecture |
| `/proc/sys/kernel/unprivileged_userns_clone` | present; `1` | user namespaces are not administratively disabled by this switch; usability remains untested |
| `/proc/sys/user/max_user_namespaces` | present; `31585` | nonzero limit; not an allocation or permission proof |
| inspection `CapEff` | `0000000000000000` | no effective capabilities in the inspected process |
| inspection `NoNewPrivs` | `0` | not set during inspection; `setpriv --nnp` is only a future candidate |
| cgroup v2 controllers | `cpuset cpu io memory hugetlb pids rdma misc` | `pids` exists; no delegated writable child, `pids.max` or teardown authority was inspected |
| `/sys/fs/cgroup/cgroup.type` | absent at the inspected root path | no non-root cgroup type or domain/threaded placement claim |
| inspection cgroup | `0::/user.slice/user-1000.slice/session-84137.scope` | one SSH inspection scope only |

One Main Control inspection observed namespace links `cgroup:[4026531835]`, `ipc:[4026531839]`, `mnt:[4026531841]`, `net:[4026531840]`, `pid:[4026531836]`, `time:[4026531834]`, `user:[4026531837]` and `uts:[4026531838]`. The independent kernel review observed the same namespace identities in a separate SSH inspection scope. No namespace was created or entered.

## 6. Provider fingerprint table

### 6.1 Exact candidate identities

| Candidate | Availability and canonical path | Fixed stat tuple | SHA-256 | Product/build | Package/source provenance | ELF build ID |
| --- | --- | --- | --- | --- | --- | --- |
| `/usr/bin/bwrap` | absent before and after | not applicable | not applicable | unavailable | no present candidate file; no fallback queried | not applicable |
| `/usr/bin/unshare` | present; `/usr/bin/unshare` | `64513|9057|81ed|755|0|0|root|root|31336|1772813404|1773382197` | `72a34e6ba98a59f1da0c7b4d8c9722b746b5ade54e4d7e8de8e519c2993858ad` | `unshare from util-linux 2.37.2` | `util-linux|2.37.2-4ubuntu3.5|amd64|ii |util-linux|2.37.2-4ubuntu3.5` | `7117e14f0d1c89fbd91fd6271a2a0e72fde47710` |
| `/usr/bin/setpriv` | present; `/usr/bin/setpriv` | `64513|9051|81ed|755|0|0|root|root|39304|1772813404|1773382197` | `960ac94d6b4d095d67d44b00b9b23b3f5e5e609d4539d2223c7c70ed559108ba` | `setpriv from util-linux 2.37.2` | same `util-linux` binary/source package | `cfb744e3c51448238b95cc05fc7397364ab38758` |
| `/usr/bin/strace` | present; `/usr/bin/strace` | `64513|2171|81ed|755|0|0|root|root|1972848|1645004241|1719848457` | `38a5c75cb29dd85ddd7780d54f5bf595554d7a1b5c42524b23065f5dc4c4b01d` | `strace -- version 5.16`; stack trace via libunwind; m32/mx32 personalities enabled | `strace|5.16-0ubuntu3|amd64|ii |strace|5.16-0ubuntu3` | `a96352a6275e8d696622277f522fafe9e2252f7c` |
| `/usr/bin/timeout` | present; `/usr/bin/timeout` | `64513|1836|81ed|755|0|0|root|root|39880|1707363999|1719848457` | `8d21b4cf1b204cc2387377a63c542ecdd0ae0895613db67ceb7da1e253110741` | `timeout (GNU coreutils) 8.32` | `coreutils|8.32-4.1ubuntu1.2|amd64|ii |coreutils|8.32-4.1ubuntu1.2` | `5a6c90dcaf689dabf04f9f2d743ccacb2b1c9bdd` |

Every present candidate is root-owned mode `0755`, has no setuid/setgid bit and returned no file capability through the fixed `/usr/sbin/getcap -n` read. This does not grant privilege or prove future invocation under the same LSM policy.

All present candidate canonical paths, stat tuples and hashes were identical after version/help/manual/package/ELF inspection. `/usr/bin/bwrap` remained absent.

### 6.2 Installed manual identities

| Manual | SHA-256 |
| --- | --- |
| `/usr/share/man/man1/unshare.1.gz` | `6e52fed7b305f51c3582bc1913803cfefeb4b362b58dad0eaaa37b32a9ff8468` |
| `/usr/share/man/man1/setpriv.1.gz` | `a5ecc5564283d5d53a0817477fc10e93461aa0b3891cc145ca5aaa4976099fa2` |
| `/usr/share/man/man1/strace.1.gz` | `2238f1411d71f9884fe4f79ef28a1b38b1fc0803fa31ebf86b74373b6d4d767d` |
| `/usr/share/man/man1/timeout.1.gz` | `383d02396313b93bf3d6390514cdd5e351aadbfe81a016fe1167ee438bbb0b3c` |
| `/usr/share/man/man2/ptrace.2.gz` | `99c143e1253bddc29499e1a2567ef02dd534b68fccfd3e1a27b0db9bb3357772` |
| `/usr/share/info/coreutils.info.gz` | `1650ed752c98769cd3e6c270579a5a7f079ce85c267df1007ad2b1dbd0b4a20e` |

### 6.3 Dynamic interpreter and library identities

| Supplied path | Canonical path | SHA-256 | Package/source |
| --- | --- | --- | --- |
| `/lib64/ld-linux-x86-64.so.2` | `/usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2` | `9eb34cb2da3ae2a9398cc09b3cd2d069563ec40d9858cb711af15cd23fa80abf` | `libc6:amd64` / `glibc 2.35-0ubuntu3.13` |
| `/lib/x86_64-linux-gnu/libc.so.6` | `/usr/lib/x86_64-linux-gnu/libc.so.6` | `c53819710b163d3f1d2541778590d58d3ef31cb0ed75adcbe059faac68c1e72d` | `libc6:amd64` / `glibc 2.35-0ubuntu3.13` |
| `/lib/x86_64-linux-gnu/libcap-ng.so.0` | `/usr/lib/x86_64-linux-gnu/libcap-ng.so.0.0.0` | `881e0e171e84d9c0370475cd36bd998e6095180929cb79545620c6b180d9aa2e` | `libcap-ng0 0.7.9-2.2build3` |
| `/lib/x86_64-linux-gnu/libunwind-ptrace.so.0` | `/usr/lib/x86_64-linux-gnu/libunwind-ptrace.so.0.0.0` | `f791a9b0b01faa13a65ee066d2351d2e38a23d6c3752f75eebeaf0fc5c7d56f4` | `libunwind8 1.3.2-2build2.1` |
| `/lib/x86_64-linux-gnu/libunwind-x86_64.so.8` | `/usr/lib/x86_64-linux-gnu/libunwind-x86_64.so.8.0.1` | `1077e265bdd76ed4f2d628ea29150eb98f5c7c8f5a30004a561e6e93a2a6f097` | `libunwind8 1.3.2-2build2.1` |
| `/lib/x86_64-linux-gnu/libunwind.so.8` | `/usr/lib/x86_64-linux-gnu/libunwind.so.8.0.1` | `5d1f6f104f79698e137c9f17c4b0317dfd96816c0eb6a87c50619a41472ca382` | `libunwind8 1.3.2-2build2.1` |
| `/lib/x86_64-linux-gnu/liblzma.so.5` | `/usr/lib/x86_64-linux-gnu/liblzma.so.5.2.5` | `7fa51c1500cb9fcc4c7d69b7fe0a6d7203cfe6af64373f6c411c5445ef1b402c` | `liblzma5` / `xz-utils 5.2.5-2ubuntu1.1` |

`unshare` and `timeout` directly need the loader and libc. `setpriv` additionally needs libcap-ng. `strace` directly needs libunwind-ptrace and libunwind-x86_64 and transitively resolves libunwind and liblzma. All listed identities were stable pre/post. Package metadata is useful provenance but is not a reproducible-build or source-tree equivalence proof.

### 6.4 Exact locally advertised options relevant to this gate

The following option spellings come from the installed candidates' fixed `--help` output. They record availability only; none was activated.

| Candidate | Exact relevant installed option spellings | Planning interpretation |
| --- | --- | --- |
| `bwrap` | not applicable because the fixed path is absent | no option or behavior is available for selection |
| `unshare` | `-m, --mount[=<file>]`; `-u, --uts[=<file>]`; `-i, --ipc[=<file>]`; `-n, --net[=<file>]`; `-p, --pid[=<file>]`; `-U, --user[=<file>]`; `-C, --cgroup[=<file>]`; `-T, --time[=<file>]`; `-f, --fork`; `--map-user=<uid>|<name>`; `--map-group=<gid>|<name>`; `-r, --map-root-user`; `-c, --map-current-user`; `--kill-child[=<signame>]`; `--mount-proc[=<dir>]`; `--propagation slave|shared|private|unchanged`; `--setgroups allow|deny`; `--keep-caps`; `-R, --root=<dir>`; `-w, --wd=<dir>`; `-S, --setuid <uid>`; `-G, --setgid <gid>` | namespace, mapping, root-view, launch and child-death primitives are advertised; the help does not advertise a sealed-root builder, inherited-descriptor closer or syscall-denial policy |
| `setpriv` | `--nnp, --no-new-privs`; `--ambient-caps <caps,...>`; `--inh-caps <caps,...>`; `--bounding-set <caps>`; `--ruid <uid|user>`; `--euid <uid|user>`; `--rgid <gid|user>`; `--egid <gid|group>`; `--reuid <uid|user>`; `--regid <gid|group>`; `--clear-groups`; `--keep-groups`; `--init-groups`; `--groups <group,...>`; `--securebits <bits>`; `--pdeathsig keep|clear|<signame>`; `--selinux-label <label>`; `--apparmor-profile <pr>`; `--reset-env` | privilege, identity, environment and parent-death controls are advertised; no namespace, filesystem, syscall, socket, process/thread-denial or observer control is advertised |
| `strace` | `-f, --follow-forks`; `-ff, --follow-forks --output-separately`; `-I INTERRUPTIBLE, --interruptible=INTERRUPTIBLE`; `-e trace=...`; groups `%desc`, `%file`, `%ipc`, `%net`, `%process`, `%signal`; `-e signal=SET`; `-e status=SET`; statuses `successful`, `failed`, `unfinished`, `unavailable`, `detached`; `-P PATH, --trace-path=PATH`; `-o FILE, --output=FILE`; `-s STRSIZE, --string-limit=STRSIZE`; `-e decode-fds=SET`; `-y, --decode-fds[=path]`; `-yy, --decode-fds=all`; `--decode-pids=pidns`; `-Y, --decode-pids=comm`; `--seccomp-bpf`; `-e read=SET`; `-e write=SET`; `-k, --stack-traces`; `-e inject=...`; `-e fault=...`; `-p PID, --attach=PID` | relevant syscall-family observation and output controls are advertised, together with leakage- and behavior-changing options that a future contract must prohibit; installed help advertises no `--kill-on-exit` |
| `timeout` | `--preserve-status`; `--foreground`; `-k, --kill-after=DURATION`; `-s, --signal=SIGNAL`; `-v, --verbose` | an outer signal ceiling and optional later KILL escalation are advertised; help states foreground children are not timed out and leaves exact tree ownership outside this tool |

No unsupported option name may be inferred from a newer manual or another installation. Any future argv must be separately frozen against these pinned identities and rechecked immediately before activation.

### 6.5 Privilege, daemon and host-policy dependencies

| Candidate | User namespace | Ptrace | Capabilities, setuid or privilege | Daemon contact | System-wide dependency |
| --- | --- | --- | --- | --- | --- |
| `bwrap` | unproved | unproved | absent binary; no local claim | unproved | acquisition and all runtime prerequisites unproved |
| `unshare` | required for the contemplated unprivileged namespace design; actual creation was not tested | no | binary is not setuid and has no file capabilities; mappings can grant capabilities only inside owned namespaces, which a later design must drop | none advertised or contacted | kernel userns switches, LSM policy and mount/namespace permissions govern feasibility; none was changed |
| `setpriv` | no intrinsic requirement | no | binary is not setuid and has no file capabilities; it can only apply transitions permitted to the invoking process and is retained solely for reduction | none advertised or contacted | selected SELinux/AppArmor profiles would depend on host policy, but neither option is selected |
| `strace` | no intrinsic requirement | yes | binary is not setuid and has no file capabilities; child launch may work without `CAP_SYS_PTRACE`, whereas attach and some targets depend on credentials, dumpability, Yama/LSM and capabilities | none advertised or contacted | ptrace/Yama/LSM policy controls feasibility and remains a future fixed read/activation prerequisite |
| `timeout` | no | no | binary is not setuid and has no file capabilities; signaling remains constrained by ordinary process ownership/permission | none advertised or contacted | no special system-wide configuration is identified; process-group/session behavior still requires activation evidence |

No candidate contacted a daemon. No sysctl, LSM profile, capability, identity, namespace or system-wide configuration was changed.

## 7. Provider decision matrix

Recommendations in this matrix are not Owner approval.

| Candidate | Availability and provenance completeness | Privilege and kernel prerequisites | Capability coverage | Unsupported controls and leakage | Determinism/reversibility | Source overlap and future evidence cost | Recommendation | Exact prerequisite before Owner selection |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `bwrap` | absent; no installed binary fingerprint | unknown on this host because absent | none available | every proposed behavior is unproved | no activation occurred; absence is fully reversible only through a separately authorized environment change | any installation/image/package action is outside this gate and outside controller-only source | reject for this fixed host fingerprint; do not substitute | separately approved immutable acquisition/environment gate and full re-fingerprint, if Owner ever reopens it |
| `unshare` | strong installed binary/package/manual/link identity; no reproducible build proof | userns switch `1` and max `31585` make unprivileged design plausible; CapEff is zero; actual creation/LSM behavior untested | user, mount, network, PID, IPC, cgroup namespaces; `--root`; private propagation; mapping; `--fork`; `--kill-child` | does not construct the sealed read-only root, close inherited FDs, deny socket syscalls or deny `fork`/`clone`/threads; mapping root grants namespace capabilities that must later be dropped | disposable namespaces are reversible, but exact mount/PID/tree composition and teardown are unproved | requires exact bootstrap topology and likely a sealed-root preparer plus syscall/process enforcement surface | retain only as a partial D1 primitive; do not select D1 | Owner-approved enforcement composition and static/activation canaries, including the missing artifact scope |
| `setpriv` | strong installed identity; linked libcap-ng and manual pinned; no reproducible build proof | no setuid/file caps; can set `no_new_privs`, groups, capability sets and `pdeathsig`; LSM behavior remains future evidence | privilege reduction, environment reset and parent-death candidate | no namespace, filesystem, socket, syscall, fork/thread or observer control; `pdeathsig` can be affected by credential/LSM transitions | one-shot wrapper is reversible; exact ordering and inherited-FD state unproved | controller invocation only if all policy is expressible as argv; any external profile is new scope | retain only as a partial D1 primitive paired after namespace setup | exact uid/gid/group/capability/nnp/pdeathsig contract and no-test activation proof |
| `strace` | strong installed identity and exact v5.16 feature/manual evidence; no reproducible build proof | ptrace-based; same-child launch may avoid elevated capability under some policies, but exact LSM/Yama/dumpable behavior was not inspected or executed | can report file/descriptor, network, process, exec, signal and abnormal-exit syscalls; `-f` documents `fork`, `vfork`, `clone` following | raw filenames are always printed in full; arguments/socket identities can leak; tracer changes timing/parentage; descendants may survive interrupt; killed/detached/unfinished events are incomplete; `--seccomp-bpf` filters tracing stops and falls back to normal tracing, not D1 denial | disposable and discardable, but terminal completeness and loss behavior need canaries | parent/controller must quarantine, sanitize, reconcile and destroy raw trace; exact placement relative to denial is unresolved | conditionally retain as O1 candidate only; do not approve | Owner-approved observer placement, ptrace policy read, raw-output channel/schema, completeness/fault canaries and discard contract |
| `timeout` | strong installed binary/package/manual/link identity; no reproducible build proof | ordinary same-user process signaling; no namespace or provider authority | TERM ceiling, optional later KILL escalation, status signaling | `--foreground` excludes children; escaped groups/sessions are not guaranteed; `137` cannot distinguish whether command or timeout was killed; timeout death may leave command alive; owns no observer or sandbox finalization | highly reversible wrapper; numeric behavior and process-tree topology unproved | wrapper-only if exact argv suffices; controller still owns sanitized lifecycle and recovery | conditionally retain as an outer ceiling candidate only | exact non-foreground topology, numeric derivation, process-tree/failure canaries and teardown ownership |

## 8. D1 denial coverage matrix

| Required D1 outcome | `unshare` contribution | `setpriv` contribution | Remaining gap | Gate result |
| --- | --- | --- | --- | --- |
| read-only or absent filesystem | mount namespace, private propagation and `--root` are available | none | no exact sealed root is prepared; no bind/read-only policy; inherited FDs unclosed | stopped |
| private non-searchable exact source view | can consume a root directory | none | does not construct or attest exact files, ownership, modes, libraries or absence of package search | stopped |
| no database-harness file | could omit it from a separately prepared root | none | no root/view exists; A1 does not deny direct file reads | stopped |
| no MariaDB/Docker pathname sockets | could hide paths in a sealed mount view | none | no sealed view or inherited-FD closure; socket syscall remains available | stopped |
| no external network | new network namespace is a partial isolation primitive | capability drop may prevent later configuration | namespace creation untested; network namespace is not a socket-syscall denial | stopped |
| no loopback or Unix-socket operation | network namespace isolates host stack and abstract Unix-socket namespace | none | path sockets depend on view; child can still call socket syscalls; no seccomp denial | stopped |
| no child-created process, thread or queue | PID namespace and `--kill-child` can improve later cleanup | none | neither denies `fork`, `vfork`, `clone`, `clone3`, thread or queue creation; no approved seccomp or delegated `pids.max` | Blocker |
| no privilege escalation | user namespace contains privilege to owned namespaces | `--nnp`, capability/group drops and fixed IDs are partial controls | exact post-namespace drop order and LSM result unproved; `NoNewPrivs` was `0` during inspection | stopped |
| deterministic parent death | `--kill-child` plus PID namespace is a candidate | `--pdeathsig` is a candidate | wrapper/tracer/watchdog topology, races, signal ownership and exact reaping unproved | High gap |
| exact teardown ownership | namespaces end when final members exit | none | no controller implementation, observer completion, escaped-process proof, recovery or evidence discard exists | High gap |

Namespaces alone therefore cannot qualify D1. The missing process/thread/socket enforcement requires a later exact mechanism such as a seccomp policy and/or a delegated pids envelope, plus a sealed-root preparation contract. No such mechanism or artifact is approved here.

## 9. O1 observation and leakage matrix

| Required observation | Installed `strace` evidence | Residual |
| --- | --- | --- |
| file reads/writes | `%file`, `%desc`, `open`-family and descriptor syscalls can be traced | filters/personality/unknown-call coverage and exact sanitizer mapping need canaries |
| network and Unix sockets | `%net`, socket syscalls and decoded socket descriptors are available | raw addresses and paths are leakage-bearing; no body dump option may be used |
| process/thread creation | `-f` documents following `fork`, `vfork` and `clone` descendants | `clone3`, personality coverage, escaped descendants and tracer failure require evidence |
| executable transitions | `%process` and `execve` tracing are supported | exact transition/identity schema unauthored |
| signals and abnormal termination | signals and termination are printed; status classes include unfinished, unavailable and detached | any such incomplete class must force discard |
| observer independence | external launch can keep tracer outside the child | `strace -> unshare -> child` observes before denial is active; `unshare -> strace -> child` weakens independence; post-denial attach needs an unauthored stopped-child handshake |
| completeness | normal command exit is reflected and `-f` follows documented descendants | kill, detach, interruption, output failure and escaped descendant can lose evidence |
| behavior preservation | none | ptrace changes timing and parentage; installed manual states traced processes run slowly |
| sanitized evidence | raw stream can later feed a fixed sanitizer | filenames are always full; arguments, PIDs, sockets and signals may leak; raw output cannot be promoted |
| teardown | tracer can exit with command status in ordinary flow | observer completion must precede sandbox teardown and evidence promotion; killed/incomplete is discard-only |

`strace --seccomp-bpf` is rejected as a D1 control. The installed manual says it reduces ptrace stops for selected traced syscalls, requires `-f`, is inapplicable to `-p`, may fail, and on failure proceeds with ordinary tracing. It is not a fail-closed policy denying the child's syscalls.

The only supportable recommendation is conditional O1 retention. A later gate must freeze protected raw-output ownership, prohibit `-e read=`/`-e write=` body dumps, derive only allowlisted sanitized counters/enums, prove terminal completeness and destroy raw material after accepted sanitization or discard.

A future contract must also prohibit operational `-p` attachment, output-command pipe forms where `-o` begins with `|` or `!`, `-yy`, `-Y`, stack tracing, and injection/fault/poke options unless an Owner later accepts a concrete need. Installed 5.16 exposes no `--kill-on-exit`; interruption can detach and leave tracees running. Observer death, detach, parse failure, truncation, a missing terminal record or nonzero observer finalization is discard-only and requires independent teardown.

## 10. Bootstrap and source-only ordering contract

The requested stages are frozen for planning as follows:

1. **Supervisor interpreter startup.** A future exact-literal `/usr/bin/python3.10` invocation starts with no repository or test authority. Startup already initializes `__main__`, built-in, frozen and possibly file-backed modules.
2. **Already-loaded inventory.** Bind every already-loaded module as built-in, frozen, file-backed or extension, with origin/hash/provider where applicable. No module already loaded may be retroactively described as source-only.
3. **Supervisor initialization.** The same controller file enters an explicit parent mode; the parent never imports the fixture. The current file-backed imports at lines 8-12 create a C1 ordering conflict unless the Owner resolves the preamble policy.
4. **Denial activation.** Parent creates and attests the selected D1 envelope before the child imports repository code. No candidate is selected today.
5. **Observer activation.** Independent O1 must be active and acknowledged without a coverage gap. The exact external placement relative to D1 is unresolved.
6. **Child interpreter start.** Parent launches exactly one child with the same controller file, explicit literal runner mode, exact inherited descriptors and parent-death ownership.
7. **Source-only enforcement.** Child establishes cache denial and exact source policy before the controller's current line-8 import. Append-only policy is too late. If this cannot occur within the same controller file using only already bound startup primitives, stop for source/runtime scope expansion.
8. **Canonical controller alias.** Reject a conflicting module; bind the already running child controller exactly once under `erp_workspace_ui.tests.finance_gl_trial_balance_evidence_controller`; prevent double execution.
9. **Sealed parent packages.** Create only inert `erp_workspace_ui` and `erp_workspace_ui.tests` identities with empty/non-searchable package paths.
10. **Exact fixture-file load.** Verify and load only the frozen fixture source; no cache, application-root insertion, database harness or other repository module; reconcile the import ledger.
11. **Suite construction.** Instantiate exactly the frozen ten literal methods through direct `TestCase(methodName)`, put them in one flat ordered `unittest.TestSuite`, and prove exact IDs, class, count, order and uniqueness before any method starts.

### 10.1 Owner bootstrap choices

| Choice | Meaning | Consequence | Recommendation status |
| --- | --- | --- | --- |
| `B1` | keep C1 for parent and child; add a same-controller preamble before line 8; bind startup modules rather than relabeling them | preserves controller-only source but requires exact built-in/frozen bootstrap proof and a non-append-only controller edit | recommended for later Owner consideration only |
| `B2` | narrow C1 to child-only and provenance-bind ordinary supervisor imports | simpler parent but changes the accepted C1 boundary | not recommended without an explicit Owner amendment |
| `B3` | external `-c`, `sitecustomize`, bootstrap module, profile or separate runner | can activate earlier but creates another source/runtime surface | prohibited unless concrete evidence and Owner scope approval |

No bootstrap choice is approved. `B1` is planning advice only.

## 11. Watchdog, process tree and teardown

`/usr/bin/timeout` may remain only a candidate outer ceiling owner:

- parent-owned timeout and child signal handling are distinct;
- `--foreground` is not supportable because installed help states command children are not timed out in that mode;
- default process-group behavior still cannot prove termination of a descendant that changes group/session;
- a later TERM/KILL design needs independently derived values; no duration is selected here;
- GNU documentation states status `137` cannot distinguish whether `timeout` or its command received KILL, and if `timeout` itself is killed the command may remain alive;
- `unshare --kill-child`, a PID namespace and `setpriv --pdeathsig` are partial complementary mechanisms, not a proven composition;
- observer completion must occur before sandbox teardown and evidence promotion;
- child/supervisor/observer/timeout death, a missing receipt, an escaped member or incomplete teardown is discard-only; and
- timeout statuses `124`, `125`, `126`, `127` or `137` remain non-promotable failure classifications until a later exact protocol is approved;
- recovery must target exact recorded identities and may never use broad process discovery or live-environment action.

No exit `65/70`, duration, grace, process-group layout, signal set, recovery command or evidence-promotion rule is authorized.

## 12. Findings by severity

### Blocker

1. **No complete D1 provider exists in the fixed candidate scope.** `/usr/bin/bwrap` is absent. Present `unshare`/`setpriv` do not construct the exact read-only source view and cannot deny runner-created processes, threads or socket syscalls. A seccomp/pids/sealed-root mechanism or another artifact is required but unapproved.
2. **C1 bootstrap ordering is unresolved.** Controller file-backed imports begin at lines 8-12, while the requested source-only stage is later. Source-only enforcement cannot be retroactive; the Owner must select `B1`, explicitly amend to `B2`, or approve another surface through `B3`.
3. **No executable control plane exists.** The committed controller is parser-only through line 633 and contains none of the proposed parent/child, denial, observer, result, watchdog, evidence or teardown behavior.

These Blockers do not prevent this factual documentation receipt. They prevent provider selection, source authoring and every execution claim.

### High

1. **Observer placement is unresolved.** Keeping `strace` outside D1 conflicts with denial-before-observer ordering unless a race-free stopped-child/bootstrap protocol is frozen; placing it inside weakens independence.
2. **Raw observation is leakage-bearing.** Exact installed documentation states filenames are printed in full regardless of string limit, and syscall arguments may expose paths, socket identities, PIDs and values. Raw trace can never be promoted.
3. **Teardown is not deterministic.** `timeout`, PID namespaces, `--kill-child` and `--pdeathsig` exist individually, but exact process-tree termination, tracer completion, reaping, recovery and evidence discard are unproved.
4. **A1 does not provide independent unreachability.** Exact-file loading prevents ordinary package search but cannot deny direct database-harness reads or database/socket connections without D1.
5. **Namespace feasibility is not activation proof.** Userns sysctls and options are favorable, but LSM behavior, actual mappings, capability drop and runtime availability were intentionally not executed.

### Medium and deferred

1. Package/source metadata does not prove reproducible binary-to-source equivalence.
2. Exact ptrace/Yama/LSM policy for a future child remains unread and unexecuted under this gate's fixed kernel path scope.
3. Cgroup v2 advertises `pids`, but no delegated writable child cgroup, type, placement, `pids.max` value or teardown contract exists.
4. Direct `/usr/bin/python3.10` behavior, complete import provenance, provider activation, numeric limits and exit `65/70` remain deferred.

### Accounting result

No accounting-semantic finding was introduced. The source remains parser-only and cannot claim GL/TB correctness, `gl_reconstructed`, company/permission/dimension semantics, E2-B1 acquisition, Finance closure, execution or accounting authority.

## 13. Bounded reviews and Main Control synthesis

| Review | Accepted finding | Rejected inference | Deferred item |
| --- | --- | --- | --- |
| Linux sandbox/kernel | no complete D1 provider; `unshare/setpriv` are partial; bwrap absent | userns switches or namespaces alone prove isolation | exact seccomp/pids/sealed-root mechanism and activation |
| CPython bootstrap/import order | startup origins must be bound; controller policy must precede line 8 | controller can retroactively enforce source-only or append policy after line 633 | Owner `B1/B2/B3` choice and complete import ledger |
| observer/security/leakage | `strace` conditionally covers relevant syscall families; raw trace is quarantined/discard-only | availability, `-f` or `--seccomp-bpf` proves complete/safe observation | ptrace policy, placement, sanitizer and fault canaries |
| result/watchdog/teardown | `timeout` is an outer ceiling candidate only; supervisor remains lifecycle owner | timeout alone terminates exact process trees or finalizes evidence | numeric derivation, topology, signals, recovery and teardown |
| accounting/release | accounting preservation passes; release remains stopped | parser success proves Finance/accounting correctness | every separated future approval |

Main Control accepts the evidence-backed Blocker and High findings and performs one synthesis pass. It rejects provider activation, a fallback search, package installation, `strace --seccomp-bpf` as D1, ordinary root insertion, default unittest/JUnit evidence, inferred source-only startup, inferred database-harness denial and any numeric convention.

## 14. Recommended Owner choices - all unapproved

1. **D1:** do not select D1 from the current fixed tools. Either keep execution stopped or separately authorize a planning-only missing-enforcement decision covering an exact seccomp/pids/sealed-root provider and every new artifact/path.
2. **O1:** conditionally retain `/usr/bin/strace` as the sole fixed observer candidate, subject to external placement, ptrace policy, protected raw-output ownership, fixed sanitizer, completion/fault evidence and discard-only failure.
3. **Watchdog:** conditionally retain `/usr/bin/timeout` as an outer ceiling candidate only, composed later with exact PID-namespace, `--kill-child`, `pdeathsig`, observer and supervisor teardown evidence.
4. **Bootstrap:** prefer `B1` for later Owner consideration: same-controller parent/child modes with a pre-line-8 policy and separately bound startup modules. This is not source-authoring approval.
5. **Scope:** keep controller-only future source scope unless the missing D1/bootstrap mechanism proves another exact artifact unavoidable. If that occurs, stop and return an exact scope-expansion choice before writing it.

The recommended next planning-only decision task is **GL/TB D1 Missing Enforcement Provider and C1 Bootstrap Authority Amendment**. It must not begin automatically.

## 15. Exact future scopes and allowlists - all unapproved

### 15.1 Current source-authoring allowlist

```json
[]
```

### 15.2 Sole future source candidate

```text
impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/tests/finance_gl_trial_balance_evidence_controller.py
```

No seccomp policy, sandbox profile, sealed-root preparer, observer sanitizer, runner, initializer, fixture, database harness, package file or fifth source is approved. Any additional artifact requires Owner scope approval.

### 15.3 Future read-only candidate allowlist

Repository paths:

```text
impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/tests/finance_gl_trial_balance_evidence_controller.py
impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/tests/test_finance_gl_trial_balance_e2b1_parser_fixtures.py
impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/tests/test_finance_gl_trial_balance_source_proof.py
impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/__init__.py
impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/tests/__init__.py
impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/finance-accounting-cycle2-gl-tb-e2b1-parser-runner-residual-import-isolation-authority-amendment-2026-07-22.md
impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/finance-accounting-cycle2-gl-tb-e2b1-parser-sandbox-observer-bootstrap-provider-fingerprint-2026-07-22.md
impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/README.md
```

Provider, manual and kernel paths:

```text
/usr/bin/bwrap
/usr/bin/unshare
/usr/bin/setpriv
/usr/bin/strace
/usr/bin/timeout
/usr/share/man/man1/unshare.1.gz
/usr/share/man/man1/setpriv.1.gz
/usr/share/man/man1/strace.1.gz
/usr/share/man/man1/timeout.1.gz
/usr/share/man/man2/ptrace.2.gz
/usr/share/info/coreutils.info.gz
/lib64/ld-linux-x86-64.so.2
/lib/x86_64-linux-gnu/libc.so.6
/lib/x86_64-linux-gnu/libcap-ng.so.0
/lib/x86_64-linux-gnu/libunwind-ptrace.so.0
/lib/x86_64-linux-gnu/libunwind-x86_64.so.8
/lib/x86_64-linux-gnu/libunwind.so.8
/lib/x86_64-linux-gnu/liblzma.so.5
/proc/sys/kernel/unprivileged_userns_clone
/proc/sys/user/max_user_namespaces
/proc/self/status
/sys/fs/cgroup/cgroup.controllers
/sys/fs/cgroup/cgroup.type
/proc/self/cgroup
/proc/self/ns/cgroup
/proc/self/ns/ipc
/proc/self/ns/mnt
/proc/self/ns/net
/proc/self/ns/pid
/proc/self/ns/pid_for_children
/proc/self/ns/time
/proc/self/ns/time_for_children
/proc/self/ns/user
/proc/self/ns/uts
```

Exact helper paths already used for read-only evidence may be re-fingerprinted only through a later gate: `/usr/bin/realpath`, `/usr/bin/stat`, `/usr/bin/sha256sum`, `/usr/bin/readelf`, `/usr/bin/ldd`, `/usr/bin/dpkg-query`, `/usr/sbin/getcap`, `/usr/bin/zgrep`, `/usr/bin/zcat`, `/usr/bin/sed`, `/usr/bin/grep`, `/usr/bin/cat`, `/usr/bin/uname`, `/usr/bin/readlink`, `/usr/bin/test`, `/usr/bin/printf`, `/usr/bin/base64` and `/usr/bin/bash`.

No glob, PATH search, directory enumeration, alternative provider, operational process, socket, container, database, site or live path is allowed.

### 15.4 Current Python and provider execution allowlists

```json
{
  "python_observation_or_execution": [],
  "provider_activation_or_canary": [],
  "namespace_or_sandbox_creation": [],
  "trace_or_timeout_execution": [],
  "fixture_or_test_execution": []
}
```

The version/help reads completed by this gate do not authorize reuse or provider activation.

## 16. Validation and future documentation staging allowlist

Main Control validates after writing:

- repository root, branch, HEAD/upstream `c13a2d5972e6ef8131ad8239359fee3e9e89dde2` and `0/0`;
- empty Git index;
- candidate worktree scope exactly this document and README plus the four protected exclusions;
- unchanged controller, fixture, database-harness and exclusion hashes/statuses;
- `git diff --check HEAD`;
- strict UTF-8 without BOM, replacement characters, mojibake or trailing whitespace;
- balanced Markdown fences and valid local references;
- exactly one README entry;
- decision remains `stopped_for_parser_provider_gap`;
- all candidate recommendations remain unapproved;
- current Python and provider activation allowlists remain empty; and
- no provider, namespace, sandbox, trace, timeout, source, Python, fixture, Docker, infrastructure, live or accounting authority is introduced.

The exact future documentation staging allowlist, if separately authorized, is:

1. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/finance-accounting-cycle2-gl-tb-e2b1-parser-sandbox-observer-bootstrap-provider-fingerprint-2026-07-22.md`
2. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/README.md`

No staging, commit or push is authorized here.

## 17. Final control statement

**Decision:** `stopped_for_parser_provider_gap`

The fixed candidate set supplies useful namespace, privilege-drop, observation and ceiling primitives but no complete, selectable D1 provider. Provider composition, C1 bootstrap authority, observer placement, sanitized evidence and deterministic teardown remain Owner decisions behind additional planning/read gates.

No Python execution, import, compilation, collection, fixture, provider activation, namespace, sandbox, ptrace trace, timeout, cgroup creation, mount, seccomp filter, source authoring, Docker, infrastructure, Frappe, Bench, MariaDB, SQL, acquisition, runtime, live action, staging, commit, push, migration, permission change, protected gate or accounting action occurred.
