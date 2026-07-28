# Input schema

## Job file

Preferred record:

```json
{
  "job_id": "job-001",
  "title": "数据分析实习生",
  "company": "示例公司",
  "location": "深圳",
  "salary": "200-300元/天",
  "employment_type": "实习",
  "education": "本科",
  "experience": "不限",
  "description": "岗位职责与要求",
  "skills": ["Python", "SQL", "Excel"],
  "hard_requirements": ["2027届及以后"],
  "source": "export",
  "collected_at": "2026-07-28"
}
```

Only `title` or `description` is required. Supported containers:

- JSON array;
- JSON object containing `jobs`;
- JSONL, one object per line;
- CSV with a header row.

## Profile file

```json
{
  "targets": ["数据分析实习生", "AI应用开发实习生"],
  "preferred_locations": ["深圳", "远程"],
  "education": {
    "level": "本科",
    "major": "电子信息",
    "graduation_year": 2027
  },
  "years_experience": 0,
  "skills": [
    {
      "name": "Python",
      "level": "熟练",
      "evidence": ["招聘市场分析系统"]
    }
  ],
  "projects": [
    {
      "name": "招聘市场分析与投递决策系统",
      "skills": ["Python", "FastAPI", "SQLite", "TypeScript"],
      "evidence": "实现岗位采集、清洗、技能审计和可解释投递决策。"
    }
  ],
  "constraints": {
    "employment_types": ["实习"],
    "minimum_daily_salary": 150
  }
}
```

Recognized levels: `了解`, `基础`, `熟练`, `可独立完成项目`.

## Calibration labels

```json
[
  {"job_id": "job-001", "label": "apply_now"},
  {"job_id": "job-002", "label": "stretch"}
]
```

Allowed labels: `apply_now`, `stretch`, `prepare_first`, `defer`.
