/* global frappe, $ */

(function () {
  const PAGE_KEY = "sales-console";
  const BOOTSTRAP_METHOD = "erp_workspace_ui.sales_console.service.get_sales_console_bootstrap";
  const INQUIRY_METHOD = "erp_workspace_ui.sales_console.service.resolve_customer_inquiry";
  const INQUIRY_SUGGEST_METHOD = "erp_workspace_ui.sales_console.service.suggest_customer_inquiry";
  const INQUIRY_AI_METHOD = "erp_workspace_ui.sales_console.service.generate_customer_inquiry_assist";
  const consoleRuntime = window.erpWorkspaceConsoleRuntime || {};

  function getConsoleRuntimeMethod(name) {
    const method = consoleRuntime[name];
    if (typeof method === "function") return method;
    throw new Error(`Sales Console runtime is missing method: ${name}`);
  }

  function syncNativeChrome(page, title) {
    const chrome = window.erpWorkspaceUiSalesConsoleChrome;
    if (!chrome || typeof chrome.sync !== "function") return;
    chrome.sync({ page, title });
  }

  function ensureStyle() {
    if (document.getElementById("sales-console-shell-style")) return;

    const style = document.createElement("style");
    style.id = "sales-console-shell-style";
    style.textContent = `
      .sales-console-shell {
        display: grid;
        gap: 16px;
        padding: 4px 0 30px;
        width: min(1120px, calc(100% - 24px));
        min-width: 0;
        box-sizing: border-box;
        margin: 0 auto;
      }
      .sales-console-card {
        min-width: 0;
        background: var(--erpw-surface-elevated-quiet, rgba(255, 255, 255, 0.97));
        border: 1px solid var(--erpw-border-strong, rgba(255, 255, 255, 0.94));
        border-radius: 16px;
        box-shadow: var(
          --erpw-shadow-shell,
          0 1px 0 rgba(255, 255, 255, 0.98) inset,
          0 12px 28px rgba(15, 23, 42, 0.04)
        );
      }
      .sales-console-header {
        overflow: hidden;
        padding: 24px 24px 22px;
        border: none;
        background:
          radial-gradient(circle at top right, rgba(45, 212, 191, 0.16), transparent 26%),
          radial-gradient(circle at bottom left, rgba(56, 189, 248, 0.12), transparent 30%),
          linear-gradient(145deg, #131b2d 0%, #1d2b43 52%, #0b1220 100%);
        box-shadow:
          0 24px 44px rgba(15, 23, 42, 0.16),
          0 1px 0 rgba(255, 255, 255, 0.06) inset;
      }
      .sales-console-header-row {
        display: grid;
        grid-template-columns: minmax(0, 1fr);
        align-items: start;
        gap: 16px 20px;
        margin-bottom: 12px;
      }
      .sales-console-header-copy {
        display: grid;
        gap: 5px;
        min-width: 0;
      }
      .sales-console-title {
        margin: 0;
        font-size: 31px;
        line-height: 1.05;
        font-weight: 700;
        color: #f8fafc;
      }
      .sales-console-header-note {
        max-width: 760px;
        font-size: 13px;
        line-height: 1.6;
        color: #d4deea;
      }
      .sales-console-header-context {
        display: grid;
        justify-items: end;
        align-content: start;
        gap: 6px;
        min-width: 0;
      }
      .sales-console-header-chip {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-height: 30px;
        padding: 0 12px;
        border-radius: 999px;
        border: 1px solid rgba(214, 227, 240, 0.2);
        background: rgba(255, 255, 255, 0.07);
        color: #f8fafc;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        white-space: nowrap;
      }
      .sales-console-header-roleline {
        max-width: 320px;
        font-size: 12.75px;
        line-height: 1.4;
        font-weight: 600;
        color: #dde7f3;
        text-align: right;
      }
      .sales-console-header-context-note {
        max-width: 320px;
        font-size: 11.5px;
        line-height: 1.45;
        color: #c7d3e1;
        text-align: right;
      }
      .sales-console-header-context-note[hidden] {
        display: none;
      }
      .sales-console-kpi-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0;
        width: 100%;
        max-width: none;
        overflow: hidden;
        border-radius: 18px;
        border: 1px solid rgba(214, 227, 240, 0.15);
        background: linear-gradient(180deg, rgba(55, 73, 98, 0.88) 0%, rgba(40, 56, 78, 0.82) 100%);
        box-shadow:
          0 1px 0 rgba(255, 255, 255, 0.08) inset,
          0 18px 28px rgba(8, 15, 28, 0.1);
      }
      .sales-console-kpi-card {
        position: relative;
        min-width: 0;
        display: grid;
        gap: 6px;
        padding: 18px 22px 17px;
        width: 100%;
        border: none;
        appearance: none;
        text-align: left;
        cursor: pointer;
        background: linear-gradient(180deg, rgba(255, 255, 255, 0.02) 0%, rgba(255, 255, 255, 0.01) 100%);
        backdrop-filter: blur(10px);
        transition: background 120ms ease, box-shadow 120ms ease;
      }
      .sales-console-kpi-card:hover {
        background: linear-gradient(180deg, rgba(255, 255, 255, 0.035) 0%, rgba(255, 255, 255, 0.018) 100%);
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.1);
      }
      .sales-console-kpi-card + .sales-console-kpi-card {
        border-left: 1px solid rgba(214, 227, 240, 0.12);
      }
      .sales-console-kpi-label {
        margin: 0;
        font-size: 11px;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #9eb0c7;
      }
      .sales-console-kpi-value {
        margin: 0;
        font-size: 32px;
        line-height: 0.95;
        font-weight: 700;
        color: #f8fafc;
        letter-spacing: -0.03em;
      }
      .sales-console-kpi-meta {
        font-size: 12px;
        line-height: 1.55;
        color: #d4deea;
      }
      .sales-console-section {
        position: relative;
        padding: 18px 20px 20px;
      }
      .sales-console-section-head {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 12px;
        margin-bottom: 14px;
        min-width: 0;
      }
      .sales-console-section-title {
        margin: 0;
        font-size: 18px;
        font-weight: 700;
        color: #0f172a;
      }
      .sales-console-section-note {
        font-size: 11.5px;
        color: var(--erpw-note-color, #64748b);
        text-align: right;
        max-width: 250px;
        line-height: 1.45;
        white-space: normal;
      }
      .sales-console-section[data-section-key="work"] .sales-console-section-head,
      .sales-console-section[data-section-key="lifecycle"] .sales-console-section-head,
      .sales-console-section[data-section-key="approvals"] .sales-console-section-head,
      .sales-console-section[data-section-key="reports"] .sales-console-section-head {
        margin-bottom: 16px;
        padding-bottom: 10px;
        border-bottom: 1px solid #edf2f7;
      }
      .sales-console-section[data-section-key="approvals"] .sales-console-section-head {
        border-bottom-color: #e5edf7;
      }
      .sales-console-action-groups {
        display: grid;
        gap: 10px;
      }
      .sales-console-action-strip {
        display: grid;
        gap: 14px;
      }
      .sales-console-action-strip.primary {
        grid-template-columns: repeat(3, minmax(0, 1fr));
      }
      .sales-console-action-strip.secondary {
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 10px;
      }
      .sales-console-action-strip.secondary[hidden] {
        display: none;
      }
      .sales-console-action {
        position: relative;
        overflow: hidden;
        display: grid;
        grid-template-columns: 42px minmax(0, 1fr);
        align-items: start;
        gap: 14px;
        text-align: left;
        padding: 18px 20px 17px;
        border-radius: 16px;
        border: 1px solid var(--erpw-border-strong, rgba(255, 255, 255, 0.92));
        background: var(--erpw-surface-elevated, #ffffff);
        cursor: pointer;
        transition: transform 120ms ease, border-color 120ms ease, box-shadow 120ms ease;
        min-width: 0;
        box-shadow: var(
          --erpw-shadow-card,
          0 1px 0 rgba(255, 255, 255, 0.98) inset,
          0 10px 24px rgba(15, 23, 42, 0.04)
        );
      }
      .sales-console-action::before {
        content: "";
        position: absolute;
        top: 0;
        left: 20px;
        width: 44px;
        height: 4px;
        border-radius: 999px;
        background: #d7e0ea;
      }
      .sales-console-action:hover {
        border-color: rgba(255, 255, 255, 0.98);
        box-shadow: var(
          --erpw-shadow-card-hover,
          0 1px 0 rgba(255, 255, 255, 0.98) inset,
          0 14px 30px rgba(15, 23, 42, 0.07)
        );
      }
      .sales-console-action.primary {
        background: #ffffff;
      }
      .sales-console-action.primary::before {
        background: linear-gradient(90deg, #0f766e 0%, #2dd4bf 100%);
      }
      .sales-console-action.secondary {
        padding-top: 15px;
        background: #ffffff;
      }
      .sales-console-action.secondary::before {
        width: 40px;
        background: #8ea4bf;
      }
      .sales-console-action-icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 42px;
        height: 42px;
        border-radius: 11px;
        border: 1px solid var(--erpw-icon-dark-border, #35465f);
        background: var(--erpw-icon-dark-bg, #2a3850);
        color: #f8fafc;
        box-shadow:
          0 1px 0 rgba(255, 255, 255, 0.08) inset,
          0 10px 20px rgba(15, 23, 42, 0.16);
      }
      .sales-console-action.primary .sales-console-action-icon {
        border-color: var(--erpw-icon-dark-border, #314259);
        background: var(--erpw-icon-dark-bg, #243247);
        color: #f8fafc;
      }
      .sales-console-action.secondary .sales-console-action-icon {
        border-color: var(--erpw-icon-dark-border, #314259);
        background: var(--erpw-icon-dark-bg, #243247);
        color: #f8fafc;
      }
      .sales-console-action-icon .icon,
      .sales-console-link-icon .icon,
      .sales-console-sidebar-guide-mark .icon {
        width: 17px;
        height: 17px;
      }
      .sales-console-action-icon svg,
      .sales-console-link-icon svg,
      .sales-console-sidebar-guide-mark svg {
        width: 17px;
        height: 17px;
        display: block;
      }
      .sales-console-action-icon .icon use,
      .sales-console-link-icon .icon use,
      .sales-console-sidebar-guide-mark .icon use {
        stroke: currentColor;
      }
      .sales-console-action-copy {
        display: grid;
        gap: 5px;
        min-width: 0;
      }
      .sales-console-action-title {
        margin: 0;
        font-size: 13.5px;
        font-weight: 700;
        color: #0f172a;
      }
      .sales-console-action.primary .sales-console-action-title {
        font-size: 14.75px;
      }
      .sales-console-action-meta {
        margin: 0;
        font-size: 12px;
        line-height: 1.42;
        color: #64748b;
      }
      .sales-console-body {
        display: grid;
        gap: 16px;
      }
      .sales-console-inquiry {
        display: grid;
        gap: 14px;
      }
      .sales-console-inquiry-shell {
        display: grid;
        gap: 12px;
        padding: 16px;
        border-radius: 16px;
        border: 1px solid var(--erpw-border-strong, rgba(255, 255, 255, 0.94));
        background: var(--erpw-surface-shell, linear-gradient(180deg, rgba(248, 250, 252, 0.9) 0%, rgba(255, 255, 255, 0.98) 100%));
        box-shadow: var(
          --erpw-shadow-panel,
          0 1px 0 rgba(255, 255, 255, 0.98) inset,
          0 8px 18px rgba(15, 23, 42, 0.03)
        );
      }
      .sales-console-inquiry-intro {
        display: grid;
        gap: 4px;
      }
      .sales-console-inquiry-title {
        margin: 0;
        font-size: 14px;
        font-weight: 700;
        color: #0f172a;
      }
      .sales-console-inquiry-meta {
        margin: 0;
        font-size: 12px;
        line-height: 1.45;
        color: #64748b;
      }
      .sales-console-inquiry-form {
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        gap: 10px;
        align-items: start;
      }
      .sales-console-inquiry-input-shell {
        position: relative;
        min-width: 0;
      }
      .sales-console-inquiry-actions {
        display: inline-flex;
        align-items: center;
        gap: 10px;
      }
      .sales-console-inquiry-input {
        width: 100%;
        min-width: 0;
        height: 44px;
        padding: 0 14px;
        border-radius: 12px;
        border: 1px solid #dbe4ee;
        background: #ffffff;
        color: #0f172a;
        font-size: 13px;
        box-shadow: 0 1px 0 rgba(255, 255, 255, 0.98) inset;
      }
      .sales-console-inquiry-input:focus {
        outline: none;
        border-color: #8ecfca;
        box-shadow:
          0 0 0 3px rgba(45, 212, 191, 0.12),
          0 1px 0 rgba(255, 255, 255, 0.98) inset;
      }
      .sales-console-inquiry-suggestions {
        position: absolute;
        top: calc(100% + 8px);
        left: 0;
        right: 0;
        z-index: 20;
        display: grid;
        gap: 8px;
        padding: 10px;
        border-radius: 16px;
        border: 1px solid var(--erpw-border-soft, #dbe4ee);
        background: rgba(255, 255, 255, 0.99);
        box-shadow: var(
          --erpw-shadow-card-hover,
          0 1px 0 rgba(255, 255, 255, 0.98) inset,
          0 14px 30px rgba(15, 23, 42, 0.07)
        );
      }
      .sales-console-inquiry-suggestions[hidden] {
        display: none;
      }
      .sales-console-inquiry-suggestions-group {
        display: grid;
        gap: 4px;
      }
      .sales-console-inquiry-suggestions-group + .sales-console-inquiry-suggestions-group {
        padding-top: 8px;
        border-top: 1px solid #eef2f7;
      }
      .sales-console-inquiry-suggestions-label {
        padding: 0 6px;
        font-size: 10.5px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #64748b;
      }
      .sales-console-inquiry-suggestion {
        display: grid;
        grid-template-columns: auto minmax(0, 1fr);
        align-items: start;
        gap: 10px;
        width: 100%;
        padding: 10px 12px;
        border-radius: 14px;
        border: 1px solid transparent;
        background: #ffffff;
        color: #0f172a;
        text-align: left;
        cursor: pointer;
        transition: border-color 120ms ease, background 120ms ease, box-shadow 120ms ease;
      }
      .sales-console-inquiry-suggestion:hover,
      .sales-console-inquiry-suggestion.is-active {
        border-color: #d7e6e2;
        background: #f8fbff;
        box-shadow: 0 10px 22px rgba(15, 23, 42, 0.07);
      }
      .sales-console-inquiry-suggestion-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-height: 24px;
        padding: 0 10px;
        border-radius: 999px;
        border: 1px solid #dbe4ee;
        background: #f8fafc;
        font-size: 10.5px;
        font-weight: 700;
        letter-spacing: 0.03em;
        color: #334155;
        white-space: nowrap;
      }
      .sales-console-inquiry-suggestion-copy {
        display: grid;
        gap: 3px;
        min-width: 0;
      }
      .sales-console-inquiry-suggestion-title {
        font-size: 12.75px;
        font-weight: 700;
        color: #0f172a;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      .sales-console-inquiry-suggestion-meta {
        font-size: 11.5px;
        line-height: 1.45;
        color: #64748b;
      }
      .sales-console-inquiry-submit,
      .sales-console-inquiry-clear,
      .sales-console-inquiry-open-record,
      .sales-console-inquiry-choice,
      .sales-console-related-link {
        appearance: none;
        border: 1px solid rgba(255, 255, 255, 0.94);
        background: #243247;
        color: #f8fafc;
        border-radius: 12px;
        height: 44px;
        padding: 0 16px;
        font-size: 12.5px;
        font-weight: 700;
        cursor: pointer;
        box-shadow:
          0 1px 0 rgba(255, 255, 255, 0.08) inset,
          0 10px 20px rgba(15, 23, 42, 0.14);
      }
      .sales-console-inquiry-submit:hover,
      .sales-console-inquiry-clear:hover,
      .sales-console-inquiry-open-record:hover,
      .sales-console-related-link:hover {
        background: #2d3d56;
      }
      .sales-console-inquiry-submit.is-busy,
      .sales-console-inquiry-submit:disabled {
        background: #94a3b8;
        border-color: #cbd5e1;
        color: #f8fafc;
        cursor: wait;
        box-shadow: 0 8px 18px rgba(15, 23, 42, 0.08);
      }
      .sales-console-inquiry-submit.is-busy:hover,
      .sales-console-inquiry-submit:disabled:hover {
        background: #94a3b8;
      }
      .sales-console-inquiry-clear {
        border-color: #dbe4ee;
        background: #ffffff;
        color: #243247;
        box-shadow: 0 8px 18px rgba(15, 23, 42, 0.06);
      }
      .sales-console-inquiry-clear:hover {
        background: #f8fafc;
      }
      .sales-console-inquiry-open-record {
        height: 40px;
        padding: 0 14px;
      }
      .sales-console-inquiry-status {
        font-size: 12px;
        color: #64748b;
      }
      .sales-console-inquiry-result {
        display: grid;
        gap: 12px;
      }
      .sales-console-inquiry-result[hidden] {
        display: none;
      }
      .sales-console-inquiry-assist {
        display: grid;
        gap: 12px;
      }
      .sales-console-inquiry-assist[hidden] {
        display: none;
      }
      .sales-console-inquiry-assist-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        flex-wrap: wrap;
      }
      .sales-console-inquiry-assist-copy {
        display: grid;
        gap: 4px;
      }
      .sales-console-inquiry-assist-title {
        margin: 0;
        font-size: 14px;
        font-weight: 700;
        color: #0f172a;
      }
      .sales-console-inquiry-assist-status {
        font-size: 12px;
        color: #64748b;
      }
      .sales-console-inquiry-assist-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 10px;
      }
      .sales-console-inquiry-assist-card {
        display: grid;
        gap: 6px;
        min-width: 0;
        padding: 12px 13px;
        border-radius: 14px;
        border: 1px solid #edf2f7;
        background: #f8fafc;
      }
      .sales-console-inquiry-assist-card-title {
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: #0b84a5;
      }
      .sales-console-inquiry-assist-card-value {
        font-size: 12.5px;
        line-height: 1.55;
        color: #334155;
        white-space: pre-wrap;
      }
      .sales-console-inquiry-assist-footnote {
        font-size: 11.5px;
        line-height: 1.45;
        color: #64748b;
      }
      .sales-console-inquiry-placeholder {
        padding: 14px 16px;
        border-radius: 14px;
        border: 1px dashed #d9e4ef;
        background: rgba(255, 255, 255, 0.72);
        font-size: 12px;
        line-height: 1.55;
        color: #64748b;
      }
      .sales-console-inquiry-block {
        display: grid;
        gap: 8px;
        padding: 14px 16px;
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.92);
        background: #ffffff;
        box-shadow:
          0 1px 0 rgba(255, 255, 255, 0.98) inset,
          0 8px 20px rgba(15, 23, 42, 0.05);
      }
      .sales-console-inquiry-block-title {
        margin: 0;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: #0b84a5;
      }
      .sales-console-inquiry-primary {
        display: grid;
        gap: 6px;
      }
      .sales-console-inquiry-primary-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        flex-wrap: wrap;
      }
      .sales-console-inquiry-primary-summary {
        display: grid;
        gap: 6px;
        min-width: 0;
      }
      .sales-console-inquiry-primary-label {
        font-size: 16px;
        font-weight: 700;
        color: #0f172a;
      }
      .sales-console-inquiry-primary-meta {
        font-size: 12px;
        color: #64748b;
      }
      .sales-console-inquiry-doc-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: fit-content;
        min-height: 24px;
        padding: 0 10px;
        border-radius: 999px;
        border: 1px solid #dbe4ee;
        background: #f8fafc;
        font-size: 10.5px;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        color: #334155;
        white-space: nowrap;
      }
      .sales-console-inquiry-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 10px;
      }
      .sales-console-inquiry-field {
        display: grid;
        gap: 4px;
        min-width: 0;
      }
      .sales-console-inquiry-field-label {
        font-size: 10.5px;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: #7c8798;
      }
      .sales-console-inquiry-field-value {
        font-size: 13px;
        line-height: 1.45;
        color: #0f172a;
        word-break: break-word;
      }
      .sales-console-inquiry-flow {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 10px;
      }
      .sales-console-inquiry-stage {
        display: grid;
        gap: 8px;
        align-content: start;
        min-width: 0;
        padding: 12px 12px 11px;
        border-radius: 14px;
        border: 1px solid #edf2f7;
        background: #f8fafc;
      }
      .sales-console-inquiry-stage-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
      }
      .sales-console-inquiry-stage-label {
        font-size: 12px;
        font-weight: 700;
        color: #0f172a;
      }
      .sales-console-inquiry-stage-state {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 78px;
        padding: 3px 8px;
        border-radius: 999px;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        background: #eef2f7;
        color: #475569;
      }
      .sales-console-inquiry-stage-items {
        display: grid;
        gap: 6px;
      }
      .sales-console-inquiry-stage-item {
        display: grid;
        gap: 4px;
        padding: 8px 9px;
        border-radius: 10px;
        border: 1px solid #e8edf3;
        background: #ffffff;
      }
      .sales-console-inquiry-stage-item-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
        flex-wrap: wrap;
      }
      .sales-console-inquiry-stage-doc {
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: #7c8798;
      }
      .sales-console-inquiry-stage-name {
        font-size: 12px;
        line-height: 1.45;
        font-weight: 700;
        color: #0f172a;
        word-break: break-word;
      }
      .sales-console-inquiry-stage-meta {
        font-size: 11px;
        line-height: 1.4;
        color: #64748b;
      }
      .sales-console-inquiry-list {
        display: grid;
        gap: 8px;
      }
      .sales-console-inquiry-list-row {
        display: grid;
        grid-template-columns: 150px minmax(0, 1fr);
        gap: 12px;
        align-items: start;
      }
      .sales-console-inquiry-list-label {
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        color: #7c8798;
      }
      .sales-console-inquiry-list-value {
        font-size: 12.5px;
        line-height: 1.5;
        color: #334155;
      }
      .sales-console-inquiry-exception {
        display: grid;
        gap: 4px;
        padding: 10px 12px;
        border-radius: 12px;
        border: 1px solid #edf2f7;
        background: #f8fafc;
      }
      .sales-console-inquiry-exception[data-severity="blocker"] {
        border-color: #dfe5ff;
        background: #f5f7ff;
      }
      .sales-console-inquiry-exception[data-severity="attention"] {
        border-color: #d8f0f3;
        background: #f1fcfd;
      }
      .sales-console-inquiry-exception-label {
        font-size: 12px;
        font-weight: 700;
        color: #0f172a;
      }
      .sales-console-inquiry-exception-detail {
        font-size: 12px;
        line-height: 1.45;
        color: #475569;
      }
      .sales-console-inquiry-choices,
      .sales-console-related-links {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 8px;
      }
      .sales-console-inquiry-choice,
      .sales-console-related-link {
        height: auto;
        min-height: 38px;
        padding: 10px 12px;
      }
      .sales-console-inquiry-choice {
        background: #ffffff;
        color: #243247;
        border-color: #dbe4ee;
        box-shadow: 0 8px 18px rgba(15, 23, 42, 0.06);
        display: grid;
        gap: 4px;
        text-align: left;
        align-content: start;
        min-width: 220px;
      }
      .sales-console-inquiry-choice-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: fit-content;
        min-height: 22px;
        padding: 0 9px;
        border-radius: 999px;
        border: 1px solid #dbe4ee;
        background: #f8fafc;
        font-size: 10.5px;
        font-weight: 700;
        letter-spacing: 0.03em;
        color: #334155;
      }
      .sales-console-inquiry-choice-meta {
        font-size: 11px;
        color: #64748b;
      }
      .sales-console-inquiry-choice:hover {
        background: #f8fbff;
        border-color: #d7e6e2;
      }
      .sales-console-related-link {
        position: relative;
        border-color: #dbe4ee;
        background: var(--erpw-surface-panel, #ffffff);
        color: #243247;
        box-shadow: var(
          --erpw-shadow-panel,
          0 1px 0 rgba(255, 255, 255, 0.98) inset,
          0 8px 18px rgba(15, 23, 42, 0.03)
        );
        display: grid;
        gap: 5px;
        text-align: left;
        align-content: start;
        min-width: 0;
        padding-right: 44px;
      }
      .sales-console-related-link::after {
        content: "";
        position: absolute;
        top: 50%;
        right: 16px;
        width: 8px;
        height: 8px;
        border-top: 1.5px solid #94a3b8;
        border-right: 1.5px solid #94a3b8;
        transform: translateY(-50%) rotate(45deg);
        transition: border-color 120ms ease, transform 120ms ease;
      }
      .sales-console-related-link:hover {
        background: var(--erpw-surface-panel, #ffffff);
        border-color: rgba(153, 246, 228, 0.6);
        box-shadow: var(
          --erpw-shadow-panel-hover,
          0 1px 0 rgba(255, 255, 255, 0.98) inset,
          0 10px 22px rgba(15, 23, 42, 0.048)
        );
      }
      .sales-console-related-link:hover::after {
        border-color: #0f766e;
        transform: translate(1px, -50%) rotate(45deg);
      }
      .sales-console-related-card-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
        flex-wrap: wrap;
      }
      .sales-console-related-card-name {
        font-size: 13px;
        font-weight: 700;
        color: #0f172a;
        word-break: break-word;
      }
      .sales-console-related-card-meta {
        font-size: 11.5px;
        line-height: 1.45;
        color: #64748b;
      }
      .sales-console-queue-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 10px;
      }
      .sales-console-queue-grid[data-section-grid="approvals"] {
        grid-template-columns: 1fr;
      }
      .sales-console-queue-grid[data-section-grid="approvals"] > [data-queue-key]:first-child {
        grid-column: 1 / -1;
      }
      .sales-console-queue-grid[data-section-grid="approvals"] .sales-console-queue-card {
        align-items: center;
      }
      .sales-console-queue-grid[data-section-grid="approvals"] .sales-console-queue-card.regular {
        grid-template-columns: minmax(0, 1fr) 122px;
        gap: 20px;
        min-height: 122px;
        padding: 22px 22px 20px;
      }
      .sales-console-queue-grid[data-section-grid="approvals"] .sales-console-queue-card.regular .sales-console-queue-main {
        padding: 0;
      }
      .sales-console-queue-grid[data-section-grid="approvals"] .sales-console-queue-side,
      .sales-console-queue-grid[data-section-grid="approvals"] .sales-console-queue-priority-side {
        min-width: 122px;
        width: 122px;
        padding: 12px 16px;
      }
      .sales-console-queue-grid[data-section-grid="approvals"] .sales-console-queue-count {
        font-size: 24px;
        font-variant-numeric: tabular-nums;
        font-feature-settings: "tnum" 1, "lnum" 1;
      }
      .sales-console-queue-grid[data-section-grid="approvals"] .sales-console-queue-side-label {
        min-width: 7ch;
        text-align: center;
      }
      .sales-console-queue-card {
        position: relative;
        overflow: hidden;
        display: grid;
        gap: 8px;
        padding: 16px 18px;
        border-radius: 18px;
        border: 1px solid var(--erpw-border-strong, rgba(255, 255, 255, 0.92));
        background: var(--erpw-surface-elevated, #ffffff);
        cursor: pointer;
        text-align: left;
        transition: border-color 120ms ease, box-shadow 120ms ease, background 120ms ease;
        min-width: 0;
        min-height: 92px;
        box-shadow: var(
          --erpw-shadow-card,
          0 1px 0 rgba(255, 255, 255, 0.98) inset,
          0 10px 24px rgba(15, 23, 42, 0.04)
        );
      }
      .sales-console-queue-card:hover {
        border-color: rgba(255, 255, 255, 0.98);
        box-shadow: var(
          --erpw-shadow-card-hover,
          0 1px 0 rgba(255, 255, 255, 0.98) inset,
          0 14px 30px rgba(15, 23, 42, 0.07)
        );
      }
      .sales-console-queue-card.priority {
        grid-template-columns: minmax(0, 1fr) auto;
        align-items: center;
        gap: 20px;
        padding: 22px 22px 20px;
        border-color: var(--erpw-border-strong, rgba(255, 255, 255, 0.94));
        background:
          linear-gradient(90deg, rgba(34, 211, 238, 0.03) 0%, rgba(34, 211, 238, 0.01) 18%, rgba(255, 255, 255, 0) 38%),
          var(--erpw-surface-elevated, #ffffff);
        box-shadow: var(
          --erpw-shadow-card,
          0 1px 0 rgba(255, 255, 255, 0.98) inset,
          0 10px 24px rgba(15, 23, 42, 0.04)
        );
        min-height: 122px;
      }
      .sales-console-queue-card.priority:hover {
        border-color: rgba(255, 255, 255, 0.98);
        background:
          linear-gradient(90deg, rgba(34, 211, 238, 0.042) 0%, rgba(34, 211, 238, 0.016) 18%, rgba(255, 255, 255, 0) 38%),
          var(--erpw-surface-elevated, #ffffff);
        box-shadow: var(
          --erpw-shadow-card-hover,
          0 1px 0 rgba(255, 255, 255, 0.98) inset,
          0 14px 30px rgba(15, 23, 42, 0.07)
        );
      }
      .sales-console-queue-card.regular {
        grid-template-columns: minmax(0, 1fr) 112px;
        gap: 18px;
        align-items: stretch;
        min-height: 104px;
        box-shadow:
          inset 3px 0 0 #d8e0ea,
          var(--erpw-shadow-card, 0 1px 0 rgba(255, 255, 255, 0.98) inset, 0 10px 24px rgba(15, 23, 42, 0.04));
      }
      .sales-console-queue-card.regular:hover {
        box-shadow:
          inset 4px 0 0 #c7d4e2,
          var(--erpw-shadow-card-hover, 0 1px 0 rgba(255, 255, 255, 0.98) inset, 0 14px 30px rgba(15, 23, 42, 0.07));
      }
      .sales-console-queue-grid[data-section-grid="work"] .sales-console-queue-card.regular {
        box-shadow:
          inset 3px 0 0 #d0e1de,
          var(--erpw-shadow-card, 0 1px 0 rgba(255, 255, 255, 0.98) inset, 0 10px 24px rgba(15, 23, 42, 0.04));
      }
      .sales-console-queue-grid[data-section-grid="work"] .sales-console-queue-card.regular:hover {
        box-shadow:
          inset 4px 0 0 #bdd8d2,
          var(--erpw-shadow-card-hover, 0 1px 0 rgba(255, 255, 255, 0.98) inset, 0 14px 30px rgba(15, 23, 42, 0.07));
      }
      .sales-console-queue-grid[data-section-grid="lifecycle"] .sales-console-queue-card.regular {
        box-shadow:
          inset 3px 0 0 #d7e1ef,
          var(--erpw-shadow-card, 0 1px 0 rgba(255, 255, 255, 0.98) inset, 0 10px 24px rgba(15, 23, 42, 0.04));
      }
      .sales-console-queue-grid[data-section-grid="lifecycle"] .sales-console-queue-card.regular:hover {
        box-shadow:
          inset 4px 0 0 #c7d6e8,
          var(--erpw-shadow-card-hover, 0 1px 0 rgba(255, 255, 255, 0.98) inset, 0 14px 30px rgba(15, 23, 42, 0.07));
      }
      .sales-console-queue-main {
        display: grid;
        grid-template-rows: auto 1fr;
        gap: 8px;
        min-width: 0;
        align-content: start;
      }
      .sales-console-queue-card.regular .sales-console-queue-main {
        padding: 6px 0 4px 2px;
      }
      .sales-console-queue-side {
        display: grid;
        justify-items: center;
        align-content: center;
        gap: 5px;
        min-width: 112px;
        padding: 13px 16px;
        border-radius: 14px;
        border: 1px solid var(--erpw-border-strong, rgba(255, 255, 255, 0.92));
        background: var(--erpw-surface-panel, linear-gradient(135deg, #f8fafc 0%, #ffffff 100%));
        box-shadow: var(
          --erpw-shadow-panel,
          0 1px 0 rgba(255, 255, 255, 0.98) inset,
          0 8px 18px rgba(15, 23, 42, 0.03)
        );
      }
      .sales-console-queue-grid[data-section-grid="work"] .sales-console-queue-side {
        border-color: #dbe8e4;
        background: #f7fbfb;
      }
      .sales-console-queue-grid[data-section-grid="lifecycle"] .sales-console-queue-side {
        border-color: #dde6f0;
        background: #f8fbfd;
      }
      .sales-console-queue-card.priority::before {
        content: "";
        position: absolute;
        left: 0;
        top: 14px;
        bottom: 14px;
        width: 4px;
        border-radius: 0 999px 999px 0;
        background: linear-gradient(180deg, #06b6d4 0%, #22d3ee 100%);
        transition: top 120ms ease, bottom 120ms ease, width 120ms ease, box-shadow 120ms ease;
      }
      .sales-console-queue-card.priority:hover::before {
        top: 13px;
        bottom: 13px;
        width: 5px;
        box-shadow: 0 0 0 1px rgba(34, 211, 238, 0.05);
      }
      .sales-console-queue-priority-main {
        display: grid;
        gap: 8px;
      }
      .sales-console-queue-priority-side {
        display: grid;
        justify-items: center;
        align-content: center;
        gap: 4px;
        min-width: 122px;
        padding: 12px 16px;
        border-radius: 14px;
        border: 1px solid var(--erpw-border-strong, rgba(255, 255, 255, 0.94));
        background: var(--erpw-surface-panel, linear-gradient(135deg, #f8fafc 0%, #ffffff 100%));
        box-shadow: var(
          --erpw-shadow-panel,
          0 1px 0 rgba(255, 255, 255, 0.98) inset,
          0 8px 18px rgba(15, 23, 42, 0.03)
        );
      }
      .sales-console-queue-topline {
        display: flex;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
        min-width: 0;
      }
      .sales-console-queue-kicker {
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #0b84a5;
      }
      .sales-console-queue-title {
        margin: 0;
        font-size: 13.5px;
        line-height: 1.3;
        font-weight: 700;
        color: #0f172a;
        min-width: 0;
      }
      .sales-console-queue-card.priority .sales-console-queue-title {
        font-size: 14px;
      }
      .sales-console-queue-count {
        flex: 0 0 auto;
        font-size: 20px;
        font-weight: 600;
        line-height: 1;
        color: #0f172a;
        letter-spacing: -0.02em;
        font-variant-numeric: tabular-nums;
        font-feature-settings: "tnum" 1, "lnum" 1;
      }
      .sales-console-queue-card.priority .sales-console-queue-count {
        font-size: 24px;
      }
      .sales-console-queue-side-label {
        font-size: 10px;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #7c8798;
      }
      .sales-console-queue-meta {
        font-size: 11.5px;
        line-height: 1.42;
        color: #64748b;
        min-height: 0;
      }
      .sales-console-queue-card.regular .sales-console-queue-meta {
        display: -webkit-box;
        max-width: 34ch;
        min-height: 32px;
        overflow: hidden;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
      }
      .sales-console-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 68px;
        padding: 4px 8px;
        border-radius: 999px;
        font-size: 10.5px;
        font-weight: 700;
        white-space: nowrap;
      }
      .sales-console-badge.attention {
        background: #ecfeff;
        color: #0f766e;
      }
      .sales-console-badge.blocker {
        background: #eef2ff;
        color: #4338ca;
      }
      .sales-console-badge.review {
        background: #eff6ff;
        color: #1d4ed8;
      }
      .sales-console-badge.pending {
        background: #f8fafc;
        color: #475569;
      }
      .sales-console-badge.restricted {
        background: #f1f5f9;
        color: #334155;
      }
      .sales-console-report-links {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 12px;
      }
      .sales-console-link {
        position: relative;
        overflow: hidden;
        display: grid;
        grid-template-columns: 42px minmax(0, 1fr) auto;
        align-items: center;
        gap: 14px;
        width: 100%;
        text-align: left;
        padding: 15px 18px;
        min-height: 96px;
        border-radius: 16px;
        border: 1px solid #e6edf5;
        background: #fcfdff;
        cursor: pointer;
        transition: border-color 120ms ease, background 120ms ease, box-shadow 120ms ease, transform 120ms ease;
        min-width: 0;
        box-shadow: var(
          --erpw-shadow-card-quiet,
          0 1px 0 rgba(255, 255, 255, 0.98) inset,
          0 8px 18px rgba(15, 23, 42, 0.028)
        );
      }
      .sales-console-link::before {
        content: "";
        position: absolute;
        top: 0;
        left: 18px;
        width: 34px;
        height: 3px;
        border-radius: 999px;
        background: #c7e5de;
      }
      .sales-console-link:hover {
        border-color: #d8e3ee;
        background: #ffffff;
        box-shadow: var(
          --erpw-shadow-card,
          0 1px 0 rgba(255, 255, 255, 0.98) inset,
          0 10px 24px rgba(15, 23, 42, 0.04)
        );
      }
      .sales-console-action.is-pending,
      .sales-console-queue-card.is-pending,
      .sales-console-link.is-pending {
        opacity: 0.74;
        cursor: progress;
        pointer-events: none;
        box-shadow: 0 1px 0 rgba(255, 255, 255, 0.98) inset, 0 6px 14px rgba(15, 23, 42, 0.03);
      }
      .sales-console-action.is-pending .sales-console-action-meta,
      .sales-console-queue-card.is-pending .sales-console-queue-meta,
      .sales-console-link.is-pending .sales-console-link-meta {
        color: #475569;
      }
      .sales-console-link-icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 42px;
        height: 42px;
        border-radius: 11px;
        border: 1px solid var(--erpw-icon-dark-border, #3a4b65);
        background: var(--erpw-icon-dark-bg, #2d3d56);
        color: #f8fafc;
        font-size: 11px;
        font-weight: 700;
        box-shadow:
          0 1px 0 rgba(255, 255, 255, 0.08) inset,
          0 9px 18px rgba(15, 23, 42, 0.145);
      }
      .sales-console-link-copy {
        display: grid;
        gap: 4px;
        min-width: 0;
      }
      .sales-console-link-title {
        margin: 0 0 4px;
        font-size: 13.5px;
        font-weight: 700;
        color: #0f172a;
      }
      .sales-console-link-meta {
        font-size: 11.5px;
        line-height: 1.42;
        color: #64748b;
      }
      .sales-console-link .sales-console-badge.review {
        min-width: 64px;
        min-height: 32px;
        padding: 0 12px;
        border: 1px solid #d9e3ee;
        background: #f8fbff;
        color: #2a3850;
        box-shadow: 0 1px 0 rgba(255, 255, 255, 0.98) inset;
      }
      .sales-console-sidebar-guide {
        margin-top: 10px;
      }
      .sales-console-sidebar-guide-button {
        appearance: none;
        text-align: left;
        width: 100%;
        display: inline-flex;
        align-items: center;
        gap: 10px;
        padding: 10px 12px;
        border-radius: 10px;
        border: 1px solid transparent;
        background: transparent;
        color: #334155;
        font-size: 13px;
        font-weight: 600;
        cursor: pointer;
      }
      .sales-console-sidebar-guide-button:hover {
        border-color: #cfe7e3;
        background: #f2fbf9;
        color: #0f172a;
      }
      .sales-console-sidebar-guide-mark {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 18px;
        height: 18px;
        color: #64748b;
      }
      .sales-console-guide-dialog {
        display: grid;
        gap: 16px;
      }
      .sales-console-guide-block {
        display: grid;
        gap: 8px;
      }
      .sales-console-guide-heading {
        margin: 0;
        font-size: 14px;
        font-weight: 700;
        color: #0f172a;
      }
      .sales-console-guide-copy {
        font-size: 13px;
        line-height: 1.6;
        color: #475569;
      }
      .sales-console-guide-list {
        margin: 0;
        padding-left: 18px;
        color: #475569;
        font-size: 13px;
        line-height: 1.6;
      }
      .sales-console-guide-list li + li {
        margin-top: 4px;
      }
      @media (max-width: 980px) {
        .sales-console-queue-grid {
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }
        .sales-console-report-links {
          grid-template-columns: 1fr;
        }
        .sales-console-inquiry-grid,
        .sales-console-inquiry-flow {
          grid-template-columns: 1fr 1fr;
        }
        .sales-console-inquiry-assist-grid {
          grid-template-columns: 1fr;
        }
        .sales-console-section-note {
          max-width: 200px;
        }
        .sales-console-action-strip.primary {
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }
        .sales-console-action-strip.primary > :first-child {
          grid-column: 1 / -1;
        }
      }
      @media (max-width: 720px) {
        .sales-console-title {
          font-size: 28px;
        }
        .sales-console-header-row {
          grid-template-columns: 1fr;
        }
        .sales-console-header-context {
          justify-items: start;
          text-align: left;
        }
        .sales-console-section-head {
          align-items: flex-start;
        }
        .sales-console-action-strip.primary,
        .sales-console-action-strip.secondary,
        .sales-console-queue-grid,
        .sales-console-kpi-grid,
        .sales-console-inquiry-grid,
        .sales-console-inquiry-flow,
        .sales-console-inquiry-assist-grid,
        .sales-console-inquiry-form {
          grid-template-columns: 1fr;
        }
        .sales-console-inquiry-actions {
          display: grid;
          grid-template-columns: 1fr 1fr;
        }
        .sales-console-inquiry-suggestions {
          position: static;
        }
        .sales-console-kpi-grid {
          max-width: none;
        }
        .sales-console-kpi-card + .sales-console-kpi-card {
          border-left: none;
          border-top: 1px solid rgba(255, 255, 255, 0.09);
        }
        .sales-console-queue-grid[data-section-grid="approvals"] > [data-queue-key]:first-child {
          grid-column: auto;
        }
        .sales-console-action,
        .sales-console-link,
        .sales-console-queue-card.priority {
          grid-template-columns: 1fr;
        }
        .sales-console-queue-card.regular {
          grid-template-columns: 1fr;
        }
        .sales-console-queue-side {
          justify-items: start;
          min-width: 0;
        }
        .sales-console-queue-topline {
          align-items: flex-start;
        }
        .sales-console-action-icon,
        .sales-console-link-icon {
          width: 36px;
          height: 36px;
        }
        .sales-console-action {
          min-height: 0;
        }
        .sales-console-queue-priority-side {
          justify-items: start;
        }
        .sales-console-section-note {
          max-width: 160px;
        }
        .sales-console-inquiry-list-row {
          grid-template-columns: 1fr;
          gap: 4px;
        }
      }
    `;
    document.head.appendChild(style);
  }

  function escapeHtml(value) {
    return frappe.utils.escape_html(String(value == null ? "" : value));
  }

  function routeToList(doctype, filters) {
    try {
      frappe.route_options = filters && Object.keys(filters).length ? filters : null;
      frappe.set_route("List", doctype);
    } catch (error) {
      frappe.msgprint({
        title: __("Navigation unavailable"),
        message: __("Could not open {0}.", [doctype]),
        indicator: "orange",
      });
    }
  }

  function routeToReport(reportName, filters) {
    try {
      frappe.route_options = filters && Object.keys(filters).length ? filters : null;
      frappe.set_route("query-report", reportName);
    } catch (error) {
      frappe.msgprint({
        title: __("Report unavailable"),
        message: __("Could not open {0}.", [reportName]),
        indicator: "orange",
      });
    }
  }

  function routeToReportPage(reportKey) {
    try {
      frappe.set_route("sales-console-report", String(reportKey || "").replace(/_/g, "-"));
    } catch (error) {
      frappe.msgprint({
        title: __("Report unavailable"),
        message: __("Could not open the Sales Console report."),
        indicator: "orange",
      });
    }
  }

  function routeToWorklist(queueKey) {
    try {
      frappe.set_route("sales-console-worklist", String(queueKey || "").replace(/_/g, "-"));
    } catch (error) {
      frappe.msgprint({
        title: __("Worklist unavailable"),
        message: __("Could not open the Sales Console worklist."),
        indicator: "orange",
      });
    }
  }

  function executeTarget(target, fallback) {
    if (!target) {
      if (typeof fallback === "function") fallback();
      return;
    }

    if (target.notice) {
      frappe.show_alert({
        message: __(target.notice),
        indicator: "blue",
      });
    }

    const routeOwner = window.erpWorkspaceUiChildPage && window.erpWorkspaceUiChildPage.helpers;
    if (
      routeOwner
      && typeof routeOwner.routeToSalesConsoleTarget === "function"
      && routeOwner.routeToSalesConsoleTarget(target)
    ) {
      return;
    }

    if (target.kind === "new_doc" && target.doctype) {
      frappe.new_doc(target.doctype);
      return;
    }

    if (target.kind === "form" && target.doctype && target.name) {
      frappe.set_route("Form", target.doctype, target.name);
      return;
    }

    if (target.kind === "list" && target.doctype) {
      routeToList(target.doctype, target.filters || null);
      return;
    }

    if (target.kind === "report_page" && target.report_key) {
      routeToReportPage(target.report_key);
      return;
    }

    if (target.kind === "report" && target.report_name) {
      routeToReport(target.report_name, target.filters || null);
      return;
    }

    if (target.kind === "worklist" && target.queue_key) {
      routeToWorklist(target.queue_key);
      return;
    }

    if (typeof fallback === "function") fallback();
  }

  function runNavigation(pageState, group, key, fallback) {
    if (group === "actions" && key === "open_customer") {
      routeToWorklist("customer_directory");
      return;
    }
    if (group === "actions" && key === "open_item") {
      routeToWorklist("item_directory");
      return;
    }
    const navigation = (pageState && pageState.payload && pageState.payload.navigation) || {};
    const groupTargets = navigation[group] || {};
    executeTarget(groupTargets[key], fallback);
  }

  function bindConsoleNavigationDelegates($root, pageState) {
    if (!$root || !$root.length) return;

    const actionFallbacks = {
      new_quotation: () => frappe.new_doc("Quotation"),
      new_sales_order: () => frappe.new_doc("Sales Order"),
      open_customer: () => routeToWorklist("customer_directory"),
      open_item: () => routeToWorklist("item_directory"),
    };

    $root.off(".salesConsoleActions");
    $root.on("click.salesConsoleActions", "[data-action-key]", function (event) {
      event.preventDefault();
      event.stopPropagation();
      const key = this.getAttribute("data-action-key");
      if (!key) return;
      runNavigation(pageState, "actions", key, actionFallbacks[key]);
    });
  }

  function makeAction(config) {
    return getConsoleRuntimeMethod("makeAction")(config);
  }

  function makeQueueItem(config) {
    return getConsoleRuntimeMethod("makeQueueItem")(config);
  }

  function makeInsightCard(config) {
    return getConsoleRuntimeMethod("makeInsightCard")(config);
  }

  function applyHeaderContent($root, payload) {
    const profile = (payload && payload.ui_profile) || {};
    const note = String(
      profile.summary_note
      || ((payload && payload.scope) || {}).scope_label
      || "Use Sales Console as the daily starting point for commercial execution, inquiry handling, and controlled review."
    ).trim();
    $root.find("[data-header-note]").text(note);
  }

  function makeReportLink(key, title, meta, icon, onClick) {
    return getConsoleRuntimeMethod("makeReportLink")(key, title, meta, icon, onClick);
  }

  function renderReportsSection($root, pageState, reportCards) {
    return getConsoleRuntimeMethod("renderReportsSection")($root, reportCards, {
      onSelect: (card) => runNavigation(
        pageState,
        "reports",
        card.key,
        () => routeToReportCardFallback(card)
      ),
    });
  }

  function productizedReportKeys() {
    return new Set([
      "sales_analytics",
      "sales_order_analysis",
      "trend_analysis",
      "quotation_trends",
      "collections_status",
      "payment_terms_status_sales_order",
      "item_wise_sales_history",
      "lost_quotations",
    ]);
  }

  function routeToReportCardFallback(card) {
    const key = String((card && (card.report_key || card.key)) || "");
    if (productizedReportKeys().has(key)) {
      routeToReportPage(key);
      return;
    }
    routeToReport(card && card.report_name);
  }

  function defaultReportCardsForCurrentRole() {
    const roles = Array.isArray(frappe.user_roles) ? frappe.user_roles : [];
    const isManager = roles.includes("Sales Manager") || roles.includes("System Manager");
    const cards = isManager
      ? [
          ["sales_analytics", "Sales Analytics", "Sales Analytics", "Management and team performance review", "chart"],
          ["sales_order_analysis", "Sales Order Analysis", "Sales Order Analysis", "Review operational order execution and exception patterns", "order"],
          ["trend_analysis", "Trend Analysis", "Trend Analysis", "Compare billed, ordered, and quoted commercial movement in one trend view", "chart"],
          ["lost_quotations", "Lost Quotations", "Lost Quotations", "Review commercial loss patterns and follow-up quality", "quotation"],
          ["collections_status", "Collections Status", "Collections Status", "Review actual collections exposure and overdue invoice reality", "chart"],
          ["item_wise_sales_history", "Item-wise Sales History", "Item-wise Sales History", "Item-level commercial history for deeper review", "item"],
        ]
      : [
          ["trend_analysis", "Trend Analysis", "Trend Analysis", "Review invoice, order, and quotation movement from one controlled trend view", "chart"],
          ["sales_order_analysis", "Sales Order Analysis", "Sales Order Analysis", "Review order execution quality and operational follow-through", "order"],
          ["collections_status", "Collections Status", "Collections Status", "Review actual receivable exposure and invoice settlement without leaving sales context", "chart"],
          ["item_wise_sales_history", "Item-wise Sales History", "Item-wise Sales History", "Check product-level sales history when speaking with customers", "item"],
        ];

    return cards.map(([key, report_name, title, meta, icon]) => ({
      key,
      report_key: key,
      report_name,
      title,
      meta,
      icon,
    }));
  }

  function fallbackReportCards(payload) {
    const targets = (payload && payload.navigation && payload.navigation.reports) || {};
    const titleMap = {
      sales_analytics: { title: "Sales Analytics", meta: "Management and team performance review", icon: "chart" },
      sales_order_analysis: { title: "Sales Order Analysis", meta: "Review operational order execution and exception patterns", icon: "order" },
      trend_analysis: { title: "Trend Analysis", meta: "Compare billed, ordered, and quoted commercial movement in one trend view", icon: "chart" },
      sales_order_trends: { title: "Sales Order Trends", meta: "Review directional order movement over time", icon: "order" },
      quotation_trends: { title: "Trend Analysis", meta: "Review quotation movement through the unified trend view", icon: "chart" },
      lost_quotations: { title: "Lost Quotations", meta: "Review commercial loss patterns and follow-up quality", icon: "quotation" },
      payment_terms_status_sales_order: { title: "Payment Terms Status", meta: "Check sales-order payment schedule exposure", icon: "chart" },
      item_wise_sales_history: { title: "Item-wise Sales History", meta: "Item-level commercial history for deeper review", icon: "item" },
    };

    const cards = Object.entries(targets).map(([key, target]) => ({
      key,
      report_name: target.report_name,
      title: (titleMap[key] && titleMap[key].title) || target.report_name || key,
      meta: (titleMap[key] && titleMap[key].meta) || "Review target from live ERP",
      icon: (titleMap[key] && titleMap[key].icon) || "chart",
    })).filter(card => card.report_name);
    return cards.length ? cards : defaultReportCardsForCurrentRole();
  }

  function renderInquiryPlaceholder($target, message) {
    $target.html(`
      <div class="sales-console-inquiry-placeholder">
        ${escapeHtml(message)}
      </div>
    `).removeAttr("hidden");
  }

  function stageStateLabel(state) {
    const labels = {
      present: "Present",
      not_yet_created: "Not Yet Created",
      not_used: "Not Used",
      not_applicable: "Not Applicable",
      settled: "Settled",
      partly_settled: "Partly Settled",
      follow_up: "Follow Up",
      unknown: "Unknown",
    };
    return labels[state] || "Unknown";
  }

  function renderInquiryResult($target, result) {
    if (!result || result.state !== "resolved") {
      renderInquiryPlaceholder($target, "No inquiry result is available.");
      return;
    }

    const primary = result.primary_match || {};
    const customer = result.customer_summary || {};
    const flow = Array.isArray(result.document_flow) ? result.document_flow : [];
    const statusRows = Array.isArray(result.current_status) ? result.current_status : [];
    const exceptions = Array.isArray(result.exceptions) ? result.exceptions : [];
    const related = Array.isArray(result.related_documents) ? result.related_documents : [];
    const latestDocs = Array.isArray(customer.latest_documents) ? customer.latest_documents.filter(Boolean) : [];

    const latestDocsHtml = latestDocs.map((item) => `
      <div class="sales-console-inquiry-field">
        <div class="sales-console-inquiry-field-label">${escapeHtml(item.doctype || "Document")}</div>
        <div class="sales-console-inquiry-field-value">${escapeHtml(item.name ? `${item.name}${item.status ? ` (${item.status})` : ""}` : latestDocEmptyText(item.doctype))}</div>
      </div>
    `).join("");

    const flowHtml = flow.map((stage) => `
      <div class="sales-console-inquiry-stage">
        <div class="sales-console-inquiry-stage-head">
          <div class="sales-console-inquiry-stage-label">${escapeHtml(stage.label || "Stage")}</div>
          <div class="sales-console-inquiry-stage-state">${escapeHtml(stageStateLabel(stage.state))}</div>
        </div>
        <div class="sales-console-inquiry-stage-items">
          ${(Array.isArray(stage.items) && stage.items.length ? stage.items : [{ name: stageEmptyText(stage), status: "" }]).map((item) => `
            <div class="sales-console-inquiry-stage-item">
              <div class="sales-console-inquiry-stage-item-head">
                <span class="sales-console-inquiry-stage-doc">${escapeHtml(item.doctype || stage.label || "Record")}</span>
              </div>
              <div class="sales-console-inquiry-stage-name">${escapeHtml(item.name || stageEmptyText(stage))}</div>
              ${item.status ? `<div class="sales-console-inquiry-stage-meta">${escapeHtml(item.status)}</div>` : ""}
            </div>
          `).join("")}
        </div>
      </div>
    `).join("");

    const statusHtml = statusRows.map((item) => `
      <div class="sales-console-inquiry-list-row">
        <div class="sales-console-inquiry-list-label">${escapeHtml(item.label || "Status")}</div>
        <div class="sales-console-inquiry-list-value">${escapeHtml(item.value || "--")}</div>
      </div>
    `).join("");

    const exceptionsHtml = exceptions.length
      ? exceptions.map((item) => `
          <div class="sales-console-inquiry-exception" data-severity="${escapeHtml(item.severity || "review")}">
            <div class="sales-console-inquiry-exception-label">${escapeHtml(item.label || "Exception")}</div>
            <div class="sales-console-inquiry-exception-detail">${escapeHtml(item.detail || "")}</div>
          </div>
        `).join("")
      : `<div class="sales-console-inquiry-placeholder">No active commercial exception is visible in the linked chain.</div>`;

    const relatedHtml = related.length
      ? related.map((item) => `
          <button class="sales-console-related-link" type="button" data-related-doctype="${escapeHtml(item.doctype)}" data-related-name="${escapeHtml(item.name)}">
            <div class="sales-console-related-card-head">
              <span class="sales-console-inquiry-choice-badge">${escapeHtml(item.doctype || "Record")}</span>
            </div>
            <div class="sales-console-related-card-name">${escapeHtml(item.name || item.label || "Unnamed record")}</div>
            <div class="sales-console-related-card-meta">${escapeHtml(item.status || "Visible record")}</div>
          </button>
        `).join("")
      : `<div class="sales-console-inquiry-placeholder">No other linked records are visible in this chain.</div>`;

    $target.html(`
      <div class="sales-console-inquiry-block">
        <div class="sales-console-inquiry-block-title">Primary Match</div>
        <div class="sales-console-inquiry-primary">
          <div class="sales-console-inquiry-primary-head">
            <div class="sales-console-inquiry-primary-summary">
              <span class="sales-console-inquiry-doc-badge">${escapeHtml(primary.doctype || "Record")}</span>
              <div class="sales-console-inquiry-primary-label">${escapeHtml(primary.name || "Unnamed record")}</div>
            </div>
            <button
              class="sales-console-inquiry-open-record"
              type="button"
              data-primary-doctype="${escapeHtml(primary.doctype || "")}"
              data-primary-name="${escapeHtml(primary.name || "")}"
            >Open record</button>
          </div>
          <div class="sales-console-inquiry-primary-meta">${escapeHtml(primary.customer || "Customer context not available")}</div>
          <div class="sales-console-inquiry-choice-meta">${escapeHtml(primary.status || "Visible")}</div>
        </div>
      </div>
      <div class="sales-console-inquiry-block">
        <div class="sales-console-inquiry-block-title">Customer Summary</div>
        <div class="sales-console-inquiry-grid">
          <div class="sales-console-inquiry-field">
            <div class="sales-console-inquiry-field-label">Customer</div>
            <div class="sales-console-inquiry-field-value">${escapeHtml(customer.name || primary.customer || "Unknown")}</div>
          </div>
          <div class="sales-console-inquiry-field">
            <div class="sales-console-inquiry-field-label">Customer ID</div>
            <div class="sales-console-inquiry-field-value">${escapeHtml(customer.customer_id || "--")}</div>
          </div>
          <div class="sales-console-inquiry-field">
            <div class="sales-console-inquiry-field-label">Territory</div>
            <div class="sales-console-inquiry-field-value">${escapeHtml(customer.territory || "Not set")}</div>
          </div>
          <div class="sales-console-inquiry-field">
            <div class="sales-console-inquiry-field-label">Contact</div>
            <div class="sales-console-inquiry-field-value">${escapeHtml(customer.contact || "Not available")}</div>
          </div>
          ${latestDocsHtml}
        </div>
      </div>
      <div class="sales-console-inquiry-block">
        <div class="sales-console-inquiry-block-title">Document Flow</div>
        <div class="sales-console-inquiry-flow">${flowHtml}</div>
      </div>
      <div class="sales-console-inquiry-block">
        <div class="sales-console-inquiry-block-title">Current Status</div>
        <div class="sales-console-inquiry-list">${statusHtml}</div>
      </div>
      <div class="sales-console-inquiry-block">
        <div class="sales-console-inquiry-block-title">Exceptions / Blockers</div>
        <div class="sales-console-inquiry-list">${exceptionsHtml}</div>
      </div>
      <div class="sales-console-inquiry-block">
        <div class="sales-console-inquiry-block-title">Open Related Records</div>
        <div class="sales-console-related-links">${relatedHtml}</div>
      </div>
    `).removeAttr("hidden");

    $target.find("[data-primary-doctype]").on("click", function () {
      executeTarget({
        kind: "form",
        doctype: this.getAttribute("data-primary-doctype"),
        name: this.getAttribute("data-primary-name"),
      });
    });
    $target.find("[data-related-doctype]").on("click", function () {
      executeTarget({
        kind: "form",
        doctype: this.getAttribute("data-related-doctype"),
        name: this.getAttribute("data-related-name"),
      });
    });
  }

  function latestDocEmptyText(doctype) {
    const labels = {
      Quotation: "No quotation linked to this chain",
      "Sales Order": "No sales order linked to this chain",
      "Sales Invoice": "No invoice linked to this chain",
    };
    return labels[doctype] || "No linked record in this chain";
  }

  function stageEmptyText(stage) {
    const label = stage && stage.label ? String(stage.label) : "Record";
    const state = stage && stage.state ? String(stage.state) : "";
    if (state === "unknown") return `${label} visibility is limited in this chain`;
    if (label === "Quotation" && state === "not_yet_created") return "Quotation has not been created in this chain yet";
    if (label === "Sales Order" && state === "not_yet_created") return "Sales order has not been created in this chain yet";
    if (label === "Delivery" && state === "not_yet_created") return "Delivery has not been created in this chain yet";
    if (label === "Sales Invoice" && state === "not_yet_created") return "Invoice has not been created in this chain yet";
    if (label === "Sales Return" && state === "not_applicable") return "Sales return becomes relevant after delivery or invoicing";
    if (label === "Payment" && state === "not_applicable") return "Payment becomes relevant after invoicing";
    const defaults = {
      Quotation: "No quotation linked to this chain",
      "Sales Order": "No sales order linked to this chain",
      Delivery: "No delivery linked to this chain",
      "Sales Invoice": "No invoice linked to this chain",
      Payment: "No payment activity linked to this chain",
      "Sales Return": "No sales return linked to this chain",
    };
    return defaults[label] || "No linked record in this chain";
  }

  function renderInquiryChoices($target, result, runSearch) {
    const choices = Array.isArray(result.choices) ? result.choices : [];
    $target.html(`
      <div class="sales-console-inquiry-block">
        <div class="sales-console-inquiry-block-title">Possible Matches</div>
        <div class="sales-console-inquiry-meta">${escapeHtml(result.message || "Choose the correct customer chain.")}</div>
        <div class="sales-console-inquiry-choices">
          ${choices.map((item, index) => `
            <button class="sales-console-inquiry-choice" type="button" data-choice-index="${index}">
              <span class="sales-console-inquiry-choice-badge">${escapeHtml(item.doctype || "Customer")}</span>
              <div>${escapeHtml(item.label || item.name)}</div>
              <div class="sales-console-inquiry-choice-meta">${escapeHtml(item.meta || item.doctype || "Customer")}</div>
            </button>
          `).join("")}
        </div>
      </div>
    `).removeAttr("hidden");

    $target.find("[data-choice-index]").on("click", function () {
      const item = choices[Number(this.getAttribute("data-choice-index"))];
      if (!item) return;
      runSearch({
        query: item.doctype === "Customer" ? (item.label || item.name || "") : (item.name || item.label || ""),
        doctype: item.doctype,
        name: item.name,
      });
    });
  }

  function getInquirySuggestState(pageState) {
    if (!pageState.inquirySuggest) {
      pageState.inquirySuggest = {
        items: [],
        activeIndex: -1,
        requestToken: 0,
        timer: null,
      };
    }
    return pageState.inquirySuggest;
  }

  function clearInquirySuggestionTimer(pageState) {
    const state = getInquirySuggestState(pageState);
    if (state.timer) {
      clearTimeout(state.timer);
      state.timer = null;
    }
  }

  function resetInquirySuggestions(pageState, $section) {
    const state = getInquirySuggestState(pageState);
    clearInquirySuggestionTimer(pageState);
    state.requestToken += 1;
    state.items = [];
    state.activeIndex = -1;
    $section.find("[data-inquiry-suggestions]").empty().attr("hidden", true);
  }

  function setInquirySuggestionActive(pageState, $section, index) {
    const state = getInquirySuggestState(pageState);
    if (!state.items.length) {
      state.activeIndex = -1;
      return;
    }

    const boundedIndex = Math.max(0, Math.min(index, state.items.length - 1));
    state.activeIndex = boundedIndex;
    const $items = $section.find("[data-suggestion-index]");
    $items.removeClass("is-active").attr("aria-selected", "false");
    const $active = $items.filter(`[data-suggestion-index="${boundedIndex}"]`);
    $active.addClass("is-active").attr("aria-selected", "true");
    const activeNode = $active.get(0);
    if (activeNode) {
      activeNode.scrollIntoView({ block: "nearest" });
    }
  }

  function renderInquirySuggestions(pageState, $section, payload) {
    const state = getInquirySuggestState(pageState);
    state.items = Array.isArray(payload && payload.suggestions) ? payload.suggestions : [];
    state.activeIndex = state.items.length ? 0 : -1;

    const $wrap = $section.find("[data-inquiry-suggestions]");
    if (!state.items.length) {
      $wrap.empty().attr("hidden", true);
      return;
    }

    const groups = [];
    state.items.forEach((item, index) => {
      const groupKey = item.doctype || "Match";
      let group = groups.find((entry) => entry.key === groupKey);
      if (!group) {
        group = { key: groupKey, label: groupKey, items: [] };
        groups.push(group);
      }
      group.items.push({ ...item, _index: index });
    });

    $wrap.html(groups.map((group) => `
      <div class="sales-console-inquiry-suggestions-group">
        <div class="sales-console-inquiry-suggestions-label">${escapeHtml(group.label)}</div>
        ${group.items.map((item) => `
          <button
            class="sales-console-inquiry-suggestion${item._index === state.activeIndex ? " is-active" : ""}"
            type="button"
            data-suggestion-index="${item._index}"
            aria-selected="${item._index === state.activeIndex ? "true" : "false"}"
          >
            <span class="sales-console-inquiry-suggestion-badge">${escapeHtml(item.doctype || "Record")}</span>
            <span class="sales-console-inquiry-suggestion-copy">
              <span class="sales-console-inquiry-suggestion-title">${escapeHtml(item.label || item.name || "Unnamed record")}</span>
              <span class="sales-console-inquiry-suggestion-meta">${escapeHtml(item.meta || "")}</span>
            </span>
          </button>
        `).join("")}
      </div>
    `).join("")).removeAttr("hidden");

    $wrap.find("[data-suggestion-index]").on("mouseenter", function () {
      setInquirySuggestionActive(pageState, $section, Number(this.getAttribute("data-suggestion-index")));
    });
    $wrap.find("[data-suggestion-index]").on("mousedown", (event) => {
      event.preventDefault();
    });
    $wrap.find("[data-suggestion-index]").on("click", function () {
      chooseInquirySuggestion(pageState, $section, Number(this.getAttribute("data-suggestion-index")));
    });
  }

  function chooseInquirySuggestion(pageState, $section, index) {
    const state = getInquirySuggestState(pageState);
    const item = state.items[index];
    if (!item) return false;

    const query = item.doctype === "Customer"
      ? (item.label || item.name || "")
      : (item.name || item.label || "");

    $section.find("[data-inquiry-input]").val(query);
    resetInquirySuggestions(pageState, $section);
    runInquirySearch(pageState, $section, {
      query,
      doctype: item.doctype,
      name: item.name,
    });
    return true;
  }

  function maybeSelectActiveInquirySuggestion(pageState, $section) {
    const state = getInquirySuggestState(pageState);
    if (!state.items.length) return false;
    return chooseInquirySuggestion(pageState, $section, state.activeIndex >= 0 ? state.activeIndex : 0);
  }

  async function fetchInquirySuggestions(pageState, $section, query) {
    const state = getInquirySuggestState(pageState);
    const requestToken = state.requestToken + 1;
    state.requestToken = requestToken;

    if (String(query || "").trim().length < 2) {
      resetInquirySuggestions(pageState, $section);
      return;
    }

    try {
      const response = await frappe.call({
        method: INQUIRY_SUGGEST_METHOD,
        args: { query },
      });
      if (requestToken !== getInquirySuggestState(pageState).requestToken) return;

      const payload = response && response.message ? response.message : {};
      if (payload.state === "ready") {
        renderInquirySuggestions(pageState, $section, payload);
        return;
      }
      resetInquirySuggestions(pageState, $section);
    } catch (error) {
      if (requestToken !== getInquirySuggestState(pageState).requestToken) return;
      resetInquirySuggestions(pageState, $section);
    }
  }

  function scheduleInquirySuggestions(pageState, $section) {
    const query = String($section.find("[data-inquiry-input]").val() || "").trim();
    const state = getInquirySuggestState(pageState);
    clearInquirySuggestionTimer(pageState);
    if (query.length < 2) {
      resetInquirySuggestions(pageState, $section);
      return;
    }
    state.timer = setTimeout(() => {
      fetchInquirySuggestions(pageState, $section, query);
    }, 160);
  }

  function resetInquiryAssist($section, message) {
    const $wrap = $section.find("[data-inquiry-ai]");
    const $status = $section.find("[data-inquiry-ai-status]");
    const $content = $section.find("[data-inquiry-ai-content]");
    const $button = $section.find("[data-inquiry-ai-generate]");
    $content.empty();
    $status.text(message || "Generate a concise AI brief after resolving the inquiry.");
    const idleLabel = $button.attr("data-idle-label") || $button.text() || "Generate AI Brief";
    $button.attr("data-idle-label", idleLabel).text(idleLabel).removeClass("is-busy").prop("disabled", true);
    $wrap.attr("hidden", true);
  }

  function resetInquiryView(pageState, $section) {
    pageState.inquiry = null;
    pageState.inquiryAssist = null;
    const $input = $section.find("[data-inquiry-input]");
    $input.val("");
    resetInquirySuggestions(pageState, $section);
    $section.find("[data-inquiry-status]").text("Waiting for inquiry input.");
    $section.find("[data-inquiry-result]").empty().attr("hidden", true);
    resetInquiryAssist($section, "Generate a concise AI brief after resolving the inquiry.");
    $input.trigger("focus");
  }

  function showInquiryAssistReady($section, result) {
    const $wrap = $section.find("[data-inquiry-ai]");
    const $status = $section.find("[data-inquiry-ai-status]");
    const $content = $section.find("[data-inquiry-ai-content]");
    const $button = $section.find("[data-inquiry-ai-generate]");
    const primary = (result && result.primary_match) || {};
    $content.empty();
    $status.text(`Ready to summarize ${primary.doctype || "this chain"} ${primary.name || ""}.`);
    const idleLabel = $button.attr("data-idle-label") || $button.text() || "Generate AI Brief";
    $button.attr("data-idle-label", idleLabel).text(idleLabel).removeClass("is-busy").prop("disabled", false);
    $wrap.removeAttr("hidden");
  }

  function renderInquiryAssist($section, payload) {
    const assist = (payload && payload.assist) || {};
    const source = String((payload && payload.source) || "fallback").trim();
    const engine = String((payload && payload.engine) || (source === "ai" ? "qwen_runtime" : "structured_inquiry_brief")).trim();
    const $wrap = $section.find("[data-inquiry-ai]");
    const $status = $section.find("[data-inquiry-ai-status]");
    const $content = $section.find("[data-inquiry-ai-content]");

    const cards = [
      { title: "Summary", value: assist.summary || "No summary is available." },
      { title: "Blocker Explanation", value: assist.blocker_explanation || "No blocker explanation is available." },
      { title: "Next Action", value: assist.next_action || "No next action is available." },
      { title: "Customer Reply Draft", value: assist.customer_reply || "No customer reply draft is available." },
    ];

    $content.html(`
      <div class="sales-console-inquiry-assist-grid">
        ${cards.map((item) => `
          <div class="sales-console-inquiry-assist-card">
            <div class="sales-console-inquiry-assist-card-title">${escapeHtml(item.title)}</div>
            <div class="sales-console-inquiry-assist-card-value">${escapeHtml(item.value)}</div>
          </div>
        `).join("")}
      </div>
      <div class="sales-console-inquiry-assist-footnote">
        ${escapeHtml(assist.confidence_note || "Generated from the visible ERP inquiry chain.")} (${escapeHtml(source)} via ${escapeHtml(engine)})
      </div>
    `);

    $status.text(source === "ai" ? "AI brief generated from the visible inquiry chain." : "Structured fallback brief generated from the visible inquiry chain.");
    const $button = $section.find("[data-inquiry-ai-generate]");
    const idleLabel = $button.attr("data-idle-label") || "Generate AI Brief";
    $button.text(idleLabel).removeClass("is-busy").prop("disabled", false);
    $wrap.removeAttr("hidden");
  }

  async function runInquiryAssist(pageState, $section) {
    const inquiry = pageState.inquiry || {};
    if (!inquiry || inquiry.state !== "resolved") {
      resetInquiryAssist($section, "Resolve a single customer chain before generating the AI brief.");
      return;
    }

    const $status = $section.find("[data-inquiry-ai-status]");
    const $button = $section.find("[data-inquiry-ai-generate]");
    const idleLabel = $button.attr("data-idle-label") || $button.text() || "Generate AI Brief";
    $button.attr("data-idle-label", idleLabel).text("Generating...").addClass("is-busy").prop("disabled", true);
    $status.text("Generating concise AI brief from the visible inquiry chain...");

    try {
      const response = await frappe.call({
        method: INQUIRY_AI_METHOD,
        args: {
          query: inquiry.query || "",
          doctype: inquiry.anchor && inquiry.anchor.doctype,
          name: inquiry.anchor && inquiry.anchor.name,
        },
      });
      const payload = response && response.message ? response.message : {};
      pageState.inquiryAssist = payload;
      if (payload.state === "ready") {
        renderInquiryAssist($section, payload);
        return;
      }
      $status.text(payload.message || "AI brief is not available for this inquiry.");
      $button.text(idleLabel).removeClass("is-busy").prop("disabled", false);
    } catch (error) {
      $status.text("AI brief is temporarily unavailable.");
      $button.text(idleLabel).removeClass("is-busy").prop("disabled", false);
    }
  }

  async function runInquirySearch(pageState, $section, forcedQuery) {
    const $input = $section.find("[data-inquiry-input]");
    const $status = $section.find("[data-inquiry-status]");
    const $result = $section.find("[data-inquiry-result]");
    const lookup = forcedQuery && typeof forcedQuery === "object" && !Array.isArray(forcedQuery)
      ? forcedQuery
      : null;
    const query = String(
      lookup
        ? (lookup.query != null ? lookup.query : (lookup.name || ""))
        : (forcedQuery != null ? forcedQuery : ($input.val() || ""))
    ).trim();
    const selectedDoctype = lookup && lookup.doctype ? String(lookup.doctype).trim() : null;
    const selectedName = lookup && lookup.name ? String(lookup.name).trim() : null;

    if (!query) {
      renderInquiryPlaceholder($result, "Enter a customer, quotation, sales order, invoice, or delivery reference.");
      $status.text("Waiting for inquiry input.");
      resetInquirySuggestions(pageState, $section);
      resetInquiryAssist($section, "Generate a concise AI brief after resolving the inquiry.");
      return;
    }

    resetInquirySuggestions(pageState, $section);
    $status.text("Searching linked customer and document context...");
    renderInquiryPlaceholder($result, "Resolving the commercial chain...");

    try {
      const response = await frappe.call({
        method: INQUIRY_METHOD,
        args: {
          query,
          doctype: selectedDoctype,
          name: selectedName,
        },
      });
      const result = response && response.message ? response.message : {};
      pageState.inquiry = result;

      if (result.state === "resolved") {
        renderInquiryResult($result, result);
        $status.text(`Showing linked result for ${query}.`);
        showInquiryAssistReady($section, result);
        return;
      }

      if (result.state === "multiple_matches") {
        renderInquiryChoices($result, result, (choiceQuery) => runInquirySearch(pageState, $section, choiceQuery));
        $status.text("Multiple customer matches found.");
        resetInquiryAssist($section, "Choose a single customer chain before generating the AI brief.");
        return;
      }

      renderInquiryPlaceholder($result, result.message || "No inquiry result is available.");
      $status.text(result.message || "No matching customer chain was found.");
      resetInquiryAssist($section, result.message || "AI brief is available only after a visible customer chain is resolved.");
    } catch (error) {
      renderInquiryPlaceholder($result, "Customer inquiry is not available right now.");
      $status.text("Customer inquiry is temporarily unavailable.");
      resetInquiryAssist($section, "AI brief is temporarily unavailable.");
    }
  }

  function iconMarkup(name) {
    return getConsoleRuntimeMethod("iconMarkup")(name);
  }

  function metricValueText(metric) {
    return getConsoleRuntimeMethod("metricValueText")(metric);
  }

  function metricBadge(metric, key) {
    return getConsoleRuntimeMethod("metricBadge")(metric, key);
  }

  function applyQueueMetric($root, key, metric) {
    return getConsoleRuntimeMethod("applyQueueMetric")($root, key, metric);
  }

  function applyInsightMetric($root, key, metric) {
    return getConsoleRuntimeMethod("applyInsightMetric")($root, key, metric);
  }

  function hydrateKnownMetrics($root, payload) {
    return getConsoleRuntimeMethod("hydrateKnownMetrics")($root, payload);
  }

  function reorderChildren($container, order, attributeName) {
    return getConsoleRuntimeMethod("reorderChildren")($container, order, attributeName);
  }

  function applyActionOrder($root, order) {
    return getConsoleRuntimeMethod("applyActionOrder")($root, order);
  }

  function rebalanceActionStrips($root) {
    return getConsoleRuntimeMethod("rebalanceActionStrips")($root);
  }

  function applyUiProfile($root, profile) {
    if (!profile) return;

    if (Array.isArray(profile.action_order)) {
      applyActionOrder($root, profile.action_order);
    }
    if (Array.isArray(profile.queue_order)) {
      reorderChildren($root.find('[data-section-grid="work"]'), profile.queue_order, "data-queue-key");
    }

    const hiddenActions = new Set(profile.hidden_actions || []);
    $root.find("[data-action-key]").each((_, element) => {
      const $element = $(element);
      const key = $element.attr("data-action-key");
      $element.toggle(!hiddenActions.has(key));
    });
    rebalanceActionStrips($root);

    const hiddenInsights = new Set(profile.hidden_insights || []);
    const $kpiCards = $root.find("[data-insight-key]");
    $kpiCards.each((_, element) => {
      const $element = $(element);
      const key = $element.attr("data-insight-key");
      $element.toggle(!hiddenInsights.has(key));
    });
    const visibleInsightCount = $kpiCards.filter((_, element) => $(element).css("display") !== "none").length;
    const $kpiGrid = $root.find(".sales-console-kpi-grid");
    $kpiGrid.css("grid-template-columns", visibleInsightCount <= 1 ? "1fr" : "repeat(2, minmax(0, 1fr))");

    if (profile.section_notes) {
      Object.entries(profile.section_notes).forEach(([key, value]) => {
        $root.find(`[data-section-note="${key}"]`).text(value);
      });
    }

    if (profile.show_reports === false) {
      $root.find('[data-section="reports"]').hide();
    } else {
      $root.find('[data-section="reports"]').show();
    }

    if (Array.isArray(profile.section_order) && profile.section_order.length) {
      reorderChildren($root.find(".sales-console-body"), profile.section_order, "data-section-key");
    }
  }

  function buildGuideHtml(payload) {
    const context = payload.context || {};
    const scope = payload.scope || {};
    const profile = payload.ui_profile || {};

    return `
      <div class="sales-console-guide-dialog">
        <div class="sales-console-guide-block">
          <h3 class="sales-console-guide-heading">What this workspace is for</h3>
          <div class="sales-console-guide-copy">
            Use Sales Console as the daily starting point for quotations, blocked orders, customer follow-up, and lightweight operational review.
          </div>
        </div>
        <div class="sales-console-guide-block">
          <h3 class="sales-console-guide-heading">How to work here</h3>
          <ul class="sales-console-guide-list">
            <li>Start with the queue, especially blocked orders and active quotation follow-up.</li>
            <li>Use Inquiry before hunting across lists when a customer asks for status.</li>
            <li>Use the action row to create documents quickly without broad module browsing.</li>
            <li>Use reports after operational work is under control, not before.</li>
          </ul>
        </div>
        <div class="sales-console-guide-block">
          <h3 class="sales-console-guide-heading">Controls and handoffs</h3>
          <ul class="sales-console-guide-list">
            <li>Approval and finance-sensitive issues should remain explicit and controlled.</li>
            <li>AI should return here only when it provides real operational value.</li>
            <li>Branch and permission scope should support the page silently, not dominate it.</li>
          </ul>
        </div>
        <div class="sales-console-guide-block">
          <h3 class="sales-console-guide-heading">Current session context</h3>
          <ul class="sales-console-guide-list">
            <li>Mode: ${escapeHtml(profile.mode_label || "Sales workspace")}</li>
            <li>Role: ${escapeHtml(context.primary_role || "Sales")}</li>
            <li>Scope: ${escapeHtml(scope.scope_label || "Controlled by permissions")}</li>
          </ul>
        </div>
      </div>
    `;
  }

  function showGuideDialog(payload) {
    const dialog = new frappe.ui.Dialog({
      title: __("Sales Console Guidelines"),
      fields: [
        {
          fieldtype: "HTML",
          fieldname: "guide_html",
        },
      ],
      primary_action_label: __("Got It"),
      primary_action() {
        dialog.hide();
      },
    });

    dialog.fields_dict.guide_html.$wrapper.html(buildGuideHtml(payload));
    dialog.show();
  }

  function ensureSidebarGuide(openGuide) {
    const itemContainer = document.querySelector(".body-sidebar-top .sidebar-items");
    const bottomContainer = document.querySelector(".body-sidebar-bottom");
    const container = itemContainer || bottomContainer;

    if (!container) return false;
    if (document.querySelector("[data-sales-console-guide='1']")) return true;

    const wrap = document.createElement("div");
    wrap.className = "sales-console-sidebar-guide sidebar-item-container";
    wrap.setAttribute("data-sales-console-guide", "1");
    wrap.innerHTML = `
      <div class="standard-sidebar-item">
        <button type="button" class="item-anchor sales-console-sidebar-guide-button">
          <span class="sales-console-sidebar-guide-mark">${iconMarkup("guide")}</span>
          <span class="sidebar-item-label">Guideline</span>
        </button>
      </div>
    `;
    wrap.querySelector("button").addEventListener("click", openGuide);

    if (itemContainer) {
      itemContainer.appendChild(wrap);
    } else if (bottomContainer.querySelector(".collapse-sidebar-link")) {
      bottomContainer.insertBefore(wrap, bottomContainer.querySelector(".collapse-sidebar-link"));
    } else {
      bottomContainer.appendChild(wrap);
    }

    return true;
  }

  function scheduleSidebarGuide(openGuide) {
    let attempts = 0;
    const timer = window.setInterval(() => {
      attempts += 1;
      if (ensureSidebarGuide(openGuide) || attempts >= 12) {
        window.clearInterval(timer);
      }
    }, 500);
  }

  async function loadBootstrap($root, pageState) {
    try {
      const response = await frappe.call({
        method: BOOTSTRAP_METHOD,
      });

      const payload = response && response.message ? response.message : {};
      pageState.payload = payload;
      if (window.erpWorkspaceConsoleSidebar && typeof window.erpWorkspaceConsoleSidebar.primePayload === "function") {
        window.erpWorkspaceConsoleSidebar.primePayload(payload);
        window.erpWorkspaceConsoleSidebar.refresh();
      }

      applyHeaderContent($root, payload);
      applyUiProfile($root, payload.ui_profile || {});

      [payload.work || {}, payload.lifecycle || {}, payload.blockers || {}, payload.queues || {}].forEach((group) => {
        Object.entries(group).forEach(([key, metric]) => {
          applyQueueMetric($root, key, metric);
        });
      });

      Object.entries(payload.insights || {}).forEach(([key, metric]) => {
        applyInsightMetric($root, key, metric);
      });

      hydrateKnownMetrics($root, payload);
      window.setTimeout(() => hydrateKnownMetrics($root, payload), 30);

      try {
        const reportsCatalog = Array.isArray(payload.reports_catalog) && payload.reports_catalog.length
          ? payload.reports_catalog
          : fallbackReportCards(payload);
        renderReportsSection($root, pageState, reportsCatalog);
      } catch (reportError) {
        $root.find('[data-section="reports"]').hide();
      }

      $root.attr("data-erpw-console-bootstrap", "ready");
    } catch (error) {
      $root.attr("data-erpw-console-bootstrap", "degraded");
      frappe.show_alert({
        message: __("Sales Console data is not available yet."),
        indicator: "orange",
      });
    }
  }

  function renderFailureState(wrapper, error) {
    try {
      // Keep a browser-visible breadcrumb for debugging without trapping Desk boot.
      console.error("Sales Console render failed", error);
    } catch (consoleError) {
      // Ignore console failures and continue with the fallback shell.
    }

    const host = wrapper && wrapper.page && wrapper.page.body ? wrapper.page.body : wrapper;
    const $host = $(host || []);
    const detail = error && error.message ? String(error.message) : "Unexpected render error";

    $host.empty().append(`
      <div class="sales-console-shell" data-erpw-console-runtime="failed" data-erpw-console-bootstrap="failed">
        <section class="sales-console-card sales-console-section">
          <div class="sales-console-section-head">
            <h2 class="sales-console-section-title">Sales Console Unavailable</h2>
            <div class="sales-console-section-note">Fallback workspace state</div>
          </div>
          <div class="sales-console-inquiry-placeholder">
            Sales Console could not finish loading, so Desk is staying available in a safe fallback state.
            ${escapeHtml(detail)}
          </div>
        </section>
      </div>
    `);

    frappe.show_alert({
      message: __("Sales Console is temporarily unavailable."),
      indicator: "orange",
    });
  }

  function render(wrapper) {
    ensureStyle();

    const page = frappe.ui.make_app_page({
      parent: wrapper,
      title: "Sales Console",
      single_column: true,
    });
    syncNativeChrome(page, "Overview");

    const pageState = { payload: {} };
    const openGuide = () => showGuideDialog(pageState.payload);

    const $root = $('<div class="sales-console-shell" data-erpw-console-runtime="ready" data-erpw-console-bootstrap="loading"></div>');

    const $header = $(`
      <section class="sales-console-card sales-console-header">
        <div class="sales-console-header-row">
          <div class="sales-console-header-copy">
            <h1 class="sales-console-title">Sales Console</h1>
            <div class="sales-console-header-note" data-header-note>Execution-first sales workspace for inquiry handling, approvals, and day-to-day control.</div>
          </div>
        </div>
        <div class="sales-console-kpi-grid"></div>
      </section>
    `);

    const $kpiGrid = $header.find(".sales-console-kpi-grid");
    $kpiGrid.append(
      makeInsightCard({
        key: "awaiting_approval",
        label: "Awaiting Approval",
        meta: "Quotations and orders waiting on approval.",
      }).on("click", () => runNavigation(
        pageState,
        "insights",
        "awaiting_approval",
        () => routeToList("Quotation")
      )),
      makeInsightCard({
        key: "open_orders",
        label: "Open Orders",
        meta: "Current order pipeline.",
      }).on("click", () => runNavigation(
        pageState,
        "insights",
        "open_orders",
        () => routeToList("Sales Order")
      ))
    );

    const $actionsSection = $(`
      <section class="sales-console-card sales-console-section" data-section-key="actions">
        <div class="sales-console-section-head">
          <h2 class="sales-console-section-title">Quick Actions</h2>
          <div class="sales-console-section-note" data-section-note="actions">Daily entry points</div>
        </div>
        <div class="sales-console-action-groups">
          <div class="sales-console-action-strip primary"></div>
          <div class="sales-console-action-strip secondary"></div>
        </div>
      </section>
    `);

    const $primaryActions = $actionsSection.find(".sales-console-action-strip.primary");
    const $secondaryActions = $actionsSection.find(".sales-console-action-strip.secondary");
    $primaryActions.append(
      makeAction({
        key: "new_quotation",
        title: "New Quotation",
        meta: "Create a customer quotation",
        icon: "quotation",
        primary: true,
        tier: "primary",
        onClick: () => runNavigation(
          pageState,
          "actions",
          "new_quotation",
          () => frappe.new_doc("Quotation")
        ),
      }),
      makeAction({
        key: "new_sales_order",
        title: "New Sales Order",
        meta: "Create a sales order",
        icon: "order",
        primary: true,
        tier: "primary",
        onClick: () => runNavigation(
          pageState,
          "actions",
          "new_sales_order",
          () => frappe.new_doc("Sales Order")
        ),
      }),
    );
    $secondaryActions.append(
      makeAction({
        key: "open_customer",
        title: "Customers",
        meta: "Browse customer records",
        icon: "customer",
        tier: "secondary",
        onClick: () => runNavigation(
          pageState,
          "actions",
          "open_customer",
          () => routeToWorklist("customer_directory")
        ),
      }),
      makeAction({
        key: "open_item",
        title: "Items",
        meta: "Browse item records",
        icon: "item",
        tier: "secondary",
        onClick: () => runNavigation(
          pageState,
          "actions",
          "open_item",
          () => routeToWorklist("item_directory")
        ),
      })
    );

    const $body = $('<div class="sales-console-body"></div>');

    const $inquirySection = $(`
      <section class="sales-console-card sales-console-section" data-section-key="inquiry">
        <div class="sales-console-section-head">
          <h2 class="sales-console-section-title">Inquiry</h2>
          <div class="sales-console-section-note" data-section-note="inquiry">Search once to answer questions across the full sales chain</div>
        </div>
        <div class="sales-console-inquiry">
          <div class="sales-console-inquiry-shell">
            <div class="sales-console-inquiry-intro">
              <div class="sales-console-inquiry-title">Single-point commercial lookup</div>
              <p class="sales-console-inquiry-meta">Search by customer or commercial document. Suggestions appear while you type so the nearest visible chain can be opened without exact ID recall.</p>
            </div>
            <div class="sales-console-inquiry-form">
              <div class="sales-console-inquiry-input-shell">
                <input class="sales-console-inquiry-input" data-inquiry-input type="text" autocomplete="off" placeholder="Customer, quotation, sales order, invoice, or delivery note" />
                <div class="sales-console-inquiry-suggestions" data-inquiry-suggestions hidden></div>
              </div>
              <div class="sales-console-inquiry-actions">
                <button class="sales-console-inquiry-submit" type="button" data-inquiry-submit>Search</button>
                <button class="sales-console-inquiry-clear" type="button" data-inquiry-clear>Clear</button>
              </div>
            </div>
            <div class="sales-console-inquiry-status" data-inquiry-status>Waiting for inquiry input.</div>
          </div>
          <div class="sales-console-inquiry-result" data-inquiry-result hidden></div>
          <div class="sales-console-inquiry-assist" data-inquiry-ai hidden>
            <div class="sales-console-inquiry-block">
              <div class="sales-console-inquiry-assist-head">
                <div class="sales-console-inquiry-assist-copy">
                  <div class="sales-console-inquiry-assist-title">AI Assist</div>
                  <div class="sales-console-inquiry-meta">Generate a concise summary, blocker explanation, next action, and customer-facing reply draft from the resolved inquiry chain.</div>
                </div>
                <button class="sales-console-inquiry-submit" type="button" data-idle-label="Generate AI Brief" data-inquiry-ai-generate>Generate AI Brief</button>
              </div>
              <div class="sales-console-inquiry-assist-status" data-inquiry-ai-status>Generate a concise AI brief after resolving the inquiry.</div>
              <div data-inquiry-ai-content></div>
            </div>
          </div>
        </div>
      </section>
    `);

    $inquirySection.find("[data-inquiry-submit]").on("click", () => {
      if (maybeSelectActiveInquirySuggestion(pageState, $inquirySection)) return;
      runInquirySearch(pageState, $inquirySection);
    });
    $inquirySection.find("[data-inquiry-clear]").on("click", () => resetInquiryView(pageState, $inquirySection));
    $inquirySection.find("[data-inquiry-ai-generate]").on("click", () => runInquiryAssist(pageState, $inquirySection));
    $inquirySection.find("[data-inquiry-input]").on("input", () => {
      scheduleInquirySuggestions(pageState, $inquirySection);
    });
    $inquirySection.find("[data-inquiry-input]").on("focus", () => {
      const state = getInquirySuggestState(pageState);
      if (state.items.length) {
        renderInquirySuggestions(pageState, $inquirySection, { suggestions: state.items });
        return;
      }
      scheduleInquirySuggestions(pageState, $inquirySection);
    });
    $inquirySection.find("[data-inquiry-input]").on("keydown", (event) => {
      const state = getInquirySuggestState(pageState);
      if (event.key === "ArrowDown" && state.items.length) {
        event.preventDefault();
        setInquirySuggestionActive(pageState, $inquirySection, state.activeIndex + 1);
        return;
      }
      if (event.key === "ArrowUp" && state.items.length) {
        event.preventDefault();
        setInquirySuggestionActive(pageState, $inquirySection, state.activeIndex - 1);
        return;
      }
      if (event.key === "Escape" && state.items.length) {
        event.preventDefault();
        resetInquirySuggestions(pageState, $inquirySection);
        return;
      }
      if (event.key === "Enter") {
        event.preventDefault();
        if (maybeSelectActiveInquirySuggestion(pageState, $inquirySection)) return;
        runInquirySearch(pageState, $inquirySection);
      }
    });
    $(document).off("mousedown.sales-console-inquiry-suggest").on("mousedown.sales-console-inquiry-suggest", (event) => {
      if (!$inquirySection.get(0).contains(event.target)) {
        resetInquirySuggestions(pageState, $inquirySection);
      }
    });
    resetInquiryAssist($inquirySection, "Generate a concise AI brief after resolving the inquiry.");

    const $workSection = $(`
      <section class="sales-console-card sales-console-section" data-section-key="work">
        <div class="sales-console-section-head">
          <h2 class="sales-console-section-title">My Sales Work</h2>
          <div class="sales-console-section-note" data-section-note="work">Execution-first commercial queue</div>
        </div>
        <div class="sales-console-queue-grid" data-section-grid="work"></div>
      </section>
    `);

    const $queue = $workSection.find(".sales-console-queue-grid");
    $queue.append(
      makeQueueItem({
        key: "sales_orders_pending_fulfillment",
        title: "Sales Orders Pending Fulfillment",
        meta: "Open orders still waiting on operational movement.",
        badgeClass: "review",
        sideLabel: "Open",
        onClick: () => runNavigation(
          pageState,
          "work",
          "sales_orders_pending_fulfillment",
          () => routeToList("Sales Order")
        ),
      }),
      makeQueueItem({
        key: "quotations_waiting_action",
        title: "Quotations Waiting For Action",
        meta: "Active quotations needing reply, revision, or follow-up.",
        badgeClass: "attention",
        sideLabel: "Open",
        onClick: () => runNavigation(
          pageState,
          "work",
          "quotations_waiting_action",
          () => routeToList("Quotation")
        ),
      }),
      makeQueueItem({
        key: "expiring_quotations",
        title: "Active Quotations Nearing Expiry",
        meta: "Draft or open quotations at risk of slipping out of cycle.",
        badgeClass: "attention",
        sideLabel: "Due",
        onClick: () => runNavigation(
          pageState,
          "work",
          "expiring_quotations",
          () => routeToList("Quotation")
        ),
      }),
      makeQueueItem({
        key: "customer_follow_up_tasks",
        title: "Customer Follow-Up Tasks",
        meta: "Promised callbacks and overdue commercial follow-up.",
        badgeClass: "attention",
        sideLabel: "Open",
        onClick: () => runNavigation(
          pageState,
          "work",
          "customer_follow_up_tasks",
          () => routeToList("ToDo")
        ),
      })
    );

    const $lifecycleSection = $(`
      <section class="sales-console-card sales-console-section" data-section-key="lifecycle">
        <div class="sales-console-section-head">
          <h2 class="sales-console-section-title">Customer Lifecycle Visibility</h2>
          <div class="sales-console-section-note" data-section-note="lifecycle">Delivery, invoice, and return visibility for customer response</div>
        </div>
        <div class="sales-console-queue-grid" data-section-grid="lifecycle"></div>
      </section>
    `);

    const $lifecycleGrid = $lifecycleSection.find(".sales-console-queue-grid");
    $lifecycleGrid.append(
      makeQueueItem({
        key: "orders_due_soon",
        title: "Orders Due Soon",
        meta: "Confirmed orders with delivery commitments coming up soon.",
        badgeClass: "review",
        sideLabel: "Due Soon",
        onClick: () => runNavigation(
          pageState,
          "lifecycle",
          "orders_due_soon",
          () => routeToList("Sales Order")
        ),
      }),
      makeQueueItem({
        key: "partially_delivered_orders",
        title: "Partially Delivered Orders",
        meta: "Orders already moving, but not yet fully delivered.",
        badgeClass: "review",
        sideLabel: "Open",
        onClick: () => runNavigation(
          pageState,
          "lifecycle",
          "partially_delivered_orders",
          () => routeToList("Sales Order")
        ),
      }),
      makeQueueItem({
        key: "invoices_outstanding",
        title: "Invoices Outstanding",
        meta: "Customer-facing invoice follow-up still requiring settlement.",
        badgeClass: "attention",
        sideLabel: "Open",
        onClick: () => runNavigation(
          pageState,
          "lifecycle",
          "invoices_outstanding",
          () => routeToList("Sales Invoice")
        ),
      }),
      makeQueueItem({
        key: "sales_returns_in_progress",
        title: "Recent Sales Returns",
        meta: "Recent customer return and credit-note records requiring awareness.",
        badgeClass: "attention",
        sideLabel: "Recent",
        onClick: () => runNavigation(
          pageState,
          "lifecycle",
          "sales_returns_in_progress",
          () => routeToList("Delivery Note")
        ),
      })
    );

    const $approvalsSection = $(`
      <section class="sales-console-card sales-console-section" data-section-key="approvals">
        <div class="sales-console-section-head">
          <h2 class="sales-console-section-title">Approvals / Blockers</h2>
          <div class="sales-console-section-note" data-section-note="approvals">Approval and exception visibility without leaving sales context</div>
        </div>
        <div class="sales-console-queue-grid" data-section-grid="approvals"></div>
      </section>
    `);

    const $approvalsGrid = $approvalsSection.find(".sales-console-queue-grid");
    $approvalsGrid.append(
      makeQueueItem({
        key: "orders_blocked_by_approval",
        title: "Orders Blocked By Approval",
        meta: "Commercial cases waiting for approval or exception handling.",
        badgeClass: "blocker",
        priority: true,
        sideLabel: "Pending",
        onClick: () => runNavigation(
          pageState,
          "blockers",
          "orders_blocked_by_approval",
          () => routeToList("Sales Order")
        ),
      }),
      makeQueueItem({
        key: "quotations_awaiting_approval",
        title: "Quotations Awaiting Approval",
        meta: "Quotations currently waiting on manager or executive approval.",
        badgeClass: "blocker",
        sideLabel: "Pending",
        onClick: () => runNavigation(
          pageState,
          "blockers",
          "quotations_awaiting_approval",
          () => routeToList("Quotation")
        ),
      })
    );

    const $reportsSection = $(`
      <section class="sales-console-card sales-console-section" data-section="reports" data-section-key="reports">
        <div class="sales-console-section-head">
          <h2 class="sales-console-section-title">Reports And Review</h2>
          <div class="sales-console-section-note" data-section-note="reports">Truthful review targets from the live ERP</div>
        </div>
        <div class="sales-console-report-links"></div>
      </section>
    `);

    $body.append($inquirySection, $workSection, $lifecycleSection, $approvalsSection, $reportsSection);
    $root.append($header, $actionsSection, $body);
    renderReportsSection($root, pageState, defaultReportCardsForCurrentRole());
    $(page.body).empty().append($root);
    bindConsoleNavigationDelegates($root, pageState);

    scheduleSidebarGuide(openGuide);
    loadBootstrap($root, pageState);
  }

  function renderSafely(wrapper) {
    try {
      render(wrapper);
    } catch (error) {
      renderFailureState(wrapper, error);
    }
  }

  frappe.pages[PAGE_KEY] = frappe.pages[PAGE_KEY] || {};
  frappe.pages[PAGE_KEY].on_page_load = function (wrapper) {
    renderSafely(wrapper);
  };
  frappe.pages[PAGE_KEY].on_page_show = function (wrapper) {
    if (window.erpWorkspaceConsoleSidebar && typeof window.erpWorkspaceConsoleSidebar.refresh === "function") {
      window.erpWorkspaceConsoleSidebar.refresh();
    }
    if (wrapper && wrapper.page) {
      syncNativeChrome(wrapper.page, "Overview");
    }
    const host = wrapper && wrapper.page && wrapper.page.body ? wrapper.page.body : wrapper;
    if ($(host || []).find(".sales-console-shell").length) return;
    renderSafely(wrapper);
  };
})();
