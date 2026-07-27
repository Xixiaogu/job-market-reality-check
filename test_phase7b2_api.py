from __future__ import annotations

import argparse
import urllib.request


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8765",
    )
    args = parser.parse_args()

    url = args.base_url.rstrip("/") + "/manage"
    with urllib.request.urlopen(url, timeout=10) as response:
        html = response.read().decode("utf-8")
        cache_control = (
            response.headers.get("Cache-Control") or ""
        )
        status = response.status

    assert status == 200
    assert "岗位管理中心" in html
    assert "bulk-management" in html
    assert "no-store" in cache_control

    print("Phase 7B.2 management page API test passed.")
    print(f"URL: {url}")
    print(f"HTML bytes: {len(html.encode('utf-8'))}")


if __name__ == "__main__":
    main()
