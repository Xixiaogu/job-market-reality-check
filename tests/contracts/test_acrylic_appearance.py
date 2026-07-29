from __future__ import annotations

# WINDOWS_GLASS_EXPERIMENT_V1_TEST

import os
from dataclasses import dataclass

from local_api.app_shell import inject_app_shell
from desktop.windows_effects import (
    MODE_OFF,
    MODE_SYSTEM,
    WEBVIEW_BACKGROUND_ENV,
    configure_webview_environment,
    normalize_glass_mode,
    normalize_material,
)


@dataclass
class FakeRoute:
    path: str


class FakeApp:
    routes = [
        FakeRoute("/decision"),
        FakeRoute("/manage"),
        FakeRoute("/dashboard"),
        FakeRoute("/profile"),
        FakeRoute("/calibrate"),
        FakeRoute("/setup"),
    ]


def test_environment_configuration() -> None:
    env: dict[str, str] = {}
    result = configure_webview_environment("system", env)
    assert result["mode"] == MODE_SYSTEM
    assert env[WEBVIEW_BACKGROUND_ENV] == "00000000"

    result = configure_webview_environment("off", env)
    assert result["mode"] == MODE_OFF
    assert WEBVIEW_BACKGROUND_ENV not in env

    assert normalize_glass_mode("true") == MODE_SYSTEM
    assert normalize_glass_mode("standard") == MODE_OFF
    assert normalize_material("mica") == "mica"
    assert normalize_material("unknown") == "acrylic"


def test_shell_system_glass_injection() -> None:
    source = "<html><head></head><body><main>OK</main></body></html>"
    previous = os.environ.get("JM_GLASS_MODE")
    try:
        os.environ["JM_GLASS_MODE"] = "system"
        rendered = inject_app_shell(source, "/profile", FakeApp())
        assert 'id="jm-app-shell"' in rendered
        assert 'id="jm-system-glass-style"' in rendered
        assert "jm-system-glass" in rendered

        os.environ["JM_GLASS_MODE"] = "off"
        rendered = inject_app_shell(source, "/profile", FakeApp())
        assert 'id="jm-app-shell"' in rendered
        assert 'id="jm-system-glass-style"' not in rendered
        assert "jm-system-glass" not in rendered
    finally:
        if previous is None:
            os.environ.pop("JM_GLASS_MODE", None)
        else:
            os.environ["JM_GLASS_MODE"] = previous


def test_source_markers() -> None:
    desktop = open("desktop/app.py", encoding="utf-8").read()
    native = open("desktop/windows_effects.py", encoding="utf-8").read()
    shell = open("local_api/app_shell.py", encoding="utf-8").read()

    assert "1.0.7-appearance" in desktop
    assert "configure_webview_environment" in desktop
    assert "apply_windows_glass" in desktop
    assert "WINDOWS_GLASS_EXPERIMENT_V1" in native
    assert "DWMWA_SYSTEMBACKDROP_TYPE" in native
    assert "WEBVIEW2_DEFAULT_BACKGROUND_COLOR" in native
    assert "jm-system-glass-style" in shell


if __name__ == "__main__":
    test_environment_configuration()
    test_shell_system_glass_injection()
    test_source_markers()
    print("Windows Acrylic appearance contract tests passed.")
