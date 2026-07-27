from __future__ import annotations

import json
import math
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from statistics import median
from typing import Any, Iterable

from .config import DB_PATH
from .database import connect, initialize_database, utc_now
from .management import initialize_management_schema
from .profile import (
    get_profile,
    initialize_profile_schema,
    list_locations,
    list_preferences,
    list_projects,
    list_skills,
    load_skill_definitions,
)


ACTION_GROUPS = (
    "apply_now",
    "stretch",
    "prepare_first",
    "defer",
)

ACTION_GROUP_LABELS = {
    "apply_now": "立即投递",
    "stretch": "值得冲刺",
    "prepare_first": "补材料后投递",
    "defer": "暂缓",
}

CALIBRATION_LIMIT = 10

PROFICIENCY_WEIGHTS = {
    "aware": 0.30,
    "basic": 0.55,
    "proficient": 0.80,
    "project_ready": 1.00,
}

INTEREST_WEIGHTS = {
    "very_high": 1.00,
    "high": 0.80,
    "acceptable": 0.55,
    "low": 0.25,
    "none": 0.00,
}

EDUCATION_RANK = {
    "初中及以下": 0,
    "高中": 1,
    "中专": 1,
    "中专/中技": 1,
    "大专": 2,
    "大专及以上": 2,
    "本科": 3,
    "本科及以上": 3,
    "硕士": 4,
    "硕士及以上": 4,
    "博士": 5,
    "博士及以上": 5,
}

DATA_ROLE_PATTERNS = (
    r"数据分析",
    r"商业分析",
    r"经营分析",
    r"BI",
    r"分析师",
    r"数据运营",
)

AI_ROLE_PATTERNS = (
    r"AI",
    r"大模型",
    r"LLM",
    r"Agent",
    r"智能体",
    r"RAG",
    r"算法",
    r"机器学习",
)


@dataclass(frozen=True)
class Candidate:
    job_id: str
    payload: dict[str, Any]
    metrics: dict[str, Any]


def initialize_calibration_schema(
    db_path: Path = DB_PATH,
) -> dict[str, int]:
    initialize_database(db_path)
    initialize_management_schema(db_path)
    initialize_profile_schema(db_path)

    with connect(db_path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS decision_calibration_sample (
                sample_order INTEGER PRIMARY KEY,
                job_id TEXT NOT NULL UNIQUE,
                selection_bucket TEXT NOT NULL,
                selection_reason TEXT NOT NULL DEFAULT '',
                generated_at TEXT NOT NULL,
                FOREIGN KEY (job_id)
                    REFERENCES jobs(job_id)
                    ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_decision_calibration_job
            ON decision_calibration_sample(job_id);

            CREATE TABLE IF NOT EXISTS decision_calibration_labels (
                job_id TEXT PRIMARY KEY,
                action_group TEXT NOT NULL,
                reason TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (job_id)
                    REFERENCES jobs(job_id)
                    ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_decision_calibration_action
            ON decision_calibration_labels(action_group);
            """
        )

        sample_count = connection.execute(
            "SELECT COUNT(*) AS count FROM decision_calibration_sample"
        ).fetchone()["count"]
        label_count = connection.execute(
            "SELECT COUNT(*) AS count FROM decision_calibration_labels"
        ).fetchone()["count"]

    return {
        "sample_count": int(sample_count),
        "label_count": int(label_count),
    }


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        return " ".join(_text(item) for item in value)
    if isinstance(value, dict):
        return " ".join(_text(item) for item in value.values())
    return re.sub(r"\s+", " ", str(value)).strip()


def _job_text(record: dict[str, Any]) -> str:
    parts = [
        _text(record.get("job_title")),
        _text(record.get("job_description")),
        _text(record.get("core_text")),
        _text(record.get("job_tags")),
        _text(record.get("role_category_v11")),
        _text(record.get("role_category_v1")),
        _text(record.get("role_secondary_tags")),
        _text(record.get("category_manual")),
    ]
    return "\n".join(part for part in parts if part)


def _parse_json(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    try:
        parsed = json.loads(str(value or ""))
    except (TypeError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _load_raw_jobs(
    *,
    db_path: Path,
) -> list[dict[str, Any]]:
    initialize_calibration_schema(db_path)

    with connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT
                j.job_id,
                j.job_title,
                j.company_name,
                j.city,
                j.salary,
                j.source_url,
                j.first_seen_at,
                j.updated_at,
                j.canonical_json,
                COALESCE(m.user_status, 'to_review') AS user_status,
                COALESCE(m.listing_status, 'unknown') AS listing_status,
                COALESCE(m.quality_override, 'auto') AS quality_override,
                COALESCE(m.category_manual, '') AS category_manual,
                COALESCE(m.notes, '') AS management_notes,
                m.archived_at
            FROM jobs AS j
            LEFT JOIN job_management AS m
              ON m.job_id = j.job_id
            WHERE COALESCE(m.quality_override, 'auto') != 'exclude'
              AND m.archived_at IS NULL
              AND COALESCE(m.user_status, 'to_review') NOT IN (
                    'rejected', 'abandoned'
              )
            ORDER BY j.rowid
            """
        ).fetchall()

    jobs: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        canonical = _parse_json(item.pop("canonical_json"))
        canonical.update(
            {
                "job_id": item["job_id"],
                "job_title": item["job_title"] or canonical.get("job_title", ""),
                "company_name": item["company_name"],
                "city": item["city"] or canonical.get("city", ""),
                "salary": item["salary"] or canonical.get("salary", ""),
                "source_url": item["source_url"],
                "first_seen_at": item["first_seen_at"],
                "updated_at": item["updated_at"],
                "user_status": item["user_status"],
                "listing_status": item["listing_status"],
                "quality_override": item["quality_override"],
                "category_manual": item["category_manual"],
                "management_notes": item["management_notes"],
            }
        )
        jobs.append(canonical)
    return jobs


def _profile_context(*, db_path: Path) -> dict[str, Any]:
    profile = get_profile(db_path=db_path)
    skills = list_skills(db_path=db_path)
    projects = list_projects(db_path=db_path)
    locations = list_locations(db_path=db_path)
    preferences = list_preferences(db_path=db_path)

    skill_map = {
        str(item["skill_name"]).casefold(): item
        for item in skills
    }
    direction_map = {
        str(item["direction"]).casefold(): item
        for item in preferences
    }

    return {
        "profile": profile,
        "skills": skills,
        "skill_map": skill_map,
        "projects": projects,
        "locations": locations,
        "preferences": preferences,
        "direction_map": direction_map,
    }


def _detect_skills(record: dict[str, Any]) -> list[str]:
    text = _job_text(record)
    detected: list[str] = []
    for name, _, patterns in load_skill_definitions():
        if any(
            re.search(pattern, text, flags=re.IGNORECASE)
            for pattern in patterns
        ):
            detected.append(name)
    return detected


def _direction(record: dict[str, Any]) -> str:
    for key in (
        "category_manual",
        "role_category_v11",
        "role_category_v1",
        "role_category",
    ):
        value = _text(record.get(key))
        if value:
            return value

    title_and_text = _job_text(record)
    if any(re.search(pattern, title_and_text, re.IGNORECASE) for pattern in DATA_ROLE_PATTERNS):
        return "数据分析与BI"
    if any(re.search(pattern, title_and_text, re.IGNORECASE) for pattern in AI_ROLE_PATTERNS):
        return "AI与大模型开发"
    return "其他"


def _salary_numbers(value: Any) -> list[float]:
    text = _text(value).lower().replace(",", "")
    numbers = [float(item) for item in re.findall(r"\d+(?:\.\d+)?", text)]
    if not numbers:
        return []

    multiplier = 1.0
    if "k" in text:
        multiplier = 1000.0
    elif "万" in text:
        multiplier = 10000.0

    return [number * multiplier for number in numbers[:2]]


def _salary_value(value: Any) -> tuple[float | None, str]:
    text = _text(value)
    numbers = _salary_numbers(text)
    if not numbers:
        return None, "unknown"

    midpoint = sum(numbers) / len(numbers)
    if "天" in text or "/日" in text or "日薪" in text:
        return midpoint, "daily"
    if "月" in text or "k" in text.lower() or "万" in text:
        return midpoint, "monthly"
    return midpoint, "unknown"


def _parse_first_int(value: Any) -> int | None:
    match = re.search(r"\d+", _text(value))
    return int(match.group()) if match else None


def _required_education(record: dict[str, Any]) -> str:
    return _text(record.get("education"))


def _user_education_rank(value: Any) -> int | None:
    text = _text(value)
    if not text:
        return None
    for key, rank in sorted(
        EDUCATION_RANK.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    ):
        if key in text:
            return rank
    return None


def _required_education_rank(value: Any) -> int | None:
    text = _text(value)
    if not text or "不限" in text:
        return None
    return _user_education_rank(text)


def _direction_interest(direction: str, context: dict[str, Any]) -> float:
    normalized = direction.casefold()
    best = 0.50
    for key, item in context["direction_map"].items():
        if key in normalized or normalized in key:
            best = max(
                best,
                INTEREST_WEIGHTS.get(str(item.get("interest_level")), 0.50),
            )
    return best


def _hard_conflicts(
    record: dict[str, Any],
    context: dict[str, Any],
) -> list[str]:
    conflicts: list[str] = []
    profile = context["profile"]

    hard_cities = {
        _text(item.get("city")).casefold()
        for item in context["locations"]
        if item.get("constraint_level") == "hard"
        and _text(item.get("city"))
    }
    city = _text(record.get("city")).casefold()
    if hard_cities and city and not any(
        allowed in city or city in allowed
        for allowed in hard_cities
    ):
        conflicts.append("岗位城市不在硬性可接受城市中")

    user_rank = _user_education_rank(profile.get("education"))
    required_rank = _required_education_rank(_required_education(record))
    if (
        user_rank is not None
        and required_rank is not None
        and required_rank > user_rank
    ):
        conflicts.append("学历要求高于当前学历")

    required_days = _parse_first_int(
        record.get("internship_days_per_week")
        or record.get("job_basic_info_raw")
    )
    max_days = profile.get("max_days_per_week")
    if required_days is not None and max_days is not None:
        try:
            if int(required_days) > int(max_days):
                conflicts.append("每周到岗天数不足")
        except (TypeError, ValueError):
            pass

    required_months = _parse_first_int(
        record.get("internship_duration")
        or record.get("job_basic_info_raw")
    )
    max_months = profile.get("max_internship_months")
    if required_months is not None and max_months is not None:
        try:
            if int(required_months) > int(max_months):
                conflicts.append("可实习总时长不足")
        except (TypeError, ValueError):
            pass

    listing_status = _text(record.get("listing_status"))
    if listing_status == "closed":
        conflicts.append("岗位已标记关闭")

    return conflicts


def _missing_fields(record: dict[str, Any]) -> list[str]:
    fields = (
        ("salary", "薪资"),
        ("city", "城市"),
        ("education", "学历"),
        ("job_description", "岗位描述"),
        ("company_name", "公司"),
    )
    return [label for key, label in fields if not _text(record.get(key))]


def _skill_metrics(
    required_skills: Iterable[str],
    context: dict[str, Any],
) -> dict[str, Any]:
    required = list(dict.fromkeys(required_skills))
    matched: list[str] = []
    gaps: list[str] = []
    weighted = 0.0

    for skill in required:
        item = context["skill_map"].get(skill.casefold())
        if item is None:
            gaps.append(skill)
            continue
        matched.append(skill)
        weighted += PROFICIENCY_WEIGHTS.get(
            str(item.get("proficiency_level")),
            0.50,
        )

    denominator = max(1, len(required))
    return {
        "required_skills": required,
        "matched_skills": matched,
        "skill_gaps": gaps,
        "skill_fit_proxy": round(weighted / denominator, 4),
        "skill_coverage": round(len(matched) / denominator, 4),
    }


def _project_evidence_count(
    matched_skills: Iterable[str],
    context: dict[str, Any],
) -> int:
    matched = {item.casefold() for item in matched_skills}
    evidence_skills: set[str] = set()
    for project in context["projects"]:
        for item in project.get("skills", []):
            name = _text(item.get("skill_name"))
            if name.casefold() in matched:
                evidence_skills.add(name.casefold())
    return len(evidence_skills)


def _candidate_metrics(
    record: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    required_skills = _detect_skills(record)
    skill = _skill_metrics(required_skills, context)
    direction = _direction(record)
    direction_interest = _direction_interest(direction, context)
    conflicts = _hard_conflicts(record, context)
    missing = _missing_fields(record)
    salary_value, salary_unit = _salary_value(record.get("salary"))
    evidence_count = _project_evidence_count(skill["matched_skills"], context)

    information_score = max(0.0, 1.0 - len(missing) / 5.0)
    listing_status = _text(record.get("listing_status"))
    active_bonus = 1.0 if listing_status == "active" else 0.7 if listing_status == "unknown" else 0.3

    match_proxy = (
        0.65 * float(skill["skill_fit_proxy"])
        + 0.20 * direction_interest
        + 0.15 * min(1.0, evidence_count / 3.0)
    )
    opportunity_proxy = (
        0.55 * direction_interest
        + 0.25 * information_score
        + 0.20 * active_bonus
    )

    return {
        **skill,
        "direction": direction,
        "direction_interest_proxy": round(direction_interest, 4),
        "project_evidence_count": evidence_count,
        "hard_conflicts": conflicts,
        "missing_fields": missing,
        "salary_value": salary_value,
        "salary_unit": salary_unit,
        "match_proxy": round(match_proxy, 4),
        "opportunity_proxy": round(opportunity_proxy, 4),
        "listing_status": listing_status or "unknown",
        "user_status": _text(record.get("user_status")) or "to_review",
    }


def _salary_percentiles(candidates: list[Candidate]) -> dict[str, dict[str, float]]:
    by_unit: dict[str, list[float]] = {}
    for candidate in candidates:
        value = candidate.metrics.get("salary_value")
        unit = str(candidate.metrics.get("salary_unit") or "unknown")
        if value is None or unit == "unknown":
            continue
        by_unit.setdefault(unit, []).append(float(value))

    result: dict[str, dict[str, float]] = {}
    for unit, values in by_unit.items():
        ordered = sorted(values)
        if not ordered:
            continue
        result[unit] = {
            "median": float(median(ordered)),
            "min": float(ordered[0]),
            "max": float(ordered[-1]),
        }
    return result


def _salary_relative(candidate: Candidate, stats: dict[str, dict[str, float]]) -> float:
    value = candidate.metrics.get("salary_value")
    unit = str(candidate.metrics.get("salary_unit") or "unknown")
    if value is None or unit not in stats:
        return 0.5
    minimum = stats[unit]["min"]
    maximum = stats[unit]["max"]
    if math.isclose(minimum, maximum):
        return 0.5
    return max(0.0, min(1.0, (float(value) - minimum) / (maximum - minimum)))


def _contains_role(candidate: Candidate, patterns: Iterable[str]) -> bool:
    text = _job_text(candidate.payload)
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def _selection_reason(bucket: str, candidate: Candidate) -> str:
    metrics = candidate.metrics
    reasons = {
        "hard_conflict": "用于检查硬条件冲突是否会覆盖普通高分。",
        "inactive": "用于检查岗位失效状态是否会进入暂缓组。",
        "information_missing": "用于检查信息缺失是否被误判为不满足。",
        "data_analysis": "用于校准数据分析类目标岗位。",
        "ai_application": "用于校准AI应用或机器学习类目标岗位。",
        "high_match_high_value": "用于校准高匹配且较有价值的岗位。",
        "high_match_low_value": "用于区分匹配度与机会价值。",
        "low_match_high_value": "用于校准值得冲刺的高价值岗位。",
        "skill_gap": "用于检查明显技能缺口的处理方式。",
        "salary_outlier": "用于检查薪资异常或样本极端值。",
        "diversity_fallback": "用于补足职位方向、城市和信息结构的多样性。",
    }
    detail: list[str] = []
    if metrics["hard_conflicts"]:
        detail.append("冲突：" + "；".join(metrics["hard_conflicts"][:2]))
    if metrics["skill_gaps"]:
        detail.append("缺口：" + "、".join(metrics["skill_gaps"][:3]))
    if metrics["missing_fields"]:
        detail.append("缺失：" + "、".join(metrics["missing_fields"][:3]))
    suffix = " " + "；".join(detail) if detail else ""
    return reasons[bucket] + suffix


def _choose_unique(
    selected: list[tuple[str, Candidate]],
    bucket: str,
    candidates: Iterable[Candidate],
) -> None:
    used = {candidate.job_id for _, candidate in selected}
    for candidate in candidates:
        if candidate.job_id not in used:
            selected.append((bucket, candidate))
            return


def _generate_sample(
    candidates: list[Candidate],
    *,
    limit: int,
) -> list[tuple[str, Candidate]]:
    if not candidates:
        return []

    salary_stats = _salary_percentiles(candidates)
    selected: list[tuple[str, Candidate]] = []

    _choose_unique(
        selected,
        "hard_conflict",
        sorted(
            [item for item in candidates if item.metrics["hard_conflicts"]],
            key=lambda item: (
                -len(item.metrics["hard_conflicts"]),
                -item.metrics["match_proxy"],
                item.job_id,
            ),
        ),
    )

    _choose_unique(
        selected,
        "inactive",
        sorted(
            [
                item
                for item in candidates
                if item.metrics["listing_status"] in {"closed", "suspected_inactive"}
            ],
            key=lambda item: (item.metrics["listing_status"] != "closed", item.job_id),
        ),
    )

    _choose_unique(
        selected,
        "information_missing",
        sorted(
            [item for item in candidates if item.metrics["missing_fields"]],
            key=lambda item: (-len(item.metrics["missing_fields"]), item.job_id),
        ),
    )

    _choose_unique(
        selected,
        "data_analysis",
        sorted(
            [item for item in candidates if _contains_role(item, DATA_ROLE_PATTERNS)],
            key=lambda item: (-item.metrics["match_proxy"], -item.metrics["opportunity_proxy"], item.job_id),
        ),
    )

    _choose_unique(
        selected,
        "ai_application",
        sorted(
            [item for item in candidates if _contains_role(item, AI_ROLE_PATTERNS)],
            key=lambda item: (-item.metrics["match_proxy"], -item.metrics["opportunity_proxy"], item.job_id),
        ),
    )

    _choose_unique(
        selected,
        "high_match_high_value",
        sorted(
            candidates,
            key=lambda item: (
                -(0.55 * item.metrics["match_proxy"] + 0.45 * item.metrics["opportunity_proxy"]),
                len(item.metrics["hard_conflicts"]),
                item.job_id,
            ),
        ),
    )

    _choose_unique(
        selected,
        "high_match_low_value",
        sorted(
            candidates,
            key=lambda item: (
                -item.metrics["match_proxy"],
                item.metrics["opportunity_proxy"],
                item.job_id,
            ),
        ),
    )

    _choose_unique(
        selected,
        "low_match_high_value",
        sorted(
            candidates,
            key=lambda item: (
                -item.metrics["opportunity_proxy"],
                item.metrics["match_proxy"],
                item.job_id,
            ),
        ),
    )

    _choose_unique(
        selected,
        "skill_gap",
        sorted(
            [item for item in candidates if item.metrics["skill_gaps"]],
            key=lambda item: (-len(item.metrics["skill_gaps"]), item.metrics["match_proxy"], item.job_id),
        ),
    )

    _choose_unique(
        selected,
        "salary_outlier",
        sorted(
            [item for item in candidates if item.metrics["salary_value"] is not None],
            key=lambda item: (-abs(_salary_relative(item, salary_stats) - 0.5), item.job_id),
        ),
    )

    if len(selected) < limit:
        used_directions = {candidate.metrics["direction"] for _, candidate in selected}
        used_cities = {_text(candidate.payload.get("city")) for _, candidate in selected}
        fallback = sorted(
            candidates,
            key=lambda item: (
                item.metrics["direction"] in used_directions,
                _text(item.payload.get("city")) in used_cities,
                -len(item.metrics["required_skills"]),
                item.job_id,
            ),
        )
        for candidate in fallback:
            if len(selected) >= limit:
                break
            _choose_unique(selected, "diversity_fallback", [candidate])

    return selected[:limit]


def _persist_sample(
    selected: list[tuple[str, Candidate]],
    *,
    db_path: Path,
) -> None:
    now = utc_now()
    with connect(db_path) as connection:
        connection.execute("DELETE FROM decision_calibration_sample")
        connection.executemany(
            """
            INSERT INTO decision_calibration_sample (
                sample_order,
                job_id,
                selection_bucket,
                selection_reason,
                generated_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            [
                (
                    index,
                    candidate.job_id,
                    bucket,
                    _selection_reason(bucket, candidate),
                    now,
                )
                for index, (bucket, candidate) in enumerate(selected, start=1)
            ],
        )


def _existing_sample_rows(
    *,
    db_path: Path,
) -> list[dict[str, Any]]:
    with connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT
                s.sample_order,
                s.job_id,
                s.selection_bucket,
                s.selection_reason,
                s.generated_at
            FROM decision_calibration_sample AS s
            JOIN jobs AS j ON j.job_id = s.job_id
            LEFT JOIN job_management AS m ON m.job_id = s.job_id
            WHERE COALESCE(m.quality_override, 'auto') != 'exclude'
              AND m.archived_at IS NULL
            ORDER BY s.sample_order
            """
        ).fetchall()
    return [dict(row) for row in rows]


def _label_map(*, db_path: Path) -> dict[str, dict[str, Any]]:
    with connect(db_path) as connection:
        rows = connection.execute(
            "SELECT * FROM decision_calibration_labels"
        ).fetchall()
    return {str(row["job_id"]): dict(row) for row in rows}


def get_representative_jobs(
    *,
    limit: int = CALIBRATION_LIMIT,
    refresh: bool = False,
    db_path: Path = DB_PATH,
) -> dict[str, Any]:
    initialize_calibration_schema(db_path)
    safe_limit = max(1, min(int(limit), CALIBRATION_LIMIT))
    jobs = _load_raw_jobs(db_path=db_path)
    context = _profile_context(db_path=db_path)
    candidates = [
        Candidate(
            job_id=str(record.get("job_id") or ""),
            payload=record,
            metrics=_candidate_metrics(record, context),
        )
        for record in jobs
        if str(record.get("job_id") or "").strip()
    ]
    candidate_map = {item.job_id: item for item in candidates}

    sample_rows = [] if refresh else _existing_sample_rows(db_path=db_path)
    target_count = min(safe_limit, len(candidates))
    if len(sample_rows) < target_count:
        selected = _generate_sample(candidates, limit=target_count)
        _persist_sample(selected, db_path=db_path)
        sample_rows = _existing_sample_rows(db_path=db_path)

    labels = _label_map(db_path=db_path)
    items: list[dict[str, Any]] = []
    for row in sample_rows[:safe_limit]:
        candidate = candidate_map.get(str(row["job_id"]))
        if candidate is None:
            continue
        payload = candidate.payload
        label = labels.get(candidate.job_id)
        description = _text(payload.get("job_description"))
        items.append(
            {
                "sample_order": int(row["sample_order"]),
                "job_id": candidate.job_id,
                "job_title": _text(payload.get("job_title")),
                "company_name": _text(
                    payload.get("company_full_name")
                    or payload.get("company_short_name")
                    or payload.get("company_name")
                ),
                "city": _text(payload.get("city")),
                "salary": _text(payload.get("salary")),
                "education": _text(payload.get("education")),
                "experience": _text(payload.get("experience")),
                "internship_days_per_week": _text(payload.get("internship_days_per_week")),
                "internship_duration": _text(payload.get("internship_duration")),
                "source_url": _text(payload.get("source_url")),
                "description_excerpt": description[:700],
                "selection_bucket": row["selection_bucket"],
                "selection_reason": row["selection_reason"],
                "generated_at": row["generated_at"],
                "metrics": candidate.metrics,
                "label": label,
            }
        )

    return {
        "total_candidates": len(candidates),
        "sample_count": len(items),
        "target_count": target_count,
        "labeled_count": sum(1 for item in items if item["label"]),
        "complete": bool(items) and all(item["label"] for item in items),
        "items": items,
        "note": (
            "这些代理指标仅用于挑选有代表性的人工校准样本，"
            "不是最终投递优先级，也不会直接进入Phase 8.2B评分。"
        ),
    }


def list_calibration_labels(
    *,
    db_path: Path = DB_PATH,
) -> list[dict[str, Any]]:
    initialize_calibration_schema(db_path)
    with connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT
                l.job_id,
                j.job_title,
                j.company_name,
                l.action_group,
                l.reason,
                l.created_at,
                l.updated_at
            FROM decision_calibration_labels AS l
            JOIN jobs AS j ON j.job_id = l.job_id
            ORDER BY l.updated_at DESC, l.job_id
            """
        ).fetchall()
    return [dict(row) for row in rows]


def upsert_calibration_label(
    job_id: str,
    payload: dict[str, Any],
    *,
    db_path: Path = DB_PATH,
) -> dict[str, Any]:
    initialize_calibration_schema(db_path)
    normalized_job_id = str(job_id or "").strip()
    if not normalized_job_id:
        raise ValueError("job_id 不能为空。")
    if not isinstance(payload, dict):
        raise ValueError("标注内容必须是JSON对象。")

    action_group = str(payload.get("action_group") or "").strip()
    if action_group not in ACTION_GROUPS:
        raise ValueError(
            "action_group 必须是以下值之一："
            + ", ".join(ACTION_GROUPS)
        )
    reason = _text(payload.get("reason"))
    if not reason:
        raise ValueError("请填写一句人工判断理由。")
    if len(reason) > 2000:
        raise ValueError("人工判断理由不能超过2000个字符。")

    now = utc_now()
    with connect(db_path) as connection:
        exists = connection.execute(
            "SELECT 1 FROM jobs WHERE job_id = ?",
            (normalized_job_id,),
        ).fetchone()
        if exists is None:
            raise KeyError(f"岗位不存在：{normalized_job_id}")

        connection.execute(
            """
            INSERT INTO decision_calibration_labels (
                job_id,
                action_group,
                reason,
                created_at,
                updated_at
            ) VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(job_id) DO UPDATE SET
                action_group = excluded.action_group,
                reason = excluded.reason,
                updated_at = excluded.updated_at
            """,
            (
                normalized_job_id,
                action_group,
                reason,
                now,
                now,
            ),
        )

    return get_calibration_label(normalized_job_id, db_path=db_path)


def get_calibration_label(
    job_id: str,
    *,
    db_path: Path = DB_PATH,
) -> dict[str, Any]:
    initialize_calibration_schema(db_path)
    with connect(db_path) as connection:
        row = connection.execute(
            "SELECT * FROM decision_calibration_labels WHERE job_id = ?",
            (str(job_id),),
        ).fetchone()
    if row is None:
        raise KeyError(f"岗位尚未标注：{job_id}")
    return dict(row)


def delete_calibration_label(
    job_id: str,
    *,
    db_path: Path = DB_PATH,
) -> dict[str, Any]:
    initialize_calibration_schema(db_path)
    with connect(db_path) as connection:
        cursor = connection.execute(
            "DELETE FROM decision_calibration_labels WHERE job_id = ?",
            (str(job_id),),
        )
    return {
        "deleted": bool(cursor.rowcount),
        "job_id": str(job_id),
    }


def calibration_summary(
    *,
    db_path: Path = DB_PATH,
) -> dict[str, Any]:
    result = get_representative_jobs(db_path=db_path)
    counts = {group: 0 for group in ACTION_GROUPS}
    for item in result["items"]:
        label = item.get("label")
        if label and label.get("action_group") in counts:
            counts[label["action_group"]] += 1

    return {
        "sample_count": result["sample_count"],
        "labeled_count": result["labeled_count"],
        "remaining_count": result["sample_count"] - result["labeled_count"],
        "complete": result["complete"],
        "by_action_group": counts,
        "action_group_labels": ACTION_GROUP_LABELS,
        "next_step": (
            "可以进入Phase 8.2B评分引擎开发。"
            if result["complete"]
            else "请先完成全部代表岗位的人工分组和理由。"
        ),
    }


# PHASE_82A_CALIBRATION_MODEL
