# Phase 8.2B：可解释投递优先级引擎

## 目标

在不使用机器学习模型或大模型直接打分的前提下，根据本地岗位、个人档案、技能等级、项目证据、求职偏好和岗位管理状态，生成稳定、可解释、可复现的投递决策结果。

## 输出

每个岗位输出：

- 岗位匹配度；
- 机会价值；
- 投递优先级；
- 立即投递 / 值得冲刺 / 补材料后投递 / 暂缓；
- 硬条件冲突；
- 匹配技能、部分匹配和技能缺口；
- 项目证据及简历项目建议；
- 信息矛盾、缺失字段和岗位风险；
- 建议动作与完整评分组成。

## 核心规则

1. 明确硬条件冲突覆盖普通高分。
2. 岗位信息缺失不会直接等同于不满足。
3. `R/Python`、`PyTorch/TensorFlow` 等显式二选一要求按替代组判断。
4. `优先`、`加分`、`更佳`等技能与核心必备技能分开处理。
5. 技能等级与项目证据共同决定能力得分。
6. 项目描述中的 FastAPI、SQLite、滚动回测、MAE、xG 等内容也可以形成可追溯的辅助证据。
7. 高薪只影响机会价值的一部分，不会覆盖岗位信息矛盾或严重不匹配。
8. 人工校准标签只用于评估，不直接写入岗位分数。

## 策略

- `conservative`：更重视当前匹配、硬条件和项目证据；
- `balanced`：默认策略，平衡匹配度与机会价值；
- `stretch`：更重视成长价值和高价值岗位。

## API

```text
GET  /api/v1/decision/options
POST /api/v1/decision/recalculate?strategy=balanced
GET  /api/v1/decision/summary?strategy=balanced
GET  /api/v1/decision/jobs?strategy=balanced&pending_only=true
GET  /api/v1/decision/jobs/{job_id}?strategy=balanced
GET  /api/v1/decision/calibration?strategy=balanced
```

## 缓存与重算

每次计算会写入 `decision_runs` 和 `decision_results`。引擎会对岗位、管理状态、个人档案、技能、项目和偏好生成输入哈希；输入发生变化时，读取接口会自动生成新运行。每种策略最多保留最近 20 次运行。

## 校准指标

- 四组完全一致率；
- 相邻分组一致率；
- 人工 Top 5 与系统 Top 5 重合度；
- 硬条件漏判数；
- 逐条不一致原因。

完全一致率不是唯一目标。更重要的是硬条件不能漏判，明显不相关或信息矛盾岗位不能进入“立即投递”，并且每个差异都有可以检查的规则来源。
