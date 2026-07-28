from __future__ import annotations


def render_calibration_page() -> str:
    return r'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>投递决策人工校准</title>
<style>
:root{font-family:Inter,"PingFang SC","Microsoft YaHei",sans-serif;color:#0f172a;background:#f4f7fb}*{box-sizing:border-box}body{margin:0}.shell{max-width:1180px;margin:0 auto;padding:28px 20px 64px}.hero{padding:28px;border-radius:24px;background:linear-gradient(135deg,#0f766e,#0891b2);color:#fff;box-shadow:0 20px 60px rgba(15,118,110,.22)}.hero-top{display:flex;justify-content:space-between;gap:20px;align-items:flex-start}.eyebrow{font-size:13px;font-weight:800;letter-spacing:.08em;opacity:.82}.hero h1{margin:8px 0 10px;font-size:34px}.hero p{margin:0;max-width:760px;line-height:1.75;opacity:.94}.nav{display:flex;gap:9px;flex-wrap:wrap}.nav a,.nav button{border:1px solid rgba(255,255,255,.45);background:rgba(255,255,255,.12);color:#fff;border-radius:12px;padding:10px 14px;text-decoration:none;font-weight:700;cursor:pointer}.pair{margin-top:18px;display:none;gap:12px;padding:16px;border:1px solid #fed7aa;background:#fff7ed;border-radius:16px;color:#9a3412}.pair.show{display:flex}.pair input{flex:1;min-width:180px;border:1px solid #fdba74;border-radius:10px;padding:10px 12px}.pair button{border:0;border-radius:10px;padding:10px 14px;background:#ea580c;color:#fff;font-weight:800;cursor:pointer}.metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:20px 0}.metric{background:#fff;border:1px solid #e2e8f0;border-radius:18px;padding:18px;box-shadow:0 8px 24px rgba(15,23,42,.05)}.metric span{display:block;color:#64748b;font-size:13px;font-weight:700}.metric strong{display:block;margin-top:8px;font-size:28px}.notice{background:#ecfeff;border:1px solid #a5f3fc;color:#155e75;border-radius:16px;padding:15px 18px;line-height:1.7;margin-bottom:18px}.toolbar{display:flex;justify-content:space-between;align-items:center;gap:12px;margin:20px 0}.toolbar h2{margin:0}.toolbar-actions{display:flex;gap:10px;flex-wrap:wrap}.btn{border:1px solid #cbd5e1;background:#fff;color:#0f172a;border-radius:11px;padding:10px 14px;font-weight:800;cursor:pointer}.btn.primary{background:#0f766e;border-color:#0f766e;color:#fff}.btn.danger{color:#b91c1c}.cards{display:grid;gap:18px}.card{background:#fff;border:1px solid #e2e8f0;border-radius:22px;overflow:hidden;box-shadow:0 12px 30px rgba(15,23,42,.06)}.card-head{display:flex;justify-content:space-between;gap:20px;padding:20px 22px;border-bottom:1px solid #e2e8f0}.order{width:40px;height:40px;display:grid;place-items:center;border-radius:12px;background:#ccfbf1;color:#115e59;font-size:18px;font-weight:900;flex:none}.title-wrap{flex:1}.title{font-size:20px;font-weight:900}.company{margin-top:6px;color:#475569}.meta{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}.tag{font-size:12px;padding:5px 9px;border-radius:999px;background:#f1f5f9;color:#334155;font-weight:700}.tag.warn{background:#fff7ed;color:#9a3412}.tag.good{background:#ecfdf5;color:#047857}.sample-reason{max-width:330px;padding:12px 14px;border-radius:14px;background:#f8fafc;color:#475569;line-height:1.6;font-size:13px}.card-body{display:grid;grid-template-columns:1.2fr .8fr;gap:22px;padding:22px}.excerpt{white-space:pre-wrap;line-height:1.75;color:#334155;max-height:250px;overflow:auto}.section-title{font-size:13px;text-transform:uppercase;letter-spacing:.06em;color:#64748b;font-weight:900;margin-bottom:9px}.chips{display:flex;gap:7px;flex-wrap:wrap}.chip{font-size:12px;border-radius:999px;padding:6px 9px;background:#eef2ff;color:#3730a3}.chip.gap{background:#fff1f2;color:#be123c}.chip.conflict{background:#fef2f2;color:#b91c1c}.chip.missing{background:#fffbeb;color:#a16207}.empty{color:#94a3b8}.label-panel{border-top:1px solid #e2e8f0;padding:20px 22px;background:#fbfdff}.groups{display:grid;grid-template-columns:repeat(4,1fr);gap:9px}.group-btn{border:1px solid #cbd5e1;background:#fff;border-radius:12px;padding:12px 8px;font-weight:800;cursor:pointer}.group-btn.active{border-color:#0f766e;background:#ccfbf1;color:#115e59}.reason{width:100%;min-height:84px;margin-top:12px;border:1px solid #cbd5e1;border-radius:12px;padding:12px;resize:vertical;font:inherit}.save-row{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-top:12px}.status{font-size:13px;color:#64748b}.status.ok{color:#047857}.status.error{color:#b91c1c}.loading{padding:48px;text-align:center;color:#64748b}.complete{padding:20px;border-radius:18px;background:#ecfdf5;border:1px solid #a7f3d0;color:#065f46;margin-top:18px;font-weight:800;display:none}.complete.show{display:block}@media(max-width:860px){.metrics{grid-template-columns:repeat(2,1fr)}.card-body{grid-template-columns:1fr}.groups{grid-template-columns:repeat(2,1fr)}.hero-top{display:block}.nav{margin-top:18px}}@media(max-width:520px){.metrics{grid-template-columns:1fr}.card-head{flex-direction:column}.groups{grid-template-columns:1fr}.shell{padding:16px 12px 48px}}
</style>
</head>
<body>
<div class="shell">
  <section class="hero">
    <div class="hero-top">
      <div>
        <div class="eyebrow">PHASE 8.2A · HUMAN CALIBRATION</div>
        <h1>投递决策人工校准</h1>
        <p>系统从本地岗位中挑选10个具有代表性的样本。你只需要给出真实的投递分组和一句理由，后续评分引擎将用这组人工基准检查规则是否符合你的判断。</p>
      </div>
      <div class="nav">
        <a href="/profile">个人档案</a>
        <a href="/manage">岗位管理</a>
        <a href="/dashboard">市场看板</a>
      </div>
    </div>
  </section>

  <section id="pair" class="pair">
    <input id="token" type="password" placeholder="粘贴首次启动页提供的本地 API 令牌">
    <button id="save-token">保存并连接</button>
  </section>

  <section class="metrics">
    <article class="metric"><span>代表岗位</span><strong id="sample-count">—</strong></article>
    <article class="metric"><span>已完成标注</span><strong id="labeled-count">—</strong></article>
    <article class="metric"><span>剩余</span><strong id="remaining-count">—</strong></article>
    <article class="metric"><span>候选岗位池</span><strong id="candidate-count">—</strong></article>
  </section>

  <div class="notice"><strong>说明：</strong>页面中的“匹配代理值”和“机会代理值”只用于挑选不同类型的样本，不是最终投递评分。真正的Phase 8.2B评分会在你完成人工标注后单独设计和校准。</div>

  <div class="toolbar">
    <h2>代表性岗位样本</h2>
    <div class="toolbar-actions">
      <button id="reload" class="btn">重新读取</button>
      <button id="refresh-sample" class="btn danger">重新抽取样本</button>
    </div>
  </div>

  <main id="cards" class="cards"><div class="loading">正在读取本地岗位和个人档案……</div></main>
  <div id="complete" class="complete">10个代表岗位已经全部完成标注，可以进入Phase 8.2B评分引擎开发。</div>
</div>
<script>
(()=>{'use strict';
const TOKEN_KEY='jobMarketApiTokenV1';
const GROUPS={apply_now:'立即投递',stretch:'值得冲刺',prepare_first:'补材料后投递',defer:'暂缓'};
const $=selector=>document.querySelector(selector);
const esc=value=>String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
let token=localStorage.getItem(TOKEN_KEY)||'';
let current=null;

function headers(){return {'Content-Type':'application/json','X-Job-Market-Token':token};}
async function request(path,options={}){const response=await fetch(path,{...options,headers:{...headers(),...(options.headers||{})}});if(response.status===401){$('#pair').classList.add('show');throw new Error('请先保存本地API令牌。');}const data=await response.json().catch(()=>({}));if(!response.ok)throw new Error(data.detail||`请求失败：${response.status}`);return data;}
function chips(items,className=''){if(!items||!items.length)return '<span class="empty">无</span>';return `<div class="chips">${items.map(item=>`<span class="chip ${className}">${esc(item)}</span>`).join('')}</div>`;}
function labelPanel(item){const label=item.label||{};return `<div class="label-panel" data-job-id="${esc(item.job_id)}"><div class="section-title">你的人工判断</div><div class="groups">${Object.entries(GROUPS).map(([key,text])=>`<button class="group-btn ${label.action_group===key?'active':''}" data-group="${key}">${text}</button>`).join('')}</div><textarea class="reason" placeholder="写一句真实理由，例如：方向非常匹配，项目证据足够，今天直接投递。">${esc(label.reason||'')}</textarea><div class="save-row"><span class="status">${label.action_group?'已保存，可继续修改':'请选择分组并填写理由'}</span><button class="btn primary save-label">保存判断</button></div></div>`;}
function card(item){const m=item.metrics||{};const meta=[item.city,item.salary,item.education,item.experience,item.internship_days_per_week,item.internship_duration].filter(Boolean);return `<article class="card"><div class="card-head"><div class="order">${item.sample_order}</div><div class="title-wrap"><div class="title">${esc(item.job_title||'未命名岗位')}</div><div class="company">${esc(item.company_name||'公司信息缺失')}</div><div class="meta">${meta.map(value=>`<span class="tag">${esc(value)}</span>`).join('')}<span class="tag good">${esc(m.direction||'其他')}</span>${m.listing_status!=='active'?`<span class="tag warn">招聘状态：${esc(m.listing_status)}</span>`:''}</div></div><div class="sample-reason"><strong>入选原因</strong><br>${esc(item.selection_reason)}</div></div><div class="card-body"><div><div class="section-title">岗位描述摘录</div><div class="excerpt">${esc(item.description_excerpt||'岗位描述缺失')}</div>${item.source_url?`<p><a href="${esc(item.source_url)}" target="_blank" rel="noreferrer">打开原始岗位</a></p>`:''}</div><div><div class="section-title">岗位技能</div>${chips(m.required_skills)}<div class="section-title" style="margin-top:16px">已匹配</div>${chips(m.matched_skills)}<div class="section-title" style="margin-top:16px">技能缺口</div>${chips(m.skill_gaps,'gap')}<div class="section-title" style="margin-top:16px">硬条件冲突</div>${chips(m.hard_conflicts,'conflict')}<div class="section-title" style="margin-top:16px">信息缺失</div>${chips(m.missing_fields,'missing')}<div class="meta" style="margin-top:18px"><span class="tag">匹配代理 ${(Number(m.match_proxy||0)*100).toFixed(0)}</span><span class="tag">机会代理 ${(Number(m.opportunity_proxy||0)*100).toFixed(0)}</span><span class="tag">项目证据 ${Number(m.project_evidence_count||0)}</span></div></div></div>${labelPanel(item)}</article>`;}
function bindCards(){document.querySelectorAll('.label-panel').forEach(panel=>{panel.querySelectorAll('.group-btn').forEach(button=>button.addEventListener('click',()=>{panel.querySelectorAll('.group-btn').forEach(item=>item.classList.remove('active'));button.classList.add('active');}));panel.querySelector('.save-label').addEventListener('click',async()=>{const active=panel.querySelector('.group-btn.active');const reason=panel.querySelector('.reason').value.trim();const status=panel.querySelector('.status');if(!active){status.textContent='请先选择一个投递分组。';status.className='status error';return;}if(!reason){status.textContent='请写一句人工判断理由。';status.className='status error';return;}status.textContent='保存中……';status.className='status';try{await request(`/api/v1/calibration/labels/${encodeURIComponent(panel.dataset.jobId)}`,{method:'PUT',body:JSON.stringify({action_group:active.dataset.group,reason})});status.textContent='已保存';status.className='status ok';await load(false);}catch(error){status.textContent=error.message;status.className='status error';}});});}
async function load(refresh=false){$('#cards').innerHTML='<div class="loading">正在读取本地岗位和个人档案……</div>';try{current=refresh?await request('/api/v1/calibration/representatives/refresh',{method:'POST'}):await request('/api/v1/calibration/representatives');$('#sample-count').textContent=current.sample_count;$('#labeled-count').textContent=current.labeled_count;$('#remaining-count').textContent=Math.max(0,current.sample_count-current.labeled_count);$('#candidate-count').textContent=current.total_candidates;$('#cards').innerHTML=current.items.length?current.items.map(card).join(''):'<div class="loading">当前没有可用于校准的岗位。请先采集岗位并完善个人档案。</div>';$('#complete').classList.toggle('show',Boolean(current.complete));bindCards();}catch(error){$('#cards').innerHTML=`<div class="loading">${esc(error.message)}</div>`;}}
$('#save-token').addEventListener('click',()=>{const value=$('#token').value.trim();if(!value)return;token=value;localStorage.setItem(TOKEN_KEY,value);$('#pair').classList.remove('show');load(false);});
$('#reload').addEventListener('click',()=>load(false));
$('#refresh-sample').addEventListener('click',()=>{if(confirm('重新抽取会替换当前10个代表样本，但已经保存的岗位标注仍会保留。继续吗？'))load(true);});
if(!token){$('#pair').classList.add('show');}else{load(false);}
})();
</script>
</body>
</html>'''


# PHASE_82A_CALIBRATION_UI
