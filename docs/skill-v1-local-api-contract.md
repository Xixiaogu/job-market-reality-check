# Skill v1 本地 API 只读契约

状态：`frozen-for-skill-v1`  
契约版本：`1.0.0`  
桌面基线：`desktop-v1.0.7-appearance`  
冻结日期：`2026-07-29`

Skill 0.1 参考实现：

```text
skills/job-market-reality-check/scripts/local_api_client.py
```

## 1. 目标与边界

本契约固定 Job Market Skill v1 可以读取的本地事实来源。Skill 负责自然语言路由、解释、比较和行动计划，不重新实现 SQLite、岗位管理、档案管理或评分引擎。

Skill v1 只允许发送本文件列出的 `GET` 请求。以下行为不属于 v1：

- 直接打开或修改 `job_market.db`；
- 调用岗位、档案、校准、决策重算或流水线的写接口；
- 自动投递、自动联系招聘者或绕过招聘平台限制；
- 把 API Token、数据库路径、个人档案或真实岗位数据写入日志和报告；
- 把决策分数表述为录用概率、Offer 概率或机器学习预测。

## 2. 服务发现与鉴权

开发和桌面模式默认地址：

```text
http://127.0.0.1:8765
```

健康接口不需要鉴权：

```http
GET /api/v1/health
```

其余接口必须携带：

```http
X-Job-Market-Token: <local token>
```

桌面模式 Token 默认位于：

```text
%LOCALAPPDATA%\JobMarketDecisionSystem\runtime\api_token.txt
```

开发模式 Token 默认位于：

```text
<project-root>\local_api\runtime\api_token.txt
```

Token 的处理规则：

- 只在请求头中使用；
- 不在终端、聊天、报告、异常栈或测试快照中输出；
- 不通过查询参数传递；
- 收到 `401` 时提示用户确认桌面程序正在运行并重新配对，不猜测 Token。

## 3. 版本与一致性

Skill 在每次分析开始时读取：

```http
GET /api/v1/health
GET /api/v1/decision/options
```

必须记录以下元数据：

- `contract_version`: 本文件的 `1.0.0`；
- `service_version`: 健康接口的 `version`；
- `engine_version`: 决策选项或决策结果中的 `engine_version`；
- `decision_run_id`: 决策响应 `run.run_id`；
- `generated_at`: Skill 生成结果的本地时间；
- `job_id`: 每个岗位的稳定标识。

如果必需字段缺失，Skill 应停止该工作流并报告“本地 API 契约不兼容”，不得猜测字段。

## 4. Skill v1 允许的接口

| 用途 | 方法与路径 | 主要参数 |
|---|---|---|
| 服务状态 | `GET /api/v1/health` | 无 |
| 岗位池 | `GET /api/v1/jobs` | `limit`, `offset`, `archived`, `keyword`, `city` |
| 岗位事实 | `GET /api/v1/jobs/{job_id}` | `job_id` |
| 岗位状态历史 | `GET /api/v1/jobs/{job_id}/history` | `job_id`, `limit` |
| 管理概况 | `GET /api/v1/management/summary` | 无 |
| 完整个人档案 | `GET /api/v1/profile` | 无 |
| 决策引擎信息 | `GET /api/v1/decision/options` | 无 |
| 决策概况 | `GET /api/v1/decision/summary` | `strategy` |
| 决策队列 | `GET /api/v1/decision/jobs` | `strategy`, `action_group`, `pending_only`, `limit`, `offset` |
| 单岗位解释数据 | `GET /api/v1/decision/jobs/{job_id}` | `job_id`, `strategy` |
| 校准质量 | `GET /api/v1/decision/calibration` | `strategy` |

Skill v1 固定使用 `strategy=balanced`，除非用户明确要求解释其他已存在策略。Skill 不得使用 `refresh=true`，因为刷新可能写入新的决策运行。

## 5. 核心响应字段

### 5.1 健康状态

`GET /api/v1/health` 至少读取：

```json
{
  "ok": true,
  "service": "job-market-reality-check-local-api",
  "version": "1.0.0",
  "app_mode": "development|desktop|packaged",
  "job_count": 0,
  "management": {},
  "profile": {}
}
```

`project_root`、`user_data_root`、`database_path` 和日志路径属于本地诊断信息，不进入 Skill 输出。

### 5.2 岗位列表

`GET /api/v1/jobs`：

```json
{
  "total": 0,
  "limit": 100,
  "offset": 0,
  "items": []
}
```

每个列表项的稳定字段：

- `job_id`, `job_title`, `company_name`, `city`, `salary`;
- `source_url`, `source_type`, `schema_version`, `revision`;
- `user_status`, `listing_status`, `quality_override`;
- `category_manual`, `notes`, `archived`;
- `job_updated_at`, `management_updated_at`.

分页规则：

- `limit` 范围 `1..500`；
- 必须根据 `total`, `limit`, `offset` 完成分页；
- 默认排除 `archived=true` 的岗位；
- 不得只读取第一页后声称分析了全部岗位。

### 5.3 岗位详情

`GET /api/v1/jobs/{job_id}` 返回岗位数据库记录，并包含：

```json
{
  "job_id": "stable-id",
  "canonical": {},
  "management": {}
}
```

Skill 需要从 `canonical` 中优先读取：

- 标题、公司、城市、薪资和来源链接；
- 完整职位描述；
- 学历、经验、招聘类型、实习天数和周期；
- 技能、岗位方向及其他清洗字段；
- 内容更新时间和修订号。

当字段缺失时标记为 `unknown`，不得自动视为满足。

### 5.4 个人档案

`GET /api/v1/profile`：

```json
{
  "profile": {},
  "cities": [],
  "skills": [],
  "projects": [],
  "directions": [],
  "options": {},
  "summary": {},
  "onboarding": {}
}
```

证据使用顺序：

1. `projects` 中明确记录的项目与技能证据；
2. `skills` 中的能力等级和备注；
3. `profile` 中的教育、毕业时间、可用时间和硬约束；
4. `cities` 与 `directions` 中的地点和方向偏好。

未写入档案的经历一律视为未知；Skill 可以向用户提问，但不能补造事实。

### 5.5 决策概况

`GET /api/v1/decision/summary?strategy=balanced`：

```json
{
  "run": {},
  "strategy": "balanced",
  "strategy_label": "平衡",
  "job_count": 0,
  "queue_count": 0,
  "by_action_group": {},
  "hard_conflict_count": 0,
  "information_risk_count": 0,
  "top_jobs": []
}
```

Skill 用它生成 `brief`，但最终推荐必须结合岗位明细和个人证据，不能只复述总分。

### 5.6 决策岗位

`GET /api/v1/decision/jobs` 返回：

```json
{
  "run": {},
  "total": 0,
  "limit": 100,
  "offset": 0,
  "items": []
}
```

每个决策项的稳定字段包括：

- 身份与状态：`job_id`, `job_title`, `company_name`, `user_status`, `listing_status`;
- 行动结论：`queue_eligible`, `action_group`, `action_group_label`, `action_reason`;
- 分数：`match_score`, `opportunity_score`, `priority_score`, `components`;
- 证据：`requirements`, `matched_skills`, `partial_skills`, `requirement_details`, `resume_projects`;
- 缺口与风险：`skill_gaps`, `hard_conflicts`, `soft_risks`, `information_risks`, `missing_fields`;
- 解释与行动：`reasons`, `risks`, `suggested_action`;
- 追踪：`engine_version`, `strategy`, `run.run_id`.

分数只能用于相对排序。Skill 的解释必须指出证据、缺口、风险和不确定性。

### 5.7 单岗位决策

`GET /api/v1/decision/jobs/{job_id}?strategy=balanced`：

```json
{
  "run": {},
  "item": {}
}
```

该接口是 `explain <job_id>` 的主要数据源。若返回 `404`，Skill 应提示岗位不存在或当前决策运行未包含该岗位。

## 6. 工作流到接口的映射

### `brief`

1. `health`;
2. `management/summary`;
3. `profile`;
4. `decision/summary`;
5. `decision/jobs?pending_only=true`.

输出：样本概况、重点方向、优先岗位、主要优势、集中缺口、当前瓶颈和一个最优下一步。

### `explain <job_id>`

1. `jobs/{job_id}`;
2. `profile`;
3. `decision/jobs/{job_id}`;
4. 必要时读取岗位状态历史。

输出：直接证据、可迁移证据、真实缺口、风险、机会价值、置信度和建议动作。

### `compare <job_id...>`

对每个岗位读取岗位事实和单岗位决策，并使用同一次 `decision_run_id`。如果运行 ID 不一致，停止比较并重新读取，不混合不同决策快照。

输出：匹配度、机会价值、简历改动成本、准备时间、成长价值、风险和明确顺序。

### `plan`

1. `management/summary`;
2. `profile`;
3. `decision/summary`;
4. 全部分页读取待处理决策队列。

输出：今天必须完成、本周优先投递、简历修改、证据补充、非阻塞学习项、暂缓岗位和检查节点。

## 7. 错误处理

| 状态 | Skill 行为 |
|---|---|
| 连接失败 | 提示启动桌面程序，不回退到直接读 SQLite |
| `401` | 提示重新配对 Token，不输出 Token 内容 |
| `404` | 明确说明岗位或结果不存在 |
| `422` | 报告参数或策略不兼容 |
| `500` | 报告本地服务错误并停止当前工作流 |
| 空岗位池 | 建议先采集岗位 |
| 档案未完成 | 说明缺失项，并限制结论置信度 |
| 决策运行不一致 | 重新读取；仍不一致则停止比较 |

## 8. 变更规则

在 Skill v1 完成前：

- 本文件列出的路径、鉴权头和稳定字段不得删除或重命名；
- 新增字段允许，Skill 必须忽略未知字段；
- 破坏性变更必须提升契约版本，并同步更新 Skill 客户端与契约测试；
- 桌面服务版本和决策引擎版本彼此独立，输出必须同时记录；
- 写接口只有在后续版本获得用户逐次确认后才可开放。

