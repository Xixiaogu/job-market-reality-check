from __future__ import annotations

import tempfile
from pathlib import Path

from local_api.database import iter_canonical_jobs, upsert_canonical_job
from local_api.management import initialize_management_schema, patch_management
from local_api.management_ui import render_management_page


def main() -> None:
    html = render_management_page()
    for marker in (
        "岗位管理中心",
        "bulk-management",
        "drawer-quality",
        "/api/v1/jobs/",
        "localStorage",
    ):
        if marker not in html:
            raise AssertionError(
                f"Management UI marker missing: {marker}"
            )

    with tempfile.TemporaryDirectory(
        prefix="job-market-phase7b2-"
    ) as directory:
        db_path = Path(directory) / "test.db"

        for job_id, title in (
            ("phase7b2-keep", "保留岗位"),
            ("phase7b2-exclude", "排除岗位"),
        ):
            upsert_canonical_job(
                {
                    "job_id": job_id,
                    "job_title": title,
                    "company_short_name": "测试公司",
                    "city": "深圳",
                    "salary": "200元/天",
                    "source_url": (
                        f"https://example.invalid/{job_id}"
                    ),
                },
                source_type="phase7b2_test",
                db_path=db_path,
            )

        initialize_management_schema(db_path)
        patch_management(
            "phase7b2-exclude",
            {"quality_override": "exclude"},
            db_path=db_path,
        )

        exported = list(
            iter_canonical_jobs(db_path=db_path)
        )
        assert len(exported) == 1
        assert exported[0]["job_id"] == "phase7b2-keep"

    print("Job-management UI tests passed.")


if __name__ == "__main__":
    main()
