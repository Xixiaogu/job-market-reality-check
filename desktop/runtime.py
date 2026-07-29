from __future__ import annotations

# PHASE_91_DESKTOP_PRODUCTIZATION

import argparse
import json
import logging
import os
import runpy
import shutil
import socket
import sqlite3
import sys
import threading
import time
import traceback
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path
from typing import IO, Any


APP_NAME = "JobMarketDecisionSystem"
SERVICE_NAME = "job-market-reality-check-local-api"
DEFAULT_PORT = 8765
TOKEN_MIN_LENGTH = 32
PIPELINE_STEP_MODULES = (
    "pipeline.clean_jobs",
    "pipeline.analyze_jobs",
    "pipeline.audit_skills",
    "pipeline.build_dashboard",
)


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def source_root() -> Path:
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent)).resolve()
    return Path(__file__).resolve().parent


def install_root() -> Path:
    return (
        Path(sys.executable).resolve().parent
        if is_frozen()
        else Path(__file__).resolve().parent
    )


def default_user_data_root() -> Path:
    local_app_data = Path(
        os.environ.get(
            "LOCALAPPDATA",
            Path.home() / "AppData" / "Local",
        )
    )
    return (local_app_data / APP_NAME).resolve()


def locate_extension(root: Path, install: Path) -> Path:
    candidates = (
        install / "browser-extension" / "chrome-mv3",
        root / "extension" / ".output" / "chrome-mv3",
        root / "extension" / ".output" / "chrome-mv3-dev",
        root / "browser-extension" / "chrome-mv3",
    )
    for candidate in candidates:
        if (candidate / "manifest.json").exists():
            return candidate.resolve()
    return candidates[0].resolve()


def configure_environment(user_data: Path) -> dict[str, Path | str]:
    root = source_root()
    install = install_root()
    extension = locate_extension(root, install)
    mode = "packaged" if is_frozen() else "desktop"

    values = {
        "JOB_MARKET_APP_MODE": mode,
        "JOB_MARKET_INSTALL_ROOT": str(install),
        "JOB_MARKET_RESOURCE_ROOT": str(root),
        "JOB_MARKET_USER_DATA_DIR": str(user_data),
        "JOB_MARKET_DATA_DIR": str(user_data / "data"),
        "JOB_MARKET_RUNTIME_DIR": str(user_data / "runtime"),
        "JOB_MARKET_LOCAL_OUTPUT_DIR": str(user_data / "output"),
        "JOB_MARKET_LOG_DIR": str(user_data / "logs"),
        "JOB_MARKET_EXPORT_DIR": str(user_data / "exports"),
        "JOB_MARKET_BACKUP_DIR": str(user_data / "backups"),
        "JOB_MARKET_EXTENSION_DIR": str(extension),
        "PYTHONUTF8": "1",
    }
    os.environ.update(values)
    return {
        "mode": mode,
        "resource_root": root,
        "install_root": install,
        "user_data_root": user_data,
        "extension_dir": extension,
    }


def ensure_directories(user_data: Path) -> None:
    for name in ("data", "runtime", "output", "logs", "exports", "backups"):
        (user_data / name).mkdir(parents=True, exist_ok=True)


def sqlite_backup(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".migrating")
    if temporary.exists():
        temporary.unlink()

    source_connection = sqlite3.connect(source)
    destination_connection = sqlite3.connect(temporary)
    try:
        source_connection.backup(destination_connection)
        destination_connection.commit()
    finally:
        destination_connection.close()
        source_connection.close()

    temporary.replace(destination)


def migrate_legacy_data(root: Path, user_data: Path) -> dict[str, Any]:
    ensure_directories(user_data)
    result: dict[str, Any] = {
        "database_migrated": False,
        "token_migrated": False,
    }

    source_db = root / "data" / "job_market.db"
    destination_db = user_data / "data" / "job_market.db"
    if source_db.exists() and not destination_db.exists():
        sqlite_backup(source_db, destination_db)
        result["database_migrated"] = True
        result["database_source"] = str(source_db)

    source_token = root / "local_api" / "runtime" / "api_token.txt"
    destination_token = user_data / "runtime" / "api_token.txt"
    if source_token.exists() and not destination_token.exists():
        token = source_token.read_text(encoding="utf-8").strip()
        if len(token) >= TOKEN_MIN_LENGTH:
            destination_token.write_text(token, encoding="utf-8")
            result["token_migrated"] = True
            result["token_source"] = str(source_token)

    migration_path = user_data / "runtime" / "migration.json"
    if result["database_migrated"] or result["token_migrated"]:
        migration_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
    return result


# PHASE_92_WINDOWS_PACKAGE
def run_bundled_step(
    module_name: str,
    *,
    user_data: Path,
) -> int:
    if module_name not in PIPELINE_STEP_MODULES:
        raise RuntimeError(f"不允许执行的分析步骤：{module_name}")

    old_cwd = Path.cwd()
    old_argv = sys.argv[:]
    try:
        os.chdir(user_data)
        sys.argv = [module_name]
        try:
            runpy.run_module(
                module_name,
                run_name="__main__",
                alter_sys=True,
            )
        except SystemExit as exc:
            if exc.code in (None, 0):
                return 0
            if isinstance(exc.code, int):
                return int(exc.code)
            print(str(exc.code), file=sys.stderr)
            return 1
        return 0
    finally:
        sys.argv = old_argv
        os.chdir(old_cwd)


def configure_logging(log_path: Path, *, console: bool) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    handlers: list[logging.Handler] = [
        logging.FileHandler(log_path, encoding="utf-8")
    ]
    if console:
        handlers.append(logging.StreamHandler(sys.stdout))
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=handlers,
        force=True,
    )


def probe_service(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with urllib.request.urlopen(
            f"http://{host}:{port}/api/v1/health",
            timeout=timeout,
        ) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, urllib.error.URLError, json.JSONDecodeError):
        return False
    return bool(payload.get("ok") and payload.get("service") == SERVICE_NAME)


def port_available(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
        except OSError:
            return False
    return True


def acquire_lock(path: Path) -> tuple[IO[bytes], bool]:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("a+b")
    handle.seek(0)
    if handle.tell() == 0:
        handle.write(b"0")
        handle.flush()
    handle.seek(0)
    try:
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        handle.close()
        return path.open("rb"), False
    return handle, True


def release_lock(handle: IO[bytes], locked: bool) -> None:
    try:
        if locked:
            handle.seek(0)
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    finally:
        handle.close()


def bootstrap_url(host: str, port: int, token: str, next_path: str) -> str:
    query = urllib.parse.urlencode({"next": next_path})
    fragment = urllib.parse.urlencode({"token": token})
    return f"http://{host}:{port}/launch?{query}#{fragment}"


def open_when_ready(
    host: str,
    port: int,
    token: str,
    next_path: str,
    timeout: float = 20.0,
) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if probe_service(host, port):
            webbrowser.open(bootstrap_url(host, port, token, next_path))
            return
        time.sleep(0.25)
    logging.error("Local service did not become ready within %.1f seconds", timeout)


def show_startup_error(message: str) -> None:
    if os.name == "nt" and is_frozen():
        try:
            import ctypes

            ctypes.windll.user32.MessageBoxW(
                0,
                message,
                "招聘市场分析与投递决策系统",
                0x10,
            )
            return
        except Exception:
            pass
    print(message, file=sys.stderr)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Job Market Decision System desktop launcher"
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--force-setup", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--no-migrate", action="store_true")
    parser.add_argument("--user-data-dir", type=Path)
    parser.add_argument(
        "--run-step",
        dest="run_step",
        choices=PIPELINE_STEP_MODULES,
        help=argparse.SUPPRESS,
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    user_data = (args.user_data_dir or default_user_data_root()).resolve()
    context = configure_environment(user_data)
    ensure_directories(user_data)
    configure_logging(
        user_data / "logs" / "app.log",
        console=not is_frozen(),
    )

    try:
        if args.run_step:
            return run_bundled_step(
                args.run_step,
                user_data=user_data,
            )

        if not args.no_migrate:
            migration = migrate_legacy_data(
                Path(context["resource_root"]),
                user_data,
            )
            if migration["database_migrated"] or migration["token_migrated"]:
                logging.info("Legacy data migration: %s", migration)

        from local_api.config import (
            APP_MODE,
            DB_PATH,
            EXTENSION_DIR,
            TOKEN_PATH,
            USER_DATA_ROOT,
            ensure_runtime_directories,
        )
        from local_api.desktop_runtime import read_desktop_state, write_desktop_state
        from local_api.security import get_or_create_token

        ensure_runtime_directories()
        token = get_or_create_token()
        state = write_desktop_state(
            {
                "last_launcher_mode": APP_MODE,
                "last_launcher_version": "1.0.0",
            }
        )

        if args.check:
            print("Phase 9.1 desktop launcher check passed.")
            print(f"Mode: {APP_MODE}")
            print(f"User data: {USER_DATA_ROOT}")
            print(f"Database: {DB_PATH}")
            print(f"Token: {TOKEN_PATH}")
            print(f"Extension: {EXTENSION_DIR}")
            print(f"Extension bundled: {(EXTENSION_DIR / 'manifest.json').exists()}")
            return 0

        next_path = (
            "/setup"
            if args.force_setup or not bool(state.get("setup_completed"))
            else "/decision"
        )

        if probe_service(args.host, args.port):
            if not args.no_browser:
                webbrowser.open(
                    bootstrap_url(args.host, args.port, token, next_path)
                )
            return 0

        lock_handle, locked = acquire_lock(
            USER_DATA_ROOT / "runtime" / "desktop.lock"
        )
        if not locked:
            deadline = time.monotonic() + 12.0
            while time.monotonic() < deadline:
                if probe_service(args.host, args.port):
                    if not args.no_browser:
                        webbrowser.open(
                            bootstrap_url(args.host, args.port, token, next_path)
                        )
                    lock_handle.close()
                    return 0
                time.sleep(0.3)
            lock_handle.close()
            raise RuntimeError("另一个启动器正在运行，但本地服务没有成功启动。")

        try:
            if not port_available(args.host, args.port):
                raise RuntimeError(
                    f"端口 {args.port} 已被其他程序占用。请关闭占用程序后重试。"
                )

            if not args.no_browser:
                threading.Thread(
                    target=open_when_ready,
                    args=(args.host, args.port, token, next_path),
                    name="open-browser-when-ready",
                    daemon=True,
                ).start()

            import uvicorn

            logging.info(
                "Starting local service mode=%s user_data=%s port=%s",
                APP_MODE,
                USER_DATA_ROOT,
                args.port,
            )
            uvicorn.run(
                "local_api.main:app",
                host=args.host,
                port=args.port,
                reload=False,
                log_config=None,
                access_log=True,
            )
            return 0
        finally:
            release_lock(lock_handle, locked)

    except Exception as exc:
        logging.exception("Desktop launcher failed")
        show_startup_error(
            f"启动失败：{exc}\n\n日志：{user_data / 'logs' / 'app.log'}"
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
