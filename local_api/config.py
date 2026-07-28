from __future__ import annotations

import os
import sys
from pathlib import Path


# PHASE_91_DESKTOP_PRODUCTIZATION
PACKAGE_ROOT = Path(__file__).resolve().parent
SOURCE_ROOT = PACKAGE_ROOT.parent
IS_FROZEN = bool(getattr(sys, "frozen", False))

_default_install_root = (
    Path(sys.executable).resolve().parent
    if IS_FROZEN
    else SOURCE_ROOT
)
INSTALL_ROOT = Path(
    os.environ.get(
        "JOB_MARKET_INSTALL_ROOT",
        _default_install_root,
    )
).resolve()

_default_resource_root = Path(
    getattr(sys, "_MEIPASS", SOURCE_ROOT)
)
RESOURCE_ROOT = Path(
    os.environ.get(
        "JOB_MARKET_RESOURCE_ROOT",
        _default_resource_root,
    )
).resolve()

# Compatibility name used throughout the existing codebase.
PROJECT_ROOT = RESOURCE_ROOT
APP_MODE = os.environ.get(
    "JOB_MARKET_APP_MODE",
    "packaged" if IS_FROZEN else "development",
).strip().lower()

_desktop_mode = APP_MODE in {"desktop", "packaged"}
_local_app_data = Path(
    os.environ.get(
        "LOCALAPPDATA",
        Path.home() / "AppData" / "Local",
    )
)
_default_user_data_root = (
    _local_app_data / "JobMarketDecisionSystem"
    if _desktop_mode
    else SOURCE_ROOT
)
USER_DATA_ROOT = Path(
    os.environ.get(
        "JOB_MARKET_USER_DATA_DIR",
        _default_user_data_root,
    )
).resolve()
WORK_ROOT = USER_DATA_ROOT if _desktop_mode else SOURCE_ROOT

DATA_DIR = Path(
    os.environ.get(
        "JOB_MARKET_DATA_DIR",
        USER_DATA_ROOT / "data" if _desktop_mode else SOURCE_ROOT / "data",
    )
).resolve()
DB_PATH = Path(
    os.environ.get(
        "JOB_MARKET_DB_PATH",
        DATA_DIR / "job_market.db",
    )
).resolve()
RUNTIME_DIR = Path(
    os.environ.get(
        "JOB_MARKET_RUNTIME_DIR",
        USER_DATA_ROOT / "runtime"
        if _desktop_mode
        else SOURCE_ROOT / "local_api" / "runtime",
    )
).resolve()
TOKEN_PATH = RUNTIME_DIR / "api_token.txt"
DESKTOP_STATE_PATH = RUNTIME_DIR / "desktop_state.json"

LOCAL_OUTPUT_DIR = Path(
    os.environ.get(
        "JOB_MARKET_LOCAL_OUTPUT_DIR",
        USER_DATA_ROOT / "output"
        if _desktop_mode
        else SOURCE_ROOT / "output" / "local_api",
    )
).resolve()
PIPELINE_LOG_DIR = LOCAL_OUTPUT_DIR / "pipeline_logs"
PIPELINE_BACKUP_DIR = LOCAL_OUTPUT_DIR / "backups"
LOG_DIR = Path(
    os.environ.get(
        "JOB_MARKET_LOG_DIR",
        USER_DATA_ROOT / "logs"
        if _desktop_mode
        else LOCAL_OUTPUT_DIR / "logs",
    )
).resolve()
EXPORT_DIR = Path(
    os.environ.get(
        "JOB_MARKET_EXPORT_DIR",
        USER_DATA_ROOT / "exports"
        if _desktop_mode
        else SOURCE_ROOT / "output" / "exports",
    )
).resolve()
APP_BACKUP_DIR = Path(
    os.environ.get(
        "JOB_MARKET_BACKUP_DIR",
        USER_DATA_ROOT / "backups"
        if _desktop_mode
        else LOCAL_OUTPUT_DIR / "app_backups",
    )
).resolve()

TARGET_JSONL = Path(
    os.environ.get(
        "JOB_MARKET_TARGET_JSONL",
        WORK_ROOT / "output" / "boss_batch" / "jobs.jsonl",
    )
).resolve()
DASHBOARD_PATH = Path(
    os.environ.get(
        "JOB_MARKET_DASHBOARD_PATH",
        WORK_ROOT
        / "output"
        / "visualization_v1_1"
        / "visual_dashboard_v11.html",
    )
).resolve()


def _default_extension_dir() -> Path:
    candidates = (
        INSTALL_ROOT / "browser-extension" / "chrome-mv3",
        SOURCE_ROOT / "extension" / ".output" / "chrome-mv3",
        SOURCE_ROOT / "extension" / ".output" / "chrome-mv3-dev",
        SOURCE_ROOT / "browser-extension" / "chrome-mv3",
    )
    for candidate in candidates:
        if (candidate / "manifest.json").exists():
            return candidate
    return candidates[0]


EXTENSION_DIR = Path(
    os.environ.get(
        "JOB_MARKET_EXTENSION_DIR",
        _default_extension_dir(),
    )
).resolve()

PIPELINE_SCRIPTS = (
    "clean_boss_jobs.py",
    "analyze_boss_jobs.py",
    "audit_boss_skills.py",
    "visualize_boss_jobs_v11.py",
)
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765


def ensure_runtime_directories() -> None:
    for path in (
        USER_DATA_ROOT,
        DATA_DIR,
        RUNTIME_DIR,
        LOCAL_OUTPUT_DIR,
        PIPELINE_LOG_DIR,
        PIPELINE_BACKUP_DIR,
        LOG_DIR,
        EXPORT_DIR,
        APP_BACKUP_DIR,
        TARGET_JSONL.parent,
    ):
        path.mkdir(parents=True, exist_ok=True)
