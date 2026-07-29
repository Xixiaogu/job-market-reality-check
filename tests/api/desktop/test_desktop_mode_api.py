from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path


BASE_URL = os.environ.get("JOB_MARKET_API_URL", "http://127.0.0.1:8765").rstrip("/")
LOCAL_APP_DATA = Path(
    os.environ.get(
        "LOCALAPPDATA",
        Path.home() / "AppData" / "Local",
    )
)
USER_DATA_ROOT = Path(
    os.environ.get(
        "JOB_MARKET_USER_DATA_DIR",
        LOCAL_APP_DATA / "JobMarketDecisionSystem",
    )
).resolve()
TOKEN_PATH = USER_DATA_ROOT / "runtime" / "api_token.txt"


def request_json(path: str, *, token: str | None = None) -> dict:
    headers = {}
    if token:
        headers["X-Job-Market-Token"] = token
    request = urllib.request.Request(BASE_URL + path, headers=headers)
    with urllib.request.urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> None:
    if not TOKEN_PATH.exists():
        raise SystemExit(f"Desktop token was not found: {TOKEN_PATH}")
    token = TOKEN_PATH.read_text(encoding="utf-8").strip()

    health = request_json("/api/v1/health")
    status = request_json("/api/v1/desktop/status", token=token)

    assert health.get("ok") is True
    assert health.get("app_mode") in {"desktop", "packaged"}
    assert Path(health["user_data_root"]).resolve() == USER_DATA_ROOT
    assert status.get("ok") is True
    assert Path(status["user_data_root"]).resolve() == USER_DATA_ROOT
    assert "extension_bundle_exists" in status
    assert "extension_state" in status

    print("Desktop-mode API tests passed.")
    print(f"Mode: {health['app_mode']}")
    print(f"User data: {status['user_data_root']}")
    print(f"Jobs: {status['job_count']}")
    print(f"Extension bundled: {status['extension_bundle_exists']}")
    print(f"Extension state: {status['extension_state']}")


if __name__ == "__main__":
    main()
