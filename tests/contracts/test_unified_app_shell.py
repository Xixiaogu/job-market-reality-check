from __future__ import annotations

# TEST_UNIFIED_APP_SHELL_V1

from types import SimpleNamespace

from local_api.app_shell import inject_app_shell


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


def main() -> None:
    source = """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>测试</title></head>
<body>
<div class="shell">
  <header class="top">
    <a href="/profile" target="_blank">个人档案</a>
    <a href="/manage" target="_blank">岗位管理</a>
    <a href="https://example.com/job/1" target="_blank">原岗位</a>
  </header>
  <main>content</main>
</div>
</body>
</html>"""

    result = inject_app_shell(source, "/decision", fake_app())
    assert 'id="jm-app-shell"' in result
    assert 'class="jm-nav-item is-active"' in result
    assert 'href="/decision"' in result
    assert 'href="/manage"' in result
    assert 'href="/dashboard"' in result
    assert 'href="/profile"' in result
    assert "jm-unified-shell-body" in result
    assert result.count('id="jm-app-shell"') == 1

    second = inject_app_shell(result, "/decision", fake_app())
    assert second == result

    print("Unified app shell injection test passed.")


if __name__ == "__main__":
    main()
