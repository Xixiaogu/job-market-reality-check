from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

from local_api.database import connect, utc_now
from local_api.profile import (
    direction_suggestions,
    initialize_profile_schema,
    patch_profile,
    profile_onboarding_status,
    replace_preferences,
    skill_suggestions,
)
from local_api.profile_ui import PAGE_VERSION, render_profile_page


def insert_job(db_path: Path, job_id: str, payload: dict[str, object]) -> None:
    now = utc_now()
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    with connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO jobs (
                job_id, job_title, company_name, city, salary,
                source_url, source_type, schema_version, canonical_json,
                content_hash, first_seen_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job_id,
                str(payload.get("job_title", "")),
                str(payload.get("company_name", "")),
                str(payload.get("city", "")),
                str(payload.get("salary", "")),
                str(payload.get("source_url", "")),
                "boss",
                "1.0",
                canonical,
                digest,
                now,
                now,
            ),
        )


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="job-market-phase81c-") as directory:
        db_path = Path(directory) / "test.db"
        initialize_profile_schema(db_path)

        cold = profile_onboarding_status(db_path=db_path)
        assert cold["job_count"] == 0
        assert cold["maturity"]["stage"] == "cold_start"
        assert cold["next_action"] == "collect_first_job"
        assert cold["project_is_optional"] is True

        patch_profile(
            {
                "education": "本科",
                "graduation_year": 2027,
                "target_job_types": ["daily_internship"],
                "accepts_remote": True,
            },
            db_path=db_path,
        )
        replace_preferences(
            [{"direction": "数据分析与BI", "interest_level": "very_high"}],
            db_path=db_path,
        )

        starter_skills = skill_suggestions(db_path=db_path, limit=50)
        assert starter_skills["mode"] == "cold_start"
        assert starter_skills["starter_used"] is True
        assert any(item["source"] == "direction_starter" for item in starter_skills["items"])
        assert all(item["source_label"] for item in starter_skills["items"])

        starter_directions = direction_suggestions(db_path=db_path, limit=50)
        assert starter_directions["mode"] == "cold_start"
        assert any(item["source"] == "starter_pack" for item in starter_directions["items"])

        insert_job(
            db_path,
            "job-first",
            {
                "job_title": "数据分析实习生",
                "company_name": "示例公司",
                "city": "深圳",
                "salary": "200-250元/天",
                "source_url": "https://example.invalid/job-first",
                "job_description": "使用 Python、SQL、Pandas 完成数据分析和可视化。",
                "role_category_v11": "数据分析与BI",
                "job_tags": ["Python", "SQL"],
            },
        )

        first = profile_onboarding_status(db_path=db_path)
        assert first["job_count"] == 1
        assert first["maturity"]["stage"] == "first_sample"

        corpus_skills = skill_suggestions(db_path=db_path, limit=50)
        python_item = next(item for item in corpus_skills["items"] if item["skill_name"] == "Python")
        assert python_item["source"] == "job_corpus"
        assert python_item["job_count"] == 1
        assert "已采集岗位" in python_item["source_label"]

        html = render_profile_page()
        for fragment in (
            "首次使用引导",
            "先用一个真实岗位启动你的档案",
            "来源：用户确认",
            "冷启动方向建议",
            "项目证据可稍后补充",
        ):
            assert fragment in html, fragment
        assert PAGE_VERSION == "8.1C"

    print("Profile-onboarding offline tests passed.")


if __name__ == "__main__":
    main()
