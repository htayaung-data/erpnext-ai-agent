const { expect } = require("@playwright/test");

const DIAGNOSTIC_TIMEOUT = Number(process.env.ERPW_DIAGNOSTIC_TIMEOUT || 30_000);

function requireEnv(name) {
  const value = process.env[name];
  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}

function escapeRegex(value) {
  return String(value).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function buildDocRoute({ routeEnv, nameEnv, slug }) {
  const routeOverride = process.env[routeEnv];
  if (routeOverride) return routeOverride;

  const name = requireEnv(nameEnv);
  return `/app/${slug}/${encodeURIComponent(name)}`;
}

async function ensureSessionCookie(page) {
  const sid = process.env.ERPW_SESSION_SID;
  if (!sid) {
    return false;
  }

  const baseUrl = process.env.ERPW_BASE_URL || "http://127.0.0.1:8000";
  await page.context().addCookies([
    {
      name: "sid",
      value: sid,
      url: baseUrl,
      httpOnly: true,
      sameSite: "Lax",
    },
  ]);

  return true;
}

async function ensureAuthenticated(page) {
  const hasSessionCookie = await ensureSessionCookie(page);

  await page.goto("/app", { waitUntil: "domcontentloaded" });
  if (!/\/login(?:[/?#]|$)/.test(page.url())) {
    return;
  }

  if (hasSessionCookie) {
    throw new Error("Session cookie authentication did not grant access to Desk");
  }

  const username = requireEnv("ERPW_USERNAME");
  const password = requireEnv("ERPW_PASSWORD");

  const userField = page
    .locator("#login_email, input[name='usr'], input[name='login_email'], input[type='email'], input[type='text']")
    .first();
  const passwordField = page
    .locator("#login_password, input[name='pwd'], input[name='login_password'], input[type='password']")
    .first();
  const loginButton = page
    .locator("button:has-text('Login'), button.btn-login, .btn-login")
    .first();

  await userField.waitFor({ state: "visible", timeout: DIAGNOSTIC_TIMEOUT });
  await userField.fill(username);
  await passwordField.fill(password);

  await Promise.all([
    page.waitForURL(/\/(?:app|desk)(?:[/?#]|$)/, { timeout: DIAGNOSTIC_TIMEOUT }),
    loginButton.click(),
  ]);
}

async function openRuntimePage(page, route) {
  await ensureAuthenticated(page);
  await page.goto(route, { waitUntil: "domcontentloaded" });

  if (/\/login(?:[/?#]|$)/.test(page.url())) {
    await ensureAuthenticated(page);
    await page.goto(route, { waitUntil: "domcontentloaded" });
  }

  await expect
    .poll(async () => page.url(), {
      timeout: DIAGNOSTIC_TIMEOUT,
      message: `Expected page to resolve into an app route for ${route}`,
    })
    .toMatch(/\/(?:app|desk)\//);
}

async function waitForDiagnosticAttr(page, attrName, allowedStatuses) {
  const statusPattern = new RegExp(`^(?:${allowedStatuses.map(escapeRegex).join("|")})$`);

  await expect
    .poll(
      async () =>
        page.evaluate((attr) => {
          const element = document.querySelector(`[${attr}]`);
          return element ? element.getAttribute(attr) || "" : "";
        }, attrName),
      {
        timeout: DIAGNOSTIC_TIMEOUT,
        message: `Expected ${attrName} to settle to one of: ${allowedStatuses.join(", ")}`,
      }
    )
    .toMatch(statusPattern);
}

async function waitForFeatureReady(page, featureKey) {
  await expect
    .poll(
      async () =>
        page.evaluate((feature) => {
          const entry =
            window.cur_frm && window.cur_frm.__erpwDiagnostics
              ? window.cur_frm.__erpwDiagnostics.features[feature]
              : null;
          return Boolean(entry && entry.readyCount > 0);
        }, featureKey),
      {
        timeout: DIAGNOSTIC_TIMEOUT,
        message: `Expected ${featureKey} to report at least one ready state`,
      }
    )
    .toBe(true);
}

async function waitForFeatureAttempt(page, featureKey) {
  await expect
    .poll(
      async () =>
        page.evaluate((feature) => {
          const entry =
            window.cur_frm && window.cur_frm.__erpwDiagnostics
              ? window.cur_frm.__erpwDiagnostics.features[feature]
              : null;
          return Boolean(entry && entry.attempts > 0);
        }, featureKey),
      {
        timeout: DIAGNOSTIC_TIMEOUT,
        message: `Expected ${featureKey} to record at least one diagnostic attempt`,
      }
    )
    .toBe(true);
}

module.exports = {
  DIAGNOSTIC_TIMEOUT,
  buildDocRoute,
  openRuntimePage,
  waitForDiagnosticAttr,
  waitForFeatureReady,
  waitForFeatureAttempt,
};
