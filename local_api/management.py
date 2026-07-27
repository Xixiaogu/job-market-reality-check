from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Iterable

from .config import DB_PATH
from .database import connect, get_job_record, initialize_database, utc_now


USER_STATUSES = (
    "to_review",
    "interested",
    "preparing",
    "applied",
    "written_test",
    "interview",
    "offer",
    "rejected",
    "abandoned",
)

LISTING_STATUSES = (
    "unknown",
    "active",
    "suspected_inactive",
    "closed",
)

QUALITY_OVERRIDES = (
    "auto",
    "include",
    "review",
    "exclude",
)

ANALYSIS_AFFECTING_FIELDS = {
    "quality_override",
    "category_manual",
}

PATCHABLE_FIELDS = {
    "user_status",
    "listing_status",
    "quality_override",
    "category_manual",
    "notes",
    "archived",
}


def initialize_management_schema(
    db_path: Path = DB_PATH,
) -> dict[str, int]:
    initialize_database(db_path)
    now = utc_now()

    with connect(db_path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS job_management (
                job_id TEXT PRIMARY KEY,
                user_status TEXT NOT NULL DEFAULT 'to_review',
                listing_status TEXT NOT NULL DEFAULT 'unknown',
                quality_override TEXT NOT NULL DEFAULT 'auto',
                category_manual TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT '',
                archived_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (job_id)
                    REFERENCES jobs(job_id)
                    ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_job_management_user_status
            ON job_management(user_status);

            CREATE INDEX IF NOT EXISTS idx_job_management_listing_status
            ON job_management(listing_status);

            CREATE INDEX IF NOT EXISTS idx_job_management_quality
            ON job_management(quality_override);

            CREATE INDEX IF NOT EXISTS idx_job_management_archived
            ON job_management(archived_at);

            CREATE TABLE IF NOT EXISTS job_status_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL,
                field_name TEXT NOT NULL,
                old_value TEXT,
                new_value TEXT,
                changed_at TEXT NOT NULL,
                FOREIGN KEY (job_id)
                    REFERENCES jobs(job_id)
                    ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_job_status_events_job
            ON job_status_events(job_id, event_id DESC);

            CREATE INDEX IF NOT EXISTS idx_job_status_events_changed
            ON job_status_events(changed_at DESC);
            """
        )

        before = connection.execute(
            "SELECT COUNT(*) AS count FROM job_management"
        ).fetchone()["count"]

        connection.execute(
            """
            INSERT OR IGNORE INTO job_management (
                job_id,
                user_status,
                listing_status,
                quality_override,
                category_manual,
                notes,
                archived_at,
                created_at,
                updated_at
            )
            SELECT
                job_id,
                'to_review',
                'unknown',
                'auto',
                '',
                '',
                NULL,
                ?,
                ?
            FROM jobs
            """,
            (now, now),
        )

        after = connection.execute(
            "SELECT COUNT(*) AS count FROM job_management"
        ).fetchone()["count"]

        job_count = connection.execute(
            "SELECT COUNT(*) AS count FROM jobs"
        ).fetchone()["count"]

    return {
        "job_count": int(job_count),
        "management_count": int(after),
        "backfilled": int(after) - int(before),
    }


def _validate_enum(
    field: str,
    value: Any,
    allowed: tuple[str, ...],
) -> str:
    normalized = str(value or "").strip()
    if normalized not in allowed:
        choices = ", ".join(allowed)
        raise ValueError(f"{field} 必须是以下值之一：{choices}")
    return normalized


def normalize_management_patch(
    patch: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(patch, dict):
        raise ValueError("management patch 必须是 JSON 对象。")

    unknown = sorted(set(patch) - PATCHABLE_FIELDS)
    if unknown:
        raise ValueError("不支持的管理字段：" + ", ".join(unknown))

    normalized: dict[str, Any] = {}

    if "user_status" in patch:
        normalized["user_status"] = _validate_enum(
            "user_status",
            patch["user_status"],
            USER_STATUSES,
        )

    if "listing_status" in patch:
        normalized["listing_status"] = _validate_enum(
            "listing_status",
            patch["listing_status"],
            LISTING_STATUSES,
        )

    if "quality_override" in patch:
        normalized["quality_override"] = _validate_enum(
            "quality_override",
            patch["quality_override"],
            QUALITY_OVERRIDES,
        )

    if "category_manual" in patch:
        category = str(patch.get("category_manual") or "").strip()
        if len(category) > 100:
            raise ValueError("category_manual 不能超过100个字符。")
        normalized["category_manual"] = category

    if "notes" in patch:
        notes = str(patch.get("notes") or "").strip()
        if len(notes) > 4000:
            raise ValueError("notes 不能超过4000个字符。")
        normalized["notes"] = notes

    if "archived" in patch:
        archived = patch["archived"]
        if not isinstance(archived, bool):
            raise ValueError("archived 必须是布尔值。")
        normalized["archived"] = archived

    if not normalized:
        raise ValueError("没有可更新的管理字段。")

    return normalized


def _ensure_job_exists(
    connection: sqlite3.Connection,
    job_id: str,
) -> None:
    row = connection.execute(
        "SELECT 1 FROM jobs WHERE job_id = ?",
        (job_id,),
    ).fetchone()
    if row is None:
        raise KeyError(f"岗位不存在：{job_id}")


def _ensure_management_row(
    connection: sqlite3.Connection,
    job_id: str,
) -> None:
    now = utc_now()
    connection.execute(
        """
        INSERT OR IGNORE INTO job_management (
            job_id,
            user_status,
            listing_status,
            quality_override,
            category_manual,
            notes,
            archived_at,
            created_at,
            updated_at
        ) VALUES (?, 'to_review', 'unknown', 'auto', '', '', NULL, ?, ?)
        """,
        (job_id, now, now),
    )


def _row_to_management(
    row: sqlite3.Row,
) -> dict[str, Any]:
    result = dict(row)
    result["archived"] = bool(result.get("archived_at"))
    return result


def get_management(
    job_id: str,
    *,
    db_path: Path = DB_PATH,
) -> dict[str, Any] | None:
    initialize_management_schema(db_path)

    with connect(db_path) as connection:
        row = connection.execute(
            "SELECT * FROM job_management WHERE job_id = ?",
            (job_id,),
        ).fetchone()

    return _row_to_management(row) if row else None


def _apply_patch_in_connection(
    connection: sqlite3.Connection,
    job_id: str,
    patch: dict[str, Any],
) -> dict[str, Any]:
    _ensure_job_exists(connection, job_id)
    _ensure_management_row(connection, job_id)

    old_row = connection.execute(
        "SELECT * FROM job_management WHERE job_id = ?",
        (job_id,),
    ).fetchone()

    if old_row is None:
        raise RuntimeError("岗位管理记录初始化失败。")

    old = dict(old_row)
    now = utc_now()
    updates: dict[str, Any] = {}
    event_values: list[tuple[str, str | None, str | None]] = []

    for field, value in patch.items():
        if field == "archived":
            new_value = now if value else None
            old_value = old.get("archived_at")
            if bool(old_value) == value:
                continue
            updates["archived_at"] = new_value
            event_values.append(
                (
                    "archived_at",
                    str(old_value) if old_value else None,
                    str(new_value) if new_value else None,
                )
            )
            continue

        old_value = old.get(field)
        if old_value == value:
            continue

        updates[field] = value
        event_values.append(
            (
                field,
                str(old_value) if old_value is not None else None,
                str(value) if value is not None else None,
            )
        )

    if updates:
        updates["updated_at"] = now
        assignments = ", ".join(f"{field} = ?" for field in updates)
        values = list(updates.values()) + [job_id]
        connection.execute(
            f"""
            UPDATE job_management
            SET {assignments}
            WHERE job_id = ?
            """,
            values,
        )

        connection.executemany(
            """
            INSERT INTO job_status_events (
                job_id,
                field_name,
                old_value,
                new_value,
                changed_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            [
                (job_id, field_name, old_value, new_value, now)
                for field_name, old_value, new_value in event_values
            ],
        )

    current_row = connection.execute(
        "SELECT * FROM job_management WHERE job_id = ?",
        (job_id,),
    ).fetchone()

    changed_fields = [field_name for field_name, _, _ in event_values]
    analysis_required = any(
        field in ANALYSIS_AFFECTING_FIELDS
        for field in changed_fields
    )

    return {
        "job_id": job_id,
        "changed": bool(changed_fields),
        "changed_fields": changed_fields,
        "analysis_required": analysis_required,
        "management": _row_to_management(current_row),
    }


def patch_management(
    job_id: str,
    patch: dict[str, Any],
    *,
    db_path: Path = DB_PATH,
) -> dict[str, Any]:
    initialize_management_schema(db_path)
    normalized = normalize_management_patch(patch)

    with connect(db_path) as connection:
        return _apply_patch_in_connection(connection, job_id, normalized)


def bulk_patch_management(
    job_ids: Iterable[str],
    patch: dict[str, Any],
    *,
    db_path: Path = DB_PATH,
) -> dict[str, Any]:
    initialize_management_schema(db_path)
    normalized = normalize_management_patch(patch)

    unique_job_ids = list(
        dict.fromkeys(
            str(job_id or "").strip()
            for job_id in job_ids
            if str(job_id or "").strip()
        )
    )

    if not unique_job_ids:
        raise ValueError("job_ids 不能为空。")

    if len(unique_job_ids) > 500:
        raise ValueError("单次最多批量管理500条岗位。")

    results: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []

    with connect(db_path) as connection:
        for job_id in unique_job_ids:
            try:
                results.append(
                    _apply_patch_in_connection(
                        connection,
                        job_id,
                        normalized,
                    )
                )
            except KeyError as exc:
                errors.append(
                    {
                        "job_id": job_id,
                        "error": str(exc),
                    }
                )

    changed_count = sum(1 for item in results if item["changed"])
    analysis_required = any(
        item["analysis_required"] for item in results
    )

    return {
        "input": len(unique_job_ids),
        "succeeded": len(results),
        "failed": len(errors),
        "changed": changed_count,
        "analysis_required": analysis_required,
        "results": results,
        "errors": errors,
    }


def get_management_history(
    job_id: str,
    *,
    limit: int = 100,
    db_path: Path = DB_PATH,
) -> list[dict[str, Any]]:
    initialize_management_schema(db_path)
    safe_limit = max(1, min(int(limit), 500))

    with connect(db_path) as connection:
        _ensure_job_exists(connection, job_id)
        rows = connection.execute(
            """
            SELECT
                event_id,
                job_id,
                field_name,
                old_value,
                new_value,
                changed_at
            FROM job_status_events
            WHERE job_id = ?
            ORDER BY event_id DESC
            LIMIT ?
            """,
            (job_id, safe_limit),
        ).fetchall()

    return [dict(row) for row in rows]


def _validate_optional_filter(
    name: str,
    value: str | None,
    allowed: tuple[str, ...],
) -> str | None:
    if value is None or value == "":
        return None
    return _validate_enum(name, value, allowed)


def list_managed_jobs(
    *,
    limit: int = 100,
    offset: int = 0,
    user_status: str | None = None,
    listing_status: str | None = None,
    quality_override: str | None = None,
    archived: bool | None = None,
    category_manual: str | None = None,
    city: str | None = None,
    keyword: str | None = None,
    db_path: Path = DB_PATH,
) -> dict[str, Any]:
    initialize_management_schema(db_path)

    safe_limit = max(1, min(int(limit), 500))
    safe_offset = max(0, int(offset))
    user_status = _validate_optional_filter(
        "user_status", user_status, USER_STATUSES
    )
    listing_status = _validate_optional_filter(
        "listing_status", listing_status, LISTING_STATUSES
    )
    quality_override = _validate_optional_filter(
        "quality_override", quality_override, QUALITY_OVERRIDES
    )

    conditions: list[str] = []
    parameters: list[Any] = []

    if user_status:
        conditions.append("m.user_status = ?")
        parameters.append(user_status)

    if listing_status:
        conditions.append("m.listing_status = ?")
        parameters.append(listing_status)

    if quality_override:
        conditions.append("m.quality_override = ?")
        parameters.append(quality_override)

    if archived is True:
        conditions.append("m.archived_at IS NOT NULL")
    elif archived is False:
        conditions.append("m.archived_at IS NULL")

    if category_manual:
        conditions.append("m.category_manual = ?")
        parameters.append(str(category_manual).strip())

    if city:
        conditions.append("j.city = ?")
        parameters.append(str(city).strip())

    if keyword:
        pattern = f"%{str(keyword).strip()}%"
        conditions.append(
            """
            (
                j.job_title LIKE ?
                OR j.company_name LIKE ?
                OR j.city LIKE ?
                OR m.category_manual LIKE ?
                OR m.notes LIKE ?
            )
            """
        )
        parameters.extend([pattern] * 5)

    where_sql = "WHERE " + " AND ".join(conditions) if conditions else ""

    base_sql = f"""
        FROM jobs AS j
        JOIN job_management AS m
          ON m.job_id = j.job_id
        {where_sql}
    """

    with connect(db_path) as connection:
        total_row = connection.execute(
            "SELECT COUNT(*) AS count " + base_sql,
            parameters,
        ).fetchone()

        rows = connection.execute(
            f"""
            SELECT
                j.job_id,
                j.job_title,
                j.company_name,
                j.city,
                j.salary,
                j.source_url,
                j.source_type,
                j.schema_version,
                j.first_seen_at,
                j.updated_at AS job_updated_at,
                j.revision,
                m.user_status,
                m.listing_status,
                m.quality_override,
                m.category_manual,
                m.notes,
                m.archived_at,
                m.created_at AS management_created_at,
                m.updated_at AS management_updated_at
            {base_sql}
            ORDER BY
                CASE WHEN m.archived_at IS NULL THEN 0 ELSE 1 END,
                j.updated_at DESC,
                j.rowid DESC
            LIMIT ? OFFSET ?
            """,
            parameters + [safe_limit, safe_offset],
        ).fetchall()

    items = []
    for row in rows:
        item = dict(row)
        item["archived"] = bool(item.get("archived_at"))
        items.append(item)

    return {
        "total": int(total_row["count"]),
        "limit": safe_limit,
        "offset": safe_offset,
        "items": items,
    }


def get_managed_job_record(
    job_id: str,
    *,
    db_path: Path = DB_PATH,
) -> dict[str, Any] | None:
    initialize_management_schema(db_path)
    record = get_job_record(job_id, db_path=db_path)
    if record is None:
        return None

    record["management"] = get_management(job_id, db_path=db_path)
    return record


def management_counts(
    *,
    db_path: Path = DB_PATH,
) -> dict[str, Any]:
    initialize_management_schema(db_path)

    with connect(db_path) as connection:
        total = connection.execute(
            "SELECT COUNT(*) AS count FROM job_management"
        ).fetchone()["count"]

        archived = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM job_management
            WHERE archived_at IS NOT NULL
            """
        ).fetchone()["count"]

        status_rows = connection.execute(
            """
            SELECT user_status, COUNT(*) AS count
            FROM job_management
            GROUP BY user_status
            ORDER BY user_status
            """
        ).fetchall()

        quality_rows = connection.execute(
            """
            SELECT quality_override, COUNT(*) AS count
            FROM job_management
            GROUP BY quality_override
            ORDER BY quality_override
            """
        ).fetchall()

    return {
        "total": int(total),
        "active": int(total) - int(archived),
        "archived": int(archived),
        "by_user_status": {
            row["user_status"]: int(row["count"])
            for row in status_rows
        },
        "by_quality_override": {
            row["quality_override"]: int(row["count"])
            for row in quality_rows
        },
    }


def management_options() -> dict[str, Any]:
    return {
        "user_statuses": list(USER_STATUSES),
        "listing_statuses": list(LISTING_STATUSES),
        "quality_overrides": list(QUALITY_OVERRIDES),
        "analysis_affecting_fields": sorted(
            ANALYSIS_AFFECTING_FIELDS
        ),
    }
