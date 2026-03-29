/* global frappe, $ */

(function () {
  const PAGE_KEY = "sales-console";
  const BOOTSTRAP_METHOD = "erp_workspace_ui.sales_console.service.get_sales_console_bootstrap";

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
        background: rgba(255, 255, 255, 0.97);
        border: 1px solid rgba(255, 255, 255, 0.94);
        border-radius: 16px;
        box-shadow:
          0 26px 50px rgba(15, 23, 42, 0.085),
          0 1px 0 rgba(255, 255, 255, 0.78) inset;
      }
      .sales-console-header {
        overflow: hidden;
        padding: 26px 24px 24px;
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
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 16px;
        margin-bottom: 20px;
      }
      .sales-console-header-copy {
        display: grid;
        gap: 4px;
      }
      .sales-console-title {
        margin: 0;
        font-size: 31px;
        line-height: 1.05;
        font-weight: 700;
        color: #f8fafc;
      }
      .sales-console-kpi-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0;
        max-width: 820px;
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
        padding: 18px 20px 20px;
      }
      .sales-console-section-head {
        display: flex;
        align-items: center;
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
        font-size: 12px;
        color: #64748b;
        text-align: right;
        max-width: 260px;
        line-height: 1.4;
        white-space: normal;
      }
      .sales-console-action-groups {
        display: grid;
        gap: 12px;
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
        gap: 12px;
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
        border: 1px solid rgba(255, 255, 255, 0.92);
        background: #ffffff;
        cursor: pointer;
        transition: transform 120ms ease, border-color 120ms ease, box-shadow 120ms ease;
        min-width: 0;
        box-shadow:
          0 1px 0 rgba(255, 255, 255, 0.98) inset,
          0 10px 28px rgba(0, 0, 0, 0.085);
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
        transform: translateY(-1px);
        border-color: rgba(255, 255, 255, 0.98);
        box-shadow:
          0 1px 0 rgba(255, 255, 255, 0.98) inset,
          0 14px 38px rgba(0, 0, 0, 0.115);
      }
      .sales-console-action.primary {
        background: #ffffff;
      }
      .sales-console-action.primary::before {
        background: linear-gradient(90deg, #0f766e 0%, #2dd4bf 100%);
      }
      .sales-console-action.secondary {
        padding-top: 16px;
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
        border: 1px solid #35465f;
        background: #2a3850;
        color: #f8fafc;
        box-shadow:
          0 1px 0 rgba(255, 255, 255, 0.08) inset,
          0 10px 20px rgba(15, 23, 42, 0.16);
      }
      .sales-console-action.primary .sales-console-action-icon {
        border-color: #314259;
        background: #243247;
        color: #f8fafc;
      }
      .sales-console-action.secondary .sales-console-action-icon {
        border-color: #314259;
        background: #243247;
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
      .sales-console-queue-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 10px;
      }
      .sales-console-queue-grid > [data-queue-key]:first-child {
        grid-column: 1 / -1;
      }
      .sales-console-queue-card {
        position: relative;
        overflow: hidden;
        display: grid;
        gap: 8px;
        padding: 16px 18px;
        border-radius: 18px;
        border: 1px solid rgba(255, 255, 255, 0.92);
        background: #ffffff;
        cursor: pointer;
        text-align: left;
        transition: border-color 120ms ease, box-shadow 120ms ease, background 120ms ease;
        min-width: 0;
        min-height: 92px;
        box-shadow:
          0 1px 0 rgba(255, 255, 255, 0.98) inset,
          0 10px 28px rgba(0, 0, 0, 0.085);
      }
      .sales-console-queue-card:hover {
        border-color: rgba(255, 255, 255, 0.98);
        box-shadow:
          0 1px 0 rgba(255, 255, 255, 0.98) inset,
          0 14px 38px rgba(0, 0, 0, 0.115);
      }
      .sales-console-queue-card.priority {
        grid-template-columns: minmax(0, 1fr) auto;
        align-items: center;
        gap: 20px;
        padding: 22px 22px 20px;
        border-color: rgba(255, 255, 255, 0.94);
        background:
          linear-gradient(90deg, rgba(34, 211, 238, 0.035) 0%, rgba(34, 211, 238, 0.012) 18%, rgba(255, 255, 255, 0) 38%),
          #ffffff;
        box-shadow:
          0 1px 0 rgba(255, 255, 255, 0.99) inset,
          0 10px 28px rgba(0, 0, 0, 0.085);
        min-height: 122px;
      }
      .sales-console-queue-card.priority:hover {
        border-color: rgba(255, 255, 255, 0.98);
        background:
          linear-gradient(90deg, rgba(34, 211, 238, 0.05) 0%, rgba(34, 211, 238, 0.018) 18%, rgba(255, 255, 255, 0) 38%),
          #ffffff;
        box-shadow:
          0 1px 0 rgba(255, 255, 255, 0.99) inset,
          0 14px 38px rgba(0, 0, 0, 0.115);
      }
      .sales-console-queue-card.regular {
        grid-template-columns: minmax(0, 1fr) 104px;
        gap: 16px;
        align-items: stretch;
        min-height: 96px;
        box-shadow:
          inset 3px 0 0 #d8e0ea,
          0 1px 0 rgba(255, 255, 255, 0.98) inset,
          0 10px 28px rgba(0, 0, 0, 0.085);
      }
      .sales-console-queue-card.regular:hover {
        box-shadow:
          inset 4px 0 0 #c7d4e2,
          0 1px 0 rgba(255, 255, 255, 0.98) inset,
          0 14px 38px rgba(0, 0, 0, 0.115);
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
        gap: 4px;
        min-width: 104px;
        padding: 12px 14px;
        border-radius: 14px;
        border: 1px solid rgba(255, 255, 255, 0.92);
        background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%);
        box-shadow:
          0 2px 10px rgba(0, 0, 0, 0.04),
          0 1px 0 rgba(255, 255, 255, 0.98) inset;
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
        border: 1px solid rgba(255, 255, 255, 0.94);
        background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%);
        box-shadow:
          0 2px 8px rgba(0, 0, 0, 0.035),
          0 1px 0 rgba(255, 255, 255, 0.99) inset;
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
      }
      .sales-console-queue-card.priority .sales-console-queue-count {
        font-size: 24px;
      }
      .sales-console-queue-side::after,
      .sales-console-queue-priority-side::after {
        content: "queued";
        font-size: 10px;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #7c8798;
      }
      .sales-console-queue-priority-side::after {
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
        gap: 10px;
      }
      .sales-console-link {
        position: relative;
        overflow: hidden;
        display: grid;
        grid-template-columns: 42px minmax(0, 1fr) auto;
        align-items: start;
        gap: 14px;
        width: 100%;
        text-align: left;
        padding: 14px 16px;
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.92);
        background: #ffffff;
        cursor: pointer;
        transition: border-color 120ms ease, background 120ms ease, box-shadow 120ms ease, transform 120ms ease;
        min-width: 0;
        box-shadow:
          0 1px 0 rgba(255, 255, 255, 0.98) inset,
          0 9px 26px rgba(0, 0, 0, 0.078);
      }
      .sales-console-link::before {
        content: "";
        position: absolute;
        top: 0;
        left: 16px;
        width: 30px;
        height: 3px;
        border-radius: 999px;
        background: linear-gradient(90deg, #a8d8d2 0%, #dff0ed 100%);
      }
      .sales-console-link:hover {
        border-color: rgba(255, 255, 255, 0.98);
        background: #ffffff;
        transform: translateY(-1px);
        box-shadow:
          0 1px 0 rgba(255, 255, 255, 0.98) inset,
          0 13px 35px rgba(0, 0, 0, 0.108);
      }
      .sales-console-link-icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 42px;
        height: 42px;
        border-radius: 11px;
        border: 1px solid #3a4b65;
        background: #2d3d56;
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
        min-width: 62px;
        border: 1px solid rgba(42, 56, 80, 0.16);
        background: #ffffff;
        color: #2a3850;
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
        .sales-console-section-head {
          align-items: flex-start;
        }
        .sales-console-action-strip.primary,
        .sales-console-action-strip.secondary,
        .sales-console-queue-grid,
        .sales-console-kpi-grid {
          grid-template-columns: 1fr;
        }
        .sales-console-kpi-grid {
          max-width: none;
        }
        .sales-console-kpi-card + .sales-console-kpi-card {
          border-left: none;
          border-top: 1px solid rgba(255, 255, 255, 0.09);
        }
        .sales-console-queue-grid > [data-queue-key]:first-child {
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

    if (target.kind === "new_doc" && target.doctype) {
      frappe.new_doc(target.doctype);
      return;
    }

    if (target.kind === "list" && target.doctype) {
      routeToList(target.doctype, target.filters || null);
      return;
    }

    if (target.kind === "report" && target.report_name) {
      routeToReport(target.report_name, target.filters || null);
      return;
    }

    if (typeof fallback === "function") fallback();
  }

  function runNavigation(pageState, group, key, fallback) {
    const navigation = (pageState && pageState.payload && pageState.payload.navigation) || {};
    const groupTargets = navigation[group] || {};
    executeTarget(groupTargets[key], fallback);
  }

  function makeAction(config) {
    const variantClass = config.primary ? "primary" : "secondary";
    const $button = $(`
      <button class="sales-console-action ${variantClass}" data-action-key="${escapeHtml(config.key)}">
        <span class="sales-console-action-icon">${iconMarkup(config.icon || "square")}</span>
        <span class="sales-console-action-copy">
          <span class="sales-console-action-title">${escapeHtml(config.title)}</span>
          <span class="sales-console-action-meta">${escapeHtml(config.meta)}</span>
        </span>
      </button>
    `);
    $button.on("click", config.onClick);
    return $button;
  }

  function makeQueueItem(config) {
    const badgeClass = config.badgeClass || "pending";
    if (config.priority) {
      const $priority = $(`
        <button class="sales-console-queue-card priority" data-queue-key="${escapeHtml(config.key)}">
          <div class="sales-console-queue-priority-main">
            <div class="sales-console-queue-kicker">Priority Queue</div>
            <div class="sales-console-queue-topline">
              <div class="sales-console-queue-title">${escapeHtml(config.title)}</div>
              <span class="sales-console-badge ${badgeClass}" data-role="badge">Pending</span>
            </div>
            <div class="sales-console-queue-meta" data-role="meta">${escapeHtml(config.meta)}</div>
          </div>
          <div class="sales-console-queue-priority-side">
            <div class="sales-console-queue-count" data-role="count">--</div>
          </div>
        </button>
      `);
      $priority.on("click", config.onClick);
      return $priority;
    }
    const $row = $(`
      <button class="sales-console-queue-card regular" data-queue-key="${escapeHtml(config.key)}">
        <div class="sales-console-queue-main">
          <div class="sales-console-queue-title">${escapeHtml(config.title)}</div>
          <div class="sales-console-queue-meta" data-role="meta">${escapeHtml(config.meta)}</div>
        </div>
        <div class="sales-console-queue-side">
          <div class="sales-console-queue-count" data-role="count">--</div>
        </div>
      </button>
    `);
    $row.on("click", config.onClick);
    return $row;
  }

  function makeInsightCard(config) {
    return $(`
      <button class="sales-console-kpi-card" data-insight-key="${escapeHtml(config.key)}" type="button">
        <div class="sales-console-kpi-label">${escapeHtml(config.label)}</div>
        <div class="sales-console-kpi-value" data-role="value">--</div>
        <div class="sales-console-kpi-meta" data-role="meta">${escapeHtml(config.meta)}</div>
      </button>
    `);
  }

  function makeReportLink(key, title, meta, icon, onClick) {
    const $row = $(`
      <button class="sales-console-link" data-report-key="${escapeHtml(key)}" type="button">
        <span class="sales-console-link-icon">${iconMarkup(icon || "chart")}</span>
        <div class="sales-console-link-copy">
          <div class="sales-console-link-title">${escapeHtml(title)}</div>
          <div class="sales-console-link-meta">${escapeHtml(meta)}</div>
        </div>
        <span class="sales-console-badge review">Open</span>
      </button>
    `);
    $row.on("click", onClick);
    return $row;
  }

  function iconMarkup(name) {
    const icons = {
      quotation: `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.85" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M12 20h8"></path>
          <path d="M16.5 3.5a2.12 2.12 0 1 1 3 3L7 19l-4 1 1-4 12.5-12.5z"></path>
        </svg>
      `,
      order: `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.85" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <circle cx="9" cy="19.5" r="1.35"></circle>
          <circle cx="17" cy="19.5" r="1.35"></circle>
          <path d="M3 4h2l2.4 10.2a1 1 0 0 0 1 .8h8.9a1 1 0 0 0 1-.76L20 8H7"></path>
        </svg>
      `,
      customer: `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.85" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M20 21a8 8 0 0 0-16 0"></path>
          <circle cx="12" cy="8" r="3.2"></circle>
        </svg>
      `,
      opportunity: `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.85" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M4 16l5.5-5.5 4 4L20 8"></path>
          <path d="M14.5 8H20v5.5"></path>
        </svg>
      `,
      item: `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M12 3l7 4-7 4-7-4 7-4z"></path>
          <path d="M5 7v10l7 4 7-4V7"></path>
          <path d="M12 11v10"></path>
        </svg>
      `,
      chart: `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.85" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M4 20V10"></path>
          <path d="M10 20V4"></path>
          <path d="M16 20v-7"></path>
          <path d="M22 20V8"></path>
        </svg>
      `,
      guide: `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.85" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <circle cx="12" cy="12" r="9"></circle>
          <path d="M9.4 9a2.6 2.6 0 1 1 3.9 2.25c-.85.48-1.3.98-1.3 2"></path>
          <circle cx="12" cy="17" r="1"></circle>
        </svg>
      `,
      square: `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.85" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M12 5v14"></path>
          <path d="M5 12h14"></path>
        </svg>
      `,
    };

    return icons[name] || icons.square;
  }

  function metricValueText(metric) {
    if (!metric || metric.value == null) return "--";
    return String(metric.value);
  }

  function metricBadge(metric, key) {
    if (key === "orders_blocked_by_approval") {
      return { text: "Pending Approval", className: "blocker" };
    }
    if (!metric) {
      return { text: "Pending", className: "pending" };
    }
    if (metric.state === "live") {
      return { text: "Active", className: metric.badgeClass || "attention" };
    }
    if (metric.state === "restricted") {
      return { text: "Restricted", className: "restricted" };
    }
    return { text: "Pending", className: "pending" };
  }

  function applyQueueMetric($root, key, metric) {
    const $item = $root.find(`[data-queue-key="${key}"]`);
    if (!$item.length) return;

    const badge = metricBadge(metric, key);
    $item.find('[data-role="count"]').text(metricValueText(metric));
    $item.find('[data-role="badge"]')
      .removeClass("attention blocker review pending restricted")
      .addClass(badge.className)
      .text(badge.text);

    if (metric && metric.state !== "live" && metric.note) {
      $item.find('[data-role="meta"]').text(metric.note);
    }
  }

  function applyInsightMetric($root, key, metric) {
    const $card = $root.find(`[data-insight-key="${key}"]`);
    if (!$card.length) return;

    $card.find('[data-role="value"]').text(metricValueText(metric));
    if (metric && metric.state !== "live" && metric.note) {
      $card.find('[data-role="meta"]').text(metric.note);
    }
  }

  function reorderChildren($container, order, attributeName) {
    if (!Array.isArray(order) || !order.length) return;

    const children = $container.children().get();
    const byKey = new Map(children.map(element => [element.getAttribute(attributeName), element]));

    order.forEach(key => {
      const element = byKey.get(key);
      if (element) {
        $container.append(element);
      }
    });
  }

  function applyActionOrder($root, order) {
    if (!Array.isArray(order) || !order.length) return;

    const elements = $root.find("[data-action-key]").get();
    const byKey = new Map(elements.map(element => [element.getAttribute("data-action-key"), element]));
    const arranged = [];

    order.forEach(key => {
      const element = byKey.get(key);
      if (element) {
        arranged.push(element);
        byKey.delete(key);
      }
    });

    byKey.forEach(element => arranged.push(element));

    const $primary = $root.find(".sales-console-action-strip.primary");
    const $secondary = $root.find(".sales-console-action-strip.secondary");
    $primary.empty();
    $secondary.empty();

    arranged.forEach((element, index) => {
      if (index < 3) {
        $primary.append(element);
      } else {
        $secondary.append(element);
      }
    });
  }

  function applyUiProfile($root, profile) {
    if (!profile) return;

    if (Array.isArray(profile.action_order)) {
      applyActionOrder($root, profile.action_order);
    }
    if (Array.isArray(profile.queue_order)) {
      reorderChildren($root.find(".sales-console-queue-grid"), profile.queue_order, "data-queue-key");
    }

    const hiddenActions = new Set(profile.hidden_actions || []);
    $root.find("[data-action-key]").each((_, element) => {
      const $element = $(element);
      const key = $element.attr("data-action-key");
      $element.toggle(!hiddenActions.has(key));
    });

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

      applyUiProfile($root, payload.ui_profile || {});

      Object.entries(payload.queues || {}).forEach(([key, metric]) => {
        applyQueueMetric($root, key, metric);
      });

      Object.entries(payload.insights || {}).forEach(([key, metric]) => {
        applyInsightMetric($root, key, metric);
      });
    } catch (error) {
      frappe.show_alert({
        message: __("Sales Console data is not available yet."),
        indicator: "orange",
      });
    }
  }

  function render(wrapper) {
    ensureStyle();

    const page = frappe.ui.make_app_page({
      parent: wrapper,
      title: "Sales Console",
      single_column: true,
    });

    const pageState = { payload: {} };
    const openGuide = () => showGuideDialog(pageState.payload);

    const $root = $('<div class="sales-console-shell"></div>');

    const $header = $(`
      <section class="sales-console-card sales-console-header">
        <div class="sales-console-header-row">
          <div class="sales-console-header-copy">
            <h1 class="sales-console-title">Sales Console</h1>
          </div>
        </div>
        <div class="sales-console-kpi-grid"></div>
      </section>
    `);

    const $kpiGrid = $header.find(".sales-console-kpi-grid");
    $kpiGrid.append(
      makeInsightCard({
        key: "quotations_awaiting_approval",
        label: "Awaiting Approval",
        meta: "Quotation approval queue.",
      }).on("click", () => runNavigation(
        pageState,
        "insights",
        "quotations_awaiting_approval",
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
      <section class="sales-console-card sales-console-section">
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
        onClick: () => runNavigation(
          pageState,
          "actions",
          "new_sales_order",
          () => frappe.new_doc("Sales Order")
        ),
      }),
      makeAction({
        key: "open_customer",
        title: "Open Customer",
        meta: "Jump into customer records",
        icon: "customer",
        primary: true,
        onClick: () => runNavigation(
          pageState,
          "actions",
          "open_customer",
          () => routeToList("Customer")
        ),
      }),
    );
    $secondaryActions.append(
      makeAction({
        key: "new_opportunity",
        title: "Opportunity",
        meta: "Open a new opportunity",
        icon: "opportunity",
        onClick: () => runNavigation(
          pageState,
          "actions",
          "new_opportunity",
          () => frappe.new_doc("Opportunity")
        ),
      }),
      makeAction({
        key: "open_item",
        title: "Item",
        meta: "Open item records",
        icon: "item",
        onClick: () => runNavigation(
          pageState,
          "actions",
          "open_item",
          () => routeToList("Item")
        ),
      })
    );

    const $body = $('<div class="sales-console-body"></div>');

    const $workSection = $(`
      <section class="sales-console-card sales-console-section">
        <div class="sales-console-section-head">
          <h2 class="sales-console-section-title">Sales Work Queue</h2>
          <div class="sales-console-section-note" data-section-note="work">Blocker-first review and queue control</div>
        </div>
        <div class="sales-console-queue-grid"></div>
      </section>
    `);

    const $queue = $workSection.find(".sales-console-queue-grid");
    $queue.append(
      makeQueueItem({
        key: "orders_blocked_by_approval",
        title: "Orders Blocked By Approval",
        meta: "Commercial cases waiting for approval or exception handling.",
        badgeClass: "blocker",
        priority: true,
        onClick: () => runNavigation(
          pageState,
          "queues",
          "orders_blocked_by_approval",
          () => routeToList("Sales Order")
        ),
      }),
      makeQueueItem({
        key: "sales_orders_pending_fulfillment",
        title: "Sales Orders Pending Fulfillment",
        meta: "Open orders still waiting on operational movement.",
        badgeClass: "review",
        onClick: () => runNavigation(
          pageState,
          "queues",
          "sales_orders_pending_fulfillment",
          () => routeToList("Sales Order")
        ),
      }),
      makeQueueItem({
        key: "quotations_waiting_action",
        title: "Quotations Waiting For Action",
        meta: "Active quotations needing reply, revision, or follow-up.",
        badgeClass: "attention",
        onClick: () => runNavigation(
          pageState,
          "queues",
          "quotations_waiting_action",
          () => routeToList("Quotation")
        ),
      }),
      makeQueueItem({
        key: "expiring_quotations",
        title: "Open Quotations Nearing Expiry",
        meta: "Open quotations at risk of slipping out of cycle.",
        badgeClass: "attention",
        onClick: () => runNavigation(
          pageState,
          "queues",
          "expiring_quotations",
          () => routeToList("Quotation")
        ),
      }),
      makeQueueItem({
        key: "customer_follow_up_tasks",
        title: "Customer Follow-Up Tasks",
        meta: "Promised callbacks and overdue commercial follow-up.",
        badgeClass: "attention",
        onClick: () => runNavigation(
          pageState,
          "queues",
          "customer_follow_up_tasks",
          () => routeToList("ToDo")
        ),
      })
    );

    const $reportsSection = $(`
      <section class="sales-console-card sales-console-section" data-section="reports">
        <div class="sales-console-section-head">
          <h2 class="sales-console-section-title">Reports And Review</h2>
          <div class="sales-console-section-note" data-section-note="reports">Management review and exception follow-up</div>
        </div>
        <div class="sales-console-report-links"></div>
      </section>
    `);

    const $reportLinks = $reportsSection.find(".sales-console-report-links");
    $reportLinks.append(
      makeReportLink("sales_analytics", "Sales Analytics", "Management and performance review", "chart", () => runNavigation(
        pageState,
        "reports",
        "sales_analytics",
        () => routeToReport("Sales Analytics")
      )),
      makeReportLink("customer_wise_sales_history", "Customer-wise Sales History", "Account-level sales history", "customer", () => runNavigation(
        pageState,
        "reports",
        "customer_wise_sales_history",
        () => routeToReport("Customer-wise Sales History")
      )),
      makeReportLink("item_wise_sales_register", "Item-wise Sales Register", "Item-level review", "item", () => runNavigation(
        pageState,
        "reports",
        "item_wise_sales_register",
        () => routeToReport("Item-wise Sales Register")
      )),
      makeReportLink("open_orders", "Open Orders", "Review active order pipeline", "order", () => runNavigation(
        pageState,
        "reports",
        "open_orders",
        () => routeToList("Sales Order")
      ))
    );

    $body.append($workSection, $reportsSection);
    $root.append($header, $actionsSection, $body);
    $(page.body).empty().append($root);

    scheduleSidebarGuide(openGuide);
    loadBootstrap($root, pageState);
  }

  frappe.pages[PAGE_KEY] = frappe.pages[PAGE_KEY] || {};
  frappe.pages[PAGE_KEY].on_page_load = function (wrapper) {
    render(wrapper);
  };
})();
