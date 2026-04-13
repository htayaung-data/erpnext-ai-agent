(function () {
  let footerPatched = false;
  let sidebarPatched = false;
  let routeChromeBound = false;
  let salesOrderSidebarCollapsed = false;
  let priorSidebarExpandedState = null;

  function matchesChildExecutionPath(slug) {
    const path = window.location.pathname || "";
    return new RegExp(`^/desk/${slug}/[^/]+(?:/|$)`).test(path);
  }

  function isSalesOrderRoute() {
    return matchesChildExecutionPath("sales-order");
  }

  function isQuotationRoute() {
    return matchesChildExecutionPath("quotation");
  }

  function isDeliveryNoteRoute() {
    return matchesChildExecutionPath("delivery-note");
  }

  function isSalesInvoiceRoute() {
    return matchesChildExecutionPath("sales-invoice");
  }

  function isChildExecutionRoute() {
    return isSalesOrderRoute() || isQuotationRoute() || isDeliveryNoteRoute() || isSalesInvoiceRoute();
  }

  function isChildExecutionDocType(doctype) {
    return doctype === "Sales Order" || doctype === "Quotation" || doctype === "Delivery Note" || doctype === "Sales Invoice";
  }

  function applySalesOrderRouteChrome() {
    const isSalesOrder = isChildExecutionRoute();
    if (!isSalesOrder) {
      lastChildExecutionScrollPath = null;
    }
    const root = document.documentElement;
    const body = document.body;
    const sidebar = document.querySelector(".body-sidebar");
    const sidebarContainer = document.querySelector(".body-sidebar-container");

    [root, body, sidebar, sidebarContainer].forEach((node) => {
      if (!node) return;
      node.classList.toggle("erpw-route-sales-order-ready", isSalesOrder);
      node.classList.remove("erpw-route-sales-order-prep");
      node.classList.remove("erpw-so-left-sidebar-compact");
    });

    salesOrderSidebarCollapsed = false;
    priorSidebarExpandedState = null;
  }

  const childPageBootstrapRegistry = {};
  let childPageBootstrapWatcherToken = 0;
  let lastChildExecutionScrollPath = null;
  let childExecutionScrollToken = 0;

  function forceChildExecutionHeaderTop() {
    try {
      const mainSection = document.querySelector(".main-section");
      const layoutMainSection = document.querySelector(".layout-main-section");
      const scrollingElement = document.scrollingElement || document.documentElement || document.body;

      if (mainSection) {
        mainSection.scrollTop = 0;
      }
      if (layoutMainSection) {
        layoutMainSection.scrollTop = 0;
      }
      if (scrollingElement) {
        scrollingElement.scrollTop = 0;
      }
      if (document.body) {
        document.body.scrollTop = 0;
      }
      if (document.documentElement) {
        document.documentElement.scrollTop = 0;
      }
      window.scrollTo(0, 0);
    } catch (error) {
      // Ignore scroll reset failures and keep route flow usable.
    }
  }

  function scrollChildExecutionRouteTop() {
    const path = window.location.pathname || "";
    if (!path || lastChildExecutionScrollPath === path) return;
    lastChildExecutionScrollPath = path;
    const scrollToken = ++childExecutionScrollToken;
    [0, 90, 220, 460, 900].forEach((delay) => {
      window.setTimeout(() => {
        if (scrollToken !== childExecutionScrollToken) return;
        if (!isChildExecutionRoute()) return;
        if ((window.location.pathname || "") !== path) return;
        forceChildExecutionHeaderTop();
      }, delay);
    });
  }

  function runActiveChildPageBootstrap() {
    const frm = window.cur_frm;
    if (!frm || !frm.doctype || !isChildExecutionDocType(frm.doctype)) {
      return false;
    }

    const bootstrap = childPageBootstrapRegistry[frm.doctype];
    if (typeof bootstrap !== "function") {
      return false;
    }

    try {
      const booted = bootstrap() === true;
      if (booted) {
        scrollChildExecutionRouteTop();
      }
      return booted;
    } catch (error) {
      return false;
    }
  }

  function ensureActiveChildPageBootstrap(options) {
    const settings = Object.assign({
      maxAttempts: 18,
    }, options || {});

    const watcherToken = ++childPageBootstrapWatcherToken;
    let attempts = 0;

    const tick = () => {
      if (watcherToken !== childPageBootstrapWatcherToken) return;
      if (!isChildExecutionRoute()) return;
      if (runActiveChildPageBootstrap()) return;

      attempts += 1;
      if (attempts >= settings.maxAttempts) return;

      const delay = attempts < 6 ? 120 : attempts < 12 ? 260 : 420;
      window.setTimeout(tick, delay);
    };

    tick();
  }

  function scheduleActiveChildPageBootstrap() {
    [0, 140, 360, 720].forEach((delay) => {
      window.setTimeout(runActiveChildPageBootstrap, delay);
    });
    ensureActiveChildPageBootstrap({ maxAttempts: 20 });
  }

  function bindRouteChrome() {
    if (routeChromeBound) return;
    routeChromeBound = true;

    const syncSoon = () => {
      window.requestAnimationFrame(() => {
        applySalesOrderRouteChrome();
        ensureActiveChildPageBootstrap({ maxAttempts: 20 });
      });
    };

    const originalPushState = history.pushState;
    const originalReplaceState = history.replaceState;

    history.pushState = function () {
      const result = originalPushState.apply(this, arguments);
      syncSoon();
      return result;
    };

    history.replaceState = function () {
      const result = originalReplaceState.apply(this, arguments);
      syncSoon();
      return result;
    };

    window.addEventListener("popstate", syncSoon);
    window.addEventListener("hashchange", syncSoon);
    window.addEventListener("resize", syncSoon);
    document.addEventListener("readystatechange", syncSoon);

    syncSoon();
    setTimeout(syncSoon, 0);
    setTimeout(syncSoon, 120);
    setTimeout(syncSoon, 320);
  }

  function ensureSupportHeadMarkup($wrapper) {
    if (!$wrapper || !$wrapper.length) return;

    let $head = $wrapper.find(".erpw-so-support-head").first();
    if (!$head.length) {
      $head = $(`
        <div class="erpw-so-support-head">
          <div class="erpw-so-support-copy">
            <div class="erpw-so-support-title">Activity & Comments</div>
            <div class="erpw-so-support-note">Comments stay available. Expand activity only when you need deeper audit history.</div>
          </div>
          <button type="button" class="erpw-so-support-toggle" aria-expanded="false">
            <span class="erpw-so-support-toggle-text">Show Full Activity</span>
            <span class="erpw-so-support-toggle-icon" aria-hidden="true"></span>
          </button>
        </div>
      `);
      $wrapper.prepend($head);
      return;
    }

    if (!$head.find(".erpw-so-support-copy").length) {
      $head.prepend(`
        <div class="erpw-so-support-copy">
          <div class="erpw-so-support-title">Activity & Comments</div>
          <div class="erpw-so-support-note">Comments stay available. Expand activity only when you need deeper audit history.</div>
        </div>
      `);
    }

    if (!$head.find(".erpw-so-support-toggle").length) {
      $head.append(`
        <button type="button" class="erpw-so-support-toggle" aria-expanded="false">
          <span class="erpw-so-support-toggle-text">Show Full Activity</span>
          <span class="erpw-so-support-toggle-icon" aria-hidden="true"></span>
        </button>
      `);
    }
  }

  function patchFooter() {
    if (
      footerPatched ||
      !window.frappe ||
      !frappe.ui ||
      !frappe.ui.form ||
      !frappe.ui.form.Footer
    ) {
      return;
    }

    const proto = frappe.ui.form.Footer.prototype;
    if (!proto || typeof proto.make !== "function") return;

    const originalMake = proto.make;
    proto.make = function () {
      const result = originalMake.apply(this, arguments);
      if (this.frm && isChildExecutionDocType(this.frm.doctype) && this.wrapper) {
        this.wrapper.addClass("erpw-so-support-shell");
        this.wrapper.find(".comment-box").addClass("erpw-so-comment-block");
        this.wrapper.find(".timeline, .new-timeline").addClass("erpw-so-timeline-block");
        ensureSupportHeadMarkup(this.wrapper);
      }
      return result;
    };

    footerPatched = true;
  }

  function patchSidebar() {
    if (
      sidebarPatched ||
      !window.frappe ||
      !frappe.ui ||
      !frappe.ui.form ||
      !frappe.ui.form.Sidebar
    ) {
      return;
    }

    const proto = frappe.ui.form.Sidebar.prototype;
    if (!proto || typeof proto.make !== "function") return;

    const originalMake = proto.make;
    proto.make = function () {
      const result = originalMake.apply(this, arguments);
      if (this.frm && isChildExecutionDocType(this.frm.doctype) && this.sidebar) {
        this.sidebar.addClass("erpw-so-sidebar-shell");
        this.sidebar.find(".sidebar-section.text-muted.border-top.pt-3").addClass("erpw-so-sidebar-meta-hidden").hide();
      }
      return result;
    };

    sidebarPatched = true;
  }

  window.erpWorkspaceUiBoot = Object.assign(window.erpWorkspaceUiBoot || {}, {
    registerChildPageBootstrap(doctype, bootstrap) {
      if (!doctype || typeof bootstrap !== "function") return;
      childPageBootstrapRegistry[doctype] = bootstrap;
      scheduleActiveChildPageBootstrap();
    },
    runActiveChildPageBootstrap,
    ensureActiveChildPageBootstrap,
    scheduleActiveChildPageBootstrap,
    setSalesOrderPrep() {
      // First-paint prep takeover has been intentionally disabled.
      // Sales Order enhancement should never be allowed to blank the route.
    },
  });

  patchFooter();
  patchSidebar();
  bindRouteChrome();
  setTimeout(patchFooter, 0);
  setTimeout(patchFooter, 80);
  setTimeout(patchFooter, 220);
  setTimeout(patchSidebar, 0);
  setTimeout(patchSidebar, 80);
  setTimeout(patchSidebar, 220);
  setTimeout(bindRouteChrome, 80);
  setTimeout(bindRouteChrome, 220);
})();
