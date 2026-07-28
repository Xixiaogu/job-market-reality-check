# Phase 9.1 桌面启动器与双模式运行

## 目标

将项目从“必须打开 PowerShell 启动 FastAPI”改造成可双击启动的 Windows 本地软件基础架构，同时保留开发模式。

## 两种运行方式

### 开发模式

```powershell
.\run_local_api.ps1
```

继续使用仓库内的 `data/`、`local_api/runtime/` 和 `output/`，便于调试。

### 桌面模式

```powershell
python .\desktop_launcher.py
```

使用：

```text
%LOCALAPPDATA%\JobMarketDecisionSystem\
├─ data\job_market.db
├─ runtime\api_token.txt
├─ logs\app.log
├─ output\
├─ exports\
└─ backups\
```

首次桌面启动会在目标目录为空时安全迁移现有 SQLite 数据库和 API Token。

## 首次启动流程

桌面启动器会：

1. 建立用户数据目录；
2. 迁移旧数据库与 Token；
3. 检查单实例和端口占用；
4. 启动 Uvicorn；
5. 通过 URL fragment 将 Token 写入当前浏览器的 localStorage；
6. 打开 `/setup` 首次安装页；
7. 引导加载随软件附带的 Chrome MV3 扩展。

Token 放在 URL fragment 中，不会发送到 FastAPI 服务端访问日志；页面写入 localStorage 后立即清除 fragment。

## 浏览器扩展目录

开发模式按以下顺序查找：

```text
extension/.output/chrome-mv3
extension/.output/chrome-mv3-dev
browser-extension/chrome-mv3
```

打包模式优先使用：

```text
browser-extension/chrome-mv3
```

Phase 9.2 构建脚本会把扩展复制到正式发行目录。
