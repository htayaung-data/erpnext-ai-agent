/* global $ */

(function () {
  let navigationPendingTimer = null;

  function clearNavigationPending() {
    if (navigationPendingTimer) {
      clearTimeout(navigationPendingTimer);
      navigationPendingTimer = null;
    }
    $("[data-erpw-nav-pending=\"true\"]").each(function () {
      const $target = $(this);
      $target.attr("data-erpw-nav-pending", "false").removeClass("is-pending").prop("disabled", false).removeAttr("aria-busy");
      const originalLabel = $target.attr("data-erpw-nav-original-label");
      if (originalLabel) {
        const $sideLabel = $target.find(".sales-console-queue-side-label").first();
        if ($sideLabel.length) $sideLabel.text(originalLabel);
        const $badge = $target.find("[data-role=badge]").first();
        if ($badge.length) $badge.text(originalLabel);
        $target.removeAttr("data-erpw-nav-original-label");
      }
    });
  }

  function armNavigationPendingReset() {
    if (navigationPendingTimer) {
      clearTimeout(navigationPendingTimer);
    }
    navigationPendingTimer = setTimeout(clearNavigationPending, 6000);
  }

  function markNavigationPending($target) {
    clearNavigationPending();
    if (!$target || !$target.length) return;
    $target.attr("data-erpw-nav-pending", "true").addClass("is-pending").prop("disabled", true).attr("aria-busy", "true");
    const $sideLabel = $target.find(".sales-console-queue-side-label").first();
    if ($sideLabel.length) {
      $target.attr("data-erpw-nav-original-label", $sideLabel.text());
      $sideLabel.text("Opening...");
    } else {
      const $badge = $target.find("[data-role=badge]").first();
      if ($badge.length) {
        $target.attr("data-erpw-nav-original-label", $badge.text());
        $badge.text("Opening");
      }
    }
    armNavigationPendingReset();
  }

  window.addEventListener("hashchange", clearNavigationPending);
  window.addEventListener("popstate", clearNavigationPending);
  function escapeHtml(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function iconMarkup(name) {
    const icons = {
      home: `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.85" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M4 10.5L12 4l8 6.5"></path>
          <path d="M6.5 9.5V20h11V9.5"></path>
        </svg>
      `,
      search: `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.85" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <circle cx="11" cy="11" r="6"></circle>
          <path d="M20 20l-4.2-4.2"></path>
        </svg>
      `,
      notification: `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.85" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M18 9a6 6 0 1 0-12 0c0 7-2.5 7.5-2.5 7.5h17S18 16 18 9"></path>
          <path d="M9.8 20a2.4 2.4 0 0 0 4.4 0"></path>
        </svg>
      `,
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
      review: `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.85" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M12 3l7 3.5V12c0 4.4-2.9 7.7-7 9-4.1-1.3-7-4.6-7-9V6.5L12 3z"></path>
          <path d="M9.5 12l1.7 1.7L15 10"></path>
        </svg>
      `,
      save: `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.85" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M5 4.5h11l3 3V19.5H5z"></path>
          <path d="M8 4.5v6h7v-6"></path>
          <path d="M9 15.5h6"></path>
        </svg>
      `,
      print: `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.85" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M7 8V4.5h10V8"></path>
          <path d="M6.5 18.5h11v-5h-11z"></path>
          <path d="M5 10h14a2 2 0 0 1 2 2v4H3v-4a2 2 0 0 1 2-2z"></path>
        </svg>
      `,
      email: `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.85" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M4 6.5h16v11H4z"></path>
          <path d="M4.5 7l7.5 6l7.5-6"></path>
        </svg>
      `,
      assign: `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.85" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M12 12a3.5 3.5 0 1 0 0-7a3.5 3.5 0 0 0 0 7z"></path>
          <path d="M5.5 20a6.5 6.5 0 0 1 13 0"></path>
          <path d="M18.5 6.5h4"></path>
          <path d="M20.5 4.5v4"></path>
        </svg>
      `,
      comment: `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.85" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M5 6.5h14v9H9l-4 3z"></path>
        </svg>
      `,
      share: `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.85" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <circle cx="6" cy="12" r="2"></circle>
          <circle cx="18" cy="6" r="2"></circle>
          <circle cx="18" cy="18" r="2"></circle>
          <path d="M8 11l8-4"></path>
          <path d="M8 13l8 4"></path>
        </svg>
      `,
      follow_up: `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.85" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M20 6L9 17l-5-5"></path>
        </svg>
      `,
      invoice: `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.85" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M7 3.5h7l4 4v13H7z"></path>
          <path d="M14 3.5v4h4"></path>
          <path d="M10 12h5"></path>
          <path d="M10 15.5h5"></path>
          <path d="M10 19h3"></path>
        </svg>
      `,
      return_doc: `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.85" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M9 7H5v4"></path>
          <path d="M5 11a7 7 0 1 0 2.1-5"></path>
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

  function makeAction(config) {
    const variantClass = config.primary ? "primary" : "secondary";
    const actionTier = config.tier || (config.primary ? "primary" : "secondary");
    const $button = $(`
      <button class="sales-console-action ${variantClass}" data-action-key="${escapeHtml(config.key)}" data-action-tier="${escapeHtml(actionTier)}" type="button">
        <span class="sales-console-action-icon">${iconMarkup(config.icon || "square")}</span>
        <span class="sales-console-action-copy">
          <span class="sales-console-action-title">${escapeHtml(config.title)}</span>
          <span class="sales-console-action-meta">${escapeHtml(config.meta)}</span>
        </span>
      </button>
    `);
    $button.on("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      if (typeof config.onClick === "function") config.onClick(event);
    });
    return $button;
  }

  function makeQueueItem(config) {
    const badgeClass = config.badgeClass || "pending";
    const sideLabel = config.sideLabel || "Open";
    if (config.priority) {
      const $priority = $(`
        <button class="sales-console-queue-card priority" data-queue-key="${escapeHtml(config.key)}" type="button">
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
            <div class="sales-console-queue-side-label">${escapeHtml(sideLabel)}</div>
          </div>
        </button>
      `);
      $priority.on("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        markNavigationPending($priority);
        try {
          if (typeof config.onClick === "function") config.onClick(event);
        } catch (error) {
          clearNavigationPending();
          throw error;
        }
      });
      return $priority;
    }

    const $row = $(`
      <button class="sales-console-queue-card regular" data-queue-key="${escapeHtml(config.key)}" type="button">
        <div class="sales-console-queue-main">
          <div class="sales-console-queue-title">${escapeHtml(config.title)}</div>
          <div class="sales-console-queue-meta" data-role="meta">${escapeHtml(config.meta)}</div>
        </div>
        <div class="sales-console-queue-side">
          <div class="sales-console-queue-count" data-role="count">--</div>
          <div class="sales-console-queue-side-label">${escapeHtml(sideLabel)}</div>
        </div>
      </button>
    `);
    $row.on("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      markNavigationPending($row);
      try {
        if (typeof config.onClick === "function") config.onClick(event);
      } catch (error) {
        clearNavigationPending();
        throw error;
      }
    });
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
    $row.on("click", (event) => {
      markNavigationPending($row);
      try {
        onClick(event);
      } catch (error) {
        clearNavigationPending();
        throw error;
      }
    });
    return $row;
  }

  function renderReportsSection($root, reportCards, options) {
    const config = options || {};
    const sectionSelector = config.sectionSelector || '[data-section="reports"]';
    const linkContainerSelector = config.linkContainerSelector || ".sales-console-report-links";
    const onSelect = typeof config.onSelect === "function" ? config.onSelect : function () {};
    const $section = $root.find(sectionSelector);
    const $reportLinks = $root.find(linkContainerSelector);
    $reportLinks.empty();

    if (!Array.isArray(reportCards) || !reportCards.length) {
      $section.hide();
      return;
    }

    $section.show();
    reportCards.forEach((card) => {
      $reportLinks.append(
        makeReportLink(
          card.key,
          card.title,
          card.meta,
          card.icon,
          (event) => onSelect(card, event)
        )
      );
    });
  }

  function metricValueText(metric) {
    if (!metric) return "--";
    if (metric.state === "restricted") return "LOCK";
    if (metric.state === "unavailable") return "N/A";
    if (metric.value == null) return "--";
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
    if (metric.state === "unavailable") {
      return { text: "Unavailable", className: "pending" };
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

  function hydrateKnownMetrics($root, payload) {
    const queueSources = {
      sales_orders_pending_fulfillment: (payload.work || {}).sales_orders_pending_fulfillment,
      quotations_waiting_action: (payload.work || {}).quotations_waiting_action,
      expiring_quotations: (payload.work || {}).expiring_quotations,
      customer_follow_up_tasks: (payload.work || {}).customer_follow_up_tasks,
      orders_due_soon: (payload.lifecycle || {}).orders_due_soon,
      partially_delivered_orders: (payload.lifecycle || {}).partially_delivered_orders,
      invoices_outstanding: (payload.lifecycle || {}).invoices_outstanding,
      sales_returns_in_progress: (payload.lifecycle || {}).sales_returns_in_progress,
      orders_blocked_by_approval: (payload.blockers || {}).orders_blocked_by_approval,
      quotations_awaiting_approval: (payload.blockers || {}).quotations_awaiting_approval,
    };

    Object.entries(queueSources).forEach(([key, metric]) => {
      if (metric) applyQueueMetric($root, key, metric);
    });

    const insightSources = {
      awaiting_approval: (payload.insights || {}).awaiting_approval,
      open_orders: (payload.insights || {}).open_orders,
    };
    Object.entries(insightSources).forEach(([key, metric]) => {
      if (metric) applyInsightMetric($root, key, metric);
    });
  }

  function reorderChildren($container, order, attributeName) {
    if (!Array.isArray(order) || !order.length) return;

    const children = $container.children().get();
    const byKey = new Map(children.map((element) => [element.getAttribute(attributeName), element]));

    order.forEach((key) => {
      const element = byKey.get(key);
      if (element) {
        $container.append(element);
      }
    });
  }

  function applyActionOrder($root, order) {
    if (!Array.isArray(order) || !order.length) return;

    const elements = $root.find("[data-action-key]").get();
    const byKey = new Map(elements.map((element) => [element.getAttribute("data-action-key"), element]));
    const arranged = [];

    order.forEach((key) => {
      const element = byKey.get(key);
      if (element) {
        arranged.push(element);
        byKey.delete(key);
      }
    });

    byKey.forEach((element) => arranged.push(element));

    const $primary = $root.find(".sales-console-action-strip.primary");
    const $secondary = $root.find(".sales-console-action-strip.secondary");
    $(elements).detach();
    $primary.empty();
    $secondary.empty();

    const primaryTier = [];
    const secondaryTier = [];
    arranged.forEach((element) => {
      if (element.getAttribute("data-action-tier") === "secondary") {
        secondaryTier.push(element);
      } else {
        primaryTier.push(element);
      }
    });

    primaryTier.forEach((element, index) => {
      if (index < 3) {
        $primary.append(element);
      } else {
        $secondary.append(element);
      }
    });
    secondaryTier.forEach((element) => $secondary.append(element));
  }

  function rebalanceActionStrips($root) {
    const $primary = $root.find(".sales-console-action-strip.primary");
    const $secondary = $root.find(".sales-console-action-strip.secondary");
    const $actions = $root.find("[data-action-key]");
    if (!$actions.length) return;

    const visible = [];
    const hidden = [];

    $actions.each((_, element) => {
      if ($(element).css("display") === "none") {
        hidden.push(element);
      } else {
        visible.push(element);
      }
    });

    $actions.detach();
    $primary.empty();
    $secondary.empty();

    const visiblePrimary = [];
    const visibleSecondary = [];
    visible.forEach((element) => {
      if (element.getAttribute("data-action-tier") === "secondary") {
        visibleSecondary.push(element);
      } else {
        visiblePrimary.push(element);
      }
    });

    visiblePrimary.forEach((element, index) => {
      if (index < 3) {
        $primary.append(element);
      } else {
        $secondary.append(element);
      }
    });
    visibleSecondary.forEach((element) => $secondary.append(element));
    hidden.forEach((element) => {
      $secondary.append(element);
    });

    const primaryVisibleCount = Math.min(visiblePrimary.length, 3);
    const secondaryVisibleCount = Math.max(visiblePrimary.length - 3, 0) + visibleSecondary.length;

    const primaryColumns = Math.max(primaryVisibleCount, 1);
    $primary.css("grid-template-columns", `repeat(${primaryColumns}, minmax(0, 1fr))`);

    if (secondaryVisibleCount > 0) {
      const secondaryColumns = Math.min(Math.max(secondaryVisibleCount, 1), 2);
      $secondary.css("grid-template-columns", `repeat(${secondaryColumns}, minmax(0, 1fr))`);
      $secondary.removeAttr("hidden");
    } else {
      $secondary.attr("hidden", true);
    }
  }

  window.erpWorkspaceConsoleRuntime = Object.assign(window.erpWorkspaceConsoleRuntime || {}, {
    escapeHtml,
    iconMarkup,
    makeAction,
    makeQueueItem,
    makeInsightCard,
    makeReportLink,
    renderReportsSection,
    metricValueText,
    metricBadge,
    applyQueueMetric,
    applyInsightMetric,
    hydrateKnownMetrics,
    reorderChildren,
    applyActionOrder,
    rebalanceActionStrips,
  });
})();
