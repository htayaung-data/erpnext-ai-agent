(function () {
  const METHOD = "erp_workspace_ui.api.get_delivery_note_page_context";
  const childPageRuntime = window.erpWorkspaceUiChildPage || {};
  const childPageHelpers = childPageRuntime.helpers || {};
  const childPageShell = childPageRuntime.shell || {};
  const childPageLifecycle = childPageRuntime.runtime || {};
  const childPageConnections = childPageRuntime.connections || {};
  const childPageSections = childPageRuntime.sections || {};
  const childPageDetails = childPageRuntime.details || {};
  const childPageTerms = childPageRuntime.terms || {};
  const childPageSummaries = childPageRuntime.summaries || {};
  const childPageSupport = childPageRuntime.support || {};
  const childPageSidebar = childPageRuntime.sidebar || {};
  const childPageShellContent = childPageRuntime.shellContent || {};

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

  function routeToDoc(doctype, name) {
    if (!doctype || !name) return;
    const helpers = window.erpWorkspaceUiChildPage && window.erpWorkspaceUiChildPage.helpers;
    if (
      helpers
      && typeof helpers.routeToSalesConsoleTarget === "function"
      && helpers.routeToSalesConsoleTarget({ kind: "form", doctype, name })
    ) {
      return;
    }
    frappe.set_route("Form", doctype, name);
  }

  function routeToList(doctype, filters) {
    const helpers = window.erpWorkspaceUiChildPage && window.erpWorkspaceUiChildPage.helpers;
    if (
      helpers
      && typeof helpers.routeToSalesConsoleTarget === "function"
      && helpers.routeToSalesConsoleTarget({ kind: "list", doctype, filters })
    ) {
      return;
    }
    frappe.route_options = filters && Object.keys(filters).length ? filters : null;
    frappe.set_route("List", doctype);
  }
  const applySalesConsoleDocumentActionPolicy = childPageHelpers.applySalesConsoleDocumentActionPolicy || function (actions) {
    return (Array.isArray(actions) ? actions : []).filter((action) => {
      if (!action) return false;
      const category = String(action.category || "").trim();
      if (["linked_document", "reference_document", "supporting_navigation"].includes(category)) return false;
      if (category === "follow_up") return !!action.attention;
      return category === "primary_business_action" || category === "business_next_step";
    }).slice(0, 2);
  };
  const applySalesConsoleGuidancePolicy = childPageHelpers.applySalesConsoleGuidancePolicy || function (cards) {
    return (Array.isArray(cards) ? cards : []).filter((card) => card && (card.attention || card.priority)).slice(0, 2);
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

  function pct(value) {
    const numeric = Number(value || 0);
    return `${Math.round(numeric)}%`;
  }

  function ensureDeliveryNoteCriticalStyles() {
    if (typeof childPageDetails.ensureCriticalStyles === "function") {
      childPageDetails.ensureCriticalStyles();
    }
  }

  function getPrintLanguageLabel(value) {
    const normalized = String(value || "").trim();
    if (!normalized) return "Default";

    const labels = {
      en: "English",
      my: "Burmese",
    };

    return labels[normalized.toLowerCase()] || normalized;
  }

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
      shellClasses: ["erpws-order-shell", "erpwdn-delivery-shell"],
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
      doc.customer || "",
      doc.posting_date || "",
      doc.posting_time || "",
      doc.grand_total == null ? "" : String(doc.grand_total),
      doc.total_qty == null ? "" : String(doc.total_qty),
      doc.per_billed == null ? "" : String(doc.per_billed),
      doc.per_returned == null ? "" : String(doc.per_returned),
      doc.is_return == null ? "" : String(doc.is_return),
      doc.return_against || "",
      doc.set_warehouse || "",
      doc.set_target_warehouse || "",
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
      ? $mount.siblings(".erpw-child-shell.erpwdn-delivery-shell").first()
      : $root.children(".erpw-child-shell.erpwdn-delivery-shell").first();

    if (!$shell.length) {
      $shell = $('<div class="erpw-child-shell erpwdn-delivery-shell"></div>');
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

  function showShellSkeleton(frm) {
    if (typeof childPageShell.showShellSkeleton === "function") {
      return childPageShell.showShellSkeleton(frm, getShellOptions());
    }

    const $shell = getShell(frm);
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
      loadingMessage: "Loading delivery note execution context...",
    });
    const prepareShell = childPageShell.prepareShell || showShellSkeleton;
    prepareShell(frm, getShellOptions());
    markFeatureReady(frm, "shell_prepare", {
      loadingMessage: "Loading delivery note execution context...",
    });
  }

  function getFieldWrapper(frm, fieldname) {
    const field = frm.fields_dict && frm.fields_dict[fieldname];
    if (!field) return null;
    const $wrapper = field.$wrapper && field.$wrapper.length ? field.$wrapper : $(field.wrapper || []);
    return $wrapper.length ? $wrapper : null;
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

  function setTabVisibility(frm, fieldname, visible) {
    const $root = $(frm.page && frm.page.main ? frm.page.main : frm.$wrapper || []);
    if (!$root.length) return;

    const shouldShow = Boolean(visible);
    const $tabLink = $root.find(`.form-tabs .nav-link[data-fieldname="${fieldname}"], .form-tabs-list .nav-link[data-fieldname="${fieldname}"]`).first();
    const $tab = getTabByFieldname(frm, fieldname);

    if ($tabLink.length) {
      $tabLink.toggle(shouldShow);
      $tabLink.closest(".nav-item, li").toggle(shouldShow);
    }
    if ($tab.length) {
      if (shouldShow) {
        $tab.removeAttr("hidden");
        if (!$tab.hasClass("active")) {
          $tab.css("display", "");
        }
      } else {
        $tab.attr("hidden", "hidden").removeClass("show active").css("display", "none");
        if ($tabLink.hasClass("active")) {
          const $fallbackLink = $root
            .find(".form-tabs .nav-link:visible, .form-tabs-list .nav-link:visible")
            .not($tabLink)
            .first();
          if ($fallbackLink.length) {
            $fallbackLink.trigger("click");
          }
        }
      }
    }
  }

  function hasMeaningfulValue(value) {
    if (value == null) return false;
    if (Array.isArray(value)) return value.length > 0;
    if (typeof value === "number") return value !== 0;
    if (typeof value === "boolean") return value;
    const normalized = String(value).trim();
    return normalized !== "" && normalized !== "0";
  }

  function normalizeComparableText(value) {
    return String(value == null ? "" : value)
      .trim()
      .replace(/\s+/g, " ")
      .toLowerCase();
  }

  function toggleField(frm, fieldname, visible) {
    const field = frm && frm.fields_dict ? frm.fields_dict[fieldname] : null;
    if (!field) return;

    if (typeof field.toggle === "function") {
      field.toggle(Boolean(visible));
    } else if (field.df) {
      field.df.hidden = visible ? 0 : 1;
      if (typeof field.refresh === "function") {
        field.refresh();
      }
    }
  }

  function setFieldPrecision(frm, fieldname, precision) {
    const field = frm && frm.fields_dict ? frm.fields_dict[fieldname] : null;
    if (!field || !field.df) return;

    field.df.precision = precision;
    if (typeof field.refresh === "function") {
      field.refresh();
    }
  }

  function focusField(frm, fieldname) {
    const field = frm && frm.fields_dict ? frm.fields_dict[fieldname] : null;
    const $wrapper = getFieldWrapper(frm, fieldname);

    if ($wrapper && $wrapper.length) {
      $(frm.page && frm.page.main ? frm.page.main : frm.$wrapper || []).find(".erpw-so-address-focus-target")
        .removeClass("erpw-so-address-focus-target");
      $wrapper.addClass("erpw-so-address-focus-target");
      const node = $wrapper.get(0);
      if (node && typeof node.scrollIntoView === "function") {
        node.scrollIntoView({ behavior: "smooth", block: "center" });
      }
      setTimeout(() => $wrapper.removeClass("erpw-so-address-focus-target"), 2200);
    }

    if (field && typeof field.focus === "function") {
      try {
        field.focus();
      } catch (error) {
        // Some Frappe fields do not expose a stable focus method.
      }
    }
  }

  function setManagedSectionVisibility($section, visible, className) {
    if (!$section || !$section.length) return;
    const markerClass = String(className || "erpwdn-managed-hidden").trim();
    if (!markerClass) return;

    if (visible) {
      $section.removeClass(markerClass).show();
      return;
    }

    $section.addClass(markerClass).hide();
  }

  function nearlyEqual(left, right, epsilon) {
    const a = Number(left || 0);
    const b = Number(right || 0);
    return Math.abs(a - b) <= (epsilon == null ? 0.0001 : Number(epsilon));
  }

  function hasDeliveryPriceSignal(frm) {
    const companyCurrency = frappe.defaults.get_default("currency");
    const currency = String(frm.doc.currency || "").trim();
    const priceListCurrency = String(frm.doc.price_list_currency || "").trim();
    const companyCurrencyMismatch = currency && companyCurrency
      ? normalizeComparableText(currency) !== normalizeComparableText(companyCurrency)
      : false;
    const priceCurrencyMismatch = priceListCurrency && currency
      ? normalizeComparableText(priceListCurrency) !== normalizeComparableText(currency)
      : false;
    const exchangeVariance = !nearlyEqual(frm.doc.conversion_rate || 1, 1)
      || !nearlyEqual(frm.doc.plc_conversion_rate || 1, 1);

    return companyCurrencyMismatch || priceCurrencyMismatch || exchangeVariance;
  }

  function hasAdditionalDiscountSignal(frm) {
    return Number(frm.doc.additional_discount_percentage || 0) !== 0
      || Number(frm.doc.discount_amount || 0) !== 0;
  }

  function hasTaxesSignal(frm) {
    return (Array.isArray(frm.doc.taxes) && frm.doc.taxes.length > 0)
      || Number(frm.doc.total_taxes_and_charges || 0) !== 0
      || hasMeaningfulValue(frm.doc.taxes_and_charges);
  }

  function hasPackedItemsSignal(frm) {
    return Array.isArray(frm.doc.packed_items) && frm.doc.packed_items.length > 0;
  }

  function hasPricingSignal(frm) {
    return Number(frm.doc.ignore_pricing_rule || 0) === 1
      || hasMeaningfulValue(frm.doc.pricing_rules)
      || hasMeaningfulValue(frm.doc.pricing_rule_details);
  }

  function hasTaxBreakupSignal(frm) {
    return hasMeaningfulValue(frm.doc.item_wise_tax_details);
  }

  function hasNetWeightSignal(frm) {
    return Number(frm.doc.total_net_weight || 0) !== 0;
  }

  function enhanceDetailsGovernance(frm) {
    if (!frm || !frm.fields_dict) {
      markFeatureMissing(frm, "details_governance", { reason: "missing_form" });
      return false;
    }

    const isSubmitted = Number(frm.doc.docstatus || 0) === 1;
    const warehouseNames = uniqueMeaningfulValues((Array.isArray(frm.doc.items) ? frm.doc.items : []).map((item) => item && item.warehouse));
    const hideDuplicateSourceWarehouse = isSubmitted
      && warehouseNames.length === 1
      && hasMeaningfulValue(frm.doc.set_warehouse)
      && warehouseNames[0] === frm.doc.set_warehouse;
    const managedSections = [
      {
        fieldname: "currency",
        visible: !isSubmitted || hasDeliveryPriceSignal(frm),
      },
      {
        fieldname: "taxes",
        visible: !isSubmitted || hasTaxesSignal(frm),
      },
      {
        fieldname: "total_taxes_and_charges",
        visible: !isSubmitted || hasTaxesSignal(frm),
      },
      {
        fieldname: "apply_discount_on",
        visible: !isSubmitted || hasAdditionalDiscountSignal(frm),
      },
      {
        fieldname: "packed_items",
        visible: !isSubmitted || hasPackedItemsSignal(frm),
      },
      {
        fieldname: "pricing_rules",
        visible: !isSubmitted || hasPricingSignal(frm),
      },
      {
        fieldname: "item_wise_tax_details",
        visible: !isSubmitted || hasTaxBreakupSignal(frm),
      },
    ];

    managedSections.forEach((config) => {
      const $section = getSectionForField(frm, config.fieldname);
      setManagedSectionVisibility($section, config.visible, "erpwdn-details-hidden-source");
    });

    const $totalsOverviewSection = getSectionForField(frm, "total_qty");
    setManagedSectionVisibility($totalsOverviewSection, !isSubmitted || hasNetWeightSignal(frm), "erpwdn-details-hidden-source");

    toggleField(frm, "naming_series", !isSubmitted);
    toggleField(frm, "customer_name", !isSubmitted);
    toggleField(frm, "company", !isSubmitted);
    toggleField(frm, "set_warehouse", !hideDuplicateSourceWarehouse);

    markFeatureReady(frm, "details_governance", {
      has_discount: hasAdditionalDiscountSignal(frm),
      has_price_signal: hasDeliveryPriceSignal(frm),
      hide_duplicate_source_warehouse: hideDuplicateSourceWarehouse,
      has_taxes: hasTaxesSignal(frm),
      submitted: isSubmitted,
    });
    return true;
  }

  function ensureSectionStack($tab, className) {
    if (typeof childPageSections.ensureSectionStack === "function") {
      return childPageSections.ensureSectionStack($tab, className);
    }

    if (!$tab || !$tab.length) return $();

    let $stack = $tab.children(`.${className}`).first();
    if ($stack.length) return $stack;

    $stack = $(`<div class="${className}"></div>`);
    $tab.prepend($stack);
    return $stack;
  }

  function containerHasVisibleControls($container) {
    return hasVisibleControls($container);
  }

  function countVisibleControls($container) {
    if (!$container || !$container.length) return 0;
    return $container.find(".frappe-control:visible").length;
  }

  function updateVisibleColumnState($section) {
    if (!$section || !$section.length) return;

    const $columns = $section.find("> .section-body > .form-column");
    if (!$columns.length) return;

    $columns.each((_, element) => {
      const $column = $(element);
      const hasVisibleControl = $column.find(".frappe-control:visible").length > 0;
      $column
        .toggleClass("erpw-so-moreinfo-column-empty", !hasVisibleControl)
        .toggleClass("erpw-so-moreinfo-column-active", hasVisibleControl);
    });
  }

  function promoteSingleFieldColumn($section, fieldname) {
    if (!$section || !$section.length || !fieldname) return false;

    const $body = $section.find("> .section-body").first();
    if (!$body.length) return false;

    const $targetControl = $body.find(`.frappe-control[data-fieldname="${fieldname}"]`).first();
    if (!$targetControl.length) return false;

    const $targetColumn = $targetControl.closest(".form-column");
    if (!$targetColumn.length) return false;

    $body.children(".form-column")
      .addClass("erpw-so-moreinfo-column-empty")
      .removeClass("erpw-so-moreinfo-column-active");

    $targetColumn
      .prependTo($body)
      .removeClass("erpw-so-moreinfo-column-empty")
      .addClass("erpw-so-moreinfo-column-active");

    return true;
  }

  function ensureAddressContactSectionHeader($section, config, presentation) {
    if (typeof childPageSections.ensureAddressSectionHeader === "function") {
      return childPageSections.ensureAddressSectionHeader($section, {
        iconMarkup: actionIconMarkup(config.icon || "customer"),
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

    $header.find(".erpw-so-address-header-icon").html(actionIconMarkup(config.icon || "customer"));
    $header.find(".erpw-so-address-header-title").text(config.title || "");
    $header.find(".erpw-so-address-header-note").text(config.note || "");

    const statusText = String((presentation && presentation.statusText) || "").trim();
    const statusTone = String((presentation && presentation.statusTone) || "neutral").trim();
    const $status = $header.find(".erpw-so-address-header-status");

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

  function getDeliveryAddressContactSectionPresentation(frm, key) {
    const hasBillingAddress = [frm.doc.customer_address, frm.doc.address_display].some((value) => hasMeaningfulValue(value));
    const hasContact = [
      frm.doc.contact_person,
      frm.doc.contact_display,
      frm.doc.contact_mobile,
      frm.doc.contact_email,
    ].some((value) => hasMeaningfulValue(value));
    const hasShippingAddress = [frm.doc.shipping_address_name, frm.doc.shipping_address].some((value) => hasMeaningfulValue(value));
    const hasCompanyAddress = [frm.doc.company_address, frm.doc.company_address_display].some((value) => hasMeaningfulValue(value));

    const presentations = {
      customer: {
        wide: true,
        priority: true,
        statusTone: hasBillingAddress && hasContact ? "active" : "attention",
        statusText: hasBillingAddress && hasContact
          ? "Ready"
          : hasBillingAddress
            ? "Contact needed"
            : hasContact
              ? "Billing needed"
              : "Incomplete",
        state: (!hasBillingAddress || !hasContact) ? {
          title: !hasBillingAddress && !hasContact
            ? "Billing address and contact missing"
            : !hasBillingAddress
              ? "Billing address missing"
              : "Contact missing",
          note: !hasBillingAddress
            ? "Link billing address so delivery paperwork and customer references stay aligned."
            : "Set a delivery contact so handoff stays clear.",
          actionLabel: !hasBillingAddress ? "Select billing" : "Select contact",
          focusField: !hasBillingAddress ? "customer_address" : "contact_person",
        } : null,
      },
      shipping: {
        statusTone: hasShippingAddress ? "active" : "attention",
        statusText: hasShippingAddress ? "Destination set" : "Needs destination",
        state: !hasShippingAddress ? {
          title: "Shipping address missing",
          note: "Set destination so dispatch and proof of delivery stay aligned.",
          actionLabel: "Select shipping",
          focusField: "shipping_address_name",
        } : null,
      },
      company: {
        quiet: true,
        statusTone: hasCompanyAddress ? "active" : "neutral",
        statusText: hasCompanyAddress ? "Configured" : "Optional",
        state: !hasCompanyAddress ? {
          title: "Company address not linked",
          note: "Set it only when the printed delivery should show a specific issuing location.",
          actionLabel: "Select company",
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
      .off(".erpwDeliveryAddressState")
      .on("click.erpwDeliveryAddressState", (event) => {
        event.preventDefault();
        event.stopPropagation();
        if (state.focusField) {
          focusField(frm, state.focusField);
        }
      });
    $panel.prop("hidden", false);
  }

  function resetAddressContactTab(frm, $tab) {
    if (!$tab || !$tab.length) return;

    restoreRelocatedFieldPlacements(frm, "delivery-note-address");

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

  function arrangeDeliveryCustomerContactGrid(frm, $section) {
    return arrangeSharedAddressFieldGrid($section, {
      fieldnames: coreAddressFieldOrder,
      getWrapper: (fieldname) => getFieldWrapper(frm, fieldname),
      placeholders: coreAddressPlaceholders,
      values: frm.doc || {},
    });
  }

  function enhanceAddressContactTab(frm) {
    if (!frm || !frm.fields_dict) {
      markFeatureMissing(frm, "address_contact_tab", { reason: "missing_form" });
      return false;
    }

    const $tab = getTabByFieldname(frm, "address_and_contact_tab");
    if (!$tab.length) {
      markFeatureMissing(frm, "address_contact_tab", { reason: "missing_tab" });
      return false;
    }

    resetAddressContactTab(frm, $tab);
    $tab.addClass("erpw-so-address-tab erpwdn-address-tab");

    const hasShippingAddress = [frm.doc.shipping_address_name, frm.doc.shipping_address].some((value) => hasMeaningfulValue(value));
    const hasCompanyAddress = [frm.doc.company_address, frm.doc.company_address_display].some((value) => hasMeaningfulValue(value));

    toggleField(frm, "contact_person", true);
    toggleField(frm, "customer_address", true);
    toggleField(frm, "address_display", true);
    toggleField(frm, "contact_display", false);
    toggleField(frm, "contact_mobile", true);
    toggleField(frm, "contact_email", true);
    toggleField(frm, "territory", true);
    toggleField(frm, "shipping_address", hasShippingAddress);
    toggleField(frm, "company_address_display", hasCompanyAddress);

    const $stack = ensureSectionStack($tab, "erpw-so-address-stack");
    const configs = [
      {
        key: "customer",
        fieldname: "customer_address",
        title: "Customer Billing & Contact",
        note: "Billing address and delivery contact for this note.",
        icon: "customer",
      },
      {
        key: "shipping",
        fieldname: "shipping_address_name",
        title: "Shipping Destination",
        note: "Destination for dispatch, proof, and customer receipt.",
        icon: "delivery",
      },
      {
        key: "company",
        fieldname: "company_address",
        title: "Company Address",
        note: "Issuing location shown only when this delivery needs a specific outbound address.",
        icon: "warehouse",
      },
    ];

    let seen = 0;
    configs.forEach((config) => {
      const $section = getSectionForField(frm, config.fieldname);
      if (!$section || !$section.length) return;

      const presentation = getDeliveryAddressContactSectionPresentation(frm, config.key);
      $section
        .addClass(`erpw-so-address-section erpw-so-address-section-${config.key}`)
        .toggleClass("erpw-so-address-section-wide", !!presentation.wide)
        .toggleClass("erpw-so-address-section-priority", !!presentation.priority)
        .toggleClass("erpw-so-address-section-quiet", !!presentation.quiet)
        .show();

      ensureAddressContactSectionHeader($section, config, presentation);
      applyAddressContactSectionState(frm, $section, presentation);
      if (config.key === "customer") {
        coreAddressFieldOrder.forEach((fieldname) => {
          moveFieldIntoSectionBodyIfNeeded(frm, fieldname, $section, "delivery-note-address");
        });
        arrangeDeliveryCustomerContactGrid(frm, $section);
      }
      $stack.append($section);
      seen += 1;
    });

    if (typeof childPageSections.normalizeAddressFieldDisplays === "function") {
      childPageSections.normalizeAddressFieldDisplays($stack, [
        "customer_address",
        "shipping_address_name",
        "dispatch_address_name",
        "company_address",
      ]);
    }

    if (frm.layout && typeof frm.layout.refresh_sections === "function") {
      frm.layout.refresh_sections();
    }

    if (!seen) {
      markFeatureMissing(frm, "address_contact_tab", { reason: "no_sections_found" });
      return false;
    }

    markFeatureReady(frm, "address_contact_tab", { sections: seen });
    return true;
  }

  function ensureMoreInfoSectionHeader($section, optionsOrTitle, note) {
    const settings = (optionsOrTitle && typeof optionsOrTitle === "object")
      ? Object.assign({}, optionsOrTitle)
      : {
        note,
        title: optionsOrTitle,
      };

    if (typeof childPageSections.ensureMoreInfoSectionHeader === "function") {
      return childPageSections.ensureMoreInfoSectionHeader($section, settings);
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

    if (settings.interactive) {
      $header.attr({
        "aria-expanded": "true",
        "aria-label": settings.ariaLabel || settings.title || "",
        role: "button",
        tabindex: "0",
      });
    } else {
      $header.removeAttr("role tabindex aria-expanded aria-label");
    }

    $header.find(".erpw-so-moreinfo-header-title").text(settings.title || "");
    $header.find(".erpw-so-moreinfo-header-note").text(settings.note || "");
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

  function getDeliveryMoreInfoSectionPresentation(frm, key, context) {
    const runtimeContext = context || frm.__erpwDeliveryNoteContext || contextFallbackFromDoc(frm);
    const summaryData = runtimeContext.summary || {};
    const linked = runtimeContext.linked_documents || {};
    const salesTeamCount = Array.isArray(frm.doc.sales_team)
      ? frm.doc.sales_team.filter((row) => row && Object.keys(row).length).length
      : 0;
    const billingPct = Number(frm.doc.per_billed || 0);
    const returnedPct = Number(frm.doc.per_returned || 0);
    const installedPct = Number(frm.doc.per_installed || 0);
    const invoiceCount = Math.max(
      Number(summaryData.invoice_count || 0),
      Array.isArray(linked.invoices) ? linked.invoices.length : 0
    );
    const isReturnFlow = Number(frm.doc.is_return || 0) === 1;

    const metricList = [];
    const pushMetric = (label, value, formatter) => {
      if (!hasMeaningfulValue(value)) return;
      const rawValue = typeof formatter === "function" ? formatter(value) : value;
      if (!hasMeaningfulValue(rawValue)) return;
      const textValue = String(rawValue).trim();
      if (!textValue || textValue === "--") return;
      metricList.push({
        label,
        value: textValue,
      });
    };
    const compactText = (value, limit = 92) => {
      const text = String(value == null ? "" : value).replace(/\s+/g, " ").trim();
      if (!text) return "";
      return text.length > limit ? `${text.slice(0, limit - 1).trim()}…` : text;
    };
    const buildMetrics = (builder) => {
      metricList.length = 0;
      builder();
      return metricList.slice();
    };

    const billingMetrics = buildMetrics(() => {
      pushMetric("Billed", pct(billingPct));
      if (invoiceCount > 0) {
        pushMetric("Invoices", `${invoiceCount} linked`);
      }
      if (isReturnFlow) {
        pushMetric("Flow", "Return");
      }
      if (returnedPct > 0) {
        pushMetric("Returned", pct(returnedPct));
      }
      if (installedPct > 0) {
        pushMetric("Installed", pct(installedPct));
      }
    });
    const customerPoMetrics = buildMetrics(() => {
      pushMetric("PO No", frm.doc.po_no);
      pushMetric("PO Date", frm.doc.po_date, (value) => formatDateLabel(value));
    });
    const transportMetrics = buildMetrics(() => {
      pushMetric("Receipt No", frm.doc.lr_no);
      pushMetric("Receipt Date", frm.doc.lr_date, (value) => formatDateLabel(value));
      pushMetric("Transporter", frm.doc.transporter_name || frm.doc.transporter);
      pushMetric("Trip", frm.doc.delivery_trip);
      pushMetric("Driver", frm.doc.driver_name || frm.doc.driver);
      pushMetric("Vehicle", frm.doc.vehicle_no);
    });
    const contextMetrics = buildMetrics(() => {
      pushMetric("Instructions", compactText(frm.doc.instructions));
      pushMetric("Territory", frm.doc.territory);
      pushMetric("Incoterm", frm.doc.incoterm);
      pushMetric("Named Place", frm.doc.named_place);
      pushMetric("Internal Ref", frm.doc.inter_company_reference);
    });
    const commercialMetrics = buildMetrics(() => {
      pushMetric("Sales Partner", frm.doc.sales_partner);
      if (salesTeamCount > 0) {
        pushMetric("Sales Team", `${salesTeamCount} row${salesTeamCount === 1 ? "" : "s"}`);
      }
      if (Number(frm.doc.commission_rate || 0) !== 0) {
        pushMetric("Commission Rate", `${pct(frm.doc.commission_rate)} rate`);
      }
      if (Number(frm.doc.total_commission || 0) !== 0) {
        pushMetric("Total Commission", formatMoney(frm.doc.total_commission, frm.doc.currency));
      }
    });

    const hasSecondaryBillingFacts = isReturnFlow || returnedPct > 0 || installedPct > 0 || invoiceCount > 1;
    const billingStatusText = isReturnFlow
      ? "Return flow"
      : returnedPct > 0
        ? `${pct(returnedPct)} returned`
        : invoiceCount > 1
          ? `${invoiceCount} invoices`
          : installedPct > 0
            ? `${pct(installedPct)} installed`
            : "";
    const transportStatusText = hasMeaningfulValue(frm.doc.delivery_trip)
      ? "Trip linked"
      : hasMeaningfulValue(frm.doc.transporter_name || frm.doc.transporter)
        ? "Transport set"
        : hasMeaningfulValue(frm.doc.lr_no)
          ? "Receipt captured"
          : hasMeaningfulValue(frm.doc.lr_date)
            ? "Receipt date"
            : "";
    const contextStatusText = hasMeaningfulValue(frm.doc.instructions)
      ? "Instruction added"
      : hasMeaningfulValue(frm.doc.incoterm)
        ? "Incoterm set"
        : hasMeaningfulValue(frm.doc.territory)
          ? "Territory set"
          : hasMeaningfulValue(frm.doc.inter_company_reference)
            ? "Internal ref"
            : "";
    const commercialStatusText = salesTeamCount > 0
      ? `${salesTeamCount} team row${salesTeamCount === 1 ? "" : "s"}`
      : hasMeaningfulValue(frm.doc.sales_partner)
        ? "Partner linked"
        : Number(frm.doc.total_commission || 0) !== 0
          ? "Commission set"
          : Number(frm.doc.commission_rate || 0) !== 0
            ? "Rate set"
            : "";

    const presentations = {
      status: {
        hidden: !hasSecondaryBillingFacts,
        priority: isReturnFlow || returnedPct > 0,
        quiet: !(isReturnFlow || returnedPct > 0),
        wide: billingMetrics.length > 2,
        statusTone: isReturnFlow || returnedPct > 0 ? "attention" : "active",
        statusText: billingStatusText,
        metrics: billingMetrics,
        summary: hasSecondaryBillingFacts ? {
          title: isReturnFlow
            ? "Return handling is affecting billing posture on this delivery"
            : returnedPct > 0
              ? "Returned value is already recorded against this delivery"
              : installedPct > 0
                ? "Installation progress is also tracked on this delivery"
                : `${invoiceCount} invoices are linked to this delivery`,
          note: "Only secondary billing facts beyond the main header are surfaced here.",
        } : null,
      },
      reference: {
        hidden: !customerPoMetrics.length,
        quiet: false,
        statusTone: customerPoMetrics.length > 1 ? "active" : "attention",
        statusText: customerPoMetrics.length > 1 ? "PO recorded" : "PO partial",
        metrics: customerPoMetrics,
        summary: customerPoMetrics.length ? {
          title: customerPoMetrics.length > 1
            ? "Customer purchase-order details are recorded on this delivery"
            : "Customer purchase-order reference is only partially recorded",
          note: "Use these values when matching the posted delivery to the customer's buying trail.",
        } : null,
      },
      transport: {
        hidden: !transportMetrics.length,
        quiet: transportMetrics.length <= 2,
        wide: transportMetrics.length >= 4,
        statusTone: "active",
        statusText: transportStatusText,
        metrics: transportMetrics,
        summary: transportMetrics.length ? {
          title: "Dispatch trace is recorded on this delivery",
          note: "Receipt and transport facts are surfaced here without moving navigation out of Connections.",
        } : null,
      },
      controls: {
        hidden: !contextMetrics.length,
        quiet: true,
        wide: contextMetrics.length >= 3,
        statusTone: hasMeaningfulValue(frm.doc.instructions) ? "attention" : "active",
        statusText: contextStatusText,
        metrics: contextMetrics,
        summary: contextMetrics.length ? {
          title: "Additional execution context is recorded",
          note: "Only secondary context that affects this delivery is kept here.",
        } : null,
      },
      commercial: {
        hidden: !commercialMetrics.length,
        quiet: salesTeamCount === 0,
        wide: commercialMetrics.length >= 3,
        statusTone: "active",
        statusText: commercialStatusText,
        metrics: commercialMetrics,
        summary: commercialMetrics.length ? {
          title: "Commercial attribution is recorded on this delivery",
          note: "Partner and incentive facts appear here only when they exist on the document.",
        } : null,
      },
    };

    return presentations[key] || {};
  }

  function getDeliveryTermsOutputPresentation(frm, key) {
    const isSubmitted = frm.doc.docstatus === 1;
    const hasTermsTemplate = hasMeaningfulValue(frm.doc.tc_name);
    const hasTermsText = hasMeaningfulValue(frm.doc.terms);
    const hasLetterHead = hasMeaningfulValue(frm.doc.letter_head);
    const hasPrintHeading = hasMeaningfulValue(frm.doc.select_print_heading);
    const hideAmount = Number(frm.doc.print_without_amount || 0) === 1;
    const groupItems = Number(frm.doc.group_same_items || 0) === 1;
    const hasLanguageOverride = hasMeaningfulValue(frm.doc.language);
    const hasOutputSignal = hasLetterHead || hasPrintHeading || hideAmount || groupItems;
    const outputMetrics = [];

    if (hasLetterHead) {
      outputMetrics.push({
        label: "Letter Head",
        value: String(frm.doc.letter_head || ""),
      });
    }

    if (hasPrintHeading) {
      outputMetrics.push({
        label: "Heading",
        value: String(frm.doc.select_print_heading || ""),
      });
    }

    if (hideAmount) {
      outputMetrics.push({
        label: "Amounts",
        value: "Hidden",
      });
    }

    if (groupItems) {
      outputMetrics.push({
        label: "Item Rows",
        value: "Grouped",
      });
    }

    if (hasLanguageOverride || !outputMetrics.length) {
      outputMetrics.push({
        label: "Language",
        value: getPrintLanguageLabel(frm.doc.language),
      });
    }

    const presentations = {
      conditions: {
        wide: true,
        quiet: !hasTermsTemplate && !hasTermsText,
        readonly: isSubmitted,
        statusTone: hasTermsTemplate || hasTermsText ? "active" : "neutral",
        statusText: hasTermsTemplate ? "Template linked" : (hasTermsText ? "Custom text" : "Not set"),
        metrics: hasTermsTemplate || hasTermsText ? [
          {
            label: "Terms",
            value: hasTermsTemplate ? String(frm.doc.tc_name || "") : "Manual text",
          },
          {
            label: "Detail",
            value: hasTermsText ? "Text included" : "Template only",
          },
        ] : [],
        state: !hasTermsTemplate && !hasTermsText ? (
          isSubmitted ? {
            title: "No delivery terms were recorded on this note",
            note: "This submitted delivery note has no attached terms and conditions.",
          } : {
            title: "No delivery terms are added yet",
            note: "Add terms only when this delivery note needs explicit customer-facing clauses beyond the linked order flow.",
            actionLabel: "Add terms",
            focusField: "tc_name",
            revealFields: true,
          }
        ) : null,
      },
      output: {
        hidden: !hasOutputSignal && isSubmitted,
        wide: true,
        quiet: !hasOutputSignal,
        statusTone: hideAmount ? "attention" : (hasOutputSignal ? "active" : "neutral"),
        statusText: hideAmount ? "Amount hidden" : (hasOutputSignal ? "Output adjusted" : "Standard output"),
        metrics: hasOutputSignal ? outputMetrics : [],
        assistNote: !hasOutputSignal ? "" : "Keep output changes secondary to the delivery record.",
        state: !hasOutputSignal ? {
          title: "Standard delivery print settings are in use",
          note: "Language, heading, amounts, and grouping are following the standard delivery output.",
          actionLabel: isSubmitted ? "" : "Adjust output",
          focusField: isSubmitted ? "" : "letter_head",
          revealFields: !isSubmitted,
        } : null,
      },
    };

    return presentations[key] || {};
  }

  function applyMoreInfoSectionBodyState(frm, $section, presentation) {
    if (!$section || !$section.length) return;

    const summary = presentation && presentation.summary;
    const hasMetrics = presentation && Array.isArray(presentation.metrics) && presentation.metrics.length > 0;
    const revealRaw = Boolean($section.data("erpwDeliveryMoreInfoRevealRaw"));
    const showSummary = Boolean(summary && !revealRaw && !hasMetrics);
    const $panel = ensureMoreInfoStatePanel($section);

    if (typeof childPageSections.applyMoreInfoMetrics === "function") {
      childPageSections.applyMoreInfoMetrics($section, presentation);
    }

    $section.toggleClass("erpw-so-moreinfo-section-facts-mode", !!hasMetrics);
    $section.toggleClass("erpw-so-moreinfo-section-summary-mode", showSummary);
    if (!$panel.length) return;

    if (!showSummary) {
      $panel.prop("hidden", true);
      return;
    }

    $panel.find(".erpw-so-moreinfo-state-title").text(summary.title || "");
    $panel.find(".erpw-so-moreinfo-state-note").text(summary.note || "");
    const $action = $panel.find(".erpw-so-moreinfo-state-action");
    const hasAction = Boolean(summary.actionLabel);

    if (hasAction) {
      $action
        .text(summary.actionLabel || "Update")
        .prop("hidden", false)
        .off(".erpwDeliveryMoreInfoState")
        .on("click.erpwDeliveryMoreInfoState", (event) => {
          event.preventDefault();
          event.stopPropagation();

          $section.data("erpwDeliveryMoreInfoRevealRaw", 1);
          applyMoreInfoSectionBodyState(frm, $section, presentation);
          if (summary.focusField) {
            focusField(frm, summary.focusField);
          }
        });
    } else {
      $action.text("").prop("hidden", true).off(".erpwDeliveryMoreInfoState");
    }
    $panel.prop("hidden", false);
  }

  function resetMoreInfoTab($tab) {
    if (!$tab || !$tab.length) return;

    $tab.children(".erpw-so-moreinfo-stack").remove();
    $tab.find(".erpw-so-moreinfo-metrics").remove();
    $tab.find(".erpw-so-moreinfo-state-panel").remove();
    $tab.find(".erpw-so-moreinfo-header").remove();
    $tab.find(".form-section").removeData("erpwDeliveryMoreInfoRevealRaw");
    $tab.find(".erpw-so-moreinfo-default-head").removeClass("erpw-so-moreinfo-default-head").show();
    $tab.find(".form-section")
      .show()
      .removeClass("hide-control empty-section visible-section erpw-so-moreinfo-hidden-source erpw-so-moreinfo-section-summary-mode");
    $tab.find(".section-body").removeClass("hide");
    $tab.find(".section-head").removeClass("collapsed");
    $tab.find(".form-section").removeClass([
      "erpw-so-moreinfo-section",
      "erpwdn-moreinfo-section",
      "erpwdn-moreinfo-section-status",
      "erpwdn-moreinfo-section-reference",
      "erpwdn-moreinfo-section-transport",
      "erpwdn-moreinfo-section-controls",
      "erpwdn-moreinfo-section-commercial",
      "erpw-so-moreinfo-section-execution",
      "erpw-so-moreinfo-section-commercial",
      "erpw-so-moreinfo-section-sales-team",
      "erpw-so-moreinfo-section-priority",
      "erpw-so-moreinfo-section-quiet",
      "erpw-so-moreinfo-section-wide",
    ].join(" "));
  }

  function enhanceMoreInfoTab(frm) {
    if (!frm || !frm.fields_dict) {
      markFeatureMissing(frm, "more_info_tab", { reason: "missing_form" });
      return false;
    }

    const $tab = getTabByFieldname(frm, "more_info_tab");
    if (!$tab.length) {
      markFeatureMissing(frm, "more_info_tab", { reason: "missing_tab" });
      return false;
    }

    resetMoreInfoTab($tab);
    $tab.addClass("erpw-so-moreinfo-tab");
    setTabVisibility(frm, "more_info_tab", true);

    const hasInternalCompany = Boolean(frm.doc.is_internal_customer) || hasMeaningfulValue(frm.doc.represents_company);
    const context = frm.__erpwDeliveryNoteContext || contextFallbackFromDoc(frm);

    setFieldPrecision(frm, "per_billed", 2);
    setFieldPrecision(frm, "per_installed", 2);
    setFieldPrecision(frm, "per_returned", 2);

    toggleField(frm, "named_place", hasMeaningfulValue(frm.doc.incoterm));
    toggleField(frm, "is_internal_customer", Boolean(frm.doc.is_internal_customer));
    toggleField(frm, "represents_company", hasInternalCompany);

    const $stack = ensureSectionStack($tab, "erpw-so-moreinfo-stack");
    const configs = [
      {
        key: "status",
        fieldname: "section_break_83",
        title: "Billing Status",
        note: "Billing progress and return posture carried by this delivery note.",
      },
      {
        key: "reference",
        fieldname: "customer_po_details",
        title: "Customer PO",
        note: "Customer purchase-order reference captured on this delivery note.",
      },
      {
        key: "transport",
        fieldname: "transporter_info",
        title: "Delivery Trace",
        note: "Receipt, transporter, and dispatch trace recorded on this delivery.",
      },
      {
        key: "controls",
        fieldname: "more_info",
        title: "Additional Context",
        note: "Handling instructions, territory, Incoterm, and internal references for this delivery.",
      },
      {
        key: "commercial",
        fieldname: "sales_team_section_break",
        title: "Commercial Attribution",
        note: "Partner, commission, and sales allocation attached to this delivery when used.",
      },
    ];

    let seen = 0;

    configs.forEach((config) => {
      const $section = getSectionForField(frm, config.fieldname);
      if (!$section || !$section.length) return;

      const presentation = getDeliveryMoreInfoSectionPresentation(frm, config.key, context);
      const hasControls = containerHasVisibleControls($section);
      const visibleControlCount = countVisibleControls($section);
      const forceSingleField = !presentation.summary && typeof presentation.singleField === "string" && presentation.singleField;
      const isSingleControl = !presentation.summary && (visibleControlCount === 1 || !!forceSingleField);
      const shouldShow = !presentation.hidden && (hasControls || !!presentation.summary);

      $section
        .addClass(`erpw-so-moreinfo-section erpwdn-moreinfo-section erpwdn-moreinfo-section-${config.key}`)
        .toggleClass("hide-control", !shouldShow)
        .toggleClass("erpw-so-moreinfo-hidden-source", !shouldShow)
        .toggleClass("erpw-so-moreinfo-section-wide", !!presentation.wide)
        .toggleClass("erpw-so-moreinfo-section-priority", !!presentation.priority)
        .toggleClass("erpw-so-moreinfo-section-quiet", !!presentation.quiet)
        .toggleClass("erpw-so-moreinfo-section-execution", ["status", "transport", "controls"].includes(config.key))
        .toggleClass("erpw-so-moreinfo-section-commercial", ["reference", "commercial"].includes(config.key))
        .toggleClass("erpw-so-moreinfo-section-sales-team", config.key === "commercial")
        .toggleClass("erpw-so-moreinfo-section-single-control", isSingleControl)
        .toggleClass("erpw-so-moreinfo-section-summary-mode", !!presentation.summary)
        .toggle(shouldShow);

      if (!shouldShow) return;

      updateVisibleColumnState($section);
      if (forceSingleField) {
        promoteSingleFieldColumn($section, presentation.singleField);
      }
      $section.children(".section-head").removeClass("collapsed");
      $section.children(".section-body").removeClass("hide").show();
      ensureMoreInfoSectionHeader($section, {
        ariaLabel: config.title,
        interactive: false,
        note: config.note,
        title: config.title,
      });
      applyMoreInfoHeaderState($section, presentation);
      applyMoreInfoSectionBodyState(frm, $section, presentation);
      $stack.append($section);
      seen += 1;
    });

    const hiddenDuplicateSections = new Set();
    const $printingDetailsSection = getSectionForField(frm, "printing_details");
    if ($printingDetailsSection && $printingDetailsSection.length) {
      hiddenDuplicateSections.add($printingDetailsSection.get(0));
    }

    $tab.children(".form-section").each((_, element) => {
      const $section = $(element);
      const shouldHide = hiddenDuplicateSections.has(element) || !$section.closest(".erpw-so-moreinfo-stack").length;
      $section
        .toggleClass("erpw-so-moreinfo-hidden-source", shouldHide)
        .toggle(!shouldHide);
    });

    if (typeof childPageSections.balanceMoreInfoStack === "function") {
      childPageSections.balanceMoreInfoStack($stack);
    }

    if (frm.layout && typeof frm.layout.refresh_sections === "function") {
      frm.layout.refresh_sections();
    }

    if (!seen) {
      setTabVisibility(frm, "more_info_tab", false);
      markFeatureMissing(frm, "more_info_tab", { reason: "no_sections_found" });
      return false;
    }

    setTabVisibility(frm, "more_info_tab", true);
    markFeatureReady(frm, "more_info_tab", { sections: seen });
    return true;
  }

  function enhanceTermsOutputTab(frm) {
    if (!frm || !frm.fields_dict) {
      markFeatureMissing(frm, "terms_output_tab", { reason: "missing_form" });
      return false;
    }

    if (typeof childPageTerms.ensureTermsStack !== "function"
      || typeof childPageTerms.ensureTermsSectionHeader !== "function"
      || typeof childPageTerms.applyTermsSectionState !== "function"
      || typeof childPageTerms.applyTermsMetrics !== "function"
      || typeof childPageTerms.applyTermsAssistNote !== "function"
      || typeof childPageTerms.resetTermsTab !== "function") {
      markFeatureMissing(frm, "terms_output_tab", { reason: "runtime_unavailable" });
      return false;
    }

    const $tab = getTabByFieldname(frm, "terms_tab");
    if (!$tab.length) {
      markFeatureMissing(frm, "terms_output_tab", { reason: "missing_tab" });
      return false;
    }

    childPageTerms.resetTermsTab($tab);
    $tab.addClass("erpw-so-terms-tab");

    const hasTermsTemplate = hasMeaningfulValue(frm.doc.tc_name);
    const hasTermsText = hasMeaningfulValue(frm.doc.terms);

    toggleField(frm, "tc_name", true);
    toggleField(frm, "terms", hasTermsText);
    toggleField(frm, "letter_head", true);
    toggleField(frm, "select_print_heading", true);
    toggleField(frm, "print_without_amount", true);
    toggleField(frm, "group_same_items", true);
    toggleField(frm, "language", true);

    const configs = [
      {
        key: "conditions",
        fieldname: "tc_name",
        title: "Terms & Conditions",
        note: "Keep customer-facing delivery terms explicit only when this note truly needs them.",
        icon: "policy",
      },
      {
        key: "output",
        fieldname: "printing_details",
        title: "Print & Output",
        note: "Keep print controls available without making them louder than the fulfillment story.",
        icon: "output",
      },
    ];

    const $stack = childPageTerms.ensureTermsStack($tab, "erpw-so-terms-stack");
    const seen = new Set();

    configs.forEach((config) => {
      const $section = getSectionForField(frm, config.fieldname);
      if (!$section || !$section.length) return;

      const presentation = getDeliveryTermsOutputPresentation(frm, config.key);
      if (presentation.hidden) return;

      const sectionNode = $section.get(0);
      if (seen.has(sectionNode)) return;
      seen.add(sectionNode);

      $section
        .addClass(`erpw-so-terms-section erpwdn-terms-section erpwdn-terms-section-${config.key} erpw-so-terms-section-${config.key}`)
        .toggleClass("erpw-so-terms-section-wide", !!presentation.wide)
        .toggleClass("erpw-so-terms-section-priority", !!presentation.priority)
        .toggleClass("erpw-so-terms-section-quiet", !!presentation.quiet)
        .toggleClass("erpw-so-terms-section-readonly", !!presentation.readonly);

      childPageTerms.ensureTermsSectionHeader($section, {
        icon: config.icon || "policy",
        note: config.note,
        statusText: String((presentation && presentation.statusText) || "").trim(),
        statusTone: String((presentation && presentation.statusTone) || "neutral").trim(),
        title: config.title,
      });
      childPageTerms.applyTermsMetrics($section, presentation);
      childPageTerms.applyTermsAssistNote($section, presentation);
      childPageTerms.applyTermsSectionState($section, presentation, {
        onFocusField(fieldname) {
          focusField(frm, fieldname);
        },
        onRevealFields() {
          if (config.key === "conditions") {
            toggleField(frm, "tc_name", true);
            toggleField(frm, "terms", true);
          }
        },
      });
      $stack.append($section);
    });

    $tab.children(".form-section").not($stack.children(".form-section")).each((_, element) => {
      $(element).addClass("erpw-so-terms-hidden-source").hide();
    });

    if (typeof childPageTerms.balanceTermsStack === "function") {
      childPageTerms.balanceTermsStack($stack);
    }

    if (frm.layout && typeof frm.layout.refresh_sections === "function") {
      frm.layout.refresh_sections();
    }

    if (!seen.size) {
      markFeatureMissing(frm, "terms_output_tab", { reason: "no_sections_found" });
      return false;
    }

    markFeatureReady(frm, "terms_output_tab", {
      has_output_signal: Number(frm.doc.print_without_amount || 0) === 1
        || Number(frm.doc.group_same_items || 0) === 1
        || hasMeaningfulValue(frm.doc.letter_head)
        || hasMeaningfulValue(frm.doc.select_print_heading),
      has_terms: hasTermsTemplate || hasTermsText,
      sections: seen.size,
    });
    return true;
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

  function formatPostingContextLabel(dateValue, timeValue) {
    const dateLabel = formatDateLabel(dateValue);
    const timeLabel = String(timeValue || "").trim();
    return timeLabel ? `${dateLabel} • ${timeLabel}` : dateLabel;
  }

  function getReferenceNames(frm, data) {
    const summary = data.summary || {};
    const linked = data.linked_documents || {};
    return [frm.doc.name, summary.customer]
      .concat((linked.sales_orders || []).map((row) => row.name))
      .concat((linked.invoices || []).map((row) => row.name))
      .concat((linked.returns || []).map((row) => row.name))
      .concat(linked.source_delivery && linked.source_delivery.name ? [linked.source_delivery.name] : [])
      .filter(Boolean);
  }

  function createFollowUpTask(frm, data) {
    const summary = data.summary || {};
    frappe.new_doc("ToDo", {
      description: `Follow up ${summary.name || frm.doc.name || "Delivery Note"} for ${summary.customer_label || summary.customer || "customer"}`,
      reference_type: "Delivery Note",
      reference_name: summary.name || frm.doc.name,
      allocated_to: frm.doc.owner || frappe.session.user,
      date: summary.posting_date || frappe.datetime.get_today(),
    });
  }

  function draftContext(frm) {
    const owner = frm.doc.owner || frappe.session.user;
    const ownerDisplay = frappe.user && typeof frappe.user.full_name === "function" ? frappe.user.full_name(owner) : owner;

    return {
      summary: {
        name: frm.doc.name || "New Delivery Note",
        customer: frm.doc.customer || null,
        customer_label: frm.doc.customer_name || frm.doc.customer || "Customer not selected yet",
        status: frm.doc.docstatus === 0 ? "Draft" : (frm.doc.status || "Draft"),
        workflow_state: frm.doc.workflow_state || null,
        owner,
        owner_display: ownerDisplay,
        posting_date: frm.doc.posting_date || frappe.datetime.get_today(),
        posting_time: frm.doc.posting_time || null,
        currency: frm.doc.currency || frappe.defaults.get_default("currency"),
        grand_total: frm.doc.grand_total || 0,
        total_qty: frm.doc.total_qty || 0,
        per_billed: frm.doc.per_billed || 0,
        per_returned: frm.doc.per_returned || 0,
        is_return: frm.doc.is_return || 0,
        return_against: frm.doc.return_against || null,
        company: frm.doc.company || null,
        set_warehouse: frm.doc.set_warehouse || null,
        set_target_warehouse: frm.doc.set_target_warehouse || null,
        transporter: frm.doc.transporter || null,
        driver: frm.doc.driver || null,
        vehicle_no: frm.doc.vehicle_no || null,
        delivery_trip: frm.doc.delivery_trip || null,
        sales_order_count: 0,
        invoice_count: 0,
        return_count: 0,
      },
      linked_documents: {
        customer: frm.doc.customer ? { doctype: "Customer", name: frm.doc.customer } : null,
        sales_orders: [],
        invoices: [],
        source_delivery: null,
        returns: [],
        source_warehouse: frm.doc.set_warehouse ? { doctype: "Warehouse", name: frm.doc.set_warehouse } : null,
        target_warehouse: frm.doc.set_target_warehouse ? { doctype: "Warehouse", name: frm.doc.set_target_warehouse } : null,
        delivery_trip: frm.doc.delivery_trip ? { doctype: "Delivery Trip", name: frm.doc.delivery_trip } : null,
        driver: frm.doc.driver ? { doctype: "Driver", name: frm.doc.driver } : null,
        transporter: frm.doc.transporter ? { doctype: "Supplier", name: frm.doc.transporter } : null,
      },
      support: {
        latest_task: null,
        open_task_count: 0,
        approval_note: "Use the standard toolbar to save, submit, or route workflow review for this delivery note.",
        fulfillment_note: "This delivery note will become the main fulfillment reading surface after it is saved.",
        customer_response_hint: "Confirm the delivery state and linked billing context before giving a customer-facing status update.",
        next_action: "Complete the delivery details, then save so the fulfillment workspace can evaluate linked order, invoice, and return context.",
        detail_guide: "Use the detailed form sections below to maintain items, stock movement, addresses, and transport details before submission.",
      },
    };
  }

  function contextFallbackFromDoc(frm) {
    const base = draftContext(frm);
    const items = Array.isArray(frm.doc.items) ? frm.doc.items : [];
    const linkedSalesOrders = uniqueMeaningfulValues(items.map((item) => item && item.against_sales_order))
      .map((name) => ({ name }));
    const sourceDelivery = hasMeaningfulValue(frm.doc.return_against)
      ? { doctype: "Delivery Note", name: frm.doc.return_against }
      : null;

    base.summary = Object.assign({}, base.summary, {
      customer: frm.doc.customer || base.summary.customer,
      customer_label: frm.doc.customer_name || frm.doc.customer || base.summary.customer_label,
      company: frm.doc.company || null,
      currency: frm.doc.currency || base.summary.currency,
      delivery_trip: frm.doc.delivery_trip || null,
      docstatus: frm.doc.docstatus,
      driver: frm.doc.driver || null,
      grand_total: frm.doc.grand_total || 0,
      invoice_count: 0,
      is_return: frm.doc.is_return || 0,
      owner: frm.doc.owner || base.summary.owner,
      owner_display: base.summary.owner_display,
      per_billed: frm.doc.per_billed || 0,
      per_returned: frm.doc.per_returned || 0,
      posting_date: frm.doc.posting_date || frappe.datetime.get_today(),
      posting_time: frm.doc.posting_time || null,
      return_against: frm.doc.return_against || null,
      return_count: Number(frm.doc.is_return || 0) ? 0 : (hasMeaningfulValue(frm.doc.return_against) ? 1 : 0),
      sales_order_count: linkedSalesOrders.length,
      set_target_warehouse: frm.doc.set_target_warehouse || null,
      set_warehouse: frm.doc.set_warehouse || null,
      status: frm.doc.status || (Number(frm.doc.docstatus || 0) === 1 ? "Submitted" : "Draft"),
      total_qty: frm.doc.total_qty || 0,
      transporter: frm.doc.transporter || null,
      vehicle_no: frm.doc.vehicle_no || null,
      workflow_state: frm.doc.workflow_state || null,
    });

    base.linked_documents = Object.assign({}, base.linked_documents, {
      customer: frm.doc.customer ? { doctype: "Customer", name: frm.doc.customer } : null,
      delivery_trip: frm.doc.delivery_trip ? { doctype: "Delivery Trip", name: frm.doc.delivery_trip } : null,
      driver: frm.doc.driver ? { doctype: "Driver", name: frm.doc.driver } : null,
      invoices: [],
      returns: Number(frm.doc.is_return || 0) ? [] : [],
      sales_orders: linkedSalesOrders,
      source_delivery: sourceDelivery,
      source_warehouse: frm.doc.set_warehouse ? { doctype: "Warehouse", name: frm.doc.set_warehouse } : null,
      target_warehouse: frm.doc.set_target_warehouse ? { doctype: "Warehouse", name: frm.doc.set_target_warehouse } : null,
      transporter: frm.doc.transporter ? { doctype: "Supplier", name: frm.doc.transporter } : null,
    });

    base.support = Object.assign({}, base.support, {
      approval_note: "Live context is still loading. Delivery sections remain usable below.",
      fulfillment_note: "Use the delivery sections while the workspace refreshes linked order and billing context.",
      next_action: Number(frm.doc.docstatus || 0) === 1
        ? "Use the delivery sections while the workspace refreshes this delivery context."
        : base.support.next_action,
    });

    return base;
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
      return_doc: `
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M9 8l-4 4l4 4M5 12h9a4 4 0 1 0 0 8" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      `,
      warehouse: `
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M4 9.5l8-4l8 4v9l-8 4l-8-4zM12 5.5v13M4 9.5l8 4l8-4" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      `,
      transport: `
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M3 8h10v7H3zM13 10.5h3l2 2v2h-5zM7 17.5a1.5 1.5 0 1 1-3 0a1.5 1.5 0 0 1 3 0zm11 0a1.5 1.5 0 1 1-3 0a1.5 1.5 0 0 1 3 0z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      `,
    };
    return icons[kind] || icons.delivery;
  }

  function uniqueMeaningfulValues(values) {
    return Array.from(new Set((Array.isArray(values) ? values : [])
      .filter((value) => hasMeaningfulValue(value))
      .map((value) => String(value).trim())));
  }

  function warehouseContextLabel(warehouseNames) {
    const names = Array.isArray(warehouseNames) ? warehouseNames : [];
    if (!names.length) return "Warehouse not set";
    if (names.length === 1) return names[0];
    return `${names.length} warehouses`;
  }

  function sumNumeric(items, fieldname) {
    return (Array.isArray(items) ? items : []).reduce((sum, item) => sum + Number(item && item[fieldname] || 0), 0);
  }

  function actionConfig(frm, data) {
    const summary = data.summary || {};
    const linked = data.linked_documents || {};
    const support = data.support || {};
    const actions = [];

    if (Array.isArray(linked.sales_orders) && linked.sales_orders.length) {
      actions.push({
        category: "linked_document",
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

    if (Array.isArray(linked.invoices) && linked.invoices.length) {
      actions.push({
        category: "linked_document",
        title: formatCountTitle("Open Invoice", "Open Invoices", linked.invoices.length),
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
        category: "reference_document",
        title: "Open Customer",
        variant: actions.length ? "secondary" : "primary",
        icon: "customer",
        handler: () => routeToDoc("Customer", summary.customer),
      });
    }

    actions.push({
      attention: Number(support.open_task_count || 0) > 0,
      category: "follow_up",
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

    if (linked.source_delivery && linked.source_delivery.name) {
      actions.push({
        category: "linked_document",
        title: "Open Source Delivery",
        variant: "secondary",
        icon: "return_doc",
        handler: () => routeToDoc("Delivery Note", linked.source_delivery.name),
      });
    } else if (Array.isArray(linked.returns) && linked.returns.length) {
      actions.push({
        category: "linked_document",
        title: formatCountTitle("Open Return", "Open Returns", linked.returns.length),
        variant: "secondary",
        icon: "return_doc",
        handler: () => {
          if (linked.returns.length === 1) {
            routeToDoc("Delivery Note", linked.returns[0].name);
            return;
          }
          routeToList("Delivery Note", { name: ["in", linked.returns.map((row) => row.name)] });
        },
      });
    }

    return applySalesConsoleDocumentActionPolicy(actions, {
      maxTopActions: 2,
    });
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

  function connectionGroupIconMarkup(key) {
    const icons = {
      fulfillment: actionIconMarkup("delivery"),
      relationship: actionIconMarkup("customer"),
      operations: actionIconMarkup("warehouse"),
    };
    return icons[key] || icons.fulfillment;
  }

  function connectionDocIconMarkup(doctype) {
    const icons = {
      "Sales Order": actionIconMarkup("sales_order"),
      "Sales Invoice": actionIconMarkup("invoice"),
      "Delivery Note": actionIconMarkup("delivery"),
      Customer: actionIconMarkup("customer"),
      Warehouse: actionIconMarkup("warehouse"),
      "Delivery Trip": actionIconMarkup("transport"),
      Driver: actionIconMarkup("transport"),
      Supplier: actionIconMarkup("transport"),
    };
    return icons[doctype] || actionIconMarkup("delivery");
  }

  function buildConnectionsGroups(data) {
    const summary = data.summary || {};
    const linked = data.linked_documents || {};
    const groups = [];

    const fulfillmentItems = [
      {
        doctype: "Sales Order",
        title: "Sales Order",
        note: linked.sales_orders && linked.sales_orders.length
          ? "Order commitment linked upstream from this fulfillment record."
          : "No upstream sales order is linked from this delivery note.",
        count: Array.isArray(linked.sales_orders) ? linked.sales_orders.length : 0,
        emptyLabel: "Not linked",
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
        doctype: "Sales Invoice",
        title: "Sales Invoice",
        note: linked.invoices && linked.invoices.length
          ? "Billing records already linked to this delivery note."
          : "No invoice is linked yet from this delivery note.",
        count: Array.isArray(linked.invoices) ? linked.invoices.length : 0,
        emptyLabel: "Not billed",
        emptyTone: "attention",
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

    if (summary.is_return) {
      fulfillmentItems.push({
        doctype: "Delivery Note",
        title: "Source Delivery",
        note: linked.source_delivery && linked.source_delivery.name
          ? "Original delivery record linked to this return."
          : "This return delivery does not yet show a linked source document.",
        count: linked.source_delivery && linked.source_delivery.name ? 1 : 0,
        emptyLabel: "Missing source",
        emptyTone: "attention",
        onOpen: linked.source_delivery && linked.source_delivery.name
          ? () => routeToDoc("Delivery Note", linked.source_delivery.name)
          : null,
      });
    } else {
      fulfillmentItems.push({
        doctype: "Delivery Note",
        title: "Return Delivery",
        note: linked.returns && linked.returns.length
          ? "Return records already linked against this delivery note."
          : "No return delivery is linked against this record.",
        count: Array.isArray(linked.returns) ? linked.returns.length : 0,
        emptyLabel: "No return",
        emptyTone: "neutral",
        required: false,
        onOpen: linked.returns && linked.returns.length
          ? () => {
            if (linked.returns.length === 1) {
              routeToDoc("Delivery Note", linked.returns[0].name);
              return;
            }
            routeToList("Delivery Note", { name: ["in", linked.returns.map((row) => row.name)] });
          }
          : null,
      });
    }

    groups.push({
      key: "fulfillment",
      title: "Fulfillment Chain",
      note: "Keep upstream order, billing follow-through, and return handling visible together.",
      iconMarkup: connectionGroupIconMarkup("fulfillment"),
      status: getConnectionGroupStatus(fulfillmentItems),
      items: fulfillmentItems.map((item) => ({
        doctype: item.doctype,
        title: item.title,
        note: item.note,
        count: item.count,
        visibility: item.required === false ? "optional" : "meaningful-empty",
        iconMarkup: connectionDocIconMarkup(item.doctype),
        status: getConnectionDocStatus(item),
        actions: item.onOpen ? [{ label: "Open linked", run: item.onOpen }] : [],
      })),
    });

    const relationshipItems = [
      {
        doctype: "Customer",
        title: "Customer",
        note: linked.customer && linked.customer.name
          ? "Customer record linked to this delivery note."
          : "No customer is linked yet.",
        count: linked.customer && linked.customer.name ? 1 : 0,
        emptyLabel: "Not linked",
        emptyTone: "attention",
        onOpen: linked.customer && linked.customer.name ? () => routeToDoc("Customer", linked.customer.name) : null,
      },
    ];

    groups.push({
      key: "relationship",
      title: "Relationship Context",
      note: "Keep the customer relationship visible next to the fulfillment record.",
      iconMarkup: connectionGroupIconMarkup("relationship"),
      status: getConnectionGroupStatus(relationshipItems),
      items: relationshipItems.map((item) => ({
        doctype: item.doctype,
        title: item.title,
        note: item.note,
        count: item.count,
        visibility: "meaningful-empty",
        iconMarkup: connectionDocIconMarkup(item.doctype),
        status: getConnectionDocStatus(item),
        actions: item.onOpen ? [{ label: "Open linked", run: item.onOpen }] : [],
      })),
    });

    const operationsItems = [
      {
        doctype: "Warehouse",
        title: "Source Warehouse",
        note: linked.source_warehouse && linked.source_warehouse.name
          ? "Default source warehouse referenced on this delivery note."
          : "No default source warehouse is set on the document header.",
        count: linked.source_warehouse && linked.source_warehouse.name ? 1 : 0,
        emptyLabel: "Header warehouse not set",
        emptyTone: "neutral",
        required: false,
        onOpen: linked.source_warehouse && linked.source_warehouse.name ? () => routeToDoc("Warehouse", linked.source_warehouse.name) : null,
      },
      {
        doctype: "Warehouse",
        title: "Target Warehouse",
        note: linked.target_warehouse && linked.target_warehouse.name
          ? "Target warehouse referenced on this delivery note."
          : "No target warehouse is set on the document header.",
        count: linked.target_warehouse && linked.target_warehouse.name ? 1 : 0,
        emptyLabel: "Not set",
        emptyTone: "neutral",
        required: false,
        onOpen: linked.target_warehouse && linked.target_warehouse.name ? () => routeToDoc("Warehouse", linked.target_warehouse.name) : null,
      },
      {
        doctype: "Delivery Trip",
        title: "Delivery Trip",
        note: linked.delivery_trip && linked.delivery_trip.name
          ? "Delivery trip linked to this record."
          : "No delivery trip is linked on this document.",
        count: linked.delivery_trip && linked.delivery_trip.name ? 1 : 0,
        emptyLabel: "Not linked",
        emptyTone: "neutral",
        required: false,
        onOpen: linked.delivery_trip && linked.delivery_trip.name ? () => routeToDoc("Delivery Trip", linked.delivery_trip.name) : null,
      },
      {
        doctype: "Driver",
        title: "Driver",
        note: linked.driver && linked.driver.name
          ? "Driver record linked to this delivery note."
          : "No driver is linked on this document.",
        count: linked.driver && linked.driver.name ? 1 : 0,
        emptyLabel: "Not linked",
        emptyTone: "neutral",
        required: false,
        onOpen: linked.driver && linked.driver.name ? () => routeToDoc("Driver", linked.driver.name) : null,
      },
      {
        doctype: "Supplier",
        title: "Transporter",
        note: linked.transporter && linked.transporter.name
          ? "Transporter linked to this delivery note."
          : "No transporter is linked on this document.",
        count: linked.transporter && linked.transporter.name ? 1 : 0,
        emptyLabel: "Not linked",
        emptyTone: "neutral",
        required: false,
        onOpen: linked.transporter && linked.transporter.name ? () => routeToDoc("Supplier", linked.transporter.name) : null,
      },
    ].filter((item) => item.count > 0);

    if (operationsItems.length) {
      groups.push({
        key: "operations",
        title: "Operational Context",
        note: "Keep warehouse and transport references visible without making them the dominant story.",
        iconMarkup: connectionGroupIconMarkup("operations"),
        status: getConnectionGroupStatus(operationsItems),
        items: operationsItems.map((item) => ({
          doctype: item.doctype,
          title: item.title,
          note: item.note,
          count: item.count,
          visibility: item.required === false ? "optional" : "meaningful-empty",
          iconMarkup: connectionDocIconMarkup(item.doctype),
          status: getConnectionDocStatus(item),
          actions: item.onOpen ? [{ label: "Open linked", run: item.onOpen }] : [],
        })),
      });
    }

    return groups;
  }

  function renderConnectionsWorkspace(frm, data) {
    const $tab = getTabByFieldname(frm, "connections_tab");
    if (!$tab.length) return false;
    if (typeof childPageConnections.renderCardWorkspace !== "function") {
      markFeatureMissing(frm, "connection_workspace", { reason: "runtime_unavailable" });
      return false;
    }

    const rendered = childPageConnections.renderCardWorkspace(frm, {
      featureKey: "connection_workspace",
      layout: "card",
      model: {
        groups: buildConnectionsGroups(data),
      },
      mount: {
        cleanupRoot: $tab,
        cleanupSelector: ".erpwq-quotation-connections, .erpw-so-connections-workspace",
        insert: ($workspace) => {
          $tab.prepend($workspace);
        },
      },
      theme: {
        namespace: ".erpwDeliveryNoteConnectionWorkspace",
        workspaceClassName: "erpw-so-connections-workspace",
        pendingNoteClass: "erpw-so-connections-pending-note",
        groupClass: "erpw-so-connection-primary-group",
        groupCompactClass: "erpw-so-connection-primary-group-compact",
        groupHeadClass: "erpw-so-connection-primary-head",
        groupSummaryClass: "erpw-so-connection-primary-summary",
        groupIconClass: "erpw-so-connection-primary-icon",
        groupCopyClass: "erpw-so-connection-primary-copy",
        groupTitleClass: "erpw-so-connection-primary-title",
        groupNoteClass: "erpw-so-connection-primary-note",
        groupStatusClass: "erpw-so-connection-primary-status",
        itemsClass: "erpw-so-connection-primary-grid",
        itemClass: "erpw-so-connection-doc-card",
        itemCompactClass: "erpw-so-connection-doc-card-compact",
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
        secondaryRowCompactClass: "erpw-so-connections-secondary-row-compact",
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
      $nativeNodes.removeClass("erpwq-quotation-connections-native erpw-so-connections-source").show();
      return false;
    }

    $nativeNodes.addClass("erpw-so-connections-source").hide();
    return true;
  }

  function renderExecutionSummary(frm) {
    const $itemsSection = getSectionForField(frm, "items");
    if (!$itemsSection || !$itemsSection.length) {
      markFeatureMissing(frm, "items_execution_zone", { reason: "missing_items_section" });
      return false;
    }

    $itemsSection.find(".erpw-child-inline-summary-soft").remove();

    const items = Array.isArray(frm.doc.items) ? frm.doc.items : [];
    const warehouseNames = uniqueMeaningfulValues(items.map((item) => item && item.warehouse));
    const salesOrderNames = uniqueMeaningfulValues(items.map((item) => item && item.against_sales_order));
    const billedAmount = sumNumeric(items, "billed_amt");
    const chips = [];

    if (Number(frm.doc.is_return || 0) && hasMeaningfulValue(frm.doc.return_against)) {
      chips.push({
        label: `Return against ${frm.doc.return_against}`,
        tone: "blocker",
      });
    } else if (Number(frm.doc.per_billed || 0) > 0 && Number(frm.doc.per_billed || 0) < 100) {
      chips.push({
        label: `${pct(100 - Number(frm.doc.per_billed || 0))} still open to invoice`,
        tone: "attention",
      });
    }

    if (warehouseNames.length === 1) {
      chips.push({
        label: warehouseNames[0],
        tone: "neutral",
      });
    } else if (warehouseNames.length > 1) {
      chips.push({
        label: `${warehouseNames.length} source warehouses`,
        tone: "neutral",
      });
    }

    if (salesOrderNames.length === 1) {
      chips.push({
        label: `Source order ${salesOrderNames[0]}`,
        tone: "pending",
      });
    } else if (salesOrderNames.length > 1) {
      chips.push({
        label: `${salesOrderNames.length} source orders`,
        tone: "pending",
      });
    }

    const metrics = [
      {
        label: "Lines",
        value: items.length ? String(items.length) : "--",
      },
      {
        label: "Warehouses",
        value: warehouseNames.length ? String(warehouseNames.length) : "--",
      },
      {
        label: "Source Orders",
        value: salesOrderNames.length ? String(salesOrderNames.length) : "--",
      },
      {
        label: "Billed Value",
        value: formatMoney(billedAmount, frm.doc.currency),
        className: "erpw-so-inline-metric-grand",
      },
    ];

    if (typeof childPageSummaries.renderInlineSummary !== "function") {
      markFeatureMissing(frm, "items_execution_zone", { reason: "runtime_unavailable" });
      return false;
    }

    const $summary = childPageSummaries.renderInlineSummary($itemsSection, {
      chips,
      insertMode: "append-section",
      metrics,
      note: "Read invoice follow-through, warehouse context, and source order linkage while keeping the stock grid in place.",
      removeSelector: ".erpw-child-inline-summary-soft",
      summaryClass: "erpw-so-inline-summary erpw-child-inline-summary-soft",
      title: "Execution Focus",
    });
    if ($summary && $summary.length && $summary.parent().hasClass("form-group")) {
      $summary.detach();
      $itemsSection.append($summary);
    }

    markFeatureReady(frm, "items_execution_zone", {
      billed_value: billedAmount,
      lines: items.length,
      sales_orders: salesOrderNames.length,
      warehouses: warehouseNames.length,
    });
    return true;
  }

  function renderCommercialPosture(frm) {
    const $totalsSection = getSectionForField(frm, "grand_total") || getSectionForField(frm, "base_grand_total");
    if (!$totalsSection || !$totalsSection.length) {
      markFeatureMissing(frm, "commercial_posture", { reason: "missing_totals_section" });
      return false;
    }

    $totalsSection.find(".erpw-child-inline-summary-soft").remove();

    const taxRows = Array.isArray(frm.doc.taxes) ? frm.doc.taxes.length : 0;
    const hasDiscount = Number(frm.doc.additional_discount_percentage || 0) !== 0 || Number(frm.doc.discount_amount || 0) !== 0;
    const hasRounding = Number(frm.doc.rounding_adjustment || 0) !== 0;
    const chips = [];

    if (hasDiscount) {
      chips.push({
        label: "Additional discount applied",
        tone: "pending",
      });
    }
    if (hasRounding) {
      chips.push({
        label: "Rounded total active",
        tone: "pending",
      });
    }
    if (Number(frm.doc.is_return || 0)) {
      chips.push({
        label: "Return valuation",
        tone: "blocker",
      });
    }

    const metrics = [
      {
        label: "Items Total",
        value: formatMoney(frm.doc.total, frm.doc.currency),
      },
      {
        label: "Taxes",
        value: formatMoney(frm.doc.total_taxes_and_charges, frm.doc.currency),
      },
      {
        label: "Net Total",
        value: formatMoney(frm.doc.net_total, frm.doc.currency),
      },
      {
        label: "Grand Total",
        value: formatMoney(frm.doc.grand_total, frm.doc.currency),
        className: "erpw-so-inline-metric-grand",
      },
    ];

    if (typeof childPageSummaries.renderInlineSummary !== "function") {
      markFeatureMissing(frm, "commercial_posture", { reason: "runtime_unavailable" });
      return false;
    }

    childPageSummaries.renderInlineSummary($totalsSection, {
      chips,
      insertMode: "prepend-body",
      metrics,
      note: "Review delivery value, discount, rounding, and return impact before operational follow-up.",
      removeSelector: ".erpw-child-inline-summary-soft",
      summaryClass: "erpw-so-inline-summary erpw-child-inline-summary-soft",
      title: "Commercial Posture",
    });

    markFeatureReady(frm, "commercial_posture", {
      has_discount: hasDiscount,
      has_rounding: hasRounding,
      tax_rows: taxRows,
    });
    return true;
  }

  function renderDetailWorkspace(frm) {
    const $itemsSection = getSectionForField(frm, "items");
    if (!$itemsSection || !$itemsSection.length) {
      markFeatureMissing(frm, "detail_workspace", { reason: "missing_items_section" });
      return false;
    }

    const $currentWorkspace = $itemsSection.closest(".erpw-child-detail-workspace");
    const $snapshot = $currentWorkspace.length
      ? $currentWorkspace.prev(".erpw-child-detail-snapshot").first()
      : $itemsSection.prev(".erpw-child-detail-snapshot").first();
    const $scopeRoot = $currentWorkspace.length ? $currentWorkspace : $itemsSection.parent();
    const $standaloneSummary = $scopeRoot.children(".erpw-child-inline-summary-soft-standalone").first();
    const $taxesSection = getSectionForField(frm, "taxes");
    const $totalsSection = getSectionForField(frm, "grand_total") || getSectionForField(frm, "base_grand_total");

    const $workspace = ensureSharedDetailWorkspace([
      $itemsSection,
      $standaloneSummary,
      $taxesSection,
      $totalsSection,
    ], {
      className: "erpw-child-detail-workspace",
      insertAfter: $snapshot,
      scope: "delivery-note",
    });

    if (!$workspace.length) {
      markFeatureMissing(frm, "detail_workspace", { reason: "runtime_unavailable" });
      return false;
    }

    markFeatureReady(frm, "detail_workspace", {
      sections: $workspace.children().length || 0,
    });
    return true;
  }

  function enhanceSupportArea(frm) {
    if (typeof childPageSupport.enhanceSupportArea === "function") {
      return childPageSupport.enhanceSupportArea(frm);
    }
    markFeatureMissing(frm, "support_shell", { reason: "runtime_unavailable" });
    return false;
  }

  function cleanSidebarUtilityRail(frm) {
    if (typeof childPageSidebar.cleanSidebarUtilityRail === "function") {
      return childPageSidebar.cleanSidebarUtilityRail(frm);
    }
    markFeatureMissing(frm, "sidebar_cleanup", { reason: "runtime_unavailable" });
    return false;
  }

  function enhanceWorkflowReadonlyBanner(frm) {
    if (typeof childPageSupport.enhanceWorkflowReadonlyBanner === "function") {
      return childPageSupport.enhanceWorkflowReadonlyBanner(frm, {
        title: "Workflow-controlled delivery",
      });
    }
    markFeatureMissing(frm, "workflow_banner", { reason: "runtime_unavailable" });
    return false;
  }

  function renderDetailsSnapshot(frm) {
    const $topSection = getSectionForField(frm, "customer");
    const $itemsSection = getSectionForField(frm, "items");
    if (!$itemsSection || !$itemsSection.length) {
      markFeatureMissing(frm, "details_snapshot", { reason: "missing_items_section" });
      return false;
    }

    $itemsSection.closest(".erpw-child-detail-workspace").prev(".erpw-child-detail-snapshot").first().remove();
    $itemsSection.prev(".erpw-child-detail-snapshot").first().remove();

    const isSubmitted = Number(frm.doc.docstatus || 0) === 1;
    if (!$topSection || !$topSection.length || !isSubmitted) {
      setManagedSectionVisibility($topSection, true, "erpwdn-details-hidden-source");
      markFeatureMissing(frm, "details_snapshot", { reason: "draft_or_missing_top_section" });
      return false;
    }

    const items = Array.isArray(frm.doc.items) ? frm.doc.items : [];
    const warehouseNames = uniqueMeaningfulValues(items.map((item) => item && item.warehouse));
    const movementLabel = Number(frm.doc.is_return || 0)
      ? (hasMeaningfulValue(frm.doc.return_against) ? `Return against ${frm.doc.return_against}` : "Return delivery")
      : "Standard delivery";
    const statusLabel = Number(frm.doc.is_return || 0) ? "Return" : "Posted";

    const metrics = [
      {
        label: "Customer",
        value: frm.doc.customer_name || frm.doc.customer || "--",
      },
      {
        label: "Posted",
        value: formatPostingContextLabel(frm.doc.posting_date, frm.doc.posting_time),
      },
      {
        label: "Movement",
        value: movementLabel,
      },
      {
        label: "Warehouse",
        value: warehouseContextLabel(warehouseNames),
      },
    ];

    if (typeof childPageDetails.renderDetailSnapshot !== "function") {
      setManagedSectionVisibility($topSection, true, "erpwdn-details-hidden-source");
      markFeatureMissing(frm, "details_snapshot", { reason: "runtime_unavailable" });
      return false;
    }

    childPageDetails.renderDetailSnapshot($itemsSection, {
      kicker: "Dispatch Snapshot",
      metrics,
      note: "Read the posted delivery context here, then work the delivery item grid below.",
      removeSelector: ".erpw-child-detail-snapshot",
      snapshotClass: "erpw-child-detail-snapshot",
      statusText: statusLabel,
      statusTone: Number(frm.doc.is_return || 0) ? "attention" : "active",
    });
    setManagedSectionVisibility($topSection, false, "erpwdn-details-hidden-source");
    markFeatureReady(frm, "details_snapshot", {
      movement: movementLabel,
      warehouses: warehouseNames.length,
    });
    return true;
  }

  function renderItemsSectionHeader(frm) {
    const $itemsSection = getSectionForField(frm, "items");
    if (!$itemsSection || !$itemsSection.length) {
      markFeatureMissing(frm, "items_section_header", { reason: "missing_items_section" });
      return false;
    }

    const items = Array.isArray(frm.doc.items) ? frm.doc.items : [];
    const statusLabel = Number(frm.doc.is_return || 0)
      ? "Return lines"
      : `${items.length || 0} ${items.length === 1 ? "line" : "lines"}`;

    $itemsSection.addClass("erpwdn-items-section");
    $itemsSection.find(".erpw-child-section-header").remove();

    if (typeof childPageDetails.renderSectionHeader !== "function") {
      markFeatureMissing(frm, "items_section_header", { reason: "runtime_unavailable" });
      return false;
    }

    childPageDetails.renderSectionHeader($itemsSection, {
      headerClass: "erpw-child-section-header",
      note: "Review delivered items, warehouses, quantities, and linked order context before follow-up.",
      removeSelector: ".erpw-child-section-header",
      statusText: statusLabel,
      statusTone: "neutral",
      title: "Execution Lines",
    });

    markFeatureReady(frm, "items_section_header", {
      lines: items.length,
      return_mode: Number(frm.doc.is_return || 0) === 1,
    });
    return true;
  }

  function refineCommercialSectionBody(frm) {
    const $totalsSection = getSectionForField(frm, "grand_total") || getSectionForField(frm, "base_grand_total");
    if (!$totalsSection || !$totalsSection.length) {
      markFeatureMissing(frm, "commercial_section_cleanup", { reason: "missing_totals_section" });
      return false;
    }

    const isSubmitted = Number(frm.doc.docstatus || 0) === 1;
    const hasRoundingSignal = !nearlyEqual(frm.doc.rounding_adjustment || 0, 0)
      || !nearlyEqual(frm.doc.rounded_total || frm.doc.grand_total || 0, frm.doc.grand_total || 0)
      || Number(frm.doc.disable_rounded_total || 0) === 1;
    const collapseToSummaryOnly = isSubmitted && !hasRoundingSignal && !hasAdditionalDiscountSignal(frm);
    const $existingStandalone = $totalsSection.prev(".erpw-child-inline-summary-soft-standalone");
    const $summary = $totalsSection.find(".erpw-child-inline-summary-soft").first();

    toggleField(frm, "grand_total", !collapseToSummaryOnly && !isSubmitted);
    toggleField(frm, "base_grand_total", false);
    toggleField(frm, "rounded_total", !collapseToSummaryOnly && hasRoundingSignal);
    toggleField(frm, "base_rounded_total", false);
    toggleField(frm, "rounding_adjustment", !collapseToSummaryOnly && hasRoundingSignal);
    toggleField(frm, "base_rounding_adjustment", false);
    toggleField(frm, "disable_rounded_total", !isSubmitted && hasRoundingSignal);
    toggleField(frm, "in_words", !collapseToSummaryOnly && hasMeaningfulValue(frm.doc.in_words));
    toggleField(frm, "base_in_words", false);

    $totalsSection.toggleClass("erpwdn-commercial-summary-only", collapseToSummaryOnly);

    if (collapseToSummaryOnly && $summary.length) {
      $existingStandalone.remove();
      const $standalone = $('<div class="erpw-child-inline-summary-soft-standalone"></div>');
      $standalone.append($summary.detach());
      $totalsSection.before($standalone);
      setManagedSectionVisibility($totalsSection, false, "erpwdn-details-hidden-source");
    } else {
      if ($existingStandalone.length && $summary.length === 0) {
        const $standaloneSummary = $existingStandalone.find(".erpw-child-inline-summary-soft").first();
        if ($standaloneSummary.length) {
          const $body = $totalsSection.children(".section-body").first();
          if ($body.length) {
            $body.prepend($standaloneSummary.detach());
          } else {
            $totalsSection.prepend($standaloneSummary.detach());
          }
        }
      }
      $existingStandalone.remove();
      setManagedSectionVisibility($totalsSection, true, "erpwdn-details-hidden-source");
    }

    markFeatureReady(frm, "commercial_section_cleanup", {
      collapse_to_summary_only: collapseToSummaryOnly,
      has_rounding_signal: hasRoundingSignal,
    });
    return true;
  }

  function bindTabEnhancers(frm) {
    bindRuntimeTabEnhancers(frm, {
      namespace: ".erpwDeliveryNoteTabs",
      fastKey: "delivery_note_tab_enhancers_fast",
      lateKey: "delivery_note_tab_enhancers_late",
      fastDelay: 0,
      lateDelay: 180,
      run: () => {
        enhanceAddressContactTab(frm);
        enhanceTermsOutputTab(frm);
        enhanceMoreInfoTab(frm);
        renderConnectionsWorkspace(frm, frm.__erpwDeliveryNoteContext || draftContext(frm));
      },
    });
  }

  function enhanceFormBody(frm) {
    if (!frm || !frm.fields_dict) return;

    ensureDeliveryNoteCriticalStyles();

    const $root = getFormRoot(frm);
    if ($root.length) {
      $root.addClass("erpw-so-form-enhanced erpwdn-delivery-form-enhanced");
    }

    bindTabEnhancers(frm);
    enhanceDetailsGovernance(frm);
    renderDetailsSnapshot(frm);
    renderItemsSectionHeader(frm);
    renderExecutionSummary(frm);
    renderCommercialPosture(frm);
    refineCommercialSectionBody(frm);
    renderDetailWorkspace(frm);

    runRetriedEnhancers(frm, [
      {
        fastKey: "delivery_note_address_retry_fast",
        lateKey: "delivery_note_address_retry_late",
        fastDelay: 220,
        lateDelay: 760,
        run: () => enhanceAddressContactTab(frm),
      },
      {
        fastKey: "delivery_note_terms_output_retry_fast",
        lateKey: "delivery_note_terms_output_retry_late",
        fastDelay: 220,
        lateDelay: 760,
        run: () => enhanceTermsOutputTab(frm),
      },
      {
        fastKey: "delivery_note_more_info_retry_fast",
        lateKey: "delivery_note_more_info_retry_late",
        fastDelay: 220,
        lateDelay: 760,
        run: () => enhanceMoreInfoTab(frm),
      },
      {
        fastKey: "delivery_note_sidebar_retry_fast",
        lateKey: "delivery_note_sidebar_retry_late",
        fastDelay: 420,
        lateDelay: 980,
        run: () => cleanSidebarUtilityRail(frm),
      },
      {
        fastKey: "delivery_note_support_retry_fast",
        lateKey: "delivery_note_support_retry_late",
        fastDelay: 420,
        lateDelay: 980,
        run: () => enhanceSupportArea(frm),
      },
      {
        fastKey: "delivery_note_workflow_banner_retry_fast",
        lateKey: "delivery_note_workflow_banner_retry_late",
        fastDelay: 220,
        lateDelay: 760,
        run: () => enhanceWorkflowReadonlyBanner(frm),
      },
      {
        fastKey: "delivery_note_connections_retry_fast",
        lateKey: "delivery_note_connections_retry_late",
        fastDelay: 420,
        lateDelay: 980,
        run: () => renderConnectionsWorkspace(frm, frm.__erpwDeliveryNoteContext || draftContext(frm)),
      },
    ]);
  }

  function renderShell(frm, data) {
    ensureDeliveryNoteCriticalStyles();
    const summary = data.summary || {};
    const linked = data.linked_documents || {};
    const support = data.support || {};
    const $shell = getShell(frm);
    const actions = actionConfig(frm, data).map((action, idx) => ({ ...action, idx }));
    const primaryActions = actions.filter((action) => action.variant === "primary");
    const secondaryActions = actions.filter((action) => action.variant !== "primary");
    const billingValue = Number(summary.per_billed || 0) > 0 ? `${pct(summary.per_billed)} billed` : "Not billed";
    const billingMeta = Number(summary.invoice_count || 0) > 0
      ? `${Number(summary.invoice_count || 0)} invoice${Number(summary.invoice_count || 0) === 1 ? "" : "s"} linked`
      : "No invoice linked yet";
    const subtitleParts = [summary.customer_label || "Customer not selected yet"];
    if (summary.posting_date) {
      subtitleParts.push(`Posted ${formatDateLabel(summary.posting_date)}`);
    }
    const summaryChips = [
      { label: summary.status || "Draft", tone: "approved" },
      summary.workflow_state ? { label: summary.workflow_state, tone: "pending" } : null,
      Number(summary.is_return || 0) ? { label: "Return", tone: "blocker" } : null,
      !Number(summary.is_return || 0) && Number(summary.return_count || 0) > 0
        ? { label: `${summary.return_count} Return Linked`, tone: "blocker" }
        : null,
    ].filter(Boolean);
    const summaryFacts = [
      {
        label: "Grand Total",
        value: formatMoney(summary.grand_total, summary.currency),
      },
      {
        label: "Quantity",
        value: hasMeaningfulValue(summary.total_qty) ? String(summary.total_qty) : "--",
      },
      {
        label: "Billing",
        value: billingValue,
        meta: billingMeta,
      },
    ];
    const hasReturns = Number(summary.is_return || 0) || Number(summary.return_count || 0) > 0;
    const unbilled = Number(summary.per_billed || 0) < 100 && Number(summary.grand_total || 0) > 0;
    const guidanceCards = applySalesConsoleGuidancePolicy([
      hasReturns || unbilled ? {
        attention: true,
        chipLabel: "Priority",
        className: "erpw-child-guidance-card-primary",
        iconMarkup: '<svg viewBox="0 0 24 24"><path d="M6 12h12M13 7l5 5l-5 5" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/></svg>',
        text: support.next_action || (hasReturns
          ? "Review return impact before confirming fulfillment status."
          : "Confirm billing follow-through for this delivered value."),
        title: hasReturns ? "Return Impact" : "Billing Follow-Up",
      } : null,
      support.customer_response_hint && (hasReturns || unbilled) ? {
        attention: true,
        chipClass: "erpw-child-guidance-chip-secondary",
        chipLabel: "Communication",
        className: "erpw-child-guidance-card-secondary",
        iconMarkup: '<svg viewBox="0 0 24 24"><path d="M12 13a3.5 3.5 0 1 0 0-7a3.5 3.5 0 0 0 0 7zm-6 6a6 6 0 0 1 12 0" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/></svg>',
        text: support.customer_response_hint,
        title: "Customer Response",
      } : null,
    ]);
    if (typeof childPageShellContent.renderShellContent === "function") {
      childPageShellContent.renderShellContent($shell, {
        actionIconMarkup,
        actions,
        guidance: {
          cards: guidanceCards,
          title: "Attention",
        },
        summary: {
          chips: summaryChips,
          facts: summaryFacts,
          kicker: "Delivery Note",
          subtitle: subtitleParts.join(" • "),
          title: summary.name || frm.doc.name || "Delivery Note",
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
              <div class="erpw-child-kicker">Delivery Note</div>
              <h2 class="erpw-child-title">${escapeHtml(summary.name || frm.doc.name || "Delivery Note")}</h2>
              <div class="erpw-child-subtitle">${escapeHtml(subtitleParts.join(" • "))}</div>
            </div>
            <div class="erpw-child-chip-row erpw-child-chip-row-header">
              <span class="erpw-child-chip approved">${escapeHtml(summary.status || "Draft")}</span>
              ${summary.workflow_state ? `<span class="erpw-child-chip pending">${escapeHtml(summary.workflow_state)}</span>` : ""}
              ${Number(summary.is_return || 0) ? '<span class="erpw-child-chip blocker">Return</span>' : ""}
              ${!Number(summary.is_return || 0) && Number(summary.return_count || 0) > 0 ? `<span class="erpw-child-chip blocker">${escapeHtml(`${summary.return_count} Return Linked`)}</span>` : ""}
            </div>
          </div>
        </div>
        <div class="erpw-child-summary-facts">
          <div class="erpw-child-fact">
            <div class="erpw-child-fact-label">Grand Total</div>
            <div class="erpw-child-fact-value">${escapeHtml(formatMoney(summary.grand_total, summary.currency))}</div>
          </div>
          <div class="erpw-child-fact">
            <div class="erpw-child-fact-label">Quantity</div>
            <div class="erpw-child-fact-value">${escapeHtml(hasMeaningfulValue(summary.total_qty) ? String(summary.total_qty) : "--")}</div>
          </div>
          <div class="erpw-child-fact">
            <div class="erpw-child-fact-label">Billing</div>
            <div class="erpw-child-fact-value">${escapeHtml(billingValue)}</div>
            <div class="erpw-child-fact-meta">${escapeHtml(billingMeta)}</div>
          </div>
        </div>
      </section>

      <section class="erpw-child-card erpw-child-actions erpw-child-actions-band">
        <div class="erpw-child-action-stack">
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
            <div class="erpw-child-guidance-text">${escapeHtml(support.next_action || "Continue normal fulfillment follow-through.")}</div>
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
            <div class="erpw-child-guidance-text">${escapeHtml(support.customer_response_hint || "Confirm delivery and billing posture before giving customer-facing status updates.")}</div>
          </article>
          <article class="erpw-child-guidance-card erpw-child-guidance-card-secondary">
            <div class="erpw-child-guidance-head">
              <span class="erpw-child-guidance-icon" aria-hidden="true">
                <svg viewBox="0 0 24 24"><path d="M12 6v6l4 2M12 21a9 9 0 1 0 0-18a9 9 0 0 0 0 18z" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/></svg>
              </span>
              <div class="erpw-child-guidance-copy">
                <div class="erpw-child-guidance-title">Fulfillment Note</div>
                <div class="erpw-child-guidance-chip erpw-child-guidance-chip-secondary">Operations</div>
              </div>
            </div>
            <div class="erpw-child-guidance-text">${escapeHtml(support.fulfillment_note || support.approval_note || "Use the summary above as the main operating read for this delivery note.")}</div>
          </article>
        </div>
      </section>
    `);

    actions.forEach((action) => {
      $shell.find(`[data-action-index="${action.idx}"]`).on("click", action.handler);
    });
  }

  function loadContext(frm) {
    if (!frm || frm.doctype !== "Delivery Note") return;
    ensureDeliveryNoteCriticalStyles();
    const signature = getContextSignature(frm);
    if (frm.__erpwContextLoadingSignature === signature) {
      markFeatureStatus(frm, "context_load", "inflight", { signature });
      return;
    }
    if (frm.__erpwContextRenderedSignature === signature) {
      const $shell = getShell(frm);
      const shellNeedsRender = !$shell.children().length || !!$shell.children(".erpw-so-shell-skeleton").length;
      if (shellNeedsRender) {
        if (frm.__erpwDeliveryNoteContext) {
          renderShell(frm, frm.__erpwDeliveryNoteContext);
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
      frm.__erpwDeliveryNoteContext = draft;
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
    if (frm.__erpwContextTimeoutTimer) {
      clearTimeout(frm.__erpwContextTimeoutTimer);
      delete frm.__erpwContextTimeoutTimer;
    }
    markFeatureStatus(frm, "context_load", "loading", {
      requestId,
      signature,
      source: "remote",
    });

    frm.__erpwContextTimeoutTimer = setTimeout(() => {
      if (frm.__erpwContextRequestId !== requestId || frm.__erpwContextLoadingSignature !== signature) {
        return;
      }

      const fallback = contextFallbackFromDoc(frm);
      frm.__erpwDeliveryNoteContext = fallback;
      renderShell(frm, fallback);
      frm.__erpwContextRenderedSignature = signature;
      frm.__erpwContextRenderedName = frm.doc && frm.doc.name;
      frm.__erpwContextLoadingSignature = null;
      markFeatureMissing(frm, "context_load", {
        requestId,
        signature,
        source: "timeout_fallback",
        reason: "request_timeout",
      });
      scheduleFormEnhance(frm);
    }, 5200);

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
      frm.__erpwDeliveryNoteContext = message;
      renderShell(frm, message);
      frm.__erpwContextRenderedSignature = signature;
      frm.__erpwContextRenderedName = frm.doc.name;
      if (frm.__erpwContextTimeoutTimer) {
        clearTimeout(frm.__erpwContextTimeoutTimer);
        delete frm.__erpwContextTimeoutTimer;
      }
      scheduleFormEnhance(frm);
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
      getShell(frm).html('<section class="erpw-child-card erpw-child-loading">Delivery note workspace context is temporarily unavailable.</section>');
      if (frm.__erpwContextTimeoutTimer) {
        clearTimeout(frm.__erpwContextTimeoutTimer);
        delete frm.__erpwContextTimeoutTimer;
      }
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
        if (frm.__erpwContextTimeoutTimer) {
          clearTimeout(frm.__erpwContextTimeoutTimer);
          delete frm.__erpwContextTimeoutTimer;
        }
        markFeatureStatus(frm, "context_load", "idle", {
          requestId,
          signature,
        });
      }
    }, () => {
      if (frm.__erpwContextRequestId === requestId) {
        frm.__erpwContextLoadingSignature = null;
        if (frm.__erpwContextTimeoutTimer) {
          clearTimeout(frm.__erpwContextTimeoutTimer);
          delete frm.__erpwContextTimeoutTimer;
        }
        markFeatureStatus(frm, "context_load", "idle", {
          requestId,
          signature,
        });
      }
    });
  }

  frappe.ui.form.on("Delivery Note", {
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
      scheduleFormTask(frm, "connections_refresh_fast", 0, () => renderConnectionsWorkspace(frm, frm.__erpwDeliveryNoteContext || draftContext(frm)));
      scheduleFormTask(frm, "connections_refresh_late", 180, () => renderConnectionsWorkspace(frm, frm.__erpwDeliveryNoteContext || draftContext(frm)));
    },
  });

  function bootstrapCurrentDeliveryNoteForm() {
    if (!window.cur_frm || cur_frm.doctype !== "Delivery Note") return false;
    if (!cur_frm.page || !cur_frm.page.main) return false;
    loadContext(cur_frm);
    return true;
  }

  if (window.erpWorkspaceUiBoot && typeof window.erpWorkspaceUiBoot.registerChildPageBootstrap === "function") {
    window.erpWorkspaceUiBoot.registerChildPageBootstrap("Delivery Note", bootstrapCurrentDeliveryNoteForm);
  }

  $(document).ready(() => {
    setTimeout(bootstrapCurrentDeliveryNoteForm, 120);
  });
})();
