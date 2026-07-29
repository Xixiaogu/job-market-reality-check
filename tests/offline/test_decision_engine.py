from __future__ import annotations

import tempfile
from pathlib import Path

from local_api.calibration import get_representative_jobs, upsert_calibration_label
from local_api.database import upsert_canonical_job
from local_api.decision import (
    decision_calibration_report,
    decision_options,
    decision_summary,
    get_decision,
    initialize_decision_schema,
    list_decisions,
    recalculate_decisions,
)
from local_api.management import initialize_management_schema, patch_management
from local_api.profile import (
    create_project,
    create_skill,
    initialize_profile_schema,
    patch_profile,
    replace_locations,
    replace_preferences,
)


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
    upsert_canonical_job(payload, source_type="phase82b_test", db_path=db_path)
    return payload["job_id"]


def main() -> None:
    options = decision_options()
    assert options["default_strategy"] == "balanced"
    assert {item["value"] for item in options["strategies"]} == {
        "conservative", "balanced", "stretch"
    }

    with tempfile.TemporaryDirectory(prefix="job-market-phase82b-") as directory:
        db_path = Path(directory) / "test.db"
        initialize_management_schema(db_path)
        initialize_profile_schema(db_path)
        initialize_decision_schema(db_path)

        patch_profile(
            {
                "education": "本科",
                "major": "电子信息科学与技术",
                "graduation_year": 2027,
                "max_days_per_week": 5,
                "max_internship_months": 6,
                "minimum_daily_salary": 100,
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
                {"direction": "AI与大模型开发", "interest_level": "very_high"},
                {"direction": "研究助理 / RA", "interest_level": "high"},
            ],
            db_path=db_path,
        )

        skill_ids = {}
        for name, level in (
            ("Python", "project_ready"),
            ("SQL", "basic"),
            ("数据分析", "project_ready"),
            ("统计分析", "proficient"),
            ("量化分析", "proficient"),
            ("AI Agent", "proficient"),
            ("Prompt", "proficient"),
            ("需求分析", "proficient"),
        ):
            created = create_skill(
                {"skill_name": name, "proficiency_level": level},
                db_path=db_path,
            )
            skill_ids[name] = created["skill_id"]

        create_project(
            {
                "project_name": "招聘市场分析与投递决策系统",
                "project_type": "personal",
                "project_status": "completed",
                "description": "浏览器扩展、FastAPI、SQLite与本地API组成的岗位采集和决策系统。",
                "achievements": "完成需求拆解、AI Agent工作流、Prompt、数据清洗、接口设计和自动化测试。",
                "skills": [
                    {"skill_id": skill_ids["Python"], "evidence_strength": "strong"},
                    {"skill_id": skill_ids["SQL"], "evidence_strength": "supporting"},
                    {"skill_id": skill_ids["AI Agent"], "evidence_strength": "strong"},
                    {"skill_id": skill_ids["Prompt"], "evidence_strength": "strong"},
                    {"skill_id": skill_ids["需求分析"], "evidence_strength": "strong"},
                ],
            },
            db_path=db_path,
        )
        create_project(
            {
                "project_name": "英超赛前xG估计与滚动回测",
                "project_type": "research",
                "project_status": "completed",
                "description": "使用Pandas和NumPy处理足球赛事与赔率数据。",
                "achievements": "设计滚动回测，使用MAE完成模型评估、统计分析与量化分析。",
                "skills": [
                    {"skill_id": skill_ids["Python"], "evidence_strength": "strong"},
                    {"skill_id": skill_ids["数据分析"], "evidence_strength": "strong"},
                    {"skill_id": skill_ids["统计分析"], "evidence_strength": "strong"},
                    {"skill_id": skill_ids["量化分析"], "evidence_strength": "strong"},
                ],
            },
            db_path=db_path,
        )

        add_job(
            db_path,
            job_id="or-language",
            job_title="数据分析实习生",
            salary="250-350元/天",
            job_description="精通SQL，熟练使用R/Python进行数据分析，参与A/B实验。",
            role_category_v11="数据分析与BI",
            internship_days_per_week="5天/周",
            internship_duration="3个月",
        )
        add_job(
            db_path,
            job_id="hard-days",
            job_title="数据挖掘实习生",
            job_description="Python 数据分析 数据清洗，每周6天，连续5个月。",
            role_category_v11="数据分析与BI",
            internship_days_per_week="6天/周",
            internship_duration="5个月",
        )
        add_job(
            db_path,
            job_id="ai-app",
            job_title="AI应用实习生",
            salary="200-250元/天",
            job_description="熟悉Python，参与AI Agent、Prompt、Tool Calling和工作流编排，完成需求拆解与后端接口开发。",
            role_category_v11="AI与大模型开发",
            internship_days_per_week="5天/周",
            internship_duration="3个月",
        )
        add_job(
            db_path,
            job_id="football-quant",
            job_title="AI预测数据分析师实习生",
            salary="120-150元/天",
            job_description="足球赛事预测、赔率数据、Pandas、NumPy、统计分析、量化分析、机器学习、模型评估。",
            role_category_v11="数据分析与BI",
            internship_days_per_week="5天/周",
            internship_duration="3个月",
        )
        add_job(
            db_path,
            job_id="contradictory",
            job_title="数据分析师（无经验可培养）",
            salary="15-28K",
            job_description="负责平台架构与技术决策，要求5年以上经验，主导团队并精通C++。",
            role_category_v11="数据分析与BI",
        )
        add_job(
            db_path,
            job_id="collection-low",
            job_title="数据采集实习生",
            salary="150元/天",
            job_description="按照流程重复采集测试数据并完成数据录入和基础维护。",
            role_category_v11="数据处理与标注",
            internship_days_per_week="5天/周",
            internship_duration="3个月",
        )
        add_job(
            db_path,
            job_id="closed",
            job_title="商业分析实习生",
            job_description="Python SQL 数据分析 决策支持",
            role_category_v11="数据分析与BI",
        )
        add_job(
            db_path,
            job_id="in-process",
            job_title="AI Agent实习生",
            job_description="Python AI Agent Prompt FastAPI",
            role_category_v11="AI与大模型开发",
        )

        initialize_management_schema(db_path)
        patch_management("closed", {"listing_status": "closed"}, db_path=db_path)
        patch_management("in-process", {"user_status": "applied"}, db_path=db_path)

        first_run = recalculate_decisions(strategy="balanced", db_path=db_path)
        assert first_run["job_count"] == 8
        assert first_run["queue_count"] == 6

        or_job = get_decision("or-language", db_path=db_path)["item"]
        assert any("Python" in item for item in or_job["alternative_satisfied"]), or_job
        assert "R语言" not in or_job["skill_gaps"], or_job

        hard_job = get_decision("hard-days", db_path=db_path)["item"]
        assert hard_job["action_group"] == "defer"
        assert hard_job["hard_conflicts"]

        closed_job = get_decision("closed", db_path=db_path)["item"]
        assert closed_job["action_group"] == "defer"

        contradiction = get_decision("contradictory", db_path=db_path)["item"]
        assert contradiction["information_risks"], contradiction
        assert contradiction["action_group"] == "defer", contradiction

        football = get_decision("football-quant", db_path=db_path)["item"]
        assert football["match_score"] >= 60, football
        assert football["resume_projects"], football
        assert any("xG" in item["project_name"] for item in football["resume_projects"]), football

        in_process = get_decision("in-process", db_path=db_path)["item"]
        assert in_process["queue_eligible"] is False

        pending = list_decisions(db_path=db_path)
        assert pending["total"] == 6
        all_jobs = list_decisions(pending_only=False, db_path=db_path)
        assert all_jobs["total"] == 8

        summary = decision_summary(db_path=db_path)
        assert summary["queue_count"] == 6
        assert sum(summary["by_action_group"].values()) == 6

        get_representative_jobs(limit=8, refresh=True, db_path=db_path)

        upsert_calibration_label(
            "hard-days",
            {"action_group": "defer", "reason": "每周到岗天数冲突。"},
            db_path=db_path,
        )
        upsert_calibration_label(
            "football-quant",
            {"action_group": "apply_now", "reason": "足球预测项目直接匹配。"},
            db_path=db_path,
        )
        upsert_calibration_label(
            "contradictory",
            {"action_group": "defer", "reason": "岗位信息矛盾。"},
            db_path=db_path,
        )

        report = decision_calibration_report(refresh=True, db_path=db_path)
        assert report["label_count"] == 3
        assert report["hard_conflict_misses"] == 0

        second_summary = decision_summary(db_path=db_path)
        assert second_summary["run"]["run_id"] == report["run"]["run_id"]

        stretch_run = recalculate_decisions(strategy="stretch", db_path=db_path)
        assert stretch_run["strategy"] == "stretch"
        conservative_run = recalculate_decisions(strategy="conservative", db_path=db_path)
        assert conservative_run["strategy"] == "conservative"

    print("Explainable decision-engine offline tests passed.")


if __name__ == "__main__":
    main()
