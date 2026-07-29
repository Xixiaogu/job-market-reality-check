from __future__ import annotations

import ast
import json
import re
import sqlite3
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

from .config import DB_PATH, PROJECT_ROOT
from .database import connect, initialize_database, utc_now


PROFICIENCY_LEVELS = (
    "aware",
    "basic",
    "proficient",
    "project_ready",
)

PROJECT_TYPES = (
    "personal",
    "research",
    "course",
    "competition",
    "internship",
    "other",
)

PROJECT_STATUSES = (
    "idea",
    "in_progress",
    "completed",
    "maintained",
)

EVIDENCE_STRENGTHS = (
    "supporting",
    "strong",
)

INTEREST_LEVELS = (
    "very_high",
    "high",
    "acceptable",
    "low",
    "none",
)

CONSTRAINT_LEVELS = (
    "hard",
    "important",
    "preference",
)

TARGET_JOB_TYPES = (
    "summer_internship",
    "daily_internship",
    "full_time",
    "research_assistant",
    "part_time",
)

PROFILE_FIELDS = {
    "education",
    "major",
    "graduation_year",
    "max_days_per_week",
    "min_internship_months",
    "max_internship_months",
    "minimum_daily_salary",
    "minimum_monthly_salary",
    "accepts_remote",
    "accepts_relocation",
    "available_from",
    "notes",
    "target_job_types",
}

SKILL_ALIASES = {
    "ml": "机器学习",
    "machine learning": "机器学习",
    "llm": "大模型/LLM",
    "大语言模型": "大模型/LLM",
    "大模型": "大模型/LLM",
    "agent": "AI Agent",
    "ai agent": "AI Agent",
    "智能体": "AI Agent",
    "powerbi": "Power BI",
    "sklearn": "Scikit-learn",
    "scikit learn": "Scikit-learn",
    "pytorch": "PyTorch",
    "numpy": "NumPy",
    "pandas": "Pandas",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "fastapi": "FastAPI",
    "rag": "RAG",
    "sql": "SQL",
    "python": "Python",
}

FALLBACK_SKILL_DEFS: list[tuple[str, str, list[str]]] = [
    ("Python", "技术栈", [r"(?<![a-z0-9])python(?![a-z0-9])"]),
    ("SQL", "技术栈", [r"(?<![a-z0-9])sql(?![a-z0-9])"]),
    ("Pandas", "技术栈", [r"(?<![a-z0-9])pandas(?![a-z0-9])"]),
    ("PyTorch", "技术栈", [r"(?<![a-z0-9])pytorch(?![a-z0-9])"]),
    ("Excel", "技术栈", [r"(?<![a-z0-9])excel(?![a-z0-9])"]),
    ("Power BI", "技术栈", [r"power\s*bi", r"powerbi"]),
    ("Docker", "技术栈", [r"(?<![a-z0-9])docker(?![a-z0-9])"]),
    ("Git", "技术栈", [r"(?<![a-z0-9])git(?![a-z0-9])"]),
    ("FastAPI", "技术栈", [r"(?<![a-z0-9])fastapi(?![a-z0-9])"]),
    ("机器学习", "AI与统计方法", [r"机器学习", r"machine\s*learning"]),
    ("深度学习", "AI与统计方法", [r"深度学习", r"deep\s*learning"]),
    ("大模型/LLM", "AI与统计方法", [r"大模型", r"大语言模型", r"(?<![a-z0-9])llm(?![a-z0-9])"]),
    ("AI Agent", "AI与统计方法", [r"ai\s*agent", r"智能体", r"agent开发"]),
    ("RAG", "AI与统计方法", [r"(?<![a-z0-9])rag(?![a-z0-9])", r"检索增强生成"]),
    ("统计分析", "AI与统计方法", [r"统计分析", r"统计建模"]),
    ("数据分析", "工作任务", [r"数据分析"]),
    ("数据可视化", "工作任务", [r"数据可视化", r"可视化分析"]),
    ("需求分析", "产品与项目", [r"需求分析"]),
    ("API/接口", "技术栈", [r"(?<![a-z0-9])api(?![a-z0-9])", r"接口开发", r"接口设计"]),
]

COLD_START_DIRECTIONS: tuple[tuple[str, str], ...] = (
    ("数据分析与BI", "通用起始方向"),
    ("AI应用开发", "通用起始方向"),
    ("机器学习应用", "通用起始方向"),
    ("数据工程", "通用起始方向"),
    ("研究助理 / RA", "通用起始方向"),
)

DIRECTION_STARTER_SKILLS: dict[str, tuple[str, ...]] = {
    "数据分析": ("Python", "SQL", "Excel", "Pandas", "统计分析", "数据可视化"),
    "商业分析": ("SQL", "Excel", "数据分析", "数据可视化", "Power BI"),
    "BI": ("SQL", "Excel", "Power BI", "数据分析", "数据可视化"),
    "AI应用": ("Python", "FastAPI", "大模型/LLM", "RAG", "AI Agent", "API/接口"),
    "大模型": ("Python", "大模型/LLM", "RAG", "AI Agent", "FastAPI"),
    "机器学习": ("Python", "机器学习", "Pandas", "PyTorch", "统计分析"),
    "数据工程": ("Python", "SQL", "Git", "Docker", "API/接口"),
    "研究助理": ("Python", "统计分析", "数据分析", "机器学习", "Git"),
    "RA": ("Python", "统计分析", "数据分析", "机器学习", "Git"),
}

GENERAL_STARTER_SKILLS: tuple[str, ...] = (
    "Python",
    "SQL",
    "Excel",
    "数据分析",
    "Git",
)

TARGET_TYPE_DIRECTION_STARTERS: dict[str, tuple[str, ...]] = {
    "summer_internship": ("数据分析与BI", "AI应用开发", "机器学习应用"),
    "daily_internship": ("数据分析与BI", "AI应用开发", "机器学习应用"),
    "full_time": ("数据分析与BI", "AI应用开发", "数据工程"),
    "research_assistant": ("研究助理 / RA", "机器学习应用", "数据分析与BI"),
    "part_time": ("数据分析与BI", "AI应用开发"),
}



# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------


def initialize_profile_schema(db_path: Path = DB_PATH) -> dict[str, int]:
    initialize_database(db_path)
    now = utc_now()

    with connect(db_path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS user_profile (
                profile_id INTEGER PRIMARY KEY CHECK (profile_id = 1),
                education TEXT NOT NULL DEFAULT '',
                major TEXT NOT NULL DEFAULT '',
                graduation_year INTEGER,
                max_days_per_week INTEGER,
                min_internship_months INTEGER,
                max_internship_months INTEGER,
                minimum_daily_salary INTEGER,
                minimum_monthly_salary INTEGER,
                accepts_remote INTEGER NOT NULL DEFAULT 0,
                accepts_relocation INTEGER NOT NULL DEFAULT 0,
                available_from TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT '',
                target_job_types TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS user_location_preferences (
                location_id INTEGER PRIMARY KEY AUTOINCREMENT,
                city TEXT NOT NULL COLLATE NOCASE,
                constraint_level TEXT NOT NULL DEFAULT 'preference',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE UNIQUE INDEX IF NOT EXISTS idx_user_location_unique
            ON user_location_preferences(city COLLATE NOCASE);

            CREATE TABLE IF NOT EXISTS user_skills (
                skill_id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_name TEXT NOT NULL COLLATE NOCASE,
                proficiency_level TEXT NOT NULL DEFAULT 'basic',
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE UNIQUE INDEX IF NOT EXISTS idx_user_skill_unique
            ON user_skills(skill_name COLLATE NOCASE);

            CREATE INDEX IF NOT EXISTS idx_user_skill_level
            ON user_skills(proficiency_level);

            CREATE TABLE IF NOT EXISTS user_projects (
                project_id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT NOT NULL,
                project_type TEXT NOT NULL DEFAULT 'personal',
                project_status TEXT NOT NULL DEFAULT 'in_progress',
                description TEXT NOT NULL DEFAULT '',
                achievements TEXT NOT NULL DEFAULT '',
                github_url TEXT NOT NULL DEFAULT '',
                demo_url TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_user_projects_status
            ON user_projects(project_status);

            CREATE TABLE IF NOT EXISTS project_skill_evidence (
                evidence_id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                skill_id INTEGER NOT NULL,
                evidence_text TEXT NOT NULL DEFAULT '',
                evidence_strength TEXT NOT NULL DEFAULT 'supporting',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (project_id)
                    REFERENCES user_projects(project_id)
                    ON DELETE CASCADE,
                FOREIGN KEY (skill_id)
                    REFERENCES user_skills(skill_id)
                    ON DELETE CASCADE,
                UNIQUE(project_id, skill_id)
            );

            CREATE INDEX IF NOT EXISTS idx_project_evidence_project
            ON project_skill_evidence(project_id);

            CREATE INDEX IF NOT EXISTS idx_project_evidence_skill
            ON project_skill_evidence(skill_id);

            CREATE TABLE IF NOT EXISTS user_job_preferences (
                preference_id INTEGER PRIMARY KEY AUTOINCREMENT,
                direction TEXT NOT NULL COLLATE NOCASE,
                interest_level TEXT NOT NULL DEFAULT 'acceptable',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE UNIQUE INDEX IF NOT EXISTS idx_user_direction_unique
            ON user_job_preferences(direction COLLATE NOCASE);
            """
        )

        profile_columns = {
            str(row["name"])
            for row in connection.execute("PRAGMA table_info(user_profile)").fetchall()
        }
        if "target_job_types" not in profile_columns:
            connection.execute(
                "ALTER TABLE user_profile "
                "ADD COLUMN target_job_types TEXT NOT NULL DEFAULT '[]'"
            )

        connection.execute(
            """
            INSERT OR IGNORE INTO user_profile (
                profile_id,
                education,
                major,
                graduation_year,
                max_days_per_week,
                min_internship_months,
                max_internship_months,
                minimum_daily_salary,
                minimum_monthly_salary,
                accepts_remote,
                accepts_relocation,
                available_from,
                notes,
                created_at,
                updated_at
            ) VALUES (1, '', '', NULL, NULL, NULL, NULL, NULL, NULL, 0, 0, '', '', ?, ?)
            """,
            (now, now),
        )

        skill_count = connection.execute(
            "SELECT COUNT(*) AS count FROM user_skills"
        ).fetchone()["count"]
        project_count = connection.execute(
            "SELECT COUNT(*) AS count FROM user_projects"
        ).fetchone()["count"]
        preference_count = connection.execute(
            "SELECT COUNT(*) AS count FROM user_job_preferences"
        ).fetchone()["count"]

    return {
        "profile_count": 1,
        "skill_count": int(skill_count),
        "project_count": int(project_count),
        "preference_count": int(preference_count),
    }


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def _string(value: Any, *, field: str, maximum: int, required: bool = False) -> str:
    text = str(value or "").strip()
    if required and not text:
        raise ValueError(f"{field} 不能为空。")
    if len(text) > maximum:
        raise ValueError(f"{field} 不能超过 {maximum} 个字符。")
    return text


def _optional_int(
    value: Any,
    *,
    field: str,
    minimum: int,
    maximum: int,
) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        raise ValueError(f"{field} 必须是整数。")
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} 必须是整数。") from exc
    if result < minimum or result > maximum:
        raise ValueError(f"{field} 必须在 {minimum} 到 {maximum} 之间。")
    return result


def _boolean(value: Any, *, field: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{field} 必须是布尔值。")
    return value


def _enum(value: Any, *, field: str, allowed: tuple[str, ...]) -> str:
    normalized = str(value or "").strip()
    if normalized not in allowed:
        raise ValueError(f"{field} 必须是以下值之一：{', '.join(allowed)}")
    return normalized


def normalize_skill_name(value: Any) -> str:
    name = _string(value, field="skill_name", maximum=100, required=True)
    compact = re.sub(r"\s+", " ", name).strip()
    alias = SKILL_ALIASES.get(compact.casefold())
    return alias or compact


def _row_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row is not None else None


def _profile_row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    result = dict(row)
    result["accepts_remote"] = bool(result["accepts_remote"])
    result["accepts_relocation"] = bool(result["accepts_relocation"])
    raw_job_types = result.get("target_job_types") or "[]"
    try:
        parsed_job_types = json.loads(raw_job_types)
    except (TypeError, json.JSONDecodeError):
        parsed_job_types = []
    if not isinstance(parsed_job_types, list):
        parsed_job_types = []
    result["target_job_types"] = [
        item for item in parsed_job_types if item in TARGET_JOB_TYPES
    ]
    return result


def _ensure_skill(connection: sqlite3.Connection, skill_id: int) -> None:
    row = connection.execute(
        "SELECT 1 FROM user_skills WHERE skill_id = ?",
        (skill_id,),
    ).fetchone()
    if row is None:
        raise KeyError(f"技能不存在：{skill_id}")


def _ensure_project(connection: sqlite3.Connection, project_id: int) -> None:
    row = connection.execute(
        "SELECT 1 FROM user_projects WHERE project_id = ?",
        (project_id,),
    ).fetchone()
    if row is None:
        raise KeyError(f"项目不存在：{project_id}")


# ---------------------------------------------------------------------------
# Profile, locations and directions
# ---------------------------------------------------------------------------


def get_profile(*, db_path: Path = DB_PATH) -> dict[str, Any]:
    initialize_profile_schema(db_path)
    with connect(db_path) as connection:
        row = connection.execute(
            "SELECT * FROM user_profile WHERE profile_id = 1"
        ).fetchone()
    if row is None:
        raise RuntimeError("个人档案初始化失败。")
    return _profile_row_to_dict(row)


def patch_profile(
    payload: dict[str, Any],
    *,
    db_path: Path = DB_PATH,
) -> dict[str, Any]:
    initialize_profile_schema(db_path)
    if not isinstance(payload, dict):
        raise ValueError("profile payload 必须是 JSON 对象。")

    unknown = sorted(set(payload) - PROFILE_FIELDS)
    if unknown:
        raise ValueError("不支持的个人档案字段：" + ", ".join(unknown))

    normalized: dict[str, Any] = {}

    if "education" in payload:
        normalized["education"] = _string(
            payload["education"], field="education", maximum=80
        )
    if "major" in payload:
        normalized["major"] = _string(
            payload["major"], field="major", maximum=120
        )
    if "graduation_year" in payload:
        normalized["graduation_year"] = _optional_int(
            payload["graduation_year"],
            field="graduation_year",
            minimum=2000,
            maximum=2100,
        )
    if "max_days_per_week" in payload:
        normalized["max_days_per_week"] = _optional_int(
            payload["max_days_per_week"],
            field="max_days_per_week",
            minimum=0,
            maximum=7,
        )
    if "min_internship_months" in payload:
        normalized["min_internship_months"] = _optional_int(
            payload["min_internship_months"],
            field="min_internship_months",
            minimum=0,
            maximum=36,
        )
    if "max_internship_months" in payload:
        normalized["max_internship_months"] = _optional_int(
            payload["max_internship_months"],
            field="max_internship_months",
            minimum=0,
            maximum=36,
        )
    if "minimum_daily_salary" in payload:
        normalized["minimum_daily_salary"] = _optional_int(
            payload["minimum_daily_salary"],
            field="minimum_daily_salary",
            minimum=0,
            maximum=100000,
        )
    if "minimum_monthly_salary" in payload:
        normalized["minimum_monthly_salary"] = _optional_int(
            payload["minimum_monthly_salary"],
            field="minimum_monthly_salary",
            minimum=0,
            maximum=1000000,
        )
    if "accepts_remote" in payload:
        normalized["accepts_remote"] = int(
            _boolean(payload["accepts_remote"], field="accepts_remote")
        )
    if "accepts_relocation" in payload:
        normalized["accepts_relocation"] = int(
            _boolean(payload["accepts_relocation"], field="accepts_relocation")
        )
    if "available_from" in payload:
        normalized["available_from"] = _string(
            payload["available_from"], field="available_from", maximum=40
        )
    if "notes" in payload:
        normalized["notes"] = _string(
            payload["notes"], field="notes", maximum=4000
        )
    if "target_job_types" in payload:
        job_types = payload["target_job_types"]
        if not isinstance(job_types, list):
            raise ValueError("target_job_types 必须是数组。")
        if len(job_types) > len(TARGET_JOB_TYPES):
            raise ValueError("求职类型数量超出允许范围。")
        normalized_job_types: list[str] = []
        for item in job_types:
            normalized_item = _enum(
                item,
                field="target_job_types",
                allowed=TARGET_JOB_TYPES,
            )
            if normalized_item not in normalized_job_types:
                normalized_job_types.append(normalized_item)
        normalized["target_job_types"] = json.dumps(
            normalized_job_types,
            ensure_ascii=False,
        )

    if not normalized:
        return {"changed": False, "profile": get_profile(db_path=db_path)}

    normalized["updated_at"] = utc_now()
    assignments = ", ".join(f"{field} = ?" for field in normalized)
    values = list(normalized.values())

    with connect(db_path) as connection:
        connection.execute(
            f"UPDATE user_profile SET {assignments} WHERE profile_id = 1",
            values,
        )

    return {"changed": True, "profile": get_profile(db_path=db_path)}


def list_locations(*, db_path: Path = DB_PATH) -> list[dict[str, Any]]:
    initialize_profile_schema(db_path)
    with connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT location_id, city, constraint_level, created_at, updated_at
            FROM user_location_preferences
            ORDER BY location_id
            """
        ).fetchall()
    return [dict(row) for row in rows]


def replace_locations(
    items: list[dict[str, Any]],
    *,
    db_path: Path = DB_PATH,
) -> list[dict[str, Any]]:
    initialize_profile_schema(db_path)
    if not isinstance(items, list):
        raise ValueError("cities 必须是数组。")
    if len(items) > 50:
        raise ValueError("城市偏好不能超过 50 个。")

    normalized: list[tuple[str, str]] = []
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("每个城市偏好都必须是 JSON 对象。")
        city = _string(item.get("city"), field="city", maximum=80, required=True)
        level = _enum(
            item.get("constraint_level", "preference"),
            field="constraint_level",
            allowed=CONSTRAINT_LEVELS,
        )
        key = city.casefold()
        if key in seen:
            continue
        seen.add(key)
        normalized.append((city, level))

    now = utc_now()
    with connect(db_path) as connection:
        connection.execute("DELETE FROM user_location_preferences")
        connection.executemany(
            """
            INSERT INTO user_location_preferences (
                city, constraint_level, created_at, updated_at
            ) VALUES (?, ?, ?, ?)
            """,
            [(city, level, now, now) for city, level in normalized],
        )
    return list_locations(db_path=db_path)


def list_preferences(*, db_path: Path = DB_PATH) -> list[dict[str, Any]]:
    initialize_profile_schema(db_path)
    with connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT preference_id, direction, interest_level, created_at, updated_at
            FROM user_job_preferences
            ORDER BY preference_id
            """
        ).fetchall()
    return [dict(row) for row in rows]


def replace_preferences(
    items: list[dict[str, Any]],
    *,
    db_path: Path = DB_PATH,
) -> list[dict[str, Any]]:
    initialize_profile_schema(db_path)
    if not isinstance(items, list):
        raise ValueError("directions 必须是数组。")
    if len(items) > 100:
        raise ValueError("岗位方向偏好不能超过 100 个。")

    normalized: list[tuple[str, str]] = []
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("每个方向偏好都必须是 JSON 对象。")
        direction = _string(
            item.get("direction"),
            field="direction",
            maximum=100,
            required=True,
        )
        interest = _enum(
            item.get("interest_level", "acceptable"),
            field="interest_level",
            allowed=INTEREST_LEVELS,
        )
        key = direction.casefold()
        if key in seen:
            continue
        seen.add(key)
        normalized.append((direction, interest))

    now = utc_now()
    with connect(db_path) as connection:
        connection.execute("DELETE FROM user_job_preferences")
        connection.executemany(
            """
            INSERT INTO user_job_preferences (
                direction, interest_level, created_at, updated_at
            ) VALUES (?, ?, ?, ?)
            """,
            [(direction, interest, now, now) for direction, interest in normalized],
        )
    return list_preferences(db_path=db_path)


# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------


def list_skills(*, db_path: Path = DB_PATH) -> list[dict[str, Any]]:
    initialize_profile_schema(db_path)
    with connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT
                s.skill_id,
                s.skill_name,
                s.proficiency_level,
                s.notes,
                s.created_at,
                s.updated_at,
                COUNT(e.evidence_id) AS evidence_count,
                GROUP_CONCAT(DISTINCT p.project_name) AS project_names
            FROM user_skills AS s
            LEFT JOIN project_skill_evidence AS e
              ON e.skill_id = s.skill_id
            LEFT JOIN user_projects AS p
              ON p.project_id = e.project_id
            GROUP BY s.skill_id
            ORDER BY s.skill_name COLLATE NOCASE
            """
        ).fetchall()

    result: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        names = item.pop("project_names") or ""
        item["projects"] = [name for name in names.split(",") if name]
        item["evidence_count"] = int(item["evidence_count"] or 0)
        result.append(item)
    return result


def create_skill(
    payload: dict[str, Any],
    *,
    db_path: Path = DB_PATH,
) -> dict[str, Any]:
    initialize_profile_schema(db_path)
    if not isinstance(payload, dict):
        raise ValueError("skill payload 必须是 JSON 对象。")

    name = normalize_skill_name(payload.get("skill_name"))
    level = _enum(
        payload.get("proficiency_level", "basic"),
        field="proficiency_level",
        allowed=PROFICIENCY_LEVELS,
    )
    notes = _string(payload.get("notes"), field="notes", maximum=2000)
    now = utc_now()

    with connect(db_path) as connection:
        try:
            cursor = connection.execute(
                """
                INSERT INTO user_skills (
                    skill_name, proficiency_level, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (name, level, notes, now, now),
            )
        except sqlite3.IntegrityError as exc:
            existing = connection.execute(
                """
                SELECT skill_id FROM user_skills
                WHERE skill_name = ? COLLATE NOCASE
                """,
                (name,),
            ).fetchone()
            if existing is None:
                raise
            raise ValueError(f"技能已存在：{name}") from exc
        skill_id = int(cursor.lastrowid)

    return get_skill(skill_id, db_path=db_path)


def get_skill(skill_id: int, *, db_path: Path = DB_PATH) -> dict[str, Any]:
    skills = list_skills(db_path=db_path)
    for skill in skills:
        if int(skill["skill_id"]) == int(skill_id):
            return skill
    raise KeyError(f"技能不存在：{skill_id}")


def patch_skill(
    skill_id: int,
    payload: dict[str, Any],
    *,
    db_path: Path = DB_PATH,
) -> dict[str, Any]:
    initialize_profile_schema(db_path)
    if not isinstance(payload, dict):
        raise ValueError("skill payload 必须是 JSON 对象。")

    allowed = {"skill_name", "proficiency_level", "notes"}
    unknown = sorted(set(payload) - allowed)
    if unknown:
        raise ValueError("不支持的技能字段：" + ", ".join(unknown))

    updates: dict[str, Any] = {}
    if "skill_name" in payload:
        updates["skill_name"] = normalize_skill_name(payload["skill_name"])
    if "proficiency_level" in payload:
        updates["proficiency_level"] = _enum(
            payload["proficiency_level"],
            field="proficiency_level",
            allowed=PROFICIENCY_LEVELS,
        )
    if "notes" in payload:
        updates["notes"] = _string(
            payload["notes"], field="notes", maximum=2000
        )

    with connect(db_path) as connection:
        _ensure_skill(connection, skill_id)
        if updates:
            updates["updated_at"] = utc_now()
            assignments = ", ".join(f"{field} = ?" for field in updates)
            try:
                connection.execute(
                    f"UPDATE user_skills SET {assignments} WHERE skill_id = ?",
                    list(updates.values()) + [skill_id],
                )
            except sqlite3.IntegrityError as exc:
                raise ValueError("技能名称与现有技能重复。") from exc

    return get_skill(skill_id, db_path=db_path)


def delete_skill(skill_id: int, *, db_path: Path = DB_PATH) -> dict[str, Any]:
    initialize_profile_schema(db_path)
    with connect(db_path) as connection:
        _ensure_skill(connection, skill_id)
        connection.execute("DELETE FROM user_skills WHERE skill_id = ?", (skill_id,))
    return {"deleted": True, "skill_id": int(skill_id)}


# ---------------------------------------------------------------------------
# Projects and evidence
# ---------------------------------------------------------------------------


def _normalize_evidence_items(
    connection: sqlite3.Connection,
    items: Any,
) -> list[dict[str, Any]]:
    if items is None:
        return []
    if not isinstance(items, list):
        raise ValueError("skills 必须是数组。")
    if len(items) > 100:
        raise ValueError("单个项目最多关联 100 项技能。")

    normalized: list[dict[str, Any]] = []
    seen: set[int] = set()
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("项目技能证据必须是 JSON 对象。")
        try:
            skill_id = int(item.get("skill_id"))
        except (TypeError, ValueError) as exc:
            raise ValueError("skill_id 必须是整数。") from exc
        _ensure_skill(connection, skill_id)
        if skill_id in seen:
            continue
        seen.add(skill_id)
        normalized.append(
            {
                "skill_id": skill_id,
                "evidence_text": _string(
                    item.get("evidence_text"),
                    field="evidence_text",
                    maximum=1200,
                ),
                "evidence_strength": _enum(
                    item.get("evidence_strength", "supporting"),
                    field="evidence_strength",
                    allowed=EVIDENCE_STRENGTHS,
                ),
            }
        )
    return normalized


def _replace_project_evidence(
    connection: sqlite3.Connection,
    project_id: int,
    items: list[dict[str, Any]],
) -> None:
    now = utc_now()
    connection.execute(
        "DELETE FROM project_skill_evidence WHERE project_id = ?",
        (project_id,),
    )
    connection.executemany(
        """
        INSERT INTO project_skill_evidence (
            project_id,
            skill_id,
            evidence_text,
            evidence_strength,
            created_at,
            updated_at
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (
                project_id,
                item["skill_id"],
                item["evidence_text"],
                item["evidence_strength"],
                now,
                now,
            )
            for item in items
        ],
    )


def list_projects(*, db_path: Path = DB_PATH) -> list[dict[str, Any]]:
    initialize_profile_schema(db_path)
    with connect(db_path) as connection:
        project_rows = connection.execute(
            """
            SELECT * FROM user_projects
            ORDER BY project_id DESC
            """
        ).fetchall()
        evidence_rows = connection.execute(
            """
            SELECT
                e.evidence_id,
                e.project_id,
                e.skill_id,
                s.skill_name,
                e.evidence_text,
                e.evidence_strength,
                e.created_at,
                e.updated_at
            FROM project_skill_evidence AS e
            JOIN user_skills AS s ON s.skill_id = e.skill_id
            ORDER BY e.project_id, s.skill_name COLLATE NOCASE
            """
        ).fetchall()

    by_project: dict[int, list[dict[str, Any]]] = {}
    for row in evidence_rows:
        item = dict(row)
        by_project.setdefault(int(item["project_id"]), []).append(item)

    result: list[dict[str, Any]] = []
    for row in project_rows:
        item = dict(row)
        item["skills"] = by_project.get(int(item["project_id"]), [])
        result.append(item)
    return result


def get_project(project_id: int, *, db_path: Path = DB_PATH) -> dict[str, Any]:
    for project in list_projects(db_path=db_path):
        if int(project["project_id"]) == int(project_id):
            return project
    raise KeyError(f"项目不存在：{project_id}")


def create_project(
    payload: dict[str, Any],
    *,
    db_path: Path = DB_PATH,
) -> dict[str, Any]:
    initialize_profile_schema(db_path)
    if not isinstance(payload, dict):
        raise ValueError("project payload 必须是 JSON 对象。")

    name = _string(
        payload.get("project_name"),
        field="project_name",
        maximum=180,
        required=True,
    )
    project_type = _enum(
        payload.get("project_type", "personal"),
        field="project_type",
        allowed=PROJECT_TYPES,
    )
    project_status = _enum(
        payload.get("project_status", "in_progress"),
        field="project_status",
        allowed=PROJECT_STATUSES,
    )
    description = _string(
        payload.get("description"), field="description", maximum=6000
    )
    achievements = _string(
        payload.get("achievements"), field="achievements", maximum=6000
    )
    github_url = _string(
        payload.get("github_url"), field="github_url", maximum=1000
    )
    demo_url = _string(payload.get("demo_url"), field="demo_url", maximum=1000)
    now = utc_now()

    with connect(db_path) as connection:
        evidence = _normalize_evidence_items(connection, payload.get("skills", []))
        cursor = connection.execute(
            """
            INSERT INTO user_projects (
                project_name,
                project_type,
                project_status,
                description,
                achievements,
                github_url,
                demo_url,
                created_at,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                project_type,
                project_status,
                description,
                achievements,
                github_url,
                demo_url,
                now,
                now,
            ),
        )
        project_id = int(cursor.lastrowid)
        _replace_project_evidence(connection, project_id, evidence)

    return get_project(project_id, db_path=db_path)


def patch_project(
    project_id: int,
    payload: dict[str, Any],
    *,
    db_path: Path = DB_PATH,
) -> dict[str, Any]:
    initialize_profile_schema(db_path)
    if not isinstance(payload, dict):
        raise ValueError("project payload 必须是 JSON 对象。")

    allowed = {
        "project_name",
        "project_type",
        "project_status",
        "description",
        "achievements",
        "github_url",
        "demo_url",
        "skills",
    }
    unknown = sorted(set(payload) - allowed)
    if unknown:
        raise ValueError("不支持的项目字段：" + ", ".join(unknown))

    updates: dict[str, Any] = {}
    if "project_name" in payload:
        updates["project_name"] = _string(
            payload["project_name"],
            field="project_name",
            maximum=180,
            required=True,
        )
    if "project_type" in payload:
        updates["project_type"] = _enum(
            payload["project_type"], field="project_type", allowed=PROJECT_TYPES
        )
    if "project_status" in payload:
        updates["project_status"] = _enum(
            payload["project_status"],
            field="project_status",
            allowed=PROJECT_STATUSES,
        )
    if "description" in payload:
        updates["description"] = _string(
            payload["description"], field="description", maximum=6000
        )
    if "achievements" in payload:
        updates["achievements"] = _string(
            payload["achievements"], field="achievements", maximum=6000
        )
    if "github_url" in payload:
        updates["github_url"] = _string(
            payload["github_url"], field="github_url", maximum=1000
        )
    if "demo_url" in payload:
        updates["demo_url"] = _string(
            payload["demo_url"], field="demo_url", maximum=1000
        )

    with connect(db_path) as connection:
        _ensure_project(connection, project_id)
        evidence = None
        if "skills" in payload:
            evidence = _normalize_evidence_items(connection, payload["skills"])
        if updates:
            updates["updated_at"] = utc_now()
            assignments = ", ".join(f"{field} = ?" for field in updates)
            connection.execute(
                f"UPDATE user_projects SET {assignments} WHERE project_id = ?",
                list(updates.values()) + [project_id],
            )
        if evidence is not None:
            _replace_project_evidence(connection, project_id, evidence)

    return get_project(project_id, db_path=db_path)


def delete_project(project_id: int, *, db_path: Path = DB_PATH) -> dict[str, Any]:
    initialize_profile_schema(db_path)
    with connect(db_path) as connection:
        _ensure_project(connection, project_id)
        connection.execute(
            "DELETE FROM user_projects WHERE project_id = ?", (project_id,)
        )
    return {"deleted": True, "project_id": int(project_id)}


# ---------------------------------------------------------------------------
# Dynamic corpus suggestions
# ---------------------------------------------------------------------------


def _literal_skill_defs_from_script(path: Path) -> list[tuple[str, str, list[str]]]:
    source = path.read_text(encoding="utf-8-sig")
    tree = ast.parse(source)
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "SKILL_DEFS" for target in node.targets):
            continue
        value = ast.literal_eval(node.value)
        if not isinstance(value, list):
            break
        result: list[tuple[str, str, list[str]]] = []
        for item in value:
            if not isinstance(item, tuple) or len(item) != 3:
                continue
            name, group, patterns = item
            if not isinstance(name, str) or not isinstance(group, str):
                continue
            if not isinstance(patterns, list) or not all(
                isinstance(pattern, str) for pattern in patterns
            ):
                continue
            result.append((name, group, patterns))
        if result:
            return result
    raise ValueError("未能从 pipeline/audit_skills.py 读取 SKILL_DEFS。")


@lru_cache(maxsize=1)
def load_skill_definitions() -> tuple[tuple[str, str, tuple[str, ...]], ...]:
    script_path = PROJECT_ROOT / "pipeline" / "audit_skills.py"
    try:
        definitions = _literal_skill_defs_from_script(script_path)
    except (OSError, SyntaxError, ValueError):
        definitions = FALLBACK_SKILL_DEFS

    compiled_safe: list[tuple[str, str, tuple[str, ...]]] = []
    known_names: set[str] = set()
    for name, group, patterns in definitions:
        safe_patterns: list[str] = []
        for pattern in patterns:
            try:
                re.compile(pattern, flags=re.IGNORECASE)
            except re.error:
                continue
            safe_patterns.append(pattern)
        if safe_patterns:
            compiled_safe.append((name, group, tuple(safe_patterns)))
            known_names.add(name.casefold())

    for name, group, patterns in FALLBACK_SKILL_DEFS:
        if name.casefold() in known_names:
            continue
        compiled_safe.append((name, group, tuple(patterns)))

    return tuple(compiled_safe)


def _job_text(record: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in (
        "job_title",
        "job_description",
        "core_text",
        "role_category_v11",
        "role_secondary_tags",
    ):
        value = record.get(key)
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, list):
            parts.extend(str(item) for item in value)

    tags = record.get("job_tags")
    if isinstance(tags, list):
        parts.extend(str(item) for item in tags)
    elif isinstance(tags, str):
        parts.append(tags)

    return "\n".join(parts)


def _iter_skill_source_jobs(
    connection: sqlite3.Connection,
) -> Iterable[dict[str, Any]]:
    management_exists = connection.execute(
        """
        SELECT 1 FROM sqlite_master
        WHERE type = 'table' AND name = 'job_management'
        """
    ).fetchone()

    if management_exists:
        rows = connection.execute(
            """
            SELECT j.canonical_json
            FROM jobs AS j
            LEFT JOIN job_management AS m ON m.job_id = j.job_id
            WHERE COALESCE(m.quality_override, 'auto') != 'exclude'
              AND m.archived_at IS NULL
            ORDER BY j.rowid
            """
        ).fetchall()
    else:
        rows = connection.execute(
            "SELECT canonical_json FROM jobs ORDER BY rowid"
        ).fetchall()

    for row in rows:
        try:
            value = json.loads(row["canonical_json"])
        except (TypeError, json.JSONDecodeError):
            continue
        if isinstance(value, dict):
            yield value


def _profile_job_count(*, db_path: Path = DB_PATH) -> int:
    initialize_profile_schema(db_path)
    with connect(db_path) as connection:
        return sum(1 for _ in _iter_skill_source_jobs(connection))


def _onboarding_maturity(job_count: int) -> dict[str, Any]:
    if job_count <= 0:
        return {
            "stage": "cold_start",
            "label": "尚未采集岗位",
            "confidence": "起始建议",
            "progress": 0,
            "message": "先采集一个真正感兴趣的岗位，系统会立即用真实岗位要求替换通用起始建议。",
        }
    if job_count < 3:
        return {
            "stage": "first_sample",
            "label": f"基于 {job_count} 个岗位",
            "confidence": "初步参考",
            "progress": 30,
            "message": "已经形成第一批岗位技能候选；继续采集 3—5 个同方向岗位会更稳定。",
        }
    if job_count < 10:
        return {
            "stage": "emerging",
            "label": f"基于 {job_count} 个岗位",
            "confidence": "初步画像",
            "progress": min(80, 35 + job_count * 5),
            "message": "目标画像正在形成；达到 10 个左右岗位后，技能缺口与优先级会更可信。",
        }
    return {
        "stage": "stable",
        "label": f"基于 {job_count} 个岗位",
        "confidence": "样本较稳定",
        "progress": 100,
        "message": "当前岗位样本已足以支撑较稳定的技能建议与后续投递优先级分析。",
    }


def _starter_direction_names(profile: dict[str, Any]) -> list[str]:
    names: list[str] = []
    for job_type in profile.get("target_job_types", []):
        for direction in TARGET_TYPE_DIRECTION_STARTERS.get(str(job_type), ()):
            if direction not in names:
                names.append(direction)
    for direction, _ in COLD_START_DIRECTIONS:
        if direction not in names:
            names.append(direction)
    return names


def _starter_skill_names(
    *,
    selected_directions: Iterable[str],
) -> list[tuple[str, str]]:
    results: list[tuple[str, str]] = []
    seen: set[str] = set()
    directions = [str(item).strip() for item in selected_directions if str(item).strip()]

    for direction in directions:
        matched = False
        for keyword, skill_names in DIRECTION_STARTER_SKILLS.items():
            if keyword.casefold() not in direction.casefold():
                continue
            matched = True
            for skill_name in skill_names:
                key = skill_name.casefold()
                if key not in seen:
                    seen.add(key)
                    results.append((skill_name, direction))
        if not matched:
            continue

    if not results:
        for skill_name in GENERAL_STARTER_SKILLS:
            key = skill_name.casefold()
            if key not in seen:
                seen.add(key)
                results.append((skill_name, "通用起始建议"))

    return results


def skill_suggestions(
    *,
    query: str | None = None,
    limit: int = 100,
    db_path: Path = DB_PATH,
) -> dict[str, Any]:
    initialize_profile_schema(db_path)
    safe_limit = max(1, min(int(limit), 500))
    query_text = str(query or "").strip().casefold()
    definitions = load_skill_definitions()
    groups_by_name = {name: group for name, group, _ in definitions}

    with connect(db_path) as connection:
        added_rows = connection.execute(
            "SELECT skill_name FROM user_skills"
        ).fetchall()
        added = {str(row["skill_name"]).casefold() for row in added_rows}
        jobs = list(_iter_skill_source_jobs(connection))
        profile_row = connection.execute(
            "SELECT * FROM user_profile WHERE profile_id = 1"
        ).fetchone()
        direction_rows = connection.execute(
            "SELECT direction FROM user_job_preferences ORDER BY preference_id"
        ).fetchall()

    profile = _profile_row_to_dict(profile_row) if profile_row else {"target_job_types": []}
    selected_directions = [str(row["direction"]) for row in direction_rows]
    if not selected_directions:
        selected_directions = _starter_direction_names(profile)[:3]

    counts: dict[str, int] = {}
    corpus_groups: dict[str, str] = {}
    for record in jobs:
        job_text = _job_text(record)
        for name, group, patterns in definitions:
            if any(re.search(pattern, job_text, flags=re.IGNORECASE) for pattern in patterns):
                counts[name] = counts.get(name, 0) + 1
                corpus_groups[name] = group

    by_name: dict[str, dict[str, Any]] = {}
    for name, count in counts.items():
        by_name[name.casefold()] = {
            "skill_name": name,
            "skill_group": corpus_groups.get(name, "其他"),
            "job_count": count,
            "coverage": round(count / len(jobs), 4) if jobs else 0.0,
            "already_added": name.casefold() in added,
            "source": "job_corpus",
            "source_label": f"{count} 个已采集岗位提及",
            "source_detail": "来自本地岗位语料",
            "starter_direction": None,
        }

    starter_used = len(jobs) < 5 or len(by_name) < 8
    if starter_used:
        for skill_name, direction in _starter_skill_names(
            selected_directions=selected_directions,
        ):
            key = skill_name.casefold()
            if key in by_name:
                continue
            by_name[key] = {
                "skill_name": skill_name,
                "skill_group": groups_by_name.get(skill_name, "起始能力"),
                "job_count": 0,
                "coverage": 0.0,
                "already_added": key in added,
                "source": "direction_starter" if direction != "通用起始建议" else "general_starter",
                "source_label": (
                    f"来自目标方向：{direction}"
                    if direction != "通用起始建议"
                    else "通用起始建议"
                ),
                "source_detail": "仅用于冷启动，需要用户自行确认，不代表已经掌握",
                "starter_direction": direction,
            }

    items = [
        item
        for item in by_name.values()
        if not query_text
        or query_text in str(item["skill_name"]).casefold()
        or query_text in str(item["skill_group"]).casefold()
        or query_text in str(item["source_label"]).casefold()
    ]
    items.sort(
        key=lambda item: (
            0 if item["source"] == "job_corpus" else 1,
            -int(item["job_count"]),
            str(item["skill_name"]).casefold(),
        )
    )
    maturity = _onboarding_maturity(len(jobs))

    return {
        "source_job_count": len(jobs),
        "total": len(items),
        "items": items[:safe_limit],
        "mode": (
            "job_corpus"
            if jobs and not starter_used
            else "blended"
            if jobs
            else "cold_start"
        ),
        "starter_used": starter_used,
        "maturity": maturity,
    }


def direction_suggestions(
    *,
    query: str | None = None,
    limit: int = 100,
    db_path: Path = DB_PATH,
) -> dict[str, Any]:
    initialize_profile_schema(db_path)
    safe_limit = max(1, min(int(limit), 500))
    query_text = str(query or "").strip().casefold()

    with connect(db_path) as connection:
        jobs = list(_iter_skill_source_jobs(connection))
        existing_rows = connection.execute(
            "SELECT direction FROM user_job_preferences"
        ).fetchall()
        profile_row = connection.execute(
            "SELECT * FROM user_profile WHERE profile_id = 1"
        ).fetchone()
    existing = {str(row["direction"]).casefold() for row in existing_rows}
    profile = _profile_row_to_dict(profile_row) if profile_row else {"target_job_types": []}

    counts: dict[str, int] = {}
    for record in jobs:
        value = record.get("role_category_v11") or record.get("role_category_v1")
        if isinstance(value, str) and value.strip():
            direction = value.strip()
            counts[direction] = counts.get(direction, 0) + 1

    by_name: dict[str, dict[str, Any]] = {}
    for direction, count in counts.items():
        by_name[direction.casefold()] = {
            "direction": direction,
            "job_count": count,
            "already_added": direction.casefold() in existing,
            "source": "job_corpus",
            "source_label": f"{count} 个已采集岗位归入此方向",
        }

    starter_used = len(jobs) < 5 or len(by_name) < 4
    if starter_used:
        for direction in _starter_direction_names(profile):
            key = direction.casefold()
            if key in by_name:
                continue
            by_name[key] = {
                "direction": direction,
                "job_count": 0,
                "already_added": key in existing,
                "source": "starter_pack",
                "source_label": "冷启动方向建议",
            }

    items = [
        item
        for item in by_name.values()
        if not query_text or query_text in str(item["direction"]).casefold()
    ]
    items.sort(
        key=lambda item: (
            0 if item["source"] == "job_corpus" else 1,
            -int(item["job_count"]),
            str(item["direction"]).casefold(),
        )
    )
    maturity = _onboarding_maturity(len(jobs))

    return {
        "source_job_count": len(jobs),
        "total": len(items),
        "items": items[:safe_limit],
        "mode": (
            "job_corpus"
            if jobs and not starter_used
            else "blended"
            if jobs
            else "cold_start"
        ),
        "starter_used": starter_used,
        "maturity": maturity,
    }


def profile_onboarding_status(*, db_path: Path = DB_PATH) -> dict[str, Any]:
    initialize_profile_schema(db_path)
    profile = get_profile(db_path=db_path)
    summary = profile_summary(db_path=db_path)
    job_count = _profile_job_count(db_path=db_path)
    maturity = _onboarding_maturity(job_count)

    checks = {
        "identity": bool(profile.get("education") and profile.get("graduation_year")),
        "target_job_type": bool(profile.get("target_job_types")),
        "location": bool(
            summary["city_count"]
            or profile.get("accepts_remote")
            or profile.get("accepts_relocation")
        ),
        "direction": bool(summary["direction_count"]),
        "skill": bool(summary["skill_count"]),
    }
    completed_steps = sum(1 for value in checks.values() if value)
    profile_initialized = all(checks.values())

    if job_count <= 0:
        next_action = "collect_first_job"
        action_label = "采集第一个岗位"
    elif not checks["identity"] or not checks["target_job_type"]:
        next_action = "complete_minimal_profile"
        action_label = "完成 60 秒设置"
    elif not checks["direction"] or not checks["skill"]:
        next_action = "confirm_recommendations"
        action_label = "确认方向与技能"
    elif summary["project_count"] <= 0:
        next_action = "optional_project"
        action_label = "可选：补充项目证据"
    else:
        next_action = "ready"
        action_label = "档案已可用于决策"

    return {
        "profile_initialized": profile_initialized,
        "completed_steps": completed_steps,
        "total_steps": len(checks),
        "completion_percent": round(completed_steps / len(checks) * 100),
        "checks": checks,
        "job_count": job_count,
        "maturity": maturity,
        "next_action": next_action,
        "action_label": action_label,
        "can_generate_initial_match": profile_initialized and job_count >= 1,
        "project_is_optional": True,
        "recommendation_basis": (
            "通用与方向起始建议"
            if job_count <= 0
            else f"{job_count} 个本地岗位样本"
        ),
        "source_explanations": {
            "user_confirmed": "由用户填写或确认",
            "job_corpus": "来自已采集岗位语料",
            "direction_starter": "来自用户选择的目标方向，仅用于冷启动",
            "project_evidence": "来自用户录入项目及其技能关联",
        },
    }


# ---------------------------------------------------------------------------
# Combined reads
# ---------------------------------------------------------------------------


def profile_options() -> dict[str, Any]:
    return {
        "proficiency_levels": list(PROFICIENCY_LEVELS),
        "project_types": list(PROJECT_TYPES),
        "project_statuses": list(PROJECT_STATUSES),
        "evidence_strengths": list(EVIDENCE_STRENGTHS),
        "interest_levels": list(INTEREST_LEVELS),
        "constraint_levels": list(CONSTRAINT_LEVELS),
        "target_job_types": list(TARGET_JOB_TYPES),
    }


def profile_summary(*, db_path: Path = DB_PATH) -> dict[str, Any]:
    initialize_profile_schema(db_path)
    with connect(db_path) as connection:
        skill_count = int(
            connection.execute("SELECT COUNT(*) AS count FROM user_skills").fetchone()["count"]
        )
        project_count = int(
            connection.execute("SELECT COUNT(*) AS count FROM user_projects").fetchone()["count"]
        )
        direction_count = int(
            connection.execute("SELECT COUNT(*) AS count FROM user_job_preferences").fetchone()["count"]
        )
        city_count = int(
            connection.execute("SELECT COUNT(*) AS count FROM user_location_preferences").fetchone()["count"]
        )
        evidence_count = int(
            connection.execute("SELECT COUNT(*) AS count FROM project_skill_evidence").fetchone()["count"]
        )
    return {
        "skill_count": skill_count,
        "project_count": project_count,
        "direction_count": direction_count,
        "city_count": city_count,
        "evidence_count": evidence_count,
    }


def get_full_profile(*, db_path: Path = DB_PATH) -> dict[str, Any]:
    return {
        "profile": get_profile(db_path=db_path),
        "cities": list_locations(db_path=db_path),
        "skills": list_skills(db_path=db_path),
        "projects": list_projects(db_path=db_path),
        "directions": list_preferences(db_path=db_path),
        "options": profile_options(),
        "summary": profile_summary(db_path=db_path),
        "onboarding": profile_onboarding_status(db_path=db_path),
    }


# PHASE_81_PROFILE_MODEL
# PHASE_81C_COLD_START_PROFILE_MODEL
