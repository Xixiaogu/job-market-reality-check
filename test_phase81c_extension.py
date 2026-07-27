from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "extension" / "entrypoints" / "popup" / "main.ts"
STYLE = ROOT / "extension" / "entrypoints" / "popup" / "style.css"
CONFIG = ROOT / "extension" / "wxt.config.ts"


def main() -> None:
    main_text = MAIN.read_text(encoding="utf-8-sig")
    style_text = STYLE.read_text(encoding="utf-8-sig")
    config_text = CONFIG.read_text(encoding="utf-8-sig")

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
    assert "version: '0.9.0'" in config_text

    print("Phase 8.1C extension static test passed.")


if __name__ == "__main__":
    main()
