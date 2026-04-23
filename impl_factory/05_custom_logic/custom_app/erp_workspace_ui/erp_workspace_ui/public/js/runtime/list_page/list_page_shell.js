(function () {
  const root = window;
  const listPageRuntime = root.erpWorkspaceUiListPage = root.erpWorkspaceUiListPage || {};
  const STYLE_ID = 'erpw-list-shell-runtime-overrides';

  function ensureStyles() {
    if (document.getElementById(STYLE_ID)) return;
    const style = document.createElement('style');
    style.id = STYLE_ID;
    style.textContent = `
      .erpw-list-table {
        width: 100%;
        table-layout: fixed;
      }
      .erpw-list-table th {
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.08em;
      }
      .erpw-list-table td {
        font-size: 13.5px;
        font-weight: 400;
        color: #0f172a;
        vertical-align: top;
      }
      .erpw-list-cell-primary,
      .erpw-list-cell-link,
      .erpw-list-inline-open,
      .erpw-list-inline-open-label,
      .erpw-list-inline-open-icon,
      .erpw-list-inline-open *,
      .erpw-list-cell-link * {
        text-decoration: none !important;
      }
      .erpw-list-cell-primary {
        font-weight: 500;
        line-height: 1.45;
        color: #334155;
      }
      .erpw-list-cell-link {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 0;
        border: none;
        background: transparent;
        color: #334155;
        font-size: 13.5px;
        font-weight: 500;
        line-height: 1.45;
        text-align: left;
      }
      .erpw-list-cell-link:hover,
      .erpw-list-cell-link:focus-visible {
        color: #0f172a;
        text-decoration: none;
      }
      .erpw-list-inline-open {
        display: inline-grid;
        grid-template-columns: minmax(0, 1fr) auto;
        align-items: center;
        gap: 10px;
        width: 100%;
        padding: 0;
        border: none;
        background: transparent;
        color: #1e293b;
        text-align: left;
      }
      .erpw-list-inline-open-label {
        font-size: 14px;
        font-weight: 600;
        line-height: 1.4;
        color: inherit;
      }
      .erpw-list-inline-open-icon {
        font-size: 14px;
        font-weight: 700;
        color: #94a3b8;
        transition: transform 140ms ease, color 140ms ease;
      }
      .erpw-list-inline-open:hover,
      .erpw-list-inline-open:focus-visible {
        color: #0f172a;
        text-decoration: none;
      }
      .erpw-list-inline-open:hover .erpw-list-inline-open-label,
      .erpw-list-inline-open:focus-visible .erpw-list-inline-open-label {
        text-decoration: none !important;
      }
      .erpw-list-inline-open:hover .erpw-list-inline-open-icon,
      .erpw-list-inline-open:focus-visible .erpw-list-inline-open-icon {
        color: #64748b;
        transform: translateX(2px) scale(1.08);
      }
      .erpw-list-cell-meta {
        margin-top: 3px;
        font-size: 12px;
        font-weight: 400;
        line-height: 1.45;
        color: #64748b;
      }
      .erpw-list-controls-strip {
        display: grid;
        gap: 16px;
        margin-bottom: 16px;
      }
      .erpw-list-control-form {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 14px;
        align-items: end;
      }
      .erpw-list-control-field {
        display: flex;
        flex-direction: column;
        gap: 8px;
      }
      .erpw-list-control-label {
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.08em;
        color: #64748b;
        text-transform: uppercase;
      }
      .erpw-list-control-input,
      .erpw-list-control-select {
        width: 100%;
        min-height: 42px;
        border: 1px solid #cbd5e1;
        border-radius: 14px;
        background: #fff;
        color: #0f172a;
        padding: 0 14px;
        font-size: 14px;
        font-weight: 500;
      }
      .erpw-list-control-input:focus,
      .erpw-list-control-select:focus {
        outline: none;
        border-color: #94a3b8;
        box-shadow: 0 0 0 3px rgba(148, 163, 184, 0.15);
      }
      .erpw-list-toolbar-actions {
        display: inline-flex;
        flex-wrap: wrap;
        gap: 12px;
        justify-content: flex-end;
        align-items: center;
        margin-top: 0;
        padding-top: 2px;
      }
      .erpw-list-metric {
        position: relative;
      }
      .erpw-list-metric.attention {
        border-color: #dbe4ee;
        background: #ffffff;
        box-shadow:
          inset 0 3px 0 #f0b44c,
          var(--erpw-shadow-card, 0 1px 0 rgba(255, 255, 255, 0.98) inset, 0 10px 24px rgba(15, 23, 42, 0.04));
      }
      .erpw-list-metric.warning {
        border-color: #dbe4ee;
        background: #ffffff;
        box-shadow:
          inset 0 3px 0 #94a3b8,
          var(--erpw-shadow-card, 0 1px 0 rgba(255, 255, 255, 0.98) inset, 0 10px 24px rgba(15, 23, 42, 0.04));
      }
      .erpw-list-cell-meta-line {
        display: block;
        margin-top: 2px;
      }
      @media (max-width: 1180px) {
        .erpw-list-control-form {
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }
      }
      @media (max-width: 760px) {
        .erpw-list-control-form {
          grid-template-columns: minmax(0, 1fr);
        }
      }
    `;
    document.head.appendChild(style);
  }

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
    const fields = normalizeItems(controls.fields);
    const hasContent = actions.length || controls.searchHint || fields.length;
    if (!hasContent) return "";

    const fieldsMarkup = fields.length
      ? '<div class="erpw-list-control-form">' + fields.map((field) => {
          if (!field || !field.key || !field.label) return '';
          const baseAttrs =
            ' data-erpw-list-field-key="' + escapeHtml(field.key) + '"' +
            ' data-erpw-list-field-type="' + escapeHtml(field.type || 'text') + '"';

          const controlMarkup = field.type === 'select'
            ? '<select class="erpw-list-control-select"' + baseAttrs + '>' + normalizeItems(field.options).map((option) => {
                const optionValue = option && typeof option === 'object' ? option.value : option;
                const optionLabel = option && typeof option === 'object' ? option.label : option;
                const selected = String(optionValue == null ? '' : optionValue) === String(field.value == null ? '' : field.value) ? ' selected' : '';
                return '<option value="' + escapeHtml(optionValue == null ? '' : optionValue) + '"' + selected + '>' + escapeHtml(optionLabel == null ? '' : optionLabel) + '</option>';
              }).join('') + '</select>'
            : '<input type="text" class="erpw-list-control-input"' + baseAttrs + (field.placeholder ? ' placeholder="' + escapeHtml(field.placeholder) + '"' : '') + ' value="' + escapeHtml(field.value == null ? '' : field.value) + '">';

          return [
            '<label class="erpw-list-control-field">',
              '<span class="erpw-list-control-label">' + escapeHtml(field.label) + '</span>',
              controlMarkup,
            '</label>'
          ].join('');
        }).join('') + '</div>'
      : '';

    return [
      '<section class="erpw-list-controls-strip">',
        '<div class="erpw-list-controls-inline">',
          controls.searchHint ? '<div class="erpw-list-search-hint">' + escapeHtml(controls.searchHint) + '</div>' : '',
        '</div>',
        fieldsMarkup,
        actions.length ? '<div class="erpw-list-toolbar-actions">' + actions.map((action) => renderToolbarAction(action)).join('') + '</div>' : '',
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
        metaLines: normalizeItems(cell.metaLines),
        tone: cell.tone || '',
        className: cell.className || '',
        actionKey: cell.actionKey || '',
      };
    }
    return {
      value: cell == null ? '--' : cell,
      meta: '',
      metaLines: [],
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
        cell.meta || (cell.metaLines && cell.metaLines.length)
          ? '<div class="erpw-list-cell-meta">'
              + (cell.meta ? '<span class="erpw-list-cell-meta-line">' + escapeHtml(cell.meta) + '</span>' : '')
              + normalizeItems(cell.metaLines).map((line) => '<span class="erpw-list-cell-meta-line">' + escapeHtml(line) + '</span>').join('')
            + '</div>'
          : '',
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
                    columns.some((column) => column && column.width)
                      ? '<colgroup>' + columns.map((column) => '<col' + (column && column.width ? ' style="width:' + escapeHtml(column.width) + '"' : '') + '>').join('') + (config.rowActions && !showInlinePrimaryAction ? '<col style="width:120px">' : '') + '</colgroup>'
                      : '',
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
    ensureStyles();
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
