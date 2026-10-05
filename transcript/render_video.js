// Deterministic frame render of transcript.html to video (needs node + playwright, ffmpeg).
//   node render.js T0 T1 out.mp4      (seconds; writes video only, no audio)
// The page runs on a virtual clock: performance.now and requestAnimationFrame
// are replaced, and the piece time is set directly through a hook added to a
// served copy of the page. Each frame advances exactly 1/FPS, so text and
// audio line up when the segments are joined and the mp3 is muxed in.
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), { spawn } = require('child_process');
const [T0, T1, OUT] = [parseFloat(process.argv[2]), parseFloat(process.argv[3]), process.argv[4]];
const FPS = 25, W = 1920, H = 1080, WARM = 6;

let html = fs.readFileSync(require('path').join(__dirname, '..', 'transcript.html'), 'utf8');
const hook = 'let virtualT = 0;';
if (!html.includes(hook)) throw new Error('hook point missing');
html = html.replace(hook, hook + ' window.__setT = t => { virtualT = t; };')
           .replace(/AUDIO: '[^']*'/, 'AUDIO: null');

(async () => {
  const srv = http.createServer((q, r) => { r.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' }); r.end(html); });
  await new Promise(r => srv.listen(0, r));
  const b = await chromium.launch({ executablePath: process.env.CHROME || undefined });
  const pg = await b.newPage({ viewport: { width: W, height: H } });
  await pg.addInitScript(() => {
    window.__now = 0;
    performance.now = () => window.__now;
    window.requestAnimationFrame = cb => { window.__raf = cb; return 1; };
    window.setInterval = () => 0;             // the rAF-stall fallback is irrelevant on a virtual clock
  });
  await pg.goto(`http://127.0.0.1:${srv.address().port}/?mode=scroll`, { waitUntil: 'load' });   // the video is of the scrolling view
  await pg.evaluate(() => document.fonts.ready);
  await pg.evaluate(() => {
    document.getElementById('gate').classList.add('off');
    document.body.style.cursor = 'none';
  });
  const enc = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', '-r', String(FPS), OUT],
    { stdio: ['pipe', 'inherit', 'inherit'] });
  const first = Math.round(T0 * FPS), last = Math.round(T1 * FPS), warm = Math.max(0, first - WARM * FPS);
  const t0 = Date.now();
  for (let f = warm; f < last; f++) {
    const t = f / FPS;
    await pg.evaluate(t => { window.__now = t * 1000; window.__setT(t); const cb = window.__raf; window.__raf = null; if (cb) cb(t * 1000); }, t);
    if (f < first) continue;
    const buf = await pg.screenshot({ type: 'jpeg', quality: 92 });
    if (!enc.stdin.write(buf)) await new Promise(r => enc.stdin.once('drain', r));
    if ((f - first) % (FPS * 60) === 0) console.log(`${OUT}: ${(t / 60).toFixed(1)} min, ${((f - first + 1) / ((Date.now() - t0) / 1000)).toFixed(1)} fps`);
  }
  enc.stdin.end();
  await new Promise(r => enc.on('close', r));
  await b.close(); srv.close();
  console.log(`${OUT}: done, ${last - first} frames in ${((Date.now() - t0) / 60000).toFixed(1)} min`);
})();
