from __future__ import annotations

# DESKTOP_SHELL_V1

import html
import json
import logging
import os
import sys
import threading
import time
import traceback
import webbrowser
from pathlib import Path
from typing import Any

import desktop_launcher as legacy


PRODUCT_TITLE = "招聘市场分析与投递决策系统"
APP_USER_MODEL_ID = "JobMarketDecisionSystem.Desktop.1"
SHELL_VERSION = "1.0.6-glass-exp"


def is_headless_request(argv: list[str]) -> bool:
    return any(flag in argv for flag in ("--no-browser", "--check"))


def set_windows_app_id() -> None:
    if os.name != "nt":
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            APP_USER_MODEL_ID
        )
    except Exception:
        logging.debug("Could not set Windows AppUserModelID", exc_info=True)


def branding_path(filename: str) -> Path:
    candidates = (
        legacy.source_root() / "packaging" / "branding" / filename,
        legacy.install_root() / "packaging" / "branding" / filename,
        Path(__file__).resolve().parent / "packaging" / "branding" / filename,
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return candidates[0].resolve()


def startup_html(status: str, detail: str = "") -> str:
    safe_status = html.escape(status)
    safe_detail = html.escape(detail)
    detail_html = (
        f'<p class="detail">{safe_detail}</p>' if safe_detail else ""
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{PRODUCT_TITLE}</title>
<style>
:root {{
  color-scheme: light dark;
  --bg: #f4f7fb;
  --card: #ffffff;
  --text: #152033;
  --muted: #667085;
  --accent: #2563eb;
  --line: #dbe4f0;
}}
@media (prefers-color-scheme: dark) {{
  :root {{
    --bg: #101827;
    --card: #182235;
    --text: #eef4ff;
    --muted: #a9b6c9;
    --accent: #7aa7ff;
    --line: #2c3a50;
  }}
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  min-height: 100vh;
  display: grid;
  place-items: center;
  font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif;
  background: var(--bg);
  color: var(--text);
}}
main {{
  width: min(560px, calc(100vw - 48px));
  padding: 40px;
  border: 1px solid var(--line);
  border-radius: 20px;
  background: var(--card);
}}
.brand {{
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 32px;
}}
.logo {{
  width: 52px;
  height: 52px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  background: var(--accent);
  color: white;
  font-size: 26px;
  font-weight: 700;
}}
h1 {{
  margin: 0 0 6px;
  font-size: 22px;
  font-weight: 650;
}}
.subtitle {{
  margin: 0;
  color: var(--muted);
  font-size: 14px;
}}
.status {{
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 16px;
}}
.spinner {{
  width: 22px;
  height: 22px;
  border: 3px solid var(--line);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin .8s linear infinite;
}}
.detail {{
  margin: 12px 0 0 34px;
  color: var(--muted);
  font-size: 14px;
  line-height: 1.7;
}}
.note {{
  margin-top: 28px;
  padding-top: 18px;
  border-top: 1px solid var(--line);
  color: var(--muted);
  font-size: 13px;
}}
@keyframes spin {{ to {{ transform: rotate(360deg); }} }}
</style>
</head>
<body>
<main>
  <div class="brand">
    <div class="logo">J</div>
    <div>
      <h1>{PRODUCT_TITLE}</h1>
      <p class="subtitle">本地优先 · 岗位采集 · 市场分析 · 投递决策</p>
    </div>
  </div>
  <div class="status">
    <div class="spinner" aria-hidden="true"></div>
    <strong>{safe_status}</strong>
  </div>
  {detail_html}
  <div class="note">首次启动可能需要几秒钟。岗位数据和个人档案默认保存在本机。</div>
</main>
</body>
</html>"""


def error_html(message: str, log_path: Path) -> str:
    safe_message = html.escape(message)
    safe_log = html.escape(str(log_path))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>启动失败</title>
<style>
body {{
  margin: 0;
  min-height: 100vh;
  display: grid;
  place-items: center;
  font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif;
  background: #f7f7f8;
  color: #172033;
}}
main {{
  width: min(680px, calc(100vw - 48px));
  padding: 36px;
  border: 1px solid #e1e5ea;
  border-radius: 18px;
  background: white;
}}
h1 {{ margin-top: 0; font-size: 22px; }}
pre {{
  white-space: pre-wrap;
  word-break: break-word;
  padding: 16px;
  border-radius: 12px;
  background: #f4f6f8;
}}
p {{ color: #667085; line-height: 1.7; }}
</style>
</head>
<body>
<main>
  <h1>本地应用启动失败</h1>
  <pre>{safe_message}</pre>
  <p>详细日志：{safe_log}</p>
  <p>请退出托盘中的应用后重试。若窗口无法正常渲染，请确认系统已安装 Microsoft Edge WebView2 Runtime。</p>
</main>
</body>
</html>"""


def request_existing_window(signal_path: Path) -> None:
    signal_path.parent.mkdir(parents=True, exist_ok=True)
    signal_path.write_text(str(time.time_ns()), encoding="ascii")


class DesktopShell:
    def __init__(
        self,
        *,
        window: Any,
        host: str,
        port: int,
        token: str,
        next_path: str,
        user_data: Path,
        signal_path: Path,
    ) -> None:
        self.window = window
        self.host = host
        self.port = port
        self.token = token
        self.next_path = next_path
        self.user_data = user_data
        self.signal_path = signal_path
        self.log_path = user_data / "logs" / "app.log"
        self.exit_requested = False
        self.tray_ready = False
        self.tray_icon: Any | None = None
        self.server: Any | None = None
        self.server_thread: threading.Thread | None = None
        self.service_owned = False
        self.stop_event = threading.Event()
        self.signal_thread: threading.Thread | None = None
        self.tray_thread: threading.Thread | None = None
        self.glass_mode = os.environ.get("JM_GLASS_MODE", "system")
        self.glass_material = os.environ.get("JM_GLASS_MATERIAL", "acrylic")
        self.glass_result: dict[str, Any] | None = None

    def _load_status(self, status: str, detail: str = "") -> None:
        try:
            self.window.load_html(startup_html(status, detail))
        except Exception:
            logging.debug("Could not update startup window", exc_info=True)

    def before_show(self) -> None:
        if os.name != "nt":
            return

        icon_path = branding_path("app_icon.ico")
        if icon_path.exists():
            try:
                import clr

                clr.AddReference("System.Drawing")
                from System.Drawing import Icon

                self.window.native.Icon = Icon(str(icon_path))
            except Exception:
                logging.debug("Could not set native window icon", exc_info=True)

        try:
            from windows_glass import apply_windows_glass

            self.glass_result = apply_windows_glass(
                self.window.native,
                mode=self.glass_mode,
                material=self.glass_material,
            )
            logging.info("Windows glass experiment result: %s", self.glass_result)
        except Exception:
            logging.exception("Windows glass experiment failed; using standard window")

    def on_closing(self) -> bool:
        if self.exit_requested or not self.tray_ready:
            return True
        try:
            self.window.hide()
        except Exception:
            logging.debug("Could not hide window", exc_info=True)
        return False

    def on_closed(self) -> None:
        if not self.exit_requested:
            self.exit_requested = True
        self.stop_event.set()

    def show_window(self, *_: Any) -> None:
        try:
            self.window.show()
            self.window.restore()
        except Exception:
            logging.debug("Could not restore main window", exc_info=True)

    def open_in_browser(self, *_: Any) -> None:
        webbrowser.open(
            legacy.bootstrap_url(
                self.host,
                self.port,
                self.token,
                self.next_path,
            )
        )

    def open_data_directory(self, *_: Any) -> None:
        self._open_path(self.user_data)

    def open_log_directory(self, *_: Any) -> None:
        self._open_path(self.log_path.parent)

    @staticmethod
    def _open_path(path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)
        if os.name == "nt":
            os.startfile(str(path))  # type: ignore[attr-defined]
        else:
            webbrowser.open(path.as_uri())

    def request_exit(self, *_: Any) -> None:
        if self.exit_requested:
            return
        self.exit_requested = True
        self.stop_event.set()
        if self.server is not None and self.service_owned:
            self.server.should_exit = True
        if self.tray_icon is not None:
            try:
                self.tray_icon.stop()
            except Exception:
                logging.debug("Could not stop tray icon", exc_info=True)
        try:
            self.window.destroy()
        except Exception:
            logging.debug("Could not destroy main window", exc_info=True)

    def _run_tray(self) -> None:
        try:
            import pystray
            from PIL import Image

            image = Image.open(branding_path("app_icon.png")).convert("RGBA")
            menu = pystray.Menu(
                pystray.MenuItem(
                    "打开主界面",
                    self.show_window,
                    default=True,
                ),
                pystray.MenuItem(
                    "在浏览器中打开",
                    self.open_in_browser,
                ),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(
                    "打开数据目录",
                    self.open_data_directory,
                ),
                pystray.MenuItem(
                    "查看日志",
                    self.open_log_directory,
                ),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(
                    "退出",
                    self.request_exit,
                ),
            )
            self.tray_icon = pystray.Icon(
                "JobMarketDecisionSystem",
                image,
                PRODUCT_TITLE,
                menu,
            )
            self.tray_ready = True
            self.tray_icon.run()
        except Exception:
            self.tray_ready = False
            logging.exception("System tray failed to start")

    def _start_tray(self) -> None:
        self.tray_thread = threading.Thread(
            target=self._run_tray,
            name="desktop-tray",
            daemon=True,
        )
        self.tray_thread.start()

    def _watch_show_signal(self) -> None:
        last_seen = 0
        while not self.stop_event.wait(0.3):
            try:
                if not self.signal_path.exists():
                    continue
                modified = self.signal_path.stat().st_mtime_ns
                if modified > last_seen:
                    last_seen = modified
                    self.show_window()
            except OSError:
                logging.debug("Show-signal watcher failed", exc_info=True)

    def _start_signal_watcher(self) -> None:
        self.signal_thread = threading.Thread(
            target=self._watch_show_signal,
            name="desktop-show-signal",
            daemon=True,
        )
        self.signal_thread.start()

    def _run_server(self) -> None:
        assert self.server is not None
        self.server.run()

    def _start_service_if_needed(self) -> None:
        if legacy.probe_service(self.host, self.port):
            logging.info("Attaching desktop shell to existing local service")
            self.service_owned = False
            return

        if not legacy.port_available(self.host, self.port):
            raise RuntimeError(
                f"端口 {self.port} 已被其他程序占用，且该程序不是本系统服务。"
            )

        import uvicorn

        config = uvicorn.Config(
            "local_api.main:app",
            host=self.host,
            port=self.port,
            reload=False,
            log_config=None,
            access_log=True,
        )
        self.server = uvicorn.Server(config)
        self.service_owned = True
        self.server_thread = threading.Thread(
            target=self._run_server,
            name="local-fastapi-service",
            daemon=True,
        )
        self.server_thread.start()

    def _wait_until_ready(self, timeout: float = 25.0) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if legacy.probe_service(self.host, self.port):
                return
            if self.server_thread is not None and not self.server_thread.is_alive():
                raise RuntimeError("本地服务在启动过程中异常退出。")
            time.sleep(0.25)
        raise RuntimeError(f"本地服务在 {timeout:.0f} 秒内未能启动。")

    def bootstrap(self) -> None:
        try:
            self._start_tray()
            self._start_signal_watcher()
            self._load_status(
                "正在检查本地数据",
                str(self.user_data),
            )
            self._start_service_if_needed()
            self._load_status(
                "正在启动本地分析服务",
                f"http://{self.host}:{self.port}",
            )
            self._wait_until_ready()
            self._load_status("正在打开投递决策看板")
            url = legacy.bootstrap_url(
                self.host,
                self.port,
                self.token,
                self.next_path,
            )
            self.window.load_url(url)
            logging.info("Desktop shell loaded %s", self.next_path)
        except Exception as exc:
            logging.exception("Desktop shell bootstrap failed")
            self.window.load_html(error_html(str(exc), self.log_path))

    def cleanup(self) -> None:
        self.stop_event.set()
        if self.server is not None and self.service_owned:
            self.server.should_exit = True
        if self.server_thread is not None:
            self.server_thread.join(timeout=8)
        if self.tray_icon is not None:
            try:
                self.tray_icon.stop()
            except Exception:
                pass


def run_desktop_shell() -> int:
    args = legacy.build_parser().parse_args()
    user_data = (args.user_data_dir or legacy.default_user_data_root()).resolve()
    context = legacy.configure_environment(user_data)
    legacy.ensure_directories(user_data)
    legacy.configure_logging(
        user_data / "logs" / "app.log",
        console=not legacy.is_frozen(),
    )

    try:
        if not args.no_migrate:
            migration = legacy.migrate_legacy_data(
                Path(context["resource_root"]),
                user_data,
            )
            if migration["database_migrated"] or migration["token_migrated"]:
                logging.info("Legacy data migration: %s", migration)

        from local_api.config import (
            APP_MODE,
            USER_DATA_ROOT,
            ensure_runtime_directories,
        )
        from local_api.desktop_runtime import write_desktop_state
        from local_api.security import get_or_create_token

        ensure_runtime_directories()
        token = get_or_create_token()
        from windows_glass import (
            configure_webview_environment,
            requested_material,
            requested_mode,
        )

        glass_mode = requested_mode()
        glass_material = requested_material()
        glass_environment = configure_webview_environment(glass_mode)
        logging.info("Windows glass experiment environment: %s", glass_environment)

        state = write_desktop_state(
            {
                "last_launcher_mode": APP_MODE,
                "last_launcher_version": SHELL_VERSION,
                "desktop_shell_enabled": True,
                "windows_glass_mode": glass_mode,
                "windows_glass_material": glass_material,
            }
        )
        next_path = (
            "/setup"
            if args.force_setup or not bool(state.get("setup_completed"))
            else "/decision"
        )

        lock_handle, locked = legacy.acquire_lock(
            USER_DATA_ROOT / "runtime" / "desktop-shell.lock"
        )
        signal_path = USER_DATA_ROOT / "runtime" / "show-window.request"
        if not locked:
            request_existing_window(signal_path)
            lock_handle.close()
            return 0

        set_windows_app_id()

        import webview

        webview.settings["OPEN_EXTERNAL_LINKS_IN_BROWSER"] = True
        window = webview.create_window(
            PRODUCT_TITLE,
            html=startup_html("正在准备桌面应用"),
            width=1320,
            height=840,
            min_size=(980, 640),
            resizable=True,
            maximized=False,
            background_color=(
                "#000000" if glass_mode == "system" else "#f4f7fb"
            ),
            text_select=True,
            zoomable=True,
        )
        shell = DesktopShell(
            window=window,
            host=args.host,
            port=args.port,
            token=token,
            next_path=next_path,
            user_data=USER_DATA_ROOT,
            signal_path=signal_path,
        )
        window.events.before_show += shell.before_show
        window.events.closing += shell.on_closing
        window.events.closed += shell.on_closed

        storage_path = USER_DATA_ROOT / "runtime" / "webview-profile"
        storage_path.mkdir(parents=True, exist_ok=True)

        try:
            webview.start(
                shell.bootstrap,
                gui="edgechromium",
                debug=False,
                private_mode=False,
                storage_path=str(storage_path),
            )
            return 0
        finally:
            shell.cleanup()
            legacy.release_lock(lock_handle, locked)

    except Exception as exc:
        logging.exception("Desktop application failed")
        legacy.show_startup_error(
            "桌面应用启动失败："
            f"{exc}\n\n"
            "请确认系统已安装 Microsoft Edge WebView2 Runtime。\n"
            f"日志：{user_data / 'logs' / 'app.log'}"
        )
        return 1


def main() -> int:
    if is_headless_request(sys.argv[1:]):
        return legacy.main()
    return run_desktop_shell()


if __name__ == "__main__":
    raise SystemExit(main())
