const fs = require('node:fs/promises');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const { chromium } = require('playwright');
const sharp = require('sharp');

async function main() {
  const [input, output, executablePath] = process.argv.slice(2);
  if (!input || !output) throw new Error('请提供案例目录和新的成品目录');
  const root = path.resolve(input);
  const destination = path.resolve(output);
  await fs.access(path.join(root, 'index.html'));
  await fs.mkdir(destination, { recursive: false });
  const browser = await chromium.launch({ headless: true, ...(executablePath ? { executablePath } : {}) });
  try {
    const page = await browser.newPage({ viewport: { width: 1200, height: 1600 }, deviceScaleFactor: 1 });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(pathToFileURL(path.join(root, 'index.html')).href);
    await page.evaluate(() => document.body.classList.add('export-mode'));
    const report = [];
    for (const edition of ['xhs', 'member']) {
      await page.evaluate(value => window.setEdition(value), edition);
      await page.evaluate(async () => {
        await document.fonts.ready;
        await Promise.all(Array.from(document.images).map(image => image.decode()));
      });
      const elements = page.locator(edition === 'xhs' ? '#xhs-edition .page' : '#member-article');
      const count = await elements.count();
      if (!count || (edition === 'member' && count !== 1)) throw new Error(`导出容器数量不正确：${edition}`);
      const folder = path.join(destination, edition);
      await fs.mkdir(folder);
      for (let index = 0; index < count; index++) {
        const element = elements.nth(index);
        const bounds = await element.boundingBox();
        if (!bounds || Math.abs(bounds.width - 1080) > 1) throw new Error(`容器宽度需要检查：${edition} ${index + 1}`);
        if (edition === 'xhs' && Math.abs(bounds.height - 1440) > 1) throw new Error('小红书页面高度需要为 1440px');
        const overflow = await element.evaluate(node => node.scrollHeight > node.clientHeight + 2 || node.scrollWidth > node.clientWidth + 2);
        if (overflow) throw new Error(`内容超出容器：${edition} ${index + 1}`);
        if (!(await element.locator('img').count())) throw new Error(`导出容器缺少图片：${edition} ${index + 1}`);
        const buffer = await element.screenshot({ animations: 'disabled' });
        const metadata = await sharp(buffer).metadata();
        await sharp(buffer).raw().toBuffer();
        if (metadata.width !== 1080 || (edition === 'xhs' && metadata.height !== 1440)) throw new Error('导出图片尺寸需要检查');
        if (Math.abs(metadata.height - bounds.height) > 1) throw new Error('导出图片高度与文章容器不一致');
        const name = edition === 'xhs' ? `${String(index + 1).padStart(2, '0')}.png` : 'full.png';
        await fs.writeFile(path.join(folder, name), buffer);
        report.push({ edition, page: index + 1, file: `${edition}/${name}`, width: metadata.width, height: metadata.height });
      }
    }
    if (errors.length) throw new Error(errors.join('\n'));
    await fs.writeFile(path.join(destination, 'export-report.json'), JSON.stringify(report, null, 2));
    process.stdout.write(JSON.stringify(report, null, 2));
  } finally {
    await browser.close();
  }
}

main().catch(error => { process.stderr.write(`${error.stack}\n`); process.exitCode = 1; });
