(function () {
  const root = window;
  const childPageRuntime = root.erpWorkspaceUiChildPage = root.erpWorkspaceUiChildPage || {};
  const childPageHelpers = childPageRuntime.helpers || {};

  const escapeHtml = childPageHelpers.escapeHtml || function (value) {
    return frappe.utils.escape_html(value == null ? "" : String(value));
  };

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

  function isManagedDraftDocType(frm) {
    return !!(frm && (frm.doctype === "Sales Order" || frm.doctype === "Quotation"));
  }

  function resolveSidebarNodes(frm) {
    const $wrapper = $(frm && (frm.wrapper || frm.$wrapper) || []);
    const $sidebar = $(frm && frm.page && frm.page.sidebar ? frm.page.sidebar : $wrapper.find(".form-sidebar").first());
    const $surface = $sidebar.length
      ? ($sidebar.closest(".layout-side-section, .page-sidebar, .sidebar-column, .form-sidebar").first().length
        ? $sidebar.closest(".layout-side-section, .page-sidebar, .sidebar-column, .form-sidebar").first()
        : $sidebar.parent())
      : $();
    const $metaSection = $sidebar.length
      ? $sidebar.find(".sidebar-section.text-muted.border-top.pt-3").first()
      : $();
    return { $sidebar, $surface, $metaSection };
  }

  function hasDraftReadiness(draftReadiness) {
    return !!(draftReadiness && Array.isArray(draftReadiness.items) && draftReadiness.items.length);
  }

  function storeDraftState(frm, options) {
    if (!frm) return null;
    if (options && Object.prototype.hasOwnProperty.call(options, "draftReadiness")) {
      frm.__erpwDraftReadiness = options.draftReadiness || null;
    }
    if (options && Object.prototype.hasOwnProperty.call(options, "draftReadinessPlacement")) {
      frm.__erpwDraftReadinessPlacement = options.draftReadinessPlacement || null;
    }
    return frm.__erpwDraftReadiness || null;
  }

  function buildDraftSupportRailMarkup(draftReadiness) {
    if (!hasDraftReadiness(draftReadiness)) return "";

    const summary = String(draftReadiness.summary || "").trim();
    const note = String(draftReadiness.note || "").trim();

    return `
      <aside class="erpw-child-card erpw-child-draft-rail erpw-draft-support-rail">
        <div class="erpw-child-draft-rail-head">
          <div class="erpw-child-draft-rail-copy">
            <div class="erpw-child-section-title">${escapeHtml(draftReadiness.title || "Draft Readiness")}</div>
            ${note ? `<div class="erpw-child-draft-rail-note">${escapeHtml(note)}</div>` : ""}
          </div>
          ${summary ? `<div class="erpw-child-draft-progress">${escapeHtml(summary)}</div>` : ""}
        </div>
        <div class="erpw-child-draft-rail-list">
          ${draftReadiness.items.map((item) => `
            <article class="erpw-child-draft-rail-item ${escapeHtml(item.tone || "neutral")}">
              <div class="erpw-child-draft-rail-item-copy">
                <div class="erpw-child-draft-rail-item-title">${escapeHtml(item.title || "")}</div>
                <div class="erpw-child-draft-rail-item-value">${escapeHtml(item.value || "--")}</div>
              </div>
              ${item.status ? `<span class="erpw-child-draft-status ${escapeHtml(item.tone || "neutral")}">${escapeHtml(item.status)}</span>` : ""}
            </article>
          `).join("")}
        </div>
      </aside>
    `;
  }

  function restoreSidebarSurface(frm, $target, $sidebar) {
    if ($target.length) {
      $target.removeClass("erpw-draft-sidebar-surface erpw-draft-sidebar-hidden").css("display", "");
      $target.find(".erpw-draft-support-rail").remove();
      $target.find(".erpw-draft-native-sidebar-hidden").each(function () {
        $(this).removeClass("erpw-draft-native-sidebar-hidden").css("display", "").removeAttr("aria-hidden");
      });
    }

    if ($sidebar.length) {
      $sidebar.removeClass("erpw-draft-sidebar-hidden erpw-draft-native-sidebar-hidden").css("display", "").removeAttr("aria-hidden");
    }

    if (frm) {
      frm.__erpwDraftRailMounted = false;
    }
  }

  function hideNativeSidebarNodes($target, $sidebar) {
    if ($target.length) {
      $target.children().not(".erpw-draft-support-rail").each(function () {
        $(this).addClass("erpw-draft-native-sidebar-hidden").css("display", "none").attr("aria-hidden", "true");
      });
    }

    if ($sidebar.length) {
      $sidebar.addClass("erpw-draft-native-sidebar-hidden").css("display", "none").attr("aria-hidden", "true");
    }
  }

  function renderDraftSupportRail(frm, $target, draftReadiness) {
    if (!$target.length || !hasDraftReadiness(draftReadiness)) {
      if (frm) frm.__erpwDraftRailMounted = false;
      return false;
    }

    const markup = buildDraftSupportRailMarkup(draftReadiness);
    if (!markup) {
      if (frm) frm.__erpwDraftRailMounted = false;
      return false;
    }

    $target.find(".erpw-draft-support-rail").remove();
    $target.prepend(markup);

    if (frm) {
      frm.__erpwDraftRailMounted = true;
    }
    return true;
  }

  function syncSidebarSurface(frm, options) {
    const draftReadiness = storeDraftState(frm, options);
    const { $sidebar, $surface, $metaSection } = resolveSidebarNodes(frm);
    if (!$sidebar.length && !$surface.length) {
      if (frm) frm.__erpwDraftRailMounted = false;
      markFeatureMissing(frm, "sidebar_cleanup", { reason: "no_sidebar" });
      return false;
    }

    const $target = $surface.length ? $surface : $sidebar;
    const hideDraftSidebar = !!(
      frm
      && typeof frm.is_new === "function"
      && frm.is_new()
      && isManagedDraftDocType(frm)
    );

    if (hideDraftSidebar) {
      const wantsSidebarRail = String(frm && frm.__erpwDraftReadinessPlacement || "").toLowerCase() === "sidebar_rail";
      if (wantsSidebarRail && hasDraftReadiness(draftReadiness)) {
        restoreSidebarSurface(frm, $target, $sidebar);
        $target.addClass("erpw-draft-sidebar-surface").removeClass("erpw-draft-sidebar-hidden").css("display", "");
        const mounted = renderDraftSupportRail(frm, $target, draftReadiness);
        hideNativeSidebarNodes($target, $sidebar);
        markFeatureReady(frm, "sidebar_cleanup", {
          mode: mounted ? "draft_sidebar_rail" : "draft_sidebar_hidden",
          readinessItems: Array.isArray(draftReadiness.items) ? draftReadiness.items.length : 0,
        });
        return mounted;
      }

      restoreSidebarSurface(frm, $target, $sidebar);
      $target.addClass("erpw-draft-sidebar-hidden").css("display", "none");
      if ($sidebar.length) {
        $sidebar.addClass("erpw-draft-sidebar-hidden").css("display", "none").attr("aria-hidden", "true");
      }
      markFeatureReady(frm, "sidebar_cleanup", { mode: "draft_sidebar_hidden" });
      return false;
    }

    restoreSidebarSurface(frm, $target, $sidebar);

    if ($metaSection.length) {
      $metaSection.addClass("erpw-so-sidebar-meta-hidden").hide();
      markFeatureReady(frm, "sidebar_cleanup", { mode: "meta_section_hidden", hiddenSections: 1 });
      return true;
    }

    markFeatureReady(frm, "sidebar_cleanup", { mode: "restored_without_meta" });
    return true;
  }

  function cleanSidebarUtilityRail(frm, options) {
    return syncSidebarSurface(frm, options);
  }

  childPageRuntime.sidebar = Object.assign({}, childPageRuntime.sidebar || {}, {
    cleanSidebarUtilityRail,
    syncSidebarSurface,
  });
})();
