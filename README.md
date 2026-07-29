# Job Market Reality Check

一个本地优先的求职决策桌面系统。它把浏览器岗位采集、本地数据管理、市场分析、个人档案、人工校准、岗位优先级判断和投递状态跟踪连接成完整闭环。

当前桌面基线版本为 **v1.0.7**。桌面业务逻辑与评分引擎已冻结，后续主线是在稳定的本地 API 上开发只读 Job Market Skill。

## 当前状态

- Windows 桌面程序、ZIP 发布包和浏览器扩展已经可用；
- FastAPI 只监听 `127.0.0.1`，岗位、档案和决策数据保存在本机 SQLite；
- 决策中心提供 `apply_now`、`stretch`、`prepare_first`、`defer` 四档行动建议；
- Windows Acrylic 与标准浅色外观已经产品化；
- 可移植文件型 Skill 已存在；桌面 API 集成已完成 0.1 只读客户端和 `brief` 上下文闭环；
- 本项目适合作为求职作品集和本地演示产品，尚不是商业级自动求职软件。

## 产品闭环

```text
招聘网页
  → 浏览器扩展采集
  → 本地 FastAPI
  → SQLite 事实与状态
  → 市场分析与个人档案
  → 人工校准
  → 可解释岗位决策
  → 投递队列与状态跟踪
```

职责边界：

| 组件 | 职责 |
|---|---|
| 浏览器扩展 | 从招聘页面采集岗位并发送到本机 |
| FastAPI + SQLite | 保存岗位事实、个人档案、人工状态和决策结果 |
| 桌面程序 | 统一展示岗位管理、市场分析、档案、校准、决策和设置 |
| Job Market Skill | 读取事实，生成解释、比较和行动计划；不重复实现数据库与评分引擎 |

## 主要能力

- BOSS 直聘岗位页面采集和本地去重；
- 岗位列表、详情、归档、备注和投递状态管理；
- 薪资、城市、学历、招聘类型、技能要求和异常文本清洗；
- 市场样本统计与可筛选分析看板；
- 个人技能、项目证据、求职方向和地点约束档案；
- 代表岗位人工校准；
- 可解释的岗位匹配、机会价值、准备成本和风险分析；
- 四档投递优先级和待办队列；
- 分析自动刷新与决策重算；
- 标准浅色和 Windows Acrylic 外观；
- Windows 独立程序、ZIP 发布包和安装程序。

## 直接使用 Windows 版本

### 安装程序

运行：

```text
release\installer\JobMarketDecisionSystem-Setup-v1.0.7.exe
```

安装程序按当前用户安装，不要求管理员权限。卸载程序不会删除用户数据。

### 免安装 ZIP

解压：

```text
release\JobMarketDecisionSystem-v1.0.7-desktop-windows-x64.zip
```

然后双击：

```text
JobMarketDecisionSystem.exe
```

首次启动后，在“扩展与设置”中按照提示加载：

```text
browser-extension\chrome-mv3
```

## 用户数据与安全

桌面模式的用户数据默认位于：

```text
%LOCALAPPDATA%\JobMarketDecisionSystem
├─ data\job_market.db
├─ runtime\api_token.txt
├─ logs\app.log
├─ exports\
└─ backups\
```

- 本地服务只监听 `127.0.0.1:8765`；
- 除健康接口外，API 需要 `X-Job-Market-Token` 请求头；
- 发布包不包含开发者的数据库、令牌、岗位导出或个人档案；
- 不要提交或分享 `api_token.txt`；
- 替换程序目录或升级版本不会覆盖用户数据。

## 开发模式

推荐使用项目环境：

```powershell
conda activate base_science
python -m pip install -r .\requirements-local-api.txt
```

启动本地 API 与浏览器界面：

```powershell
.\run_local_api.ps1
```

启动桌面模式：

```powershell
python .\desktop_launcher.py
```

开发模式 API 文档：

```text
http://127.0.0.1:8765/docs
```

## 浏览器扩展开发

```powershell
Set-Location .\extension
npm install
npm run build
```

构建结果位于：

```text
extension\.output\chrome-mv3
```

## 构建发布物

生成 v1.0.7 桌面目录和 ZIP：

```powershell
.\build_windows_desktop_shell.ps1 -Version 1.0.7
```

基于相同桌面目录生成安装程序：

```powershell
.\build_windows_installer.ps1 -Version 1.0.7
```

安装器 smoke test 会执行真实的当前用户静默安装与卸载，因此需要写入用户级开始菜单和卸载注册表。

## 统一验收

运行完整基线测试：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\run_baseline_tests.ps1 -Version 1.0.7
```

测试入口依次验证：

1. 核心离线与 UI 契约；
2. 可移植 Skill 工作流；
3. 基于数据库副本的本地 API；
4. 桌面运行模式；
5. 打包后的 v1.0.7 EXE；
6. v1.0.7 安装、启动检查、卸载和用户数据保留。

只验证源码和 API、跳过发布物时可以使用：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\run_baseline_tests.ps1 `
  -Version 1.0.7 -SkipPackaged -SkipInstaller
```

## Skill 集成

当前可移植 Skill 位于：

```text
skills\job-market-reality-check
```

它可以直接分析 CSV、JSON 或 JSONL 文件。计划中的桌面集成型 Skill 必须复用本地 API，不得直接操作 SQLite。

Skill 0.1 可以在桌面服务运行时读取一致的求职简报上下文：

```powershell
python .\skills\job-market-reality-check\scripts\local_api_client.py health
python .\skills\job-market-reality-check\scripts\local_api_client.py brief
```

客户端只接受本机地址，只发送 `GET` 请求，并检查分页和决策运行一致性。

固定的只读接口、字段、鉴权和版本规则见：

```text
docs\skill-v1-local-api-contract.md
```

## 当前限制

- 浏览器扩展需要通过开发者模式手动加载固定目录；
- 安装程序尚未代码签名，Windows 可能显示未知发布者提示；
- 没有自动升级机制；
- 未完成大规模 Windows 版本、WebView2 和安全软件兼容矩阵；
- 市场分析只描述用户收集的岗位样本，不能代表整个招聘市场；
- 决策分数是透明规则与个人证据的辅助判断，不是录用概率；
- Skill v1 第一阶段只读，不自动投递、不自动联系招聘者、不批量修改数据。

## 基线冻结

桌面 v1.0.7 的 UI、数据模型和评分引擎在 Skill v1 开发期间冻结。只允许修复阻塞 Skill、数据安全、安装、测试或明确回归的问题。

冻结说明见：

```text
docs\desktop-v1.0.7-baseline-freeze.md
```
