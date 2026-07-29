from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path
from typing import Any

from tests.support.paths import PROJECT_ROOT

DEFAULT_TOKEN = PROJECT_ROOT / "local_api" / "runtime" / "api_token.txt"


def request_json(url: str, token: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={"X-Job-Market-Token": token},
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8765")
    parser.add_argument("--token-file", type=Path, default=DEFAULT_TOKEN)
    args = parser.parse_args()

    token = args.token_file.read_text(encoding="utf-8-sig").strip()
    if not token:
        raise RuntimeError("API token is empty.")

    base_url = args.base_url.rstrip("/")

    with urllib.request.urlopen(f"{base_url}/profile", timeout=15) as response:
        html = response.read().decode("utf-8")
        cache_control = response.headers.get("Cache-Control") or ""
        assert response.status == 200

    profile = request_json(f"{base_url}/api/v1/profile", token)
    suggestions = request_json(
        f"{base_url}/api/v1/profile/skill-suggestions?limit=20",
        token,
    )

    assert "60秒快速设置" in html
    assert "我的概况" in html
    assert "我的能力" in html
    assert "我的项目" in html
    assert "求职目标" in html
    assert "no-store" in cache_control

    assert "profile" in profile
    assert isinstance(profile["profile"].get("target_job_types"), list)
    assert "target_job_types" in profile["options"]
    assert "items" in suggestions

    print("Profile-preference API tests passed.")
    print(f"URL: {base_url}/profile")
    print(f"Profile completion inputs available: yes")
    print(f"Skills configured: {profile['summary']['skill_count']}")
    print(f"Projects configured: {profile['summary']['project_count']}")
    print(f"Skill suggestions returned: {len(suggestions['items'])}")


if __name__ == "__main__":
    main()
