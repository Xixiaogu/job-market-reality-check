from __future__ import annotations

import html
import json


ALLOWED_NEXT_PATHS = {
    "/setup",
    "/decision",
    "/manage",
    "/profile",
    "/calibrate",
}


def _safe_next_path(value: str) -> str:
    return value if value in ALLOWED_NEXT_PATHS else "/decision"


def render_launch_page(next_path: str) -> str:
    safe_next = _safe_next_path(next_path)
    next_json = json.dumps(safe_next, ensure_ascii=False)
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>正在启动</title>
<style>body{{font-family:Segoe UI,Microsoft YaHei,sans-serif;background:#f5f7fb;color:#172033;display:grid;place-items:center;min-height:100vh;margin:0}}main{{background:#fff;border:1px solid #dfe5ef;border-radius:18px;padding:32px;box-shadow:0 16px 50px rgba(23,32,51,.10);text-align:center;max-width:520px}}.dot{{width:14px;height:14px;border-radius:50%;background:#2f6fed;display:inline-block;animation:p 1s infinite alternate}}@keyframes p{{to{{opacity:.35;transform:scale(.75)}}}}</style></head>
<body><main><span class="dot"></span><h1>招聘市场分析与投递决策系统</h1><p id="message">正在完成本地安全配对……</p></main>
<script>(()=>{{'use strict';const KEY='jobMarketApiTokenV1';const params=new URLSearchParams(location.hash.slice(1));const token=params.get('token');if(token){{localStorage.setItem(KEY,token)}}history.replaceState(null,'',location.pathname+location.search);const next={next_json};document.getElementById('message').textContent=token?'配对完成，正在进入系统……':'正在进入系统……';setTimeout(()=>location.replace(next),120);}})();</script></body></html>"""


def render_setup_page() -> str:
    return """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>首次启动设置</title>
<style>
:root{--bg:#f4f7fb;--card:#fff;--line:#dfe6ef;--text:#172033;--muted:#667085;--blue:#2f6fed;--green:#16835b;--amber:#b36900;--red:#b42318}*{box-sizing:border-box}body{margin:0;background:var(--bg);font-family:Segoe UI,Microsoft YaHei,sans-serif;color:var(--text)}main{width:min(1120px,calc(100% - 32px));margin:28px auto 60px}.hero{display:flex;justify-content:space-between;gap:20px;align-items:flex-start;margin-bottom:18px}.hero h1{margin:0 0 8px;font-size:30px}.hero p{margin:0;color:var(--muted);line-height:1.7}.badge{background:#eaf1ff;color:#174ea6;border-radius:999px;padding:8px 12px;font-weight:700}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:18px 0}.metric,.card{background:var(--card);border:1px solid var(--line);border-radius:16px;box-shadow:0 8px 24px rgba(23,32,51,.05)}.metric{padding:16px}.metric small{display:block;color:var(--muted);margin-bottom:7px}.metric strong{font-size:18px}.card{padding:22px;margin-top:14px}.card h2{margin:0 0 10px;font-size:20px}.card p,.card li{color:var(--muted);line-height:1.75}.steps{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}.step{border:1px solid var(--line);border-radius:14px;padding:17px;background:#fbfcfe}.step b{display:block;margin-bottom:7px}.num{display:inline-grid;place-items:center;width:28px;height:28px;border-radius:50%;background:#eaf1ff;color:#174ea6;margin-right:8px}.actions{display:flex;flex-wrap:wrap;gap:10px;margin-top:14px}.btn{border:1px solid #cbd5e1;background:#fff;color:#25324a;border-radius:10px;padding:10px 14px;font-weight:700;cursor:pointer}.btn.primary{background:var(--blue);border-color:var(--blue);color:#fff}.btn.good{background:var(--green);border-color:var(--green);color:#fff}.btn:disabled{opacity:.55;cursor:not-allowed}.path{font-family:Consolas,monospace;background:#f1f4f8;border-radius:8px;padding:9px 10px;word-break:break-all;color:#334155}.notice{border-left:4px solid var(--amber);background:#fff8e8;padding:12px 14px;border-radius:8px;color:#6d4500}.pair{display:none}.pair.show{display:block}.pair input{width:min(520px,100%);padding:10px 12px;border:1px solid #cbd5e1;border-radius:9px}.ok{color:var(--green)}.warn{color:var(--amber)}.bad{color:var(--red)}#toast{position:fixed;right:20px;bottom:20px;background:#172033;color:#fff;padding:12px 16px;border-radius:10px;opacity:0;transform:translateY(8px);transition:.2s;pointer-events:none}#toast.show{opacity:1;transform:none}@media(max-width:850px){.grid{grid-template-columns:repeat(2,1fr)}.steps{grid-template-columns:1fr}.hero{display:block}.badge{display:inline-block;margin-top:12px}}@media(max-width:520px){.grid{grid-template-columns:1fr}}
</style></head>
<body><main>
<section class="hero"><div><h1>首次启动设置</h1><p>桌面程序、本地数据库和浏览器扩展共同组成完整系统。v1.0 的扩展已经随软件目录附带，不需要另找下载链接。</p></div><span class="badge">Phase 9.1</span></section>
<section class="grid"><div class="metric"><small>本地服务</small><strong id="service" class="ok">已启动</strong></div><div class="metric"><small>扩展安装包</small><strong id="bundle">检测中</strong></div><div class="metric"><small>扩展连接</small><strong id="connection">检测中</strong></div><div class="metric"><small>已有岗位</small><strong id="jobs">—</strong></div></section>
<section id="pair" class="card pair"><h2>手动配对</h2><p>当前页面没有收到桌面启动器传入的令牌。粘贴本地 API 令牌后继续。</p><input id="token-input" type="password" placeholder="粘贴本地 API 令牌"><div class="actions"><button id="save-token" class="btn primary">保存令牌</button></div></section>
<section class="card"><h2>浏览器扩展安装</h2><div class="notice">Chrome 和 Edge 不允许普通网页静默安装本地扩展。当前版本采用“软件包内置扩展目录 + 开发者模式加载”，后续商店版再改为一键跳转商店。</div><div class="steps">
<div class="step"><b><span class="num">1</span>打开扩展文件夹</b><p>点击下面按钮，确认目录中存在 <code>manifest.json</code>。</p><div id="extension-path" class="path">正在读取……</div><div class="actions"><button id="open-extension" class="btn primary">打开扩展目录</button></div></div>
<div class="step"><b><span class="num">2</span>打开扩展管理页</b><p>复制地址到 Chrome 或 Edge 地址栏，开启“开发者模式”。</p><div class="path">chrome://extensions</div><div class="actions"><button id="copy-extensions-url" class="btn">复制管理页地址</button></div></div>
<div class="step"><b><span class="num">3</span>加载已解压扩展</b><p>点击“加载已解压的扩展程序”，选择第1步打开的目录。</p></div>
<div class="step"><b><span class="num">4</span>配置本地令牌</b><p>在扩展设置中填入本地 API 地址 <code>http://127.0.0.1:8765</code> 和令牌。</p><div class="actions"><button id="copy-token" class="btn">复制 API 令牌</button></div></div>
</div></section>
<section class="card"><h2>数据与连接检查</h2><p>安装扩展后，在任意支持的岗位详情页采集一条岗位，再点击“重新检测”。已有历史岗位只说明数据已迁移，不等于当前扩展一定在线。</p><div id="data-path" class="path">正在读取……</div><div class="actions"><button id="refresh" class="btn">重新检测</button><button id="open-data" class="btn">打开用户数据目录</button><button id="complete" class="btn good">完成设置并进入决策中心</button></div></section>
</main><div id="toast"></div>
<script>(()=>{'use strict';const KEY='jobMarketApiTokenV1';let token=localStorage.getItem(KEY)||'';const $=id=>document.getElementById(id);const toast=m=>{const e=$('toast');e.textContent=m;e.classList.add('show');setTimeout(()=>e.classList.remove('show'),2600)};function headers(){return {'Content-Type':'application/json','X-Job-Market-Token':token}}async function api(path,opt={}){const r=await fetch(path,{...opt,headers:{...headers(),...(opt.headers||{})},cache:'no-store'});let p={};try{p=await r.json()}catch{}if(!r.ok)throw new Error(p.detail||('HTTP '+r.status));return p}function showPair(){if(!token)$('pair').classList.add('show')}function connectionText(s){if(s==='active')return['当前扩展已连接','ok'];if(s==='data_detected')return['检测到历史岗位','warn'];return['尚未检测到','bad']}async function load(){if(!token){showPair();return}try{const d=await api('/api/v1/desktop/status');$('extension-path').textContent=d.extension_dir;$('data-path').textContent=d.user_data_root;$('bundle').textContent=d.extension_bundle_exists?'已随软件附带':'未找到';$('bundle').className=d.extension_bundle_exists?'ok':'bad';const c=connectionText(d.extension_state);$('connection').textContent=c[0];$('connection').className=c[1];$('jobs').textContent=String(d.job_count??0);$('open-extension').disabled=!d.extension_bundle_exists}catch(e){if(String(e.message).includes('401')){token='';localStorage.removeItem(KEY);showPair()}toast('读取状态失败：'+e.message)}}$('save-token').onclick=()=>{const v=$('token-input').value.trim();if(!v)return;token=v;localStorage.setItem(KEY,v);$('pair').classList.remove('show');load()};$('copy-token').onclick=async()=>{if(!token){showPair();return}await navigator.clipboard.writeText(token);toast('API 令牌已复制')};$('copy-extensions-url').onclick=async()=>{await navigator.clipboard.writeText('chrome://extensions');toast('扩展管理页地址已复制')};$('open-extension').onclick=async()=>{try{await api('/api/v1/desktop/open-extension-folder',{method:'POST'});toast('扩展目录已打开')}catch(e){toast(e.message)}};$('open-data').onclick=async()=>{try{await api('/api/v1/desktop/open-user-data-folder',{method:'POST'});toast('用户数据目录已打开')}catch(e){toast(e.message)}};$('refresh').onclick=load;$('complete').onclick=async()=>{try{await api('/api/v1/desktop/complete-setup',{method:'POST'});location.href='/decision'}catch(e){toast(e.message)}};showPair();load()})();</script></body></html>"""
