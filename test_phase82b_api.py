from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
TOKEN_PATH = PROJECT_ROOT / "local_api" / "runtime" / "api_token.txt"
BASE_URL = "http://127.0.0.1:8765"


def request(path: str, *, method: str = "GET", body=None):
    token = TOKEN_PATH.read_text(encoding="utf-8-sig").strip()
    data = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        BASE_URL + path,
        data=data,
        method=method,
        headers={
            "Content-Type": "application/json",
            "X-Job-Market-Token": token,
        },
    )
    with urllib.request.urlopen(req, timeout=60) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def main() -> None:
    status, options = request("/api/v1/decision/options")
    assert status == 200
    assert options["default_strategy"] == "balanced"

    status, run = request(
        "/api/v1/decision/recalculate?strategy=balanced",
        method="POST",
    )
    assert status == 200
    assert run["engine_version"].startswith("8.2b")
    assert run["job_count"] > 0

    status, summary = request("/api/v1/decision/summary?strategy=balanced")
    assert status == 200
    assert summary["job_count"] == run["job_count"]
    assert sum(summary["by_action_group"].values()) == summary["queue_count"]

    status, jobs = request(
        "/api/v1/decision/jobs?strategy=balanced&pending_only=true&limit=100"
    )
    assert status == 200
    assert jobs["total"] == summary["queue_count"]
    assert jobs["items"]

    first = jobs["items"][0]
    encoded_job_id = urllib.parse.quote(str(first["job_id"]), safe="")
    status, detail = request(
        f"/api/v1/decision/jobs/{encoded_job_id}?strategy=balanced"
    )
    assert status == 200
    assert detail["item"]["job_id"] == first["job_id"]
    assert "components" in detail["item"]
    assert "suggested_action" in detail["item"]

    status, calibration = request(
        "/api/v1/decision/calibration?strategy=balanced"
    )
    assert status == 200
    assert calibration["label_count"] >= 0
    assert calibration["hard_conflict_misses"] == 0

    print("Phase 8.2B explainable decision engine API test passed.")
    print(f"Jobs scored: {summary['job_count']}")
    print(f"Pending queue: {summary['queue_count']}")
    print(
        "Action groups: "
        + ", ".join(
            f"{key}={value}"
            for key, value in summary["by_action_group"].items()
        )
    )
    if calibration["exact_accuracy"] is not None:
        print(f"Calibration exact accuracy: {calibration['exact_accuracy']:.1%}")
        print(f"Calibration adjacent accuracy: {calibration['adjacent_accuracy']:.1%}")
        print(f"Top-5 overlap: {calibration['top5_overlap_count']}/5")
    print(f"Top job: {first['job_title']} | priority={first['priority_score']}")


if __name__ == "__main__":
    main()
