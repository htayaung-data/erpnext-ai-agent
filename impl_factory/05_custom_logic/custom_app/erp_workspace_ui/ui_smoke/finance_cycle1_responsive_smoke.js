"use strict";

const assert = require("assert");
const fs = require("fs");
const path = require("path");
const { chromium } = require("@playwright/test");

const appRoot = path.resolve(process.env.ERPW_APP_ROOT || path.join(__dirname, ".."));
const financePath = path.join(appRoot, "erp_workspace_ui/erp_workspace_ui/page/finance_control_desk/finance_control_desk.js");
const source = fs.readFileSync(financePath, "utf8");
const styleMatch = source.match(/style\.textContent = `([\s\S]*?)`;\n\s*document\.head\.appendChild/);
assert(styleMatch, "Finance source CSS must be extractable for responsive smoke");

const card = (title, detail, value) => `
  <article class="finance-control-panel">
    <h2 class="finance-control-panel-title">${title}</h2>
    <p class="finance-control-panel-copy">${detail}</p>
    <div class="finance-control-chip-row"><span class="finance-control-chip">${value}</span></div>
  </article>`;

function shell(state) {
  const restricted = state === "restricted";
  const cards = restricted ? "" : [
    card("Workspace readiness", "Finance Control Desk is active for read-only overview posture.", "Read-only"),
    card("Company scope", "Company-scoped read-only aggregate posture.", "Mingalar Mobile Distribution Co., Ltd."),
    card("Fiscal period posture", "Fiscal period posture remains deferred.", "Deferred"),
    card("Receivables posture", "Sales Invoice aggregate count buckets and manager-only Payment Ledger MMK amount buckets remain separate signals. No row-level identity is shown.", "Aggregate counts + MMK buckets"),
    card("Payables posture", "Payables counts remain unavailable when payment schedules cannot be interpreted safely.", "Unavailable"),
    card("Ledger posture", "Account balances and ledger rows remain blocked.", "Blocked"),
  ].join("");
  return `<!doctype html><html><head><meta charset="utf-8"><style>${styleMatch[1]}</style></head><body>
    <main class="finance-control-shell" data-finance-cycle1-overview="${state}">
      <section class="finance-control-hero ${restricted ? "is-restricted" : ""}">
        <div class="finance-control-hero-top">
          <div><p class="finance-control-eyebrow">Finance &amp; Accounting</p><h1 class="finance-control-title">Finance Control Desk</h1>
          <p class="finance-control-summary">${restricted ? "Manager-only Finance posture is not shown for this role." : "Company-scoped aggregate posture only; no rows, reports, exports, or execution."}</p>
          <p class="finance-control-freshness">As of 2026-07-13 | Refreshed 2026-07-13 12:00:00</p></div>
          <div class="finance-control-actions"><span class="finance-control-status">${restricted ? "Restricted" : "Read-only overview"}</span><button class="finance-control-refresh">Refresh</button></div>
        </div>
        <div class="finance-control-chip-row"><span class="finance-control-chip">No row-level data shown</span><span class="finance-control-chip">Execution disabled</span></div>
      </section>
      <section class="finance-control-grid">${cards || card("Finance access restricted", "No row-level financial data, metrics, reports, exports, or execution routes are returned or shown.", "Restricted")}</section>
    </main>
  </body></html>`;
}

async function verify(page, viewport, state) {
  await page.setViewportSize(viewport);
  await page.setContent(shell(state), { waitUntil: "domcontentloaded" });
  const result = await page.evaluate(() => {
    const root = document.documentElement;
    const panels = Array.from(document.querySelectorAll(".finance-control-panel")).map((node) => node.getBoundingClientRect());
    const horizontalOverflow = root.scrollWidth - root.clientWidth;
    const outOfBounds = panels.some((box) => box.left < -0.5 || box.right > root.clientWidth + 0.5);
    const overlap = panels.some((box, index) => panels.slice(index + 1).some((other) => {
      const horizontal = box.left < other.right && box.right > other.left;
      const vertical = box.top < other.bottom && box.bottom > other.top;
      return horizontal && vertical;
    }));
    return { horizontalOverflow, outOfBounds, overlap, panelCount: panels.length };
  });
  assert(result.panelCount > 0);
  assert(result.horizontalOverflow <= 1, `${state} layout overflowed by ${result.horizontalOverflow}px at ${viewport.width}px`);
  assert.strictEqual(result.outOfBounds, false, `${state} panel escaped viewport at ${viewport.width}px`);
  assert.strictEqual(result.overlap, false, `${state} panels overlapped at ${viewport.width}px`);
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage();
    await verify(page, { width: 1366, height: 900 }, "ready");
    await verify(page, { width: 390, height: 844 }, "ready");
    await verify(page, { width: 390, height: 844 }, "restricted");
  } finally {
    await browser.close();
  }
  process.stdout.write("Finance Cycle 1 responsive smoke passed.\n");
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
