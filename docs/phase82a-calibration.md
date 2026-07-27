# Phase 8.2A：投递决策人工校准集

## 目标

在编写自动投递优先级公式之前，从本地有效岗位中挑选最多10个具有代表性的岗位，由用户人工标注：

- 立即投递
- 值得冲刺
- 补材料后投递
- 暂缓

每条标注必须包含一句理由。

## 为什么先做人工校准

系统当前只有几十个真实目标岗位，不适合训练机器学习排序模型。Phase 8.2A使用透明的代理特征挑选代表样本，但代理值只用于抽样，不作为最终投递评分。

样本覆盖：

- 硬条件冲突
- 岗位疑似失效或关闭
- 信息缺失
- 数据分析类岗位
- AI应用类岗位
- 高匹配高价值
- 高匹配低价值
- 低匹配高价值
- 技能缺口明显
- 薪资异常或极端值

## 页面

```text
http://127.0.0.1:8765/calibrate
```

## API

```text
GET    /api/v1/calibration/representatives
POST   /api/v1/calibration/representatives/refresh
GET    /api/v1/calibration/labels
PUT    /api/v1/calibration/labels/{job_id}
DELETE /api/v1/calibration/labels/{job_id}
GET    /api/v1/calibration/summary
```

## 数据表

- `decision_calibration_sample`：当前代表样本及其入选原因
- `decision_calibration_labels`：用户人工分组和理由

## 验收条件

1. 能从真实岗位池生成最多10个不重复样本；
2. 每个样本都有可解释的入选原因；
3. 人工分组和理由刷新后仍保留；
4. 全部标注完成后显示可以进入Phase 8.2B；
5. 页面中的代理值明确标注为抽样用途，不冒充最终评分。
