from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent
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
    directions = request_json(
        f"{base_url}/api/v1/profile/direction-suggestions?limit=20",
        token,
    )

    assert "个人决策档案" in html
    assert "no-store" in cache_control
    assert "profile" in profile
    assert "skills" in profile
    assert "projects" in profile
    assert "summary" in profile
    assert "items" in suggestions
    assert "items" in directions

    print("Phase 8.1 profile API test passed.")
    print(f"URL: {base_url}/profile")
    print(f"Skills configured: {profile['summary']['skill_count']}")
    print(f"Projects configured: {profile['summary']['project_count']}")
    print(f"Skill suggestions returned: {len(suggestions['items'])}")


if __name__ == "__main__":
    main()
