const { chromium } = require('playwright');
(async() => {
  const browser = await chromium.launch({headless:true});
  const page = await browser.newPage({ viewport: { width: 1440, height: 1400 } });
  if (process.env.ERP_UI_SMOKE_SID) {
    await page.context().addCookies([{
      name: 'sid',
      value: process.env.ERP_UI_SMOKE_SID,
      domain: 'meet.erpbosai.com',
      path: '/',
      httpOnly: true,
      secure: true,
      sameSite: 'Lax',
    }]);
  }
  await page.goto('https://meet.erpbosai.com/desk/quotation/SAL-QTN-2026-00008', {waitUntil:'networkidle'});
  await page.waitForTimeout(3500);
  const data = await page.evaluate(() => {
    const summarize = (fieldname) => {
      const node = document.querySelector(`.frappe-control[data-fieldname="${fieldname}"]`)
        || document.querySelector(`.grid-field[data-fieldname="${fieldname}"]`);
      if (!node) return null;
      const section = node.closest('.form-section');
      return {
        fieldname,
        sectionClass: section?.className || null,
        sectionText: section?.querySelector('.section-head')?.textContent?.trim() || null,
        sectionRect: section ? section.getBoundingClientRect().toJSON() : null,
      };
    };
    return {
      items: summarize('items'),
      taxes: summarize('taxes'),
      tax_category: summarize('tax_category'),
      payment_schedule: summarize('payment_schedule')
    };
  });
  console.log(JSON.stringify(data, null, 2));
  await browser.close();
})();
