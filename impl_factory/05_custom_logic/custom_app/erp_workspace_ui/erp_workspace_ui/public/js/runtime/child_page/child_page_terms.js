(function () {
  const root = window;
  const childPageRuntime = root.erpWorkspaceUiChildPage = root.erpWorkspaceUiChildPage || {};
  const childPageHelpers = childPageRuntime.helpers || {};
  const childPageSections = childPageRuntime.sections || {};

  const escapeHtml = childPageHelpers.escapeHtml || function (value) {
    return frappe.utils.escape_html(value == null ? "" : String(value));
  };

  function ensureCriticalStyles() {
    const styleId = "erpw-child-terms-critical-styles";
    if (document.getElementById(styleId)) return;

    const style = document.createElement("style");
    style.id = styleId;
    style.textContent = `
      .erpw-so-terms-metrics {
        display:grid;
        grid-template-columns:repeat(4, minmax(150px, 1fr));
        gap:0.72rem;
        width:100%;
        margin:0.88rem 0 1rem;
      }
      .erpw-so-terms-metric {
        min-width:0;
        width:100%;
      }
      @media (max-width: 1100px) {
        .erpw-so-terms-metrics {
          grid-template-columns:repeat(2, minmax(150px, 1fr));
        }
      }
      @media (max-width: 640px) {
        .erpw-so-terms-metrics {
          grid-template-columns:minmax(0, 1fr);
        }
      }
    `;
    document.head.appendChild(style);
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
      output: `
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M7 7.5h10M7 11h10M8 16.5h8M6 4.5h12a1.5 1.5 0 0 1 1.5 1.5v11A1.5 1.5 0 0 1 18 18.5H6A1.5 1.5 0 0 1 4.5 17V6A1.5 1.5 0 0 1 6 4.5z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      `,
    };

    return icons[kind] || icons.policy;
  }

  function ensureTermsStack($tab, className) {
    const stackClass = String(className || "erpw-so-terms-stack").trim() || "erpw-so-terms-stack";
    if (typeof childPageSections.ensureSectionStack === "function") {
      return childPageSections.ensureSectionStack($tab, stackClass);
    }

    if (!$tab || !$tab.length) return $();

    let $stack = $tab.children(`.${stackClass}`).first();
    if ($stack.length) return $stack;

    $stack = $(`<div class="${stackClass}"></div>`);
    $tab.prepend($stack);
    return $stack;
  }

  function ensureTermsSectionHeader($section, options) {
    if (!$section || !$section.length) return $();
    ensureCriticalStyles();

    const settings = Object.assign({
      defaultHeadClass: "erpw-so-terms-default-head",
      headerClass: "erpw-so-terms-header",
      icon: "policy",
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

    $header.find(".erpw-so-terms-header-icon").html(settings.iconMarkup || termsSectionIconMarkup(settings.icon));
    $header.find(".erpw-so-terms-header-title").text(settings.title || "");
    $header.find(".erpw-so-terms-header-note").text(settings.note || "");

    const $status = $header.find(".erpw-so-terms-header-status").first();
    const statusText = String(settings.statusText || "").trim();
    const statusTone = String(settings.statusTone || "neutral").trim();

    if (statusText) {
      $status.text(statusText).attr("data-tone", statusTone).prop("hidden", false);
    } else {
      $status.text("").removeAttr("data-tone").prop("hidden", true);
    }

    return $header;
  }

  function ensureTermsStatePanel($section) {
    if (typeof childPageSections.ensureSectionStatePanel === "function") {
      return childPageSections.ensureSectionStatePanel($section, "erpw-so-terms");
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
    ensureCriticalStyles();
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

  function balanceTermsStack($stack) {
    if (!$stack || !$stack.length) return;

    const countVisibleControls = typeof childPageSections.countVisibleControls === "function"
      ? childPageSections.countVisibleControls
      : function ($root) {
        if (!$root || !$root.length) return 0;
        return $root.find(".frappe-control").toArray().filter((element) => {
          const $control = $(element);
          if ($control.hasClass("hide-control") || $control.hasClass("hidden")) return false;
          if ($control.css("display") === "none") return false;
          const inlineStyle = String($control.attr("style") || "").toLowerCase();
          return !inlineStyle.includes("display: none");
        }).length;
      };

    const $sections = $stack.children(".erpw-so-terms-section").filter((_, element) => $(element).is(":visible"));
    $stack.removeAttr("data-layout").attr("data-visible-count", $sections.length || 0);

    $sections.each((_, element) => {
      $(element).removeAttr("data-density");
    });

    if (!$sections.length) return;

    const metrics = $sections.toArray().map((element) => {
      const $section = $(element);
      const $body = $section.children(".section-body").first();
      const visibleControls = countVisibleControls($body.length ? $body : $section);
      const metricCount = $section.find(".erpw-so-terms-metric:visible").length;
      const hasSummary = $section.hasClass("erpw-so-terms-section-summary-mode");
      const isQuiet = $section.hasClass("erpw-so-terms-section-quiet");
      const score = visibleControls + Math.min(metricCount, 2) + (hasSummary ? 0 : 1) + (isQuiet ? 0 : 1);
      const density = score <= 2 ? "sparse" : (score >= 5 ? "dense" : "balanced");
      return { $section, density };
    });

    const layout = metrics.length === 1 ? "single" : (metrics.length === 2 ? "paired" : "multi");
    $stack.attr("data-layout", layout);
    metrics.forEach((metric) => {
      metric.$section.attr("data-density", metric.density);
    });
  }

  function applyTermsSectionState($section, presentation, options) {
    if (!$section || !$section.length) return;

    const settings = Object.assign({
      onFocusField: null,
      onRevealFields: null,
      revealDataKey: "erpwTermsRevealRaw",
    }, options || {});
    const state = presentation && presentation.state;
    const revealRaw = Boolean($section.data(settings.revealDataKey));
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
            $section.data(settings.revealDataKey, 1);
            if (typeof settings.onRevealFields === "function") {
              settings.onRevealFields($section, state, presentation);
            }
            applyTermsSectionState($section, presentation, settings);
          }

          if (state.focusField && typeof settings.onFocusField === "function") {
            settings.onFocusField(state.focusField, $section, state, presentation);
          }
        });
    } else {
      $action.text("").prop("hidden", true).off(".erpwTermsState");
    }

    $panel.prop("hidden", false);
  }

  function applyTermsMetrics($section, presentation) {
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

  function resetTermsTab($tab, options) {
    if (!$tab || !$tab.length) return;

    const settings = Object.assign({
      extraClasses: [],
      stackClass: "erpw-so-terms-stack",
    }, options || {});
    const extraClasses = Array.isArray(settings.extraClasses) ? settings.extraClasses : [];

    $tab.children(`.${settings.stackClass}`).remove();
    $tab.find(".erpw-so-terms-state-panel").remove();
    $tab.find(".erpw-so-terms-header").remove();
    $tab.find(".erpw-so-terms-metrics").remove();
    $tab.find(".erpw-so-terms-assist-note").remove();
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
        "erpw-so-terms-section-output",
        "erpw-so-terms-section-readonly",
        "erpw-so-terms-hidden-source",
        "erpw-so-terms-section-summary-mode",
        ...extraClasses,
      ].join(" "));
  }

  childPageRuntime.terms = Object.assign({}, childPageRuntime.terms || {}, {
    applyTermsAssistNote,
    applyTermsMetrics,
    applyTermsSectionState,
    balanceTermsStack,
    ensureTermsAssistNote,
    ensureTermsMetrics,
    ensureTermsSectionHeader,
    ensureTermsStack,
    ensureTermsStatePanel,
    resetTermsTab,
    termsSectionIconMarkup,
  });
})();
