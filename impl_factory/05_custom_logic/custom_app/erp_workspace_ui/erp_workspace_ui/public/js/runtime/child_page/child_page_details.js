(function () {
  const root = window;
  const childPageRuntime = root.erpWorkspaceUiChildPage = root.erpWorkspaceUiChildPage || {};
  const childPageHelpers = childPageRuntime.helpers || {};

  const escapeHtml = childPageHelpers.escapeHtml || function (value) {
    return frappe.utils.escape_html(value == null ? "" : String(value));
  };
  const resolveBusinessNote = childPageHelpers.resolveBusinessNote || function (note) {
    return note == null ? "" : String(note).trim();
  };

  function ensureCriticalStyles() {
    const styleId = "erpw-child-details-critical-styles";
    if (document.getElementById(styleId)) return;

    const style = document.createElement("style");
    style.id = styleId;
    style.textContent = `
      .erpw-child-detail-snapshot { margin-bottom:0.9rem; padding:0.94rem 1rem 1rem; border-radius:18px; border:1px solid rgba(226,232,240,0.92); background:linear-gradient(180deg, rgba(251,253,255,0.985) 0%, rgba(255,255,255,0.99) 100%); box-shadow:0 1px 0 rgba(255,255,255,0.98) inset, 0 8px 18px rgba(15,23,42,0.022); }
      .erpw-child-detail-snapshot-head { display:flex; align-items:flex-start; justify-content:space-between; gap:0.8rem; }
      .erpw-child-detail-snapshot-kicker { color:#334155; font-size:0.7rem; line-height:1.2; letter-spacing:0.08em; text-transform:uppercase; font-weight:800; }
      .erpw-child-detail-snapshot-note { margin-top:0.24rem; max-width:560px; color:#6b7a8d; font-size:0.78rem; line-height:1.45; font-weight:500; }
      .erpw-child-detail-snapshot-status { display:inline-flex; align-items:center; justify-content:center; min-height:24px; padding:0.16rem 0.56rem; border-radius:999px; border:1px solid rgba(211,219,230,0.86); background:rgba(248,250,252,0.94); color:#5b687a; font-size:0.68rem; line-height:1; font-weight:700; white-space:nowrap; }
      .erpw-child-detail-snapshot-status[data-tone="active"] { border-color:rgba(153,246,228,0.56); background:rgba(240,253,250,0.82); color:#0f766e; }
      .erpw-child-detail-snapshot-status[data-tone="attention"] { border-color:rgba(245,217,165,0.7); background:rgba(255,248,238,0.94); color:#9a5b12; }
      .erpw-child-detail-snapshot-grid { display:grid; grid-template-columns:repeat(4, minmax(0, 1fr)); gap:0.72rem; margin-top:0.82rem; }
      .erpw-child-detail-snapshot-metric { min-width:0; padding:0.82rem 0.88rem 0.86rem; border-radius:15px; border:1px solid rgba(255,255,255,0.98); background:#fff; box-shadow:0 8px 16px rgba(15,23,42,0.04); }
      .erpw-child-detail-snapshot-label { color:#64748b; font-size:0.66rem; line-height:1.2; letter-spacing:0.08em; text-transform:uppercase; font-weight:800; }
      .erpw-child-detail-snapshot-value { margin-top:0.34rem; color:#0f172a; font-size:0.84rem; line-height:1.35; font-weight:720; word-break:break-word; }
      .erpw-child-section-header { display:flex; align-items:flex-start; justify-content:space-between; gap:0.8rem; margin-bottom:0.72rem; }
      .erpw-child-section-header-title { color:#0f172a; font-size:0.82rem; line-height:1.2; font-weight:760; }
      .erpw-child-section-header-note { margin-top:0.22rem; max-width:620px; color:#6b7a8d; font-size:0.77rem; line-height:1.45; font-weight:500; }
      .erpw-child-section-header-status { display:inline-flex; align-items:center; justify-content:center; min-height:24px; padding:0.16rem 0.56rem; border-radius:999px; border:1px solid rgba(211,219,230,0.86); background:rgba(248,250,252,0.94); color:#5b687a; font-size:0.68rem; line-height:1; font-weight:700; white-space:nowrap; }
      .erpw-child-section-header-status[data-tone="attention"] { border-color:rgba(245,217,165,0.7); background:rgba(255,248,238,0.94); color:#9a5b12; }
      .erpw-child-inline-summary-soft { margin-top:0.82rem; padding:0.88rem 0.98rem 1rem; border-radius:18px; border:1px solid rgba(226,232,240,0.92); background:linear-gradient(180deg, rgba(251,253,255,0.985) 0%, rgba(255,255,255,0.99) 100%); box-shadow:0 1px 0 rgba(255,255,255,0.98) inset, 0 8px 18px rgba(15,23,42,0.022); }
      .erpw-child-inline-summary-soft .erpw-so-inline-summary-head { display:grid; grid-template-columns:minmax(0, 1fr) auto; column-gap:0.9rem; row-gap:0.4rem; align-items:start; }
      .erpw-child-inline-summary-soft .erpw-child-inline-summary-note { display:block; grid-column:1; max-width:460px; color:#7b8796; font-size:0.74rem; line-height:1.4; }
      .erpw-child-inline-summary-soft .erpw-child-chip-row { grid-column:1 / -1; margin-top:0; }
      .erpw-child-inline-summary-soft .erpw-child-chip { border:1px solid rgba(211,219,230,0.86); background:rgba(248,250,252,0.96); color:#475569; font-size:0.7rem; font-weight:680; }
      .erpw-child-inline-summary-soft .erpw-child-chip.neutral { color:#475569; border-color:rgba(211,219,230,0.86); background:rgba(248,250,252,0.96); }
      .erpw-child-inline-summary-soft .erpw-child-chip.pending { color:#1d4ed8; border-color:rgba(191,219,254,0.72); background:rgba(239,246,255,0.96); }
      .erpw-child-inline-summary-soft .erpw-child-chip.approved, .erpw-child-inline-summary-soft .erpw-child-chip.good { color:#0f766e; border-color:rgba(153,246,228,0.64); background:rgba(240,253,250,0.96); }
      .erpw-child-inline-summary-soft .erpw-child-chip.attention { color:#9a5b12; border-color:rgba(245,217,165,0.7); background:rgba(255,248,238,0.94); }
      .erpw-child-inline-summary-soft .erpw-child-chip.blocker { color:#b91c1c; border-color:rgba(252,165,165,0.72); background:rgba(254,242,242,0.96); }
      .erpw-child-inline-summary-soft .erpw-so-inline-metric { min-height:72px; }
      .erpw-child-inline-summary-soft-standalone { margin-top:0.9rem; padding-inline:15px; }
      @media (max-width: 1100px) {
        .erpw-child-detail-snapshot-grid { grid-template-columns:repeat(2, minmax(0, 1fr)); }
        .erpw-child-inline-summary-soft .erpw-so-inline-summary-head, .erpw-child-section-header, .erpw-child-detail-snapshot-head { display:grid; grid-template-columns:1fr; }
      }
    `;
    document.head.appendChild(style);
  }

  function renderDetailSnapshot($anchorSection, options) {
    if (!$anchorSection || !$anchorSection.length) return $();
    ensureCriticalStyles();

    const settings = Object.assign({
      kicker: "",
      note: "",
      noteIntent: "",
      metrics: [],
      removeSelector: ".erpw-child-detail-snapshot",
      snapshotClass: "erpw-child-detail-snapshot",
      statusText: "",
      statusTone: "neutral",
    }, options || {});

    if (settings.removeSelector) {
      $anchorSection.prevAll(settings.removeSelector).first().remove();
    }

    const metrics = Array.isArray(settings.metrics) ? settings.metrics : [];
    const noteText = resolveBusinessNote(settings.note, {
      intent: settings.noteIntent,
      statusText: settings.statusText,
      statusTone: settings.statusTone,
      surface: "detail-snapshot",
    });
    const $snapshot = $(`
      <section class="${escapeHtml(settings.snapshotClass)}">
        <div class="erpw-child-detail-snapshot-head">
          <div class="erpw-child-detail-snapshot-copy">
            <div class="erpw-child-detail-snapshot-kicker">${escapeHtml(settings.kicker || "")}</div>
            ${noteText ? `<div class="erpw-child-detail-snapshot-note">${escapeHtml(noteText)}</div>` : ""}
          </div>
          ${settings.statusText ? `<div class="erpw-child-detail-snapshot-status" data-tone="${escapeHtml(settings.statusTone || "neutral")}">${escapeHtml(settings.statusText)}</div>` : ""}
        </div>
        <div class="erpw-child-detail-snapshot-grid">
          ${metrics.map((metric) => `
            <div class="erpw-child-detail-snapshot-metric">
              <div class="erpw-child-detail-snapshot-label">${escapeHtml(metric.label || "")}</div>
              <div class="erpw-child-detail-snapshot-value">${escapeHtml(metric.value || "--")}</div>
            </div>
          `).join("")}
        </div>
      </section>
    `);

    $anchorSection.before($snapshot);
    return $snapshot;
  }

  function renderSectionHeader($section, options) {
    if (!$section || !$section.length) return $();
    ensureCriticalStyles();

    const settings = Object.assign({
      headerClass: "erpw-child-section-header",
      note: "",
      noteIntent: "",
      removeSelector: ".erpw-child-section-header",
      statusText: "",
      statusTone: "neutral",
      title: "",
    }, options || {});

    if (settings.removeSelector) {
      $section.find(settings.removeSelector).remove();
    }

    const noteText = resolveBusinessNote(settings.note, {
      intent: settings.noteIntent,
      statusText: settings.statusText,
      statusTone: settings.statusTone,
      surface: "detail-section-header",
    });
    const $header = $(`
      <div class="${escapeHtml(settings.headerClass)}">
        <div class="erpw-child-section-header-copy">
          <div class="erpw-child-section-header-title">${escapeHtml(settings.title || "")}</div>
          ${noteText ? `<div class="erpw-child-section-header-note">${escapeHtml(noteText)}</div>` : ""}
        </div>
        ${settings.statusText ? `<div class="erpw-child-section-header-status" data-tone="${escapeHtml(settings.statusTone || "neutral")}">${escapeHtml(settings.statusText)}</div>` : ""}
      </div>
    `);

    const $gridField = $section.find(".grid-field").first();
    if ($gridField.length) {
      const $control = $gridField.closest(".frappe-control");
      if ($control.length) {
        $control.children(".control-label, .help, .grid-description").hide();
      }
      $gridField.before($header);
    } else {
      $section.prepend($header);
    }

    return $header;
  }

  childPageRuntime.details = Object.assign({}, childPageRuntime.details || {}, {
    ensureCriticalStyles,
    renderDetailSnapshot,
    renderSectionHeader,
  });
})();
