const fs=require('fs'),path=require('path'),assert=require('assert');
const {pathToFileURL}=require('url');
const {runtime}=require('./browser_runtime.cjs');
(async()=>{
  const [reference,candidate]=process.argv.slice(2,4);
  if(!reference||!candidate)throw new Error('Usage: node compare_pages.cjs approved.html rebuilt.html [--out checks/comparison.json]');
  const oi=process.argv.indexOf('--out'),out=path.resolve(oi<0?'checks/comparison.json':process.argv[oi+1]);
  const shots=path.join(path.dirname(out),path.basename(out,'.json')+'-shots');fs.mkdirSync(shots,{recursive:true});
  const {puppeteer,chrome}=runtime();const browser=await puppeteer.launch({executablePath:chrome,headless:true,args:['--no-sandbox']});
  try{
    const pages=await Promise.all([browser.newPage(),browser.newPage()]);
    for(let i=0;i<2;i++){await pages[i].bringToFront();await pages[i].goto(pathToFileURL(path.resolve([reference,candidate][i])).href);await pages[i].evaluate(()=>document.fonts.ready);}
    const cases=[];
    const strict=process.argv.includes('--strict-pixels');
    const pixelTolerance=strict?0:0.00025;
    const channelTolerance=strict?0:64;
    for(const width of [390,1254])for(const theme of ['light','dark']){
      console.log(`Comparing ${width}px ${theme}`);
      for(const p of pages){
        await p.bringToFront();await p.setViewport({width,height:900});await p.reload();
        await p.evaluate(async t=>{document.documentElement.dataset.theme=t;await document.fonts.ready;await Promise.all([...document.images].map(i=>i.decode().catch(()=>{})));scrollTo(0,0);await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));},theme);
      }
      const structure=await Promise.all(pages.map(p=>p.evaluate(()=>({text:document.querySelector('article').innerText,headings:[...document.querySelectorAll('article h1,article h2,article h3,article h4')].map(e=>e.textContent),figures:document.querySelectorAll('figure').length,steps:document.querySelectorAll('[data-step]').length,modes:document.querySelectorAll('[data-mode]').length,layout:[...document.querySelectorAll('article h1,article h2,article h3,article figure,.learning-widget')].map(e=>{const r=e.getBoundingClientRect();return [r.x,r.y,r.width,r.height].map(n=>Math.round(n*100)/100)})}))));
      assert.deepEqual(structure[0],structure[1],'Article text, components or layout differs');
      const buffers=[];
      for(let i=0;i<pages.length;i++){await pages[i].bringToFront();buffers.push(await pages[i].screenshot({path:path.join(shots,`${width}-${theme}-${i?'candidate':'reference'}.png`),fullPage:true}));}
      const diff=await pages[0].evaluate(async(data)=>{
        const images=await Promise.all(data.map(src=>new Promise((resolve,reject)=>{const im=new Image();im.onload=()=>resolve(im);im.onerror=reject;im.src='data:image/png;base64,'+src;})));
        if(images[0].width!==images[1].width||images[0].height!==images[1].height)return {dimensionsMatch:false,differentPixels:null};
        const pixels=images.map(im=>{const c=document.createElement('canvas');c.width=im.width;c.height=im.height;const context=c.getContext('2d');context.drawImage(im,0,0);return context.getImageData(0,0,c.width,c.height).data});
        let different=0,maxDelta=0;
        for(let i=0;i<pixels[0].length;i+=4){let changed=false;for(let j=0;j<4;j++){const d=Math.abs(pixels[0][i+j]-pixels[1][i+j]);if(d)changed=true;maxDelta=Math.max(maxDelta,d);}if(changed)different++;}
        return {dimensionsMatch:true,width:images[0].width,height:images[0].height,differentPixels:different,ratio:different/(images[0].width*images[0].height),maxChannelDelta:maxDelta};
      },buffers.map(b=>Buffer.from(b).toString('base64')));
      cases.push({width,theme,structureMatches:true,...diff});
    }
    const result={reference:path.resolve(reference),candidate:path.resolve(candidate),cases,
      exactPixelMatch:cases.every(c=>c.dimensionsMatch&&c.differentPixels===0),
      pixelTolerance,channelTolerance,
      passed:cases.every(c=>c.dimensionsMatch&&c.ratio<=pixelTolerance&&c.maxChannelDelta<=channelTolerance)};
    fs.writeFileSync(out,JSON.stringify(result,null,2));
    console.log(result.exactPixelMatch?'PASS: article structure and full-page pixels match in all four cases':
      result.passed?'PASS: article text/layout match; pixels stay within calibrated browser raster tolerance':'CHECK: pixel differences exceed tolerance');
    if(!result.passed)process.exitCode=1;
  }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
