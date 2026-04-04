(function () {
  const METHOD = "erp_workspace_ui.api.get_sales_order_page_context";

  function formatMoney(value, currency) {
    if (value == null) return "--";
    try {
      return format_currency(value, currency || frappe.defaults.get_default("currency"));
    } catch (e) {
      return `${currency || ""} ${value}`;
    }
  }

  function pct(value) {
    const numeric = Number(value || 0);
    return `${Math.round(numeric)}%`;
  }

  function escapeHtml(value) {
    return frappe.utils.escape_html(value == null ? "" : String(value));
  }

  function routeToDoc(doctype, name) {
    if (!doctype || !name) return;
    frappe.set_route("Form", doctype, name);
  }

  function routeToList(doctype, filters) {
    frappe.route_options = filters && Object.keys(filters).length ? filters : null;
    frappe.set_route("List", doctype);
  }

  function getFormTaskState(frm) {
    if (!frm) return { timers: {} };
    if (!frm.__erpwTaskState) {
      frm.__erpwTaskState = { timers: {} };
    }
    return frm.__erpwTaskState;
  }

  function scheduleFormTask(frm, key, delay, fn) {
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
  }

  function scheduleFormEnhance(frm) {
    scheduleFormTask(frm, "enhance_form_body_fast", 0, () => enhanceFormBody(frm));
    scheduleFormTask(frm, "enhance_form_body_late", 260, () => enhanceFormBody(frm));
  }

  function scheduleConnectionsEnhance(frm) {
    scheduleFormTask(frm, "enhance_connections_fast", 0, () => enhanceConnectionsWorkspace(frm));
    scheduleFormTask(frm, "enhance_connections_late", 180, () => enhanceConnectionsWorkspace(frm));
  }

  function requestConnectionsCounts(frm) {
    if (!frm || !frm.dashboard || typeof frm.dashboard.set_open_count !== "function") return;
    const state = getFormTaskState(frm);
    const now = Date.now();
    if (state.connectionsCountRequestedAt && now - state.connectionsCountRequestedAt < 1200) {
      return;
    }
    state.connectionsCountRequestedAt = now;
    try {
      frm.dashboard.set_open_count();
    } catch (error) {
      // Ignore transient dashboard timing issues and let the next scheduled pass retry.
    }
  }

  function getContextSignature(frm) {
    const doc = (frm && frm.doc) || {};
    return [
      doc.name || "",
      doc.modified || "",
      doc.docstatus == null ? "" : String(doc.docstatus),
      doc.status || "",
      doc.workflow_state || "",
      doc.grand_total == null ? "" : String(doc.grand_total),
      doc.per_delivered == null ? "" : String(doc.per_delivered),
      doc.per_billed == null ? "" : String(doc.per_billed),
      doc.customer || "",
      doc.customer_address || "",
      doc.shipping_address_name || "",
      doc.company_address || "",
    ].join("|");
  }

  function actionIconMarkup(kind) {
    const icons = {
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
      quotation: `
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M7 3.5h7l4 4v13H7zM14 3.5v4h4M10 12h5M10 15.5h5M10 19h3" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      `,
      return_doc: `
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M9 8l-4 4l4 4M5 12h9a4 4 0 1 0 0 8" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      `,
    };
    return icons[kind] || icons.invoice;
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

  function getFormRoot(frm) {
    return $(frm && frm.page && frm.page.main ? frm.page.main : frm && frm.$wrapper ? frm.$wrapper : []);
  }

  function getNativeLayoutAnchor(frm) {
    const $root = getFormRoot(frm);
    if (!$root.length) return $();

    return $root.find(".form-layout").first().length
      ? $root.find(".form-layout").first()
      : $root.find(".layout-main-section").first().length
        ? $root.find(".layout-main-section").first()
        : $root.find(".form-page").first().length
          ? $root.find(".form-page").first()
          : $();
  }

  function getShell(frm) {
    const $root = getFormRoot(frm);
    const $mount = getNativeLayoutAnchor(frm);

    let $shell = $root.find(".erpw-child-shell.erpws-order-shell").first();
    if (!$shell.length) {
      $shell = $('<div class="erpw-child-shell erpws-order-shell"></div>');
      if ($mount.length) {
        $shell.insertBefore($mount);
      } else {
        $root.prepend($shell);
      }
    } else if ($mount.length && $shell.parent().get(0) !== $root.get(0)) {
      $shell.detach();
      $shell.insertBefore($mount);
    }
    $shell.removeClass("erpw-preload-shell");
    return $shell;
  }

  function getShellSkeletonMarkup() {
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
  }

  function showShellSkeleton(frm) {
    const $shell = getShell(frm);
    if (!$shell.children(".erpw-so-shell-skeleton").length || frm.__erpwContextRenderedName !== (frm.doc && frm.doc.name)) {
      $shell.html(getShellSkeletonMarkup());
    }
  }

  function setNativeLayoutPrepState(frm, isPrepping) {
    const $root = getFormRoot(frm);
    const $native = getNativeLayoutAnchor(frm);
    if (window.erpWorkspaceUiBoot && typeof window.erpWorkspaceUiBoot.setSalesOrderPrep === "function") {
      window.erpWorkspaceUiBoot.setSalesOrderPrep(false);
    }
    if (document.documentElement) {
      document.documentElement.classList.remove("erpw-route-sales-order-prep");
      document.documentElement.classList.add("erpw-route-sales-order-ready");
    }
    if (document.body) {
      document.body.classList.remove("erpw-route-sales-order-prep");
      document.body.classList.add("erpw-route-sales-order-ready");
    }
    if ($root.length) {
      $root.removeClass("erpw-so-form-prepping");
    }
    if ($native.length) {
      $native.removeClass("erpw-so-native-prepping");
    }
  }

  function releasePreparedShell(frm) {
    const state = getFormTaskState(frm);
    if (state.prepReleaseTimer) {
      clearTimeout(state.prepReleaseTimer);
      delete state.prepReleaseTimer;
    }
    setNativeLayoutPrepState(frm, false);
    const $root = getFormRoot(frm);
    if ($root.length) {
      $root.addClass("erpw-so-form-enhanced");
    }
  }

  function isCustomShellReadyForRelease(frm) {
    if (!frm || !frm.doc) return false;

    if (frm.is_new()) {
      return !!getShell(frm).children().length;
    }

    const signature = getContextSignature(frm);
    if (frm.__erpwContextRenderedSignature === signature) {
      return true;
    }

    return Boolean(
      frm.__erpwContextRenderedName === frm.doc.name &&
        !frm.__erpwContextLoadingSignature
    );
  }

  function prepareFormShell(frm, loadingMessage) {
    const $root = getFormRoot(frm);
    if (!$root.length) return;

    const state = getFormTaskState(frm);
    setNativeLayoutPrepState(frm, true);

    showShellSkeleton(frm);

    if (state.prepReleaseTimer) {
      clearTimeout(state.prepReleaseTimer);
    }
    state.prepReleaseTimer = setTimeout(() => {
      releasePreparedShell(frm);
    }, 2200);
  }

  function getReferenceNames(frm, data) {
    const summary = data.summary || {};
    const linked = data.linked_documents || {};
    return [frm.doc.name, summary.customer]
      .concat((linked.deliveries || []).map((row) => row.name))
      .concat((linked.invoices || []).map((row) => row.name))
      .concat((linked.returns || []).map((row) => row.name))
      .filter(Boolean);
  }

  function createFollowUpTask(frm, data) {
    const summary = data.summary || {};
    frappe.new_doc("ToDo", {
      description: `Follow up ${summary.name || frm.doc.name || "Sales Order"} for ${summary.customer || "customer"}`,
      reference_type: "Sales Order",
      reference_name: summary.name || frm.doc.name,
      allocated_to: frm.doc.owner || frappe.session.user,
      date: summary.delivery_date || frappe.datetime.get_today(),
    });
  }

  function draftContext(frm) {
    const owner = frm.doc.owner || frappe.session.user;
    const ownerDisplay = frappe.user && typeof frappe.user.full_name === "function" ? frappe.user.full_name(owner) : owner;

    return {
      summary: {
        name: frm.doc.name || "New Sales Order",
        customer: frm.doc.customer || "Customer not selected yet",
        status: frm.doc.docstatus === 0 ? "Draft" : (frm.doc.status || "Draft"),
        workflow_state: frm.doc.workflow_state || "Draft",
        owner,
        owner_display: ownerDisplay,
        transaction_date: frm.doc.transaction_date || frappe.datetime.get_today(),
        delivery_date: frm.doc.delivery_date || null,
        currency: frm.doc.currency || frappe.defaults.get_default("currency"),
        grand_total: frm.doc.grand_total || 0,
        per_delivered: frm.doc.per_delivered || 0,
        per_billed: frm.doc.per_billed || 0,
        billing_status: frm.doc.billing_status || "Not Billed",
        advance_payment_status: frm.doc.advance_payment_status || "Not Requested",
        source_quotation: null,
      },
      linked_documents: { quotation: null, deliveries: [], invoices: [], returns: [] },
      support: {
        latest_task: null,
        open_task_count: 0,
        approval_note: "Use the standard toolbar to save, submit, or route approval for this order.",
        customer_response_hint: "Complete customer, item, and delivery commitment details before confirming a customer-facing commitment.",
        execution_note: "This draft will become the main execution-control page after the order is saved.",
        next_action: "Complete the core order details, then save so the execution workspace can evaluate linked delivery and billing context.",
        detail_guide: "Use the detailed form sections below to complete items, taxes, addresses, and terms before submitting the order.",
      },
    };
  }

  function actionConfig(frm, data) {
    const summary = data.summary || {};
    const linked = data.linked_documents || {};
    const support = data.support || {};
    const actions = [];

    if (Array.isArray(linked.deliveries) && linked.deliveries.length) {
      actions.push({
        title: linked.deliveries.length === 1 ? "Open Delivery" : `Open Deliveries (${linked.deliveries.length})`,
        variant: "primary",
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
        title: linked.invoices.length === 1 ? "Open Invoice" : `Open Invoices (${linked.invoices.length})`,
        variant: "primary",
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

    if (summary.customer) {
      actions.push({
        title: "Open Customer",
        variant: "secondary",
        icon: "customer",
        handler: () => routeToDoc("Customer", summary.customer),
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

    if (linked.quotation && linked.quotation.name) {
      actions.push({
        title: "Open Source Quotation",
        variant: "secondary",
        icon: "quotation",
        handler: () => routeToDoc("Quotation", linked.quotation.name),
      });
    }

    if (Array.isArray(linked.returns) && linked.returns.length) {
      actions.push({
        title: linked.returns.length === 1 ? "Open Return" : `Open Returns (${linked.returns.length})`,
        variant: "secondary",
        icon: "return_doc",
        handler: () => {
          if (linked.returns.length === 1) {
            routeToDoc(linked.returns[0].doctype, linked.returns[0].name);
            return;
          }
          const firstType = linked.returns[0].doctype;
          const sameType = linked.returns.every((row) => row.doctype === firstType);
          if (sameType) {
            routeToList(firstType, { name: ["in", linked.returns.map((row) => row.name)] });
            return;
          }
          routeToDoc(linked.returns[0].doctype, linked.returns[0].name);
        },
      });
    }

    return actions;
  }

  function linkConfig(data) {
    const linked = data.linked_documents || {};
    const links = [];

    if (linked.quotation && linked.quotation.name) {
      links.push({ doctype: "Quotation", name: linked.quotation.name, label: `Quotation ${linked.quotation.name}` });
    }
    (linked.deliveries || []).forEach((row) => links.push({ doctype: "Delivery Note", name: row.name, label: `Delivery ${row.name}` }));
    (linked.invoices || []).forEach((row) => links.push({ doctype: "Sales Invoice", name: row.name, label: `Invoice ${row.name}` }));
    (linked.returns || []).forEach((row) => links.push({ doctype: row.doctype, name: row.name, label: `Return ${row.name}` }));

    return links;
  }

  function hasMeaningfulValue(value) {
    if (value == null) return false;
    if (Array.isArray(value)) return value.length > 0;
    if (typeof value === "number") return value !== 0;
    if (typeof value === "boolean") return value;
    const normalized = String(value).trim();
    return normalized !== "" && normalized !== "0";
  }

  function getSectionForField(frm, fieldname) {
    const field = frm.fields_dict && frm.fields_dict[fieldname];
    if (!field || !field.$wrapper || !field.$wrapper.length) return null;
    const $section = field.$wrapper.closest(".form-section");
    return $section.length ? $section : null;
  }

  function getFieldWrapper(frm, fieldname) {
    const field = frm.fields_dict && frm.fields_dict[fieldname];
    if (!field) return null;
    const $wrapper = field.$wrapper && field.$wrapper.length ? field.$wrapper : $(field.wrapper || []);
    return $wrapper.length ? $wrapper : null;
  }

  function getTabForField(frm, fieldname) {
    const $wrapper = getFieldWrapper(frm, fieldname);
    if (!$wrapper || !$wrapper.length) return $();
    const $tab = $wrapper.closest(".form-tab");
    return $tab.length ? $tab : $();
  }

  function getTabByFieldname(frm, fieldname) {
    const $root = $(frm.page && frm.page.main ? frm.page.main : frm.$wrapper || []);
    if (!$root.length) return $();

    const $tabLink = $root.find(`.form-tabs .nav-link[data-fieldname="${fieldname}"]`).first();
    if (!$tabLink.length) return $();

    const tabId = $tabLink.attr("aria-controls");
    if (!tabId) return $();

    const $tab = $root.find(`#${tabId}`).first();
    return $tab.length ? $tab : $();
  }

  function getSectionObjectForField(frm, fieldname) {
    const field = frm.fields_dict && frm.fields_dict[fieldname];
    return field && field.section ? field.section : null;
  }

  function formatCompactNumber(value) {
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) return "";
    if (Math.abs(numeric - Math.round(numeric)) < 0.001) {
      return String(Math.round(numeric));
    }
    return numeric.toFixed(1).replace(/\.0$/, "");
  }

  function formatFixedNumber(value, precision = 2) {
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) return "";
    return numeric.toFixed(precision);
  }

  function formatDateLabel(value) {
    if (!value) return "--";
    try {
      return frappe.datetime.str_to_user(value);
    } catch (e) {
      return String(value);
    }
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

  function setFieldPrecision(frm, fieldname, precision) {
    const field = frm.fields_dict && frm.fields_dict[fieldname];
    if (!field || !field.df) return;

    field.df.precision = precision;
    if (typeof field.refresh === "function") {
      field.refresh();
    }
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

  function usesCompanyCurrencyOnly(frm) {
    const docCurrency = frm.doc.currency || frappe.defaults.get_default("currency");
    const companyCurrency = frm.doc.company_currency || docCurrency;
    return !docCurrency || !companyCurrency || docCurrency === companyCurrency;
  }

  function shouldShowPricingSection(frm) {
    const sameCurrency = usesCompanyCurrencyOnly(frm);
    const sellingPriceList = String(frm.doc.selling_price_list || frm.doc.price_list || "").trim();
    const defaultPriceList = !sellingPriceList || sellingPriceList === "Standard Selling";
    const rateSignals = [frm.doc.plc_conversion_rate, frm.doc.conversion_rate].some((value) => {
      if (!hasMeaningfulValue(value)) return false;
      return Number(value) !== 1;
    });
    const pricingSignals = [
      frm.doc.ignore_pricing_rule,
      frm.doc.additional_discount_percentage,
      frm.doc.discount_amount,
      frm.doc.base_discount_amount,
      frm.doc.coupon_code,
    ];

    const hasPricingSignal = rateSignals || pricingSignals.some((value) => hasMeaningfulValue(value));
    return !sameCurrency || !defaultPriceList || hasPricingSignal;
  }

  function ensureMoreInfoWorkspace($tab) {
    let $workspace = $tab.children(".erpw-so-moreinfo-workspace").first();
    if ($workspace.length) return $workspace;

    $workspace = $(`
      <div class="form-section erpw-so-moreinfo-workspace">
        <section class="erpw-so-moreinfo-card" data-card="context">
          <div class="erpw-so-moreinfo-head">
            <div class="erpw-so-moreinfo-title">Operational Context</div>
            <div class="erpw-so-moreinfo-note">Cross-reference and financial context for this order.</div>
          </div>
          <div class="erpw-so-moreinfo-fields erpw-so-moreinfo-fields-two" data-slot="context"></div>
        </section>
        <section class="erpw-so-moreinfo-card" data-card="print">
          <div class="erpw-so-moreinfo-head">
            <div class="erpw-so-moreinfo-title">Document Output</div>
            <div class="erpw-so-moreinfo-note">Control print language, heading, and customer-facing document presentation.</div>
          </div>
          <div class="erpw-so-moreinfo-fields erpw-so-moreinfo-fields-two" data-slot="print"></div>
        </section>
        <section class="erpw-so-moreinfo-card" data-card="execution">
          <div class="erpw-so-moreinfo-head">
            <div class="erpw-so-moreinfo-title">Execution Signals</div>
            <div class="erpw-so-moreinfo-note">Secondary delivery, billing, and picking detail beyond the main header.</div>
          </div>
          <div class="erpw-so-moreinfo-fields erpw-so-moreinfo-fields-two" data-slot="execution"></div>
        </section>
        <section class="erpw-so-moreinfo-card erpw-so-moreinfo-card-wide" data-card="commercial">
          <div class="erpw-so-moreinfo-head">
            <div class="erpw-so-moreinfo-title">Commercial Attribution</div>
            <div class="erpw-so-moreinfo-note">Commission ownership and sales allocation for this order.</div>
          </div>
          <div class="erpw-so-moreinfo-fields erpw-so-moreinfo-fields-two" data-slot="commercial"></div>
          <div class="erpw-so-moreinfo-subcard" data-subcard="sales-team">
            <div class="erpw-so-moreinfo-subtitle">Sales Team</div>
            <div class="erpw-so-moreinfo-fields" data-slot="sales-team"></div>
          </div>
        </section>
        <section class="erpw-so-moreinfo-card erpw-so-moreinfo-card-wide" data-card="controls">
          <div class="erpw-so-moreinfo-head">
            <div class="erpw-so-moreinfo-title">Internal Controls</div>
            <div class="erpw-so-moreinfo-note">Automation, routing, and internal handling settings that support execution.</div>
          </div>
          <div class="erpw-so-moreinfo-composite">
            <div class="erpw-so-moreinfo-subcard" data-subcard="automation">
              <div class="erpw-so-moreinfo-subtitle">Auto Repeat</div>
              <div class="erpw-so-moreinfo-fields erpw-so-moreinfo-fields-two" data-slot="automation"></div>
            </div>
            <div class="erpw-so-moreinfo-subcard" data-subcard="flags">
              <div class="erpw-so-moreinfo-subtitle">Internal Flags</div>
              <div class="erpw-so-moreinfo-fields erpw-so-moreinfo-fields-flags" data-slot="flags"></div>
            </div>
            <div class="erpw-so-moreinfo-subcard erpw-so-moreinfo-subcard-wide" data-subcard="routing">
              <div class="erpw-so-moreinfo-subtitle">Routing & Dispatch</div>
              <div class="erpw-so-moreinfo-fields erpw-so-moreinfo-fields-two" data-slot="routing"></div>
            </div>
          </div>
        </section>
      </div>
    `);

    $tab.prepend($workspace);
    return $workspace;
  }

  function getSectionFieldnames($section) {
    if (!$section || !$section.length) return [];
    return $section.find(".frappe-control").map((_, element) => $(element).attr("data-fieldname")).get().filter(Boolean);
  }

  function moveFieldToSlot(frm, fieldname, $slot) {
    if (!$slot || !$slot.length) return;
    const field = frm.fields_dict && frm.fields_dict[fieldname];
    const $wrapper = getFieldWrapper(frm, fieldname);
    if (!field || !$wrapper || !$wrapper.length) return;

    $wrapper
      .addClass("erpw-so-moreinfo-control")
      .attr("data-erpw-so-moreinfo-field", fieldname)
      .toggleClass("erpw-so-moreinfo-control-table", field.df && field.df.fieldtype === "Table")
      .toggleClass("erpw-so-moreinfo-control-check", field.df && field.df.fieldtype === "Check")
      .toggleClass("erpw-so-moreinfo-control-button", field.df && field.df.fieldtype === "Button");

    $slot.append($wrapper);
  }

  function slotHasVisibleControls($slot) {
    if (!$slot || !$slot.length) return false;
    return $slot.children(".frappe-control").toArray().some((element) => {
      const $control = $(element);
      if ($control.hasClass("hide-control") || $control.hasClass("hidden")) return false;
      if ($control.css("display") === "none") return false;
      const inlineStyle = String($control.attr("style") || "").toLowerCase();
      if (inlineStyle.includes("display: none")) return false;
      return true;
    });
  }

  function containerHasVisibleControls($container) {
    if (!$container || !$container.length) return false;
    return $container.find(".frappe-control").toArray().some((element) => {
      const $control = $(element);
      if ($control.hasClass("hide-control") || $control.hasClass("hidden")) return false;
      if ($control.css("display") === "none") return false;
      const inlineStyle = String($control.attr("style") || "").toLowerCase();
      if (inlineStyle.includes("display: none")) return false;
      return true;
    });
  }

  function ensureMoreInfoStack($tab) {
    let $stack = $tab.children(".erpw-so-moreinfo-stack").first();
    if ($stack.length) return $stack;

    $stack = $('<div class="erpw-so-moreinfo-stack"></div>');
    $tab.prepend($stack);
    return $stack;
  }

  function ensureMoreInfoSectionHeader($section, title, note) {
    const $defaultHead = $section.children(".section-head").first();
    if ($defaultHead.length) {
      $defaultHead.addClass("erpw-so-moreinfo-default-head").hide();
    }

    let $header = $section.children(".erpw-so-moreinfo-header").first();
    if (!$header.length) {
      $header = $(`
        <div class="erpw-so-moreinfo-header" role="button" tabindex="0" aria-expanded="true">
          <div class="erpw-so-moreinfo-header-copy">
            <div class="erpw-so-moreinfo-header-title"></div>
            <div class="erpw-so-moreinfo-header-note"></div>
          </div>
          <div class="erpw-so-moreinfo-header-side">
            <div class="erpw-so-moreinfo-header-status" hidden></div>
            <span class="erpw-so-moreinfo-header-toggle" aria-hidden="true">
              <svg viewBox="0 0 20 20">
                <path d="M5.5 7.5L10 12l4.5-4.5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </span>
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
      $status
        .text(statusText)
        .attr("data-tone", statusTone)
        .prop("hidden", false);
    } else {
      $status.text("").removeAttr("data-tone").prop("hidden", true);
    }
  }

  function ensureMoreInfoStatePanel($section) {
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

  function getMoreInfoSectionPresentation(frm, key) {
    const hasCommissionSignal = [
      frm.doc.sales_partner,
      frm.doc.commission_rate,
      frm.doc.total_commission,
    ].some((value) => hasMeaningfulValue(value));
    const salesTeamRows = Array.isArray(frm.doc.sales_team) ? frm.doc.sales_team.length : 0;
    const hasDispatchInfo = [
      frm.doc.dispatch_address_name,
      frm.doc.dispatch_address,
      frm.doc.contact_phone,
    ].some((value) => hasMeaningfulValue(value));
    const hasInternalCompany = Boolean(frm.doc.is_internal_customer) || hasMeaningfulValue(frm.doc.represents_company);
    const hasControlSignal = hasMeaningfulValue(frm.doc.auto_repeat)
      || hasDispatchInfo
      || hasInternalCompany
      || Boolean(frm.doc.disable_rounded_total)
      || hasMeaningfulValue(frm.doc.from_date)
      || hasMeaningfulValue(frm.doc.to_date);
    const hasContextSignal = [
      frm.doc.project,
      frm.doc.inter_company_order_reference,
      frm.doc.party_account_currency,
    ].some((value) => hasMeaningfulValue(value));

    const perDelivered = Number(frm.doc.per_delivered || 0);
    const perBilled = Number(frm.doc.per_billed || 0);
    const perPicked = Number(frm.doc.per_picked || 0);

    const presentations = {
      context: {
        expanded: true,
        quiet: true,
        statusText: hasMeaningfulValue(frm.doc.project) ? "Project linked" : "Reference",
      },
      print: {
        expanded: Boolean(frm.doc.group_same_items || hasMeaningfulValue(frm.doc.letter_head) || hasMeaningfulValue(frm.doc.select_print_heading)),
        quiet: true,
        statusText: getLanguageLabel(frm.doc.language),
        summary: (!frm.doc.group_same_items && !hasMeaningfulValue(frm.doc.letter_head) && !hasMeaningfulValue(frm.doc.select_print_heading)) ? {
          title: `Using ${getLanguageLabel(frm.doc.language)} print presentation`,
          note: "Standard print language is active with no custom heading or letter head.",
          actionLabel: "Edit output settings",
          actionType: "reveal",
        } : null,
      },
      execution: {
        expanded: true,
        wide: true,
        priority: true,
        statusTone: "attention",
        statusText: perDelivered > 0
          ? `${formatFixedNumber(perDelivered)}% delivered`
          : perBilled > 0
            ? `${formatFixedNumber(perBilled)}% billed`
            : perPicked > 0
              ? `${formatFixedNumber(perPicked)}% picked`
              : "Live",
      },
      commercial: {
        expanded: hasCommissionSignal,
        quiet: !hasCommissionSignal,
        statusTone: hasCommissionSignal ? "active" : "neutral",
        statusText: hasCommissionSignal
          ? (hasMeaningfulValue(frm.doc.sales_partner)
            ? "Partner set"
            : `${formatCompactNumber(frm.doc.commission_rate || 0)}% rate`)
          : "Unassigned",
        summary: hasCommissionSignal ? null : {
          title: "Commission ownership not configured",
          note: "Assign a sales partner only when commission should apply.",
          actionLabel: "Edit attribution",
          actionType: "reveal",
        },
      },
      "sales-team": {
        expanded: salesTeamRows > 0,
        wide: salesTeamRows > 0,
        quiet: salesTeamRows === 0,
        statusText: salesTeamRows > 0 ? `${salesTeamRows} row${salesTeamRows === 1 ? "" : "s"}` : "No rows",
        summary: salesTeamRows > 0 ? null : {
          title: "No sales allocation rows yet",
          note: "Add sales ownership only when multiple contributors or allocation tracking is needed.",
          actionLabel: "Add sales team",
          actionType: "add-row",
        },
      },
      controls: {
        expanded: hasControlSignal,
        wide: hasDispatchInfo,
        quiet: !hasControlSignal,
        statusTone: hasControlSignal ? "active" : "neutral",
        statusText: hasMeaningfulValue(frm.doc.auto_repeat)
          ? "Recurring"
          : hasDispatchInfo
            ? "Dispatch override"
            : hasInternalCompany
              ? "Internal"
              : "Manual",
        summary: hasControlSignal ? null : {
          title: "No automation or routing overrides",
          note: "Execution follows the default sales order workflow with no recurring or routing override.",
          actionLabel: "Configure controls",
          actionType: "reveal",
        },
      },
      dimensions: {
        expanded: true,
        quiet: true,
        statusText: hasMeaningfulValue(frm.doc.cost_center) ? "Configured" : "",
      },
    };

    if (key === "context" && !hasContextSignal) {
      presentations.context.hidden = true;
    }

    return presentations[key] || { expanded: true };
  }

  function applyMoreInfoSectionBodyState(frm, config, $section, presentation) {
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

    const $action = $panel.find(".erpw-so-moreinfo-state-action");
    $action
      .text(summary.actionLabel || "Configure")
      .off(".erpwMoreInfoState")
      .on("click.erpwMoreInfoState", (event) => {
        event.preventDefault();
        event.stopPropagation();

        $section.data("erpwMoreinfoRevealRaw", 1);
        applyMoreInfoSectionBodyState(frm, config, $section, presentation);

        if (summary.actionType === "add-row") {
          const $addRow = $section.find(".grid-add-row").filter(":visible").first();
          if ($addRow.length) {
            $addRow.trigger("click");
            return;
          }
        }

        focusFirstVisibleControl($section);
      });

    $panel.prop("hidden", false);
  }

  function setMoreInfoSectionExpanded(frm, fieldname, $section, expanded) {
    if (!$section || !$section.length) return;

    const $body = $section.children(".section-body").first();
    const $defaultHead = $section.children(".section-head").first();
    const sectionObject = getSectionObjectForField(frm, fieldname);
    if (sectionObject && typeof sectionObject.collapse === "function") {
      sectionObject.collapse(!expanded);
    }

    $body.toggleClass("hide", !expanded).prop("hidden", !expanded);
    $defaultHead.toggleClass("collapsed", !expanded);
    $section.toggleClass("erpw-so-moreinfo-section-collapsed", !expanded);
    $section.children(".erpw-so-moreinfo-header").attr("aria-expanded", expanded ? "true" : "false");
  }

  function bindMoreInfoSectionHeader(frm, fieldname, $section) {
    const $header = $section.children(".erpw-so-moreinfo-header").first();
    if (!$header.length) return;

    const toggleSection = () => {
      if (!$section.is(":visible")) return;
      const isExpanded = !$section.children(".section-body").first().hasClass("hide");
      setMoreInfoSectionExpanded(frm, fieldname, $section, !isExpanded);
    };

    $header
      .attr("data-section-fieldname", fieldname)
      .off(".erpwMoreInfo")
      .on("click.erpwMoreInfo", (event) => {
        event.preventDefault();
        toggleSection();
      })
      .on("keydown.erpwMoreInfo", (event) => {
        if (event.key !== "Enter" && event.key !== " ") return;
        event.preventDefault();
        toggleSection();
      });
  }

  function resetMoreInfoTab($tab) {
    if (!$tab || !$tab.length) return;

    $tab.children(".erpw-so-moreinfo-workspace").remove();
    $tab.children(".erpw-so-moreinfo-stack").remove();
    $tab.find(".erpw-so-moreinfo-state-panel").remove();
    $tab.find(".erpw-so-moreinfo-header").remove();
    $tab.find(".form-section").removeData("erpwMoreinfoRevealRaw");
    $tab.find(".erpw-so-moreinfo-default-head").removeClass("erpw-so-moreinfo-default-head").show();
    $tab.find(".form-section")
      .show()
      .removeClass("hide-control empty-section visible-section erpw-so-moreinfo-hidden-source erpw-so-moreinfo-section-collapsed erpw-so-moreinfo-section-summary-mode");
    $tab.find(".section-body").removeClass("hide");
    $tab.find(".section-head").removeClass("collapsed");
    $tab.find(".form-section").removeClass([
      "erpw-so-moreinfo-source",
      "erpw-so-moreinfo-section",
      "erpw-so-moreinfo-section-context",
      "erpw-so-moreinfo-section-print",
      "erpw-so-moreinfo-section-execution",
      "erpw-so-moreinfo-section-commercial",
      "erpw-so-moreinfo-section-sales-team",
      "erpw-so-moreinfo-section-controls",
      "erpw-so-moreinfo-section-dimensions",
      "erpw-so-moreinfo-section-priority",
      "erpw-so-moreinfo-section-quiet",
      "erpw-so-moreinfo-section-wide",
    ].join(" "));
  }

  function updateMoreInfoVisibility(frm, $workspace) {
    const samePartyCurrency = !hasMeaningfulValue(frm.doc.party_account_currency)
      || String(frm.doc.party_account_currency || "").trim() === String(frm.doc.currency || "").trim();
    const hasCommissionSignal = [
      frm.doc.sales_partner,
      frm.doc.commission_rate,
      frm.doc.total_commission,
    ].some((value) => hasMeaningfulValue(value));
    const hasAutoRepeat = hasMeaningfulValue(frm.doc.auto_repeat);
    const hasDispatchInfo = [
      frm.doc.dispatch_address_name,
      frm.doc.dispatch_address,
      frm.doc.contact_phone,
    ].some((value) => hasMeaningfulValue(value));
    const hasInternalCompany = Boolean(frm.doc.is_internal_customer) || hasMeaningfulValue(frm.doc.represents_company);

    toggleField(frm, "status", false);
    toggleField(frm, "inter_company_order_reference", hasMeaningfulValue(frm.doc.inter_company_order_reference));
    toggleField(frm, "party_account_currency", !samePartyCurrency);
    toggleField(frm, "letter_head", hasMeaningfulValue(frm.doc.letter_head));
    toggleField(frm, "select_print_heading", hasMeaningfulValue(frm.doc.select_print_heading));
    toggleField(frm, "per_picked", hasMeaningfulValue(frm.doc.per_picked));
    toggleField(frm, "amount_eligible_for_commission", hasCommissionSignal);
    toggleField(frm, "update_auto_repeat_reference", hasAutoRepeat);
    toggleField(frm, "represents_company", hasInternalCompany);
    toggleField(frm, "dispatch_address_name", hasDispatchInfo);
    toggleField(frm, "dispatch_address", hasDispatchInfo);
    toggleField(frm, "contact_phone", hasDispatchInfo);

    $workspace.find("[data-subcard]").each((_, cardElement) => {
      const $card = $(cardElement);
      const slotName = $card.attr("data-subcard");
      const $slot = $workspace.find(`[data-slot="${slotName}"]`).first();
      $card.toggle(slotHasVisibleControls($slot));
    });

    $workspace.find("[data-card]").each((_, cardElement) => {
      const $card = $(cardElement);
      $card.toggle(containerHasVisibleControls($card));
    });
  }

  function enhanceMoreInfoTab(frm) {
    if (!frm || !frm.fields_dict) return false;

    const $tab = getTabByFieldname(frm, "more_info");
    if (!$tab.length) return false;
    resetMoreInfoTab($tab);
    $tab.addClass("erpw-so-moreinfo-tab");

    const samePartyCurrency = !hasMeaningfulValue(frm.doc.party_account_currency)
      || String(frm.doc.party_account_currency || "").trim() === String(frm.doc.currency || "").trim();
    const hasCommissionSignal = [
      frm.doc.sales_partner,
      frm.doc.commission_rate,
      frm.doc.total_commission,
    ].some((value) => hasMeaningfulValue(value));
    const hasAutoRepeat = hasMeaningfulValue(frm.doc.auto_repeat);
    const hasDispatchInfo = [
      frm.doc.dispatch_address_name,
      frm.doc.dispatch_address,
      frm.doc.contact_phone,
    ].some((value) => hasMeaningfulValue(value));
    const hasInternalCompany = Boolean(frm.doc.is_internal_customer) || hasMeaningfulValue(frm.doc.represents_company);

    toggleField(frm, "status", false);
    toggleField(frm, "inter_company_order_reference", hasMeaningfulValue(frm.doc.inter_company_order_reference));
    toggleField(frm, "party_account_currency", !samePartyCurrency);
    toggleField(frm, "per_picked", hasMeaningfulValue(frm.doc.per_picked));
    toggleField(frm, "amount_eligible_for_commission", hasCommissionSignal);
    toggleField(frm, "update_auto_repeat_reference", hasAutoRepeat);
    toggleField(frm, "represents_company", hasInternalCompany);
    toggleField(frm, "dispatch_address_name", hasDispatchInfo);
    toggleField(frm, "dispatch_address", hasDispatchInfo);
    toggleField(frm, "contact_phone", hasDispatchInfo);
    toggleField(frm, "is_internal_customer", Boolean(frm.doc.is_internal_customer));
    toggleField(frm, "disable_rounded_total", Boolean(frm.doc.disable_rounded_total));
    ["per_delivered", "per_billed", "per_picked"].forEach((fieldname) => setFieldPrecision(frm, fieldname, 2));

    const configs = [
      {
        key: "execution",
        fieldname: "delivery_status",
        title: "Execution Signals",
        note: "Secondary delivery, billing, and picking detail beyond the main header.",
      },
      {
        key: "context",
        fieldname: "project",
        title: "Operational Context",
        note: "Cross-reference and financial context for this order.",
      },
      {
        key: "print",
        fieldname: "language",
        title: "Document Output",
        note: "Control print language, heading, and customer-facing document presentation.",
      },
      {
        key: "commercial",
        fieldname: "sales_partner",
        title: "Commercial Attribution",
        note: "Commission ownership and sales allocation for this order.",
      },
      {
        key: "sales-team",
        fieldname: "sales_team",
        title: "Sales Team",
        note: "Allocation and contribution across the assigned sales team.",
      },
      {
        key: "controls",
        fieldname: "from_date",
        title: "Internal Controls",
        note: "Automation, routing, and internal handling settings that support execution.",
      },
      {
        key: "dimensions",
        fieldname: "cost_center",
        title: "Accounting Dimensions",
        note: "Optional reporting and allocation dimensions for downstream accounting.",
      },
    ];

    const $stack = ensureMoreInfoStack($tab);
    const seen = new Set();
    const arrangedSections = [];

    configs.forEach((config) => {
      const $section = getSectionForField(frm, config.fieldname);
      if (!$section || !$section.length) return;

      const sectionNode = $section.get(0);
      if (seen.has(sectionNode)) return;
      seen.add(sectionNode);

      $section
        .addClass(`erpw-so-moreinfo-section erpw-so-moreinfo-section-${config.key}`)
        .toggleClass("erpw-so-moreinfo-section-wide", !!config.wide);

      ensureMoreInfoSectionHeader($section, config.title, config.note);
      $stack.append($section);
      arrangedSections.push({ config, $section });
    });

    if (frm.layout && typeof frm.layout.refresh_sections === "function") {
      frm.layout.refresh_sections();
    }

    arrangedSections.forEach(({ config, $section }) => {
      const hasControls = containerHasVisibleControls($section);
      const presentation = getMoreInfoSectionPresentation(frm, config.key);
      const shouldShow = hasControls && !presentation.hidden;

      $section
        .toggleClass("hide-control", !shouldShow)
        .toggleClass("erpw-so-moreinfo-hidden-source", !shouldShow)
        .toggleClass("erpw-so-moreinfo-section-wide", !!presentation.wide)
        .toggleClass("erpw-so-moreinfo-section-priority", !!presentation.priority)
        .toggleClass("erpw-so-moreinfo-section-quiet", !!presentation.quiet)
        .toggle(shouldShow);

      applyMoreInfoHeaderState($section, presentation);
      if (!shouldShow) return;

      setMoreInfoSectionExpanded(frm, config.fieldname, $section, presentation.expanded !== false);
      applyMoreInfoSectionBodyState(frm, config, $section, presentation);
      bindMoreInfoSectionHeader(frm, config.fieldname, $section);
    });

    $tab.children(".form-section").not($stack.children(".form-section")).each((_, element) => {
      const $section = $(element);
      $section.addClass("erpw-so-moreinfo-hidden-source").hide();
    });

    if (frm.layout && typeof frm.layout.refresh_sections === "function") {
      frm.layout.refresh_sections();
    }
    return seen.size > 0;
  }

  function ensureAddressContactStack($tab) {
    let $stack = $tab.children(".erpw-so-address-stack").first();
    if ($stack.length) return $stack;

    $stack = $('<div class="erpw-so-address-stack"></div>');
    $tab.prepend($stack);
    return $stack;
  }

  function ensureAddressContactSectionHeader($section, config, presentation) {
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
      $status
        .text(statusText)
        .attr("data-tone", statusTone)
        .prop("hidden", false);
    } else {
      $status.text("").removeAttr("data-tone").prop("hidden", true);
    }
  }

  function ensureAddressContactStatePanel($section) {
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

  function getAddressContactSectionPresentation(frm, key) {
    const hasBillingAddress = [frm.doc.customer_address, frm.doc.address_display].some((value) => hasMeaningfulValue(value));
    const hasContactPerson = hasMeaningfulValue(frm.doc.contact_person);
    const hasContactChannel = [frm.doc.contact_phone, frm.doc.contact_mobile, frm.doc.contact_email].some((value) => hasMeaningfulValue(value));
    const hasCustomerContact = hasContactPerson || hasContactChannel;
    const hasShippingAddress = [frm.doc.shipping_address_name, frm.doc.shipping_address].some((value) => hasMeaningfulValue(value));
    const hasDispatchAddress = [frm.doc.dispatch_address_name, frm.doc.dispatch_address].some((value) => hasMeaningfulValue(value));
    const hasCompanyAddress = [frm.doc.company_address, frm.doc.company_address_display].some((value) => hasMeaningfulValue(value));
    const hasCompanyContact = hasMeaningfulValue(frm.doc.company_contact_person);

    const presentations = {
      customer: {
        wide: true,
        priority: true,
        statusTone: hasBillingAddress && hasCustomerContact ? "active" : (!hasBillingAddress || !hasCustomerContact ? "attention" : "neutral"),
        statusText: hasBillingAddress && hasCustomerContact
          ? "Customer ready"
          : hasCustomerContact
            ? "Billing needed"
            : hasBillingAddress
              ? "Contact needed"
              : "Setup needed",
        state: (!hasBillingAddress || !hasCustomerContact) ? {
          title: !hasBillingAddress && !hasCustomerContact
            ? "Billing address and contact are not linked yet"
            : !hasBillingAddress
              ? "Billing address not linked yet"
              : "Primary contact is missing",
          note: !hasBillingAddress && !hasCustomerContact
            ? "Link the billing address and contact before formal confirmation."
            : !hasBillingAddress
              ? "Choose the billing address before invoicing or order confirmation."
              : "Add a contact so confirmation and follow-up have a clear owner.",
          actionLabel: !hasBillingAddress ? "Select billing address" : "Select contact",
          focusField: !hasBillingAddress ? "customer_address" : "contact_person",
        } : null,
      },
      shipping: {
        statusTone: hasShippingAddress ? "active" : (hasDispatchAddress ? "attention" : "neutral"),
        statusText: hasShippingAddress
          ? (hasDispatchAddress ? "Override set" : "Shipping set")
          : hasDispatchAddress
            ? "Dispatch only"
            : "Not set",
        state: !hasShippingAddress ? {
          title: hasDispatchAddress ? "Dispatch override exists without shipping address" : "Shipping address not linked yet",
          note: hasDispatchAddress
            ? "Confirm the delivery destination so the dispatch override stays traceable."
            : "Set the delivery destination once fulfillment is confirmed.",
          actionLabel: "Select shipping address",
          focusField: "shipping_address_name",
        } : null,
      },
      company: {
        quiet: true,
        statusTone: hasCompanyAddress ? "active" : "neutral",
        statusText: hasCompanyAddress ? "Configured" : (hasCompanyContact ? "Contact only" : "Not set"),
        state: !hasCompanyAddress ? {
          title: "Company address is not linked on this order",
          note: "Set the company location only when documents need a different outbound address.",
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

  function resetAddressContactTab($tab) {
    if (!$tab || !$tab.length) return;

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

  function arrangeCustomerContactGrid(frm, $section) {
    if (!$section || !$section.length) return;

    const $body = $section.children(".section-body").first();
    if (!$body.length) return;

    let $grid = $body.children(".erpw-so-address-customer-grid").first();
    if (!$grid.length) {
      $grid = $('<div class="erpw-so-address-customer-grid"></div>');
      const $state = $body.children(".erpw-so-address-state-panel").first();
      if ($state.length) {
        $grid.insertAfter($state);
      } else {
        $body.prepend($grid);
      }
    }

    ["territory", "contact_person", "contact_mobile", "contact_email"].forEach((fieldname) => {
      const $wrapper = getFieldWrapper(frm, fieldname);
      if (!$wrapper || !$wrapper.length || !$wrapper.closest($section).length) return;

      $wrapper
        .addClass("erpw-so-address-grid-field")
        .attr("data-address-grid-field", fieldname)
        .appendTo($grid);
    });

    $body.children(".form-column").each((_, element) => {
      const $column = $(element);
      const hasVisibleContent = containerHasVisibleControls($column);
      $column.toggleClass("erpw-so-address-column-empty", !hasVisibleContent).toggle(hasVisibleContent);
    });

    $grid.toggle(containerHasVisibleControls($grid));
  }

  function enhanceAddressContactTab(frm) {
    if (!frm || !frm.fields_dict) return false;

    const $tab = getTabByFieldname(frm, "contact_info");
    if (!$tab.length) return false;

    resetAddressContactTab($tab);
    $tab.addClass("erpw-so-address-tab");

    const hasBillingAddress = [frm.doc.customer_address, frm.doc.address_display].some((value) => hasMeaningfulValue(value));
    const hasContactPhone = hasMeaningfulValue(frm.doc.contact_phone);
    const hasContactMobile = hasMeaningfulValue(frm.doc.contact_mobile);
    const hasContactEmail = hasMeaningfulValue(frm.doc.contact_email);
    const hasShippingAddress = [frm.doc.shipping_address_name, frm.doc.shipping_address].some((value) => hasMeaningfulValue(value));
    const hasDispatchAddress = [frm.doc.dispatch_address_name, frm.doc.dispatch_address].some((value) => hasMeaningfulValue(value));
    const hasCompanyAddress = [frm.doc.company_address, frm.doc.company_address_display].some((value) => hasMeaningfulValue(value));
    const hasCompanyContact = hasMeaningfulValue(frm.doc.company_contact_person);

    toggleField(frm, "address_display", hasBillingAddress);
    toggleField(frm, "contact_display", false);
    toggleField(frm, "contact_phone", hasContactPhone);
    toggleField(frm, "contact_mobile", hasContactMobile);
    toggleField(frm, "contact_email", hasContactEmail);
    toggleField(frm, "customer_group", false);
    toggleField(frm, "shipping_address", hasShippingAddress);
    toggleField(frm, "dispatch_address_name", hasShippingAddress || hasDispatchAddress);
    toggleField(frm, "dispatch_address", hasDispatchAddress);
    toggleField(frm, "company_address_display", hasCompanyAddress);
    toggleField(frm, "company_contact_person", hasCompanyAddress || hasCompanyContact);

    const configs = [
      {
        key: "customer",
        fieldname: "customer_address",
        title: "Customer Billing & Contact",
        note: "Billing address, territory, and contact for this order.",
        icon: "customer",
      },
      {
        key: "shipping",
        fieldname: "shipping_address_name",
        title: "Shipping & Dispatch",
        note: "Delivery destination and dispatch override for fulfillment.",
        icon: "shipping",
      },
      {
        key: "company",
        fieldname: "company_address",
        title: "Company Address",
        note: "Issuing company location for customer-facing documents.",
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

      const presentation = getAddressContactSectionPresentation(frm, config.key);
      $section
        .addClass(`erpw-so-address-section erpw-so-address-section-${config.key}`)
        .toggleClass("erpw-so-address-section-wide", !!presentation.wide)
        .toggleClass("erpw-so-address-section-priority", !!presentation.priority)
        .toggleClass("erpw-so-address-section-quiet", !!presentation.quiet);

      ensureAddressContactSectionHeader($section, config, presentation);
      applyAddressContactSectionState(frm, $section, presentation);
      $stack.append($section);

      if (config.key === "customer") {
        arrangeCustomerContactGrid(frm, $section);
      }
    });

    $tab.children(".form-section").not($stack.children(".form-section")).each((_, element) => {
      $(element).addClass("erpw-so-address-hidden-source").hide();
    });

    if (frm.layout && typeof frm.layout.refresh_sections === "function") {
      frm.layout.refresh_sections();
    }

    return seen.size > 0;
  }

  function ensureTermsStack($tab) {
    let $stack = $tab.children(".erpw-so-terms-stack").first();
    if ($stack.length) return $stack;

    $stack = $('<div class="erpw-so-terms-stack"></div>');
    $tab.prepend($stack);
    return $stack;
  }

  function ensureTermsSectionHeader($section, config, presentation) {
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
      $status
        .text(statusText)
        .attr("data-tone", statusTone)
        .prop("hidden", false);
    } else {
      $status.text("").removeAttr("data-tone").prop("hidden", true);
    }
  }

  function ensureTermsStatePanel($section) {
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
    const $body = $section.children(".section-body").first();
    if (!$body.length) return $();

    let $metrics = $body.children(".erpw-so-terms-metrics").first();
    if ($metrics.length) return $metrics;

    $metrics = $('<div class="erpw-so-terms-metrics"></div>');
    $body.prepend($metrics);
    return $metrics;
  }

  function ensureTermsAssistNote($section) {
    const $body = $section.children(".section-body").first();
    if (!$body.length) return $();

    let $note = $body.children(".erpw-so-terms-assist-note").first();
    if ($note.length) return $note;

    $note = $('<div class="erpw-so-terms-assist-note" hidden></div>');
    $body.prepend($note);
    return $note;
  }

  function getPaymentScheduleSummary(frm) {
    const rows = Array.isArray(frm.doc.payment_schedule) ? frm.doc.payment_schedule : [];
    const visibleRows = rows.filter((row) => row);
    const milestoneCount = visibleRows.length;
    const scheduledAmount = visibleRows.reduce((sum, row) => sum + Number(row.payment_amount || 0), 0);
    const invoicePortion = visibleRows.reduce((sum, row) => sum + Number(row.invoice_portion || 0), 0);
    const dueDates = visibleRows.map((row) => row.due_date).filter(Boolean).sort();
    return {
      milestoneCount,
      scheduledAmount,
      invoicePortion,
      earliestDue: dueDates[0] || null,
      latestDue: dueDates[dueDates.length - 1] || null,
    };
  }

  function getTermsSectionPresentation(frm, key) {
    const isSubmitted = frm.doc.docstatus === 1;
    const paymentSummary = getPaymentScheduleSummary(frm);
    const hasTemplate = hasMeaningfulValue(frm.doc.payment_terms_template);
    const hasTermsTemplate = hasMeaningfulValue(frm.doc.tc_name);
    const hasTermsText = hasMeaningfulValue(frm.doc.terms);

    const presentations = {
      payment: {
        wide: true,
        priority: true,
        readonly: isSubmitted,
        statusTone: paymentSummary.milestoneCount ? "active" : "attention",
        statusText: paymentSummary.milestoneCount
          ? `${paymentSummary.milestoneCount} milestone${paymentSummary.milestoneCount === 1 ? "" : "s"}`
          : "Schedule needed",
        assistNote: isSubmitted ? "Approved order. Payment schedule is available for review only." : "",
        metrics: paymentSummary.milestoneCount ? [
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
        ] : [],
        state: !paymentSummary.milestoneCount ? (
          isSubmitted ? {
            title: "No payment schedule was recorded on this order",
            note: "This approved order has no editable payment structure.",
          } : {
            title: "Payment schedule is not configured yet",
            note: "Add a payment terms template or define at least one payment milestone.",
            actionLabel: "Select payment terms",
            focusField: "payment_terms_template",
          }
        ) : null,
      },
      conditions: {
        wide: true,
        quiet: !hasTermsTemplate && !hasTermsText,
        readonly: isSubmitted,
        statusTone: hasTermsTemplate || hasTermsText ? "active" : "neutral",
        statusText: hasTermsTemplate ? "Template linked" : (hasTermsText ? "Custom text" : "Not set"),
        state: !hasTermsTemplate && !hasTermsText ? (
          isSubmitted ? {
            title: "No terms and conditions were recorded on this order",
            note: "This approved order has no attached commercial terms.",
          } : {
            title: "No terms and conditions added yet",
            note: "Add a template or custom terms only when this order needs explicit commercial clauses.",
            actionLabel: "Add terms",
            focusField: "tc_name",
            revealFields: true,
          }
        ) : null,
      },
    };

    return presentations[key] || {};
  }

  function applyTermsSectionState(frm, $section, presentation) {
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

  function applyTermsMetrics(frm, $section, presentation) {
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

    const $tab = getTabByFieldname(frm, "payment_schedule_section");
    if (!$tab.length) return false;

    resetTermsTab($tab);
    $tab.addClass("erpw-so-terms-tab");

    const hasPaymentTemplate = hasMeaningfulValue(frm.doc.payment_terms_template);
    const hasTermsTemplate = hasMeaningfulValue(frm.doc.tc_name);
    const hasTermsText = hasMeaningfulValue(frm.doc.terms);

    toggleField(frm, "payment_terms_template", true);
    toggleField(frm, "payment_schedule", true);
    toggleField(frm, "tc_name", hasTermsTemplate || !hasTermsText);
    toggleField(frm, "terms", hasTermsText);

    const configs = [
      {
        key: "payment",
        fieldname: "payment_terms_template",
        title: "Payment Structure",
        note: "Template and milestone schedule for this order.",
        icon: "payment",
      },
      {
        key: "conditions",
        fieldname: "tc_name",
        title: "Terms & Conditions",
        note: "Customer-facing commercial terms for this order.",
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

      const presentation = getTermsSectionPresentation(frm, config.key);
      $section
        .addClass(`erpw-so-terms-section erpw-so-terms-section-${config.key}`)
        .toggleClass("erpw-so-terms-section-wide", !!presentation.wide)
        .toggleClass("erpw-so-terms-section-priority", !!presentation.priority)
        .toggleClass("erpw-so-terms-section-quiet", !!presentation.quiet)
        .toggleClass("erpw-so-terms-section-readonly", !!presentation.readonly);

      ensureTermsSectionHeader($section, config, presentation);
      applyTermsMetrics(frm, $section, presentation);
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

  function cleanSidebarUtilityRail(frm) {
    const $wrapper = $(frm.wrapper || frm.$wrapper || []);
    const $sidebar = $(frm.page && frm.page.sidebar ? frm.page.sidebar : $wrapper.find(".form-sidebar").parent());
    if (!$sidebar.length) return false;

    const $metaSection = $sidebar.find(".sidebar-section.text-muted.border-top.pt-3").first();
    if (!$metaSection.length) return false;

    $metaSection.addClass("erpw-so-sidebar-meta-hidden").hide();
    return true;
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
    } else {
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

    return $head;
  }

  function connectionGroupIconMarkup(key) {
    const icons = {
      fulfillment: `
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M3 7.5h10v7H3zM13 10.5h3l2 2v2h-5zM7 17.5a1.5 1.5 0 1 1-3 0a1.5 1.5 0 0 1 3 0zm11 0a1.5 1.5 0 1 1-3 0a1.5 1.5 0 0 1 3 0z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      `,
      purchasing: `
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M4 6h2l1.4 8h8.9l1.5-5.5H8.1M9.5 18.5a1.25 1.25 0 1 1-2.5 0a1.25 1.25 0 0 1 2.5 0zm7.5 0a1.25 1.25 0 1 1-2.5 0a1.25 1.25 0 0 1 2.5 0z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      `,
      projects: `
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M4 8.5h16v10H4zM9 8.5V6.7c0-.7.6-1.2 1.2-1.2h3.6c.7 0 1.2.5 1.2 1.2v1.8" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      `,
      manufacturing: `
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M12 7.5a4.5 4.5 0 1 1 0 9a4.5 4.5 0 0 1 0-9zm0-4v2.2m0 12.6V20.5M4.9 6.7l1.6 1.3m10.9 8l1.7 1.3M3.5 12h2.2m12.6 0h2.2M4.9 17.3l1.6-1.3m10.9-8l1.7-1.3" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      `,
      reference: `
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M10.5 13.5l3-3M8.2 15.8l-1.6 1.6a3 3 0 1 1-4.2-4.2L4 11.6m11.8-3.4l1.6-1.6a3 3 0 1 1 4.2 4.2L20 12.4" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      `,
      payment: `
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M3.5 7.5h17v9h-17zM3.5 10.5h17M7 14h3" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      `,
      schedule: `
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M7 4.5v3M17 4.5v3M4.5 8h15M5.5 6.5h13a1 1 0 0 1 1 1v11h-15v-11a1 1 0 0 1 1-1zm3.5 5h2.5v2.5H9z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      `,
      "subcontracting-inward": `
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M5 7.5l7-3l7 3M5 7.5v9l7 3l7-3v-9M12 4.5v15M8.5 9.2l7 3.2" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      `,
    };
    return icons[key] || icons.reference;
  }

  function getConnectionsWrapper(frm) {
    if (frm.dashboard && frm.dashboard.links_area && frm.dashboard.links_area.wrapper) {
      const $wrapper = $(frm.dashboard.links_area.wrapper);
      if ($wrapper.length) return $wrapper;
    }

    const $root = $(frm.page && frm.page.main ? frm.page.main : frm.$wrapper || []);
    return $root.find(".form-links").first();
  }

  function getConnectionsRenderScope($wrapper) {
    const $tab = $wrapper.closest(".form-tab");
    if ($tab.length) return $tab;

    const $section = $wrapper.closest(".layout-main-section, .form-page");
    if ($section.length) return $section.first();

    return $wrapper;
  }

  function parseDashboardCount($element, countsReady) {
    if (!$element || !$element.length) {
      return { value: countsReady ? 0 : null, ready: !!countsReady };
    }

    const raw = String($element.text() || "").trim();
    if (!raw) {
      return { value: countsReady ? 0 : null, ready: !!countsReady };
    }
    if (raw === "?") {
      return { value: null, ready: true, unknown: true, display: raw };
    }
    const numeric = Number.parseInt(raw, 10);
    return {
      value: Number.isNaN(numeric) ? null : numeric,
      ready: true,
      unknown: Number.isNaN(numeric),
      display: raw,
    };
  }

  function getConnectionRowStatus(countState, openState, countsReady) {
    if ((openState.value || 0) > 0) {
      return { text: `${openState.value} open`, variant: "attention" };
    }
    if (countState.unknown) {
      return { text: "Linked", variant: "active" };
    }
    if ((countState.value || 0) > 0) {
      return { text: `${countState.value} linked`, variant: "active" };
    }
    return null;
  }

  function getConnectionGroupStatus(groupLinkedTotal, groupOpenTotal, groupHasUnknown, countsReady) {
    if (groupOpenTotal > 0) {
      return { text: `${groupOpenTotal} open`, variant: "attention" };
    }
    if (groupLinkedTotal > 0) {
      return { text: `${groupLinkedTotal} linked`, variant: "active" };
    }
    if (groupHasUnknown) {
      return { text: "Linked", variant: "active" };
    }
    return null;
  }

  function getConnectionStatusRank(status) {
    if (!status) return 0;
    if (status.variant === "attention") return 2;
    if (status.variant === "active") return 1;
    return 0;
  }

  function getConnectionGroupDescription(label) {
    const descriptions = {
      Fulfillment: "Manage orders and deliveries",
      Payment: "Track billing and settlement records",
      Reference: "Create related reference and inventory records",
      Schedule: "Plan delivery timing and milestones",
      Purchasing: "Create purchasing follow-through for this order",
      Projects: "Connect project execution work",
      Manufacturing: "Connect production follow-through",
      "Subcontracting Inward": "Manage subcontractor inward processing",
    };
    return descriptions[label] || "Manage related documents for this order";
  }

  function getConnectionDocDescription(doctype) {
    const descriptions = {
      "Sales Invoice": "Track invoices for this order",
      "Delivery Note": "Manage delivery documentation",
      "Pick List": "Prepare warehouse picking for this order",
      Quotation: "Review source quotation context",
      "Stock Reservation Entry": "Reserve inventory for this order",
      "Delivery Schedule Item": "Plan delivery timeline and milestones",
      "Subcontracting Inward Order": "Create subcontractor inward order",
      "Payment Entry": "Track related payment receipts",
      "Payment Request": "Request customer payment",
      "Journal Entry": "Review linked journal impact",
      "Material Request": "Create downstream material demand",
      "Purchase Order": "Create related purchase orders",
      Project: "Connect project execution",
      "Work Order": "Create manufacturing execution",
      BOM: "Review linked bill of materials",
      "Blanket Order": "Review linked blanket commitment",
      "Maintenance Visit": "Track linked service execution",
      "Auto Repeat": "Manage recurring follow-through",
    };
    return descriptions[doctype] || "Manage related document flow";
  }

  function connectionDocIconMarkup(doctype) {
    const icons = {
      "Sales Invoice": `
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M7 3.5h7l4 4v13H7zM14 3.5v4h4M10 12h5M10 15.5h5M10 19h3" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      `,
      "Delivery Note": `
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M3 7.5h10v7H3zM13 10.5h3l2 2v2h-5zM7 17.5a1.5 1.5 0 1 1-3 0a1.5 1.5 0 0 1 3 0zm11 0a1.5 1.5 0 1 1-3 0a1.5 1.5 0 0 1 3 0z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      `,
      "Stock Reservation Entry": `
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M5 7.5l7-3l7 3M5 7.5v9l7 3l7-3v-9M12 4.5v15M8.5 9.2l7 3.2" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      `,
      "Delivery Schedule Item": `
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M7 4.5v3M17 4.5v3M4.5 8h15M5.5 6.5h13a1 1 0 0 1 1 1v11h-15v-11a1 1 0 0 1 1-1zm3.5 5h2.5v2.5H9z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      `,
      Quotation: `
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M7 3.5h7l4 4v13H7zM14 3.5v4h4M10 12h5M10 15.5h5M10 19h3" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      `,
      "Subcontracting Inward Order": `
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M5 7.5l7-3l7 3M5 7.5v9l7 3l7-3v-9M12 4.5v15M9 12h6" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      `,
    };

    return icons[doctype] || `
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M7 3.5h7l4 4v13H7zM14 3.5v4h4" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    `;
  }

  function getConnectionSourceLink($documents, doctype) {
    return $documents.find(`.document-link[data-doctype="${doctype}"]`).first();
  }

  function buildConnectionsModel($documents, countsReady) {
    const primaryGroups = [];
    const availableItems = [];
    let hasPendingCounts = false;

    $documents.find(".col-md-4").each((_, groupElement) => {
      const $group = $(groupElement);
      const $title = $group.find(".form-link-title").first();
      const rawLabel = $.trim($title.find("span").first().text())
        || $.trim($title.find(".erpw-so-connection-group-title").first().text())
        || $.trim($title.text())
        || "Connections";
      const label = rawLabel
        .replace(/\s+\d+\s+(open|linked)$/i, "")
        .replace(/\s+linked$/i, "")
        .trim();
      const key = label.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
      const groupStatusCounts = { linked: 0, open: 0, unknown: false };
      const primaryItems = [];

      $group.find(".document-link").each((__, linkElement) => {
        const $link = $(linkElement);
        const doctype = $link.attr("data-doctype") || $.trim($link.find(".badge-link").text()) || "Linked Document";
        const countState = parseDashboardCount($link.find(".count").first(), countsReady);
        const openState = parseDashboardCount($link.find(".open-notification").first(), countsReady);
        const status = getConnectionRowStatus(countState, openState, countsReady);
        const $newButton = $link.find(".btn-new");
        const createAllowed = $newButton.length > 0 && !$newButton.hasClass("hidden");
        const countsPending = !countsReady && !countState.ready && !openState.ready;

        if (countState.value != null) groupStatusCounts.linked += countState.value;
        if (openState.value != null) groupStatusCounts.open += openState.value;
        if (countState.unknown) groupStatusCounts.unknown = true;
        if (countsPending) hasPendingCounts = true;

        const item = {
          doctype,
          description: getConnectionDocDescription(doctype),
          status,
          createAllowed,
          countsPending,
        };

        if (status || countsPending) {
          primaryItems.push(item);
        } else if (countsReady && createAllowed) {
          availableItems.push({
            groupLabel: label,
            doctype,
            description: item.description,
          });
        }
      });

      if (primaryItems.length) {
        primaryItems.sort((left, right) => {
          const statusOrder = getConnectionStatusRank(right.status) - getConnectionStatusRank(left.status);
          if (statusOrder !== 0) return statusOrder;
          return left.doctype.localeCompare(right.doctype);
        });

        primaryGroups.push({
          label,
          key,
          description: getConnectionGroupDescription(label),
          status: getConnectionGroupStatus(
            groupStatusCounts.linked,
            groupStatusCounts.open,
            groupStatusCounts.unknown,
            countsReady
          ),
          countsPending: primaryItems.some((item) => item.countsPending),
          items: primaryItems,
        });
      }
    });

    primaryGroups.sort((left, right) => {
      const statusOrder = getConnectionStatusRank(right.status) - getConnectionStatusRank(left.status);
      if (statusOrder !== 0) return statusOrder;
      return left.label.localeCompare(right.label);
    });

    availableItems.sort((left, right) => {
      const groupOrder = left.groupLabel.localeCompare(right.groupLabel);
      if (groupOrder !== 0) return groupOrder;
      return left.doctype.localeCompare(right.doctype);
    });

    return { primaryGroups, availableItems, countsReady, hasPendingCounts };
  }

  function renderConnectionsLoadingState() {
    return `
      <section class="erpw-so-connections-loading-shell">
        <div class="erpw-so-connections-loading-title">Loading relationship status</div>
        <div class="erpw-so-connections-loading-note">Checking linked downstream documents and available creation paths for this order.</div>
      </section>
    `;
  }

  function renderConnectionsPendingState() {
    return `
      <div class="erpw-so-connections-pending-note">Live counts are updating. You can already open related lists.</div>
    `;
  }

  function renderConnectionsEmptyState(model) {
    if (!model.countsReady || model.primaryGroups.length || model.availableItems.length) {
      return "";
    }

    return `
      <section class="erpw-so-connections-empty">
        <div class="erpw-so-connections-empty-title">No linked downstream documents yet</div>
        <div class="erpw-so-connections-empty-note">Create the next related record when execution moves forward from this order.</div>
      </section>
    `;
  }

  function renderConnectionsWorkspace($wrapper, frm, $documents, model) {
    const $body = $wrapper.find(".section-body").first().length ? $wrapper.find(".section-body").first() : $wrapper;
    const $scope = getConnectionsRenderScope($wrapper);
    $scope.find(".erpw-so-connections-workspace").remove();
    const $workspace = $('<div class="erpw-so-connections-workspace"></div>');
    $workspace.insertBefore($documents);

    if (!model.primaryGroups.length && !model.availableItems.length) {
      $workspace.html(renderConnectionsLoadingState());
      return;
    }

    $workspace.html(`
      ${!model.countsReady && model.hasPendingCounts ? renderConnectionsPendingState() : ""}
      ${model.primaryGroups.map((group, groupIndex) => `
        <section class="erpw-so-connection-primary-group" data-group-index="${groupIndex}" data-group-key="${escapeHtml(group.key)}">
          <div class="erpw-so-connection-primary-head">
            <div class="erpw-so-connection-primary-summary">
              <span class="erpw-so-connection-primary-icon" aria-hidden="true">${connectionGroupIconMarkup(group.key)}</span>
              <div class="erpw-so-connection-primary-copy">
                <div class="erpw-so-connection-primary-title">${escapeHtml(group.label)}</div>
                <div class="erpw-so-connection-primary-note">${escapeHtml(group.description)}</div>
              </div>
            </div>
            ${group.status ? `<div class="erpw-so-connection-primary-status" data-status="${escapeHtml(group.status.variant)}">${escapeHtml(group.status.text)}</div>` : ""}
          </div>
          <div class="erpw-so-connection-primary-grid" data-item-count="${group.items.length}">
            ${group.items.map((item, itemIndex) => `
              <article class="erpw-so-connection-doc-card" data-group-index="${groupIndex}" data-item-index="${itemIndex}" data-doctype="${escapeHtml(item.doctype)}">
                <div class="erpw-so-connection-doc-head">
                  <div class="erpw-so-connection-doc-main">
                    <span class="erpw-so-connection-doc-icon" aria-hidden="true">${connectionDocIconMarkup(item.doctype)}</span>
                    <div class="erpw-so-connection-doc-copy">
                      <div class="erpw-so-connection-doc-title">${escapeHtml(item.doctype)}</div>
                      <div class="erpw-so-connection-doc-note">${escapeHtml(item.description)}</div>
                    </div>
                  </div>
                  ${item.status ? `<div class="erpw-so-connection-doc-status" data-status="${escapeHtml(item.status.variant)}">${escapeHtml(item.status.text)}</div>` : ""}
                </div>
                <div class="erpw-so-connection-doc-actions">
                  <button type="button" class="erpw-so-connection-action erpw-so-connection-action-primary" data-action="open" data-doctype="${escapeHtml(item.doctype)}">${item.countsPending ? "Open list" : "View linked"}</button>
                  ${item.createAllowed ? `<button type="button" class="erpw-so-connection-action erpw-so-connection-action-secondary" data-action="create" data-doctype="${escapeHtml(item.doctype)}">Create new</button>` : ""}
                </div>
              </article>
            `).join("")}
          </div>
        </section>
      `).join("")}

      ${model.availableItems.length ? `
        <section class="erpw-so-connections-secondary-shell">
          <div class="erpw-so-connections-secondary-head">
            <span class="erpw-so-connections-secondary-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24"><path d="M7.5 12h9M12 7.5l4.5 4.5L12 16.5M6 5.5h12a1.5 1.5 0 0 1 1.5 1.5v10A1.5 1.5 0 0 1 18 18.5H6A1.5 1.5 0 0 1 4.5 17V7A1.5 1.5 0 0 1 6 5.5z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
            </span>
            <div class="erpw-so-connections-secondary-copy">
              <div class="erpw-so-connections-secondary-title">Available Paths</div>
              <div class="erpw-so-connections-secondary-note">Create the next related document only when execution needs it.</div>
            </div>
          </div>
          <div class="erpw-so-connections-secondary-rows">
            ${model.availableItems.map((item, itemIndex) => `
              <div class="erpw-so-connections-secondary-row" data-available-index="${itemIndex}" data-doctype="${escapeHtml(item.doctype)}">
                <div class="erpw-so-connections-secondary-row-copy">
                  <div class="erpw-so-connections-secondary-row-title">${escapeHtml(item.doctype)}</div>
                  <div class="erpw-so-connections-secondary-row-note">${escapeHtml(item.description)}</div>
                </div>
                <button type="button" class="erpw-so-connection-action erpw-so-connection-action-tertiary" data-action="create" data-doctype="${escapeHtml(item.doctype)}">Create</button>
              </div>
            `).join("")}
          </div>
        </section>
      ` : ""}

      ${renderConnectionsEmptyState(model)}
    `);

    $workspace.find('[data-action="open"]').off("click").on("click", function () {
      const doctype = $(this).attr("data-doctype");
      if (!doctype) return;
      const $sourceLink = getConnectionSourceLink($documents, doctype);
      if (!$sourceLink.length) return;
      frm.dashboard.open_document_list($sourceLink);
    });

    $workspace.find('[data-action="create"]').off("click").on("click", function () {
      const doctype = $(this).attr("data-doctype");
      if (!doctype) return;
      frm.make_new(doctype);
    });
  }

  function enhanceConnectionsWorkspace(frm) {
    if (!frm || !frm.dashboard) return false;

    const $wrapper = getConnectionsWrapper(frm);
    if (!$wrapper.length) return false;

    const $documents = $wrapper.find(".form-documents").first();
    if (!$documents.length) return false;

    $wrapper.addClass("erpw-so-connections-shell");
    getConnectionsRenderScope($wrapper).find(".erpw-so-connections-workspace, .erpw-so-connections-secondary, .erpw-so-connections-empty").remove();
    $documents.removeClass("erpw-so-connections-documents has-single-group is-empty").addClass("erpw-so-connections-source");
    const countsReady = Boolean(frm.dashboard && frm.dashboard._fetched_counts);
    if (!countsReady) {
      requestConnectionsCounts(frm);
    }
    const model = buildConnectionsModel($documents, countsReady);
    renderConnectionsWorkspace($wrapper, frm, $documents, model);
    return true;
  }

  function enhanceSupportArea(frm) {
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

  function enhanceWorkflowReadonlyBanner(frm) {
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
            <div class="erpw-so-workflow-banner-title">Workflow-controlled record</div>
            <div class="erpw-so-workflow-banner-note">This Sales Order is currently review-only in the active workflow state.</div>
          </div>
        </div>
      `);
    }

    return true;
  }

  function bindTabEnhancers(frm) {
    if (!frm) return;
    const $root = $(frm.page && frm.page.main ? frm.page.main : frm.$wrapper || []);
    if (!$root.length) return;

    const $links = $root.find(".form-tabs-list .nav-link, .form-tabs .nav-link");
    if (!$links.length) return;

    $links.off(".erpwTabEnhancers").on("click.erpwTabEnhancers", function () {
      scheduleFormTask(frm, "tab_enhancers_fast", 0, () => {
        enhanceAddressContactTab(frm);
        enhanceTermsTab(frm);
        enhanceMoreInfoTab(frm);
        enhanceConnectionsWorkspace(frm);
      });
      scheduleFormTask(frm, "tab_enhancers_late", 180, () => {
        enhanceAddressContactTab(frm);
        enhanceTermsTab(frm);
        enhanceMoreInfoTab(frm);
        enhanceConnectionsWorkspace(frm);
      });
    });
  }

  function enhanceFormBody(frm) {
    if (!frm || !frm.fields_dict) return;

    const $root = getFormRoot(frm);
    if ($root.length) {
      $root.addClass("erpw-so-form-enhanced");
    }

    bindTabEnhancers(frm);

    markSection(frm, "customer", "erpw-so-section-primary erpw-so-section-basics");
    markSection(frm, "currency", "erpw-so-section-secondary erpw-so-section-pricing");
    markSection(frm, "items", "erpw-so-section-primary erpw-so-section-items");
    markSection(frm, "total_qty", "erpw-so-section-summary erpw-so-section-commercial-snapshot");
    markSection(frm, "taxes", "erpw-so-section-secondary erpw-so-section-taxes");
    markSection(frm, "grand_total", "erpw-so-section-summary");
    markSection(frm, "apply_discount_on", "erpw-so-section-quiet erpw-so-section-discount");

    [
      "workflow_state",
      "naming_series",
      "customer_name",
      "tax_id",
      "has_unit_price_items",
      "amended_from",
      "base_in_words",
      "in_words",
      "disable_rounded_total",
    ].forEach((fieldname) => toggleField(frm, fieldname, false));

    const sameCurrency = usesCompanyCurrencyOnly(frm);
    [
      "base_total",
      "base_net_total",
      "base_total_taxes_and_charges",
      "base_grand_total",
      "base_rounding_adjustment",
      "base_rounded_total",
      "base_discount_amount",
    ].forEach((fieldname) => toggleField(frm, fieldname, !sameCurrency));

    [
      "total_qty",
      "total",
      "total_taxes_and_charges",
      "grand_total",
    ].forEach((fieldname) => toggleField(frm, fieldname, false));

    toggleField(frm, "total_net_weight", hasMeaningfulValue(frm.doc.total_net_weight));
    toggleField(frm, "advance_paid", hasMeaningfulValue(frm.doc.advance_paid));
    toggleField(frm, "rounding_adjustment", hasMeaningfulValue(frm.doc.rounding_adjustment));
    toggleField(frm, "rounded_total", hasMeaningfulValue(frm.doc.rounded_total) && hasMeaningfulValue(frm.doc.rounding_adjustment));

    const showAccountingDimensions = hasMeaningfulValue(frm.doc.cost_center) || hasMeaningfulValue(frm.doc.project);
    toggleSection(frm, "cost_center", showAccountingDimensions);

    const showWarehouseSetup = [
      "scan_barcode",
      "last_scanned_warehouse",
      "set_warehouse",
    ].some((fieldname) => hasMeaningfulValue(frm.doc[fieldname])) || Boolean(frm.doc.reserve_stock);
    toggleSection(frm, "scan_barcode", showWarehouseSetup);

    const showDiscount = [
      "additional_discount_percentage",
      "discount_amount",
      "base_discount_amount",
      "coupon_code",
    ].some((fieldname) => hasMeaningfulValue(frm.doc[fieldname]));
    const showPricing = shouldShowPricingSection(frm);
    toggleSection(frm, "currency", showPricing);
    toggleSection(frm, "apply_discount_on", showDiscount);

    const showTotalsDetail = [
      "advance_paid",
      "rounding_adjustment",
      "rounded_total",
    ].some((fieldname) => hasMeaningfulValue(frm.doc[fieldname]));
    toggleSection(frm, "total_qty", false);
    toggleSection(frm, "grand_total", showTotalsDetail);

    renderCommercialSummary(frm);
    if (!enhanceAddressContactTab(frm)) {
      scheduleFormTask(frm, "address_contact_retry_fast", 420, () => enhanceAddressContactTab(frm));
      scheduleFormTask(frm, "address_contact_retry_late", 980, () => enhanceAddressContactTab(frm));
    }
    if (!enhanceTermsTab(frm)) {
      scheduleFormTask(frm, "terms_retry_fast", 420, () => enhanceTermsTab(frm));
      scheduleFormTask(frm, "terms_retry_late", 980, () => enhanceTermsTab(frm));
    }
    if (!enhanceMoreInfoTab(frm)) {
      scheduleFormTask(frm, "more_info_retry_fast", 420, () => enhanceMoreInfoTab(frm));
      scheduleFormTask(frm, "more_info_retry_late", 980, () => enhanceMoreInfoTab(frm));
    }
    if (!cleanSidebarUtilityRail(frm)) {
      scheduleFormTask(frm, "sidebar_retry_fast", 420, () => cleanSidebarUtilityRail(frm));
      scheduleFormTask(frm, "sidebar_retry_late", 980, () => cleanSidebarUtilityRail(frm));
    }
    const supportReady = enhanceSupportArea(frm);
    const shellReady = isCustomShellReadyForRelease(frm);
    if (!supportReady) {
      scheduleFormTask(frm, "support_retry_fast", 420, () => enhanceSupportArea(frm));
      scheduleFormTask(frm, "support_retry_late", 980, () => enhanceSupportArea(frm));
    }
    if (!enhanceWorkflowReadonlyBanner(frm)) {
      scheduleFormTask(frm, "workflow_banner_retry_fast", 220, () => enhanceWorkflowReadonlyBanner(frm));
      scheduleFormTask(frm, "workflow_banner_retry_late", 760, () => enhanceWorkflowReadonlyBanner(frm));
    }
    if (!enhanceConnectionsWorkspace(frm)) {
      scheduleConnectionsEnhance(frm);
      scheduleFormTask(frm, "connections_retry_late", 980, () => enhanceConnectionsWorkspace(frm));
    }

    if (!shellReady) {
      return;
    }

    releasePreparedShell(frm);
  }

  function renderCommercialSummary(frm) {
    const $itemsSection = getSectionForField(frm, "items");
    if (!$itemsSection || !$itemsSection.length) return;

    $itemsSection.find(".erpw-so-inline-summary").remove();

    const metrics = [
      {
        label: "Quantity",
        value: hasMeaningfulValue(frm.doc.total_qty) ? String(frm.doc.total_qty) : "--",
        modifier: "qty",
      },
      {
        label: "Items Total",
        value: formatMoney(frm.doc.total, frm.doc.currency),
        modifier: "items-total",
      },
      {
        label: "Taxes",
        value: formatMoney(frm.doc.total_taxes_and_charges, frm.doc.currency),
        modifier: "taxes",
      },
      {
        label: "Grand Total",
        value: formatMoney(frm.doc.grand_total, frm.doc.currency),
        modifier: "grand",
      },
    ];

    const $summary = $(`
      <div class="erpw-so-inline-summary">
        <div class="erpw-so-inline-summary-head">
          <div class="erpw-so-inline-summary-title">Commercial Summary</div>
        </div>
        <div class="erpw-so-inline-summary-grid">
          ${metrics.map((metric) => `
            <div class="erpw-so-inline-metric ${metric.modifier ? `erpw-so-inline-metric-${metric.modifier}` : ""}">
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

  function renderShell(frm, data) {
    const summary = data.summary || {};
    const linked = data.linked_documents || {};
    const support = data.support || {};
    const $shell = getShell(frm);

    const statusChipClass = String(summary.workflow_state || "").includes("Pending") ? "pending" : "approved";
    const dueSoon = summary.delivery_date && frappe.datetime.get_diff(summary.delivery_date, frappe.datetime.get_today()) <= 3 && Number(summary.per_delivered || 0) === 0;
    const blocker = String(summary.workflow_state || "").includes("Pending");
    const returnCount = Array.isArray(linked.returns) ? linked.returns.length : 0;
    const actions = actionConfig(frm, data);
    const links = linkConfig(data);
    const deliveryStage = blocker ? "Approval gate" : Number(summary.per_delivered || 0) >= 100 ? "Delivered" : Number(summary.per_delivered || 0) > 0 ? "In progress" : "Queued";
    const deliveryDateMeta = dueSoon ? "Due soon" : "";
    const billingStage = Number(summary.per_billed || 0) >= 100
      ? "Fully billed"
      : Number(summary.per_billed || 0) > 0
        ? "Partly billed"
        : (summary.billing_status || "Not billed");
    const executionValue = blocker ? "Approval gate" : `${pct(summary.per_delivered)} delivered`;
    const executionMeta = blocker
      ? `${pct(summary.per_billed)} billed`
      : `${pct(summary.per_billed)} billed`;
    $shell.html(`
      <section class="erpw-child-card erpw-child-summary">
        <div class="erpw-child-summary-copy">
          <div class="erpw-child-summary-top">
            <div class="erpw-child-summary-main">
              <div class="erpw-child-kicker">Sales Order</div>
              <h2 class="erpw-child-title">${escapeHtml(summary.name || frm.doc.name || "Sales Order")}</h2>
              <div class="erpw-child-subtitle">${escapeHtml(summary.customer || "Customer not selected yet")}</div>
            </div>
            <div class="erpw-child-chip-row erpw-child-chip-row-header">
              <span class="erpw-child-chip ${statusChipClass}">${escapeHtml(summary.status || "Draft")}</span>
              <span class="erpw-child-chip ${statusChipClass}">${escapeHtml(summary.workflow_state || "Draft")}</span>
              ${dueSoon ? '<span class="erpw-child-chip attention">Due Soon</span>' : ""}
              ${returnCount ? `<span class="erpw-child-chip blocker">${escapeHtml(`${returnCount} Return Linked`)}</span>` : ""}
            </div>
          </div>
        </div>
        <div class="erpw-child-summary-facts">
          <div class="erpw-child-fact">
            <div class="erpw-child-fact-label">Grand Total</div>
            <div class="erpw-child-fact-value">${escapeHtml(formatMoney(summary.grand_total, summary.currency))}</div>
          </div>
          <div class="erpw-child-fact">
            <div class="erpw-child-fact-label">Delivery Date</div>
            <div class="erpw-child-fact-value">${escapeHtml(summary.delivery_date || "--")}</div>
            ${deliveryDateMeta ? `<div class="erpw-child-fact-meta">${escapeHtml(deliveryDateMeta)}</div>` : ""}
          </div>
          <div class="erpw-child-fact">
            <div class="erpw-child-fact-label">Execution</div>
            <div class="erpw-child-fact-value">${escapeHtml(executionValue)}</div>
            <div class="erpw-child-fact-meta">${escapeHtml(executionMeta)}</div>
          </div>
        </div>
      </section>

      <section class="erpw-child-card erpw-child-actions erpw-child-actions-band">
        <div class="erpw-child-action-row erpw-child-action-row-single">
          ${actions.map((action, idx) => `
            <button type="button" class="erpw-child-action ${escapeHtml(action.variant || "secondary")}" data-action-index="${idx}">
              <span class="erpw-child-action-accent" aria-hidden="true">${actionIconMarkup(action.icon)}</span>
              <span class="erpw-child-action-copy">
                <span class="erpw-child-action-title">${escapeHtml(action.title)}</span>
              </span>
            </button>
          `).join("")}
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
            <div class="erpw-child-guidance-text">${escapeHtml(support.next_action || "Continue normal execution follow-through.")}</div>
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
            <div class="erpw-child-guidance-text">${escapeHtml(support.customer_response_hint || "Use linked delivery and invoice context before confirming customer-facing status.")}</div>
          </article>
        </div>
      </section>
    `);

    actions.forEach((action, idx) => {
      $shell.find(`[data-action-index="${idx}"]`).on("click", action.handler);
    });
    $shell.find("[data-link-doctype][data-link-name]").on("click", function () {
      routeToDoc($(this).attr("data-link-doctype"), $(this).attr("data-link-name"));
    });
  }

  function showLoading(frm, message) {
    showShellSkeleton(frm);
  }

  function loadContext(frm) {
    if (!frm || frm.doctype !== "Sales Order") return;
    const signature = getContextSignature(frm);
    if (frm.__erpwContextLoadingSignature === signature) return;
    if (frm.__erpwContextRenderedSignature === signature) {
      prepareFormShell(frm, "Loading sales order execution context...");
      scheduleFormEnhance(frm);
      return;
    }

    prepareFormShell(frm, "Loading sales order execution context...");

    if (frm.is_new()) {
      renderShell(frm, draftContext(frm));
      frm.__erpwContextRenderedSignature = signature;
      frm.__erpwContextLoadingSignature = null;
      scheduleFormEnhance(frm);
      return;
    }

    const $shell = getShell(frm);
    if (!$shell.children().length || frm.__erpwContextRenderedName !== frm.doc.name) {
      showLoading(frm, "Loading sales order execution context...");
    }

    const requestId = (frm.__erpwContextRequestId || 0) + 1;
    frm.__erpwContextRequestId = requestId;
    frm.__erpwContextLoadingSignature = signature;
    frappe.call({
      method: METHOD,
      args: { name: frm.doc.name },
      freeze: false,
    }).then((r) => {
      if (frm.__erpwContextRequestId !== requestId) return;
      if (!frm.doc || frm.doc.name !== (r.message && r.message.summary && r.message.summary.name)) {
        return;
      }
      renderShell(frm, r.message || draftContext(frm));
      frm.__erpwContextRenderedSignature = signature;
      frm.__erpwContextRenderedName = frm.doc.name;
      scheduleFormEnhance(frm);
    }).catch(() => {
      if (frm.__erpwContextRequestId !== requestId) return;
      getShell(frm).html('<section class="erpw-child-card erpw-child-loading">Sales order workspace context is temporarily unavailable.</section>');
      scheduleFormEnhance(frm);
    }).finally(() => {
      if (frm.__erpwContextRequestId === requestId) {
        frm.__erpwContextLoadingSignature = null;
      }
    });
  }

  frappe.ui.form.on("Sales Order", {
    setup(frm) {
      prepareFormShell(frm, "Loading sales order execution context...");
    },
    before_load(frm) {
      prepareFormShell(frm, "Loading sales order execution context...");
    },
    onload(frm) {
      prepareFormShell(frm, "Loading sales order execution context...");
    },
    refresh(frm) {
      loadContext(frm);
      scheduleFormTask(frm, "post_refresh_enhance", 160, () => enhanceFormBody(frm));
    },
    dashboard_update(frm) {
      scheduleConnectionsEnhance(frm);
    },
  });

  function bootstrapCurrentSalesOrderForm() {
    if (!window.cur_frm || cur_frm.doctype !== "Sales Order") return;
    if (!cur_frm.page || !cur_frm.page.main) return;
    loadContext(cur_frm);
  }

  $(document).ready(() => {
    setTimeout(bootstrapCurrentSalesOrderForm, 120);
  });
})();
