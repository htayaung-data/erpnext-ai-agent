(function () {
  const root = window;
  const childPageRuntime = root.erpWorkspaceUiChildPage = root.erpWorkspaceUiChildPage || {};
  const childPageHelpers = childPageRuntime.helpers || {};

  const escapeHtml = childPageHelpers.escapeHtml || function (value) {
    return frappe.utils.escape_html(value == null ? "" : String(value));
  };

  function normalizeActions(actions) {
    if (!Array.isArray(actions)) return [];
    return actions.map((action, idx) => Object.assign({ idx }, action || {}));
  }

  function buildActionRows(actions, options) {
    const normalizedActions = normalizeActions(actions);
    const settings = Object.assign({
      sparseSecondaryThreshold: null,
    }, options || {});

    if (
      Number.isInteger(settings.sparseSecondaryThreshold)
      && normalizedActions.length
      && normalizedActions.length <= settings.sparseSecondaryThreshold
    ) {
      return [{
        className: "erpw-child-action-row erpw-child-action-row-secondary",
        actions: normalizedActions,
      }];
    }

    const primaryActions = normalizedActions.filter((action) => action.variant === "primary");
    const secondaryActions = normalizedActions.filter((action) => action.variant !== "primary");
    const rows = [];

    if (primaryActions.length) {
      rows.push({
        className: "erpw-child-action-row erpw-child-action-row-primary",
        actions: primaryActions,
      });
    }

    if (secondaryActions.length) {
      rows.push({
        className: "erpw-child-action-row erpw-child-action-row-secondary",
        actions: secondaryActions,
      });
    }

    return rows;
  }

  function renderActionButton(action, actionIconMarkup) {
    return `
      <button type="button" class="erpw-child-action ${escapeHtml(action.variant || "secondary")}" data-action-index="${action.idx}">
        <span class="erpw-child-action-accent" aria-hidden="true">${actionIconMarkup(action.icon)}</span>
        <span class="erpw-child-action-copy">
          <span class="erpw-child-action-title">${escapeHtml(action.title)}</span>
        </span>
      </button>
    `;
  }

  function renderSummaryCard(summary) {
    const facts = Array.isArray(summary.facts) ? summary.facts : [];
    const chips = Array.isArray(summary.chips) ? summary.chips : [];

    return `
      <section class="erpw-child-card erpw-child-summary">
        <div class="erpw-child-summary-copy">
          <div class="erpw-child-summary-top">
            <div class="erpw-child-summary-main">
              <div class="erpw-child-kicker">${escapeHtml(summary.kicker || "")}</div>
              <h2 class="erpw-child-title">${escapeHtml(summary.title || "")}</h2>
              <div class="erpw-child-subtitle">${escapeHtml(summary.subtitle || "")}</div>
            </div>
            <div class="erpw-child-chip-row erpw-child-chip-row-header">
              ${chips.map((chip) => `
                <span class="erpw-child-chip ${escapeHtml(chip.tone || "pending")}">${escapeHtml(chip.label)}</span>
              `).join("")}
            </div>
          </div>
        </div>
        <div class="erpw-child-summary-facts">
          ${facts.map((fact) => `
            <div class="erpw-child-fact ${escapeHtml(fact.className || "")}">
              <div class="erpw-child-fact-label">${escapeHtml(fact.label || "")}</div>
              <div class="erpw-child-fact-value">${escapeHtml(fact.value || "--")}</div>
              ${fact.meta ? `<div class="erpw-child-fact-meta">${escapeHtml(fact.meta)}</div>` : ""}
            </div>
          `).join("")}
        </div>
      </section>
    `;
  }

  function renderActionsBand(actionRows, actionIconMarkup) {
    return `
      <section class="erpw-child-card erpw-child-actions erpw-child-actions-band">
        <div class="erpw-child-action-stack">
          ${actionRows.map((row) => `
            <div class="${escapeHtml(row.className || "erpw-child-action-row erpw-child-action-row-secondary")}" data-count="${Array.isArray(row.actions) ? row.actions.length : 0}">
              ${(Array.isArray(row.actions) ? row.actions : []).map((action) => renderActionButton(action, actionIconMarkup)).join("")}
            </div>
          `).join("")}
        </div>
      </section>
    `;
  }

  function renderGuidanceSection(guidance) {
    const cards = Array.isArray(guidance.cards) ? guidance.cards : [];
    if (!cards.length) return "";

    return `
      <section class="erpw-child-card erpw-child-context">
        <div class="erpw-child-section-heading erpw-child-section-heading-compact">
          <div class="erpw-child-section-title">${escapeHtml(guidance.title || "What To Do Now")}</div>
        </div>
        <div class="erpw-child-guidance-grid">
          ${cards.map((card) => `
            <article class="erpw-child-guidance-card ${escapeHtml(card.className || "erpw-child-guidance-card-secondary")}">
              <div class="erpw-child-guidance-head">
                <span class="erpw-child-guidance-icon" aria-hidden="true">${card.iconMarkup || ""}</span>
                <div class="erpw-child-guidance-copy">
                  <div class="erpw-child-guidance-title">${escapeHtml(card.title || "")}</div>
                  <div class="erpw-child-guidance-chip ${escapeHtml(card.chipClass || "")}">${escapeHtml(card.chipLabel || "")}</div>
                </div>
              </div>
              <div class="erpw-child-guidance-text">${escapeHtml(card.text || "")}</div>
            </article>
          `).join("")}
        </div>
      </section>
    `;
  }

  function renderShellContent($shell, options) {
    if (!$shell || !$shell.length) return [];

    const settings = Object.assign({
      actionLayout: {},
      extraSectionsHtml: "",
      guidance: {},
      summary: {},
    }, options || {});
    const actionIconMarkup = typeof settings.actionIconMarkup === "function"
      ? settings.actionIconMarkup
      : function () { return ""; };
    const actions = normalizeActions(settings.actions);
    const actionRows = Array.isArray(settings.actionRows)
      ? settings.actionRows
      : buildActionRows(actions, settings.actionLayout);

    $shell.html(`
      ${renderSummaryCard(settings.summary)}
      ${renderActionsBand(actionRows, actionIconMarkup)}
      ${renderGuidanceSection(settings.guidance)}
      ${settings.extraSectionsHtml || ""}
    `);

    actions.forEach((action) => {
      if (typeof action.handler !== "function") return;
      $shell.find(`[data-action-index="${action.idx}"]`).on("click", action.handler);
    });

    return actions;
  }

  childPageRuntime.shellContent = Object.assign({}, childPageRuntime.shellContent || {}, {
    buildActionRows,
    renderShellContent,
  });
})();
