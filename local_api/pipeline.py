from __future__ import annotations

import os
import subprocess
import sys
import threading
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import (
    DASHBOARD_PATH,
    PIPELINE_LOG_DIR,
    IS_FROZEN,
    PIPELINE_SCRIPTS,
    PROJECT_ROOT,
    USER_DATA_ROOT,
    WORK_ROOT,
    ensure_runtime_directories,
)
from .database import (
    active_pipeline_run,
    create_pipeline_run,
    export_database_to_target,
    latest_pipeline_run,
    update_pipeline_run,
    utc_now,
)


_schedule_lock = threading.Lock()
_pipeline_lock = threading.Lock()


def _new_log_path(run_id: int) -> Path:
    ensure_runtime_directories()
    timestamp = datetime.now().astimezone().strftime(
        "%Y%m%d-%H%M%S"
    )
    return PIPELINE_LOG_DIR / f"pipeline_{run_id}_{timestamp}.log"


def _append_log(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as file:
        file.write(text)
        if not text.endswith("\n"):
            file.write("\n")


def run_pipeline_sync(run_id: int | None = None) -> dict[str, Any]:
    if run_id is None:
        run_id = create_pipeline_run()

    if not _pipeline_lock.acquire(blocking=False):
        raise RuntimeError("已经有一个分析任务正在运行。")

    log_path = _new_log_path(run_id)

    try:
        update_pipeline_run(
            run_id,
            status="running",
            started_at=utc_now(),
            current_step="导出 SQLite 岗位",
            log_path=str(log_path),
        )

        export_result = export_database_to_target()
        input_count = int(export_result["count"])
        update_pipeline_run(
            run_id,
            input_count=input_count,
        )

        _append_log(
            log_path,
            "=" * 72
            + "\nSQLite 岗位导出\n"
            + "=" * 72
            + f"\n岗位数：{input_count}"
            + f"\n目标文件：{export_result['target_path']}"
            + f"\n备份文件：{export_result['backup_path']}\n",
        )

        environment = os.environ.copy()
        environment["PYTHONUTF8"] = "1"
        completed_steps = 0

        for index, script_name in enumerate(
            PIPELINE_SCRIPTS,
            start=1,
        ):
            script_path = PROJECT_ROOT / script_name
            if not script_path.exists():
                raise FileNotFoundError(
                    f"缺少分析脚本：{script_path}"
                )

            current_step = f"{index}/{len(PIPELINE_SCRIPTS)} {script_name}"
            update_pipeline_run(
                run_id,
                current_step=current_step,
                completed_steps=completed_steps,
            )
            _append_log(
                log_path,
                "\n" + "=" * 72 + f"\n{current_step}\n" + "=" * 72,
            )

            # PHASE_92_WINDOWS_PACKAGE
            command = (
                [
                    sys.executable,
                    "--run-script",
                    script_name,
                    "--no-migrate",
                    "--user-data-dir",
                    str(USER_DATA_ROOT),
                ]
                if IS_FROZEN
                else [sys.executable, str(script_path)]
            )
            result = subprocess.run(
                command,
                cwd=WORK_ROOT,
                env=environment,
                text=True,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )

            if result.stdout:
                _append_log(log_path, result.stdout)
            if result.stderr:
                _append_log(
                    log_path,
                    "[stderr]\n" + result.stderr,
                )

            if result.returncode != 0:
                raise RuntimeError(
                    f"{script_name} 失败，退出码：{result.returncode}"
                )

            completed_steps = index
            update_pipeline_run(
                run_id,
                completed_steps=completed_steps,
            )

        if not DASHBOARD_PATH.exists():
            raise FileNotFoundError(
                f"分析完成，但没有找到看板：{DASHBOARD_PATH}"
            )

        update_pipeline_run(
            run_id,
            status="success",
            finished_at=utc_now(),
            current_step="完成",
            completed_steps=len(PIPELINE_SCRIPTS),
            return_code=0,
            dashboard_path=str(DASHBOARD_PATH),
        )
        _append_log(
            log_path,
            f"\n分析完成。\n看板：{DASHBOARD_PATH}\n",
        )

        return latest_pipeline_run() or {
            "run_id": run_id,
            "status": "success",
        }

    except Exception as exc:
        error_message = str(exc)
        _append_log(
            log_path,
            "\n[异常]\n"
            + error_message
            + "\n"
            + traceback.format_exc(),
        )
        update_pipeline_run(
            run_id,
            status="failed",
            finished_at=utc_now(),
            return_code=1,
            error_message=error_message,
            log_path=str(log_path),
        )
        return latest_pipeline_run() or {
            "run_id": run_id,
            "status": "failed",
            "error_message": error_message,
        }

    finally:
        _pipeline_lock.release()


def _thread_target(run_id: int) -> None:
    run_pipeline_sync(run_id)


def schedule_pipeline() -> dict[str, Any]:
    with _schedule_lock:
        active = active_pipeline_run()
        if active:
            return {
                "started": False,
                "run": active,
            }

        run_id = create_pipeline_run()
        thread = threading.Thread(
            target=_thread_target,
            args=(run_id,),
            name=f"job-market-pipeline-{run_id}",
            daemon=True,
        )
        thread.start()

        return {
            "started": True,
            "run": latest_pipeline_run(),
        }
