from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent


def test_decision_route_bundle() -> None:
    from local_api import main

    original_recalculate = main.recalculate_decisions
    original_summary = main.decision_summary
    original_jobs = main.list_decisions
    original_calibration = main.decision_calibration_report

    calls: list[tuple[str, object]] = []

    try:
        main.recalculate_decisions = lambda *, strategy: {
            "ok": True,
            "run_id": 17,
            "strategy": strategy,
            "job_count": 34,
            "queue_count": 28,
        }
        main.decision_summary = lambda *, strategy: {
            "run": {"run_id": 17},
            "strategy": strategy,
            "job_count": 34,
            "queue_count": 28,
        }

        def fake_jobs(*, strategy, pending_only, limit):
            calls.append(("jobs", (strategy, pending_only, limit)))
            return {"run": {"run_id": 17}, "items": [{"job_id": "new-job"}]}

        main.list_decisions = fake_jobs
        main.decision_calibration_report = lambda *, strategy: {
            "strategy": strategy,
            "label_count": 10,
        }

        payload = main.recalculate_decision_scores(
            None,
            strategy="balanced",
            pending_only=False,
            limit=321,
        )
    finally:
        main.recalculate_decisions = original_recalculate
        main.decision_summary = original_summary
        main.list_decisions = original_jobs
        main.decision_calibration_report = original_calibration

    assert payload["run_id"] == 17
    assert payload["summary"]["run"]["run_id"] == 17
    assert payload["jobs"]["items"][0]["job_id"] == "new-job"
    assert payload["calibration"]["label_count"] == 10
    assert calls == [("jobs", ("balanced", False, 321))]


def test_decision_ui_markers() -> None:
    from local_api.decision_ui import render_decision_page

    html = render_decision_page()
    required = (
        "DECISION_AUTO_REFRESH_V1",
        "applyDecisionData",
        "pollDecisionChanges",
        "window.setInterval(pollDecisionChanges,2000)",
        "result.summary",
        "result.jobs",
        "result.calibration",
        "重新计算完成",
    )
    for marker in required:
        assert marker in html, marker


def test_management_ui_markers() -> None:
    from local_api.management_ui import render_management_page

    html = render_management_page()
    required = (
        "pollManagementChanges",
        "window.setInterval(pollManagementChanges,2000)",
        "岗位管理已自动刷新",
    )
    for marker in required:
        assert marker in html, marker


def test_dashboard_auto_refresh_markers() -> None:
    text = (ROOT / "dashboard_ux_v12.py").read_text(
        encoding="utf-8-sig",
    )
    required = (
        "DASHBOARD_AUTO_REFRESH_V1",
        "autoRefreshScheduled",
        "正在自动载入最新看板",
        "window.location.replace",
    )
    for marker in required:
        assert marker in text, marker


def main() -> None:
    test_decision_route_bundle()
    test_decision_ui_markers()
    test_management_ui_markers()
    test_dashboard_auto_refresh_markers()
    print("Auto-refresh and decision-recalculation tests passed.")


if __name__ == "__main__":
    main()
