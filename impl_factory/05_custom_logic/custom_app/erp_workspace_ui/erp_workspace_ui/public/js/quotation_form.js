(function () {
  const METHOD = "erp_workspace_ui.api.get_quotation_page_context";
  const childPageRuntime = window.erpWorkspaceUiChildPage || {};
  const childPageHelpers = childPageRuntime.helpers || {};
  const childPageShell = childPageRuntime.shell || {};
  const childPageLifecycle = childPageRuntime.runtime || {};
  const childPageConnections = childPageRuntime.connections || {};
  const childPageSections = childPageRuntime.sections || {};
  const childPageTerms = childPageRuntime.terms || {};
  const childPageSummaries = childPageRuntime.summaries || {};
  const childPageDetails = childPageRuntime.details || {};
  const childPageSupport = childPageRuntime.support || {};
  const childPageSidebar = childPageRuntime.sidebar || {};
  const childPageShellContent = childPageRuntime.shellContent || {};

  // Keep a local fallback so the form stays usable even if the shared asset is stale or delayed.
  const formatMoney = childPageHelpers.formatMoney || function (value, currency) {
    if (value == null) return "--";
    try {
      return format_currency(value, currency || frappe.defaults.get_default("currency"));
    } catch (e) {
      return `${currency || ""} ${value}`;
    }
  };

  const escapeHtml = childPageHelpers.escapeHtml || function (value) {
    return frappe.utils.escape_html(value == null ? "" : String(value));
  };

  const routeToDoc = childPageHelpers.routeToDoc || function (doctype, name) {
    if (!doctype || !name) return;
    frappe.set_route("Form", doctype, name);
  };

  const routeToList = childPageHelpers.routeToList || function (doctype, filters) {
    frappe.route_options = filters && Object.keys(filters).length ? filters : null;
    frappe.set_route("List", doctype);
  };

  const hasVisibleControls = childPageSections.hasVisibleControls || function ($container, options) {
    if (!$container || !$container.length) return false;

    const settings = Object.assign({
      directChildren: false,
      selector: ".frappe-control",
    }, options || {});

    const $controls = settings.directChildren
      ? $container.children(settings.selector)
      : $container.find(settings.selector);

    return $controls.toArray().some((element) => {
      const $control = $(element);
      if ($control.hasClass("hide-control") || $control.hasClass("hidden")) return false;
      if ($control.css("display") === "none") return false;
      const inlineStyle = String($control.attr("style") || "").toLowerCase();
      if (inlineStyle.includes("display: none")) return false;
      return true;
    });
  };

  const arrangeSharedAddressFieldGrid = childPageSections.arrangeAddressFieldGrid || function () {
    return $();
  };
  const ensureSharedDetailWorkspace = childPageSections.ensureDetailWorkspace || function () {
    return $();
  };
  const coreAddressFieldOrder = childPageSections.coreAddressFieldOrder || [
    "contact_person",
    "contact_mobile",
    "contact_email",
    "territory",
    "customer_address",
    "address_display",
  ];
  const coreAddressPlaceholders = childPageSections.coreAddressPlaceholders || {
    contact_person: "",
    contact_mobile: "",
    customer_address: "",
    address_display: "",
    contact_email: "",
    territory: "",
  };
  const relocateSharedFieldIntoSectionBody = childPageSections.relocateFieldIntoSectionBody || function () {};
  const restoreSharedRelocatedFieldPlacements = childPageSections.restoreRelocatedFieldPlacements || function () {};

  function getObservability() {
    return (window.erpWorkspaceUiChildPage && window.erpWorkspaceUiChildPage.observability) || {};
  }

  function markFeatureStatus(frm, feature, status, meta) {
    const observability = getObservability();
    if (typeof observability.markFeatureStatus === "function") {
      return observability.markFeatureStatus(frm, feature, status, meta);
    }
    return false;
  }

  function markFeatureReady(frm, feature, meta) {
    const observability = getObservability();
    if (typeof observability.markFeatureReady === "function") {
      return observability.markFeatureReady(frm, feature, meta);
    }
    return false;
  }

  function markFeatureMissing(frm, feature, meta) {
    const observability = getObservability();
    if (typeof observability.markFeatureMissing === "function") {
      return observability.markFeatureMissing(frm, feature, meta);
    }
    return false;
  }

  function getShellOptions() {
    return {
      shellClasses: ["erpws-order-shell", "erpwq-quotation-shell"],
    };
  }

  const getFormTaskState = childPageHelpers.getFormTaskState || function (frm) {
    if (!frm) return { timers: {} };
    if (!frm.__erpwTaskState) {
      frm.__erpwTaskState = { timers: {} };
    }
    return frm.__erpwTaskState;
  };

  const scheduleFormTask = childPageHelpers.scheduleFormTask || function (frm, key, delay, fn) {
    if (!frm || typeof fn !== "function") return;
    const state = getFormTaskState(frm);
    if (state.timers[key]) {
      clearTimeout(state.timers[key]);
    }
    state.timers[key] = setTimeout(() => {
      delete state.timers[key];
      if (!frm.doc) return;
      fn();
    }, Math.max(0, Number(delay || 0)));
  };

  const scheduleEnhancePasses = childPageLifecycle.scheduleEnhancePasses || function (frm, run, options) {
    if (typeof run !== "function") return;
    scheduleFormTask(frm, options && options.fastKey ? options.fastKey : "enhance_form_body_fast", options && options.fastDelay != null ? options.fastDelay : 0, () => run(frm));
    scheduleFormTask(frm, options && options.lateKey ? options.lateKey : "enhance_form_body_late", options && options.lateDelay != null ? options.lateDelay : 180, () => run(frm));
  };

  const scheduleRetryPair = childPageLifecycle.scheduleRetryPair || function (frm, options) {
    if (!options || typeof options.run !== "function") return;
    if (options.fastKey) {
      scheduleFormTask(frm, options.fastKey, options.fastDelay != null ? options.fastDelay : 420, () => options.run(frm));
    }
    if (options.lateKey) {
      scheduleFormTask(frm, options.lateKey, options.lateDelay != null ? options.lateDelay : 980, () => options.run(frm));
    }
  };

  const runRetriedEnhancers = childPageLifecycle.runRetriedEnhancers || function (frm, steps) {
    if (!Array.isArray(steps)) return;
    steps.forEach((step) => {
      if (!step || typeof step.run !== "function") return;
      if (!step.run(frm)) {
        scheduleRetryPair(frm, step);
      }
    });
  };

  const bindRuntimeTabEnhancers = childPageLifecycle.bindTabEnhancers || function (frm, options) {
    if (!frm || !options || typeof options.run !== "function") return;
    const $root = $(frm.page && frm.page.main ? frm.page.main : frm.$wrapper || []);
    if (!$root.length) return;

    const $links = $root.find(".form-tabs-list .nav-link, .form-tabs .nav-link");
    if (!$links.length) return;

    const namespace = options.namespace || ".erpwChildPageTabs";
    $links.off(namespace).on(`click${namespace}`, function () {
      scheduleEnhancePasses(frm, options.run, options);
    });
  };

  function scheduleFormEnhance(frm) {
    scheduleEnhancePasses(frm, () => enhanceFormBody(frm), {
      fastKey: "enhance_form_body_fast",
      lateKey: "enhance_form_body_late",
      fastDelay: 0,
      lateDelay: 220,
    });
  }

  function getContextSignature(frm) {
    const doc = (frm && frm.doc) || {};
    return [
      doc.name || "",
      doc.modified || "",
      doc.docstatus == null ? "" : String(doc.docstatus),
      doc.status || "",
      doc.workflow_state || "",
      doc.party_name || "",
      doc.customer_name || "",
      doc.transaction_date || "",
      doc.valid_till || "",
      doc.currency || "",
      doc.grand_total == null ? "" : String(doc.grand_total),
      doc.opportunity || "",
    ].join("|");
  }

  const getLayoutWrapper = childPageHelpers.getLayoutWrapper || function (frm) {
    return $(frm && frm.layout && frm.layout.wrapper ? frm.layout.wrapper : []);
  };

  const getFormRoot = childPageHelpers.getFormRoot || function (frm) {
    const $layout = getLayoutWrapper(frm);
    if ($layout.length) {
      const $mainSection = $layout.closest(".layout-main-section");
      if ($mainSection.length) return $mainSection;

      const $formPage = $layout.closest(".form-page");
      if ($formPage.length) return $formPage;

      const $parent = $layout.parent();
      if ($parent.length) return $parent;

      return $layout;
    }

    const $wrapper = $(frm && frm.wrapper ? frm.wrapper : frm && frm.$wrapper ? frm.$wrapper : []);
    if ($wrapper.length) {
      const $mainSection = $wrapper.closest(".layout-main-section");
      if ($mainSection.length) return $mainSection;

      const $formPage = $wrapper.closest(".form-page");
      if ($formPage.length) return $formPage;

      return $wrapper;
    }

    return $(frm && frm.page && frm.page.main ? frm.page.main : []);
  };

  const getNativeLayoutAnchor = childPageHelpers.getNativeLayoutAnchor || function (frm) {
    const $layout = getLayoutWrapper(frm);
    if ($layout.length) return $layout;

    const $root = getFormRoot(frm);
    if (!$root.length) return $();

    return $root.find(".std-form-layout").first().length
      ? $root.find(".std-form-layout").first()
      : $root.find(".form-layout").first().length
        ? $root.find(".form-layout").first()
      : $root.find(".layout-main-section").first().length
        ? $root.find(".layout-main-section").first()
        : $root.find(".form-page").first().length
          ? $root.find(".form-page").first()
          : $();
  };

  function getShell(frm) {
    if (typeof childPageShell.ensureShell === "function") {
      return childPageShell.ensureShell(frm, getShellOptions());
    }

    const $root = getFormRoot(frm);
    const $mount = getNativeLayoutAnchor(frm);

    let $shell = $mount.length
      ? $mount.siblings(".erpw-child-shell.erpwq-quotation-shell").first()
      : $root.children(".erpw-child-shell.erpwq-quotation-shell").first();
    if (!$shell.length) {
      $shell = $('<div class="erpw-child-shell erpws-order-shell erpwq-quotation-shell"></div>');
      if ($mount.length) {
        $shell.insertBefore($mount);
      } else {
        $root.prepend($shell);
      }
    } else if (
      $mount.length &&
      ($shell.parent().get(0) !== $mount.parent().get(0) || $shell.next().get(0) !== $mount.get(0))
    ) {
      $shell.detach();
      $shell.insertBefore($mount);
    }
    return $shell;
  }

  const getShellSkeletonMarkup = childPageShell.getShellSkeletonMarkup || function () {
    return `
      <section class="erpw-child-card erpw-child-summary erpw-so-shell-skeleton erpw-so-shell-skeleton-summary">
        <div class="erpw-so-shell-skeleton-copy">
          <div class="erpw-so-shell-skeleton-kicker"></div>
          <div class="erpw-so-shell-skeleton-title"></div>
          <div class="erpw-so-shell-skeleton-subtitle"></div>
        </div>
        <div class="erpw-so-shell-skeleton-facts">
          <div class="erpw-so-shell-skeleton-fact"></div>
          <div class="erpw-so-shell-skeleton-fact"></div>
          <div class="erpw-so-shell-skeleton-fact"></div>
        </div>
      </section>
      <section class="erpw-child-card erpw-so-shell-skeleton erpw-so-shell-skeleton-actions">
        <div class="erpw-so-shell-skeleton-action"></div>
        <div class="erpw-so-shell-skeleton-action"></div>
        <div class="erpw-so-shell-skeleton-action"></div>
      </section>
      <section class="erpw-child-card erpw-so-shell-skeleton erpw-so-shell-skeleton-guidance">
        <div class="erpw-so-shell-skeleton-guidance-card"></div>
        <div class="erpw-so-shell-skeleton-guidance-card"></div>
      </section>
    `;
  };

  function showShellSkeleton(frm) {
    if (typeof childPageShell.showShellSkeleton === "function") {
      return childPageShell.showShellSkeleton(frm, getShellOptions());
    }

    const $shell = getShell(frm);
    if (!$shell.children(".erpw-so-shell-skeleton").length || frm.__erpwContextRenderedName !== (frm.doc && frm.doc.name)) {
      $shell.html(getShellSkeletonMarkup());
    }
    return $shell;
  }

  function prepareFormShell(frm) {
    if (!frm) {
      markFeatureMissing(frm, "shell_prepare", { reason: "no_form" });
      return;
    }
    markFeatureStatus(frm, "shell_prepare", "loading", {
      loadingMessage: "Loading quotation execution context...",
    });
    const prepareShell = childPageShell.prepareShell || showShellSkeleton;
    prepareShell(frm, getShellOptions());
    markFeatureReady(frm, "shell_prepare", {
      loadingMessage: "Loading quotation execution context...",
    });
  }

  function getFieldWrapper(frm, fieldname) {
    const field = frm.fields_dict && frm.fields_dict[fieldname];
    if (!field) return null;
    const $wrapper = field.$wrapper && field.$wrapper.length ? field.$wrapper : $(field.wrapper || []);
    return $wrapper.length ? $wrapper : null;
  }

  function getSectionForField(frm, fieldname) {
    const $wrapper = getFieldWrapper(frm, fieldname);
    if (!$wrapper || !$wrapper.length) return null;
    const $section = $wrapper.closest(".form-section");
    return $section.length ? $section : null;
  }

  function getTabByFieldname(frm, fieldname) {
    const $root = $(frm.page && frm.page.main ? frm.page.main : frm.$wrapper || []);
    if (!$root.length) return $();

    const $tabLink = $root.find(`.form-tabs .nav-link[data-fieldname="${fieldname}"], .form-tabs-list .nav-link[data-fieldname="${fieldname}"]`).first();
    if (!$tabLink.length) return $();

    const tabId = $tabLink.attr("aria-controls");
    if (!tabId) return $();

    const $tab = $root.find(`#${tabId}`).first();
    return $tab.length ? $tab : $();
  }

  function toggleField(frm, fieldname, visible) {
    if (!frm.fields_dict || !frm.fields_dict[fieldname]) return;
    frm.toggle_display(fieldname, !!visible);
  }

  function toggleSection(frm, fieldname, visible) {
    const $section = getSectionForField(frm, fieldname);
    if ($section) {
      $section.toggle(!!visible);
    }
  }

  function markSection(frm, fieldname, className) {
    const $section = getSectionForField(frm, fieldname);
    if ($section) {
      $section.addClass(className);
    }
  }

  function setManagedSectionVisibility($section, visible, className) {
    if (!$section || !$section.length) return;

    const hiddenClass = className || "erpw-child-managed-hidden-source";
    $section.toggleClass(hiddenClass, !visible);
    $section.toggle(!!visible);
  }

  function hasMeaningfulValue(value) {
    if (value == null) return false;
    if (Array.isArray(value)) return value.length > 0;
    if (typeof value === "number") return value !== 0;
    if (typeof value === "boolean") return value;
    const normalized = String(value).trim();
    return normalized !== "" && normalized !== "0";
  }

  function usesCompanyCurrencyOnly(frm) {
    const docCurrency = frm.doc.currency || frappe.defaults.get_default("currency");
    const companyCurrency = frm.doc.company_currency || docCurrency;
    return !docCurrency || !companyCurrency || docCurrency === companyCurrency;
  }

  function formatCountTitle(singular, plural, count) {
    return `${count === 1 ? singular : plural} (${count})`;
  }

  function formatDateLabel(value) {
    if (!value) return "--";
    try {
      return frappe.datetime.str_to_user(value);
    } catch (e) {
      return String(value);
    }
  }

  function formatDaysToExpiry(days) {
    const numeric = Number(days);
    if (!Number.isFinite(numeric)) return "No validity set";
    if (numeric < 0) return `Expired ${Math.abs(numeric)} day${Math.abs(numeric) === 1 ? "" : "s"} ago`;
    if (numeric === 0) return "Expires today";
    if (numeric === 1) return "1 day left";
    return `${numeric} days left`;
  }

  function getReferenceNames(frm, data) {
    const summary = data.summary || {};
    const linked = data.linked_documents || {};
    const party = linked.party || {};
    return [
      frm.doc.name,
      summary.customer_label,
      party.name,
      linked.opportunity && linked.opportunity.name,
    ]
      .concat((linked.sales_orders || []).map((row) => row.name))
      .concat((linked.deliveries || []).map((row) => row.name))
      .concat((linked.invoices || []).map((row) => row.name))
      .filter(Boolean);
  }

  function createFollowUpTask(frm, data) {
    const summary = data.summary || {};
    frappe.new_doc("ToDo", {
      description: `Follow up ${summary.name || frm.doc.name || "Quotation"} for ${summary.customer_label || "customer"}`,
      reference_type: "Quotation",
      reference_name: summary.name || frm.doc.name,
      allocated_to: frm.doc.owner || frappe.session.user,
      date: summary.valid_till || frappe.datetime.get_today(),
    });
  }

  function draftContext(frm) {
    const owner = frm.doc.owner || frappe.session.user;
    const ownerDisplay = frappe.user && typeof frappe.user.full_name === "function" ? frappe.user.full_name(owner) : owner;

    return {
      summary: {
        name: frm.doc.name || "New Quotation",
        customer_label: frm.doc.customer_name || frm.doc.party_name || "Customer not selected yet",
        party_doctype: frm.doc.quotation_to || "Customer",
        party_name: frm.doc.party_name || null,
        status: frm.doc.docstatus === 0 ? "Draft" : (frm.doc.status || "Draft"),
        workflow_state: frm.doc.workflow_state || "Draft",
        owner,
        owner_display: ownerDisplay,
        transaction_date: frm.doc.transaction_date || frappe.datetime.get_today(),
        valid_till: frm.doc.valid_till || null,
        days_to_expiry: null,
        validity_state: "no_valid_till",
        currency: frm.doc.currency || frappe.defaults.get_default("currency"),
        grand_total: frm.doc.grand_total || 0,
        order_type: frm.doc.order_type || "Sales",
        opportunity: frm.doc.opportunity || null,
        sales_order_count: 0,
        delivery_count: 0,
        invoice_count: 0,
      },
      linked_documents: {
        party: frm.doc.party_name ? { doctype: frm.doc.quotation_to || "Customer", name: frm.doc.party_name } : null,
        opportunity: frm.doc.opportunity ? { name: frm.doc.opportunity } : null,
        sales_orders: [],
        deliveries: [],
        invoices: [],
      },
      support: {
        latest_task: null,
        open_task_count: 0,
        approval_note: "Use the standard toolbar to save, submit, or route approval for this quotation.",
        customer_response_hint: "Clarify pricing, validity, and customer intent before giving final commercial confirmation.",
        commercial_note: "This quotation is still being prepared and has not yet entered downstream conversion.",
        next_action: "Complete customer, pricing, and validity details, then save so the commercial workspace can evaluate approval and conversion context.",
        detail_guide: "Use the detailed form sections below to refine items, pricing, terms, and validity before commercial commitment.",
      },
    };
  }

  function getPartyLink(data) {
    const linked = data.linked_documents || {};
    const summary = data.summary || {};
    if (linked.party && linked.party.doctype && linked.party.name) {
      return linked.party;
    }
    if (summary.party_doctype && summary.party_name) {
      return { doctype: summary.party_doctype, name: summary.party_name };
    }
    return null;
  }

  function getPartyLabel(doctype) {
    if (!doctype) return "Party";
    if (doctype === "Customer") return "Customer";
    if (doctype === "Lead") return "Lead";
    return doctype;
  }

  function actionIconMarkup(kind) {
    const icons = {
      sales_order: `
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M7 3.5h7l4 4v13H7zM14 3.5v4h4M10 12h5M10 15.5h5M10 19h3" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      `,
      delivery: `
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M3 7.5h10v7H3zM13 10.5h3l2 2v2h-5zM7 17.5a1.5 1.5 0 1 1-3 0a1.5 1.5 0 0 1 3 0zm11 0a1.5 1.5 0 1 1-3 0a1.5 1.5 0 0 1 3 0z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      `,
      invoice: `
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M7 3.5h7l4 4v13H7zM14 3.5v4h4M10 12h5M10 15.5h5M10 19h3" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      `,
      customer: `
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M12 12a3.5 3.5 0 1 0 0-7a3.5 3.5 0 0 0 0 7zm-6 7a6 6 0 0 1 12 0" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      `,
      follow_up: `
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M12 5v14M5 12h14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      `,
      opportunity: `
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M4 8.5h16v10H4zM9 8.5V6.7c0-.7.6-1.2 1.2-1.2h3.6c.7 0 1.2.5 1.2 1.2v1.8" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      `,
    };
    return icons[kind] || icons.sales_order;
  }

  function actionConfig(frm, data) {
    const summary = data.summary || {};
    const linked = data.linked_documents || {};
    const support = data.support || {};
    const actions = [];
    const party = getPartyLink(data);

    if (Array.isArray(linked.sales_orders) && linked.sales_orders.length) {
      actions.push({
        title: formatCountTitle("Open Sales Order", "Open Sales Orders", linked.sales_orders.length),
        variant: "primary",
        icon: "sales_order",
        handler: () => {
          if (linked.sales_orders.length === 1) {
            routeToDoc("Sales Order", linked.sales_orders[0].name);
            return;
          }
          routeToList("Sales Order", { name: ["in", linked.sales_orders.map((row) => row.name)] });
        },
      });
    }

    if (party && party.doctype && party.name) {
      actions.push({
        title: `Open ${getPartyLabel(party.doctype)}`,
        variant: actions.length ? "secondary" : "primary",
        icon: "customer",
        handler: () => routeToDoc(party.doctype, party.name),
      });
    }

    if (linked.opportunity && linked.opportunity.name) {
      actions.push({
        title: "Open Opportunity",
        variant: "secondary",
        icon: "opportunity",
        handler: () => routeToDoc("Opportunity", linked.opportunity.name),
      });
    }

    actions.push({
      title: support.open_task_count ? `Review Follow-Up (${support.open_task_count})` : "Create Follow-Up Task",
      variant: "secondary",
      icon: "follow_up",
      handler: () => {
        if (support.open_task_count) {
          routeToList("ToDo", { reference_name: ["in", getReferenceNames(frm, data)], status: ["!=", "Closed"] });
          return;
        }
        createFollowUpTask(frm, data);
      },
    });

    if (Array.isArray(linked.deliveries) && linked.deliveries.length) {
      actions.push({
        title: formatCountTitle("Open Delivery", "Open Deliveries", linked.deliveries.length),
        variant: "secondary",
        icon: "delivery",
        handler: () => {
          if (linked.deliveries.length === 1) {
            routeToDoc("Delivery Note", linked.deliveries[0].name);
            return;
          }
          routeToList("Delivery Note", { name: ["in", linked.deliveries.map((row) => row.name)] });
        },
      });
    }

    if (Array.isArray(linked.invoices) && linked.invoices.length) {
      actions.push({
        title: formatCountTitle("Open Invoice", "Open Invoices", linked.invoices.length),
        variant: "secondary",
        icon: "invoice",
        handler: () => {
          if (linked.invoices.length === 1) {
            routeToDoc("Sales Invoice", linked.invoices[0].name);
            return;
          }
          routeToList("Sales Invoice", { name: ["in", linked.invoices.map((row) => row.name)] });
        },
      });
    }

    return actions;
  }

  function addressSectionIconMarkup(kind) {
    const icons = {
      customer: `
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M12 11.5a3.5 3.5 0 1 0 0-7a3.5 3.5 0 0 0 0 7zm-6 8a6 6 0 0 1 12 0M17.5 7.5h3M19 6v3" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      `,
      shipping: `
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M3 8h10v7H3zM13 10.5h3l2 2v2h-5zM7 17.5a1.5 1.5 0 1 1-3 0a1.5 1.5 0 0 1 3 0zm11 0a1.5 1.5 0 1 1-3 0a1.5 1.5 0 0 1 3 0z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      `,
      company: `
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M4.5 19.5h15M6.5 19.5V7.2L12 4.5l5.5 2.7v12.3M9 10h1.5M13.5 10H15M9 13.5h1.5M13.5 13.5H15" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      `,
    };

    return icons[kind] || icons.customer;
  }

  function termsSectionIconMarkup(kind) {
    const icons = {
      payment: `
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M3.5 7.5h17v9h-17zM3.5 10.5h17M7 14h3.5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      `,
      policy: `
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M7 3.5h7l4 4v13H7zM14 3.5v4h4M10 12h5M10 15.5h5M10 19h3" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      `,
    };

    return icons[kind] || icons.policy;
  }

  function getLanguageLabel(value) {
    const normalized = String(value || "").trim();
    if (!normalized) return "Default";

    const labels = {
      en: "English",
      my: "Burmese",
    };

    return labels[normalized.toLowerCase()] || normalized;
  }

  function shouldShowPricingSection(frm) {
    const sameCurrency = usesCompanyCurrencyOnly(frm);
    const rateSignals = [frm.doc.plc_conversion_rate, frm.doc.conversion_rate].some((value) => {
      if (!hasMeaningfulValue(value)) return false;
      return Number(value) !== 1;
    });
    const pricingSignals = [
      frm.doc.ignore_pricing_rule,
    ];

    const hasPricingSignal = rateSignals || pricingSignals.some((value) => hasMeaningfulValue(value));
    return !sameCurrency || hasPricingSignal;
  }

  function hasQuotationDiscountSignal(frm) {
    return [
      frm.doc.additional_discount_percentage,
      frm.doc.discount_amount,
      frm.doc.base_discount_amount,
      frm.doc.coupon_code,
    ].some((value) => hasMeaningfulValue(value));
  }

  function getQuotationDaysToExpiry(frm) {
    if (!frm.doc.valid_till) return null;
    try {
      return frappe.datetime.get_diff(frm.doc.valid_till, frappe.datetime.get_today());
    } catch (e) {
      return null;
    }
  }

  function isQuotationReviewPosture(frm) {
    const workflowLabel = String(frm.doc.workflow_state || "");
    const statusLabel = String(frm.doc.status || "");
    const daysToExpiry = getQuotationDaysToExpiry(frm);

    if (Number(frm.doc.docstatus || 0) === 1) return true;
    if (workflowLabel && /(pending|approval|review)/i.test(workflowLabel)) return true;
    if (Number.isFinite(daysToExpiry) && daysToExpiry < 0) return true;
    return ["Lost", "Ordered"].includes(statusLabel);
  }

  function focusFirstVisibleControl($section) {
    if (!$section || !$section.length) return;

    setTimeout(() => {
      const selector = [
        'input:not([type="hidden"]):not([disabled])',
        "select:not([disabled])",
        "textarea:not([disabled])",
        "button:not([disabled])",
      ].join(", ");

      const target = $section.find(selector).filter(":visible").get(0);
      if (target && typeof target.focus === "function") {
        target.focus();
      }
    }, 40);
  }

  function focusFieldControl(frm, fieldname) {
    const field = frm.fields_dict && frm.fields_dict[fieldname];
    const $wrapper = getFieldWrapper(frm, fieldname);
    if (!$wrapper || !$wrapper.length) return;

    const wrapperNode = $wrapper.get(0);
    if (wrapperNode && typeof wrapperNode.scrollIntoView === "function") {
      wrapperNode.scrollIntoView({ behavior: "smooth", block: "center", inline: "nearest" });
    }

    $(frm.page && frm.page.main ? frm.page.main : frm.$wrapper || []).find(".erpw-so-address-focus-target").removeClass("erpw-so-address-focus-target");
    $wrapper.addClass("erpw-so-address-focus-target");
    setTimeout(() => $wrapper.removeClass("erpw-so-address-focus-target"), 2200);

    setTimeout(() => {
      if (field && typeof field.set_focus === "function") {
        field.set_focus();
      }

      const selector = [
        'input:not([type="hidden"]):not([disabled])',
        "select:not([disabled])",
        "textarea:not([disabled])",
        "button:not([disabled])",
      ].join(", ");

      const target = $wrapper.find(selector).filter(":visible").get(0);
      if (target && typeof target.focus === "function") {
        target.focus();
        if (typeof target.click === "function") {
          target.click();
        }
        return;
      }

      focusFirstVisibleControl($wrapper.closest(".form-section"));
    }, 80);
  }

  function triggerFieldPrimaryAction(frm, fieldname) {
    const field = frm.fields_dict && frm.fields_dict[fieldname];
    if (!field) return;

    focusFieldControl(frm, fieldname);

    setTimeout(() => {
      if (field.df && field.df.fieldtype === "Link" && typeof field.open_advanced_search === "function") {
        field.open_advanced_search();
        return;
      }

      if (field.df && field.df.fieldtype === "Link" && field.$input && field.$input.length) {
        field.$input.trigger("focus");
        if (typeof field.on_input === "function") {
          field.on_input();
        }
      }
    }, 120);
  }

  function containerHasVisibleControls($container) {
    return hasVisibleControls($container);
  }

  function moveFieldIntoSectionBodyIfNeeded(frm, fieldname, $section, scopeKey) {
    const $wrapper = getFieldWrapper(frm, fieldname);
    relocateSharedFieldIntoSectionBody($wrapper, $section, scopeKey);
  }

  function restoreRelocatedFieldPlacements(frm, scopeKey) {
    const $root = getFormRoot(frm);
    if (!$root.length) return;
    restoreSharedRelocatedFieldPlacements($root, scopeKey);
  }

  function ensureAddressContactStack($tab) {
    if (typeof childPageSections.ensureSectionStack === "function") {
      return childPageSections.ensureSectionStack($tab, "erpw-so-address-stack");
    }

    let $stack = $tab.children(".erpw-so-address-stack").first();
    if ($stack.length) return $stack;

    $stack = $('<div class="erpw-so-address-stack"></div>');
    $tab.prepend($stack);
    return $stack;
  }

  function ensureAddressContactSectionHeader($section, config, presentation) {
    if (typeof childPageSections.ensureAddressSectionHeader === "function") {
      return childPageSections.ensureAddressSectionHeader($section, {
        iconMarkup: addressSectionIconMarkup(config.icon || "customer"),
        note: config.note,
        statusText: String((presentation && presentation.statusText) || "").trim(),
        statusTone: String((presentation && presentation.statusTone) || "neutral").trim(),
        title: config.title,
      });
    }

    const $defaultHead = $section.children(".section-head").first();
    if ($defaultHead.length) {
      $defaultHead.addClass("erpw-so-address-default-head").hide();
    }

    let $header = $section.children(".erpw-so-address-header").first();
    if (!$header.length) {
      $header = $(`
        <div class="erpw-so-address-header">
          <div class="erpw-so-address-header-main">
            <span class="erpw-so-address-header-icon" aria-hidden="true"></span>
            <div class="erpw-so-address-header-copy">
              <div class="erpw-so-address-header-title"></div>
              <div class="erpw-so-address-header-note"></div>
            </div>
          </div>
          <div class="erpw-so-address-header-status" hidden></div>
        </div>
      `);
      $section.prepend($header);
    }

    $header.find(".erpw-so-address-header-icon").html(addressSectionIconMarkup(config.icon || "customer"));
    $header.find(".erpw-so-address-header-title").text(config.title || "");
    $header.find(".erpw-so-address-header-note").text(config.note || "");

    const $status = $header.find(".erpw-so-address-header-status");
    const statusText = String((presentation && presentation.statusText) || "").trim();
    const statusTone = String((presentation && presentation.statusTone) || "neutral").trim();

    if (statusText) {
      $status.text(statusText).attr("data-tone", statusTone).prop("hidden", false);
    } else {
      $status.text("").removeAttr("data-tone").prop("hidden", true);
    }
  }

  function ensureAddressContactStatePanel($section) {
    if (typeof childPageSections.ensureSectionStatePanel === "function") {
      return childPageSections.ensureSectionStatePanel($section, "erpw-so-address");
    }

    const $body = $section.children(".section-body").first();
    if (!$body.length) return $();

    let $panel = $body.children(".erpw-so-address-state-panel").first();
    if ($panel.length) return $panel;

    $panel = $(`
      <div class="erpw-so-address-state-panel" hidden>
        <div class="erpw-so-address-state-copy">
          <div class="erpw-so-address-state-title"></div>
          <div class="erpw-so-address-state-note"></div>
        </div>
        <button type="button" class="erpw-so-address-state-action"></button>
      </div>
    `);

    $body.prepend($panel);
    return $panel;
  }

  function getQuotationAddressContactSectionPresentation(frm, key) {
    const hasBillingAddress = [frm.doc.customer_address, frm.doc.address_display].some((value) => hasMeaningfulValue(value));
    const hasContactPerson = hasMeaningfulValue(frm.doc.contact_person);
    const hasContactChannel = [frm.doc.contact_mobile, frm.doc.contact_email].some((value) => hasMeaningfulValue(value));
    const hasCustomerContact = hasContactPerson || hasContactChannel;
    const hasShippingAddress = [frm.doc.shipping_address_name, frm.doc.shipping_address].some((value) => hasMeaningfulValue(value));
    const hasCompanyAddress = [frm.doc.company_address, frm.doc.company_address_display].some((value) => hasMeaningfulValue(value));
    const hasCompanyContact = hasMeaningfulValue(frm.doc.company_contact_person);

    const presentations = {
      customer: {
        wide: true,
        priority: true,
        statusTone: hasBillingAddress && hasCustomerContact ? "active" : "attention",
        statusText: hasBillingAddress && hasCustomerContact
          ? "Commercially ready"
          : hasCustomerContact
            ? "Billing needed"
            : hasBillingAddress
              ? "Contact needed"
              : "Setup needed",
        state: (!hasBillingAddress || !hasCustomerContact) ? {
          title: !hasBillingAddress && !hasCustomerContact
            ? "Billing address and contact are not linked yet"
            : !hasBillingAddress
              ? "Billing address is not linked yet"
              : "Primary contact is missing",
          note: !hasBillingAddress && !hasCustomerContact
            ? "Link both before sending final commercial confirmation."
            : !hasBillingAddress
              ? "Set the billing address before the quotation becomes a committed commercial reference."
              : "Add a contact so commercial follow-up has a clear owner.",
          actionLabel: !hasBillingAddress ? "Select billing address" : "Select contact",
          focusField: !hasBillingAddress ? "customer_address" : "contact_person",
        } : null,
      },
      shipping: {
        statusTone: hasShippingAddress ? "active" : "neutral",
        statusText: hasShippingAddress ? "Shipping set" : "Optional",
        summaryMode: !hasShippingAddress,
        state: !hasShippingAddress ? {
          title: "Shipping address is not linked yet",
          note: "Add delivery context only when the quotation needs fulfillment-ready destination detail.",
          actionLabel: "Select shipping address",
          focusField: "shipping_address_name",
        } : null,
      },
      company: {
        quiet: true,
        statusTone: hasCompanyAddress ? "active" : "neutral",
        statusText: hasCompanyAddress ? "Configured" : (hasCompanyContact ? "Contact only" : "Not set"),
        summaryMode: !hasCompanyAddress,
        state: !hasCompanyAddress ? {
          title: "Company address is not linked on this quotation",
          note: "Set it only when the quotation should present a specific issuing location.",
          actionLabel: "Select company address",
          focusField: "company_address",
        } : null,
      },
    };

    return presentations[key] || {};
  }

  function applyAddressContactSectionState(frm, $section, presentation) {
    if (!$section || !$section.length) return;

    const state = presentation && presentation.state;
    const $panel = ensureAddressContactStatePanel($section);
    if (!$panel.length) return;

    if (!state) {
      $panel.prop("hidden", true);
      return;
    }

    $panel.find(".erpw-so-address-state-title").text(state.title || "");
    $panel.find(".erpw-so-address-state-note").text(state.note || "");
    $panel.find(".erpw-so-address-state-action")
      .text(state.actionLabel || "Update")
      .off(".erpwAddressState")
      .on("click.erpwAddressState", (event) => {
        event.preventDefault();
        event.stopPropagation();
        if (state.focusField) {
          triggerFieldPrimaryAction(frm, state.focusField);
        }
      });

    $panel.prop("hidden", false);
  }

  function resetAddressContactTab(frm, $tab) {
    if (!$tab || !$tab.length) return;

    restoreRelocatedFieldPlacements(frm, "quotation-address");
    $tab.find(".erpw-so-address-customer-grid").each((_, element) => {
      const $grid = $(element);
      const $body = $grid.closest(".section-body");
      $grid.children(".frappe-control").each((__, control) => {
        $(control)
          .removeClass("erpw-so-address-grid-field")
          .removeAttr("data-address-grid-field")
          .appendTo($body);
      });
      $grid.remove();
    });

    $tab.children(".erpw-so-address-stack").remove();
    $tab.find(".erpw-so-address-state-panel").remove();
    $tab.find(".erpw-so-address-header").remove();
    $tab.find(".erpw-so-address-default-head").removeClass("erpw-so-address-default-head").show();
    $tab.find(".form-section")
      .show()
      .removeClass([
        "erpw-so-address-section",
        "erpw-so-address-section-wide",
        "erpw-so-address-section-priority",
        "erpw-so-address-section-quiet",
        "erpw-so-address-section-customer",
        "erpw-so-address-section-shipping",
        "erpw-so-address-section-company",
        "erpw-so-address-hidden-source",
        "erpw-so-address-column-empty",
      ].join(" "));
  }

  function arrangeQuotationCustomerContactGrid(frm, $section) {
    return arrangeSharedAddressFieldGrid($section, {
      fieldnames: coreAddressFieldOrder,
      getWrapper: (fieldname) => getFieldWrapper(frm, fieldname),
      placeholders: coreAddressPlaceholders,
      values: frm.doc || {},
    });
  }

  function enhanceAddressContactTab(frm) {
    if (!frm || !frm.fields_dict) return false;

    const $tab = getTabByFieldname(frm, "address_and_contact_tab");
    if (!$tab.length) return false;

    resetAddressContactTab(frm, $tab);
    $tab.addClass("erpw-so-address-tab");

    const hasShippingAddress = [frm.doc.shipping_address_name, frm.doc.shipping_address].some((value) => hasMeaningfulValue(value));
    const hasCompanyAddress = [frm.doc.company_address, frm.doc.company_address_display].some((value) => hasMeaningfulValue(value));
    const hasCompanyContact = hasMeaningfulValue(frm.doc.company_contact_person);

    toggleField(frm, "contact_person", true);
    toggleField(frm, "customer_address", true);
    toggleField(frm, "address_display", true);
    toggleField(frm, "contact_mobile", true);
    toggleField(frm, "contact_email", true);
    toggleField(frm, "territory", true);
    toggleField(frm, "shipping_address", hasShippingAddress);
    toggleField(frm, "company_address_display", hasCompanyAddress);
    toggleField(frm, "company_contact_person", hasCompanyAddress || hasCompanyContact);
    toggleField(frm, "customer_group", false);

    const configs = [
      {
        key: "customer",
        fieldname: "customer_address",
        title: "Customer Billing & Contact",
        note: "Billing address, territory, and commercial contact for this quotation.",
        icon: "customer",
      },
      {
        key: "shipping",
        fieldname: "shipping_address_name",
        title: "Shipping Context",
        note: "Delivery destination only when the quotation needs fulfillment-ready context.",
        icon: "shipping",
      },
      {
        key: "company",
        fieldname: "company_address",
        title: "Company Address",
        note: "Issuing company location for quotation print and customer-facing commercial output.",
        icon: "company",
      },
    ];

    const $stack = ensureAddressContactStack($tab);
    const seen = new Set();

    configs.forEach((config) => {
      const $section = getSectionForField(frm, config.fieldname);
      if (!$section || !$section.length) return;

      const sectionNode = $section.get(0);
      if (seen.has(sectionNode)) return;
      seen.add(sectionNode);

      const presentation = getQuotationAddressContactSectionPresentation(frm, config.key);
      $section
        .addClass(`erpw-so-address-section erpw-so-address-section-${config.key}`)
        .toggleClass("erpw-so-address-section-wide", !!presentation.wide)
        .toggleClass("erpw-so-address-section-priority", !!presentation.priority)
        .toggleClass("erpw-so-address-section-quiet", !!presentation.quiet)
        .toggleClass("erpw-so-address-section-summary-mode", !!(presentation.summaryMode && presentation.state));

      ensureAddressContactSectionHeader($section, config, presentation);
      applyAddressContactSectionState(frm, $section, presentation);
      $stack.append($section);

      if (config.key === "customer") {
        coreAddressFieldOrder.forEach((fieldname) => {
          moveFieldIntoSectionBodyIfNeeded(frm, fieldname, $section, "quotation-address");
        });
        arrangeQuotationCustomerContactGrid(frm, $section);
      }
      if (config.key === "company") {
        moveFieldIntoSectionBodyIfNeeded(frm, "company_contact_person", $section, "quotation-address");
      }
    });

    if (typeof childPageSections.normalizeAddressFieldDisplays === "function") {
      childPageSections.normalizeAddressFieldDisplays($stack, [
        "customer_address",
        "shipping_address_name",
        "dispatch_address_name",
        "company_address",
      ]);
    }

    $tab.children(".form-section").not($stack.children(".form-section")).each((_, element) => {
      $(element).addClass("erpw-so-address-hidden-source").hide();
    });

    if (frm.layout && typeof frm.layout.refresh_sections === "function") {
      frm.layout.refresh_sections();
    }
    return seen.size > 0;
  }

  function ensureTermsStack($tab) {
    if (typeof childPageTerms.ensureTermsStack === "function") {
      return childPageTerms.ensureTermsStack($tab, "erpw-so-terms-stack");
    }

    if (typeof childPageSections.ensureSectionStack === "function") {
      return childPageSections.ensureSectionStack($tab, "erpw-so-terms-stack");
    }

    let $stack = $tab.children(".erpw-so-terms-stack").first();
    if ($stack.length) return $stack;

    $stack = $('<div class="erpw-so-terms-stack"></div>');
    $tab.prepend($stack);
    return $stack;
  }

  function ensureTermsSectionHeader($section, config, presentation) {
    if (typeof childPageTerms.ensureTermsSectionHeader === "function") {
      return childPageTerms.ensureTermsSectionHeader($section, {
        icon: config.icon || "policy",
        note: config.note,
        statusText: String((presentation && presentation.statusText) || "").trim(),
        statusTone: String((presentation && presentation.statusTone) || "neutral").trim(),
        title: config.title,
      });
    }

    const $defaultHead = $section.children(".section-head").first();
    if ($defaultHead.length) {
      $defaultHead.addClass("erpw-so-terms-default-head").hide();
    }

    let $header = $section.children(".erpw-so-terms-header").first();
    if (!$header.length) {
      $header = $(`
        <div class="erpw-so-terms-header">
          <div class="erpw-so-terms-header-main">
            <span class="erpw-so-terms-header-icon" aria-hidden="true"></span>
            <div class="erpw-so-terms-header-copy">
              <div class="erpw-so-terms-header-title"></div>
              <div class="erpw-so-terms-header-note"></div>
            </div>
          </div>
          <div class="erpw-so-terms-header-status" hidden></div>
        </div>
      `);
      $section.prepend($header);
    }

    $header.find(".erpw-so-terms-header-icon").html(termsSectionIconMarkup(config.icon || "policy"));
    $header.find(".erpw-so-terms-header-title").text(config.title || "");
    $header.find(".erpw-so-terms-header-note").text(config.note || "");

    const $status = $header.find(".erpw-so-terms-header-status");
    const statusText = String((presentation && presentation.statusText) || "").trim();
    const statusTone = String((presentation && presentation.statusTone) || "neutral").trim();

    if (statusText) {
      $status.text(statusText).attr("data-tone", statusTone).prop("hidden", false);
    } else {
      $status.text("").removeAttr("data-tone").prop("hidden", true);
    }
  }

  function ensureTermsStatePanel($section) {
    if (typeof childPageTerms.ensureTermsStatePanel === "function") {
      return childPageTerms.ensureTermsStatePanel($section);
    }

    const $body = $section.children(".section-body").first();
    if (!$body.length) return $();

    let $panel = $body.children(".erpw-so-terms-state-panel").first();
    if ($panel.length) return $panel;

    $panel = $(`
      <div class="erpw-so-terms-state-panel" hidden>
        <div class="erpw-so-terms-state-copy">
          <div class="erpw-so-terms-state-title"></div>
          <div class="erpw-so-terms-state-note"></div>
        </div>
        <button type="button" class="erpw-so-terms-state-action"></button>
      </div>
    `);

    $body.prepend($panel);
    return $panel;
  }

  function ensureTermsMetrics($section) {
    if (typeof childPageTerms.ensureTermsMetrics === "function") {
      return childPageTerms.ensureTermsMetrics($section);
    }

    const $body = $section.children(".section-body").first();
    if (!$body.length) return $();

    let $metrics = $body.children(".erpw-so-terms-metrics").first();
    if ($metrics.length) return $metrics;

    $metrics = $('<div class="erpw-so-terms-metrics"></div>');
    $body.prepend($metrics);
    return $metrics;
  }

  function ensureTermsAssistNote($section) {
    if (typeof childPageTerms.ensureTermsAssistNote === "function") {
      return childPageTerms.ensureTermsAssistNote($section);
    }

    const $body = $section.children(".section-body").first();
    if (!$body.length) return $();

    let $note = $body.children(".erpw-so-terms-assist-note").first();
    if ($note.length) return $note;

    $note = $('<div class="erpw-so-terms-assist-note" hidden></div>');
    $body.prepend($note);
    return $note;
  }

  function getQuotationPaymentScheduleSummary(frm) {
    const rows = Array.isArray(frm.doc.payment_schedule) ? frm.doc.payment_schedule : [];
    const visibleRows = rows.filter((row) => row);
    const milestoneCount = visibleRows.length;
    const scheduledAmount = visibleRows.reduce((sum, row) => sum + Number(row.payment_amount || 0), 0);
    const dueDates = visibleRows.map((row) => row.due_date).filter(Boolean).sort();
    return {
      milestoneCount,
      scheduledAmount,
      earliestDue: dueDates[0] || null,
    };
  }

  function getQuotationTermsSectionPresentation(frm, key) {
    const paymentSummary = getQuotationPaymentScheduleSummary(frm);
    const hasTemplate = hasMeaningfulValue(frm.doc.payment_terms_template);
    const hasTermsTemplate = hasMeaningfulValue(frm.doc.tc_name);
    const hasTermsText = hasMeaningfulValue(frm.doc.terms);
    const workflowPending = String(frm.doc.workflow_state || "").includes("Pending");
    const paymentMetrics = paymentSummary.milestoneCount || hasTemplate ? [
      {
        label: "Scheduled",
        value: formatMoney(paymentSummary.scheduledAmount, frm.doc.currency),
      },
      {
        label: "Due",
        value: paymentSummary.earliestDue ? formatDateLabel(paymentSummary.earliestDue) : "--",
      },
      {
        label: "Setup",
        value: hasTemplate ? "Template linked" : "Manual schedule",
      },
      ...(hasTemplate ? [
        {
          label: "Template",
          value: String(frm.doc.payment_terms_template || "").trim(),
        },
      ] : []),
    ] : [];

    const presentations = {
      payment: {
        wide: true,
        priority: true,
        statusTone: paymentSummary.milestoneCount ? "active" : (hasTemplate ? "active" : "attention"),
        statusText: paymentSummary.milestoneCount
          ? `${paymentSummary.milestoneCount} milestone${paymentSummary.milestoneCount === 1 ? "" : "s"}`
          : hasTemplate
            ? "Template linked"
            : "Schedule needed",
        assistNote: workflowPending ? "Keep payment structure aligned with the current approval and validity posture." : "",
        metrics: paymentMetrics,
        state: !paymentSummary.milestoneCount && !hasTemplate ? {
          title: "Payment structure is not configured yet",
          note: "Link a payment terms template or define the schedule only when the quotation needs explicit commercial milestones.",
          actionLabel: "Select payment terms",
          focusField: "payment_terms_template",
        } : null,
      },
      conditions: {
        wide: true,
        quiet: !hasTermsTemplate && !hasTermsText,
        statusTone: hasTermsTemplate || hasTermsText ? "active" : "neutral",
        statusText: hasTermsTemplate ? "Template linked" : (hasTermsText ? "Custom text" : "Not set"),
        state: !hasTermsTemplate && !hasTermsText ? {
          title: "No quotation terms have been added yet",
          note: "Add commercial terms only when the quote needs explicit customer-facing conditions.",
          actionLabel: "Add terms",
          focusField: "tc_name",
          revealFields: true,
        } : null,
      },
    };

    return presentations[key] || {};
  }

  function applyTermsSectionState(frm, $section, presentation) {
    if (typeof childPageTerms.applyTermsSectionState === "function") {
      return childPageTerms.applyTermsSectionState($section, presentation, {
        onFocusField(fieldname) {
          triggerFieldPrimaryAction(frm, fieldname);
        },
        onRevealFields() {
          toggleField(frm, "tc_name", true);
          toggleField(frm, "terms", true);
        },
      });
    }

    if (!$section || !$section.length) return;

    const state = presentation && presentation.state;
    const revealRaw = Boolean($section.data("erpwTermsRevealRaw"));
    const showState = Boolean(state && !revealRaw);
    const $panel = ensureTermsStatePanel($section);
    if (!$panel.length) return;

    $section.toggleClass("erpw-so-terms-section-summary-mode", showState);

    if (!showState) {
      $panel.prop("hidden", true);
      return;
    }

    $panel.find(".erpw-so-terms-state-title").text(state.title || "");
    $panel.find(".erpw-so-terms-state-note").text(state.note || "");
    const $action = $panel.find(".erpw-so-terms-state-action");
    const hasAction = Boolean(state.actionLabel && state.focusField);

    if (hasAction) {
      $action
        .text(state.actionLabel || "Configure")
        .prop("hidden", false)
        .off(".erpwTermsState")
        .on("click.erpwTermsState", (event) => {
          event.preventDefault();
          event.stopPropagation();

          if (state.revealFields) {
            toggleField(frm, "tc_name", true);
            toggleField(frm, "terms", true);
            $section.data("erpwTermsRevealRaw", 1);
            applyTermsSectionState(frm, $section, presentation);
          }

          if (state.focusField) {
            triggerFieldPrimaryAction(frm, state.focusField);
          }
        });
    } else {
      $action.text("").prop("hidden", true).off(".erpwTermsState");
    }

    $panel.prop("hidden", false);
  }

  function applyTermsMetrics($section, presentation) {
    if (typeof childPageTerms.applyTermsMetrics === "function") {
      return childPageTerms.applyTermsMetrics($section, presentation);
    }

    if (!$section || !$section.length) return;

    const metrics = presentation && Array.isArray(presentation.metrics) ? presentation.metrics : [];
    const $metrics = ensureTermsMetrics($section);
    if (!$metrics.length) return;

    if (!metrics.length) {
      $metrics.empty().hide();
      return;
    }

    $metrics.html(metrics.map((metric) => `
      <div class="erpw-so-terms-metric">
        <div class="erpw-so-terms-metric-label">${escapeHtml(metric.label)}</div>
        <div class="erpw-so-terms-metric-value">${escapeHtml(metric.value)}</div>
      </div>
    `).join(""));
    $metrics.show();
  }

  function applyTermsAssistNote($section, presentation) {
    if (typeof childPageTerms.applyTermsAssistNote === "function") {
      return childPageTerms.applyTermsAssistNote($section, presentation);
    }

    if (!$section || !$section.length) return;

    const noteText = String((presentation && presentation.assistNote) || "").trim();
    const $note = ensureTermsAssistNote($section);
    if (!$note.length) return;

    if (!noteText) {
      $note.text("").prop("hidden", true);
      return;
    }

    $note.text(noteText).prop("hidden", false);
  }

  function resetTermsTab($tab) {
    if (typeof childPageTerms.resetTermsTab === "function") {
      return childPageTerms.resetTermsTab($tab);
    }

    if (!$tab || !$tab.length) return;

    $tab.children(".erpw-so-terms-stack").remove();
    $tab.find(".erpw-so-terms-state-panel").remove();
    $tab.find(".erpw-so-terms-header").remove();
    $tab.find(".erpw-so-terms-metrics").remove();
    $tab.find(".form-section").removeData("erpwTermsRevealRaw");
    $tab.find(".erpw-so-terms-default-head").removeClass("erpw-so-terms-default-head").show();
    $tab.find(".form-section")
      .show()
      .removeClass([
        "erpw-so-terms-section",
        "erpw-so-terms-section-wide",
        "erpw-so-terms-section-priority",
        "erpw-so-terms-section-quiet",
        "erpw-so-terms-section-payment",
        "erpw-so-terms-section-conditions",
        "erpw-so-terms-hidden-source",
        "erpw-so-terms-section-summary-mode",
      ].join(" "));
  }

  function enhanceTermsTab(frm) {
    if (!frm || !frm.fields_dict) return false;

    const $tab = getTabByFieldname(frm, "terms_tab");
    if (!$tab.length) return false;

    resetTermsTab($tab);
    $tab.addClass("erpw-so-terms-tab");

    const hasPaymentTemplate = hasMeaningfulValue(frm.doc.payment_terms_template);
    const hasTermsTemplate = hasMeaningfulValue(frm.doc.tc_name);
    const hasTermsText = hasMeaningfulValue(frm.doc.terms);

    toggleField(frm, "payment_terms_template", false);
    toggleField(frm, "payment_schedule", true);
    toggleField(frm, "tc_name", hasTermsTemplate || !hasTermsText);
    toggleField(frm, "terms", hasTermsText);

    const configs = [
      {
        key: "payment",
        fieldname: "payment_terms_template",
        title: "Payment Structure",
        note: "Template and milestone schedule that support commercial commitment.",
        icon: "payment",
      },
      {
        key: "conditions",
        fieldname: "tc_name",
        title: "Terms & Conditions",
        note: "Customer-facing quotation terms and commercial clauses.",
        icon: "policy",
      },
    ];

    const $stack = ensureTermsStack($tab);
    const seen = new Set();

    configs.forEach((config) => {
      const $section = getSectionForField(frm, config.fieldname);
      if (!$section || !$section.length) return;

      const sectionNode = $section.get(0);
      if (seen.has(sectionNode)) return;
      seen.add(sectionNode);

      const presentation = getQuotationTermsSectionPresentation(frm, config.key);
      $section
        .addClass(`erpw-so-terms-section erpw-so-terms-section-${config.key}`)
        .toggleClass("erpw-so-terms-section-wide", !!presentation.wide)
        .toggleClass("erpw-so-terms-section-priority", !!presentation.priority)
        .toggleClass("erpw-so-terms-section-quiet", !!presentation.quiet);

      ensureTermsSectionHeader($section, config, presentation);
      applyTermsMetrics($section, presentation);
      applyTermsAssistNote($section, presentation);
      applyTermsSectionState(frm, $section, presentation);
      $stack.append($section);
    });

    $tab.children(".form-section").not($stack.children(".form-section")).each((_, element) => {
      $(element).addClass("erpw-so-terms-hidden-source").hide();
    });

    if (frm.layout && typeof frm.layout.refresh_sections === "function") {
      frm.layout.refresh_sections();
    }
    return seen.size > 0;
  }

  function ensureMoreInfoStack($tab) {
    let $stack = $tab.children(".erpw-so-moreinfo-stack").first();
    if ($stack.length) return $stack;

    $stack = $('<div class="erpw-so-moreinfo-stack"></div>');
    $tab.prepend($stack);
    return $stack;
  }

  function ensureMoreInfoSectionHeader($section, title, note) {
    if (typeof childPageSections.ensureMoreInfoSectionHeader === "function") {
      return childPageSections.ensureMoreInfoSectionHeader($section, {
        note,
        title,
      });
    }

    const $defaultHead = $section.children(".section-head").first();
    if ($defaultHead.length) {
      $defaultHead.addClass("erpw-so-moreinfo-default-head").hide();
    }

    let $header = $section.children(".erpw-so-moreinfo-header").first();
    if (!$header.length) {
      $header = $(`
        <div class="erpw-so-moreinfo-header">
          <div class="erpw-so-moreinfo-header-copy">
            <div class="erpw-so-moreinfo-header-title"></div>
            <div class="erpw-so-moreinfo-header-note"></div>
          </div>
          <div class="erpw-so-moreinfo-header-side">
            <div class="erpw-so-moreinfo-header-status" hidden></div>
          </div>
        </div>
      `);
      $section.prepend($header);
    }

    $header.find(".erpw-so-moreinfo-header-title").text(title || "");
    $header.find(".erpw-so-moreinfo-header-note").text(note || "");
  }

  function applyMoreInfoHeaderState($section, presentation) {
    const $header = $section.children(".erpw-so-moreinfo-header").first();
    if (!$header.length) return;

    const statusText = String((presentation && presentation.statusText) || "").trim();
    const statusTone = String((presentation && presentation.statusTone) || "neutral").trim();
    const $status = $header.find(".erpw-so-moreinfo-header-status");

    if (statusText) {
      $status.text(statusText).attr("data-tone", statusTone).prop("hidden", false);
    } else {
      $status.text("").removeAttr("data-tone").prop("hidden", true);
    }
  }

  function ensureMoreInfoStatePanel($section) {
    if (typeof childPageSections.ensureSectionStatePanel === "function") {
      return childPageSections.ensureSectionStatePanel($section, "erpw-so-moreinfo");
    }

    const $body = $section.children(".section-body").first();
    if (!$body.length) return $();

    let $panel = $body.children(".erpw-so-moreinfo-state-panel").first();
    if ($panel.length) return $panel;

    $panel = $(`
      <div class="erpw-so-moreinfo-state-panel" hidden>
        <div class="erpw-so-moreinfo-state-copy">
          <div class="erpw-so-moreinfo-state-title"></div>
          <div class="erpw-so-moreinfo-state-note"></div>
        </div>
        <button type="button" class="erpw-so-moreinfo-state-action"></button>
      </div>
    `);

    $body.prepend($panel);
    return $panel;
  }

  function getQuotationMoreInfoSectionPresentation(frm, key) {
    const languageLabel = getLanguageLabel(frm.doc.language);
    const hasContextSignal = [
      frm.doc.opportunity,
      frm.doc.supplier_quotation,
      frm.doc.referral_sales_partner,
    ].some((value) => hasMeaningfulValue(value));
    const hasLostSignal = String(frm.doc.status || "") === "Lost"
      || hasMeaningfulValue(frm.doc.order_lost_reason)
      || (Array.isArray(frm.doc.lost_reasons) && frm.doc.lost_reasons.length > 0);
    const hasCustomOutput = [
      frm.doc.letter_head,
      frm.doc.select_print_heading,
      frm.doc.group_same_items,
    ].some((value) => hasMeaningfulValue(value));
    const hasOutputSignal = hasCustomOutput || (languageLabel && languageLabel.toLowerCase() !== "english");
    const hasMarketSignal = [
      frm.doc.incoterm,
      frm.doc.named_place,
      frm.doc.utm_campaign,
      frm.doc.utm_source,
      frm.doc.utm_medium,
      frm.doc.utm_content,
    ].some((value) => hasMeaningfulValue(value));

    const presentations = {
      context: {
        wide: false,
        priority: hasLostSignal,
        hidden: !hasContextSignal && !hasLostSignal,
        statusTone: hasLostSignal ? "attention" : (hasContextSignal ? "active" : "neutral"),
        statusText: hasLostSignal
          ? "Outcome logged"
          : hasMeaningfulValue(frm.doc.opportunity)
            ? "Opportunity linked"
            : hasMeaningfulValue(frm.doc.supplier_quotation)
              ? "Supplier quote linked"
              : hasMeaningfulValue(frm.doc.referral_sales_partner)
                ? "Referral set"
                : "",
        summary: null,
      },
      print: {
        hidden: !hasOutputSignal,
        statusTone: hasCustomOutput ? "active" : "neutral",
        quiet: !hasCustomOutput,
        statusText: hasCustomOutput ? "Configured" : languageLabel,
        summary: null,
      },
      controls: {
        hidden: false,
        quiet: !hasMarketSignal,
        statusTone: hasMeaningfulValue(frm.doc.incoterm) ? "active" : (hasMarketSignal ? "attention" : "neutral"),
        statusText: hasMeaningfulValue(frm.doc.incoterm)
          ? "Incoterm set"
          : [frm.doc.utm_campaign, frm.doc.utm_source, frm.doc.utm_medium, frm.doc.utm_content].some((value) => hasMeaningfulValue(value))
            ? "Campaign linked"
            : "",
        summary: !hasMarketSignal ? {
          title: "No market or delivery context added",
          note: "Add Incoterm, named place, or campaign context only when the quotation needs stronger commercial framing.",
          actionLabel: "Add context",
          focusField: "incoterm",
        } : null,
      },
    };

    return presentations[key] || {};
  }

  function applyMoreInfoSectionBodyState(frm, $section, presentation) {
    if (!$section || !$section.length) return;

    const summary = presentation && presentation.summary;
    const revealRaw = Boolean($section.data("erpwMoreinfoRevealRaw"));
    const showSummary = Boolean(summary && !revealRaw);
    const $panel = ensureMoreInfoStatePanel($section);

    $section.toggleClass("erpw-so-moreinfo-section-summary-mode", showSummary);
    if (!$panel.length) return;

    if (!showSummary) {
      $panel.prop("hidden", true);
      return;
    }

    $panel.find(".erpw-so-moreinfo-state-title").text(summary.title || "");
    $panel.find(".erpw-so-moreinfo-state-note").text(summary.note || "");

    $panel.find(".erpw-so-moreinfo-state-action")
      .text(summary.actionLabel || "Configure")
      .off(".erpwMoreInfoState")
      .on("click.erpwMoreInfoState", (event) => {
        event.preventDefault();
        event.stopPropagation();

        $section.data("erpwMoreinfoRevealRaw", 1);
        applyMoreInfoSectionBodyState(frm, $section, presentation);

        if (summary.focusField) {
          triggerFieldPrimaryAction(frm, summary.focusField);
          return;
        }
        focusFirstVisibleControl($section);
      });

    $panel.prop("hidden", false);
  }

  function resetMoreInfoTab(frm, $tab) {
    if (!$tab || !$tab.length) return;

    restoreRelocatedFieldPlacements(frm, "quotation-moreinfo");
    $tab.children(".erpw-so-moreinfo-stack").remove();
    $tab.find(".erpw-so-moreinfo-metrics").remove();
    $tab.find(".erpw-so-moreinfo-state-panel").remove();
    $tab.find(".erpw-so-moreinfo-header").remove();
    $tab.find(".form-section").removeData("erpwMoreinfoRevealRaw");
    $tab.find(".erpw-so-moreinfo-default-head").removeClass("erpw-so-moreinfo-default-head").show();
    $tab.find(".form-section")
      .show()
      .removeClass("hide-control empty-section visible-section erpw-so-moreinfo-hidden-source erpw-so-moreinfo-section-summary-mode");
    $tab.find(".form-section").removeClass([
      "erpw-so-moreinfo-section",
      "erpw-so-moreinfo-section-context",
      "erpw-so-moreinfo-section-print",
      "erpw-so-moreinfo-section-controls",
      "erpw-so-moreinfo-section-priority",
      "erpw-so-moreinfo-section-quiet",
      "erpw-so-moreinfo-section-wide",
    ].join(" "));
  }

  function enhanceMoreInfoTab(frm) {
    if (!frm || !frm.fields_dict) return false;

    const $tab = getTabByFieldname(frm, "more_info_tab");
    if (!$tab.length) return false;

    resetMoreInfoTab(frm, $tab);
    $tab.addClass("erpw-so-moreinfo-tab");

    [
      "opportunity",
      "supplier_quotation",
      "referral_sales_partner",
      "language",
      "letter_head",
      "select_print_heading",
      "group_same_items",
      "incoterm",
      "named_place",
      "utm_campaign",
      "utm_source",
      "utm_medium",
      "utm_content",
    ].forEach((fieldname) => toggleField(frm, fieldname, true));
    toggleField(frm, "order_lost_reason", String(frm.doc.status || "") === "Lost" || hasMeaningfulValue(frm.doc.order_lost_reason));
    toggleField(frm, "lost_reasons", String(frm.doc.status || "") === "Lost" || (Array.isArray(frm.doc.lost_reasons) && frm.doc.lost_reasons.length > 0));

    const configs = [
      {
        key: "context",
        fieldname: "opportunity",
        title: "Commercial Context",
        note: "Opportunity, source quotation, referral, and closure context around this quote.",
      },
      {
        key: "print",
        fieldname: "language",
        title: "Document Output",
        note: "Print language and presentation controls for customer-facing quotation output.",
      },
      {
        key: "controls",
        fieldname: "incoterm",
        title: "Market Context",
        note: "Incoterm, named place, and campaign context supporting this quotation.",
      },
    ];

    const $stack = ensureMoreInfoStack($tab);
    const seen = new Set();

    configs.forEach((config) => {
      const $section = getSectionForField(frm, config.fieldname);
      if (!$section || !$section.length) return;

      const sectionNode = $section.get(0);
      if (seen.has(sectionNode)) return;
      seen.add(sectionNode);

      const presentation = getQuotationMoreInfoSectionPresentation(frm, config.key);
      $section
        .addClass(`erpw-so-moreinfo-section erpw-so-moreinfo-section-${config.key}`)
        .toggleClass("erpw-so-moreinfo-section-wide", !!presentation.wide)
        .toggleClass("erpw-so-moreinfo-section-priority", !!presentation.priority)
        .toggleClass("erpw-so-moreinfo-section-quiet", !!presentation.quiet);

      ensureMoreInfoSectionHeader($section, config.title, config.note);
      applyMoreInfoHeaderState($section, presentation);
      applyMoreInfoSectionBodyState(frm, $section, presentation);
      const shouldShow = !presentation.hidden;
      $section.toggle(shouldShow);
      if (shouldShow) {
        $stack.append($section);
      }

      if (config.key === "context") {
        moveFieldIntoSectionBodyIfNeeded(frm, "referral_sales_partner", $section, "quotation-moreinfo");
      }
    });

    $tab.children(".form-section").not($stack.children(".form-section")).each((_, element) => {
      $(element).addClass("erpw-so-moreinfo-hidden-source").hide();
    });

    if (typeof childPageSections.balanceMoreInfoStack === "function") {
      childPageSections.balanceMoreInfoStack($stack);
    }

    if (frm.layout && typeof frm.layout.refresh_sections === "function") {
      frm.layout.refresh_sections();
    }
    return seen.size > 0;
  }

  function renderCommercialSummary(frm) {
    const $itemsSection = getSectionForField(frm, "items");
    if (!$itemsSection || !$itemsSection.length) return;

    $itemsSection.find(".erpw-so-inline-summary").remove();

    if (typeof childPageDetails.ensureCriticalStyles === "function") {
      childPageDetails.ensureCriticalStyles();
    }

    const chips = [];
    const daysToExpiry = getQuotationDaysToExpiry(frm);
    const workflowLabel = String(frm.doc.workflow_state || "").trim();
    const hasTaxes = !Number.isNaN(Number(frm.doc.total_taxes_and_charges || 0))
      && Math.abs(Number(frm.doc.total_taxes_and_charges || 0)) > 0.0001;

    if (workflowLabel && /pending/i.test(workflowLabel)) {
      chips.push({
        label: workflowLabel,
        tone: "pending",
      });
    }

    if (Number.isFinite(daysToExpiry)) {
      if (daysToExpiry < 0) {
        chips.push({
          label: formatDaysToExpiry(daysToExpiry),
          tone: "blocker",
        });
      } else if (daysToExpiry <= 3) {
        chips.push({
          label: formatDaysToExpiry(daysToExpiry),
          tone: "attention",
        });
      }
    }

    if (!hasTaxes) {
      chips.push({
        label: "No tax rows",
        tone: "neutral",
      });
    }

    const metrics = [
      {
        label: "Quantity",
        value: hasMeaningfulValue(frm.doc.total_qty) ? String(frm.doc.total_qty) : "--",
        className: "erpw-so-inline-metric-qty",
      },
      {
        label: "Items Total",
        value: formatMoney(frm.doc.total, frm.doc.currency),
        className: "erpw-so-inline-metric-items-total",
      },
      {
        label: "Taxes",
        value: formatMoney(frm.doc.total_taxes_and_charges, frm.doc.currency),
        className: "erpw-so-inline-metric-taxes",
      },
      {
        label: "Grand Total",
        value: formatMoney(frm.doc.grand_total, frm.doc.currency),
        className: "erpw-so-inline-metric-grand",
      },
    ];

    if (typeof childPageSummaries.renderInlineSummary === "function") {
      childPageSummaries.renderInlineSummary($itemsSection, {
        chips,
        metrics: metrics.map((metric) => ({
          className: metric.className || "",
          label: metric.label,
          value: metric.value,
        })),
        note: "Read quoted value, approval pressure, and tax posture here while ERP totals stay authoritative.",
        removeSelector: ".erpw-so-inline-summary",
        summaryClass: "erpw-so-inline-summary erpw-child-inline-summary-soft",
        title: "Commercial Posture",
      });
      return;
    }

    const $summary = $(`
      <div class="erpw-so-inline-summary erpw-child-inline-summary-soft">
        <div class="erpw-so-inline-summary-head">
          <div class="erpw-so-inline-summary-title">Commercial Posture</div>
          <div class="erpw-child-subtitle erpw-child-inline-summary-note">Read quoted value, approval pressure, and tax posture here while ERP totals stay authoritative.</div>
          ${chips.length ? `
            <div class="erpw-child-chip-row">
              ${chips.map((chip) => `
                <span class="erpw-child-chip ${escapeHtml(chip.tone || "neutral")}">${escapeHtml(chip.label)}</span>
              `).join("")}
            </div>
          ` : ""}
        </div>
        <div class="erpw-so-inline-summary-grid">
          ${metrics.map((metric) => `
            <div class="erpw-so-inline-metric ${escapeHtml(metric.className || "")}">
              <div class="erpw-so-inline-metric-label">${escapeHtml(metric.label)}</div>
              <div class="erpw-so-inline-metric-value">${escapeHtml(metric.value)}</div>
            </div>
          `).join("")}
        </div>
      </div>
    `);

    const $gridField = $itemsSection.find(".grid-field").first();
    if ($gridField.length) {
      $gridField.after($summary);
    } else {
      $itemsSection.append($summary);
    }
  }

  function renderDetailWorkspace(frm) {
    const $itemsSection = getSectionForField(frm, "items");
    if (!$itemsSection || !$itemsSection.length) return false;

    const $currentWorkspace = $itemsSection.closest(".erpw-child-detail-workspace");
    const $snapshot = $currentWorkspace.length
      ? $currentWorkspace.prev(".erpw-child-detail-snapshot").first()
      : $itemsSection.prev(".erpw-child-detail-snapshot").first();
    const $taxesSection = getSectionForField(frm, "taxes");
    const $totalsSection = getSectionForField(frm, "grand_total") || getSectionForField(frm, "base_grand_total");

    return Boolean(ensureSharedDetailWorkspace([
      $itemsSection,
      $taxesSection,
      $totalsSection,
    ], {
      className: "erpw-child-detail-workspace",
      insertAfter: $snapshot,
      scope: "quotation",
    }).length);
  }

  function getQuotationSnapshotReviewMetric(frm) {
    const workflowLabel = String(frm.doc.workflow_state || "").trim();
    if (workflowLabel) {
      return {
        label: "Review Stage",
        value: workflowLabel,
      };
    }

    const orderType = String(frm.doc.order_type || "").trim();
    if (orderType) {
      return {
        label: "Order Type",
        value: orderType,
      };
    }

    return {
      label: "Commercial State",
      value: String(frm.doc.status || "Draft").trim() || "Draft",
    };
  }

  function getQuotationTopDetailsSection(frm) {
    const section = getSectionForField(frm, "quotation_to")
      || getSectionForField(frm, "party_name")
      || getSectionForField(frm, "transaction_date")
      || getSectionForField(frm, "valid_till");

    return section && section.length ? section : null;
  }

  function renderDetailsSnapshot(frm) {
    const $topSection = getQuotationTopDetailsSection(frm);
    const $itemsSection = getSectionForField(frm, "items");
    if (!$itemsSection || !$itemsSection.length) return false;

    $itemsSection.closest(".erpw-child-detail-workspace").prev(".erpw-child-detail-snapshot").first().remove();
    $itemsSection.prev(".erpw-child-detail-snapshot").first().remove();

    const reviewPosture = isQuotationReviewPosture(frm);
    if (!$topSection || !$topSection.length || !reviewPosture) {
      setManagedSectionVisibility($topSection, true, "erpwq-details-hidden-source");
      return false;
    }

    if (typeof childPageDetails.renderDetailSnapshot !== "function") {
      setManagedSectionVisibility($topSection, true, "erpwq-details-hidden-source");
      return false;
    }

    const daysToExpiry = getQuotationDaysToExpiry(frm);
    const workflowLabel = String(frm.doc.workflow_state || "").trim();
    let statusText = workflowLabel || String(frm.doc.status || "Draft").trim() || "Draft";
    let statusTone = /pending/i.test(workflowLabel) ? "attention" : "active";

    if (Number.isFinite(daysToExpiry) && daysToExpiry < 0) {
      statusText = "Expired";
      statusTone = "attention";
    } else if (Number.isFinite(daysToExpiry) && daysToExpiry <= 3) {
      statusText = "Expiring soon";
      statusTone = "attention";
    } else if (String(frm.doc.status || "") === "Ordered") {
      statusText = "Converted";
    }

    childPageDetails.renderDetailSnapshot($itemsSection, {
      kicker: "Quote Snapshot",
      metrics: [
        {
          label: "Customer",
          value: frm.doc.customer_name || frm.doc.party_name || "--",
        },
        {
          label: "Quote Date",
          value: formatDateLabel(frm.doc.transaction_date),
        },
        {
          label: "Valid Till",
          value: formatDateLabel(frm.doc.valid_till),
        },
        getQuotationSnapshotReviewMetric(frm),
      ],
      note: "Read review posture, validity, and customer context here, then work the native quotation lines below.",
      removeSelector: ".erpw-child-detail-snapshot",
      snapshotClass: "erpw-child-detail-snapshot",
      statusText,
      statusTone,
    });

    setManagedSectionVisibility($topSection, false, "erpwq-details-hidden-source");
    return true;
  }

  function renderItemsSectionHeader(frm) {
    const $itemsSection = getSectionForField(frm, "items");
    if (!$itemsSection || !$itemsSection.length) return false;

    if (typeof childPageDetails.renderSectionHeader !== "function") {
      return false;
    }

    const items = Array.isArray(frm.doc.items) ? frm.doc.items : [];
    childPageDetails.renderSectionHeader($itemsSection, {
      headerClass: "erpw-child-section-header",
      note: "Keep quotation lines native here, then use the summary below for quoted value, tax posture, and approval reading.",
      removeSelector: ".erpw-child-section-header",
      statusText: `${items.length || 0} ${items.length === 1 ? "line" : "lines"}`,
      statusTone: "neutral",
      title: "Quoted Lines",
    });

    return true;
  }

  function updateSupportToggleLabel($shell) {
    const $button = $shell.find(".erpw-so-support-toggle");
    if (!$button.length) return;
    const expanded = $shell.hasClass("is-activity-expanded");
    $button.attr("aria-expanded", expanded ? "true" : "false");
    $button.find(".erpw-so-support-toggle-text").text(expanded ? "Collapse Activity" : "Show Full Activity");
  }

  function updateSupportNote($footer, commentCount, activityCount, previewCount) {
    const note = `Comments ${commentCount} • Activity ${activityCount}.`;
    const suffix = activityCount > previewCount
      ? ` Showing ${previewCount} by default.`
      : " Full activity is already visible.";
    $footer.find(".erpw-so-support-note").text(note + suffix);
  }

  function applyActivityPreview($footer) {
    const $timeline = $footer.find(".new-timeline").first();
    if (!$timeline.length) return false;

    const $timelineItems = $timeline.find(".timeline-items").last();
    if (!$timelineItems.length) return false;

    const $items = $timelineItems.children(".timeline-item");
    if (!$items.length) return false;

    $items.removeClass("erpw-so-activity-hidden");
    const previewLimit = 3;
    const hasOverflow = $items.length > previewLimit;
    const expanded = $footer.hasClass("is-activity-expanded");

    $items.each((index, element) => {
      if (index >= previewLimit && !expanded) {
        $(element).addClass("erpw-so-activity-hidden");
      }
    });

    $timeline.find(".show-all-activity").hide();
    $footer.toggleClass("has-activity-overflow", hasOverflow);
    return {
      activityCount: $items.length,
      previewCount: Math.min(previewLimit, $items.length),
      hasOverflow,
    };
  }

  function ensureSupportHead($footer) {
    if (!$footer || !$footer.length) return $();

    let $head = $footer.find(".erpw-so-support-head").first();
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
      $footer.prepend($head);
    }

    return $head;
  }

  function enhanceSupportArea(frm) {
    if (typeof childPageSupport.enhanceSupportArea === "function") {
      return childPageSupport.enhanceSupportArea(frm);
    }

    const $wrapper = $(frm.wrapper || frm.$wrapper || []);
    if (!$wrapper.length) return false;

    const $footer = $wrapper.find(".form-footer").first();
    if (!$footer.length) return false;

    $footer.addClass("erpw-so-support-shell");
    $footer.find(".comment-box").addClass("erpw-so-comment-block");
    $footer.find(".new-timeline, .timeline").addClass("erpw-so-timeline-block");

    const $head = ensureSupportHead($footer);
    $head.find(".erpw-so-support-toggle").off(".erpwSupportToggle").on("click.erpwSupportToggle", () => {
      $footer.toggleClass("is-activity-expanded");
      const preview = applyActivityPreview($footer);
      if (preview) {
        const docinfo = frm.get_docinfo ? frm.get_docinfo() : {};
        const commentCount = Array.isArray(docinfo.comments) ? docinfo.comments.length : 0;
        updateSupportNote($footer, commentCount, preview.activityCount, preview.previewCount);
      }
      updateSupportToggleLabel($footer);
    });

    const docinfo = frm.get_docinfo ? frm.get_docinfo() : {};
    const commentCount = Array.isArray(docinfo.comments) ? docinfo.comments.length : 0;

    if (!$footer.data("erpwActivityInit")) {
      $footer.removeClass("is-activity-expanded");
      $footer.data("erpwActivityInit", 1);
    }
    const preview = applyActivityPreview($footer);
    if (preview) {
      updateSupportNote($footer, commentCount, preview.activityCount, preview.previewCount);
    }
    updateSupportToggleLabel($footer);
    $footer.find(".erpw-so-support-toggle").toggle($footer.hasClass("has-activity-overflow"));
    return true;
  }

  function cleanSidebarUtilityRail(frm) {
    if (typeof childPageSidebar.cleanSidebarUtilityRail === "function") {
      return childPageSidebar.cleanSidebarUtilityRail(frm);
    }

    const $wrapper = $(frm.wrapper || frm.$wrapper || []);
    const $sidebar = $(frm.page && frm.page.sidebar ? frm.page.sidebar : $wrapper.find(".form-sidebar").parent());
    if (!$sidebar.length) return false;

    const $metaSection = $sidebar.find(".sidebar-section.text-muted.border-top.pt-3").first();
    if (!$metaSection.length) return false;

    $metaSection.addClass("erpw-so-sidebar-meta-hidden").hide();
    return true;
  }

  function enhanceWorkflowReadonlyBanner(frm) {
    if (typeof childPageSupport.enhanceWorkflowReadonlyBanner === "function") {
      return childPageSupport.enhanceWorkflowReadonlyBanner(frm, {
        title: "Workflow review is active",
        note: "Continue from the toolbar when commercial review is ready to proceed.",
      });
    }

    const $root = $(frm.page && frm.page.main ? frm.page.main : frm.$wrapper || []);
    if (!$root.length) return false;

    const $container = $root.find(".form-message-container").first();
    if (!$container.length) return false;

    const $messages = $container.find(".form-message");
    if (!$messages.length) return false;

    const $workflowMessage = $messages.filter((_, element) => {
      const text = $.trim($(element).text() || "");
      return text === "This form is not editable due to a Workflow.";
    }).first();

    if (!$workflowMessage.length) return false;

    $container.addClass("erpw-so-workflow-banner-container");
    $workflowMessage
      .removeClass("blue yellow orange green red white")
      .addClass("white erpw-so-workflow-banner-shell");

    if (!$workflowMessage.find(".erpw-so-workflow-banner").length) {
      $workflowMessage.html(`
        <div class="erpw-so-workflow-banner">
          <span class="erpw-so-workflow-banner-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24">
              <path d="M8 10V8a4 4 0 1 1 8 0v2M7.5 10h9a1 1 0 0 1 1 1v7a1 1 0 0 1-1 1h-9a1 1 0 0 1-1-1v-7a1 1 0 0 1 1-1z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </span>
          <div class="erpw-so-workflow-banner-copy">
            <div class="erpw-so-workflow-banner-title">Workflow review is active</div>
            <div class="erpw-so-workflow-banner-note">Continue from the toolbar when commercial review is ready to proceed.</div>
          </div>
        </div>
      `);
    }

    return true;
  }

  function connectionGroupIconMarkup(key) {
    const icons = {
      conversion: `
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M7 3.5h7l4 4v13H7zM14 3.5v4h4M10 12h5M10 15.5h5M10 19h3" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      `,
      relationship: `
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M12 12a3.5 3.5 0 1 0 0-7a3.5 3.5 0 0 0 0 7zm-6 7a6 6 0 0 1 12 0" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      `,
    };

    return icons[key] || icons.relationship;
  }

  function connectionDocIconMarkup(doctype) {
    const icons = {
      "Sales Order": actionIconMarkup("sales_order"),
      "Delivery Note": actionIconMarkup("delivery"),
      "Sales Invoice": actionIconMarkup("invoice"),
      Customer: actionIconMarkup("customer"),
      Lead: actionIconMarkup("customer"),
      Opportunity: actionIconMarkup("opportunity"),
    };

    return icons[doctype] || actionIconMarkup("sales_order");
  }

  function getConnectionDocStatus(config) {
    if (config.count > 0) {
      return { label: `${config.count} linked`, tone: "active" };
    }
    if (config.required === false) {
      return { label: "Optional", tone: "neutral" };
    }
    return { label: config.emptyLabel || "Not linked", tone: config.emptyTone || "attention" };
  }

  function getConnectionGroupStatus(items) {
    const linkedTotal = Array.isArray(items)
      ? items.reduce((sum, item) => sum + Number(item.count || 0), 0)
      : 0;

    return linkedTotal
      ? { label: `${linkedTotal} linked`, tone: "active" }
      : { label: "Review", tone: "attention" };
  }

  function buildConnectionsGroups(data) {
    const summary = data.summary || {};
    const linked = data.linked_documents || {};
    const party = getPartyLink(data);

    const chainItems = [
      {
        doctype: "Sales Order",
        title: "Sales Order",
        note: linked.sales_orders && linked.sales_orders.length
          ? "Downstream order conversion from this quotation."
          : "No downstream sales order has been created from this quotation yet.",
        count: Array.isArray(linked.sales_orders) ? linked.sales_orders.length : 0,
        emptyLabel: "Not converted",
        emptyTone: "attention",
        onOpen: linked.sales_orders && linked.sales_orders.length
          ? () => {
            if (linked.sales_orders.length === 1) {
              routeToDoc("Sales Order", linked.sales_orders[0].name);
              return;
            }
            routeToList("Sales Order", { name: ["in", linked.sales_orders.map((row) => row.name)] });
          }
          : null,
      },
      {
        doctype: "Delivery Note",
        title: "Delivery Note",
        note: linked.deliveries && linked.deliveries.length
          ? "Fulfillment activity already linked through downstream sales orders."
          : "Delivery activity will appear only after quotation conversion and fulfillment work.",
        count: Array.isArray(linked.deliveries) ? linked.deliveries.length : 0,
        emptyLabel: "No delivery",
        emptyTone: "neutral",
        required: false,
        onOpen: linked.deliveries && linked.deliveries.length
          ? () => {
            if (linked.deliveries.length === 1) {
              routeToDoc("Delivery Note", linked.deliveries[0].name);
              return;
            }
            routeToList("Delivery Note", { name: ["in", linked.deliveries.map((row) => row.name)] });
          }
          : null,
      },
      {
        doctype: "Sales Invoice",
        title: "Sales Invoice",
        note: linked.invoices && linked.invoices.length
          ? "Billing activity already linked through downstream sales orders."
          : "Invoice activity will appear after downstream order processing reaches billing.",
        count: Array.isArray(linked.invoices) ? linked.invoices.length : 0,
        emptyLabel: "No invoice",
        emptyTone: "neutral",
        required: false,
        onOpen: linked.invoices && linked.invoices.length
          ? () => {
            if (linked.invoices.length === 1) {
              routeToDoc("Sales Invoice", linked.invoices[0].name);
              return;
            }
            routeToList("Sales Invoice", { name: ["in", linked.invoices.map((row) => row.name)] });
          }
          : null,
      },
    ];

    const relationshipItems = [
      {
        doctype: party && party.doctype ? party.doctype : summary.party_doctype || "Customer",
        title: party ? getPartyLabel(party.doctype) : getPartyLabel(summary.party_doctype),
        note: party
          ? "Commercial party record linked to this quotation."
          : "No party is linked yet.",
        count: party ? 1 : 0,
        emptyLabel: "Not linked",
        emptyTone: "attention",
        onOpen: party ? () => routeToDoc(party.doctype, party.name) : null,
      },
      {
        doctype: "Opportunity",
        title: "Opportunity",
        note: linked.opportunity && linked.opportunity.name
          ? "Opportunity context linked to this quotation."
          : "No originating opportunity is linked to this quotation.",
        count: linked.opportunity && linked.opportunity.name ? 1 : 0,
        emptyLabel: "Not linked",
        emptyTone: "neutral",
        required: false,
        onOpen: linked.opportunity && linked.opportunity.name ? () => routeToDoc("Opportunity", linked.opportunity.name) : null,
      },
    ];

    return [
      {
        key: "conversion",
        title: "Commercial Chain",
        note: "Track downstream conversion and order-to-cash movement from this quotation.",
        iconMarkup: connectionGroupIconMarkup("conversion"),
        status: getConnectionGroupStatus(chainItems),
        items: chainItems.map((item) => ({
          doctype: item.doctype,
          title: item.title,
          note: item.note,
          iconMarkup: connectionDocIconMarkup(item.doctype),
          status: getConnectionDocStatus(item),
          actions: item.onOpen ? [
            {
              label: "Open linked",
              run: item.onOpen,
            },
          ] : [],
        })),
      },
      {
        key: "relationship",
        title: "Relationship Context",
        note: "Keep the commercial relationship and pre-sales context visible together.",
        iconMarkup: connectionGroupIconMarkup("relationship"),
        status: getConnectionGroupStatus(relationshipItems),
        items: relationshipItems.map((item) => ({
          doctype: item.doctype,
          title: item.title,
          note: item.note,
          iconMarkup: connectionDocIconMarkup(item.doctype),
          status: getConnectionDocStatus(item),
          actions: item.onOpen ? [
            {
              label: "Open linked",
              run: item.onOpen,
            },
          ] : [],
        })),
      },
    ];
  }

  function renderConnectionsWorkspace(frm, data) {
    const $tab = getTabByFieldname(frm, "connections_tab");
    if (!$tab.length) return false;
    if (typeof childPageConnections.renderCardWorkspace !== "function") {
      markFeatureMissing(frm, "connection_workspace", { reason: "runtime_unavailable" });
      return false;
    }

    const groups = buildConnectionsGroups(data);
    const rendered = childPageConnections.renderCardWorkspace(frm, {
      featureKey: "connection_workspace",
      model: {
        groups,
      },
      mount: {
        cleanupRoot: $tab,
        cleanupSelector: ".erpwq-quotation-connections, .erpw-so-connections-workspace",
        insert: ($workspace) => {
          $tab.prepend($workspace);
        },
      },
      theme: {
        namespace: ".erpwQuotationConnectionWorkspace",
        workspaceClassName: "erpw-so-connections-workspace",
        pendingNoteClass: "erpw-so-connections-pending-note",
        groupClass: "erpw-so-connection-primary-group",
        groupHeadClass: "erpw-so-connection-primary-head",
        groupSummaryClass: "erpw-so-connection-primary-summary",
        groupIconClass: "erpw-so-connection-primary-icon",
        groupCopyClass: "erpw-so-connection-primary-copy",
        groupTitleClass: "erpw-so-connection-primary-title",
        groupNoteClass: "erpw-so-connection-primary-note",
        groupStatusClass: "erpw-so-connection-primary-status",
        itemsClass: "erpw-so-connection-primary-grid",
        itemClass: "erpw-so-connection-doc-card",
        itemHeadClass: "erpw-so-connection-doc-head",
        itemMainClass: "erpw-so-connection-doc-main",
        itemIconClass: "erpw-so-connection-doc-icon",
        itemCopyClass: "erpw-so-connection-doc-copy",
        itemTitleClass: "erpw-so-connection-doc-title",
        itemNoteClass: "erpw-so-connection-doc-note",
        itemStatusClass: "erpw-so-connection-doc-status",
        itemActionsClass: "erpw-so-connection-doc-actions",
        actionBaseClass: "erpw-so-connection-action",
        actionToneClassMap: {
          primary: "erpw-so-connection-action-primary",
          secondary: "erpw-so-connection-action-secondary",
          tertiary: "erpw-so-connection-action-tertiary",
        },
        secondaryShellClass: "erpw-so-connections-secondary-shell",
        secondaryHeadClass: "erpw-so-connections-secondary-head",
        secondaryIconClass: "erpw-so-connections-secondary-icon",
        secondaryCopyClass: "erpw-so-connections-secondary-copy",
        secondaryTitleClass: "erpw-so-connections-secondary-title",
        secondaryNoteClass: "erpw-so-connections-secondary-note",
        secondaryRowsClass: "erpw-so-connections-secondary-rows",
        secondaryRowClass: "erpw-so-connections-secondary-row",
        secondaryRowIconClass: "erpw-so-connections-secondary-row-icon",
        secondaryRowCopyClass: "erpw-so-connections-secondary-row-copy",
        secondaryRowTitleClass: "erpw-so-connections-secondary-row-title",
        secondaryRowNoteClass: "erpw-so-connections-secondary-row-note",
        loadingShellClass: "erpw-so-connections-loading-shell",
        loadingTitleClass: "erpw-so-connections-loading-title",
        loadingNoteClass: "erpw-so-connections-loading-note",
        emptyShellClass: "erpw-so-connections-empty",
        emptyTitleClass: "erpw-so-connections-empty-title",
        emptyNoteClass: "erpw-so-connections-empty-note",
      },
    });

    const $nativeNodes = $tab.find(".form-links, .form-dashboard-section, .form-documents, .document-link")
      .add($tab.children(".form-section"));

    if (!rendered) {
      $nativeNodes.removeClass("erpwq-quotation-connections-native").show();
      return false;
    }

    $nativeNodes.addClass("erpwq-quotation-connections-native").hide();
    return true;
  }

  function bindTabEnhancers(frm) {
    bindRuntimeTabEnhancers(frm, {
      namespace: ".erpwQuotationTabs",
      fastKey: "quotation_tab_enhancers_fast",
      lateKey: "quotation_tab_enhancers_late",
      fastDelay: 0,
      lateDelay: 180,
      run: () => {
        enhanceAddressContactTab(frm);
        enhanceTermsTab(frm);
        enhanceMoreInfoTab(frm);
        renderConnectionsWorkspace(frm, frm.__erpwQuotationContext || draftContext(frm));
      },
    });
  }

  function enhanceFormBody(frm) {
    if (!frm || !frm.fields_dict) return;

    const $root = getFormRoot(frm);
    if ($root.length) {
      $root.addClass("erpw-so-form-enhanced erpwq-quotation-form-enhanced");
    }

    bindTabEnhancers(frm);

    markSection(frm, "party_name", "erpw-so-section-primary erpw-so-section-basics");
    markSection(frm, "currency", "erpw-so-section-secondary erpw-so-section-pricing");
    markSection(frm, "items", "erpw-so-section-primary erpw-so-section-items");
    markSection(frm, "taxes", "erpw-so-section-secondary erpw-so-section-taxes");
    markSection(frm, "tax_category", "erpw-so-section-secondary erpw-so-section-taxes");
    markSection(frm, "grand_total", "erpw-so-section-summary");
    markSection(frm, "apply_discount_on", "erpw-so-section-quiet erpw-so-section-discount");

    [
      "workflow_state",
      "naming_series",
      "amended_from",
      "customer_name",
      "contact_display",
      "base_in_words",
      "in_words",
      "has_unit_price_items",
      "disable_rounded_total",
    ].forEach((fieldname) => toggleField(frm, fieldname, false));

    const sameCurrency = usesCompanyCurrencyOnly(frm);
    [
      "total_qty",
      "total",
      "net_total",
      "total_taxes_and_charges",
      "grand_total",
      "base_total",
      "base_net_total",
      "base_total_taxes_and_charges",
      "base_grand_total",
      "base_rounding_adjustment",
      "base_rounded_total",
      "base_discount_amount",
    ].forEach((fieldname) => toggleField(frm, fieldname, !sameCurrency));

    toggleField(frm, "price_list_currency", !sameCurrency && hasMeaningfulValue(frm.doc.price_list_currency));
    toggleField(frm, "rounding_adjustment", hasMeaningfulValue(frm.doc.rounding_adjustment));
    toggleField(frm, "rounded_total", hasMeaningfulValue(frm.doc.rounded_total) && hasMeaningfulValue(frm.doc.rounding_adjustment));
    toggleField(frm, "coupon_code", hasMeaningfulValue(frm.doc.coupon_code));
    toggleField(frm, "referral_sales_partner", hasMeaningfulValue(frm.doc.referral_sales_partner));
    toggleField(frm, "competitors", Array.isArray(frm.doc.competitors) && frm.doc.competitors.length > 0);
    toggleField(frm, "supplier_quotation", hasMeaningfulValue(frm.doc.supplier_quotation));
    toggleField(frm, "order_lost_reason", String(frm.doc.status || "") === "Lost" || hasMeaningfulValue(frm.doc.order_lost_reason));
    toggleField(frm, "lost_reasons", String(frm.doc.status || "") === "Lost" || (Array.isArray(frm.doc.lost_reasons) && frm.doc.lost_reasons.length > 0));

    const showDiscount = hasQuotationDiscountSignal(frm);
    const showTotalsDetail = [
      "rounding_adjustment",
      "rounded_total",
    ].some((fieldname) => hasMeaningfulValue(frm.doc[fieldname]));
    const showPricing = shouldShowPricingSection(frm);
    const showScanSetup = [
      "scan_barcode",
      "last_scanned_warehouse",
    ].some((fieldname) => hasMeaningfulValue(frm.doc[fieldname]));
    const hasTaxSignal = (Array.isArray(frm.doc.taxes) && frm.doc.taxes.length > 0)
      || (!Number.isNaN(Number(frm.doc.total_taxes_and_charges || 0)) && Math.abs(Number(frm.doc.total_taxes_and_charges || 0)) > 0.0001);
    const showTaxSection = hasTaxSignal || !isQuotationReviewPosture(frm);
    toggleSection(frm, "currency", showPricing);
    setManagedSectionVisibility(
      getSectionForField(frm, "selling_price_list") || getSectionForField(frm, "currency"),
      showPricing,
      "erpwq-details-hidden-source"
    );
    toggleSection(frm, "apply_discount_on", showDiscount);
    toggleSection(frm, "pricing_rules", Array.isArray(frm.doc.pricing_rules) && frm.doc.pricing_rules.length > 0);
    toggleSection(frm, "total_qty", false);
    toggleSection(frm, "grand_total", showTotalsDetail);
    toggleField(frm, "scan_barcode", showScanSetup);
    toggleField(frm, "last_scanned_warehouse", showScanSetup && hasMeaningfulValue(frm.doc.last_scanned_warehouse));
    const $taxesSection = getSectionForField(frm, "taxes");
    const $taxCategorySection = getSectionForField(frm, "tax_category");
    setManagedSectionVisibility($taxesSection, showTaxSection, "erpwq-details-hidden-source");
    if (!$taxCategorySection || !$taxesSection || !$taxCategorySection.is($taxesSection)) {
      setManagedSectionVisibility($taxCategorySection, showTaxSection, "erpwq-details-hidden-source");
    }

    renderDetailsSnapshot(frm);
    renderItemsSectionHeader(frm);
    renderCommercialSummary(frm);
    renderDetailWorkspace(frm);
    runRetriedEnhancers(frm, [
      {
        fastKey: "quotation_address_retry_fast",
        lateKey: "quotation_address_retry_late",
        fastDelay: 420,
        lateDelay: 980,
        run: () => enhanceAddressContactTab(frm),
      },
      {
        fastKey: "quotation_terms_retry_fast",
        lateKey: "quotation_terms_retry_late",
        fastDelay: 420,
        lateDelay: 980,
        run: () => enhanceTermsTab(frm),
      },
      {
        fastKey: "quotation_moreinfo_retry_fast",
        lateKey: "quotation_moreinfo_retry_late",
        fastDelay: 420,
        lateDelay: 980,
        run: () => enhanceMoreInfoTab(frm),
      },
      {
        fastKey: "quotation_sidebar_retry_fast",
        lateKey: "quotation_sidebar_retry_late",
        fastDelay: 420,
        lateDelay: 980,
        run: () => cleanSidebarUtilityRail(frm),
      },
      {
        fastKey: "quotation_support_retry_fast",
        lateKey: "quotation_support_retry_late",
        fastDelay: 420,
        lateDelay: 980,
        run: () => enhanceSupportArea(frm),
      },
      {
        fastKey: "quotation_workflow_banner_retry_fast",
        lateKey: "quotation_workflow_banner_retry_late",
        fastDelay: 220,
        lateDelay: 760,
        run: () => enhanceWorkflowReadonlyBanner(frm),
      },
      {
        fastKey: "quotation_connections_retry_fast",
        lateKey: "quotation_connections_retry_late",
        fastDelay: 420,
        lateDelay: 980,
        run: () => renderConnectionsWorkspace(frm, frm.__erpwQuotationContext || draftContext(frm)),
      },
    ]);
  }

  function renderShell(frm, data) {
    const summary = data.summary || {};
    const linked = data.linked_documents || {};
    const support = data.support || {};
    const $shell = getShell(frm);
    const actions = actionConfig(frm, data);
    const actionIndexes = actions.map((action, idx) => ({ ...action, idx }));
    const primaryActions = actionIndexes.filter((action) => action.variant === "primary");
    const secondaryActions = actionIndexes.filter((action) => action.variant !== "primary");
    const sparseActions = actionIndexes.length <= 3;
    const validityState = String(summary.validity_state || "");
    const validityChipClass = validityState === "expired"
      ? "blocker"
      : validityState === "expiring_soon"
        ? "attention"
        : validityState === "inactive"
          ? "pending"
          : "good";
    const workflowPending = String(summary.workflow_state || "").includes("Pending");
    const converted = Number(summary.sales_order_count || 0) > 0;
    const conversionValue = converted
      ? formatCountTitle("Sales Order", "Sales Orders", Number(summary.sales_order_count || 0))
      : "Not converted";
    const conversionMeta = converted
      ? `${Number(summary.delivery_count || 0)} deliveries • ${Number(summary.invoice_count || 0)} invoices`
      : linked.opportunity && linked.opportunity.name
        ? "Opportunity context linked"
        : "No downstream sales order yet";
    const approvalPanelLabel = workflowPending ? "Current Gate" : "Approval State";
    const approvalPanelValue = summary.workflow_state || summary.status || "Draft";
    const commercialWindowNote = converted
      ? "Downstream order activity has already started from this quotation."
      : validityState === "expired"
        ? "Validity expired. Reconfirm before customer commitment or conversion."
        : workflowPending
          ? "Await approval before making a final customer commitment."
          : "Quotation is still active for commercial follow-through.";
    const conversionMetrics = [
      {
        value: Number(summary.sales_order_count || 0),
        label: "Sales Orders",
      },
      {
        value: Number(summary.delivery_count || 0),
        label: "Deliveries",
      },
      {
        value: Number(summary.invoice_count || 0),
        label: "Invoices",
      },
      {
        value: Number(support.open_task_count || 0),
        label: "Follow-Ups",
      },
    ];
    const hasConversionSignal = conversionMetrics.some((metric) => Number(metric.value || 0) > 0);
    const statusLabel = String(summary.status || "Draft").trim() || "Draft";
    const workflowLabel = String(summary.workflow_state || "").trim();
    const primaryChipLabel = workflowPending && workflowLabel ? workflowLabel : statusLabel;
    const showWorkflowChip = !!(
      workflowLabel &&
      workflowLabel.toLowerCase() !== primaryChipLabel.toLowerCase() &&
      workflowLabel.toLowerCase() !== statusLabel.toLowerCase()
    );
    const summaryChips = [
      { label: primaryChipLabel, tone: workflowPending ? "pending" : "approved" },
      showWorkflowChip ? { label: workflowLabel, tone: "good" } : null,
      summary.valid_till ? { label: formatDaysToExpiry(summary.days_to_expiry), tone: validityChipClass } : null,
      converted ? { label: formatCountTitle("Sales Order", "Sales Orders", Number(summary.sales_order_count || 0)), tone: "approved" } : null,
    ].filter(Boolean);
    const summaryFacts = [
      {
        className: "erpw-child-fact-grand",
        label: "Grand Total",
        value: formatMoney(summary.grand_total, summary.currency),
      },
      {
        className: "erpw-child-fact-validity",
        label: "Valid Till",
        value: formatDateLabel(summary.valid_till),
        meta: formatDaysToExpiry(summary.days_to_expiry),
      },
      {
        className: "erpw-child-fact-conversion",
        label: "Conversion",
        value: conversionValue,
        meta: conversionMeta,
      },
    ];
    const guidanceCards = [
      {
        chipLabel: "Priority",
        className: "erpw-child-guidance-card-primary",
        iconMarkup: '<svg viewBox="0 0 24 24"><path d="M6 12h12M13 7l5 5l-5 5" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/></svg>',
        text: support.next_action || "Continue commercial follow-through.",
        title: "Next Action",
      },
      {
        chipClass: "erpw-child-guidance-chip-secondary",
        chipLabel: "Communication",
        className: "erpw-child-guidance-card-secondary",
        iconMarkup: '<svg viewBox="0 0 24 24"><path d="M12 13a3.5 3.5 0 1 0 0-7a3.5 3.5 0 0 0 0 7zm-6 6a6 6 0 0 1 12 0" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/></svg>',
        text: support.customer_response_hint || "Use the latest approval and validity context before customer confirmation.",
        title: "Customer Response",
      },
    ];
    const extraSectionsHtml = `
      <section class="erpw-child-card erpwq-quotation-review-band">
        <article class="erpwq-quotation-review-main">
          <div class="erpwq-quotation-review-title">Commercial Readiness</div>
          <div class="erpwq-quotation-review-grid">
            <div class="erpwq-quotation-review-item">
              <div class="erpwq-quotation-review-label">${escapeHtml(approvalPanelLabel)}</div>
              <div class="erpwq-quotation-review-value">${escapeHtml(approvalPanelValue)}</div>
            </div>
            <div class="erpwq-quotation-review-item">
              <div class="erpwq-quotation-review-label">Valid Till</div>
              <div class="erpwq-quotation-review-value">${escapeHtml(formatDateLabel(summary.valid_till))}</div>
            </div>
            <div class="erpwq-quotation-review-item">
              <div class="erpwq-quotation-review-label">Validity</div>
              <div class="erpwq-quotation-review-value">${escapeHtml(formatDaysToExpiry(summary.days_to_expiry))}</div>
            </div>
          </div>
          <div class="erpwq-quotation-review-note">${escapeHtml(workflowPending ? (support.approval_note || commercialWindowNote) : commercialWindowNote)}</div>
        </article>
        <article class="erpwq-quotation-review-side">
          <div class="erpwq-quotation-review-title">Conversion Signal</div>
          ${hasConversionSignal ? `
            <div class="erpwq-quotation-conversion-metrics">
              ${conversionMetrics.map((metric) => `
                <div class="erpwq-quotation-conversion-metric">
                  <div class="erpwq-quotation-conversion-metric-value">${escapeHtml(String(metric.value || 0))}</div>
                  <div class="erpwq-quotation-conversion-metric-label">${escapeHtml(metric.label)}</div>
                </div>
              `).join("")}
            </div>
          ` : `
            <div class="erpwq-quotation-conversion-empty">
              <div class="erpwq-quotation-conversion-empty-title">No downstream activity yet</div>
              <div class="erpwq-quotation-conversion-empty-note">This quotation has not been converted into order, delivery, invoice, or follow-up work.</div>
            </div>
          `}
        </article>
      </section>
    `;
    if (typeof childPageShellContent.renderShellContent === "function") {
      childPageShellContent.renderShellContent($shell, {
        actionIconMarkup,
        actionLayout: {
          sparseSecondaryThreshold: 3,
        },
        actions,
        extraSectionsHtml,
        guidance: {
          cards: guidanceCards,
          title: "What To Do Now",
        },
        summary: {
          chips: summaryChips,
          facts: summaryFacts,
          kicker: "Quotation",
          subtitle: summary.customer_label || "Customer not selected yet",
          title: summary.name || frm.doc.name || "Quotation",
        },
      });
      return;
    }
    const renderActionButton = (action) => `
      <button type="button" class="erpw-child-action ${escapeHtml(action.variant || "secondary")}" data-action-index="${action.idx}">
        <span class="erpw-child-action-accent" aria-hidden="true">${actionIconMarkup(action.icon)}</span>
        <span class="erpw-child-action-copy">
          <span class="erpw-child-action-title">${escapeHtml(action.title)}</span>
        </span>
      </button>
    `;

    $shell.html(`
      <section class="erpw-child-card erpw-child-summary">
        <div class="erpw-child-summary-copy">
          <div class="erpw-child-summary-top">
            <div class="erpw-child-summary-main">
              <div class="erpw-child-kicker">Quotation</div>
              <h2 class="erpw-child-title">${escapeHtml(summary.name || frm.doc.name || "Quotation")}</h2>
              <div class="erpw-child-subtitle">${escapeHtml(summary.customer_label || "Customer not selected yet")}</div>
            </div>
            <div class="erpw-child-chip-row erpw-child-chip-row-header">
              <span class="erpw-child-chip ${workflowPending ? "pending" : "approved"}">${escapeHtml(primaryChipLabel)}</span>
              ${showWorkflowChip ? `<span class="erpw-child-chip good">${escapeHtml(workflowLabel)}</span>` : ""}
              ${summary.valid_till ? `<span class="erpw-child-chip ${validityChipClass}">${escapeHtml(formatDaysToExpiry(summary.days_to_expiry))}</span>` : ""}
              ${converted ? `<span class="erpw-child-chip approved">${escapeHtml(formatCountTitle("Sales Order", "Sales Orders", Number(summary.sales_order_count || 0)))}</span>` : ""}
            </div>
          </div>
        </div>
        <div class="erpw-child-summary-facts">
          <div class="erpw-child-fact erpw-child-fact-grand">
            <div class="erpw-child-fact-label">Grand Total</div>
            <div class="erpw-child-fact-value">${escapeHtml(formatMoney(summary.grand_total, summary.currency))}</div>
          </div>
          <div class="erpw-child-fact erpw-child-fact-validity">
            <div class="erpw-child-fact-label">Valid Till</div>
            <div class="erpw-child-fact-value">${escapeHtml(formatDateLabel(summary.valid_till))}</div>
            <div class="erpw-child-fact-meta">${escapeHtml(formatDaysToExpiry(summary.days_to_expiry))}</div>
          </div>
          <div class="erpw-child-fact erpw-child-fact-conversion">
            <div class="erpw-child-fact-label">Conversion</div>
            <div class="erpw-child-fact-value">${escapeHtml(conversionValue)}</div>
            <div class="erpw-child-fact-meta">${escapeHtml(conversionMeta)}</div>
          </div>
        </div>
      </section>

      <section class="erpw-child-card erpw-child-actions erpw-child-actions-band">
        <div class="erpw-child-action-stack">
          ${sparseActions ? `
            <div class="erpw-child-action-row erpw-child-action-row-secondary" data-count="${actionIndexes.length}">
              ${actionIndexes.map((action) => renderActionButton(action)).join("")}
            </div>
          ` : `
            ${primaryActions.length ? `
              <div class="erpw-child-action-row erpw-child-action-row-primary" data-count="${primaryActions.length}">
                ${primaryActions.map((action) => renderActionButton(action)).join("")}
              </div>
            ` : ""}
            ${secondaryActions.length ? `
              <div class="erpw-child-action-row erpw-child-action-row-secondary" data-count="${secondaryActions.length}">
                ${secondaryActions.map((action) => renderActionButton(action)).join("")}
              </div>
            ` : ""}
          `}
        </div>
      </section>

      <section class="erpw-child-card erpw-child-context">
        <div class="erpw-child-section-heading erpw-child-section-heading-compact">
          <div class="erpw-child-section-title">What To Do Now</div>
        </div>
        <div class="erpw-child-guidance-grid">
          <article class="erpw-child-guidance-card erpw-child-guidance-card-primary">
            <div class="erpw-child-guidance-head">
              <span class="erpw-child-guidance-icon" aria-hidden="true">
                <svg viewBox="0 0 24 24"><path d="M6 12h12M13 7l5 5l-5 5" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/></svg>
              </span>
              <div class="erpw-child-guidance-copy">
                <div class="erpw-child-guidance-title">Next Action</div>
                <div class="erpw-child-guidance-chip">Priority</div>
              </div>
            </div>
            <div class="erpw-child-guidance-text">${escapeHtml(support.next_action || "Continue commercial follow-through.")}</div>
          </article>
          <article class="erpw-child-guidance-card erpw-child-guidance-card-secondary">
            <div class="erpw-child-guidance-head">
              <span class="erpw-child-guidance-icon" aria-hidden="true">
                <svg viewBox="0 0 24 24"><path d="M12 13a3.5 3.5 0 1 0 0-7a3.5 3.5 0 0 0 0 7zm-6 6a6 6 0 0 1 12 0" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/></svg>
              </span>
              <div class="erpw-child-guidance-copy">
                <div class="erpw-child-guidance-title">Customer Response</div>
                <div class="erpw-child-guidance-chip erpw-child-guidance-chip-secondary">Communication</div>
              </div>
            </div>
            <div class="erpw-child-guidance-text">${escapeHtml(support.customer_response_hint || "Use the latest approval and validity context before customer confirmation.")}</div>
          </article>
        </div>
      </section>

      <section class="erpw-child-card erpwq-quotation-review-band">
        <article class="erpwq-quotation-review-main">
          <div class="erpwq-quotation-review-title">Commercial Readiness</div>
          <div class="erpwq-quotation-review-grid">
            <div class="erpwq-quotation-review-item">
              <div class="erpwq-quotation-review-label">${escapeHtml(approvalPanelLabel)}</div>
              <div class="erpwq-quotation-review-value">${escapeHtml(approvalPanelValue)}</div>
            </div>
            <div class="erpwq-quotation-review-item">
              <div class="erpwq-quotation-review-label">Valid Till</div>
              <div class="erpwq-quotation-review-value">${escapeHtml(formatDateLabel(summary.valid_till))}</div>
            </div>
            <div class="erpwq-quotation-review-item">
              <div class="erpwq-quotation-review-label">Validity</div>
              <div class="erpwq-quotation-review-value">${escapeHtml(formatDaysToExpiry(summary.days_to_expiry))}</div>
            </div>
          </div>
          <div class="erpwq-quotation-review-note">${escapeHtml(workflowPending ? (support.approval_note || commercialWindowNote) : commercialWindowNote)}</div>
        </article>
        <article class="erpwq-quotation-review-side">
          <div class="erpwq-quotation-review-title">Conversion Status</div>
          ${hasConversionSignal ? `
            <div class="erpwq-quotation-conversion-metrics">
              ${conversionMetrics.map((metric) => `
                <div class="erpwq-quotation-conversion-metric">
                  <div class="erpwq-quotation-conversion-metric-value">${escapeHtml(String(metric.value))}</div>
                  <div class="erpwq-quotation-conversion-metric-label">${escapeHtml(metric.label)}</div>
                </div>
              `).join("")}
            </div>
          ` : `
            <div class="erpwq-quotation-conversion-empty">
              <div class="erpwq-quotation-conversion-empty-title">No downstream activity yet</div>
              <div class="erpwq-quotation-conversion-empty-note">This quotation has not been converted into order, delivery, invoice, or follow-up work.</div>
            </div>
          `}
        </article>
      </section>
    `);

    actionIndexes.forEach((action, idx) => {
      $shell.find(`[data-action-index="${idx}"]`).on("click", action.handler);
    });
  }

  function loadContext(frm) {
    if (!frm || frm.doctype !== "Quotation") return;
    const signature = getContextSignature(frm);
    if (frm.__erpwContextLoadingSignature === signature) {
      markFeatureStatus(frm, "context_load", "inflight", {
        signature,
      });
      return;
    }
    if (frm.__erpwContextRenderedSignature === signature) {
      const $shell = getShell(frm);
      const shellNeedsRender = !$shell.children().length || !!$shell.children(".erpw-so-shell-skeleton").length;
      if (shellNeedsRender) {
        if (frm.__erpwQuotationContext) {
          renderShell(frm, frm.__erpwQuotationContext);
        } else {
          frm.__erpwContextRenderedSignature = null;
          loadContext(frm);
          return;
        }
      }
      markFeatureReady(frm, "context_load", {
        signature,
        source: "cache",
      });
      scheduleFormEnhance(frm);
      return;
    }

    prepareFormShell(frm);

    if (frm.is_new()) {
      const draft = draftContext(frm);
      frm.__erpwQuotationContext = draft;
      renderShell(frm, draft);
      frm.__erpwContextRenderedSignature = signature;
      frm.__erpwContextRenderedName = frm.doc.name;
      frm.__erpwContextLoadingSignature = null;
      markFeatureReady(frm, "context_load", {
        signature,
        source: "draft",
      });
      scheduleFormEnhance(frm);
      return;
    }

    const $shell = getShell(frm);
    if (!$shell.children().length || frm.__erpwContextRenderedName !== frm.doc.name) {
      showShellSkeleton(frm);
    }

    const requestId = (frm.__erpwContextRequestId || 0) + 1;
    frm.__erpwContextRequestId = requestId;
    frm.__erpwContextLoadingSignature = signature;
    markFeatureStatus(frm, "context_load", "loading", {
      requestId,
      signature,
      source: "remote",
    });

    const request = frappe.call({
      method: METHOD,
      args: { name: frm.doc.name },
      freeze: false,
    });

    request.then((r) => {
      if (frm.__erpwContextRequestId !== requestId) {
        markFeatureStatus(frm, "context_load", "stale", {
          requestId,
          signature,
          phase: "success",
        });
        return;
      }
      const message = r.message || draftContext(frm);
      if (!frm.doc || frm.doc.name !== (message.summary && message.summary.name)) {
        markFeatureStatus(frm, "context_load", "stale", {
          requestId,
          signature,
          phase: "name_mismatch",
        });
        return;
      }
      frm.__erpwQuotationContext = message;
      renderShell(frm, message);
      frm.__erpwContextRenderedSignature = signature;
      frm.__erpwContextRenderedName = frm.doc.name;
      markFeatureReady(frm, "context_load", {
        requestId,
        signature,
        source: "remote",
      });
      scheduleFormEnhance(frm);
    }).catch(() => {
      if (frm.__erpwContextRequestId !== requestId) {
        markFeatureStatus(frm, "context_load", "stale", {
          requestId,
          signature,
          phase: "error",
        });
        return;
      }
      getShell(frm).html('<section class="erpw-child-card erpw-child-loading">Quotation workspace context is temporarily unavailable.</section>');
      markFeatureMissing(frm, "context_load", {
        requestId,
        signature,
        source: "remote",
        reason: "request_failed",
      });
      scheduleFormEnhance(frm);
    });

    Promise.resolve(request).then(() => {
      if (frm.__erpwContextRequestId === requestId) {
        frm.__erpwContextLoadingSignature = null;
        markFeatureStatus(frm, "context_load", "idle", {
          requestId,
          signature,
        });
      }
    }, () => {
      if (frm.__erpwContextRequestId === requestId) {
        frm.__erpwContextLoadingSignature = null;
        markFeatureStatus(frm, "context_load", "idle", {
          requestId,
          signature,
        });
      }
    });
  }

  frappe.ui.form.on("Quotation", {
    setup(frm) {
      prepareFormShell(frm);
    },
    before_load(frm) {
      prepareFormShell(frm);
    },
    onload(frm) {
      prepareFormShell(frm);
    },
    refresh(frm) {
      loadContext(frm);
      scheduleFormTask(frm, "post_refresh_enhance", 160, () => enhanceFormBody(frm));
    },
    dashboard_update(frm) {
      scheduleFormTask(frm, "connections_refresh_fast", 0, () => renderConnectionsWorkspace(frm, frm.__erpwQuotationContext || draftContext(frm)));
      scheduleFormTask(frm, "connections_refresh_late", 180, () => renderConnectionsWorkspace(frm, frm.__erpwQuotationContext || draftContext(frm)));
    },
  });

  function bootstrapCurrentQuotationForm() {
    if (!window.cur_frm || cur_frm.doctype !== "Quotation") return false;
    if (!cur_frm.page || !cur_frm.page.main) return false;
    loadContext(cur_frm);
    return true;
  }

  if (window.erpWorkspaceUiBoot && typeof window.erpWorkspaceUiBoot.registerChildPageBootstrap === "function") {
    window.erpWorkspaceUiBoot.registerChildPageBootstrap("Quotation", bootstrapCurrentQuotationForm);
  }

  $(document).ready(() => {
    setTimeout(bootstrapCurrentQuotationForm, 120);
  });
})();
