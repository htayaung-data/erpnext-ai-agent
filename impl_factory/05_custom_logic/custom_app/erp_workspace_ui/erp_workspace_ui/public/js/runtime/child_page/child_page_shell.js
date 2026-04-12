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

  function getShellSelector(shellClasses) {
    const classes = Array.isArray(shellClasses) ? shellClasses.filter(Boolean) : [];
    return [".erpw-child-shell"].concat(classes.map((name) => `.${name}`)).join("");
  }

  function getShellClassName(shellClasses) {
    const classes = Array.isArray(shellClasses) ? shellClasses.filter(Boolean) : [];
    return ["erpw-child-shell"].concat(classes).join(" ");
  }

  function getShellSkeletonMarkup() {
    return `
      <section class="erpw-child-card erpw-child-summary erpw-so-shell-skeleton erpw-so-shell-skeleton-summary">
        <div class="erpw-so-shell-skeleton-copy">
          <div class="erpw-so-shell-skeleton-kicker"></div>
          <div class="erpw-so-shell-skeleton-title"></div>
          <div class="erpw-so-shell-skeleton-subtitle"></div>
        </div>
        <div class="erpw-so-shell-skeleton-facts">
          <div class="erpw-so-shell-skeleton-fact"></div>
          <div class="erpw-so-shell-skeleton-fact"></div>
          <div class="erpw-so-shell-skeleton-fact"></div>
        </div>
      </section>
      <section class="erpw-child-card erpw-so-shell-skeleton erpw-so-shell-skeleton-actions">
        <div class="erpw-so-shell-skeleton-action"></div>
        <div class="erpw-so-shell-skeleton-action"></div>
        <div class="erpw-so-shell-skeleton-action"></div>
      </section>
      <section class="erpw-child-card erpw-so-shell-skeleton erpw-so-shell-skeleton-guidance">
        <div class="erpw-so-shell-skeleton-guidance-card"></div>
        <div class="erpw-so-shell-skeleton-guidance-card"></div>
      </section>
    `;
  }

  function ensureShell(frm, options) {
    const getFormRoot = childPageHelpers.getFormRoot;
    const getNativeLayoutAnchor = childPageHelpers.getNativeLayoutAnchor;
    const ensureChildPageHostSlot = childPageHelpers.ensureChildPageHostSlot;
    if (typeof getFormRoot !== "function" || typeof getNativeLayoutAnchor !== "function") {
      markFeatureMissing(frm, "shell_mount", { reason: "layout_helpers_unavailable" });
      return $();
    }

    const $root = getFormRoot(frm);
    const $mount = getNativeLayoutAnchor(frm);
    const $hostSlot = typeof ensureChildPageHostSlot === "function" ? ensureChildPageHostSlot(frm) : $();
    if (!$root.length && !$mount.length && !$hostSlot.length) {
      markFeatureMissing(frm, "shell_mount", { reason: "no_mount_anchor" });
      return $();
    }

    const shellClasses = options && Array.isArray(options.shellClasses) ? options.shellClasses : [];
    const removeClasses = options && Array.isArray(options.removeClasses) ? options.removeClasses : [];
    const selector = getShellSelector(shellClasses);

    let $shell = $hostSlot.length
      ? $hostSlot.children(selector).first()
      : $mount.length
        ? $mount.siblings(selector).first()
        : $root.children(selector).first();

    if (!$shell.length && shellClasses.length) {
      const legacySelector = [".erpw-child-shell"]
        .concat(shellClasses.map((name) => `.${name}`))
        .join(", ");
      $shell = $hostSlot.length
        ? $root.find(legacySelector).first()
        : $mount.length
          ? $mount.siblings(legacySelector).first()
          : $root.children(legacySelector).first();
      if ($shell.length) {
        $shell.addClass(shellClasses.join(" "));
      }
    }

    if (!$shell.length) {
      $shell = $(`<div class="${getShellClassName(shellClasses)}"></div>`);
      if ($hostSlot.length) {
        $hostSlot.append($shell);
      } else if ($mount.length) {
        $shell.insertBefore($mount);
      } else {
        $root.prepend($shell);
      }
    } else if ($hostSlot.length) {
      if ($shell.parent().get(0) !== $hostSlot.get(0)) {
        $shell.detach();
        $hostSlot.append($shell);
      }
    } else if (
      $mount.length &&
      ($shell.parent().get(0) !== $mount.parent().get(0) || $shell.next().get(0) !== $mount.get(0))
    ) {
      $shell.detach();
      $shell.insertBefore($mount);
    }

    if (removeClasses.length) {
      $shell.removeClass(removeClasses.join(" "));
    }

    markFeatureReady(frm, "shell_mount", {
      mode: $hostSlot.length ? "shared_child_page_host" : $mount.length ? "before_native_layout" : "root_prepend",
      shellClasses,
    });
    return $shell;
  }

  function showShellSkeleton(frm, options) {
    const $shell = ensureShell(frm, options);
    if (!$shell.length) {
      markFeatureMissing(frm, "shell_skeleton", { reason: "shell_unavailable" });
      return $shell;
    }

    if (
      !$shell.children(".erpw-so-shell-skeleton").length ||
      frm.__erpwContextRenderedName !== (frm.doc && frm.doc.name)
    ) {
      $shell.html(getShellSkeletonMarkup());
    }

    markFeatureReady(frm, "shell_skeleton", {
      childCount: $shell.children().length,
    });
    return $shell;
  }

  function prepareShell(frm, options) {
    if (!frm) return $();
    return showShellSkeleton(frm, options);
  }

  childPageRuntime.shell = Object.assign({}, childPageRuntime.shell || {}, {
    ensureShell,
    getShellSkeletonMarkup,
    prepareShell,
    showShellSkeleton,
  });
})();
