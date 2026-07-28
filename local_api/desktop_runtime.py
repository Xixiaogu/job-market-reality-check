from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import (
    APP_MODE,
    DB_PATH,
    DESKTOP_STATE_PATH,
    EXTENSION_DIR,
    INSTALL_ROOT,
    LOG_DIR,
    TOKEN_PATH,
    USER_DATA_ROOT,
    ensure_runtime_directories,
)


PHASE_MARKER = "PHASE_91_DESKTOP_PRODUCTIZATION"


def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def read_desktop_state() -> dict[str, Any]:
    ensure_runtime_directories()
    if not DESKTOP_STATE_PATH.exists():
        return {}
    try:
        payload = json.loads(DESKTOP_STATE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def write_desktop_state(updates: dict[str, Any]) -> dict[str, Any]:
    ensure_runtime_directories()
    state = read_desktop_state()
    state.update(updates)
    state["updated_at"] = utc_now()
    temporary = DESKTOP_STATE_PATH.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    temporary.replace(DESKTOP_STATE_PATH)
    return state


def record_extension_activity(
    *,
    source: str,
    imported_count: int,
) -> dict[str, Any]:
    return write_desktop_state(
        {
            "last_extension_activity_at": utc_now(),
            "last_extension_activity_source": source,
            "last_extension_imported_count": int(imported_count),
        }
    )


def complete_setup() -> dict[str, Any]:
    return write_desktop_state(
        {
            "setup_completed": True,
            "setup_completed_at": utc_now(),
        }
    )


def setup_completed() -> bool:
    return bool(read_desktop_state().get("setup_completed"))


def desktop_status(*, job_count: int = 0) -> dict[str, Any]:
    state = read_desktop_state()
    last_activity = str(state.get("last_extension_activity_at") or "")
    if last_activity:
        extension_state = "active"
    elif job_count > 0:
        extension_state = "data_detected"
    else:
        extension_state = "not_detected"

    return {
        "ok": True,
        "app_mode": APP_MODE,
        "setup_completed": bool(state.get("setup_completed")),
        "user_data_root": str(USER_DATA_ROOT),
        "database_path": str(DB_PATH),
        "token_path": str(TOKEN_PATH),
        "log_dir": str(LOG_DIR),
        "install_root": str(INSTALL_ROOT),
        "extension_dir": str(EXTENSION_DIR),
        "extension_bundle_exists": (EXTENSION_DIR / "manifest.json").exists(),
        "extension_state": extension_state,
        "last_extension_activity_at": last_activity or None,
        "job_count": int(job_count),
        "state_path": str(DESKTOP_STATE_PATH),
    }


def _open_folder(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"目录不存在：{resolved}")

    if os.name == "nt":
        os.startfile(str(resolved))  # type: ignore[attr-defined]
    elif sys_platform() == "darwin":
        subprocess.Popen(["open", str(resolved)])
    else:
        subprocess.Popen(["xdg-open", str(resolved)])

    return {"ok": True, "path": str(resolved)}


def sys_platform() -> str:
    import sys

    return sys.platform


def open_extension_folder() -> dict[str, Any]:
    return _open_folder(EXTENSION_DIR)


def open_user_data_folder() -> dict[str, Any]:
    ensure_runtime_directories()
    return _open_folder(USER_DATA_ROOT)
