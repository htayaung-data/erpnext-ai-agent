(function () {
  const root = window;
  const childPageRuntime = root.erpWorkspaceUiChildPage = root.erpWorkspaceUiChildPage || {};

  function formatMoney(value, currency) {
    if (value == null) return "--";
    try {
      return format_currency(value, currency || frappe.defaults.get_default("currency"));
    } catch (e) {
      return `${currency || ""} ${value}`;
    }
  }

  function escapeHtml(value) {
    return frappe.utils.escape_html(value == null ? "" : String(value));
  }

  function routeToDoc(doctype, name) {
    if (!doctype || !name) return;
    frappe.set_route("Form", doctype, name);
  }

  function routeToList(doctype, filters) {
    frappe.route_options = filters && Object.keys(filters).length ? filters : null;
    frappe.set_route("List", doctype);
  }


  function scrollViewportTop() {
    try {
      const scrollingElement = document.scrollingElement || document.documentElement || document.body;
      if (scrollingElement) {
        scrollingElement.scrollTop = 0;
      }
      if (document.body) {
        document.body.scrollTop = 0;
      }
      if (document.documentElement) {
        document.documentElement.scrollTop = 0;
      }
      const mainSection = document.querySelector(".main-section");
      if (mainSection) {
        mainSection.scrollTop = 0;
      }
      const layoutMainSection = document.querySelector(".layout-main-section");
      if (layoutMainSection) {
        layoutMainSection.scrollTop = 0;
      }
      window.scrollTo(0, 0);
    } catch (error) {
      // Ignore scroll reset failures and keep route flow usable.
    }
  }

  function getFormTaskState(frm) {
    if (!frm) return { timers: {} };
    if (!frm.__erpwTaskState) {
      frm.__erpwTaskState = { timers: {} };
    }
    return frm.__erpwTaskState;
  }

  function scheduleFormTask(frm, key, delay, fn) {
    if (!frm || typeof fn !== "function") return;
    const state = getFormTaskState(frm);
    if (state.timers[key]) {
      clearTimeout(state.timers[key]);
    }
    state.timers[key] = setTimeout(() => {
      delete state.timers[key];
      if (!frm.doc) return;
      fn();
    }, Math.max(0, Number(delay || 0)));
  }

  function getLayoutWrapper(frm) {
    return $(frm && frm.layout && frm.layout.wrapper ? frm.layout.wrapper : []);
  }

  function getFormRoot(frm) {
    const $layout = getLayoutWrapper(frm);
    if ($layout.length) {
      const $mainSection = $layout.closest(".layout-main-section");
      if ($mainSection.length) return $mainSection;

      const $formPage = $layout.closest(".form-page");
      if ($formPage.length) return $formPage;

      const $parent = $layout.parent();
      if ($parent.length) return $parent;

      return $layout;
    }

    const $wrapper = $(frm && frm.wrapper ? frm.wrapper : frm && frm.$wrapper ? frm.$wrapper : []);
    if ($wrapper.length) {
      const $mainSection = $wrapper.closest(".layout-main-section");
      if ($mainSection.length) return $mainSection;

      const $formPage = $wrapper.closest(".form-page");
      if ($formPage.length) return $formPage;

      return $wrapper;
    }

    return $(frm && frm.page && frm.page.main ? frm.page.main : []);
  }

  function getPageContentRoot(frm) {
    const $layout = getLayoutWrapper(frm);
    if ($layout.length) {
      const $pageContent = $layout.closest(".page-content");
      if ($pageContent.length) return $pageContent;
    }

    const $root = getFormRoot(frm);
    if ($root.length) {
      const $pageContent = $root.closest(".page-content");
      if ($pageContent.length) return $pageContent;
    }

    return $(".page-content").first();
  }

  function getPageContainerRoot(frm) {
    const $pageContent = getPageContentRoot(frm);
    if ($pageContent.length) {
      const $pageContainer = $pageContent.closest(".page-container");
      if ($pageContainer.length) return $pageContainer;
    }

    const $root = getFormRoot(frm);
    if ($root.length) {
      const $pageContainer = $root.closest(".page-container");
      if ($pageContainer.length) return $pageContainer;
    }

    return $(".page-container").first();
  }

  function ensureChildPageHostSlot(frm) {
    const $layout = getLayoutWrapper(frm);
    const $mainSection = $layout.length
      ? $layout.closest(".layout-main-section")
      : getFormRoot(frm).closest(".layout-main-section").length
        ? getFormRoot(frm).closest(".layout-main-section")
        : getFormRoot(frm).hasClass("layout-main-section")
          ? getFormRoot(frm)
          : $();

    if ($mainSection.length) {
      const $pageContent = getPageContentRoot(frm);
      const $pageContainer = getPageContainerRoot(frm);
      let $slot = $mainSection.children(".erpw-child-page-host").first();
      if (!$slot.length && $pageContent.length) {
        $slot = $pageContent.find(".erpw-child-page-host").first();
      }
      if (!$slot.length && $pageContainer.length) {
        $slot = $pageContainer.find(".erpw-child-page-host").first();
      }
      if (!$slot.length) {
        $slot = $('<div class="erpw-child-page-host" data-erpw-child-page-host="1"></div>');
      }

      const $nativeAnchor = getNativeLayoutAnchor(frm);
      const $formPage = $mainSection.children(".form-page").first();
      const $hiddenPageForm = $mainSection.children(".page-form").first();
      let $target = $();

      if ($formPage.length) {
        $target = $formPage;
      } else if ($nativeAnchor.length) {
        const $anchorFormPage = $nativeAnchor.closest(".form-page");
        if ($anchorFormPage.length && $anchorFormPage.parent().get(0) === $mainSection.get(0)) {
          $target = $anchorFormPage;
        } else if ($nativeAnchor.parent().get(0) === $mainSection.get(0)) {
          $target = $nativeAnchor;
        }
      }

      const hostParent = $slot.parent().get(0);
      const desiredParent = $mainSection.get(0);
      if (hostParent !== desiredParent) {
        $slot.detach();
      }

      if ($target.length) {
        if ($slot.next().get(0) !== $target.get(0) || hostParent !== desiredParent) {
          $slot.insertBefore($target);
        }
      } else if ($hiddenPageForm.length) {
        if ($slot.prev().get(0) !== $hiddenPageForm.get(0) || hostParent !== desiredParent) {
          $slot.insertAfter($hiddenPageForm);
        }
      } else if (hostParent !== desiredParent || !$slot.parent().length) {
        $mainSection.prepend($slot);
      }

      return $slot;
    }

    const $pageContent = getPageContentRoot(frm);
    if (!$pageContent.length) return $();

    let $slot = $pageContent.children(".erpw-child-page-host").first();
    if ($slot.length) return $slot;

    $slot = $('<div class="erpw-child-page-host" data-erpw-child-page-host="1"></div>');
    const $layoutMain = $pageContent.children(".layout-main").first();
    if ($layoutMain.length) {
      $slot.insertBefore($layoutMain);
    } else {
      $pageContent.prepend($slot);
    }
    return $slot;
  }

  function getNativeLayoutAnchor(frm) {
    const $layout = getLayoutWrapper(frm);
    if ($layout.length) return $layout;

    const $root = getFormRoot(frm);
    if (!$root.length) return $();

    return $root.find(".std-form-layout").first().length
      ? $root.find(".std-form-layout").first()
      : $root.find(".form-layout").first().length
        ? $root.find(".form-layout").first()
        : $root.find(".layout-main-section").first().length
          ? $root.find(".layout-main-section").first()
          : $root.find(".form-page").first().length
            ? $root.find(".form-page").first()
            : $();
  }

  childPageRuntime.helpers = Object.assign({}, childPageRuntime.helpers || {}, {
    ensureChildPageHostSlot,
    escapeHtml,
    formatMoney,
    getPageContainerRoot,
    getFormRoot,
    getFormTaskState,
    getLayoutWrapper,
    getNativeLayoutAnchor,
    getPageContentRoot,
    routeToDoc,
    routeToList,
    scheduleFormTask,
    scrollViewportTop,
  });
})();
