/* global frappe, $ */

(function () {
  const PAGE_KEY = 'sales-console-worklist';
  const CONTEXT_METHOD = 'erp_workspace_ui.sales_console.worklist.get_sales_console_worklist_context';
  let activeViewState = null;

  function routeToList(doctype, filters) {
    frappe.route_options = filters && Object.keys(filters).length ? filters : null;
    frappe.set_route('List', doctype);
  }

  function routeToReport(reportName, filters) {
    frappe.route_options = filters && Object.keys(filters).length ? filters : null;
    frappe.set_route('query-report', reportName);
  }

  function encodeRoutePart(value) {
    return encodeURIComponent(String(value || '').trim());
  }

  function decodeRoutePart(value) {
    try {
      return decodeURIComponent(String(value || '').trim());
    } catch (error) {
      return String(value || '').trim();
    }
  }

  function customerRouteValue(filters) {
    return filters && typeof filters === 'object' ? String(filters.customer || '').trim() : '';
  }

  function routeToWorklist(queueKey, filters) {
    const nextFilters = filters && Object.keys(filters).length ? filters : null;
    const normalizedQueueKey = String(queueKey || '').replace(/_/g, '-');
    const customer = customerRouteValue(nextFilters);
    frappe.route_options = nextFilters;
    if (['customer_detail', 'customer_editor'].includes(String(queueKey || '').replace(/-/g, '_')) && customer) {
      frappe.set_route(PAGE_KEY, normalizedQueueKey, encodeRoutePart(customer));
      return;
    }
    frappe.set_route(PAGE_KEY, normalizedQueueKey);
  }

  function resolveQueueKey(route) {
    return Array.isArray(route) && route.length > 1 ? String(route[1] || '').replace(/-/g, '_') : '';
  }

  function routeSegmentFilters(route, queueKey) {
    if (!Array.isArray(route) || !['customer_detail', 'customer_editor'].includes(queueKey) || !route[2]) return {};
    const customer = decodeRoutePart(route[2]);
    if (!customer) return {};
    return queueKey === 'customer_editor' ? { customer, mode: 'edit' } : { customer };
  }

  function consumeRouteFilters() {
    const options = frappe.route_options && typeof frappe.route_options === 'object'
      ? Object.assign({}, frappe.route_options)
      : null;
    frappe.route_options = null;
    return options;
  }

  function executeTarget(target) {
    if (!target) return;
    if (target.notice) {
      frappe.show_alert({ message: __(target.notice), indicator: 'blue' });
    }
    const routeOwner = window.erpWorkspaceUiChildPage && window.erpWorkspaceUiChildPage.helpers;
    if (
      routeOwner
      && typeof routeOwner.routeToSalesConsoleTarget === 'function'
      && routeOwner.routeToSalesConsoleTarget(target)
    ) {
      return;
    }
    if (target.kind === 'new_doc' && target.doctype) return frappe.new_doc(target.doctype);
    if (target.kind === 'form' && target.doctype && target.name) return frappe.set_route('Form', target.doctype, target.name);
    if (target.kind === 'list' && target.doctype) return routeToList(target.doctype, target.filters || null);
    if (target.kind === 'report' && target.report_name) return routeToReport(target.report_name, target.filters || null);
    if (target.kind === 'worklist' && target.queue_key) return routeToWorklist(target.queue_key, target.filters || null);
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
          { key: 'back_to_console', label: 'Back to Sales Console' },
          { key: 'refresh', label: 'Refresh' },
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
    return targets[details.scope + ':' + details.key] || targets[details.key] || null;
  }

  function collectFilterValues($host) {
    const values = {};
    if (!$host || !$host.length) return values;

    $host.find('[data-erpw-list-field-key]').each(function () {
      const $field = $(this);
      const key = ($field.attr('data-erpw-list-field-key') || '').trim();
      if (!key) return;
      const value = ($field.val() || '').toString().trim();
      if (value) {
        values[key] = value;
      }
    });

    return values;
  }

  function collectAllFieldValues($host) {
    const values = {};
    if (!$host || !$host.length) return values;

    $host.find('[data-erpw-list-field-key]').each(function () {
      const $field = $(this);
      const key = ($field.attr('data-erpw-list-field-key') || '').trim();
      if (!key) return;
      values[key] = ($field.val() || '').toString().trim();
    });

    return values;
  }

  function collectHiddenFilterValues($host) {
    const values = {};
    if (!$host || !$host.length) return values;

    $host.find('[data-erpw-list-field-type="hidden"][data-erpw-list-field-key]').each(function () {
      const $field = $(this);
      const key = ($field.attr('data-erpw-list-field-key') || '').trim();
      if (!key) return;
      const value = ($field.val() || '').toString().trim();
      if (value) {
        values[key] = value;
      }
    });

    return values;
  }

  function bindFilterInteractions(viewState) {
    if (!viewState || !viewState.$host || !viewState.$host.length) return;
    const $host = viewState.$host;

    $host.off('.erpwListFilterInputs');
    $host.on('keydown.erpwListFilterInputs', '[data-erpw-list-field-key]', function (event) {
      if (event.key !== 'Enter') return;
      event.preventDefault();
      loadRoute(viewState, collectFilterValues($host));
    });
  }

  function duplicateMessage(duplicates) {
    const items = Array.isArray(duplicates) ? duplicates.slice(0, 5) : [];
    if (!items.length) return __('A possible duplicate customer already exists.');
    return [
      '<p>' + __('A possible duplicate customer already exists. Please open Customers and confirm before creating a new account.') + '</p>',
      '<ul>',
        items.map((item) => {
          const label = frappe.utils.escape_html(item.label || item.name || __('Customer'));
          const meta = item.meta ? '<br><small>' + frappe.utils.escape_html(item.meta) + '</small>' : '';
          return '<li><strong>' + label + '</strong>' + meta + '</li>';
        }).join(''),
      '</ul>',
    ].join('');
  }

  function applyReturnedFieldValues($host, values) {
    if (!$host || !$host.length || !values || typeof values !== 'object') return;
    Object.keys(values).forEach((key) => {
      const $field = $host.find('[data-erpw-list-field-key="' + frappe.utils.escape_html(key) + '"]').first();
      if ($field.length) {
        $field.val(values[key] == null ? '' : String(values[key]));
      }
    });
  }

  function executeApiTarget(viewState, target) {
    if (!target || !target.method) return;
    const payload = target.collect_fields ? collectAllFieldValues(viewState.$host) : {};
    frappe.call({
      method: target.method,
      args: { payload },
      freeze: true,
      freeze_message: __('Saving customer profile...'),
    }).then((response) => {
      const message = response && response.message ? response.message : {};
      if (message.state === 'duplicate_warning') {
        frappe.msgprint({
          title: __('Possible duplicate customer'),
          indicator: 'orange',
          message: duplicateMessage(message.duplicates),
        });
        return;
      }
      if (message.message) {
        frappe.show_alert({ message: __(message.message), indicator: 'green' });
      }
      if (target.stay_on_success) {
        applyReturnedFieldValues(viewState.$host, message.values);
        const nextFilters = Object.assign({}, viewState.activeFilters || {}, message.filters || {});
        viewState.activeFilters = nextFilters;
        if (payload.mode === 'new' && message.customer) {
          routeToWorklist('customer_editor', nextFilters);
          return;
        }
        loadRoute(viewState, nextFilters);
        return;
      }
      if (message.customer) {
        routeToWorklist('customer_detail', { customer: message.customer });
        return;
      }
      loadRoute(viewState, viewState.activeFilters || {});
    }).catch((error) => {
      const message = error && error.message ? error.message : __('Customer profile could not be saved.');
      frappe.msgprint({ title: __('Customer save failed'), indicator: 'red', message });
    });
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
        if (details.key === 'refresh') return loadRoute(viewState, viewState.activeFilters || {});
        if (details.key === 'back_to_console') return frappe.set_route('sales-console');
        if (details.key === 'apply_filters') return loadRoute(viewState, collectFilterValues(viewState.$host));
        if (details.key === 'reset_filters') return loadRoute(viewState, collectHiddenFilterValues(viewState.$host));
        const target = resolveActionTarget(payload, details);
        if (target && target.kind === 'api_method') return executeApiTarget(viewState, target);
        executeTarget(target);
      },
    }));

    bindFilterInteractions(viewState);
  }

  function loadRoute(viewState, nextFilters) {
    const route = frappe.get_route ? frappe.get_route() : [];
    const queueKey = resolveQueueKey(route);
    const routeSignature = Array.isArray(route) ? route.join('|') : '';
    viewState.routeSignature = routeSignature;
    const routedFilters = nextFilters === undefined ? consumeRouteFilters() : null;
    const routeFilters = routeSegmentFilters(route, queueKey);
    viewState.activeFilters = nextFilters !== undefined
      ? Object.assign({}, routeFilters, nextFilters || {})
      : Object.assign({}, routeFilters, routedFilters || viewState.activeFilters || {});

    if (!queueKey) {
      mountPayload(viewState, errorConfig('Open this page from a Sales Console card so the queue key is passed through.'));
      return;
    }

    mountPayload(viewState, loadingConfig(queueKey));

    frappe.call({
      method: CONTEXT_METHOD,
      args: {
        queue_key: queueKey,
        filters: viewState.activeFilters || {},
      },
    }).then((response) => {
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
      activeFilters: {},
    };
    wrapper.__erpwSalesConsoleWorklist = viewState;
    activeViewState = viewState;
    loadRoute(viewState);
  }

  frappe.pages[PAGE_KEY] = frappe.pages[PAGE_KEY] || {};
  frappe.pages[PAGE_KEY].on_page_load = function (wrapper) { render(wrapper); };
  frappe.pages[PAGE_KEY].on_page_show = function (wrapper) {
    if (wrapper && wrapper.__erpwSalesConsoleWorklist) {
      activeViewState = wrapper.__erpwSalesConsoleWorklist;
      loadRoute(wrapper.__erpwSalesConsoleWorklist);
    }
  };

  window.erpWorkspaceSalesConsoleWorklist = Object.assign(window.erpWorkspaceSalesConsoleWorklist || {}, {
    applyFilters(queueKey, filters) {
      const route = frappe.get_route ? frappe.get_route() : [];
      if (!activeViewState || resolveQueueKey(route) !== String(queueKey || '')) return false;
      loadRoute(activeViewState, filters && typeof filters === 'object' ? Object.assign({}, filters) : {});
      return true;
    },
  });
})();
