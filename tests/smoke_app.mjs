/* Zero-dependency smoke test for app.js.

Drives the real script against a minimal fake DOM so the manifest load, feed
render, empty-date and archive-failure paths are exercised without a browser.
Built-ins only.   Run:  node tests/smoke_app.mjs
*/
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';

const ROOT = path.resolve(import.meta.dirname, '..');
const SRC = fs.readFileSync(path.join(ROOT, 'app.js'), 'utf8');
const HTML = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');
let pass = 0, fail = 0;
const ok = (name, cond, extra) => {
  if (cond) { pass++; console.log('  ok   ' + name); }
  else { fail++; console.log('  FAIL ' + name + (extra ? '  (' + extra + ')' : '')); }
};

function classList() {
  const s = new Set();
  return { add: c => s.add(c), remove: c => s.delete(c), contains: c => s.has(c),
    toggle: (c, on) => { if (on === undefined) { s.has(c) ? s.delete(c) : s.add(c); }
      else if (on) { s.add(c); } else { s.delete(c); } return s.has(c); } };
}
class El {
  constructor(id) {
    this.id = id; this._html = ''; this.textContent = ''; this.hidden = false;
    this.disabled = false; this.value = ''; this.checked = false; this.dataset = {};
    this.style = {}; this.children = []; this.attrs = {}; this.classList = classList();
  }
  set innerHTML(v) {
    this._html = String(v);
    this.children = [];               // the real DOM drops children on assignment
    const rx = /id="([\w-]+)"/g; let m;
    while ((m = rx.exec(this._html))) els.get(m[1]) || els.set(m[1], new El(m[1]));
  }
  get innerHTML() { return this._html; }
  setAttribute(k, v) { this.attrs[k] = String(v); }
  getAttribute(k) { return this.attrs[k]; }
  appendChild(c) { this.children.push(c); return c; }
  addEventListener() {}
  querySelector(sel) { return sel.startsWith('.') ? new El(sel.slice(1)) : els.get(sel.replace('#', '')) || new El(''); }
  querySelectorAll(sel) { return sel === '.tweet-actions button' ? [new El(''), new El(''), new El(''), new El('')] : [this.querySelector(sel)]; }
}
const els = new Map();
for (const m of HTML.matchAll(/id="([\w-]+)"/g)) els.set(m[1], new El(m[1]));
// honour the initial disabled/hidden attributes the real DOM would apply
for (const m of HTML.matchAll(/<[^>]*id="([\w-]+)"[^>]*>/g)) {
  const el = els.get(m[1]);
  if (!el) continue;
  if (/\sdisabled(\s|>)/.test(m[0])) el.disabled = true;
  if (/\shidden(\s|>)/.test(m[0])) el.hidden = true;
}
const get = id => els.get(id);
const document = {
  querySelector: sel => els.get(sel.replace('#', '')) || new El(''),
  querySelectorAll: () => [], createElement: () => new El(''), addEventListener() {},
};
const FAIL = new Set();
async function fetchStub(url) {
  if (FAIL.has(url)) return { ok: false, status: 404, json: async () => ({}) };
  const p = path.join(ROOT, url);
  if (!fs.existsSync(p)) return { ok: false, status: 404, json: async () => ({}) };
  return { ok: true, status: 200, json: async () => JSON.parse(fs.readFileSync(p, 'utf8')) };
}
const ctx = vm.createContext({
  document, fetch: fetchStub, console, setTimeout,
  window: { scrollTo() {} },
  navigator: { clipboard: { writeText() {} } },
  localStorage: { _d: {}, getItem(k) { return this._d[k] ?? null; }, setItem(k, v) { this._d[k] = String(v); } },
});
const call = expr => vm.runInContext(expr, ctx, { filename: 'app.js' });
const wait = ms => new Promise(r => setTimeout(r, ms));
const index = JSON.parse(fs.readFileSync(path.join(ROOT, 'data', 'index.json'), 'utf8'));
const runIn = code => vm.runInContext(code, ctx, { filename: 'app.js' });

console.log('app.js headless smoke test\n');
runIn(SRC);
for (let i = 0; i < 60 && get('enterBtn').disabled; i++) await wait(50);

console.log('manifest boot');
ok('enter button enabled after the manifest loads', get('enterBtn').disabled === false);
ok('landing note is filled from the manifest', /\d+ documents/.test(get('landingNote').textContent || ''), get('landingNote').textContent);
ok('year picker spans appRange', get('selYear').innerHTML.includes('1789') && get('selYear').innerHTML.includes('1821'));
ok('all moments offered', (get('featuredSelect').innerHTML.match(/value="/g) || []).length === index.events.length + 1,
   (get('featuredSelect').innerHTML.match(/value="/g) || []).length + ' vs ' + (index.events.length + 1) + ' with placeholder');
ok('no error banner on a healthy load', get('archiveError').hidden === true);

console.log('\nboot date must not be empty');
const busiest = Object.keys(index.dateCount).sort()
  // lowest wins ties (matches bestDayIn's strict-greater scan over sorted keys)
  .reduce((a, k) => (a === null || index.dateCount[k] > index.dateCount[a] ? k : a), null);
ok('boot date carries documents', index.dateCount[busiest] > 0, busiest + ' has ' + index.dateCount[busiest]);
ok('landing note counts documents', /\d+ documents/.test(get('landingNote').textContent || ''));

console.log('\ndocumented day (' + busiest + ')');
const [by, bm, bd] = busiest.split('-').map(Number);
const appDefault = runIn('iso(cur)');
ok('busiest date resolves from the manifest', !!busiest, JSON.stringify(busiest));
ok('boot opens on the earliest of the busiest dates', appDefault === busiest, 'cur=' + appDefault + ' vs tiebreak=' + busiest);
await runIn(`enter({d:${bd},m:${bm},y:${by}})`);
ok('feed has cards', get('feed').children.length > 0, 'nodes=' + get('feed').children.length);
ok('tweet count matches the manifest', Number(get('tweetCount').textContent) === index.dateCount[busiest],
   get('tweetCount').textContent + ' vs manifest ' + index.dateCount[busiest]);
ok('empty state stays hidden', get('emptyState').hidden === true);
ok('coverage note counts the date', /from this date/.test(get('coverageNote').textContent || ''), get('coverageNote').textContent);
ok('era label shown on the profile card', /Empire|Consulate|Italy|Egypt|Revolution|Russia|St Helena/.test(get('profilePeriod').textContent || ''),
   get('profilePeriod').textContent);

console.log('\nquiet day (92% of the range)');
let empty = null;
for (let d = 1; d <= 28 && !empty; d++) {
  const s = '1800-07-' + String(d).padStart(2, '0');
  if (!index.dateCount[s]) empty = s;
}
ok('found a date with no documents to test', !!empty, 'none found in July 1800');
const [ey, em, ed] = empty.split('-').map(Number);
await runIn(`goTo({d:${ed},m:${em},y:${ey}})`);
ok('empty state is shown', get('emptyState').hidden === false);
ok('empty state offers the nearest document', /nearest document/.test(get('emptyState').innerHTML));
ok('empty state names the era and its size', /Consulate/.test(get('emptyState').innerHTML), get('emptyState').innerHTML.slice(0, 130));
ok('coverage note reports none', /No Tweets/.test(get('coverageNote').textContent || ''), get('coverageNote').textContent);
ok('feed is empty', get('feed').children.length === 0);

console.log('\narchive failure must be loud');
FAIL.add('data/shard_crisis.json');
await runIn('goTo({d:16,m:10,y:1813})');
ok('banner appears when a shard 404s', get('archiveError').hidden === false);
ok('banner names the failed file', /shard_crisis\.json/.test(get('archiveError').innerHTML));
ok('banner offers a retry', /retryBtn/.test(get('archiveError').innerHTML));
ok('date still navigates despite the failure', get('curDate').textContent === '16 October 1813', get('curDate').textContent);
FAIL.delete('data/shard_crisis.json');
await runIn("$('#retryBtn').onclick()");
await wait(120);
ok('retry clears the banner', get('archiveError').hidden === true, get('archiveError').innerHTML.slice(0, 90));
ok('retry keeps the current date', get('curDate').textContent === '16 October 1813');

console.log('\nmanifest failure must be loud too');
FAIL.add('data/index.json');
get('enterBtn').disabled = false;
get('archiveError').hidden = true;
const ctx2 = vm.createContext({
  document, fetch: fetchStub, console, setTimeout,
  window: { scrollTo() {} },
  navigator: { clipboard: { writeText() {} } },
  localStorage: { _d: {}, getItem(k) { return this._d[k] ?? null; }, setItem(k, v) { this._d[k] = String(v); } },
});
vm.runInContext(SRC, ctx2, { filename: 'app.js' });
await wait(250);
ok('enter button is not left enabled', get('enterBtn').disabled === true);
ok('button says why', /unavailable/i.test(get('enterBtn').textContent || ''), get('enterBtn').textContent);
ok('banner names the manifest', /index\.json/.test(get('archiveError').innerHTML));
ok('banner is visible', get('archiveError').hidden === false);

console.log('\nUI contract');
ok('landing offers no day picker', !HTML.includes('selDay'));
ok('year picker lists years with their counts', /1789 · \d+/.test(get('selYear').innerHTML),
   (get('selYear').innerHTML.match(/>[^<]+</g) || []).slice(0, 2).join(' '));
ok('month picker is populated', /January/.test(get('selMonth').innerHTML) && /December/.test(get('selMonth').innerHTML));
ok('month options carry counts', / · \d+| · —/.test(get('selMonth').innerHTML));

console.log('\nfull text, not two lines');
const eraId = index.shardByYear[busiest.slice(0, 4)];
const eraFile = index.shards.find(s => s.id === eraId).file;
const recs = JSON.parse(fs.readFileSync(path.join(ROOT, eraFile), 'utf8')).filter(r => r.date === busiest);
const [rby, rbm, rbd] = busiest.split('-').map(Number);
await runIn(`enter({d:${rbd},m:${rbm},y:${rby}})`);
// enter twice: the first may interleave with an in-flight retry goTo
await runIn(`enter({d:${rbd},m:${rbm},y:${rby}})`);
const cards = [];
for (const child of get('feed').children) cards.push(...(child.children.length ? child.children : [child]));
ok('one card per document', cards.length === recs.length, cards.length + ' cards vs ' + recs.length + ' records');
const fullShown = recs.filter(r => cards.some(c => c.innerHTML.includes(r.displayText))).length;
ok('every quote renders in full', fullShown === recs.length, fullShown + '/' + recs.length + ' in full');
ok('no card asks you to expand a short quote', cards.every(c => !c.innerHTML.includes('Show more')));
ok('source line shows without a click', cards.every(c => /tweet-meta/.test(c.innerHTML)));
ok('every card opens on a caption, not the raw quote', cards.every(c => /class="tweet-text"/.test(c.innerHTML) && /caption · quoted words below/.test(c.innerHTML)));
ok('verbatim quote is collapsed but present', cards.every(c => /class="quote" hidden/.test(c.innerHTML)));
ok('quoted-words expander is wired', cards.every(c => /data-k="quote"/.test(c.innerHTML)));
ok('no leftover frame chrome', cards.every(c => !/class="frame"|chain-next/.test(c.innerHTML)) && !fs.readFileSync(path.join(ROOT, 'styles.css'), 'utf8').includes('.frame{'));
ok('longest excerpt is inside the clamp', Math.max(...recs.map(r => r.displayText.length)) <= 420,
   'max ' + Math.max(...recs.map(r => r.displayText.length)) + ' chars');

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
