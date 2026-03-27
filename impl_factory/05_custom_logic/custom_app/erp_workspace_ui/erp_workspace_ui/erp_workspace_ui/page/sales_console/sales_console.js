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
        padding-bottom: 24px;
      }
      .sales-console-card {
        background: var(--fg-color);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        box-shadow: var(--shadow-xs);
      }
      .sales-console-header {
        display: grid;
        grid-template-columns: minmax(0, 1.6fr) minmax(280px, 0.9fr);
        gap: 16px;
        padding: 20px;
        background:
          radial-gradient(circle at top right, rgba(191, 83, 41, 0.16), transparent 34%),
          linear-gradient(135deg, #fffdf8 0%, #fff7eb 100%);
      }
      .sales-console-kicker {
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #9a3412;
        margin-bottom: 8px;
      }
      .sales-console-title {
        font-size: 28px;
        line-height: 1.1;
        font-weight: 700;
        color: #431407;
        margin: 0 0 8px;
      }
      .sales-console-subtitle {
        font-size: 14px;
        line-height: 1.6;
        color: #7c2d12;
        margin: 0;
        max-width: 64ch;
      }
      .sales-console-scope {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 14px;
      }
      .sales-console-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 10px;
        border-radius: 999px;
        border: 1px solid rgba(154, 52, 18, 0.18);
        background: rgba(255, 255, 255, 0.7);
        font-size: 12px;
        color: #7c2d12;
      }
      .sales-console-brief {
        padding: 18px;
        background: rgba(255, 255, 255, 0.78);
      }
      .sales-console-brief-title {
        font-size: 13px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #9a3412;
        margin-bottom: 10px;
      }
      .sales-console-brief-list {
        display: grid;
        gap: 10px;
        margin: 0;
        padding: 0;
        list-style: none;
      }
      .sales-console-brief-list li {
        padding: 10px 12px;
        border-radius: 12px;
        background: rgba(255, 247, 237, 0.9);
        border: 1px solid rgba(191, 83, 41, 0.14);
        color: #7c2d12;
        font-size: 13px;
        line-height: 1.5;
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
      }
      .sales-console-section-title {
        font-size: 17px;
        font-weight: 700;
        color: var(--heading-color);
        margin: 0;
      }
      .sales-console-section-note {
        font-size: 12px;
        color: var(--text-muted);
      }
      .sales-console-actions {
        display: grid;
        grid-template-columns: repeat(5, minmax(0, 1fr));
        gap: 12px;
      }
      .sales-console-action {
        border: 1px solid var(--border-color);
        border-radius: 14px;
        padding: 16px 14px;
        background: linear-gradient(180deg, #ffffff 0%, #fcfcfd 100%);
        cursor: pointer;
        text-align: left;
        transition: border-color 120ms ease, transform 120ms ease, box-shadow 120ms ease;
      }
      .sales-console-action:hover {
        border-color: #f97316;
        box-shadow: 0 10px 25px rgba(124, 45, 18, 0.08);
        transform: translateY(-1px);
      }
      .sales-console-action-title {
        display: block;
        font-size: 14px;
        font-weight: 700;
        color: #7c2d12;
        margin-bottom: 6px;
      }
      .sales-console-action-meta {
        font-size: 12px;
        line-height: 1.5;
        color: var(--text-muted);
      }
      .sales-console-grid {
        display: grid;
        grid-template-columns: minmax(0, 1.6fr) minmax(290px, 0.9fr);
        gap: 16px;
      }
      .sales-console-list {
        display: grid;
        gap: 10px;
      }
      .sales-console-list-item {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 12px;
        padding: 14px;
        border: 1px solid var(--border-color);
        border-radius: 14px;
        background: #fff;
        cursor: pointer;
        text-align: left;
      }
      .sales-console-list-item:hover {
        border-color: #fdba74;
      }
      .sales-console-list-title {
        font-size: 14px;
        font-weight: 700;
        color: var(--heading-color);
        margin: 0 0 4px;
      }
      .sales-console-list-meta {
        font-size: 12px;
        color: var(--text-muted);
        line-height: 1.5;
      }
      .sales-console-badge {
        display: inline-flex;
        align-items: center;
        padding: 4px 8px;
        border-radius: 999px;
        font-size: 11px;
        font-weight: 700;
        white-space: nowrap;
      }
      .sales-console-badge.attention {
        background: #fff7ed;
        color: #c2410c;
      }
      .sales-console-badge.blocker {
        background: #fef2f2;
        color: #b91c1c;
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
        background: #f8fafc;
        color: #334155;
      }
      .sales-console-mini-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 12px;
      }
      .sales-console-mini-card {
        padding: 14px;
        border-radius: 14px;
        border: 1px solid var(--border-color);
        background: #fff;
      }
      .sales-console-mini-label {
        font-size: 12px;
        color: var(--text-muted);
        margin-bottom: 8px;
      }
      .sales-console-mini-value {
        font-size: 26px;
        font-weight: 700;
        color: var(--heading-color);
        line-height: 1;
        margin-bottom: 8px;
      }
      .sales-console-mini-meta {
        font-size: 12px;
        color: var(--text-muted);
        line-height: 1.5;
      }
      .sales-console-ai {
        background:
          radial-gradient(circle at top right, rgba(30, 64, 175, 0.12), transparent 34%),
          linear-gradient(180deg, #f8fbff 0%, #f3f7fc 100%);
      }
      .sales-console-ai-state {
        padding: 14px;
        border-radius: 14px;
        border: 1px solid rgba(29, 78, 216, 0.12);
        background: rgba(255, 255, 255, 0.82);
        margin-bottom: 10px;
      }
      .sales-console-ai-state:last-child {
        margin-bottom: 0;
      }
      .sales-console-ai-title {
        font-size: 14px;
        font-weight: 700;
        color: #1e3a8a;
        margin-bottom: 6px;
      }
      .sales-console-ai-copy {
        font-size: 12px;
        line-height: 1.6;
        color: #334155;
      }
      .sales-console-report-links {
        display: grid;
        gap: 10px;
      }
      .sales-console-link {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        padding: 13px 14px;
        border: 1px solid var(--border-color);
        border-radius: 14px;
        background: #fff;
        cursor: pointer;
        text-align: left;
      }
      .sales-console-link:hover {
        border-color: #fdba74;
      }
      @media (max-width: 1200px) {
        .sales-console-actions {
          grid-template-columns: repeat(3, minmax(0, 1fr));
        }
      }
      @media (max-width: 980px) {
        .sales-console-header,
        .sales-console-grid {
          grid-template-columns: 1fr;
        }
        .sales-console-actions,
        .sales-console-mini-grid {
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }
      }
      @media (max-width: 640px) {
        .sales-console-actions,
        .sales-console-mini-grid {
          grid-template-columns: 1fr;
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
      if (filters) {
        frappe.set_route("List", doctype, filters);
      } else {
        frappe.set_route("List", doctype);
      }
    } catch (error) {
      frappe.msgprint({
        title: __("Navigation unavailable"),
        message: __("Could not open {0}.", [doctype]),
        indicator: "orange",
      });
    }
  }

  function routeToReport(reportName) {
    try {
      frappe.set_route("query-report", reportName);
    } catch (error) {
      frappe.msgprint({
        title: __("Report unavailable"),
        message: __("Could not open {0}.", [reportName]),
        indicator: "orange",
      });
    }
  }

  function makeAction(config) {
    const $button = $(`
      <button class="sales-console-action" data-action-key="${escapeHtml(config.key)}">
        <span class="sales-console-action-title">${escapeHtml(config.title)}</span>
        <span class="sales-console-action-meta">${escapeHtml(config.meta)}</span>
      </button>
    `);
    $button.on("click", config.onClick);
    return $button;
  }

  function makeQueueItem(config) {
    const badgeClass = config.badgeClass || "pending";
    const $row = $(`
      <button class="sales-console-list-item" data-queue-key="${escapeHtml(config.key)}">
        <div>
          <div class="sales-console-list-title">${escapeHtml(config.title)}</div>
          <div class="sales-console-list-meta" data-role="meta">${escapeHtml(config.meta)}</div>
        </div>
        <span class="sales-console-badge ${badgeClass}" data-role="badge">Loading</span>
      </button>
    `);
    $row.on("click", config.onClick);
    return $row;
  }

  function makeInsightCard(config) {
    return $(`
      <div class="sales-console-mini-card" data-insight-key="${escapeHtml(config.key)}">
        <div class="sales-console-mini-label">${escapeHtml(config.label)}</div>
        <div class="sales-console-mini-value" data-role="value">--</div>
        <div class="sales-console-mini-meta" data-role="meta">${escapeHtml(config.meta)}</div>
      </div>
    `);
  }

  function makeReportLink(title, meta, onClick) {
    const $row = $(`
      <button class="sales-console-link">
        <div>
          <div class="sales-console-list-title">${escapeHtml(title)}</div>
          <div class="sales-console-list-meta">${escapeHtml(meta)}</div>
        </div>
        <span class="sales-console-badge review">Open</span>
      </button>
    `);
    $row.on("click", onClick);
    return $row;
  }

  function metricValueText(metric) {
    if (!metric || metric.value == null) return "--";
    return String(metric.value);
  }

  function metricBadge(metric) {
    if (!metric) {
      return { text: "Pending", className: "pending" };
    }
    if (metric.state === "live") {
      return { text: metricValueText(metric), className: metric.badgeClass || "attention" };
    }
    if (metric.state === "restricted") {
      return { text: "Restricted", className: "restricted" };
    }
    return { text: "Pending", className: "pending" };
  }

  function applyQueueMetric($root, key, metric) {
    const $item = $root.find(`[data-queue-key="${key}"]`);
    if (!$item.length) return;

    const badge = metricBadge(metric);
    const $badge = $item.find('[data-role="badge"]');
    $badge
      .removeClass("attention blocker review pending restricted")
      .addClass(badge.className)
      .text(badge.text);

    if (metric && metric.note) {
      $item.find('[data-role="meta"]').text(metric.note);
    }
  }

  function applyInsightMetric($root, key, metric) {
    const $card = $root.find(`[data-insight-key="${key}"]`);
    if (!$card.length) return;

    $card.find('[data-role="value"]').text(metricValueText(metric));

    if (metric && metric.note) {
      $card.find('[data-role="meta"]').text(metric.note);
    }
  }

  function applyContext($root, context) {
    if (!context) return;

    if (context.user_display_name) {
      $root.find('[data-context="user"]').text(`User: ${context.user_display_name}`);
    }
    if (context.primary_role) {
      $root.find('[data-context="role"]').text(`Role family: ${context.primary_role}`);
    }
    if (context.branch_label) {
      $root.find('[data-context="branch"]').text(`Branch context: ${context.branch_label}`);
    } else if (context.branch_note) {
      $root.find('[data-context="branch"]').text(`Branch context: ${context.branch_note}`);
    }
  }

  function applyScope($root, scope) {
    if (!scope) return;

    if (scope.scope_label) {
      $root.find('[data-context="scope"]').text(`Scope: ${scope.scope_label}`);
    }
  }

  function reorderChildren($container, order, attributeName) {
    if (!Array.isArray(order) || !order.length) return;

    const children = $container.children().get();
    const byKey = new Map(
      children.map(element => [element.getAttribute(attributeName), element])
    );

    order.forEach(key => {
      const element = byKey.get(key);
      if (element) {
        $container.append(element);
      }
    });
  }

  function applyUiProfile($root, profile) {
    if (!profile) return;

    if (profile.mode_label) {
      $root.find('[data-role="mode-label"]').text(`Commercial Workspace | ${profile.mode_label}`);
    }
    if (profile.summary_note) {
      $root.find('[data-role="summary-note"]').text(profile.summary_note);
    }
    if (Array.isArray(profile.brief_points) && profile.brief_points.length) {
      const $list = $root.find('[data-role="brief-list"]');
      $list.empty();
      profile.brief_points.forEach(point => {
        $list.append(`<li>${escapeHtml(point)}</li>`);
      });
    }

    if (Array.isArray(profile.action_order)) {
      reorderChildren($root.find(".sales-console-actions"), profile.action_order, "data-action-key");
    }
    if (Array.isArray(profile.queue_order)) {
      reorderChildren($root.find(".sales-console-list"), profile.queue_order, "data-queue-key");
    }

    const hiddenActions = new Set(profile.hidden_actions || []);
    $root.find("[data-action-key]").each((_, element) => {
      const $element = $(element);
      const key = $element.attr("data-action-key");
      $element.toggle(!hiddenActions.has(key));
    });

    const hiddenInsights = new Set(profile.hidden_insights || []);
    $root.find("[data-insight-key]").each((_, element) => {
      const $element = $(element);
      const key = $element.attr("data-insight-key");
      $element.toggle(!hiddenInsights.has(key));
    });

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

  async function loadBootstrap($root) {
    try {
      const response = await frappe.call({
        method: BOOTSTRAP_METHOD,
      });

      const payload = response && response.message ? response.message : {};
      applyContext($root, payload.context || {});
      applyScope($root, payload.scope || {});
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

    const userName = frappe.session && frappe.session.user_fullname
      ? frappe.session.user_fullname
      : frappe.session.user;

    const $root = $('<div class="sales-console-shell"></div>');

    const $header = $(`
      <section class="sales-console-card sales-console-header">
        <div>
          <div class="sales-console-kicker" data-role="mode-label">Commercial Workspace</div>
          <h1 class="sales-console-title">Sales Console</h1>
          <p class="sales-console-subtitle" data-role="summary-note">
            Action-first commercial workspace for quotation, order follow-up, customer review,
            and blocker visibility. This slice adds guarded live data for queue and insight
            surfaces without forcing unapproved business logic into the page.
          </p>
          <div class="sales-console-scope">
            <span class="sales-console-pill" data-context="user">User: ${escapeHtml(userName || "Current User")}</span>
            <span class="sales-console-pill" data-context="branch">Branch context: resolving</span>
            <span class="sales-console-pill" data-context="role">Role family: sales</span>
            <span class="sales-console-pill" data-context="scope">Scope: resolving</span>
            <span class="sales-console-pill">AI assist: reserved, compact, secondary</span>
          </div>
        </div>
        <aside class="sales-console-card sales-console-brief">
          <div class="sales-console-brief-title">Today At A Glance</div>
          <ul class="sales-console-brief-list" data-role="brief-list">
            <li>Start with quotations needing follow-up, then review blocked commercial cases.</li>
            <li>Use full ERP transaction pages for quotation and sales order creation.</li>
            <li>Keep invoice ownership in Finance while preserving sales-side visibility where needed.</li>
          </ul>
        </aside>
      </section>
    `);

    const $actionsSection = $(`
      <section class="sales-console-card sales-console-section" data-section="actions">
        <div class="sales-console-section-head">
          <h2 class="sales-console-section-title">Quick Actions</h2>
          <div class="sales-console-section-note" data-section-note="actions">Primary one-click entry points</div>
        </div>
        <div class="sales-console-actions"></div>
      </section>
    `);

    const $actions = $actionsSection.find(".sales-console-actions");
    $actions.append(
      makeAction({
        key: "new_opportunity",
        title: "New Opportunity",
        meta: "Open full opportunity form",
        onClick: () => frappe.new_doc("Opportunity"),
      }),
      makeAction({
        key: "new_quotation",
        title: "New Quotation",
        meta: "Open full quotation form",
        onClick: () => frappe.new_doc("Quotation"),
      }),
      makeAction({
        key: "new_sales_order",
        title: "New Sales Order",
        meta: "Open full sales order form",
        onClick: () => frappe.new_doc("Sales Order"),
      }),
      makeAction({
        key: "open_customer",
        title: "Open Customer",
        meta: "Go to customer list and records",
        onClick: () => routeToList("Customer"),
      }),
      makeAction({
        key: "open_item",
        title: "Open Item",
        meta: "Go to item list and records",
        onClick: () => routeToList("Item"),
      })
    );

    const $mainGrid = $('<div class="sales-console-grid"></div>');
    const $leftColumn = $('<div class="sales-console-shell"></div>');
    const $rightColumn = $('<div class="sales-console-shell"></div>');

    const $workSection = $(`
      <section class="sales-console-card sales-console-section" data-section="work">
        <div class="sales-console-section-head">
          <h2 class="sales-console-section-title">My Sales Work</h2>
          <div class="sales-console-section-note" data-section-note="work">Queue-first execution and review</div>
        </div>
        <div class="sales-console-list"></div>
      </section>
    `);

    const $workList = $workSection.find(".sales-console-list");
    $workList.append(
      makeQueueItem({
        key: "quotations_waiting_action",
        title: "Quotations Waiting For Action",
        meta: "Review pending customer reply, needed revision, and active follow-up items.",
        badgeClass: "attention",
        onClick: () => routeToList("Quotation"),
      }),
      makeQueueItem({
        key: "expiring_quotations",
        title: "Open Quotations Nearing Expiry",
        meta: "Focus on expiring commercial opportunities before they fall out of cycle.",
        badgeClass: "attention",
        onClick: () => routeToList("Quotation"),
      }),
      makeQueueItem({
        key: "sales_orders_pending_fulfillment",
        title: "Sales Orders Pending Fulfillment",
        meta: "Check fulfillment visibility and intervene when customer commitments are at risk.",
        badgeClass: "review",
        onClick: () => routeToList("Sales Order"),
      }),
      makeQueueItem({
        key: "orders_blocked_by_approval",
        title: "Orders Blocked By Approval",
        meta: "Open blocked commercial cases where approval or control action is still pending.",
        badgeClass: "blocker",
        onClick: () => routeToList("Sales Order"),
      }),
      makeQueueItem({
        key: "customer_follow_up_tasks",
        title: "Customer Follow-Up Tasks",
        meta: "Work promised callbacks, quote chasing, and inactive customer recovery.",
        badgeClass: "attention",
        onClick: () => routeToList("ToDo"),
      })
    );

    const $reportSection = $(`
      <section class="sales-console-card sales-console-section" data-section="reports">
        <div class="sales-console-section-head">
          <h2 class="sales-console-section-title">Reports And Review</h2>
          <div class="sales-console-section-note" data-section-note="reports">Deep review after operational triage</div>
        </div>
        <div class="sales-console-report-links"></div>
      </section>
    `);

    const $reportLinks = $reportSection.find(".sales-console-report-links");
    $reportLinks.append(
      makeReportLink("Sales Analytics", "Commercial performance review", () => routeToReport("Sales Analytics")),
      makeReportLink("Customer-wise Sales History", "Account-level commercial history", () => routeToReport("Customer-wise Sales History")),
      makeReportLink("Item-wise Sales Register", "Item-level sales performance review", () => routeToReport("Item-wise Sales Register")),
      makeReportLink("Open Orders", "Review active order pipeline", () => routeToList("Sales Order"))
    );

    const $insightSection = $(`
      <section class="sales-console-card sales-console-section" data-section="insights">
        <div class="sales-console-section-head">
          <h2 class="sales-console-section-title">Sales Insight</h2>
          <div class="sales-console-section-note" data-section-note="insights">Lightweight operational signals</div>
        </div>
        <div class="sales-console-mini-grid"></div>
      </section>
    `);

    const $insightGrid = $insightSection.find(".sales-console-mini-grid");
    $insightGrid.append(
      makeInsightCard({
        key: "quotations_awaiting_approval",
        label: "Awaiting Approval",
        meta: "Loading approval-aware quotation signal.",
      }),
      makeInsightCard({
        key: "open_orders",
        label: "Open Orders",
        meta: "Loading active order pipeline count.",
      }),
      makeInsightCard({
        key: "credit_risk_flags",
        label: "Credit-Risk Flags",
        meta: "Reserved for finance-approved commercial exposure contract.",
      }),
      makeInsightCard({
        key: "customers_needing_follow_up",
        label: "Customers Needing Follow-Up",
        meta: "Loading follow-up visibility where supported by current contract.",
      })
    );

    const $aiSection = $(`
      <section class="sales-console-card sales-console-section sales-console-ai" data-section="ai">
        <div class="sales-console-section-head">
          <h2 class="sales-console-section-title">AI Assist</h2>
          <div class="sales-console-section-note" data-section-note="ai">Reserved, compact, and secondary</div>
        </div>
        <div class="sales-console-ai-state">
          <div class="sales-console-ai-title">Today</div>
          <div class="sales-console-ai-copy">
            Reserved for a compact daily sales briefing after assistant embedding is approved for this workspace.
          </div>
        </div>
        <div class="sales-console-ai-state">
          <div class="sales-console-ai-title">Customer Context</div>
          <div class="sales-console-ai-copy">
            Reserved for short customer briefing and next-best-action guidance, never as the main path to work.
          </div>
        </div>
        <div class="sales-console-ai-state">
          <div class="sales-console-ai-title">Quotation Context</div>
          <div class="sales-console-ai-copy">
            Reserved for approval-risk and follow-up explanation after the quote page contract is defined.
          </div>
        </div>
      </section>
    `);

    $leftColumn.append($workSection, $reportSection);
    $rightColumn.append($insightSection, $aiSection);
    $mainGrid.append($leftColumn, $rightColumn);

    $root.append($header, $actionsSection, $mainGrid);
    $(page.body).empty().append($root);

    loadBootstrap($root);
  }

  frappe.pages[PAGE_KEY] = frappe.pages[PAGE_KEY] || {};
  frappe.pages[PAGE_KEY].on_page_load = function (wrapper) {
    render(wrapper);
  };
})();
