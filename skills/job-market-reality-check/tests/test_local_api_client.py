from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "job_market_local_api_client",
    ROOT / "scripts" / "local_api_client.py",
)
assert SPEC and SPEC.loader
CLIENT_MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CLIENT_MODULE)

TOKEN = "test-token-" + "x" * 32


class Handler(BaseHTTPRequestHandler):
    requests: list[dict[str, Any]] = []

    def log_message(self, *_: Any) -> None:
        return

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)
        Handler.requests.append(
            {
                "method": self.command,
                "path": parsed.path,
                "query": query,
                "token": self.headers.get("X-Job-Market-Token"),
            }
        )
        if parsed.path != "/api/v1/health" and self.headers.get(
            "X-Job-Market-Token"
        ) != TOKEN:
            self._json({"detail": "unauthorized"}, status=401)
            return
        payloads: dict[str, dict[str, Any]] = {
            "/api/v1/health": {
                "ok": True,
                "service": "job-market-reality-check-local-api",
                "version": "1.0.0",
                "app_mode": "desktop",
                "job_count": 3,
                "database_path": "must-not-leak",
            },
            "/api/v1/decision/options": {
                "engine_version": "8.2",
                "default_strategy": "balanced",
                "strategies": [{"value": "balanced", "label": "平衡"}],
            },
            "/api/v1/management/summary": {
                "total": 3,
                "active": 3,
                "archived": 0,
                "by_user_status": {"to_review": 3},
                "by_quality_override": {"auto": 3},
            },
            "/api/v1/profile": {
                "profile": {"education": "本科"},
                "cities": [],
                "skills": [{"skill_name": "Python"}],
                "projects": [{"project_name": "测试项目"}],
                "directions": [],
                "options": {},
                "summary": {"skill_count": 1},
                "onboarding": {"complete": True},
            },
            "/api/v1/decision/summary": {
                "run": {"run_id": 7, "created_at": "2026-07-29T00:00:00Z"},
                "strategy": "balanced",
                "strategy_label": "平衡",
                "job_count": 3,
                "queue_count": 3,
                "by_action_group": {"apply_now": 1, "stretch": 2},
                "hard_conflict_count": 0,
                "information_risk_count": 0,
                "top_jobs": [],
            },
        }
        if parsed.path == "/api/v1/decision/jobs":
            offset = int(query.get("offset", ["0"])[0])
            all_items = [
                {"job_id": "job-1", "action_group": "apply_now"},
                {"job_id": "job-2", "action_group": "stretch"},
                {"job_id": "job-3", "action_group": "stretch"},
            ]
            page_size = 2
            self._json(
                {
                    "run": {"run_id": 7},
                    "total": len(all_items),
                    "limit": 500,
                    "offset": offset,
                    "items": all_items[offset : offset + page_size],
                }
            )
            return
        payload = payloads.get(parsed.path)
        if payload is None:
            self._json({"detail": "not found"}, status=404)
            return
        self._json(payload)

    def _json(self, payload: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    Handler.requests = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with tempfile.TemporaryDirectory(prefix="job-market-api-client-") as directory:
            token_file = Path(directory) / "api_token.txt"
            token_file.write_text(TOKEN, encoding="utf-8")
            client = CLIENT_MODULE.LocalAPIClient(
                base_url=f"http://127.0.0.1:{server.server_port}",
                token_path=token_file,
            )
            context = client.brief_context()
        assert context["contract_version"] == "1.0.0"
        assert context["metadata"]["decision_run_id"] == 7
        assert len(context["decision_jobs"]) == 3
        assert context["health"]["job_count"] == 3
        serialized = json.dumps(context, ensure_ascii=False)
        assert TOKEN not in serialized
        assert "database_path" not in serialized
        assert Handler.requests[0]["path"] == "/api/v1/health"
        assert Handler.requests[0]["token"] is None
        assert all(
            item["method"] == "GET"
            for item in Handler.requests
        )
        assert all(
            item["token"] == TOKEN
            for item in Handler.requests[1:]
        )
        decision_pages = [
            item
            for item in Handler.requests
            if item["path"] == "/api/v1/decision/jobs"
        ]
        assert len(decision_pages) == 2

        Handler.requests = []
        with tempfile.TemporaryDirectory(prefix="job-market-api-cli-") as directory:
            token_file = Path(directory) / "api_token.txt"
            token_file.write_text(TOKEN, encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "local_api_client.py"),
                    "--base-url",
                    f"http://127.0.0.1:{server.server_port}",
                    "--token-file",
                    str(token_file),
                    "brief",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
        assert completed.returncode == 0, completed.stdout
        cli_context = json.loads(completed.stdout)
        assert cli_context["metadata"]["decision_run_id"] == 7
        assert len(cli_context["decision_jobs"]) == 3
        assert TOKEN not in completed.stdout
        assert all(item["method"] == "GET" for item in Handler.requests)

        try:
            CLIENT_MODULE.LocalAPIClient(base_url="https://example.com")
        except ValueError:
            pass
        else:
            raise AssertionError("Non-local API host was accepted.")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    print("Skill local API client unit test passed.")


if __name__ == "__main__":
    main()
