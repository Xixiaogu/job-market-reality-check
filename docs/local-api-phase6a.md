# Phase 6A：本地 FastAPI + SQLite

## 目标

把原来的：

```text
浏览器扩展
→ 手动导出 JSONL
→ PowerShell 导入
→ Python 分析
```

改造成可被扩展直接调用的本地服务：

```text
浏览器扩展
→ 127.0.0.1 FastAPI
→ SQLite
→ Python 分析管线
→ HTML 看板
```

Phase 6A 先完成并验证后端。Phase 6B 再修改扩展，让“采集当前岗位”直接调用本地 API。

## 数据库定位

SQLite 文件：

```text
data/job_market.db
```

数据库中的 `jobs` 表保存：

- 规范化岗位 JSON；
- 扩展原始 JSON（存在时）；
- 岗位摘要字段；
- 内容哈希；
- 首次出现时间；
- 最近更新时间；
- 修订版本号。

初始化时，会把当前：

```text
output/boss_batch/jobs.jsonl
```

迁移到 SQLite。此后分析任务会从 SQLite 导出规范岗位，再执行现有四个 Python 脚本。

## 安全边界

服务只监听：

```text
127.0.0.1:8765
```

写入岗位和运行分析必须提供：

```text
X-Job-Market-Token
```

令牌保存在：

```text
local_api/runtime/api_token.txt
```

该目录应被 `.gitignore` 忽略。

## 主要接口

| 方法 | 路径 | 作用 |
|---|---|---|
| GET | `/dashboard` | 在浏览器中打开最新 HTML 看板 |
| GET | `/api/v1/health` | 健康状态、岗位数、最近任务 |
| GET | `/api/v1/jobs` | 岗位摘要列表 |
| GET | `/api/v1/jobs/{job_id}` | 单条岗位及原始数据 |
| POST | `/api/v1/jobs/upsert` | 新增或更新一条扩展岗位 |
| POST | `/api/v1/jobs/bulk-upsert` | 批量写入扩展岗位 |
| POST | `/api/v1/pipeline/run` | 异步运行分析管线 |
| GET | `/api/v1/pipeline/status` | 查询分析任务状态 |

交互式接口文档：

```text
http://127.0.0.1:8765/docs
```

## 启动

```powershell
conda activate base_science
Set-Location "<PROJECT_ROOT>"
.\scripts\run_api.ps1
```

服务终端需要保持开启。

## 完整验收

另开一个 PowerShell：

```powershell
conda activate base_science
Set-Location "<PROJECT_ROOT>"

python -m tests.api.development.test_pipeline_api `
    --input "<DOWNLOAD_DIR>\boss-jobs-20260727-024416.jsonl" `
    --run-pipeline `
    --open-dashboard
```

预期结果：

- 健康检查返回 `ok: true`；
- SQLite 岗位总数保持25条；
- 两条扩展岗位显示 `unchanged` 或 `updated`，不会重复新增；
- 分析任务最终状态为 `success`；
- HTML 看板正常打开。

## 管理命令

```powershell
python -m local_api.cli stats
python -m local_api.cli doctor
python -m local_api.cli token
python -m local_api.cli import-extension "<DOWNLOAD_DIR>\boss-jobs.jsonl"
python -m local_api.cli pipeline
```
