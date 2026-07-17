# Finance & Accounting Cycle 2 C2B1 Exact Installed-Source Fingerprint Receipt

**Main Control authority:** Main Control v2

**Parent plan:** [Finance & Accounting Cycle 2 GL / Trial Balance Scope and Implementation Plan](finance-accounting-cycle2-gl-trial-balance-scope-implementation-plan-2026-07-17.md)

**Preceding inventory:** [Finance & Accounting Cycle 2 C2A1/C2B1 Baseline and Installed-Source Inventory](finance-accounting-cycle2-c2a1-c2b1-baseline-installed-source-inventory-2026-07-17.md)

**Accepted governance profile:** [Finance & Accounting Cycle 2 C2A2-C2A5 Scope and Governance Profile](finance-accounting-cycle2-c2a2-c2a5-scope-governance-profile-2026-07-17.md)

**Owner gate received:** `finance_cycle2_gl_tb_installed_source_fingerprint_access_authorized`

**Decision:** `c2b1_installed_source_fingerprint_closed`

**Evidence timestamp:** `2026-07-17T09:24:48Z`

**State:** C2B1 closed for the frozen 69-file selected-source scope; C2B2-C2B7 and runtime remain unapproved

## 1. Outcome and bounded claim

The exact installed-source fingerprint completed within the approved code-only boundary.

- the named backend container maps to one immutable image ID and repository digest;
- the ERPNext and Frappe app roots resolve to the expected locations;
- the committed manifest contains exactly 69 unique valid paths: 43 ERPNext and 26 Frappe;
- all 69 installed paths are present, regular, non-symlink, readable and contained within the approved app roots;
- all 69 raw-byte SHA-256 values exactly match the official ERPNext v16.4.1 and Frappe v16.5.0 references;
- an immediate second full collection is byte-identical to the first;
- the container identity, image identity, start timestamp and restart count remained unchanged;
- the source repository, index, governing-document hashes and four exclusions remained unchanged;
- no prohibited data or state-changing action was used.

C2B1 therefore closes for this exact selected-source manifest.

The installed app roots do not contain `.git` metadata. Exact app Git revisions, branches and whole-tree dirty state are unavailable and are not inferred. This receipt proves only that the 69 selected installed files in the recorded immutable image are byte-identical to their accepted official-tag references. It does not prove that either complete app tree is clean or wholly identical to an official release tag.

No accounting formula, permission behavior, snapshot rule, fiscal/closing treatment, Finance Book behavior, dimension behavior, adapter choice, runtime contract or public payload is accepted by hash equality alone.

## 2. Source and container provenance receipt

### 2.1 Authoritative source before and after fingerprinting

| Item | Verified value |
| --- | --- |
| Source repository | `/home/deploy/erp-projects/erpai_project1_erpnext_ui_design` |
| Branch | `feature/erpnext-ui-design` |
| `HEAD` and upstream | `83e309c309dc7c9512ddf40877a64bac9a0e5df9` |
| Ahead/behind | `0/0` |
| Git index | Empty |
| Capability-map SHA-256 | `9c9748a243744c57175d684d1f963e337dacaac5aa36f1faf420d7a92642e2bd` |
| Five-phase-plan SHA-256 | `5081302170ce7657b93c8ba9a8e98dc5bcf65057d329c2b591ebc21a39e5de28` |
| C2A1/C2B1 inventory SHA-256 | `99a4c8826c8b02ef9c584d6acd6693104d55dfdbb1a7dd8a9e01818c9d6931d8` |
| C2A2-C2A5 profile SHA-256 | `e4f9aee3e160f7bc07f9f6cadf247c069ffe0dc2dd60f598b04cbe00c6803e8b` |

### 2.2 Immutable container/image relationship

| Item | Verified value |
| --- | --- |
| Backend container | `erpai_project1-backend-1` |
| Container ID | `d7835253b02c0176fb49d84672037c8566d6ac7d29f6b92b4e3baa7c9df20813` |
| Configured image | `ghcr.io/htayaung-data/erpnext-factory:erp16.4.1-hrms16.4.0-fac2.3.1-frappe16.5.0` |
| Immutable image ID | `sha256:4c8b6fb188d81f5a355008730a1122658af88799ec759029c2dbd297dfc8e257` |
| Repository digest | `ghcr.io/htayaung-data/erpnext-factory@sha256:4c8b6fb188d81f5a355008730a1122658af88799ec759029c2dbd297dfc8e257` |
| Image creation timestamp | `2026-02-11T03:00:05.608819397+06:30` |
| Container start timestamp, pre/post | `2026-07-16T10:35:05.171026789Z` |
| Container restart count, pre/post | `0` |

Only explicitly formatted Docker fields were read. Environment, labels, mounts, networking, commands, host configuration, history and logs were not inspected.

### 2.3 Installed app provenance

| App | Exact root | Declared/selected reference | Official reference | Git metadata | Selected-file result |
| --- | --- | --- | --- | --- | --- |
| ERPNext | `/home/frappe/frappe-bench/apps/erpnext` | v16.4.1 from immutable image tag and selected-source equality | Commit `d74a649016d8bb12ee3c5a24361171cebe860bfc`, tree `89af8accb3b1c5d1a1000a792301ca2eec300f7d` | Absent; revision and dirty state unavailable | 43/43 exact matches |
| Frappe | `/home/frappe/frappe-bench/apps/frappe` | v16.5.0 from immutable image tag and selected-source equality | Commit `4dfcc56090eb3101d18ddb03750391511f163fcf`, tree `725e06e6319cef5a671884cba1b8b8841f40f99e` | Absent; revision and dirty state unavailable | 26/26 exact matches |

## 3. Manifest authority and validation

The manifest was extracted only from the committed C2A1/C2B1 receipt at source `HEAD`.

| Check | Result |
| --- | --- |
| Receipt Git blob | `f5f13fe408cba29b0eec1654d52715e8635c20a6` |
| ERPNext path count | 43 |
| Frappe path count | 26 |
| Total path count | 69 |
| Duplicate paths | 0 |
| Duplicate hashes | 0 |
| Prefix mismatches | 0 |
| Invalid SHA-256 formats | 0 |
| Canonical manifest SHA-256 | `063f716c4138d6bf1f69ecf9e71b4f1bd9c0e5cb4118a5841aa2b5cc6de9d40c` |

Canonical manifest form is UTF-8 without BOM, rows `repository|relative_path|sha256` using the exact repository labels `ERPNext` and `Frappe`, sorted by repository and path, LF separators and a final LF. Because every installed hash matches, the installed selected-source path/hash manifest has the same canonical digest. The reviewer-proposed digest `3a3371c01766ff9fd530c2c56969e660265e66f6a9f5c397c73ce81ea094c849` was rejected because it was not reproducible under its stated canonicalization; no installed-file result changed.

## 4. Exact installed-file matrix

SHA-256 values are over raw installed bytes without line-ending normalization.

| App | Relative path | Bytes | Official SHA-256 | Installed SHA-256 | Result |
| --- | --- | ---: | --- | --- | --- |
| ERPNext | `erpnext/__init__.py` | 5418 | `bbb8c9817966cb87fcdbf23fde36183facc71f669c11b6f6f6bb2cd18ec4b995` | `bbb8c9817966cb87fcdbf23fde36183facc71f669c11b6f6f6bb2cd18ec4b995` | Match |
| ERPNext | `erpnext/accounts/report/trial_balance/trial_balance.py` | 16272 | `3da0acd3e65e9203193a7914dbdadac077b2cfb316e9313e0fc450edb3feedc9` | `3da0acd3e65e9203193a7914dbdadac077b2cfb316e9313e0fc450edb3feedc9` | Match |
| ERPNext | `erpnext/accounts/report/trial_balance/trial_balance.js` | 3338 | `28fecc0dd936d3518b4c907bbdc24809d43ffd7779ecec2d85a6ddd4dedbe3b4` | `28fecc0dd936d3518b4c907bbdc24809d43ffd7779ecec2d85a6ddd4dedbe3b4` | Match |
| ERPNext | `erpnext/accounts/report/trial_balance/trial_balance.json` | 566 | `72c9725546a40ad08356fc634fcece441b4a2e6a01e02b666c23d47edb630c07` | `72c9725546a40ad08356fc634fcece441b4a2e6a01e02b666c23d47edb630c07` | Match |
| ERPNext | `erpnext/accounts/report/general_ledger/general_ledger.py` | 24588 | `d0c3d97d31815bb2bbe093a93f863961a17b451a6dfcd83bd711f48dad4085eb` | `d0c3d97d31815bb2bbe093a93f863961a17b451a6dfcd83bd711f48dad4085eb` | Match |
| ERPNext | `erpnext/accounts/report/general_ledger/general_ledger.js` | 5786 | `91142805f9b3210736c7f65c3a2525859df36f63cf1c1b2c3429c11d77620499` | `91142805f9b3210736c7f65c3a2525859df36f63cf1c1b2c3429c11d77620499` | Match |
| ERPNext | `erpnext/accounts/report/general_ledger/general_ledger.json` | 634 | `0240470a761b0c7d82d5dfc4e2978a4141cf6450de33bb6e45d0b16d18997c7f` | `0240470a761b0c7d82d5dfc4e2978a4141cf6450de33bb6e45d0b16d18997c7f` | Match |
| ERPNext | `erpnext/accounts/report/financial_statements.py` | 23855 | `8390fe5ffc99c9e78734dda304a7c569e50b57f7bf006b7266584ae92a001c27` | `8390fe5ffc99c9e78734dda304a7c569e50b57f7bf006b7266584ae92a001c27` | Match |
| ERPNext | `erpnext/accounts/report/utils.py` | 12737 | `e80e643e6c6587c2986d088ab9fb9290e6e637c7dc3e80416f7414a21ba5b650` | `e80e643e6c6587c2986d088ab9fb9290e6e637c7dc3e80416f7414a21ba5b650` | Match |
| ERPNext | `erpnext/accounts/utils.py` | 80475 | `3154dec3a4ad34e62060736869a68ade0583e2219f8c86e602e409f36091757b` | `3154dec3a4ad34e62060736869a68ade0583e2219f8c86e602e409f36091757b` | Match |
| ERPNext | `erpnext/accounts/general_ledger.py` | 27679 | `f6c73176bee3c5de9f62ace638b7e4f14d3e6db51bfe68c460c70657ddc2cab5` | `f6c73176bee3c5de9f62ace638b7e4f14d3e6db51bfe68c460c70657ddc2cab5` | Match |
| ERPNext | `erpnext/accounts/doctype/gl_entry/gl_entry.py` | 16389 | `0a165bc5f3d6e456dc475153dd316f973fb41b7d3dcb6b0f40baf9d7c52b8418` | `0a165bc5f3d6e456dc475153dd316f973fb41b7d3dcb6b0f40baf9d7c52b8418` | Match |
| ERPNext | `erpnext/accounts/doctype/gl_entry/gl_entry.json` | 9122 | `f7d2c1d47f22828ea02a9eb2500ab62ae1c30c0789a3d9fd364a3600fc632547` | `f7d2c1d47f22828ea02a9eb2500ab62ae1c30c0789a3d9fd364a3600fc632547` | Match |
| ERPNext | `erpnext/accounts/doctype/account/account.py` | 23045 | `2dea7a8f232fbbbb73f9663a912e3c31f4c8c336e06bd160f43ca964d3fccb3d` | `2dea7a8f232fbbbb73f9663a912e3c31f4c8c336e06bd160f43ca964d3fccb3d` | Match |
| ERPNext | `erpnext/accounts/doctype/account/account.json` | 6103 | `201c924aa67073d8cea3f0de7025427144d26194630b3f394cdea59af1b4776d` | `201c924aa67073d8cea3f0de7025427144d26194630b3f394cdea59af1b4776d` | Match |
| ERPNext | `erpnext/accounts/doctype/account_closing_balance/account_closing_balance.py` | 5968 | `ff995a103e7409ddd31a8f3c5aa76652aafadbde655a08f323f7ba80371363e3` | `ff995a103e7409ddd31a8f3c5aa76652aafadbde655a08f323f7ba80371363e3` | Match |
| ERPNext | `erpnext/accounts/doctype/account_closing_balance/account_closing_balance.json` | 4107 | `de0d4e67720be4538a36322870d9f503785a70be794dcfe2e1d1692f39553036` | `de0d4e67720be4538a36322870d9f503785a70be794dcfe2e1d1692f39553036` | Match |
| ERPNext | `erpnext/accounts/doctype/period_closing_voucher/period_closing_voucher.py` | 18198 | `a7eaa7a1c95a82cce8f1be67f2a028791e4cab36596cb8292e32a23f807b3a79` | `a7eaa7a1c95a82cce8f1be67f2a028791e4cab36596cb8292e32a23f807b3a79` | Match |
| ERPNext | `erpnext/accounts/doctype/period_closing_voucher/period_closing_voucher.json` | 3437 | `cb2b9e21a29ffc5bc46dc5aa60064632b72e656191e08bf625fe1f4ad451189c` | `cb2b9e21a29ffc5bc46dc5aa60064632b72e656191e08bf625fe1f4ad451189c` | Match |
| ERPNext | `erpnext/accounts/doctype/process_period_closing_voucher/process_period_closing_voucher.py` | 18851 | `bd56d5fd76074a488bd1572242b3dc518f06c3a062ba76b6d003dc1c37e2869a` | `bd56d5fd76074a488bd1572242b3dc518f06c3a062ba76b6d003dc1c37e2869a` | Match |
| ERPNext | `erpnext/accounts/doctype/process_period_closing_voucher/process_period_closing_voucher.json` | 2292 | `58368d5cd2018b20ce973a4c48587a8dde507be9eac410bbc25ecf238e53bf46` | `58368d5cd2018b20ce973a4c48587a8dde507be9eac410bbc25ecf238e53bf46` | Match |
| ERPNext | `erpnext/setup/doctype/company/company.py` | 34494 | `6992db08e59a78051e1ae44ec111afb167675c4ddac0d02b2ae86064d18c4818` | `6992db08e59a78051e1ae44ec111afb167675c4ddac0d02b2ae86064d18c4818` | Match |
| ERPNext | `erpnext/setup/doctype/company/company.json` | 25867 | `56027e0202cf41bd113a3c0488a1610d1acb3cddf2bce8dad0476f5be42dc8f1` | `56027e0202cf41bd113a3c0488a1610d1acb3cddf2bce8dad0476f5be42dc8f1` | Match |
| ERPNext | `erpnext/accounts/doctype/fiscal_year/fiscal_year.py` | 4852 | `2553443adede8bec90ccce18d77b62fc3d46857126ffb8ab919c4db6e2a7d6b6` | `2553443adede8bec90ccce18d77b62fc3d46857126ffb8ab919c4db6e2a7d6b6` | Match |
| ERPNext | `erpnext/accounts/doctype/fiscal_year/fiscal_year.json` | 2598 | `2cb667684dba596e23240457b88cbc46833692fe8516c6dc26dcf41eeb1863b9` | `2cb667684dba596e23240457b88cbc46833692fe8516c6dc26dcf41eeb1863b9` | Match |
| ERPNext | `erpnext/accounts/doctype/fiscal_year_company/fiscal_year_company.py` | 530 | `0040ed34b21ef5d768a29d60585e555178ff091363d04331a3669297c98a740b` | `0040ed34b21ef5d768a29d60585e555178ff091363d04331a3669297c98a740b` | Match |
| ERPNext | `erpnext/accounts/doctype/fiscal_year_company/fiscal_year_company.json` | 692 | `18d042d4fd1b8bfb651c1a329d0d233a8514b46f168fd1a4b5c0ed7ea4daf19c` | `18d042d4fd1b8bfb651c1a329d0d233a8514b46f168fd1a4b5c0ed7ea4daf19c` | Match |
| ERPNext | `erpnext/accounts/doctype/accounting_period/accounting_period.py` | 3710 | `9175996f1f5cd83d74572f8abbd995e398ab5ff11ff5421b43aa091c61352278` | `9175996f1f5cd83d74572f8abbd995e398ab5ff11ff5421b43aa091c61352278` | Match |
| ERPNext | `erpnext/accounts/doctype/accounting_period/accounting_period.json` | 2405 | `202369edfacae81848e00e4e53928d3babf3393e35d84acacde285f73a3bb1bd` | `202369edfacae81848e00e4e53928d3babf3393e35d84acacde285f73a3bb1bd` | Match |
| ERPNext | `erpnext/accounts/doctype/accounts_settings/accounts_settings.py` | 6031 | `a43284a9f40eee726367ee8a317193e2cebc55458159bba3dd5ef29e8f163e7a` | `a43284a9f40eee726367ee8a317193e2cebc55458159bba3dd5ef29e8f163e7a` | Match |
| ERPNext | `erpnext/accounts/doctype/accounts_settings/accounts_settings.json` | 20168 | `35874c00ba3450e9c0a0122064b29763dc3ba7b817ab504e63d0655e0fd89eb8` | `35874c00ba3450e9c0a0122064b29763dc3ba7b817ab504e63d0655e0fd89eb8` | Match |
| ERPNext | `erpnext/accounts/doctype/finance_book/finance_book.py` | 454 | `b607368d79c5c2c046bc31481b9974ba5f1e8df47ed3df16877cadf700125e82` | `b607368d79c5c2c046bc31481b9974ba5f1e8df47ed3df16877cadf700125e82` | Match |
| ERPNext | `erpnext/accounts/doctype/finance_book/finance_book.json` | 1177 | `b87733b195add89b5dbfdb635a419ce0d76cffbecdd5574edab17f8c01e7c4d5` | `b87733b195add89b5dbfdb635a419ce0d76cffbecdd5574edab17f8c01e7c4d5` | Match |
| ERPNext | `erpnext/accounts/doctype/accounting_dimension/accounting_dimension.py` | 10005 | `15a7fefbf1aa39ef0a2fc30a3624901a64aec08ed36fd85c889c2812dd64ca5a` | `15a7fefbf1aa39ef0a2fc30a3624901a64aec08ed36fd85c889c2812dd64ca5a` | Match |
| ERPNext | `erpnext/accounts/doctype/accounting_dimension/accounting_dimension.json` | 1614 | `4f5281ac4428fc575a95a1d9fd1f1b231223ffc33a1007838b8836986983f56d` | `4f5281ac4428fc575a95a1d9fd1f1b231223ffc33a1007838b8836986983f56d` | Match |
| ERPNext | `erpnext/accounts/doctype/accounting_dimension_detail/accounting_dimension_detail.py` | 770 | `75dc4e564bf629e05a125a49592c857d52d1a2019b10f84cf3e2a4bbb1fe12ac` | `75dc4e564bf629e05a125a49592c857d52d1a2019b10f84cf3e2a4bbb1fe12ac` | Match |
| ERPNext | `erpnext/accounts/doctype/accounting_dimension_detail/accounting_dimension_detail.json` | 1981 | `df2c6950613b5e54a91b76b1f260e4df38949eafd0393dabc123311f17a177f5` | `df2c6950613b5e54a91b76b1f260e4df38949eafd0393dabc123311f17a177f5` | Match |
| ERPNext | `erpnext/accounts/doctype/accounting_dimension_filter/accounting_dimension_filter.py` | 3329 | `2ae391d894f04ce3de919ae4a772451d6693807e115436b1984c5ed74d15cd1c` | `2ae391d894f04ce3de919ae4a772451d6693807e115436b1984c5ed74d15cd1c` | Match |
| ERPNext | `erpnext/accounts/doctype/accounting_dimension_filter/accounting_dimension_filter.json` | 3128 | `bed452531a1b16c2e4dc1c8fb6dc511cf17ead662e12daacd908fd0509ad366b` | `bed452531a1b16c2e4dc1c8fb6dc511cf17ead662e12daacd908fd0509ad366b` | Match |
| ERPNext | `erpnext/accounts/doctype/cost_center/cost_center.py` | 4879 | `676e1b52af9088ec21e2ddf33a7af1b8289923c0f221797e2cf19c5eb9902c63` | `676e1b52af9088ec21e2ddf33a7af1b8289923c0f221797e2cf19c5eb9902c63` | Match |
| ERPNext | `erpnext/accounts/doctype/cost_center/cost_center.json` | 3501 | `9cd8aa58d8ea6988a57c294461dd9001d20aa869d860dfd19dd04ca101d3116e` | `9cd8aa58d8ea6988a57c294461dd9001d20aa869d860dfd19dd04ca101d3116e` | Match |
| ERPNext | `erpnext/projects/doctype/project/project.py` | 23305 | `8d7f0da733b11770df2eb92366a6e508357ade5742d464e4e42f1a24705521d1` | `8d7f0da733b11770df2eb92366a6e508357ade5742d464e4e42f1a24705521d1` | Match |
| ERPNext | `erpnext/projects/doctype/project/project.json` | 11791 | `b26beb7707127e58723030274578a128895485b2305cef40ca892076c35ba313` | `b26beb7707127e58723030274578a128895485b2305cef40ca892076c35ba313` | Match |
| Frappe | `frappe/__init__.py` | 44389 | `3e70b6fd55b5a2947bc8961ea6ec47a41dd0f4a0e287c3c9eabed21a3c894340` | `3e70b6fd55b5a2947bc8961ea6ec47a41dd0f4a0e287c3c9eabed21a3c894340` | Match |
| Frappe | `frappe/desk/query_report.py` | 28589 | `af65b6f40eaaf54e561fe4e3f06429b1114d650c7ef91d8bf77a9971eea7de70` | `af65b6f40eaaf54e561fe4e3f06429b1114d650c7ef91d8bf77a9971eea7de70` | Match |
| Frappe | `frappe/desk/reportview.py` | 24161 | `d5f4e02d07253026a43dfc7ed1f1f4a2dc5a36e2d8ffa99ad0f5995acda4574e` | `d5f4e02d07253026a43dfc7ed1f1f4a2dc5a36e2d8ffa99ad0f5995acda4574e` | Match |
| Frappe | `frappe/core/doctype/report/report.py` | 12801 | `8e30fe3330f40b75637a0c24be4492be98405e68d79e0dff09041360c798f164` | `8e30fe3330f40b75637a0c24be4492be98405e68d79e0dff09041360c798f164` | Match |
| Frappe | `frappe/core/doctype/report/report.json` | 5830 | `68babac28939a617bce0b59eafd849130c49d2ea1ff08343f3013b0bf5b62704` | `68babac28939a617bce0b59eafd849130c49d2ea1ff08343f3013b0bf5b62704` | Match |
| Frappe | `frappe/core/doctype/page/page.py` | 5756 | `0e865063a1652a1cafc37311191f29175b8e71a7f3faa0143ee2deb9f2b6b56b` | `0e865063a1652a1cafc37311191f29175b8e71a7f3faa0143ee2deb9f2b6b56b` | Match |
| Frappe | `frappe/core/doctype/page/page.json` | 2514 | `db6a3829afcb0bb04a76f97b2cd89295776a62d312498ef1f861eae40794e7c0` | `db6a3829afcb0bb04a76f97b2cd89295776a62d312498ef1f861eae40794e7c0` | Match |
| Frappe | `frappe/core/doctype/doctype/doctype.py` | 64903 | `a0cb3ba030e81a2462b88b603bdb989514a1b4befac9a50ab8ba3a8c386e52e3` | `a0cb3ba030e81a2462b88b603bdb989514a1b4befac9a50ab8ba3a8c386e52e3` | Match |
| Frappe | `frappe/core/doctype/doctype/doctype.json` | 18750 | `0b44ecc676ebe52fdd984bc6f02b1702b49b2f272102b8977568df120c287cd8` | `0b44ecc676ebe52fdd984bc6f02b1702b49b2f272102b8977568df120c287cd8` | Match |
| Frappe | `frappe/core/doctype/docfield/docfield.py` | 3960 | `bab8a19fcdfea33d01f2ad624d221c0dd7164cc3d9fcbcb872612e5cfedb926b` | `bab8a19fcdfea33d01f2ad624d221c0dd7164cc3d9fcbcb872612e5cfedb926b` | Match |
| Frappe | `frappe/core/doctype/docfield/docfield.json` | 15955 | `56b6c07252605a085e525648b92cdb889aac6c3e967f8a05e382328fd68fa48c` | `56b6c07252605a085e525648b92cdb889aac6c3e967f8a05e382328fd68fa48c` | Match |
| Frappe | `frappe/core/doctype/user_permission/user_permission.py` | 9396 | `7976aa1a74422267bbf5967ca179ee24796cd7f8ccabb6fd8437b9fbb2d07eae` | `7976aa1a74422267bbf5967ca179ee24796cd7f8ccabb6fd8437b9fbb2d07eae` | Match |
| Frappe | `frappe/core/doctype/user_permission/user_permission.json` | 2334 | `522034601b85231aecc97b976c34043edfc0e16ed57cd6564319729805e4fa3c` | `522034601b85231aecc97b976c34043edfc0e16ed57cd6564319729805e4fa3c` | Match |
| Frappe | `frappe/permissions.py` | 27887 | `5097cb7f6a65bd1bf9ace8ad91e8b5a7aa5dfaf5eab71cc6b5b207cdda44963d` | `5097cb7f6a65bd1bf9ace8ad91e8b5a7aa5dfaf5eab71cc6b5b207cdda44963d` | Match |
| Frappe | `frappe/model/db_query.py` | 46117 | `73817632e1fb76e48bb33ef9ae0b098b80a0dabc7a1119a677301fc3419b8651` | `73817632e1fb76e48bb33ef9ae0b098b80a0dabc7a1119a677301fc3419b8651` | Match |
| Frappe | `frappe/model/qb_query.py` | 11831 | `06b1434b3bb9cc264daa103c4bf8bcce7da763982e9a5e3c63e171435b79d490` | `06b1434b3bb9cc264daa103c4bf8bcce7da763982e9a5e3c63e171435b79d490` | Match |
| Frappe | `frappe/model/meta.py` | 30892 | `aa06e26a6b0f506c2d7b138a36a09320a977ee8c823e7bc8efa4896a7a8dace7` | `aa06e26a6b0f506c2d7b138a36a09320a977ee8c823e7bc8efa4896a7a8dace7` | Match |
| Frappe | `frappe/model/document.py` | 68286 | `e4f80af70712c50a16d574123cd4c4dab115f60ff0f2a0f8bdb7ae668f4a69e2` | `e4f80af70712c50a16d574123cd4c4dab115f60ff0f2a0f8bdb7ae668f4a69e2` | Match |
| Frappe | `frappe/database/database.py` | 46670 | `efd51bd657ef9b24734399b8808927689ca1438eb4790e3dd8c22fbb4151a4d1` | `efd51bd657ef9b24734399b8808927689ca1438eb4790e3dd8c22fbb4151a4d1` | Match |
| Frappe | `frappe/database/query.py` | 83365 | `79a7e3bc6f6e6045aa6fdf483c078e33fc2386088c54841e3a4311a56cb309ed` | `79a7e3bc6f6e6045aa6fdf483c078e33fc2386088c54841e3a4311a56cb309ed` | Match |
| Frappe | `frappe/core/doctype/system_settings/system_settings.py` | 8969 | `7529723ab1675e6476d6d9254661b7fddc65f2f5ac732bed5942abf66ada0474` | `7529723ab1675e6476d6d9254661b7fddc65f2f5ac732bed5942abf66ada0474` | Match |
| Frappe | `frappe/core/doctype/system_settings/system_settings.json` | 22090 | `ed0f0d3d0ba8c9d3c0b4baf8d03b72943e7b7f6b77475002921f779d00bb5497` | `ed0f0d3d0ba8c9d3c0b4baf8d03b72943e7b7f6b77475002921f779d00bb5497` | Match |
| Frappe | `frappe/geo/doctype/currency/currency.py` | 1114 | `849a5565ad955146964c9262cf0edb88c73a0d9b9d0a44cd3c9b400cf2d95d4d` | `849a5565ad955146964c9262cf0edb88c73a0d9b9d0a44cd3c9b400cf2d95d4d` | Match |
| Frappe | `frappe/geo/doctype/currency/currency.json` | 2811 | `3febb4d294ca1f046580fa4beb41cda64f79fd62c0ceac32dd7e25b9a86c0693` | `3febb4d294ca1f046580fa4beb41cda64f79fd62c0ceac32dd7e25b9a86c0693` | Match |
| Frappe | `frappe/utils/data.py` | 82267 | `147f36c2e591f93178cf9eb8c8326bd9c0699f0f924d602a1b3b7125ad3d73f8` | `147f36c2e591f93178cf9eb8c8326bd9c0699f0f924d602a1b3b7125ad3d73f8` | Match |
| Frappe | `frappe/query_builder/functions.py` | 4818 | `79ff6564f325af739de2698755280d914269fd42fb0f9e56dcf9a780a748daf5` | `79ff6564f325af739de2698755280d914269fd42fb0f9e56dcf9a780a748daf5` | Match |

## 5. Repeatability and no-change evidence

| Control | Result |
| --- | --- |
| First selected-file collection | 69 present, 69 matches, 0 deltas, 0 other states |
| Immediate second collection | Identical to the first |
| Container ID/image ID | Unchanged pre/post |
| Container start/restart posture | Unchanged; start timestamp stable, restart count 0 |
| Source `HEAD`/upstream | Unchanged at `83e309c309dc7c9512ddf40877a64bac9a0e5df9`, `0/0` |
| Source Git index | Empty before and after |
| Governing-document hashes | Unchanged before and after |
| Four exclusion hashes | Unchanged before and after |

Any later change to image identity, selected path, file type, byte size or SHA-256 invalidates this receipt and reopens C2B1 for the affected evidence.

## 6. Access and command containment receipt

Permitted operations actually used were limited to:

- committed source Git reads and manifest parsing;
- formatted container/image identity fields;
- exact app-root resolution and `.git` presence checks;
- exact manifest count, prefix, uniqueness and hash-format validation;
- for each selected path: regular-file, symlink, readability and root-containment checks, byte size and SHA-256;
- one immediate repeat collection;
- pre/post source, exclusion and container-identity checks.

The following were not accessed or invoked:

- `/home/deploy/erp-projects/erpai_project1` or any live deployment-tree file;
- site databases, SQL, ORM, DocTypes, reports, bench console or operational records;
- site configuration, environment variables, credentials, secrets, logs, backups, private files or uploads;
- raw source copying from the container;
- network fetch, package installation, Git fetch/checkout/reset/clean or repair;
- container or file writes, restarts, cache clear, metadata reload, migration or permission changes;
- endpoints, browsers, protected gates, AI tools or accounting execution.

Two bounded command-format attempts failed before evidence collection stabilized: one was rejected locally by PowerShell and one established that the app root was not a Git repository; a delimiter-format attempt emitted only generic tokens. Independent security review found no sensitive disclosure, path broadening, write or High/Blocker issue. The corrected evidence commands stayed within the approved boundary.

## 7. Findings and independent review disposition

| Severity | Finding | Disposition |
| --- | --- | --- |
| None for C2B1 closure | All 69 selected installed files match their accepted official-tag references under one immutable image identity. | Close C2B1 for the bounded manifest. |
| Provenance limitation | App `.git` metadata is absent; exact revision, branch and dirty state are unavailable. | Do not claim whole-app equivalence or cleanliness. Selected-file equality plus immutable image identity is the accepted substitute for C2B1. |
| High future containment | A semantic dependency outside the 69-file manifest may be discovered during C2B2-C2B6. | Stop and obtain an exact allowlist/fingerprint extension before relying on it. |
| High future accounting/permission gate | Hash equality proves bytes, not formulas, permission behavior, complete-chart authority, consistency or public safety. | C2B2-C2B7 remain required and unstarted. |
| High future Finance-to-AI gate | AI company, row/report authority and trace-retention posture remain incompatible and unapproved. | No Finance-to-AI work. |

Reviewer dispositions from the single bounded synthesis pass:

- accounting/source provenance: accepted `c2b1_installed_source_fingerprint_closed_for_bounded_69_path_manifest`;
- security: `security_boundary_pass_with_provenance_caveat`;
- release/governance: accepted `c2b1_installed_source_fingerprint_closed`;
- Main Control synthesis: accept closure for the 69-path selected-source scope and carry the provenance limitation forward.

## 8. Phase state and next approval boundary

| Mini-phase | State |
| --- | --- |
| C2A1-C2A5 | Complete and published. |
| C2B1 Installed source inventory/fingerprint | Closed for the frozen 69-path scope. |
| C2B2 GL Entry lifecycle proof | Not started. |
| C2B3 Trial Balance algorithm proof | Not started. |
| C2B4 Fiscal and closing proof | Not started. |
| C2B5 Finance Book, currency and dimension proof | Not started. |
| C2B6 Permission, completeness, consistency and adapter proof | Not started. |
| C2B7 Synthesis | Not started. |
| C2C-C2E | Not started. |

The next substantive Owner gate is:

`finance_cycle2_gl_tb_c2b2_c2b6_source_semantic_proof_authorized`

If granted, it authorizes bounded read-only semantic and permission analysis of only fingerprinted installed source, with internally parallel specialist research where dependencies permit and one C2B7 synthesis later. It does not authorize operational data, runtime code, endpoint/UI work, staging, commit, push, live alignment, metadata, permissions, protected gates, Finance-to-AI access or accounting execution.

## 9. Exact documentation candidate and exclusions

The exact documentation candidate for this result is:

1. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/finance-accounting-cycle2-c2b1-exact-installed-source-fingerprint-receipt-2026-07-17.md`
2. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/README.md`

The four unrelated exclusions remain outside the candidate:

| Path | Required status and SHA-256 |
| --- | --- |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py` | Modified, unstaged; `01668e175610d9d090ea51018badbde8b021103afe13ed878782a58b8ce3b224` |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/browser_supplier_payables_fixture_diagnostic.py` | Untracked; `d9822184b26f3c1ebaf5b93663b1f6c3a495b6482f013092d955748dfdf963c5` |
| `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/ui_smoke/sales_final_acceptance_audit.js` | Untracked; `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/a.out` | Untracked; `0063411e61152850243132aa87ef12844a8724adb671bf4f38793bcd2b1ce339` |

No staging, commit or push is implied. Those remain separate documentation gates.
