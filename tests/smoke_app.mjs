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

console.log('\nvoice tweets, caps, and stripped chrome');
const eraId = index.shardByYear[busiest.slice(0, 4)];
const eraFile = index.shards.find(s => s.id === eraId).file;
const recs = JSON.parse(fs.readFileSync(path.join(ROOT, eraFile), 'utf8')).filter(r => r.date === busiest);
const [rby, rbm, rbd] = busiest.split('-').map(Number);
await runIn(`enter({d:${rbd},m:${rbm},y:${rby}})`);
// enter twice: the first may interleave with an in-flight retry goTo
await runIn(`enter({d:${rbd},m:${rbm},y:${rby}})`);
const cards = [];
for (const child of get('feed').children) cards.push(...(child.children.length ? child.children : [child]));
const headOf = c => (c.innerHTML.match(/class="tweet-text">([\s\S]*?)<\/div>/) || [])[1] || '';
ok('one card per document', cards.length === recs.length, cards.length + ' cards vs ' + recs.length + ' records');
ok('every card leads with a context headline', cards.every(c => headOf(c).trim().length > 10), cards.map(headOf).join(' | ').slice(0, 120));
const withVoice = recs.map((r, i) => [r, cards[i]]).filter(([r]) => r.voice && !r.tweet);
const withoutVoice = recs.map((r, i) => [r, cards[i]]).filter(([r]) => !r.voice && !r.tweet);
const withTweet = recs.map((r, i) => [r, cards[i]]).filter(([r]) => r.tweet);
ok('records with a voice line tweet it', withVoice.every(([r, c]) => headOf(c).includes((r.voice || '').slice(0, 60))),
  withVoice.length + ' voice cards');
ok('paraphrased records tweet the paraphrase', withTweet.every(([r, c]) => headOf(c).includes((r.tweet || '').slice(0, 60))),
  withTweet.length + ' paraphrase cards');
ok('voice lines are first-person', withVoice.every(([r, c]) => /@\w+|\b(I|we|my|our|me|myself)\b|^(Let|Write|See|Take|Send|Tell|Reply|Be|Soldiers|Citizens)/i.test(headOf(c))));
for (const [r, c] of withoutVoice) {
  const head = await runIn(`headlineFor(${JSON.stringify(r)})`);
  const live = await runIn(`voiceFor(${JSON.stringify({ sourceTitle: r.sourceTitle, location: r.location, date: r.date, displayText: r.displayText })})`);
  if (headOf(c) !== (live || head)) { ok('voiceless records fall back to the narrative', false, r.id); break; }
}
ok('voiceless records fall back to the narrative', true);
ok('no context cap line on any card (lives in Source & context)', cards.every(c => !/tweet-cap/.test(c.innerHTML)));
ok('no card shows the whole quote as its tweet', cards.every(c => !c.innerHTML.match(/class="tweet-text">[\s\S]*?[\u201c"]/) ||
  !recs.some(r => r.displayText.length < 200 && headOf(c).includes(r.displayText))));
ok('verbatim sits behind its button, hidden', cards.every(c => /class="verbatim" hidden/.test(c.innerHTML) || !/data-k="quote"/.test(c.innerHTML)));
ok('voice picker takes first-person clauses (codicil regression)', (() => {
  const v = runIn(`voiceFor({sourceTitle:'Codicil on burial, April 1821', location:'Longwood', date:'1821-04-15', displayText:'“I desire my ashes to rest on the banks of the Seine, amid the French people I loved so well. […]”'})`);
  return /I desire my ashes/.test(v || '');
})());
ok('capitalised You/My openers count as first-person', (() => {
  const a = runIn(`voiceFor({sourceTitle:'To Prince Joseph, Paris, 1806-02-01', location:'Paris', date:'1806-02-01', displayText:'“Disarm Naples, and levy a contribution of 10,000,000 francs on the city. It will be paid easily. You have certain resources by confiscating English merchandise.”'})`);
  const b = runIn(`voiceFor({sourceTitle:'To M. Fouche, Paris, 1806-02-01', location:'Paris', date:'1806-02-01', displayText:'“My intention is consequently that the religious journals shall cease to appear.”'})`);
  return /You have certain resources/.test(a || '') && /My intention is consequently/.test(b || '');
})());
ok('paraphrase tweets render where present, with disclosure', await (async () => {
  const html = runIn(`card({author:'Napoleon Bonaparte',handle:'@bonaparte',accountType:'person',faction:'Empire',date:'1806-02-01',timeLabel:'TIME UNCERTAIN',timePrecision:'day',location:'Paris',originalLanguage:'French',displayText:'“Disarm Naples.”',sourceTitle:'To Prince Joseph, Paris, 1806-02-01',archive:'A',sourceUrl:'http://x',documentType:'letter',evidenceType:'TRANSLATION',dateCertainty:'certain',eventIds:[],editorialStatus:'verified',context:'Paris. Some context.',tweet:'You cannot want money. Take ten million francs.'}).innerHTML`);
  return html.includes('You cannot want money') && /paraphrase in his voice/.test(html);
})());
ok('whole-quote tweets hide their verbatim block', (() => {
  const html = runIn(`card({author:'Napoleon Bonaparte',handle:'@bonaparte',accountType:'person',faction:'Empire',date:'1806-02-01',timeLabel:'TIME UNCERTAIN',timePrecision:'day',location:'Paris',originalLanguage:'French',displayText:'“I die.”',sourceTitle:'X',archive:'A',sourceUrl:'http://x',documentType:'letter',evidenceType:'TRANSLATION',dateCertainty:'certain',eventIds:[],editorialStatus:'verified',context:'A short note here.',voice:'I die.'}).innerHTML`);
  const html2 = runIn(`card({author:'Napoleon Bonaparte',handle:'@bonaparte',accountType:'person',faction:'Empire',date:'1806-02-01',timeLabel:'TIME UNCERTAIN',timePrecision:'day',location:'Paris',originalLanguage:'French',displayText:'“I die and I return to haunt the Tuileries at midnight.”',sourceTitle:'X',archive:'A',sourceUrl:'http://x',documentType:'letter',evidenceType:'TRANSLATION',dateCertainty:'certain',eventIds:[],editorialStatus:'verified',context:'A short note here.',voice:'I die.'}).innerHTML`);
  return !/verbatim/.test(html) && /verbatim/.test(html2);
})());
ok('verbatim text is in the card (full, cut+rest, or tweeted whole)', recs.filter(r => cards.some(c => {
  if (c.innerHTML.includes(r.displayText)) return true;
  if (r.displayText.length > 420 && c.innerHTML.includes(r.displayText.slice(0, 60))) return true;
  const t = (c.innerHTML.match(/class="tweet-text">([\s\S]*?)<\/div>/) || [])[1] || '';
  const n = s => s.toLowerCase().replace(/[^a-z]/g, '');
  return n(t) === n(r.displayText); // dupQuote: tweet IS the quote
})).length === recs.length);
ok('no source-title meta line on any card (lives in Source & context)', cards.every(c => !/tweet-meta/.test(c.innerHTML)));
ok('source lives in the context panel', cards.every((c, i) => c.innerHTML.includes(recs[i].sourceTitle)));
ok('no evidence pills on any card', cards.every(c => !/class="ev"/.test(c.innerHTML)));
ok('no dates in tweet text (the UI shows the date)', cards.every(c => {
  const t = headOf(c);
  return !/\b(?:January|February|April|June|July|August|September|October|November|December)\b/i.test(t) &&
    !/\bMay\b/.test(t) && !/\bMarch\b/.test(t) &&
    !/\b1[789]\d\d\b/.test(t) && !/\b1[78]\s\d\d\b/.test(t) && !/\b\d{1,2}(st|nd|rd|th)\b/.test(t) &&
    !/\d{4}-\d{2}-\d{2}/.test(t);
}), cards.map(headOf).join(' | ').slice(0, 200));
ok('no builder notes leak into cards', cards.every(c => !/Trivial OCR repairs|single characters/i.test(headOf(c))));
ok('thread shows one Follow button, not one per card', (() => {
  const threads = get('feed').children.filter(c => c.children.length > 1);
  return threads.every(t => t.children.filter(x => /follow-btn/.test(x.innerHTML)).length === 1);
})());
ok('longest excerpt is inside the clamp', Math.max(...recs.map(r => r.displayText.length)) <= 420,
   'max ' + Math.max(...recs.map(r => r.displayText.length)) + ' chars');

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
