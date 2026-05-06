/* global frappe, $ */

(function () {
  const workspaceRegistry = window.erpWorkspaceUiWorkspaceRegistry || {};
  const salesWorkspace = typeof workspaceRegistry.sales === 'function' ? workspaceRegistry.sales() : null;
  const salesRoutes = salesWorkspace && salesWorkspace.routes ? salesWorkspace.routes : {};
  const salesMethods = salesWorkspace && salesWorkspace.methods ? salesWorkspace.methods : {};
  const PAGE_KEY = salesRoutes.worklist || 'sales-console-worklist';
  const HOME_ROUTE = salesRoutes.home || 'sales-console';
  const CONTEXT_METHOD = salesMethods.worklistContext || 'erp_workspace_ui.sales_console.worklist.get_sales_console_worklist_context';
  const DIRECTORY_QUEUE_BY_DOCTYPE = Object.assign({
    Quotation: 'quotation_directory',
    'Sales Order': 'sales_order_directory',
    Customer: 'customer_directory',
    Item: 'item_directory',
  }, (salesWorkspace && salesWorkspace.directoryQueuesByDoctype) || {});
  let activeViewState = null;

  function routeToList(doctype, filters) {
    const queueKey = DIRECTORY_QUEUE_BY_DOCTYPE[doctype];
    if (queueKey) return routeToWorklist(queueKey, filters || null);
    frappe.route_options = filters && Object.keys(filters).length ? filters : null;
    frappe.set_route('List', doctype);
  }

  function syncNativeChrome(page, title) {
    const chrome = window.erpWorkspaceUiSalesConsoleChrome;
    if (!chrome || typeof chrome.sync !== 'function') return;
    chrome.sync({ page, title });
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

  function itemRouteValue(filters) {
    return filters && typeof filters === 'object' ? String(filters.item || filters.item_code || '').trim() : '';
  }

  function routeToWorklist(queueKey, filters) {
    const nextFilters = filters && Object.keys(filters).length ? filters : null;
    const normalizedQueueKey = String(queueKey || '').replace(/_/g, '-');
    const normalizedTargetKey = String(queueKey || '').replace(/-/g, '_');
    const customer = customerRouteValue(nextFilters);
    const item = itemRouteValue(nextFilters);
    frappe.route_options = nextFilters;
    if (['customer_detail', 'customer_editor'].includes(normalizedTargetKey) && customer) {
      frappe.set_route(PAGE_KEY, normalizedQueueKey, encodeRoutePart(customer));
      return;
    }
    if (normalizedTargetKey === 'item_detail' && item) {
      frappe.set_route(PAGE_KEY, normalizedQueueKey, encodeRoutePart(item));
      return;
    }
    frappe.set_route(PAGE_KEY, normalizedQueueKey);
  }

  function resolveQueueKey(route) {
    return Array.isArray(route) && route.length > 1 ? String(route[1] || '').replace(/-/g, '_') : '';
  }

  function routeSegmentFilters(route, queueKey) {
    if (!Array.isArray(route) || !route[2]) return {};
    if (['customer_detail', 'customer_editor'].includes(queueKey)) {
      const customer = decodeRoutePart(route[2]);
      if (!customer) return {};
      return queueKey === 'customer_editor' ? { customer, mode: 'edit' } : { customer };
    }
    if (queueKey === 'item_detail') {
      const item = decodeRoutePart(route[2]);
      return item ? { item } : {};
    }
    return {};
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
          detail: 'Pulling live operational records and access context.',
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
    const lifecycle = window.erpWorkspaceUiRouteLifecycle;
    if (lifecycle && typeof lifecycle.ensureManagedHost === 'function') {
      return lifecycle.ensureManagedHost({
        page,
        wrapper,
        hostClass: 'erpw-sales-console-worklist-page',
        routeGroup: 'sales',
        routeKind: 'worklist',
      });
    }
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

  function controlField($host, key) {
    if (!$host || !$host.length || !key) return $();
    return $host.find('[data-erpw-list-field-key]').filter(function () {
      return String($(this).attr('data-erpw-list-field-key') || '') === String(key);
    }).first();
  }

  function setControlFieldValue($field, value) {
    if (!$field || !$field.length) return;
    const nextValue = value == null ? '' : String(value);
    const nodeName = String($field.prop('tagName') || '').toLowerCase();

    if (nodeName === 'select') {
      const hasExactOption = $field.find('option').toArray().some((option) => String(option.value) === nextValue);
      if (hasExactOption) {
        $field.val(nextValue);
      } else {
        $field.prop('selectedIndex', 0);
      }
      return;
    }

    const picker = $field.data('datepicker');
    if (!nextValue && picker && typeof picker.clear === 'function') {
      picker.clear();
    }
    $field.val(nextValue);
  }

  function resetVisibleFilterFields($host) {
    if (!$host || !$host.length) return;
    $host.find('[data-erpw-list-field-key]').each(function () {
      const $field = $(this);
      if (($field.attr('data-erpw-list-field-type') || '') === 'hidden') return;
      setControlFieldValue($field, '');
    });
  }

  function syncControlFieldValues($host, controls) {
    if (!$host || !$host.length || !controls || typeof controls !== 'object') return;
    const fields = Array.isArray(controls.fields) ? controls.fields : [];
    fields.forEach((field) => {
      if (!field || !field.key) return;
      const $field = controlField($host, field.key);
      setControlFieldValue($field, field.value);
    });
  }

  function bindFilterInteractions(viewState) {
    if (!viewState || !viewState.$host || !viewState.$host.length) return;
    const $host = viewState.$host;

    $host.off('.erpwListFilterInputs');
    $host.on('keydown.erpwListFilterInputs', '[data-erpw-list-field-key]', function (event) {
      if (event.key !== 'Enter') return;
      event.preventDefault();
      loadRoute(viewState, collectFilterValues($host), { partialDataRefresh: true });
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

  function setDataRefreshing(viewState, enabled) {
    const runtime = window.erpWorkspaceUiListPage && window.erpWorkspaceUiListPage.shell;
    if (!runtime || typeof runtime.setDataRefreshing !== 'function') return;
    runtime.setDataRefreshing(viewState && viewState.$host, enabled);
  }

  function mountPayload(viewState, payload, options) {
    const runtime = window.erpWorkspaceUiListPage && window.erpWorkspaceUiListPage.shell;
    if (!runtime || typeof runtime.mountWorklist !== 'function') {
      viewState.$host.html('<div class="erpw-list-shell"><section class="erpw-child-card erpw-list-results"><div class="erpw-list-state error"><div class="erpw-list-state-title">List runtime unavailable</div><div class="erpw-list-state-detail">Shared worklist runtime is not loaded on this page.</div></div></section></div>');
      return;
    }

    const config = Object.assign({}, payload || {}, {
      onAction(details) {
        if (!details) return;
        if (details.key === 'refresh') return loadRoute(viewState, viewState.activeFilters || {}, { partialDataRefresh: true });
        if (details.key === 'back_to_console') return frappe.set_route(HOME_ROUTE);
        if (details.key === 'apply_filters') return loadRoute(viewState, collectFilterValues(viewState.$host), { partialDataRefresh: true });
        if (details.key === 'reset_filters') {
          const resetFilters = collectHiddenFilterValues(viewState.$host);
          resetVisibleFilterFields(viewState.$host);
          return loadRoute(viewState, resetFilters, { partialDataRefresh: true, refreshControls: true });
        }
        const target = resolveActionTarget(payload, details);
        if (target && target.kind === 'api_method') return executeApiTarget(viewState, target);
        executeTarget(target);
      },
    });

    if (options && options.partialDataRefresh && typeof runtime.refreshWorklistData === 'function') {
      runtime.refreshWorklistData(viewState.$host, config, { refreshControls: Boolean(options.refreshControls) });
      if (options.refreshControls) {
        syncControlFieldValues(viewState.$host, payload && payload.controls);
      }
    } else {
      runtime.mountWorklist(viewState.$host, config);
    }

    bindFilterInteractions(viewState);
  }

  function loadRoute(viewState, nextFilters, options) {
    const settings = options && typeof options === 'object' ? options : {};
    const route = frappe.get_route ? frappe.get_route() : [];
    const queueKey = resolveQueueKey(route);
    const routeSignature = Array.isArray(route) ? route.join('|') : '';
    viewState.routeSignature = routeSignature;
    const requestToken = (viewState.requestToken || 0) + 1;
    viewState.requestToken = requestToken;
    const routedFilters = nextFilters === undefined ? consumeRouteFilters() : null;
    const routeFilters = routeSegmentFilters(route, queueKey);
    viewState.activeFilters = nextFilters !== undefined
      ? Object.assign({}, routeFilters, nextFilters || {})
      : Object.assign({}, routeFilters, routedFilters || viewState.activeFilters || {});

    if (!queueKey) {
      mountPayload(viewState, errorConfig('Open this page from a Sales Console card so the queue key is passed through.'));
      return;
    }

    const partialDataRefresh = Boolean(settings.partialDataRefresh && viewState.$host && viewState.$host.find('.erpw-list-shell').length);
    if (partialDataRefresh) {
      setDataRefreshing(viewState, true);
    } else {
      mountPayload(viewState, loadingConfig(queueKey));
    }
    syncNativeChrome(viewState.page);

    frappe.call({
      method: CONTEXT_METHOD,
      args: {
        queue_key: queueKey,
        filters: viewState.activeFilters || {},
      },
    }).then((response) => {
      if (viewState.routeSignature !== routeSignature || viewState.requestToken !== requestToken) return;
      const payload = response && response.message ? response.message : {};
      if (viewState.page && typeof viewState.page.set_title === 'function' && payload.page && payload.page.title) {
        viewState.page.set_title(payload.page.title);
      }
      syncNativeChrome(viewState.page, payload.page && payload.page.title);
      mountPayload(viewState, payload, { partialDataRefresh, refreshControls: Boolean(settings.refreshControls) });
    }).catch((error) => {
      if (viewState.routeSignature !== routeSignature || viewState.requestToken !== requestToken) return;
      setDataRefreshing(viewState, false);
      mountPayload(viewState, errorConfig(error && error.message ? error.message : 'The operational queue could not be loaded.'));
    });
  }

  function render(wrapper) {
    const page = frappe.ui.make_app_page({
      parent: wrapper,
      title: 'Sales Console Worklist',
      single_column: true,
    });
    syncNativeChrome(page);
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
      loadRoute(activeViewState, filters && typeof filters === 'object' ? Object.assign({}, filters) : {}, { partialDataRefresh: true });
      return true;
    },
  });
})();
