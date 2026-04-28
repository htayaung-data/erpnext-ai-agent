const fs = require("fs");
const path = require("path");

const CAPTURE_ENABLED = process.env.ERPW_CAPTURE_REFERENCE === "1";
const CAPTURE_ROOT = path.resolve(
  process.env.ERPW_CAPTURE_ROOT || path.join(__dirname, "..", "..", "artifacts", "reference_screenshots")
);
const CAPTURE_SETTLE_MS = Number(process.env.ERPW_CAPTURE_SETTLE_MS || 900);
const CAPTURE_LOCATOR_TIMEOUT = Number(process.env.ERPW_CAPTURE_LOCATOR_TIMEOUT || 15_000);

const VIEWPORTS = [
  { key: "desktop_wide", width: 1600, height: 2200 },
  { key: "laptop", width: 1366, height: 2000 },
];

function ensureCaptureDir(pageKey, viewportKey) {
  const dir = path.join(CAPTURE_ROOT, pageKey, viewportKey);
  fs.mkdirSync(dir, { recursive: true });
  return dir;
}

function resetCaptureDir(pageKey, viewportKey) {
  const dir = ensureCaptureDir(pageKey, viewportKey);
  for (const entry of fs.readdirSync(dir)) {
    fs.rmSync(path.join(dir, entry), { recursive: true, force: true });
  }
  return dir;
}

function capturePath(pageKey, viewportKey, label) {
  return path.join(ensureCaptureDir(pageKey, viewportKey), `${label}.png`);
}

function jsonPath(pageKey, viewportKey, label) {
  return path.join(ensureCaptureDir(pageKey, viewportKey), `${label}.json`);
}

function normalizeCaptureLabel(value) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace(/&/g, " and ")
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "")
    || "unnamed";
}

function writeCaptureJson(pageKey, viewportKey, label, value) {
  fs.writeFileSync(jsonPath(pageKey, viewportKey, label), `${JSON.stringify(value, null, 2)}\n`, "utf8");
}

async function applyViewport(page, viewport) {
  await page.setViewportSize({ width: viewport.width, height: viewport.height });
}

async function waitForUiSettle(page, delayMs = CAPTURE_SETTLE_MS) {
  try {
    await page.waitForLoadState("networkidle", { timeout: 5_000 });
  } catch (error) {
    // ERP Desk can keep network activity alive; a short delay is still enough for stable capture.
  }
  await page.waitForTimeout(delayMs);
}

async function captureFullPage(page, pageKey, viewportKey, label) {
  await waitForUiSettle(page);
  await page.screenshot({
    path: capturePath(pageKey, viewportKey, label),
    fullPage: true,
    animations: "disabled",
  });
}

async function captureLocator(locator, pageKey, viewportKey, label) {
  const count = await locator.count();
  if (!count) return false;

  const target = locator.first();
  await target.waitFor({ state: "visible", timeout: CAPTURE_LOCATOR_TIMEOUT });
  await target.scrollIntoViewIfNeeded();
  await target.screenshot({
    path: capturePath(pageKey, viewportKey, label),
    animations: "disabled",
  });
  return true;
}

async function clickTabByName(page, tabName) {
  const tab = page.getByRole("tab", { name: tabName, exact: true }).first();
  if ((await tab.count()) === 0) return false;
  try {
    await tab.click({ timeout: CAPTURE_LOCATOR_TIMEOUT });
  } catch (error) {
    try {
      await tab.click({ force: true, timeout: CAPTURE_LOCATOR_TIMEOUT });
    } catch (forceError) {
      await tab.evaluate((element) => element.click());
    }
  }
  await waitForUiSettle(page);
  return true;
}

async function listVisibleTabs(page) {
  const tablist = page.locator('[role="tablist"]:visible').first();
  if ((await tablist.count()) === 0) return [];

  const tabs = tablist.locator('[role="tab"]:visible');
  const count = await tabs.count();
  const items = [];
  const seen = new Set();

  for (let index = 0; index < count; index += 1) {
    const tab = tabs.nth(index);
    const name = (await tab.innerText()).trim().replace(/\s+/g, " ");
    if (!name) continue;

    const key = name.toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);

    items.push({
      index,
      name,
      normalized: normalizeCaptureLabel(name),
      selected: (await tab.getAttribute("aria-selected")) === "true",
    });
  }

  return items;
}

module.exports = {
  CAPTURE_ENABLED,
  CAPTURE_ROOT,
  VIEWPORTS,
  applyViewport,
  captureFullPage,
  captureLocator,
  clickTabByName,
  listVisibleTabs,
  normalizeCaptureLabel,
  resetCaptureDir,
  waitForUiSettle,
  writeCaptureJson,
};
