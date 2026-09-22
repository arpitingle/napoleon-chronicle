/* Chronicle — Napoleon. Manifest-driven: data/index.json lists the era shards,
   the app fetches only the era it needs and reports any archive failure loudly. */
let POSTS=[], EVENTS=[], INDEX=null;
let AUTHOR={}, AVATAR={};
let cur={d:12,m:4,y:1796};
let followed=new Set(JSON.parse(localStorage.getItem('nap_follow')||'[]'));
let replayOn=false, ready=false, DEFAULT=null;
let view='date', pendingFlash=null;
const problems=[];
const shardCache=new Map();
const seenIds=new Set();
const $=s=>document.querySelector(s);
const ORDER={'MORNING':0,'AFTERNOON':1,'EVENING':2,'TIME UNCERTAIN':3};
const MONTHS=['January','February','March','April','May','June','July','August','September','October','November','December'];
function fmt(d,m,y){return `${d} ${MONTHS[m-1]} ${y}`}
function iso(o){return `${o.y}-${String(o.m).padStart(2,'0')}-${String(o.d).padStart(2,'0')}`}
function parseIso(s){const[a,b,c]=s.split('-').map(Number);return{y:a,m:b,d:c}}
function saveFollow(){localStorage.setItem('nap_follow',JSON.stringify([...followed]))}
const EV_SHORT={'ORIGINAL MANUSCRIPT':'📜 manuscript','CONTEMPORARY NEWSPAPER':'📰 newspaper','OFFICIAL RECORD':'🏛 official','CONTEMPORARY TRANSCRIPT':'🗣 transcript','EYEWITNESS ACCOUNT':'👁 eyewitness','LATER MEMOIR':'💭 memoir','TRANSLATION':'🌐 translation','DATE APPROXIMATE':'~ approx date'};
/* EV_SHORT no longer renders (badges removed) but stays as the display
   contract verify.py checks evidenceType values against. */
function avatarHTML(a){const u=AVATAR[a];return u?`<img class="ava" src="${u}" alt="${a}">`:`${a.trim()[0]}`}
function shortHTML(t){
  /* the archive caps excerpts at ~300 chars (a handful reach ~400), so almost
     every record can show in full — only genuinely long ones get a Show more */
  const plain=t.replace(/^“|”$/g,''),LIMIT=420;
  if(plain.length<=LIMIT)return null;
  let cut=plain.slice(0,LIMIT);const k=cut.lastIndexOf(' ');cut=cut.slice(0,k>LIMIT*0.7?k:LIMIT);
  return {cut,rest:plain.slice(cut.length)};
}
/* ---- archive loading ---- */
async function getJSON(url){
  const r=await fetch(url,{cache:'no-cache'});
  if(!r.ok)throw new Error(`${url} → HTTP ${r.status}`);
  return r.json();
}
function noteProblem(msg){if(!problems.includes(msg))problems.push(msg);renderProblems()}
function renderProblems(){
  const b=$('#archiveError');
  if(!problems.length){b.hidden=true;b.innerHTML='';return}
  b.hidden=false;
  b.innerHTML=`<b>⚠ Parts of the archive did not load.</b> Showing what did. <button id="retryBtn">Retry</button><ul>${problems.map(p=>`<li>${p}</li>`).join('')}</ul>`;
  $('#retryBtn').onclick=()=>{problems.length=0;shardCache.clear();renderProblems();goTo(cur)};
}
function shardMeta(id){return (INDEX.shards||[]).find(s=>s.id===id)||null}
async function loadShard(id){
  if(shardCache.has(id))return shardCache.get(id);
  const meta=shardMeta(id);
  if(!meta){noteProblem(`no shard covers ${cur.y} — data/index.json lists ${(INDEX.shards||[]).length}`);return []}
  const p=getJSON(meta.file).then(recs=>{
    if(!Array.isArray(recs)){noteProblem(`${meta.file} is not a list of records`);return []}
    const need=(INDEX.meta.schema&&INDEX.meta.schema.required)||[];
    const bad=[],ok=[];
    recs.forEach(r=>{
      if(r.editorialStatus!=='verified'){bad.push(r.id||'?');return}
      const miss=need.filter(k=>!(k in r));
      if(miss.length){bad.push((r.id||'?')+' missing '+miss.join('/'));return}
      if(seenIds.has(r.id))return;
      seenIds.add(r.id);
      ok.push(r);
    });
    if(bad.length)noteProblem(`${meta.file}: ${bad.length} record(s) rejected — ${bad.slice(0,2).join('; ')}`);
    if(recs.length!==meta.count)noteProblem(`${meta.file}: expected ${meta.count} records, got ${recs.length}`);
    POSTS=POSTS.concat(ok);
    return ok;
  }).catch(e=>{noteProblem(`${meta.file} failed to load (${e.message||e})`);return []});
  shardCache.set(id,p);
  return p;
}
async function ensureDate(){
  const id=(INDEX.shardByYear||{})[String(cur.y)];
  if(id)await loadShard(id);
  else noteProblem(`year ${cur.y} has no shard mapping in data/index.json`);
}
/* ---- boot ---- */
async function load(){
  const btn=$('#enterBtn');
  try{INDEX=await getJSON('data/index.json')}
  catch(e){noteProblem(`data/index.json failed to load (${e.message||e})`);btn.disabled=true;btn.textContent='Archive unavailable';return}
  const need=['meta','counts','authors','events','shards','shardByYear','appRange'];
  const miss=need.filter(k=>!(k in INDEX));
  if(miss.length){noteProblem(`data/index.json is missing: ${miss.join(', ')}`);btn.disabled=true;btn.textContent='Archive unavailable';return}
  EVENTS=INDEX.events||[];
  (INDEX.authors||[]).forEach(a=>{AUTHOR[a.author]=a;if(a.avatar)AVATAR[a.author]=a.avatar});
  const r=INDEX.appRange;const j=$('#jumpDate');j.min=r.from;j.max=r.to;
  DEFAULT=busiestDate();
  if(DEFAULT)cur=parseIso(DEFAULT);          /* never open on an empty day */
  try{
    const saved=localStorage.getItem('nap_last');
    if(saved&&/^\d{4}-\d{2}-\d{2}$/.test(saved)&&INDEX.dateCount[saved])cur=parseIso(saved);
  }catch(e){}                                /* reading position, when kept */
  j.value=iso(cur);
  initLanding();
  ready=true;btn.disabled=false;btn.textContent='Enter timeline';
  $('#timelineTitle').textContent='Latest Tweets';
  $('#landingNote').textContent=`${INDEX.counts.posts} documents · ${INDEX.counts.dates} dated days · ${INDEX.counts.authors} voices`;
  updateSavedCount();
  let nav=null;
  try{nav=parseHash(typeof location!=='undefined'?location.hash:'')}catch(e){}
  if(nav){
    if(nav.kind==='date')enter(nav.o);
    else if(nav.kind==='post')enterPost(nav.id);
  }
}
function monthCounts(y){
  const out={};
  Object.keys(INDEX.dateCount).forEach(k=>{
    if(k.slice(0,4)===String(y)){const m=+k.slice(5,7);out[m]=(out[m]||0)+INDEX.dateCount[k]}
  });
  return out;
}
function bestDayIn(y,m){
  /* the fullest documented day inside a month, straight from the manifest */
  const pre=String(y)+'-'+String(m).padStart(2,'0')+'-';
  let best=null,bc=-1;
  Object.keys(INDEX.dateCount).sort().forEach(k=>{
    if(k.indexOf(pre)===0&&INDEX.dateCount[k]>bc){bc=INDEX.dateCount[k];best=k}
  });
  return best;
}
function updatePickNote(){
  const y=+$('#selYear').value,m=+$('#selMonth').value;
  if(!y||!m)return;
  const c=monthCounts(y)[m]||0,d=bestDayIn(y,m);
  $('#landingNote').textContent=c
    ? `${MONTHS[m-1]} ${y} · ${c} document${c===1?'':'s'} · opens ${fmt(+d.slice(8),+d.slice(5,7),+d.slice(0,4))}`
    : `${MONTHS[m-1]} ${y} · nothing survives for this month — you will land on the nearest date`;
}
function fillMonths(y){
  const m=$('#selMonth'),c=monthCounts(y),want=+m.value||cur.m;
  m.innerHTML=MONTHS.map((n,i)=>{
    const v=i+1,cnt=c[v]||0;
    return `<option value="${v}" ${v===want?'selected':''}>${n}${cnt?' · '+cnt:' · —'}</option>`;
  }).join('');
}
function initLanding(){
  const m=$('#selMonth'),y=$('#selYear'),r=INDEX.appRange;
  const y0=+r.from.slice(0,4),y1=+r.to.slice(0,4);
  y.innerHTML=Array.from({length:y1-y0+1},(_,i)=>y0+i)
    .map(v=>`<option value="${v}" ${v===cur.y?'selected':''}>${v} · ${INDEX.byYear[v]||0}</option>`).join('');
  fillMonths(cur.y);
  y.onchange=()=>{fillMonths(+y.value);updatePickNote()};
  m.onchange=updatePickNote;
  const fs=$('#featuredSelect');
  fs.innerHTML='<option value="">— Choose a moment —</option>'+
    EVENTS.map(ev=>`<option value="${ev.date}">${ev.label} · ${ev.date}</option>`).join('');
  fs.onchange=()=>{if(fs.value)enter(parseIso(fs.value))};
  $('#enterBtn').onclick=()=>{
    const yy=+y.value,mm=+m.value;
    enter(parseIso(bestDayIn(yy,mm)||`${yy}-${String(mm).padStart(2,'0')}-01`));
  };
}
function showBanner(ev){
  const b=$('#eventBanner');
  if(!ev){b.hidden=true;return}
  b.hidden=false;
  b.innerHTML=`<b>${ev.label}</b> · ${ev.date} — ${ev.blurb} <button id="repEv">Replay</button>`;
  $('#repEv').onclick=()=>{replayOn=true;render()};
}
async function enter(o){
  $('#landing').style.display='none';$('#app').hidden=false;
  await goTo(o);window.scrollTo(0,0);
}
async function goTo(o){view='date';pendingFlash=null;await showCur(o)}
async function showCur(o){
  cur=o;
  $('#jumpDate').value=iso(cur);
  showBanner(EVENTS.find(e=>e.date===iso(cur))||null);
  if(ready)await ensureDate();
  render();
  try{localStorage.setItem('nap_last',iso(cur))}catch(e){}
  syncHash();flashPending();
}
async function goToPost(id){
  let p=POSTS.find(x=>x.id===id);
  if(!p){await ensureAll();p=POSTS.find(x=>x.id===id)}
  if(!p){noteProblem(`shared post ${id} is not in the archive`);return}
  view='post';cur=parseIso(p.date);pendingFlash=id;
  await showCur(cur);
}
/* ---- feed ---- */
function era(){return shardMeta((INDEX.shardByYear||{})[String(cur.y)])}
function busiestDate(){
  /* the best-documented date in the archive, derived — never hardcoded */
  let best=null,bc=-1;
  Object.keys(INDEX.dateCount||{}).sort().forEach(k=>{const c=INDEX.dateCount[k];if(c>bc){bc=c;best=k}});
  return best;
}
function nearestDate(target){
  const keys=Object.keys(INDEX.dateCount||{});
  if(!keys.length)return null;
  let best=null,bd=Infinity;
  keys.forEach(k=>{const n=Math.abs(Math.round((new Date(k)-new Date(target))/86400000));if(n<bd){bd=n;best=k}});
  return {date:best,days:bd};
}
function visiblePosts(){
  const target=iso(cur);
  let list=POSTS.filter(p=>p.date===target);
  list.sort((a,b)=>(ORDER[a.timeLabel]??3)-(ORDER[b.timeLabel]??3)||(a.id<b.id?-1:1));
  return {list,target,spoiler:false};
}
function redact(t,on){if(!on)return t;return t.replace(/guillotin\w*|execut\w*|behead\w*|massacr\w*/gi,'████')}
function render(){
  destroyMap();
  const{list,target,spoiler}=visiblePosts();
  $('#curDate').textContent=fmt(cur.d,cur.m,cur.y);
  $('#tweetCount').textContent=list.length;
  const e=era();
  $('#timelineTitle').textContent=replayOn?'Replay day':(e?e.label:'Latest Tweets');
  if(e)$('#profilePeriod').textContent=e.label;
  $('#coverageNote').textContent=list.length?`${list.length} Tweet${list.length===1?'':'s'} from this date`:'No Tweets for this date.';
  const feed=$('#feed');feed.innerHTML='';
  const es=$('#emptyState');
  if(!list.length){
    es.hidden=false;
    const n=nearestDate(target);
    const near=n?`<p>The nearest document is <a href="#" id="goNear">${fmt(+n.date.slice(8),+n.date.slice(5,7),+n.date.slice(0,4))}</a> — ${n.days} day${n.days===1?'':'s'} away.</p>`:'';
    const gap=e?`<p class="gray">${e.label} · ${e.count} documents, ${e.from}–${e.to}.</p>`:'';
    const best=DEFAULT?`<p><a href="#" id="go1796">Go to the best-documented date — ${fmt(+DEFAULT.slice(8),+DEFAULT.slice(5,7),+DEFAULT.slice(0,4))} (${INDEX.dateCount[DEFAULT]} documents)</a></p>`:'';
    es.innerHTML=`<p>This date is quiet in the archive.</p>${near}${gap}${best}`;
    const g=$('#go1796');if(g)g.onclick=ev=>{ev.preventDefault();goTo(parseIso(DEFAULT))};
    const gn=$('#goNear');if(gn)gn.onclick=ev=>{ev.preventDefault();goTo(parseIso(n.date))};
  }else es.hidden=true;
  if(replayOn&&list.length){let i=0;const step=()=>{if(i<list.length){feed.appendChild(card(list[i],spoiler));i++;setTimeout(step,500)}};step();return}
  let run=[];
  const flush=()=>{if(!run.length)return;
    if(run.length>1){const w=document.createElement('div');w.className='thread';
      run.forEach((p,i)=>{w.appendChild(card(p,spoiler,i+1,run.length))});
      feed.appendChild(w)}else feed.appendChild(card(run[0],spoiler));
    run=[]};
  list.forEach(p=>{const l=run[run.length-1];
    if(l&&l.author===p.author&&l.date===p.date)run.push(p);else{flush();run=[p]}});
  flush();
}
/* ---- context is the tweet; verbatim is one tap down ----
   The visible line is editorial context (captionFor) or, where the context
   is pure boilerplate, a line composed from verified fields (addressee /
   place / date). It never rewords the letter. The exact historical text
   lives behind the Verbatim button, unaltered. */
const PROV=/translated for chronicle|english from the|french in the|full text in the|public domain|public-domain/i;
/* the auto-generated "Letter to X from Y, date." line — reworded, not quoted */
/* ---- caption: only when the context says something the quote doesn't ----
   Provenance boilerplate and lines that merely restate the source title
   never become visible text. Short hand-written summaries ("Ultimatum
   season.") do: the 12-char floor keeps one-line telegrams, not fragments. */
const NOTEISH=/trivial ocr|ocr repairs|single characters|running head/i;
function sentencesOf(t){return (t||'').match(/[^.!?]+[.!?]+["\u201d']?|\S[^.!?]*$/g)||[]}
function captionFor(p){
  const raw=(p.context||'').trim();
  const sents=sentencesOf(raw).map(s=>s.trim());
  const auto=/^letter to .+ from .+\d{4}/i.test(raw);
  let cand;
  if(auto){
    const i=sents.findIndex(s=>PROV.test(s));
    cand=i>-1?sents.slice(i+1).filter(s=>!PROV.test(s)).join(' '):'';
  }else{
    cand=sents.filter(s=>!PROV.test(s)).join(' ');
  }
  cand=(cand||'').trim();
  if(cand.length<12||!/[a-z]/i.test(cand)||NOTEISH.test(cand))return '';
  const norm=s=>(s||'').toLowerCase().replace(/[^a-z]/g,'');
  if(norm(cand).replace(/\d/g,'') && norm(p.sourceTitle).indexOf(norm(cand).replace(/\d/g,'').slice(0,30))>-1)return '';
  if(!/[.!?]$/.test(cand))cand+='.';
  return cand.charAt(0).toUpperCase()+cand.slice(1);
}
function fmtDate(isoStr){
  const m=/^(\d{4})-(\d{2})-(\d{2})$/.exec(isoStr||'');
  if(!m)return isoStr||'';
  return fmt(+m[3],+m[2],+m[1]);
}
function headlineFor(p){
  const cap=captionFor(p);
  if(cap)return cap;
  /* fallback: the source title minus any trailing date — the UI shows
     the date on every card, so the tweet never repeats it */
  const base=(p.sourceTitle||'A document')
    .replace(/,\s*\d{4}-\d{2}-\d{2}\s*$/,'')
    .replace(/,\s*(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\s*$/,'')
    .trim();
  const rawLoc=p.location||'';
  const loc=(/\d|\^|\*|•/.test(rawLoc)||/^[^A-Za-zÀ-Þ]/.test(rawLoc))?'':rawLoc;
  if(loc&&base.toLowerCase().endsWith(loc.toLowerCase()))return `${base}.`;
  if(loc)return `${base} — ${loc}.`;
  return `${base}.`;
}
function hasCaption(p){return captionFor(p)!==''}
/* ---- the tweet is Napoleon's voice: a first-person clause from the letter.
   Bulk records carry a pipeline-picked voice line (record.voice); the rest
   fall back to picking one from the excerpt here, else the narrative. */
const VOICE_CRUST=[/^[“"'\s*<>.,;:\-—–]+/,/^(To\s+[A-Z][^.!?]{5,80}?\.\s*)/,
  /^("[A-Z][A-Za-z \-']{3,40}?,\s*)/,/^([A-Z][a-z]+\s*,?\s*(th|st|nd|rd)?\s*[A-Za-z]*\s*1[78]\d\d\.?\s*\*?\s*)/,
  /^((O|«)\s*)?CHAPTER[^.!?]*[.!?]\s*/i,/^((O|«)\s*)?THE YEAR 1[78]\d\d[^.!?]*[.!?]\s*/i,
  /^\([^)]*omitted\)\.?\s*/i,/^(My\s+)?(Sir|Madame|Monsieur|Lord|Cousin|Son|Daughter|Sister|Brother)[^:—–-]*[:—–-]\s*/,
  /^u\s+BONAPARTE\.?\s*/i,/^"?\s*Napoleon\.?"?\s*/,/^BONAPARTE\.?\s*/,
  /^[A-Z][A-Z \-/']{4,40}?\.\s*/,/^\d{1,3}\s+(?!(?:men|francs|guns|ships|soldiers|crowns|troops|artillery|cavalry|horses|waggons|miles|leagues|days|months|years|prisoners|o'clock)\b)/i];
const VOICE_JUNK=[/\b[A-Z]{9,}\b/,/[A-Za-z]+\d+[A-Za-z]+/,/\b1[78]\s\d\d\b/,/\S  \S/,/[a-z][A-Z][a-z]/,
  /\b[A-Z]{3,}\b.*\b[A-Z]{3,}\b.*\b[A-Z]{3,}\b/,/(?<![\d,])\b\d{1,3}\s+[a-zà-þ]/,
  /(?<=[A-Za-z]{4})\. +(?=[A-Z][a-z])/];
function cleanVoice(t){
  t=(t||'').replace(/[“”]/g,'"').replace(' […]',' ').replace('[…]',' ');
  t=t.replace(/\s+/g,' ').trim();
  for(let i=0;i<6;i++)for(const rx of VOICE_CRUST)t=t.replace(rx,'').trim();
  return t;
}
function handleOf(p){
  const m=/^To\s+(.+?)(?:,|$)/i.exec(p.sourceTitle||'');
  if(!m)return null;
  const fold=s=>s.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'');
  const key=fold(m[1].trim().replace(/\.$/,'')).replace(/[^a-z]/g,'');
  const special={pope:'pope',holyfather:'pope',hhthepope:'pope',directory:'directory',senate:'senate',
    russia:'alexander',emperorofrussia:'alexander',peace:'godoy',princeofthepeace:'godoy'};
  if(special[key])return special[key];
  const titles=new Set(['general','marshal','admiral','cardinal','prince','princess','count','comte','duke','king','queen','emperor','minister','secretary','chief','staff','grand','judge','arch','chancellor','foreign','war','interior','police','navy','the','of','de','m']);
  const words=fold(m[1]).match(/[a-z]+/g)||[];
  const names=words.filter(w=>!titles.has(w)&&w.length>2);
  if(!names.length||/\d/.test(m[1])||/[A-Z]{5,}/.test(m[1]))return null;
  return names[names.length-1];
}
function voiceFor(p){
  /* records without a pipeline voice: pick a first-person clause live.
     Never a date (the UI shows it), never junk. */
  const NODATE=/\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\b|\b1[789]\d\d\b|\b1[78]\s\d\d\b|\b\d{1,2}(st|nd|rd|th)\b/i;
  const sents=sentencesOf(cleanVoice(p.displayText)).map(s=>s.trim()).filter(s=>s.length>=35&&s.length<=220);
  const first=/\b(I|We|My|Our|Me|we|my|our|me|myself|ourselves|You|you|Your|your|Yours|yours|moi|je|nous|mon|ma|mes|notre|nos)\b/;
  const dang=/^(He|She|It|They|This|That|These|Those|There|Then|Thus|Such|Which|Who|What|Where|When|While|Without|With|For|From|On|At|As|By|If|Though|Although|However|Meanwhile|Instead|Besides|Yet|Second|Third|Art|Your\s+(Majesty|Lordship|Highness|Excellency))\b/i;
  const verb=/\b(order(?:s|ed|ing)?|sen[dt]|despatch|dispatch|report|inform|apprise|demand|insist|refus|declin|deny|pay|paid|fund|march|warn|caution|request|beg|pray|announce|proclaim|declare|instruct|direct|forward|transmit|enclos|approv|sanction|propos|suggest|appoint|nominat|attack|assault|storm|defeat|beat|rout|retreat|withdraw|surrender|capitulat|complain|congratulate|arrest|assur|promis|authoris|forbid|forbade|forbidden|grant|resolv|learn|hear|receiv|arriv|seiz|occup|cross|enter|recall|dismiss|expect|hope|wish|fear|need|wrote|written|examin|pronounc|repli|answer|speak|talk|mention|continu|remain|long|urg|recommend|threaten|punish|reward|promot|transfer|detach|embark|sail|land|besieg|invest|blockad|burn|destroy|ruin|abdicat|resign|marry|marriage|divorce|crown|am|is|are|was|were|have|has|had|will|shall|must|do|does|did|let|take|took|taken|make|made|give|gave|given|send|sent|come|came|go|went|see|saw|know|knew|think|thought|find|found|leave|left|hold|held|keep|kept|put|set|seem|become|became|grow|grew|live|fall|fell|rise|fight|fought|win|won|lose|lost|owe|want|believe|desire|seek|gain|save|spare|join|quit|stay|serve|deserve|contain|explain|state|observe|remark|require|suppos|imagine)\b/i;
  let best=null,bs=-1;
  for(const s of sents){
    if(dang.test(s)||!first.test(s)||!verb.test(s.slice(0,140)))continue;
    if(NODATE.test(s))continue;
    if(VOICE_JUNK.some(rx=>rx.test(s)))continue;
    let sc=0;
    if(/^(I|We|My|Our|You|Your|Let|Soldiers|Citizens)\b/.test(s))sc+=3;
    sc+=2;
    if(/\b(her|him|them)\b/i.test(s)&&!/([A-ZÀ-Þ][a-zà-þ]+(\s+[A-ZÀ-Þ][a-zà-þ]+){0,2})/.test(s))sc-=4;
    if(sc>bs){bs=sc;best=s}
  }
  if(!best||bs<4)return null;
  let h=handleOf(p);
  if(h&&/\byou\b|\byour\b/i.test(best))best='@'+h+' '+best;
  best=best.replace(/["'\s]+$/,'');
  if(!/[.!?…]$/.test(best))best+='.';
  if(best.length>200){const cut=best.slice(0,200);const k=cut.lastIndexOf(' ');best=(k>120?cut.slice(0,k):cut).trimEnd()+'…'}
  return best;
}
function card(p,spoiler,nth,ofN){
  const d=document.createElement('article');d.className='post'+(ofN>1?' in-thread':'');
  d.id='p-'+p.id;
  const v=p.accountType==='person'?'<span class="verified">✔</span>':'';
  const threadTag=ofN>1?`<span class="tag"> · 🧵 ${nth}/${ofN}</span>`:'';
  const voice=p.voice||voiceFor(p);
  const head=redact(headlineFor(p),spoiler);
  const tweet=p.tweet?redact(p.tweet,spoiler):(voice?redact(voice,spoiler):head);
  const full=redact(p.displayText,spoiler),sh=shortHTML(p.displayText);
  const quoteHtml=sh?`“${redact(sh.cut,spoiler)}… <a href="#" class="more">Show more</a><span class="rest" hidden> ${redact(sh.rest,spoiler)}</span>”`:full;
  /* the tweet already is the whole quote: no verbatim block to reveal */
  const norm=s=>(s||'').toLowerCase().replace(/[^a-z]/g,'');
  const dupQuote=!sh&&norm(tweet)===norm(full);
  const rc=p.reactions?Object.keys(p.reactions).length:0;
  const showFollow=!ofN||ofN===1||nth===1;   /* one Follow per thread, not eight */
  d.innerHTML=`<div class="avatar">${avatarHTML(p.author)}</div>
  <div class="tweet-body">
    <div class="tweet-head"><button class="author" data-a="${p.author}">${p.author}</button>${v}<span class="h">${p.handle}</span><span class="t">${threadTag}</span>
    ${showFollow?`<button class="follow-btn">${followed.has(p.author)?'Following':'Follow'}</button>`:''}</div>
    <div class="tweet-text">${tweet}</div>
    ${dupQuote?'':`<div class="verbatim" hidden>${quoteHtml}</div>`}
    ${p.originalText?`<div class="orig"><b>Original (${p.originalLanguage}):</b> ${p.originalText}</div>`:''}
    ${p.location&&!/^[^A-Za-zÀ-Þ]/.test(p.location||'')&&!/[\d^*•]/.test(p.location||'')?`<div class="tweet-src">${p.location}</div>`:''}
    <div class="tweet-actions">
      ${dupQuote?'':'<button data-k="quote" aria-expanded="false">Verbatim</button>'}<button data-k="ctx" aria-expanded="false">Source &amp; context</button>${rc?`<button data-k="react" aria-expanded="false">Reactions (${rc})</button>`:''}${p.originalText?'<button data-k="orig" aria-expanded="false">French original</button>':''}<button data-k="share">Share</button><button data-k="link">Link</button><button data-k="card">Card</button><button data-k="save">${saved.has(p.id)?'Saved ✓':'Save'}</button>
    </div>
    <div class="ctx">${p.tweet?`<i>The tweet above is a modern paraphrase in his voice — the verbatim quote is under Verbatim.</i><br>`:''}<b>Source:</b> ${p.sourceTitle} (<a href="${p.sourceUrl}" target="_blank" rel="noopener">${p.archive}</a>)<br>${redact(sentencesOf(p.context||'').filter(s=>!NOTEISH.test(s)).join(' ')||'',spoiler)}${p.reactions?`<br><br>${Object.entries(p.reactions).map(([k,v])=>`— <i>${k}</i>: ${redact(v,spoiler)}`).join('<br>')}`:''}</div>
  </div>`;
  const ctx=d.querySelector('.ctx'),orig=d.querySelector('.orig'),verb=d.querySelector('.verbatim');
  const show=(el,btn,on)=>{if(!el)return;el.classList.toggle('show',on);el.hidden=!on;if(btn)btn.setAttribute('aria-expanded',String(on))};
  d.querySelectorAll('.tweet-actions button').forEach(b=>b.onclick=e=>{e.stopPropagation();const k=b.dataset.k;
    if(k==='quote')show(verb,b,!(verb.classList.contains('show')));
    if(k==='orig'&&orig)show(orig,b,!orig.classList.contains('show'));
    if(k==='ctx')show(ctx,b,!ctx.classList.contains('show'));
    if(k==='share'){const t=`${p.tweet||p.voice||voiceFor(p)||headlineFor(p)} — ${p.author}, ${p.date} via Chronicle`;navigator.clipboard?.writeText(t);b.textContent='Copied ✓';setTimeout(()=>b.textContent='Share',1200)}
    if(k==='link'){copyPostLink(p,b)}
    if(k==='card'){shareCard(p,b)}
    if(k==='save'){saved.has(p.id)?saved.delete(p.id):saved.add(p.id);saveSet();updateSavedCount();b.textContent=saved.has(p.id)?'Saved ✓':'Save'}});
  const more=d.querySelector('.more');
  if(more)more.onclick=e=>{e.stopPropagation();e.preventDefault();show(verb,d.querySelector('[data-k="quote"]'),true);const r=d.querySelector('.rest');if(r)r.hidden=false;more.hidden=true};
  const fb=d.querySelector('.follow-btn');
  if(fb)fb.onclick=e=>{e.stopPropagation();followed.has(p.author)?followed.delete(p.author):followed.add(p.author);saveFollow();render()};
  d.querySelector('.author').onclick=e=>{e.stopPropagation();openProfile(p.author)};
  d.onclick=()=>show(verb,d.querySelector('[data-k="quote"]'),!(verb.classList.contains('show')));
  return d;
}
async function openProfile(a){
  const meta=AUTHOR[a]||{};
  $('#profileModal').hidden=false;
  $('#profileCard').innerHTML=`<p class="gray">Loading ${a}…</p>`;
  for(const y of (meta.years||[cur.y]))await loadShard((INDEX.shardByYear||{})[String(y)]);
  const ps=POSTS.filter(p=>p.author===a).sort((x,y)=>x.date<y.date?-1:1);
  const f=(meta.factions||[]).join(' → ');
  $('#profileCard').innerHTML=`<div style="display:flex;gap:10px;align-items:center"><div class="avatar">${avatarHTML(a)}</div><div><h3 style="margin:0">${a}</h3><p class="gray" style="margin:0">${meta.handle||ps[0]?.handle||''} · ${f}</p></div></div>
  <p>${ps.length} Tweets in archive${meta.firstDate?` · ${meta.firstDate} → ${meta.lastDate}`:''}</p>
  <ul>${ps.slice(0,5).map(p=>`<li>${p.date} — ${p.displayText.slice(0,80)}…</li>`).join('')}</ul>
  <p><button id="fBtn" class="tweet-btn">${followed.has(a)?'Following':'Follow'}</button> <button id="cBtn">Close</button></p>`;
  $('#fBtn').onclick=()=>{followed.has(a)?followed.delete(a):followed.add(a);saveFollow();$('#profileModal').hidden=true;render()};
  $('#cBtn').onclick=()=>$('#profileModal').hidden=true;
}
/* ---- controls ---- */
function shiftDay(n){
  const d=new Date(iso(cur));d.setDate(d.getDate()+n);
  const r=INDEX?INDEX.appRange:{from:'1789-01-01',to:'1821-12-31'};
  const s=`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
  if(s<r.from||s>r.to)return;
  goTo({d:d.getDate(),m:d.getMonth()+1,y:d.getFullYear()});
  window.scrollTo(0,0);
}
$('#prevDay').onclick=()=>shiftDay(-1);
$('#nextDay').onclick=()=>shiftDay(1);
$('#backBtn').onclick=()=>{$('#app').hidden=true;$('#landing').style.display='flex'};
$('#replayBtn').onclick=()=>{replayOn=!replayOn;$('#replayBtn').textContent=replayOn?'Stop replay':'Replay day';render()};
$('#jumpBtn').onclick=()=>{const v=$('#jumpDate').value;if(v)goTo(parseIso(v))};
$('#jumpDate').onchange=()=>{$('#jumpDate').value&&goTo(parseIso($('#jumpDate').value))};
$('#profileModal').onclick=e=>{if(e.target.id==='profileModal')e.target.hidden=true};
document.addEventListener('keydown',e=>{
  const t=e.target.tagName;
  if(t==='INPUT'||t==='SELECT'||t==='TEXTAREA'||e.metaKey||e.ctrlKey)return;
  if($('#app').hidden)return;
  if(e.key==='ArrowLeft'){shiftDay(-1)}
  else if(e.key==='ArrowRight'){shiftDay(1)}
  else if(e.key==='Escape'){$('#profileModal').hidden=true}
  else if(e.key==='r'){$('#replayBtn').click()}
});
load();

/* ================= deep links, search, map, people, saved, theme ========= */
function esc(s){return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;')}
function foldAcc(s){return (s||'').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g,'')}
function setHead(t,s){$('#timelineTitle').textContent=t;$('#coverageNote').textContent=s||''}
function parseHash(h){
  let m=/^#\/d\/(\d{4})-(\d{2})-(\d{2})$/.exec(h||'');
  if(m)return{kind:'date',o:{y:+m[1],m:+m[2],d:+m[3]}};
  m=/^#\/p\/([\w-]+)$/.exec(h||'');
  if(m)return{kind:'post',id:m[1]};
  return null;
}
function syncHash(){
  try{
    if(typeof history==='undefined'||!history.replaceState)return;
    history.replaceState(null,'',view==='post'&&pendingFlash?'#/p/'+pendingFlash:'#/d/'+iso(cur));
  }catch(e){}
}
function flashPending(){
  if(!pendingFlash)return;
  const el=document.getElementById&&document.getElementById('p-'+pendingFlash);
  if(el){el.scrollIntoView({block:'center'});el.classList.add('flash');setTimeout(()=>el.classList.remove('flash'),2200)}
}
async function enterPost(id){$('#landing').style.display='none';$('#app').hidden=false;await goToPost(id);window.scrollTo(0,0)}
if(typeof window!=='undefined'&&window.addEventListener){
  window.addEventListener('hashchange',()=>{
    let nav=null;
    try{nav=parseHash(location.hash)}catch(e){}
    if(!nav||!ready)return;
    if(nav.kind==='date'&&nav.o&&iso(nav.o)!==iso(cur))goTo(nav.o);
    else if(nav.kind==='post')goToPost(nav.id);
  });
}
async function ensureAll(){await Promise.all((INDEX.shards||[]).map(s=>loadShard(s.id)))}
function snippet(p,n){return esc(((p.tweet||p.voice||p.displayText)||'').replace(/\s+/g,' ').slice(0,n||140))}
function rowHTML(p){
  return `<button class="srow" data-id="${p.id}"><b>${fmtDate(p.date)}</b>${p.location?` · ${esc(p.location)}`:''}<span>${snippet(p)}</span></button>`;
}
function wireRows(root,fn){
  root.querySelectorAll('.srow').forEach(b=>{b.onclick=()=>fn(b.dataset?b.dataset.id:b.getAttribute('data-id'))});
}
function backRow(label){return `<button class="backbtn" id="viewBack">‹ ${label||'Back'}</button>`}
/* ---- search ---- */
function matchQuery(p,toks){
  const hay=foldAcc([p.tweet,p.voice,p.displayText,p.sourceTitle,p.location].join(' '));
  return toks.every(t=>hay.includes(t));
}
let searchTimer=null;
function searchView(q){
  destroyMap();view='search';
  setHead('Search',POSTS.length+' documents loaded — type to search the whole archive');
  const feed=$('#feed');
  feed.innerHTML=`${backRow('Timeline')}<div class="searchbox"><input id="q" type="search" placeholder="Search letters, places, people…" value="${esc(q||'')}" aria-label="Search the archive"><div id="searchHint" class="gray">Loading every era for full-archive search…</div></div><div id="searchRes"></div>`;
  const back=$('#viewBack');if(back)back.onclick=()=>goTo(cur);
  const input=$('#q');
  const run=()=>{
    const toks=foldAcc(input.value).split(/\s+/).filter(Boolean);
    const box=$('#searchRes'),hint=$('#searchHint');
    if(!toks.length){box.innerHTML='';if(hint)hint.textContent='Type two or more characters — every word must match.';return}
    const res=POSTS.filter(p=>matchQuery(p,toks)).sort((a,b)=>a.date<b.date?-1:1);
    if(hint)hint.textContent=`${res.length} match${res.length===1?'':'es'}${res.length>60?' — showing the first 60, refine to narrow':''}`;
    box.innerHTML=res.slice(0,60).map(rowHTML).join('')||'<p class="gray">Nothing matches. Try fewer words.</p>';
    wireRows(box,goToPost);
  };
  input.oninput=()=>{clearTimeout(searchTimer);searchTimer=setTimeout(run,160)};
  ensureAll().then(()=>{const h=$('#searchHint');if(h)h.textContent='Type two or more characters — every word must match.';if(input.value)run()});
  if(q)run();
  input.focus&&input.focus();
}
/* ---- people (correspondent threads) ---- */
const PTITLES=new Set(['m','gen','general','marshal','mar','prince','princess','king','queen','emperor','admiral','cardinal','count','comte','duke','duchess','minister','ministre','citizen','sir','madame','monsieur','lord','lady','baron','baronne','archbishop','prefect','governor','commandant','major','colonel','captain','the','of','de','la','le','les','der','von','van','st','saint','hh','h','a','g','j','his','her','my','mme','at','in','on','to','for','with','from','by','near','until','till','before','after','between','against','into','over','under','toward','towards','around','off','out','via','per']);
const PERSON_ALIAS={joseph:'Joseph Bonaparte',josephbuonaparte:'Joseph Bonaparte',eugene:'Prince Eugène',davout:'Marshal Davout',davoust:'Marshal Davout',talleyrand:'Talleyrand',clarke:'General Clarke',champagny:'Champagny',maret:'M. Maret',berthier:'Berthier',carnot:'Carnot',josephine:'Josephine',empress:'The Empress',directory:'The Directory',pope:'The Pope',holyfather:'The Pope',murat:'Murat',granddukeofberg:'Murat',soult:'Marshal Soult',ney:'Marshal Ney',massena:'Masséna',augereau:'Augereau',lannes:'Lannes',macdonald:'Macdonald',marmont:'Marmont',victor:'Victor',mortier:'Mortier',moncey:'Moncey',suchet:'Suchet',bernadotte:'Bernadotte',alexander:'Emperor Alexander',francis:'Emperor Francis',selim:'Sultan Selim',louis:'King Louis',ferdinand:'Ferdinand VII',josephbonaparte:'Joseph Bonaparte',princeeugene:'Prince Eugène'};
function normalizeAddressee(st){
  const m=/^To\s+(.+?)(?:,|$)/i.exec(st||'');if(!m)return null;
  if(/\d/.test(m[1])||/[A-Z]{5,}/.test(m[1]))return null;
  const seg=m[1].replace(/\s+\b(at|in|near|nearby)\b.*$/i,'');
  if(/\d/.test(seg))return null;
  const words=(foldAcc(seg).match(/[a-z]+/g)||[]).filter(w=>!PTITLES.has(w));
  if(!words.length)return null;
  let key=words.join('');
  if(PERSON_ALIAS[key])key=PERSON_ALIAS[key].toLowerCase().replace(/[^a-z]/g,'');
  else if(PERSON_ALIAS[words.join('')])key=PERSON_ALIAS[words.join('')].toLowerCase().replace(/[^a-z]/g,'');
  return{key,raw:seg.trim().replace(/\.$/,'')};
}
function peopleView(){
  destroyMap();view='people';
  setHead('People','everyone Napoleon wrote to, most-written first');
  const feed=$('#feed');
  feed.innerHTML=`${backRow('Timeline')}<div id="peopleRes"><p class="gray">Gathering every era…</p></div>`;
  const back=$('#viewBack');if(back)back.onclick=()=>goTo(cur);
  ensureAll().then(()=>{
    const agg={};
    POSTS.forEach(p=>{
      const a=normalizeAddressee(p.sourceTitle);if(!a)return;
      const g=agg[a.key]=agg[a.key]||{label:a.raw,count:0,first:p.date,last:p.date,labels:{}};
      g.labels[a.raw]=(g.labels[a.raw]||0)+1;
      if(g.labels[a.raw]> (g.labels[g.label]||0))g.label=a.raw;
      g.count++;if(p.date<g.first)g.first=p.date;if(p.date>g.last)g.last=p.date;
    });
    const rows=Object.entries(agg).sort((a,b)=>b[1].count-a[1].count);
    setHead('People',rows.length+' correspondents · '+POSTS.length+' letters');
    const box=$('#peopleRes');if(!box)return;
    box.innerHTML=rows.map(([k,g])=>`<button class="srow prow" data-id="${esc(k)}"><span class="pava">${esc(g.label.trim()[0]||'?')}</span><b>${esc(g.label)}</b><span class="gray">${g.count} letter${g.count===1?'':'s'} · ${g.first} → ${g.last}</span></button>`).join('');
    box.querySelectorAll('.prow').forEach(b=>b.onclick=()=>personView(b.dataset?b.dataset.id:b.getAttribute('data-id')));
  });
}
function personView(key){
  destroyMap();
  const list=POSTS.filter(p=>{const a=normalizeAddressee(p.sourceTitle);return a&&a.key===key}).sort((a,b)=>a.date<b.date?-1:1);
  const name=list.length?(normalizeAddressee(list[0].sourceTitle)||{}).raw||key:key;
  view='person';setHead(name,list.length+' letters');
  const feed=$('#feed');
  feed.innerHTML=`${backRow('People')}<div>${list.map(rowHTML).join('')}</div>`;
  const back=$('#viewBack');if(back)back.onclick=()=>peopleView();
  wireRows(feed,goToPost);
}
/* ---- map ---- */
const PLACES={'paris':[48.85,2.35],'st. cloud':[48.84,2.22],'cairo':[30.04,31.24],'milan':[45.46,9.19],'fontainebleau':[48.4,2.7],'schonbrunn':[48.19,16.31],'dresden':[51.05,13.74],'bayonne':[43.49,-1.47],'nice':[43.7,7.27],'verona':[45.44,10.99],'finckenstein':[53.87,19.37],'warsaw':[52.23,21.01],'osterode':[53.7,20.0],'eylau':[54.4,20.63],'tilsit':[55.08,21.9],'albenga':[44.05,8.21],'acre':[32.93,35.08],'trianon':[48.8,2.11],'austerlitz':[49.13,16.76],'posen':[52.41,16.93],'montebello':[45.0,9.08],'alexandria':[31.2,29.92],'mayence':[50.0,8.27],'longwood':[-7.93,-14.41],'erfurt':[50.98,11.03],'boulogne':[50.73,1.61],'malmaison':[48.87,2.17],'la malmaison':[48.87,2.17],'munich':[48.14,11.58],'mantua':[45.16,10.8],'konigsberg':[54.71,20.45],'nogent':[48.49,3.5],'rheims':[49.26,4.03],'charleroi':[50.41,4.44],'strasbourg':[48.58,7.75],'compiegne':[49.42,2.83],'pont-de-briques':[50.68,1.61],'passariano':[45.95,13.0],'jaffa':[32.05,34.75],'portoferraio':[42.82,10.33],'berlin':[52.52,13.4],'carcare':[44.36,8.29],'tortona':[44.9,8.86],'brescia':[45.54,10.23],'mombello':[45.0,8.5],'damietta':[31.42,31.82],'giza':[30.01,31.21],'moscow':[55.76,37.62],'lyons':[45.76,4.84],'linz':[48.31,14.29],'benavente':[42.0,-5.68],'treves':[49.76,6.64],'peschiera':[45.44,10.69],'bologna':[44.49,11.34],'toulon':[43.12,5.93],'vitebsk':[55.19,30.2],'molodetchna':[54.32,26.85],'wurzen':[51.37,12.74],'bautzen':[51.18,14.43],'stolpen':[51.05,14.08],'frankfurt':[50.11,8.68],'troyes':[48.3,4.08],'nangis':[48.55,3.02],'fismes':[49.31,3.68],'soissons':[49.38,3.32],'sedan':[49.7,4.94],'calais':[50.95,1.86],'dunkirk':[51.04,2.38],'aix-la-chapelle':[50.78,6.08],'aix':[43.53,5.45],'lausanne':[46.52,6.63],'marengo':[44.88,8.68],'dusseldorf':[51.23,6.78],'nantes':[47.22,-1.55],'enns':[48.21,14.48],'wittenberg':[51.87,12.65],'dessau':[51.84,12.24],'jena':[50.93,11.59],'ludwigsburg':[48.9,9.19],'golymin':[52.81,20.87],'pultusk':[52.71,21.09],'smolensk':[54.78,32.05],'wilna':[54.69,25.28],'dorogobuzh':[54.92,33.3],'vienna':[48.21,16.37],'borodino':[55.52,35.82],'danzig':[54.35,18.65],'savona':[44.31,8.48],'genoa':[44.41,8.93],'venice':[45.44,12.34],'naples':[40.85,14.27],'turin':[45.07,7.69],'florence':[43.77,11.25],'lisbon':[38.72,-9.14],'copenhagen':[55.68,12.57],'stockholm':[59.33,18.07],'st petersburg':[59.94,30.31],'ulm':[48.4,10.0],'augsburg':[48.37,10.9],'ratisbon':[49.02,12.1],'wagram':[48.28,16.56],'rivoli':[45.57,10.77],'arcole':[45.35,11.28],'lodi':[45.31,9.5],'bassano':[45.77,11.73],'trento':[46.07,11.12],'klagenfurt':[46.63,14.31],'leoben':[47.38,15.09],'rastatt':[48.86,8.2],'malta':[35.9,14.4],'aboukir':[31.32,30.07],'gaza':[31.5,34.47],'el arish':[31.13,33.8],'suez':[29.97,32.55],'damascus':[33.51,36.29],'ajaccio':[41.92,8.74],'bastia':[42.7,9.45],'marseille':[43.3,5.37],'lyon':[45.76,4.84],'brest':[48.39,-4.48],'cherbourg':[49.64,-1.62],'antwerp':[51.22,4.4],'brussels':[50.85,4.35],'namur':[50.47,4.87],'frankfurt am main':[50.11,8.68],'nuremberg':[49.45,11.08],'stuttgart':[48.78,9.18],'cologne':[50.94,6.96],'leipzig':[51.34,12.38],'potsdam':[52.4,13.06],'stettin':[53.43,14.55],'danzig2':[0,0],'thorn':[53.01,18.61],'gorlitz':[51.15,14.99],'hanau':[50.13,8.92],'seville':[37.39,-5.99],'cadiz':[36.53,-6.29],'valladolid':[41.65,-4.72],'salamanca':[40.97,-5.66],'vitoria':[42.85,-2.67],'talavera':[39.96,-4.83],'badajoz':[38.88,-6.97],'ciudad rodrigo':[40.6,-6.53],'santarem':[39.24,-8.69],'oporto':[41.16,-8.63],'braunau':[48.26,13.03],'stettin2':[0,0],'elba':[42.78,10.28],'porto longone':[42.78,10.2],'livorno':[43.55,10.32],'piacenza':[45.05,9.7],'tolentino':[43.21,13.29],'forli':[44.22,12.04],'pesaro':[43.91,12.9],'gorizia':[45.94,13.62],'castiglione':[45.39,10.5],'marmirolo':[45.22,10.75],'carru':[44.48,7.87],'cherasco':[44.65,7.86],'plancy':[48.47,3.97],'stupinigi':[45.01,7.61],'la madone':[42.8,10.3],'porto-ferrajo':[42.82,10.33]};
const PALIAS={'saint cloud':'st. cloud','schoenbrunn':'schonbrunn','mainz':'mayence','reims':'rheims','erfurth':'erfurt','livorno':'livorno','leghorn':'livorno','st helena':'longwood','saint helena':'longwood','porto ferrajo':'portoferraio','porto-ferrajo':'portoferraio','porto ferraio':'portoferraio','trianon':'trianon'};
const NOVAGUE=new Set(['italy','headquarters','egypt','off malta','before acre','at sea','cloud.','france','europe','spain','germany','russia','prussia','austria','syria','poland']);
function placeKey(loc){
  if(!loc)return null;
  let k=foldAcc(loc.trim());
  if(!k||NOVAGUE.has(k))return null;
  if(PALIAS[k])k=PALIAS[k];
  return PLACES[k]?k:null;
}
function destroyMap(){if(typeof window!=='undefined'&&window.__napMap){try{window.__napMap.remove()}catch(e){}window.__napMap=null}}
function loadLeaflet(){
  try{if(typeof window!=='undefined'&&window.L)return Promise.resolve(true)}catch(e){}
  return new Promise(res=>{
    try{
      if(!document.head)return res(false);
      const s=document.createElement('script');
      s.src='https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
      s.onload=()=>res(true);s.onerror=()=>res(false);
      document.head.appendChild(s);
    }catch(e){res(false)}
  });
}
function mapView(){
  destroyMap();view='map';
  setHead('Map','where the letters were written');
  const feed=$('#feed');
  feed.innerHTML=`${backRow('Timeline')}<div id="map" role="application" aria-label="Map of letter origins"></div><div id="placeList"><p class="gray">Gathering every era…</p></div>`;
  const back=$('#viewBack');if(back)back.onclick=()=>goTo(cur);
  ensureAll().then(()=>{
    const agg={};
    POSTS.forEach(p=>{
      const k=placeKey(p.location);if(!k)return;
      const g=agg[k]=agg[k]||{count:0,latest:p.date,label:p.location};
      g.count++;if(p.date>g.latest)g.latest=p.date;
    });
    const rows=Object.entries(agg).sort((a,b)=>b[1].count-a[1].count);
    const box=$('#placeList');if(!box)return;
    box.innerHTML=rows.map(([k,g])=>`<button class="srow" data-id="${g.latest}"><b>${esc(g.label)}</b><span class="gray">${g.count} letter${g.count===1?'':'s'} · latest ${g.latest}</span></button>`).join('');
    box.querySelectorAll('.srow').forEach(b=>b.onclick=()=>goTo(parseIso(b.dataset?b.dataset.id:b.getAttribute('data-id'))));
    loadLeaflet().then(ok=>{
      const el=document.getElementById&&document.getElementById('map');
      if(!ok||!el||typeof window==='undefined'||!window.L){
        if(el)el.innerHTML='<p class="gray">Map tiles need a network connection — the place list below works offline.</p>';
        return;
      }
      const map=window.__napMap=window.L.map('map').setView([47,12],4);
      window.L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:18,attribution:'© OpenStreetMap'}).addTo(map);
      const pts=[];
      rows.forEach(([k,g])=>{
        const[la,lo]=PLACES[k];pts.push([la,lo]);
        const m=window.L.circleMarker([la,lo],{radius:4+Math.sqrt(g.count)*2.2,color:'#1b95e0',weight:2,fillColor:'#1b95e0',fillOpacity:0.45}).addTo(map);
        m.bindPopup(`<b>${esc(g.label)}</b><br>${g.count} letter${g.count===1?'':'s'}<br><button data-go="${g.latest}">Open latest →</button>`);
      });
      if(pts.length)map.fitBounds(window.L.latLngBounds(pts).pad(0.15));
      el.onclick=e=>{
        const t=e.target&&e.target.closest?e.target.closest('[data-go]'):null;
        if(t)goTo(parseIso(t.getAttribute('data-go')));
      };
    });
  });
}
/* ---- share cards ---- */
function wrapText(g,text,x,y,maxW,lh){
  const words=text.split(/\s+/);let line='',yy=y;
  for(const w of words){
    const t=line?line+' '+w:w;
    if(g.measureText(t).width>maxW&&line){g.fillText(line,x,yy);line=w;yy+=lh}else line=t;
  }
  if(line)g.fillText(line,x,yy);
  return yy;
}
function shareCard(p,b){
  const done=ok=>{if(b){b.textContent=ok?'Saved ✓':'Card';if(ok)setTimeout(()=>{b.textContent='Card'},1400)}};
  try{
    const W=1080,H=1350,cv=document.createElement('canvas');cv.width=W;cv.height=H;
    const g=cv.getContext('2d');if(!g){done(false);return}
    g.fillStyle='#fff';g.fillRect(0,0,W,H);
    g.fillStyle='#1b95e0';g.fillRect(0,0,W,16);
    g.fillStyle='#1b95e0';g.beginPath();g.arc(120,170,64,0,7);g.fill();
    g.fillStyle='#fff';g.font='700 64px Georgia,serif';g.textAlign='center';
    g.fillText((p.author||'N').trim()[0],120,192);
    g.textAlign='left';g.fillStyle='#14171a';g.font='700 44px Georgia,serif';
    g.fillText(p.author||'Napoleon Bonaparte',210,152);
    g.fillStyle='#657786';g.font='34px Georgia,serif';
    g.fillText((p.handle||'@bonaparte')+' · '+fmtDate(p.date),210,198);
    g.strokeStyle='#e6ecf0';g.lineWidth=2;g.beginPath();g.moveTo(96,262);g.lineTo(984,262);g.stroke();
    g.fillStyle='#14171a';g.font='40px Georgia,serif';
    let txt=(p.tweet||p.voice||'').replace(/\s+/g,' ').trim();
    if(txt.length>640)txt=txt.slice(0,640).rsplit(' ',1)[0]+'…';
    const yEnd=wrapText(g,txt,96,340,888,60);
    g.fillStyle='#657786';g.font='30px Georgia,serif';
    g.fillText((p.location?p.location+' · ':'')+fmtDate(p.date),96,Math.min(yEnd+70,1150));
    g.fillText(String(p.sourceTitle||'').slice(0,72),96,Math.min(yEnd+112,1192));
    g.textAlign='center';g.fillStyle='#657786';g.font='30px Georgia,serif';
    g.fillText('Chronicle — Napoleon',540,1290);
    cv.toBlob(blob=>{
      if(!blob){done(false);return}
      const file=typeof File!=='undefined'?new File([blob],'napoleon-'+p.date+'.png',{type:'image/png'}):null;
      if(file&&navigator.canShare&&navigator.canShare({files:[file]})){
        navigator.share({files:[file],title:'Napoleon — '+p.date}).then(()=>done(true),()=>done(false));
      }else{
        const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='napoleon-'+p.date+'.png';
        document.body.appendChild(a);a.click();setTimeout(()=>{URL.revokeObjectURL(a.href);a.remove()},4000);done(true);
      }
    },'image/png');
  }catch(e){done(false)}
}
function copyPostLink(p,b){
  let url='';
  try{url=location.origin+location.pathname+'#/p/'+p.id}catch(e){url='#/p/'+p.id}
  const done=()=>{if(b){b.textContent='Copied ✓';setTimeout(()=>b.textContent='Link',1200)}};
  if(navigator.clipboard&&navigator.clipboard.writeText)navigator.clipboard.writeText(url).then(done,done);
  else done();
}
/* ---- bookmarks ---- */
let saved=new Set([]);
try{saved=new Set(JSON.parse(localStorage.getItem('nap_saved')||'[]'))}catch(e){saved=new Set()}
function saveSet(){try{localStorage.setItem('nap_saved',JSON.stringify([...saved]))}catch(e){}}
function updateSavedCount(){const el=$('#savedCount');if(el)el.textContent=saved.size?` (${saved.size})`:''}
function savedView(){
  destroyMap();view='saved';
  setHead('Saved',saved.size?saved.size+' bookmarked':'nothing saved yet');
  const feed=$('#feed');
  feed.innerHTML=`${backRow('Timeline')}<div id="savedRes"></div>`;
  const back=$('#viewBack');if(back)back.onclick=()=>goTo(cur);
  if(!saved.size){const r=$('#savedRes');if(r)r.innerHTML='<p class="gray">Tap Save on any letter to keep it here.</p>';return}
  ensureAll().then(()=>{
    const list=POSTS.filter(p=>saved.has(p.id)).sort((a,b)=>a.date<b.date?-1:1);
    const box=$('#savedRes');if(!box)return;
    setHead('Saved',list.length+' bookmarked');
    box.innerHTML=list.map(rowHTML).join('')||'<p class="gray">Saved letters are in eras not loaded — this should not happen.</p>';
    wireRows(box,goToPost);
  });
}
/* ---- theme ---- */
function applyTheme(){
  let t='light';
  try{t=localStorage.getItem('nap_theme')||'light'}catch(e){}
  if(document.documentElement)document.documentElement.dataset.theme=t;
  const b=$('#btnTheme');if(b)b.textContent=t==='dark'?'☀️ Light':'🌙 Dark';
}
function wireExplore(){
  const w=(id,fn)=>{const el=$('#'+id);if(el)el.onclick=fn};
  w('btnSearch',()=>searchView());
  w('btnMap',()=>mapView());
  w('btnPeople',()=>peopleView());
  w('btnSaved',()=>savedView());
  w('btnTheme',()=>{
    let t='light';
    try{t=localStorage.getItem('nap_theme')||'light';t=t==='dark'?'light':'dark';localStorage.setItem('nap_theme',t)}catch(e){}
    applyTheme();
  });
}
wireExplore();
applyTheme();
updateSavedCount();
if(typeof window!=='undefined'&&window.addEventListener){
  window.addEventListener('hashchange',()=>{
    let nav=null;
    try{nav=parseHash(location.hash)}catch(e){}
    if(!nav||!ready)return;
    if(nav.kind==='date'&&nav.o&&iso(nav.o)!==iso(cur))goTo(nav.o);
    else if(nav.kind==='post')goToPost(nav.id);
  });
}
async function enterPost(id){$('#landing').style.display='none';$('#app').hidden=false;await goToPost(id);window.scrollTo(0,0)}
