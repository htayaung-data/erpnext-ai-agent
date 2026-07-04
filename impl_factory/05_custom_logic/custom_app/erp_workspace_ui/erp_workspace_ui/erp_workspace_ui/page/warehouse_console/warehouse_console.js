/* global frappe */

(function () {
  const PAGE_KEY = "warehouse-console";
  const ASSET = "/assets/erp_workspace_ui/js/warehouse_console/warehouse_console_page.js";
  let renderSerial = 0;
  let assetLoadPromise = null;

  function currentWrapper(fallback) {
    return fallback || (frappe.container && frappe.container.page && frappe.container.page.wrapper) || document.getElementById("body");
  }

  function renderRouteLoadingShell(wrapper) {
    const target = currentWrapper(wrapper);
    if (!target || !target.querySelector) return;
    if (target === document.body || target.id === "body") return;
    if (target.querySelector('.sales-console-shell[data-erpw-workspace="warehouse"][data-warehouse-cockpit="ready"]')) return;
    if (target.querySelector('[data-warehouse-route-loading="overview"]')) return;
    target.innerHTML = `
      <div class="erpw-direct-warehouse-page" data-erpw-page-key="warehouse-console" aria-busy="true">
        <main class="layout-main-section erpw-direct-warehouse-body">
          <section data-warehouse-route-loading="overview" aria-label="Loading Warehouse Console" style="box-sizing:border-box;max-width:1120px;margin:0 auto;padding:8px 20px 18px;">
            <div style="border-radius:20px;background:linear-gradient(135deg,#12213a 0%,#133d47 74%,#07111f 100%);box-shadow:0 22px 54px rgba(15,23,42,.12);padding:25px 25px 22px;color:#fff;">
              <div style="font-size:29px;font-weight:760;letter-spacing:-.035em;line-height:1.1;margin-bottom:13px;">Warehouse Console</div>
              <div style="max-width:760px;font-size:13px;line-height:1.55;color:rgba(255,255,255,.86);">Custom Warehouse workflow workspace for receiving, picking, returns, internal transfer, cycle count, stock exceptions, posted movement visibility, and transfer visibility.</div>
              <div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1px;margin-top:28px;border:1px solid rgba(255,255,255,.16);border-radius:16px;overflow:hidden;background:rgba(255,255,255,.12);">
                <div style="min-height:84px;padding:15px 18px;background:rgba(255,255,255,.06);">
                  <div style="height:10px;width:120px;border-radius:999px;background:rgba(186,205,226,.42);margin-bottom:14px;"></div>
                  <div style="height:31px;width:36px;border-radius:10px;background:rgba(255,255,255,.82);opacity:.9;"></div>
                  <div style="height:10px;width:170px;border-radius:999px;background:rgba(255,255,255,.22);margin-top:12px;"></div>
                </div>
                <div style="min-height:84px;padding:15px 18px;background:rgba(255,255,255,.06);">
                  <div style="height:10px;width:118px;border-radius:999px;background:rgba(186,205,226,.42);margin-bottom:14px;"></div>
                  <div style="height:31px;width:32px;border-radius:10px;background:rgba(255,255,255,.82);opacity:.9;"></div>
                  <div style="height:10px;width:160px;border-radius:999px;background:rgba(255,255,255,.22);margin-top:12px;"></div>
                </div>
                <div style="min-height:84px;padding:15px 18px;background:rgba(255,255,255,.06);">
                  <div style="height:10px;width:112px;border-radius:999px;background:rgba(186,205,226,.42);margin-bottom:14px;"></div>
                  <div style="height:31px;width:30px;border-radius:10px;background:rgba(255,255,255,.82);opacity:.9;"></div>
                  <div style="height:10px;width:154px;border-radius:999px;background:rgba(255,255,255,.22);margin-top:12px;"></div>
                </div>
              </div>
            </div>
          </section>
        </main>
      </div>
    `;
  }

  function resolveRenderer() {
    const api = window.erpWorkspaceWarehouseConsole || {};
    if (typeof api.renderOverview === "function") return api.renderOverview;
    const pageDef = frappe.pages && frappe.pages[PAGE_KEY] ? frappe.pages[PAGE_KEY] : null;
    if (pageDef && pageDef.__erpwWarehouseConsoleRenderer && typeof pageDef.on_page_show === "function" && pageDef.on_page_show !== ensureAndRender) {
      return pageDef.on_page_show;
    }
    return null;
  }

  function invokeRenderer(wrapper) {
    const renderer = resolveRenderer();
    if (typeof renderer !== "function") return false;
    renderer(currentWrapper(wrapper));
    return true;
  }

  function hasAssetScript() {
    return Array.from(document.querySelectorAll("script[src]")).some((script) => String(script.getAttribute("src") || "").indexOf(ASSET) !== -1);
  }

  function loadWarehouseAsset() {
    if (resolveRenderer()) return Promise.resolve();
    const globalPromise = window.__erpwWarehouseConsoleAssetPromise;
    if (globalPromise && typeof globalPromise.then === "function") return globalPromise;
    if (assetLoadPromise) return assetLoadPromise;
    assetLoadPromise = new Promise((resolve) => {
      let settled = false;
      const finish = () => {
        if (settled) return;
        settled = true;
        resolve();
      };
      try {
        frappe.require([ASSET], finish);
      } catch (error) {
        // Direct script fallback below handles loader differences across desk boot states.
      }
      window.setTimeout(() => {
        if (resolveRenderer()) {
          finish();
          return;
        }
        if (hasAssetScript() || window.__erpwWarehouseConsoleAssetRequested) {
          finish();
          return;
        }
        window.__erpwWarehouseConsoleAssetRequested = true;
        const script = document.createElement("script");
        script.src = ASSET;
        script.async = false;
        script.onload = finish;
        script.onerror = finish;
        document.head.appendChild(script);
      }, 250);
      window.setTimeout(finish, 3000);
    }).then(() => {
      assetLoadPromise = null;
      window.__erpwWarehouseConsoleAssetPromise = null;
    });
    window.__erpwWarehouseConsoleAssetPromise = assetLoadPromise;
    return assetLoadPromise;
  }

  function ensureAndRender(wrapper) {
    const token = ++renderSerial;
    const wrapperEl = currentWrapper(wrapper);
    renderRouteLoadingShell(wrapperEl);
    const attempt = () => {
      const readyShell = document.querySelector('.sales-console-shell[data-erpw-workspace="warehouse"][data-warehouse-cockpit="ready"]');
      if (readyShell) return true;
      if (token !== renderSerial) return true;
      return invokeRenderer(wrapperEl);
    };
    if (attempt()) return;
    loadWarehouseAsset().then(() => {
      attempt();
      if (window.requestAnimationFrame) window.requestAnimationFrame(attempt);
      window.setTimeout(attempt, 80);
      window.setTimeout(attempt, 220);
      window.setTimeout(attempt, 700);
      window.setTimeout(attempt, 1200);
    });
  }

  const pageDef = frappe.pages[PAGE_KEY] = frappe.pages[PAGE_KEY] || {};
  if (!pageDef.__erpwWarehouseConsoleRenderer) {
    pageDef.on_page_load = ensureAndRender;
    pageDef.on_page_show = ensureAndRender;
  }
})();
