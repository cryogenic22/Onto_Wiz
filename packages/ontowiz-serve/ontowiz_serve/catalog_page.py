"""The served Domain Intelligence Catalog page (Tier A).

A single self-contained HTML page that renders the catalog from the *live* REST
API (``/v1/catalog``, ``/search``, ``/functions``, ``/artifacts/{id}``) — the
real, data-backed counterpart to the ``vision/DOMAIN_INTELLIGENCE_CATALOG.html``
mock. No business logic here; it is a thin browser client over the runtime.
"""

from __future__ import annotations

_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>OntoWiz · Domain Intelligence Catalog</title>
<style>
 :root{--bg:#06080f;--panel:#0e1322;--panel2:#131a2e;--line:#1d2740;--line2:#2a3858;
  --ink:#eef2fb;--ink2:#c3ccdf;--mut:#8a96b4;--teal:#2dd4bf;--blue:#5b9dff;--violet:#a78bfa;--green:#46d18a;
  --grad:linear-gradient(100deg,#2dd4bf,#5b9dff 45%,#a78bfa)}
 *{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
  font:15px/1.5 Inter,"Segoe UI",system-ui,sans-serif}
 .wrap{max-width:1180px;margin:0 auto;padding:0 24px}
 nav{position:sticky;top:0;background:rgba(6,8,15,.8);backdrop-filter:blur(12px);border-bottom:1px solid var(--line)}
 nav .wrap{display:flex;align-items:center;gap:14px;height:60px}
 .logo{width:24px;height:24px;border-radius:7px;background:var(--grad)}
 .brand{font-weight:700}.brand small{color:var(--mut);font-weight:500}
 .role{margin-left:auto;background:var(--panel2);color:var(--ink);border:1px solid var(--line2);
  border-radius:9px;padding:6px 10px;font:inherit;font-size:13px}
 h1{font-size:34px;letter-spacing:-.02em;margin:.4em 0 .1em}
 h1 .g{background:var(--grad);-webkit-background-clip:text;background-clip:text;color:transparent}
 .lede{color:var(--ink2);max-width:680px}
 .search{display:flex;gap:10px;margin:20px 0;background:var(--panel2);border:1px solid var(--line2);
  border-radius:12px;padding:11px 14px}
 .search input{flex:1;background:transparent;border:0;outline:0;color:var(--ink);font:inherit}
 .grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
 @media(max-width:900px){.grid{grid-template-columns:1fr}}
 .card{background:linear-gradient(180deg,var(--panel),var(--bg));border:1px solid var(--line);
  border-radius:18px;padding:18px;cursor:pointer;transition:.16s}
 .card:hover{transform:translateY(-3px);border-color:var(--line2);box-shadow:0 24px 50px -28px #000}
 .ver{color:var(--teal);font-size:12.5px;font-weight:650}
 .desc{color:var(--mut);font-size:13.5px;min-height:34px}
 .tags{display:flex;flex-wrap:wrap;gap:6px;margin-top:12px}
 .tg{font-size:11px;padding:3px 9px;border-radius:999px;border:1px solid var(--line2);color:var(--ink2)}
 .foot{display:flex;gap:12px;margin-top:12px;color:var(--mut);font-size:12px}
 .foot b{color:var(--ink2)}
 .back{color:var(--mut);cursor:pointer;font-weight:600;display:inline-block;margin:6px 0 14px}
 .panel{background:linear-gradient(180deg,var(--panel),var(--bg));border:1px solid var(--line);
  border-radius:18px;padding:18px;margin-top:14px}
 .slice{display:inline-block;padding:7px 12px;border:1px solid var(--line2);border-radius:10px;margin:4px 6px 4px 0;
  cursor:pointer;font-size:13px;color:var(--ink2)}.slice.on{background:var(--panel2);color:var(--ink)}
 .arow{display:flex;gap:10px;align-items:center;padding:10px 12px;border:1px solid var(--line);border-radius:10px;
  margin-bottom:7px;cursor:pointer;background:var(--bg)}.arow:hover{border-color:var(--line2)}
 .pill{font-size:10.5px;padding:2px 8px;border-radius:999px;margin-left:auto}
 .ok{color:var(--green);border:1px solid #46d18a59}.no{color:var(--mut);border:1px solid var(--line2)}
 pre{background:#05070d;border:1px solid var(--line);border-radius:10px;padding:12px;overflow:auto;font-size:12.5px;color:var(--ink2)}
 .scrim{position:fixed;inset:0;background:#03050baa;display:none}.scrim.on{display:block}
 .drawer{position:fixed;top:0;right:0;height:100%;width:min(540px,94vw);background:#0a0e1a;
  border-left:1px solid var(--line2);transform:translateX(100%);transition:.25s;overflow:auto;padding:22px}
 .drawer.on{transform:none}.x{float:right;cursor:pointer;color:var(--mut)}
 .verdict{background:linear-gradient(120deg,#2dd4bf28,#5b9dff20);border:1px solid var(--line2);border-radius:10px;padding:12px}
 .muted{color:var(--mut);font-size:12.5px}
</style></head>
<body>
<nav><div class="wrap"><span class="logo"></span>
 <span class="brand">OntoWiz <small>· Domain Intelligence Catalog</small></span>
 <select class="role" id="role">
  <option value="sme">SME</option><option value="curator">Curator</option>
  <option value="builder">Builder</option><option value="manager">Manager</option></select>
</div></nav>
<div class="wrap">
 <h1>Inside a governed <span class="g">domain brain.</span></h1>
 <p class="lede">Every pack of your firm's judgment — searchable, versioned, eval-proven and governed.
  Served live from the registry.</p>
 <div class="search"><input id="q" placeholder="Search packs, functions, heuristics…"/></div>
 <div id="grid" class="grid"></div>
 <div id="detail" style="display:none"></div>
</div>
<div class="scrim" id="scrim"></div><aside class="drawer" id="drawer"></aside>
<script>
const $=s=>document.querySelector(s);
let CUR=null, SLICE="all";
async function jget(u){const r=await fetch(u);return r.ok?r.json():null;}
function fnTags(fns){return Object.entries(fns||{}).map(([k,v])=>`<span class="tg">${k} · ${v}</span>`).join("");}
async function loadGrid(q=""){
 const data = q ? await jget('/v1/catalog/search?q='+encodeURIComponent(q)) : await jget('/v1/catalog');
 const grid=$("#grid"); $("#detail").style.display="none"; grid.style.display="grid"; grid.innerHTML="";
 (data||[]).forEach(e=>{
  const name=e.name, ver=e.latest_version||"", fns=e.functions||{};
  const el=document.createElement("div"); el.className="card"; el.onclick=()=>openPack(name,ver);
  el.innerHTML=`<div class="ver">${e.domain||""}</div><h3 style="margin:.2em 0">${name} <span class="muted">v${ver}</span></h3>
   <p class="desc">${e.description||""}</p><div class="tags">${fnTags(fns)}</div>
   <div class="foot"><span><b>${e.artifact_count!=null?e.artifact_count:(e.score||"")}</b> ${e.artifact_count!=null?"artifacts":"score"}</span>
   ${e.agent_lift!=null?`<span>lift <b>+${e.agent_lift}</b></span>`:""}${e.signed?'<span style="color:var(--green)">● sealed</span>':''}</div>`;
  grid.appendChild(el);
 });
 if(!grid.children.length) grid.innerHTML='<p class="muted">No packs match.</p>';
}
async function openPack(name,ver){
 CUR={name,ver}; SLICE="all";
 const [funcs,detail]=await Promise.all([
   jget(`/v1/packs/${name}/${ver}/functions`), jget(`/v1/packs/${name}/${ver}/detail`)]);
 $("#grid").style.display="none"; const d=$("#detail"); d.style.display="block";
 d.innerHTML=`<span class="back" onclick="loadGrid($('#q').value)">← Back to catalog</span>
  <h1 style="font-size:26px">${name} <span class="muted">v${ver}</span></h1>
  <div class="panel"><b>Function slices</b><div id="slices" style="margin-top:8px"></div>
   <p class="muted" id="slicenote"></p></div>
  <div class="panel"><b>Artifacts</b><div id="arts" style="margin-top:10px"></div></div>`;
 window._funcs=funcs||[]; window._rows=(detail&&detail.artifacts)||[];
 renderSlices(); renderArts();
}
function renderSlices(){
 const wrap=$("#slices");
 const all=`<span class="slice ${SLICE==='all'?'on':''}" data-s="all">Full pack · ${window._rows.length}</span>`;
 wrap.innerHTML=all+(window._funcs).map(s=>
   `<span class="slice ${SLICE===s.function?'on':''}" data-s="${s.function}">${s.function} · ${s.count}</span>`).join("");
 wrap.querySelectorAll(".slice").forEach(el=>el.onclick=()=>{SLICE=el.dataset.s;renderSlices();renderArts();
  const s=window._funcs.find(f=>f.function===SLICE);
  $("#slicenote").textContent=s?`Serving this slice ≈ ${s.slice_tokens} tokens vs ${s.full_tokens} for the full pack.`:"";});
}
async function fnOf(id){const v=await jget(`/v1/packs/${CUR.name}/${CUR.ver}/artifacts/${id}`);return v;}
function renderArts(){
 // function membership comes from the live artifact view; filter client-side via tags we already know
 const rows=window._rows;
 const wrap=$("#arts"); wrap.innerHTML="";
 rows.forEach(r=>{
  const el=document.createElement("div"); el.className="arow"; el.dataset.id=r.id; el.dataset.fn="";
  el.onclick=()=>openArt(r.id);
  el.innerHTML=`<span><b>${r.name}</b><div class="muted">${r.id} · ${r.kind}</div></span>
   <span class="pill ${r.served?'ok':'no'}">${r.served?'served':'gated'}</span>`;
  wrap.appendChild(el);
 });
 if(SLICE!=='all') filterBySlice();
}
async function filterBySlice(){
 // ask the artifact view for each row's function lazily, then hide non-matching
 const rows=[...$("#arts").children];
 for(const el of rows){
  const v=await fnOf(el.dataset.id);
  if(!v||v.function!==SLICE) el.style.display="none"; else el.style.display="flex";
 }
}
async function openArt(id){
 const v=await fnOf(id); if(!v) return;
 $("#drawer").innerHTML=`<span class="x" onclick="closeD()">✕</span>
  <div class="muted">${v.id}</div><h2 style="margin:.2em 0">${v.name}</h2>
  <div class="tags">${(v.tags||[]).map(t=>`<span class="tg">${t.dimension}:${t.value}</span>`).join("")}</div>
  <p style="margin-top:14px"><b>Concludes</b></p><div class="verdict">${v.summary||""}</div>
  ${(v.anti_patterns||[]).map(a=>`<p class="muted" style="border-left:3px solid #ff6b81;padding-left:10px">
    <b>Not →</b> ${a.wrong_conclusion}. ${a.why_wrong}</p>`).join("")}
  <p style="margin-top:14px"><b>Governance</b></p>
  ${(v.governance||[]).map(g=>`<div class="muted">→ ${g.to_state} by ${g.changed_by} ${g.delta_id?('· '+g.delta_id):''}</div>`).join("")}
  <p style="margin-top:14px"><b>YAML</b></p><pre>${(v.yaml||"").replace(/</g,"&lt;")}</pre>
  <p style="margin-top:14px"><b>Discussion</b> <span class="muted" id="cc"></span></p>
  <div id="cmts"></div>
  <div style="display:flex;gap:8px;margin-top:10px"><input id="cin" class="role" style="flex:1"
    placeholder="Comment as ${$('#role').value}…"/><button class="slice" onclick="postC('${id}')">Post</button></div>`;
 $("#scrim").classList.add("on"); $("#drawer").classList.add("on"); loadC(id);
}
async function loadC(id){
 const c=await jget(`/v1/packs/${CUR.name}/${CUR.ver}/artifacts/${id}/comments`);
 const box=$("#cmts"); if(!box) return;
 box.innerHTML=(c||[]).map(x=>`<div class="muted" style="margin-top:8px"><b>${x.author}</b>
   <span class="tg">${x.role}</span> — ${x.text}</div>`).join("")||'<p class="muted">No comments yet.</p>';
 const cc=$("#cc"); if(cc) cc.textContent=`· ${(c||[]).length}`;
}
async function postC(id){
 const t=$("#cin").value.trim(); if(!t) return;
 await fetch(`/v1/packs/${CUR.name}/${CUR.ver}/artifacts/${id}/comments`,{method:"POST",
   headers:{"Content-Type":"application/json","X-OntoWiz-Role":$('#role').value},
   body:JSON.stringify({author:"You",text:t})}); $("#cin").value=""; loadC(id);
}
function closeD(){$("#scrim").classList.remove("on");$("#drawer").classList.remove("on");}
$("#scrim").onclick=closeD;
$("#q").oninput=e=>loadGrid(e.target.value);
loadGrid();
</script>
</body></html>
"""


def catalog_html() -> str:
    """Return the self-contained catalog page (served at ``/``)."""
    return _PAGE
