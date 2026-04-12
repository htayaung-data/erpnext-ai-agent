(function () {
  const root = window;
  const childPageRuntime = root.erpWorkspaceUiChildPage = root.erpWorkspaceUiChildPage || {};
  const childPageHelpers = childPageRuntime.helpers || {};

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

  const escapeHtml = childPageHelpers.escapeHtml || function (value) {
    return frappe.utils.escape_html(value == null ? "" : String(value));
  };

  function getText(value, fallback) {
    const text = value == null ? "" : String(value);
    return text || (fallback || "");
  }

  function joinClasses(parts) {
    return (Array.isArray(parts) ? parts : [parts]).filter(Boolean).join(" ");
  }

  function renderStatus(statusClassName, status) {
    if (!status || !getText(status.text || status.label)) return "";
    return `
      <div class="${statusClassName}" data-status="${escapeHtml(status.tone || "neutral")}">
        ${escapeHtml(status.text || status.label)}
      </div>
    `;
  }

  function renderActions(actions, theme, scope, groupIndex, itemIndex) {
    if (!Array.isArray(actions) || !actions.length) return "";

    return actions.map((action, actionIndex) => `
      <button
        type="button"
        class="${joinClasses([
          theme.actionBaseClass,
          theme.actionToneClassMap && theme.actionToneClassMap[action.tone],
          action.className,
        ])}"
        data-erpw-connection-action="1"
        data-erpw-connection-scope="${escapeHtml(scope)}"
        data-erpw-connection-group-index="${groupIndex}"
        data-erpw-connection-item-index="${itemIndex}"
        data-erpw-connection-action-index="${actionIndex}"
      >
        ${escapeHtml(action.label || "Open")}
      </button>
    `).join("");
  }

  function resolveMountInsertionAnchor(mount) {
    const $anchor = $(mount && mount.anchor ? mount.anchor : []);
    if (!$anchor.length) {
      return { $anchor, $sourceShell: $() };
    }

    if ((mount && mount.insertMode) === "before" && $anchor.hasClass("form-documents")) {
      const $sourceShell = $anchor.closest(".form-links").first();
      if ($sourceShell.length) {
        return { $anchor: $sourceShell, $sourceShell };
      }
    }

    return { $anchor, $sourceShell: $() };
  }

  function mountWorkspace(frm, config) {
    const mount = config && config.mount ? config.mount : {};
    const $cleanupRoot = $(mount.cleanupRoot || []);
    if ($cleanupRoot.length && mount.cleanupSelector) {
      $cleanupRoot.find(mount.cleanupSelector).remove();
    }

    const $workspace = $(`<div class="${config.theme.workspaceClassName}"></div>`);
    let inserted = false;

    if (typeof mount.insert === "function") {
      mount.insert($workspace);
      inserted = Boolean($workspace.parent().length);
    } else {
      const { $anchor, $sourceShell } = resolveMountInsertionAnchor(mount);
      if (mount.insertMode === "before" && $anchor.length) {
        $workspace.insertBefore($anchor);
        if ($sourceShell.length) {
          $sourceShell.addClass("erpw-connection-source-shell");
        }
        inserted = true;
      } else if (mount.insertMode === "prepend" && $anchor.length) {
        $anchor.prepend($workspace);
        inserted = true;
      } else if ($cleanupRoot.length) {
        $cleanupRoot.prepend($workspace);
        inserted = true;
      }
    }

    if (!inserted) {
      markFeatureMissing(frm, config.featureKey, { reason: "mount_failed" });
      return $();
    }

    return $workspace;
  }

  function summarizeModel(config, groups, secondaryItems) {
    return {
      layout: config.layout,
      groupCount: groups.length,
      itemCount: groups.reduce((sum, group) => sum + (Array.isArray(group.items) ? group.items.length : 0), 0),
      secondaryCount: secondaryItems.length,
      actionCount: groups.reduce((sum, group) => sum + (Array.isArray(group.items) ? group.items.reduce((itemSum, item) => itemSum + (Array.isArray(item.actions) ? item.actions.length : 0), 0) : 0), 0)
        + secondaryItems.reduce((sum, item) => sum + (Array.isArray(item.actions) ? item.actions.length : 0), 0),
    };
  }

  function bindActions($workspace, config, groups, secondaryItems) {
    const namespace = config.theme.namespace || ".erpwConnectionWorkspace";
    $workspace.find("[data-erpw-connection-action='1']").off(namespace).on(`click${namespace}`, function () {
      const $button = $(this);
      const scope = $button.attr("data-erpw-connection-scope");
      const groupIndex = Number($button.attr("data-erpw-connection-group-index"));
      const itemIndex = Number($button.attr("data-erpw-connection-item-index"));
      const actionIndex = Number($button.attr("data-erpw-connection-action-index"));

      let group = null;
      let item = null;
      let action = null;

      if (scope === "secondary") {
        item = secondaryItems[itemIndex] || null;
        action = item && Array.isArray(item.actions) ? item.actions[actionIndex] : null;
      } else {
        group = groups[groupIndex] || null;
        item = group && Array.isArray(group.items) ? group.items[itemIndex] : null;
        action = item && Array.isArray(item.actions) ? item.actions[actionIndex] : null;
      }

      if (!action || typeof action.run !== "function") return;
      action.run({
        frm: config.frm,
        group,
        item,
        action,
        scope,
      });
    });
  }

  function renderCardWorkspace(frm, config) {
    const model = config && config.model ? config.model : {};
    const groups = Array.isArray(model.groups) ? model.groups : [];
    const secondary = model.secondary && Array.isArray(model.secondary.items) ? model.secondary : null;
    const secondaryItems = secondary ? secondary.items : [];
    const featureKey = config.featureKey || "connection_workspace";
    const $workspace = mountWorkspace(frm, Object.assign({}, config, { frm, featureKey, layout: "card" }));

    if (!$workspace.length) return false;

    if (!groups.length && !secondaryItems.length) {
      if (model.loading) {
        $workspace.html(`
          <section class="${config.theme.loadingShellClass}">
            <div class="${config.theme.loadingTitleClass}">${escapeHtml(model.loading.title || "Loading relationship status")}</div>
            <div class="${config.theme.loadingNoteClass}">${escapeHtml(model.loading.note || "Checking linked document status.")}</div>
          </section>
        `);
        markFeatureReady(frm, featureKey, { layout: "card", state: "loading" });
        return true;
      }

      if (model.empty) {
        $workspace.html(`
          <section class="${config.theme.emptyShellClass}">
            <div class="${config.theme.emptyTitleClass}">${escapeHtml(model.empty.title || "No related documents yet")}</div>
            <div class="${config.theme.emptyNoteClass}">${escapeHtml(model.empty.note || "Create the next related record when work moves forward.")}</div>
          </section>
        `);
        markFeatureReady(frm, featureKey, { layout: "card", state: "empty" });
        return true;
      }

      markFeatureMissing(frm, featureKey, { reason: "no_workspace_content" });
      $workspace.remove();
      return false;
    }

    $workspace.html(`
      ${model.pendingNote ? `<div class="${config.theme.pendingNoteClass}">${escapeHtml(model.pendingNote)}</div>` : ""}
      ${groups.map((group, groupIndex) => `
        <section class="${config.theme.groupClass}" data-group-index="${groupIndex}" data-group-key="${escapeHtml(group.key || "")}">
          <div class="${config.theme.groupHeadClass}">
            <div class="${config.theme.groupSummaryClass}">
              <span class="${config.theme.groupIconClass}" aria-hidden="true">${group.iconMarkup || ""}</span>
              <div class="${config.theme.groupCopyClass}">
                <div class="${config.theme.groupTitleClass}">${escapeHtml(getText(group.title, group.label))}</div>
                <div class="${config.theme.groupNoteClass}">${escapeHtml(getText(group.note, group.description))}</div>
              </div>
            </div>
            ${renderStatus(config.theme.groupStatusClass, group.status)}
          </div>
          <div class="${config.theme.itemsClass}" data-item-count="${Array.isArray(group.items) ? group.items.length : 0}">
            ${(Array.isArray(group.items) ? group.items : []).map((item, itemIndex) => `
              <article class="${config.theme.itemClass}" data-group-index="${groupIndex}" data-item-index="${itemIndex}" data-doctype="${escapeHtml(getText(item.doctype))}">
                <div class="${config.theme.itemHeadClass}">
                  <div class="${config.theme.itemMainClass}">
                    <span class="${config.theme.itemIconClass}" aria-hidden="true">${item.iconMarkup || ""}</span>
                    <div class="${config.theme.itemCopyClass}">
                      <div class="${config.theme.itemTitleClass}">${escapeHtml(getText(item.title, item.doctype))}</div>
                      <div class="${config.theme.itemNoteClass}">${escapeHtml(getText(item.note, item.description))}</div>
                    </div>
                  </div>
                  ${renderStatus(config.theme.itemStatusClass, item.status)}
                </div>
                <div class="${config.theme.itemActionsClass}">
                  ${renderActions(item.actions, config.theme, "primary", groupIndex, itemIndex)}
                </div>
              </article>
            `).join("")}
          </div>
        </section>
      `).join("")}
      ${secondaryItems.length ? `
        <section class="${config.theme.secondaryShellClass}">
          <div class="${config.theme.secondaryHeadClass}">
            <span class="${config.theme.secondaryIconClass}" aria-hidden="true">${secondary.iconMarkup || ""}</span>
            <div class="${config.theme.secondaryCopyClass}">
              <div class="${config.theme.secondaryTitleClass}">${escapeHtml(getText(secondary.title, "Available Paths"))}</div>
              <div class="${config.theme.secondaryNoteClass}">${escapeHtml(getText(secondary.note, ""))}</div>
            </div>
          </div>
          <div class="${config.theme.secondaryRowsClass}" data-secondary-count="${secondaryItems.length}">
            ${secondaryItems.map((item, itemIndex) => `
              <div class="${config.theme.secondaryRowClass}" data-secondary-index="${itemIndex}" data-doctype="${escapeHtml(getText(item.doctype))}">
                ${item.iconMarkup && config.theme.secondaryRowIconClass ? `<span class="${config.theme.secondaryRowIconClass}" aria-hidden="true">${item.iconMarkup}</span>` : ""}
                <div class="${config.theme.secondaryRowCopyClass}">
                  <div class="${config.theme.secondaryRowTitleClass}">${escapeHtml(getText(item.title, item.doctype))}</div>
                  <div class="${config.theme.secondaryRowNoteClass}">${escapeHtml(getText(item.note, item.description))}</div>
                </div>
                ${renderActions(item.actions, config.theme, "secondary", 0, itemIndex)}
              </div>
            `).join("")}
          </div>
        </section>
      ` : ""}
      ${model.empty && (groups.length || secondaryItems.length) ? `
        <section class="${config.theme.emptyShellClass}">
          <div class="${config.theme.emptyTitleClass}">${escapeHtml(model.empty.title || "No related documents yet")}</div>
          <div class="${config.theme.emptyNoteClass}">${escapeHtml(model.empty.note || "Create the next related record when work moves forward.")}</div>
        </section>
      ` : ""}
    `);

    bindActions($workspace, Object.assign({}, config, { frm }), groups, secondaryItems);
    markFeatureReady(frm, featureKey, summarizeModel({ layout: "card" }, groups, secondaryItems));
    return true;
  }

  function renderListWorkspace(frm, config) {
    const model = config && config.model ? config.model : {};
    const groups = Array.isArray(model.groups) ? model.groups : [];
    const featureKey = config.featureKey || "connection_workspace";
    const $workspace = mountWorkspace(frm, Object.assign({}, config, { frm, featureKey, layout: "list" }));

    if (!$workspace.length) return false;

    if (!groups.length) {
      if (model.empty) {
        $workspace.html(`
          <section class="${config.theme.emptyShellClass}">
            <div class="${config.theme.emptyTitleClass}">${escapeHtml(model.empty.title || "No relationship context yet")}</div>
            <div class="${config.theme.emptyNoteClass}">${escapeHtml(model.empty.note || "Relationship links will appear here.")}</div>
          </section>
        `);
        markFeatureReady(frm, featureKey, { layout: "list", state: "empty" });
        return true;
      }

      markFeatureMissing(frm, featureKey, { reason: "no_groups" });
      $workspace.remove();
      return false;
    }

    $workspace.html(groups.map((group, groupIndex) => `
      <section class="${config.theme.groupClass}" data-group-key="${escapeHtml(group.key || "")}">
        <div class="${config.theme.groupHeadClass}">
          <div class="${config.theme.groupSummaryClass}">
            <span class="${config.theme.groupIconClass}" aria-hidden="true">${group.iconMarkup || ""}</span>
            <div class="${config.theme.groupCopyClass}">
              <div class="${config.theme.groupTitleClass}">${escapeHtml(getText(group.title, group.label))}</div>
              <div class="${config.theme.groupNoteClass}">${escapeHtml(getText(group.note, group.description))}</div>
            </div>
          </div>
          ${renderStatus(config.theme.groupStatusClass, group.status)}
        </div>
        <div class="${config.theme.itemsClass}">
          ${(Array.isArray(group.items) ? group.items : []).map((item, itemIndex) => `
            <article class="${config.theme.itemClass}" data-group-index="${groupIndex}" data-item-index="${itemIndex}">
              <div class="${config.theme.itemMainClass}">
                <span class="${config.theme.itemIconClass}" aria-hidden="true">${item.iconMarkup || ""}</span>
                <div class="${config.theme.itemCopyClass}">
                  <div class="${config.theme.itemTitleClass}">${escapeHtml(getText(item.title, item.doctype))}</div>
                  <div class="${config.theme.itemNoteClass}">${escapeHtml(getText(item.note, item.description))}</div>
                </div>
              </div>
              <div class="${config.theme.itemMetaClass}">
                ${renderStatus(config.theme.itemStatusClass, item.status)}
                ${renderActions(item.actions, config.theme, "primary", groupIndex, itemIndex)}
              </div>
            </article>
          `).join("")}
        </div>
      </section>
    `).join(""));

    bindActions($workspace, Object.assign({}, config, { frm }), groups, []);
    markFeatureReady(frm, featureKey, summarizeModel({ layout: "list" }, groups, []));
    return true;
  }

  childPageRuntime.connections = Object.assign({}, childPageRuntime.connections || {}, {
    renderCardWorkspace,
    renderListWorkspace,
  });
})();
