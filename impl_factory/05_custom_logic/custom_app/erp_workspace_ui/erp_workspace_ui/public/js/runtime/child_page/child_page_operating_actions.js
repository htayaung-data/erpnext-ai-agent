(function () {
  const root = window;
  const childPageRuntime = root.erpWorkspaceUiChildPage = root.erpWorkspaceUiChildPage || {};

  function getDoctype(frm) {
    return String((frm && (frm.doctype || (frm.doc && frm.doc.doctype))) || "").trim();
  }

  function getDocStatus(frm) {
    return Number((frm && frm.doc && frm.doc.docstatus) || 0);
  }

  function isLocalDoc(frm) {
    if (!frm) return true;
    if (typeof frm.is_new === "function") {
      return !!frm.is_new();
    }
    return !!(frm.doc && frm.doc.__islocal);
  }

  function isDirty(frm) {
    if (!frm) return false;
    if (typeof frm.is_dirty === "function") {
      return !!frm.is_dirty();
    }
    return !!(frm.doc && frm.doc.__unsaved);
  }

  function safeModelCall(methodName, ...args) {
    try {
      if (!frappe.model || typeof frappe.model[methodName] !== "function") {
        return null;
      }
      return frappe.model[methodName](...args);
    } catch (error) {
      return null;
    }
  }

  function safeShowAlert(message, indicator) {
    if (!message || typeof frappe.show_alert !== "function") return false;
    frappe.show_alert({
      message,
      indicator: indicator || "blue",
    });
    return true;
  }

  function routeToSalesConsole() {
    const sidebar = root.erpWorkspaceConsoleSidebar || {};
    if (typeof sidebar.executeTarget === "function") {
      sidebar.executeTarget({ kind: "page", route: "sales-console" });
      return true;
    }
    frappe.set_route("sales-console");
    return true;
  }

  function getPrintSettings() {
    const settings = safeModelCall("get_doc", ":Print Settings", "Print Settings") || {};
    return {
      allowDraft: Number(settings.allow_print_for_draft || 0) === 1,
      allowCancelled: Number(settings.allow_print_for_cancelled || 0) === 1,
    };
  }

  function isSubmittable(frm) {
    const doctype = getDoctype(frm);
    if (!doctype) return false;
    return !!safeModelCall("is_submittable", doctype);
  }

  function hasWorkflow(frm) {
    const doctype = getDoctype(frm);
    if (!doctype) return false;
    return !!safeModelCall("has_workflow", doctype);
  }

  function canSubmitNow(frm) {
    const permissions = frm && Array.isArray(frm.perm) && frm.perm.length ? (frm.perm[0] || {}) : {};
    return !!(
      frm
      && isSubmittable(frm)
      && getDocStatus(frm) === 0
      && !isLocalDoc(frm)
      && !isDirty(frm)
      && permissions.submit
      && !hasWorkflow(frm)
    );
  }

  function canPrintForStatus(frm, status) {
    const settings = getPrintSettings();
    if (!isSubmittable(frm)) return true;
    if (Number(status) === 1) return true;
    if (Number(status) === 2) return settings.allowCancelled;
    if (Number(status) === 0) return settings.allowDraft;
    return false;
  }

  function getPrintActionState(frm) {
    const hasPrintPermission = !!(
      safeModelCall("can_print", null, frm)
      && !(frm && frm.meta && frm.meta.issingle)
    );
    if (!hasPrintPermission) {
      return { show: false };
    }

    const local = isLocalDoc(frm);
    const status = getDocStatus(frm);
    if (local) {
      if (canPrintForStatus(frm, 0)) {
        return { disabledReason: "Save draft first", enabled: false, note: "", show: true };
      }
      if (isSubmittable(frm) && canPrintForStatus(frm, 1)) {
        return { disabledReason: "Save and submit to unlock print", enabled: false, note: "", show: true };
      }
      return { show: false };
    }

    if (canPrintForStatus(frm, status)) {
      return { disabledReason: "", enabled: true, note: "Open the printable document view.", show: true };
    }
    if (status === 0 && isSubmittable(frm) && canPrintForStatus(frm, 1)) {
      return { disabledReason: "Submit to unlock print", enabled: false, note: "", show: true };
    }
    return { show: false };
  }

  function getEmailActionState(frm) {
    const canEmail = !!safeModelCall("can_email", null, frm);
    if (!canEmail || getDocStatus(frm) >= 2) {
      return { show: false };
    }
    if (isLocalDoc(frm)) {
      return { disabledReason: "Save draft first", enabled: false, note: "", show: true };
    }
    return { disabledReason: "", enabled: true, note: "Prepare an email for this document.", show: true };
  }

  function getAssignActionState(frm) {
    const canCreateTodo = safeModelCall("can_create", "ToDo");
    const assignDialogReady = !!(
      frm
      && frm.assign_to
      && typeof frm.assign_to.add === "function"
    ) || !!(
      frappe.ui
      && frappe.ui.form
      && typeof frappe.ui.form.AssignToDialog === "function"
    );

    if (!assignDialogReady || canCreateTodo === false) {
      return { show: false };
    }

    if (isLocalDoc(frm)) {
      return { disabledReason: "Save draft first", enabled: false, note: "", show: true };
    }

    return { disabledReason: "", enabled: true, note: "Assign follow-up ownership for this document.", show: true };
  }

  function getCommentActionState(frm) {
    if (!frm) return { show: false };
    if (isLocalDoc(frm)) {
      return { disabledReason: "Save draft first", enabled: false, note: "", show: true };
    }
    return { disabledReason: "", enabled: true, note: "Add an internal note in the activity area.", show: true };
  }

  function getShareActionState(frm) {
    const canShare = !!(
      (typeof (frm && frm.share_doc) === "function" || !!(frm && frm.shared && typeof frm.shared.show === "function"))
      && (safeModelCall("can_share", null, frm) !== false)
    );
    if (!canShare) {
      return { show: false };
    }

    if (isLocalDoc(frm)) {
      return { disabledReason: "Save draft first", enabled: false, note: "", show: true };
    }

    return { disabledReason: "", enabled: true, note: "Share this document with permitted teammates.", show: true };
  }

  function openAssignDialog(frm) {
    if (!frm) return false;
    if (isLocalDoc(frm)) {
      safeShowAlert("Save draft first", "orange");
      return false;
    }

    if (frm.assign_to && typeof frm.assign_to.add === "function") {
      frm.assign_to.add();
      return true;
    }

    if (!(frappe.ui && frappe.ui.form && typeof frappe.ui.form.AssignToDialog === "function")) {
      safeShowAlert("Assignment tools are not ready yet", "orange");
      return false;
    }

    if (!frm.__erpwAssignToDialog) {
      frm.__erpwAssignToDialog = new frappe.ui.form.AssignToDialog({
        callback(response) {
          const assignments = response && response.message ? response.message : [];
          if (frm.assign_to && typeof frm.assign_to.render === "function") {
            frm.assign_to.render(assignments);
          }
        },
        doctype: frm.doctype,
        docname: frm.docname,
        frm,
        method: "frappe.desk.form.assign_to.add",
      });
    }

    const dialog = frm.__erpwAssignToDialog;
    if (!dialog || !dialog.dialog) {
      safeShowAlert("Assignment tools are not ready yet", "orange");
      return false;
    }

    dialog.dialog.clear();
    dialog.dialog.show();
    return true;
  }

  function focusCommentComposer(frm) {
    if (!frm) return false;
    if (isLocalDoc(frm)) {
      safeShowAlert("Save draft first", "orange");
      return false;
    }

    const $wrapper = $(frm.wrapper || frm.$wrapper || []);
    const $footer = $wrapper.find(".form-footer").first();
    if ($footer.length) {
      const footerNode = $footer.get(0);
      try {
        footerNode.scrollIntoView({ behavior: "smooth", block: "start" });
      } catch (error) {
        footerNode.scrollIntoView(true);
      }
      const $toggle = $footer.find(".erpw-so-support-toggle").first();
      if (
        $toggle.length
        && $footer.hasClass("has-activity-overflow")
        && !$footer.hasClass("is-activity-expanded")
      ) {
        $toggle.trigger("click");
      }
    }

    window.setTimeout(() => {
      if (frm.comment_box && typeof frm.comment_box.set_focus === "function") {
        frm.comment_box.set_focus();
        return;
      }

      const $target = $wrapper.find(".comment-box [contenteditable='true'], .comment-box .ql-editor, .comment-box textarea, .comment-box input").filter(":visible").first();
      const node = $target.get(0);
      if (node && typeof node.focus === "function") {
        node.focus();
      }
    }, 120);

    return true;
  }

  function fallbackCopyText(value) {
    try {
      const input = document.createElement("textarea");
      input.value = value;
      input.setAttribute("readonly", "readonly");
      input.style.position = "fixed";
      input.style.top = "-1000px";
      input.style.opacity = "0";
      document.body.appendChild(input);
      input.select();
      const copied = document.execCommand("copy");
      document.body.removeChild(input);
      return copied;
    } catch (error) {
      return false;
    }
  }

  function copyDocumentLink() {
    const url = root.location && root.location.href ? root.location.href : "";
    if (!url) {
      safeShowAlert("Document link is not available", "orange");
      return false;
    }

    if (navigator.clipboard && typeof navigator.clipboard.writeText === "function") {
      navigator.clipboard.writeText(url)
        .then(() => safeShowAlert("Document link copied", "green"))
        .catch(() => {
          const copied = fallbackCopyText(url);
          safeShowAlert(copied ? "Document link copied" : "Could not copy link", copied ? "green" : "orange");
        });
      return true;
    }

    const copied = fallbackCopyText(url);
    safeShowAlert(copied ? "Document link copied" : "Could not copy link", copied ? "green" : "orange");
    return copied;
  }

  function createAction(base, state) {
    return {
      disabled: !!(state && state.enabled === false),
      disabledReason: state && state.enabled === false ? (state.disabledReason || "") : "",
      note: state && state.enabled === false ? "" : String((state && state.note) || (base && base.note) || "").trim(),
      ...base,
      ...state,
    };
  }

  function buildDocumentActions(frm, options) {
    const settings = Object.assign({
      backLabel: "Back to Sales Console",
      docLabel: getDoctype(frm) || "Document",
      saveLabel: "Save Draft",
      submitLabel: "Submit",
    }, options || {});

    const actions = [];
    const docLabel = String(settings.docLabel || "Document").toLowerCase();
    const docStatus = getDocStatus(frm);
    const local = isLocalDoc(frm);
    const dirty = isDirty(frm);
    const submitReady = canSubmitNow(frm);

    if (docStatus === 0 && (local || dirty)) {
      actions.push(createAction({
        family: "commit",
        icon: "save",
        key: "save_draft",
        handler: () => frm.save("Save"),
        note: local
          ? `Save this ${docLabel} to unlock communication and collaboration actions.`
          : (dirty
            ? "Store the latest changes without final submission."
            : `Keep this ${docLabel} as a working draft.`),
        title: settings.saveLabel,
        tier: submitReady ? "secondary" : "primary",
        variant: submitReady ? "secondary" : "primary",
      }));
    }

    if (docStatus === 0 && submitReady) {
      actions.push(createAction({
        family: "commit",
        icon: "review",
        key: "submit",
        handler: () => frm.save("Submit"),
        note: `Submit this ${docLabel} for live processing.`,
        title: settings.submitLabel,
        tier: "primary",
        variant: "primary",
      }));
    }

    return actions;
  }

  function buildDocumentCommunicationActions(frm) {
    if (!frm || isLocalDoc(frm)) return [];

    const actions = [];
    const printState = getPrintActionState(frm);
    const emailState = getEmailActionState(frm);

    if (printState.show) {
      actions.push(createAction({
        family: "document",
        icon: "print",
        key: "print",
        handler: () => {
          if (typeof frm.print_doc === "function") {
            frm.print_doc();
            return true;
          }
          if (frappe.ui && frappe.ui.form && typeof frappe.ui.form.print_doc === "function") {
            frappe.ui.form.print_doc(frm.doctype, frm.docname);
            return true;
          }
          safeShowAlert("Print is not ready yet", "orange");
          return false;
        },
        title: "Print",
        variant: "secondary",
      }, printState));
    }

    if (emailState.show) {
      actions.push(createAction({
        family: "document",
        icon: "email",
        key: "email",
        handler: () => {
          if (typeof frm.email_doc === "function") {
            frm.email_doc();
            return true;
          }
          safeShowAlert("Email composer is not ready yet", "orange");
          return false;
        },
        title: "Email",
        variant: "secondary",
      }, emailState));
    }

    actions.push({
      family: "document",
      icon: "share",
      key: "copy_link",
      handler: copyDocumentLink,
      note: "Copy this document URL for internal follow-up.",
      title: "Copy Link",
      variant: "secondary",
    });

    return actions;
  }

  function emailIconMarkup() {
    return `
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
        <rect x="4" y="6.5" width="16" height="11" rx="1.8"></rect>
        <path d="M5 8l7 5.5L19 8"></path>
      </svg>
    `;
  }

  function getPrintUrl(frm) {
    const doctype = encodeURIComponent(getDoctype(frm));
    const docname = encodeURIComponent(String((frm && (frm.docname || (frm.doc && frm.doc.name))) || ""));
    if (!doctype || !docname) return "";
    return `/desk/print/${doctype}/${docname}`;
  }

  function openPrintWithoutRouteEscape(frm) {
    const printUrl = getPrintUrl(frm);
    if (!printUrl) {
      safeShowAlert("Print is not ready yet", "orange");
      return false;
    }
    root.open(printUrl, "_blank", "noopener,noreferrer");
    return true;
  }

  function lockNativePrintRoute(frm, $sidebar) {
    if (!frm || !$sidebar || !$sidebar.length) return false;
    const $printButton = $sidebar.find(".form-print button").first();
    if (!$printButton.length || $printButton.attr("data-erpw-print-route-locked") === "1") return false;

    const $replacement = $printButton.clone(false);
    $replacement.attr("data-erpw-print-route-locked", "1");
    $replacement.attr("title", $printButton.attr("title") || "Print");
    $replacement.on("click.erpWorkspacePrintRouteLock", (event) => {
      event.preventDefault();
      event.stopImmediatePropagation();
      openPrintWithoutRouteEscape(frm);
      return false;
    });
    $printButton.replaceWith($replacement);
    return true;
  }

  function enhanceNativeDocumentActions(frm) {
    if (!frm || isLocalDoc(frm)) return false;

    const $wrapper = $(frm.wrapper || frm.$wrapper || []);
    const $sidebar = $(frm.sidebar && frm.sidebar.sidebar ? frm.sidebar.sidebar : [])
      .add($(frm.page && frm.page.sidebar ? frm.page.sidebar : []).find(".form-sidebar"))
      .add($wrapper.find(".form-sidebar"))
      .filter(".form-sidebar")
      .first();
    if (!$sidebar.length) return false;

    const $stats = $sidebar.find(".form-stats-likes").first();
    if (!$stats.length) return false;

    $sidebar.addClass("erpw-native-document-sidebar");
    lockNativePrintRoute(frm, $sidebar);
    $stats.find(".erpw-native-document-action").remove();

    const emailState = getEmailActionState(frm);
    if (!emailState.show) return true;

    const disabled = emailState.enabled === false;
    const title = disabled ? (emailState.disabledReason || "Email unavailable") : "Email";
    const $email = $(`
      <button type="button" class="erpw-native-document-action erpw-native-document-email" title="${frappe.utils.escape_html(title)}" aria-label="${frappe.utils.escape_html(title)}" ${disabled ? 'disabled aria-disabled="true"' : ''}>
        ${emailIconMarkup()}
      </button>
    `);

    if (!disabled) {
      $email.on("click.erpWorkspaceNativeDocumentAction", () => {
        if (typeof frm.email_doc === "function") {
          frm.email_doc();
          return true;
        }
        safeShowAlert("Email composer is not ready yet", "orange");
        return false;
      });
    }

    const $print = $stats.find(".form-print").first();
    if ($print.length) {
      $email.insertAfter($print);
    } else {
      $stats.prepend($email);
    }

    return true;
  }

  function hideNativeMenuItems(frm, labels) {
    if (!frm || !frm.page || !Array.isArray(labels) || !labels.length) return false;
    const normalizedLabels = new Set(labels.map((label) => String(label || "").trim().toLowerCase()).filter(Boolean));
    if (!normalizedLabels.size) return false;

    const $menus = $(frm.page.menu || [])
      .add($(frm.page.wrapper || []).find(".dropdown-menu"))
      .filter(".dropdown-menu");
    if (!$menus.length) return false;

    let hiddenCount = 0;
    $menus.find("a, button, .dropdown-item").each(function () {
      const $item = $(this);
      const label = $.trim($item.clone().find(".shortcut, .pull-right, kbd").remove().end().text() || $item.text() || "")
        .replace(/\s+/g, " ")
        .trim()
        .toLowerCase();
      if (!normalizedLabels.has(label)) return;
      const $row = $item.closest("li, .dropdown-item").first();
      ($row.length ? $row : $item).addClass("erpw-native-menu-hidden").hide();
      hiddenCount += 1;
    });

    return hiddenCount > 0;
  }

  function curateNativeSalesMenu(frm) {
    if (!frm || !frm.page) return false;
    const apply = () => {
      hideNativeMenuItems(frm, [
        "Toggle Sidebar",
        "Delete",
        "Duplicate",
        "New Quotation",
        "New Sales Order",
        "Show Links",
        "Copy to Clipboard",
        "Repeat",
      ]);

      const $wrapper = $(frm.page.wrapper || []);
      const $menuButton = $wrapper.find(".menu-btn-group, .page-actions .btn:has(.icon-dot-horizontal), .page-actions button:contains('...')").first();
      if ($menuButton.length) {
        $menuButton.addClass("erpw-native-overflow-hidden").hide();
        return true;
      }
      return false;
    };
    const applied = apply();

    [50, 180, 420, 900].forEach((delay) => {
      root.setTimeout(apply, delay);
    });

    const $page = $(frm.page.wrapper || []);
    if ($page.length && !frm.__erpwNativeMenuCurationBound) {
      frm.__erpwNativeMenuCurationBound = true;
      $page.on("click.erpWorkspaceNativeMenu shown.bs.dropdown.erpWorkspaceNativeMenu show.bs.dropdown.erpWorkspaceNativeMenu", ".dropdown-toggle, .menu-btn-group button, .menu-btn-group .btn", () => {
        [0, 30, 120, 300].forEach((delay) => root.setTimeout(apply, delay));
      });
    }

    if ($page.length && !frm.__erpwNativeMenuObserver && typeof MutationObserver === "function") {
      let observerTimer = null;
      frm.__erpwNativeMenuObserver = new MutationObserver(() => {
        if (observerTimer) root.clearTimeout(observerTimer);
        observerTimer = root.setTimeout(apply, 20);
      });
      frm.__erpwNativeMenuObserver.observe($page.get(0), {
        childList: true,
        subtree: true,
      });
    }

    return applied;
  }

  function combineActionLists(...lists) {
    const combined = [];
    const seen = new Set();

    lists.forEach((list) => {
      (Array.isArray(list) ? list : []).forEach((action) => {
        if (!action) return;
        const dedupeKey = [
          String(action.key || "").trim(),
          String(action.title || "").trim(),
          String(action.icon || "").trim(),
        ].join("::");
        if (seen.has(dedupeKey)) return;
        seen.add(dedupeKey);
        combined.push(action);
      });
    });

    return combined;
  }

  childPageRuntime.operatingActions = Object.assign({}, childPageRuntime.operatingActions || {}, {
    buildDocumentActions,
    buildDocumentCommunicationActions,
    combineActionLists,
    enhanceNativeDocumentActions,
    curateNativeSalesMenu,
    focusCommentComposer,
    routeToSalesConsole,
  });
})();
