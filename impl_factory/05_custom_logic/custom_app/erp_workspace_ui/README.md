### ERP Workspace UI

Enterprise ERPNext workspace and console experience for the UI workstream.

### Purpose

- Own role-based ERPNext workspace and page implementation for the UI branch.
- Keep workspace UX implementation separate from the AI Assistant app.
- Provide the production home for consoles such as `Sales Console`.

### Ownership Boundary

- This app owns ERPNext workspace and page UX for the UI workstream.
- This app does not own AI runtime, assistant orchestration, or governed query logic.
- AI integration inside workspaces should consume approved assistant surfaces without moving assistant logic into this app.

### Initial Scope

- app foundation and module ownership
- Sales Console implementation surface
- future workspace/page assets for console families

### Current Sales Console Source Of Truth

Current confirmed branch: `feature/erpnext-ui-design`

Current confirmed commit: `6dbd85c fix: forward socket origin through caddy`

The confirmed Sale Console surface is:

1. `/desk/sales-console`
2. `/desk/sales-console-worklist/<queue-key>`
3. `/desk/sales-console-report/<report-key>`
4. managed ERP forms for `Quotation`, `Sales Order`, `Delivery Note`, and `Sales Invoice`

Confirmed stable sidebar destinations:

1. `Overview`
2. `Quotations`
3. `Sales Orders`
4. `Customers`
5. `Items`

Confirmed report family:

1. `Sales Analytics`
2. `Sales Order Analysis`
3. `Trend Analysis`
4. `Lost Quotations`
5. `Collections Status`
6. `Item-wise Sales History`

The standalone `Sales Dashboard` page was removed before freeze. `Trend Analysis` is the visible trend page; legacy `quotation_trends` remains only as a backward-compatible route into `Trend Analysis` with `Quotation` selected.

Final validation on 2026-05-03 covered unit contracts, JavaScript and Python syntax, Docker browser role smoke, Sales Order Analysis smoke, full live Sales Console route probing for Sales Manager and Sales User, restricted-route safety checks, and Socket.IO realtime connection.

### Deployment Note

The production Caddy `/socket.io` proxy must forward `Origin`:

```caddyfile
header_up Origin https://{host}
```

This keeps ERPNext realtime connected and prevents the Frappe Socket.IO `Invalid origin` rejection.

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch feature/erpnext-ui-design
bench install-app erp_workspace_ui
```

### License

mit
