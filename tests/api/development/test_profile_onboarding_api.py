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
        assert response.status == 200
        assert "no-store" in (response.headers.get("Cache-Control") or "")

    profile = request_json(f"{base_url}/api/v1/profile", token)
    onboarding = request_json(f"{base_url}/api/v1/profile/onboarding", token)
    skills = request_json(
        f"{base_url}/api/v1/profile/skill-suggestions?limit=30",
        token,
    )
    directions = request_json(
        f"{base_url}/api/v1/profile/direction-suggestions?limit=30",
        token,
    )

    assert "onboarding" in profile
    assert onboarding["job_count"] >= 0
    assert onboarding["maturity"]["stage"] in {
        "cold_start", "first_sample", "emerging", "stable"
    }
    assert "recommendation_basis" in onboarding
    assert "source_explanations" in onboarding
    assert "mode" in skills and "maturity" in skills
    assert "mode" in directions and "maturity" in directions
    assert all("source_label" in item for item in skills["items"])
    assert all("source_label" in item for item in directions["items"])
    assert "首次使用引导" in html
    assert "项目证据可稍后补充" in html

    print("Profile-onboarding API tests passed.")
    print(f"URL: {base_url}/profile")
    print(f"Job samples: {onboarding['job_count']}")
    print(f"Maturity: {onboarding['maturity']['confidence']}")
    print(f"Recommendation basis: {onboarding['recommendation_basis']}")
    print(f"Skill suggestion mode: {skills['mode']}")


if __name__ == "__main__":
    main()
