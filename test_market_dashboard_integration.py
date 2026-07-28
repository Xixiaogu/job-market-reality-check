from __future__ import annotations

# TEST_MARKET_DASHBOARD_INTEGRATION_V1

from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from dashboard_management_link_v13 import (
    END_MARKER,
    START_MARKER,
    enhance_management_link,
)
from local_api.app_shell import SHELL_STYLE, inject_app_shell


class Route:
    def __init__(self, path: str) -> None:
        self.path = path


def fake_app() -> SimpleNamespace:
    return SimpleNamespace(
        routes=[
            Route("/decision"),
            Route("/manage"),
            Route("/dashboard"),
            Route("/profile"),
            Route("/calibrate"),
            Route("/setup"),
        ]
    )


def test_shell_contract() -> None:
    source = """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>岗位市场分析看板</title></head>
<body>
<div class="page"><header><h1>岗位市场分析看板</h1></header></div>
<script>
const sidebar = document.createElement("aside");
sidebar.id = "ux-sidebar";
document.body.append(sidebar);
</script>
<a id="job-management-link" href="/manage" target="_blank">岗位管理中心</a>
</body>
</html>"""

    result = inject_app_shell(source, "/dashboard", fake_app())

    assert 'href="/dashboard"' in result
    assert 'class="jm-nav-item is-active"' in result
    assert "MARKET_DASHBOARD_INTEGRATION_V1" in result
    assert "jm-market-route" in result
    assert 'layout.id = "jm-market-layout"' in result
    assert 'content.id = "jm-market-content"' in result
    assert 'marketNav.setAttribute("aria-label", "市场分析子导航")' in result
    assert 'document.getElementById("job-management-link")?.remove()' in result
    assert "#jm-market-layout" in SHELL_STYLE


def test_legacy_management_link_cleanup() -> None:
    with TemporaryDirectory() as directory:
        path = Path(directory) / "dashboard.html"
        path.write_text(
            "<html><body>"
            + START_MARKER
            + '<a id="job-management-link" href="/manage">岗位管理中心</a>'
            + END_MARKER
            + "</body></html>",
            encoding="utf-8",
        )

        result = enhance_management_link(path)
        cleaned = path.read_text(encoding="utf-8")

        assert "job-management-link" not in cleaned
        assert "岗位管理中心" not in cleaned
        assert result["management_link_removed"] is True


def main() -> None:
    test_shell_contract()
    test_legacy_management_link_cleanup()
    print("Market dashboard integration tests passed.")


if __name__ == "__main__":
    main()
