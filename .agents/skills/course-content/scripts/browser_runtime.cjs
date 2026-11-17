const fs = require('fs');
const path = require('path');
const os = require('os');
function runtime() {
  const candidates = [process.env.PUPPETEER_MODULE,
    process.env.CONTENT_WRITE_CACHE && path.join(process.env.CONTENT_WRITE_CACHE, 'node_modules/puppeteer-core'),
    path.join(os.homedir(), '.cache/content-write/node_modules/puppeteer-core'), 'puppeteer-core'].filter(Boolean);
  let puppeteer;
  for (const candidate of candidates) { try { puppeteer = require(candidate); break; } catch {} }
  if (!puppeteer) throw new Error('Install the renderer dependencies first, or set PUPPETEER_MODULE to puppeteer-core.');
  const chrome = [process.env.CHROME_PATH, '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser',
    process.env.PROGRAMFILES && path.join(process.env.PROGRAMFILES, 'Google/Chrome/Application/chrome.exe')].find(p => p && fs.existsSync(p));
  if (!chrome) throw new Error('Set CHROME_PATH to an installed Chrome or Chromium executable.');
  return {puppeteer, chrome};
}
module.exports = {runtime};
