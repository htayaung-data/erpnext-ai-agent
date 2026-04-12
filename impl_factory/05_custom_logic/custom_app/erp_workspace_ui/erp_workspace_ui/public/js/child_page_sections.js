(function () {
  const root = window;
  const childPageRuntime = root.erpWorkspaceUiChildPage = root.erpWorkspaceUiChildPage || {};
  const childPageHelpers = childPageRuntime.helpers || {};

  const escapeHtml = childPageHelpers.escapeHtml || function (value) {
    return frappe.utils.escape_html(value == null ? "" : String(value));
  };

  function ensureSectionStack($tab, className) {
    if (!$tab || !$tab.length || !className) return $();

    let $stack = $tab.children(`.${className}`).first();
    if ($stack.length) return $stack;

    $stack = $(`<div class="${className}"></div>`);
    $tab.prepend($stack);
    return $stack;
  }

  function countVisibleControls($container, options) {
    if (!$container || !$container.length) return 0;

    const settings = Object.assign({
      directChildren: false,
      selector: ".frappe-control",
    }, options || {});

    const $controls = settings.directChildren
      ? $container.children(settings.selector)
      : $container.find(settings.selector);

    return $controls.toArray().filter((element) => {
      const $control = $(element);
      if ($control.hasClass("hide-control") || $control.hasClass("hidden")) return false;
      if ($control.css("display") === "none") return false;
      const inlineStyle = String($control.attr("style") || "").toLowerCase();
      if (inlineStyle.includes("display: none")) return false;
      return true;
    }).length;
  }

  function hasVisibleControls($container, options) {
    return countVisibleControls($container, options) > 0;
  }

  const coreAddressFieldOrder = Object.freeze([
    "contact_person",
    "contact_mobile",
    "contact_email",
    "territory",
    "customer_address",
    "address_display",
  ]);

  const coreAddressPlaceholders = Object.freeze({
    contact_person: "",
    contact_mobile: "",
    customer_address: "",
    address_display: "",
    contact_email: "",
    territory: "",
  });

  const coreAddressLabels = Object.freeze({
    contact_person: "Contact Person",
    contact_mobile: "Mobile No",
    contact_email: "Contact Email",
    territory: "Territory",
    customer_address: "Customer Address",
    address_display: "Address",
  });

  function hasMeaningfulFieldValue(value) {
    if (value == null) return false;
    if (typeof value === "number") return !Number.isNaN(value);
    if (typeof value === "boolean") return value;
    if (typeof value === "string") return value.trim() !== "";
    if (Array.isArray(value)) return value.length > 0;
    return Boolean(value);
  }

  function applyFieldPlaceholder($wrapper, value, placeholder) {
    if (!$wrapper || !$wrapper.length) return;

    const emptyLabel = placeholder == null ? "" : String(placeholder);
    const isEmpty = !hasMeaningfulFieldValue(value);
    const $input = $wrapper.find(".control-input :input").first();
    const $richTarget = $wrapper.find(".control-value.for-description .ql-editor.read-mode").first();
    const $target = $richTarget.length ? $richTarget : $wrapper.find(".control-value").first();
    const $displayValue = $richTarget.length
      ? $richTarget.closest(".control-value.for-description").first()
      : $target;

    if ($input.length) {
      if (isEmpty) {
        $input.attr("placeholder", emptyLabel);
      } else if (String($input.attr("placeholder") || "") === emptyLabel) {
        $input.attr("placeholder", "");
      }
    }

    if (!$target.length) return;

    if (isEmpty) {
      $target
        .addClass("erpw-read-value-empty")
        .attr("data-erpw-empty-label", emptyLabel);
      if ($displayValue.length && $displayValue.get(0) !== $target.get(0)) {
        $displayValue
          .addClass("erpw-read-value-empty")
          .attr("data-erpw-empty-label", emptyLabel);
      }
    } else {
      $target
        .removeClass("erpw-read-value-empty")
        .removeAttr("data-erpw-empty-label");
      if ($displayValue.length && $displayValue.get(0) !== $target.get(0)) {
        $displayValue
          .removeClass("erpw-read-value-empty")
          .removeAttr("data-erpw-empty-label");
      }
    }
  }

  function normalizeAddressFieldLabel($wrapper, fieldname) {
    if (!$wrapper || !$wrapper.length || !fieldname) return;
    const $label = $wrapper.find(".control-label").first();
    if (!$label.length) return;
    if (String($label.text() || "").trim()) return;
    const fallback = coreAddressLabels[fieldname];
    if (fallback) {
      $label.text(fallback);
    }
  }

  function forceAddressFieldReadMode($wrapper, fieldname) {
    if (!$wrapper || !$wrapper.length) return;

    normalizeAddressFieldLabel($wrapper, fieldname);

    $wrapper.find(".control-input, .link-btn").css("display", "none");
    const $value = $wrapper.find(".control-value").first();
    if ($value.length) {
      $value.css("display", "block");
    }
  }

  function arrangeAddressFieldGrid($section, options) {
    if (!$section || !$section.length) return $();

    const settings = Object.assign({
      fieldnames: coreAddressFieldOrder,
      getWrapper: null,
      placeholders: coreAddressPlaceholders,
      values: {},
    }, options || {});

    const $body = $section.children(".section-body").first();
    if (!$body.length) return $();

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

    settings.fieldnames.forEach((fieldname) => {
      if (!fieldname) return;

      const $wrapper = typeof settings.getWrapper === "function"
        ? settings.getWrapper(fieldname)
        : $section.find(`.frappe-control[data-fieldname="${fieldname}"]`).first();
      if (!$wrapper || !$wrapper.length || !$wrapper.closest($section).length) return;

      if (Object.prototype.hasOwnProperty.call(settings.placeholders, fieldname)) {
        const value = settings.values && Object.prototype.hasOwnProperty.call(settings.values, fieldname)
          ? settings.values[fieldname]
          : undefined;
        applyFieldPlaceholder($wrapper, value, settings.placeholders[fieldname]);
      }

      $wrapper
        .removeClass("hide-control hidden")
        .addClass("erpw-so-address-grid-field")
        .attr("data-address-grid-field", fieldname)
        .css("display", "")
        .appendTo($grid);

      $wrapper.find(".hide-control, .hidden").removeClass("hide-control hidden").css("display", "");
      forceAddressFieldReadMode($wrapper, fieldname);
    });

    $body.children(".form-column").each((_, element) => {
      const $column = $(element);
      const hasVisibleContent = hasVisibleControls($column);
      $column.toggleClass("erpw-so-address-column-empty", !hasVisibleContent).toggle(hasVisibleContent);
    });

    $grid.toggle($grid.children(".frappe-control").length > 0);
    return $grid;
  }

  function relocateFieldIntoSectionBody($wrapper, $section, scopeKey) {
    if (!$wrapper || !$wrapper.length || !$section || !$section.length) return;
    if ($wrapper.closest($section).length) return;

    let $marker = $wrapper.data("erpwRestoreMarker");
    if (!$marker || !$marker.length) {
      $marker = $('<div class="erpw-field-restore-marker" hidden></div>');
      $wrapper.before($marker);
      $wrapper.data("erpwRestoreMarker", $marker);
    }

    $wrapper.attr("data-erpw-relocated-key", scopeKey);
    const $body = $section.children(".section-body").first();
    if ($body.length) {
      $body.append($wrapper);
    }
  }

  function restoreRelocatedFieldPlacements($root, scopeKey) {
    if (!$root || !$root.length || !scopeKey) return;

    $root.find(`.frappe-control[data-erpw-relocated-key="${scopeKey}"]`).each((_, element) => {
      const $wrapper = $(element);
      const $marker = $wrapper.data("erpwRestoreMarker");
      if ($marker && $marker.length) {
        $wrapper.insertAfter($marker);
        $marker.remove();
      }
      $wrapper.removeAttr("data-erpw-relocated-key");
      $wrapper.removeData("erpwRestoreMarker");
    });
  }

  function ensureDetailWorkspace(nodes, options) {
    const settings = Object.assign({
      className: "erpw-child-detail-workspace",
      insertAfter: null,
      scope: "",
    }, options || {});

    const elements = [];
    const pushNode = (candidate) => {
      if (!candidate) return;
      const $candidate = candidate.jquery ? candidate : $(candidate);
      if (!$candidate || !$candidate.length) return;
      $candidate.each((_, element) => {
        if (!element || elements.includes(element)) return;
        elements.push(element);
      });
    };

    if (Array.isArray(nodes)) {
      nodes.forEach(pushNode);
    } else {
      pushNode(nodes);
    }

    const $nodes = $(elements);
    if (!$nodes.length) return $();

    const classSelector = `.${settings.className}`;
    const unwrapWorkspace = ($workspace) => {
      if (!$workspace || !$workspace.length) return;
      $workspace.replaceWith($workspace.contents());
    };

    $nodes.each((_, element) => {
      const $node = $(element);
      const $workspace = $node.closest(classSelector);
      if ($workspace.length) {
        unwrapWorkspace($workspace);
      }
    });

    const $firstNode = $nodes.first();
    const $parent = $firstNode.parent();
    if (!$parent.length) return $();

    $parent.children(classSelector).each((_, element) => {
      unwrapWorkspace($(element));
    });

    return $parent;
  }

  function ensureSectionStatePanel($section, baseClass) {
    const prefix = String(baseClass || "").trim();
    if (!$section || !$section.length || !prefix) return $();

    const $body = $section.children(".section-body").first();
    if (!$body.length) return $();

    let $panel = $body.children(`.${prefix}-state-panel`).first();
    if ($panel.length) return $panel;

    $panel = $(`
      <div class="${prefix}-state-panel" hidden>
        <div class="${prefix}-state-copy">
          <div class="${prefix}-state-title"></div>
          <div class="${prefix}-state-note"></div>
        </div>
        <button type="button" class="${prefix}-state-action"></button>
      </div>
    `);

    $body.prepend($panel);
    return $panel;
  }

  function ensureMoreInfoMetrics($section) {
    const $body = $section.children(".section-body").first();
    if (!$body.length) return $();

    let $metrics = $body.children(".erpw-so-moreinfo-metrics").first();
    if ($metrics.length) return $metrics;

    $metrics = $('<div class="erpw-so-moreinfo-metrics"></div>');
    $body.prepend($metrics);
    return $metrics;
  }

  function applyMoreInfoMetrics($section, presentation) {
    if (!$section || !$section.length) return;

    const metrics = presentation && Array.isArray(presentation.metrics) ? presentation.metrics : [];
    const $metrics = ensureMoreInfoMetrics($section);
    if (!$metrics.length) return;

    if (!metrics.length) {
      $metrics.empty().hide();
      return;
    }

    $metrics.html(metrics.map((metric) => `
      <div class="erpw-so-moreinfo-metric">
        <div class="erpw-so-moreinfo-metric-label">${escapeHtml(metric.label)}</div>
        <div class="erpw-so-moreinfo-metric-value">${escapeHtml(metric.value)}</div>
      </div>
    `).join(""));
    $metrics.show();
  }

  function setSectionStatus($header, statusSelector, statusText, statusTone) {
    if (!$header || !$header.length) return;

    const text = String(statusText || "").trim();
    const tone = String(statusTone || "neutral").trim();
    const $status = $header.find(statusSelector).first();
    if (!$status.length) return;

    if (text) {
      $status.text(text).attr("data-tone", tone).prop("hidden", false);
    } else {
      $status.text("").removeAttr("data-tone").prop("hidden", true);
    }
  }

  function formatAddressRecordLabel(value) {
    const raw = String(value == null ? "" : value).trim();
    if (!raw) return "";

    function collapseSegment(segment) {
      const normalized = String(segment || "").trim();
      const withoutTrailingSeparator = normalized.replace(/\s*-\s*$/, "").trim();
      if (withoutTrailingSeparator && withoutTrailingSeparator !== normalized) {
        return withoutTrailingSeparator;
      }
      if (!normalized.includes("-")) return normalized;
      const parts = normalized.split("-").map((part) => part.trim()).filter(Boolean);
      if (parts.length === 2 && parts[0].toLowerCase() === parts[1].toLowerCase()) {
        return parts[0];
      }
      return normalized;
    }

    const separator = " - ";
    const separatorIndex = raw.lastIndexOf(separator);
    if (separatorIndex === -1) {
      return collapseSegment(raw);
    }

    const prefix = raw.slice(0, separatorIndex).trim();
    const suffix = raw.slice(separatorIndex + separator.length).trim();
    const collapsedSuffix = collapseSegment(suffix);
    if (!collapsedSuffix || collapsedSuffix === suffix) return raw;
    return `${prefix}${separator}${collapsedSuffix}`;
  }

  function normalizeAddressFieldDisplays($container, fieldnames) {
    if (!$container || !$container.length || !Array.isArray(fieldnames)) return;

    fieldnames.forEach((fieldname) => {
      if (!fieldname) return;
      const $control = $container.find(`.frappe-control[data-fieldname="${fieldname}"]`).first();
      if (!$control.length) return;

      const $value = $control.find('.control-value').first();
      if (!$value.length || $value.hasClass('for-description')) return;

      const $link = $value.find('a').first();
      if ($link.length) {
        const original = String($link.attr('data-erpw-raw-label') || $link.text() || '').trim();
        if (!original) return;
        const normalized = formatAddressRecordLabel(original);
        if (!normalized || normalized === original) return;
        $link.attr('data-erpw-raw-label', original).attr('title', original).text(normalized);
        return;
      }

      const original = String($value.attr('data-erpw-raw-label') || $value.text() || '').trim();
      if (!original) return;
      const normalized = formatAddressRecordLabel(original);
      if (!normalized || normalized === original) return;
      $value.attr('data-erpw-raw-label', original).attr('title', original).text(normalized);
    });
  }

  function ensureAddressSectionHeader($section, options) {
    if (!$section || !$section.length) return $();

    const settings = Object.assign({
      defaultHeadClass: "erpw-so-address-default-head",
      headerClass: "erpw-so-address-header",
      iconMarkup: "",
      note: "",
      statusText: "",
      statusTone: "neutral",
      title: "",
    }, options || {});

    const $defaultHead = $section.children(".section-head").first();
    if ($defaultHead.length) {
      $defaultHead.addClass(settings.defaultHeadClass).hide();
    }

    let $header = $section.children(`.${settings.headerClass}`).first();
    if (!$header.length) {
      $header = $(`
        <div class="${settings.headerClass}">
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

    $header.find(".erpw-so-address-header-icon").html(settings.iconMarkup || "");
    $header.find(".erpw-so-address-header-title").text(settings.title || "");
    $header.find(".erpw-so-address-header-note").text(settings.note || "");
    setSectionStatus($header, ".erpw-so-address-header-status", settings.statusText, settings.statusTone);

    return $header;
  }

  function ensureMoreInfoSectionHeader($section, options) {
    if (!$section || !$section.length) return $();

    const settings = Object.assign({
      ariaLabel: "",
      defaultHeadClass: "erpw-so-moreinfo-default-head",
      expanded: true,
      headerClass: "erpw-so-moreinfo-header",
      interactive: false,
      note: "",
      showToggle: false,
      statusText: "",
      statusTone: "neutral",
      title: "",
    }, options || {});

    const $defaultHead = $section.children(".section-head").first();
    if ($defaultHead.length) {
      $defaultHead.addClass(settings.defaultHeadClass).hide();
    }

    let $header = $section.children(`.${settings.headerClass}`).first();
    if (!$header.length) {
      $header = $(`
        <div class="${settings.headerClass}">
          <div class="erpw-so-moreinfo-header-copy">
            <div class="erpw-so-moreinfo-header-title"></div>
            <div class="erpw-so-moreinfo-header-note"></div>
          </div>
          <div class="erpw-so-moreinfo-header-side">
            <div class="erpw-so-moreinfo-header-status" hidden></div>
            ${settings.showToggle ? `
              <span class="erpw-so-moreinfo-header-toggle" aria-hidden="true">
                <svg viewBox="0 0 20 20">
                  <path d="M5.5 7.5L10 12l4.5-4.5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </span>
            ` : ""}
          </div>
        </div>
      `);
      $section.prepend($header);
    }

    if (settings.interactive) {
      $header.attr({
        "aria-expanded": settings.expanded ? "true" : "false",
        "aria-label": settings.ariaLabel || settings.title || "",
        role: "button",
        tabindex: "0",
      });
    } else {
      $header.removeAttr("role tabindex aria-expanded aria-label");
    }

    if (!settings.showToggle) {
      $header.find(".erpw-so-moreinfo-header-toggle").remove();
    }

    $header.find(".erpw-so-moreinfo-header-title").text(settings.title || "");
    $header.find(".erpw-so-moreinfo-header-note").text(settings.note || "");
    setSectionStatus($header, ".erpw-so-moreinfo-header-status", settings.statusText, settings.statusTone);

    return $header;
  }

  function balanceMoreInfoStack($stack) {
    if (!$stack || !$stack.length) return;

    const $sections = $stack.children('.erpw-so-moreinfo-section').filter((_, element) => $(element).is(':visible'));
    $stack.removeAttr('data-layout').attr('data-visible-count', $sections.length || 0);

    $sections.each((_, element) => {
      $(element)
        .removeClass('erpw-so-moreinfo-section-auto-compact erpw-so-moreinfo-section-layout-single erpw-so-moreinfo-section-layout-paired')
        .removeAttr('data-density');
    });

    if (!$sections.length) return;

    const metrics = $sections.toArray().map((element) => {
      const $section = $(element);
      const $body = $section.children('.section-body').first();
      const visibleControls = countVisibleControls($body.length ? $body : $section);
      const visibleChildren = ($body.length ? $body.children(':visible') : $section.children(':visible')).not('.erpw-so-moreinfo-state-panel').length;
      const metricCount = $section.find('.erpw-so-moreinfo-metric:visible').length;
      const visibleGridRows = $section.find('.grid-row:visible').length;
      const hasSummary = $section.hasClass('erpw-so-moreinfo-section-summary-mode');
      const isSingleControl = $section.hasClass('erpw-so-moreinfo-section-single-control');
      const isWide = $section.hasClass('erpw-so-moreinfo-section-wide');
      const score = visibleControls + Math.min(visibleChildren, 3) + Math.min(metricCount, 2) + Math.min(visibleGridRows, 2) + (hasSummary ? 0 : 1) + (isSingleControl ? 0 : 1);
      const density = score <= 2 ? 'sparse' : (score >= 6 ? 'dense' : 'balanced');
      return {
        $section,
        density,
        isSparse: density === 'sparse',
        isWide,
      };
    });

    const visibleCount = metrics.length;
    const hasSparseWide = metrics.some((metric) => metric.isWide && metric.isSparse);
    const layout = visibleCount === 1 ? 'single' : (visibleCount === 2 ? 'paired' : 'multi');
    $stack.attr('data-layout', layout);

    metrics.forEach((metric) => {
      metric.$section.attr('data-density', metric.density);

      if (layout === 'single') {
        metric.$section.addClass('erpw-so-moreinfo-section-layout-single');
      }

      if (layout === 'paired') {
        metric.$section.addClass('erpw-so-moreinfo-section-layout-paired');
      }

      if (
        layout === 'single'
        || (layout === 'paired' && metric.isWide && hasSparseWide)
        || (layout === 'multi' && metric.isWide && metric.isSparse)
      ) {
        metric.$section.addClass('erpw-so-moreinfo-section-auto-compact');
      }
    });
  }

  childPageRuntime.sections = Object.assign({}, childPageRuntime.sections || {}, {
    applyFieldPlaceholder,
    arrangeAddressFieldGrid,
    applyMoreInfoMetrics,
    balanceMoreInfoStack,
    countVisibleControls,
    coreAddressFieldOrder,
    coreAddressLabels,
    coreAddressPlaceholders,
    ensureAddressSectionHeader,
    ensureDetailWorkspace,
    ensureMoreInfoMetrics,
    formatAddressRecordLabel,
    normalizeAddressFieldDisplays,
    relocateFieldIntoSectionBody,
    restoreRelocatedFieldPlacements,
    ensureMoreInfoSectionHeader,
    ensureSectionStack,
    ensureSectionStatePanel,
    hasVisibleControls,
  });
})();
