/* Capture the live dashboard's Overview tab for the weekly PDF, with headless Chromium (Playwright).
   Usage: node epps_capture_overview.js overview.png [url]
   Output: 3264 x 2170 PNG (1632 x 1085 viewport at 2x), parcel map fitted to the parcels, no scrollbars.
   Needs network access to epps-dashboard-ii.vercel.app, maps.segland.com, server.arcgisonline.com and unpkg.com. */
const { chromium } = require('playwright');
const out = process.argv[2] || 'overview.png';
const url = process.argv[3] || 'https://epps-dashboard-ii.vercel.app/';

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1632, height: 1085 }, deviceScaleFactor: 2 });
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  await page.goto(url, { waitUntil: 'networkidle', timeout: 90000 });

  // Wait for the GIS parcel layer, then fit the map to it.
  let parcels = 0;
  for (let t = 0; t < 30 && !parcels; t++) {
    parcels = await page.evaluate(() => { try { let c = 0; leafletParcelLayer.eachFeature(() => c++); return c; } catch (e) { return 0; } });
    if (!parcels) await page.waitForTimeout(1000);
  }
  if (!parcels) { console.error('Parcel layer did not load; is maps.segland.com reachable?'); process.exit(1); }

  await page.evaluate(() => {
    document.documentElement.style.overflow = 'hidden';
    let b = null;
    leafletParcelLayer.eachFeature(l => { const bb = l.getBounds(); b = b ? b.extend(bb) : L.latLngBounds(bb.getSouthWest(), bb.getNorthEast()); });
    leafletMap.invalidateSize();
    leafletMap.fitBounds(b, { padding: [4, 4] });
    const s = document.createElement('style');
    s.textContent = '*::-webkit-scrollbar{display:none!important;width:0!important;height:0!important}*{scrollbar-width:none!important}';
    document.head.appendChild(s);
    document.querySelectorAll('*').forEach(e => {
      if (e.scrollWidth > e.clientWidth + 1 && getComputedStyle(e).overflowX !== 'visible') e.style.overflowX = 'hidden';
    });
  });
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(5000); // imagery tiles

  const stamp = await page.evaluate(() => (document.body.innerText.match(/Last updated[^\n]*/) || [''])[0]);
  await page.screenshot({ path: out });
  await browser.close();
  console.log(`wrote ${out} · ${parcels} parcels · ${stamp}`);
  if (errors.length) console.log('page errors:', errors);
})();
