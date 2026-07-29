from __future__ import annotations

import json
import urllib.error
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
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def main() -> None:
    with urllib.request.urlopen(BASE_URL + "/calibrate", timeout=15) as response:
        html = response.read().decode("utf-8")
        assert response.status == 200
        assert "投递决策校准" in html

    status, sample = request("/api/v1/calibration/representatives")
    assert status == 200
    assert sample["sample_count"] <= 10
    assert sample["sample_count"] > 0
    assert len(sample["items"]) == sample["sample_count"]

    first = sample["items"][0]
    original_label = first.get("label")
    try:
        status, saved = request(
            f"/api/v1/calibration/labels/{first['job_id']}",
            method="PUT",
            body={
                "action_group": "apply_now",
                "reason": "Phase 8.2A在线测试：方向匹配且无明显硬冲突。",
            },
        )
        assert status == 200
        assert saved["label"]["action_group"] == "apply_now"
    finally:
        if original_label:
            request(
                f"/api/v1/calibration/labels/{first['job_id']}",
                method="PUT",
                body={
                    "action_group": original_label["action_group"],
                    "reason": original_label["reason"],
                },
            )
        else:
            request(
                f"/api/v1/calibration/labels/{first['job_id']}",
                method="DELETE",
            )

    status, summary = request("/api/v1/calibration/summary")
    assert status == 200
    assert summary["sample_count"] == sample["sample_count"]

    print("Phase 8.2A calibration API test passed.")
    print(f"URL: {BASE_URL}/calibrate")
    print(f"Representative jobs: {sample['sample_count']}")
    print(f"Labeled jobs: {summary['labeled_count']}")


if __name__ == "__main__":
    main()
