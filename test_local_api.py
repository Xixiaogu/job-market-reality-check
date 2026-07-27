from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent
TOKEN_PATH = PROJECT_ROOT / "local_api" / "runtime" / "api_token.txt"
DASHBOARD_PATH = (
    PROJECT_ROOT
    / "output"
    / "visualization_v1_1"
    / "visual_dashboard_v11.html"
)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as file:
        for line_number, line in enumerate(file, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            value = json.loads(stripped)
            if not isinstance(value, dict):
                raise RuntimeError(
                    f"第 {line_number} 行不是 JSON 对象。"
                )
            records.append(value)
    return records


def request_json(
    method: str,
    url: str,
    *,
    token: str | None = None,
    body: Any = None,
    timeout: float = 30,
) -> Any:
    headers = {
        "Accept": "application/json",
    }
    data = None

    if token:
        headers["X-Job-Market-Token"] = token

    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(
            body,
            ensure_ascii=False,
        ).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=data,
        headers=headers,
        method=method,
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=timeout,
        ) as response:
            return json.loads(
                response.read().decode("utf-8")
            )
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode(
            "utf-8",
            errors="replace",
        )
        raise RuntimeError(
            f"HTTP {exc.code}：{body_text}"
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(
            "无法连接本地 API。请先运行 run_local_api.ps1。"
        ) from exc


def print_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="测试本地 FastAPI + SQLite 闭环。"
    )
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8765",
    )
    parser.add_argument(
        "--input",
        type=Path,
        help="可选：扩展导出的 boss-jobs-*.jsonl。",
    )
    parser.add_argument(
        "--run-pipeline",
        action="store_true",
    )
    parser.add_argument(
        "--open-dashboard",
        action="store_true",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=600,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    base_url = args.base_url.rstrip("/")

    if not TOKEN_PATH.exists():
        raise FileNotFoundError(
            f"找不到 API 令牌：{TOKEN_PATH}"
        )

    token = TOKEN_PATH.read_text(
        encoding="utf-8"
    ).strip()

    print("\n[1/4] 健康检查")
    health = request_json(
        "GET",
        f"{base_url}/api/v1/health",
    )
    print_json(health)

    if args.input:
        input_path = args.input.resolve()
        if not input_path.exists():
            raise FileNotFoundError(
                f"找不到扩展 JSONL：{input_path}"
            )

        print("\n[2/4] 通过 API 批量写入岗位")
        jobs = load_jsonl(input_path)
        upsert_result = request_json(
            "POST",
            f"{base_url}/api/v1/jobs/bulk-upsert",
            token=token,
            body={"jobs": jobs},
        )
        print_json(upsert_result)
    else:
        print("\n[2/4] 未提供 --input，跳过岗位写入。")

    if args.run_pipeline:
        print("\n[3/4] 启动分析任务")
        start_result = request_json(
            "POST",
            f"{base_url}/api/v1/pipeline/run",
            token=token,
            body={},
        )
        print_json(start_result)

        deadline = time.time() + args.timeout_seconds

        while True:
            status_result = request_json(
                "GET",
                f"{base_url}/api/v1/pipeline/status",
                token=token,
            )
            run = status_result.get("run") or {}
            status_value = run.get("status")
            current_step = run.get("current_step")
            completed_steps = run.get("completed_steps")

            print(
                f"状态：{status_value} | "
                f"步骤：{completed_steps} | "
                f"当前：{current_step}"
            )

            if status_value in {
                "success",
                "failed",
                "interrupted",
            }:
                print_json(status_result)
                if status_value != "success":
                    return 2
                break

            if time.time() >= deadline:
                raise TimeoutError(
                    "等待分析任务完成超时。"
                )

            time.sleep(2)
    else:
        print("\n[3/4] 未指定 --run-pipeline，跳过分析。")

    print("\n[4/4] 验收结果")
    final_health = request_json(
        "GET",
        f"{base_url}/api/v1/health",
    )
    print_json(final_health)

    if args.open_dashboard:
        if not DASHBOARD_PATH.exists():
            raise FileNotFoundError(
                f"找不到看板：{DASHBOARD_PATH}"
            )

        if os.name == "nt":
            os.startfile(DASHBOARD_PATH)  # type: ignore[attr-defined]
        else:
            print(f"看板：{DASHBOARD_PATH}")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"错误：{exc}", file=sys.stderr)
        raise SystemExit(1)
