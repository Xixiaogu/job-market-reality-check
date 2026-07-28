from __future__ import annotations

PAGE_VERSION = "8.1C"

HTML_TEMPLATE = r"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>个人决策档案</title>
  <style>
    :root{
      --bg:#f3f7f8;--panel:#fff;--text:#173236;--muted:#667c81;--border:#d7e5e7;
      --primary:#0f766e;--primary-hover:#0b675f;--primary-soft:#e7f5f2;
      --danger:#b63d3d;--danger-soft:#fdecec;--warn:#946900;--warn-soft:#fff4d6;
      --shadow:0 14px 38px rgba(20,55,62,.09)
    }
    *{box-sizing:border-box}
    body{
      margin:0;color:var(--text);
      background:radial-gradient(circle at 8% 0%,rgba(38,160,142,.13),transparent 31%),var(--bg);
      font-family:Inter,"PingFang SC","Microsoft YaHei",system-ui,sans-serif
    }
    button,input,select,textarea{font:inherit}
    button{cursor:pointer}
    a{color:inherit}
    .shell{width:min(1450px,calc(100% - 28px));margin:auto;padding:18px 0 70px}
    .top{
      position:sticky;top:10px;z-index:30;display:flex;justify-content:space-between;align-items:center;
      gap:15px;padding:15px 17px;border:1px solid var(--border);border-radius:17px;
      background:rgba(255,255,255,.95);box-shadow:var(--shadow);backdrop-filter:blur(14px)
    }
    h1{margin:0;font-size:21px}.sub{margin:4px 0 0;color:var(--muted);font-size:11px}
    .actions,.tabs,.row-actions,.chips,.choice-row{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
    .btn{
      min-height:37px;border:1px solid var(--border);border-radius:10px;padding:7px 12px;
      background:#fff;color:#314b50;text-decoration:none;font-size:12px;font-weight:750
    }
    .btn:hover{border-color:#8fc8c1;background:#f7fcfb}
    .btn.primary{color:#fff;background:var(--primary);border-color:var(--primary)}
    .btn.primary:hover{background:var(--primary-hover)}
    .btn.danger{color:var(--danger);border-color:#efbcbc}
    .btn.small{min-height:31px;padding:5px 9px;font-size:11px}
    .btn.ghost{background:transparent}
    .btn:disabled{opacity:.55;cursor:not-allowed}
    .dot{display:inline-block;width:8px;height:8px;margin-right:6px;border-radius:50%;background:#aab7ba}
    .dot.online{background:#17a293;box-shadow:0 0 0 4px rgba(23,162,147,.12)}
    .dot.offline{background:#d35b5b}
    .pair{display:none;margin:15px 0;padding:17px;border:1px solid #ead690;border-radius:15px;background:#fffaf0}
    .pair.show{display:grid;grid-template-columns:1fr minmax(300px,520px);gap:18px;align-items:center}
    .pair h2{margin:0;font-size:16px}.pair p{margin:7px 0 0;color:#745f25;font-size:11px;line-height:1.6}
    .pair-controls{display:grid;grid-template-columns:1fr auto;gap:8px}
    .onboarding-card{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:18px;align-items:center;margin:15px 0;padding:16px 18px;border:1px solid #b8dcd7;border-radius:16px;background:linear-gradient(135deg,#f1fbf8,#fff);box-shadow:0 5px 18px rgba(20,55,62,.045)}
    .onboarding-card.warn{border-color:#ead690;background:linear-gradient(135deg,#fff9e8,#fff)}
    .onboarding-card h2{margin:0 0 6px;font-size:16px}.onboarding-card p{margin:0;color:var(--muted);font-size:11px;line-height:1.6}
    .onboarding-meta{display:flex;gap:7px;align-items:center;flex-wrap:wrap;margin-top:10px}
    .maturity-bar{height:8px;margin-top:10px;border-radius:999px;background:#e6efef;overflow:hidden}.maturity-bar i{display:block;height:100%;border-radius:999px;background:var(--primary)}
    .source-badge{display:inline-flex;align-items:center;min-height:23px;padding:3px 8px;border-radius:999px;background:#eef4f4;color:#587075;font-size:9px;font-weight:750}
    .source-badge.corpus{background:#e4f5f1;color:#0b6b62}.source-badge.starter{background:#fff1cc;color:#8a6400}.source-badge.user{background:#eaf0fb;color:#315b97}
    .cold-note{margin:10px 0 0;padding:10px 12px;border:1px solid #ead690;border-radius:10px;background:#fff9e8;color:#765b18;font-size:10px;line-height:1.55}
    .summary{display:grid;grid-template-columns:1.4fr repeat(4,minmax(120px,1fr));gap:11px;margin:15px 0}
    .metric{padding:15px;border:1px solid var(--border);border-radius:14px;background:#fff}
    .metric span{color:var(--muted);font-size:11px}
    .metric strong{display:block;margin-top:7px;font-size:27px}
    .metric.identity strong{font-size:17px;line-height:1.45}
    .progress{height:7px;margin-top:11px;border-radius:999px;background:#e9f0f1;overflow:hidden}
    .progress i{display:block;height:100%;background:var(--primary);border-radius:999px}
    .panel{border:1px solid var(--border);border-radius:17px;background:#fff;box-shadow:0 5px 18px rgba(20,55,62,.045)}
    .tabs{padding:12px 14px;border-bottom:1px solid var(--border)}
    .tab{border:1px solid var(--border);border-radius:999px;padding:8px 13px;background:#fff;color:#556b70;font-size:12px;font-weight:750}
    .tab.active{color:#fff;background:var(--primary);border-color:var(--primary)}
    .content{padding:18px}
    .section-head{display:flex;justify-content:space-between;align-items:flex-start;gap:14px;margin-bottom:14px}
    .section-head h2{margin:0;font-size:18px}.section-head h3{margin:0;font-size:14px}
    .section-head p{margin:5px 0 0;color:var(--muted);font-size:11px;line-height:1.55}
    .grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:13px}
    .grid.three{grid-template-columns:repeat(3,minmax(0,1fr))}
    .overview-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:13px}
    .card{padding:15px;border:1px solid var(--border);border-radius:14px;background:#fff}
    .card.soft{background:#f8fbfb}
    .card h3{margin:0 0 11px;font-size:14px}
    .summary-card{position:relative;min-height:155px}
    .summary-card .edit-link{position:absolute;right:12px;top:12px}
    .summary-line{margin:7px 0;color:#3c565b;font-size:13px;line-height:1.55}
    .summary-line.muted{color:var(--muted);font-size:11px}
    .big-summary{font-size:17px;font-weight:800;line-height:1.45}
    .field{display:grid;gap:5px}.field.full{grid-column:1/-1}
    .field label{color:#526a6f;font-size:10px;font-weight:750}
    .input,.select,.textarea{width:100%;border:1px solid #cadbdd;border-radius:10px;background:#fff;color:var(--text)}
    .input,.select{min-height:40px;padding:8px 10px}
    .textarea{min-height:95px;padding:10px;resize:vertical;line-height:1.55}
    .input:focus,.select:focus,.textarea:focus{outline:none;border-color:#65b9ae;box-shadow:0 0 0 3px rgba(15,118,110,.11)}
    .help{color:#83959a;font-size:9px;line-height:1.5}
    .checkline{display:flex;gap:9px;align-items:center;min-height:40px}
    .checkline input{width:17px;height:17px;accent-color:var(--primary)}
    .separator{height:1px;margin:15px 0;background:var(--border)}
    details.advanced{margin-top:14px;border:1px dashed #c8dadd;border-radius:12px;background:#fbfdfd}
    details.advanced summary{padding:12px 14px;color:#4f686d;font-size:11px;font-weight:750;cursor:pointer}
    details.advanced>div{padding:0 14px 14px}
    .badge{
      display:inline-flex;align-items:center;min-height:24px;border-radius:999px;padding:4px 8px;
      background:var(--primary-soft);color:#0a655e;font-size:9px;font-weight:750
    }
    .badge.warn{background:var(--warn-soft);color:var(--warn)}
    .badge.muted{background:#eef3f4;color:#60767b}
    .badge.hard{background:#fdeaea;color:#a43838}
    .choice{
      display:flex;align-items:center;gap:7px;min-height:37px;padding:7px 10px;border:1px solid var(--border);
      border-radius:10px;background:#fff;font-size:11px
    }
    .choice input{width:16px;height:16px;accent-color:var(--primary)}
    .skill-layout{display:grid;grid-template-columns:minmax(0,1fr) minmax(390px,.78fr);gap:14px}
    .suggestion-list,.skill-list,.project-list,.rows{display:grid;gap:10px}
    .suggestion-row{
      display:grid;grid-template-columns:24px minmax(130px,1fr) 150px 120px;
      gap:9px;align-items:center;padding:10px;border:1px solid var(--border);border-radius:11px;background:#fff
    }
    .suggestion-row input[type=checkbox]{width:17px;height:17px;accent-color:var(--primary)}
    .suggestion-row strong{font-size:12px}.suggestion-row small{display:block;margin-top:3px;color:var(--muted);font-size:9px}
    .skill-card,.project-card,.pref-row{border:1px solid var(--border);border-radius:12px;background:#fff}
    .skill-card{padding:12px}
    .skill-title{display:flex;justify-content:space-between;gap:10px;margin-bottom:9px}
    .skill-title strong{font-size:14px}
    .skill-edit{display:grid;grid-template-columns:180px 1fr auto auto;gap:8px;align-items:end}
    .project-toolbar{display:flex;justify-content:flex-end;margin-bottom:12px}
    .project-form{margin-bottom:14px}
    .skill-picker{display:flex;gap:8px;flex-wrap:wrap}
    .skill-chip{position:relative}
    .skill-chip input{position:absolute;opacity:0;pointer-events:none}
    .skill-chip span{
      display:inline-flex;align-items:center;min-height:34px;padding:6px 10px;border:1px solid var(--border);
      border-radius:999px;background:#fff;color:#51696e;font-size:10px;font-weight:750
    }
    .skill-chip input:checked+span{border-color:#57afa4;background:var(--primary-soft);color:#08665e}
    .project-card{padding:14px}.project-card h3{margin:0;font-size:15px}
    .project-meta{margin:5px 0 9px;color:var(--muted);font-size:10px}
    .project-card p{margin:8px 0;color:#536b70;font-size:11px;line-height:1.6;white-space:pre-wrap}
    .pref-row{display:grid;grid-template-columns:1fr 190px auto;gap:8px;align-items:center;padding:9px}
    .direction-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}
    .direction-card{display:grid;grid-template-columns:1fr 170px auto;gap:8px;align-items:center;padding:10px;border:1px solid var(--border);border-radius:11px;background:#fff}
    .empty{padding:34px 20px;border:1px dashed #bfd5d7;border-radius:12px;background:#f9fcfc;color:var(--muted);text-align:center;font-size:11px;line-height:1.6}
    .toasts{position:fixed;z-index:220;right:18px;bottom:18px;display:grid;gap:8px;width:min(380px,calc(100% - 36px))}
    .toast{padding:11px 13px;border:1px solid #cfe0df;border-radius:11px;background:#fff;box-shadow:var(--shadow);font-size:11px;line-height:1.5}
    .toast.error{color:#8e3030;border-color:#efbaba}
    .hidden{display:none!important}
    .modal-backdrop{display:none;position:fixed;inset:0;z-index:180;background:rgba(18,39,43,.46);padding:24px;overflow:auto}
    .modal-backdrop.show{display:flex;align-items:flex-start;justify-content:center}
    .modal{
      width:min(900px,100%);margin:auto;border:1px solid var(--border);border-radius:19px;background:#fff;
      box-shadow:0 24px 80px rgba(13,37,41,.24);overflow:hidden
    }
    .modal-head{display:flex;justify-content:space-between;gap:12px;padding:17px 19px;border-bottom:1px solid var(--border)}
    .modal-head h2{margin:0;font-size:18px}.modal-head p{margin:5px 0 0;color:var(--muted);font-size:11px}
    .modal-body{padding:19px}.modal-foot{display:flex;justify-content:space-between;gap:10px;padding:14px 19px;border-top:1px solid var(--border);background:#fafcfc}
    .steps{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:18px}
    .step{padding:8px;border-radius:999px;background:#edf3f4;color:#72868a;text-align:center;font-size:10px;font-weight:750}
    .step.active{background:var(--primary);color:#fff}
    .setup-skill-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}
    .setup-skill{display:grid;grid-template-columns:22px 1fr 135px;gap:8px;align-items:center;padding:9px;border:1px solid var(--border);border-radius:10px}
    @media(max-width:1100px){
      .summary{grid-template-columns:repeat(3,1fr)}.skill-layout{grid-template-columns:1fr}
      .grid.three{grid-template-columns:repeat(2,1fr)}
    }
    @media(max-width:760px){
      .top{align-items:flex-start;flex-direction:column}.pair.show,.onboarding-card{grid-template-columns:1fr}
      .summary,.overview-grid,.grid,.grid.three,.direction-grid,.setup-skill-grid{grid-template-columns:1fr}
      .skill-edit,.pref-row,.direction-card,.suggestion-row,.setup-skill{grid-template-columns:1fr}
      .content{padding:13px}.modal-backdrop{padding:10px}
    }
    @media(max-width:520px){.shell{width:calc(100% - 18px)}.pair-controls{grid-template-columns:1fr}}
  </style>
</head>
<body>
<div class="shell">
  <header class="top">
    <div>
      <h1>个人决策档案</h1>
      <p class="sub">Phase __PAGE_VERSION__ · 首次使用、建议来源与样本成熟度</p>
    </div>
    <div class="actions">
      <span id="conn"><i id="dot" class="dot"></i>未连接</span>
      <button id="quick-setup" class="btn primary">60秒快速设置</button>
      <a class="btn" href="/dashboard" target="_blank">分析看板</a>
      <a class="btn" href="/manage" target="_blank">岗位管理</a>
      <button id="refresh" class="btn">刷新</button>
      <button id="forget" class="btn danger">重新配对</button>
    </div>
  </header>

  <section id="pair" class="pair">
    <div>
      <h2>首次使用需要配对本地 API</h2>
      <p>从首次启动设置页复制本地 API 令牌。与岗位管理中心共用同一个浏览器令牌。</p>
    </div>
    <div class="pair-controls">
      <input id="token" class="input" type="password" placeholder="粘贴本地 API 令牌">
      <button id="save-token" class="btn primary">保存并连接</button>
    </div>
  </section>

  <section id="onboarding-card" class="onboarding-card hidden">
    <div>
      <h2 id="onboarding-title">首次使用引导</h2>
      <p id="onboarding-message">系统会区分通用起始建议与真实岗位语料，不会把推荐技能直接算作用户能力。</p>
      <div id="onboarding-meta" class="onboarding-meta"><span class="source-badge user">来源：用户确认</span><span class="source-badge corpus">来源：已采集岗位</span><span class="source-badge starter">来源：冷启动方向建议</span><span class="source-badge">项目证据可稍后补充</span></div>
      <div class="maturity-bar"><i id="onboarding-progress" style="width:0%"></i></div>
    </div>
    <div class="row-actions">
      <button id="onboarding-primary" class="btn primary">60秒快速设置</button>
      <a id="onboarding-profile-action" class="btn" href="/manage" target="_blank">查看岗位样本</a>
    </div>
  </section>

  <section class="summary">
    <article class="metric identity">
      <span>档案概况</span>
      <strong id="m-identity">尚未设置</strong>
      <div class="progress"><i id="m-progress" style="width:0%"></i></div>
    </article>
    <article class="metric"><span>我的技能</span><strong id="m-skills">—</strong></article>
    <article class="metric"><span>我的项目</span><strong id="m-projects">—</strong></article>
    <article class="metric"><span>目标方向</span><strong id="m-directions">—</strong></article>
    <article class="metric"><span>城市偏好</span><strong id="m-cities">—</strong></article>
  </section>

  <main class="panel">
    <nav class="tabs">
      <button class="tab active" data-tab="overview">我的概况</button>
      <button class="tab" data-tab="skills">我的能力</button>
      <button class="tab" data-tab="projects">我的项目</button>
      <button class="tab" data-tab="preferences">求职目标</button>
    </nav>
    <section id="content" class="content"><div class="empty">正在加载个人档案……</div></section>
  </main>
</div>

<div id="setup-modal" class="modal-backdrop" aria-hidden="true">
  <section class="modal">
    <header class="modal-head">
      <div>
        <h2>60秒快速设置</h2>
        <p>只确认影响投递判断的核心信息，其他细节以后再补。</p>
      </div>
      <button id="setup-close" class="btn">关闭</button>
    </header>
    <div id="setup-body" class="modal-body"></div>
    <footer class="modal-foot">
      <button id="setup-skip" class="btn ghost">暂时跳过</button>
      <div class="row-actions">
        <button id="setup-prev" class="btn">上一步</button>
        <button id="setup-next" class="btn primary">下一步</button>
      </div>
    </footer>
  </section>
</div>

<div id="toasts" class="toasts"></div>

<script>
const TOKEN_KEY='jobMarketApiTokenV1';
const ONBOARDING_DISMISSED_KEY='jobMarketProfileOnboardingDismissedV3';

const labels={
  proficiency:{aware:'了解',basic:'基础',proficient:'熟练',project_ready:'可独立完成项目'},
  projectType:{personal:'个人工程',research:'研究项目',course:'课程项目',competition:'竞赛项目',internship:'实习项目',other:'其他'},
  projectStatus:{idea:'构思中',in_progress:'进行中',completed:'已完成',maintained:'持续维护'},
  interest:{very_high:'非常感兴趣',high:'比较感兴趣',acceptable:'可以接受',low:'兴趣较低',none:'不考虑'},
  constraint:{hard:'硬条件',important:'重要偏好',preference:'普通偏好'},
  jobType:{
    summer_internship:'暑期实习',
    daily_internship:'日常实习',
    full_time:'全职岗位',
    research_assistant:'研究助理 / RA',
    part_time:'兼职 / 项目制'
  }
};

const state={
  token:localStorage.getItem(TOKEN_KEY)||'',
  tab:'overview',
  data:null,
  skillSuggestions:null,
  directionSuggestions:null,
  basicEditing:false,
  projectFormOpen:false,
  editingProject:null,
  setupStep:1,
  onboarding:null
};

const content=document.getElementById('content');

function esc(value){
  return String(value??'').replace(/[&<>"']/g,ch=>({
    '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
  }[ch]));
}

function optionHtml(map,value){
  return Object.entries(map).map(([key,label])=>
    `<option value="${key}" ${key===value?'selected':''}>${esc(label)}</option>`
  ).join('');
}

function toast(message,error=false){
  const node=document.createElement('div');
  node.className='toast'+(error?' error':'');
  node.textContent=message;
  document.getElementById('toasts').appendChild(node);
  setTimeout(()=>node.remove(),3600);
}

function setConnection(ok,text){
  document.getElementById('dot').className='dot '+(ok?'online':'offline');
  document.getElementById('conn').lastChild.textContent=text;
  document.getElementById('pair').classList.toggle('show',!ok);
}

async function api(path,options={}){
  const headers={'Accept':'application/json',...(options.headers||{})};
  if(state.token)headers['X-Job-Market-Token']=state.token;
  if(options.body!==undefined){
    headers['Content-Type']='application/json';
    options.body=JSON.stringify(options.body);
  }
  const response=await fetch(path,{...options,headers});
  let payload=null;
  try{payload=await response.json();}catch{}
  if(!response.ok){
    const detail=payload?.detail;
    throw new Error(typeof detail==='string'?detail:JSON.stringify(detail||`HTTP ${response.status}`));
  }
  return payload;
}

function profileCompletion(){
  if(!state.data)return 0;
  return state.data.onboarding?.completion_percent??0;
}

function profileNeedsSetup(){
  if(!state.data)return false;
  return !Boolean(state.data.onboarding?.profile_initialized);
}

function sourceBadge(item){
  const source=item?.source||'';
  const label=item?.source_label||'';
  const tone=source==='job_corpus'?'corpus':source.includes('starter')||source==='general_starter'?'starter':'user';
  return label?`<span class="source-badge ${tone}">${esc(label)}</span>`:'';
}

function renderOnboarding(){
  const card=document.getElementById('onboarding-card');
  const onboarding=state.data?.onboarding;
  if(!onboarding){
    card.classList.add('hidden');
    return;
  }
  state.onboarding=onboarding;
  card.classList.remove('hidden');
  card.classList.toggle('warn',onboarding.job_count<3);
  document.getElementById('onboarding-title').textContent=
    onboarding.job_count===0?'先用一个真实岗位启动你的档案':onboarding.maturity.label;
  document.getElementById('onboarding-message').textContent=onboarding.maturity.message;
  document.getElementById('onboarding-progress').style.width=`${onboarding.maturity.progress}%`;
  document.getElementById('onboarding-meta').innerHTML=`
    <span class="badge ${onboarding.job_count<3?'warn':''}">${esc(onboarding.maturity.confidence)}</span>
    <span class="source-badge user">档案完成 ${onboarding.completion_percent}%</span>
    <span class="source-badge ${onboarding.job_count?'corpus':'starter'}">${esc(onboarding.recommendation_basis)}</span>
    ${onboarding.project_is_optional?'<span class="source-badge">项目证据可稍后补充</span>':''}
  `;
  const primary=document.getElementById('onboarding-primary');
  primary.textContent=onboarding.next_action==='collect_first_job'?'先完成60秒设置':'继续完善档案';
  primary.onclick=openQuickSetup;
}

async function loadAll(){
  if(!state.token){
    setConnection(false,'待配对');
    return;
  }
  try{
    const [data,skills,directions]=await Promise.all([
      api('/api/v1/profile'),
      api('/api/v1/profile/skill-suggestions?limit=200'),
      api('/api/v1/profile/direction-suggestions?limit=100')
    ]);
    state.data=data;
    state.skillSuggestions=skills;
    state.directionSuggestions=directions;
    state.onboarding=data.onboarding||null;
    setConnection(true,'已连接');
    renderOnboarding();
    renderSummary();
    render();
    if(profileNeedsSetup()&&!localStorage.getItem(ONBOARDING_DISMISSED_KEY)){
      openQuickSetup();
    }
  }catch(error){
    setConnection(false,'连接失败');
    toast(error.message,true);
  }
}

function renderSummary(){
  const p=state.data?.profile||{};
  const s=state.data?.summary||{};
  const identity=[p.graduation_year?`${p.graduation_year}届`:null,p.education,p.major].filter(Boolean).join(' · ');
  document.getElementById('m-identity').textContent=identity||'尚未设置';
  document.getElementById('m-progress').style.width=`${profileCompletion()}%`;
  document.getElementById('m-skills').textContent=s.skill_count??0;
  document.getElementById('m-projects').textContent=s.project_count??0;
  document.getElementById('m-directions').textContent=s.direction_count??0;
  document.getElementById('m-cities').textContent=s.city_count??0;
}

function render(){
  document.querySelectorAll('.tab').forEach(btn=>
    btn.classList.toggle('active',btn.dataset.tab===state.tab)
  );
  if(!state.data){
    content.innerHTML='<div class="empty">请先连接本地 API。</div>';
    return;
  }
  if(state.tab==='overview')renderOverview();
  if(state.tab==='skills')renderSkills();
  if(state.tab==='projects')renderProjects();
  if(state.tab==='preferences')renderPreferences();
}

function jobTypeChoices(selected=[]){
  return Object.entries(labels.jobType).map(([key,label])=>
    `<label class="choice"><input type="checkbox" name="job-type" value="${key}" ${selected.includes(key)?'checked':''}>${esc(label)}</label>`
  ).join('');
}

function renderOverview(){
  const p=state.data.profile;
  const cities=state.data.cities||[];
  const directions=state.data.directions||[];

  if(state.basicEditing){
    renderBasicEditor();
    return;
  }

  const jobTypes=(p.target_job_types||[]).map(item=>labels.jobType[item]||item);
  const cityBadges=cities.map(item=>
    `<span class="badge ${item.constraint_level==='hard'?'hard':item.constraint_level==='important'?'':'muted'}">${esc(item.city)}</span>`
  ).join('');
  const directionBadges=directions.slice(0,8).map(item=>
    `<span class="badge ${item.interest_level==='none'||item.interest_level==='low'?'muted':''}">${esc(item.direction)}</span>`
  ).join('');

  content.innerHTML=`
    <div class="section-head">
      <div>
        <h2>我的概况</h2>
        <p>日常以查看为主。蓝色来源表示用户确认，绿色来源表示岗位语料，黄色来源表示冷启动建议。</p>
      </div>
      <div class="row-actions">
        <button id="edit-overview" class="btn">编辑核心信息</button>
        <button id="overview-setup" class="btn primary">重新快速设置</button>
      </div>
    </div>

    <div class="overview-grid">
      <article class="card summary-card">
        <h3>身份信息</h3>
        <div class="big-summary">${esc([p.graduation_year?`${p.graduation_year}届`:null,p.education,p.major].filter(Boolean).join(' · ')||'尚未设置')}</div>
        <div class="onboarding-meta"><span class="source-badge user">来源：用户确认</span></div>
        <div class="summary-line muted">这些信息用于学历、专业和毕业时间条件判断。</div>
      </article>

      <article class="card summary-card">
        <h3>求职类型</h3>
        <div class="chips">${jobTypes.length?jobTypes.map(item=>`<span class="badge">${esc(item)}</span>`).join(''):'<span class="badge warn">尚未设置</span>'}</div>
        <div class="summary-line muted">不同求职类型会决定后续更关注日薪、月薪或研究经历。</div>
      </article>

      <article class="card summary-card">
        <h3>可到岗条件</h3>
        <div class="summary-line">${p.available_from?`最早 ${esc(p.available_from)} 到岗`:'到岗时间未设置'}</div>
        <div class="summary-line">${p.max_days_per_week!=null?`每周最多 ${p.max_days_per_week} 天`:'每周到岗天数未设置'}</div>
        <div class="summary-line">${p.min_internship_months!=null?`至少连续 ${p.min_internship_months} 个月`:'实习周期未设置'}</div>
      </article>

      <article class="card summary-card">
        <h3>工作方式</h3>
        <div class="chips">
          <span class="badge ${p.accepts_remote?'':'muted'}">${p.accepts_remote?'接受远程':'暂不接受远程'}</span>
          <span class="badge ${p.accepts_relocation?'':'muted'}">${p.accepts_relocation?'接受异地或搬迁':'暂不接受搬迁'}</span>
        </div>
      </article>

      <article class="card summary-card">
        <h3>目标城市</h3>
        <div class="chips">${cityBadges||'<span class="badge warn">尚未设置</span>'}</div>
      </article>

      <article class="card summary-card">
        <h3>目标方向</h3>
        <div class="chips">${directionBadges||'<span class="badge warn">尚未设置</span>'}</div>
      </article>
    </div>
  `;

  document.getElementById('edit-overview').addEventListener('click',()=>{
    state.basicEditing=true;
    renderOverview();
  });
  document.getElementById('overview-setup').addEventListener('click',openQuickSetup);
}

function renderBasicEditor(){
  const p=state.data.profile;
  const targetTypes=p.target_job_types||[];
  const showDaily=targetTypes.some(item=>['summer_internship','daily_internship','part_time'].includes(item));
  const showMonthly=targetTypes.includes('full_time')||targetTypes.includes('research_assistant');

  content.innerHTML=`
    <div class="section-head">
      <div>
        <h2>编辑核心信息</h2>
        <p>只保留评分真正需要的核心条件。薪资、最长周期和补充说明放在高级设置中。</p>
      </div>
      <div class="row-actions">
        <button id="cancel-basic" class="btn">取消</button>
        <button id="save-basic" class="btn primary">保存</button>
      </div>
    </div>

    <div class="card soft">
      <div class="grid three">
        <div class="field">
          <label>当前学历</label>
          <input id="education" class="input" value="${esc(p.education)}" placeholder="例如：本科">
        </div>
        <div class="field">
          <label>专业</label>
          <input id="major" class="input" value="${esc(p.major)}" placeholder="例如：电子信息科学与技术">
        </div>
        <div class="field">
          <label>毕业年份</label>
          <input id="graduation-year" class="input" type="number" min="2000" max="2100" value="${p.graduation_year??''}" placeholder="2027">
        </div>

        <div class="field full">
          <label>当前主要寻找什么</label>
          <div class="choice-row">${jobTypeChoices(targetTypes)}</div>
        </div>

        <div class="field">
          <label>最早可到岗时间</label>
          <input id="available-from" class="input" value="${esc(p.available_from)}" placeholder="例如：2026年8月">
        </div>
        <div class="field">
          <label>每周最多到岗天数</label>
          <input id="max-days" class="input" type="number" min="0" max="7" value="${p.max_days_per_week??''}">
        </div>
        <div class="field">
          <label>至少可连续实习月数</label>
          <input id="min-months" class="input" type="number" min="0" max="36" value="${p.min_internship_months??''}">
        </div>

        <label class="checkline"><input id="accepts-remote" type="checkbox" ${p.accepts_remote?'checked':''}>接受远程岗位</label>
        <label class="checkline"><input id="accepts-relocation" type="checkbox" ${p.accepts_relocation?'checked':''}>接受异地实习或搬迁</label>
      </div>

      <details class="advanced">
        <summary>高级设置：薪资、最长周期和补充说明</summary>
        <div class="grid three">
          <div class="field">
            <label>最长可实习月数</label>
            <input id="max-months" class="input" type="number" min="0" max="36" value="${p.max_internship_months??''}">
          </div>
          <div class="field ${showDaily?'':'hidden'}" data-salary-daily>
            <label>最低日薪（元/天）</label>
            <input id="daily-salary" class="input" type="number" min="0" value="${p.minimum_daily_salary??''}" placeholder="不设置则留空">
          </div>
          <div class="field ${showMonthly?'':'hidden'}" data-salary-monthly>
            <label>最低月薪（元/月）</label>
            <input id="monthly-salary" class="input" type="number" min="0" value="${p.minimum_monthly_salary??''}" placeholder="不设置则留空">
          </div>
          <div class="field full">
            <label>补充说明</label>
            <textarea id="profile-notes" class="textarea" placeholder="例如：课程安排、无法到岗的日期等">${esc(p.notes)}</textarea>
          </div>
        </div>
      </details>
    </div>
  `;

  document.querySelectorAll('input[name="job-type"]').forEach(input=>
    input.addEventListener('change',updateSalaryVisibility)
  );
  document.getElementById('cancel-basic').addEventListener('click',()=>{
    state.basicEditing=false;
    renderOverview();
  });
  document.getElementById('save-basic').addEventListener('click',saveBasic);
}

function selectedJobTypes(){
  return [...document.querySelectorAll('input[name="job-type"]:checked')].map(input=>input.value);
}

function updateSalaryVisibility(){
  const selected=selectedJobTypes();
  const showDaily=selected.some(item=>['summer_internship','daily_internship','part_time'].includes(item));
  const showMonthly=selected.includes('full_time')||selected.includes('research_assistant');
  document.querySelector('[data-salary-daily]')?.classList.toggle('hidden',!showDaily);
  document.querySelector('[data-salary-monthly]')?.classList.toggle('hidden',!showMonthly);
}

function numberOrNull(id){
  const node=document.getElementById(id);
  if(!node)return null;
  const value=node.value.trim();
  return value===''?null:Number(value);
}

async function saveBasic(){
  try{
    await api('/api/v1/profile',{
      method:'PATCH',
      body:{
        education:document.getElementById('education').value,
        major:document.getElementById('major').value,
        graduation_year:numberOrNull('graduation-year'),
        target_job_types:selectedJobTypes(),
        max_days_per_week:numberOrNull('max-days'),
        min_internship_months:numberOrNull('min-months'),
        max_internship_months:numberOrNull('max-months'),
        minimum_daily_salary:numberOrNull('daily-salary'),
        minimum_monthly_salary:numberOrNull('monthly-salary'),
        accepts_remote:document.getElementById('accepts-remote').checked,
        accepts_relocation:document.getElementById('accepts-relocation').checked,
        available_from:document.getElementById('available-from').value,
        notes:document.getElementById('profile-notes')?.value||''
      }
    });
    state.basicEditing=false;
    toast('核心信息已保存。');
    await loadAll();
  }catch(error){
    toast(error.message,true);
  }
}

function renderSkills(){
  const suggestions=(state.skillSuggestions?.items||[]).filter(item=>!item.already_added).slice(0,20);
  const skills=state.data.skills||[];

  content.innerHTML=`
    <div class="section-head">
      <div>
        <h2>我的能力</h2>
        <p>系统优先使用真实岗位语料；样本不足时才补充目标方向起始建议，并清楚标注来源。</p>
      </div>
      <div class="chips">
        <span class="badge">发现 ${state.skillSuggestions?.total||0} 项 · ${state.skillSuggestions?.source_job_count||0} 个岗位</span>
        <span class="badge ${state.skillSuggestions?.starter_used?'warn':'muted'}">${esc(state.skillSuggestions?.maturity?.confidence||'')}</span>
      </div>
    </div>

    <div class="skill-layout">
      <div class="card soft">
        <div class="section-head">
          <div>
            <h3>待确认的技能建议</h3>
            <p>选择真实具备的技能，系统不会因为岗位提到了某项技能就自动认定你会。</p>
          </div>
          <button id="confirm-skills" class="btn primary">确认选中</button>
        </div>

        <div class="field" style="margin-bottom:10px">
          <label>筛选建议</label>
          <input id="skill-filter" class="input" placeholder="搜索技能或技能组">
        </div>

        <div id="skill-suggestions" class="suggestion-list">
          ${suggestions.length?suggestions.map(renderSuggestionRow).join(''):'<div class="empty">暂无新的技能建议。你已经确认了当前候选项，或岗位语料尚未识别到技能。</div>'}
        </div>

        <details class="advanced">
          <summary>自由添加未出现在岗位建议中的技能</summary>
          <div class="grid">
            <div class="field">
              <label>技能名称</label>
              <input id="new-skill" class="input" placeholder="例如：LangGraph、因果推断">
            </div>
            <div class="field">
              <label>熟练程度</label>
              <select id="new-level" class="select">${optionHtml(labels.proficiency,'basic')}</select>
            </div>
            <div class="field full">
              <button id="add-skill" class="btn">添加技能</button>
            </div>
          </div>
        </details>
      </div>

      <div class="card soft">
        <h3>已确认技能</h3>
        <div class="skill-list">
          ${skills.length?skills.map(renderSkillCard).join(''):'<div class="empty">尚未确认技能。先从左侧建议中勾选真实具备的能力。</div>'}
        </div>
      </div>
    </div>
  `;

  document.getElementById('skill-filter').addEventListener('input',event=>{
    const q=event.target.value.trim().toLowerCase();
    document.querySelectorAll('[data-suggestion-row]').forEach(node=>
      node.classList.toggle('hidden',q&&!node.dataset.search.includes(q))
    );
  });
  document.getElementById('confirm-skills').addEventListener('click',confirmSelectedSkills);
  document.getElementById('add-skill')?.addEventListener('click',()=>
    addSkill(document.getElementById('new-skill').value,document.getElementById('new-level').value)
  );
  document.querySelectorAll('[data-save-skill]').forEach(btn=>
    btn.addEventListener('click',()=>saveSkill(Number(btn.dataset.saveSkill)))
  );
  document.querySelectorAll('[data-delete-skill]').forEach(btn=>
    btn.addEventListener('click',()=>deleteSkill(Number(btn.dataset.deleteSkill)))
  );
}

function renderSuggestionRow(item){
  const corpus=item.source==='job_corpus';
  return `
    <div class="suggestion-row" data-suggestion-row data-search="${esc((item.skill_name+' '+item.skill_group+' '+(item.source_label||'')).toLowerCase())}">
      <input type="checkbox" class="suggestion-check" data-skill-name="${esc(item.skill_name)}">
      <div>
        <strong>${esc(item.skill_name)}</strong>
        <small>${esc(item.skill_group)}${corpus?` · 覆盖 ${(item.coverage*100).toFixed(1)}%`:''}</small>
        <div class="onboarding-meta">${sourceBadge(item)}</div>
      </div>
      <select class="select suggestion-level">${optionHtml(labels.proficiency,'basic')}</select>
      <span class="badge muted">需本人确认</span>
    </div>
  `;
}

function renderSkillCard(skill){
  return `
    <div class="skill-card">
      <div class="skill-title">
        <div>
          <strong>${esc(skill.skill_name)}</strong>
          <div class="chips">
            <span class="badge muted">${skill.evidence_count} 个项目证据</span>
            ${(skill.projects||[]).map(name=>`<span class="badge">${esc(name)}</span>`).join('')}
          </div>
        </div>
      </div>
      <div class="skill-edit">
        <div class="field">
          <label>熟练程度</label>
          <select id="skill-level-${skill.skill_id}" class="select">${optionHtml(labels.proficiency,skill.proficiency_level)}</select>
        </div>
        <div class="field">
          <label>可选说明</label>
          <input id="skill-notes-${skill.skill_id}" class="input" value="${esc(skill.notes)}" placeholder="例如：近期在项目中持续使用">
        </div>
        <button class="btn" data-save-skill="${skill.skill_id}">保存</button>
        <button class="btn danger" data-delete-skill="${skill.skill_id}">删除</button>
      </div>
    </div>
  `;
}

async function confirmSelectedSkills(){
  const rows=[...document.querySelectorAll('[data-suggestion-row]')].filter(row=>
    row.querySelector('.suggestion-check').checked
  );
  if(!rows.length){
    toast('请先勾选至少一项真实具备的技能。',true);
    return;
  }

  const button=document.getElementById('confirm-skills');
  button.disabled=true;
  let success=0;
  try{
    for(const row of rows){
      const skillName=row.querySelector('.suggestion-check').dataset.skillName;
      const level=row.querySelector('.suggestion-level').value;
      await api('/api/v1/profile/skills',{
        method:'POST',
        body:{skill_name:skillName,proficiency_level:level}
      });
      success+=1;
    }
    toast(`已确认 ${success} 项技能。`);
    await loadAll();
  }catch(error){
    toast(`已成功 ${success} 项；${error.message}`,true);
    await loadAll();
  }finally{
    button.disabled=false;
  }
}

async function addSkill(name,level){
  if(!name.trim()){
    toast('请输入技能名称。',true);
    return;
  }
  try{
    await api('/api/v1/profile/skills',{
      method:'POST',
      body:{skill_name:name,proficiency_level:level}
    });
    toast(`已添加技能：${name}`);
    await loadAll();
  }catch(error){
    toast(error.message,true);
  }
}

async function saveSkill(id){
  try{
    await api(`/api/v1/profile/skills/${id}`,{
      method:'PATCH',
      body:{
        proficiency_level:document.getElementById(`skill-level-${id}`).value,
        notes:document.getElementById(`skill-notes-${id}`).value
      }
    });
    toast('技能已更新。');
    await loadAll();
  }catch(error){
    toast(error.message,true);
  }
}

async function deleteSkill(id){
  if(!confirm('删除技能后，它与项目的关联证据也会删除。继续吗？'))return;
  try{
    await api(`/api/v1/profile/skills/${id}`,{method:'DELETE'});
    toast('技能已删除。');
    await loadAll();
  }catch(error){
    toast(error.message,true);
  }
}

function renderProjects(){
  const projects=state.data.projects||[];

  content.innerHTML=`
    <div class="section-head">
      <div>
        <h2>我的项目</h2>
        <p>以项目为中心选择使用过的技能，系统自动生成能力证据，不再要求逐项填写技能证据表。</p>
      </div>
      <button id="new-project" class="btn primary">${state.projectFormOpen?'收起表单':'添加项目'}</button>
    </div>

    <div id="project-form-slot">
      ${state.projectFormOpen?renderProjectForm():''}
    </div>

    <div class="project-list">
      ${projects.length?projects.map(renderProjectCard).join(''):'<div class="empty">尚未添加项目。建议先录入最能证明能力的 1—3 个核心项目。</div>'}
    </div>
  `;

  document.getElementById('new-project').addEventListener('click',()=>{
    if(state.projectFormOpen){
      state.projectFormOpen=false;
      state.editingProject=null;
    }else{
      state.projectFormOpen=true;
      state.editingProject=null;
    }
    renderProjects();
  });

  wireProjectForm();
  document.querySelectorAll('[data-edit-project]').forEach(btn=>
    btn.addEventListener('click',()=>{
      state.editingProject=state.data.projects.find(
        project=>Number(project.project_id)===Number(btn.dataset.editProject)
      );
      state.projectFormOpen=true;
      renderProjects();
      window.scrollTo({top:0,behavior:'smooth'});
    })
  );
  document.querySelectorAll('[data-delete-project]').forEach(btn=>
    btn.addEventListener('click',()=>deleteProject(Number(btn.dataset.deleteProject)))
  );
}

function renderProjectForm(){
  const edit=state.editingProject||{};
  const skills=state.data.skills||[];
  const selected=new Set((edit.skills||[]).map(item=>Number(item.skill_id)));

  return `
    <div class="card soft project-form">
      <div class="section-head">
        <div>
          <h3>${state.editingProject?'编辑项目':'新增项目'}</h3>
          <p>只写项目本身，再勾选真实使用过的技能。能力证据由系统自动关联。</p>
        </div>
        ${state.editingProject?'<button id="cancel-project-edit" class="btn small">取消编辑</button>':''}
      </div>

      <div class="grid">
        <div class="field full">
          <label>项目名称</label>
          <input id="project-name" class="input" value="${esc(edit.project_name||'')}" placeholder="例如：招聘市场分析与投递决策系统">
        </div>
        <div class="field">
          <label>项目类型</label>
          <select id="project-type" class="select">${optionHtml(labels.projectType,edit.project_type||'personal')}</select>
        </div>
        <div class="field">
          <label>项目状态</label>
          <select id="project-status" class="select">${optionHtml(labels.projectStatus,edit.project_status||'in_progress')}</select>
        </div>
        <div class="field full">
          <label>一句话简介</label>
          <textarea id="project-description" class="textarea" placeholder="项目解决了什么问题，整体做了什么">${esc(edit.description||'')}</textarea>
        </div>
        <div class="field full">
          <label>成果与技术工作</label>
          <textarea id="project-achievements" class="textarea" placeholder="每行写一项可验证成果；系统会把这些内容作为能力证据来源">${esc(edit.achievements||'')}</textarea>
        </div>
        <div class="field full">
          <label>本项目真实使用的技能</label>
          <div class="skill-picker">
            ${skills.length?skills.map(skill=>`
              <label class="skill-chip">
                <input type="checkbox" class="project-skill" value="${skill.skill_id}" ${selected.has(Number(skill.skill_id))?'checked':''}>
                <span>${esc(skill.skill_name)}</span>
              </label>
            `).join(''):'<span class="badge warn">请先在“我的能力”中确认技能</span>'}
          </div>
          <span class="help">保存后系统自动建立“项目 → 技能”的能力证据。无需为每项技能重复写说明。</span>
        </div>
      </div>

      <details class="advanced">
        <summary>高级设置：代码仓库和演示地址</summary>
        <div class="grid">
          <div class="field">
            <label>GitHub 地址</label>
            <input id="project-github" class="input" value="${esc(edit.github_url||'')}">
          </div>
          <div class="field">
            <label>演示地址</label>
            <input id="project-demo" class="input" value="${esc(edit.demo_url||'')}">
          </div>
        </div>
      </details>

      <div class="row-actions" style="margin-top:14px">
        <button id="save-project" class="btn primary">${state.editingProject?'保存项目修改':'创建项目'}</button>
      </div>
    </div>
  `;
}

function wireProjectForm(){
  document.getElementById('save-project')?.addEventListener('click',saveProject);
  document.getElementById('cancel-project-edit')?.addEventListener('click',()=>{
    state.editingProject=null;
    state.projectFormOpen=false;
    renderProjects();
  });
}

function renderProjectCard(project){
  return `
    <article class="project-card">
      <div class="section-head">
        <div>
          <h3>${esc(project.project_name)}</h3>
          <div class="project-meta">${esc(labels.projectType[project.project_type]||project.project_type)} · ${esc(labels.projectStatus[project.project_status]||project.project_status)}</div>
        </div>
        <div class="row-actions">
          <button class="btn small" data-edit-project="${project.project_id}">编辑</button>
          <button class="btn small danger" data-delete-project="${project.project_id}">删除</button>
        </div>
      </div>
      ${project.description?`<p>${esc(project.description)}</p>`:''}
      ${project.achievements?`<p><strong>成果：</strong>\n${esc(project.achievements)}</p>`:''}
      <div class="chips">
        ${(project.skills||[]).map(item=>
          `<span class="badge" title="${esc(item.evidence_text)}">${esc(item.skill_name)} · 已形成证据</span>`
        ).join('')||'<span class="badge warn">尚未关联技能</span>'}
      </div>
    </article>
  `;
}

function automaticEvidenceText(projectName,description,achievements,skillName){
  const firstAchievement=(achievements||'').split(/\r?\n/).map(item=>item.trim()).find(Boolean);
  const source=firstAchievement||String(description||'').trim();
  const prefix=`在项目“${projectName}”中实际使用 ${skillName}`;
  return source?`${prefix}：${source}`:`${prefix}。`;
}

async function saveProject(){
  const projectName=document.getElementById('project-name').value.trim();
  const description=document.getElementById('project-description').value;
  const achievements=document.getElementById('project-achievements').value;

  if(!projectName){
    toast('请填写项目名称。',true);
    return;
  }

  const existingEvidence=new Map(
    (state.editingProject?.skills||[]).map(item=>[Number(item.skill_id),item])
  );

  const skillItems=[...document.querySelectorAll('.project-skill:checked')].map(input=>{
    const skillId=Number(input.value);
    const skill=state.data.skills.find(item=>Number(item.skill_id)===skillId);
    const existing=existingEvidence.get(skillId);
    return {
      skill_id:skillId,
      evidence_strength:existing?.evidence_strength||'supporting',
      evidence_text:existing?.evidence_text||automaticEvidenceText(
        projectName,
        description,
        achievements,
        skill?.skill_name||'该技能'
      )
    };
  });

  const body={
    project_name:projectName,
    project_type:document.getElementById('project-type').value,
    project_status:document.getElementById('project-status').value,
    description,
    achievements,
    github_url:document.getElementById('project-github')?.value||'',
    demo_url:document.getElementById('project-demo')?.value||'',
    skills:skillItems
  };

  try{
    if(state.editingProject){
      await api(`/api/v1/profile/projects/${state.editingProject.project_id}`,{
        method:'PATCH',
        body
      });
    }else{
      await api('/api/v1/profile/projects',{method:'POST',body});
    }
    state.editingProject=null;
    state.projectFormOpen=false;
    toast('项目已保存，能力证据已自动关联。');
    await loadAll();
  }catch(error){
    toast(error.message,true);
  }
}

async function deleteProject(id){
  if(!confirm('确定删除这个项目及其能力证据吗？'))return;
  try{
    await api(`/api/v1/profile/projects/${id}`,{method:'DELETE'});
    toast('项目已删除。');
    await loadAll();
  }catch(error){
    toast(error.message,true);
  }
}

function renderPreferences(){
  const p=state.data.profile||{};
  const cities=state.data.cities||[];
  const directions=state.data.directions||[];
  const suggested=(state.directionSuggestions?.items||[]).filter(item=>!item.already_added).slice(0,12);

  content.innerHTML=`
    <div class="section-head">
      <div>
        <h2>求职目标</h2>
        <p>这里记录“想找什么”和“愿意去哪里”。每个方向建议都会标明来自真实岗位还是冷启动方向包。</p>
      </div>
      <button id="save-preferences" class="btn primary">保存求职目标</button>
    </div>

    <div class="card soft" style="margin-bottom:13px">
      <h3>求职类型</h3>
      <div class="choice-row">${jobTypeChoices(p.target_job_types||[])}</div>
    </div>

    <div class="grid">
      <div class="card soft">
        <div class="section-head">
          <div>
            <h3>目标城市</h3>
            <p>“硬条件”表示其他城市原则上不投；“重要偏好”只是优先考虑。</p>
          </div>
          <button id="add-city" class="btn small">添加城市</button>
        </div>
        <div id="city-rows" class="rows">
          ${cities.length?cities.map(renderCityRow).join(''):'<div class="empty" id="city-empty">尚未设置目标城市。</div>'}
        </div>
      </div>

      <div class="card soft">
        <div class="section-head">
          <div>
            <h3>目标岗位方向</h3>
            <p>先点选样本中出现的方向，再调整兴趣等级。</p>
          </div>
          <button id="add-direction" class="btn small">自由添加</button>
        </div>
        <div class="chips" style="margin-bottom:10px">
          ${suggested.map(item=>`<button class="btn small" title="${esc(item.source_label||'')}" data-direction-suggestion="${esc(item.direction)}">+ ${esc(item.direction)} · ${esc(item.source==='job_corpus'?`${item.job_count}岗`:'起始建议')}</button>`).join('')}
        </div>
        <div id="direction-rows" class="direction-grid">
          ${directions.length?directions.map(renderDirectionRow).join(''):'<div class="empty" id="direction-empty">尚未设置目标方向。</div>'}
        </div>
      </div>
    </div>
  `;

  document.getElementById('add-city').addEventListener('click',()=>appendCityRow());
  document.getElementById('add-direction').addEventListener('click',()=>appendDirectionRow());
  document.getElementById('save-preferences').addEventListener('click',savePreferences);
  document.querySelectorAll('[data-direction-suggestion]').forEach(btn=>
    btn.addEventListener('click',()=>appendDirectionRow(btn.dataset.directionSuggestion,'high'))
  );
  wireRemoveRows();
}

function renderCityRow(item){
  return `
    <div class="pref-row" data-city-row>
      <input class="input city-value" value="${esc(item.city)}" placeholder="城市名称">
      <select class="select city-level">${optionHtml(labels.constraint,item.constraint_level)}</select>
      <button class="btn danger small remove-row">删除</button>
    </div>
  `;
}

function renderDirectionRow(item){
  return `
    <div class="direction-card" data-direction-row>
      <input class="input direction-value" value="${esc(item.direction)}" placeholder="岗位方向">
      <select class="select direction-level">${optionHtml(labels.interest,item.interest_level)}</select>
      <button class="btn danger small remove-row">删除</button>
    </div>
  `;
}

function appendCityRow(city='',level='important'){
  document.getElementById('city-empty')?.remove();
  document.getElementById('city-rows').insertAdjacentHTML(
    'beforeend',
    renderCityRow({city,constraint_level:level})
  );
  wireRemoveRows();
}

function appendDirectionRow(direction='',level='acceptable'){
  document.getElementById('direction-empty')?.remove();
  if([...document.querySelectorAll('.direction-value')].some(input=>
    input.value.trim().toLowerCase()===direction.trim().toLowerCase()&&direction.trim()
  ))return;
  document.getElementById('direction-rows').insertAdjacentHTML(
    'beforeend',
    renderDirectionRow({direction,interest_level:level})
  );
  wireRemoveRows();
}

function wireRemoveRows(){
  document.querySelectorAll('.remove-row').forEach(btn=>{
    btn.onclick=()=>btn.closest('[data-city-row],[data-direction-row]').remove();
  });
}

async function savePreferences(){
  const cities=[...document.querySelectorAll('[data-city-row]')].map(row=>({
    city:row.querySelector('.city-value').value,
    constraint_level:row.querySelector('.city-level').value
  })).filter(item=>item.city.trim());

  const directions=[...document.querySelectorAll('[data-direction-row]')].map(row=>({
    direction:row.querySelector('.direction-value').value,
    interest_level:row.querySelector('.direction-level').value
  })).filter(item=>item.direction.trim());

  try{
    await Promise.all([
      api('/api/v1/profile',{method:'PATCH',body:{target_job_types:selectedJobTypes()}}),
      api('/api/v1/profile/cities',{method:'PUT',body:{cities}}),
      api('/api/v1/profile/preferences',{method:'PUT',body:{directions}})
    ]);
    toast('求职目标已保存。');
    await loadAll();
  }catch(error){
    toast(error.message,true);
  }
}

function openQuickSetup(){
  if(!state.data){
    toast('请先连接本地 API。',true);
    return;
  }
  state.setupStep=1;
  document.getElementById('setup-modal').classList.add('show');
  document.getElementById('setup-modal').setAttribute('aria-hidden','false');
  renderSetupStep();
}

function closeQuickSetup(){
  document.getElementById('setup-modal').classList.remove('show');
  document.getElementById('setup-modal').setAttribute('aria-hidden','true');
}

function setupStepsHtml(){
  return `
    <div class="steps">
      <div class="step ${state.setupStep===1?'active':''}">1. 身份与目标</div>
      <div class="step ${state.setupStep===2?'active':''}">2. 到岗与城市</div>
      <div class="step ${state.setupStep===3?'active':''}">3. 方向与技能</div>
    </div>
  `;
}

function setupJobTypeChoices(selected=[]){
  return Object.entries(labels.jobType).map(([key,label])=>
    `<label class="choice"><input type="checkbox" class="setup-job-type" value="${key}" ${selected.includes(key)?'checked':''}>${esc(label)}</label>`
  ).join('');
}

function renderSetupStep(){
  const p=state.data.profile||{};
  const body=document.getElementById('setup-body');
  document.getElementById('setup-prev').classList.toggle('hidden',state.setupStep===1);
  document.getElementById('setup-next').textContent=state.setupStep===3?'生成初始档案':'下一步';

  if(state.setupStep===1){
    body.innerHTML=`
      ${setupStepsHtml()}
      <div class="grid three">
        <div class="field">
          <label>当前学历</label>
          <input id="setup-education" class="input" value="${esc(p.education)}" placeholder="本科">
        </div>
        <div class="field">
          <label>专业</label>
          <input id="setup-major" class="input" value="${esc(p.major)}" placeholder="电子信息科学与技术">
        </div>
        <div class="field">
          <label>毕业年份</label>
          <input id="setup-graduation" class="input" type="number" min="2000" max="2100" value="${p.graduation_year??''}" placeholder="2027">
        </div>
        <div class="field full">
          <label>当前主要寻找什么</label>
          <div class="choice-row">${setupJobTypeChoices(p.target_job_types||[])}</div>
        </div>
      </div>
    `;
  }

  if(state.setupStep===2){
    const cities=(state.data.cities||[]).map(item=>item.city).join('、');
    body.innerHTML=`
      ${setupStepsHtml()}
      <div class="grid three">
        <div class="field">
          <label>最早可到岗时间</label>
          <input id="setup-available" class="input" value="${esc(p.available_from)}" placeholder="例如：2026年8月">
        </div>
        <div class="field">
          <label>每周最多到岗天数</label>
          <input id="setup-days" class="input" type="number" min="0" max="7" value="${p.max_days_per_week??''}">
        </div>
        <div class="field">
          <label>至少可连续实习月数</label>
          <input id="setup-months" class="input" type="number" min="0" max="36" value="${p.min_internship_months??''}">
        </div>
        <div class="field full">
          <label>可接受城市</label>
          <input id="setup-cities" class="input" value="${esc(cities)}" placeholder="例如：深圳、广州、香港">
          <span class="help">使用顿号、逗号或空格分隔；快速设置默认记为“重要偏好”，之后可改成硬条件。</span>
        </div>
        <label class="checkline"><input id="setup-remote" type="checkbox" ${p.accepts_remote?'checked':''}>接受远程岗位</label>
        <label class="checkline"><input id="setup-relocation" type="checkbox" ${p.accepts_relocation?'checked':''}>接受异地实习或搬迁</label>
      </div>
    `;
  }

  if(state.setupStep===3){
    const existingDirections=new Set((state.data.directions||[]).map(item=>item.direction));
    const directionCandidates=[
      ...(state.data.directions||[]).map(item=>({direction:item.direction,job_count:null,already:true,source:'user_confirmed',source_label:'已由用户确认'})),
      ...(state.directionSuggestions?.items||[]).filter(item=>!existingDirections.has(item.direction)).slice(0,10)
    ];
    const existingSkills=new Set((state.data.skills||[]).map(item=>item.skill_name));
    const skillCandidates=(state.skillSuggestions?.items||[]).filter(item=>!existingSkills.has(item.skill_name)).slice(0,12);

    body.innerHTML=`
      ${setupStepsHtml()}
      <div class="cold-note">${esc(state.skillSuggestions?.maturity?.message||'')} 当前建议模式：${state.skillSuggestions?.mode==='job_corpus'?'真实岗位语料':state.skillSuggestions?.mode==='blended'?'岗位语料 + 冷启动建议':'冷启动方向建议'}。推荐不等于掌握，仍需你本人勾选确认。</div>
      <div class="grid" style="margin-top:12px">
        <div class="card soft">
          <h3>优先方向</h3>
          <div class="choice-row">
            ${directionCandidates.map(item=>`
              <label class="choice">
                <input type="checkbox" class="setup-direction" value="${esc(item.direction)}" ${item.already?'checked':''}>
                <span>${esc(item.direction)}</span>${sourceBadge(item)}
              </label>
            `).join('')||'<span class="badge warn">暂无方向建议</span>'}
          </div>
        </div>

        <div class="card soft">
          <h3>确认真实具备的技能</h3>
          <div class="setup-skill-grid">
            ${skillCandidates.map(item=>`
              <div class="setup-skill">
                <input type="checkbox" class="setup-skill-check" data-name="${esc(item.skill_name)}">
                <div><strong>${esc(item.skill_name)}</strong><div class="onboarding-meta">${sourceBadge(item)}</div></div>
                <select class="select setup-skill-level">${optionHtml(labels.proficiency,'basic')}</select>
              </div>
            `).join('')||'<div class="empty">暂无新的技能建议。</div>'}
          </div>
          <p class="help" style="margin-top:10px">已有技能不会被删除；这里只补充新确认的技能。</p>
        </div>
      </div>
    `;
  }
}

function captureSetupStep(){
  const p=state.data.profile;

  if(state.setupStep===1){
    p.education=document.getElementById('setup-education').value.trim();
    p.major=document.getElementById('setup-major').value.trim();
    const graduation=document.getElementById('setup-graduation').value.trim();
    p.graduation_year=graduation===''?null:Number(graduation);
    p.target_job_types=[...document.querySelectorAll('.setup-job-type:checked')].map(input=>input.value);
  }

  if(state.setupStep===2){
    p.available_from=document.getElementById('setup-available').value.trim();
    const days=document.getElementById('setup-days').value.trim();
    const months=document.getElementById('setup-months').value.trim();
    p.max_days_per_week=days===''?null:Number(days);
    p.min_internship_months=months===''?null:Number(months);
    p.accepts_remote=document.getElementById('setup-remote').checked;
    p.accepts_relocation=document.getElementById('setup-relocation').checked;
    state.setupCities=document.getElementById('setup-cities').value;
  }
}

async function finishQuickSetup(){
  const p=state.data.profile;
  const directions=[...document.querySelectorAll('.setup-direction:checked')].map(input=>({
    direction:input.value,
    interest_level:'high'
  }));

  const existingDirections=(state.data.directions||[]).filter(item=>
    !directions.some(selected=>selected.direction.toLowerCase()===item.direction.toLowerCase())
  );
  const mergedDirections=[
    ...existingDirections.map(item=>({
      direction:item.direction,
      interest_level:item.interest_level
    })),
    ...directions
  ];

  const rawCities=state.setupCities??(state.data.cities||[]).map(item=>item.city).join('、');
  const cityNames=String(rawCities).split(/[、，,\s]+/).map(item=>item.trim()).filter(Boolean);
  const cities=[...new Set(cityNames)].map(city=>({city,constraint_level:'important'}));

  const selectedSkills=[...document.querySelectorAll('.setup-skill-check:checked')].map(input=>{
    const row=input.closest('.setup-skill');
    return {
      skill_name:input.dataset.name,
      proficiency_level:row.querySelector('.setup-skill-level').value
    };
  });

  const nextButton=document.getElementById('setup-next');
  nextButton.disabled=true;
  try{
    await Promise.all([
      api('/api/v1/profile',{
        method:'PATCH',
        body:{
          education:p.education,
          major:p.major,
          graduation_year:p.graduation_year,
          target_job_types:p.target_job_types||[],
          max_days_per_week:p.max_days_per_week,
          min_internship_months:p.min_internship_months,
          accepts_remote:Boolean(p.accepts_remote),
          accepts_relocation:Boolean(p.accepts_relocation),
          available_from:p.available_from||''
        }
      }),
      api('/api/v1/profile/cities',{method:'PUT',body:{cities}}),
      api('/api/v1/profile/preferences',{method:'PUT',body:{directions:mergedDirections}})
    ]);

    for(const skill of selectedSkills){
      await api('/api/v1/profile/skills',{method:'POST',body:skill});
    }

    localStorage.setItem(ONBOARDING_DISMISSED_KEY,'1');
    closeQuickSetup();
    toast('初始档案已生成。后续只需在发生变化时修改。');
    await loadAll();
  }catch(error){
    toast(error.message,true);
  }finally{
    nextButton.disabled=false;
  }
}

document.querySelectorAll('.tab').forEach(btn=>btn.addEventListener('click',()=>{
  state.tab=btn.dataset.tab;
  state.basicEditing=false;
  render();
}));

document.getElementById('onboarding-primary').addEventListener('click',openQuickSetup);
document.getElementById('refresh').addEventListener('click',loadAll);
document.getElementById('quick-setup').addEventListener('click',openQuickSetup);
document.getElementById('forget').addEventListener('click',()=>{
  localStorage.removeItem(TOKEN_KEY);
  state.token='';
  state.data=null;
  setConnection(false,'待配对');
  render();
});
document.getElementById('save-token').addEventListener('click',async()=>{
  const value=document.getElementById('token').value.trim();
  if(!value){
    toast('请粘贴 API 令牌。',true);
    return;
  }
  state.token=value;
  localStorage.setItem(TOKEN_KEY,value);
  await loadAll();
});

document.getElementById('setup-close').addEventListener('click',closeQuickSetup);
document.getElementById('setup-skip').addEventListener('click',()=>{
  localStorage.setItem(ONBOARDING_DISMISSED_KEY,'1');
  closeQuickSetup();
});
document.getElementById('setup-prev').addEventListener('click',()=>{
  captureSetupStep();
  if(state.setupStep>1)state.setupStep-=1;
  renderSetupStep();
});
document.getElementById('setup-next').addEventListener('click',async()=>{
  captureSetupStep();
  if(state.setupStep<3){
    state.setupStep+=1;
    renderSetupStep();
  }else{
    await finishQuickSetup();
  }
});
document.getElementById('setup-modal').addEventListener('click',event=>{
  if(event.target.id==='setup-modal')closeQuickSetup();
});

loadAll();
</script>
</body>
</html>"""


def render_profile_page() -> str:
    return HTML_TEMPLATE.replace("__PAGE_VERSION__", PAGE_VERSION)


# PHASE_81B_LOW_FRICTION_PROFILE_UI
# PHASE_81C_COLD_START_PROFILE_UI
