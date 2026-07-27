from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .config import (
    DB_PATH,
    PIPELINE_BACKUP_DIR,
    TARGET_JSONL,
    ensure_runtime_directories,
)
from .importer_adapter import (
    canonical_job_id,
    convert_payload,
    merge_canonical_nonempty,
    merge_extension_into_canonical,
)


ACTIVE_PIPELINE_STATUSES = ("queued", "running")



class ClosingConnection(sqlite3.Connection):
    """Commit or roll back, then close the SQLite handle on context exit."""

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            return super().__exit__(exc_type, exc_value, traceback)
        finally:
            self.close()


# PHASE_81_SQLITE_CLOSE_FIX

def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def json_dumps(value: Any, *, pretty: bool = False) -> str:
    if pretty:
        return json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )

    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def json_hash(value: Any) -> str:
    return hashlib.sha256(
        json_dumps(value).encode("utf-8")
    ).hexdigest()


def connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    ensure_runtime_directories()
    connection = sqlite3.connect(
        db_path,
        timeout=30,
        check_same_thread=False,
        factory=ClosingConnection,
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA synchronous = NORMAL")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def initialize_database(db_path: Path = DB_PATH) -> None:
    with connect(db_path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                job_title TEXT NOT NULL DEFAULT '',
                company_name TEXT NOT NULL DEFAULT '',
                city TEXT NOT NULL DEFAULT '',
                salary TEXT NOT NULL DEFAULT '',
                source_url TEXT NOT NULL DEFAULT '',
                source_type TEXT NOT NULL DEFAULT '',
                schema_version TEXT NOT NULL DEFAULT '',
                canonical_json TEXT NOT NULL,
                raw_extension_json TEXT,
                content_hash TEXT NOT NULL,
                raw_hash TEXT,
                first_seen_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                revision INTEGER NOT NULL DEFAULT 1
            );

            CREATE INDEX IF NOT EXISTS idx_jobs_title
            ON jobs(job_title);

            CREATE INDEX IF NOT EXISTS idx_jobs_company
            ON jobs(company_name);

            CREATE INDEX IF NOT EXISTS idx_jobs_city
            ON jobs(city);

            CREATE INDEX IF NOT EXISTS idx_jobs_updated_at
            ON jobs(updated_at DESC);

            CREATE TABLE IF NOT EXISTS pipeline_runs (
                run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                status TEXT NOT NULL,
                requested_at TEXT NOT NULL,
                started_at TEXT,
                finished_at TEXT,
                input_count INTEGER NOT NULL DEFAULT 0,
                completed_steps INTEGER NOT NULL DEFAULT 0,
                current_step TEXT NOT NULL DEFAULT '',
                return_code INTEGER,
                dashboard_path TEXT NOT NULL DEFAULT '',
                log_path TEXT NOT NULL DEFAULT '',
                error_message TEXT NOT NULL DEFAULT ''
            );

            CREATE INDEX IF NOT EXISTS idx_pipeline_runs_requested
            ON pipeline_runs(requested_at DESC);
            """
        )




def recover_interrupted_pipeline_runs(
    *,
    db_path: Path = DB_PATH,
) -> int:
    initialize_database(db_path)

    with connect(db_path) as connection:
        cursor = connection.execute(
            """
            UPDATE pipeline_runs
            SET status = 'interrupted',
                finished_at = ?,
                error_message = CASE
                    WHEN error_message = ''
                    THEN '服务重启时任务仍处于活动状态。'
                    ELSE error_message
                END
            WHERE status IN ('queued', 'running')
            """,
            (utc_now(),),
        )
        return int(cursor.rowcount)

def _company_name(record: dict[str, Any]) -> str:
    return str(
        record.get("company_full_name")
        or record.get("company_short_name")
        or ""
    ).strip()


def _summary_fields(record: dict[str, Any]) -> dict[str, str]:
    return {
        "job_title": str(record.get("job_title") or "").strip(),
        "company_name": _company_name(record),
        "city": str(record.get("city") or "").strip(),
        "salary": str(record.get("salary") or "").strip(),
        "source_url": str(
            record.get("source_url")
            or record.get("final_url")
            or ""
        ).strip(),
        "schema_version": str(
            record.get("extension_schema_version") or ""
        ).strip(),
    }


def get_canonical_job(
    job_id: str,
    *,
    db_path: Path = DB_PATH,
) -> dict[str, Any] | None:
    with connect(db_path) as connection:
        row = connection.execute(
            "SELECT canonical_json FROM jobs WHERE job_id = ?",
            (job_id,),
        ).fetchone()

    if row is None:
        return None

    return json.loads(row["canonical_json"])


def upsert_canonical_job(
    incoming: dict[str, Any],
    *,
    source_type: str,
    raw_extension: dict[str, Any] | None = None,
    db_path: Path = DB_PATH,
) -> dict[str, Any]:
    initialize_database(db_path)

    job_id = canonical_job_id(incoming)
    if not job_id:
        raise ValueError("规范岗位记录缺少 job_id。")

    now = utc_now()
    raw_json = (
        json_dumps(raw_extension)
        if raw_extension is not None
        else None
    )
    raw_hash = (
        json_hash(raw_extension)
        if raw_extension is not None
        else None
    )

    with connect(db_path) as connection:
        row = connection.execute(
            "SELECT * FROM jobs WHERE job_id = ?",
            (job_id,),
        ).fetchone()

        if row is None:
            canonical = dict(incoming)
            canonical_hash = json_hash(canonical)
            fields = _summary_fields(canonical)

            connection.execute(
                """
                INSERT INTO jobs (
                    job_id,
                    job_title,
                    company_name,
                    city,
                    salary,
                    source_url,
                    source_type,
                    schema_version,
                    canonical_json,
                    raw_extension_json,
                    content_hash,
                    raw_hash,
                    first_seen_at,
                    updated_at,
                    revision
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """,
                (
                    job_id,
                    fields["job_title"],
                    fields["company_name"],
                    fields["city"],
                    fields["salary"],
                    fields["source_url"],
                    source_type,
                    fields["schema_version"],
                    json_dumps(canonical),
                    raw_json,
                    canonical_hash,
                    raw_hash,
                    now,
                    now,
                ),
            )

            return {
                "action": "inserted",
                "job_id": job_id,
                "revision": 1,
                "canonical": canonical,
            }

        existing = json.loads(row["canonical_json"])

        if raw_extension is not None:
            canonical, canonical_changed = (
                merge_extension_into_canonical(
                    existing,
                    incoming,
                )
            )
        else:
            canonical, canonical_changed = (
                merge_canonical_nonempty(
                    existing,
                    incoming,
                )
            )

        canonical_hash = json_hash(canonical)
        raw_changed = (
            raw_extension is not None
            and raw_hash != row["raw_hash"]
        )
        changed = (
            canonical_changed
            or canonical_hash != row["content_hash"]
            or raw_changed
        )

        if not changed:
            return {
                "action": "unchanged",
                "job_id": job_id,
                "revision": int(row["revision"]),
                "canonical": existing,
            }

        revision = int(row["revision"]) + 1
        fields = _summary_fields(canonical)
        effective_raw_json = (
            raw_json
            if raw_extension is not None
            else row["raw_extension_json"]
        )
        effective_raw_hash = (
            raw_hash
            if raw_extension is not None
            else row["raw_hash"]
        )
        effective_source_type = (
            source_type
            if raw_extension is not None
            else row["source_type"] or source_type
        )

        connection.execute(
            """
            UPDATE jobs
            SET job_title = ?,
                company_name = ?,
                city = ?,
                salary = ?,
                source_url = ?,
                source_type = ?,
                schema_version = ?,
                canonical_json = ?,
                raw_extension_json = ?,
                content_hash = ?,
                raw_hash = ?,
                updated_at = ?,
                revision = ?
            WHERE job_id = ?
            """,
            (
                fields["job_title"],
                fields["company_name"],
                fields["city"],
                fields["salary"],
                fields["source_url"],
                effective_source_type,
                fields["schema_version"],
                json_dumps(canonical),
                effective_raw_json,
                canonical_hash,
                effective_raw_hash,
                now,
                revision,
                job_id,
            ),
        )

        return {
            "action": "updated",
            "job_id": job_id,
            "revision": revision,
            "canonical": canonical,
        }


def upsert_extension_job(
    payload: dict[str, Any],
    *,
    db_path: Path = DB_PATH,
) -> dict[str, Any]:
    canonical = convert_payload(payload)
    return upsert_canonical_job(
        canonical,
        source_type="browser_extension",
        raw_extension=payload,
        db_path=db_path,
    )


def import_canonical_jsonl(
    path: Path,
    *,
    db_path: Path = DB_PATH,
) -> dict[str, int]:
    initialize_database(db_path)

    if not path.exists():
        raise FileNotFoundError(f"找不到规范岗位 JSONL：{path}")

    stats = {
        "input": 0,
        "inserted": 0,
        "updated": 0,
        "unchanged": 0,
    }

    with path.open("r", encoding="utf-8-sig") as file:
        for line_number, line in enumerate(file, start=1):
            stripped = line.strip()
            if not stripped:
                continue

            stats["input"] += 1

            try:
                record = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise RuntimeError(
                    f"{path} 第 {line_number} 行不是有效 JSON：{exc}"
                ) from exc

            if not isinstance(record, dict):
                raise RuntimeError(
                    f"{path} 第 {line_number} 行必须是 JSON 对象。"
                )

            result = upsert_canonical_job(
                record,
                source_type=str(
                    record.get("collector")
                    or record.get("source_sheet")
                    or "legacy_jsonl"
                ),
                db_path=db_path,
            )
            stats[result["action"]] += 1

    return stats


def import_extension_jsonl(
    path: Path,
    *,
    db_path: Path = DB_PATH,
) -> dict[str, Any]:
    initialize_database(db_path)

    if not path.exists():
        raise FileNotFoundError(f"找不到扩展 JSONL：{path}")

    from .importer_adapter import validate_payload

    stats: dict[str, Any] = {
        "input": 0,
        "inserted": 0,
        "updated": 0,
        "unchanged": 0,
        "issues": [],
    }

    latest_by_job_id: dict[str, dict[str, Any]] = {}

    with path.open("r", encoding="utf-8-sig") as file:
        for line_number, line in enumerate(file, start=1):
            stripped = line.strip()
            if not stripped:
                continue

            stats["input"] += 1
            try:
                payload = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise RuntimeError(
                    f"{path} 第 {line_number} 行不是有效 JSON：{exc}"
                ) from exc

            if not isinstance(payload, dict):
                raise RuntimeError(
                    f"{path} 第 {line_number} 行必须是 JSON 对象。"
                )

            issues = validate_payload(payload)
            if issues:
                stats["issues"].extend(issues)
                continue

            job_id = str(payload.get("jobId") or "").strip()
            if job_id:
                latest_by_job_id[job_id] = payload

    for payload in latest_by_job_id.values():
        result = upsert_extension_job(
            payload,
            db_path=db_path,
        )
        stats[result["action"]] += 1

    stats["unique"] = len(latest_by_job_id)
    return stats


def count_jobs(*, db_path: Path = DB_PATH) -> int:
    initialize_database(db_path)
    with connect(db_path) as connection:
        row = connection.execute(
            "SELECT COUNT(*) AS count FROM jobs"
        ).fetchone()
    return int(row["count"])


def list_job_summaries(
    *,
    limit: int = 100,
    offset: int = 0,
    db_path: Path = DB_PATH,
) -> list[dict[str, Any]]:
    initialize_database(db_path)
    safe_limit = max(1, min(limit, 500))
    safe_offset = max(0, offset)

    with connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT
                job_id,
                job_title,
                company_name,
                city,
                salary,
                source_url,
                source_type,
                schema_version,
                first_seen_at,
                updated_at,
                revision
            FROM jobs
            ORDER BY rowid
            LIMIT ? OFFSET ?
            """,
            (safe_limit, safe_offset),
        ).fetchall()

    return [dict(row) for row in rows]


def get_job_record(
    job_id: str,
    *,
    db_path: Path = DB_PATH,
) -> dict[str, Any] | None:
    initialize_database(db_path)

    with connect(db_path) as connection:
        row = connection.execute(
            "SELECT * FROM jobs WHERE job_id = ?",
            (job_id,),
        ).fetchone()

    if row is None:
        return None

    result = dict(row)
    result["canonical"] = json.loads(result.pop("canonical_json"))
    raw_json = result.pop("raw_extension_json")
    result["raw_extension"] = (
        json.loads(raw_json)
        if raw_json
        else None
    )
    return result


def iter_canonical_jobs(
    *,
    db_path: Path = DB_PATH,
) -> Iterable[dict[str, Any]]:
    initialize_database(db_path)

    with connect(db_path) as connection:
        management_exists = connection.execute(
            """
            SELECT 1
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'job_management'
            """
        ).fetchone()

        if management_exists:
            rows = connection.execute(
                """
                SELECT j.canonical_json
                FROM jobs AS j
                LEFT JOIN job_management AS m
                  ON m.job_id = j.job_id
                WHERE COALESCE(
                    m.quality_override,
                    'auto'
                ) != 'exclude'
                ORDER BY j.rowid
                """
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT canonical_json
                FROM jobs
                ORDER BY rowid
                """
            ).fetchall()

    for row in rows:
        yield json.loads(row["canonical_json"])




def write_jsonl_atomic(
    path: Path,
    records: Iterable[dict[str, Any]],
) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f"{path.name}.tmp")
    count = 0

    with temporary_path.open(
        "w",
        encoding="utf-8",
        newline="\n",
    ) as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False))
            file.write("\n")
            count += 1

    temporary_path.replace(path)
    return count


def export_database_to_target(
    *,
    db_path: Path = DB_PATH,
    target_path: Path = TARGET_JSONL,
) -> dict[str, Any]:
    initialize_database(db_path)
    ensure_runtime_directories()

    backup_path: Path | None = None
    if target_path.exists():
        timestamp = datetime.now().astimezone().strftime(
            "%Y%m%d-%H%M%S"
        )
        backup_path = (
            PIPELINE_BACKUP_DIR
            / f"jobs_before_db_export_{timestamp}.jsonl"
        )
        shutil.copy2(target_path, backup_path)

    count = write_jsonl_atomic(
        target_path,
        iter_canonical_jobs(db_path=db_path),
    )

    return {
        "count": count,
        "target_path": str(target_path),
        "backup_path": str(backup_path) if backup_path else "",
    }


def create_pipeline_run(
    *,
    db_path: Path = DB_PATH,
) -> int:
    initialize_database(db_path)

    with connect(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO pipeline_runs (
                status,
                requested_at
            ) VALUES ('queued', ?)
            """,
            (utc_now(),),
        )
        return int(cursor.lastrowid)


def update_pipeline_run(
    run_id: int,
    *,
    db_path: Path = DB_PATH,
    **fields: Any,
) -> None:
    initialize_database(db_path)

    allowed = {
        "status",
        "started_at",
        "finished_at",
        "input_count",
        "completed_steps",
        "current_step",
        "return_code",
        "dashboard_path",
        "log_path",
        "error_message",
    }
    updates = {
        key: value
        for key, value in fields.items()
        if key in allowed
    }

    if not updates:
        return

    assignments = ", ".join(
        f"{key} = ?" for key in updates
    )
    values = list(updates.values()) + [run_id]

    with connect(db_path) as connection:
        connection.execute(
            f"UPDATE pipeline_runs SET {assignments} WHERE run_id = ?",
            values,
        )


def latest_pipeline_run(
    *,
    db_path: Path = DB_PATH,
) -> dict[str, Any] | None:
    initialize_database(db_path)

    with connect(db_path) as connection:
        row = connection.execute(
            """
            SELECT *
            FROM pipeline_runs
            ORDER BY run_id DESC
            LIMIT 1
            """
        ).fetchone()

    return dict(row) if row else None


def active_pipeline_run(
    *,
    db_path: Path = DB_PATH,
) -> dict[str, Any] | None:
    initialize_database(db_path)

    placeholders = ", ".join("?" for _ in ACTIVE_PIPELINE_STATUSES)
    with connect(db_path) as connection:
        row = connection.execute(
            f"""
            SELECT *
            FROM pipeline_runs
            WHERE status IN ({placeholders})
            ORDER BY run_id DESC
            LIMIT 1
            """,
            ACTIVE_PIPELINE_STATUSES,
        ).fetchone()

    return dict(row) if row else None


# PHASE_7B2_EXCLUDE_EXPORT
