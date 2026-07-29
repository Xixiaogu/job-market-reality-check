from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


SYNTHETIC_JOBS: tuple[dict[str, Any], ...] = (
    {
        "job_id": "demo-data-analyst-001",
        "job_title": "数据分析实习生",
        "company_full_name": "示例内容科技有限公司",
        "city": "深圳",
        "salary": "250-350元/天",
        "job_description": (
            "负责业务指标建设、SQL取数、Python数据分析、统计分析和专题复盘，"
            "支持产品与运营决策。"
        ),
    },
    {
        "job_id": "demo-agent-engineer-002",
        "job_title": "AI Agent 应用开发实习生",
        "company_full_name": "示例智能科技有限公司",
        "city": "深圳",
        "salary": "220-320元/天",
        "job_description": (
            "参与Python、FastAPI、大语言模型、RAG和知识库应用开发，"
            "完成接口、评测与可运行Demo。"
        ),
    },
    {
        "job_id": "demo-bi-analyst-003",
        "job_title": "BI 数据分析实习生",
        "company_full_name": "示例零售科技有限公司",
        "city": "广州",
        "salary": "180-250元/天",
        "job_description": (
            "使用SQL、Excel和数据可视化工具维护经营报表，"
            "开展异常分析并与业务团队协作。"
        ),
    },
    {
        "job_id": "demo-data-scientist-004",
        "job_title": "高级数据科学家",
        "company_full_name": "示例研究院有限公司",
        "city": "北京",
        "salary": "35-50K",
        "job_description": (
            "要求硕士学历、三年以上全职经验，负责机器学习、深度学习、"
            "模型训练与线上部署。"
        ),
    },
    {
        "job_id": "demo-product-analyst-005",
        "job_title": "产品数据分析实习生",
        "company_full_name": "示例互动科技有限公司",
        "city": "深圳",
        "salary": "200-280元/天",
        "job_description": (
            "负责埋点分析、A/B测试、假设检验、用户行为分析和报告撰写，"
            "使用Python与SQL支持产品迭代。"
        ),
    },
    {
        "job_id": "demo-data-governance-006",
        "job_title": "数据治理实习生",
        "company_full_name": "示例云计算有限公司",
        "city": "远程",
        "salary": "180-240元/天",
        "job_description": (
            "参与数据质量检查、元数据管理、数据清洗和流程优化，"
            "需要Python、SQL及跨团队协作。"
        ),
    },
    {
        "job_id": "demo-python-api-007",
        "job_title": "Python 后端开发实习生",
        "company_full_name": "示例软件有限公司",
        "city": "深圳",
        "salary": "200-300元/天",
        "job_description": (
            "使用Python、FastAPI、SQLite和REST API开发本地服务，"
            "编写自动化测试并完成桌面端集成。"
        ),
    },
    {
        "job_id": "demo-research-assistant-008",
        "job_title": "数据研究助理",
        "company_full_name": "示例实验室",
        "city": "远程",
        "salary": "180-220元/天",
        "job_description": (
            "负责文献整理、数据清洗、NumPy统计分析、实验设计和结果复现，"
            "使用Python完成研究支持。"
        ),
    },
    {
        "job_id": "demo-ops-analyst-009",
        "job_title": "数据运营实习生",
        "company_full_name": "示例电商有限公司",
        "city": "杭州",
        "salary": "150-200元/天",
        "job_description": (
            "负责Excel报表、SQL取数、活动复盘和基础数据清洗，"
            "每周至少到岗四天。"
        ),
    },
    {
        "job_id": "demo-llm-evaluation-010",
        "job_title": "大模型评测实习生",
        "company_full_name": "示例人工智能有限公司",
        "city": "深圳",
        "salary": "220-300元/天",
        "job_description": (
            "参与Prompt设计、大语言模型评测、数据标注与误差分析，"
            "使用Python搭建自动化评测流程。"
        ),
    },
    {
        "job_id": "demo-visualization-011",
        "job_title": "数据可视化实习生",
        "company_full_name": "示例商业智能有限公司",
        "city": "上海",
        "salary": "200-260元/天",
        "job_description": (
            "使用SQL、Python和BI工具构建仪表盘，"
            "完成指标解释、需求分析与业务汇报。"
        ),
    },
    {
        "job_id": "demo-six-days-012",
        "job_title": "数据挖掘实习生",
        "company_full_name": "示例增长科技有限公司",
        "city": "深圳",
        "salary": "230-300元/天",
        "job_description": (
            "负责数据分析、统计建模和用户增长研究，要求每周到岗六天，"
            "熟悉Python、SQL和机器学习。"
        ),
    },
)


def canonical_record(job: dict[str, Any]) -> dict[str, Any]:
    job_id = str(job["job_id"])
    return {
        **job,
        "company_short_name": str(job["company_full_name"]).removesuffix(
            "有限公司"
        ),
        "source_url": f"https://example.invalid/jobs/{job_id}",
        "collector": "synthetic_ci",
        "extension_schema_version": "public-ci-v1",
        "job_type": "实习",
        "education": "本科",
        "experience": "不限",
        "captured_at": "2026-01-01T00:00:00Z",
    }


def build_fixture(output: Path) -> int:
    output = output.resolve()
    if output.exists():
        raise FileExistsError(
            f"Refusing to overwrite an existing fixture: {output}"
        )
    output.parent.mkdir(parents=True, exist_ok=True)

    os.environ["JOB_MARKET_DB_PATH"] = str(output)
    os.environ["JOB_MARKET_LOCAL_OUTPUT_DIR"] = str(
        output.parent / "output"
    )
    os.environ["JOB_MARKET_LOG_DIR"] = str(output.parent / "logs")

    from local_api.database import (  # noqa: PLC0415
        count_jobs,
        initialize_database,
        upsert_canonical_job,
    )
    from local_api.profile import (  # noqa: PLC0415
        create_project,
        create_skill,
        patch_profile,
        replace_locations,
        replace_preferences,
    )

    initialize_database(output)
    for job in SYNTHETIC_JOBS:
        upsert_canonical_job(
            canonical_record(job),
            source_type="synthetic_ci",
            db_path=output,
        )

    patch_profile(
        {
            "education": "本科",
            "major": "电子信息",
            "graduation_year": 2027,
            "max_days_per_week": 5,
            "min_internship_months": 3,
            "max_internship_months": 6,
            "minimum_daily_salary": 180,
            "accepts_remote": True,
            "accepts_relocation": True,
            "available_from": "2026年8月",
            "target_job_types": [
                "daily_internship",
                "research_assistant",
            ],
        },
        db_path=output,
    )
    replace_locations(
        [{"city": "深圳", "constraint_level": "important"}],
        db_path=output,
    )
    replace_preferences(
        [{"direction": "数据分析师", "interest_level": "high"}],
        db_path=output,
    )

    skill_ids: dict[str, int] = {}
    for name, level in (
        ("Python", "proficient"),
        ("SQL", "basic"),
        ("数据分析", "proficient"),
        ("NumPy", "basic"),
        ("FastAPI", "proficient"),
        ("AI Agent", "basic"),
        ("Prompt", "proficient"),
        ("需求分析", "basic"),
    ):
        created = create_skill(
            {
                "skill_name": name,
                "proficiency_level": level,
                "notes": "Synthetic public CI profile.",
            },
            db_path=output,
        )
        skill_ids[name] = int(created["skill_id"])

    create_project(
        {
            "project_name": "本地求职决策系统 Demo",
            "project_type": "personal",
            "project_status": "completed",
            "description": (
                "使用浏览器扩展、FastAPI、SQLite和桌面界面构建本地优先的"
                "岗位管理与可解释投递决策闭环。"
            ),
            "achievements": (
                "实现合成岗位采集、只读本地API、自动测试和Windows发布流程。"
            ),
            "skills": [
                {
                    "skill_id": skill_ids[name],
                    "evidence_text": f"在合成演示项目中使用{name}。",
                    "evidence_strength": "strong",
                }
                for name in (
                    "Python",
                    "SQL",
                    "FastAPI",
                    "需求分析",
                )
            ],
        },
        db_path=output,
    )
    create_project(
        {
            "project_name": "足球 xG 滚动回测 Demo",
            "project_type": "personal",
            "project_status": "completed",
            "description": (
                "使用Python与NumPy处理虚构比赛样本，设计无未来信息泄露的"
                "滚动回测并比较多种基线。"
            ),
            "achievements": "完成可复现的数据清洗、误差分析和结果解释。",
            "skills": [
                {
                    "skill_id": skill_ids[name],
                    "evidence_text": f"在合成演示项目中使用{name}。",
                    "evidence_strength": "strong",
                }
                for name in ("Python", "NumPy", "数据分析")
            ],
        },
        db_path=output,
    )

    total = count_jobs(db_path=output)
    if total != len(SYNTHETIC_JOBS):
        raise RuntimeError(
            f"Expected {len(SYNTHETIC_JOBS)} jobs, found {total}."
        )
    return total


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a synthetic SQLite fixture for public CI."
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    total = build_fixture(args.output)
    print(f"Synthetic CI database created with {total} fictional jobs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
