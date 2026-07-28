from __future__ import annotations

import argparse
import json
import shutil
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def request_bytes(url: str, *, token: str | None = None, method: str = "GET") -> bytes:
    headers = {}
    if token:
        headers["X-Job-Market-Token"] = token
    request = urllib.request.Request(url, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=8) as response:
        return response.read()


def request_json(url: str, *, token: str | None = None, method: str = "GET") -> dict:
    return json.loads(request_bytes(url, token=token, method=method).decode("utf-8"))


def wait_for_health(base_url: str, process: subprocess.Popen[bytes], timeout: float) -> dict:
    deadline = time.monotonic() + timeout
    last_error = ""
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"Packaged application exited early with code {process.returncode}.")
        try:
            payload = request_json(base_url + "/api/v1/health")
            if payload.get("ok"):
                return payload
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
            last_error = str(exc)
        time.sleep(0.35)
    raise RuntimeError(f"Packaged service did not become healthy: {last_error}")


def tail_log(path: Path, limit: int = 100) -> str:
    if not path.exists():
        return "(app.log was not created)"
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(lines[-limit:])


def remove_tree_with_retries(path: Path) -> None:
    for attempt in range(8):
        try:
            shutil.rmtree(path)
            return
        except FileNotFoundError:
            return
        except OSError:
            if attempt == 7:
                raise
            time.sleep(0.4)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release-dir", required=True, type=Path)
    args = parser.parse_args()

    release_dir = args.release_dir.resolve()
    executable = release_dir / "JobMarketDecisionSystem.exe"
    manifest = release_dir / "browser-extension" / "chrome-mv3" / "manifest.json"
    readme = release_dir / "README_FIRST.txt"

    for required in (executable, manifest, readme):
        if not required.exists():
            raise SystemExit(f"Required release file was not found: {required}")

    manifest_payload = json.loads(manifest.read_text(encoding="utf-8"))
    if int(manifest_payload.get("manifest_version", 0)) != 3:
        raise SystemExit("The bundled browser extension is not a Manifest V3 extension.")

    temp_root = Path(tempfile.mkdtemp(prefix="phase92-release-"))
    user_data = temp_root / "user-data"
    port = free_port()
    base_url = f"http://127.0.0.1:{port}"
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

    process = subprocess.Popen(
        [
            str(executable),
            "--no-browser",
            "--no-migrate",
            "--user-data-dir",
            str(user_data),
            "--port",
            str(port),
        ],
        cwd=str(release_dir),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creationflags,
    )

    try:
        health = wait_for_health(base_url, process, timeout=60.0)
        token_path = user_data / "runtime" / "api_token.txt"
        deadline = time.monotonic() + 10.0
        while not token_path.exists() and time.monotonic() < deadline:
            time.sleep(0.2)
        if not token_path.exists():
            raise RuntimeError(f"Packaged token was not created: {token_path}")

        token = token_path.read_text(encoding="utf-8").strip()
        status = request_json(base_url + "/api/v1/desktop/status", token=token)
        request_bytes(base_url + "/setup")
        request_bytes(base_url + "/decision")
        completed = request_json(
            base_url + "/api/v1/desktop/complete-setup",
            token=token,
            method="POST",
        )

        assert health.get("app_mode") == "packaged", health
        assert Path(health["user_data_root"]).resolve() == user_data.resolve(), health
        assert status.get("extension_bundle_exists") is True, status
        assert Path(status["extension_dir"]).resolve() == manifest.parent.resolve(), status
        assert completed.get("setup_completed") is True, completed
        assert (user_data / "data" / "job_market.db").exists()
        assert (user_data / "logs" / "app.log").exists()

        print("Phase 9.2 packaged release smoke test passed.")
        print(f"Executable: {executable}")
        print(f"Mode: {health['app_mode']}")
        print(f"Extension: {status['extension_dir']}")
        print(f"Database initialized: {user_data / 'data' / 'job_market.db'}")
    except Exception as exc:
        log_text = tail_log(user_data / "logs" / "app.log")
        raise SystemExit(f"{exc}\n\nPackaged app log:\n{log_text}") from exc
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=12)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        time.sleep(0.5)
        remove_tree_with_retries(temp_root)


if __name__ == "__main__":
    main()
