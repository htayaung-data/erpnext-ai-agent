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
      supplierDetail: "procurement-console-supplier",
      itemDetail: "procurement-console-item",
      purchaseRequestReview: "procurement-console-purchase-request-review",
      purchaseRequestForm: "procurement-console-purchase-request-form",
      rfqForm: "procurement-console-rfq-form",
      rfqReview: "procurement-console-rfq-review",
      supplierQuotationForm: "procurement-console-supplier-quotation-form",
      supplierQuotationReview: "procurement-console-supplier-quotation-review",
      purchaseOrderForm: "procurement-console-purchase-order-form",
    },
    methods: {
      bootstrap: "erp_workspace_ui.procurement_console.service.get_procurement_console_bootstrap",
      sidebarContext: "erp_workspace_ui.procurement_console.service.get_procurement_console_sidebar_context",
      workspaceSearch: "erp_workspace_ui.procurement_console.service.search_procurement_console_workspace",
      quickFind: "erp_workspace_ui.procurement_console.service.get_procurement_quick_find_suggestions",
      worklistContext: "erp_workspace_ui.procurement_console.worklist.get_procurement_console_worklist_context",
      reportContext: "erp_workspace_ui.procurement_console.report.get_procurement_console_report_context",
      poFollowUpDetailContext: "erp_workspace_ui.procurement_console.purchase_order_detail.get_purchase_order_follow_up_detail_context",
      supplierDetailContext: "erp_workspace_ui.procurement_console.supplier_detail.get_supplier_detail_context",
      itemDetailContext: "erp_workspace_ui.procurement_console.items.get_item_detail_context",
      purchaseRequestReviewContext: "erp_workspace_ui.procurement_console.document_reviews.get_purchase_request_review_context",
      managedPurchaseRequestContext: "erp_workspace_ui.procurement_console.managed_purchase_request.get_managed_purchase_request_context",
      managedPurchaseRequestSave: "erp_workspace_ui.procurement_console.managed_purchase_request.save_managed_purchase_request_draft",
      managedPurchaseRequestItemDefaults: "erp_workspace_ui.procurement_console.managed_purchase_request.get_managed_purchase_request_item_defaults",
      managedRfqContext: "erp_workspace_ui.procurement_console.managed_rfq.get_managed_rfq_context",
      managedRfqSave: "erp_workspace_ui.procurement_console.managed_rfq.save_managed_rfq_draft",
      managedRfqItemDefaults: "erp_workspace_ui.procurement_console.managed_rfq.get_managed_rfq_item_defaults",
      managedSupplierQuotationContext: "erp_workspace_ui.procurement_console.managed_supplier_quotation.get_managed_supplier_quotation_context",
      managedSupplierQuotationSave: "erp_workspace_ui.procurement_console.managed_supplier_quotation.save_managed_supplier_quotation_draft",
      managedSupplierQuotationItemDefaults: "erp_workspace_ui.procurement_console.managed_supplier_quotation.get_managed_supplier_quotation_item_defaults",
      managedPurchaseOrderContext: "erp_workspace_ui.procurement_console.managed_purchase_order.get_managed_purchase_order_context",
      managedPurchaseOrderSave: "erp_workspace_ui.procurement_console.managed_purchase_order.save_managed_purchase_order",
      managedPurchaseOrderItemDefaults: "erp_workspace_ui.procurement_console.managed_purchase_order.get_managed_purchase_order_item_defaults",
      rfqReviewContext: "erp_workspace_ui.procurement_console.document_reviews.get_rfq_review_context",
      supplierQuotationReviewContext: "erp_workspace_ui.procurement_console.document_reviews.get_supplier_quotation_review_context",
    },
    managedDoctypes: {
      Supplier: "supplier_directory",
      "Supplier Group": "supplier_directory",
      Item: "buying_item_directory",
      "Item Price": "buying_item_directory",
      "Item Supplier": "buying_item_directory",
      "Material Request": "purchase_request_directory",
      "Request for Quotation": "rfq_directory",
      "Supplier Quotation": "supplier_quotation_directory",
      "Purchase Order": "purchase_order_directory",
      "Purchase Receipt": "pending_receipt_visibility",
      "Purchase Invoice": "billing_status_visibility",
    },
    directoryQueuesByDoctype: {
      Supplier: "supplier_directory",
      Item: "buying_item_directory",
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
      { key: "buying_item_directory", label: "Buying Items", icon: "item", target: { kind: "worklist", queue_key: "buying_item_directory" } },
      { key: "procurement_reports", label: "Reports", icon: "report", target: { kind: "page", route: "procurement-console-report" } },
    ],
  };

  const warehouseWorkspace = {
    workspaceId: "warehouse",
    status: "w5b_outbound_picking_review",
    title: "Warehouse Console",
    modeLabel: "Warehouse Workspace",
    roleFamily: "Warehouse",
    routes: {
      home: "warehouse-console",
      homePath: "/desk/warehouse-console",
      worklist: "warehouse-console-worklist",
      worklistPath: "/desk/warehouse-console-worklist",
      receiving: "warehouse-console-receiving",
      receivingPath: "/desk/warehouse-console-receiving",
      picking: "warehouse-console-picking",
      pickingPath: "/desk/warehouse-console-picking",
    },
    methods: {
      overview: "erp_workspace_ui.warehouse_console.service.get_warehouse_console_overview",
      inboundQueue: "erp_workspace_ui.warehouse_console.service.get_warehouse_inbound_receiving_queue",
      outboundQueue: "erp_workspace_ui.warehouse_console.service.get_warehouse_outbound_picking_queue",
      receivingDetail: "erp_workspace_ui.warehouse_console.service.get_warehouse_receiving_review",
      pickingDetail: "erp_workspace_ui.warehouse_console.service.get_warehouse_picking_review",
      sidebarContext: "erp_workspace_ui.warehouse_console.service.get_warehouse_console_sidebar_context",
    },
    managedDoctypes: {
      Warehouse: "warehouse_console_home",
      Item: "warehouse_console_home",
      Bin: "warehouse_console_home",
      "Purchase Order": "inbound_receiving",
      "Sales Order": "outbound_picking",
    },
    sidebar: {
      homeKey: "warehouse_console_home",
      homeLabel: "Overview",
      sectionKey: "workspace",
      sectionLabel: "Workspace",
    },
    search: {
      enabled: false,
    },
    fallbackItems: [
      { key: "warehouse_console_home", label: "Overview", icon: "item", target: { kind: "page", route: "warehouse-console" } },
      { key: "inbound_receiving", label: "Inbound Receiving", icon: "quotation", target: { kind: "worklist", queue_key: "inbound_receiving" } },
      { key: "outbound_picking", label: "Outbound Picking", icon: "order", target: { kind: "worklist", queue_key: "outbound_picking" } },
    ],
  };


  const activeWorkspaces = {
    sales: salesWorkspace,
    procurement: procurementWorkspace,
    warehouse: warehouseWorkspace,
  };

  const roadmap = [
    { workspaceId: "sales", matrixName: "Sales Console", recommendedName: "Sales Console", wave: "first", priority: 1, status: "frozen" },
    { workspaceId: "procurement", matrixName: "Procurement Console", recommendedName: "Procurement Console", wave: "first", priority: 2, status: "phase_3" },
    { workspaceId: "warehouse", matrixName: "Warehouse Console", recommendedName: "Warehouse Console", wave: "first", priority: 3, status: "w5b_outbound_picking_review" },
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
      const routeValues = Object.keys(routes).filter((key) => !/Path$/.test(key)).map((key) => routes[key]);
      if (routeValues.includes(normalized)) {
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

  function warehouse() {
    return get("warehouse");
  }

  root.erpWorkspaceUiWorkspaceRegistry = {
    get,
    getByRoute,
    route,
    sales,
    procurement,
    warehouse,
    roadmap: () => clone(roadmap),
  };
})();
