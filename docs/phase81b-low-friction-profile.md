# Phase 8.1B：低摩擦个人决策档案

## 目标

将原本偏后台 CRUD 的个人档案页改为低输入成本的决策档案：

- 首次进入提供三步、约 60 秒的快速设置；
- 日常页面以摘要查看为主，编辑表单按需展开；
- 技能由岗位语料动态推荐，支持批量确认；
- 项目以项目本身为中心录入，选择技能后自动生成能力证据；
- 薪资、最长实习周期和补充说明折叠进高级设置；
- 求职类型、目标城市与目标方向集中在“求职目标”页面。

## 新增数据

`user_profile.target_job_types` 以 JSON 数组存储，可选值：

- `summer_internship`
- `daily_internship`
- `full_time`
- `research_assistant`
- `part_time`

初始化会自动检测旧数据库并执行增量迁移，不删除或重建原有档案数据。

## 页面结构

- 我的概况
- 我的能力
- 我的项目
- 求职目标

页面地址仍为：

`http://127.0.0.1:8765/profile`

## 验收

离线测试：

```powershell
python -m tests.offline.test_profile_preferences
```

启动 API 后在线测试：

```powershell
python -m tests.api.development.test_profile_preferences_api
```
