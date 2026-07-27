# Phase 7B.1：岗位生命周期数据层与 API

本阶段只建立稳定的数据模型和接口，不修改 Phase 7A 看板，也不修改浏览器扩展采集流程。

## 三个独立维度

### 个人求职进度

`to_review`、`interested`、`preparing`、`applied`、`written_test`、`interview`、`offer`、`rejected`、`abandoned`

### 招聘状态

`unknown`、`active`、`suspected_inactive`、`closed`

### 分析口径覆盖

`auto`、`include`、`review`、`exclude`

## 新增数据表

- `job_management`：保存当前管理状态、人工分类、备注和归档时间。
- `job_status_events`：保存每次状态变化的审计记录。

现有 `jobs` 表继续保存采集到的岗位原始事实，个人管理信息不会覆盖采集数据。

## 新增或升级接口

- `GET /api/v1/jobs`
- `GET /api/v1/jobs/{job_id}`
- `GET /api/v1/jobs/{job_id}/history`
- `PATCH /api/v1/jobs/{job_id}/management`
- `POST /api/v1/jobs/bulk-management`
- `GET /api/v1/management/options`
- `GET /api/v1/management/summary`

## 分析任务触发规则

个人状态、招聘状态、备注和归档不会要求重新分析。

`quality_override` 和 `category_manual` 会返回 `analysis_required=true`。

只有显式传入 `run_pipeline=true` 时，API 才会启动分析任务。Phase 7B.2 看板会根据这个返回值决定是否触发分析。

## 安全设计

- 所有管理接口继续要求 `X-Job-Market-Token`。
- 不提供永久删除接口。
- 归档只改变管理状态，不删除 `jobs` 数据。
- 所有改变都有事件历史记录。
