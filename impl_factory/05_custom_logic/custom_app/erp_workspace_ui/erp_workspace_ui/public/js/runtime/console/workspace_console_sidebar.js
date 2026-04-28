/* global frappe */

(function () {
  const root = window;
  const consoleRuntime = root.erpWorkspaceConsoleRuntime || {};
  const sidebarRuntime = root.erpWorkspaceConsoleSidebar = root.erpWorkspaceConsoleSidebar || {};
  const STYLE_ID = "erpw-sales-console-sidebar-style";
  const SIDEBAR_METHOD = "erp_workspace_ui.sales_console.service.get_sales_console_sidebar_context";
  const SEARCH_METHOD = "erp_workspace_ui.sales_console.service.search_sales_console_workspace";
  const MANAGED_BODY_CLASS = "erpw-sales-console-sidebar-managed";
  const MANAGED_FORM_ACTIVE_KEYS = {
    "Quotation": "quotation_directory",
    "Sales Order": "sales_order_directory",
    "Customer": "customer_directory",
    "Item": "item_directory",
    "Delivery Note": "sales_order_directory",
    "Sales Invoice": "sales_order_directory",
  };
  const SLUG_FORM_DOCTYPES = {
    quotation: "Quotation",
    "sales-order": "Sales Order",
    sales_order: "Sales Order",
    customer: "Customer",
    item: "Item",
    "delivery-note": "Delivery Note",
    delivery_note: "Delivery Note",
    "sales-invoice": "Sales Invoice",
    sales_invoice: "Sales Invoice",
  };

  let cachedContext = null;
  let contextPromise = null;
  let syncTimer = null;
  let mutationSyncTimer = null;
  let sidebarMutationObserver = null;
  let listenersBound = false;
  let searchDialog = null;
  let searchTimer = null;
  let searchRequestToken = 0;
  let searchResults = [];
  let searchActiveIndex = -1;

  function escapeHtml(value) {
    if (typeof consoleRuntime.escapeHtml === "function") {
      return consoleRuntime.escapeHtml(value);
    }
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function iconMarkup(name) {
    if (typeof consoleRuntime.iconMarkup === "function") {
      return consoleRuntime.iconMarkup(name);
    }
    return "";
  }

  function ensureStyles() {
    if (document.getElementById(STYLE_ID)) return;

    const style = document.createElement("style");
    style.id = STYLE_ID;
    style.textContent = `
      .erpw-sales-console-sidebar-nav {
        margin-top: 8px;
      }
      .${MANAGED_BODY_CLASS} .body-sidebar {
        container-type: inline-size;
      }
      .${MANAGED_BODY_CLASS} .body-sidebar .item-anchor,
      .${MANAGED_BODY_CLASS} .body-sidebar .collapse-sidebar-link,
      .${MANAGED_BODY_CLASS} .body-sidebar button {
        cursor: pointer;
        user-select: none;
      }
      .${MANAGED_BODY_CLASS} .body-sidebar .erpw-sales-console-sidebar-header .drop-icon {
        display: none !important;
        pointer-events: none !important;
      }
      .${MANAGED_BODY_CLASS} .body-sidebar .navbar-search-bar {
        display: none !important;
      }
      .${MANAGED_BODY_CLASS} .body-sidebar .sidebar-notification {
        display: none !important;
      }
      .${MANAGED_BODY_CLASS} .body-sidebar .body-sidebar-top .sidebar-items > .sidebar-item-container:not([data-erpw-sales-console-nav='1']) {
        display: none !important;
      }
      .${MANAGED_BODY_CLASS} .body-sidebar .body-sidebar-top .edit-mode {
        display: none !important;
      }
      .${MANAGED_BODY_CLASS} .body-sidebar .sidebar-item-container:has(> .standard-sidebar-item > .item-anchor[href="/desk/sales-console"]),
      .${MANAGED_BODY_CLASS} .body-sidebar .sidebar-item-container:has(> .standard-sidebar-item > .item-anchor[href$="/desk/sales-console"]) {
        display: none !important;
      }
      .${MANAGED_BODY_CLASS} .body-sidebar .sidebar-item-container > .standard-sidebar-item.active-sidebar {
        min-height: 40px;
        border-radius: 12px;
        border: 1px solid rgba(230, 235, 242, 0.98);
        background: #ffffff;
        box-shadow:
          0 1px 2px rgba(15, 23, 42, 0.04),
          0 6px 16px rgba(15, 23, 42, 0.05);
      }
      .${MANAGED_BODY_CLASS} .body-sidebar .sidebar-item-container > .standard-sidebar-item.active-sidebar .item-anchor {
        min-height: 40px;
        height: 40px;
        gap: 10px;
        padding: 5px 9px;
      }
      .${MANAGED_BODY_CLASS} .body-sidebar .sidebar-item-container > .standard-sidebar-item.active-sidebar .sidebar-item-icon {
        padding: 7px;
      }
      .erpw-sales-console-sidebar-shell {
        display: grid;
        gap: 10px;
      }
      .erpw-sales-console-sidebar-utilities {
        display: grid;
        gap: 6px;
        margin-bottom: 2px;
        padding-bottom: 8px;
        border-bottom: 1px solid rgba(229, 235, 243, 0.88);
      }
      .erpw-sales-console-sidebar-utility {
        display: grid;
        grid-template-columns: 28px minmax(0, 1fr) auto;
        align-items: center;
        justify-items: start;
        gap: 8px;
        width: 100%;
        min-width: 0;
        max-width: 100%;
        box-sizing: border-box;
        min-height: 40px;
        padding: 5px 9px;
        border: 1px solid rgba(255, 255, 255, 0);
        border-radius: 12px;
        background: transparent;
        color: #334155;
        box-shadow: none;
        text-align: left;
        transition: background 120ms ease, border-color 120ms ease, box-shadow 120ms ease, color 120ms ease;
      }
      .erpw-sales-console-sidebar-utility:hover {
        background: rgba(255, 255, 255, 0.92);
        border-color: rgba(229, 235, 243, 0.96);
        color: #0f172a;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
      }
      .erpw-sales-console-sidebar-utility-icon {
        width: 28px;
        height: 28px;
        display: inline-grid;
        place-items: center;
        border-radius: 9px;
        border: 1px solid rgba(228, 234, 242, 0.96);
        background: #ffffff;
        color: #64748b;
      }
      .erpw-sales-console-sidebar-utility-icon svg {
        width: 14px;
        height: 14px;
      }
      .erpw-sales-console-sidebar-utility-copy {
        min-width: 0;
        justify-self: start;
        text-align: left;
      }
      .erpw-sales-console-sidebar-utility-title {
        display: block;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        font-size: 13px;
        font-weight: 600;
        line-height: 1.35;
      }
      .erpw-sales-console-sidebar-utility-meta {
        font-size: 11px;
        line-height: 1.35;
        color: #94a3b8;
      }
      .erpw-sales-console-sidebar-utility-shortcut {
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.01em;
        color: #94a3b8;
        justify-self: end;
        white-space: nowrap;
      }
      .erpw-sales-console-sidebar-head {
        display: grid;
        gap: 4px;
        padding: 0 8px 4px;
      }
      .erpw-sales-console-sidebar-title {
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #52627a;
      }
      .erpw-sales-console-sidebar-mode {
        font-size: 13px;
        font-weight: 600;
        color: #0f172a;
        line-height: 1.35;
      }
      .erpw-sales-console-sidebar-scope {
        font-size: 11.5px;
        line-height: 1.45;
        color: #64748b;
      }
      .erpw-sales-console-sidebar-section {
        display: grid;
        gap: 2px;
      }
      .erpw-sales-console-sidebar-section-label {
        padding: 0 8px 2px;
        font-size: 10.5px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #94a3b8;
      }
      .erpw-sales-console-sidebar-item .standard-sidebar-item {
        width: 100%;
      }
      .erpw-sales-console-sidebar-link {
        display: grid !important;
        grid-template-columns: 28px minmax(0, 1fr);
        align-items: center;
        justify-items: start;
        gap: 8px !important;
        width: 100%;
        min-width: 0;
        max-width: 100%;
        box-sizing: border-box;
        min-height: 40px;
        padding: 5px 9px;
        border: 1px solid rgba(255, 255, 255, 0);
        border-radius: 12px;
        background: transparent;
        color: #334155;
        box-shadow: none;
        text-align: left;
        transition: background 120ms ease, border-color 120ms ease, color 120ms ease, box-shadow 120ms ease;
        outline: none;
      }
      .erpw-sales-console-sidebar-link:hover {
        background: rgba(255, 255, 255, 0.92);
        border-color: rgba(229, 235, 243, 0.96);
        color: #0f172a;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
      }
      .erpw-sales-console-sidebar-link.is-active {
        background: #ffffff;
        border-color: rgba(230, 235, 242, 0.98);
        color: #0f172a;
        box-shadow:
          0 1px 2px rgba(15, 23, 42, 0.04),
          0 6px 16px rgba(15, 23, 42, 0.05);
      }
      .erpw-sales-console-sidebar-link:focus,
      .erpw-sales-console-sidebar-link:active {
        outline: none;
      }
      .erpw-sales-console-sidebar-link:focus-visible {
        outline: none;
        border-color: rgba(230, 235, 242, 0.98);
        box-shadow:
          0 1px 2px rgba(15, 23, 42, 0.04),
          0 0 0 2px rgba(255, 255, 255, 0.9);
      }
      .erpw-sales-console-sidebar-icon {
        width: 28px;
        height: 28px;
        display: inline-grid;
        place-items: center;
        border-radius: 9px;
        border: 1px solid rgba(228, 234, 242, 0.96);
        background: #ffffff;
        color: #64748b;
        box-shadow: none;
      }
      .erpw-sales-console-sidebar-link.is-active .erpw-sales-console-sidebar-icon {
        border-color: rgba(228, 234, 242, 0.98);
        background: #ffffff;
        color: #334155;
      }
      .erpw-sales-console-sidebar-icon svg {
        width: 14px;
        height: 14px;
      }
      .erpw-sales-console-sidebar-copy {
        min-width: 0;
        justify-self: start;
        text-align: left;
      }
      .erpw-sales-console-sidebar-text {
        display: block;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        font-size: 13px;
        font-weight: 600;
        line-height: 1.35;
      }
      .erpw-sales-console-search-dialog .modal-dialog {
        max-width: 760px;
      }
      .erpw-sales-console-search-shell {
        display: grid;
        gap: 12px;
        padding-top: 2px;
      }
      .erpw-sales-console-search-bar {
        display: grid;
        grid-template-columns: 38px minmax(0, 1fr) auto;
        align-items: center;
        gap: 10px;
        min-height: 52px;
        padding: 0 14px;
        border: 1px solid rgba(214, 223, 236, 0.98);
        border-radius: 16px;
        background: #ffffff;
        box-shadow:
          0 1px 2px rgba(15, 23, 42, 0.03),
          0 10px 24px rgba(15, 23, 42, 0.04);
      }
      .erpw-sales-console-search-bar-icon {
        width: 28px;
        height: 28px;
        display: inline-grid;
        place-items: center;
        border-radius: 10px;
        border: 1px solid rgba(228, 234, 242, 0.98);
        background: #ffffff;
        color: #64748b;
      }
      .erpw-sales-console-search-bar-icon svg {
        width: 15px;
        height: 15px;
      }
      .erpw-sales-console-search-input {
        width: 100%;
        border: none;
        background: transparent;
        font-size: 13.5px;
        font-weight: 500;
        color: #0f172a;
        outline: none;
        box-shadow: none;
      }
      .erpw-sales-console-search-input::placeholder {
        color: #94a3b8;
        font-weight: 500;
      }
      .erpw-sales-console-search-status {
        font-size: 12px;
        line-height: 1.5;
        color: #64748b;
      }
      .erpw-sales-console-search-status[hidden] {
        display: none;
      }
      .erpw-sales-console-search-results {
        display: grid;
        gap: 12px;
        max-height: min(58vh, 560px);
        overflow: auto;
        padding-right: 2px;
      }
      .erpw-sales-console-search-results[hidden] {
        display: none;
      }
      .erpw-sales-console-search-group {
        display: grid;
        gap: 6px;
      }
      .erpw-sales-console-search-group-label {
        padding-left: 2px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #94a3b8;
      }
      .erpw-sales-console-search-result {
        display: grid;
        grid-template-columns: auto minmax(0, 1fr);
        align-items: start;
        gap: 12px;
        width: 100%;
        padding: 12px 14px;
        border: 1px solid rgba(229, 235, 243, 0.96);
        border-radius: 14px;
        background: #ffffff;
        text-align: left;
        transition: border-color 120ms ease, box-shadow 120ms ease, transform 120ms ease;
      }
      .erpw-sales-console-search-result:hover,
      .erpw-sales-console-search-result.is-active {
        border-color: rgba(203, 213, 225, 0.96);
        box-shadow:
          0 1px 2px rgba(15, 23, 42, 0.04),
          0 10px 20px rgba(15, 23, 42, 0.05);
      }
      .erpw-sales-console-search-result-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-height: 24px;
        padding: 0 8px;
        border-radius: 999px;
        border: 1px solid rgba(228, 234, 242, 0.98);
        background: #f8fafc;
        color: #52627a;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        white-space: nowrap;
      }
      .erpw-sales-console-search-result-copy {
        min-width: 0;
        display: grid;
        gap: 3px;
      }
      .erpw-sales-console-search-result-title {
        font-size: 13px;
        font-weight: 700;
        color: #0f172a;
        line-height: 1.4;
      }
      .erpw-sales-console-search-result-meta {
        font-size: 12px;
        line-height: 1.5;
        color: #64748b;
      }
      @container (max-width: 80px) {
        .erpw-sales-console-sidebar-nav {
          margin-top: 8px;
        }
        .erpw-sales-console-sidebar-shell,
        .erpw-sales-console-sidebar-section {
          gap: 8px;
        }
        .erpw-sales-console-sidebar-utilities {
          gap: 8px;
          padding-bottom: 10px;
        }
        .erpw-sales-console-sidebar-section-label,
        .erpw-sales-console-sidebar-utility-copy,
        .erpw-sales-console-sidebar-utility-shortcut,
        .erpw-sales-console-sidebar-copy {
          display: none !important;
        }
        .erpw-sales-console-sidebar-utility,
        .erpw-sales-console-sidebar-link {
          display: inline-grid;
          grid-template-columns: 28px;
          justify-content: center;
          justify-items: center;
          width: 31px;
          min-width: 31px;
          max-width: 31px;
          min-height: 40px;
          padding: 5px 1px;
          gap: 0;
        }
        .erpw-sales-console-sidebar-item,
        .erpw-sales-console-sidebar-item .standard-sidebar-item {
          width: 31px;
          min-width: 31px;
          max-width: 31px;
        }
      }
    `;
    document.head.appendChild(style);
  }

  function decodeRoutePart(value) {
    try {
      return decodeURIComponent(String(value || ""));
    } catch (error) {
      return String(value || "");
    }
  }

  function routeFromLocation() {
    const pathname = String((root.location && root.location.pathname) || "");
    const parts = pathname
      .replace(/^\/+/, "")
      .split("/")
      .filter(Boolean)
      .map(decodeRoutePart);
    if (!parts.length) return [];

    const routeParts = parts[0] === "desk" || parts[0] === "app" ? parts.slice(1) : parts;
    if (!routeParts.length) return [];

    const pageKey = routeParts[0];
    if (SLUG_FORM_DOCTYPES[pageKey]) {
      return ["Form", SLUG_FORM_DOCTYPES[pageKey], routeParts[1] || ""];
    }
    return routeParts;
  }

  function getRoute() {
    const route = frappe.get_route ? frappe.get_route() : [];
    return Array.isArray(route) && route.length ? route : routeFromLocation();
  }

  function isSalesConsoleHomeRoute(route) {
    const pageKey = Array.isArray(route) ? String(route[0] || "") : "";
    return pageKey === "sales-console" || pageKey === "sales-console-home";
  }

  function getManagedFormDoctype(route) {
    if (!Array.isArray(route) || !route.length) return "";

    const pageKey = String(route[0] || "");
    if (pageKey === "Form") {
      const doctype = String(route[1] || "");
      return MANAGED_FORM_ACTIVE_KEYS[doctype] ? doctype : "";
    }

    const slugDoctype = SLUG_FORM_DOCTYPES[pageKey];
    return slugDoctype && MANAGED_FORM_ACTIVE_KEYS[slugDoctype] ? slugDoctype : "";
  }

  function isManagedRoute(route) {
    if (!Array.isArray(route) || !route.length) return false;
    const pageKey = String(route[0] || "");
    if (pageKey === "sales-console" || pageKey === "sales-console-home") return true;
    if (pageKey === "sales-console-worklist" || pageKey === "sales-console-report") return true;
    if (getManagedFormDoctype(route)) return true;
    return false;
  }

  function resolveActiveKey(route) {
    if (!Array.isArray(route) || !route.length) return "";
    const pageKey = String(route[0] || "");
    const managedDoctype = getManagedFormDoctype(route);
    if (managedDoctype) return MANAGED_FORM_ACTIVE_KEYS[managedDoctype] || "";
    if (pageKey === "sales-console" || pageKey === "sales-console-home") return "sales_console_home";
    if (pageKey === "sales-console-worklist") {
      const worklistKey = String(route[1] || "").replace(/-/g, "_");
      if (["quotation_directory", "quotations_waiting_action", "quotations_awaiting_approval", "expiring_quotations"].includes(worklistKey)) {
        return "quotation_directory";
      }
      if ([
        "sales_order_directory",
        "open_orders",
        "sales_orders_pending_fulfillment",
        "orders_due_soon",
        "orders_blocked_by_approval",
        "partially_delivered_orders",
        "invoices_outstanding",
        "sales_returns_in_progress",
      ].includes(worklistKey)) {
        return "sales_order_directory";
      }
      return worklistKey;
    }
    if (pageKey === "sales-console-report") return "";
    return "";
  }

  function getSidebarHost() {
    const topHost = document.querySelector(".body-sidebar-top .sidebar-items");
    const bottomHost = document.querySelector(".body-sidebar-bottom");
    return {
      topHost,
      bottomHost,
      host: topHost || bottomHost,
    };
  }

  function ensureManagedSidebarHost() {
    let bodySidebar = document.querySelector(".body-sidebar");
    if (!bodySidebar) return getSidebarHost();

    let topSection = bodySidebar.querySelector(".body-sidebar-top");
    if (!topSection) {
      topSection = document.createElement("div");
      topSection.className = "body-sidebar-top";
      const bottomSection = bodySidebar.querySelector(".body-sidebar-bottom");
      bodySidebar.insertBefore(topSection, bottomSection || null);
    }

    let topHost = topSection.querySelector(".sidebar-items");
    if (!topHost) {
      topHost = document.createElement("div");
      topHost.className = "sidebar-items";
      topSection.insertBefore(topHost, topSection.firstChild);
    }

    return getSidebarHost();
  }

  function removeGuideItem() {
    document.querySelectorAll("[data-sales-console-guide='1']").forEach((node) => node.remove());
  }

  function removeSidebar() {
    document.querySelectorAll("[data-erpw-sales-console-nav='1']").forEach((node) => node.remove());
  }

  function clearSidebarArtifacts(route) {
    setManagedBodyState(false);
    setManagedSidebarHeader(false);
    removeSidebar();
    if (searchDialog && !isManagedRoute(route)) {
      searchDialog.hide();
    }
    if (!isSalesConsoleHomeRoute(route)) {
      removeGuideItem();
    }
  }

  function hasVisibleNativeSidebarArtifacts() {
    return Array.from(document.querySelectorAll(
      ".body-sidebar .navbar-search-bar, .body-sidebar-top .sidebar-items > .sidebar-item-container:not([data-erpw-sales-console-nav='1'])"
    )).some((node) => {
      const style = root.getComputedStyle ? root.getComputedStyle(node) : null;
      const rect = typeof node.getBoundingClientRect === "function" ? node.getBoundingClientRect() : null;
      return (!style || (style.display !== "none" && style.visibility !== "hidden"))
        && (!rect || (rect.width > 0 && rect.height > 0));
    });
  }

  function setManagedBodyState(enabled) {
    if (!document.body) return;
    document.body.classList.toggle(MANAGED_BODY_CLASS, Boolean(enabled));
  }

  function getSidebarHeaderParts() {
    const header = document.querySelector(".body-sidebar .sidebar-header");
    if (!header) return null;
    return {
      header,
      icon: header.querySelector(".sidebar-item-icon .header-logo"),
      title: header.querySelector(".header-title"),
      subtitle: header.querySelector(".header-subtitle"),
    };
  }

  function createManagedSidebarHeader() {
    const bodySidebar = document.querySelector(".body-sidebar");
    if (!bodySidebar) return null;

    const header = document.createElement("a");
    header.className = "sidebar-header erpw-sales-console-sidebar-header";
    header.setAttribute("data-erpw-created-sales-console-header", "1");
    header.setAttribute("href", "/desk/sales-console");
    header.style.textDecoration = "none";
    header.style.width = "auto";
    header.style.cursor = "pointer";
    header.style.paddingLeft = "8px";
    header.style.paddingRight = "8px";
    header.innerHTML = `
      <div class="sidebar-item-icon" style="background-color: var();">
        <div class="header-logo">${managedHeaderIconMarkup()}</div>
      </div>
      <div class="title-container">
        <div class="sidebar-item-label header-title" data-name-style="">PrimeAxis</div>
        <div class="sidebar-item-label header-subtitle">Sales Console</div>
      </div>
      <button class="btn-reset drop-icon show-in-edit-mode">
        <svg class="icon icon-sm" style="display: block;margin:auto;" aria-hidden="true">
          <use class="" href="#icon-chevron-down"></use>
        </svg>
      </button>
    `;
    bodySidebar.insertBefore(header, bodySidebar.firstChild);
    return getSidebarHeaderParts();
  }

  function managedHeaderIconMarkup() {
    return `
      <div class="icon-container" style="background-color: rgb(123, 128, 138);">
        <svg fill="currentColor" class="desktop-alphabet icon text-ink-gray-7 icon-sm" stroke="none" style="color: var(--white);" aria-hidden="true">
          <use class="" href="#P"></use>
        </svg>
      </div>
    `;
  }

  function setManagedSidebarHeader(enabled) {
    let parts = getSidebarHeaderParts();
    if (!parts && enabled) {
      parts = createManagedSidebarHeader();
    }
    if (!parts) return;

    const { header, icon, title, subtitle } = parts;
    if (enabled) {
      if (!header.dataset.erpwNativeHeaderCaptured) {
        header.dataset.erpwNativeHeaderCaptured = "1";
        header.dataset.erpwNativeHeaderIcon = icon ? icon.innerHTML : "";
        header.dataset.erpwNativeHeaderTitle = title ? title.textContent : "";
        header.dataset.erpwNativeHeaderSubtitle = subtitle ? subtitle.textContent : "";
      }
      header.classList.add("erpw-sales-console-sidebar-header");
      header.setAttribute("href", "/desk/sales-console");
      if (icon) icon.innerHTML = managedHeaderIconMarkup();
      if (title) title.textContent = "PrimeAxis";
      if (subtitle) subtitle.textContent = "Sales Console";
      const dropIcon = header.querySelector(".drop-icon");
      if (dropIcon) {
        dropIcon.setAttribute("aria-hidden", "true");
        dropIcon.setAttribute("tabindex", "-1");
      }
      return;
    }

    if (header.getAttribute("data-erpw-created-sales-console-header") === "1") {
      header.remove();
      return;
    }

    if (!header.dataset.erpwNativeHeaderCaptured) return;
    header.classList.remove("erpw-sales-console-sidebar-header");
    if (icon) icon.innerHTML = header.dataset.erpwNativeHeaderIcon || "";
    if (title) title.textContent = header.dataset.erpwNativeHeaderTitle || "";
    if (subtitle) subtitle.textContent = header.dataset.erpwNativeHeaderSubtitle || "";
    delete header.dataset.erpwNativeHeaderCaptured;
    delete header.dataset.erpwNativeHeaderIcon;
    delete header.dataset.erpwNativeHeaderTitle;
    delete header.dataset.erpwNativeHeaderSubtitle;
  }

  function ensureSidebarWrapper() {
    const { topHost, bottomHost, host } = ensureManagedSidebarHost();
    if (!host) return null;

    let wrapper = document.querySelector("[data-erpw-sales-console-nav='1']");
    if (wrapper) return wrapper;

    wrapper = document.createElement("div");
    wrapper.className = "erpw-sales-console-sidebar-nav sidebar-item-container";
    wrapper.setAttribute("data-erpw-sales-console-nav", "1");

    if (topHost) {
      topHost.insertBefore(wrapper, topHost.firstChild);
      return wrapper;
    }

    const collapseLink = bottomHost ? bottomHost.querySelector(".collapse-sidebar-link") : null;
    if (collapseLink && bottomHost) {
      bottomHost.insertBefore(wrapper, collapseLink);
      return wrapper;
    }

    if (bottomHost) {
      bottomHost.appendChild(wrapper);
      return wrapper;
    }

    return null;
  }

  function fallbackContext() {
    return {
      sidebar: {
        title: "Sales Console",
        mode_label: "Sales Workspace",
        scope_label: "",
        sections: [
          {
            key: "browse",
            label: "Browse",
            items: [
              { key: "sales_console_home", label: "Overview", icon: "home", target: { kind: "page", route: "sales-console" } },
              { key: "quotation_directory", label: "Quotations", icon: "quotation", target: { kind: "worklist", queue_key: "quotation_directory" } },
              { key: "sales_order_directory", label: "Sales Orders", icon: "order", target: { kind: "worklist", queue_key: "sales_order_directory" } },
              { key: "customer_directory", label: "Customers", icon: "customer", target: { kind: "worklist", queue_key: "customer_directory" } },
              { key: "item_directory", label: "Items", icon: "item", target: { kind: "worklist", queue_key: "item_directory" } },
            ],
          },
        ],
      },
    };
  }

  function shortcutLabel() {
    const isMac = typeof navigator !== "undefined" && /Mac|iPhone|iPad/.test(String(navigator.platform || ""));
    return isMac ? "⌘K" : "Ctrl+K";
  }

  function routeToPage(route) {
    if (!route) return;
    frappe.set_route(String(route));
  }

  function routeToList(doctype, filters) {
    frappe.route_options = filters && Object.keys(filters).length ? filters : null;
    frappe.set_route("List", doctype);
  }

  function routeToReport(reportName, filters) {
    frappe.route_options = filters && Object.keys(filters).length ? filters : null;
    frappe.set_route("query-report", reportName);
  }

  function encodeRoutePart(value) {
    return encodeURIComponent(String(value || "").trim());
  }

  function customerRouteValue(filters) {
    return filters && typeof filters === "object" ? String(filters.customer || "").trim() : "";
  }

  function routeToWorklist(queueKey, filters) {
    const nextFilters = filters && Object.keys(filters).length ? filters : null;
    const normalizedQueueKey = String(queueKey || "").replace(/_/g, "-");
    const routeCustomer = customerRouteValue(nextFilters);
    frappe.route_options = nextFilters;
    if (["customer_detail", "customer_editor"].includes(String(queueKey || "").replace(/-/g, "_")) && routeCustomer) {
      frappe.set_route("sales-console-worklist", normalizedQueueKey, encodeRoutePart(routeCustomer));
      return;
    }
    frappe.set_route("sales-console-worklist", normalizedQueueKey);
  }

  function routeToReportPage(reportKey) {
    frappe.set_route("sales-console-report", String(reportKey || "").replace(/_/g, "-"));
  }

  function openNativeNotifications() {
    const dropdown = document.querySelector(".body-sidebar .dropdown-notifications");
    if (dropdown) {
      dropdown.classList.toggle("hidden");
      return true;
    }

    return false;
  }

  function executeTarget(target) {
    if (!target) return;
    if (target.notice) {
      frappe.show_alert({ message: __(target.notice), indicator: "blue" });
    }
    const routeOwner = root.erpWorkspaceUiChildPage && root.erpWorkspaceUiChildPage.helpers;
    if (
      routeOwner
      && typeof routeOwner.routeToSalesConsoleTarget === "function"
      && routeOwner.routeToSalesConsoleTarget(target)
    ) {
      return;
    }
    if (target.kind === "page" && target.route) return routeToPage(target.route);
    if (target.kind === "new_doc" && target.doctype) return frappe.new_doc(target.doctype);
    if (target.kind === "form" && target.doctype && target.name) return frappe.set_route("Form", target.doctype, target.name);
    if (target.kind === "list" && target.doctype) return routeToList(target.doctype, target.filters || null);
    if (target.kind === "report" && target.report_name) return routeToReport(target.report_name, target.filters || null);
    if (target.kind === "report_page" && target.report_key) return routeToReportPage(target.report_key);
    if (target.kind === "worklist" && target.queue_key) {
      const route = getRoute();
      const currentQueueKey = Array.isArray(route) && route[0] === "sales-console-worklist"
        ? String(route[1] || "").replace(/-/g, "_")
        : "";
      const filters = target.filters && typeof target.filters === "object" ? target.filters : null;
      if (["customer_detail", "customer_editor"].includes(String(target.queue_key || "").replace(/-/g, "_")) && customerRouteValue(filters)) {
        return routeToWorklist(target.queue_key, filters);
      }
      const worklistRuntime = root.erpWorkspaceSalesConsoleWorklist;
      if (
        filters &&
        currentQueueKey === String(target.queue_key || "") &&
        worklistRuntime &&
        typeof worklistRuntime.applyFilters === "function"
      ) {
        if (worklistRuntime.applyFilters(target.queue_key, filters)) return;
      }
      return routeToWorklist(target.queue_key, filters);
    }
  }

  function resetSearchTimer() {
    if (searchTimer) {
      window.clearTimeout(searchTimer);
      searchTimer = null;
    }
  }

  function currentSearchElements() {
    if (!searchDialog || !searchDialog.fields_dict || !searchDialog.fields_dict.search_html) return null;
    const $root = searchDialog.fields_dict.search_html.$wrapper;
    return {
      $root,
      $input: $root.find("[data-erpw-sales-search-input]"),
      $status: $root.find("[data-erpw-sales-search-status]"),
      $results: $root.find("[data-erpw-sales-search-results]"),
    };
  }

  function resetWorkspaceSearch(message) {
    resetSearchTimer();
    searchRequestToken += 1;
    searchResults = [];
    searchActiveIndex = -1;
    const elements = currentSearchElements();
    if (!elements) return;
    if (message) {
      elements.$status.text(message).removeAttr("hidden");
    } else {
      elements.$status.text("").attr("hidden", true);
    }
    elements.$results.empty().attr("hidden", true);
  }

  function setWorkspaceSearchActive(index) {
    if (!searchResults.length) {
      searchActiveIndex = -1;
      return;
    }
    const boundedIndex = Math.max(0, Math.min(index, searchResults.length - 1));
    searchActiveIndex = boundedIndex;
    const elements = currentSearchElements();
    if (!elements) return;
    const $items = elements.$results.find("[data-erpw-sales-search-index]");
    $items.removeClass("is-active").attr("aria-selected", "false");
    const $active = $items.filter(`[data-erpw-sales-search-index="${boundedIndex}"]`);
    $active.addClass("is-active").attr("aria-selected", "true");
    const activeNode = $active.get(0);
    if (activeNode) activeNode.scrollIntoView({ block: "nearest" });
  }

  function chooseWorkspaceSearchResult(index) {
    const item = searchResults[index];
    if (!item) return false;
    if (searchDialog) searchDialog.hide();
    executeTarget(item.target || null);
    return true;
  }

  function renderWorkspaceSearchResults(payload) {
    const elements = currentSearchElements();
    if (!elements) return;

    searchResults = Array.isArray(payload && payload.results) ? payload.results : [];
    searchActiveIndex = searchResults.length ? 0 : -1;

    if (!searchResults.length) {
      elements.$status.text((payload && payload.message) || "No Sales Console records match this search yet.").removeAttr("hidden");
      elements.$results.empty().attr("hidden", true);
      return;
    }

    elements.$status.text((payload && payload.message) || `${searchResults.length} result(s) found.`).removeAttr("hidden");

    const groups = [];
    searchResults.forEach((item, index) => {
      const groupKey = String(item.doctype || "Record");
      let group = groups.find((entry) => entry.key === groupKey);
      if (!group) {
        group = { key: groupKey, label: groupKey, items: [] };
        groups.push(group);
      }
      group.items.push(Object.assign({}, item, { _index: index }));
    });

    elements.$results.html(groups.map((group) => `
      <div class="erpw-sales-console-search-group">
        <div class="erpw-sales-console-search-group-label">${escapeHtml(group.label)}</div>
        ${group.items.map((item) => `
          <button
            type="button"
            class="erpw-sales-console-search-result${item._index === searchActiveIndex ? " is-active" : ""}"
            data-erpw-sales-search-index="${item._index}"
            aria-selected="${item._index === searchActiveIndex ? "true" : "false"}"
          >
            <span class="erpw-sales-console-search-result-badge">${escapeHtml(item.doctype || "Record")}</span>
            <span class="erpw-sales-console-search-result-copy">
              <span class="erpw-sales-console-search-result-title">${escapeHtml(item.label || item.name || "Unnamed record")}</span>
              <span class="erpw-sales-console-search-result-meta">${escapeHtml(item.meta || "")}</span>
            </span>
          </button>
        `).join("")}
      </div>
    `).join("")).removeAttr("hidden");

    elements.$results.find("[data-erpw-sales-search-index]").on("mouseenter", function () {
      setWorkspaceSearchActive(Number(this.getAttribute("data-erpw-sales-search-index")));
    });
    elements.$results.find("[data-erpw-sales-search-index]").on("mousedown", (event) => {
      event.preventDefault();
    });
    elements.$results.find("[data-erpw-sales-search-index]").on("click", function () {
      chooseWorkspaceSearchResult(Number(this.getAttribute("data-erpw-sales-search-index")));
    });
  }

  function runWorkspaceSearch(query) {
    const needle = String(query || "").trim();
    const requestToken = searchRequestToken + 1;
    searchRequestToken = requestToken;

    if (needle.length < 2) {
      resetWorkspaceSearch();
      return;
    }

    const elements = currentSearchElements();
    if (elements) {
      elements.$status.text("Searching...").removeAttr("hidden");
    }

    Promise.resolve(frappe.call({
      method: SEARCH_METHOD,
      args: { query: needle, limit: 12 },
    })).then((response) => {
      if (requestToken !== searchRequestToken) return;
      renderWorkspaceSearchResults(response && response.message ? response.message : {});
    }).catch(() => {
      if (requestToken !== searchRequestToken) return;
      resetWorkspaceSearch("Sales Console search is temporarily unavailable.");
    });
  }

  function scheduleWorkspaceSearch(query) {
    const needle = String(query || "").trim();
    resetSearchTimer();
    if (needle.length < 2) {
      resetWorkspaceSearch();
      return;
    }
    searchTimer = window.setTimeout(() => {
      runWorkspaceSearch(needle);
    }, 160);
  }

  function bindWorkspaceSearchDialog(dialog) {
    if (!dialog || !dialog.fields_dict || !dialog.fields_dict.search_html) return;
    const $root = dialog.fields_dict.search_html.$wrapper;
    $root.html(`
      <div class="erpw-sales-console-search-shell">
        <div class="erpw-sales-console-search-bar">
          <span class="erpw-sales-console-search-bar-icon" aria-hidden="true">${iconMarkup("search")}</span>
          <input
            type="text"
            class="erpw-sales-console-search-input"
            data-erpw-sales-search-input
            placeholder="Search customers, items, quotations, or sales orders"
            autocomplete="off"
          />
          <span class="erpw-sales-console-sidebar-utility-shortcut">${escapeHtml(shortcutLabel())}</span>
        </div>
        <div class="erpw-sales-console-search-status" data-erpw-sales-search-status hidden></div>
        <div class="erpw-sales-console-search-results" data-erpw-sales-search-results hidden></div>
      </div>
    `);

    const $input = $root.find("[data-erpw-sales-search-input]");
    $input.on("input", function () {
      scheduleWorkspaceSearch(this.value);
    });
    $input.on("keydown", function (event) {
      if (event.key === "ArrowDown") {
        event.preventDefault();
        setWorkspaceSearchActive(searchActiveIndex + 1);
        return;
      }
      if (event.key === "ArrowUp") {
        event.preventDefault();
        setWorkspaceSearchActive(searchActiveIndex - 1);
        return;
      }
      if (event.key === "Enter") {
        event.preventDefault();
        if (searchResults.length) {
          chooseWorkspaceSearchResult(searchActiveIndex >= 0 ? searchActiveIndex : 0);
        } else {
          runWorkspaceSearch(this.value);
        }
        return;
      }
      if (event.key === "Escape") {
        event.preventDefault();
        dialog.hide();
      }
    });
  }

  function ensureWorkspaceSearchDialog() {
    if (searchDialog) return searchDialog;
    searchDialog = new frappe.ui.Dialog({
      title: __("Sales Console Search"),
      size: "large",
      fields: [
        {
          fieldtype: "HTML",
          fieldname: "search_html",
        },
      ],
    });
    searchDialog.$wrapper.addClass("erpw-sales-console-search-dialog");
    bindWorkspaceSearchDialog(searchDialog);
    searchDialog.$wrapper.on("hidden.bs.modal", () => {
      resetWorkspaceSearch();
    });
    return searchDialog;
  }

  function openWorkspaceSearch(prefill) {
    const route = getRoute();
    if (!isManagedRoute(route)) return;
    const dialog = ensureWorkspaceSearchDialog();
    dialog.show();
    const elements = currentSearchElements();
    if (!elements) return;
    const value = String(prefill != null ? prefill : elements.$input.val() || "").trim();
    elements.$input.val(value);
    resetWorkspaceSearch();
    window.setTimeout(() => {
      elements.$input.trigger("focus").trigger("select");
      if (value.length >= 2) {
        scheduleWorkspaceSearch(value);
      }
    }, 30);
  }

  function primePayload(payload) {
    if (!payload || !payload.sidebar) return false;
    cachedContext = {
      context: payload.context || {},
      scope: payload.scope || {},
      ui_profile: payload.ui_profile || {},
      sidebar: payload.sidebar || {},
      fetched_at: payload.fetched_at || null,
    };
    return true;
  }

  function loadSidebarContext() {
    if (cachedContext && cachedContext.sidebar) {
      return Promise.resolve(cachedContext);
    }

    if (contextPromise) return contextPromise;

    contextPromise = Promise.resolve(frappe.call({
      method: SIDEBAR_METHOD,
    })).then((response) => {
      const payload = response && response.message ? response.message : {};
      cachedContext = payload && payload.sidebar ? payload : fallbackContext();
      return cachedContext;
    }).catch(() => {
      cachedContext = fallbackContext();
      return cachedContext;
    }).then((payload) => {
      contextPromise = null;
      return payload;
    });

    return contextPromise;
  }

  function buildSignature(sidebar, activeKey) {
    return JSON.stringify({
      activeKey: activeKey || "",
      mode_label: sidebar && sidebar.mode_label,
      scope_label: sidebar && sidebar.scope_label,
      sections: sidebar && sidebar.sections,
    });
  }

  function renderSidebar(contextPayload, activeKey) {
    ensureStyles();
    const wrapper = ensureSidebarWrapper();
    if (!wrapper) return false;

    const sidebar = contextPayload && contextPayload.sidebar ? contextPayload.sidebar : fallbackContext().sidebar;
    const sections = Array.isArray(sidebar.sections) ? sidebar.sections.filter(Boolean) : [];
    if (!sections.length) {
      removeSidebar();
      return false;
    }

    const signature = buildSignature(sidebar, activeKey);
    if (wrapper.getAttribute("data-erpw-sidebar-signature") === signature) {
      return true;
    }

    const utilitiesMarkup = `
      <div class="erpw-sales-console-sidebar-utilities">
        <button type="button" class="erpw-sales-console-sidebar-utility" data-erpw-sales-notifications-open="1">
          <span class="erpw-sales-console-sidebar-utility-icon" aria-hidden="true">${iconMarkup("notification")}</span>
          <span class="erpw-sales-console-sidebar-utility-copy">
            <span class="erpw-sales-console-sidebar-utility-title">Notification</span>
          </span>
        </button>
        <button type="button" class="erpw-sales-console-sidebar-utility" data-erpw-sales-search-open="1">
          <span class="erpw-sales-console-sidebar-utility-icon" aria-hidden="true">${iconMarkup("search")}</span>
          <span class="erpw-sales-console-sidebar-utility-copy">
            <span class="erpw-sales-console-sidebar-utility-title">Search</span>
          </span>
          <span class="erpw-sales-console-sidebar-utility-shortcut">${escapeHtml(shortcutLabel())}</span>
        </button>
      </div>
    `;

    const itemIndex = new Map();
    const showSectionLabels = sections.length > 1;
    let currentIndex = 0;
    const sectionsMarkup = sections.map((section) => {
      const items = Array.isArray(section.items) ? section.items.filter(Boolean) : [];
      if (!items.length) return "";

      const itemsMarkup = items.map((item) => {
        currentIndex += 1;
        const indexKey = String(currentIndex);
        itemIndex.set(indexKey, item);
        const activeClass = item.key === activeKey ? " is-active" : "";
        return `
          <div class="erpw-sales-console-sidebar-item">
            <div class="standard-sidebar-item">
              <button type="button" class="item-anchor erpw-sales-console-sidebar-link${activeClass}" data-erpw-sidebar-index="${escapeHtml(indexKey)}">
                <span class="erpw-sales-console-sidebar-icon" aria-hidden="true">${iconMarkup(item.icon || "square")}</span>
                <span class="erpw-sales-console-sidebar-copy">
                  <span class="erpw-sales-console-sidebar-text">${escapeHtml(item.label || "Sales Console")}</span>
                </span>
              </button>
            </div>
          </div>
        `;
      }).join("");

      return `
        <section class="erpw-sales-console-sidebar-section" data-erpw-sidebar-section="${escapeHtml(section.key || "")}">
          ${showSectionLabels ? `<div class="erpw-sales-console-sidebar-section-label">${escapeHtml(section.label || "Section")}</div>` : ""}
          ${itemsMarkup}
        </section>
      `;
    }).join("");

    wrapper.innerHTML = `
      <div class="erpw-sales-console-sidebar-shell">
        ${utilitiesMarkup}
        ${sectionsMarkup}
      </div>
    `;
    wrapper._erpwSidebarItems = itemIndex;
    wrapper.setAttribute("data-erpw-sidebar-signature", signature);

    wrapper.querySelectorAll("[data-erpw-sales-search-open]").forEach((element) => {
      element.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        openWorkspaceSearch("");
      });
    });
    wrapper.querySelectorAll("[data-erpw-sales-notifications-open]").forEach((element) => {
      element.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        openNativeNotifications();
      });
    });
    wrapper.querySelectorAll("[data-erpw-sidebar-index]").forEach((element) => {
      element.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        const item = wrapper._erpwSidebarItems && wrapper._erpwSidebarItems.get(element.getAttribute("data-erpw-sidebar-index"));
        executeTarget(item && item.target ? item.target : null);
      });
    });

    return true;
  }

  function syncSidebarNow() {
    const route = getRoute();
    if (!isManagedRoute(route)) {
      clearSidebarArtifacts(route);
      return Promise.resolve(false);
    }

    setManagedBodyState(true);
    setManagedSidebarHeader(true);

    if (!isSalesConsoleHomeRoute(route)) {
      removeGuideItem();
    }

    const activeKey = resolveActiveKey(route);
    renderSidebar(cachedContext && cachedContext.sidebar ? cachedContext : fallbackContext(), activeKey);
    return loadSidebarContext().then((contextPayload) => renderSidebar(contextPayload, activeKey));
  }

  function scheduleSync(delayMs) {
    if (syncTimer) {
      window.clearTimeout(syncTimer);
    }

    let attempts = 0;
    const tick = () => {
      const route = getRoute();
      if (!isManagedRoute(route)) {
        clearSidebarArtifacts(route);
        return;
      }

      if (!ensureManagedSidebarHost().host && attempts < 12) {
        attempts += 1;
        syncTimer = window.setTimeout(tick, 280);
        return;
      }

      syncTimer = null;
      syncSidebarNow();
    };

    syncTimer = window.setTimeout(tick, Number.isFinite(delayMs) ? delayMs : 0);
  }

  function scheduleSyncSeries() {
    [0, 40, 90, 160, 260, 420, 720].forEach((delay) => {
      window.setTimeout(() => {
        if (isManagedRoute(getRoute())) {
          syncSidebarNow();
        }
      }, delay);
    });
  }

  function scheduleMutationSync() {
    if (mutationSyncTimer) return;
    mutationSyncTimer = window.setTimeout(() => {
      mutationSyncTimer = null;
      scheduleSync(0);
    }, 60);
  }

  function bindSidebarMutationObserver() {
    if (sidebarMutationObserver || typeof MutationObserver !== "function" || !document.body) return;
    sidebarMutationObserver = new MutationObserver(() => {
      const route = getRoute();
      if (!isManagedRoute(route)) return;
      if (!document.querySelector("[data-erpw-sales-console-nav='1']") || hasVisibleNativeSidebarArtifacts()) {
        scheduleMutationSync();
      }
    });
    sidebarMutationObserver.observe(document.body, { childList: true, subtree: true });
  }

  function handleWorkspaceSearchShortcut(event) {
    const route = getRoute();
    if (!isManagedRoute(route)) return;
    const isSearchShortcut = (event.ctrlKey || event.metaKey) && !event.shiftKey && !event.altKey && String(event.key || "").toLowerCase() === "k";
    if (!isSearchShortcut) return;
    event.preventDefault();
    event.stopPropagation();
    if (typeof event.stopImmediatePropagation === "function") {
      event.stopImmediatePropagation();
    }
    openWorkspaceSearch("");
  }

  function bindListeners() {
    if (listenersBound) return;
    listenersBound = true;
    if (frappe.router && typeof frappe.router.on === "function") {
      frappe.router.on("change", () => {
        frappe.after_ajax(() => scheduleSyncSeries());
      });
    }
    window.addEventListener("hashchange", () => scheduleSyncSeries());
    window.addEventListener("popstate", () => scheduleSyncSeries());
    document.addEventListener("readystatechange", () => scheduleSync(10));
    if (document.body) {
      bindSidebarMutationObserver();
    } else {
      document.addEventListener("DOMContentLoaded", bindSidebarMutationObserver, { once: true });
    }
    window.addEventListener("keydown", handleWorkspaceSearchShortcut, true);
    document.addEventListener("keydown", handleWorkspaceSearchShortcut, true);
  }

  bindListeners();
  scheduleSyncSeries();

  root.erpWorkspaceConsoleSidebar = Object.assign(sidebarRuntime, {
    executeTarget,
    primePayload,
    refresh() {
      scheduleSyncSeries();
    },
    syncSidebarNow,
  });
})();
