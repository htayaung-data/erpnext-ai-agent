const { chromium } = require('playwright');
(async() => {
  const browser = await chromium.launch({headless:true});
  const page = await browser.newPage({ viewport: { width: 1600, height: 1200 } });
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
  await page.goto('https://meet.erpbosai.com/desk/sales-order/SAL-ORD-2026-00021', {waitUntil:'networkidle'});
  await page.waitForTimeout(4000);
  const result = await page.evaluate(() => {
    const pick = (sel) => {
      const el = document.querySelector(sel);
      if (!el) return null;
      const r = el.getBoundingClientRect();
      return { sel, top: r.top, left: r.left, width: r.width, height: r.height, cls: el.className };
    };
    return {
      pageHead: pick('.page-head'),
      pageBody: pick('.page-body'),
      pageContent: pick('.page-content'),
      layoutMain: pick('.layout-main'),
      layoutMainSection: pick('.layout-main-section'),
      formSidebar: pick('.form-sidebar'),
      formSidebarParent: pick('.form-sidebar') ? (() => { const el=document.querySelector('.form-sidebar').parentElement; const r=el.getBoundingClientRect(); return {top:r.top,left:r.left,width:r.width,height:r.height,cls:el.className}; })() : null,
      childHost: pick('.erpw-child-page-host'),
      childShell: pick('.erpw-child-shell, .erpwq-quotation-shell, .erpws-order-shell, .erpwdn-delivery-shell'),
      tabs: pick('.form-tabs-list, .form-tabs'),
      stdFormLayout: pick('.std-form-layout')
    };
  });
  console.log(JSON.stringify(result, null, 2));
  await browser.close();
})();
