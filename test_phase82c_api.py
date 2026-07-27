from __future__ import annotations

import json
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
        raw = response.read()
        content_type = response.headers.get("Content-Type", "")
        if "application/json" in content_type:
            return response.status, json.loads(raw.decode("utf-8"))
        return response.status, raw.decode("utf-8")


def main() -> None:
    status, html = request("/decision")
    assert status == 200
    assert "投递决策中心" in html
    assert "只看待投递队列" in html

    status, options = request("/api/v1/decision/options")
    assert status == 200
    strategy = options["default_strategy"]

    status, summary = request(
        "/api/v1/decision/summary?strategy=" + urllib.parse.quote(strategy)
    )
    assert status == 200
    assert summary["job_count"] > 0
    assert sum(summary["by_action_group"].values()) == summary["queue_count"]

    status, jobs = request(
        "/api/v1/decision/jobs?strategy="
        + urllib.parse.quote(strategy)
        + "&pending_only=true&limit=500"
    )
    assert status == 200
    assert jobs["total"] == summary["queue_count"]
    assert jobs["items"]

    first = jobs["items"][0]
    status, detail = request(
        "/api/v1/decision/jobs/"
        + urllib.parse.quote(str(first["job_id"]), safe="")
        + "?strategy="
        + urllib.parse.quote(strategy)
    )
    assert status == 200
    assert detail["item"]["job_id"] == first["job_id"]
    assert "components" in detail["item"]
    assert "resume_projects" in detail["item"]

    status, calibration = request(
        "/api/v1/decision/calibration?strategy=" + urllib.parse.quote(strategy)
    )
    assert status == 200
    assert calibration["hard_conflict_misses"] == 0

    print("Phase 8.2C decision center API test passed.")
    print("URL: http://127.0.0.1:8765/decision")
    print(f"Strategy: {summary['strategy_label']}")
    print(f"Pending queue: {summary['queue_count']}")
    print(
        "Action groups: "
        + ", ".join(
            f"{key}={value}" for key, value in summary["by_action_group"].items()
        )
    )
    print(f"Top job: {first['job_title']} | priority={first['priority_score']}")


if __name__ == "__main__":
    main()
