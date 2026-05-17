(function () {
  let footerPatched = false;
  let sidebarPatched = false;

  function ensureSupportHeadMarkup($wrapper) {
    if (!$wrapper || !$wrapper.length) return;

    let $head = $wrapper.find(".erpw-so-support-head").first();
    if (!$head.length) {
      $head = $(`
        <div class="erpw-so-support-head">
          <div class="erpw-so-support-copy">
            <div class="erpw-so-support-title">Activity & Comments</div>
            <div class="erpw-so-support-note">Comments stay available. Expand activity only when you need deeper audit history.</div>
          </div>
          <button type="button" class="erpw-so-support-toggle" aria-expanded="false">
            <span class="erpw-so-support-toggle-text">Show Full Activity</span>
            <span class="erpw-so-support-toggle-icon" aria-hidden="true"></span>
          </button>
        </div>
      `);
      $wrapper.prepend($head);
      return;
    }

    if (!$head.find(".erpw-so-support-copy").length) {
      $head.prepend(`
        <div class="erpw-so-support-copy">
          <div class="erpw-so-support-title">Activity & Comments</div>
          <div class="erpw-so-support-note">Comments stay available. Expand activity only when you need deeper audit history.</div>
        </div>
      `);
    }

    if (!$head.find(".erpw-so-support-toggle").length) {
      $head.append(`
        <button type="button" class="erpw-so-support-toggle" aria-expanded="false">
          <span class="erpw-so-support-toggle-text">Show Full Activity</span>
          <span class="erpw-so-support-toggle-icon" aria-hidden="true"></span>
        </button>
      `);
    }
  }

  function patchFooter() {
    if (
      footerPatched ||
      !window.frappe ||
      !frappe.ui ||
      !frappe.ui.form ||
      !frappe.ui.form.Footer
    ) {
      return;
    }

    const proto = frappe.ui.form.Footer.prototype;
    if (!proto || typeof proto.make !== "function") return;

    const originalMake = proto.make;
    proto.make = function () {
      const result = originalMake.apply(this, arguments);
      if (this.frm && this.frm.doctype === "Sales Order" && this.wrapper) {
        this.wrapper.addClass("erpw-so-support-shell");
        this.wrapper.find(".comment-box").addClass("erpw-so-comment-block");
        this.wrapper.find(".timeline, .new-timeline").addClass("erpw-so-timeline-block");
        ensureSupportHeadMarkup(this.wrapper);
      }
      return result;
    };

    footerPatched = true;
  }

  function patchSidebar() {
    if (
      sidebarPatched ||
      !window.frappe ||
      !frappe.ui ||
      !frappe.ui.form ||
      !frappe.ui.form.Sidebar
    ) {
      return;
    }

    const proto = frappe.ui.form.Sidebar.prototype;
    if (!proto || typeof proto.make !== "function") return;

    const originalMake = proto.make;
    proto.make = function () {
      const result = originalMake.apply(this, arguments);
      if (this.frm && this.frm.doctype === "Sales Order" && this.sidebar) {
        this.sidebar.addClass("erpw-so-sidebar-shell");
        this.sidebar.find(".sidebar-section.text-muted.border-top.pt-3").addClass("erpw-so-sidebar-meta-hidden").hide();
      }
      return result;
    };

    sidebarPatched = true;
  }

  window.erpWorkspaceUiBoot = Object.assign(window.erpWorkspaceUiBoot || {}, {
    setSalesOrderPrep() {
      // First-paint prep takeover has been intentionally disabled.
      // Sales Order enhancement should never be allowed to blank the route.
    },
  });

  patchFooter();
  patchSidebar();
  setTimeout(patchFooter, 0);
  setTimeout(patchFooter, 80);
  setTimeout(patchFooter, 220);
  setTimeout(patchSidebar, 0);
  setTimeout(patchSidebar, 80);
  setTimeout(patchSidebar, 220);
})();
