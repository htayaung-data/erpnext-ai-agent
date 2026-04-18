(function () {
  const root = window;
  const listPageRuntime = root.erpWorkspaceUiListPage = root.erpWorkspaceUiListPage || {};

  function escapeHtml(value) {
    return frappe.utils.escape_html(value == null ? "" : String(value));
  }

  function normalizeItems(items) {
    return Array.isArray(items) ? items.filter(Boolean) : [];
  }

  function joinClassNames() {
    return Array.from(arguments)
      .flatMap((value) => Array.isArray(value) ? value : [value])
      .filter(Boolean)
      .join(" ");
  }

  function renderBadge(item, extraClass) {
    if (!item) return "";
    const label = typeof item === "string" ? item : item.label;
    if (!label) return "";
    const tone = typeof item === "object" && item.tone ? item.tone : "neutral";
    return '<span class="' + joinClassNames('erpw-list-pill', tone, extraClass) + '">' + escapeHtml(label) + '</span>';
  }

  function renderSummary(summary, controls) {
    if (!summary || !summary.title) return "";
    const chips = normalizeItems(summary.chips);

    return [
      '<section class="erpw-child-card erpw-list-summary-card">',
        '<div class="erpw-list-summary-head">',
          '<div class="erpw-list-summary-copy">',
            summary.title ? '<h2 class="erpw-list-title">' + escapeHtml(summary.title) + '</h2>' : '',
            summary.subtitle ? '<div class="erpw-list-subtitle">' + escapeHtml(summary.subtitle) + '</div>' : '',
          '</div>',
          chips.length ? '<div class="erpw-list-chip-row">' + chips.map((chip) => renderBadge(chip)).join('') + '</div>' : '',
        '</div>',
      '</section>'
    ].join('');
  }

  function renderToolbarAction(action) {
    if (!action || !action.key || !action.label) return "";
    const buttonClass = action.kind === 'primary'
      ? 'erpw-list-action-button primary'
      : 'erpw-list-action-button';
    return '<button type="button" class="' + buttonClass + '" data-erpw-list-action-key="' + escapeHtml(action.key) + '" data-erpw-list-action-scope="toolbar">' + escapeHtml(action.label) + '</button>';
  }

  function renderControls(controls) {
    if (!controls) return "";

    const actions = normalizeItems(controls.actions).filter((action) => action.key !== 'open_native');
    const hasContent = actions.length || controls.searchHint;
    if (!hasContent) return "";

    return [
      '<section class="erpw-list-controls-strip">',
        '<div class="erpw-list-controls-inline">',
          controls.searchHint ? '<div class="erpw-list-search-hint">' + escapeHtml(controls.searchHint) + '</div>' : '',
          actions.length ? '<div class="erpw-list-toolbar-actions">' + actions.map((action) => renderToolbarAction(action)).join('') + '</div>' : '',
        '</div>',
      '</section>'
    ].join('');
  }

  function renderMetrics(metrics) {
    const items = normalizeItems(metrics);
    if (!items.length) return "";

    return [
      '<section class="erpw-list-metrics">',
        items.map((item) => [
          '<article class="erpw-child-card erpw-list-metric ' + escapeHtml(item.tone || 'neutral') + '">',
            '<div class="erpw-list-metric-label">' + escapeHtml(item.label || '') + '</div>',
            '<div class="erpw-list-metric-value">' + escapeHtml(item.value == null ? '--' : item.value) + '</div>',
            item.meta ? '<div class="erpw-list-metric-meta">' + escapeHtml(item.meta) + '</div>' : '',
          '</article>'
        ].join('')).join(''),
      '</section>'
    ].join('');
  }

  function normalizeCell(row, column) {
    const cells = row && row.cells && typeof row.cells === 'object' ? row.cells : {};
    const cell = cells[column.key];
    if (cell && typeof cell === 'object' && !Array.isArray(cell)) {
      return {
        value: cell.value == null ? '--' : cell.value,
        meta: cell.meta || '',
        tone: cell.tone || '',
        className: cell.className || '',
        actionKey: cell.actionKey || '',
      };
    }
    return {
      value: cell == null ? '--' : cell,
      meta: '',
      tone: '',
      className: '',
      actionKey: '',
    };
  }

  function normalizeRowActions(row) {
    return normalizeItems(row && row.actions);
  }

  function renderRowAction(action, row) {
    if (!action || !action.key || !action.label) return "";
    return '<button type="button" class="erpw-list-row-action" data-erpw-list-action-key="' + escapeHtml(action.key) + '" data-erpw-list-action-scope="row" data-erpw-row-key="' + escapeHtml(row.key || '') + '">' + escapeHtml(action.label) + '</button>';
  }

  function renderCell(row, column, columnIndex, inlinePrimaryAction) {
    const cell = normalizeCell(row, column);
    const inlineAction = inlinePrimaryAction && columnIndex === 0 ? normalizeRowActions(row)[0] : null;
    const primary = inlineAction
      ? '<button type="button" class="erpw-list-inline-open" data-erpw-list-action-key="' + escapeHtml(inlineAction.key) + '" data-erpw-list-action-scope="row" data-erpw-row-key="' + escapeHtml(row.key || '') + '"><span class="erpw-list-inline-open-label">' + escapeHtml(cell.value) + '</span><span class="erpw-list-inline-open-icon" aria-hidden="true">&rarr;</span></button>'
      : cell.actionKey
        ? '<button type="button" class="erpw-list-cell-link" data-erpw-list-action-key="' + escapeHtml(cell.actionKey) + '" data-erpw-list-action-scope="row" data-erpw-row-key="' + escapeHtml(row.key || '') + '">' + escapeHtml(cell.value) + '</button>'
      : '<div class="erpw-list-cell-primary">' + escapeHtml(cell.value) + '</div>';

    return [
      '<td class="' + joinClassNames(column.align || '', cell.className, cell.tone ? 'tone-' + cell.tone : '') + '">',
        primary,
        cell.meta ? '<div class="erpw-list-cell-meta">' + escapeHtml(cell.meta) + '</div>' : '',
      '</td>'
    ].join('');
  }

  function renderResultsState(state) {
    if (!state) return '';
    return [
      '<div class="erpw-list-state ' + escapeHtml(state.kind || 'neutral') + '">',
        '<div class="erpw-list-state-title">' + escapeHtml(state.title || 'Workspace state') + '</div>',
        state.detail ? '<div class="erpw-list-state-detail">' + escapeHtml(state.detail) + '</div>' : '',
        state.action && state.action.key && state.action.label
          ? '<button type="button" class="erpw-list-action-button" data-erpw-list-action-key="' + escapeHtml(state.action.key) + '" data-erpw-list-action-scope="state">' + escapeHtml(state.action.label) + '</button>'
          : '',
      '</div>'
    ].join('');
  }

  function compactScopeItems(controls) {
    return normalizeItems(controls && controls.scopeChips)
      .map((chip) => typeof chip === 'string' ? chip : chip && chip.label)
      .filter(Boolean);
  }

  function renderResults(results, controls) {
    const config = results || {};
    const columns = normalizeItems(config.columns);
    const rows = normalizeItems(config.rows);
    const scopeItems = compactScopeItems(controls);
    const scopeContext = scopeItems.length ? scopeItems.join(' \u00b7 ') : '';
    const showInlinePrimaryAction = Boolean(config.rowActions) && rows.length && rows.every((row) => {
      const actions = normalizeRowActions(row);
      return actions.length === 1 && actions[0].key === 'open_record';
    });
    const showResultsTitle = Boolean(config.title);
    const showResultsHeader = showResultsTitle || config.subtitle || config.meta || scopeContext;

    return [
      '<section class="erpw-child-card erpw-list-results">',
        showResultsHeader ? [
          '<div class="erpw-list-results-head">',
            '<div class="erpw-list-results-copy">',
              showResultsTitle ? '<div class="erpw-list-results-title">' + escapeHtml(config.title) + '</div>' : '',
              config.subtitle ? '<div class="erpw-list-results-note">' + escapeHtml(config.subtitle) + '</div>' : '',
              !config.subtitle && scopeContext ? '<div class="erpw-list-results-note erpw-list-results-context">' + escapeHtml(scopeContext) + '</div>' : '',
            '</div>',
            config.meta ? '<div class="erpw-list-results-meta">' + escapeHtml(config.meta) + '</div>' : '',
          '</div>'
        ].join('') : '',
        config.state && config.state.kind && config.state.kind !== 'ready'
          ? renderResultsState(config.state)
          : columns.length
            ? [
                '<div class="erpw-list-table-wrap">',
                  '<table class="erpw-list-table">',
                    '<thead><tr>',
                      columns.map((column) => '<th class="' + escapeHtml(column.align || '') + '">' + escapeHtml(column.label || '') + '</th>').join(''),
                      config.rowActions && !showInlinePrimaryAction ? '<th class="actions">Action</th>' : '',
                    '</tr></thead>',
                    '<tbody>',
                      rows.length
                        ? rows.map((row) => [
                            '<tr data-erpw-row-key="' + escapeHtml(row.key || '') + '">',
                              columns.map((column, index) => renderCell(row, column, index, showInlinePrimaryAction)).join(''),
                              config.rowActions && !showInlinePrimaryAction
                                ? '<td class="actions"><div class="erpw-list-row-actions">' + normalizeRowActions(row).map((action) => renderRowAction(action, row)).join('') + '</div></td>'
                                : '',
                            '</tr>'
                          ].join('')).join('')
                        : '<tr><td colspan="' + escapeHtml(columns.length + (config.rowActions && !showInlinePrimaryAction ? 1 : 0)) + '"><div class="erpw-list-empty-inline">No records match the current view.</div></td></tr>',
                    '</tbody>',
                  '</table>',
                '</div>'
              ].join('')
            : renderResultsState({
                kind: 'empty',
                title: 'No list structure defined',
                detail: 'Columns were not configured for this list surface.',
              }),
      '</section>'
    ].join('');
  }

  function renderWorklist(config) {
    const page = config || {};
    return [
      renderSummary(page.summary, page.controls),
      renderControls(page.controls),
      renderMetrics(page.metrics),
      renderResults(page.results, page.controls),
    ].filter(Boolean).join('');
  }

  function resolveTarget(target) {
    if (!target) return $();
    return target.jquery ? target.first() : $(target).first();
  }

  function ensureShell(target) {
    const $target = resolveTarget(target);
    if (!$target.length) return $();

    let $shell = $target.children('.erpw-list-shell').first();
    if (!$shell.length) {
      $shell = $('<section class="erpw-list-shell"></section>');
      $target.empty().append($shell);
    }

    return $shell;
  }

  function bindActions($shell, config) {
    if (!$shell || !$shell.length) return;
    const onAction = config && typeof config.onAction === 'function' ? config.onAction : null;

    $shell.off('.erpwListShell');
    if (!onAction) return;

    $shell.on('click.erpwListShell', '[data-erpw-list-action-key]', function (event) {
      event.preventDefault();
      const $button = $(this);
      onAction({
        key: $button.attr('data-erpw-list-action-key') || '',
        scope: $button.attr('data-erpw-list-action-scope') || 'toolbar',
        rowKey: $button.attr('data-erpw-row-key') || '',
        trigger: this,
      });
    });
  }

  function mountWorklist(target, config) {
    const $shell = ensureShell(target);
    if (!$shell.length) return $();

    const markup = renderWorklist(config || {});
    const signature = markup;
    if ($shell.attr('data-erpw-list-signature') !== signature) {
      $shell.attr('data-erpw-list-signature', signature);
      $shell.html(markup);
    }

    bindActions($shell, config || {});
    return $shell;
  }

  listPageRuntime.shell = Object.assign({}, listPageRuntime.shell || {}, {
    ensureShell,
    mountWorklist,
    renderWorklist,
  });
})();
