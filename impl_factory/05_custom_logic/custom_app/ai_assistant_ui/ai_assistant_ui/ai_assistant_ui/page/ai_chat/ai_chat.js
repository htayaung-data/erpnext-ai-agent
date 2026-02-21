/* global frappe, $ */

(function () {
  function registerPage(pageKey) {
    frappe.pages[pageKey] = frappe.pages[pageKey] || {};
    frappe.pages[pageKey].on_page_load = function (wrapper) {
      const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: "AI Chat",
        single_column: true,
      });

      const state = {
        session: localStorage.getItem("ai_chat_session") || null,
        sessions: [],
        messages: [],
        renaming: null,
        menuOpenFor: null,
      };

      const MENU_ID = "ai-chat-session-popover-menu";

      const $root = $(`
        <div style="display:flex; gap:12px; height: calc(100vh - 140px);">
          <div class="ai-sidebar" style="width: 280px; border: 1px solid var(--border-color); border-radius: 8px; padding: 10px; overflow:auto; position:relative;">
            <div style="display:flex; gap:8px; align-items:center; margin-bottom:10px;">
              <button class="btn btn-sm btn-primary ai-new-chat">New chat</button>
            </div>
            <div class="ai-sessions"></div>
          </div>

          <div style="flex:1; border: 1px solid var(--border-color); border-radius: 8px; display:flex; flex-direction:column; overflow:hidden;">
            <div class="ai-messages" style="flex:1; padding: 12px; overflow:auto;"></div>
            <div style="border-top:1px solid var(--border-color); padding: 10px; display:flex; gap:8px;">
              <input class="form-control ai-input" placeholder="Ask something…" />
              <button class="btn btn-primary ai-send">Send</button>
            </div>
          </div>
        </div>
      `);

      $(page.body).empty().append($root);

      const $sessions = $root.find(".ai-sessions");
      const $messages = $root.find(".ai-messages");
      const $input = $root.find(".ai-input");

      function escapeHtml(s) {
        return String(s)
          .replaceAll("&", "&amp;")
          .replaceAll("<", "&lt;")
          .replaceAll(">", "&gt;")
          .replaceAll('"', "&quot;")
          .replaceAll("'", "&#039;");
      }

      function parseJsonIfPossible(content) {
        if (!content) return null;
        const s = String(content).trim();
        if (!s.startsWith("{") && !s.startsWith("[")) return null;
        try {
          return JSON.parse(s);
        } catch (e) {
          return null;
        }
      }

      function renderReportTable(payload) {
        const title = payload.title ? `<div style="font-weight:600; margin-bottom:4px;">${escapeHtml(payload.title)}</div>` : "";
        const subtitle = payload.subtitle ? `<div style="opacity:.7; margin-bottom:8px;">${escapeHtml(payload.subtitle)}</div>` : "";

        const cols = (payload.table && payload.table.columns) || [];
        const rows = (payload.table && payload.table.rows) || [];

        const th = cols.map(c => `<th style="white-space:nowrap;">${escapeHtml(c.label || c.fieldname)}</th>`).join("");
        const fns = cols.map(c => c.fieldname);

        const tr = rows.map(r => {
          const tds = fns.map(fn => `<td>${escapeHtml(r[fn] == null ? "" : r[fn])}</td>`).join("");
          return `<tr>${tds}</tr>`;
        }).join("");

        const tableHtml = `
          <div style="overflow:auto;">
            <table class="table table-bordered table-sm" style="margin:0;">
              <thead><tr>${th}</tr></thead>
              <tbody>${tr}</tbody>
            </table>
          </div>
        `;

        const dls = Array.isArray(payload.downloads) ? payload.downloads : [];
        const dlHtml = dls
          .filter(x => x && x.url)
          .map(x => `<a class="btn btn-xs btn-default" href="${encodeURI(x.url)}" target="_blank" rel="noopener">${escapeHtml(x.label || "Download")}</a>`)
          .join(" ");

        const dlBlock = dlHtml ? `<div style="margin-top:10px; display:flex; gap:8px; flex-wrap:wrap;">${dlHtml}</div>` : "";
        return `${title}${subtitle}${tableHtml}${dlBlock}`;
      }

      function renderTextPayload(payload) {
        if (payload && (payload.type === "text" || payload.type === "error") && payload.text) {
          return `<div>${escapeHtml(payload.text)}</div>`;
        }
        return null;
      }

      function renderMessage(msg) {
        const role = msg.role || "assistant";
        const payload = parseJsonIfPossible(msg.content);

        // Hide internal state + tool/audit messages from end users
        if (payload && (payload.type === "pending_state" || payload.type === "tool_result")) {
          return null;
        }

        let inner = null;
        if (payload && payload.type === "report_table") inner = renderReportTable(payload);
        else inner = renderTextPayload(payload);

        if (!inner) inner = `<div style="white-space:pre-wrap;">${escapeHtml(msg.content || "")}</div>`;

        const align = role === "user" ? "flex-end" : "flex-start";
        const bg = role === "user" ? "var(--blue-50)" : "var(--gray-50)";
        const border = "1px solid var(--border-color)";

        return $(`
          <div style="display:flex; justify-content:${align}; margin: 6px 0;">
            <div style="max-width: 88%; background:${bg}; ${border}; border-radius: 10px; padding: 10px 12px;">
              ${inner}
            </div>
          </div>
        `);
      }

      function redrawMessages() {
        $messages.empty();
        state.messages.forEach(m => {
          const $el = renderMessage(m);
          if ($el) $messages.append($el);
        });
        $messages.scrollTop($messages.prop("scrollHeight"));
      }

      function removePopover() {
        $("#" + MENU_ID).remove();
        state.menuOpenFor = null;
      }

      function ensurePopover() {
        let $menu = $("#" + MENU_ID);
        if ($menu.length) return $menu;

        $menu = $(`
          <div id="${MENU_ID}" style="
            position: fixed;
            z-index: 9999;
            min-width: 180px;
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            box-shadow: var(--shadow-lg, 0 8px 24px rgba(0,0,0,0.15));
            padding: 6px;
            display: none;
          ">
            <button class="btn btn-default btn-sm ai-menu-rename" style="width:100%; text-align:left; display:flex; gap:8px; align-items:center;">
              <i class="fa fa-pencil"></i><span>Rename</span>
            </button>
            <button class="btn btn-default btn-sm ai-menu-delete" style="width:100%; text-align:left; display:flex; gap:8px; align-items:center; margin-top:6px; color: var(--red-500);">
              <i class="fa fa-trash"></i><span>Delete</span>
            </button>
          </div>
        `);

        $("body").append($menu);
        return $menu;
      }

      function openPopoverFor(sessionName, anchorEl) {
        const rect = anchorEl.getBoundingClientRect();
        state.menuOpenFor = sessionName;

        const $menu = ensurePopover();
        $menu.show();

        const gap = 6;
        let top = rect.bottom + gap;
        let left = rect.right - 180;
        $menu.css({ top: top + "px", left: left + "px" });

        const mw = $menu.outerWidth();
        const mh = $menu.outerHeight();
        left = rect.right - mw;
        if (left < 8) left = 8;

        const vw = window.innerWidth;
        const vh = window.innerHeight;

        if (left + mw > vw - 8) left = vw - mw - 8;
        if (top + mh > vh - 8) top = rect.top - mh - gap;
        if (top < 8) top = 8;

        $menu.css({ top: top + "px", left: left + "px" });

        $menu.find(".ai-menu-rename").off("click").on("click", (e) => {
          e.preventDefault();
          e.stopPropagation();
          removePopover();
          state.renaming = sessionName;
          redrawSessions();
          setTimeout(() => {
            $sessions.find(`.ai-session-row[data-session="${sessionName}"] .ai-title-input`).focus().select();
          }, 0);
        });

        $menu.find(".ai-menu-delete").off("click").on("click", (e) => {
          e.preventDefault();
          e.stopPropagation();
          removePopover();
          frappe.confirm("Delete this chat session?", () => {
            frappe.call({
              method: "ai_assistant_ui.api.delete_session",
              args: { session_name: sessionName },
              callback: async () => {
                if (state.session === sessionName) {
                  state.session = null;
                  localStorage.removeItem("ai_chat_session");
                }
                await loadSessions();
                if (!state.session && state.sessions.length) {
                  await setSession(state.sessions[0].name);
                }
              },
            });
          });
        });
      }

      $(document).off("click.ai_chat_popover").on("click.ai_chat_popover", (e) => {
        const $menu = $("#" + MENU_ID);
        if (!$menu.length) return;
        if ($(e.target).closest("#" + MENU_ID).length) return;
        if ($(e.target).closest(".ai-ellipsis").length) return;
        removePopover();
      });
      $(window).off("resize.ai_chat_popover").on("resize.ai_chat_popover", removePopover);
      $root.find(".ai-sidebar").off("scroll.ai_chat_popover").on("scroll.ai_chat_popover", removePopover);

      function redrawSessions() {
        $sessions.empty();

        state.sessions.forEach(s => {
          const isActive = s.name === state.session;
          const isRenaming = state.renaming === s.name;

          const $row = $(`
            <div class="ai-session-row" data-session="${escapeHtml(s.name)}"
                 style="display:flex; align-items:center; justify-content:space-between; gap:8px; padding:6px; border-radius:6px; cursor:pointer; ${isActive ? "background: var(--gray-100);" : ""}">
              <div style="flex:1; min-width:0;">
                <span class="ai-title-text" style="display:${isRenaming ? "none" : "block"}; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">
                  ${escapeHtml(s.title || s.name)}
                </span>
                <input class="form-control input-xs ai-title-input"
                       style="display:${isRenaming ? "block" : "none"}; height:26px; padding:2px 6px;"
                       value="${escapeHtml(s.title || "")}" />
              </div>

              <button class="btn btn-xs btn-default ai-ellipsis" title="More"
                      style="width:28px; height:28px; flex:0 0 auto; display:${isRenaming ? "none" : "inline-flex"}; align-items:center; justify-content:center;">
                <i class="fa fa-ellipsis-h"></i>
              </button>
            </div>
          `);

          $row.on("click", (e) => {
            if ($(e.target).closest("button").length) return;
            if ($(e.target).closest("input").length) return;
            setSession(s.name);
          });

          $row.find(".ai-ellipsis").on("click", (e) => {
            e.preventDefault();
            e.stopPropagation();
            const btn = e.currentTarget;
            if (state.menuOpenFor === s.name && $("#" + MENU_ID).length) {
              removePopover();
              return;
            }
            removePopover();
            openPopoverFor(s.name, btn);
          });

          function closeRename() {
            state.renaming = null;
            redrawSessions();
          }

          function commitRename(newTitle) {
            const title = String(newTitle || "").trim();
            if (!title) {
              closeRename();
              return;
            }
            frappe.call({
              method: "ai_assistant_ui.api.rename_session",
              args: { session_name: s.name, title },
              callback: async () => {
                await loadSessions();
                closeRename();
              },
            });
          }

          $row.find(".ai-title-input").on("keydown", function (e) {
            if (e.key === "Enter") {
              e.preventDefault();
              commitRename($(this).val());
            } else if (e.key === "Escape") {
              e.preventDefault();
              closeRename();
            }
          });

          $row.find(".ai-title-input").on("blur", function () {
            commitRename($(this).val());
          });

          $sessions.append($row);
        });
      }

      function loadSessions() {
        return new Promise((resolve) => {
          frappe.call({
            method: "ai_assistant_ui.api.get_sessions",
            callback: (r) => {
              state.sessions = r.message || [];
              redrawSessions();
              resolve();
            },
          });
        });
      }

      function createSession() {
        return new Promise((resolve) => {
          frappe.call({
            method: "ai_assistant_ui.api.create_session",
            args: {},
            callback: (r) => resolve(r.message),
          });
        });
      }

      function loadMessages(sessionName) {
        return new Promise((resolve) => {
          frappe.call({
            method: "ai_assistant_ui.api.get_messages",
            args: { session_name: sessionName },
            callback: (r) => {
              state.messages = r.message || [];
              redrawMessages();
              resolve();
            },
          });
        });
      }

      async function setSession(sessionName) {
        state.session = sessionName;
        localStorage.setItem("ai_chat_session", sessionName);
        redrawSessions();
        await loadMessages(sessionName);
      }

      async function sendMessage() {
        const text = ($input.val() || "").trim();
        if (!text) return;

        if (!state.session) {
          const created = await createSession();
          state.session = created.name;
          localStorage.setItem("ai_chat_session", state.session);
          await loadSessions();
        }

        $input.val("");
        state.messages.push({ role: "user", content: text });
        redrawMessages();

        frappe.call({
          method: "ai_assistant_ui.api.chat_send",
          args: { session_name: state.session, message: text },
          callback: async () => {
            await loadMessages(state.session);
            await loadSessions();
          },
          error: async () => {
            await loadMessages(state.session);
          },
        });
      }

      $root.find(".ai-new-chat").on("click", async () => {
        removePopover();
        const created = await createSession();
        await loadSessions();
        await setSession(created.name);
      });

      $root.find(".ai-send").on("click", sendMessage);
      $input.on("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
          e.preventDefault();
          sendMessage();
        }
      });

      (async function init() {
        await loadSessions();
        if (state.session && state.sessions.some(s => s.name === state.session)) {
          await loadMessages(state.session);
        } else if (state.sessions.length) {
          await setSession(state.sessions[0].name);
        } else {
          const created = await createSession();
          await loadSessions();
          await setSession(created.name);
        }
      })();
    };
  }

  registerPage("ai-chat");
  registerPage("ai_chat");
})();
