from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = Path(
    os.environ.get(
        "JOB_MARKET_DATA_DIR",
        PROJECT_ROOT / "data",
    )
).resolve()
DB_PATH = Path(
    os.environ.get(
        "JOB_MARKET_DB_PATH",
        DATA_DIR / "job_market.db",
    )
).resolve()
RUNTIME_DIR = PROJECT_ROOT / "local_api" / "runtime"
TOKEN_PATH = RUNTIME_DIR / "api_token.txt"
LOCAL_OUTPUT_DIR = PROJECT_ROOT / "output" / "local_api"
PIPELINE_LOG_DIR = LOCAL_OUTPUT_DIR / "pipeline_logs"
PIPELINE_BACKUP_DIR = LOCAL_OUTPUT_DIR / "backups"
TARGET_JSONL = PROJECT_ROOT / "output" / "boss_batch" / "jobs.jsonl"
DASHBOARD_PATH = (
    PROJECT_ROOT
    / "output"
    / "visualization_v1_1"
    / "visual_dashboard_v11.html"
)
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
        DATA_DIR,
        RUNTIME_DIR,
        LOCAL_OUTPUT_DIR,
        PIPELINE_LOG_DIR,
        PIPELINE_BACKUP_DIR,
        TARGET_JSONL.parent,
    ):
        path.mkdir(parents=True, exist_ok=True)
