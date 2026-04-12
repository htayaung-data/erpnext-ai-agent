(function () {
  const root = window;
  const childPageRuntime = root.erpWorkspaceUiChildPage = root.erpWorkspaceUiChildPage || {};
  const childPageHelpers = childPageRuntime.helpers || {};

  function scheduleEnhancePasses(frm, run, options) {
    const scheduleFormTask = childPageHelpers.scheduleFormTask;
    if (typeof scheduleFormTask !== "function" || typeof run !== "function") return;

    const fastKey = options && options.fastKey ? options.fastKey : "enhance_form_body_fast";
    const lateKey = options && options.lateKey ? options.lateKey : "enhance_form_body_late";
    const fastDelay = options && options.fastDelay != null ? options.fastDelay : 0;
    const lateDelay = options && options.lateDelay != null ? options.lateDelay : 180;

    scheduleFormTask(frm, fastKey, fastDelay, () => run(frm));
    scheduleFormTask(frm, lateKey, lateDelay, () => run(frm));
  }

  function scheduleRetryPair(frm, options) {
    const scheduleFormTask = childPageHelpers.scheduleFormTask;
    if (typeof scheduleFormTask !== "function" || !options || typeof options.run !== "function") return;

    const fastKey = options.fastKey;
    const lateKey = options.lateKey;
    const fastDelay = options.fastDelay != null ? options.fastDelay : 420;
    const lateDelay = options.lateDelay != null ? options.lateDelay : 980;

    if (fastKey) {
      scheduleFormTask(frm, fastKey, fastDelay, () => options.run(frm));
    }
    if (lateKey) {
      scheduleFormTask(frm, lateKey, lateDelay, () => options.run(frm));
    }
  }

  function runRetriedEnhancers(frm, steps) {
    if (!Array.isArray(steps)) return;

    steps.forEach((step) => {
      if (!step || typeof step.run !== "function") return;
      if (!step.run(frm)) {
        scheduleRetryPair(frm, step);
      }
    });
  }

  function bindTabEnhancers(frm, options) {
    if (!frm || !options || typeof options.run !== "function") return;

    const $root = $(frm.page && frm.page.main ? frm.page.main : frm.$wrapper || []);
    if (!$root.length) return;

    const $links = $root.find(".form-tabs-list .nav-link, .form-tabs .nav-link");
    if (!$links.length) return;

    const namespace = options.namespace || ".erpwChildPageTabs";

    $links.off(namespace).on(`click${namespace}`, function () {
      scheduleEnhancePasses(frm, options.run, {
        fastKey: options.fastKey,
        lateKey: options.lateKey,
        fastDelay: options.fastDelay,
        lateDelay: options.lateDelay,
      });
    });
  }

  childPageRuntime.runtime = Object.assign({}, childPageRuntime.runtime || {}, {
    bindTabEnhancers,
    runRetriedEnhancers,
    scheduleEnhancePasses,
    scheduleRetryPair,
  });
})();
