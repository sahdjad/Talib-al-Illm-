// Renders cover/front/body to PDF (two-pass for TOC page numbers) and merges them.
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const { chromium } = require('playwright-core');
const { PDFDocument } = require('pdf-lib');
const B = require('./build');

const CHROME = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
const OUT = B.OUT;
const FOOTER = `<div style="width:100%;text-align:center;font-family:serif;font-size:9pt;color:#6b7a70;padding-top:2mm"><span class="pageNumber"></span></div>`;

async function pdf(browser, htmlFile, pdfFile, { footer }) {
  const page = await browser.newPage();
  await page.goto('file://' + htmlFile, { waitUntil: 'load' });
  await page.evaluate(() => document.fonts.ready);
  await page.pdf({
    path: pdfFile, preferCSSPageSize: true, printBackground: true,
    displayHeaderFooter: !!footer, headerTemplate: '<div></div>', footerTemplate: footer ? FOOTER : '<div></div>',
  });
  await page.close();
}

async function renderBody(browser, pageMap) {
  const { bodyHtml, tocHtml, toc } = B.build(pageMap);
  fs.writeFileSync(path.join(OUT, 'body.html'), bodyHtml);
  fs.writeFileSync(path.join(OUT, 'front.html'), B.frontHtml(tocHtml));
  fs.writeFileSync(path.join(OUT, 'cover.html'), B.COVER);
  fs.writeFileSync(path.join(OUT, 'toc.json'), JSON.stringify(toc, null, 1));
  await pdf(browser, path.join(OUT, 'body.html'), path.join(OUT, 'body.pdf'), { footer: true });
  await pdf(browser, path.join(OUT, 'front.html'), path.join(OUT, 'front.pdf'), { footer: false });
  return toc;
}

(async () => {
  const browser = await chromium.launch({ executablePath: CHROME });
  await pdf(browser, (fs.writeFileSync(path.join(OUT, 'cover.html'), B.COVER), path.join(OUT, 'cover.html')), path.join(OUT, 'cover.pdf'), { footer: false });
  let toc = await renderBody(browser, null);
  // find pages of headings
  const run = () => JSON.parse(execFileSync('python3', [path.join(__dirname, 'tocpages.py'), path.join(OUT, 'body.pdf'), path.join(OUT, 'toc.json')], { encoding: 'utf8', maxBuffer: 1 << 26 }));
  let map = run();
  toc = await renderBody(browser, map);
  const map2 = run();
  if (JSON.stringify(map) !== JSON.stringify(map2)) { console.log('TOC pages shifted; re-rendering'); toc = await renderBody(browser, map2); map = map2; }
  await browser.close();

  const out = await PDFDocument.create();
  for (const f of ['cover.pdf', 'front.pdf', 'body.pdf']) {
    const src = await PDFDocument.load(fs.readFileSync(path.join(OUT, f)));
    const pages = await out.copyPages(src, src.getPageIndices());
    pages.forEach((p) => out.addPage(p));
    console.log(f, src.getPageCount(), 'pages');
  }
  out.setTitle('Šarḥ al-Fatwā al-Ḥamawiyyah');
  out.setAuthor('Šayḫ al-Islām Ibn Taymiyyah – Erklärung: Abū Muḥammad as-Sanzakī');
  const final = path.join(OUT, 'Sharh-al-Fatwa-al-Hamawiyyah.pdf');
  fs.writeFileSync(final, await out.save());
  console.log('Wrote', final, out.getPageCount(), 'pages');
})().catch((e) => { console.error(e); process.exit(1); });
