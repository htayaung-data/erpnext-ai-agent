(function () {
  const root = window;
  const childPageRuntime = root.erpWorkspaceUiChildPage = root.erpWorkspaceUiChildPage || {};
  const childPageHelpers = childPageRuntime.helpers || {};

  const escapeHtml = childPageHelpers.escapeHtml || function (value) {
    return frappe.utils.escape_html(value == null ? "" : String(value));
  };

  function renderInlineSummary($section, options) {
    if (!$section || !$section.length) return $();

    const settings = Object.assign({
      chips: [],
      insertMode: "after-grid",
      metrics: [],
      note: "",
      removeSelector: ".erpw-so-inline-summary",
      summaryClass: "erpw-so-inline-summary",
      title: "",
    }, options || {});

    if (settings.removeSelector) {
      $section.find(settings.removeSelector).remove();
    }

    const metrics = Array.isArray(settings.metrics) ? settings.metrics : [];
    const chips = Array.isArray(settings.chips) ? settings.chips.filter((chip) => chip && chip.label) : [];
    const summaryClasses = String(settings.summaryClass || "erpw-so-inline-summary").trim();

    const $summary = $(`
      <div class="${summaryClasses}">
        <div class="erpw-so-inline-summary-head">
          <div class="erpw-so-inline-summary-title">${escapeHtml(settings.title || "")}</div>
          ${settings.note ? `
            <div class="erpw-child-subtitle erpw-child-inline-summary-note">${escapeHtml(settings.note)}</div>
          ` : ""}
          ${chips.length ? `
            <div class="erpw-child-chip-row">
              ${chips.map((chip) => `
                <span class="erpw-child-chip ${escapeHtml(chip.tone || "pending")}">${escapeHtml(chip.label)}</span>
              `).join("")}
            </div>
          ` : ""}
        </div>
        <div class="erpw-so-inline-summary-grid">
          ${metrics.map((metric) => `
            <div class="erpw-so-inline-metric ${escapeHtml(metric.className || "")}">
              <div class="erpw-so-inline-metric-label">${escapeHtml(metric.label || "")}</div>
              <div class="erpw-so-inline-metric-value">${escapeHtml(metric.value || "--")}</div>
            </div>
          `).join("")}
        </div>
      </div>
    `);

    if (settings.insertMode === "prepend-body" || settings.insertMode === "append-body") {
      const $body = $section.children(".section-body").first();
      if ($body.length) {
        if (settings.insertMode === "prepend-body") {
          $body.prepend($summary);
        } else {
          $body.append($summary);
        }
      } else {
        if (settings.insertMode === "prepend-body") {
          $section.prepend($summary);
        } else {
          $section.append($summary);
        }
      }
      return $summary;
    }

    const $gridField = $section.find(".grid-field").first();
    if ($gridField.length) {
      $gridField.after($summary);
    } else if (settings.insertMode === "prepend-section") {
      $section.prepend($summary);
    } else if (settings.insertMode === "append-section") {
      $section.append($summary);
    } else {
      $section.append($summary);
    }

    return $summary;
  }

  childPageRuntime.summaries = Object.assign({}, childPageRuntime.summaries || {}, {
    renderInlineSummary,
  });
})();
