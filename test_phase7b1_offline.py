from __future__ import annotations

import tempfile
from pathlib import Path

from local_api.database import upsert_canonical_job
from local_api.management import (
    bulk_patch_management,
    get_management_history,
    initialize_management_schema,
    list_managed_jobs,
    management_counts,
    patch_management,
)


def main() -> None:
    with tempfile.TemporaryDirectory(
        prefix="job-market-phase7b1-"
    ) as directory:
        db_path = Path(directory) / "test.db"

        upsert_canonical_job(
            {
                "job_id": "phase7b1-test-a",
                "job_title": "AI应用实习生",
                "company_short_name": "测试公司",
                "city": "深圳",
                "salary": "200-300元/天",
                "source_url": "https://example.invalid/a",
            },
            source_type="phase7b1_test",
            db_path=db_path,
        )
        upsert_canonical_job(
            {
                "job_id": "phase7b1-test-b",
                "job_title": "数据分析实习生",
                "company_short_name": "测试公司",
                "city": "杭州",
                "salary": "180-220元/天",
                "source_url": "https://example.invalid/b",
            },
            source_type="phase7b1_test",
            db_path=db_path,
        )

        migration = initialize_management_schema(db_path)
        assert migration["job_count"] == 2
        assert migration["management_count"] == 2

        personal = patch_management(
            "phase7b1-test-a",
            {
                "user_status": "interested",
                "notes": "适合Agent项目经历",
            },
            db_path=db_path,
        )
        assert personal["changed"] is True
        assert personal["analysis_required"] is False

        analysis = patch_management(
            "phase7b1-test-a",
            {
                "quality_override": "exclude",
                "category_manual": "AI与大模型开发",
            },
            db_path=db_path,
        )
        assert analysis["analysis_required"] is True

        bulk = bulk_patch_management(
            [
                "phase7b1-test-a",
                "phase7b1-test-b",
            ],
            {
                "listing_status": "active",
                "archived": True,
            },
            db_path=db_path,
        )
        assert bulk["failed"] == 0
        assert bulk["changed"] == 2
        assert bulk["analysis_required"] is False

        filtered = list_managed_jobs(
            archived=True,
            limit=20,
            db_path=db_path,
        )
        assert filtered["total"] == 2

        history = get_management_history(
            "phase7b1-test-a",
            db_path=db_path,
        )
        assert len(history) >= 5

        counts = management_counts(db_path=db_path)
        assert counts["total"] == 2
        assert counts["archived"] == 2

    print("Phase 7B.1 offline smoke test passed.")


if __name__ == "__main__":
    main()
