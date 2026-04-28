/* global frappe, $ */

(function () {
  const SHELL_VERSION = "2026-04-21-report-table-fit";
  const root = window;
  const reportPageRuntime = root.erpWorkspaceUiReportPage = root.erpWorkspaceUiReportPage || {};

  function escapeHtml(value) {
    return frappe.utils.escape_html(value == null ? "" : String(value));
  }

  function normalizeItems(items) {
    return Array.isArray(items) ? items.filter(Boolean) : [];
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

  function ensureStyle() {
    if (document.getElementById("erpw-report-shell-style")) return;

    const style = document.createElement("style");
    style.id = "erpw-report-shell-style";
    style.textContent = `
      .erpw-report-shell {
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
        padding: 12px 14px 14px;
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
        min-height: 34px;
        padding: 0 10px;
        border-radius: 10px;
        background: #f8fbff;
        font-size: 12.5px;
      }
      .erpw-report-control-input:focus {
        border-color: #9eb7d4;
        background: #ffffff;
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
        min-height: 30px;
        padding: 0 12px;
        font-size: 12px;
      }
      .erpw-report-control-button.primary {
        border-color: #2f475f;
        background: #22324b;
        color: #ffffff;
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
        overflow-x: auto;
        border: 1px solid rgba(220, 230, 241, 0.88);
        border-radius: 16px;
      }
      .erpw-report-table {
        width: 100%;
        min-width: 840px;
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
      .erpw-report-table thead th.nowrap,
      .erpw-report-table tbody td.nowrap {
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
      @media (max-width: 1024px) {
        .erpw-report-control-grid,
        .erpw-report-metrics,
        .erpw-report-insight-grid {
          grid-template-columns: repeat(2, minmax(0, 1fr));
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
        .erpw-report-results-head {
          display: grid;
        }
        .erpw-report-results-meta {
          white-space: normal;
        }
        .erpw-report-control-actions {
          justify-content: stretch;
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
    const key = escapeHtml(field.key || "");
    const value = escapeHtml(field.value == null ? "" : field.value);
    const type = field.type || "text";
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
    return '<input class="erpw-report-control-input" type="' + escapeHtml(type) + '" data-erpw-control-key="' + key + '" value="' + value + '">';
  }

  function renderControlField(field) {
    const label = escapeHtml(field.label || "");
    const span = normalizeControlSpan(field);
    const spanAttr = span > 1 ? ' data-erpw-control-span="' + span + '"' : "";
    return [
      '<label class="erpw-report-control-field"' + spanAttr + '>',
        '<span class="erpw-report-control-label">' + label + '</span>',
        renderControlInput(field),
      '</label>'
    ].join("");
  }

  function renderAnalyticsControlField(field) {
    const label = escapeHtml(field.label || "");
    const span = normalizeControlSpan(field);
    const spanAttr = span > 1 ? ' data-erpw-control-span="' + span + '"' : "";
    return [
      '<label class="erpw-report-control-tile"' + spanAttr + '>',
        '<span class="erpw-report-control-label">' + label + '</span>',
        renderControlInput(field),
      '</label>'
    ].join("");
  }

  function renderToolbarAction(action) {
    if (!action || !action.key || !action.label) return "";
    const buttonClass = action.kind === "primary"
      ? "erpw-report-control-button primary"
      : "erpw-report-control-button";
    return '<button type="button" class="' + buttonClass + '" data-erpw-report-action-key="' + escapeHtml(action.key) + '">' + escapeHtml(action.label) + '</button>';
  }

  function renderControls(controls) {
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
        '<div class="erpw-report-control-actions">',
          '<button type="button" class="erpw-report-control-button erpw-report-control-reset">' + escapeHtml((controls && controls.resetLabel) || 'Reset') + '</button>',
          '<button type="submit" class="erpw-report-control-button primary">' + escapeHtml((controls && controls.submitLabel) || 'Apply') + '</button>',
        '</div>',
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
        return [
          '<section class="erpw-report-card erpw-report-controls analytics-compact">',
            '<form class="erpw-report-control-form analytics-compact">',
              '<div class="erpw-report-controls-head">',
                metaMarkup,
                headRightMarkup,
              '</div>',
              renderFieldRows(renderAnalyticsControlField, true),
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
    return [
      '<section class="erpw-report-metrics' + (isAnalyticsCompact ? ' analytics-compact' : '') + '">',
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

    function renderCell(row, column) {
      const cells = row && row.cells && typeof row.cells === "object" ? row.cells : {};
      const cell = cells[column.key] || {};
      const value = cell.value == null ? "--" : cell.value;
      const labelClass = column && column.nowrap ? 'erpw-report-cell-link-label nowrap' : 'erpw-report-cell-link-label';
      if (cell.actionKey) {
        return '<button type="button" class="erpw-report-cell-link" data-erpw-report-action-key="' + escapeHtml(cell.actionKey) + '"><span class="' + labelClass + '">' + escapeHtml(value) + '</span></button>';
      }
      return escapeHtml(value);
    }

    function renderResults(results) {
      const config = results || {};
      const columns = normalizeItems(config.columns);
      const rows = normalizeItems(config.rows);
      const tableMinWidth = Number(config.tableMinWidth || 0);
      const tableStyle = tableMinWidth > 0 ? ' style="min-width:' + tableMinWidth + 'px"' : '';
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
                 '<div class="erpw-report-table-wrap">',
                   '<table class="erpw-report-table"' + tableStyle + '>',
                      '<thead><tr>',
                        columns.map((column) => '<th class="' + escapeHtml(((column.align || '') + ' ' + (column.nowrap ? 'nowrap' : '')).trim()) + '">' + escapeHtml(column.label || '') + '</th>').join(""),
                      '</tr></thead>',
                      '<tbody>',
                        rows.length
                          ? rows.map((row) => [
                              '<tr>',
                               columns.map((column) => '<td class="' + escapeHtml(((column.align || '') + ' ' + (column.nowrap ? 'nowrap' : '')).trim()) + '">' + renderCell(row, column) + '</td>').join(""),
                              '</tr>'
                            ].join("")).join("")
                        : '<tr><td colspan="' + escapeHtml(columns.length) + '"><div class="erpw-report-empty">No visible rows match the current report window.</div></td></tr>',
                    '</tbody>',
                  '</table>',
                '</div>'
              ].join("")
            : renderState({
                kind: 'empty',
                title: 'No report structure defined',
                detail: 'Columns were not configured for this report surface.',
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

    let $shell = $target.children('.erpw-report-shell').first();
    if (!$shell.length) {
      $shell = $('<section class="erpw-report-shell"></section>');
      $target.empty().append($shell);
    }
    return $shell;
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

  function bindInteractions($shell, config) {
    const onAction = config && typeof config.onAction === 'function' ? config.onAction : null;
    const onControlSubmit = config && typeof config.onControlSubmit === 'function' ? config.onControlSubmit : null;

    $shell.off('.erpwReportShell');

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
      $shell.on('submit.erpwReportShell', '.erpw-report-control-form', function (event) {
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

  function mountReport(target, config) {
    ensureStyle();
    const $shell = ensureShell(target);
    if (!$shell.length) return $shell;

    $shell.attr('data-report-key', escapeHtml((config && config.reportKey) || ''));
    $shell.html([
      renderSummary(config && config.summary),
      renderControls(config && config.controls),
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
  });
})();
