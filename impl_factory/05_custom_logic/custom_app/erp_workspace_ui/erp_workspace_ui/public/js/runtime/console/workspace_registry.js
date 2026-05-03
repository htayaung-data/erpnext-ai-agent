/* global window */

(function () {
  const root = window;

  const salesWorkspace = {
    workspaceId: "sales",
    status: "frozen",
    title: "Sales Console",
    modeLabel: "Sales Workspace",
    roleFamily: "Sales",
    freezeTag: "sales-console-freeze-v1",
    routes: {
      launcher: "sales-console-home",
      launcherPath: "/desk/sales-console-home",
      home: "sales-console",
      homePath: "/desk/sales-console",
      worklist: "sales-console-worklist",
      report: "sales-console-report",
    },
    methods: {
      bootstrap: "erp_workspace_ui.sales_console.service.get_sales_console_bootstrap",
      sidebarContext: "erp_workspace_ui.sales_console.service.get_sales_console_sidebar_context",
      workspaceSearch: "erp_workspace_ui.sales_console.service.search_sales_console_workspace",
      worklistContext: "erp_workspace_ui.sales_console.worklist.get_sales_console_worklist_context",
      reportContext: "erp_workspace_ui.sales_console.report.get_sales_console_report_context",
    },
    managedDoctypes: {
      Quotation: "quotation_directory",
      "Sales Order": "sales_order_directory",
      Customer: "customer_directory",
      Item: "item_directory",
      "Delivery Note": "sales_order_directory",
      "Sales Invoice": "sales_order_directory",
    },
    directoryQueuesByDoctype: {
      Quotation: "quotation_directory",
      "Sales Order": "sales_order_directory",
      Customer: "customer_directory",
      Item: "item_directory",
    },
    sidebar: {
      homeKey: "sales_console_home",
      homeLabel: "Overview",
      sectionKey: "browse",
      sectionLabel: "Browse",
    },
    fallbackItems: [
      { key: "sales_console_home", label: "Overview", icon: "home", target: { kind: "page", route: "sales-console" } },
      { key: "quotation_directory", label: "Quotations", icon: "quotation", target: { kind: "worklist", queue_key: "quotation_directory" } },
      { key: "sales_order_directory", label: "Sales Orders", icon: "order", target: { kind: "worklist", queue_key: "sales_order_directory" } },
      { key: "customer_directory", label: "Customers", icon: "customer", target: { kind: "worklist", queue_key: "customer_directory" } },
      { key: "item_directory", label: "Items", icon: "item", target: { kind: "worklist", queue_key: "item_directory" } },
    ],
  };

  const procurementWorkspace = {
    workspaceId: "procurement",
    status: "phase_3",
    title: "Procurement Console",
    modeLabel: "Procurement Workspace",
    roleFamily: "Procurement",
    routes: {
      launcher: "procurement-console-home",
      launcherPath: "/desk/procurement-console-home",
      home: "procurement-console",
      homePath: "/desk/procurement-console",
      worklist: "procurement-console-worklist",
      report: "procurement-console-report",
      poFollowUp: "procurement-console-po-follow-up",
    },
    methods: {
      bootstrap: "erp_workspace_ui.procurement_console.service.get_procurement_console_bootstrap",
      sidebarContext: "erp_workspace_ui.procurement_console.service.get_procurement_console_sidebar_context",
      workspaceSearch: "erp_workspace_ui.procurement_console.service.search_procurement_console_workspace",
      worklistContext: "erp_workspace_ui.procurement_console.worklist.get_procurement_console_worklist_context",
      reportContext: "erp_workspace_ui.procurement_console.report.get_procurement_console_report_context",
      poFollowUpDetailContext: "erp_workspace_ui.procurement_console.purchase_order_detail.get_purchase_order_follow_up_detail_context",
    },
    managedDoctypes: {
      Supplier: "supplier_directory",
      "Supplier Group": "supplier_directory",
      Item: "supplier_price_review",
      "Item Price": "supplier_price_review",
      "Item Supplier": "supplier_price_review",
      "Material Request": "purchase_request_directory",
      "Request for Quotation": "rfq_directory",
      "Supplier Quotation": "supplier_quotation_directory",
      "Purchase Order": "purchase_order_directory",
      "Purchase Receipt": "pending_receipt_visibility",
      "Purchase Invoice": "billing_status_visibility",
    },
    directoryQueuesByDoctype: {
      Supplier: "supplier_directory",
      "Material Request": "purchase_request_directory",
      "Request for Quotation": "rfq_directory",
      "Supplier Quotation": "supplier_quotation_directory",
      "Purchase Order": "purchase_order_directory",
    },
    downstreamVisibilityDoctypes: {
      "Purchase Receipt": "pending_receipt_visibility",
      "Purchase Invoice": "billing_status_visibility",
    },
    sidebar: {
      homeKey: "procurement_console_home",
      homeLabel: "Overview",
      sectionKey: "workspace",
      sectionLabel: "Workspace",
    },
    fallbackItems: [
      { key: "procurement_console_home", label: "Overview", icon: "home", target: { kind: "page", route: "procurement-console" } },
      { key: "supplier_directory", label: "Suppliers", icon: "customer", target: { kind: "worklist", queue_key: "supplier_directory" } },
      { key: "purchase_request_directory", label: "Purchase Requests", icon: "quotation", target: { kind: "worklist", queue_key: "purchase_request_directory" } },
      { key: "purchase_order_directory", label: "Purchase Orders", icon: "order", target: { kind: "worklist", queue_key: "purchase_order_directory" } },
      { key: "rfq_directory", label: "RFQs", icon: "quotation", target: { kind: "worklist", queue_key: "rfq_directory" } },
      { key: "supplier_quotation_directory", label: "Supplier Quotations", icon: "quotation", target: { kind: "worklist", queue_key: "supplier_quotation_directory" } },
      { key: "supplier_quotation_comparison", label: "Quote Comparison", icon: "report", target: { kind: "report", report_key: "supplier_quotation_comparison" } },
    ],
  };

  const activeWorkspaces = {
    sales: salesWorkspace,
    procurement: procurementWorkspace,
  };

  const roadmap = [
    { workspaceId: "sales", matrixName: "Sales Console", recommendedName: "Sales Console", wave: "first", priority: 1, status: "frozen" },
    { workspaceId: "procurement", matrixName: "Procurement Console", recommendedName: "Procurement Console", wave: "first", priority: 2, status: "phase_3" },
    { workspaceId: "warehouse", matrixName: "Warehouse Console", recommendedName: "Warehouse Console", wave: "first", priority: 3, status: "planned" },
    { workspaceId: "finance", matrixName: "Finance Console", recommendedName: "Finance Control Desk", wave: "first", priority: 4, status: "name_review" },
    { workspaceId: "executive", matrixName: "Executive Console", recommendedName: "Management Daily Brief", wave: "second", priority: 5, status: "name_review" },
    { workspaceId: "customer_service", matrixName: "Customer Service Console", recommendedName: "Customer Service Console", wave: "second", priority: 6, status: "planned" },
    { workspaceId: "hr_admin", matrixName: "HR and Admin Console", recommendedName: "HR and Admin Console", wave: "second", priority: 7, status: "planned" },
    { workspaceId: "erp_admin", matrixName: "ERP Admin Console", recommendedName: "ERP Admin Console", wave: "second", priority: 8, status: "planned" },
  ];

  function clone(value) {
    return JSON.parse(JSON.stringify(value || null));
  }

  function get(workspaceId) {
    return clone(activeWorkspaces[String(workspaceId || "sales").trim()] || null);
  }

  function getByRoute(routeKey) {
    const normalized = String(routeKey || "").trim();
    if (!normalized) return null;
    const workspaces = Object.keys(activeWorkspaces).map((key) => activeWorkspaces[key]);
    for (let index = 0; index < workspaces.length; index += 1) {
      const workspace = workspaces[index];
      const routes = workspace.routes || {};
      if ([routes.launcher, routes.home, routes.worklist, routes.report, routes.poFollowUp].includes(normalized)) {
        return clone(workspace);
      }
    }
    return null;
  }

  function route(workspaceId, routeKind) {
    const workspace = activeWorkspaces[String(workspaceId || "sales").trim()];
    return workspace && workspace.routes ? workspace.routes[String(routeKind || "").trim()] || "" : "";
  }

  function sales() {
    return get("sales");
  }

  function procurement() {
    return get("procurement");
  }

  root.erpWorkspaceUiWorkspaceRegistry = {
    get,
    getByRoute,
    route,
    sales,
    procurement,
    roadmap: () => clone(roadmap),
  };
})();
