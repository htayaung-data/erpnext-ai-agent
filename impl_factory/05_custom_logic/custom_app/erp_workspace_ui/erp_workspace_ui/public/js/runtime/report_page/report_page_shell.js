/* global frappe, $ */

(function () {
  const SHELL_VERSION = "2026-05-02-report-link-suggest-v1";
  const root = window;
  const reportPageRuntime = root.erpWorkspaceUiReportPage = root.erpWorkspaceUiReportPage || {};

  function escapeHtml(value) {
    return frappe.utils.escape_html(value == null ? "" : String(value));
  }

  function normalizeItems(items) {
    return Array.isArray(items) ? items.filter(Boolean) : [];
  }

  function cssToken(value) {
    return String(value || "")
      .toLowerCase()
      .replace(/[^a-z0-9-]+/g, "-")
      .replace(/^-+|-+$/g, "");
  }

  function isProcurementReport(config) {
    return String(config && (config.workspace || (config.page && config.page.workspace)) || '').toLowerCase() === 'procurement';
  }

  function normalizeFields(fields) {
    return Array.isArray(fields) ? fields.filter((field) => field && field.key) : [];
  }

  function normalizeControlSpan(field) {
    const raw = Number(field && field.span);
    if (!Number.isFinite(raw)) return 1;
    const span = Math.max(1, Math.min(4, Math.floor(raw)));
    return span || 1;
  }

  function normalizeControlRow(field) {
    const raw = Number(field && field.row);
    if (!Number.isFinite(raw)) return 1;
    const row = Math.max(1, Math.floor(raw));
    return row || 1;
  }

  function groupFieldsByRow(fields) {
    const grouped = new Map();
    normalizeFields(fields).forEach((field) => {
      const row = normalizeControlRow(field);
      if (!grouped.has(row)) grouped.set(row, []);
      grouped.get(row).push(field);
    });
    return Array.from(grouped.entries())
      .sort((a, b) => a[0] - b[0])
      .map((entry) => entry[1]);
  }

  function procurementReportFilterPriority(field, index, fieldKeys) {
    const key = String(field && field.key || '').toLowerCase();
    const role = reportFieldRole(field);
    const explicit = Number(field && field.priority);
    if (Number.isFinite(explicit)) return explicit;
    const hasPoAnalysisShape = fieldKeys && fieldKeys.has('purchase_order');
    const hasDemandShape = fieldKeys && fieldKeys.has('material_request');
    const order = {
      item_code: hasPoAnalysisShape ? 40 : hasDemandShape ? 30 : 10,
      item: hasPoAnalysisShape ? 40 : hasDemandShape ? 30 : 10,
      purchase_order: 10,
      material_request: 10,
      purchase_request: 10,
      status: 20,
      coverage_status: 20,
      supplier: 30,
      supplier_quotation: 30,
      request_for_quotation: 34,
      item_group: 36,
      warehouse: 40,
      categorize_by: 54,
      include_expired: 58,
      from_date: 80,
      to_date: 82,
    };
    if (Object.prototype.hasOwnProperty.call(order, key)) return order[key] + (index / 1000);
    if (role === 'date') return 80 + (index / 1000);
    if (role === 'search') return 32 + (index / 1000);
    return 40 + (index / 1000);
  }

  function prioritizedProcurementFields(fields) {
    const items = normalizeFields(fields);
    const fieldKeys = new Set(items.map((field) => String(field && field.key || '').toLowerCase()));
    return items
      .map((field, index) => ({ field, index }))
      .sort((left, right) => {
        const priority = procurementReportFilterPriority(left.field, left.index, fieldKeys) - procurementReportFilterPriority(right.field, right.index, fieldKeys);
        return priority || (left.index - right.index);
      })
      .map((entry) => entry.field);
  }

  function composeProcurementAnalyticsRows(fields) {
    const items = prioritizedProcurementFields(fields);
    const count = items.length;
    if (!count) return [];
    if (count <= 3) return [items];
    if (count === 4) return [items.slice(0, 2), items.slice(2)];
    if (count === 5) return [items.slice(0, 3), items.slice(3)];
    if (count === 6) return [items.slice(0, 3), items.slice(3)];
    if (count === 7) return [items.slice(0, 3), items.slice(3, 5), items.slice(5)];
    if (count === 8) return [items.slice(0, 4), items.slice(4)];
    const rows = [];
    let index = 0;
    while (index < count) {
      const remaining = count - index;
      let size = remaining >= 4 ? 4 : remaining;
      if (remaining - size === 1 && size > 2) size -= 1;
      rows.push(items.slice(index, index + size));
      index += size;
    }
    return rows;
  }

  function composeAnalyticsFieldRows(fields, pageConfig) {
    if (isProcurementReport(pageConfig)) return composeProcurementAnalyticsRows(fields);
    return groupFieldsByRow(fields);
  }

  function reportFieldRole(field) {
    const explicit = String(field && (field.layoutRole || field.filterRole) || '').trim().toLowerCase();
    if (explicit) return explicit;
    const key = String(field && field.key || '').toLowerCase();
    const type = String(field && field.type || '').toLowerCase();
    if (type === 'date' || /(^|_)(date|from|to|start|end)($|_)/.test(key)) return 'date';
    if (type === 'link' || type === 'text') return 'search';
    if (!type && /keyword|search|customer|item|supplier/.test(key)) return 'search';
    return 'standard';
  }

  function reportFieldAttrs(field) {
    const key = String(field && field.key || '');
    const role = reportFieldRole(field);
    return ' data-erpw-report-field-key="' + escapeHtml(key) + '" data-erpw-report-field-role="' + escapeHtml(role) + '"';
  }

  function reportFieldTrack(field, pageConfig) {
    if (isProcurementReport(pageConfig)) return '';
    const role = reportFieldRole(field);
    if (role === 'search') return 'minmax(240px, 1fr)';
    if (role === 'date') return 'minmax(170px, 208px)';
    if (role === 'compact') return 'minmax(144px, 176px)';
    return 'minmax(170px, 208px)';
  }

  function reportCommandFieldsStyle(rowFields, pageConfig) {
    if (isProcurementReport(pageConfig)) return '';
    const tracks = normalizeFields(rowFields).map((field) => reportFieldTrack(field, pageConfig)).filter(Boolean);
    return tracks.length ? ' style="grid-template-columns:' + escapeHtml(tracks.join(' ')) + '"' : '';
  }

  function ensureStyle() {
    if (document.getElementById("erpw-report-shell-style")) return;

    const style = document.createElement("style");
    style.id = "erpw-report-shell-style";
    style.textContent = `
      .erpw-report-shell {
        --erpw-report-control-height: 40px;
        --erpw-report-control-label-offset: 22px;
        display: grid;
        gap: 16px;
        width: min(1120px, calc(100% - 24px));
        margin: 0 auto;
        padding: 4px 0 30px;
      }
      .erpw-report-card {
        background: #ffffff;
        border: 1px solid rgba(223, 232, 242, 0.78);
        border-radius: 18px;
        box-shadow:
          0 1px 0 rgba(255, 255, 255, 0.98) inset,
          0 10px 24px rgba(15, 23, 42, 0.028),
          0 2px 5px rgba(15, 23, 42, 0.018);
      }
      .erpw-report-shell.is-data-refreshing .erpw-report-metrics,
      .erpw-report-shell.is-data-refreshing .erpw-report-secondary,
      .erpw-report-shell.is-data-refreshing .erpw-report-results {
        opacity: 0.58;
        pointer-events: none;
        transition: opacity 120ms ease;
      }
      .erpw-report-summary {
        padding: 18px 20px;
        display: grid;
        gap: 6px;
      }
      .erpw-report-kicker {
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #64748b;
      }
      .erpw-report-title {
        margin: 0;
        font-size: 20px;
        line-height: 1.15;
        font-weight: 700;
        color: #0f172a;
      }
      .erpw-report-subtitle {
        font-size: 13px;
        line-height: 1.55;
        color: #52627a;
      }
      .erpw-report-filter-strip {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        padding: 0 2px;
      }
      .erpw-report-filter-chip {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        min-height: 34px;
        padding: 0 12px;
        border-radius: 999px;
        border: 1px solid #d7e2ef;
        background: #ffffff;
        color: #243449;
        font-size: 12px;
        line-height: 1;
        white-space: nowrap;
      }
      .erpw-report-filter-label {
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        color: #6b7c93;
      }
      .erpw-report-filter-value {
        font-weight: 600;
        color: #132033;
      }
      .erpw-report-controls {
        padding: 16px 18px;
        display: grid;
        gap: 14px;
      }
	      .erpw-report-controls.analytics-compact {
	        width: 100%;
	        max-width: 100%;
	        padding: 14px;
	        gap: 10px;
	      }
      .erpw-report-controls-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        flex-wrap: wrap;
      }
      .erpw-report-controls-right {
        display: flex;
        align-items: center;
        justify-content: flex-end;
        gap: 10px;
        flex-wrap: wrap;
      }
      .erpw-report-controls-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        align-items: center;
      }
      .erpw-report-controls-meta-item {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        min-height: 30px;
        padding: 0 12px;
        border-radius: 999px;
        border: 1px solid #d7e2ef;
        background: #ffffff;
        color: #243449;
        font-size: 12px;
      }
      .erpw-report-controls-meta-item strong {
        font-size: 11px;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: #64748b;
      }
      .erpw-report-controls.analytics-compact .erpw-report-controls-meta {
        gap: 14px;
      }
      .erpw-report-controls.analytics-compact .erpw-report-controls-meta-item {
        min-height: auto;
        padding: 0;
        border: none;
        border-radius: 0;
        background: transparent;
        font-size: 12px;
        color: #607089;
      }
      .erpw-report-controls.analytics-compact .erpw-report-controls-meta-item strong {
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0;
        text-transform: none;
        color: #132033;
      }
      .erpw-report-control-form {
        display: grid;
        gap: 14px;
      }
	      .erpw-report-control-form.analytics-compact {
	        gap: 10px;
	      }
	      .erpw-report-command-panel {
	        display: grid;
	        gap: 10px;
	      }
	      .erpw-report-command-meta {
	        display: flex;
	        flex-wrap: wrap;
	        gap: 8px;
	        align-items: center;
	        color: #64748b;
	        font-size: 12px;
	      }
	      .erpw-report-command-meta strong {
	        color: #132033;
	        font-size: 12px;
	        font-weight: 650;
	      }
	      .erpw-report-command-row {
	        display: grid;
	        grid-template-columns: minmax(0, 1fr) auto;
	        align-items: stretch;
	        gap: 10px;
	      }
	      .erpw-report-shell:not(.is-procurement-report) .erpw-report-command-row.field-count-4:not(.without-actions) {
	        grid-template-columns: minmax(0, 1fr);
	      }
	      .erpw-report-command-row.without-actions {
	        grid-template-columns: minmax(0, 1fr);
	      }
	      .erpw-report-command-fields {
	        display: grid;
	        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
	        gap: 10px;
	        align-items: end;
	        min-width: 0;
	      }
	      .erpw-report-command-fields.field-count-1 {
	        grid-template-columns: minmax(220px, 280px);
	      }
	      .erpw-report-command-fields.field-count-2 {
	        grid-template-columns: repeat(2, minmax(190px, 240px));
	      }
	      .erpw-report-command-fields.field-count-3 {
	        grid-template-columns: repeat(3, minmax(180px, 240px));
	      }
	      .erpw-report-command-fields.field-count-4 {
	        grid-template-columns: repeat(4, minmax(150px, 1fr));
	      }
	      .erpw-report-command-actions {
	        display: inline-flex;
	        flex-wrap: wrap;
	        align-items: center;
	        justify-content: center;
	        gap: 6px;
	        align-self: start;
	        box-sizing: border-box;
	        min-height: var(--erpw-report-control-height);
	        margin-top: var(--erpw-report-control-label-offset);
	        padding: 2px;
	        border: 1px solid rgba(226, 232, 240, 0.76);
	        border-radius: 15px;
	        background: rgba(255, 255, 255, 0.9);
	        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.96);
	      }
	      .erpw-report-shell:not(.is-procurement-report) .erpw-report-command-row.field-count-4:not(.without-actions) .erpw-report-command-actions {
	        justify-self: end;
	        margin-top: 0;
	      }
	      .erpw-report-command-row.actions-only .erpw-report-command-actions {
	        justify-content: flex-start;
	        margin-top: 0;
	      }
	      .erpw-report-control-grid {
	        display: grid;
	        grid-template-columns: repeat(4, minmax(0, 1fr));
	        gap: 12px;
      }
      .erpw-report-control-grid-stack {
        display: grid;
        gap: 12px;
      }
      .erpw-report-control-grid.analytics-compact {
        gap: 10px;
      }
      .erpw-report-control-grid-stack.analytics-compact {
        gap: 10px;
      }
      .erpw-report-control-field {
        position: relative;
        display: grid;
        gap: 6px;
      }
      .erpw-report-control-field[data-erpw-control-span="2"],
      .erpw-report-control-tile[data-erpw-control-span="2"] {
        grid-column: span 2;
      }
      .erpw-report-control-field[data-erpw-control-span="3"],
      .erpw-report-control-tile[data-erpw-control-span="3"] {
        grid-column: span 3;
      }
      .erpw-report-control-field[data-erpw-control-span="4"],
      .erpw-report-control-tile[data-erpw-control-span="4"] {
        grid-column: span 4;
      }
      .erpw-report-control-tile {
        position: relative;
        display: grid;
        gap: 7px;
        padding: 12px 14px 11px;
        border: 1px solid rgba(221, 231, 242, 0.9);
        border-radius: 14px;
        background: linear-gradient(180deg, #ffffff 0%, #f9fbfe 100%);
        box-shadow: 0 1px 0 rgba(255, 255, 255, 0.96) inset;
      }
      .erpw-report-control-tile::before {
        content: "";
        position: absolute;
        top: 0;
        left: 14px;
        width: 32px;
        height: 3px;
        border-radius: 999px;
        background: #9fb0c7;
      }
      .erpw-report-control-tile:nth-child(1)::before { background: #2ec5a7; }
      .erpw-report-control-tile:nth-child(2)::before { background: #94a3b8; }
      .erpw-report-control-tile:nth-child(3)::before { background: #e8b44f; }
      .erpw-report-control-tile:nth-child(4)::before { background: #768ab1; }
      .erpw-report-control-label {
        font-size: 10.5px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #64748b;
      }
      .erpw-report-control-input {
        width: 100%;
        min-height: 38px;
        padding: 0 12px;
        border-radius: 10px;
        border: 1px solid #d8e4f2;
        background: #ffffff;
        color: #132033;
        font-size: 13px;
        outline: none;
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.96);
      }
	      .erpw-report-controls.analytics-compact .erpw-report-control-input {
	        min-height: 40px;
	        padding: 0 13px;
	        border-radius: 13px;
	        background: #ffffff;
	        font-size: 14px;
	        font-weight: 500;
	      }
      .erpw-report-control-input:focus {
        border-color: #9eb7d4;
        background: #ffffff;
      }
      .erpw-report-link-suggestions {
        position: absolute;
        left: 0;
        right: 0;
        top: calc(100% + 6px);
        z-index: 60;
        display: grid;
        gap: 3px;
        max-height: 230px;
        overflow-y: auto;
        padding: 7px;
        border: 1px solid rgba(190, 205, 225, 0.92);
        border-radius: 14px;
        background: #ffffff;
        box-shadow: 0 18px 44px rgba(23, 42, 69, 0.16), 0 2px 8px rgba(23, 42, 69, 0.08);
      }
      .erpw-report-link-suggestions[hidden] {
        display: none;
      }
      .erpw-report-link-suggestion {
        display: grid;
        gap: 2px;
        padding: 9px 10px;
        border-radius: 10px;
        color: #17233a;
        cursor: pointer;
      }
      .erpw-report-link-suggestion:hover,
      .erpw-report-link-suggestion.is-active {
        background: linear-gradient(180deg, #f4f8fd 0%, #edf4fb 100%);
      }
      .erpw-report-link-suggestion-value {
        font-size: 13px;
        font-weight: 700;
        line-height: 1.25;
      }
      .erpw-report-link-suggestion-label {
        color: #60728c;
        font-size: 12px;
        line-height: 1.25;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
      .erpw-report-link-suggestion-note {
        padding: 10px;
        color: #71839d;
        font-size: 12.5px;
        font-weight: 600;
      }
      .erpw-report-control-actions {
        display: flex;
        gap: 10px;
        justify-content: flex-end;
      }
      .erpw-report-toolbar-actions {
        display: flex;
        gap: 10px;
        justify-content: flex-end;
        flex-wrap: wrap;
      }
      .erpw-report-controls.analytics-compact .erpw-report-control-actions {
        justify-content: flex-end;
      }
	      .erpw-report-control-button {
        min-height: 32px;
        padding: 0 14px;
        border-radius: 999px;
        border: 1px solid #cdd9e8;
        background: #ffffff;
        color: #0f172a;
        font-size: 12px;
        font-weight: 600;
        cursor: pointer;
      }
	      .erpw-report-controls.analytics-compact .erpw-report-control-button {
	        min-height: 34px;
	        padding: 0 13px;
	        font-size: 12px;
	      }
	      .erpw-report-command-actions .erpw-report-control-button {
	        border-color: transparent;
	        border-radius: 11px;
	      }
	      .erpw-report-control-button.primary {
	        border-color: #2f475f;
	        background: #22324b;
	        color: #ffffff;
	      }
	      .erpw-report-control-button.is-refresh:not(.primary) {
	        background: transparent;
	        color: #334155;
	      }
	      .erpw-report-control-button.navigation {
	        display: inline-flex;
	        align-items: center;
	        justify-content: center;
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
	      .erpw-report-control-button-navigation-icon {
	        color: #64748b;
	        font-size: 0.82rem;
	        line-height: 1;
	        transform: translateY(-0.5px);
	      }
      .erpw-report-metrics {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 12px;
      }
      .erpw-report-metrics.analytics-compact {
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 10px;
      }
      .erpw-report-metric {
        position: relative;
        padding: 16px 18px 14px;
        display: grid;
        gap: 6px;
        overflow: hidden;
      }
      .erpw-report-metric.analytics-compact {
        padding: 13px 14px 12px;
        gap: 4px;
      }
      .erpw-report-metric::before {
        content: "";
        position: absolute;
        top: 0;
        left: 18px;
        width: 44px;
        height: 3px;
        border-radius: 999px;
        background: #94a3b8;
      }
      .erpw-report-metric.analytics-compact::before {
        left: 14px;
        width: 34px;
      }
      .erpw-report-metric.tone-teal::before { background: #2ec5a7; }
      .erpw-report-metric.tone-slate::before { background: #9fb0c7; }
      .erpw-report-metric.tone-amber::before { background: #e8b44f; }
      .erpw-report-metric.tone-indigo::before { background: #768ab1; }
      .erpw-report-metric-label {
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #64748b;
      }
      .erpw-report-metric.analytics-compact .erpw-report-metric-label {
        font-size: 10.5px;
      }
      .erpw-report-metric-value {
        font-size: 17px;
        line-height: 1.25;
        font-weight: 700;
        color: #0f172a;
      }
      .erpw-report-metric.analytics-compact .erpw-report-metric-value {
        font-size: 15px;
        line-height: 1.3;
        word-break: break-word;
      }
      .erpw-report-metric-meta {
        font-size: 12px;
        line-height: 1.5;
        color: #607089;
      }
      .erpw-report-metric.analytics-compact .erpw-report-metric-meta {
        font-size: 11px;
        line-height: 1.45;
      }
      .erpw-report-secondary {
        padding: 18px 20px;
        display: grid;
        gap: 14px;
      }
      .erpw-report-secondary.analytics-trend-compact {
        padding: 12px 14px 14px;
        gap: 10px;
      }
      .erpw-report-section-head {
        display: grid;
        gap: 4px;
      }
      .erpw-report-section-title {
        font-size: 16px;
        font-weight: 700;
        color: #0f172a;
      }
      .erpw-report-section-subtitle {
        font-size: 12.5px;
        line-height: 1.55;
        color: #64748b;
      }
      .erpw-report-secondary.analytics-trend-compact .erpw-report-section-title {
        font-size: 13px;
      }
      .erpw-report-secondary.analytics-trend-compact .erpw-report-section-subtitle {
        font-size: 11px;
        line-height: 1.45;
      }
      .erpw-report-insight-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 12px;
      }
      .erpw-report-insight {
        padding: 14px 16px;
        border-radius: 14px;
        border: 1px solid #e1eaf4;
        background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
        display: grid;
        gap: 4px;
      }
      .erpw-report-insight-label {
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #64748b;
      }
      .erpw-report-insight-value {
        font-size: 17px;
        line-height: 1.2;
        font-weight: 700;
        color: #0f172a;
      }
      .erpw-report-insight-meta {
        font-size: 12px;
        color: #607089;
      }
      .erpw-report-chart {
        display: grid;
        gap: 10px;
      }
      .erpw-report-secondary.analytics-trend-compact .erpw-report-chart {
        gap: 6px;
      }
      .erpw-report-chart-summary {
        font-size: 12px;
        color: #52627a;
      }
      .erpw-report-secondary.analytics-trend-compact .erpw-report-chart-summary {
        display: none;
      }
      .erpw-report-chart-strip {
        display: grid;
        grid-auto-flow: column;
        grid-auto-columns: minmax(70px, 1fr);
        gap: 10px;
        overflow-x: auto;
        padding-bottom: 4px;
      }
      .erpw-report-secondary.analytics-trend-compact .erpw-report-chart-strip {
        grid-auto-columns: minmax(54px, 1fr);
        gap: 6px;
      }
      .erpw-report-chart-point {
        display: grid;
        gap: 8px;
        min-width: 70px;
      }
      .erpw-report-secondary.analytics-trend-compact .erpw-report-chart-point {
        gap: 5px;
        min-width: 54px;
      }
      .erpw-report-chart-track {
        position: relative;
        height: 122px;
        display: flex;
        align-items: flex-end;
        padding: 0 6px;
        border-radius: 14px;
        background: linear-gradient(180deg, #fbfdff 0%, #f3f8fd 100%);
        border: 1px solid rgba(226, 235, 245, 0.82);
      }
      .erpw-report-secondary.analytics-trend-compact .erpw-report-chart-track {
        height: 84px;
        padding: 0 5px;
        border-radius: 12px;
      }
      .erpw-report-chart-bar {
        width: 100%;
        min-height: 8px;
        border-radius: 10px 10px 4px 4px;
        background: linear-gradient(180deg, #95abc7 0%, #5f7898 100%);
      }
      .erpw-report-chart-point.is-highlighted .erpw-report-chart-bar {
        background: linear-gradient(180deg, #2ec5a7 0%, #218c77 100%);
      }
      .erpw-report-chart-label {
        font-size: 11px;
        line-height: 1.35;
        font-weight: 700;
        color: #425269;
        text-align: center;
      }
      .erpw-report-secondary.analytics-trend-compact .erpw-report-chart-label {
        font-size: 10px;
      }
      .erpw-report-chart-value {
        font-size: 11px;
        color: #64748b;
        text-align: center;
      }
      .erpw-report-secondary.analytics-trend-compact .erpw-report-chart-value {
        display: none;
      }
      .erpw-report-results {
        padding: 18px 20px 20px;
        display: grid;
        gap: 14px;
      }
      .erpw-report-results-head {
        display: flex;
        justify-content: space-between;
        align-items: start;
        gap: 12px;
      }
      .erpw-report-results-copy {
        display: grid;
        gap: 4px;
      }
      .erpw-report-results-title {
        font-size: 17px;
        font-weight: 700;
        color: #0f172a;
      }
      .erpw-report-results-subtitle {
        font-size: 12.5px;
        line-height: 1.55;
        color: #64748b;
      }
      .erpw-report-results-meta {
        font-size: 12px;
        color: #64748b;
        white-space: nowrap;
      }
      .erpw-report-table-wrap {
        position: relative;
        max-width: 100%;
        overflow-x: auto;
        overflow-y: hidden;
        overscroll-behavior-x: contain;
        border: 1px solid rgba(220, 230, 241, 0.88);
        border-radius: 16px;
        background: #ffffff;
        scrollbar-gutter: stable;
        scrollbar-width: thin;
        scrollbar-color: rgba(100, 116, 139, 0.42) rgba(241, 245, 249, 0.86);
      }
      .erpw-report-table-wrap.is-wide {
        box-shadow: inset -24px 0 24px -30px rgba(15, 23, 42, 0.62);
      }
      .erpw-report-table-wrap.is-wide:focus {
        outline: 2px solid rgba(37, 99, 235, 0.18);
        outline-offset: 3px;
      }
      .erpw-report-table-wrap::-webkit-scrollbar {
        height: 10px;
      }
      .erpw-report-table-wrap::-webkit-scrollbar-track {
        background: rgba(241, 245, 249, 0.86);
        border-radius: 999px;
      }
      .erpw-report-table-wrap::-webkit-scrollbar-thumb {
        background: rgba(100, 116, 139, 0.42);
        border: 2px solid rgba(241, 245, 249, 0.86);
        border-radius: 999px;
      }
      .erpw-report-table {
        width: 100%;
        min-width: 840px;
        table-layout: auto;
        border-collapse: separate;
        border-spacing: 0;
      }
      .erpw-report-table thead th {
        padding: 13px 16px;
        border-bottom: 1px solid #d8e4f2;
        background: linear-gradient(180deg, #f8fbff 0%, #f2f7fc 100%);
        font-size: 10.5px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #687a92;
        text-align: left;
      }
      .erpw-report-table thead th.right,
      .erpw-report-table tbody td.right {
        text-align: right;
      }
      .erpw-report-table thead th.numeric,
      .erpw-report-table tbody td.numeric,
      .erpw-report-table thead th.right,
      .erpw-report-table tbody td.right {
        font-variant-numeric: tabular-nums;
        font-feature-settings: "tnum" 1, "lnum" 1;
      }
      .erpw-report-table thead th.nowrap,
      .erpw-report-table tbody td.nowrap,
      .erpw-report-table thead th.numeric,
      .erpw-report-table tbody td.numeric {
        white-space: nowrap;
      }
      .erpw-report-table tbody td {
        padding: 14px 16px;
        border-bottom: 1px solid #edf3fa;
        font-size: 14px;
        line-height: 1.5;
        color: #132033;
        vertical-align: top;
        background: #ffffff;
        transition: background-color 140ms ease;
      }
      .erpw-report-table tbody tr:hover td {
        background: #fbfdff;
      }
      .erpw-report-table tbody tr:last-child td {
        border-bottom: none;
      }
      .erpw-report-table thead th:first-child,
      .erpw-report-table tbody td:first-child {
        position: sticky;
        left: 0;
        z-index: 2;
        min-width: 170px;
        max-width: 280px;
        background: #ffffff;
        box-shadow: 10px 0 18px -18px rgba(15, 23, 42, 0.34);
      }
      .erpw-report-table thead th:first-child {
        z-index: 3;
        background: linear-gradient(180deg, #f8fbff 0%, #f2f7fc 100%);
      }
      .erpw-report-cell-link {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
        width: 100%;
        padding: 0;
        border: none;
        background: transparent;
        font: inherit;
        color: #0f172a;
        font-weight: 600;
        text-align: left;
        cursor: pointer;
        transition: color 140ms ease;
      }
      .erpw-report-cell-link-label {
        flex: 1;
        min-width: 0;
      }
      .erpw-report-cell-link:hover {
        color: #0b1324;
      }
      .erpw-report-cell-link::after {
        content: "\\2192";
        font-size: 13px;
        color: #94a3b8;
        transition: color 140ms ease, transform 140ms ease;
      }
      .erpw-report-cell-link:hover::after {
        color: #71839d;
        transform: translateX(1px);
      }
      .erpw-report-empty,
      .erpw-report-state {
        padding: 22px 20px;
        border-radius: 16px;
        border: 1px solid #d8e4f2;
        background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
        display: grid;
        gap: 6px;
      }
      .erpw-report-state-title {
        font-size: 16px;
        font-weight: 700;
        color: #0f172a;
      }
      .erpw-report-state-detail {
        font-size: 13px;
        line-height: 1.55;
        color: #64748b;
      }
      .erpw-report-state.error {
        border-color: #f3d0d0;
        background: linear-gradient(180deg, #fffdfd 0%, #fff6f6 100%);
      }
      .erpw-report-state.loading {
        border-color: #d8e4f2;
      }
      .erpw-report-state-button {
        justify-self: start;
        min-height: 34px;
        padding: 0 14px;
        border-radius: 999px;
        border: 1px solid #cdd9e8;
        background: #ffffff;
        color: #0f172a;
        font-size: 13px;
        font-weight: 600;
        cursor: pointer;
      }

      .erpw-report-shell.is-procurement-report {
        width: min(1360px, calc(100% - 24px));
        gap: 12px;
      }
      .erpw-report-shell.is-procurement-report .erpw-report-summary {
        padding: 13px 16px;
        gap: 5px;
        border-radius: 14px;
        border-color: rgba(221, 229, 239, 0.9);
        background: #ffffff;
        box-shadow: 0 1px 0 rgba(255, 255, 255, 0.98) inset, 0 8px 18px rgba(15, 23, 42, 0.022);
      }
      .erpw-report-shell.is-procurement-report .erpw-report-kicker {
        font-size: 10.5px;
        letter-spacing: 0.08em;
        color: #64748b;
      }
      .erpw-report-shell.is-procurement-report .erpw-report-title {
        font-size: 18px;
        line-height: 1.18;
      }
      .erpw-report-shell.is-procurement-report .erpw-report-subtitle {
        max-width: 760px;
        font-size: 12.75px;
        line-height: 1.42;
        color: #475569;
      }
      .erpw-report-shell.is-procurement-report .erpw-report-controls.analytics-compact {
        width: min(100%, 980px);
        justify-self: center;
        padding: 12px 14px;
        gap: 12px;
        border-radius: 14px;
        border-color: rgba(221, 229, 239, 0.9);
        background: #ffffff;
        box-shadow: 0 1px 0 rgba(255, 255, 255, 0.98) inset, 0 6px 16px rgba(15, 23, 42, 0.018);
      }
      .erpw-report-shell.is-procurement-report .erpw-report-command-panel {
        gap: 12px;
      }
      .erpw-report-shell.is-procurement-report .erpw-report-command-meta {
        gap: 10px;
        padding: 0 2px;
        color: #475569;
      }
      .erpw-report-shell.is-procurement-report .erpw-report-command-meta strong {
        color: #0f172a;
        font-weight: 700;
      }
      .erpw-report-shell.is-procurement-report .erpw-report-command-row {
        grid-template-columns: minmax(0, 1fr) max-content;
        align-items: end;
        gap: 14px;
      }
      .erpw-report-shell.is-procurement-report .erpw-report-command-row.without-actions {
        grid-template-columns: minmax(0, 1fr);
      }
      .erpw-report-shell.is-procurement-report .erpw-report-command-row.without-actions .erpw-report-command-fields {
        justify-self: start;
      }
      .erpw-report-shell.is-procurement-report .erpw-report-command-row.field-count-4:not(.without-actions) {
        grid-template-columns: minmax(0, 1fr) max-content;
      }
      .erpw-report-shell.is-procurement-report .erpw-report-command-fields {
        gap: 10px;
        align-items: end;
      }
      /* Procurement report filter composition contract:
         rows are composed by the shared shell into balanced groups, then fields
         flex across the available content width so final-row actions stay attached. */
      .erpw-report-shell.is-procurement-report .erpw-report-command-fields {
        justify-content: stretch;
        width: 100%;
      }
      .erpw-report-shell.is-procurement-report .erpw-report-command-fields.field-count-1 {
        grid-template-columns: minmax(240px, min(360px, 100%));
      }
      .erpw-report-shell.is-procurement-report .erpw-report-command-fields.field-count-2 {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
      .erpw-report-shell.is-procurement-report .erpw-report-command-fields.field-count-3 {
        grid-template-columns: repeat(3, minmax(0, 1fr));
      }
      .erpw-report-shell.is-procurement-report .erpw-report-command-fields.field-count-4 {
        grid-template-columns: repeat(4, minmax(150px, 1fr));
      }
      .erpw-report-shell.is-procurement-report .erpw-report-command-actions {
        align-self: end;
        min-height: 38px;
        margin-top: 0;
        padding: 2px;
        border-radius: 14px;
        border-color: rgba(226, 232, 240, 0.86);
        background: #ffffff;
        box-shadow: 0 1px 0 rgba(255, 255, 255, 0.98) inset;
        white-space: nowrap;
      }
      .erpw-report-shell.is-procurement-report .erpw-report-command-actions .erpw-report-control-button {
        min-height: 32px;
        padding: 0 13px;
        border-radius: 10px;
        font-size: 12px;
      }
      .erpw-report-shell.is-procurement-report .erpw-report-command-actions .erpw-report-control-button.navigation {
        border-radius: 999px;
      }
      .erpw-report-shell.is-procurement-report .erpw-report-command-row.actions-only {
        grid-template-columns: minmax(0, 1fr);
      }
      .erpw-report-shell.is-procurement-report .erpw-report-command-row.actions-only .erpw-report-command-actions {
        justify-self: end;
      }
      .erpw-report-shell.is-procurement-report .erpw-report-metrics.analytics-compact {
        grid-template-columns: repeat(auto-fit, minmax(180px, 240px));
        justify-content: start;
        gap: 10px;
      }
      .erpw-report-shell.is-procurement-report .erpw-report-metrics.analytics-compact.layout-five-up {
        grid-template-columns: repeat(5, minmax(0, 1fr)) !important;
        justify-content: stretch;
      }
      .erpw-report-shell.is-procurement-report .erpw-report-metric.analytics-compact {
        min-height: 84px;
        padding: 12px 13px;
        border-radius: 14px;
      }
      .erpw-report-shell.is-procurement-report .erpw-report-command-row.field-count-2:not(.without-actions) {
        grid-template-columns: minmax(0, 1fr) max-content;
      }
      @media (max-width: 1080px) {
        .erpw-report-shell.is-procurement-report .erpw-report-command-row {
          grid-template-columns: minmax(0, 1fr);
        }
        .erpw-report-shell.is-procurement-report .erpw-report-command-row.actions-only .erpw-report-command-actions,
        .erpw-report-shell.is-procurement-report .erpw-report-command-actions {
          justify-self: start;
          justify-content: flex-start;
        }
        .erpw-report-shell.is-procurement-report .erpw-report-command-row.field-count-4:not(.without-actions) .erpw-report-command-actions {
          justify-self: start;
        }
      }
      @media (max-width: 1024px) {
        .erpw-report-control-grid,
        .erpw-report-metrics,
        .erpw-report-insight-grid {
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }
        .erpw-report-shell.is-procurement-report .erpw-report-metrics.analytics-compact.layout-five-up {
          grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
        }
      }
      @media (max-width: 720px) {
        .erpw-report-shell {
          width: calc(100% - 16px);
          gap: 12px;
        }
        .erpw-report-summary,
        .erpw-report-controls,
        .erpw-report-secondary,
        .erpw-report-results {
          padding: 16px;
        }
        .erpw-report-control-grid,
        .erpw-report-metrics,
        .erpw-report-insight-grid {
          grid-template-columns: minmax(0, 1fr);
        }
        .erpw-report-shell.is-procurement-report .erpw-report-metrics.analytics-compact.layout-five-up {
          grid-template-columns: minmax(0, 1fr) !important;
        }
        .erpw-report-results-head {
          display: grid;
        }
        .erpw-report-results-meta {
          white-space: normal;
        }
	        .erpw-report-control-actions {
	          justify-content: stretch;
	        }
	        .erpw-report-controls.analytics-compact {
	          width: 100%;
	        }
	        .erpw-report-command-row,
	        .erpw-report-command-actions {
	          width: 100%;
	        }
	        .erpw-report-command-row {
	          grid-template-columns: minmax(0, 1fr);
	        }
	        .erpw-report-command-actions {
	          margin-top: 0;
	        }
	        .erpw-report-command-fields,
	        .erpw-report-command-fields.field-count-1,
	        .erpw-report-command-fields.field-count-2,
	        .erpw-report-command-fields.field-count-3,
	        .erpw-report-command-fields.field-count-4 {
	          width: 100%;
	          grid-template-columns: minmax(0, 1fr);
	        }
	        .erpw-report-control-field[data-erpw-control-span],
	        .erpw-report-control-tile[data-erpw-control-span] {
	          grid-column: auto;
	        }
      }
    `;
    document.head.appendChild(style);
  }

  function renderSummary(summary) {
    if (!summary || !summary.title) return "";
    return [
      '<section class="erpw-report-card erpw-report-summary">',
        summary.kicker ? '<div class="erpw-report-kicker">' + escapeHtml(summary.kicker) + '</div>' : '',
        '<h2 class="erpw-report-title">' + escapeHtml(summary.title) + '</h2>',
        summary.subtitle ? '<div class="erpw-report-subtitle">' + escapeHtml(summary.subtitle) + '</div>' : '',
      '</section>'
    ].join("");
  }

  function renderControlInput(field) {
    const rawKey = String(field.key || "");
    const key = escapeHtml(rawKey);
    const value = escapeHtml(field.value == null ? "" : field.value);
    const type = field.type || "text";
    const placeholder = escapeHtml(field.placeholder || "");
    const linkDoctype = field.linkDoctype || field.doctype || field.optionsDoctype || "";
    if (type === "select") {
      const options = normalizeItems(field.options).map((option) => {
        const optionValue = option && option.value != null ? String(option.value) : "";
        const selected = optionValue === String(field.value == null ? "" : field.value) ? ' selected' : '';
        return '<option value="' + escapeHtml(optionValue) + '"' + selected + '>' + escapeHtml(option.label || optionValue) + '</option>';
      }).join("");
      return [
        '<select class="erpw-report-control-input" data-erpw-control-key="' + key + '">',
          options,
        '</select>'
      ].join("");
    }
    if (type === "link" && linkDoctype) {
      const popupId = 'erpw-report-link-options-' + rawKey.replace(/[^a-zA-Z0-9_-]/g, '-');
      return [
        '<input class="erpw-report-control-input" type="text" autocomplete="off" role="combobox" aria-autocomplete="list" aria-expanded="false" aria-controls="' + escapeHtml(popupId) + '" data-erpw-control-key="' + key + '" data-erpw-link-doctype="' + escapeHtml(linkDoctype) + '"' + (placeholder ? ' placeholder="' + placeholder + '"' : '') + ' value="' + value + '">',
        '<div class="erpw-report-link-suggestions" id="' + escapeHtml(popupId) + '" role="listbox" hidden></div>',
      ].join("");
    }
    return '<input class="erpw-report-control-input" type="' + escapeHtml(type) + '" data-erpw-control-key="' + key + '"' + (placeholder ? ' placeholder="' + placeholder + '"' : '') + ' value="' + value + '">';
  }

  function renderControlField(field) {
    const label = escapeHtml(field.label || "");
    const span = normalizeControlSpan(field);
    const spanAttr = span > 1 ? ' data-erpw-control-span="' + span + '"' : "";
    return [
      '<label class="erpw-report-control-field"' + spanAttr + reportFieldAttrs(field) + '>',
        '<span class="erpw-report-control-label">' + label + '</span>',
        renderControlInput(field),
      '</label>'
    ].join("");
  }

	  function renderAnalyticsControlField(field) {
	    const label = escapeHtml(field.label || "");
	    return [
	      '<label class="erpw-report-control-field"' + reportFieldAttrs(field) + '>',
	        '<span class="erpw-report-control-label">' + label + '</span>',
	        renderControlInput(field),
	      '</label>'
	    ].join("");
	  }

	  function renderToolbarAction(action) {
	    if (!action || !action.key || !action.label) return "";
	    const key = String(action.key || "");
	    const isNavigation = action.category === "navigation" || /^back_/.test(key);
	    const isBackNavigation = isNavigation && (
	      /^back_/.test(key)
	      || /^cancel_/.test(key)
	      || /^back to\b/i.test(String(action.label || ""))
	    );
	    const buttonClass = [
	      "erpw-report-control-button",
	      action.kind === "primary" ? "primary" : "",
	      key === "refresh" ? "is-refresh" : "",
	      isNavigation ? "navigation" : "",
	    ].filter(Boolean).join(" ");
	    const iconMarkup = isBackNavigation
	      ? '<span class="erpw-report-control-button-navigation-icon" aria-hidden="true">&larr;</span>'
	      : '';
	    return '<button type="button" class="' + buttonClass + '" data-erpw-report-action-key="' + escapeHtml(action.key) + '">' + iconMarkup + '<span>' + escapeHtml(action.label) + '</span></button>';
	  }

	  function sortToolbarActions(actions) {
	    const order = {
	      refresh: 10,
	      back_to_console: 20,
	    };
	    return normalizeItems(actions).slice().sort((left, right) => {
	      const leftOrder = order[String(left && left.key || "")] || 100;
	      const rightOrder = order[String(right && right.key || "")] || 100;
	      if (leftOrder !== rightOrder) return leftOrder - rightOrder;
	      return String(left && left.label || "").localeCompare(String(right && right.label || ""));
	    });
	  }

  function renderControls(controls, pageConfig) {
    const fields = normalizeFields(controls && controls.fields);
    const actions = normalizeItems(controls && controls.actions);
    const toolbarMarkup = actions.length
      ? '<div class="erpw-report-toolbar-actions">' + actions.map((action) => renderToolbarAction(action)).join("") + '</div>'
      : "";
    const appearance = (controls && controls.appearance) || "";
    const isAnalyticsCompact = appearance === "analytics_compact";
    const fieldRows = groupFieldsByRow(fields);
    const renderFieldRows = (renderer, compact) => [
      '<div class="erpw-report-control-grid-stack' + (compact ? ' analytics-compact' : '') + '">',
        fieldRows.map((rowFields) => [
          '<div class="erpw-report-control-grid' + (compact ? ' analytics-compact' : '') + '">',
            rowFields.map(renderer).join(''),
          '</div>'
        ].join('')).join(''),
      '</div>'
    ].join('');
	    if (fields.length) {
	      const meta = normalizeItems(controls && controls.meta);
	      const submitActionsMarkup = [
	        '<button type="submit" class="erpw-report-control-button primary">' + escapeHtml((controls && controls.submitLabel) || 'Apply') + '</button>',
	        '<button type="button" class="erpw-report-control-button erpw-report-control-reset">' + escapeHtml((controls && controls.resetLabel) || 'Reset') + '</button>',
	      ].join('');
	      const headRightMarkup = toolbarMarkup
	        ? '<div class="erpw-report-controls-right">' + toolbarMarkup + submitActionsMarkup + '</div>'
	        : submitActionsMarkup;
      const metaMarkup = meta.length ? [
        '<div class="erpw-report-controls-meta">',
          meta.map((item) => [
            '<div class="erpw-report-controls-meta-item">',
              item.label ? '<strong>' + escapeHtml(item.label || '') + '</strong>' : '',
              '<span>' + escapeHtml(item.value || '--') + '</span>',
            '</div>'
          ].join('')).join(''),
        '</div>'
	      ].join('') : '<div></div>';
	      if (isAnalyticsCompact) {
	        const separateActionRow = String((controls && controls.actionLayout) || '').toLowerCase() === 'separate_row';
	        const compactMetaMarkup = meta.length ? [
	          '<div class="erpw-report-command-meta">',
	            meta.map((item) => [
	              item.label ? '<strong>' + escapeHtml(item.label || '') + '</strong>' : '',
	              '<span>' + escapeHtml(item.value || '--') + '</span>',
	            ].join('')).join(''),
	          '</div>',
	        ].join('') : '';
	        const compactActionsMarkup = [
	          '<div class="erpw-report-command-actions">',
	            submitActionsMarkup,
	            sortToolbarActions(actions).map((action) => renderToolbarAction(action)).join(''),
	          '</div>',
	        ].join('');
	        const compactFieldRows = composeAnalyticsFieldRows(fields, pageConfig);
	        const compactRowsMarkup = compactFieldRows.map((rowFields, rowIndex) => {
	          const isLastRow = !separateActionRow && rowIndex === compactFieldRows.length - 1;
	          const searchIndex = rowFields.findIndex((field) => reportFieldRole(field) === 'search');
	          const searchClass = searchIndex >= 0 ? ' has-search search-index-' + Math.min(searchIndex + 1, 4) : ' no-search';
	          const rowCountClass = 'field-count-' + Math.min(rowFields.length, 4);
	          const compactFieldsClass = 'erpw-report-command-fields ' + rowCountClass + searchClass;
	          return [
	            '<div class="erpw-report-command-row ' + rowCountClass + searchClass + (isLastRow ? '' : ' without-actions') + '">',
	              '<div class="' + compactFieldsClass + '"' + reportCommandFieldsStyle(rowFields, pageConfig) + '>',
	                rowFields.map(renderAnalyticsControlField).join(''),
	              '</div>',
	              isLastRow ? compactActionsMarkup : '',
	            '</div>',
	          ].join('');
	        }).join('');
	        const separateActionsMarkup = separateActionRow ? [
	          '<div class="erpw-report-command-row actions-only">',
	            compactActionsMarkup,
	          '</div>',
	        ].join('') : '';
	        return [
	          '<section class="erpw-report-card erpw-report-controls analytics-compact">',
	            '<form class="erpw-report-command-panel">',
	              compactMetaMarkup,
	              compactRowsMarkup,
	              separateActionsMarkup,
	            '</form>',
	          '</section>'
	        ].join('');
      }

      return [
        '<section class="erpw-report-card erpw-report-controls">',
          (meta.length || toolbarMarkup) ? [
            '<div class="erpw-report-controls-head">',
              metaMarkup,
              toolbarMarkup ? '<div class="erpw-report-controls-right">' + toolbarMarkup + '</div>' : '',
            '</div>'
          ].join("") : '',
          '<form class="erpw-report-control-form">',
            renderFieldRows(renderControlField, false),
            submitActionsMarkup,
          '</form>',
        '</section>'
      ].join("");
    }

    const chips = normalizeItems(controls && controls.filterChips);
    if (!chips.length && !toolbarMarkup) return "";
    return [
      '<section class="erpw-report-card erpw-report-controls">',
        toolbarMarkup ? [
          '<div class="erpw-report-controls-head">',
            '<div></div>',
            '<div class="erpw-report-controls-right">' + toolbarMarkup + '</div>',
          '</div>'
        ].join('') : '',
        chips.length ? [
          '<div class="erpw-report-filter-strip">',
            chips.map((chip) => [
              '<div class="erpw-report-filter-chip">',
                '<span class="erpw-report-filter-label">' + escapeHtml(chip.label || '') + '</span>',
                '<span class="erpw-report-filter-value">' + escapeHtml(chip.value || '--') + '</span>',
              '</div>'
            ].join("")).join(""),
          '</div>'
        ].join("") : '',
      '</section>'
    ].join("");
  }

  function renderMetrics(metrics) {
    const config = Array.isArray(metrics) ? { appearance: '', items: metrics } : (metrics || {});
    const items = normalizeItems(config.items != null ? config.items : metrics);
    if (!items.length) return "";
    const appearance = config.appearance || '';
    const isAnalyticsCompact = appearance === 'analytics_compact';
    const layout = cssToken(config.layout || '');
    const layoutClass = layout ? ' layout-' + layout : '';
    return [
      '<section class="erpw-report-metrics' + (isAnalyticsCompact ? ' analytics-compact' : '') + layoutClass + '">',
        items.map((item) => [
          '<article class="erpw-report-card erpw-report-metric tone-' + escapeHtml(item.tone || 'slate') + (isAnalyticsCompact ? ' analytics-compact' : '') + '">',
            '<div class="erpw-report-metric-label">' + escapeHtml(item.label || '') + '</div>',
            '<div class="erpw-report-metric-value">' + escapeHtml(item.value == null ? '--' : item.value) + '</div>',
            item.meta ? '<div class="erpw-report-metric-meta">' + escapeHtml(item.meta) + '</div>' : '',
          '</article>'
        ].join("")).join(""),
      '</section>'
    ].join("");
  }

  function renderChart(chart) {
    const points = normalizeItems(chart && chart.points);
    if (!chart || !points.length) return "";
    return [
      '<div class="erpw-report-chart">',
        chart.summary ? '<div class="erpw-report-chart-summary">' + escapeHtml(chart.summary) + '</div>' : '',
        '<div class="erpw-report-chart-strip">',
          points.map((point) => {
            const ratio = Math.max(0, Math.min(1, Number(point.ratio || 0)));
            const height = Math.max(8, Math.round(ratio * 100));
            return [
              '<div class="erpw-report-chart-point ' + (point.highlighted ? 'is-highlighted' : '') + '">',
                '<div class="erpw-report-chart-track" title="' + escapeHtml(point.formatted || '') + '">',
                  '<div class="erpw-report-chart-bar" style="height:' + height + '%"></div>',
                '</div>',
                '<div class="erpw-report-chart-label">' + escapeHtml(point.label || '') + '</div>',
                '<div class="erpw-report-chart-value">' + escapeHtml(point.formatted || '--') + '</div>',
              '</div>'
            ].join('');
          }).join(''),
        '</div>',
      '</div>'
    ].join('');
  }

  function renderSecondary(secondary) {
    const config = secondary || {};
    const appearance = config.appearance || '';
    const items = normalizeItems(config.items);
    const chartMarkup = renderChart(config.chart);
    if (!secondary || (!items.length && !chartMarkup)) return "";
    return [
      '<section class="erpw-report-card erpw-report-secondary' + (appearance === 'analytics_trend_compact' ? ' analytics-trend-compact' : '') + '">',
        '<div class="erpw-report-section-head">',
          config.title ? '<div class="erpw-report-section-title">' + escapeHtml(config.title) + '</div>' : '',
          config.subtitle ? '<div class="erpw-report-section-subtitle">' + escapeHtml(config.subtitle) + '</div>' : '',
        '</div>',
        chartMarkup,
        items.length ? [
          '<div class="erpw-report-insight-grid">',
            items.map((item) => [
              '<article class="erpw-report-insight">',
                '<div class="erpw-report-insight-label">' + escapeHtml(item.label || '') + '</div>',
                '<div class="erpw-report-insight-value">' + escapeHtml(item.value == null ? '--' : item.value) + '</div>',
                item.meta ? '<div class="erpw-report-insight-meta">' + escapeHtml(item.meta) + '</div>' : '',
              '</article>'
            ].join("")).join(""),
          '</div>'
        ].join("") : '',
      '</section>'
    ].join("");
  }

  function renderState(state) {
    if (!state) return "";
    return [
      '<div class="erpw-report-state ' + escapeHtml(state.kind || 'neutral') + '">',
        state.title ? '<div class="erpw-report-state-title">' + escapeHtml(state.title) + '</div>' : '',
        state.detail ? '<div class="erpw-report-state-detail">' + escapeHtml(state.detail) + '</div>' : '',
        state.action && state.action.key && state.action.label
          ? '<button type="button" class="erpw-report-state-button" data-erpw-report-action-key="' + escapeHtml(state.action.key) + '">' + escapeHtml(state.action.label) + '</button>'
          : '',
      '</div>'
    ].join("");
  }

    function isNumericColumn(column) {
      const fieldType = String(column && column.fieldtype || column && column.type || '').toLowerCase();
      const key = String(column && column.key || '').toLowerCase();
      const label = String(column && column.label || '').toLowerCase();
      return String(column && column.align || '').toLowerCase() === 'right'
        || ['currency', 'float', 'int', 'percent', 'number'].includes(fieldType)
        || /amount|billed|collected|outstanding|total|value|qty|quantity|count|percent|rate|orders_count|order_count/.test(key)
        || /amount|billed|collected|outstanding|total|value|qty|quantity|count|percent|rate|orders/.test(label);
    }

    function reportColumnClass(column) {
      const classes = [];
      const align = String(column && column.align || '').trim();
      if (align) classes.push(align);
      if (column && column.nowrap) classes.push('nowrap');
      if (isNumericColumn(column)) classes.push('numeric', 'nowrap');
      return Array.from(new Set(classes)).join(' ');
    }

    function effectiveTableMinWidth(config, columns) {
      const explicit = Number(config && config.tableMinWidth || 0);
      if (explicit > 0) return explicit;
      if (!columns || columns.length <= 6) return 840;
      const numericCount = columns.filter((column) => isNumericColumn(column)).length;
      const baseWidth = 240 + ((columns.length - 1) * 140) + (numericCount * 18);
      return Math.max(1040, baseWidth);
    }

    function renderCell(row, column) {
      const cells = row && row.cells && typeof row.cells === "object" ? row.cells : {};
      const cell = cells[column.key] || {};
      const value = cell.value == null ? "--" : cell.value;
      const labelClass = column && (column.nowrap || isNumericColumn(column)) ? 'erpw-report-cell-link-label nowrap' : 'erpw-report-cell-link-label';
      if (cell.actionKey) {
        return '<button type="button" class="erpw-report-cell-link" data-erpw-report-action-key="' + escapeHtml(cell.actionKey) + '"><span class="' + labelClass + '">' + escapeHtml(value) + '</span></button>';
      }
      return escapeHtml(value);
    }

    function renderResults(results) {
      if (!results) return "";
      const config = results || {};
      const columns = normalizeItems(config.columns);
      const rows = normalizeItems(config.rows);
      const tableMinWidth = effectiveTableMinWidth(config, columns);
      const tableStyle = tableMinWidth > 0 ? ' style="min-width:' + tableMinWidth + 'px"' : '';
      const isWideTable = tableMinWidth > 980 || columns.length > 6;
      const tableWrapClass = 'erpw-report-table-wrap' + (isWideTable ? ' is-wide' : '');
      const tableWrapAttrs = isWideTable
        ? ' tabindex="0" aria-label="Scrollable report table"'
        : '';
      return [
        '<section class="erpw-report-card erpw-report-results">',
        '<div class="erpw-report-results-head">',
          '<div class="erpw-report-results-copy">',
            config.title ? '<div class="erpw-report-results-title">' + escapeHtml(config.title) + '</div>' : '',
            config.subtitle ? '<div class="erpw-report-results-subtitle">' + escapeHtml(config.subtitle) + '</div>' : '',
          '</div>',
          config.meta ? '<div class="erpw-report-results-meta">' + escapeHtml(config.meta) + '</div>' : '',
        '</div>',
        config.state && config.state.kind && config.state.kind !== 'ready'
          ? renderState(config.state)
          : columns.length
              ? [
                 '<div class="' + tableWrapClass + '"' + tableWrapAttrs + '>',
                   '<table class="erpw-report-table"' + tableStyle + '>',
                      '<thead><tr>',
                        columns.map((column) => '<th class="' + escapeHtml(reportColumnClass(column)) + '">' + escapeHtml(column.label || '') + '</th>').join(""),
                      '</tr></thead>',
                      '<tbody>',
                        rows.length
                          ? rows.map((row) => [
                              '<tr>',
                               columns.map((column) => '<td class="' + escapeHtml(reportColumnClass(column)) + '">' + renderCell(row, column) + '</td>').join(""),
                              '</tr>'
                            ].join("")).join("")
                        : '<tr><td colspan="' + escapeHtml(columns.length) + '"><div class="erpw-report-empty">No visible rows match the current report window.</div></td></tr>',
                    '</tbody>',
                  '</table>',
                '</div>'
              ].join("")
            : renderState({
                kind: 'empty',
                title: 'Report is not ready yet',
                detail: 'This Sales Console report is missing its table setup. Refresh the page or return to the console.',
              }),
      '</section>'
    ].join("");
  }

  function resolveTarget(target) {
    if (!target) return $();
    return target.jquery ? target.first() : $(target).first();
  }

  function ensureShell(target) {
    const $target = resolveTarget(target);
    if (!$target.length) return $();
    if ($target.hasClass('erpw-report-shell')) return $target;

    let $shell = $target.children('.erpw-report-shell').first();
    if (!$shell.length) {
      $shell = $('<section class="erpw-report-shell"></section>');
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

  function applyWorkspaceMode($shell, config) {
    if (!$shell || !$shell.length) return;
    $shell.toggleClass('is-procurement-report', isProcurementReport(config));
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

    const beforeSelectors = String(beforeSelector || '').split(',').map((item) => item.trim()).filter(Boolean);
    let $before = $();
    beforeSelectors.some((selector) => {
      $before = $shell.children(selector).first();
      return Boolean($before.length);
    });
    if ($before.length) {
      $next.insertBefore($before);
      return;
    }

    $shell.append($next);
  }

  function collectControlValues(form) {
    const values = {};
    $(form).find('[data-erpw-control-key]').each(function () {
      const key = this.getAttribute('data-erpw-control-key') || '';
      if (!key) return;
      const rawValue = this.value == null ? '' : String(this.value).trim();
      if (rawValue) values[key] = rawValue;
    });
    return values;
  }

  function normalizeLinkSearchRows(rows) {
    return normalizeItems(rows).map((row) => {
      if (typeof row === "string") return { value: row, label: "" };
      const value = row.value || row.name || row.label || "";
      const description = row.description || row.label || "";
      return {
        value: String(value || ""),
        label: description && description !== value ? String(description) : "",
      };
    }).filter((row) => row.value);
  }

  function getLinkSuggestionPanel(input) {
    const field = input && input.closest ? input.closest(".erpw-report-control-field") : null;
    return field ? field.querySelector(".erpw-report-link-suggestions") : null;
  }

  function closeLinkSuggestions(input) {
    const panel = getLinkSuggestionPanel(input);
    if (!panel) return;
    panel.innerHTML = "";
    panel.hidden = true;
    input.__erpwReportLinkRows = [];
    input.__erpwReportLinkActiveIndex = -1;
    input.setAttribute("aria-expanded", "false");
    input.removeAttribute("aria-activedescendant");
  }

  function setLinkSuggestionActive(input, index) {
    const panel = getLinkSuggestionPanel(input);
    const rows = input.__erpwReportLinkRows || [];
    if (!panel || !rows.length) return;
    const nextIndex = Math.max(0, Math.min(index, rows.length - 1));
    input.__erpwReportLinkActiveIndex = nextIndex;
    Array.prototype.forEach.call(panel.querySelectorAll("[data-erpw-report-link-option]"), (option, optionIndex) => {
      const isActive = optionIndex === nextIndex;
      option.classList.toggle("is-active", isActive);
      option.setAttribute("aria-selected", isActive ? "true" : "false");
    });
    if (panel.id) {
      input.setAttribute("aria-activedescendant", panel.id + "-option-" + nextIndex);
    }
  }

  function renderLinkSuggestions(input, rows) {
    const panel = getLinkSuggestionPanel(input);
    if (!panel) return;
    const normalizedRows = normalizeLinkSearchRows(rows).slice(0, 8);
    input.__erpwReportLinkRows = normalizedRows;
    input.__erpwReportLinkActiveIndex = normalizedRows.length ? 0 : -1;
    input.setAttribute("aria-expanded", "true");
    panel.hidden = false;
    if (!normalizedRows.length) {
      input.removeAttribute("aria-activedescendant");
      panel.innerHTML = '<div class="erpw-report-link-suggestion-note">No matches found</div>';
      return;
    }
    panel.innerHTML = normalizedRows.map((row, index) => {
      const label = row.label && row.label !== row.value
        ? '<span class="erpw-report-link-suggestion-label">' + escapeHtml(row.label) + '</span>'
        : '';
      const id = panel.id ? ' id="' + escapeHtml(panel.id + "-option-" + index) + '"' : '';
      return [
        '<div class="erpw-report-link-suggestion" role="option"', id, ' aria-selected="false" data-erpw-report-link-option="', index, '">',
          '<span class="erpw-report-link-suggestion-value">', escapeHtml(row.value), '</span>',
          label,
        '</div>'
      ].join("");
    }).join("");
    setLinkSuggestionActive(input, 0);
  }

  function selectLinkSuggestion(input, row) {
    if (!row || !row.value) return;
    input.value = row.value;
    closeLinkSuggestions(input);
    $(input).trigger("change");
  }

  function fetchLinkSuggestions(input) {
    const doctype = input.getAttribute("data-erpw-link-doctype") || "";
    const txt = String(input.value || "").trim();
    if (!doctype || txt.length < 1 || typeof frappe === "undefined" || !frappe.call) {
      closeLinkSuggestions(input);
      return;
    }
    const requestToken = String(Date.now()) + "-" + Math.random();
    input.__erpwReportLinkRequestToken = requestToken;
    frappe.call({
      method: "frappe.desk.search.search_link",
      args: {
        doctype,
        txt,
        page_length: 8,
      },
    }).then((response) => {
      if (!document.body.contains(input)) return;
      if (input.__erpwReportLinkRequestToken !== requestToken) return;
      renderLinkSuggestions(input, response && response.message ? response.message : []);
    }).catch(() => {
      if (input.__erpwReportLinkRequestToken === requestToken) closeLinkSuggestions(input);
    });
  }

  function bindLinkSuggestions($shell) {
    const timers = new WeakMap();
    $shell.on("input.erpwReportShell focus.erpwReportShell", "[data-erpw-link-doctype]", function () {
      const input = this;
      const existingTimer = timers.get(input);
      if (existingTimer) clearTimeout(existingTimer);
      const timer = setTimeout(() => fetchLinkSuggestions(input), 180);
      timers.set(input, timer);
    });
    $shell.on("keydown.erpwReportShell", "[data-erpw-link-doctype]", function (event) {
      const input = this;
      const rows = input.__erpwReportLinkRows || [];
      const panel = getLinkSuggestionPanel(input);
      const isOpen = panel && !panel.hidden && rows.length;
      if (event.key === "Escape") {
        closeLinkSuggestions(input);
        return;
      }
      if (!isOpen) return;
      if (event.key === "ArrowDown") {
        event.preventDefault();
        setLinkSuggestionActive(input, (input.__erpwReportLinkActiveIndex || 0) + 1);
      } else if (event.key === "ArrowUp") {
        event.preventDefault();
        setLinkSuggestionActive(input, (input.__erpwReportLinkActiveIndex || 0) - 1);
      } else if (event.key === "Enter") {
        const activeIndex = input.__erpwReportLinkActiveIndex == null ? 0 : input.__erpwReportLinkActiveIndex;
        if (rows[activeIndex]) {
          event.preventDefault();
          selectLinkSuggestion(input, rows[activeIndex]);
        }
      }
    });
    $shell.on("mousedown.erpwReportShell", "[data-erpw-report-link-option]", function (event) {
      event.preventDefault();
      const option = this;
      const field = option.closest(".erpw-report-control-field");
      const input = field ? field.querySelector("[data-erpw-link-doctype]") : null;
      const rows = input && input.__erpwReportLinkRows ? input.__erpwReportLinkRows : [];
      const index = parseInt(option.getAttribute("data-erpw-report-link-option") || "0", 10);
      if (input && rows[index]) selectLinkSuggestion(input, rows[index]);
    });
    $shell.on("focusout.erpwReportShell", "[data-erpw-link-doctype]", function () {
      const input = this;
      setTimeout(() => {
        const field = input.closest ? input.closest(".erpw-report-control-field") : null;
        if (field && field.contains(document.activeElement)) return;
        closeLinkSuggestions(input);
      }, 120);
    });
  }

  function bindInteractions($shell, config) {
    const onAction = config && typeof config.onAction === 'function' ? config.onAction : null;
    const onControlSubmit = config && typeof config.onControlSubmit === 'function' ? config.onControlSubmit : null;

    $shell.off('.erpwReportShell');
    bindLinkSuggestions($shell);

    if (onAction) {
      $shell.on('click.erpwReportShell', '[data-erpw-report-action-key]', function (event) {
        event.preventDefault();
        onAction({
          key: this.getAttribute('data-erpw-report-action-key') || '',
          trigger: this,
        });
      });
    }

    if (onControlSubmit) {
      $shell.on('submit.erpwReportShell', '.erpw-report-control-form, .erpw-report-command-panel', function (event) {
        event.preventDefault();
        onControlSubmit({
          mode: 'apply',
          values: collectControlValues(this),
          trigger: this,
        });
      });
      $shell.on('click.erpwReportShell', '.erpw-report-control-reset', function (event) {
        event.preventDefault();
        onControlSubmit({
          mode: 'reset',
          values: {},
          trigger: this,
        });
      });
    }
  }

  function refreshReportData(target, config, options) {
    ensureStyle();
    const $shell = ensureShell(target);
    if (!$shell.length) return $shell;

    const page = config || {};
    const settings = options && typeof options === 'object' ? options : {};
    $shell.attr('data-report-key', escapeHtml(page.reportKey || ''));
    applyWorkspaceMode($shell, page);

    if (settings.refreshControls) {
      replaceShellSection($shell, '.erpw-report-controls', renderControls(page.controls, page), '.erpw-report-metrics, .erpw-report-secondary, .erpw-report-results');
    }
    replaceShellSection($shell, '.erpw-report-metrics', renderMetrics(page.metrics), '.erpw-report-secondary, .erpw-report-results');
    replaceShellSection($shell, '.erpw-report-secondary', renderSecondary(page.secondary), '.erpw-report-results');
    replaceShellSection($shell, '.erpw-report-results', renderResults(page.results));
    setDataRefreshing($shell, false);
    bindInteractions($shell, config || {});
    return $shell;
  }

  function mountReport(target, config) {
    ensureStyle();
    const $shell = ensureShell(target);
    if (!$shell.length) return $shell;

    $shell.attr('data-report-key', escapeHtml((config && config.reportKey) || ''));
    applyWorkspaceMode($shell, config || {});
    $shell.html([
      renderSummary(config && config.summary),
      renderControls(config && config.controls, config || {}),
      renderMetrics(config && config.metrics),
      renderSecondary(config && config.secondary),
      renderResults(config && config.results),
    ].filter(Boolean).join(''));

    bindInteractions($shell, config);
    return $shell;
  }

  reportPageRuntime.shell = Object.assign({}, reportPageRuntime.shell, {
    version: SHELL_VERSION,
    mountReport,
    refreshReportData,
    setDataRefreshing,
  });
})();
