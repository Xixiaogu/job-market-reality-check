# Phase 5A：浏览器扩展与 Python 分析管线桥接审查

## 1. 审查结论

现有浏览器扩展导出的 JSONL 可以接入当前 Python 分析管线，但不能直接作为 `clean_boss_jobs.py` 的输入。

原因是两端字段命名和数据层级不同：

- 浏览器扩展使用 camelCase，例如 `jobId`、`jobTitle`、`jobDescription`。
- 原 Python 管线使用 snake_case，例如 `job_id`、`job_title`、`job_description`。
- 清洗脚本依赖 `job_basic_info_raw`，用于重新识别城市、学历、实习出勤和实习周期。
- 浏览器扩展当前没有采集公司名称、招聘者和工作地址。

因此需要增加一个导入适配器，而不是修改所有旧脚本。

---

## 2. 适配后的数据流

```text
Chrome / Edge 插件
→ 导出 boss-jobs-*.jsonl
→ import_extension_jobs.py
→ output/boss_batch/jobs.jsonl
→ clean_boss_jobs.py
→ analyze_boss_jobs.py
→ audit_boss_skills.py
→ visualize_boss_jobs_v11.py
→ HTML 看板
```

---

## 3. 字段映射

| 扩展字段 | Python 管线字段 |
|---|---|
| `jobId` | `job_id` |
| `jobTitle` | `job_title` |
| `salary` | `salary` |
| `city` | `city` |
| `education` | `education` |
| `internshipDays` | `internship_days_per_week` |
| `internshipDuration` | `internship_duration` |
| `jobDescription` | `job_description` |
| `sourceUrl` | `source_url`、`final_url` |
| `collectedAt` | `collected_at` |
| `savedAt` | `extension_saved_at` |
| `extraction` | `extension_extraction` |

适配器还会组合生成：

```text
job_basic_info_raw =
城市·实习出勤·实习周期·学历
```

例如：

```text
深圳·4天/周·3个月·本科
```

这样现有清洗脚本不需要修改。

---

## 4. 合并与去重策略

默认模式不会覆盖现有岗位数据，而是：

1. 读取现有 `output/boss_batch/jobs.jsonl`。
2. 读取扩展导出的 JSONL。
3. 按 `job_id` 去重。
4. 新岗位追加到原数据。
5. 同一岗位重复导入时，只更新扩展能够提供的非空字段。
6. 保留原数据中更完整的公司、招聘者和地址信息。
7. 写入前自动备份原始目标文件。

使用 `--replace` 时，才会只保留本次扩展导出的岗位。

---

## 5. 当前已验证结果

使用现有 23 条岗位和扩展新增的 2 条岗位进行了完整测试：

| 阶段 | 结果 |
|---|---:|
| 合并后原始岗位 | 25 条 |
| 清洗通过 | 23 条 |
| 需要复核 | 2 条 |
| 分析岗位 | 25 条 |
| 技能证据行 | 411 行 |
| 核心分析样本 | 24 条 |
| 图表 | 13 张 |
| HTML 看板 | 成功生成 |

两条新增扩展岗位被标记为 `review`，原因是扩展当前未采集 `company_full_name`，不是字段解析失败。

后续技能审计、岗位分类和可视化均能继续运行。

---

## 6. 当前已知缺口

浏览器扩展暂未采集：

- 公司全称
- 公司简称
- 公司规模
- 行业
- 融资阶段
- 招聘者姓名
- 招聘者职位
- 工作地址
- 普通正式岗位的工作经验字段

这些缺口不阻塞 Phase 5A，但会导致新增岗位在清洗阶段进入人工复核，并使看板中的公司列为空。

下一轮插件字段开发应优先补：

1. 公司名称
2. 工作经验
3. 公司规模与行业
4. 工作地址

---

## 7. 本阶段新增文件

```text
import_extension_jobs.py
run_extension_pipeline.ps1
```

`import_extension_jobs.py` 负责：

- 校验扩展 JSONL
- camelCase 转 snake_case
- 构造旧管线兼容字段
- 按岗位 ID 去重
- 合并现有岗位
- 备份旧输入文件
- 输出导入报告

`run_extension_pipeline.ps1` 负责一条命令依次运行：

```text
导入
→ 清洗
→ 基础分析
→ 技能审计
→ 看板生成
```

---

## 8. 使用方法

将两个文件放在项目根目录后运行：

```powershell
powershell.exe `
    -NoProfile `
    -ExecutionPolicy Bypass `
    -File ".\run_extension_pipeline.ps1" `
    -InputPath "<DOWNLOAD_DIR>\boss-jobs-20260727-014635.jsonl" `
    -OpenDashboard
```

首次测试建议先复制一份项目或确认导入报告中的自动备份路径。

默认模式会将扩展岗位合并到已有样本中。

只分析本次扩展岗位时使用：

```powershell
powershell.exe `
    -NoProfile `
    -ExecutionPolicy Bypass `
    -File ".\run_extension_pipeline.ps1" `
    -InputPath "<DOWNLOAD_DIR>\boss-jobs-20260727-014635.jsonl" `
    -Replace `
    -OpenDashboard
```
