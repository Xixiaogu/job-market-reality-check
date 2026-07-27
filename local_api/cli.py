from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .config import (
    DASHBOARD_PATH,
    DB_PATH,
    PIPELINE_SCRIPTS,
    PROJECT_ROOT,
    TARGET_JSONL,
    TOKEN_PATH,
)
from .database import (
    count_jobs,
    import_canonical_jsonl,
    import_extension_jsonl,
    initialize_database,
    latest_pipeline_run,
    recover_interrupted_pipeline_runs,
)
from .pipeline import run_pipeline_sync
from .security import get_or_create_token


def print_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def command_init(args: argparse.Namespace) -> int:
    initialize_database()
    recover_interrupted_pipeline_runs()
    token = get_or_create_token()

    result: dict[str, Any] = {
        "database_path": str(DB_PATH),
        "token_path": str(TOKEN_PATH),
        "token_length": len(token),
        "imported": None,
    }

    source = Path(args.source).resolve()
    if source.exists():
        result["imported"] = import_canonical_jsonl(source)
    elif not args.allow_empty:
        raise FileNotFoundError(
            f"初始化时找不到现有岗位文件：{source}"
        )

    result["job_count"] = count_jobs()
    print_json(result)
    return 0


def command_doctor(_: argparse.Namespace) -> int:
    initialize_database()
    get_or_create_token()

    checks = {
        "project_root": PROJECT_ROOT.exists(),
        "database_parent": DB_PATH.parent.exists(),
        "token_exists": TOKEN_PATH.exists(),
        "importer_exists": (
            PROJECT_ROOT / "import_extension_jobs.py"
        ).exists(),
        "target_jsonl_exists": TARGET_JSONL.exists(),
        "pipeline_scripts": {
            script: (PROJECT_ROOT / script).exists()
            for script in PIPELINE_SCRIPTS
        },
        "dashboard_exists": DASHBOARD_PATH.exists(),
        "job_count": count_jobs(),
        "latest_pipeline": latest_pipeline_run(),
    }

    print_json(checks)

    required_ok = (
        checks["project_root"]
        and checks["database_parent"]
        and checks["token_exists"]
        and checks["importer_exists"]
        and all(checks["pipeline_scripts"].values())
    )
    return 0 if required_ok else 2


def command_stats(_: argparse.Namespace) -> int:
    initialize_database()
    print_json(
        {
            "database_path": str(DB_PATH),
            "job_count": count_jobs(),
            "latest_pipeline": latest_pipeline_run(),
            "dashboard_path": str(DASHBOARD_PATH),
            "dashboard_exists": DASHBOARD_PATH.exists(),
        }
    )
    return 0


def command_import_extension(
    args: argparse.Namespace,
) -> int:
    result = import_extension_jsonl(
        Path(args.input).resolve()
    )
    result["job_count"] = count_jobs()
    print_json(result)
    return 0 if not result["issues"] else 2


def command_pipeline(_: argparse.Namespace) -> int:
    result = run_pipeline_sync()
    print_json(result)
    return 0 if result.get("status") == "success" else 2


def command_token(_: argparse.Namespace) -> int:
    print(get_or_create_token())
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Job Market Reality Check 本地 API 管理工具。"
    )
    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    init_parser = subparsers.add_parser(
        "init",
        help="初始化 SQLite，并导入现有规范岗位 JSONL。",
    )
    init_parser.add_argument(
        "--source",
        default=str(TARGET_JSONL),
        help="现有 output/boss_batch/jobs.jsonl 路径。",
    )
    init_parser.add_argument(
        "--allow-empty",
        action="store_true",
        help="源文件不存在时允许创建空数据库。",
    )
    init_parser.set_defaults(func=command_init)

    doctor_parser = subparsers.add_parser(
        "doctor",
        help="检查数据库、脚本、令牌和看板路径。",
    )
    doctor_parser.set_defaults(func=command_doctor)

    stats_parser = subparsers.add_parser(
        "stats",
        help="显示 SQLite 岗位数和最近分析任务。",
    )
    stats_parser.set_defaults(func=command_stats)

    import_parser = subparsers.add_parser(
        "import-extension",
        help="把扩展 JSONL 直接写入 SQLite。",
    )
    import_parser.add_argument("input")
    import_parser.set_defaults(func=command_import_extension)

    pipeline_parser = subparsers.add_parser(
        "pipeline",
        help="从 SQLite 导出岗位并同步运行分析管线。",
    )
    pipeline_parser.set_defaults(func=command_pipeline)

    token_parser = subparsers.add_parser(
        "token",
        help="显示本地 API 写入令牌。",
    )
    token_parser.set_defaults(func=command_token)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        return int(args.func(args))
    except Exception as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
