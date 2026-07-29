from __future__ import annotations

import tempfile
from pathlib import Path

import desktop_app


def main() -> None:
    assert desktop_app.PRODUCT_TITLE == "招聘市场分析与投递决策系统"
    assert desktop_app.is_headless_request(["--no-browser"])
    assert desktop_app.is_headless_request(["--check"])
    assert not desktop_app.is_headless_request([])

    page = desktop_app.startup_html("正在启动", "测试")
    assert "正在启动" in page
    assert "测试" in page
    assert "本地优先" in page

    with tempfile.TemporaryDirectory(prefix="desktop-shell-test-") as directory:
        signal = Path(directory) / "runtime" / "show-window.request"
        desktop_app.request_existing_window(signal)
        assert signal.exists()
        assert signal.read_text(encoding="ascii").isdigit()

    source = Path(desktop_app.__file__).read_text(encoding="utf-8")
    assert 'gui="edgechromium"' in source
    assert "pystray.MenuItem" in source
    assert "webbrowser.open" in source
    assert "window.events.closing" in source
    assert "desktop-shell.lock" in source

    root = Path(desktop_app.__file__).resolve().parent
    icon_png = root / "packaging" / "branding" / "app_icon.png"
    icon_ico = root / "packaging" / "branding" / "app_icon.ico"
    assert icon_png.exists(), icon_png
    assert icon_ico.exists(), icon_ico

    print("Desktop shell source tests passed.")


if __name__ == "__main__":
    main()
