(function () {
  const root = window;
  const listPageRuntime = root.erpWorkspaceUiListPage = root.erpWorkspaceUiListPage || {};
  const STYLE_ID = 'erpw-list-shell-runtime-overrides';

  function ensureStyles() {
    if (document.getElementById(STYLE_ID)) return;
    const style = document.createElement('style');
    style.id = STYLE_ID;
    style.textContent = `
      .erpw-list-table {
        width: 100%;
        table-layout: fixed;
      }
      .erpw-list-table th {
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.08em;
      }
      .erpw-list-table td {
        font-size: 13.5px;
        font-weight: 400;
        color: #0f172a;
        vertical-align: top;
      }
      .erpw-list-cell-primary,
      .erpw-list-cell-link,
      .erpw-list-inline-open,
      .erpw-list-inline-open-label,
      .erpw-list-inline-open-icon,
      .erpw-list-inline-open *,
      .erpw-list-cell-link * {
        text-decoration: none !important;
      }
      .erpw-list-cell-primary {
        font-weight: 500;
        line-height: 1.45;
        color: #334155;
      }
      .erpw-list-cell-link {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 0;
        border: none;
        background: transparent;
        color: #334155;
        font-size: 13.5px;
        font-weight: 500;
        line-height: 1.45;
        text-align: left;
      }
      .erpw-list-cell-link:hover,
      .erpw-list-cell-link:focus-visible {
        color: #0f172a;
        text-decoration: none;
      }
      .erpw-list-inline-open {
        display: inline-grid;
        grid-template-columns: minmax(0, 1fr) auto;
        align-items: center;
        gap: 10px;
        width: 100%;
        padding: 0;
        border: none;
        background: transparent;
        color: #1e293b;
        text-align: left;
      }
      .erpw-list-inline-open-label {
        font-size: 14px;
        font-weight: 600;
        line-height: 1.4;
        color: inherit;
      }
      .erpw-list-inline-open-icon {
        font-size: 14px;
        font-weight: 700;
        color: #94a3b8;
        transition: transform 140ms ease, color 140ms ease;
      }
      .erpw-list-inline-open:hover,
      .erpw-list-inline-open:focus-visible {
        color: #0f172a;
        text-decoration: none;
      }
      .erpw-list-inline-open:hover .erpw-list-inline-open-label,
      .erpw-list-inline-open:focus-visible .erpw-list-inline-open-label {
        text-decoration: none !important;
      }
      .erpw-list-inline-open:hover .erpw-list-inline-open-icon,
      .erpw-list-inline-open:focus-visible .erpw-list-inline-open-icon {
        color: #64748b;
        transform: translateX(2px) scale(1.08);
      }
      .erpw-list-cell-meta {
        margin-top: 3px;
        font-size: 12px;
        font-weight: 400;
        line-height: 1.45;
        color: #64748b;
      }
      .erpw-list-shell.is-data-refreshing .erpw-list-metrics,
      .erpw-list-shell.is-data-refreshing .erpw-list-results {
        opacity: 0.58;
        pointer-events: none;
        transition: opacity 120ms ease;
      }
	      .erpw-list-controls-strip {
	        --erpw-list-control-height: 40px;
	        --erpw-list-control-label-offset: 23px;
	        --erpw-list-action-rail-height: calc(var(--erpw-list-control-height) + var(--erpw-list-control-label-offset));
	        display: grid;
	        width: min(1120px, 100%);
	        max-width: 100%;
	        gap: 10px;
	        margin: 2px 0 18px;
	        padding: 14px;
	        border: 1px solid rgba(226, 232, 240, 0.82);
	        border-radius: 20px;
	        background: #ffffff;
	        box-shadow:
	          inset 0 1px 0 rgba(255, 255, 255, 0.96),
	          0 10px 24px rgba(15, 23, 42, 0.035);
	      }
	      .erpw-list-controls-strip.is-utility-only {
	        display: flex;
	        justify-content: flex-end;
	        width: 100%;
	        padding: 0;
	        border: 0;
	        border-radius: 0;
	        background: transparent;
	        box-shadow: none;
	      }
	      .erpw-list-controls-strip.is-form-panel {
	        width: min(920px, 100%);
	        padding: 14px;
        border-radius: 22px;
        background: #ffffff;
        justify-self: center;
      }
      .erpw-list-summary-card:has(+ .erpw-list-controls-strip.is-form-panel) {
        width: min(920px, 100%);
        justify-self: center;
      }
      .erpw-list-summary-card:has(+ .erpw-list-controls-strip.is-form-panel) .erpw-list-summary-head {
        align-items: center;
        min-height: 28px;
      }
      .erpw-list-summary-card:has(+ .erpw-list-controls-strip.is-form-panel) .erpw-list-title {
        line-height: 1.25;
	      }
	      .erpw-list-filter-row {
	        display: grid;
	        gap: 10px;
	      }
	      .erpw-list-command-panel {
	        display: block;
	        max-width: 100%;
	        width: 100%;
	      }
	      .erpw-list-command-grid {
	        display: grid;
	        gap: 10px;
	        align-items: stretch;
	        min-width: 0;
	        max-width: 100%;
	      }
	      .erpw-list-command-grid.field-count-1 {
	        grid-template-columns: minmax(220px, 280px) max-content;
	      }
	      .erpw-list-command-grid.field-count-2 {
	        grid-template-columns: repeat(2, minmax(220px, 260px)) max-content;
	      }
	      .erpw-list-command-grid.field-count-3 {
	        grid-template-columns: repeat(3, minmax(210px, 230px)) max-content;
	      }
	      .erpw-list-command-grid.field-count-4,
	      .erpw-list-command-grid.field-count-5 {
	        grid-template-columns: minmax(210px, 250px) minmax(210px, 250px) minmax(250px, max-content);
	      }
	      .erpw-list-command-grid.field-count-5.has-date-window {
	        grid-template-columns:
	          minmax(220px, 1.1fr)
	          minmax(220px, 1.1fr)
	          minmax(190px, 0.95fr)
	          minmax(190px, 0.95fr);
	      }
	      .erpw-list-command-grid.field-count-5.has-date-window .erpw-list-control-field[data-erpw-list-field-shell-key="keyword"] {
	        grid-column: 1 / span 2;
	      }
	      .erpw-list-command-grid.field-count-5.has-date-window .erpw-list-command-action-cell {
	        grid-column: 3 / span 2;
	        justify-content: flex-end;
	      }
	      .erpw-list-command-action-cell {
	        display: inline-flex;
	        align-items: flex-start;
	        justify-content: flex-end;
	        align-self: stretch;
	        min-height: var(--erpw-list-action-rail-height);
	        padding-top: var(--erpw-list-control-label-offset);
	        box-sizing: border-box;
	      }
	      .erpw-list-command-grid.field-count-4 .erpw-list-command-action-cell {
	        grid-column: 3;
	      }
      .erpw-list-unified-command {
        display: grid;
        gap: 8px;
      }
      .erpw-list-unified-command-label {
        font-size: 11px;
        font-weight: 750;
        letter-spacing: 0.08em;
        color: #64748b;
        text-transform: uppercase;
      }
      .erpw-list-unified-command-row {
        display: inline-flex;
        flex-wrap: wrap;
        gap: 8px;
        align-items: center;
      }
      .erpw-list-unified-command-control {
        width: min(280px, calc(100vw - 64px));
      }
      .erpw-list-navigation-actions {
        display: inline-flex;
        flex-wrap: wrap;
        gap: 10px;
        justify-content: flex-end;
        align-items: center;
      }
	      .erpw-list-control-form {
	        display: grid;
	        flex: 0 1 auto;
	        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
	        gap: 10px;
	        align-items: stretch;
	        width: 100%;
	        max-width: 100%;
	      }
	      .erpw-list-control-form.is-single-field {
	        grid-template-columns: minmax(210px, 280px);
      }
      .erpw-list-control-form.is-two-fields {
        grid-template-columns: repeat(2, minmax(210px, 280px));
      }
      .erpw-list-control-form.is-form-panel {
        width: 100%;
        grid-template-columns: repeat(2, minmax(240px, 1fr));
        gap: 14px;
      }
      .erpw-list-form-note {
        max-width: 760px;
        color: #475569;
        font-size: 12.5px;
        line-height: 1.55;
        margin-top: -2px;
      }
      .erpw-list-control-field {
        display: flex;
        flex-direction: column;
        gap: 7px;
      }
	      .erpw-list-control-field.is-date {
	        position: relative;
	      }
	      .erpw-list-action-field {
	        align-self: stretch;
	        justify-content: flex-start;
	        min-width: max-content;
	        min-height: var(--erpw-list-action-rail-height);
	        padding-top: var(--erpw-list-control-label-offset);
	        box-sizing: border-box;
	      }
	      .erpw-list-action-spacer {
	        display: none;
	      }
	      .erpw-list-control-label {
	        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.08em;
        color: #64748b;
        text-transform: uppercase;
      }
      .erpw-list-control-input,
      .erpw-list-control-select {
        width: 100%;
        min-height: 40px;
        border: 1px solid rgba(203, 213, 225, 0.88);
        border-radius: 13px;
        background: #fff;
        color: #0f172a;
        padding: 0 14px;
        font-size: 14px;
        font-weight: 500;
      }
      .erpw-list-control-input:focus,
      .erpw-list-control-select:focus {
        outline: none;
        border-color: #94a3b8;
        box-shadow: 0 0 0 3px rgba(148, 163, 184, 0.15);
      }
      .erpw-list-control-input.erpw-list-control-date {
        padding-right: 42px;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2364758b' stroke-width='1.9' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='3' y='4' width='18' height='17' rx='3'/%3E%3Cpath d='M8 2v4M16 2v4M3 9h18'/%3E%3C/svg%3E");
        background-repeat: no-repeat;
        background-position: right 13px center;
        background-size: 16px 16px;
        cursor: pointer;
      }
	      .erpw-list-toolbar-actions {
	        display: inline-flex;
	        flex-wrap: wrap;
	        gap: 6px;
	        justify-content: flex-start;
	        align-items: center;
	        flex: 0 0 auto;
	        box-sizing: border-box;
	        min-height: var(--erpw-list-control-height);
        margin-top: 0;
        padding: 2px;
        border: 1px solid rgba(226, 232, 240, 0.76);
        border-radius: 15px;
	        background: rgba(255, 255, 255, 0.88);
	        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.96);
	      }
	      .erpw-list-controls-strip.is-utility-only .erpw-list-toolbar-actions {
	        border-color: transparent;
	        background: transparent;
	        box-shadow: none;
	        padding: 0;
	      }
	      .erpw-list-controls-strip.is-utility-only .erpw-list-action-button {
	        border-color: rgba(226, 232, 240, 0.72);
	        background: #ffffff;
	        box-shadow: 0 6px 16px rgba(15, 23, 42, 0.035);
	      }
	      .erpw-list-toolbar-actions .erpw-list-action-button {
	        min-height: 34px;
	        padding-inline: 0.72rem;
	        border-color: transparent;
	        border-radius: 11px;
	      }
	      .erpw-list-toolbar-actions .erpw-list-action-button.is-refresh:not(.primary) {
	        color: #334155;
	        background: transparent;
	      }
	      .erpw-list-toolbar-actions .erpw-list-action-button.create:not(.primary) {
	        color: #0f3f46;
	        background: rgba(240, 253, 250, 0.56);
	      }
      .erpw-list-form-action-row {
        display: flex;
        justify-content: flex-end;
        align-items: center;
        margin-top: 0;
      }
      .erpw-list-form-action-row .erpw-list-toolbar-actions {
        margin-left: auto;
      }
	      .erpw-list-action-button.navigation {
	        display: inline-flex;
	        align-items: center;
	        justify-content: center;
	        min-height: 34px;
	        gap: 7px;
	        padding: 0.34rem 0.68rem;
	        border-color: rgba(226, 232, 240, 0.62);
	        border-radius: 999px;
	        background: #ffffff;
	        color: #475569;
	        font-size: 0.76rem;
	        box-shadow:
	          0 1px 1px rgba(15, 23, 42, 0.02),
	          0 8px 18px rgba(15, 23, 42, 0.035);
	      }
	      .erpw-list-action-button.navigation:hover,
	      .erpw-list-action-button.navigation:focus-visible {
	        border-color: rgba(203, 213, 225, 0.7);
	        background: #ffffff;
	        color: #0f172a;
	        box-shadow:
	          0 1px 1px rgba(15, 23, 42, 0.025),
	          0 10px 22px rgba(15, 23, 42, 0.045);
	      }
      .erpw-list-summary-card .erpw-list-navigation-actions {
        margin-left: auto;
      }
      .erpw-list-action-button-navigation-icon {
        color: #64748b;
        font-size: 0.82rem;
        line-height: 1;
        transform: translateY(-0.5px);
      }
      .erpw-list-metric {
        position: relative;
      }
      .erpw-list-metric.attention {
        border-color: #dbe4ee;
        background: #ffffff;
        box-shadow:
          inset 0 3px 0 #f0b44c,
          var(--erpw-shadow-card, 0 1px 0 rgba(255, 255, 255, 0.98) inset, 0 10px 24px rgba(15, 23, 42, 0.04));
      }
      .erpw-list-metric.warning {
        border-color: #dbe4ee;
        background: #ffffff;
        box-shadow:
          inset 0 3px 0 #94a3b8,
          var(--erpw-shadow-card, 0 1px 0 rgba(255, 255, 255, 0.98) inset, 0 10px 24px rgba(15, 23, 42, 0.04));
      }
      .erpw-list-cell-meta-line {
        display: block;
        margin-top: 2px;
      }
      @media (max-width: 1180px) {
        .erpw-list-control-form {
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }
      }
      @media (max-width: 980px) {
        .erpw-list-command-panel {
          width: 100%;
        }
        .erpw-list-command-grid.field-count-5.has-date-window {
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }
        .erpw-list-command-grid.field-count-5.has-date-window .erpw-list-control-field[data-erpw-list-field-shell-key="keyword"],
        .erpw-list-command-grid.field-count-5.has-date-window .erpw-list-command-action-cell {
          grid-column: 1 / -1;
        }
      }
	      @media (max-width: 760px) {
	        .erpw-list-controls-strip {
	          width: 100%;
	        }
	        .erpw-list-unified-command-row {
	          display: grid;
	          grid-template-columns: minmax(0, 1fr);
	        }
	        .erpw-list-command-panel {
	          width: 100%;
	        }
	        .erpw-list-command-grid,
	        .erpw-list-command-grid.field-count-1,
	        .erpw-list-command-grid.field-count-2,
	        .erpw-list-command-grid.field-count-3,
	        .erpw-list-command-grid.field-count-4,
	        .erpw-list-command-grid.field-count-5 {
	          grid-template-columns: minmax(0, 1fr);
	        }
	        .erpw-list-command-grid.field-count-5.has-date-window .erpw-list-control-field[data-erpw-list-field-shell-key="keyword"],
	        .erpw-list-command-grid.field-count-5.has-date-window .erpw-list-command-action-cell {
	          grid-column: auto;
	        }
	        .erpw-list-command-grid.field-count-4 .erpw-list-command-action-cell {
	          grid-column: auto;
	        }
	        .erpw-list-command-action-cell,
	        .erpw-list-command-action-cell .erpw-list-toolbar-actions {
	          width: 100%;
	        }
	        .erpw-list-command-action-cell,
	        .erpw-list-action-field {
	          min-height: var(--erpw-list-control-height);
	          padding-top: 0;
	        }
        .erpw-list-unified-command-control {
          width: 100%;
        }
        .erpw-list-filter-row {
          display: grid;
          grid-template-columns: minmax(0, 1fr);
        }
        .erpw-list-control-form {
          grid-template-columns: minmax(0, 1fr);
        }
        .erpw-list-control-form.is-form-panel {
          grid-template-columns: minmax(0, 1fr);
        }
        .erpw-list-form-action-row {
          justify-content: flex-start;
        }
        .erpw-list-toolbar-actions,
        .erpw-list-navigation-actions {
          justify-content: flex-start;
        }
      }
    `;
    document.head.appendChild(style);
  }

  function escapeHtml(value) {
    return frappe.utils.escape_html(value == null ? "" : String(value));
  }

  function normalizeItems(items) {
    return Array.isArray(items) ? items.filter(Boolean) : [];
  }

  function joinClassNames() {
    return Array.from(arguments)
      .flatMap((value) => Array.isArray(value) ? value : [value])
      .filter(Boolean)
      .join(" ");
  }

  function renderBadge(item, extraClass) {
    if (!item) return "";
    const label = typeof item === "string" ? item : item.label;
    if (!label) return "";
    const tone = typeof item === "object" && item.tone ? item.tone : "neutral";
    return '<span class="' + joinClassNames('erpw-list-pill', tone, extraClass) + '">' + escapeHtml(label) + '</span>';
  }

  function renderSummary(summary, controls) {
    if (!summary || !summary.title) return "";
    const chips = normalizeItems(summary.chips);
    const navigationActions = normalizeItems(controls && controls.actions)
      .filter((action) => action && action.key !== 'open_native')
      .filter((action) => action.category === 'navigation' || /^back_/.test(String(action.key || '')));

    return [
      '<section class="erpw-child-card erpw-list-summary-card">',
        '<div class="erpw-list-summary-head">',
          '<div class="erpw-list-summary-copy">',
            summary.title ? '<h2 class="erpw-list-title">' + escapeHtml(summary.title) + '</h2>' : '',
            summary.subtitle ? '<div class="erpw-list-subtitle">' + escapeHtml(summary.subtitle) + '</div>' : '',
          '</div>',
          chips.length ? '<div class="erpw-list-chip-row">' + chips.map((chip) => renderBadge(chip)).join('') + '</div>' : '',
          navigationActions.length ? '<div class="erpw-list-navigation-actions">' + navigationActions.map((action) => renderToolbarAction(action, 'navigation')).join('') + '</div>' : '',
        '</div>',
      '</section>'
    ].join('');
  }

	  function renderToolbarAction(action, extraClass) {
	    if (!action || !action.key || !action.label) return "";
	    const isNavigation = String(extraClass || '').split(/\s+/).includes('navigation');
	    const isBackNavigation = isNavigation && (
	      /^back_/.test(String(action.key || ''))
	      || /^cancel_/.test(String(action.key || ''))
	      || /^back to\b/i.test(String(action.label || ''))
	    );
	    const kindClass = action.kind === 'primary'
      ? 'primary'
      : action.kind === 'create'
        ? 'create'
        : '';
    const behaviorClass = action.key === 'refresh' ? 'is-refresh' : '';
    const buttonClass = joinClassNames(
      'erpw-list-action-button',
      kindClass,
      behaviorClass,
      extraClass || ''
    );
	    const iconMarkup = isBackNavigation
	      ? '<span class="erpw-list-action-button-navigation-icon" aria-hidden="true">&larr;</span>'
	      : '';
    return '<button type="button" class="' + buttonClass + '" data-erpw-list-action-key="' + escapeHtml(action.key) + '" data-erpw-list-action-scope="toolbar">' + iconMarkup + '<span>' + escapeHtml(action.label) + '</span></button>';
  }

  function sortOperatingActions(actions) {
    const order = {
      save_customer_profile: 5,
      apply_filters: 10,
      reset_filters: 20,
      refresh: 30,
      create_customer: 40,
      new_quotation: 40,
      new_sales_order: 40,
    };
    return normalizeItems(actions).slice().sort((left, right) => {
      const leftRank = Object.prototype.hasOwnProperty.call(order, left.key) ? order[left.key] : 100;
      const rightRank = Object.prototype.hasOwnProperty.call(order, right.key) ? order[right.key] : 100;
      return leftRank - rightRank;
    });
  }

  function renderControlInput(field, baseAttrs) {
    if (field.type === 'select') {
      return '<select class="erpw-list-control-select"' + baseAttrs + '>' + normalizeItems(field.options).map((option) => {
        const optionValue = option && typeof option === 'object' ? option.value : option;
        const optionLabel = option && typeof option === 'object' ? option.label : option;
        const selected = String(optionValue == null ? '' : optionValue) === String(field.value == null ? '' : field.value) ? ' selected' : '';
        return '<option value="' + escapeHtml(optionValue == null ? '' : optionValue) + '"' + selected + '>' + escapeHtml(optionLabel == null ? '' : optionLabel) + '</option>';
      }).join('') + '</select>';
    }

    return '<input type="text" class="erpw-list-control-input' + (field.type === 'date' ? ' erpw-list-control-date' : '') + '"' + baseAttrs + ' autocomplete="off"' + (field.placeholder || field.type === 'date' ? ' placeholder="' + escapeHtml(field.placeholder || 'YYYY-MM-DD') + '"' : '') + ' value="' + escapeHtml(field.value == null ? '' : field.value) + '">';
  }

  function renderControlField(field) {
    if (!field || !field.key || !field.label) return '';
    const baseAttrs =
      ' data-erpw-list-field-key="' + escapeHtml(field.key) + '"' +
      ' data-erpw-list-field-type="' + escapeHtml(field.type || 'text') + '"';

    if (field.type === 'hidden') {
      return '<input type="hidden"' + baseAttrs + ' value="' + escapeHtml(field.value == null ? '' : field.value) + '">';
    }

    return [
      '<label class="erpw-list-control-field' + (field.type === 'date' ? ' is-date' : '') + '" data-erpw-list-field-shell-key="' + escapeHtml(field.key) + '">',
        '<span class="erpw-list-control-label">' + escapeHtml(field.label) + '</span>',
        renderControlInput(field, baseAttrs),
      '</label>'
    ].join('');
  }

  function renderUnifiedCommandField(field, hiddenFieldsMarkup, operatingActions) {
    if (!field || !field.key || !field.label) return "";
    const baseAttrs =
      ' data-erpw-list-field-key="' + escapeHtml(field.key) + '"' +
      ' data-erpw-list-field-type="' + escapeHtml(field.type || 'text') + '"';

    return [
      '<div class="erpw-list-unified-command">',
        hiddenFieldsMarkup,
        '<div class="erpw-list-unified-command-label">' + escapeHtml(field.label) + '</div>',
        '<div class="erpw-list-unified-command-row">',
          '<div class="erpw-list-unified-command-control">',
            renderControlInput(field, baseAttrs),
          '</div>',
          operatingActions.length ? '<div class="erpw-list-toolbar-actions">' + operatingActions.map((action) => renderToolbarAction(action)).join('') + '</div>' : '',
        '</div>',
      '</div>',
    ].join('');
  }

	  function renderControlActionField(operatingActions) {
	    if (!operatingActions.length) return "";
	    return [
	      '<div class="erpw-list-control-field erpw-list-action-field">',
        '<span class="erpw-list-control-label erpw-list-action-spacer" aria-hidden="true">Actions</span>',
        '<div class="erpw-list-toolbar-actions">',
          operatingActions.map((action) => renderToolbarAction(action)).join(''),
        '</div>',
	      '</div>',
	    ].join('');
	  }

	  function renderCommandPanel(visibleFields, hiddenFieldsMarkup, operatingActions) {
	    const normalizedFields = normalizeItems(visibleFields);
	    const fieldCountClass = 'field-count-' + Math.min(normalizedFields.length, 5);
	    const fieldKeys = normalizedFields.map((field) => String(field && field.key || ''));
	    const hasDateWindow = fieldKeys.includes('date_start') && fieldKeys.includes('date_end');
	    return [
	      '<div class="erpw-list-command-panel">',
	        hiddenFieldsMarkup,
	        '<div class="' + joinClassNames('erpw-list-command-grid', fieldCountClass, hasDateWindow ? 'has-date-window' : '') + '">',
	          normalizedFields.map((field) => renderControlField(field)).join(''),
	          operatingActions.length ? [
	            '<div class="erpw-list-command-action-cell">',
	            '<div class="erpw-list-toolbar-actions">',
	              operatingActions.map((action) => renderToolbarAction(action)).join(''),
	            '</div>',
	            '</div>',
	          ].join('') : '',
	        '</div>',
	      '</div>',
	    ].join('');
	  }

	  function renderControls(controls) {
	    if (!controls) return "";

	    const actions = normalizeItems(controls.actions).filter((action) => action.key !== 'open_native');
	    const navigationActions = actions.filter((action) => action.category === 'navigation' || /^back_/.test(String(action.key || '')));
	    const operatingActions = sortOperatingActions(actions.filter((action) => !navigationActions.includes(action)));
	    const fields = normalizeItems(controls.fields);
	    const isFormPanel = controls.layout === 'form_panel';
	    const visibleFields = fields.filter((field) => field && field.type !== 'hidden');
	    const hiddenFields = fields.filter((field) => field && field.type === 'hidden');
	    const visibleFieldCount = visibleFields.length;
	    const hasContent = operatingActions.length || controls.searchHint || fields.length;
	    if (!hasContent) return "";

    const hiddenFieldsMarkup = hiddenFields.map((field) => renderControlField(field)).join('');
	    const unifiedCommandMarkup = visibleFieldCount === 1 && operatingActions.length
	      ? renderUnifiedCommandField(visibleFields[0], hiddenFieldsMarkup, operatingActions)
	      : '';
	    const commandPanelMarkup = !isFormPanel && visibleFieldCount > 1 && operatingActions.length
	      ? renderCommandPanel(visibleFields, hiddenFieldsMarkup, operatingActions)
	      : '';

	    const renderedVisibleFields = visibleFields.map((field) => renderControlField(field)).join('');
	    const fieldsMarkup = !commandPanelMarkup && (visibleFieldCount || (isFormPanel && hiddenFields.length))
	      ? '<div class="' + joinClassNames(
	          'erpw-list-control-form',
	          isFormPanel ? 'is-form-panel' : '',
	          visibleFieldCount === 1 ? 'is-single-field' : '',
	          visibleFieldCount === 2 ? 'is-two-fields' : ''
	        ) + '">'
	          + hiddenFieldsMarkup
	          + renderedVisibleFields
	          + (!isFormPanel && visibleFieldCount > 1 && operatingActions.length ? renderControlActionField(operatingActions) : '')
	        + '</div>'
	      : '';
	    const utilityActionsMarkup = !unifiedCommandMarkup && !commandPanelMarkup && !fieldsMarkup && operatingActions.length
	      ? hiddenFieldsMarkup + '<div class="erpw-list-toolbar-actions is-standalone">' + operatingActions.map((action) => renderToolbarAction(action)).join('') + '</div>'
	      : '';
	    const utilityOnly = !visibleFieldCount && operatingActions.length;

    if (isFormPanel) {
      return [
        '<section class="' + joinClassNames('erpw-list-controls-strip', 'is-form-panel') + '">',
          controls.searchHint ? '<div class="erpw-list-controls-inline"><div class="erpw-list-search-hint">' + escapeHtml(controls.searchHint) + '</div></div>' : '',
          fieldsMarkup ? '<div class="erpw-list-filter-row">' + fieldsMarkup + '</div>' : hiddenFieldsMarkup,
          controls.note ? '<div class="erpw-list-form-note">' + escapeHtml(controls.note) + '</div>' : '',
          operatingActions.length ? '<div class="erpw-list-form-action-row"><div class="erpw-list-toolbar-actions">' + operatingActions.map((action) => renderToolbarAction(action)).join('') + '</div></div>' : '',
        '</section>'
      ].join('');
    }

	    return [
	      '<section class="' + joinClassNames('erpw-list-controls-strip', utilityOnly ? 'is-utility-only' : '') + '">',
	        controls.searchHint ? '<div class="erpw-list-controls-inline"><div class="erpw-list-search-hint">' + escapeHtml(controls.searchHint) + '</div></div>' : '',
	        unifiedCommandMarkup || commandPanelMarkup || fieldsMarkup || utilityActionsMarkup
	          ? '<div class="erpw-list-filter-row">'
	              + (unifiedCommandMarkup || commandPanelMarkup || fieldsMarkup)
	              + utilityActionsMarkup
	            + '</div>'
	          : '',
	      '</section>'
	    ].join('');
  }

  function renderMetrics(metrics) {
    const items = normalizeItems(metrics);
    if (!items.length) return "";

    return [
      '<section class="erpw-list-metrics">',
        items.map((item) => [
          '<article class="erpw-child-card erpw-list-metric ' + escapeHtml(item.tone || 'neutral') + '">',
            '<div class="erpw-list-metric-label">' + escapeHtml(item.label || '') + '</div>',
            '<div class="erpw-list-metric-value">' + escapeHtml(item.value == null ? '--' : item.value) + '</div>',
            item.meta ? '<div class="erpw-list-metric-meta">' + escapeHtml(item.meta) + '</div>' : '',
          '</article>'
        ].join('')).join(''),
      '</section>'
    ].join('');
  }

  function normalizeCell(row, column) {
    const cells = row && row.cells && typeof row.cells === 'object' ? row.cells : {};
    const cell = cells[column.key];
    if (cell && typeof cell === 'object' && !Array.isArray(cell)) {
      return {
        value: cell.value == null ? '--' : cell.value,
        meta: cell.meta || '',
        metaLines: normalizeItems(cell.metaLines),
        tone: cell.tone || '',
        className: cell.className || '',
        actionKey: cell.actionKey || '',
      };
    }
    return {
      value: cell == null ? '--' : cell,
      meta: '',
      metaLines: [],
      tone: '',
      className: '',
      actionKey: '',
    };
  }

  function normalizeRowActions(row) {
    return normalizeItems(row && row.actions);
  }

  function renderRowAction(action, row) {
    if (!action || !action.key || !action.label) return "";
    return '<button type="button" class="erpw-list-row-action" data-erpw-list-action-key="' + escapeHtml(action.key) + '" data-erpw-list-action-scope="row" data-erpw-row-key="' + escapeHtml(row.key || '') + '">' + escapeHtml(action.label) + '</button>';
  }

  function renderCell(row, column, columnIndex, inlinePrimaryAction) {
    const cell = normalizeCell(row, column);
    const inlineAction = inlinePrimaryAction && columnIndex === 0 ? normalizeRowActions(row)[0] : null;
    const primary = inlineAction
      ? '<button type="button" class="erpw-list-inline-open" data-erpw-list-action-key="' + escapeHtml(inlineAction.key) + '" data-erpw-list-action-scope="row" data-erpw-row-key="' + escapeHtml(row.key || '') + '"><span class="erpw-list-inline-open-label">' + escapeHtml(cell.value) + '</span><span class="erpw-list-inline-open-icon" aria-hidden="true">&rarr;</span></button>'
      : cell.actionKey
        ? '<button type="button" class="erpw-list-cell-link" data-erpw-list-action-key="' + escapeHtml(cell.actionKey) + '" data-erpw-list-action-scope="row" data-erpw-row-key="' + escapeHtml(row.key || '') + '">' + escapeHtml(cell.value) + '</button>'
      : '<div class="erpw-list-cell-primary">' + escapeHtml(cell.value) + '</div>';

    return [
      '<td class="' + joinClassNames(column.align || '', cell.className, cell.tone ? 'tone-' + cell.tone : '') + '">',
        primary,
        cell.meta || (cell.metaLines && cell.metaLines.length)
          ? '<div class="erpw-list-cell-meta">'
              + (cell.meta ? '<span class="erpw-list-cell-meta-line">' + escapeHtml(cell.meta) + '</span>' : '')
              + normalizeItems(cell.metaLines).map((line) => '<span class="erpw-list-cell-meta-line">' + escapeHtml(line) + '</span>').join('')
            + '</div>'
          : '',
      '</td>'
    ].join('');
  }

  function renderResultsState(state) {
    if (!state) return '';
    return [
      '<div class="erpw-list-state ' + escapeHtml(state.kind || 'neutral') + '">',
        '<div class="erpw-list-state-title">' + escapeHtml(state.title || 'Workspace state') + '</div>',
        state.detail ? '<div class="erpw-list-state-detail">' + escapeHtml(state.detail) + '</div>' : '',
        state.action && state.action.key && state.action.label
          ? '<button type="button" class="erpw-list-action-button" data-erpw-list-action-key="' + escapeHtml(state.action.key) + '" data-erpw-list-action-scope="state">' + escapeHtml(state.action.label) + '</button>'
          : '',
      '</div>'
    ].join('');
  }

  function compactScopeItems(controls) {
    return normalizeItems(controls && controls.scopeChips)
      .map((chip) => typeof chip === 'string' ? chip : chip && chip.label)
      .filter(Boolean);
  }

  function renderResults(results, controls) {
    if (results === null || (controls && controls.layout === 'form_panel' && !results)) return "";
    const config = results || {};
    const columns = normalizeItems(config.columns);
    const rows = normalizeItems(config.rows);
    const scopeItems = compactScopeItems(controls);
    const scopeContext = scopeItems.length ? scopeItems.join(' \u00b7 ') : '';
    const showInlinePrimaryAction = Boolean(config.rowActions) && rows.length && rows.every((row) => {
      const actions = normalizeRowActions(row);
      return actions.length === 1 && actions[0].key === 'open_record';
    });
    const showResultsTitle = Boolean(config.title);
    const showResultsHeader = showResultsTitle || config.subtitle || config.meta || scopeContext;

    return [
      '<section class="erpw-child-card erpw-list-results">',
        showResultsHeader ? [
          '<div class="erpw-list-results-head">',
            '<div class="erpw-list-results-copy">',
              showResultsTitle ? '<div class="erpw-list-results-title">' + escapeHtml(config.title) + '</div>' : '',
              config.subtitle ? '<div class="erpw-list-results-note">' + escapeHtml(config.subtitle) + '</div>' : '',
              !config.subtitle && scopeContext ? '<div class="erpw-list-results-note erpw-list-results-context">' + escapeHtml(scopeContext) + '</div>' : '',
            '</div>',
            config.meta ? '<div class="erpw-list-results-meta">' + escapeHtml(config.meta) + '</div>' : '',
          '</div>'
        ].join('') : '',
        config.state && config.state.kind && config.state.kind !== 'ready'
          ? renderResultsState(config.state)
          : columns.length
              ? [
                '<div class="erpw-list-table-wrap">',
                  '<table class="erpw-list-table">',
                    columns.some((column) => column && column.width)
                      ? '<colgroup>' + columns.map((column) => '<col' + (column && column.width ? ' style="width:' + escapeHtml(column.width) + '"' : '') + '>').join('') + (config.rowActions && !showInlinePrimaryAction ? '<col style="width:120px">' : '') + '</colgroup>'
                      : '',
                    '<thead><tr>',
                      columns.map((column) => '<th class="' + escapeHtml(column.align || '') + '">' + escapeHtml(column.label || '') + '</th>').join(''),
                      config.rowActions && !showInlinePrimaryAction ? '<th class="actions">Action</th>' : '',
                    '</tr></thead>',
                    '<tbody>',
                      rows.length
                        ? rows.map((row) => [
                            '<tr data-erpw-row-key="' + escapeHtml(row.key || '') + '">',
                              columns.map((column, index) => renderCell(row, column, index, showInlinePrimaryAction)).join(''),
                              config.rowActions && !showInlinePrimaryAction
                                ? '<td class="actions"><div class="erpw-list-row-actions">' + normalizeRowActions(row).map((action) => renderRowAction(action, row)).join('') + '</div></td>'
                                : '',
                            '</tr>'
                          ].join('')).join('')
                        : '<tr><td colspan="' + escapeHtml(columns.length + (config.rowActions && !showInlinePrimaryAction ? 1 : 0)) + '"><div class="erpw-list-empty-inline">No records match the current view.</div></td></tr>',
                    '</tbody>',
                  '</table>',
                '</div>'
              ].join('')
            : renderResultsState({
                kind: 'empty',
                title: 'List is not ready yet',
                detail: 'This Sales Console view is missing its table setup. Refresh the page or return to the console.',
              }),
      '</section>'
    ].join('');
  }

  function renderWorklist(config) {
    const page = config || {};
    return [
      renderSummary(page.summary, page.controls),
      renderControls(page.controls),
      renderMetrics(page.metrics),
      renderResults(page.results, page.controls),
    ].filter(Boolean).join('');
  }

  function resolveTarget(target) {
    if (!target) return $();
    return target.jquery ? target.first() : $(target).first();
  }

  function ensureShell(target) {
    const $target = resolveTarget(target);
    if (!$target.length) return $();
    if ($target.hasClass('erpw-list-shell')) return $target;

    let $shell = $target.children('.erpw-list-shell').first();
    if (!$shell.length) {
      $shell = $('<section class="erpw-list-shell"></section>');
      $target.empty().append($shell);
    }

    return $shell;
  }

  function setDataRefreshing(target, enabled) {
    const $shell = ensureShell(target);
    if (!$shell.length) return $shell;
    $shell.toggleClass('is-data-refreshing', Boolean(enabled));
    $shell.attr('aria-busy', enabled ? 'true' : 'false');
    return $shell;
  }

  function replaceShellSection($shell, selector, markup, beforeSelector) {
    const $existing = $shell.children(selector).first();
    if (!markup) {
      $existing.remove();
      return;
    }

    const $next = $(markup);
    if ($existing.length) {
      $existing.replaceWith($next);
      return;
    }

    const $before = beforeSelector ? $shell.children(beforeSelector).first() : $();
    if ($before.length) {
      $next.insertBefore($before);
      return;
    }

    $shell.append($next);
  }

  function refreshWorklistData(target, config, options) {
    ensureStyles();
    const $shell = ensureShell(target);
    if (!$shell.length) return $();

    const page = config || {};
    const settings = options && typeof options === 'object' ? options : {};
    if (settings.refreshControls) {
      replaceShellSection($shell, '.erpw-list-controls-strip', renderControls(page.controls), '.erpw-list-metrics, .erpw-list-results');
    }
    replaceShellSection($shell, '.erpw-list-metrics', renderMetrics(page.metrics), '.erpw-list-results');
    replaceShellSection($shell, '.erpw-list-results', renderResults(page.results, page.controls));
    $shell.attr('data-erpw-list-signature', renderWorklist(page));
    setDataRefreshing($shell, false);
    bindDateFields($shell);
    bindActions($shell, config || {});
    return $shell;
  }

  function bindActions($shell, config) {
    if (!$shell || !$shell.length) return;
    const onAction = config && typeof config.onAction === 'function' ? config.onAction : null;

    $shell.off('.erpwListShell');
    if (!onAction) return;

    $shell.on('click.erpwListShell', '[data-erpw-list-action-key]', function (event) {
      event.preventDefault();
      const $button = $(this);
      onAction({
        key: $button.attr('data-erpw-list-action-key') || '',
        scope: $button.attr('data-erpw-list-action-scope') || 'toolbar',
        rowKey: $button.attr('data-erpw-row-key') || '',
        trigger: this,
      });
    });
  }

  function initDateField($input) {
    if (!$input || !$input.length) return;
    if (typeof $input.datepicker !== 'function') return;
    if ($input.data('datepicker')) return;

    let lang = 'en';
    if (frappe.boot && frappe.boot.user && frappe.boot.user.language) {
      lang = frappe.boot.user.language;
    }
    if (!($.fn.datepicker && $.fn.datepicker.language && $.fn.datepicker.language[lang])) {
      lang = 'en';
    }

    const options = {
      language: lang,
      autoClose: true,
      todayButton: true,
      dateFormat: 'yyyy-mm-dd',
      keyboardNav: false,
      firstDay: frappe.datetime && typeof frappe.datetime.get_first_day_of_the_week_index === 'function'
        ? frappe.datetime.get_first_day_of_the_week_index()
        : 0,
      onSelect: function () {
        $input.trigger('change');
      },
    };

    $input.datepicker(options);
    const picker = $input.data('datepicker');
    if (picker && picker.$datepicker) {
      picker.$datepicker.find('[data-action="today"]').click(function () {
        picker.selectDate(new Date());
        picker.hide();
      });
    }
  }

  function bindDateFields($shell) {
    if (!$shell || !$shell.length) return;
    $shell.find('[data-erpw-list-field-type="date"]').each(function () {
      initDateField($(this));
    });
  }

  function mountWorklist(target, config) {
    ensureStyles();
    const $shell = ensureShell(target);
    if (!$shell.length) return $();

    const markup = renderWorklist(config || {});
    const signature = markup;
    if ($shell.attr('data-erpw-list-signature') !== signature) {
      $shell.attr('data-erpw-list-signature', signature);
      $shell.html(markup);
    }

    bindDateFields($shell);
    bindActions($shell, config || {});
    return $shell;
  }

  listPageRuntime.shell = Object.assign({}, listPageRuntime.shell || {}, {
    ensureShell,
    mountWorklist,
    refreshWorklistData,
    renderWorklist,
    setDataRefreshing,
  });
})();
