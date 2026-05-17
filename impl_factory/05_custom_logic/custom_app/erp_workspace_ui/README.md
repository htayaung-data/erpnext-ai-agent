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

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch feature/erpnext-ui-design
bench install-app erp_workspace_ui
```

### License

mit
