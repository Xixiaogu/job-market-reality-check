from __future__ import annotations

import json

from tests.support.paths import PROJECT_ROOT

ROOT = PROJECT_ROOT
MAIN = ROOT / "extension" / "entrypoints" / "popup" / "main.ts"
STYLE = ROOT / "extension" / "entrypoints" / "popup" / "style.css"
CONFIG = ROOT / "extension" / "wxt.config.ts"
PACKAGE = ROOT / "extension" / "package.json"


def main() -> None:
    main_text = MAIN.read_text(encoding="utf-8-sig")
    style_text = STYLE.read_text(encoding="utf-8-sig")
    config_text = CONFIG.read_text(encoding="utf-8-sig")
    package_version = json.loads(
        PACKAGE.read_text(encoding="utf-8")
    )["version"]

    for fragment in (
        "ProfileOnboardingStatus",
        "/api/v1/profile/onboarding",
        "采集为第一个样本",
        "完成60秒设置",
        "PHASE_81C_EXTENSION_COLD_START",
    ):
        assert fragment in main_text, fragment

    assert "cold-start-panel" in style_text
    assert "PHASE_81C_EXTENSION_COLD_START_STYLE" in style_text
    assert f"version: '{package_version}'" in config_text

    print("Extension profile-onboarding contract tests passed.")


if __name__ == "__main__":
    main()
