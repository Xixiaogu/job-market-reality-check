# Phase 8.1：个人决策档案

Phase 8.1 为后续可解释投递优先级提供用户侧数据，不进行岗位排序。

## 页面

- `http://127.0.0.1:8765/profile`

页面包含：

1. 基本条件：学历、专业、毕业年份、到岗天数、实习周期、最低薪资和可到岗时间；
2. 动态技能：从当前有效岗位语料中识别候选技能，同时允许自由添加任意技能；
3. 项目证据：将技能关联到具体项目和可验证的实现证据；
4. 求职偏好：城市约束级别和目标岗位方向兴趣等级。

## 数据表

- `user_profile`
- `user_location_preferences`
- `user_skills`
- `user_projects`
- `project_skill_evidence`
- `user_job_preferences`

所有表都存储在现有 `data/job_market.db` 中。初始化过程只新增表，不修改和删除现有岗位数据。

## 动态技能建议

系统会读取现有 `audit_boss_skills.py` 中的 `SKILL_DEFS`，但不会导入 pandas 或运行完整分析管线。它通过 AST 安全读取技能定义，然后在 SQLite 当前有效、未归档且未排除的岗位语料中统计技能覆盖。

技能建议不是白名单。用户可以直接添加 `LangGraph`、`因果推断` 或其他任意新技能。

## API

- `GET /api/v1/profile`
- `PATCH /api/v1/profile`
- `PUT /api/v1/profile/cities`
- `GET|POST /api/v1/profile/skills`
- `PATCH|DELETE /api/v1/profile/skills/{skill_id}`
- `GET /api/v1/profile/skill-suggestions`
- `GET|POST /api/v1/profile/projects`
- `PATCH|DELETE /api/v1/profile/projects/{project_id}`
- `PUT /api/v1/profile/preferences`
- `GET /api/v1/profile/direction-suggestions`

除 `/profile` 页面本身外，API 与现有岗位管理接口一样需要 `X-Job-Market-Token`。

## 验收

安装后先重启本地 API，再运行：

```powershell
python .\test_phase81_api.py
```

离线数据层测试：

```powershell
python .\test_phase81_offline.py
```

## Phase 8.1 边界

当前阶段不包含：

- 岗位匹配评分；
- A/B/C/D 投递分组；
- Offer 概率；
- 简历 PDF 自动解析；
- 完整职业技能知识库；
- 多用户和云端同步。
