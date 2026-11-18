// Render the cover PNGs of an edition from tools/cover.html and
// <edition>/covers.json.
// Usage: node tools/render_covers.js editions/erstausgaben
const fs = require('fs');
const path = require('path');
const {chromium} = require('playwright');

const edition = path.resolve(process.argv[2] || 'editions/erstausgaben');
const fonts = path.join(
  path.dirname(require.resolve('@fontsource/crimson-pro/package.json')),
  'files');
const template = fs.readFileSync(path.join(__dirname, 'cover.html'), 'utf8');
const covers = JSON.parse(
  fs.readFileSync(path.join(edition, 'covers.json'), 'utf8'));

(async () => {
  const browser = await chromium.launch();
  for (const [file, c] of Object.entries(covers)) {
    const ed = c.editor
      ? `<div class="ed"><i>Herausgegeben von</i> ${c.editor}</div>`
      : '';
    const html = template
      .replaceAll('{{FONTS}}', 'file://' + fonts)
      .replace('{{VOL}}', c.vol)
      .replace('{{BOOK}}', c.book)
      .replace('{{YEAR}}', c.year)
      .replace('{{SRC}}', c.src)
      .replace('{{ED}}', ed);
    const tmp = path.join(edition, 'covers', '.cover.html');
    fs.writeFileSync(tmp, html);
    const page = await browser.newPage({viewport: {width: 1264, height: 1680}});
    await page.goto('file://' + tmp);
    await page.evaluate(() => document.fonts.ready);
    await page.screenshot({path: path.join(edition, 'covers', file)});
    await page.close();
    fs.unlinkSync(tmp);
    console.log(file);
  }
  await browser.close();
})();
