/* global frappe, $ */

(function () {
  function registerPage(pageKey) {
    frappe.pages[pageKey] = frappe.pages[pageKey] || {};
    frappe.pages[pageKey].on_page_load = function (wrapper) {
      const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: "Qwen Chat",
        single_column: true,
      });

      const state = {
        session: localStorage.getItem("qwen_chat_session") || null,
        sessions: [],
        messages: [],
        pendingRequests: 0,
        optimisticMessages: [],
        renaming: null,
        menuOpenFor: null,
      };

      const MENU_ID = "qwen-chat-session-popover-menu";

      const $root = $(`
        <div style="display:flex; gap:12px; height: calc(100vh - 140px);">
          <div class="qwen-sidebar" style="width: 280px; border: 1px solid var(--border-color); border-radius: 8px; padding: 10px; overflow:auto; position:relative;">
            <div style="display:flex; gap:8px; align-items:center; margin-bottom:10px;">
              <button class="btn btn-sm btn-primary qwen-new-chat">New chat</button>
              <button class="btn btn-sm btn-default qwen-clear-history">Clear history</button>
            </div>
            <div class="qwen-sessions"></div>
          </div>

          <div style="flex:1; border: 1px solid var(--border-color); border-radius: 8px; display:flex; flex-direction:column; overflow:hidden;">
            <div class="qwen-messages" style="flex:1; padding: 12px; overflow:auto;"></div>
            <div style="border-top:1px solid var(--border-color); padding: 10px; display:flex; gap:8px;">
              <input class="form-control qwen-input" placeholder="Ask ERP with Qwen…" />
              <button class="btn btn-primary qwen-send">Send</button>
            </div>
          </div>
        </div>
      `);

      $(page.body).empty().append($root);

      const $sessions = $root.find(".qwen-sessions");
      const $messages = $root.find(".qwen-messages");
      const $input = $root.find(".qwen-input");
      const $send = $root.find(".qwen-send");
      const $newChat = $root.find(".qwen-new-chat");
      const $clearHistory = $root.find(".qwen-clear-history");

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

      function renderTextPayload(payload) {
        if (payload && (payload.type === "text" || payload.type === "error") && payload.text) {
          return renderMarkdownText(String(payload.text || ""));
        }
        return null;
      }

      function renderInlineMarkdown(text) {
        return String(text || "")
          .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
          .replace(/`([^`]+)`/g, "<code>$1</code>");
      }

      function isMarkdownTableSeparator(line) {
        return /^\s*\|?(?:\s*:?-{3,}:?\s*\|)+\s*:?-{3,}:?\s*\|?\s*$/.test(line || "");
      }

      function splitMarkdownCells(line) {
        let value = String(line || "").trim();
        if (value.startsWith("|")) value = value.slice(1);
        if (value.endsWith("|")) value = value.slice(0, -1);
        return value.split("|").map(cell => renderInlineMarkdown(escapeHtml(cell.trim())));
      }

      function renderMarkdownTable(blockLines) {
        if (blockLines.length < 2) return "";
        const headerCells = splitMarkdownCells(blockLines[0]);
        const bodyLines = blockLines.slice(2).filter(line => String(line || "").trim());
        const thead = `<thead><tr>${headerCells.map(cell => `<th>${cell}</th>`).join("")}</tr></thead>`;
        const tbody = bodyLines.map(line => {
          const cells = splitMarkdownCells(line);
          return `<tr>${cells.map(cell => `<td>${cell}</td>`).join("")}</tr>`;
        }).join("");
        return `
          <div class="qwen-md-table-wrap">
            <table class="qwen-md-table">
              ${thead}
              <tbody>${tbody}</tbody>
            </table>
          </div>
        `;
      }

      function renderMarkdownText(text) {
        const source = String(text || "").replace(/\r\n/g, "\n").trim();
        if (!source) return "<div></div>";

        const lines = source.split("\n");
        const parts = [];
        let i = 0;

        while (i < lines.length) {
          const rawLine = lines[i];
          const line = String(rawLine || "");
          const trimmed = line.trim();

          if (!trimmed) {
            i += 1;
            continue;
          }

          const nextLine = i + 1 < lines.length ? lines[i + 1] : "";
          if (trimmed.includes("|") && isMarkdownTableSeparator(nextLine)) {
            const tableBlock = [line, nextLine];
            i += 2;
            while (i < lines.length) {
              const bodyLine = String(lines[i] || "");
              if (!bodyLine.trim() || !bodyLine.includes("|")) break;
              tableBlock.push(bodyLine);
              i += 1;
            }
            parts.push(renderMarkdownTable(tableBlock));
            continue;
          }

          if (trimmed.startsWith("### ")) {
            parts.push(`<h4 class="qwen-md-h3">${renderInlineMarkdown(escapeHtml(trimmed.slice(4)))}</h4>`);
            i += 1;
            continue;
          }

          if (trimmed.startsWith("## ")) {
            parts.push(`<h3 class="qwen-md-h2">${renderInlineMarkdown(escapeHtml(trimmed.slice(3)))}</h3>`);
            i += 1;
            continue;
          }

          if (trimmed.startsWith("# ")) {
            parts.push(`<h2 class="qwen-md-h1">${renderInlineMarkdown(escapeHtml(trimmed.slice(2)))}</h2>`);
            i += 1;
            continue;
          }

          if (trimmed.startsWith("- ")) {
            const items = [];
            while (i < lines.length) {
              const bullet = String(lines[i] || "").trim();
              if (!bullet.startsWith("- ")) break;
              items.push(`<li>${renderInlineMarkdown(escapeHtml(bullet.slice(2)))}</li>`);
              i += 1;
            }
            parts.push(`<ul class="qwen-md-list">${items.join("")}</ul>`);
            continue;
          }

          const paragraphLines = [line];
          i += 1;
          while (i < lines.length) {
            const lookahead = String(lines[i] || "");
            const lookaheadTrimmed = lookahead.trim();
            const lookaheadNext = i + 1 < lines.length ? lines[i + 1] : "";
            if (
              !lookaheadTrimmed ||
              lookaheadTrimmed.startsWith("#") ||
              lookaheadTrimmed.startsWith("- ") ||
              (lookaheadTrimmed.includes("|") && isMarkdownTableSeparator(lookaheadNext))
            ) {
              break;
            }
            paragraphLines.push(lookahead);
            i += 1;
          }
          parts.push(
            `<p class="qwen-md-paragraph">${renderInlineMarkdown(
              escapeHtml(paragraphLines.join(" "))
            )}</p>`
          );
        }

        return `<div class="qwen-md-body">${parts.join("")}</div>`;
      }

      function renderMessage(msg) {
        const role = msg.role || "assistant";
        if (role === "tool") return null;

        const payload = parseJsonIfPossible(msg.content);
        let inner = renderTextPayload(payload);
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

      function ensureTypingStyle() {
        if (document.getElementById("qwen-chat-typing-style")) return;
        const styleEl = document.createElement("style");
        styleEl.id = "qwen-chat-typing-style";
        styleEl.textContent = `
          @keyframes qwenChatTypingPulse {
            0%, 80%, 100% { opacity: .3; transform: translateY(0); }
            40% { opacity: 1; transform: translateY(-2px); }
          }
          .qwen-chat-typing-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: var(--text-muted, #8d99a6);
            display: inline-block;
            animation: qwenChatTypingPulse 1.2s infinite ease-in-out;
          }
          .qwen-md-body {
            line-height: 1.5;
          }
          .qwen-md-body > *:first-child {
            margin-top: 0;
          }
          .qwen-md-body > *:last-child {
            margin-bottom: 0;
          }
          .qwen-md-h1,
          .qwen-md-h2,
          .qwen-md-h3 {
            margin: 0 0 8px;
            font-weight: 600;
          }
          .qwen-md-h1 { font-size: 1.15rem; }
          .qwen-md-h2 { font-size: 1.05rem; }
          .qwen-md-h3 { font-size: 0.98rem; }
          .qwen-md-paragraph {
            margin: 0 0 8px;
            white-space: normal;
          }
          .qwen-md-list {
            margin: 0 0 8px 18px;
            padding: 0;
          }
          .qwen-md-table-wrap {
            overflow-x: auto;
            margin: 8px 0;
          }
          .qwen-md-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
          }
          .qwen-md-table th,
          .qwen-md-table td {
            border: 1px solid var(--border-color);
            padding: 6px 8px;
            vertical-align: top;
            text-align: left;
            white-space: nowrap;
          }
          .qwen-md-table th {
            background: var(--gray-100);
            font-weight: 600;
          }
        `;
        document.head.appendChild(styleEl);
      }

      function renderTypingIndicator() {
        return $(`
          <div style="display:flex; justify-content:flex-start; margin: 6px 0;">
            <div style="background: var(--gray-50); border: 1px solid var(--border-color); border-radius: 10px; padding: 12px 12px;">
              <span class="qwen-chat-typing-dot" style="animation-delay:0s;"></span>
              <span class="qwen-chat-typing-dot" style="animation-delay:0.2s; margin-left:4px;"></span>
              <span class="qwen-chat-typing-dot" style="animation-delay:0.4s; margin-left:4px;"></span>
            </div>
          </div>
        `);
      }

      function redrawMessages() {
        $messages.empty();
        const allMessages = state.messages.concat(state.optimisticMessages);
        allMessages.forEach(m => {
          const $el = renderMessage(m);
          if ($el) $messages.append($el);
        });
        if (state.pendingRequests > 0) {
          $messages.append(renderTypingIndicator());
        }
        $messages.scrollTop($messages.prop("scrollHeight"));
        syncComposerState();
      }

      function syncComposerState() {
        const busy = state.pendingRequests > 0;
        $input.prop("disabled", busy);
        $send.prop("disabled", busy);
        $newChat.prop("disabled", busy);
        $input.attr("placeholder", busy ? "Qwen is answering..." : "Ask ERP with Qwen…");
      }

      function showPendingRequestAlert(actionLabel) {
        frappe.show_alert({
          message: `Please wait for the current Qwen response to finish before ${actionLabel}.`,
          indicator: "orange",
        });
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
            <button class="btn btn-default btn-sm qwen-menu-rename" style="width:100%; text-align:left; display:flex; gap:8px; align-items:center;">
              <i class="fa fa-pencil"></i><span>Rename</span>
            </button>
            <button class="btn btn-default btn-sm qwen-menu-delete" style="width:100%; text-align:left; display:flex; gap:8px; align-items:center; margin-top:6px; color: var(--red-500);">
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

        $menu.find(".qwen-menu-rename").off("click").on("click", e => {
          e.preventDefault();
          e.stopPropagation();
          removePopover();
          state.renaming = sessionName;
          redrawSessions();
          setTimeout(() => {
            $sessions.find(`.qwen-session-row[data-session="${sessionName}"] .qwen-title-input`).focus().select();
          }, 0);
        });

        $menu.find(".qwen-menu-delete").off("click").on("click", e => {
          e.preventDefault();
          e.stopPropagation();
          removePopover();
          frappe.confirm("Delete this Qwen chat session?", async () => {
            await frappe.call({
              method: "ai_assistant_ui.api.delete_qwen_session",
              args: { session_name: sessionName },
            });
            if (state.session === sessionName) {
              state.session = null;
              localStorage.removeItem("qwen_chat_session");
              state.messages = [];
              state.optimisticMessages = [];
              redrawMessages();
            }
            await loadSessions();
            if (!state.session && state.sessions.length) {
              state.session = state.sessions[0].name;
              localStorage.setItem("qwen_chat_session", state.session);
              await loadMessages();
            }
          });
        });
      }

      $(document).off("click.qwen_chat_popover").on("click.qwen_chat_popover", e => {
        const $menu = $("#" + MENU_ID);
        if (!$menu.length) return;
        if ($(e.target).closest("#" + MENU_ID).length) return;
        if ($(e.target).closest(".qwen-ellipsis").length) return;
        removePopover();
      });
      $(window).off("resize.qwen_chat_popover").on("resize.qwen_chat_popover", removePopover);
      $root.find(".qwen-sidebar").off("scroll.qwen_chat_popover").on("scroll.qwen_chat_popover", removePopover);

      function redrawSessions() {
        $sessions.empty();
        $clearHistory.prop("disabled", state.pendingRequests > 0 || !state.sessions.length);
        if (!state.sessions.length) {
          $sessions.append(`<div style="opacity:.7; font-size:12px;">No Qwen chats yet.</div>`);
          return;
        }
        state.sessions.forEach(s => {
          const active = state.session === s.name;
          const isRenaming = state.renaming === s.name;
          const $row = $(`
            <div class="qwen-session-row" data-session="${escapeHtml(s.name)}"
                 style="display:flex; align-items:center; justify-content:space-between; gap:8px; padding:6px; border-radius:6px; cursor:pointer; ${active ? "background: var(--gray-100);" : ""}">
              <div style="flex:1; min-width:0;">
                <span class="qwen-title-text" style="display:${isRenaming ? "none" : "block"}; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">
                  ${escapeHtml(s.title || s.name)}
                </span>
                <input class="form-control input-xs qwen-title-input"
                       style="display:${isRenaming ? "block" : "none"}; height:26px; padding:2px 6px;"
                       value="${escapeHtml(s.title || "")}" />
              </div>
              <button class="btn btn-xs btn-default qwen-ellipsis" title="More"
                      style="width:28px; height:28px; flex:0 0 auto; display:${isRenaming ? "none" : "inline-flex"}; align-items:center; justify-content:center;">
                <i class="fa fa-ellipsis-h"></i>
              </button>
            </div>
          `);

          $row.on("click", e => {
            if ($(e.target).closest("button").length) return;
            if ($(e.target).closest("input").length) return;
            if (state.pendingRequests > 0) {
              showPendingRequestAlert("switching chats");
              return;
            }
            state.session = s.name;
            localStorage.setItem("qwen_chat_session", state.session);
            redrawSessions();
            loadMessages();
          });

          $row.find(".qwen-ellipsis").on("click", e => {
            e.preventDefault();
            e.stopPropagation();
            if (state.pendingRequests > 0) {
              showPendingRequestAlert("opening chat actions");
              return;
            }
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
              method: "ai_assistant_ui.api.rename_qwen_session",
              args: { session_name: s.name, title },
              callback: async () => {
                await loadSessions();
                closeRename();
              },
            });
          }

          $row.find(".qwen-title-input").on("keydown", function (e) {
            if (e.key === "Enter") {
              e.preventDefault();
              commitRename($(this).val());
            } else if (e.key === "Escape") {
              e.preventDefault();
              closeRename();
            }
          });

          $row.find(".qwen-title-input").on("blur", function () {
            commitRename($(this).val());
          });

          $sessions.append($row);
        });
      }

      async function loadSessions() {
        const r = await frappe.call({ method: "ai_assistant_ui.api.get_qwen_sessions" });
        state.sessions = Array.isArray(r.message) ? r.message : [];
        if (state.session && !state.sessions.find(s => s.name === state.session)) {
          state.session = null;
          localStorage.removeItem("qwen_chat_session");
        }
        if (!state.session && state.sessions.length) {
          state.session = state.sessions[0].name;
          localStorage.setItem("qwen_chat_session", state.session);
        }
        redrawSessions();
      }

      async function createSession() {
        removePopover();
        const r = await frappe.call({ method: "ai_assistant_ui.api.create_qwen_session" });
        const row = r.message || {};
        state.session = row.name || null;
        if (state.session) {
          localStorage.setItem("qwen_chat_session", state.session);
        }
        await loadSessions();
        await loadMessages();
      }

      async function clearHistory() {
        removePopover();
        if (state.pendingRequests > 0) {
          showPendingRequestAlert("clearing chat history");
          return;
        }
        if (!state.sessions.length) {
          frappe.show_alert({ message: "There is no Qwen chat history to clear.", indicator: "blue" });
          return;
        }
        frappe.confirm("Clear all Qwen chat history for your account? This cannot be undone.", async () => {
          await frappe.call({
            method: "ai_assistant_ui.api.clear_qwen_sessions",
            args: { confirm: 1 },
          });
          state.session = null;
          state.sessions = [];
          state.messages = [];
          state.optimisticMessages = [];
          localStorage.removeItem("qwen_chat_session");
          redrawSessions();
          redrawMessages();
          await createSession();
          frappe.show_alert({ message: "Qwen chat history cleared.", indicator: "green" });
        });
      }

      async function loadMessages() {
        if (!state.session) {
          state.messages = [];
          state.optimisticMessages = [];
          redrawMessages();
          return;
        }
        const r = await frappe.call({
          method: "ai_assistant_ui.api.get_qwen_messages",
          args: { session_name: state.session },
        });
        state.messages = Array.isArray(r.message) ? r.message : [];
        state.optimisticMessages = [];
        redrawMessages();
      }

      async function sendMessage() {
        if (state.pendingRequests > 0) {
          showPendingRequestAlert("sending another message in this chat");
          return;
        }
        const text = ($input.val() || "").trim();
        if (!text) return;
        if (!state.session) {
          await createSession();
        }
        $input.val("");
        state.optimisticMessages.push({ role: "user", content: text });
        state.pendingRequests += 1;
        redrawMessages();
        try {
          const r = await frappe.call({
            method: "ai_assistant_ui.api.qwen_chat_send",
            args: { session_name: state.session, message: text },
          });
          if (r.message && r.message.ok === false && r.message.error) {
            frappe.show_alert({ message: r.message.error, indicator: "red" });
          }
          await loadSessions();
          await loadMessages();
        } catch (e) {
          state.optimisticMessages.push({
            role: "assistant",
            content: JSON.stringify({
              type: "error",
              text: "Qwen chat request failed before the response could be saved. Please try again.",
            }),
          });
          redrawMessages();
          throw e;
        } finally {
          state.pendingRequests = Math.max(0, state.pendingRequests - 1);
          redrawMessages();
        }
      }

      ensureTypingStyle();
      $newChat.on("click", async () => {
        if (state.pendingRequests > 0) {
          showPendingRequestAlert("starting a new chat");
          return;
        }
        await createSession();
      });
      $clearHistory.on("click", clearHistory);
      $send.on("click", sendMessage);
      $input.on("keydown", e => {
        if (e.key === "Enter") {
          e.preventDefault();
          sendMessage();
        }
      });

      (async function init() {
        await loadSessions();
        if (!state.session) {
          await createSession();
        } else {
          await loadMessages();
        }
      })();
    };
  }

  registerPage("qwen-chat");
  registerPage("qwen_chat");
})();
