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

  function ensureDraftSideRailLayout(frm) {
    const getFormRoot = childPageHelpers.getFormRoot;
    const getNativeLayoutAnchor = childPageHelpers.getNativeLayoutAnchor;
    const ensureChildPageHostSlot = childPageHelpers.ensureChildPageHostSlot;
    if (typeof getFormRoot !== "function" || typeof getNativeLayoutAnchor !== "function" || typeof ensureChildPageHostSlot !== "function") {
      return { $hostSlot: $(), $layout: $(), $main: $(), $nativeAnchor: $(), $sideSlot: $() };
    }

    const $root = getFormRoot(frm);
    const $hostSlot = ensureChildPageHostSlot(frm);
    const $nativeAnchor = getNativeLayoutAnchor(frm);
    if (!$hostSlot.length || !$nativeAnchor.length) {
      return { $hostSlot, $layout: $(), $main: $(), $nativeAnchor, $sideSlot: $() };
    }

    let $layout = $nativeAnchor.closest('.erpw-child-draft-page');
    if (!$layout.length && $root.length) {
      $layout = $root.children('.erpw-child-draft-page').first();
    }

    if (!$layout.length) {
      $layout = $('<section class="erpw-child-draft-page" data-erpw-child-draft-page="1"></section>');
      const $insertTarget = $hostSlot.length ? $hostSlot : $nativeAnchor;
      $layout.insertBefore($insertTarget);
    }

    let $main = $layout.children('.erpw-child-draft-main').first();
    if (!$main.length) {
      $main = $('<div class="erpw-child-draft-main"></div>');
      $layout.prepend($main);
    }

    let $sideSlot = $layout.children('.erpw-child-draft-side-slot').first();
    if (!$sideSlot.length) {
      $sideSlot = $('<aside class="erpw-child-draft-side-slot" aria-hidden="true"></aside>');
      $layout.append($sideSlot);
    }

    if ($hostSlot.parent().get(0) !== $main.get(0)) {
      $hostSlot.detach();
      $main.append($hostSlot);
    }
    if ($nativeAnchor.parent().get(0) !== $main.get(0)) {
      $nativeAnchor.detach();
      $main.append($nativeAnchor);
    }
    if ($main.children('.erpw-child-page-host').first().get(0) !== $hostSlot.get(0)) {
      $hostSlot.detach();
      $main.prepend($hostSlot);
    }
    if ($main.children().last().get(0) !== $nativeAnchor.get(0)) {
      $nativeAnchor.detach();
      $main.append($nativeAnchor);
    }

    $layout.addClass('has-draft-rail');
    return { $hostSlot, $layout, $main, $nativeAnchor, $sideSlot };
  }

  function teardownDraftSideRailLayout(frm) {
    const getFormRoot = childPageHelpers.getFormRoot;
    if (typeof getFormRoot !== "function") return;

    const $root = getFormRoot(frm);
    if (!$root.length) return;

    const $layout = $root.children('.erpw-child-draft-page').first();
    if (!$layout.length) return;

    const $main = $layout.children('.erpw-child-draft-main').first();
    if ($main.length) {
      const $children = $main.children().detach();
      $layout.before($children);
    }
    $layout.remove();
  }

  function ensureShell(frm, options) {
    const getFormRoot = childPageHelpers.getFormRoot;
    const getNativeLayoutAnchor = childPageHelpers.getNativeLayoutAnchor;
    const ensureChildPageHostSlot = childPageHelpers.ensureChildPageHostSlot;
    if (typeof getFormRoot !== "function" || typeof getNativeLayoutAnchor !== "function") {
      markFeatureMissing(frm, "shell_mount", { reason: "layout_helpers_unavailable" });
      return $();
    }

    const settings = Object.assign({}, options || {});
    const shellClasses = Array.isArray(settings.shellClasses) ? settings.shellClasses : [];
    const removeClasses = Array.isArray(settings.removeClasses) ? settings.removeClasses : [];
    const selector = getShellSelector(shellClasses);
    const useDraftSideRail = settings.layoutMode === 'draft_side_rail';

    if (useDraftSideRail) {
      ensureDraftSideRailLayout(frm);
    } else {
      teardownDraftSideRailLayout(frm);
    }

    const $root = getFormRoot(frm);
    const $mount = getNativeLayoutAnchor(frm);
    const $hostSlot = typeof ensureChildPageHostSlot === "function" ? ensureChildPageHostSlot(frm) : $();
    if (!$root.length && !$mount.length && !$hostSlot.length) {
      markFeatureMissing(frm, "shell_mount", { reason: "no_mount_anchor" });
      return $();
    }

    let $shell = $hostSlot.length
      ? $hostSlot.children(selector).first()
      : $mount.length
        ? $mount.siblings(selector).first()
        : $root.children(selector).first();

    if (!$shell.length && shellClasses.length) {
      const legacySelector = ['.erpw-child-shell']
        .concat(shellClasses.map((name) => `.${name}`))
        .join(', ');
      $shell = $hostSlot.length
        ? $root.find(legacySelector).first()
        : $mount.length
          ? $mount.siblings(legacySelector).first()
          : $root.children(legacySelector).first();
      if ($shell.length) {
        $shell.addClass(shellClasses.join(' '));
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
      $shell.removeClass(removeClasses.join(' '));
    }

    markFeatureReady(frm, 'shell_mount', {
      mode: useDraftSideRail
        ? 'draft_side_rail_layout'
        : $hostSlot.length
          ? 'shared_child_page_host'
          : $mount.length
            ? 'before_native_layout'
            : 'root_prepend',
      shellClasses,
    });
    return $shell;
  }

  function showShellSkeleton(frm, options) {
    const $shell = ensureShell(frm, options);
    if (!$shell.length) {
      markFeatureMissing(frm, 'shell_skeleton', { reason: 'shell_unavailable' });
      return $shell;
    }

    if (
      !$shell.children('.erpw-so-shell-skeleton').length ||
      frm.__erpwContextRenderedName !== (frm.doc && frm.doc.name)
    ) {
      $shell.html(getShellSkeletonMarkup());
    }

    markFeatureReady(frm, 'shell_skeleton', {
      childCount: $shell.children().length,
    });
    return $shell;
  }

  function prepareShell(frm, options) {
    if (!frm) return $();
    if (
      typeof frm.is_new === "function"
      && frm.is_new()
      && (frm.doctype === "Quotation" || frm.doctype === "Sales Order")
    ) {
      return ensureShell(frm, options);
    }
    return showShellSkeleton(frm, options);
  }

  childPageRuntime.shell = Object.assign({}, childPageRuntime.shell || {}, {
    ensureShell,
    getShellSkeletonMarkup,
    prepareShell,
    showShellSkeleton,
  });
})();
