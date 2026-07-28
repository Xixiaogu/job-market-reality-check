from __future__ import annotations

# APPEARANCE_SETTINGS_V1

import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Mapping

from .config import RUNTIME_DIR, USER_DATA_ROOT


STANDARD = "standard"
ACRYLIC = "acrylic"
ALLOWED_APPEARANCES = {STANDARD, ACRYLIC}
SETTINGS_PATH = USER_DATA_ROOT / "settings.json"
RESTART_REQUEST_PATH = RUNTIME_DIR / "restart-app.request"


def normalize_appearance(value: object) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {ACRYLIC, "system", "glass", "true", "1", "on"}:
        return ACRYLIC
    return STANDARD


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
        text=True,
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        temp_path.replace(path)
    finally:
        temp_path.unlink(missing_ok=True)


def inferred_appearance(environ: Mapping[str, str] | None = None) -> str:
    target = os.environ if environ is None else environ
    mode = str(target.get("JM_GLASS_MODE", "")).strip().lower()
    return ACRYLIC if mode in {"system", "glass", "1", "true", "yes", "on"} else STANDARD


def get_appearance(
    *,
    path: Path = SETTINGS_PATH,
    environ: Mapping[str, str] | None = None,
) -> str:
    payload = _read_json(path)
    if "appearance" in payload:
        return normalize_appearance(payload.get("appearance"))
    return inferred_appearance(environ)


def get_settings(path: Path = SETTINGS_PATH) -> dict[str, Any]:
    payload = _read_json(path)
    payload["appearance"] = get_appearance(path=path)
    return payload


def save_appearance(
    appearance: object,
    *,
    path: Path = SETTINGS_PATH,
) -> dict[str, Any]:
    normalized = normalize_appearance(appearance)
    payload = _read_json(path)
    payload["appearance"] = normalized
    payload["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    _atomic_write_json(path, payload)
    return payload


def request_application_restart(path: Path = RESTART_REQUEST_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(time.time_ns()), encoding="ascii")
    return path


def appearance_status() -> dict[str, Any]:
    selected = get_appearance()
    windows_build = 0
    supported = os.name == "nt"
    try:
        from windows_glass import windows_build_number

        windows_build = windows_build_number()
        supported = os.name == "nt" and windows_build >= 22621
    except Exception:
        supported = os.name == "nt"

    effective = selected
    fallback_reason = None
    if selected == ACRYLIC and not supported:
        effective = STANDARD
        fallback_reason = "当前系统不支持 Windows Acrylic，已使用标准浅色。"

    return {
        "selected": selected,
        "effective": effective,
        "supported": supported,
        "windows_build": windows_build,
        "fallback_reason": fallback_reason,
        "settings_path": str(SETTINGS_PATH),
        "restart_required": False,
    }
