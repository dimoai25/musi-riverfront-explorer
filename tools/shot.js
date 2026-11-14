// node shot.js in.html out.png width [height]
const { chromium } = require('playwright');
(async () => {
  const [inp, out, w, h] = process.argv.slice(2);
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: +w, height: +(h || 800) } });
  await p.goto('file://' + inp);
  await p.waitForTimeout(500);
  await p.screenshot({ path: out, fullPage: !h });
  await b.close();
})();
