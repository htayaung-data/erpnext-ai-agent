(function () {
  const root = window;
  const childPageRuntime = root.erpWorkspaceUiChildPage = root.erpWorkspaceUiChildPage || {};
  const childPageHelpers = childPageRuntime.helpers || {};

  const escapeHtml = childPageHelpers.escapeHtml || function (value) {
    return frappe.utils.escape_html(value == null ? "" : String(value));
  };

  function normalizeActions(actions) {
    if (!Array.isArray(actions)) return [];
    return actions.map((action, idx) => Object.assign({ idx }, action || {}));
  }

  function buildActionRows(actions, options) {
    const normalizedActions = normalizeActions(actions);
    const settings = Object.assign({
      sparseSecondaryThreshold: null,
    }, options || {});

    if (
      Number.isInteger(settings.sparseSecondaryThreshold)
      && normalizedActions.length
      && normalizedActions.length <= settings.sparseSecondaryThreshold
    ) {
      return [{
        className: `erpw-child-action-row erpw-child-action-row-secondary${normalizedActions.length <= 2 ? ' erpw-child-action-row-compact' : ''}`,
        actions: normalizedActions,
      }];
    }

    const primaryActions = normalizedActions.filter((action) => action.variant === 'primary');
    const secondaryActions = normalizedActions.filter((action) => action.variant !== 'primary');
    const rows = [];

    if (primaryActions.length) {
      rows.push({
        className: `erpw-child-action-row erpw-child-action-row-primary${primaryActions.length <= 2 ? ' erpw-child-action-row-compact' : ''}`,
        actions: primaryActions,
      });
    }

    if (secondaryActions.length) {
      rows.push({
        className: `erpw-child-action-row erpw-child-action-row-secondary${secondaryActions.length <= 2 ? ' erpw-child-action-row-compact' : ''}`,
        actions: secondaryActions,
      });
    }

    return rows;
  }

  function renderActionButton(action, actionIconMarkup) {
    const disabled = !!action.disabled;
    const note = String(action.note || action.disabledReason || '').trim();
    const titleAttr = note ? ` title="${escapeHtml(note)}"` : '';
    return `
      <button type="button" class="erpw-child-action ${escapeHtml(action.variant || 'secondary')}${disabled ? ' is-disabled' : ''}" data-action-index="${action.idx}" ${disabled ? 'disabled aria-disabled="true"' : ''}${titleAttr}>
        <span class="erpw-child-action-accent" aria-hidden="true">${actionIconMarkup(action.icon)}</span>
        <span class="erpw-child-action-copy">
          <span class="erpw-child-action-title">${escapeHtml(action.title)}</span>
          ${note ? `<span class="erpw-child-action-note">${escapeHtml(note)}</span>` : ''}
        </span>
      </button>
    `;
  }

  function renderGuidanceActionButton(action, actionIconMarkup) {
    const disabled = !!action.disabled;
    const note = String(action.note || action.disabledReason || '').trim();
    const titleAttr = note ? ` title="${escapeHtml(note)}"` : '';
    return `
      <button type="button" class="erpw-child-guidance-action ${escapeHtml(action.variant || 'secondary')}${disabled ? ' is-disabled' : ''}" data-action-index="${action.idx}" ${disabled ? 'disabled aria-disabled="true"' : ''}${titleAttr}>
        <span class="erpw-child-guidance-action-icon" aria-hidden="true">${actionIconMarkup(action.icon)}</span>
        <span class="erpw-child-guidance-action-title">${escapeHtml(action.title || '')}</span>
      </button>
    `;
  }

  function renderSummaryCard(summary) {
    const facts = Array.isArray(summary.facts) ? summary.facts : [];
    const chips = Array.isArray(summary.chips) ? summary.chips : [];

    return `
      <section class="erpw-child-card erpw-child-summary">
        <div class="erpw-child-summary-copy">
          <div class="erpw-child-summary-top">
            <div class="erpw-child-summary-main">
              <div class="erpw-child-kicker">${escapeHtml(summary.kicker || '')}</div>
              <h2 class="erpw-child-title">${escapeHtml(summary.title || '')}</h2>
              <div class="erpw-child-subtitle">${escapeHtml(summary.subtitle || '')}</div>
            </div>
            <div class="erpw-child-chip-row erpw-child-chip-row-header">
              ${chips.map((chip) => `
                <span class="erpw-child-chip ${escapeHtml(chip.tone || 'pending')}">${escapeHtml(chip.label)}</span>
              `).join('')}
            </div>
          </div>
        </div>
        <div class="erpw-child-summary-facts">
          ${facts.map((fact) => `
            <div class="erpw-child-fact ${escapeHtml(fact.className || '')}">
              <div class="erpw-child-fact-label">${escapeHtml(fact.label || '')}</div>
              <div class="erpw-child-fact-value">${escapeHtml(fact.value || '--')}</div>
              ${fact.meta ? `<div class="erpw-child-fact-meta">${escapeHtml(fact.meta)}</div>` : ''}
            </div>
          `).join('')}
        </div>
      </section>
    `;
  }

  function renderActionsBand(actionRows, actionIconMarkup) {
    if (!Array.isArray(actionRows) || !actionRows.length) return '';
    const compact = actionRows.every((row) => Array.isArray(row.actions) && row.actions.length <= 2);
    return `
      <section class="erpw-child-card erpw-child-actions erpw-child-actions-band${compact ? ' erpw-child-actions-compact' : ''}">
        <div class="erpw-child-action-stack">
          ${actionRows.map((row) => `
            <div class="${escapeHtml(row.className || 'erpw-child-action-row erpw-child-action-row-secondary')}" data-count="${Array.isArray(row.actions) ? row.actions.length : 0}">
              ${(Array.isArray(row.actions) ? row.actions : []).map((action) => renderActionButton(action, actionIconMarkup)).join('')}
            </div>
          `).join('')}
        </div>
      </section>
    `;
  }

  function renderDocumentActionButton(action, actionIconMarkup) {
    const disabled = !!action.disabled;
    const note = String(action.note || action.disabledReason || '').trim();
    const titleAttr = note ? ` title="${escapeHtml(note)}"` : '';
    return `
      <button type="button" class="erpw-child-document-action ${escapeHtml(action.variant || 'secondary')}${disabled ? ' is-disabled' : ''}" data-document-action-index="${action.idx}" ${disabled ? 'disabled aria-disabled="true"' : ''}${titleAttr}>
        <span class="erpw-child-document-action-icon" aria-hidden="true">${actionIconMarkup(action.icon)}</span>
        <span class="erpw-child-document-action-title">${escapeHtml(action.title || '')}</span>
      </button>
    `;
  }

  function renderDocumentActions(documentActions, actionIconMarkup) {
    const actions = Array.isArray(documentActions) ? documentActions : [];
    if (!actions.length) return '';
    return `
      <section class="erpw-child-card erpw-child-document-actions" aria-label="Document actions">
        <div class="erpw-child-document-actions-head">
          <div class="erpw-child-document-actions-title">Document</div>
        </div>
        <div class="erpw-child-document-actions-list">
          ${actions.map((action) => renderDocumentActionButton(action, actionIconMarkup)).join('')}
        </div>
      </section>
    `;
  }

  function renderGuidanceSection(guidance, actionIconMarkup) {
    const cards = (Array.isArray(guidance.cards) ? guidance.cards : []).slice(0, 2);
    const inlineActions = Array.isArray(guidance.inlineActions) ? guidance.inlineActions : [];
    if (!cards.length && !inlineActions.length) return '';
    const compact = guidance.compact !== false;

    return `
      <section class="erpw-child-card erpw-child-context${compact ? ' erpw-child-context-compact' : ''}">
        <div class="erpw-child-section-heading erpw-child-section-heading-compact">
          <div class="erpw-child-section-title">${escapeHtml(guidance.title || 'Attention')}</div>
          ${inlineActions.length ? `
            <div class="erpw-child-guidance-actions">
              ${inlineActions.map((action) => renderGuidanceActionButton(action, actionIconMarkup)).join('')}
            </div>
          ` : ''}
        </div>
        ${cards.length ? `
          <div class="erpw-child-guidance-grid">
            ${cards.map((card) => `
              <article class="erpw-child-guidance-card ${escapeHtml(card.className || 'erpw-child-guidance-card-secondary')}">
                <div class="erpw-child-guidance-head">
                  <span class="erpw-child-guidance-icon" aria-hidden="true">${card.iconMarkup || ''}</span>
                  <div class="erpw-child-guidance-copy">
                    <div class="erpw-child-guidance-title">${escapeHtml(card.title || '')}</div>
                    <div class="erpw-child-guidance-chip ${escapeHtml(card.chipClass || '')}">${escapeHtml(card.chipLabel || '')}</div>
                  </div>
                </div>
                <div class="erpw-child-guidance-text">${escapeHtml(card.text || '')}</div>
              </article>
            `).join('')}
          </div>
        ` : ''}
      </section>
    `;
  }

  function renderDraftReadinessSection(draftReadiness) {
    if (!draftReadiness || !Array.isArray(draftReadiness.items) || !draftReadiness.items.length) return '';

    const summary = String(draftReadiness.summary || '').trim();
    const note = String(draftReadiness.note || '').trim();
    const metaItems = Array.isArray(draftReadiness.metaItems) ? draftReadiness.metaItems.filter(Boolean) : [];

    return `
      <section class="erpw-child-card erpw-child-draft-readiness">
        <div class="erpw-child-section-heading erpw-child-section-heading-compact erpw-child-draft-heading">
          <div class="erpw-child-draft-heading-copy">
            <div class="erpw-child-section-title">${escapeHtml(draftReadiness.title || 'Draft Readiness')}</div>
            ${note ? `<div class="erpw-child-draft-note">${escapeHtml(note)}</div>` : ''}
          </div>
          ${summary ? `<div class="erpw-child-draft-progress">${escapeHtml(summary)}</div>` : ''}
        </div>
        <div class="erpw-child-draft-checklist">
          ${draftReadiness.items.map((item) => `
            <article class="erpw-child-draft-check ${escapeHtml(item.tone || 'neutral')}">
              <div class="erpw-child-draft-check-main">
                <div class="erpw-child-draft-check-title">${escapeHtml(item.title || '')}</div>
                <div class="erpw-child-draft-check-value">${escapeHtml(item.value || '--')}</div>
              </div>
              ${item.status ? `<span class="erpw-child-draft-status ${escapeHtml(item.tone || 'neutral')}">${escapeHtml(item.status)}</span>` : ''}
            </article>
          `).join('')}
        </div>
        ${metaItems.length ? `
          <div class="erpw-child-draft-meta">
            ${metaItems.map((item) => `
              <span class="erpw-child-draft-meta-item">
                <span class="erpw-child-draft-meta-label">${escapeHtml(item.label || '')}</span>
                <span class="erpw-child-draft-meta-value ${escapeHtml(item.tone || 'neutral')}">${escapeHtml(item.value || '--')}</span>
              </span>
            `).join('')}
          </div>
        ` : ''}
      </section>
    `;
  }

  function renderDraftReadinessRail(draftReadiness) {
    if (!draftReadiness || !Array.isArray(draftReadiness.items) || !draftReadiness.items.length) return '';

    const summary = String(draftReadiness.summary || '').trim();

    return `
      <aside class="erpw-child-card erpw-child-draft-rail">
        <div class="erpw-child-draft-rail-head">
          <div class="erpw-child-draft-rail-copy">
            <div class="erpw-child-section-title">${escapeHtml(draftReadiness.title || 'Draft Readiness')}</div>
          </div>
          ${summary ? `<div class="erpw-child-draft-progress">${escapeHtml(summary)}</div>` : ''}
        </div>
        <div class="erpw-child-draft-rail-list">
          ${draftReadiness.items.map((item) => `
            <article class="erpw-child-draft-rail-item ${escapeHtml(item.tone || 'neutral')}">
              <div class="erpw-child-draft-rail-item-main">
                <span class="erpw-child-draft-rail-item-title">${escapeHtml(item.title || '')}</span>
                <span class="erpw-child-draft-rail-item-value">${escapeHtml(item.value || '--')}</span>
              </div>
              ${item.status ? `<span class="erpw-child-draft-status ${escapeHtml(item.tone || 'neutral')}">${escapeHtml(item.status)}</span>` : ''}
            </article>
          `).join('')}
        </div>
      </aside>
    `;
  }

  function syncDraftRail($shell, draftReadiness, placement) {
    const $draftPage = $shell.closest('.erpw-child-draft-page');
    if (!$draftPage.length) return false;

    const $sideSlot = $draftPage.children('.erpw-child-draft-side-slot').first();
    if (!$sideSlot.length) return false;

    if (draftReadiness && placement === 'side_rail') {
      const railMarkup = renderDraftReadinessRail(draftReadiness);
      const railKey = `side_rail::${railMarkup}`;
      if ($sideSlot.attr('data-erpw-draft-rail-key') !== railKey) {
        $sideSlot.html(railMarkup);
        $sideSlot.attr('data-erpw-draft-rail-key', railKey);
      }
      $draftPage.addClass('has-draft-rail');
      return true;
    }

    if ($sideSlot.attr('data-erpw-draft-rail-key') || $sideSlot.children().length) {
      $sideSlot.empty();
      $sideSlot.removeAttr('data-erpw-draft-rail-key');
    }
    $draftPage.removeClass('has-draft-rail');
    return false;
  }

  function renderDraftLead(summary, draftReadiness, placement, useExternalRail) {
    if (placement === 'sidebar_rail') {
      return renderSummaryCard(summary);
    }

    if (draftReadiness && placement === 'side_rail' && !useExternalRail) {
      return `
        <section class="erpw-child-draft-cluster">
          ${renderSummaryCard(summary)}
          ${renderDraftReadinessRail(draftReadiness)}
        </section>
      `;
    }

    if (draftReadiness && placement === 'side_rail') {
      return renderSummaryCard(summary);
    }

    return `
      ${renderSummaryCard(summary)}
      ${renderDraftReadinessSection(draftReadiness)}
    `;
  }

  function buildShellContentMarkup(settings, actionRows, actionIconMarkup, useExternalRail) {
    return `
      ${renderDraftLead(settings.summary, settings.draftReadiness, settings.draftReadinessPlacement, useExternalRail)}
      ${renderDocumentActions(settings.documentActions, actionIconMarkup)}
      ${renderActionsBand(actionRows, actionIconMarkup)}
      ${renderGuidanceSection(settings.guidance, actionIconMarkup)}
      ${settings.extraSectionsHtml || ''}
    `;
  }

  function shouldFoldActionsIntoGuidance(actions, guidance, options) {
    const settings = Object.assign({
      enabled: true,
      maxActions: 1,
    }, options || {});
    if (!settings.enabled) return false;
    if (!Array.isArray(actions) || !actions.length || actions.length > Number(settings.maxActions || 0)) return false;
    if (!guidance || !Array.isArray(guidance.cards) || !guidance.cards.length) return false;
    return actions.every((action) => {
      const family = String(action.family || '').trim();
      const category = String(action.category || '').trim();
      return family !== 'commit'
        && action.variant !== 'primary'
        && (category === 'follow_up' || category === 'business_next_step' || category === 'primary_business_action');
    });
  }

  function withShellHeightLock($shell, update) {
    if (!$shell || !$shell.length || typeof update !== 'function') return;

    const currentHeight = Math.ceil(Number($shell.outerHeight() || 0));
    if (currentHeight > 0) {
      $shell.css('min-height', `${currentHeight}px`);
    }

    update();

    const release = () => {
      $shell.css('min-height', '');
    };

    if (typeof window.requestAnimationFrame === 'function') {
      window.requestAnimationFrame(() => {
        window.requestAnimationFrame(release);
      });
      return;
    }

    window.setTimeout(release, 0);
  }

  function renderShellContent($shell, options) {
    if (!$shell || !$shell.length) return [];

    const settings = Object.assign({
      actionLayout: {},
      draftReadiness: null,
      draftReadinessPlacement: 'inline',
      documentActions: [],
      extraSectionsHtml: '',
      guidance: {},
      summary: {},
    }, options || {});
    const actionIconMarkup = typeof settings.actionIconMarkup === 'function'
      ? settings.actionIconMarkup
      : function () { return ''; };
    const actions = normalizeActions(settings.actions);
    const documentActions = normalizeActions(settings.documentActions);
    const guidance = Object.assign({}, settings.guidance || {});
    const foldIntoGuidance = shouldFoldActionsIntoGuidance(actions, guidance, settings.actionLayout);
    const shellActions = foldIntoGuidance ? [] : actions;
    if (foldIntoGuidance) {
      guidance.inlineActions = (Array.isArray(guidance.inlineActions) ? guidance.inlineActions : []).concat(actions);
    }
    const actionRows = Array.isArray(settings.actionRows)
      ? settings.actionRows
      : buildActionRows(shellActions, settings.actionLayout);
    settings.documentActions = documentActions;
    settings.guidance = guidance;
    const useExternalRail = syncDraftRail($shell, settings.draftReadiness, settings.draftReadinessPlacement);
    const markup = buildShellContentMarkup(settings, actionRows, actionIconMarkup, useExternalRail);
    const renderKey = [
      settings.draftReadinessPlacement || 'inline',
      useExternalRail ? 'rail' : 'inline',
      markup,
    ].join('||');

    if ($shell.attr('data-erpw-shell-render-key') !== renderKey) {
      withShellHeightLock($shell, () => {
        $shell.html(markup);
        $shell.attr('data-erpw-shell-render-key', renderKey);
      });
    }

    $shell.find('[data-action-index]').off('click.erpwShellAction');
    actions.forEach((action) => {
      if (action.disabled || typeof action.handler !== 'function') return;
      $shell.find(`[data-action-index="${action.idx}"]`).on('click.erpwShellAction', action.handler);
    });

    $shell.find('[data-document-action-index]').off('click.erpwShellDocumentAction');
    documentActions.forEach((action) => {
      if (action.disabled || typeof action.handler !== 'function') return;
      $shell.find(`[data-document-action-index="${action.idx}"]`).on('click.erpwShellDocumentAction', action.handler);
    });

    return actions;
  }

  childPageRuntime.shellContent = Object.assign({}, childPageRuntime.shellContent || {}, {
    buildActionRows,
    renderShellContent,
  });
})();
