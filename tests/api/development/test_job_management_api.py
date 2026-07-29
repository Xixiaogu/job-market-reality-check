from __future__ import annotations

import argparse
import json
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from tests.support.paths import PROJECT_ROOT

DEFAULT_TOKEN = (
    PROJECT_ROOT
    / "local_api"
    / "runtime"
    / "api_token.txt"
)


def request_json(
    url: str,
    token: str,
) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={
            "X-Job-Market-Token": token,
        },
    )
    with urllib.request.urlopen(
        request,
        timeout=10,
    ) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8765",
    )
    parser.add_argument(
        "--token-file",
        type=Path,
        default=DEFAULT_TOKEN,
    )
    args = parser.parse_args()

    token = args.token_file.read_text(
        encoding="utf-8-sig"
    ).strip()
    if not token:
        raise RuntimeError("API token is empty.")

    base_url = args.base_url.rstrip("/")

    health = request_json(
        f"{base_url}/api/v1/health",
        token,
    )
    options = request_json(
        f"{base_url}/api/v1/management/options",
        token,
    )
    summary = request_json(
        f"{base_url}/api/v1/management/summary",
        token,
    )
    jobs = request_json(
        f"{base_url}/api/v1/jobs?"
        + urllib.parse.urlencode(
            {
                "limit": 5,
                "archived": "false",
            }
        ),
        token,
    )

    assert health["ok"] is True
    assert "management" in health
    assert "user_statuses" in options
    assert summary["total"] == health["job_count"]
    assert "items" in jobs

    output = {
        "ok": True,
        "job_count": health["job_count"],
        "management_count": summary["total"],
        "active": summary["active"],
        "archived": summary["archived"],
        "sample_returned": len(jobs["items"]),
        "user_statuses": options["user_statuses"],
    }
    print(
        json.dumps(
            output,
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
