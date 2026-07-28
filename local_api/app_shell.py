from __future__ import annotations

# UNIFIED_APP_SHELL_V1

import html
import json
import os
import re
from typing import Any

from fastapi import Request
from starlette.responses import Response


SHELL_VERSION = "1.1.0"
SHELL_MARKER = 'id="jm-app-shell"'
SYSTEM_GLASS_MARKER = 'id="jm-system-glass-style"'

def _system_glass_enabled() -> bool:
    value = os.environ.get("JM_GLASS_MODE", "").strip().lower()
    return value in {"1", "true", "yes", "on", "system", "glass"}

EXCLUDED_PATHS = {
    "/launch",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/favicon.ico",
}

NAV_DEFINITIONS = (
    {
        "key": "decision",
        "label": "投递决策",
        "candidates": ("/decision",),
        "icon": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 13.5 10 19l10-14"/><path d="M4 5.5h7"/></svg>',
    },
    {
        "key": "manage",
        "label": "岗位管理",
        "candidates": ("/manage", "/jobs"),
        "icon": '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="7" width="18" height="13" rx="3"/><path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M3 12h18"/></svg>',
    },
    {
        "key": "dashboard",
        "label": "分析看板",
        "candidates": ("/dashboard", "/analytics", "/analysis"),
        "icon": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/></svg>',
    },
    {
        "key": "profile",
        "label": "个人档案",
        "candidates": ("/profile",),
        "icon": '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/></svg>',
    },
    {
        "key": "calibrate",
        "label": "人工校准",
        "candidates": ("/calibrate", "/calibration"),
        "icon": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 6h10M18 6h2M4 12h3M11 12h9M4 18h8M16 18h4"/><circle cx="16" cy="6" r="2"/><circle cx="9" cy="12" r="2"/><circle cx="14" cy="18" r="2"/></svg>',
    },
    {
        "key": "setup",
        "label": "扩展与设置",
        "candidates": ("/setup",),
        "icon": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8Z"/><path d="M4.9 4.9 7 7m10-2.1L15 7m4.1 12.1L17 17M4.9 19.1 7 17M2 12h3m14 0h3M12 2v3m0 14v3"/></svg>',
    },
)


def _available_paths(app: Any) -> set[str]:
    return {
        str(getattr(route, "path", ""))
        for route in getattr(app, "routes", ())
        if getattr(route, "path", None)
    }


def _resolve_nav(app: Any) -> list[dict[str, str]]:
    paths = _available_paths(app)
    resolved: list[dict[str, str]] = []
    for definition in NAV_DEFINITIONS:
        path = next(
            (candidate for candidate in definition["candidates"] if candidate in paths),
            None,
        )
        if path is None:
            continue
        resolved.append(
            {
                "key": str(definition["key"]),
                "label": str(definition["label"]),
                "path": path,
                "icon": str(definition["icon"]),
            }
        )
    return resolved


def _active_key(path: str, nav_items: list[dict[str, str]]) -> str:
    for item in nav_items:
        item_path = item["path"]
        if path == item_path or (item_path != "/" and path.startswith(item_path + "/")):
            return item["key"]
    return ""


def _nav_html(path: str, app: Any) -> tuple[str, list[str]]:
    nav_items = _resolve_nav(app)
    active_key = _active_key(path, nav_items)
    links: list[str] = []
    global_paths: list[str] = []
    for item in nav_items:
        global_paths.append(item["path"])
        active_class = " is-active" if item["key"] == active_key else ""
        current = ' aria-current="page"' if item["key"] == active_key else ""
        links.append(
            '<a class="jm-nav-item%s" href="%s" data-shell-nav="1"%s>'
            '<span class="jm-nav-icon">%s</span>'
            '<span class="jm-nav-label">%s</span>'
            "</a>"
            % (
                active_class,
                html.escape(item["path"], quote=True),
                current,
                item["icon"],
                html.escape(item["label"]),
            )
        )
    return "".join(links), global_paths


SHELL_STYLE = r'''
<style id="jm-unified-shell-style">
:root{
  --jm-sidebar-width:224px;
  --jm-sidebar-collapsed:82px;
  --jm-bg:#edf6f4;
  --jm-bg-2:#f4f3fb;
  --jm-glass:rgba(255,255,255,.68);
  --jm-line:rgba(125,151,157,.20);
  --jm-text:#17282d;
  --jm-muted:#6c7d84;
  --jm-accent:#2cae96;
  --jm-accent-dark:#16836f;
  --jm-shadow:0 24px 70px rgba(65,92,99,.13);
  --jm-card-shadow:0 12px 34px rgba(72,101,108,.08);
}
html{background:var(--jm-bg)}
body.jm-unified-shell-body{
  min-height:100vh;
  margin:0!important;
  overflow-x:hidden;
  color:var(--jm-text);
  background:
    radial-gradient(circle at 3% 9%,rgba(88,205,174,.20),transparent 28%),
    radial-gradient(circle at 88% 4%,rgba(153,166,244,.15),transparent 27%),
    linear-gradient(135deg,var(--jm-bg),#f8fbfb 48%,var(--jm-bg-2));
}
body.jm-unified-shell-body::before{
  content:"";
  position:fixed;
  inset:0;
  z-index:-2;
  pointer-events:none;
  background:
    radial-gradient(circle at 8% 82%,rgba(119,210,158,.13),transparent 28%),
    radial-gradient(circle at 82% 82%,rgba(126,197,235,.12),transparent 31%);
}
#jm-app-shell{
  display:grid;
  grid-template-columns:var(--jm-sidebar-width) minmax(0,1fr);
  width:100%;
  min-height:100vh;
  transition:grid-template-columns .24s cubic-bezier(.22,.8,.24,1);
}
#jm-app-shell.is-collapsed{grid-template-columns:var(--jm-sidebar-collapsed) minmax(0,1fr)}
#jm-sidebar{
  position:sticky;
  top:0;
  z-index:70;
  display:flex;
  flex-direction:column;
  height:100vh;
  padding:18px 14px 16px;
  border-right:1px solid rgba(255,255,255,.58);
  background:linear-gradient(180deg,rgba(255,255,255,.61),rgba(244,251,249,.46)),rgba(238,248,246,.54);
  box-shadow:12px 0 40px rgba(81,113,120,.08);
  backdrop-filter:blur(28px) saturate(145%);
  -webkit-backdrop-filter:blur(28px) saturate(145%);
}
.jm-brand{display:flex;align-items:center;gap:11px;min-height:56px;padding:5px 8px 16px;overflow:hidden}
.jm-brand-mark{
  flex:0 0 42px;
  width:42px;
  height:42px;
  display:grid;
  place-items:center;
  border:1px solid rgba(255,255,255,.78);
  border-radius:14px;
  color:white;
  background:radial-gradient(circle at 30% 26%,rgba(255,255,255,.55),transparent 28%),linear-gradient(145deg,#67d7bd,#26ae96);
  box-shadow:0 10px 22px rgba(36,169,143,.24),inset 0 1px 0 rgba(255,255,255,.62);
}
.jm-brand-mark svg{width:23px;height:23px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.jm-brand-copy{min-width:0;white-space:nowrap;transition:opacity .18s,transform .18s}
.jm-brand-copy strong{display:block;font-size:14px;line-height:1.4}
.jm-brand-copy span{display:block;margin-top:2px;color:var(--jm-muted);font-size:10px}
.jm-nav{display:grid;gap:6px;margin-top:6px}
.jm-nav-item{
  position:relative;
  display:flex;
  align-items:center;
  gap:12px;
  min-height:46px;
  padding:9px 11px;
  overflow:hidden;
  border:1px solid transparent;
  border-radius:14px;
  color:#52656b!important;
  text-decoration:none!important;
  font-size:13px;
  font-weight:650;
  white-space:nowrap;
  transition:background .18s,border-color .18s,color .18s,transform .18s,box-shadow .18s;
}
.jm-nav-item:hover{color:var(--jm-accent-dark)!important;background:rgba(255,255,255,.58);border-color:rgba(255,255,255,.74);transform:translateX(2px)}
.jm-nav-item.is-active{
  color:var(--jm-accent-dark)!important;
  border-color:rgba(255,255,255,.90);
  background:linear-gradient(135deg,rgba(255,255,255,.88),rgba(218,247,239,.72));
  box-shadow:0 10px 26px rgba(55,141,125,.11),inset 0 1px 0 rgba(255,255,255,.92);
}
.jm-nav-item.is-active::before{content:"";position:absolute;left:0;width:3px;height:22px;border-radius:0 4px 4px 0;background:var(--jm-accent)}
.jm-nav-icon{flex:0 0 22px;width:22px;height:22px;display:grid;place-items:center}
.jm-nav-icon svg{width:20px;height:20px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
.jm-nav-label{overflow:hidden;text-overflow:ellipsis;transition:opacity .18s,transform .18s}
.jm-sidebar-spacer{flex:1}
.jm-sidebar-status{
  margin-top:14px;
  padding:12px;
  border:1px solid rgba(255,255,255,.75);
  border-radius:16px;
  background:rgba(255,255,255,.48);
  box-shadow:inset 0 1px 0 rgba(255,255,255,.74);
  overflow:hidden;
}
.jm-status-line{display:flex;align-items:center;gap:8px;color:#4f646a;font-size:11px;font-weight:650;white-space:nowrap}
.jm-status-dot{flex:0 0 8px;width:8px;height:8px;border-radius:50%;background:#2fbea2;box-shadow:0 0 0 4px rgba(47,190,162,.12)}
.jm-status-meta{display:block;margin:7px 0 0 16px;color:var(--jm-muted);font-size:9px;white-space:nowrap}
.jm-collapse{display:flex;align-items:center;justify-content:center;width:100%;min-height:35px;margin-top:9px;border:1px solid rgba(255,255,255,.76);border-radius:11px;color:#65777d;background:rgba(255,255,255,.48);cursor:pointer}
.jm-collapse:hover{color:var(--jm-accent-dark);background:rgba(255,255,255,.76)}
.jm-collapse svg{width:17px;height:17px;fill:none;stroke:currentColor;stroke-width:2;transition:transform .22s}
#jm-app-shell.is-collapsed .jm-brand-copy,
#jm-app-shell.is-collapsed .jm-nav-label,
#jm-app-shell.is-collapsed .jm-sidebar-status{opacity:0;pointer-events:none;transform:translateX(-7px)}
#jm-app-shell.is-collapsed .jm-brand{padding-left:6px;padding-right:6px}
#jm-app-shell.is-collapsed .jm-nav-item{justify-content:center;padding-left:8px;padding-right:8px}
#jm-app-shell.is-collapsed .jm-collapse svg{transform:rotate(180deg)}
#jm-app-main{min-width:0;padding:18px 20px 48px}
#jm-app-main > .shell,
#jm-app-main > main.shell,
#jm-app-main > .container,
#jm-app-main > main.container{width:100%!important;max-width:none!important;margin:0!important;padding:0 0 60px!important}
#jm-app-main .top{
  top:10px!important;
  border-color:rgba(255,255,255,.72)!important;
  border-radius:20px!important;
  background:rgba(255,255,255,.72)!important;
  box-shadow:var(--jm-card-shadow)!important;
  backdrop-filter:blur(25px) saturate(135%)!important;
  -webkit-backdrop-filter:blur(25px) saturate(135%)!important;
}
#jm-app-main .panel,
#jm-app-main .metric,
#jm-app-main .card,
#jm-app-main .calibration{border-color:rgba(132,158,164,.18)!important;background:rgba(255,255,255,.78)!important;box-shadow:var(--jm-card-shadow)!important;backdrop-filter:blur(18px) saturate(122%);-webkit-backdrop-filter:blur(18px) saturate(122%)}
#jm-app-main .btn,#jm-app-main button,#jm-app-main input,#jm-app-main select,#jm-app-main textarea{transition:border-color .16s,background .16s,box-shadow .16s,transform .16s}
#jm-app-main .btn:hover,#jm-app-main button:hover{transform:translateY(-1px)}
#jm-app-main .btn.primary,#jm-app-main button.primary{background:linear-gradient(145deg,#35b89f,#168b77)!important;border-color:transparent!important;box-shadow:0 8px 18px rgba(27,148,124,.18)}
#jm-app-main .jm-hide-global-link{display:none!important}
#jm-mobile-toggle{
  display:none;
  position:fixed;
  left:14px;
  top:14px;
  z-index:95;
  width:42px;
  height:42px;
  border:1px solid rgba(255,255,255,.85);
  border-radius:13px;
  color:#36545a;
  background:rgba(255,255,255,.78);
  box-shadow:0 10px 28px rgba(73,100,108,.15);
  backdrop-filter:blur(20px);
}
#jm-mobile-toggle svg{width:20px;height:20px;fill:none;stroke:currentColor;stroke-width:2}

/* MARKET_DASHBOARD_INTEGRATION_V1 */
#jm-market-layout{
  display:grid;
  grid-template-columns:190px minmax(0,1fr);
  gap:16px;
  align-items:start;
  min-width:0;
}
#jm-market-content{min-width:0}
body.jm-market-integrated #jm-app-main{padding:18px 18px 48px}
body.jm-market-integrated #jm-market-layout #ux-sidebar{
  position:sticky!important;
  left:auto!important;
  right:auto!important;
  top:18px!important;
  bottom:auto!important;
  width:100%!important;
  height:calc(100vh - 36px)!important;
  min-height:480px;
  transform:none!important;
  z-index:35!important;
  border-radius:18px!important;
  box-shadow:0 16px 44px rgba(68,98,105,.10)!important;
}
body.jm-market-integrated #jm-market-layout .ux-sidebar-head{padding:17px 14px 13px}
body.jm-market-integrated #jm-market-layout .ux-sidebar-kicker{font-size:9px}
body.jm-market-integrated #jm-market-layout .ux-sidebar-title{font-size:17px}
body.jm-market-integrated #jm-market-layout .ux-sidebar-summary{margin-top:7px}
body.jm-market-integrated #jm-market-layout .ux-toc{padding:9px}
body.jm-market-integrated #jm-market-layout .ux-toc-link{
  gap:8px;
  margin:2px 0;
  padding:9px 9px;
  font-size:12px;
}
body.jm-market-integrated #jm-market-layout .ux-toc-index{width:20px}
body.jm-market-integrated #jm-market-layout .ux-sidebar-footer{padding:9px}
body.jm-market-integrated #jm-market-content > .page{
  width:100%!important;
  max-width:none!important;
  margin:0!important;
  padding:0 0 64px!important;
}
body.jm-market-route #job-management-link{display:none!important}
body.jm-market-route #ux-sidebar{visibility:hidden}
body.jm-market-integrated #ux-sidebar{visibility:visible}
body.jm-market-integrated #ux-mobile-toc-button{display:none!important}
body.jm-market-integrated #ux-livebar{top:10px}
@media(max-width:1080px){
  #jm-market-layout{grid-template-columns:1fr}
  body.jm-market-integrated #jm-market-layout #ux-sidebar{
    position:sticky!important;
    top:10px!important;
    height:auto!important;
    min-height:0;
    display:block!important;
    transform:none!important;
  }
  body.jm-market-integrated #jm-market-layout .ux-sidebar-head{
    display:flex;
    align-items:center;
    gap:12px;
    padding:11px 13px;
  }
  body.jm-market-integrated #jm-market-layout .ux-sidebar-kicker,
  body.jm-market-integrated #jm-market-layout .ux-sidebar-summary{display:none}
  body.jm-market-integrated #jm-market-layout .ux-sidebar-title{
    flex:0 0 auto;
    font-size:14px;
  }
  body.jm-market-integrated #jm-market-layout .ux-toc{
    display:flex;
    gap:6px;
    overflow-x:auto;
    padding:8px 10px 10px;
  }
  body.jm-market-integrated #jm-market-layout .ux-toc-link{
    flex:0 0 auto;
    margin:0;
    white-space:nowrap;
  }
  body.jm-market-integrated #jm-market-layout .ux-sidebar-footer{display:none}
}

@media(max-width:1120px){:root{--jm-sidebar-width:202px}#jm-app-main{padding-left:14px;padding-right:14px}}
@media(max-width:820px){
  #jm-app-shell{display:block}
  #jm-sidebar{position:fixed;left:0;top:0;width:min(82vw,280px);transform:translateX(-104%);transition:transform .24s cubic-bezier(.22,.8,.24,1)}
  #jm-app-shell.is-mobile-open #jm-sidebar{transform:translateX(0)}
  #jm-app-main{padding:66px 10px 38px}
  #jm-mobile-toggle{display:grid;place-items:center}
  #jm-app-shell.is-mobile-open::after{content:"";position:fixed;inset:0;z-index:60;background:rgba(29,45,50,.22);backdrop-filter:blur(3px)}
}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{scroll-behavior:auto!important;transition:none!important;animation-duration:.01ms!important}}
</style>
'''



SYSTEM_GLASS_STYLE = r"""
<style id="jm-system-glass-style">
html{
  background:transparent!important;
}
body.jm-unified-shell-body.jm-system-glass{
  --jm-glass:rgba(255,255,255,.34);
  --jm-line:rgba(255,255,255,.42);
  --jm-shadow:0 28px 78px rgba(25,43,49,.20);
  --jm-card-shadow:0 16px 46px rgba(29,49,55,.14);
  background:transparent!important;
}
body.jm-system-glass::before{
  display:none!important;
  background:none!important;
}
body.jm-system-glass #jm-app-shell,
body.jm-system-glass #jm-app-main{
  background:transparent!important;
}
body.jm-system-glass #jm-sidebar{
  border-right-color:rgba(255,255,255,.48)!important;
  background:
    linear-gradient(180deg,rgba(255,255,255,.30),rgba(235,248,244,.14))!important;
  box-shadow:
    12px 0 44px rgba(21,42,48,.13),
    inset -1px 0 0 rgba(255,255,255,.24)!important;
  backdrop-filter:blur(42px) saturate(155%)!important;
  -webkit-backdrop-filter:blur(42px) saturate(155%)!important;
}
body.jm-system-glass .jm-nav-item:hover,
body.jm-system-glass .jm-collapse,
body.jm-system-glass .jm-sidebar-status{
  background:rgba(255,255,255,.30)!important;
}
body.jm-system-glass .jm-nav-item.is-active{
  border-color:rgba(255,255,255,.60)!important;
  background:
    linear-gradient(135deg,rgba(255,255,255,.55),rgba(188,239,224,.31))!important;
}
body.jm-system-glass #jm-app-main .top{
  border-color:rgba(255,255,255,.56)!important;
  background:rgba(255,255,255,.39)!important;
  box-shadow:0 18px 48px rgba(28,48,54,.13)!important;
  backdrop-filter:blur(34px) saturate(145%)!important;
  -webkit-backdrop-filter:blur(34px) saturate(145%)!important;
}
body.jm-system-glass #jm-app-main .panel,
body.jm-system-glass #jm-app-main .metric,
body.jm-system-glass #jm-app-main .card,
body.jm-system-glass #jm-app-main .calibration{
  border-color:rgba(255,255,255,.48)!important;
  background:rgba(255,255,255,.45)!important;
  box-shadow:0 18px 50px rgba(29,48,54,.14)!important;
  backdrop-filter:blur(30px) saturate(140%)!important;
  -webkit-backdrop-filter:blur(30px) saturate(140%)!important;
}
body.jm-system-glass #jm-app-main input,
body.jm-system-glass #jm-app-main select,
body.jm-system-glass #jm-app-main textarea,
body.jm-system-glass #jm-app-main button:not(.primary){
  border-color:rgba(255,255,255,.48)!important;
  background:rgba(255,255,255,.42)!important;
}
body.jm-system-glass #jm-market-layout #ux-sidebar{
  border-color:rgba(255,255,255,.48)!important;
  background:rgba(255,255,255,.31)!important;
  backdrop-filter:blur(38px) saturate(150%)!important;
  -webkit-backdrop-filter:blur(38px) saturate(150%)!important;
}
body.jm-system-glass #jm-market-content > .page{
  background:transparent!important;
}
</style>
"""


def _shell_open(nav_links: str) -> str:
    return f'''
<button id="jm-mobile-toggle" type="button" aria-label="打开导航">
  <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg>
</button>
<div id="jm-app-shell">
  <aside id="jm-sidebar" aria-label="应用导航">
    <div class="jm-brand">
      <span class="jm-brand-mark">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12.5 10 17l9-10"/><circle cx="12" cy="12" r="9"/></svg>
      </span>
      <span class="jm-brand-copy">
        <strong>招聘市场分析与<br>投递决策系统</strong>
        <span>本地优先 · 可解释决策</span>
      </span>
    </div>
    <nav class="jm-nav">{nav_links}</nav>
    <div class="jm-sidebar-spacer"></div>
    <div class="jm-sidebar-status">
      <span class="jm-status-line"><i class="jm-status-dot"></i>本地服务已连接</span>
      <span class="jm-status-meta">统一桌面界面 · {SHELL_VERSION}</span>
    </div>
    <button class="jm-collapse" id="jm-collapse" type="button" aria-label="折叠导航">
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m15 18-6-6 6-6"/></svg>
    </button>
  </aside>
  <main id="jm-app-main">
'''


SHELL_SCRIPT_TEMPLATE = r'''
<script id="jm-unified-shell-script">
(() => {
  const shell = document.getElementById("jm-app-shell");
  const collapse = document.getElementById("jm-collapse");
  const mobile = document.getElementById("jm-mobile-toggle");
  if (!shell) return;

  const globalPaths = new Set(__GLOBAL_PATHS__);
  const storageKey = "jm.desktop.sidebar.collapsed";
  if (localStorage.getItem(storageKey) === "1") shell.classList.add("is-collapsed");

  collapse?.addEventListener("click", () => {
    shell.classList.toggle("is-collapsed");
    localStorage.setItem(storageKey, shell.classList.contains("is-collapsed") ? "1" : "0");
  });

  mobile?.addEventListener("click", () => shell.classList.toggle("is-mobile-open"));

  document.addEventListener("click", (event) => {
    const anchor = event.target.closest("a[href]");
    if (!anchor) {
      if (shell.classList.contains("is-mobile-open") && !event.target.closest("#jm-sidebar")) {
        shell.classList.remove("is-mobile-open");
      }
      return;
    }

    let url;
    try {
      url = new URL(anchor.getAttribute("href"), location.href);
    } catch {
      return;
    }

    if (url.origin === location.origin) {
      anchor.removeAttribute("target");
      if (anchor.dataset.shellNav === "1") {
        event.preventDefault();
        location.assign(url.pathname + url.search + url.hash);
      }
      shell.classList.remove("is-mobile-open");
      return;
    }

    anchor.setAttribute("target", "_blank");
    anchor.setAttribute("rel", "noopener noreferrer");
  });

  const normalizePath = (value) => {
    try { return new URL(value, location.href).pathname; }
    catch { return ""; }
  };

  document.querySelectorAll('a[href]').forEach((anchor) => {
    const path = normalizePath(anchor.getAttribute("href"));
    let sameOrigin = false;
    try { sameOrigin = new URL(anchor.getAttribute("href"), location.href).origin === location.origin; }
    catch { sameOrigin = false; }

    if (sameOrigin) anchor.removeAttribute("target");

    if (
      sameOrigin &&
      globalPaths.has(path) &&
      !anchor.closest("#jm-sidebar") &&
      anchor.closest(".top, header, .actions, .nav, .navigation")
    ) {
      anchor.classList.add("jm-hide-global-link");
    }
  });

  const integrateMarketDashboard = () => {
    if (location.pathname !== "/dashboard") return;

    const appMain = document.getElementById("jm-app-main");
    const page = appMain?.querySelector(":scope > .page") || appMain?.querySelector(".page");
    const marketNav = document.getElementById("ux-sidebar");
    if (!appMain || !page || !marketNav || document.getElementById("jm-market-layout")) return;

    document.body.classList.add("jm-market-integrated");
    marketNav.setAttribute("aria-label", "市场分析子导航");

    const kicker = marketNav.querySelector(".ux-sidebar-kicker");
    const title = marketNav.querySelector(".ux-sidebar-title");
    if (kicker) kicker.textContent = "MARKET ANALYSIS";
    if (title) title.textContent = "市场分析";

    document.getElementById("job-management-link")?.remove();

    const layout = document.createElement("div");
    layout.id = "jm-market-layout";

    const content = document.createElement("div");
    content.id = "jm-market-content";

    appMain.insertBefore(layout, page);
    layout.append(marketNav, content);
    content.append(page);
  };

  integrateMarketDashboard();
})();
</script>
'''


def inject_app_shell(document: str, path: str, app: Any) -> str:
    if SHELL_MARKER in document:
        return document
    if "<html" not in document.lower() or "<body" not in document.lower():
        return document

    nav_links, global_paths = _nav_html(path, app)
    if not nav_links:
        return document

    script = SHELL_SCRIPT_TEMPLATE.replace(
        "__GLOBAL_PATHS__",
        json.dumps(global_paths, ensure_ascii=False),
    )

    if re.search(r"</head\s*>", document, flags=re.IGNORECASE):
        document = re.sub(
            r"</head\s*>",
            SHELL_STYLE
            + (SYSTEM_GLASS_STYLE if _system_glass_enabled() else "")
            + "\n</head>",
            document,
            count=1,
            flags=re.IGNORECASE,
        )
    else:
        document = (
            SHELL_STYLE
            + (SYSTEM_GLASS_STYLE if _system_glass_enabled() else "")
            + document
        )

    body_pattern = re.compile(r"<body(?P<attrs>[^>]*)>", flags=re.IGNORECASE)
    match = body_pattern.search(document)
    if match is None:
        return document

    attrs = match.group("attrs")
    route_class = " jm-market-route" if path == "/dashboard" else ""
    if _system_glass_enabled():
        route_class += " jm-system-glass"
    if re.search(r"\bclass=", attrs, flags=re.IGNORECASE):
        attrs = re.sub(
            r'class=(["\'])(.*?)\1',
            lambda item: (
                f'class={item.group(1)}{item.group(2)} '
                f'jm-unified-shell-body{route_class}{item.group(1)}'
            ),
            attrs,
            count=1,
            flags=re.IGNORECASE,
        )
    else:
        attrs += f' class="jm-unified-shell-body{route_class}"'

    replacement = f"<body{attrs}>\n{_shell_open(nav_links)}"
    document = document[: match.start()] + replacement + document[match.end() :]

    close = "\n  </main>\n</div>\n" + script + "\n</body>"
    document = re.sub(
        r"</body\s*>",
        close,
        document,
        count=1,
        flags=re.IGNORECASE,
    )
    return document


def _is_html_response(response: Response) -> bool:
    return "text/html" in response.headers.get("content-type", "").lower()


def _should_wrap(path: str) -> bool:
    if path in EXCLUDED_PATHS:
        return False
    if path.startswith("/api/") or path.startswith("/static/"):
        return False
    return True


def install_unified_app_shell(app: Any) -> None:
    if getattr(app.state, "unified_app_shell_installed", False):
        return
    app.state.unified_app_shell_installed = True

    @app.middleware("http")
    async def unified_app_shell_middleware(request: Request, call_next: Any) -> Response:
        response = await call_next(request)
        if request.method != "GET" or not _should_wrap(request.url.path):
            return response
        if response.status_code >= 400 or not _is_html_response(response):
            return response

        if hasattr(response, "body_iterator"):
            chunks = [chunk async for chunk in response.body_iterator]
            body = b"".join(
                chunk.encode("utf-8") if isinstance(chunk, str) else chunk
                for chunk in chunks
            )
        else:
            body = bytes(getattr(response, "body", b""))

        try:
            document = body.decode("utf-8")
        except UnicodeDecodeError:
            return response

        transformed = inject_app_shell(document, request.url.path, request.app)
        headers = dict(response.headers)
        headers.pop("content-length", None)
        content = transformed.encode("utf-8") if transformed != document else body
        return Response(
            content=content,
            status_code=response.status_code,
            headers=headers,
            media_type="text/html",
            background=response.background,
        )
