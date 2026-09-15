/* Chronicle — Napoleon. Manifest-driven: data/index.json lists the era shards,
   the app fetches only the era it needs and reports any archive failure loudly. */
let POSTS=[], EVENTS=[], INDEX=null;
let AUTHOR={}, AVATAR={};
let cur={d:12,m:4,y:1796};
let followed=new Set(JSON.parse(localStorage.getItem('nap_follow')||'[]'));
let replayOn=false, ready=false, DEFAULT=null;
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
  j.value=iso(cur);
  initLanding();
  ready=true;btn.disabled=false;btn.textContent='Enter timeline';
  $('#timelineTitle').textContent='Latest Tweets';
  $('#landingNote').textContent=`${INDEX.counts.posts} documents · ${INDEX.counts.dates} dated days · ${INDEX.counts.authors} voices`;
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
async function goTo(o){
  cur=o;
  $('#jumpDate').value=iso(cur);
  showBanner(EVENTS.find(e=>e.date===iso(cur))||null);
  if(ready)await ensureDate();
  render();
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
  const target=iso(cur),mode=$('#followFilter').value,spoiler=$('#spoilerToggle').checked;
  let list=POSTS.filter(p=>p.date===target);
  list.sort((a,b)=>(ORDER[a.timeLabel]??3)-(ORDER[b.timeLabel]??3)||(a.id<b.id?-1:1));
  if(mode==='following')list=list.filter(p=>followed.has(p.author));
  return {list,target,spoiler};
}
function redact(t,on){if(!on)return t;return t.replace(/guillotin\w*|execut\w*|behead\w*|massacr\w*/gi,'████')}
function render(){
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
function card(p,spoiler,nth,ofN){
  const d=document.createElement('article');d.className='post'+(ofN>1?' in-thread':'');
  const v=p.accountType==='person'?'<span class="verified">✔</span>':'';
  const threadTag=ofN>1?`<span class="tag"> · 🧵 ${nth}/${ofN}</span>`:'';
  const evs=[p.evidenceType,p.dateCertainty==='approximate'?'DATE APPROXIMATE':'',(p.originalLanguage!=='English'&&p.evidenceType!=='TRANSLATION')?'TRANSLATION':''].filter(Boolean).map(e=>`<span class="ev">${EV_SHORT[e]||e.toLowerCase()}</span>`).join('');
  const full=redact(p.displayText,spoiler),sh=shortHTML(p.displayText);
  const txtHtml=sh?`“${redact(sh.cut,spoiler)}… <a href="#" class="more">Show more</a><span class="rest" hidden> ${redact(sh.rest,spoiler)}</span>”`:full;
  const rc=p.reactions?Object.keys(p.reactions).length:0;
  d.innerHTML=`<div class="avatar">${avatarHTML(p.author)}</div>
  <div class="tweet-body">
    <div class="tweet-head"><button class="author" data-a="${p.author}">${p.author}</button>${v}<span class="h">${p.handle}</span><span class="t">· ${p.timeLabel.toLowerCase()}${threadTag}</span>
    <button class="follow-btn">${followed.has(p.author)?'Following':'Follow'}</button></div>
    <div class="tweet-text">${txtHtml}</div>
    <div class="tweet-meta">${p.sourceTitle}</div>
    ${p.originalText?`<div class="orig"><b>Original (${p.originalLanguage}):</b> ${p.originalText}</div>`:''}
    <div class="tweet-src">${p.location}${evs?' · '+evs:''}</div>
    <div class="tweet-actions">
      <button data-k="ctx" aria-expanded="false">Source &amp; context</button>${rc?`<button data-k="react" aria-expanded="false">Reactions (${rc})</button>`:''}${p.originalText?'<button data-k="orig" aria-expanded="false">French original</button>':''}<button data-k="share">Share</button>
    </div>
    <div class="ctx"><b>Source:</b> ${p.sourceTitle} (<a href="${p.sourceUrl}" target="_blank" rel="noopener">${p.archive}</a>)<br>${redact(p.context||'',spoiler)}${p.reactions?`<br><br>${Object.entries(p.reactions).map(([k,v])=>`— <i>${k}</i>: ${redact(v,spoiler)}`).join('<br>')}`:''}</div>
  </div>`;
  const ctx=d.querySelector('.ctx'),orig=d.querySelector('.orig'),more=d.querySelector('.more');
  const show=(el,btn,on)=>{el.classList.toggle('show',on);if(btn)btn.setAttribute('aria-expanded',String(on))};
  if(more)more.onclick=e=>{e.stopPropagation();const r=d.querySelector('.rest');const open=r.hidden;r.hidden=!open;more.textContent=open?'Show less':'Show more'};
  d.querySelectorAll('.tweet-actions button').forEach(b=>b.onclick=e=>{e.stopPropagation();const k=b.dataset.k;
    if(k==='orig'&&orig)show(orig,b,!orig.classList.contains('show'));
    if(k==='ctx'||k==='react')show(ctx,b,!ctx.classList.contains('show'));
    if(k==='share'){const t=`"${p.displayText}" — ${p.author}, ${p.date} via Chronicle`;navigator.clipboard?.writeText(t);b.textContent='Copied ✓';setTimeout(()=>b.textContent='Share',1200)}});
  d.querySelector('.follow-btn').onclick=e=>{e.stopPropagation();followed.has(p.author)?followed.delete(p.author):followed.add(p.author);saveFollow();render()};
  d.querySelector('.author').onclick=e=>{e.stopPropagation();openProfile(p.author)};
  d.onclick=()=>show(ctx,null,!ctx.classList.contains('show'));
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
$('#spoilerToggle').onchange=render;$('#followFilter').onchange=render;
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
  else if(e.key==='s'){$('#spoilerToggle').checked=!$('#spoilerToggle').checked;render()}
});
load();
