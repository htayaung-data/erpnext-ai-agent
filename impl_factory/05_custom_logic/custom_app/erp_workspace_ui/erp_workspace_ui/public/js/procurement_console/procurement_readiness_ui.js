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
      .erpw-readiness-chip.is-zero { border-color: #e2e8f0; background: #f8fafc; color: #64748b; }
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
      .erpw-manager-readiness .sales-console-section-head { align-items: flex-start; }
      .erpw-manager-readiness-copy { flex: 1 1 560px; min-width: 360px; }
      .erpw-manager-readiness-copy .sales-console-section-note { max-width: 680px; text-align: left; }
      .erpw-manager-readiness-severity { display: flex; gap: 7px; align-items: center; justify-content: flex-end; flex-wrap: wrap; }
      .erpw-manager-readiness-severity .erpw-readiness-chip { min-height: 27px; }
      .erpw-manager-readiness-layout { display: grid; grid-template-columns: minmax(310px, 0.82fr) minmax(420px, 1.18fr); gap: 12px; align-items: start; }
      .erpw-manager-readiness-groups { display: grid; grid-template-columns: 1fr; gap: 8px; }
      .erpw-manager-readiness-category { display: grid; gap: 7px; min-height: 82px; border: 1px solid #e2ebf5; border-radius: 12px; padding: 12px; background: #fbfdff; box-sizing: border-box; box-shadow: inset 3px 0 0 #f59e0b; }
      .erpw-manager-readiness-category.has-critical { border-color: #fecaca; box-shadow: inset 3px 0 0 #dc2626; }
      .erpw-manager-readiness-category.has-warning { border-color: #fde2b8; background: #fffdf8; }
      .erpw-manager-readiness-category.has-info { border-color: #bfdbfe; box-shadow: inset 3px 0 0 #2563eb; }
      .erpw-manager-readiness-category-title { color: #0f172a; font-size: 12.6px; font-weight: 800; line-height: 1.2; }
      .erpw-manager-readiness-category .erpw-readiness-chip { min-height: 22px; padding: 0 7px; font-size: 11px; }
      .erpw-manager-readiness-category-status { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
      .erpw-manager-readiness-category-status .erpw-readiness-chip.clear { border-color: #d9eadf; background: #f3faf6; color: #166534; }
      .erpw-manager-readiness-category-preview { color: #64748b; font-size: 11.5px; line-height: 1.28; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
      .erpw-manager-readiness-clear-line { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; color: #64748b; font-size: 11.6px; line-height: 1.3; }
      .erpw-manager-readiness-clear-title { display: inline-flex; align-items: center; min-height: 23px; color: #475569; font-size: 11px; font-weight: 800; letter-spacing: .03em; text-transform: uppercase; margin-right: 2px; }
      .erpw-manager-readiness-clear-pill { display: inline-flex; align-items: center; min-height: 23px; padding: 0 8px; border-radius: 999px; border: 1px solid #d9eadf; background: #f5fbf7; color: #166534; font-size: 11.2px; font-weight: 740; white-space: nowrap; }
      .erpw-manager-readiness-clear-pill::before { content: ""; width: 6px; height: 6px; border-radius: 999px; background: #22c55e; margin-right: 6px; }
      .erpw-manager-readiness-hero { display: flex; justify-content: space-between; gap: 14px; align-items: flex-start; border: 1px solid #dbe8f5; border-radius: 13px; padding: 13px 14px; background: linear-gradient(180deg, #fbfdff 0%, #f7fbff 100%); box-shadow: inset 0 1px 0 rgba(255,255,255,.7); }
      .erpw-manager-readiness-hero-copy { display: grid; gap: 6px; min-width: 0; }
      .erpw-manager-readiness-hero-main { display: flex; align-items: baseline; gap: 9px; flex-wrap: wrap; color: #0f172a; line-height: 1.2; font-weight: 820; }
      .erpw-manager-readiness-hero-count { display: inline-flex; align-items: baseline; color: #10233f; font-size: 19px; font-weight: 880; letter-spacing: 0; line-height: 1; }
      .erpw-manager-readiness-hero-text { display: inline-flex; min-width: 0; color: #17243a; font-size: 14.3px; font-weight: 820; letter-spacing: 0; }
      .erpw-manager-readiness-hero-main.is-clear .erpw-manager-readiness-hero-count { color: #166534; font-size: 15px; }
      .erpw-manager-readiness-hero-note { color: #475569; font-size: 12.1px; line-height: 1.35; max-width: 860px; }
      .erpw-manager-readiness-hero-actions { display: flex; justify-content: flex-end; flex: 0 0 auto; }
      .erpw-manager-readiness-top { display: grid; gap: 8px; }
      .erpw-manager-readiness-top-head { display: flex; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: wrap; color: #334155; font-size: 12px; font-weight: 760; }
      .erpw-manager-readiness-top .erpw-readiness-row { padding: 9px 10px; }
      .erpw-manager-readiness-actions { display: flex; align-items: center; gap: 8px; justify-content: flex-end; flex-wrap: wrap; }
      .erpw-manager-readiness-toggle { min-height: 33px; border: 1px solid #173b66; border-radius: 9px; background: #173b66; color: #fff; font-weight: 790; font-size: 12px; padding: 0 12px; white-space: nowrap; box-shadow: 0 5px 12px rgba(23,59,102,0.14); }
      .erpw-manager-readiness-toggle:hover { border-color: #0f2f55; background: #0f2f55; }
      .erpw-manager-readiness-toggle.is-secondary { border-color: #d5e2ef; background: #fff; color: #12365f; box-shadow: none; }
      .erpw-manager-readiness-toggle.is-secondary:hover { border-color: #9db7d2; background: #f8fbff; }
      .erpw-manager-readiness-expanded { display: grid; gap: 10px; border-top: 1px solid #edf2f7; padding-top: 12px; max-height: min(460px, 58vh); overflow: auto; overscroll-behavior: contain; padding-right: 3px; }
      .erpw-manager-readiness-expanded[hidden] { display: none !important; }
      .erpw-manager-readiness-group { display: grid; gap: 8px; border: 1px solid #edf2f7; border-radius: 13px; padding: 11px; background: #fbfdff; }
      .erpw-manager-readiness-group-head { display: flex; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: wrap; }
      .erpw-manager-readiness-group-title { color: #0f172a; font-size: 13px; font-weight: 790; }
      .erpw-manager-readiness.is-loading .erpw-readiness-empty, .erpw-manager-readiness.is-error .erpw-readiness-empty { min-height: 58px; display: flex; align-items: center; }
      .erpw-readiness-skeleton-line { display: block; height: 10px; border-radius: 999px; background: linear-gradient(90deg, #e8eef6 0%, #f6f9fc 45%, #e8eef6 100%); background-size: 180% 100%; animation: erpwReadinessPulse 1.35s ease-in-out infinite; }
      .erpw-readiness-skeleton-line.short { width: 42%; }
      .erpw-readiness-skeleton-line.medium { width: 64%; }
      @keyframes erpwReadinessPulse { 0% { background-position: 0% 0; } 100% { background-position: -180% 0; } }
      @media (max-width: 1280px) { .erpw-manager-readiness-layout { grid-template-columns: 1fr; } .erpw-manager-readiness-top { order: -1; } }
      @media (max-width: 920px) { .erpw-manager-readiness-hero { display: grid; } .erpw-manager-readiness-hero-actions { justify-content: flex-start; } }
      @media (max-width: 640px) { .erpw-manager-readiness-copy { min-width: 0; } .erpw-manager-readiness-groups { grid-template-columns: 1fr; } }
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
          <div class="erpw-readiness-row-source">${escapeHtml(issue.group_label || issue.group || "Readiness")} - ${escapeHtml(issue.source_name || issue.source_type || "Record")}</div>
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

  const MANAGER_READINESS_CATEGORIES = [
    { key: 'supplier_readiness', label: 'Supplier readiness', groups: ['supplier_readiness'] },
    { key: 'item_readiness', label: 'Item buying readiness', groups: ['item_readiness'] },
    { key: 'rfq_communication', label: 'RFQ communication', groups: ['rfq_readiness'] },
    { key: 'document_quality', label: 'Document quality', groups: ['purchase_request_readiness', 'supplier_quotation_readiness'] },
    { key: 'order_follow_up', label: 'Order follow-up', groups: ['purchase_order_readiness'] },
  ];

  function issueSeverity(issue) {
    return String(issue && issue.severity || 'info').toLowerCase();
  }

  function issueCounts(issues) {
    return (issues || []).reduce((counts, issue) => {
      const severity = issueSeverity(issue);
      if (counts[severity] == null) counts.info += 1;
      else counts[severity] += 1;
      return counts;
    }, { critical: 0, warning: 0, info: 0, ready: 0, total: (issues || []).length });
  }

  function managerSummaryChips(summary) {
    const counts = summary || {};
    const chips = ['critical', 'warning', 'info'].map((severity) => {
      const count = Number(counts[severity] || 0);
      if (!count) return '';
      return `<span class='erpw-readiness-chip ${severity}' data-procurement-readiness-severity='${severity}'>${count} ${escapeHtml(severityLabel(severity))}</span>`;
    }).join('');
    return chips || `<span class='erpw-readiness-chip ready' data-procurement-readiness-severity='ready'>Clear</span>`;
  }

  function managerIssues(readiness) {
    return Array.isArray(readiness && readiness.issues) ? readiness.issues : [];
  }

  function issueIsQueued(issue) {
    return ['critical', 'warning', 'info'].includes(issueSeverity(issue));
  }

  function topManagerIssues(issues) {
    const queued = (issues || []).filter(issueIsQueued);
    const priority = queued.filter((issue) => issueSeverity(issue) === 'critical');
    const fallback = priority.length ? priority : queued;
    return fallback.slice(0, 3);
  }

  function categoryIssues(issues, category) {
    const groupSet = new Set(category.groups || []);
    return (issues || []).filter((issue) => groupSet.has(String(issue.group || '')));
  }

  function pluralize(count, singular, plural) {
    return `${count} ${count === 1 ? singular : (plural || `${singular}s`)}`;
  }

  function statusChipForCounts(counts) {
    const data = counts || {};
    if (data.critical) return `<span class='erpw-readiness-chip critical'>${escapeHtml(pluralize(data.critical, 'Critical'))}</span>`;
    if (data.warning) return `<span class='erpw-readiness-chip warning'>${escapeHtml(pluralize(data.warning, 'Warning'))}</span>`;
    if (data.info) return `<span class='erpw-readiness-chip info'>${escapeHtml(pluralize(data.info, 'Info'))}</span>`;
    return `<span class='erpw-readiness-chip clear'>Clear</span>`;
  }

  function categoryAdvice(category, counts) {
    if (!counts || !counts.total) return 'No current exception';
    if (category.key === 'item_readiness') return 'Review buying context before sourcing or orders.';
    if (category.key === 'supplier_readiness') return 'Review supplier buying profile before sourcing.';
    if (category.key === 'rfq_communication') return 'Review communication readiness before supplier outreach.';
    if (category.key === 'document_quality') return 'Review draft evidence before governed workflow steps.';
    if (category.key === 'order_follow_up') return 'Review buyer follow-up context for active orders.';
    return 'Review this readiness item before action.';
  }

  function readinessMessageLabel(category) {
    if (!category) return 'readiness';
    if (category.key === 'item_readiness') return 'item buying';
    if (category.key === 'supplier_readiness') return 'supplier';
    if (category.key === 'rfq_communication') return 'RFQ communication';
    if (category.key === 'document_quality') return 'document quality';
    if (category.key === 'order_follow_up') return 'order follow-up';
    return String(category.label || 'readiness').toLowerCase();
  }

  function mainReadinessSummary(categories) {
    const active = (categories || []).filter((entry) => entry.counts && entry.counts.total).sort((a, b) => {
      if (b.counts.critical !== a.counts.critical) return b.counts.critical - a.counts.critical;
      if (b.counts.warning !== a.counts.warning) return b.counts.warning - a.counts.warning;
      return b.counts.total - a.counts.total;
    })[0];
    if (!active) {
      return {
        count: 'Clear',
        text: 'No readiness exceptions need manager attention.',
        severity: 'clear',
      };
    }
    const counts = active.counts || {};
    const count = counts.critical || counts.warning || counts.info || counts.total;
    const severity = counts.critical ? 'critical' : (counts.warning ? 'warning' : 'info');
    const severityText = counts.critical
      ? (count === 1 ? 'critical issue' : 'critical issues')
      : (counts.warning ? (count === 1 ? 'warning' : 'warnings') : (count === 1 ? 'info item' : 'info items'));
    return {
      count: String(count),
      text: `${readinessMessageLabel(active.category)} ${severityText} need review`,
      severity,
    };
  }

  function renderManagerCategory(category, issues) {
    const counts = issueCounts(issues);
    if (!counts.total) return '';
    const preview = issues.find((issue) => issueSeverity(issue) === 'critical') || issues[0] || null;
    const stateClass = counts.critical ? ' has-critical' : (counts.warning ? ' has-warning' : ' has-info');
    return `
      <div class='erpw-manager-readiness-category${stateClass}' data-procurement-readiness-group-card='${escapeHtml(category.key)}'>
        <div class='erpw-manager-readiness-category-title'>${escapeHtml(category.label)}</div>
        <div class='erpw-manager-readiness-category-status'>${statusChipForCounts(counts)}</div>
        <div class='erpw-manager-readiness-category-preview'>${escapeHtml(preview ? categoryAdvice(category, counts) : 'No current exception')}</div>
      </div>
    `;
  }

  function renderManagerClearLine(entries) {
    const clearEntries = (entries || []).filter((entry) => !(entry.counts && entry.counts.total));
    if (!clearEntries.length) return '';
    return `
      <div class='erpw-manager-readiness-clear-line' data-procurement-readiness-clear-line>
        <span class='erpw-manager-readiness-clear-title'>Clear areas</span>
        ${clearEntries.map((entry) => `<span class='erpw-manager-readiness-clear-pill' data-procurement-readiness-clear-group='${escapeHtml(entry.category.key)}'>${escapeHtml(entry.category.label)} clear</span>`).join('')}
      </div>
    `;
  }

  function managerIssueReason(issue) {
    const group = String(issue && issue.group || '');
    if (group === 'item_readiness') return 'Buying context not reviewed';
    if (group === 'supplier_readiness') return 'Supplier buying profile needs review';
    if (group === 'rfq_readiness') return 'Supplier communication readiness needs review';
    if (group === 'purchase_request_readiness') return 'Request evidence needs review';
    if (group === 'supplier_quotation_readiness') return 'Quotation evidence needs review';
    if (group === 'purchase_order_readiness') return 'Order follow-up context needs review';
    return issue && issue.detail ? String(issue.detail) : 'Readiness context needs review';
  }

  function managerIssueActionLabel(issue) {
    const group = String(issue && issue.group || '');
    if (group === 'item_readiness') return 'Review item';
    if (group === 'supplier_readiness') return 'Review supplier';
    if (group === 'rfq_readiness') return 'Review RFQ';
    if (group === 'purchase_request_readiness') return 'Review request';
    if (group === 'supplier_quotation_readiness') return 'Review quotation';
    if (group === 'purchase_order_readiness') return 'Review order';
    return 'Review';
  }

  function managerIssueTitle(issue) {
    return issue && (issue.source_name || issue.title || issue.source_type) ? String(issue.source_name || issue.title || issue.source_type) : 'Readiness item';
  }

  function renderManagerIssue(issue) {
    const fixRoute = issue && issue.fix_route && Object.keys(issue.fix_route).length ? issue.fix_route : null;
    const fixLabel = managerIssueActionLabel(issue);
    return `
      <div class="erpw-readiness-row" data-procurement-readiness-issue data-readiness-severity="${escapeHtml(issue.severity || "info")}" data-readiness-group="${escapeHtml(issue.group || "")}">
        <div class="erpw-readiness-row-main">
          <div class="erpw-readiness-row-title"><span class="erpw-readiness-chip ${escapeHtml(issue.severity || "info")}">${escapeHtml(severityLabel(issue.severity))}</span>${escapeHtml(managerIssueTitle(issue))}</div>
          <div class="erpw-readiness-row-detail">${escapeHtml(managerIssueReason(issue))}</div>
          <div class="erpw-readiness-row-source">${escapeHtml(issue.group_label || issue.group || "Readiness")}</div>
        </div>
        ${fixRoute ? `<button type="button" class="erpw-readiness-action" data-procurement-readiness-route="${routePayload(fixRoute)}">${escapeHtml(fixLabel)}</button>` : ""}
      </div>
    `;
  }

  function renderExpandedManagerGroup(category, issues) {
    if (!issues.length) return '';
    return `
      <div class='erpw-manager-readiness-group' data-procurement-readiness-group='${escapeHtml(category.key)}'>
        <div class='erpw-manager-readiness-group-head'>
          <div class='erpw-manager-readiness-group-title'>${escapeHtml(category.label)}</div>
          <div class='erpw-readiness-summary'>${statusChipForCounts(issueCounts(issues))}</div>
        </div>
        <div class='erpw-readiness-list'>${issues.map(renderManagerIssue).join('')}</div>
      </div>
    `;
  }

  function renderManagerReadinessShell(content, stateClass, stateAttr) {
    return `
      <section class='sales-console-card sales-console-section erpw-manager-readiness ${escapeHtml(stateClass || '')}' data-section-key='manager-readiness' data-procurement-manager-readiness data-procurement-manager-readiness-state='${escapeHtml(stateAttr || 'ready')}' data-readiness-expanded='false'>
        ${content}
      </section>
    `;
  }

  function renderManagerReadinessLoading() {
    ensureStyles();
    return renderManagerReadinessShell(`
      <div class='sales-console-section-head'>
          <div class='erpw-manager-readiness-copy'>
          <h2 class='sales-console-section-title' data-procurement-manager-readiness-title>Readiness Review</h2>
          <div class='sales-console-section-note'>Loading manager exceptions without blocking the workbench.</div>
        </div>
      </div>
      <div class='erpw-readiness-empty'>
        <span class='erpw-readiness-skeleton-line medium'></span>
        <span class='erpw-readiness-skeleton-line short' style='margin-top:8px;'></span>
      </div>
    `, 'is-loading', 'loading');
  }

  function renderManagerReadinessError(message) {
    ensureStyles();
    return renderManagerReadinessShell(`
      <div class='sales-console-section-head'>
          <div class='erpw-manager-readiness-copy'>
          <h2 class='sales-console-section-title' data-procurement-manager-readiness-title>Readiness Review</h2>
          <div class='sales-console-section-note'>Manager exceptions could not be refreshed. The rest of the Overview remains usable.</div>
        </div>
      </div>
      <div class='erpw-readiness-empty'>${escapeHtml(message || 'Readiness review could not be loaded right now.')}</div>
    `, 'is-error', 'error');
  }

  function renderManagerReadiness(readiness) {
    ensureStyles();
    if (!readiness || !readiness.visible) return '';
    const issues = managerIssues(readiness).filter(issueIsQueued);
    const topIssues = topManagerIssues(issues);
    const hasMore = issues.length > topIssues.length;
    const categories = MANAGER_READINESS_CATEGORIES.map((category) => {
      const list = categoryIssues(issues, category);
      return { category, issues: list, counts: issueCounts(list) };
    });
    const headline = mainReadinessSummary(categories);
    const headlineText = headline.count === 'Clear' ? headline.text : `${headline.count} ${headline.text}`;
    const content = `
        <div class='sales-console-section-head'>
          <div class='erpw-manager-readiness-copy'>
            <h2 class='sales-console-section-title' data-procurement-manager-readiness-title>Readiness Review</h2>
            <div class='sales-console-section-note'>Business exceptions that need manager attention.</div>
          </div>
          <div class='erpw-manager-readiness-severity' data-procurement-readiness-severity-strip>${managerSummaryChips(readiness.summary)}</div>
        </div>
        <div class='erpw-manager-readiness-hero'>
          <div class='erpw-manager-readiness-hero-copy'>
            <div class='erpw-manager-readiness-hero-main${headline.severity === 'clear' ? ' is-clear' : ''}' data-procurement-readiness-main-message aria-label='${escapeHtml(headlineText)}'>
              <span class='erpw-manager-readiness-hero-count' data-procurement-readiness-main-count>${escapeHtml(headline.count)}</span>
              <span class='erpw-manager-readiness-hero-text' data-procurement-readiness-main-text>${escapeHtml(headline.text)}</span>
            </div>
            <div class='erpw-manager-readiness-hero-note'>Review buying context before using these records in sourcing or orders.</div>
          </div>
          <div class='erpw-manager-readiness-hero-actions'>
            ${hasMore ? `<button type='button' class='erpw-manager-readiness-toggle' data-procurement-readiness-toggle aria-expanded='false'>Review all issues</button>` : ''}
          </div>
        </div>
        ${issues.length ? `
          <div class='erpw-manager-readiness-layout'>
            <div class='erpw-manager-readiness-groups' data-procurement-readiness-group-grid>
              ${categories.map((entry) => renderManagerCategory(entry.category, entry.issues)).join('')}
              ${renderManagerClearLine(categories)}
            </div>
            <div class='erpw-manager-readiness-top' data-procurement-readiness-top-list>
              <div class='erpw-manager-readiness-top-head'>
                <span>Priority exceptions</span>
              </div>
              <div class='erpw-readiness-list'>${topIssues.map((issue) => renderManagerIssue(issue).replace('data-procurement-readiness-issue', 'data-procurement-readiness-issue data-procurement-readiness-top-issue')).join('')}</div>
            </div>
          </div>
          <div class='erpw-manager-readiness-expanded' data-procurement-readiness-expanded-list hidden>
            ${categories.map((entry) => renderExpandedManagerGroup(entry.category, entry.issues)).join('')}
          </div>
        ` : `<div class='erpw-readiness-empty'>${escapeHtml(readiness.empty_message || 'No readiness issues found for current checks.')}</div>`}
    `;
    return renderManagerReadinessShell(content, '', 'ready');
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
    $root.find('[data-procurement-readiness-route]').off('click.readiness').on('click.readiness', function () {
      executeRoute(parseRoutePayload(this.getAttribute('data-procurement-readiness-route')));
    });
    $root.find('[data-procurement-readiness-toggle]').off('click.readinessToggle').on('click.readinessToggle', function () {
      const section = this.closest('[data-procurement-manager-readiness]');
      if (!section) return;
      const expanded = section.getAttribute('data-readiness-expanded') === 'true';
      const nextExpanded = !expanded;
      section.setAttribute('data-readiness-expanded', nextExpanded ? 'true' : 'false');
      this.setAttribute('aria-expanded', nextExpanded ? 'true' : 'false');
      this.textContent = nextExpanded ? 'Show top issues' : 'Review all issues';
      this.classList.toggle('is-secondary', nextExpanded);
      const fullList = section.querySelector('[data-procurement-readiness-expanded-list]');
      if (fullList) fullList.hidden = !nextExpanded;
    });
  }

  window.erpWorkspaceUiProcurementReadiness = {
    renderReadinessCard,
    renderManagerReadiness,
    renderManagerReadinessLoading,
    renderManagerReadinessError,
    bindReadinessLinks,
  };
})();
