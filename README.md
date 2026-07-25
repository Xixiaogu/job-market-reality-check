# Job Market Reality Check

一个面向个人求职决策的招聘岗位分析工具。

项目从个人收藏的招聘岗位出发，完成岗位信息整理、字段清洗、技能证据提取、异常文本审计和可视化展示，帮助快速看清自己关注的岗位方向、常见技能要求、薪资范围和实习条件。

## 项目成果

当前版本已完成：

- 招聘岗位信息结构化整理
- 薪资、城市、学历、招聘类型和实习要求清洗
- Python、SQL、机器学习、LLM、RAG、AI Agent 等技能识别
- 保存每项技能对应的原始 JD 证据
- 区分必备、优先、岗位职责和普通提及
- 标记低信息密度岗位和疑似模板残留文本
- 生成 13 张统计图表
- 生成可搜索、可筛选的单文件 HTML 看板

## 当前样本结果

本次测试共整理 23 条个人收藏岗位，其中 22 条进入核心分析样本。

| 指标 | 结果 |
|---|---:|
| 核心样本 | 22 条 |
| 实习相关岗位 | 18 条 |
| Python 覆盖率 | 86.4% |
| 数据分析覆盖率 | 59.1% |
| SQL 覆盖率 | 50.0% |
| 大模型 / LLM 覆盖率 | 45.5% |
| 日薪区间中点中位数 | 225 元/天 |
| 月薪区间中点中位数 | 12.5K/月 |

这些结果只描述当前个人收藏样本，不代表整个招聘市场。

## 分析流程

```text
岗位链接
→ 岗位信息采集
→ 字段清洗
→ 技能证据提取
→ 异常样本审计
→ 描述性统计
→ HTML 可视化看板
```

## 主要文件

| 文件 | 作用 |
|---|---|
| `collect_all_boss_jobs.py` | 批量采集岗位信息 |
| `clean_boss_jobs.py` | 清洗薪资、城市、学历和实习要求等字段 |
| `analyze_boss_jobs.py` | 生成基础岗位统计和技能频率 |
| `audit_boss_skills.py` | 保存技能证据并审计异常样本 |
| `visualize_boss_jobs_v11.py` | 生成图表和可筛选 HTML 看板 |
| `base_science_environment.yml` | Conda 环境配置 |

## 运行方法

创建并进入环境：

```powershell
conda env create -f base_science_environment.yml
conda activate base_science
```

依次运行：

```powershell
python .\collect_all_boss_jobs.py
python .\clean_boss_jobs.py
python .\analyze_boss_jobs.py
python .\audit_boss_skills.py
python .\visualize_boss_jobs_v11.py
```

打开最终看板：

```powershell
Start-Process .\output\visualization_v1_1\visual_dashboard_v11.html
```

## 输出内容

主要输出位于：

```text
output/
├── boss_batch/
├── boss_cleaned/
├── analysis_v1/
├── analysis_v1_1/
└── visualization_v1_1/
```

最终看板：

```text
output/visualization_v1_1/visual_dashboard_v11.html
```

该 HTML 已内嵌全部图表，可以作为单文件打开。

## 数据与隐私

真实岗位链接、招聘者信息、浏览器会话、原始页面和分析结果默认不会提交到公开仓库。

本项目仅用于个人学习、岗位研究和求职决策。使用时应遵守目标网站的服务条款和访问限制。

## 当前局限

- 样本来自个人主动收藏，存在明显选择偏差
- 当前样本量较小，且城市分布不均衡
- 技能识别和要求性质判断主要基于规则
- 部分岗位描述仍需要人工复核
- 当前版本不用于推断整个招聘市场

## 后续计划

- 增加脱敏演示数据
- 增加自动化测试
- 将技能词典改为可配置文件
- 加入个人能力与岗位要求匹配
- 输出技能缺口和学习优先级
