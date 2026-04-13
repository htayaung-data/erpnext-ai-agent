(function () {
  const root = window;
  const childPageRuntime = root.erpWorkspaceUiChildPage = root.erpWorkspaceUiChildPage || {};
  const childPageHelpers = childPageRuntime.helpers || {};

  function getObservability() {
    return (root.erpWorkspaceUiChildPage && root.erpWorkspaceUiChildPage.observability) || {};
  }

  function markFeatureReady(frm, feature, meta) {
    const observability = getObservability();
    if (typeof observability.markFeatureReady === "function") {
      return observability.markFeatureReady(frm, feature, meta);
    }
    return false;
  }

  function markFeatureMissing(frm, feature, meta) {
    const observability = getObservability();
    if (typeof observability.markFeatureMissing === "function") {
      return observability.markFeatureMissing(frm, feature, meta);
    }
    return false;
  }

  function updateSupportToggleLabel($shell) {
    const $button = $shell.find(".erpw-so-support-toggle");
    if (!$button.length) return;

    const expanded = $shell.hasClass("is-activity-expanded");
    $button.attr("aria-expanded", expanded ? "true" : "false");
    $button.find(".erpw-so-support-toggle-text").text(
      expanded ? "Collapse Activity" : "Show Full Activity"
    );
  }

  function updateSupportNote($footer, commentCount, activityCount, previewCount) {
    const summary = [
      `${commentCount} comment${commentCount === 1 ? "" : "s"}`,
      `${activityCount} activit${activityCount === 1 ? "y" : "ies"}`,
      activityCount > previewCount
        ? `showing latest ${previewCount}`
        : "all visible",
    ];

    $footer.find(".erpw-so-support-note").text(summary.join(" • "));
  }

  function applyActivityPreview($footer) {
    const $timeline = $footer.find(".new-timeline").first();
    if (!$timeline.length) return false;

    const $timelineItems = $timeline.find(".timeline-items").last();
    if (!$timelineItems.length) return false;

    const $items = $timelineItems.children(".timeline-item");
    if (!$items.length) return false;

    $items.removeClass("erpw-so-activity-hidden");
    const previewLimit = 3;
    const hasOverflow = $items.length > previewLimit;
    const expanded = $footer.hasClass("is-activity-expanded");

    $items.each((index, element) => {
      if (index >= previewLimit && !expanded) {
        $(element).addClass("erpw-so-activity-hidden");
      }
    });

    $timeline.find(".show-all-activity").hide();
    $footer.toggleClass("has-activity-overflow", hasOverflow);

    return {
      activityCount: $items.length,
      previewCount: Math.min(previewLimit, $items.length),
      hasOverflow,
    };
  }

  function ensureSupportHead($footer) {
    if (!$footer || !$footer.length) return $();

    let $head = $footer.find(".erpw-so-support-head").first();
    if (!$head.length) {
      $head = $(`
        <div class="erpw-so-support-head">
          <div class="erpw-so-support-copy">
            <div class="erpw-so-support-title">Activity & Comments</div>
            <div class="erpw-so-support-note">Keep the current discussion visible without letting the full audit trail dominate the page.</div>
          </div>
          <button type="button" class="erpw-so-support-toggle" aria-expanded="false">
            <span class="erpw-so-support-toggle-text">Show Full Activity</span>
            <span class="erpw-so-support-toggle-icon" aria-hidden="true"></span>
          </button>
        </div>
      `);
      $footer.prepend($head);
    }

    return $head;
  }

  function enhanceSupportArea(frm) {
    const $wrapper = $(frm && (frm.wrapper || frm.$wrapper) || []);
    if (!$wrapper.length) {
      markFeatureMissing(frm, "support_shell", { reason: "no_wrapper" });
      return false;
    }

    const $footer = $wrapper.find(".form-footer").first();
    if (!$footer.length) {
      markFeatureMissing(frm, "support_shell", { reason: "no_footer" });
      return false;
    }

    $footer.addClass("erpw-so-support-shell");
    $footer.find(".comment-box").addClass("erpw-so-comment-block");
    $footer.find(".new-timeline, .timeline").addClass("erpw-so-timeline-block");

    const $head = ensureSupportHead($footer);
    $head.find(".erpw-so-support-toggle").off(".erpwSupportToggle").on("click.erpwSupportToggle", () => {
      $footer.toggleClass("is-activity-expanded");
      const preview = applyActivityPreview($footer);
      if (preview) {
        const docinfo = frm && frm.get_docinfo ? frm.get_docinfo() : {};
        const commentCount = Array.isArray(docinfo.comments) ? docinfo.comments.length : 0;
        updateSupportNote($footer, commentCount, preview.activityCount, preview.previewCount);
      }
      updateSupportToggleLabel($footer);
    });

    const docinfo = frm && frm.get_docinfo ? frm.get_docinfo() : {};
    const commentCount = Array.isArray(docinfo.comments) ? docinfo.comments.length : 0;

    if (!$footer.data("erpwActivityInit")) {
      $footer.removeClass("is-activity-expanded");
      $footer.data("erpwActivityInit", 1);
    }

    const preview = applyActivityPreview($footer);
    if (preview) {
      updateSupportNote($footer, commentCount, preview.activityCount, preview.previewCount);
    }
    updateSupportToggleLabel($footer);
    $footer.find(".erpw-so-support-toggle").toggle($footer.hasClass("has-activity-overflow"));
    markFeatureReady(frm, "support_shell", {
      hasOverflow: $footer.hasClass("has-activity-overflow"),
    });
    return true;
  }

  function getWorkflowBannerMarkup(options) {
    const escapeHtml = childPageHelpers.escapeHtml || function (value) {
      return frappe.utils.escape_html(value == null ? "" : String(value));
    };
    const title = options && options.title ? options.title : "Workflow-controlled record";
    const note = options && options.note
      ? options.note
      : "This record is currently review-only in the active workflow state.";

    return `
      <div class="erpw-so-workflow-banner">
        <span class="erpw-so-workflow-banner-icon" aria-hidden="true">
          <svg viewBox="0 0 24 24">
            <path d="M8 10V8a4 4 0 1 1 8 0v2M7.5 10h9a1 1 0 0 1 1 1v7a1 1 0 0 1-1 1h-9a1 1 0 0 1-1-1v-7a1 1 0 0 1 1-1z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </span>
        <div class="erpw-so-workflow-banner-copy">
          <div class="erpw-so-workflow-banner-title">${escapeHtml(title)}</div>
          <div class="erpw-so-workflow-banner-note">${escapeHtml(note)}</div>
        </div>
      </div>
    `;
  }

  function normalizeWorkflowMessageText(value) {
    return String(value == null ? "" : value)
      .replace(/\s+/g, " ")
      .trim()
      .toLowerCase();
  }

  function matchesWorkflowReadonlyMessage(text, options) {
    const normalized = normalizeWorkflowMessageText(text);
    if (!normalized) return false;

    const exactMessages = [];
    if (options && options.targetMessage) {
      exactMessages.push(options.targetMessage);
    }
    if (options && Array.isArray(options.targetMessages)) {
      exactMessages.push(...options.targetMessages);
    }

    if (
      exactMessages
        .map(normalizeWorkflowMessageText)
        .filter(Boolean)
        .includes(normalized)
    ) {
      return true;
    }

    const includeFragments = options && Array.isArray(options.targetIncludes)
      ? options.targetIncludes
      : [];
    if (
      includeFragments
        .map(normalizeWorkflowMessageText)
        .filter(Boolean)
        .some((fragment) => normalized.includes(fragment))
    ) {
      return true;
    }

    const hasWorkflowSignal = normalized.includes("workflow");
    const hasReadonlySignal = [
      "not editable",
      "read only",
      "read-only",
      "readonly",
      "review only",
      "review-only",
      "cannot edit",
      "can't edit",
    ].some((fragment) => normalized.includes(fragment));

    return hasWorkflowSignal && hasReadonlySignal;
  }

  function findWorkflowReadonlyMessage($messages, options) {
    const $existing = $messages.filter(".erpw-so-workflow-banner-shell").first();
    if ($existing.length) return $existing;

    return $messages.filter((_, element) => {
      return matchesWorkflowReadonlyMessage($(element).text(), options);
    }).first();
  }

  function enhanceWorkflowReadonlyBanner(frm, options) {
    const $root = $(frm && frm.page && frm.page.main ? frm.page.main : frm && frm.$wrapper || []);
    if (!$root.length) {
      markFeatureMissing(frm, "workflow_banner", { reason: "no_root" });
      return false;
    }

    const $container = $root.find(".form-message-container").first();
    if (!$container.length) {
      markFeatureMissing(frm, "workflow_banner", { reason: "no_message_container" });
      return false;
    }

    const $messages = $container.find(".form-message");
    if (!$messages.length) {
      markFeatureMissing(frm, "workflow_banner", { reason: "no_messages" });
      return false;
    }

    const $workflowMessage = findWorkflowReadonlyMessage($messages, Object.assign({
      targetMessage: "This form is not editable due to a Workflow.",
    }, options || {}));

    if (!$workflowMessage.length) {
      markFeatureMissing(frm, "workflow_banner", { reason: "no_workflow_message_match" });
      return false;
    }

    $container.addClass("erpw-so-workflow-banner-container");
    $workflowMessage
      .removeClass("blue yellow orange green red white")
      .addClass("white erpw-so-workflow-banner-shell");

    if (!$workflowMessage.find(".erpw-so-workflow-banner").length) {
      $workflowMessage.html(getWorkflowBannerMarkup(options));
    }

    markFeatureReady(frm, "workflow_banner", {
      title: options && options.title ? options.title : "Workflow-controlled record",
    });
    return true;
  }

  childPageRuntime.support = Object.assign({}, childPageRuntime.support || {}, {
    enhanceSupportArea,
    enhanceWorkflowReadonlyBanner,
  });
})();
