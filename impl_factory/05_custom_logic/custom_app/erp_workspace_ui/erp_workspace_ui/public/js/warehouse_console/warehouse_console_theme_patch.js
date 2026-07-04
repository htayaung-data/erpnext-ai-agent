/* global window, document */

(function () {
  const STYLE_ID = "erpw-warehouse-console-theme-patch-w16c";

  function applyWarehouseConsoleThemePatch() {
    let style = document.getElementById(STYLE_ID);
    if (!style) {
      style = document.createElement("style");
      style.id = STYLE_ID;
      document.head.appendChild(style);
    }
    style.textContent = `
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-actions,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-actions {
        align-items: center !important;
        gap: 8px !important;
        padding-top: 1px !important;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-button,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-button {
        box-sizing: border-box !important;
        min-height: 33px !important;
        padding: 0 13px !important;
        border: 1px solid rgba(124, 154, 143, 0.30) !important;
        border-radius: 11px !important;
        background: #ffffff !important;
        color: #10261f !important;
        font-size: 12px !important;
        font-weight: 730 !important;
        line-height: 1 !important;
        white-space: nowrap !important;
        box-shadow: none !important;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-button:hover,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-button:focus-visible,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-button:hover,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-button:focus-visible {
        border-color: rgba(74, 117, 101, 0.46) !important;
        background: #f6faf8 !important;
        color: #10261f !important;
        outline: none !important;
        box-shadow: none !important;
        transform: none !important;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-header .warehouse-receiving-chip,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-header .warehouse-receiving-chip {
        min-height: 23px !important;
        padding: 0 9px !important;
        border: 1px solid rgba(148, 163, 184, 0.28) !important;
        border-radius: 8px !important;
        background: #f8faf9 !important;
        color: #334155 !important;
        font-size: 10.5px !important;
        font-weight: 650 !important;
        letter-spacing: 0.002em !important;
        line-height: 1.18 !important;
        text-transform: none !important;
        box-shadow: none !important;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-header .warehouse-receiving-chip.is-read-only,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-header .warehouse-receiving-chip.is-read-only {
        border-color: rgba(13, 148, 136, 0.26) !important;
        background: #f0fdfa !important;
        color: #0f766e !important;
      }
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] [data-warehouse-receiving-command-fact='state'] strong,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] [data-warehouse-receiving-card='state'] .warehouse-receiving-card-value,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] [data-warehouse-picking-command-fact='state'] strong,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] [data-warehouse-picking-card='state'] .warehouse-receiving-card-value,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-receiving-shell[data-warehouse-view='receiving-review'] .warehouse-receiving-card-value.warehouse-receiving-status-value,
      .sales-console-shell[data-erpw-workspace='warehouse'].warehouse-picking-shell[data-warehouse-view='picking-review'] .warehouse-receiving-card-value.warehouse-receiving-status-value {
        color: #10261f !important;
        font-size: 13px !important;
        font-weight: 640 !important;
        letter-spacing: 0 !important;
        line-height: 1.2 !important;
      }
    `;
  }

  window.erpWorkspaceWarehouseConsoleThemePatch = applyWarehouseConsoleThemePatch;
  applyWarehouseConsoleThemePatch();
})();
