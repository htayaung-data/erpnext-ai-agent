(function () {
  const root = window;
  const childPageRuntime = root.erpWorkspaceUiChildPage = root.erpWorkspaceUiChildPage || {};

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

  function cleanSidebarUtilityRail(frm) {
    const $wrapper = $(frm && (frm.wrapper || frm.$wrapper) || []);
    const $sidebar = $(frm && frm.page && frm.page.sidebar ? frm.page.sidebar : $wrapper.find(".form-sidebar").parent());
    if (!$sidebar.length) {
      markFeatureMissing(frm, "sidebar_cleanup", { reason: "no_sidebar" });
      return false;
    }

    const $metaSection = $sidebar.find(".sidebar-section.text-muted.border-top.pt-3").first();
    if (!$metaSection.length) {
      markFeatureMissing(frm, "sidebar_cleanup", { reason: "no_meta_section" });
      return false;
    }

    $metaSection.addClass("erpw-so-sidebar-meta-hidden").hide();
    markFeatureReady(frm, "sidebar_cleanup", { hiddenSections: 1 });
    return true;
  }

  childPageRuntime.sidebar = Object.assign({}, childPageRuntime.sidebar || {}, {
    cleanSidebarUtilityRail,
  });
})();
