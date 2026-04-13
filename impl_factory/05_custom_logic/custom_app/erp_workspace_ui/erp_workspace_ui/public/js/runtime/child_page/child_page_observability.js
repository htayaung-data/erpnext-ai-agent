(function () {
  const root = window;
  const childPageRuntime = root.erpWorkspaceUiChildPage = root.erpWorkspaceUiChildPage || {};
  const childPageHelpers = childPageRuntime.helpers || {};

  function shouldLogDiagnostics() {
    try {
      return Boolean(root.localStorage && root.localStorage.getItem("erpw-ui-debug") === "1");
    } catch (error) {
      return false;
    }
  }

  function getDiagnosticsState(frm) {
    if (!frm) return { features: {} };
    if (!frm.__erpwDiagnostics) {
      frm.__erpwDiagnostics = {
        features: {},
        startedAt: Date.now(),
        updatedAt: null,
      };
    }
    return frm.__erpwDiagnostics;
  }

  function normalizeFeatureKey(feature) {
    const normalized = String(feature == null ? "" : feature)
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/^_+|_+$/g, "");
    return normalized || "feature";
  }

  function getDiagnosticRoot(frm) {
    const getFormRoot = childPageHelpers.getFormRoot;
    if (typeof getFormRoot === "function") {
      const $root = getFormRoot(frm);
      if ($root.length) return $root;
    }

    const $wrapper = $(frm && (frm.wrapper || frm.$wrapper) || []);
    if ($wrapper.length) return $wrapper;

    return $(frm && frm.page && frm.page.main ? frm.page.main : []);
  }

  function applyDiagnosticMarker(frm, feature, status) {
    const $root = getDiagnosticRoot(frm);
    if (!$root.length) return;

    const dataKey = normalizeFeatureKey(feature).replace(/_/g, "-");
    $root.attr(`data-erpw-diag-${dataKey}`, status);
  }

  function logDiagnostic(feature, status, meta) {
    if (!shouldLogDiagnostics() || !root.console || typeof root.console.debug !== "function") return;
    root.console.debug("[erpw-child-page]", feature, status, meta || {});
  }

  function markFeatureStatus(frm, feature, status, meta) {
    if (!frm || !feature || !status) return false;

    const diagnostics = getDiagnosticsState(frm);
    const key = normalizeFeatureKey(feature);
    const entry = diagnostics.features[key] || {
      attempts: 0,
      readyCount: 0,
      missingCount: 0,
      lastStatus: null,
      lastMeta: null,
      lastAt: null,
      firstReadyAt: null,
      lastReadyAt: null,
      firstMissingAt: null,
      lastMissingAt: null,
    };
    const now = Date.now();

    entry.attempts += 1;
    entry.lastStatus = status;
    entry.lastMeta = meta || null;
    entry.lastAt = now;

    if (status === "ready") {
      entry.readyCount += 1;
      if (!entry.firstReadyAt) entry.firstReadyAt = now;
      entry.lastReadyAt = now;
    } else if (status === "missing") {
      entry.missingCount += 1;
      if (!entry.firstMissingAt) entry.firstMissingAt = now;
      entry.lastMissingAt = now;
    }

    diagnostics.features[key] = entry;
    diagnostics.updatedAt = now;

    applyDiagnosticMarker(frm, key, status);
    logDiagnostic(key, status, meta);
    return status === "ready";
  }

  function markFeatureReady(frm, feature, meta) {
    return markFeatureStatus(frm, feature, "ready", meta);
  }

  function markFeatureMissing(frm, feature, meta) {
    return markFeatureStatus(frm, feature, "missing", meta);
  }

  function getDiagnosticSnapshot(frm) {
    const diagnostics = getDiagnosticsState(frm);
    return JSON.parse(JSON.stringify(diagnostics));
  }

  childPageRuntime.observability = Object.assign({}, childPageRuntime.observability || {}, {
    getDiagnosticSnapshot,
    getDiagnosticsState,
    markFeatureMissing,
    markFeatureReady,
    markFeatureStatus,
  });
})();
