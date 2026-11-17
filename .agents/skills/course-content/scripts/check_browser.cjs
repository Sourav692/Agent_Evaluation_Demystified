const fs = require('fs'), path = require('path'), assert = require('assert');
const {pathToFileURL} = require('url');
const {runtime} = require('./browser_runtime.cjs');
(async () => {
  const input = process.argv[2];
  if (!input) throw new Error('Usage: node check_browser.cjs lesson.html [--out checks/browser.json]');
  const outIndex = process.argv.indexOf('--out');
  const output = path.resolve(outIndex < 0 ? 'checks/browser.json' : process.argv[outIndex + 1]);
  const shots = path.join(path.dirname(output), path.basename(output, '.json') + '-shots');
  fs.mkdirSync(shots, {recursive:true});
  const {puppeteer, chrome} = runtime();
  const browser = await puppeteer.launch({executablePath:chrome, headless:true, args:['--no-sandbox']});
  try {
    const page = await browser.newPage(), errors = [], requests = [], snapshots = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.setRequestInterception(true);
    page.on('request', r => {if (/^https?:/.test(r.url())) {requests.push(r.url());r.abort();} else r.continue();});
    const url = pathToFileURL(path.resolve(input)).href;
    await page.goto(url); await page.evaluate(() => document.fonts.ready);
    const widgetSelector = '[data-stepper],.walkthrough,[data-comparison],.evidence-switcher';
    for (const width of [320,390,1254,1920]) for (const theme of ['light','dark']) {
      await page.setViewport({width,height:900});
      await page.evaluate(t => {document.documentElement.dataset.theme=t;scrollTo(0,0);}, theme);
      const widgets = await page.$$(widgetSelector);
      let stages = 0, modes = 0;
      for (let wi = 0; wi < widgets.length; wi++) {
        const widget = widgets[wi];
        const stepper = await widget.evaluate(e => e.hasAttribute('data-stepper') || e.classList.contains('walkthrough'));
        const selector = stepper ? '[data-step]' : '[data-mode]';
        const buttons = await widget.$$(selector);
        const targets = await widget.$$eval(selector, bs => bs.map(b => b.getAttribute('aria-controls')));
        for (let i=0;i<buttons.length;i++) {
          await buttons[i].evaluate(e=>e.click());
          const selected = await widget.$$eval(selector, bs => bs.map(b => b.getAttribute('aria-pressed')==='true'));
          assert.equal(selected.filter(Boolean).length,1,'One selection per component'); assert(selected[i]);
          for (let j=0;j<targets.length;j++) assert.equal(await page.$eval('#'+targets[j], e=>e.hidden), j!==i);
          if (stepper) {
            stages++;
            assert.equal(await widget.$eval('[data-walk="previous"]',e=>e.disabled),i===0);
            assert.equal(await widget.$eval('[data-walk="next"]',e=>e.disabled),i===buttons.length-1);
          } else modes++;
          await buttons[i].focus(); await page.keyboard.press('Enter');
          assert.equal(await buttons[i].evaluate(e=>e.getAttribute('aria-pressed')),'true');
          if (width===390 || width===1254) {
            await page.$eval('.topbar',e=>e.style.visibility='hidden');
            await widget.screenshot({path:path.join(shots,`${width}-${theme}-widget${wi+1}-panel${i+1}.png`)});
            await page.$eval('.topbar',e=>e.style.visibility='');
          }
        }
        await buttons[0].evaluate(e=>e.click());
        if (stepper && buttons.length>1) {
          await widget.$eval('[data-walk="next"]',e=>e.click());
          assert.equal(await buttons[1].evaluate(e=>e.getAttribute('aria-pressed')),'true');
          await widget.$eval('[data-walk="previous"]',e=>e.click());
          assert.equal(await buttons[0].evaluate(e=>e.getAttribute('aria-pressed')),'true');
        }
      }
      const snapshot=await page.evaluate(()=>({width:innerWidth,theme:document.documentElement.dataset.theme,
        scrollWidth:document.documentElement.scrollWidth,figures:document.querySelectorAll('.prose figure').length,
        images:[...document.images].filter(i=>i.getBoundingClientRect().height>0).map(i=>i.complete&&i.naturalWidth>0),
        brokenAnchors:[...document.querySelectorAll('a[href^="#"]')].filter(a=>!document.getElementById(a.hash.slice(1))).map(a=>a.hash)}));
      assert(snapshot.scrollWidth<=width,'Page overflow');assert(snapshot.images.every(Boolean),'Broken image');assert.equal(snapshot.brokenAnchors.length,0);
      snapshots.push({...snapshot,stagesChecked:stages,modesChecked:modes});
      if (width===390 || width===1254) {
        await page.evaluate(()=>scrollTo(0,0));await page.screenshot({path:path.join(shots,`${width}-${theme}-top.png`)});
        await page.$eval('.topbar',e=>e.style.visibility='hidden');
        for (const [i,figure] of (await page.$$('.prose figure')).entries()) await figure.screenshot({path:path.join(shots,`${width}-${theme}-figure${i+1}.png`)});
        await page.$eval('.topbar',e=>e.style.visibility='');
      }
    }
    await page.evaluate(()=>document.documentElement.dataset.theme='light');
    await page.$eval('.theme',e=>e.click());assert.equal(await page.$eval('html',e=>e.dataset.theme),'dark');
    await page.$eval('.theme',e=>e.click());assert.equal(await page.$eval('html',e=>e.dataset.theme),'light');
    for (const detail of await page.$$('.prose details')) {await detail.$eval('summary',e=>e.click());assert(await detail.evaluate(e=>e.open));}
    const nojs=await browser.newPage();await nojs.setJavaScriptEnabled(false);await nojs.goto(url);
    const panels=await nojs.$$eval('.step-panel,.mode-panel',ps=>ps.map(p=>p.getBoundingClientRect().height>0));assert(panels.every(Boolean),'No-script explanation missing');
    const controls=await nojs.$$eval('.step-controls,.step-footer,.mode-controls',cs=>cs.map(c=>getComputedStyle(c).display==='none'));assert(controls.every(Boolean),'No-script inactive controls visible');
    assert.equal(errors.length,0);assert.equal(requests.length,0,'Remote runtime asset requests');
    fs.writeFileSync(output,JSON.stringify({passed:true,input:path.resolve(input),snapshots,errors,remoteRequests:requests,noScriptPanels:panels.length,noScriptControlsHidden:true,theme:true,keyboard:true},null,2));
    console.log('PASS: responsive, offline, keyboard, all component states and no-script checks');
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exit(1);});
