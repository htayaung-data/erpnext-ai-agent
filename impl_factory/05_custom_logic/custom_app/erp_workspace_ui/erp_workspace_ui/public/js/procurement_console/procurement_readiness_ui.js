/* global frappe, $ */

(function () {
  const workspaceRegistry = window.erpWorkspaceUiWorkspaceRegistry || {};
  const procurementWorkspace = typeof workspaceRegistry.procurement === "function" ? workspaceRegistry.procurement() : null;
  const procurementRoutes = procurementWorkspace && procurementWorkspace.routes ? procurementWorkspace.routes : {};
  const WORKLIST_ROUTE = procurementRoutes.worklist || "procurement-console-worklist";
  const REPORT_ROUTE = procurementRoutes.report || "procurement-console-report";

  function escapeHtml(value) {
    if (frappe.utils && typeof frappe.utils.escape_html === "function") {
      return frappe.utils.escape_html(value == null ? "" : String(value));
    }
    return String(value == null ? "" : value).replace(/[&<>"']/g, (character) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      "\"": "&quot;",
      "'": "&#39;",
    }[character] || character));
  }

  function routePayload(route) {
    try {
      return encodeURIComponent(JSON.stringify(route || {}));
    } catch (error) {
      return "";
    }
  }

  function parseRoutePayload(value) {
    try {
      return JSON.parse(decodeURIComponent(value || ""));
    } catch (error) {
      return {};
    }
  }

  function ensureStyles() {
    if (document.getElementById("erpw-procurement-readiness-styles")) return;
    const style = document.createElement("style");
    style.id = "erpw-procurement-readiness-styles";
    style.textContent = `
      .erpw-readiness-card { display: grid; gap: 12px; padding: 15px 18px 18px; border: 1px solid #dbe6f2; border-radius: 14px; background: #fff; box-shadow: inset 0 1px 0 rgba(255,255,255,0.98), 0 7px 16px rgba(15,23,42,0.03); box-sizing: border-box; }
      .erpw-readiness-top { display: flex; align-items: flex-start; justify-content: space-between; gap: 14px; flex-wrap: wrap; }
      .erpw-readiness-title { font-size: 15px; line-height: 1.25; font-weight: 790; color: #0f172a; }
      .erpw-readiness-note { margin-top: 3px; color: #475569; font-size: 12.5px; line-height: 1.36; max-width: 760px; }
      .erpw-readiness-summary { display: flex; gap: 7px; align-items: center; flex-wrap: wrap; }
      .erpw-readiness-chip { display: inline-flex; min-height: 25px; align-items: center; padding: 0 9px; border-radius: 999px; border: 1px solid #dbe6f2; background: #f8fafc; color: #334155; font-size: 11.5px; font-weight: 760; white-space: nowrap; }
      .erpw-readiness-chip.critical { border-color: #fecaca; background: #fff1f2; color: #991b1b; }
      .erpw-readiness-chip.warning { border-color: #fde2b8; background: #fff8ed; color: #9a5b13; }
      .erpw-readiness-chip.info { border-color: #bfdbfe; background: #eff6ff; color: #1d4ed8; }
      .erpw-readiness-chip.ready { border-color: #d9eadf; background: #f3faf6; color: #166534; }
      .erpw-readiness-list { display: grid; gap: 8px; }
      .erpw-readiness-row { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 12px; align-items: center; border: 1px solid #edf2f7; border-radius: 12px; padding: 10px 11px; background: #fbfdff; }
      .erpw-readiness-row-main { min-width: 0; display: grid; gap: 3px; }
      .erpw-readiness-row-title { display: flex; align-items: center; gap: 7px; flex-wrap: wrap; color: #0f172a; font-size: 12.8px; font-weight: 770; line-height: 1.25; }
      .erpw-readiness-row-detail { color: #475569; font-size: 12.2px; line-height: 1.35; overflow-wrap: anywhere; }
      .erpw-readiness-row-source { color: #64748b; font-size: 11.4px; line-height: 1.3; }
      .erpw-readiness-action { min-height: 31px; border: 1px solid #d5e2ef; border-radius: 9px; background: #fff; color: #12365f; font-weight: 740; font-size: 12px; padding: 0 10px; white-space: nowrap; }
      .erpw-readiness-action:hover { border-color: #9db7d2; background: #f8fbff; }
      .erpw-readiness-empty { border: 1px solid #edf2f7; border-radius: 12px; padding: 10px 11px; background: #fbfdff; color: #475569; font-size: 12.4px; }
      .erpw-manager-readiness { display: grid; gap: 12px; }
      .erpw-manager-readiness-grid { display: grid; gap: 10px; }
      .erpw-manager-readiness-group { display: grid; gap: 8px; border: 1px solid #edf2f7; border-radius: 13px; padding: 11px; background: #fbfdff; }
      .erpw-manager-readiness-group-head { display: flex; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: wrap; }
      .erpw-manager-readiness-group-title { color: #0f172a; font-size: 13px; font-weight: 790; }
      @media (max-width: 760px) { .erpw-readiness-row { grid-template-columns: 1fr; align-items: start; } .erpw-readiness-action { justify-self: start; } }
    `;
    document.head.appendChild(style);
  }

  function severityLabel(severity) {
    const value = String(severity || "info").toLowerCase();
    if (value === "critical") return "Critical";
    if (value === "warning") return "Warning";
    if (value === "ready") return "Ready";
    return "Info";
  }

  function summaryChips(summary) {
    const counts = summary || {};
    return ["critical", "warning", "info", "ready"].map((severity) => {
      const count = Number(counts[severity] || 0);
      if (!count) return "";
      return `<span class="erpw-readiness-chip ${severity}">${count} ${escapeHtml(severityLabel(severity))}</span>`;
    }).join("") || '<span class="erpw-readiness-chip ready">Ready</span>';
  }

  function renderIssue(issue) {
    const fixRoute = issue && issue.fix_route && Object.keys(issue.fix_route).length ? issue.fix_route : null;
    const fixLabel = issue && issue.fix_label ? String(issue.fix_label) : "";
    return `
      <div class="erpw-readiness-row" data-procurement-readiness-issue data-readiness-severity="${escapeHtml(issue.severity || "info")}" data-readiness-group="${escapeHtml(issue.group || "")}">
        <div class="erpw-readiness-row-main">
          <div class="erpw-readiness-row-title"><span class="erpw-readiness-chip ${escapeHtml(issue.severity || "info")}">${escapeHtml(severityLabel(issue.severity))}</span>${escapeHtml(issue.title || "Readiness issue")}</div>
          <div class="erpw-readiness-row-detail">${escapeHtml(issue.detail || "Review this record before future governed action.")}</div>
          <div class="erpw-readiness-row-source">${escapeHtml(issue.group_label || issue.group || "Readiness")} ? ${escapeHtml(issue.source_name || issue.source_type || "Record")}</div>
        </div>
        ${fixRoute && fixLabel ? `<button type="button" class="erpw-readiness-action" data-procurement-readiness-route="${routePayload(fixRoute)}">${escapeHtml(fixLabel)}</button>` : ""}
      </div>
    `;
  }

  function renderReadinessCard(context, options) {
    ensureStyles();
    const cfg = options || {};
    const issues = Array.isArray(context && context.issues) ? context.issues : [];
    const title = cfg.title || "Readiness Review";
    const note = cfg.note || "Read-only guidance for future governed procurement steps.";
    const empty = context && context.empty_message ? context.empty_message : "No readiness issues found for current checks.";
    return `
      <section class="erpw-readiness-card" data-procurement-readiness-card>
        <div class="erpw-readiness-top">
          <div>
            <div class="erpw-readiness-title">${escapeHtml(title)}</div>
            <div class="erpw-readiness-note">${escapeHtml(note)}</div>
          </div>
          <div class="erpw-readiness-summary">${summaryChips(context && context.summary)}</div>
        </div>
        <div class="erpw-readiness-list">
          ${issues.length ? issues.map(renderIssue).join("") : `<div class="erpw-readiness-empty">${escapeHtml(empty)}</div>`}
        </div>
      </section>
    `;
  }

  function renderManagerReadiness(readiness) {
    ensureStyles();
    if (!readiness || !readiness.visible) return "";
    const groups = Array.isArray(readiness.groups) ? readiness.groups : [];
    return `
      <section class="sales-console-card sales-console-section erpw-manager-readiness" data-section-key="manager-readiness" data-procurement-manager-readiness>
        <div class="sales-console-section-head">
          <div>
            <h2 class="sales-console-section-title">Manager Readiness</h2>
            <div class="sales-console-section-note">Readiness exceptions and productized fix paths</div>
          </div>
          <div class="erpw-readiness-summary">${summaryChips(readiness.summary)}</div>
        </div>
        <div class="erpw-manager-readiness-grid">
          ${groups.length ? groups.map((group) => `
            <div class="erpw-manager-readiness-group" data-procurement-readiness-group="${escapeHtml(group.key || "")}">
              <div class="erpw-manager-readiness-group-head">
                <div class="erpw-manager-readiness-group-title">${escapeHtml(group.label || "Readiness")}</div>
                <div class="erpw-readiness-summary">${summaryChips(group.summary)}</div>
              </div>
              <div class="erpw-readiness-list">${(Array.isArray(group.issues) ? group.issues : []).map(renderIssue).join("")}</div>
            </div>
          `).join("") : `<div class="erpw-readiness-empty">${escapeHtml(readiness.empty_message || "No readiness issues found for current checks.")}</div>`}
        </div>
      </section>
    `;
  }

  function executeRoute(target) {
    if (!target || typeof target !== "object") return;
    if (target.kind === "worklist" && target.queue_key) {
      frappe.route_options = target.filters && Object.keys(target.filters).length ? target.filters : {};
      return frappe.set_route(WORKLIST_ROUTE, String(target.queue_key || "").replace(/_/g, "-"));
    }
    if (target.kind === "report_page" && target.report_key) {
      frappe.route_options = target.filters && Object.keys(target.filters).length ? target.filters : {};
      return frappe.set_route(REPORT_ROUTE, String(target.report_key || "").replace(/_/g, "-"));
    }
    if (target.kind === "page" && target.route) {
      frappe.route_options = target.options || {};
      const parts = [target.route].concat(Array.isArray(target.route_parts) ? target.route_parts : []);
      return frappe.set_route.apply(frappe, parts);
    }
  }

  function bindReadinessLinks(root) {
    const $root = root && root.jquery ? root : $(root || document);
    $root.find("[data-procurement-readiness-route]").off("click.readiness").on("click.readiness", function () {
      executeRoute(parseRoutePayload(this.getAttribute("data-procurement-readiness-route")));
    });
  }

  window.erpWorkspaceUiProcurementReadiness = {
    renderReadinessCard,
    renderManagerReadiness,
    bindReadinessLinks,
  };
})();
