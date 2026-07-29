from __future__ import annotations

# APPEARANCE_UI_PRODUCTIZATION_V1_TEST

import os
import tempfile
from pathlib import Path

from local_api.appearance_settings import (
    ACRYLIC,
    STANDARD,
    get_appearance,
    save_appearance,
)
from local_api.calibration_ui import render_calibration_page
from local_api.decision_ui import render_decision_page
from local_api.management_ui import render_management_page
from local_api.profile_ui import render_profile_page
from local_api.setup_ui import render_setup_page


FORBIDDEN_USER_LABELS = (
    "Phase 9.1",
    "PHASE 8.2A",
    "Phase 8.2B",
    "Phase 8.1C",
    "Phase 7B.2",
    "Phase 8.2C",
    "岗位市场分析看板 v1.2",
    "统一桌面界面 ·",
)


def test_persisted_appearance() -> None:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "settings.json"
        assert get_appearance(path=path, environ={"JM_GLASS_MODE": "off"}) == STANDARD
        assert get_appearance(path=path, environ={"JM_GLASS_MODE": "system"}) == ACRYLIC

        payload = save_appearance(ACRYLIC, path=path)
        assert payload["appearance"] == ACRYLIC
        assert get_appearance(path=path, environ={"JM_GLASS_MODE": "off"}) == ACRYLIC

        payload = save_appearance(STANDARD, path=path)
        assert payload["appearance"] == STANDARD
        assert get_appearance(path=path, environ={"JM_GLASS_MODE": "system"}) == STANDARD


def test_settings_page_contains_appearance_controls() -> None:
    page = render_setup_page()
    assert "扩展与设置" in page
    assert "标准浅色" in page
    assert "Windows Acrylic" in page
    assert "/api/v1/desktop/appearance" in page
    assert "保存并重启应用" in page


def test_user_pages_hide_internal_phase_labels() -> None:
    pages = (
        render_setup_page(),
        render_decision_page(),
        render_management_page(),
        render_profile_page(),
        render_calibration_page(),
    )
    rendered = "\n".join(pages)
    for label in FORBIDDEN_USER_LABELS:
        assert label not in rendered, label

    dashboard_source = Path("dashboard_ux_v12.py").read_text(encoding="utf-8")
    shell_source = Path("local_api/app_shell.py").read_text(encoding="utf-8")
    assert "岗位市场分析看板 v1.2" not in dashboard_source
    assert "统一桌面界面 ·" not in shell_source


def test_restart_wiring_is_present() -> None:
    desktop = Path("desktop_app.py").read_text(encoding="utf-8")
    main = Path("local_api/main.py").read_text(encoding="utf-8-sig")
    assert "restart-app.request" in desktop
    assert "relaunch_current_process" in desktop
    assert '@app.put("/api/v1/desktop/appearance")' in main
    assert "request_application_restart" in main


if __name__ == "__main__":
    test_persisted_appearance()
    test_settings_page_contains_appearance_controls()
    test_user_pages_hide_internal_phase_labels()
    test_restart_wiring_is_present()
    print("Appearance settings and UI productization tests passed.")
