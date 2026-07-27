from __future__ import annotations

import tempfile
from pathlib import Path

from local_api.database import upsert_canonical_job
from local_api.management import initialize_management_schema, patch_management
from local_api.profile import (
    create_project,
    create_skill,
    delete_project,
    delete_skill,
    direction_suggestions,
    get_full_profile,
    initialize_profile_schema,
    patch_profile,
    patch_project,
    patch_skill,
    replace_locations,
    replace_preferences,
    skill_suggestions,
)
from local_api.profile_ui import render_profile_page


def main() -> None:
    html = render_profile_page()
    for marker in (
        "个人决策档案",
        "/api/v1/profile",
        "skill-suggestions",
        "项目证据",
        "jobMarketApiTokenV1",
    ):
        if marker not in html:
            raise AssertionError(f"Profile UI marker missing: {marker}")

    with tempfile.TemporaryDirectory(prefix="job-market-phase81-") as directory:
        db_path = Path(directory) / "test.db"

        upsert_canonical_job(
            {
                "job_id": "phase81-python",
                "job_title": "AI应用实习生",
                "company_short_name": "示例公司",
                "city": "深圳",
                "salary": "200-300元/天",
                "job_description": (
                    "要求熟悉 Python、SQL 和机器学习，"
                    "有大模型智能体或 RAG 项目经验优先。"
                ),
                "role_category_v11": "AI与大模型开发",
                "source_url": "https://example.invalid/phase81-python",
            },
            source_type="phase81_test",
            db_path=db_path,
        )
        upsert_canonical_job(
            {
                "job_id": "phase81-excluded",
                "job_title": "数据标注实习生",
                "company_short_name": "排除公司",
                "city": "北京",
                "salary": "100元/天",
                "job_description": "使用 Excel 完成数据标注。",
                "role_category_v11": "数据标注",
                "source_url": "https://example.invalid/phase81-excluded",
            },
            source_type="phase81_test",
            db_path=db_path,
        )

        initialize_management_schema(db_path)
        patch_management(
            "phase81-excluded",
            {"quality_override": "exclude"},
            db_path=db_path,
        )
        initialize_profile_schema(db_path)

        patch_profile(
            {
                "education": "本科",
                "major": "电子信息工程",
                "graduation_year": 2027,
                "max_days_per_week": 5,
                "minimum_daily_salary": 150,
                "accepts_remote": True,
                "accepts_relocation": True,
            },
            db_path=db_path,
        )
        replace_locations(
            [
                {"city": "深圳", "constraint_level": "important"},
                {"city": "杭州", "constraint_level": "preference"},
            ],
            db_path=db_path,
        )
        replace_preferences(
            [
                {
                    "direction": "AI与大模型开发",
                    "interest_level": "very_high",
                }
            ],
            db_path=db_path,
        )

        python_skill = create_skill(
            {
                "skill_name": "python",
                "proficiency_level": "project_ready",
                "notes": "用于多个数据分析项目",
            },
            db_path=db_path,
        )
        sql_skill = create_skill(
            {
                "skill_name": "SQL",
                "proficiency_level": "basic",
            },
            db_path=db_path,
        )
        custom_skill = create_skill(
            {
                "skill_name": "LangGraph",
                "proficiency_level": "aware",
            },
            db_path=db_path,
        )

        project = create_project(
            {
                "project_name": "JobLens",
                "project_type": "personal",
                "project_status": "completed",
                "description": "岗位采集与投递决策系统",
                "achievements": "实现浏览器扩展到 SQLite 的完整链路",
                "skills": [
                    {
                        "skill_id": python_skill["skill_id"],
                        "evidence_strength": "strong",
                        "evidence_text": "使用 Python 构建数据处理管线",
                    },
                    {
                        "skill_id": sql_skill["skill_id"],
                        "evidence_strength": "supporting",
                        "evidence_text": "使用 SQLite 设计本地数据模型",
                    },
                ],
            },
            db_path=db_path,
        )

        patch_skill(
            sql_skill["skill_id"],
            {"proficiency_level": "proficient"},
            db_path=db_path,
        )
        patch_project(
            project["project_id"],
            {"demo_url": "https://example.invalid/demo"},
            db_path=db_path,
        )

        suggestions = skill_suggestions(db_path=db_path)
        suggestion_names = {item["skill_name"] for item in suggestions["items"]}
        assert suggestions["source_job_count"] == 1
        assert "Python" in suggestion_names
        assert "SQL" in suggestion_names
        assert "Excel" not in suggestion_names

        directions = direction_suggestions(db_path=db_path)
        assert directions["source_job_count"] == 1
        assert any(
            item["direction"] == "AI与大模型开发"
            for item in directions["items"]
        )

        profile = get_full_profile(db_path=db_path)
        assert profile["profile"]["graduation_year"] == 2027
        assert profile["summary"]["skill_count"] == 3
        assert profile["summary"]["project_count"] == 1
        assert profile["summary"]["evidence_count"] == 2
        assert len(profile["cities"]) == 2
        assert len(profile["directions"]) == 1
        assert profile["projects"][0]["skills"][0]["skill_name"] in {
            "Python",
            "SQL",
        }

        delete_project(project["project_id"], db_path=db_path)
        delete_skill(custom_skill["skill_id"], db_path=db_path)
        final_profile = get_full_profile(db_path=db_path)
        assert final_profile["summary"]["project_count"] == 0
        assert final_profile["summary"]["skill_count"] == 2
        assert final_profile["summary"]["evidence_count"] == 0

    print("Phase 8.1 offline smoke test passed.")


if __name__ == "__main__":
    main()
