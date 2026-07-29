from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

from local_api.profile import (
    TARGET_JOB_TYPES,
    get_full_profile,
    get_profile,
    initialize_profile_schema,
    patch_profile,
    profile_options,
)
from local_api.profile_ui import render_profile_page


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="job-market-phase81b-") as directory:
        db_path = Path(directory) / "test.db"

        initialize_profile_schema(db_path)
        profile = get_profile(db_path=db_path)
        assert profile["target_job_types"] == []

        patched = patch_profile(
            {
                "education": "本科",
                "major": "电子信息科学与技术",
                "graduation_year": 2027,
                "target_job_types": [
                    "daily_internship",
                    "research_assistant",
                ],
                "max_days_per_week": 5,
                "min_internship_months": 3,
                "accepts_remote": True,
                "accepts_relocation": True,
                "available_from": "2026年8月",
            },
            db_path=db_path,
        )
        assert patched["profile"]["target_job_types"] == [
            "daily_internship",
            "research_assistant",
        ]

        full_profile = get_full_profile(db_path=db_path)
        assert full_profile["profile"]["education"] == "本科"
        assert set(profile_options()["target_job_types"]) == set(TARGET_JOB_TYPES)

        html = render_profile_page()
        required_fragments = (
            "60秒快速设置",
            "我的概况",
            "我的能力",
            "我的项目",
            "求职目标",
        )
        for fragment in required_fragments:
            assert fragment in html, fragment
        assert "PHASE_" not in html
        assert "Phase " not in html

    print("Phase 8.1B low-friction profile offline test passed.")


if __name__ == "__main__":
    main()
