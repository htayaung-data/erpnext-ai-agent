/* global frappe, $ */

(function () {
  const PAGE_KEY = 'sales-console-worklist';
  const CONTEXT_METHOD = 'erp_workspace_ui.sales_console.worklist.get_sales_console_worklist_context';

  function routeToList(doctype, filters) {
    frappe.route_options = filters && Object.keys(filters).length ? filters : null;
    frappe.set_route('List', doctype);
  }

  function routeToReport(reportName, filters) {
    frappe.route_options = filters && Object.keys(filters).length ? filters : null;
    frappe.set_route('query-report', reportName);
  }

  function routeToWorklist(queueKey) {
    frappe.set_route(PAGE_KEY, String(queueKey || '').replace(/_/g, '-'));
  }

  function executeTarget(target) {
    if (!target) return;
    if (target.notice) {
      frappe.show_alert({ message: __(target.notice), indicator: 'blue' });
    }
    if (target.kind === 'new_doc' && target.doctype) return frappe.new_doc(target.doctype);
    if (target.kind === 'form' && target.doctype && target.name) return frappe.set_route('Form', target.doctype, target.name);
    if (target.kind === 'list' && target.doctype) return routeToList(target.doctype, target.filters || null);
    if (target.kind === 'report' && target.report_name) return routeToReport(target.report_name, target.filters || null);
    if (target.kind === 'worklist' && target.queue_key) return routeToWorklist(target.queue_key);
  }

  function loadingConfig(queueKey) {
    return {
      summary: {
        kicker: 'Sales Console queue',
        title: 'Loading operational list',
        subtitle: 'Reading live ERP records for ' + String(queueKey || 'this queue').replace(/_/g, ' ') + '.',
      },
      results: {
        title: 'Preparing queue',
        state: {
          kind: 'loading',
          title: 'Loading queue',
          detail: 'Pulling live operational records and permission scope.',
        },
      },
    };
  }

  function errorConfig(message) {
    return {
      summary: {
        kicker: 'Sales Console queue',
        title: 'Operational queue unavailable',
        subtitle: 'This route could not be resolved into a supported Sales Console list.',
      },
      controls: {
        actions: [
          { key: 'back_to_console', label: 'Back to Console' },
          { key: 'refresh', label: 'Retry', kind: 'primary' },
        ],
      },
      results: {
        title: 'Queue state',
        state: {
          kind: 'error',
          title: 'Queue context failed',
          detail: message || 'Live queue context could not be loaded right now.',
        },
      },
    };
  }

  function ensureHost(page, wrapper) {
    const $parent = page && page.body ? $(page.body) : $(wrapper);
    let $host = $parent.children('.erpw-sales-console-worklist-page').first();
    if (!$host.length) {
      $host = $('<section class="erpw-sales-console-worklist-page"></section>');
      $parent.empty().append($host);
    }
    return $host;
  }

  function resolveActionTarget(payload, details) {
    const targets = (payload && payload.action_targets) || {};
    if (details.scope === 'row') {
      return targets['row:' + details.rowKey + ':' + details.key] || null;
    }
    return targets[details.scope + ':' + details.key] || null;
  }

  function mountPayload(viewState, payload) {
    const runtime = window.erpWorkspaceUiListPage && window.erpWorkspaceUiListPage.shell;
    if (!runtime || typeof runtime.mountWorklist !== 'function') {
      viewState.$host.html('<div class="erpw-list-shell"><section class="erpw-child-card erpw-list-results"><div class="erpw-list-state error"><div class="erpw-list-state-title">List runtime unavailable</div><div class="erpw-list-state-detail">Shared worklist runtime is not loaded on this page.</div></div></section></div>');
      return;
    }

    runtime.mountWorklist(viewState.$host, Object.assign({}, payload || {}, {
      onAction(details) {
        if (!details) return;
        if (details.key === 'refresh') return loadRoute(viewState);
        if (details.key === 'back_to_console') return frappe.set_route('sales-console');
        executeTarget(resolveActionTarget(payload, details));
      },
    }));
  }

  function loadRoute(viewState) {
    const route = frappe.get_route ? frappe.get_route() : [];
    const queueKey = Array.isArray(route) && route.length > 1 ? String(route[1] || '').replace(/-/g, '_') : '';
    const routeSignature = Array.isArray(route) ? route.join('|') : '';
    viewState.routeSignature = routeSignature;

    if (!queueKey) {
      mountPayload(viewState, errorConfig('Open this page from a Sales Console card so the queue key is passed through.'));
      return;
    }

    mountPayload(viewState, loadingConfig(queueKey));

    frappe.call({ method: CONTEXT_METHOD, args: { queue_key: queueKey } }).then((response) => {
      if (viewState.routeSignature !== routeSignature) return;
      const payload = response && response.message ? response.message : {};
      if (viewState.page && typeof viewState.page.set_title === 'function' && payload.page && payload.page.title) {
        viewState.page.set_title(payload.page.title);
      }
      mountPayload(viewState, payload);
    }).catch((error) => {
      if (viewState.routeSignature !== routeSignature) return;
      mountPayload(viewState, errorConfig(error && error.message ? error.message : 'The operational queue could not be loaded.'));
    });
  }

  function render(wrapper) {
    const page = frappe.ui.make_app_page({
      parent: wrapper,
      title: 'Sales Console Worklist',
      single_column: true,
    });
    const viewState = {
      page,
      $host: ensureHost(page, wrapper),
      routeSignature: '',
    };
    wrapper.__erpwSalesConsoleWorklist = viewState;
    loadRoute(viewState);
  }

  frappe.pages[PAGE_KEY] = frappe.pages[PAGE_KEY] || {};
  frappe.pages[PAGE_KEY].on_page_load = function (wrapper) { render(wrapper); };
  frappe.pages[PAGE_KEY].on_page_show = function (wrapper) {
    if (wrapper && wrapper.__erpwSalesConsoleWorklist) loadRoute(wrapper.__erpwSalesConsoleWorklist);
  };
})();
