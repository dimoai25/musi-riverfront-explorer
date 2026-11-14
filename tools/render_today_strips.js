const { chromium } = require('playwright');
(async () => {
  const [inp, outdir] = process.argv.slice(2);
  const W = 13925, SH = 2100, PT = 2.5;
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: W, height: SH } });
  await p.goto('file://' + inp);
  await p.waitForTimeout(500);
  for (let i = 0; i < 5; i++) {
    await p.evaluate(([i, SH, PT, W]) => {
      const s = document.querySelector('svg');
      s.setAttribute('viewBox', `0 ${i * SH / PT} ${W / PT} ${SH / PT}`);
      s.setAttribute('width', W); s.setAttribute('height', SH);
      s.querySelector('rect').setAttribute('height', 99999);
    }, [i, SH, PT, W]);
    await p.waitForTimeout(300);
    await p.screenshot({ path: `${outdir}/today_${i}.png`, clip: { x: 0, y: 0, width: W, height: SH } });
    console.log('strip', i);
  }
  await b.close();
})();
