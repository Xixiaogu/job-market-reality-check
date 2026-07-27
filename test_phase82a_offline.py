from __future__ import annotations

import tempfile
from pathlib import Path

from local_api.calibration import (
    ACTION_GROUPS,
    calibration_summary,
    get_representative_jobs,
    initialize_calibration_schema,
    upsert_calibration_label,
)
from local_api.database import upsert_canonical_job
from local_api.management import initialize_management_schema, patch_management
from local_api.profile import (
    create_skill,
    initialize_profile_schema,
    patch_profile,
    replace_locations,
    replace_preferences,
)
from local_api.calibration_ui import render_calibration_page


def add_job(db_path: Path, **record) -> str:
    payload = {
        "job_id": record.pop("job_id"),
        "job_title": record.pop("job_title"),
        "company_short_name": record.pop("company_short_name", "测试公司"),
        "city": record.pop("city", "深圳"),
        "salary": record.pop("salary", "200-300元/天"),
        "education": record.pop("education", "本科"),
        "experience": record.pop("experience", "经验不限"),
        "job_description": record.pop("job_description", "Python SQL 数据分析"),
        "source_url": record.pop("source_url", "https://example.invalid/job"),
        **record,
    }
    upsert_canonical_job(payload, source_type="phase82a_test", db_path=db_path)
    return payload["job_id"]


def main() -> None:
    html = render_calibration_page()
    for marker in (
        "投递决策人工校准",
        "/api/v1/calibration/representatives",
        "立即投递",
        "值得冲刺",
        "补材料后投递",
        "暂缓",
    ):
        if marker not in html:
            raise AssertionError(f"Calibration UI marker missing: {marker}")

    with tempfile.TemporaryDirectory(prefix="job-market-phase82a-") as directory:
        db_path = Path(directory) / "test.db"
        initialize_management_schema(db_path)
        initialize_profile_schema(db_path)
        initialize_calibration_schema(db_path)

        patch_profile(
            {
                "education": "本科",
                "major": "电子信息科学与技术",
                "graduation_year": 2027,
                "max_days_per_week": 5,
                "max_internship_months": 6,
                "target_job_types": ["daily_internship", "research_assistant"],
            },
            db_path=db_path,
        )
        replace_locations(
            [
                {"city": "深圳", "constraint_level": "hard"},
                {"city": "广州", "constraint_level": "preference"},
            ],
            db_path=db_path,
        )
        replace_preferences(
            [
                {"direction": "数据分析与BI", "interest_level": "very_high"},
                {"direction": "AI与大模型开发", "interest_level": "high"},
            ],
            db_path=db_path,
        )
        create_skill(
            {"skill_name": "Python", "proficiency_level": "project_ready"},
            db_path=db_path,
        )
        create_skill(
            {"skill_name": "SQL", "proficiency_level": "basic"},
            db_path=db_path,
        )
        create_skill(
            {"skill_name": "FastAPI", "proficiency_level": "proficient"},
            db_path=db_path,
        )

        ids = []
        ids.append(add_job(db_path, job_id="data-high", job_title="数据分析实习生", salary="300-400元/天", job_description="Python SQL Excel 数据分析 数据可视化", role_category_v11="数据分析与BI"))
        ids.append(add_job(db_path, job_id="ai-stretch", job_title="AI Agent开发实习生", salary="250-350元/天", job_description="Python FastAPI RAG AI Agent Docker", role_category_v11="AI与大模型开发"))
        ids.append(add_job(db_path, job_id="hard-city", job_title="商业分析实习生", city="北京", job_description="Python SQL 数据分析", role_category_v11="数据分析与BI"))
        ids.append(add_job(db_path, job_id="hard-edu", job_title="机器学习研究助理", education="硕士及以上", job_description="Python PyTorch 深度学习", role_category_v11="算法与机器学习"))
        ids.append(add_job(db_path, job_id="missing-info", job_title="数据岗", salary="", education="", job_description=""))
        ids.append(add_job(db_path, job_id="low-salary", job_title="数据处理实习生", salary="80元/天", job_description="Excel 数据清洗 数据标注", role_category_v11="数据处理与标注"))
        ids.append(add_job(db_path, job_id="salary-outlier", job_title="量化分析实习生", salary="800-1000元/天", job_description="Python SQL 量化分析 时间序列", role_category_v11="数据分析与BI"))
        ids.append(add_job(db_path, job_id="data-engineer", job_title="数据开发实习生", job_description="Python SQL ETL Spark Docker", role_category_v11="数据工程与平台"))
        ids.append(add_job(db_path, job_id="product", job_title="AI产品实习生", job_description="需求分析 产品设计 大模型", role_category_v11="AI产品与项目"))
        ids.append(add_job(db_path, job_id="research", job_title="足球数据研究助理", job_description="Python 统计分析 机器学习 报告撰写", role_category_v11="研究助理 / RA"))
        ids.append(add_job(db_path, job_id="inactive", job_title="数据分析师", job_description="Python SQL 数据分析", role_category_v11="数据分析与BI"))
        ids.append(add_job(db_path, job_id="generic", job_title="运营分析实习生", city="广州", job_description="Excel 数据分析 报告撰写", role_category_v11="数据分析与BI"))

        initialize_management_schema(db_path)
        patch_management("inactive", {"listing_status": "closed"}, db_path=db_path)

        result = get_representative_jobs(refresh=True, db_path=db_path)
        assert result["sample_count"] == 10, result
        assert len({item["job_id"] for item in result["items"]}) == 10
        assert any(item["metrics"]["hard_conflicts"] for item in result["items"])
        assert any(item["selection_bucket"] == "inactive" for item in result["items"])
        assert all("selection_reason" in item for item in result["items"])

        for index, item in enumerate(result["items"]):
            upsert_calibration_label(
                item["job_id"],
                {
                    "action_group": ACTION_GROUPS[index % len(ACTION_GROUPS)],
                    "reason": f"人工校准理由 {index + 1}",
                },
                db_path=db_path,
            )

        refreshed = get_representative_jobs(db_path=db_path)
        assert refreshed["complete"] is True
        assert refreshed["labeled_count"] == 10

        summary = calibration_summary(db_path=db_path)
        assert summary["complete"] is True
        assert summary["remaining_count"] == 0
        assert sum(summary["by_action_group"].values()) == 10

    print("Phase 8.2A calibration offline test passed.")


if __name__ == "__main__":
    main()
