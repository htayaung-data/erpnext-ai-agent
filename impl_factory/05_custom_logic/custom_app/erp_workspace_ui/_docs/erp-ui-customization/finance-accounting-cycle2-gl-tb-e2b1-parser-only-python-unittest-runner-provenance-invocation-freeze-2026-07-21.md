# Finance & Accounting Cycle 2 GL / Trial Balance E2-B1 Parser-Only Python/Unittest Runner Provenance and Exact Invocation Freeze Gate

Date: 2026-07-21

Repository: `/home/deploy/erp-projects/erpai_project1_erpnext_ui_design`

Branch: `feature/erpnext-ui-design`

Verified baseline: `d639d4955015578027c5709096db57bf78c8c43a`

Authority: Main Control v2; planning, read-only provenance and documentation only

Decision: `stopped_for_parser_runner_provenance_gap`

## 1. Outcome and controlling effect

The published parser-only source boundary resolves the former module-level Frappe/MariaDB import problem. The committed fixture module and controller are statically pure, their package initializers are inert, and direct construction of the ten literal `TestCase(methodName)` objects followed by one explicit `unittest.TestSuite` remains the preferred future runner design.

The installed CPython 3.10 `unittest` sources now support the proposed named-construction, ordered-suite, class-setup, callback and teardown semantics. That is a material narrowing of the prior [parser-runner stop](finance-accounting-cycle2-gl-tb-e2b1-parser-fixture-execution-contract-isolated-runner-freeze-2026-07-20.md).

The exact invocation cannot yet be frozen. Static evidence does not establish which source/cache/frozen bytes the future interpreter will execute across the complete new import closure; no accepted constrained import mechanism makes the database harness independently unreachable; and no accepted external watchdog, denial, side-effect observer, result promotion or recovery owner exists. The current controller also contains no runner, argument boundary, result adapter or finalizer.

This is a tooling, import-provenance and control-plane stop. It is not an accounting-design failure and does not reopen parser semantics, fixture completeness, database accounting tests or the completed parser source-boundary review.

No Python import, compilation, collection, test or runner execution is authorized. The execution allowlist remains empty.

## 2. Verified repository and protected state

| Item | Verified value |
| --- | --- |
| repository root | `/home/deploy/erp-projects/erpai_project1_erpnext_ui_design` |
| branch | `feature/erpnext-ui-design` |
| local HEAD | `d639d4955015578027c5709096db57bf78c8c43a` |
| configured upstream | `origin/feature/erpnext-ui-design` |
| upstream revision | `d639d4955015578027c5709096db57bf78c8c43a` |
| ahead/behind | `0/0` |
| Git index | empty |

The authoritative committed sources remain:

| Surface | SHA-256 |
| --- | --- |
| [parser-only fixture module](../../erp_workspace_ui/tests/test_finance_gl_trial_balance_e2b1_parser_fixtures.py) | `b46dc6b02db57b0611346abad8665567fecf91456ce1db6fd488af9cbfea3afb` |
| [evidence controller](../../erp_workspace_ui/tests/finance_gl_trial_balance_evidence_controller.py) | `69e67523d893b38b6559c75152f5802f6e5acf19642fd95d82cc2631d5a485b3` |
| [database harness](../../erp_workspace_ui/tests/test_finance_gl_trial_balance_source_proof.py) | `c8d0bb0556f9abb04e1be69c1d67a7f92c4ed37a64d8270d84339ad590e9cea5` |

The four unrelated protected worktree items remain unchanged and unstaged:

| Path | Status | SHA-256 |
| --- | --- | --- |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py` | modified, unstaged | `01668e175610d9d090ea51018badbde8b021103afe13ed878782a58b8ce3b224` |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/browser_supplier_payables_fixture_diagnostic.py` | untracked | `d9822184b26f3c1ebaf5b93663b1f6c3a495b6482f013092d955748dfdf963c5` |
| `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/ui_smoke/sales_final_acceptance_audit.js` | untracked | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/a.out` | untracked | `0063411e61152850243132aa87ef12844a8724adb671bf4f38793bcd2b1ce339` |

## 3. Controlling evidence

This gate used only:

1. the committed sources in Section 2;
2. the [canonical Python standard-library parser provenance contract](finance-accounting-cycle2-gl-tb-e2b1-python-stdlib-parser-provenance-contract-freeze-2026-07-19.md), SHA-256 `d86161c9f7df4836f12783fbfa30a495c79b5155e4e5ccdb985fb649803e5b1e`;
3. the [parser fixture execution-contract stop](finance-accounting-cycle2-gl-tb-e2b1-parser-fixture-execution-contract-isolated-runner-freeze-2026-07-20.md), SHA-256 `df3f4a730381245a00e1615acbdebefa9412ea486f4fff70fbf9e71401eb6f4f`;
4. the [toolchain provenance record](finance-accounting-cycle2-gl-tb-toolchain-docker-endpoint-parser-provenance-2026-07-19.md), SHA-256 `bdbc50634ec5d01604e464fe92345486cfdf5a196a147403764fb2ccfc0dbf0c`; and
5. the [residual toolchain and `/usr/bin/env` record](finance-accounting-cycle2-gl-tb-residual-toolchain-provenance-docker-endpoint-authority-2026-07-19.md), SHA-256 `58025cf63d8aeb8bd051d9a4f63608b7bc278769338ad198fabff1af272b2010`.

The bounded new read used only fixed files under the already accepted `/usr/lib/python3.10` standard-library boundary plus the two committed package initializers. No directory outside that boundary, application runtime, Frappe, MariaDB, Docker or live surface was inspected.

## 4. Executable and clean-environment evidence

The accepted interpreter identity is:

| Field | Accepted evidence |
| --- | --- |
| supplied path previously exercised | `/usr/bin/python3` |
| canonical binary path | `/usr/bin/python3.10` |
| canonical binary stat | `fc01|3507|81ed|755|0|0|5917224|1782154527|1783494034` |
| canonical binary SHA-256 | `7d51cd6b48b521277f5caa4610a82126e315fa2be4df069823a8b1eeb5bd4a86` |
| interpreter | CPython `3.10.12 (main, Jun 22 2026, 18:55:27) [GCC 11.4.0]` |
| implementation/cache tag | CPython / `cpython-310` |
| SOABI | `cpython-310-x86_64-linux-gnu` |
| multiarch | `x86_64-linux-gnu` |
| filesystem encoding/errors | `utf-8` / `surrogateescape` |

The accepted clean-environment owner is `/usr/bin/env`, stat `64513|1642|81ed|755|0|0|43976|1707363999|1719848457`, SHA-256 `85036540673319c6c2f54233fd2b9e45a8a71246b51cc96c4e6ab8ee6c419eb0`, GNU coreutils `8.32`.

The accepted prior interpreter prefix was:

```text
/usr/bin/env -i PATH=/usr/local/bin:/usr/bin LC_ALL=C TZ=UTC /usr/bin/python3 -I -S -B -X utf8
```

It produced the exact initial module-search path:

```text
/usr/lib/python310.zip
/usr/lib/python3.10
/usr/lib/python3.10/lib-dynload
```

That path excludes the current directory, script directory, repository, user site and system site-packages. `-S` prevents `site` and `.pth` processing; `-I` ignores `PYTHONPATH`, user-site and current/script-directory import broadening; and `-B` prevents new bytecode writes but permits eligible existing cache reads.

The requested direct `/usr/bin/python3.10` literal identifies the same canonical file, so it remains the sole binary candidate. It was not the literal used by the accepted self-report, whose `sys.executable` was `/usr/bin/python3`. Direct-literal `sys.executable`, flags, path and environment behavior therefore require a fresh separately authorized observation before exact argv approval.

The only candidate future environment is the accepted three-entry environment plus the required hard gate:

```text
PATH=/usr/local/bin:/usr/bin
LC_ALL=C
TZ=UTC
FINANCE_GL_TB_E2B1_PARSER_GATE=finance_gl_tb_e2b1_parser_v1
```

No `HOME`, `PYTHONHOME`, `PYTHONPATH`, `PYTHONSTARTUP`, proxy, credential, CA override, `LD_*` override or other variable is permitted. This is a planning candidate, not an executable environment allowlist.

## 5. Installed `unittest` identities

Top-level `import unittest` eagerly imports `result`, `case`, `suite`, `loader`, `main`, `runner` and `signals` at installed `unittest/__init__.py:59-67`. `async_case` is lazy at lines 68 and 83-94 and is excluded unless accessed. The fixture contains no `assertLogs`, `assertNoLogs`, `subTest`, module fixture or cleanup-registration use, so `_log.py`, `mock.py`, `async_case.py` and `__main__.py` are not part of the proposed runner surface.

The exact installed eager package sources and eligible timestamp-based caches observed in this gate are:

| Module | Source bytes | Source SHA-256 | Cache bytes | Cache SHA-256 |
| --- | ---: | --- | ---: | --- |
| `unittest/__init__.py` | 3,761 | `07bdf1fff20e4121ba61cfb64ea3c404d54ac56b053475a3a105907f48685210` | 3,395 | `0dcf57f84543e16632145185e6a070bc92f152c333be9dd8bc4256da8fefbfa9` |
| `unittest/result.py` | 8,518 | `eb3f6ed6a6d339b8113479f6878f1946bf082b8818a89daf85f0b63a5be1f9c1` | 8,039 | `821c38478e2fd023de9ff9e4591163d678f144b44fcec7b259762d58c7f28a9b` |
| `unittest/case.py` | 57,680 | `9fa2e873ba608253b6e3d2158e36baf02433a46e68071b76b5e961a7accec2d2` | 48,490 | `8d130474bafb5274a71b8bf43a98b5bc537688feea8acd86260966039fd82954` |
| `unittest/suite.py` | 13,512 | `ed2da92bc9f97c53403ee2d3d12cc53b16a96e85d596ebc887b5a93458f3f6bc` | 10,268 | `b1cd21c8af2c6d164265b27a27e4ee576b5058e320b3df4f2c0a33acc4bafecc` |
| `unittest/loader.py` | 22,702 | `4b8d7dbfe68bc38f50e6b3952fda338e1cf9de43f299ab910cfef31c219e0342` | 14,424 | `3075431e81e7f0ec2a320521e387c448f363462e5d310b022b8e07447481f3d0` |
| `unittest/main.py` | 11,256 | `360d56268ce4d561681faccf0206dc2164830de7a6dcd135f655ae5fdbdc59cf` | 7,556 | `f2ed3e618b3bbdde19e8d45afba8dd42be63785585da79d579fa7e1a6e9098c0` |
| `unittest/runner.py` | 8,051 | `7ab57b963cd64f210d5a074b15e8dae9b4d1699da980dd523362d3f88e966847` | 6,952 | `2bb81ee08b8a4444e9eb5477c430fbbec06ba340b2a72bfff267d7caf65f3dcf` |
| `unittest/signals.py` | 2,403 | `f8286e818ca56e10e03745bc056cdfd31147678f9a1dc8cb6b0fe96ef9a4362a` | 2,253 | `01ebda9519717d63dec96393200490dcf630c78fbcd9f498ebecd250236c6244` |
| `unittest/util.py` | 5,215 | `fdcc640c3505d16deab9c32eae7c3f5f67c3b5e81c563dc6698fa7fcf403854d` | 4,540 | `db99c2706e4328026e01e3b2b8a695f66b1ab74c88b6aae1c9f70218d7e5b304` |

Every source/cache stat classified a root-owned mode-`0644` regular file. Each cache header is timestamp based and carries the observed source mtime `1782154527` plus its exact source byte count. This establishes cache eligibility metadata and exact file identities; it does not prove that marshalled cache code is semantically equal to the readable source or that the future run will select the same source/cache path.

## 6. Direct dependency and importlib observations

The fixture adds `contextlib`, `io`, `os`, `unittest` and annotation-only `typing.Callable` to the already accepted parser closure. Fixed source/cache observations were:

| Module | Source SHA-256 | Eligible-cache SHA-256 |
| --- | --- | --- |
| `/usr/lib/python3.10/contextlib.py` | `2e17d45cf3da698c9752c58a668c8a03d0ce2280fdffd6e352794a38a94d9f07` | `2cf98c8006a69b5a6a7c886ffdf4a5324b17bdb8f63d215b490f03950809a50b` |
| `/usr/lib/python3.10/io.py` | `ee094fcf87d17a3a25816c663b67bd8797dccc3eebabad5a23f6da162146a0a8` | `1c3e590a8662739ede267d444c03abbc2cd96ef89d36b706593b94714dc35f69` |
| `/usr/lib/python3.10/os.py` | `70e420e105d021d5ba2ec4d8a9b2131561db6d93e800e8580ddeb86cbd6959c3` | `ed0aced830f1d1c5a74130880545754422ebb2f6ba1c01b941505ab36d34920b` |
| `/usr/lib/python3.10/typing.py` | `ec7b7f73fc92827c78a7d2aff90cffe070530cad6c693460165c26f76d195f41` | `09211acb4a92df1d6823045bb2627acbf2f34db2209ee51ce9471368e9c902bb` |

Fixed installed importlib references were also observed:

| Module | Source SHA-256 | Eligible-cache SHA-256 |
| --- | --- | --- |
| `importlib/__init__.py` | `49ad4fdc8139026f7f3773e3f50f09207ff6bd8e92a2c382545525235448e525` | `c246f02ebe9792e8d0a1bcef557127deaa3690933f6ba18fac8739b889c1a685` |
| `importlib/_abc.py` | `e24fa90513d1fd6e10df30dc28044dfcad857b88161c79de10f7109c18227e8d` | `d05cfe15a58752db85ec6523a4cdfe148ebf22384ca31ec12e43f1c4b84333f4` |
| `importlib/_bootstrap.py` | `11125bbe628d2f82afdcd480c6454f6248f229d9caf6a8ac1e231c3402facaa1` | `8d1ca21605aeca3a726ea99c68dbb74c02bce346aba05a45c8aae133301da873` |
| `importlib/_bootstrap_external.py` | `a5eaa30689fd793ca058fce597a4c8781c36e5bce4930e441f899494071d3989` | `42ec34afcb86e589cb9ffb18aff142d6872bbdfb17919860a68658a077e270fd` |
| `importlib/machinery.py` | `b7b47efe3d95ae817e0c61d852682ddf8b8ce95aaf36ae4cf333e145416baf18` | `4cc756a39fdaa8e6174e3e0f317056c7d88047e8da3bf705e9c6085e0c35622c` |
| `importlib/util.py` | `de645b9f6d595f5e415d117f4d04ce77f144ce5ad2a6477659a9b5547d54b9dd` | `eeb287893416d3aed7d9dec12ff9bdcb62847c5e5ba081916d2c97b294c9e3cf` |

These observations do not close the import provenance chain:

1. CPython executes frozen `_frozen_importlib` and `_frozen_importlib_external` machinery from the interpreter; installed `_bootstrap*.py` hashes do not independently identify the embedded frozen code.
2. `unittest` imports additional modules including `argparse`, `difflib`, `pprint`, `traceback`, `fnmatch`, `signal` and `weakref`; their complete source/cache/extension and transitive identities were not previously accepted.
3. Static source inspection cannot determine the exact future import delta, source-versus-cache selection, dynamic extension/provider loading or module origin set.

A bounded, separately authorized isolated import-ledger observation is therefore execution-blocking even though no test execution is needed for that future observation.

## 7. Source-supported direct-suite semantics

The exact installed source supports the following design facts:

1. `unittest/case.py:357-375` stores the literal `methodName`, resolves it with `getattr` and raises `ValueError` for a missing non-`runTest` method before setup or test execution.
2. `case.py:451-452` and `util.py:54-55` form each ID as `module.qualname.method`.
3. `unittest/suite.py:21-24` and `44-58` append direct cases in supplied order. The suite does not deduplicate them, so uniqueness remains controller-owned.
4. `suite.py:102-133` executes stored cases in order and replaces completed entries with `None` at lines 126-127 and 69-81. Prestart inventory plus a callback ledger, not post-run suite contents, must be authoritative.
5. `suite.py:142-186` performs class setup before the first method. A class-setup exception becomes an `_ErrorHolder` through lines 233-248 and 328-364; no test method starts.
6. `case.py:557-622` calls `startTest`, processes skip/setup/test/teardown/cleanup and one outcome callback, and attempts `stopTest` in its outer `finally` after a successful `startTest` call.
7. `suite.py:285-325` owns class teardown and class cleanups after ordinary suite flow. `TestSuite.run` has no enclosing `try/finally`, so `KeyboardInterrupt`, a result-callback escape or another abnormal exit can bypass final class/module teardown.
8. `unittest/result.py:110-158` and 173 onward can format and retain tracebacks and captured streams. The default result and `TextTestRunner` are therefore prohibited for this evidence boundary.
9. `unittest/signals.py` imports signal support, but it changes process handlers only when its handler functions are called. The future controller must call none of them.

These are planning-source facts. They become executable behavior only after the source/cache/import provenance Blocker is closed.

## 8. Exact ten-method contract

The sole target class is:

```text
erp_workspace_ui.tests.test_finance_gl_trial_balance_e2b1_parser_fixtures.TestFinanceGLTrialBalanceE2B1ParserFixtures
```

The sole method order is:

| Order | Fixture line | Literal method name |
| ---: | ---: | --- |
| 1 | 213 | `test_e2b1_01_canonical_commit_bodies` |
| 2 | 261 | `test_e2b1_02_canonical_tree_bodies` |
| 3 | 322 | `test_e2b1_03_missing_q_and_ambiguity_rejections` |
| 4 | 370 | `test_e2b1_04_json_encoding_and_complete_value_boundaries` |
| 5 | 409 | `test_e2b1_05_complete_schemas_additive_policy_and_enum` |
| 6 | 607 | `test_e2b1_06_identity_and_invocation_boundaries` |
| 7 | 739 | `test_e2b1_07_https_and_rfc3339_boundaries` |
| 8 | 887 | `test_e2b1_08_tree_modes_sizes_paths_and_late_failure` |
| 9 | 1045 | `test_e2b1_09_classification_rejections_and_hashing` |
| 10 | 1104 | `test_e2b1_10_controlled_and_internal_fail_closed_behavior` |

The future controller must own one immutable literal tuple containing those names. It must instantiate the exact class once per literal name with direct `TestCase(methodName)` construction and place those ten objects, in that order, in one explicit `unittest.TestSuite`.

Before any test starts, the controller must compare:

- literal count exactly `10`;
- uniqueness exactly `10`;
- exact order equality with the table;
- exact class identity, module and qualified name;
- each literal name as a callable class member;
- each case's exact `_testMethodName` and `id()`;
- a flat suite containing exactly those ten direct case objects; and
- absence of `_FailedTest`, `_ErrorHolder`, a nested suite, a database-harness ID or any other object.

The controller must not call or reference:

- `unittest.main`;
- `unittest.TestLoader` or `defaultTestLoader`;
- `discover`;
- `loadTestsFromModule`;
- `loadTestsFromName`;
- `loadTestsFromNames`;
- `TextTestRunner`;
- a module, class, filename-pattern, package or application discovery path; or
- a fallback or automatically broadened selector.

Importing top-level `unittest` necessarily loads its eager modules, but calling their loader, main, text-runner or signal seams remains prohibited and must be proven absent by later controller static review.

## 9. Repository import and database-harness containment

The committed package initializers are inert:

| Path | Content classification | SHA-256 |
| --- | --- | --- |
| `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/__init__.py` | only `__version__ = "0.0.1"` | `b172e1ee0dca0b84021717191814e91b6b1c47b866981b0c8eae8ba91a6d9118` |
| `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/tests/__init__.py` | empty | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

The parser fixture imports only `contextlib`, `hashlib`, `io`, `os`, `unittest` and `typing.Callable` at lines 3-10. It lazily imports only `_E2B1ParseRejected`, `_E2B1ParserInternal` and `_parse_e2b1_response` from the controller at lines 63-70. Its hard gate is lines 105-112. It has no database-harness, Frappe, MariaDB, filesystem, network, Docker, thread, subprocess, queue, email, notification, integration or accounting import/action surface.

The controller imports only `datetime`, `hashlib`, `json`, `re` and `urllib.parse` at lines 8-12. It ends at line 633 with parser functions. It has no runner, suite, argument, import-root, evidence, process, signal, promotion or finalization boundary.

This proves source-level non-dependence. It does not make the database harness independently unreachable. Adding the application root to `sys.path` would expose the entire deploy-writable package tree, including the database harness, even though the accepted fixture/controller source does not import it. Removing that root after import does not by itself erase retained package `__path__` values.

The Owner must later choose one containment design:

1. **Exact-file import and canonical aliasing - recommended.** The controller verifies its own realpath, registers its already-running module under the one canonical controller name, creates sealed parent package identities, loads only the exact fixture file under its frozen canonical module name, and exposes no searchable package path.
2. **Temporary exact app-root insertion plus deny policy.** The controller preloads the complete permitted standard-library closure, installs a source-controlled deny-first import policy, inserts the verified app root only long enough to import the exact fixture and inert package initializers, removes it in `finally`, seals package paths and rejects every unexpected repository module delta. Independent filesystem denial must still prevent direct access to the database-harness file.

Neither design is selected or authored here. Both require exact importlib behavior, static source review and independent pre-import enforcement before an unreachability claim.

## 10. Setup, result, failure and finalization contract

The future controller-owned sanitized result must be total and nonthrowing. It must never call default traceback formatting, `TextTestRunner`, `str()` or `repr()` on an exception, traceback, setup holder, fixture value, object ID, path or leakage canary. It may retain only an allowlisted ordinal, exact expected selector and generic outcome enum.

The required failure treatment is:

| Condition | Required disposition |
| --- | --- |
| missing method | catch constructor `ValueError`; generic prestart failure; no partial suite |
| duplicate, reordered, missing or extra literal | stop before import/construction where possible and again at suite inventory; discard |
| missing or incorrect parser gate | generic class-setup failure; zero method starts; no skip/success claim; discard |
| class/module setup holder | reject the non-ten object; discard |
| per-test setup failure | one start, generic error terminal, stop attempt, no test/teardown; discard |
| assertion failure | one start, generic failure terminal and stop attempt; stop remaining cases; discard |
| other test/internal error | one start, generic error terminal and stop attempt; stop; discard |
| skip, expected failure or unexpected success | rejected terminal enum; stop; discard |
| teardown or cleanup error | generic error; discard |
| callback exception, `KeyboardInterrupt`, signal or timeout | incomplete finalization; discard; outer recovery owns cleanup |
| missing stop, duplicate callback or missing terminal callback | incomplete ledger; discard |
| unexpected stdout/stderr, raw traceback or sensitive value | leakage failure; discard and destroy raw material |

The controller must explicitly own begin and finalization events because passing an explicit result means `TestCase.run` does not call `startTestRun` or `stopTestRun`, and `TestSuite.run` does not add them.

Promotion requires all of the following:

- exactly ten starts;
- exactly ten terminal callbacks;
- each frozen selector exactly once;
- exactly ten successes;
- exactly ten stop callbacks;
- zero skips, expected failures, unexpected successes, failures or errors;
- zero setup/module/class holder objects;
- no `_FailedTest`, database-harness ID, nested or extra suite object;
- ordinary suite return and ordinary controller finalization;
- unchanged controller and fixture hashes; and
- complete independent side-effect and teardown reconciliation.

Exit `65/70` remains deferred. No exit mapping may be claimed by convention.

## 11. Invocation freeze matrix

| Contract field | Current disposition |
| --- | --- |
| absolute executable | canonical binary `/usr/bin/python3.10` is fingerprinted; direct-literal invocation behavior remains unobserved |
| exact argv | unresolved; no runner subcommand or exact child/supervisor split exists in source |
| absolute cwd | unresolved; it must not supply an implicit import root |
| environment | accepted clean base plus hard-gate candidate in Section 4; unexecuted and unapproved |
| locale/timezone | `LC_ALL=C`, `TZ=UTC` retained as the sole candidates |
| import root | unresolved pending the Owner choice in Section 9 |
| pre-execution hashes | controller, fixture, database harness, package initializers, interpreter and observed standard-library identities are known; complete closure and provider set are not |
| suite inventory | frozen by Section 8 as a planning contract |
| timeout/termination | unresolved; no provider and no numeric ceiling approved |
| result callbacks | generic sanitized design frozen; source implementation absent |
| stdout/stderr | raw content prohibited; exact successful/error byte and hash contract unresolved |
| process exit | unresolved; `65/70` deferred |
| source-hash reconciliation | pre/post controller and fixture equality mandatory; implementation absent |
| evidence destination | unresolved; no filesystem destination or promotion authority approved |
| promotion/discard | prior discard-only semantics preserved; implementation absent |
| deterministic teardown | unresolved; no outer watchdog/recovery owner accepted |

The candidate interpreter prefix is not an execution allowlist:

```text
/usr/bin/env -i PATH=/usr/local/bin:/usr/bin LC_ALL=C TZ=UTC FINANCE_GL_TB_E2B1_PARSER_GATE=finance_gl_tb_e2b1_parser_v1 /usr/bin/python3.10 -I -S -B -X utf8
```

No controller argument may be appended until the runner mode, import design, watchdog, result protocol, evidence destination and teardown owner are separately frozen.

## 12. Isolation and side-effect proof

Three evidence layers remain distinct:

1. **Source proof.** The committed fixture/controller and inert package initializers contain no Frappe, MariaDB, database-harness or prohibited action dependency. This layer passes.
2. **Independent runtime denial.** Controls active before interpreter import must deny database/SQL, network/Unix-socket, filesystem-write, Docker, process/thread/queue and application/runtime actions. No accepted provider exists.
3. **Independent observation.** A separate observer must report attempted actions and prove its own activation, identity and completeness. No accepted provider exists.

Source inspection alone cannot prove zero runtime counters. A future run must independently establish:

- zero database connection and SQL attempts;
- zero network, acquisition and Unix-socket attempts;
- zero filesystem writes and bytes, including bytecode, temporary files and logs;
- zero Docker contact;
- zero runner-created threads, subprocesses and queues;
- zero email, notification and integration attempts;
- zero site initialization and runtime, permission, metadata or accounting actions; and
- unchanged source identities before and after.

The single expected supervisor-to-runner process relationship, if the Owner later selects a same-source parent/child design, must be explicitly separated from prohibited runner-created subprocesses and independently observed. That design is not selected here.

## 13. Numeric limits

No per-method timeout, total timeout, memory ceiling, stdout/stderr ceiling or evidence-size ceiling is selected or implied.

The existing later derivation rule remains controlling: limits may be proposed only from separately authorized isolated observations after the runner, full import closure, denial/observation providers and evidence writer are frozen. Each value requires later Owner approval and pass/limit-plus-one proof. No average, percentile, multiplier or margin is authoritative by convention.

## 14. Findings by severity

### Blocker

1. **Actual import/source/cache closure is incomplete.** Exact `unittest` source and cache identities are now known, but cache semantic equivalence, actual source/cache/frozen selection, frozen importlib identity and the complete new transitive module/extension set are not.
2. **Database-harness unreachability is not independently enforced.** Source-level non-import passes, but an ordinary application-root insertion exposes the database harness and deploy-writable package tree. No exact-file alias or deny-first root policy has been selected, authored or proven.
3. **Exact process and evidence ownership is absent.** The controller has no runner mode, exact argv, result adapter, watchdog, evidence writer, promotion/discard implementation, recovery or teardown entrypoint.

### High

1. **Independent denial and observation are absent.** Source inspection cannot establish the required zero-attempt runtime counters.
2. **Default unittest failures can leak.** Installed default result code formats tracebacks and captured streams; a generic controller-owned adapter is mandatory.
3. **Unittest does not guarantee outer finalization.** Abnormal suite/result escapes can bypass class/module teardown; the external controller/watchdog must own incomplete-run discard and recovery.
4. **Controller module identity is unresolved.** Absolute-script execution creates `__main__`, while the fixture imports the canonical controller module. Exact aliasing or deliberate, reviewed double loading must be frozen; silent double loading is rejected.
5. **Non-atomic identity residual remains accepted.** Pre/use/post equality cannot exclude replace-and-restore between observations. Fresh binding and discard on observed drift remain mandatory.

### Medium and deferred

1. The accepted self-report used literal `/usr/bin/python3`, not `/usr/bin/python3.10`; the same canonical binary identity does not prove direct-literal invocation fields.
2. Default stream encodings and exact stdout/stderr/exit bytes were not retained by the prior parser proof.
3. Numeric time, memory, output and evidence limits remain intentionally unselected.
4. Dynamic `dlopen`, provider, locale-data and plugin identities remain outside source-only proof.

### Accounting result

No accounting-semantic Blocker, High or Medium was found. The stop preserves the reporting-only, no-execution and no-accounting-authority boundaries.

## 15. Bounded reviews and Main Control synthesis

| Review | Result |
| --- | --- |
| CPython/unittest provenance | Direct named construction, suite order and lifecycle are source-supported; actual cache/frozen selection and complete transitive import identity remain stopped. |
| exact suite and failure semantics | The ten literal methods and prestart inventory can be frozen; default result leakage and exceptional finalization require a controller adapter and outer owner. |
| import/security containment | Pure source boundary and inert initializers pass; constrained import-root enforcement and independent denial/observation remain stopped. |
| accounting/source preservation | Pass for static isolation; parser fixtures cannot establish GL/TB accounting correctness or authority. |
| release/evidence integrity | Stop; no exact argv, watchdog, evidence destination, promotion/discard implementation, numeric limits or deterministic recovery owner exists. |

Main Control accepts the evidence-supported Blocker and High findings. The preferred explicit-suite design remains viable, but readiness is not inferred from source names or source inspection. One synthesis pass was performed; no general parser, fixture, accounting or architecture review was reopened.

Rejected inferences include: `-B` as cache-read denial; installed `_bootstrap*.py` as proof of embedded frozen importlib bytes; ordinary app-root insertion as database-harness unreachability; source inspection as zero side-effect counters; default unittest output as sanitized evidence; exit `65/70` by convention; an invented numeric limit; Frappe/Bench/ERPNext/MariaDB involvement; E2-B1 acquisition; or Finance/accounting execution authority.

## 16. Future scopes and allowlists - all unapproved

### 16.1 Controller source-authoring allowlist

If the Owner later closes the provenance and containment decisions and separately authorizes source authoring, the exact source allowlist can remain one path:

```text
impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/tests/finance_gl_trial_balance_evidence_controller.py
```

No fixture, database harness, package initializer, runner file, external fixture, parser file or fifth source is required by the current preferred design. Any later evidence that another source is unavoidable must stop for Owner approval.

### 16.2 Future read-only path allowlist

A later bounded provenance gate may re-read/hash only these fixed groups, with no glob, discovery or directory-wide fallback:

1. `/usr/bin/env`, `/usr/bin/python3.10`, `/usr/bin/realpath`, `/usr/bin/stat` and `/usr/bin/sha256sum`;
2. the nine `unittest` source/cache pairs listed in Section 5;
3. the four direct fixture source/cache pairs and six importlib source/cache pairs listed in Section 6;
4. fixed immediate transitive seeds `/usr/lib/python3.10/abc.py`, `argparse.py`, `difflib.py`, `fnmatch.py`, `pprint.py`, `traceback.py`, `signal.py`, `weakref.py`, `stat.py`, `posixpath.py`, `genericpath.py`, `collections/abc.py`, `_weakrefset.py`, `copy.py`, `heapq.py`, `linecache.py`, `textwrap.py` and `gettext.py`, plus their exact `cpython-310.pyc` peers when present;
5. the two package initializers and three committed source paths in Section 2; and
6. the exact controller-derived directory chain needed by the Owner-selected import design.

The accepted fixed read command forms are:

```text
/usr/bin/realpath --canonicalize-existing --physical -- <ONE_EXACT_ALLOWLISTED_LITERAL>
LC_ALL=C /usr/bin/stat --dereference --printf='%d|%i|%f|%a|%u|%g|%s|%Y|%Z\n' -- <ONE_EXACT_CANONICAL_LITERAL>
LC_ALL=C /usr/bin/sha256sum --binary -- <ONE_EXACT_CANONICAL_LITERAL>
```

Source contents must be transported byte-preservingly and rehashed against the remote record. If a fixed seed reveals an unlisted transitive source/extension, the later gate must stop and return one consolidated exact-path expansion for Owner approval.

### 16.3 Future Python observation and execution allowlist

```json
[]
```

No Python self-report, import ledger, source/cache comparison, runner, suite or test command is approved. A later import-ledger proposal must itself freeze the exact code bytes, argv, environment, output schema and read-only effects before the Owner may authorize it.

## 17. Remaining Owner decisions

Before runner source authoring, the Owner must separately decide:

1. whether to authorize one isolated no-test Python provenance observation to bind direct `/usr/bin/python3.10`, actual source/cache/frozen origins and the complete import delta;
2. whether to require source-only loading or accept exact eligible `.pyc` identities after a separately proven source/bytecode equivalence method;
3. whether the repository import contract uses the recommended exact-file/canonical-alias design or the temporary-root/deny-first design;
4. which independent pre-import denial and side-effect observation providers may be evaluated;
5. whether one controller source may own separate supervisor and runner modes so the child remains filesystem-write-free while the parent owns watchdog, sanitized capture, evidence and teardown;
6. which sanitized result/output schema and evidence destination may be authored; and
7. after source review, whether to authorize a separate numeric-derivation gate and only later fixture execution.

None of these decisions starts E2-B1 acquisition, E3-B1, E1, Finance Cycle 2 runtime work or accounting execution.

## 18. Validation and future documentation staging allowlist

Main Control validates after writing:

- repository root, branch, local HEAD, upstream and `0/0`;
- empty Git index;
- candidate scope exactly this document and README plus the four unchanged exclusions;
- the three committed source hashes and two package-initializer hashes;
- `git diff --check HEAD`;
- strict UTF-8 without BOM, replacement characters, mojibake or trailing whitespace;
- balanced Markdown fences and valid local references;
- exactly one README index entry; and
- no source, runtime or execution authority beyond the evidence-backed planning contract.

The exact future documentation staging allowlist, if separately authorized, is:

1. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/finance-accounting-cycle2-gl-tb-e2b1-parser-only-python-unittest-runner-provenance-invocation-freeze-2026-07-21.md`
2. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/README.md`

This gate does not authorize staging, commit or push.

## 19. Final control statement

**Decision:** `stopped_for_parser_runner_provenance_gap`

The parser-only fixture/controller boundary remains accepted and unchanged. Direct literal `TestCase(methodName)` construction and one explicit ordered `TestSuite` are source-supported, and the ten-selector contract is frozen for planning. Execution remains stopped on complete import/cache/frozen provenance, independently enforced database-harness unreachability, controller-owned exact invocation/result/finalization and independent denial/observation providers.

No Python execution, `--help`, import, compilation, collection, test, runner authoring, E2-B1 acquisition, Frappe, Bench, ERPNext, MariaDB, Docker, infrastructure, source modification, staging, commit, push, live action, migration, permission change, protected gate or accounting action occurred.
