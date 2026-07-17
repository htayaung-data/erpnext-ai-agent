# Finance & Accounting Cycle 2 C2A1/C2B1 Baseline and Installed-Source Inventory

**Main Control authority:** Main Control v2

**Parent plan:** [Finance & Accounting Cycle 2 GL / Trial Balance Scope and Implementation Plan](finance-accounting-cycle2-gl-trial-balance-scope-implementation-plan-2026-07-17.md)

**Owner gate received:** `finance_cycle2_gl_tb_source_proof_authorized`

**Evidence scope:** C2A1 baseline and authority plus C2B1 installed-source inventory only

**Decision:** `c2a1_verified_c2b1_stopped_for_exact_installed_fingerprint`

**Date:** 2026-07-17

## 1. Outcome

Finance Cycle 2 has started only as the bounded, read-only GL / Trial Balance source-proof cycle authorized by the Owner. C2A1 is complete: the source baseline, authority chain, protection boundaries, exclusions and current Finance posture are verified without contradiction.

C2B1 is not closed. The source repository records a dated installed-version receipt and a mutable custom image tag, but it does not contain the ERPNext/Frappe application trees, an immutable image digest, exact installed app Git revisions, installed app dirty state, or installed-file SHA-256 values. Official ERPNext and Frappe tags were independently fingerprinted as supporting reference material, but they are not proof of the custom image's installed bytes.

Accordingly:

- C2B2-C2B7 have not started;
- no GL/TB accounting or permission contract is accepted;
- no source adapter is selected;
- no endpoint, UI, role, permission, route, registry, governance, Shared UI, AI or live change is authorized;
- official tag behavior must not be represented as installed behavior;
- exact installed-source fingerprint access is the next explicit Owner decision.

## 2. Authority and point-in-time source receipt

### 2.1 Source baseline before this evidence candidate

| Item | Verified value |
| --- | --- |
| Source repository | `/home/deploy/erp-projects/erpai_project1_erpnext_ui_design` |
| Branch | `feature/erpnext-ui-design` |
| Source `HEAD` | `de1f57dd5fc2122269574b2df8b18bfa3a8edc55` |
| Upstream | `origin/feature/erpnext-ui-design` |
| Upstream revision | `de1f57dd5fc2122269574b2df8b18bfa3a8edc55` |
| Ahead/behind | `0/0` |
| Git index | Empty |
| Capability-map SHA-256 | `9c9748a243744c57175d684d1f963e337dacaac5aa36f1faf420d7a92642e2bd` |
| Cycle 2 plan SHA-256 | `5081302170ce7657b93c8ba9a8e98dc5bcf65057d329c2b591ebc21a39e5de28` |

The accepted Main Control v2 handoff, accepted Codex Delivery Operating Model, canonical Finance capability map, published Cycle 2 plan, latest Cycle 1 closure artifacts and current committed source form the authority chain. The Owner's later approval activates only the bounded source-proof gate and supersedes the older planning snapshot that said source proof had not started.

Historical phase labels do not override later accepted closure. Existing stale registry phase labels are traceability debt and are not changed during this task.

### 2.2 Four unrelated exclusions

| Path | Status | SHA-256 |
| --- | --- | --- |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py` | Modified, unstaged | `01668e175610d9d090ea51018badbde8b021103afe13ed878782a58b8ce3b224` |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/browser_supplier_payables_fixture_diagnostic.py` | Untracked | `d9822184b26f3c1ebaf5b93663b1f6c3a495b6482f013092d955748dfdf963c5` |
| `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/ui_smoke/sales_final_acceptance_audit.js` | Untracked | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/a.out` | Untracked | `0063411e61152850243132aa87ef12844a8724adb671bf4f38793bcd2b1ce339` |

The excluded AI `service.py` was inspected only through committed-object operations such as `git show HEAD:<path>` and `git grep ... HEAD -- <path>`. Its working-tree content was not used.

## 3. Current ownership and protection receipt

| Surface | Current accepted posture | Owner and Cycle 2 boundary |
| --- | --- | --- |
| Sales | Formally protected route, landing, role authority, request isolation, navigation and accepted browser behavior. | Sales owner; no Cycle 2 edit or regression claim. |
| Procurement | Formally protected route, landing, role authority, navigation and accepted behavior. | Procurement owner; no Cycle 2 edit or regression claim. |
| Warehouse | Accepted bounded W16H closure; preserve routes, landing, roles and accepted behavior. | Warehouse owner; no Cycle 2 edit. |
| Finance Cycle 1 | Closed only for one-company, aggregate-only AR/AP posture with identity suppression, fail-closed behavior and no execution. | Finance owner; Cycle 1 semantics and UI remain unchanged. |
| Finance Cycle 2 | Read-only source proof only; current runtime still explicitly blocks Trial Balance figures. | Main Control owns proof scope; no runtime owner activated. |
| Shared UI | Owns neutral shell, lifecycle, sidebar/header/filter grammar, request isolation, accessibility, responsiveness, focus and teardown. | Locked. A separate impact proposal is required before any shared edit. |
| Routing and landing | Landing precedence remains `Sales > Procurement > Finance > Warehouse`. | Locked; no new Finance route. |
| Backend/browser registries | One Finance Overview, disabled search and no native report target. | Locked; stale labels are not cleaned up. |
| Governance manifest | Finance route, read-only Overview, Refresh and sidebar navigation only. | Locked; no native report, export or action expansion. |
| AI Assistant | Separate data-access, retention and security owner; no Finance Cycle 1 or Cycle 2 authority is inherited. | No Finance-to-AI integration is approved. |

Current committed Finance page metadata grants `Accounts Manager` and `Accounts User`. Broader shell-role names do not grant GL/TB data authority, and `System Manager` is not a Finance accounting bypass.

## 4. Current custom Finance and boundary anchors

These SHA-256 values fingerprint current clean source anchors; they are protection evidence, not a future runtime allowlist.

| Source anchor | SHA-256 |
| --- | --- |
| `erp_workspace_ui/finance_accounting/service.py` | `f7a5aa8c82011b385cc0c5963575162ace51341477286c054fb9dbcc8290ecad` |
| Finance Control Desk `finance_control_desk.js` | `52356627d4be4843c200c51a3b1bb11c070b5fdb4c51e2f26e5952ff94011e0c` |
| Finance Control Desk `finance_control_desk.json` | `fb0e0964cf9883e6224090f1e1efcd27c96798f585bc8afcbeb8dff5e4eaf765` |
| `boot.py` | `9c8b422821586822825349484977a12b858631b4e876b14918a7ed37f0d62dae` |
| `workspace_registry.py` | `efaafaa2c7a95bf0efe67d019328c1ff8cdc45e03faaab4233adcbb468375822` |
| Browser `workspace_registry.js` | `1196afd99234296e41671196bb357af546d1e04212dffbf0dc51bb8a78f144b6` |
| `workspace_governance_manifest.py` | `b8f582938ee9737484b60637e959248bdaa3e56298221084cf99c59d6342768f` |
| `hooks.py` | `44e96bb4f33d4ff83970d5de0f0a53767ffb4f0e9cbc5044b1bf49f769b2a3b4` |

Committed source proves the following current boundary:

- authentication and Finance shell/overview role checks exist;
- company resolution uses permission-preserving `frappe.get_list`, explicit permission checks, bounded results and fail-closed states;
- public Finance methods expose shell, aggregate overview, resolver, sidebar and disabled search only;
- browser validation rejects rows, native routes, actions and account/customer/supplier/voucher/bank identities;
- `GL Entry` and `General Ledger` remain blocked Cycle 1 sources;
- no custom GL/TB service, public response, UI section or test exists at this `HEAD`;
- the current ledger card remains explicitly unavailable rather than implying Trial Balance data.

## 5. Committed installed-version receipts

The source repository contains these dated/mutable build references:

- `.env.example` and `Readme.md` name image `ghcr.io/htayaung-data/erpnext-factory` with tag `erp16.4.1-hrms16.4.0-fac2.3.1-frappe16.5.0`;
- `compose.yaml` consumes `${CUSTOM_IMAGE}:${CUSTOM_TAG}` rather than an immutable digest;
- the accepted handoff reports Frappe `16.5.0`, ERPNext `16.4.1`, HRMS `16.4.0` and Frappe Assistant Core `2.3.1` as of 2026-07-16;
- the handoff expressly requires version revalidation before future source proof that depends on installed behavior.

Receipt Git blobs are:

| Receipt | Git blob |
| --- | --- |
| `.env.example` | `545866a4e3a6410e4c599d5129944505b074635b` |
| `Readme.md` | `2286a22a0f7340829b92c08ce8a7ec71b68d7982` |
| `compose.yaml` | `42068a16fbdaf129c59d5d8e4ec749ce24d83b10` |

The repository does not contain:

- an ERPNext or Frappe app tree;
- an ERPNext/Frappe Git submodule;
- an immutable custom-image digest;
- installed ERPNext/Frappe Git revisions or dirty-state receipts;
- installed selected-file SHA-256 values;
- a source-only export that can be proven byte-identical to the installed custom image.

The custom image tag includes `fac2.3.1`; tag equality alone cannot prove that its ERPNext/Frappe files equal public release-tag bytes.

## 6. Official release-tag crosswalk

This section is supporting primary-source evidence only.

- [ERPNext v16.4.1](https://github.com/frappe/erpnext/tree/v16.4.1) resolves to commit `d74a649016d8bb12ee3c5a24361171cebe860bfc`, tree `89af8accb3b1c5d1a1000a792301ca2eec300f7d`.
- [Frappe v16.5.0](https://github.com/frappe/frappe/tree/v16.5.0) resolves to commit `4dfcc56090eb3101d18ddb03750391511f163fcf`, tree `725e06e6319cef5a671884cba1b8b8841f40f99e`.
- ERPNext's `pyproject.toml` accepts Frappe `>=16.0.0,<17.0.0`; it does not establish the exact installed Frappe revision.

### 6.1 ERPNext v16.4.1 candidate-source SHA-256 manifest

| Candidate source | SHA-256 |
| --- | --- |
| `erpnext/__init__.py` | `bbb8c9817966cb87fcdbf23fde36183facc71f669c11b6f6f6bb2cd18ec4b995` |
| `erpnext/accounts/report/trial_balance/trial_balance.py` | `3da0acd3e65e9203193a7914dbdadac077b2cfb316e9313e0fc450edb3feedc9` |
| `erpnext/accounts/report/trial_balance/trial_balance.js` | `28fecc0dd936d3518b4c907bbdc24809d43ffd7779ecec2d85a6ddd4dedbe3b4` |
| `erpnext/accounts/report/trial_balance/trial_balance.json` | `72c9725546a40ad08356fc634fcece441b4a2e6a01e02b666c23d47edb630c07` |
| `erpnext/accounts/report/general_ledger/general_ledger.py` | `d0c3d97d31815bb2bbe093a93f863961a17b451a6dfcd83bd711f48dad4085eb` |
| `erpnext/accounts/report/general_ledger/general_ledger.js` | `91142805f9b3210736c7f65c3a2525859df36f63cf1c1b2c3429c11d77620499` |
| `erpnext/accounts/report/general_ledger/general_ledger.json` | `0240470a761b0c7d82d5dfc4e2978a4141cf6450de33bb6e45d0b16d18997c7f` |
| `erpnext/accounts/report/financial_statements.py` | `8390fe5ffc99c9e78734dda304a7c569e50b57f7bf006b7266584ae92a001c27` |
| `erpnext/accounts/report/utils.py` | `e80e643e6c6587c2986d088ab9fb9290e6e637c7dc3e80416f7414a21ba5b650` |
| `erpnext/accounts/utils.py` | `3154dec3a4ad34e62060736869a68ade0583e2219f8c86e602e409f36091757b` |
| `erpnext/accounts/general_ledger.py` | `f6c73176bee3c5de9f62ace638b7e4f14d3e6db51bfe68c460c70657ddc2cab5` |
| `erpnext/accounts/doctype/gl_entry/gl_entry.py` | `0a165bc5f3d6e456dc475153dd316f973fb41b7d3dcb6b0f40baf9d7c52b8418` |
| `erpnext/accounts/doctype/gl_entry/gl_entry.json` | `f7d2c1d47f22828ea02a9eb2500ab62ae1c30c0789a3d9fd364a3600fc632547` |
| `erpnext/accounts/doctype/account/account.py` | `2dea7a8f232fbbbb73f9663a912e3c31f4c8c336e06bd160f43ca964d3fccb3d` |
| `erpnext/accounts/doctype/account/account.json` | `201c924aa67073d8cea3f0de7025427144d26194630b3f394cdea59af1b4776d` |
| `erpnext/accounts/doctype/account_closing_balance/account_closing_balance.py` | `ff995a103e7409ddd31a8f3c5aa76652aafadbde655a08f323f7ba80371363e3` |
| `erpnext/accounts/doctype/account_closing_balance/account_closing_balance.json` | `de0d4e67720be4538a36322870d9f503785a70be794dcfe2e1d1692f39553036` |
| `erpnext/accounts/doctype/period_closing_voucher/period_closing_voucher.py` | `a7eaa7a1c95a82cce8f1be67f2a028791e4cab36596cb8292e32a23f807b3a79` |
| `erpnext/accounts/doctype/period_closing_voucher/period_closing_voucher.json` | `cb2b9e21a29ffc5bc46dc5aa60064632b72e656191e08bf625fe1f4ad451189c` |
| `erpnext/accounts/doctype/process_period_closing_voucher/process_period_closing_voucher.py` | `bd56d5fd76074a488bd1572242b3dc518f06c3a062ba76b6d003dc1c37e2869a` |
| `erpnext/accounts/doctype/process_period_closing_voucher/process_period_closing_voucher.json` | `58368d5cd2018b20ce973a4c48587a8dde507be9eac410bbc25ecf238e53bf46` |
| `erpnext/setup/doctype/company/company.py` | `6992db08e59a78051e1ae44ec111afb167675c4ddac0d02b2ae86064d18c4818` |
| `erpnext/setup/doctype/company/company.json` | `56027e0202cf41bd113a3c0488a1610d1acb3cddf2bce8dad0476f5be42dc8f1` |
| `erpnext/accounts/doctype/fiscal_year/fiscal_year.py` | `2553443adede8bec90ccce18d77b62fc3d46857126ffb8ab919c4db6e2a7d6b6` |
| `erpnext/accounts/doctype/fiscal_year/fiscal_year.json` | `2cb667684dba596e23240457b88cbc46833692fe8516c6dc26dcf41eeb1863b9` |
| `erpnext/accounts/doctype/fiscal_year_company/fiscal_year_company.py` | `0040ed34b21ef5d768a29d60585e555178ff091363d04331a3669297c98a740b` |
| `erpnext/accounts/doctype/fiscal_year_company/fiscal_year_company.json` | `18d042d4fd1b8bfb651c1a329d0d233a8514b46f168fd1a4b5c0ed7ea4daf19c` |
| `erpnext/accounts/doctype/accounting_period/accounting_period.py` | `9175996f1f5cd83d74572f8abbd995e398ab5ff11ff5421b43aa091c61352278` |
| `erpnext/accounts/doctype/accounting_period/accounting_period.json` | `202369edfacae81848e00e4e53928d3babf3393e35d84acacde285f73a3bb1bd` |
| `erpnext/accounts/doctype/accounts_settings/accounts_settings.py` | `a43284a9f40eee726367ee8a317193e2cebc55458159bba3dd5ef29e8f163e7a` |
| `erpnext/accounts/doctype/accounts_settings/accounts_settings.json` | `35874c00ba3450e9c0a0122064b29763dc3ba7b817ab504e63d0655e0fd89eb8` |
| `erpnext/accounts/doctype/finance_book/finance_book.py` | `b607368d79c5c2c046bc31481b9974ba5f1e8df47ed3df16877cadf700125e82` |
| `erpnext/accounts/doctype/finance_book/finance_book.json` | `b87733b195add89b5dbfdb635a419ce0d76cffbecdd5574edab17f8c01e7c4d5` |
| `erpnext/accounts/doctype/accounting_dimension/accounting_dimension.py` | `15a7fefbf1aa39ef0a2fc30a3624901a64aec08ed36fd85c889c2812dd64ca5a` |
| `erpnext/accounts/doctype/accounting_dimension/accounting_dimension.json` | `4f5281ac4428fc575a95a1d9fd1f1b231223ffc33a1007838b8836986983f56d` |
| `erpnext/accounts/doctype/accounting_dimension_detail/accounting_dimension_detail.py` | `75dc4e564bf629e05a125a49592c857d52d1a2019b10f84cf3e2a4bbb1fe12ac` |
| `erpnext/accounts/doctype/accounting_dimension_detail/accounting_dimension_detail.json` | `df2c6950613b5e54a91b76b1f260e4df38949eafd0393dabc123311f17a177f5` |
| `erpnext/accounts/doctype/accounting_dimension_filter/accounting_dimension_filter.py` | `2ae391d894f04ce3de919ae4a772451d6693807e115436b1984c5ed74d15cd1c` |
| `erpnext/accounts/doctype/accounting_dimension_filter/accounting_dimension_filter.json` | `bed452531a1b16c2e4dc1c8fb6dc511cf17ead662e12daacd908fd0509ad366b` |
| `erpnext/accounts/doctype/cost_center/cost_center.py` | `676e1b52af9088ec21e2ddf33a7af1b8289923c0f221797e2cf19c5eb9902c63` |
| `erpnext/accounts/doctype/cost_center/cost_center.json` | `9cd8aa58d8ea6988a57c294461dd9001d20aa869d860dfd19dd04ca101d3116e` |
| `erpnext/projects/doctype/project/project.py` | `8d7f0da733b11770df2eb92366a6e508357ade5742d464e4e42f1a24705521d1` |
| `erpnext/projects/doctype/project/project.json` | `b26beb7707127e58723030274578a128895485b2305cef40ca892076c35ba313` |

### 6.2 Frappe v16.5.0 candidate-source SHA-256 manifest

| Candidate source | SHA-256 |
| --- | --- |
| `frappe/__init__.py` | `3e70b6fd55b5a2947bc8961ea6ec47a41dd0f4a0e287c3c9eabed21a3c894340` |
| `frappe/desk/query_report.py` | `af65b6f40eaaf54e561fe4e3f06429b1114d650c7ef91d8bf77a9971eea7de70` |
| `frappe/desk/reportview.py` | `d5f4e02d07253026a43dfc7ed1f1f4a2dc5a36e2d8ffa99ad0f5995acda4574e` |
| `frappe/core/doctype/report/report.py` | `8e30fe3330f40b75637a0c24be4492be98405e68d79e0dff09041360c798f164` |
| `frappe/core/doctype/report/report.json` | `68babac28939a617bce0b59eafd849130c49d2ea1ff08343f3013b0bf5b62704` |
| `frappe/core/doctype/page/page.py` | `0e865063a1652a1cafc37311191f29175b8e71a7f3faa0143ee2deb9f2b6b56b` |
| `frappe/core/doctype/page/page.json` | `db6a3829afcb0bb04a76f97b2cd89295776a62d312498ef1f861eae40794e7c0` |
| `frappe/core/doctype/doctype/doctype.py` | `a0cb3ba030e81a2462b88b603bdb989514a1b4befac9a50ab8ba3a8c386e52e3` |
| `frappe/core/doctype/doctype/doctype.json` | `0b44ecc676ebe52fdd984bc6f02b1702b49b2f272102b8977568df120c287cd8` |
| `frappe/core/doctype/docfield/docfield.py` | `bab8a19fcdfea33d01f2ad624d221c0dd7164cc3d9fcbcb872612e5cfedb926b` |
| `frappe/core/doctype/docfield/docfield.json` | `56b6c07252605a085e525648b92cdb889aac6c3e967f8a05e382328fd68fa48c` |
| `frappe/core/doctype/user_permission/user_permission.py` | `7976aa1a74422267bbf5967ca179ee24796cd7f8ccabb6fd8437b9fbb2d07eae` |
| `frappe/core/doctype/user_permission/user_permission.json` | `522034601b85231aecc97b976c34043edfc0e16ed57cd6564319729805e4fa3c` |
| `frappe/permissions.py` | `5097cb7f6a65bd1bf9ace8ad91e8b5a7aa5dfaf5eab71cc6b5b207cdda44963d` |
| `frappe/model/db_query.py` | `73817632e1fb76e48bb33ef9ae0b098b80a0dabc7a1119a677301fc3419b8651` |
| `frappe/model/qb_query.py` | `06b1434b3bb9cc264daa103c4bf8bcce7da763982e9a5e3c63e171435b79d490` |
| `frappe/model/meta.py` | `aa06e26a6b0f506c2d7b138a36a09320a977ee8c823e7bc8efa4896a7a8dace7` |
| `frappe/model/document.py` | `e4f80af70712c50a16d574123cd4c4dab115f60ff0f2a0f8bdb7ae668f4a69e2` |
| `frappe/database/database.py` | `efd51bd657ef9b24734399b8808927689ca1438eb4790e3dd8c22fbb4151a4d1` |
| `frappe/database/query.py` | `79a7e3bc6f6e6045aa6fdf483c078e33fc2386088c54841e3a4311a56cb309ed` |
| `frappe/core/doctype/system_settings/system_settings.py` | `7529723ab1675e6476d6d9254661b7fddc65f2f5ac732bed5942abf66ada0474` |
| `frappe/core/doctype/system_settings/system_settings.json` | `ed0f0d3d0ba8c9d3c0b4baf8d03b72943e7b7f6b77475002921f779d00bb5497` |
| `frappe/geo/doctype/currency/currency.py` | `849a5565ad955146964c9262cf0edb88c73a0d9b9d0a44cd3c9b400cf2d95d4d` |
| `frappe/geo/doctype/currency/currency.json` | `3febb4d294ca1f046580fa4beb41cda64f79fd62c0ceac32dd7e25b9a86c0693` |
| `frappe/utils/data.py` | `147f36c2e591f93178cf9eb8c8326bd9c0699f0f924d602a1b3b7125ad3d73f8` |
| `frappe/query_builder/functions.py` | `79ff6564f325af739de2698755280d914269fd42fb0f9e56dcf9a780a748daf5` |

These hashes establish reproducible public release-tag references. A matching installed hash would support equivalence for that file; a mismatch would require the installed file to be treated as separate authority and reviewed directly.

## 7. Function and dependency inventory

The official ERPNext tag establishes these candidate proof entry points:

| Domain | Candidate functions and dependencies |
| --- | --- |
| Trial Balance | `execute`, `validate_filters`, `get_data`, `get_opening_balances`, `get_rootwise_opening_balances`, `get_opening_balance`, `calculate_values`, `calculate_total_row`, `accumulate_values_into_parents`, `prepare_data`, `prepare_opening_closing` |
| General Ledger | `execute`, `validate_filters`, `get_result`, `get_gl_entries`, `get_conditions`, `get_party_name_map`, `get_data_with_opening_closing`, `get_accountwise_gle`, `get_balance` |
| Shared statement logic | `get_accounts`, `filter_accounts`, `set_gl_entries_by_account`, `get_accounting_entries`, `apply_additional_conditions`, `get_cost_centers_with_children` |
| Closing | `PeriodClosingVoucher`, `process_gl_and_closing_entries`, `process_cancellation`, `delete_closing_entries`, `make_closing_entries`, `aggregate_with_last_account_closing_balance`, `get_previous_closing_entries` |
| Frappe report/permission | query report execution, Report and Page permission metadata, `build_match_conditions`, `get_list`, `get_all`, DatabaseQuery/QB query permission conditions, User Permission, DocType/DocField metadata |

Evidence-backed safety observations remain hypotheses until installed equality is proven:

- Trial Balance obtains account hierarchy and some opening/closing inputs through direct SQL, Query Builder or `get_all` paths while movement logic can apply match conditions; permission equivalence must be proven path by path.
- General Ledger builds GL match conditions but also loads Customer, Supplier, Employee and Account maps through `frappe.get_all`.
- In Frappe v16.5.0, `frappe.get_list` checks permissions while `frappe.get_all` explicitly sets `ignore_permissions=True`.
- A native report call is therefore not automatically a safe custom-service adapter and cannot be passed through to the browser.

No C2B2-C2B6 semantic conclusion is accepted from this inventory alone.

## 8. Permission, company, identity and AI boundaries

### 8.1 Finance source-proof boundary

The future proof must establish one identical complete authorized chart across opening, movement, hierarchy, PCV/cache, Finance Book and dimension reads. A user who cannot read every required ledger account cannot receive a `balanced` claim for a visible subset.

Every future adapter candidate must independently prove:

1. authenticated Finance purpose;
2. one exact server-authorized company;
3. Page/Report authority where applicable;
4. GL Entry, Account, PCV/cache and field authority;
5. complete-chart authority;
6. explicit Finance Book and no-dimension initial mode;
7. exact fiscal/date/currency/precision settings;
8. bounded consistency and source-change detection;
9. identity-free public schema;
10. no execution.

### 8.2 AI Assistant findings

Finance-to-AI remains prohibited. Three evidence-backed High future stop gates were found in committed source:

1. **Company authority mismatch.** AI query compilation strips a user-supplied company, assumes single-company mode and derives a company through `frappe.get_all("Company")`; it does not call the Finance permission-preserving company resolver.
2. **Unproven report authority and direct-query bypass.** The committed FAC implementation is absent, so its report/row permission behavior cannot be proven. A separate governed direct-query path uses `frappe.get_all` and is excluded from GL/TB.
3. **Broader identity and retention surface.** AI report metadata already permits customer/supplier/party dimensions and financial-statement-shaped reports, while the executor returns rows and retains result objects in tool traces. That authority is materially broader than Finance Cycle 1 and cannot be inherited by Cycle 2.

No General Ledger, Trial Balance or GL Entry capability is registered in committed AI metadata at this `HEAD`. No Finance-to-AI design should be proposed until company authority, report/row permissions, account/dimension classification, prompt/model exposure and trace retention/redaction have separate Security and Owner approval.

## 9. Finding register

| Severity | Finding | Evidence and disposition |
| --- | --- | --- |
| High stop gate | Exact installed ERPNext/Frappe authority is unavailable in the approved source-only evidence scope. | App trees/submodules, immutable image digest, installed revisions, dirty state and installed hashes are absent. Stop C2B1 closure and C2B2-C2B7. |
| High future gate | Official Trial Balance paths do not themselves prove identical permissions across opening, movement, hierarchy, PCV/cache and dimensions. | Direct SQL, Query Builder, cached reads, match conditions and `get_all` coexist. Must be rechecked against installed bytes. |
| High future gate | Native GL loads unnecessary party/account identity maps through permission-bypassing `get_all`. | Exclude native GL from runtime; oracle only if separately authorized. |
| High future gate | Finance-to-AI company, report, row, identity and retention authority is not compatible with the Finance boundary. | Finance-to-AI remains deferred and unapproved. |
| Medium | Custom image tag and dated version receipt are mutable/incomplete proof. | Require image digest and installed file/revision receipts. |
| Medium | Backend/browser registry phase labels are stale. | Later accepted closures supersede them; no cleanup in source proof. |

No present source-repository contradiction or documentation Blocker exists. The installed fingerprint gap is a deliberate stop condition, not permission to infer from release tags.

## 10. Exact next read-only installed-source fingerprint scope

The preferred next evidence source is either:

1. an immutable, source-only export/mirror proven byte-identical to the installed custom image; or
2. separately approved, read-only code fingerprinting inside the installed backend image/container.

The second option requires explicit Owner decision `finance_cycle2_gl_tb_installed_source_fingerprint_access_authorized` because it enters a live runtime container even though it reads code only.

### 10.1 Permitted evidence if authorized

- custom image name, immutable image ID/digest and container image relationship;
- installed Frappe and ERPNext version strings;
- exact app roots;
- app Git revision and dirty state when `.git` exists;
- file existence, byte length and SHA-256 for only the paths enumerated in Sections 6.1 and 6.2;
- direct comparison of installed hashes to the official-tag manifest;
- absent, extra or mismatched selected paths recorded without repair.

### 10.2 Additional path dependencies to include

- `erpnext/accounts/report/utils.py`;
- `erpnext/accounts/doctype/process_period_closing_voucher/process_period_closing_voucher.py` and `.json`;
- `erpnext/accounts/doctype/fiscal_year_company/fiscal_year_company.py` and `.json`;
- `frappe/model/qb_query.py`;
- `frappe/query_builder/functions.py`;
- Frappe Page, DocField, DocType, Report, User Permission, System Settings and Currency controllers/metadata listed above.

### 10.3 Explicitly prohibited during fingerprinting

- no `/home/deploy/erp-projects/erpai_project1` file inspection or alignment;
- no site database, SQL, ORM, DocType, report, bench console or operational-data query;
- no logs, environment secrets, site configuration or credentials;
- no source edit, package installation, checkout, reset, fetch or pull inside installed apps;
- no restart, cache clear, metadata reload, migration, permission change or service action;
- no endpoint, browser, protected gate or accounting execution;
- no copying installed code into the authoritative source repository without a later exact approval.

If an installed app is dirty, lacks source provenance, differs from the expected tag on a selected path, or cannot be hashed without prohibited access, C2B1 remains stopped and Main Control reports the exact gap.

## 11. Evidence candidate and phase state

The exact source documentation candidate for this outcome is:

1. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/finance-accounting-cycle2-c2a1-c2b1-baseline-installed-source-inventory-2026-07-17.md`
2. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/README.md`

No staging, commit or push is implied. Those remain separate gates.

Current mini-phase state:

| Mini-phase | State |
| --- | --- |
| C2A1 Baseline and authority | Complete for this point-in-time receipt. |
| C2A2-C2A5 | Not started; Owner business context, role/SoD and later scope decisions remain outstanding. |
| C2B1 Installed source inventory | Repository and official-tag inventory complete; exact installed fingerprint stopped pending separate access. |
| C2B2-C2B7 | Not started. |
| C2C-C2E | Not started. |

No runtime, test, smoke, registry, manifest, route, Shared UI, protected-workspace, AI, live, metadata, permission or accounting state was changed by the evidence work. Temporary official-source clones were used only outside the authoritative repository for primary-source fingerprinting and are not project artifacts.
