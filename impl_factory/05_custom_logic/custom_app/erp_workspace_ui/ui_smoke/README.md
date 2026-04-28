# ERP Workspace UI Smoke Suite

This folder contains the first Playwright smoke suite for the PrimeAxis child-page runtime.

Scope in this first pass:

1. authenticate into Desk
2. open one `Sales Order` page
3. open one `Quotation` page
4. open one `Delivery Note` page
5. open one `Sales Invoice` page
6. assert shared runtime diagnostics markers for:
   - shell mount
   - shell skeleton
   - shell prepare
   - support shell
   - sidebar cleanup
   - workflow banner attach attempt
   - context load ready state
   - shell release on `Sales Order`

## Environment

Required:

1. `ERPW_BASE_URL`
2. `ERPW_SALES_ORDER_NAME` or `ERPW_SALES_ORDER_ROUTE`
3. `ERPW_QUOTATION_NAME` or `ERPW_QUOTATION_ROUTE`
4. `ERPW_DELIVERY_NOTE_NAME` or `ERPW_DELIVERY_NOTE_ROUTE`
5. `ERPW_SALES_INVOICE_NAME` or `ERPW_SALES_INVOICE_ROUTE`

Optional:

1. `ERPW_HEADLESS`
   - set to `0` for headed mode
2. `ERPW_DIAGNOSTIC_TIMEOUT`
   - default `30000`
3. `ERPW_SESSION_SID`
   - preferred for live local smoke if a valid Desk session already exists
4. `ERPW_USERNAME`
5. `ERPW_PASSWORD`
   - only required when `ERPW_SESSION_SID` is not provided

## Install

```bash
cd impl_factory/05_custom_logic/custom_app/erp_workspace_ui/ui_smoke
npm install
npx playwright install chromium
```

Containerized fallback:

```bash
docker run --rm --network host \
  -v "$PWD":/workspace \
  -w /workspace/impl_factory/05_custom_logic/custom_app/erp_workspace_ui/ui_smoke \
  mcr.microsoft.com/playwright:v1.59.1-jammy \
  bash -lc 'npm test'
```

## Run

```bash
cd impl_factory/05_custom_logic/custom_app/erp_workspace_ui/ui_smoke
ERPW_BASE_URL="http://127.0.0.1:8000" \
ERPW_USERNAME="Administrator" \
ERPW_PASSWORD="admin" \
ERPW_SALES_ORDER_NAME="SAL-ORD-0001" \
ERPW_QUOTATION_NAME="QTN-0001" \
ERPW_DELIVERY_NOTE_NAME="DN-0001" \
ERPW_SALES_INVOICE_NAME="SINV-0001" \
npm test
```

Session-cookie mode:

```bash
cd impl_factory/05_custom_logic/custom_app/erp_workspace_ui/ui_smoke
ERPW_BASE_URL="http://127.0.0.1:8083" \
ERPW_SESSION_SID="existing-session-sid" \
ERPW_SALES_ORDER_NAME="SAL-ORD-2026-00025" \
ERPW_QUOTATION_NAME="SAL-QTN-2026-00005" \
ERPW_DELIVERY_NOTE_NAME="MAT-DN-2026-00015" \
ERPW_SALES_INVOICE_NAME="ACC-SINV-2026-00209" \
npm test
```

## Notes

1. this suite intentionally asserts runtime diagnostics instead of deep visual layout
2. workflow banner is allowed to settle to either `ready` or `missing`, because not every document will be workflow-locked
3. session-cookie mode is the safest option for local validation when the site already has a valid authenticated session
4. the Docker image tag should match the pinned Playwright package version in `package.json`
5. this suite is the minimum smoke foundation, not the full enterprise UI regression layer

## Reference Screenshot Capture

This suite now supports governed reference screenshot capture for the finished PrimeAxis pages.

Captured pages:

1. `Sales Console`
2. `Sales Order`
3. `Quotation`
4. `Delivery Note`
5. `Sales Invoice`

Additional required environment variables for capture mode:

1. `ERPW_CAPTURE_REFERENCE`
   - set to `1` to enable the capture spec
2. `ERPW_CAPTURE_ROOT`
   - optional output root
   - default: `ui_smoke/artifacts/reference_screenshots`
3. `ERPW_SALES_CONSOLE_ROUTE`
   - optional override for `Sales Console`
   - default: `/desk/sales-console`

Run screenshot capture:

```bash
cd impl_factory/05_custom_logic/custom_app/erp_workspace_ui/ui_smoke
ERPW_BASE_URL="http://127.0.0.1:8000" \
ERPW_SESSION_SID="existing-session-sid" \
ERPW_SALES_ORDER_NAME="SAL-ORD-2026-00025" \
ERPW_QUOTATION_NAME="SAL-QTN-2026-00005" \
ERPW_DELIVERY_NOTE_NAME="MAT-DN-2026-00015" \
ERPW_SALES_INVOICE_NAME="ACC-SINV-2026-00209" \
ERPW_CAPTURE_REFERENCE="1" \
npm run capture:references
```

Output structure:

1. `artifacts/reference_screenshots/sales_console/...`
2. `artifacts/reference_screenshots/sales_order/...`
3. `artifacts/reference_screenshots/quotation/...`
4. `artifacts/reference_screenshots/delivery_note/...`
5. `artifacts/reference_screenshots/sales_invoice/...`

Capture mode is intentionally separate from the default smoke run.
