from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any, Iterable

from .calibration import (
    ACTION_GROUPS,
    ACTION_GROUP_LABELS,
    initialize_calibration_schema,
)
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


# PHASE_82B_EXPLAINABLE_DECISION_ENGINE
ENGINE_VERSION = "8.2b.1"

STRATEGIES = ("conservative", "balanced", "stretch")
DEFAULT_STRATEGY = "balanced"

STRATEGY_LABELS = {
    "conservative": "保守",
    "balanced": "平衡",
    "stretch": "冲刺",
}

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

PENDING_USER_STATUSES = {"to_review", "interested", "preparing"}
IN_PROCESS_USER_STATUSES = {"applied", "written_test", "interview", "offer"}

ROLE_PATTERNS = {
    "数据分析与BI": (
        r"数据分析", r"商业分析", r"经营分析", r"分析师", r"BI\b",
        r"数据运营", r"策略分析", r"量化", r"预测",
    ),
    "AI与大模型开发": (
        r"AI", r"大模型", r"LLM", r"Agent", r"智能体", r"RAG",
        r"机器学习", r"算法", r"深度学习",
    ),
    "研究助理 / RA": (
        r"研究助理", r"科研助理", r"\bRA\b", r"研究实习", r"研究员",
    ),
    "数据工程与平台": (
        r"数据开发", r"数据工程", r"ETL", r"数仓", r"数据仓库",
        r"数据治理", r"数据平台", r"Spark", r"Hadoop", r"Hive",
    ),
    "AI产品与项目": (
        r"AI产品", r"产品实习", r"产品经理", r"项目实习", r"需求分析",
    ),
    "数据处理与标注": (
        r"数据标注", r"数据采集", r"数据录入", r"数据处理",
    ),
}

POSITIVE_GROWTH_PATTERNS = (
    r"A/B\s*实验", r"决策支持", r"业务增长", r"模型.*(?:搭建|训练|优化|部署)",
    r"端到端", r"全流程", r"落地上线", r"研发", r"算法", r"策略设计",
    r"异常分析", r"独立负责", r"核心模块", r"转正机会", r"真实项目",
)

LOW_GROWTH_PATTERNS = (
    r"数据标注", r"数据录入", r"按照流程", r"重复性", r"简单采集",
    r"测试数据", r"纯资料整理", r"仅.*Excel", r"基础维护",
)

RESPONSIBILITY_MARKERS = (
    r"岗位职责", r"工作职责", r"工作内容", r"负责", r"参与", r"协助",
)

SENIOR_MARKERS = (
    r"[3-9]\s*年(?:以上)?经验", r"负责人", r"架构师", r"主导", r"带领团队",
    r"专家", r"精通\s*C\+\+", r"平台架构", r"技术决策",
)

OPTIONAL_MARKERS = (
    r"优先", r"加分", r"最好", r"有.*经验者优先", r"了解.*优先",
    r"具备.*更佳", r"非必须",
)

STRONG_REQUIREMENT_MARKERS = (
    r"必须", r"精通", r"熟练", r"熟悉", r"掌握", r"能够", r"要求",
)

EXTRA_PROJECT_EVIDENCE_PATTERNS: dict[str, tuple[str, ...]] = {
    "统计分析": (r"统计分析", r"假设检验", r"置信区间", r"回归", r"xG"),
    "量化分析": (r"量化", r"滚动回测", r"回测", r"赔率", r"xG"),
    "数据采集": (r"岗位采集", r"数据采集", r"浏览器扩展", r"爬虫"),
    "数据清洗": (r"数据清洗", r"标准化", r"去重", r"规范化"),
    "模型评测": (r"模型评估", r"模型评测", r"MAE", r"RMSE", r"Brier", r"AUC"),
    "工作流编排": (r"工作流", r"workflow", r"pipeline", r"任务编排"),
    "工具调用": (r"Tool\s*Calling", r"工具调用", r"函数调用"),
    "API/接口": (r"FastAPI", r"REST\s*API", r"接口设计", r"API设计"),
    "自动化脚本": (r"PowerShell", r"自动化测试", r"安装脚本", r"自动化脚本"),
    "需求分析": (r"需求拆解", r"需求分析", r"架构设计", r"产品规划"),
    "Pandas": (r"Pandas"),
    "NumPy": (r"NumPy"),
    "Matplotlib": (r"Matplotlib", r"数据可视化"),
    "TypeScript": (r"TypeScript"),
    "FastAPI": (r"FastAPI"),
    "SQL": (r"SQLite", r"\bSQL\b"),
    "AI Agent": (r"Agent", r"智能体"),
    "Prompt": (r"Prompt", r"提示词"),
}

RELATED_SKILLS: dict[str, dict[str, float]] = {
    "API/接口": {"FastAPI": 0.90},
    "FastAPI": {"API/接口": 0.75},
    "模型评测": {"统计分析": 0.55, "量化分析": 0.65},
    "统计分析": {"量化分析": 0.55, "数据分析": 0.45},
    "量化分析": {"统计分析": 0.55, "数据分析": 0.45},
    "数据预处理": {"数据清洗": 0.85, "数据治理": 0.55},
    "数据治理": {"数据清洗": 0.45, "ETL": 0.55},
    "工作流编排": {"AI Agent": 0.45, "自动化脚本": 0.50},
    "工具调用": {"AI Agent": 0.45, "API/接口": 0.45},
    "数据采集": {"爬虫": 0.75},
    "爬虫": {"数据采集": 0.75},
}

STRATEGY_CONFIG = {
    "conservative": {
        "weights": {"match": 0.58, "opportunity": 0.18, "urgency": 0.12, "preference": 0.12},
        "prep_penalty": 0.13,
        "uncertainty_penalty": 0.10,
        "apply_priority": 73,
        "apply_match": 68,
        "apply_evidence": 45,
        "stretch_priority": 62,
        "stretch_match": 46,
        "stretch_opportunity": 62,
        "prepare_priority": 46,
    },
    "balanced": {
        "weights": {"match": 0.50, "opportunity": 0.27, "urgency": 0.13, "preference": 0.10},
        "prep_penalty": 0.10,
        "uncertainty_penalty": 0.08,
        "apply_priority": 68,
        "apply_match": 62,
        "apply_evidence": 38,
        "stretch_priority": 59,
        "stretch_match": 40,
        "stretch_opportunity": 62,
        "prepare_priority": 44,
    },
    "stretch": {
        "weights": {"match": 0.40, "opportunity": 0.38, "urgency": 0.12, "preference": 0.10},
        "prep_penalty": 0.07,
        "uncertainty_penalty": 0.06,
        "apply_priority": 64,
        "apply_match": 55,
        "apply_evidence": 30,
        "stretch_priority": 55,
        "stretch_match": 34,
        "stretch_opportunity": 58,
        "prepare_priority": 40,
    },
}

ACTION_ORDER = {
    "defer": 0,
    "prepare_first": 1,
    "stretch": 2,
    "apply_now": 3,
}


@dataclass(frozen=True)
class SkillMention:
    skill_name: str
    start: int
    end: int
    target_level: float
    optional: bool
    context: str


@dataclass(frozen=True)
class DecisionCandidate:
    job_id: str
    payload: dict[str, Any]


def _clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, value))


def _score(value: float) -> int:
    return int(round(_clamp(value)))


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        return " ".join(_text(item) for item in value)
    if isinstance(value, dict):
        return " ".join(_text(item) for item in value.values())
    return re.sub(r"\s+", " ", str(value)).strip()


def _parse_json(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    try:
        parsed = json.loads(str(value or ""))
    except (TypeError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _json_hash(value: Any) -> str:
    return hashlib.sha256(_json_dumps(value).encode("utf-8")).hexdigest()


def _validate_strategy(strategy: str) -> str:
    normalized = str(strategy or DEFAULT_STRATEGY).strip().lower()
    if normalized not in STRATEGIES:
        raise ValueError("strategy 必须是 conservative、balanced 或 stretch。")
    return normalized


def initialize_decision_schema(db_path: Path = DB_PATH) -> dict[str, int]:
    initialize_database(db_path)
    initialize_management_schema(db_path)
    initialize_profile_schema(db_path)
    initialize_calibration_schema(db_path)

    with connect(db_path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS decision_runs (
                run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy TEXT NOT NULL,
                engine_version TEXT NOT NULL,
                input_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                job_count INTEGER NOT NULL DEFAULT 0,
                queue_count INTEGER NOT NULL DEFAULT 0,
                exact_accuracy REAL,
                adjacent_accuracy REAL,
                calibration_count INTEGER NOT NULL DEFAULT 0
            );

            CREATE INDEX IF NOT EXISTS idx_decision_runs_strategy
            ON decision_runs(strategy, run_id DESC);

            CREATE TABLE IF NOT EXISTS decision_results (
                run_id INTEGER NOT NULL,
                job_id TEXT NOT NULL,
                action_group TEXT NOT NULL,
                match_score INTEGER NOT NULL,
                opportunity_score INTEGER NOT NULL,
                priority_score INTEGER NOT NULL,
                queue_eligible INTEGER NOT NULL DEFAULT 1,
                result_json TEXT NOT NULL,
                PRIMARY KEY (run_id, job_id),
                FOREIGN KEY (run_id)
                    REFERENCES decision_runs(run_id)
                    ON DELETE CASCADE,
                FOREIGN KEY (job_id)
                    REFERENCES jobs(job_id)
                    ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_decision_results_rank
            ON decision_results(run_id, queue_eligible, priority_score DESC);

            CREATE INDEX IF NOT EXISTS idx_decision_results_group
            ON decision_results(run_id, action_group, priority_score DESC);
            """
        )
        run_count = int(connection.execute(
            "SELECT COUNT(*) AS count FROM decision_runs"
        ).fetchone()["count"])
        result_count = int(connection.execute(
            "SELECT COUNT(*) AS count FROM decision_results"
        ).fetchone()["count"])

    return {"run_count": run_count, "result_count": result_count}


def _load_jobs(*, db_path: Path) -> list[DecisionCandidate]:
    initialize_decision_schema(db_path)
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
                j.revision,
                j.content_hash,
                j.canonical_json,
                COALESCE(m.user_status, 'to_review') AS user_status,
                COALESCE(m.listing_status, 'unknown') AS listing_status,
                COALESCE(m.quality_override, 'auto') AS quality_override,
                COALESCE(m.category_manual, '') AS category_manual,
                COALESCE(m.notes, '') AS management_notes,
                COALESCE(m.updated_at, '') AS management_updated_at,
                m.archived_at
            FROM jobs AS j
            LEFT JOIN job_management AS m
              ON m.job_id = j.job_id
            WHERE COALESCE(m.quality_override, 'auto') != 'exclude'
              AND m.archived_at IS NULL
              AND COALESCE(m.user_status, 'to_review') NOT IN ('rejected', 'abandoned')
            ORDER BY j.rowid
            """
        ).fetchall()

    result: list[DecisionCandidate] = []
    for row in rows:
        item = dict(row)
        canonical = _parse_json(item.pop("canonical_json"))
        canonical.update(
            {
                "job_id": item["job_id"],
                "job_title": item["job_title"] or canonical.get("job_title", ""),
                "company_name": item["company_name"] or canonical.get("company_name", ""),
                "city": item["city"] or canonical.get("city", ""),
                "salary": item["salary"] or canonical.get("salary", ""),
                "source_url": item["source_url"] or canonical.get("source_url", ""),
                "first_seen_at": item["first_seen_at"],
                "updated_at": item["updated_at"],
                "revision": item["revision"],
                "content_hash": item["content_hash"],
                "user_status": item["user_status"],
                "listing_status": item["listing_status"],
                "quality_override": item["quality_override"],
                "category_manual": item["category_manual"],
                "management_notes": item["management_notes"],
                "management_updated_at": item["management_updated_at"],
            }
        )
        result.append(DecisionCandidate(job_id=str(item["job_id"]), payload=canonical))
    return result


def _skill_definitions() -> list[tuple[str, str, list[str]]]:
    definitions = list(load_skill_definitions())
    existing = {item[0].casefold() for item in definitions}
    extras = [
        ("TypeScript", "技术栈", [r"(?<![a-z0-9])typescript(?![a-z0-9])"]),
        ("SQLite", "技术栈", [r"(?<![a-z0-9])sqlite(?![a-z0-9])"]),
        ("自动化测试", "工程能力", [r"自动化测试", r"单元测试", r"集成测试"]),
        ("模型评估", "AI与统计方法", [r"模型评估", r"滚动回测", r"MAE", r"RMSE"]),
    ]
    for item in extras:
        if item[0].casefold() not in existing:
            definitions.append(item)
    return definitions


def _job_text(record: dict[str, Any]) -> str:
    parts = [
        record.get("job_title"),
        record.get("job_description"),
        record.get("core_text"),
        record.get("job_tags"),
        record.get("role_category_v11"),
        record.get("role_category_v1"),
        record.get("role_secondary_tags"),
        record.get("category_manual"),
        record.get("job_basic_info_raw"),
        record.get("education"),
        record.get("experience"),
        record.get("internship_days_per_week"),
        record.get("internship_duration"),
    ]
    return "\n".join(_text(item) for item in parts if _text(item))


def _project_text(project: dict[str, Any]) -> str:
    return "\n".join(
        item for item in (
            _text(project.get("project_name")),
            _text(project.get("description")),
            _text(project.get("achievements")),
        ) if item
    )


def _profile_context(*, db_path: Path) -> dict[str, Any]:
    profile = get_profile(db_path=db_path)
    skills = list_skills(db_path=db_path)
    projects = list_projects(db_path=db_path)
    locations = list_locations(db_path=db_path)
    preferences = list_preferences(db_path=db_path)

    skill_map = {
        str(item["skill_name"]).casefold(): dict(item)
        for item in skills
    }
    preference_map = {
        str(item["direction"]).casefold(): dict(item)
        for item in preferences
    }

    evidence_map: dict[str, list[dict[str, Any]]] = {}
    for project in projects:
        project_name = _text(project.get("project_name"))
        for evidence in project.get("skills", []):
            skill_name = _text(evidence.get("skill_name"))
            if not skill_name:
                continue
            evidence_map.setdefault(skill_name.casefold(), []).append(
                {
                    "skill_name": skill_name,
                    "project_id": project.get("project_id"),
                    "project_name": project_name,
                    "source": "structured",
                    "strength": evidence.get("evidence_strength", "supporting"),
                    "evidence_text": _text(evidence.get("evidence_text")),
                }
            )

        text = _project_text(project)
        for skill_name, _, patterns in _skill_definitions():
            if any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns):
                evidence_map.setdefault(skill_name.casefold(), []).append(
                    {
                        "skill_name": skill_name,
                        "project_id": project.get("project_id"),
                        "project_name": project_name,
                        "source": "project_text",
                        "strength": "supporting",
                        "evidence_text": "项目文本中明确提及该能力。",
                    }
                )

        for skill_name, patterns in EXTRA_PROJECT_EVIDENCE_PATTERNS.items():
            if any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns):
                evidence_map.setdefault(skill_name.casefold(), []).append(
                    {
                        "skill_name": skill_name,
                        "project_id": project.get("project_id"),
                        "project_name": project_name,
                        "source": "project_inference",
                        "strength": "supporting",
                        "evidence_text": "由项目成果与技术工作推断。",
                    }
                )

    for key, items in evidence_map.items():
        unique: dict[tuple[Any, Any, Any], dict[str, Any]] = {}
        for item in items:
            marker = (item.get("project_id"), item.get("skill_name"), item.get("source"))
            unique[marker] = item
        evidence_map[key] = list(unique.values())

    return {
        "profile": profile,
        "skills": skills,
        "skill_map": skill_map,
        "projects": projects,
        "evidence_map": evidence_map,
        "locations": locations,
        "preferences": preferences,
        "preference_map": preference_map,
    }


def _target_level(context: str) -> float:
    if re.search(r"精通", context, re.IGNORECASE):
        return 1.00
    if re.search(r"熟练|熟悉|掌握", context, re.IGNORECASE):
        return 0.80
    if re.search(r"了解|基础", context, re.IGNORECASE):
        return 0.45
    return 0.55


def _optional_mention(context: str) -> bool:
    optional = any(re.search(pattern, context, re.IGNORECASE) for pattern in OPTIONAL_MARKERS)
    strong = any(re.search(pattern, context, re.IGNORECASE) for pattern in STRONG_REQUIREMENT_MARKERS)
    return optional and not strong


def _skill_mentions(text: str) -> list[SkillMention]:
    mentions: list[SkillMention] = []
    for skill_name, _, patterns in _skill_definitions():
        best: re.Match[str] | None = None
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match is not None and (best is None or match.start() < best.start()):
                best = match
        if best is None:
            continue
        context = text[max(0, best.start() - 42): min(len(text), best.end() + 42)]
        mentions.append(
            SkillMention(
                skill_name=skill_name,
                start=best.start(),
                end=best.end(),
                target_level=_target_level(context),
                optional=_optional_mention(context),
                context=context,
            )
        )
    return sorted(mentions, key=lambda item: (item.start, item.end, item.skill_name))


def _alternative_groups(mentions: list[SkillMention], text: str) -> list[list[SkillMention]]:
    required = [item for item in mentions if not item.optional]
    if not required:
        return []

    parent = list(range(len(required)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left: int, right: int) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    for index in range(len(required) - 1):
        left = required[index]
        right = required[index + 1]
        if right.start - left.end > 20:
            continue
        separator = text[left.end:right.start]
        surrounding = text[max(0, left.start - 12):min(len(text), right.end + 12)]
        if re.search(r"/|／|\b(?:or)\b|或|任选|至少(?:一门|一种|一项)", separator, re.IGNORECASE):
            union(index, index + 1)
        elif re.search(r"至少(?:熟悉|掌握)?.{0,8}(?:一门|一种|一项)", surrounding, re.IGNORECASE):
            union(index, index + 1)

    groups: dict[int, list[SkillMention]] = {}
    for index, mention in enumerate(required):
        groups.setdefault(find(index), []).append(mention)
    return list(groups.values())


def _requirements(record: dict[str, Any]) -> dict[str, Any]:
    text = _job_text(record)
    mentions = _skill_mentions(text)
    groups = _alternative_groups(mentions, text)
    requirements: list[dict[str, Any]] = []
    for group in groups:
        alternatives = []
        for item in group:
            if item.skill_name not in alternatives:
                alternatives.append(item.skill_name)
        requirements.append(
            {
                "alternatives": alternatives,
                "label": " 或 ".join(alternatives),
                "target_level": max(item.target_level for item in group),
                "contexts": [item.context for item in group],
            }
        )

    bonus_skills = []
    for item in mentions:
        if item.optional and item.skill_name not in bonus_skills:
            bonus_skills.append(item.skill_name)

    return {
        "requirements": requirements,
        "bonus_skills": bonus_skills,
        "all_detected_skills": list(dict.fromkeys(item.skill_name for item in mentions)),
    }


def _evidence_for_skill(skill_name: str, context: dict[str, Any]) -> list[dict[str, Any]]:
    direct = list(context["evidence_map"].get(skill_name.casefold(), []))
    for related, factor in RELATED_SKILLS.get(skill_name, {}).items():
        if factor < 0.60:
            continue
        for item in context["evidence_map"].get(related.casefold(), []):
            enriched = dict(item)
            enriched["related_skill"] = related
            enriched["relation_factor"] = factor
            direct.append(enriched)
    return direct


def _raw_skill_score(skill_name: str, context: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    skill = context["skill_map"].get(skill_name.casefold())
    direct_score = PROFICIENCY_WEIGHTS.get(str(skill.get("proficiency_level")), 0.0) if skill else 0.0
    evidence = _evidence_for_skill(skill_name, context)
    evidence_score = 0.0
    for item in evidence:
        strength = 0.78 if item.get("strength") == "strong" else 0.66
        if item.get("source") == "project_inference":
            strength = 0.62
        strength *= float(item.get("relation_factor", 1.0))
        evidence_score = max(evidence_score, strength)

    related_score = 0.0
    related_source = ""
    for related, factor in RELATED_SKILLS.get(skill_name, {}).items():
        related_skill = context["skill_map"].get(related.casefold())
        if related_skill:
            candidate = PROFICIENCY_WEIGHTS.get(str(related_skill.get("proficiency_level")), 0.0) * factor
            if candidate > related_score:
                related_score = candidate
                related_source = related

    raw = max(direct_score, evidence_score, related_score)
    if direct_score > 0 and evidence:
        raw = min(1.0, raw + 0.12)

    return raw, {
        "skill_name": skill_name,
        "profile_level": skill.get("proficiency_level") if skill else None,
        "direct_score": round(direct_score, 4),
        "evidence_score": round(evidence_score, 4),
        "related_score": round(related_score, 4),
        "related_source": related_source or None,
        "raw_score": round(raw, 4),
        "evidence": evidence[:5],
    }


def _skill_assessment(requirement_data: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    requirements = requirement_data["requirements"]
    if not requirements:
        return {
            "skill_score": 55,
            "skill_coverage": 0.0,
            "matched_skills": [],
            "partial_skills": [],
            "skill_gaps": [],
            "alternative_satisfied": [],
            "requirement_details": [],
            "evidence_score": 35 if context["projects"] else 15,
            "relevant_evidence_count": 0,
        }

    details: list[dict[str, Any]] = []
    matched: list[str] = []
    partial: list[str] = []
    gaps: list[str] = []
    alternative_satisfied: list[str] = []
    normalized_scores: list[float] = []
    evidence_hit_count = 0

    for requirement in requirements:
        target = max(0.30, float(requirement["target_level"]))
        alternatives = []
        for skill_name in requirement["alternatives"]:
            raw, skill_detail = _raw_skill_score(skill_name, context)
            normalized = min(1.0, raw / target) if target else raw
            skill_detail["target_level"] = round(target, 4)
            skill_detail["normalized_score"] = round(normalized, 4)
            alternatives.append(skill_detail)

        best = max(alternatives, key=lambda item: item["normalized_score"])
        best_score = float(best["normalized_score"])
        normalized_scores.append(best_score)
        if best.get("evidence"):
            evidence_hit_count += 1

        label = requirement["label"]
        if best_score >= 0.75:
            matched.append(str(best["skill_name"]))
        elif best_score >= 0.45:
            partial.append(label)
        else:
            gaps.append(label)

        if len(requirement["alternatives"]) > 1 and best_score >= 0.45:
            alternative_satisfied.append(
                f"{label}：由 {best['skill_name']} 满足"
            )

        details.append(
            {
                "label": label,
                "target_level": round(target, 4),
                "best_alternative": best["skill_name"],
                "best_score": round(best_score, 4),
                "alternatives": alternatives,
            }
        )

    skill_score = 100 * sum(normalized_scores) / len(normalized_scores)
    coverage = sum(1 for value in normalized_scores if value >= 0.75) / len(normalized_scores)
    evidence_score = 100 * evidence_hit_count / len(requirements)

    return {
        "skill_score": _score(skill_score),
        "skill_coverage": round(coverage, 4),
        "matched_skills": matched,
        "partial_skills": partial,
        "skill_gaps": gaps,
        "alternative_satisfied": alternative_satisfied,
        "requirement_details": details,
        "evidence_score": _score(evidence_score),
        "relevant_evidence_count": evidence_hit_count,
    }


def _direction(record: dict[str, Any]) -> str:
    for key in ("category_manual", "role_category_v11", "role_category_v1", "role_category"):
        value = _text(record.get(key))
        if value:
            for canonical, patterns in ROLE_PATTERNS.items():
                if canonical in value or any(re.search(pattern, value, re.IGNORECASE) for pattern in patterns):
                    return canonical
            return value

    text = _job_text(record)
    for canonical, patterns in ROLE_PATTERNS.items():
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns):
            return canonical
    return "其他"


def _direction_score(direction: str, context: dict[str, Any]) -> tuple[int, str]:
    best_score = 55.0
    best_source = "未设置直接对应的方向偏好"
    direction_text = direction.casefold()
    for item in context["preferences"]:
        preference = _text(item.get("direction"))
        if not preference:
            continue
        preference_text = preference.casefold()
        direct = preference_text in direction_text or direction_text in preference_text
        pattern_overlap = False
        for canonical, patterns in ROLE_PATTERNS.items():
            if canonical.casefold() in preference_text and canonical.casefold() in direction_text:
                pattern_overlap = True
                break
            if any(re.search(pattern, preference, re.IGNORECASE) for pattern in patterns) and any(
                re.search(pattern, direction, re.IGNORECASE) for pattern in patterns
            ):
                pattern_overlap = True
                break
        if direct or pattern_overlap:
            score = 100 * INTEREST_WEIGHTS.get(str(item.get("interest_level")), 0.55)
            if score > best_score:
                best_score = score
                best_source = f"方向偏好：{preference}"
    return _score(best_score), best_source


def _education_rank(value: Any) -> int | None:
    text = _text(value)
    if not text or "不限" in text:
        return None
    for label, rank in sorted(EDUCATION_RANK.items(), key=lambda item: len(item[0]), reverse=True):
        if label in text:
            return rank
    return None


def _first_weekly_days(record: dict[str, Any]) -> int | None:
    text = " ".join(
        _text(record.get(key))
        for key in (
            "internship_days_per_week", "experience", "education",
            "job_basic_info_raw", "job_description",
        )
    )
    match = re.search(r"([1-7])\s*天\s*(?:/|／|每)?\s*周", text)
    return int(match.group(1)) if match else None


def _required_months(record: dict[str, Any]) -> int | None:
    text = " ".join(
        _text(record.get(key))
        for key in (
            "internship_duration", "experience", "education",
            "job_basic_info_raw", "job_description",
        )
    )
    matches = [
        int(item)
        for item in re.findall(
            r"(?:连续|至少|实习|可实习|保证)?\s*(\d{1,2})\s*个(?:月|月份)",
            text,
        )
    ]
    sensible = [item for item in matches if 1 <= item <= 36]
    return max(sensible) if sensible else None


def _graduation_years(record: dict[str, Any]) -> list[int]:
    text = _job_text(record)
    return sorted({int(item) for item in re.findall(r"(20\d{2})\s*届", text)})


def _job_type(record: dict[str, Any]) -> str:
    text = _job_text(record)
    title = _text(record.get("job_title"))
    if re.search(r"研究助理|科研助理|\bRA\b", text, re.IGNORECASE):
        return "research_assistant"
    if "实习" in title or re.search(r"实习生|日常实习|暑期实习", text):
        return "internship"
    if re.search(r"兼职|项目制", text):
        return "part_time"
    return "full_time"


def _hard_and_soft_constraints(record: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    profile = context["profile"]
    hard: list[str] = []
    soft: list[str] = []

    hard_cities = {
        _text(item.get("city")).casefold()
        for item in context["locations"]
        if item.get("constraint_level") == "hard" and _text(item.get("city"))
    }
    city = _text(record.get("city")).casefold()
    remote_job = bool(re.search(r"远程|居家", _job_text(record)))
    if hard_cities and city and not remote_job and not any(
        allowed in city or city in allowed for allowed in hard_cities
    ):
        hard.append("岗位城市不在硬性可接受城市中")

    user_rank = _education_rank(profile.get("education"))
    required_rank = _education_rank(record.get("education") or _job_text(record))
    if user_rank is not None and required_rank is not None and required_rank > user_rank:
        hard.append("学历要求高于当前学历")

    required_days = _first_weekly_days(record)
    max_days = profile.get("max_days_per_week")
    if required_days is not None and max_days is not None:
        try:
            if required_days > int(max_days):
                hard.append(f"岗位要求每周{required_days}天，超过当前最多{max_days}天")
        except (TypeError, ValueError):
            pass

    required_months = _required_months(record)
    max_months = profile.get("max_internship_months")
    if required_months is not None and max_months is not None:
        try:
            if required_months > int(max_months):
                hard.append(f"岗位要求至少{required_months}个月，超过当前最长{max_months}个月")
        except (TypeError, ValueError):
            pass

    user_graduation = profile.get("graduation_year")
    years = _graduation_years(record)
    if user_graduation and years and int(user_graduation) not in years:
        restrictive = bool(re.search(r"仅限|面向|要求|招聘", _job_text(record)))
        if restrictive:
            hard.append(f"岗位面向{'/'.join(map(str, years))}届，与当前毕业年份不符")
        else:
            soft.append("岗位提到的毕业年份与当前年份不同")

    target_types = set(profile.get("target_job_types") or [])
    current_type = _job_type(record)
    if target_types:
        type_match = (
            (current_type == "internship" and bool(target_types & {"summer_internship", "daily_internship"}))
            or (current_type == "research_assistant" and "research_assistant" in target_types)
            or (current_type == "full_time" and "full_time" in target_types)
            or (current_type == "part_time" and "part_time" in target_types)
        )
        if not type_match:
            soft.append("岗位类型不在当前主要求职类型中")

    salary_value, salary_unit = _salary_value(record.get("salary"))
    if salary_value is not None:
        if salary_unit == "daily" and profile.get("minimum_daily_salary"):
            if salary_value < float(profile["minimum_daily_salary"]):
                soft.append("岗位日薪低于当前最低期望")
        if salary_unit == "monthly" and profile.get("minimum_monthly_salary"):
            if salary_value < float(profile["minimum_monthly_salary"]):
                soft.append("岗位月薪低于当前最低期望")

    listing_status = _text(record.get("listing_status")) or "unknown"
    if listing_status == "closed":
        hard.append("岗位已关闭")
    elif listing_status == "suspected_inactive":
        soft.append("岗位疑似失效")

    return {
        "hard_conflicts": list(dict.fromkeys(hard)),
        "soft_risks": list(dict.fromkeys(soft)),
        "required_days": required_days,
        "required_months": required_months,
        "job_type": current_type,
    }


def _missing_fields(record: dict[str, Any]) -> list[str]:
    fields = [
        ("岗位名称", record.get("job_title")),
        ("公司", record.get("company_name") or record.get("company_full_name") or record.get("company_short_name")),
        ("城市", record.get("city")),
        ("薪资", record.get("salary")),
        ("学历", record.get("education")),
        ("岗位描述", record.get("job_description") or record.get("core_text")),
    ]
    return [label for label, value in fields if not _text(value)]


def _information_risks(record: dict[str, Any], requirement_data: dict[str, Any]) -> list[str]:
    text = _job_text(record)
    title = _text(record.get("job_title"))
    risks: list[str] = []

    junior_title = bool(re.search(r"实习|无经验|应届|可培养|大二|大三", title))
    senior_hits = [pattern for pattern in SENIOR_MARKERS if re.search(pattern, text, re.IGNORECASE)]
    if junior_title and len(senior_hits) >= 2:
        risks.append("岗位标题偏初级，但正文包含明显资深职责或要求")

    if len(text) > 800 and not any(re.search(pattern, text) for pattern in RESPONSIBILITY_MARKERS):
        risks.append("职位描述较长，但缺少清晰的岗位职责结构")

    title_is_technical = bool(re.search(r"AI|数据|算法|开发|分析|预测", title, re.IGNORECASE))
    detected_count = len(requirement_data["all_detected_skills"])
    if title_is_technical and not detected_count:
        risks.append("技术岗位标题与正文中的技能信息不充分")
    elif (
        title_is_technical
        and detected_count <= 2
        and len(text) > 500
        and not any(re.search(pattern, text) for pattern in RESPONSIBILITY_MARKERS)
    ):
        risks.append("岗位正文以公司介绍为主，具体职责和技能要求不足")

    salary_value, salary_unit = _salary_value(record.get("salary"))
    if "实习" in title and salary_unit == "monthly" and salary_value and salary_value >= 15000:
        risks.append("实习岗位薪资显著偏高，需要核实职位定位")

    if re.search(r"无经验|可培养", title) and re.search(r"负责人|架构|主导|专家", text):
        risks.append("“无经验可培养”与负责人或架构职责不一致")

    return list(dict.fromkeys(risks))


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


def _percentile_stats(candidates: list[DecisionCandidate]) -> dict[str, list[float]]:
    values: dict[str, list[float]] = {"daily": [], "monthly": [], "unknown": []}
    for candidate in candidates:
        value, unit = _salary_value(candidate.payload.get("salary"))
        if value is not None:
            values.setdefault(unit, []).append(value)
    return {key: sorted(items) for key, items in values.items()}


def _salary_percentile(record: dict[str, Any], stats: dict[str, list[float]]) -> int:
    value, unit = _salary_value(record.get("salary"))
    if value is None:
        return 50
    peers = stats.get(unit, [])
    if len(peers) < 2:
        return 55
    below = sum(1 for item in peers if item < value)
    equal = sum(1 for item in peers if item == value)
    percentile = (below + 0.5 * equal) / len(peers)
    return _score(25 + 65 * percentile)


def _growth_score(record: dict[str, Any]) -> tuple[int, list[str], list[str]]:
    text = _job_text(record)
    positives = [pattern for pattern in POSITIVE_GROWTH_PATTERNS if re.search(pattern, text, re.IGNORECASE)]
    negatives = [pattern for pattern in LOW_GROWTH_PATTERNS if re.search(pattern, text, re.IGNORECASE)]
    value = 50 + min(38, 7 * len(positives)) - min(40, 11 * len(negatives))
    title = _text(record.get("job_title"))
    if re.search(r"数据采集|数据标注|数据录入", title) and len(positives) <= 1:
        value -= 18
        negatives.append("title_low_growth")
    return _score(value), positives, negatives


def _parse_timestamp(value: Any) -> datetime | None:
    text = _text(value)
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def _urgency_score(record: dict[str, Any]) -> int:
    listing = _text(record.get("listing_status")) or "unknown"
    base = {"active": 75, "unknown": 55, "suspected_inactive": 20, "closed": 0}.get(listing, 50)
    updated = _parse_timestamp(record.get("updated_at"))
    if updated:
        age_days = max(0, (datetime.now(timezone.utc) - updated).days)
        if age_days <= 7:
            base += 15
        elif age_days <= 30:
            base += 5
        elif age_days > 120:
            base -= 10
    if record.get("user_status") == "interested":
        base += 5
    return _score(base)


def _city_preference_score(record: dict[str, Any], context: dict[str, Any]) -> int:
    city = _text(record.get("city")).casefold()
    if not city:
        return 50
    best = 50
    for item in context["locations"]:
        preference_city = _text(item.get("city")).casefold()
        if preference_city and (preference_city in city or city in preference_city):
            level = item.get("constraint_level")
            best = max(best, {"hard": 100, "important": 85, "preference": 72}.get(level, 60))
    return best


RARE_DOMAIN_PATTERNS = {
    "足球": r"足球|赛事",
    "体育": r"体育|运动分析",
    "赔率": r"赔率|盘口|投注",
    "xG": r"\bxg\b|预期进球",
    "招聘市场": r"招聘市场|岗位采集|求职决策",
    "浏览器扩展": r"浏览器扩展|Chrome扩展",
}


def _domain_project_match(record: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    job_text = _job_text(record)
    job_domains = {
        label
        for label, pattern in RARE_DOMAIN_PATTERNS.items()
        if re.search(pattern, job_text, re.IGNORECASE)
    }
    if not job_domains:
        return {"score": 0, "domains": [], "projects": []}

    projects: list[str] = []
    matched_domains: set[str] = set()
    for project in context["projects"]:
        text = _project_text(project)
        overlap = {
            label
            for label in job_domains
            if re.search(RARE_DOMAIN_PATTERNS[label], text, re.IGNORECASE)
        }
        if overlap:
            matched_domains.update(overlap)
            projects.append(_text(project.get("project_name")))

    score = min(100, 55 + 20 * len(matched_domains)) if matched_domains else 0
    return {
        "score": score,
        "domains": sorted(matched_domains),
        "projects": list(dict.fromkeys(projects)),
    }


def _project_recommendations(
    requirement_data: dict[str, Any],
    context: dict[str, Any],
) -> list[dict[str, Any]]:
    required_names = {
        name.casefold()
        for requirement in requirement_data["requirements"]
        for name in requirement["alternatives"]
    }
    ranked: list[tuple[int, dict[str, Any], list[str]]] = []
    for project in context["projects"]:
        project_skills = {
            _text(item.get("skill_name")).casefold()
            for item in project.get("skills", [])
            if _text(item.get("skill_name"))
        }
        project_text = _project_text(project)
        inferred = {
            name.casefold()
            for name, _, patterns in _skill_definitions()
            if any(re.search(pattern, project_text, re.IGNORECASE) for pattern in patterns)
        }
        all_project_skills = project_skills | inferred
        overlap = sorted(required_names & all_project_skills)
        score = len(overlap)
        if score:
            ranked.append((score, project, overlap))

    ranked.sort(key=lambda item: (-item[0], -int(item[1].get("project_status") == "completed"), int(item[1].get("project_id", 0))))
    return [
        {
            "project_id": project.get("project_id"),
            "project_name": project.get("project_name"),
            "matched_skill_count": score,
            "matched_skills": overlap,
            "suggestion": f"简历优先突出“{project.get('project_name')}”中的相关技术与可验证成果。",
        }
        for score, project, overlap in ranked[:2]
    ]


def _group_action(
    *,
    strategy: str,
    priority: int,
    match_score: int,
    opportunity_score: int,
    evidence_score: int,
    skill_gaps: list[str],
    hard_conflicts: list[str],
    information_risks: list[str],
    soft_risks: list[str],
    listing_status: str,
    growth_score: int,
    domain_match_score: int,
) -> tuple[str, str]:
    config = STRATEGY_CONFIG[strategy]
    if hard_conflicts:
        return "defer", "存在明确硬条件冲突。"
    if listing_status in {"closed", "suspected_inactive"}:
        return "defer", "岗位已关闭或疑似失效。"
    severe_information_risk = any(
        "不一致" in item or "明显资深职责" in item
        for item in information_risks
    )
    if severe_information_risk or (len(information_risks) >= 2 and opportunity_score < 65):
        return "defer", "岗位信息存在明显矛盾或可信度风险。"
    if information_risks and match_score < 40:
        return "defer", "岗位具体职责或要求不足，且当前直接匹配较低。"
    if growth_score <= 40 and any("重复采集" in item or "成长价值较低" in item for item in soft_risks):
        return "defer", "岗位以重复采集、录入或基础维护为主，成长价值较低。"
    if any("高门槛业务分析" in item for item in soft_risks):
        return "stretch", "岗位业务分析要求较高，适合作为高价值冲刺目标。"
    if any("研发深度" in item or "材料与报告" in item for item in soft_risks):
        return "prepare_first", "岗位值得考虑，但应先补齐研发深度或材料型能力证据。"
    if domain_match_score >= 70 and priority >= 64 and match_score >= 65:
        return "apply_now", "现有项目与岗位业务领域直接对应，领域证据足以支持立即投递。"

    allowed_gap_count = 3 if domain_match_score >= 70 else 2
    if (
        priority >= config["apply_priority"]
        and match_score >= config["apply_match"]
        and evidence_score >= config["apply_evidence"]
        and len(skill_gaps) <= allowed_gap_count
    ):
        return "apply_now", "匹配度、证据和机会价值达到当前策略的直接投递阈值。"

    if (
        priority >= config["stretch_priority"]
        and match_score >= config["stretch_match"]
        and opportunity_score >= config["stretch_opportunity"]
    ):
        if len(skill_gaps) >= 3 and evidence_score < 35:
            return "prepare_first", "岗位值得尝试，但核心技能缺口和项目证据不足。"
        return "stretch", "机会价值较高，存在可接受的能力缺口，值得直接冲刺。"

    if priority >= config["prepare_priority"] and (match_score >= 35 or opportunity_score >= 50):
        return "prepare_first", "具备部分匹配基础，但需要补材料、证据或关键技能后再投。"

    return "defer", "当前匹配、价值或信息质量不足，暂不占用优先投递时间。"


def _decision_reasons(
    *,
    direction: str,
    direction_score: int,
    skill_assessment: dict[str, Any],
    opportunity_score: int,
    salary_percentile: int,
    growth_score: int,
    listing_status: str,
    project_recommendations: list[dict[str, Any]],
) -> list[str]:
    reasons: list[str] = []
    if direction_score >= 75:
        reasons.append(f"岗位方向“{direction}”与当前求职偏好一致。")
    if skill_assessment["skill_score"] >= 70:
        reasons.append("核心技能要求覆盖较好。")
    if skill_assessment["evidence_score"] >= 50:
        reasons.append("已有项目能够为多项岗位技能提供证据。")
    if skill_assessment["alternative_satisfied"]:
        reasons.append(skill_assessment["alternative_satisfied"][0] + "。")
    if salary_percentile >= 70:
        reasons.append("薪资位于当前同口径岗位样本的较高区间。")
    if growth_score >= 68:
        reasons.append("职责包含真实分析、研发、决策支持或完整项目交付。")
    if listing_status == "active":
        reasons.append("岗位已人工确认仍在招聘。")
    if project_recommendations:
        reasons.append(f"可使用“{project_recommendations[0]['project_name']}”作为主要简历证据。")
    if not reasons and opportunity_score >= 55:
        reasons.append("岗位综合价值处于可考虑区间。")
    return reasons[:5]


def _suggested_action(
    action_group: str,
    gaps: list[str],
    projects: list[dict[str, Any]],
    hard_conflicts: list[str],
) -> str:
    project_name = projects[0]["project_name"] if projects else "最相关项目"
    if action_group == "apply_now":
        return f"今天投递，简历优先突出“{project_name}”及其中的可验证成果。"
    if action_group == "stretch":
        gap_text = "、".join(gaps[:2]) if gaps else "岗位业务场景"
        return f"直接投递，同时针对{gap_text}准备面试说明，突出“{project_name}”。"
    if action_group == "prepare_first":
        gap_text = "、".join(gaps[:3]) if gaps else "项目证据和岗位定制内容"
        return f"先补充{gap_text}的简历证据或小型Demo，再完成针对性投递。"
    if hard_conflicts:
        return "先确认硬条件是否可以协商；不能协商则不投入额外准备时间。"
    return "暂缓投递，仅在岗位信息更新或个人条件变化后重新评估。"


def _calculate_one(
    candidate: DecisionCandidate,
    *,
    context: dict[str, Any],
    salary_stats: dict[str, list[float]],
    strategy: str,
) -> dict[str, Any]:
    record = candidate.payload
    requirement_data = _requirements(record)
    skills = _skill_assessment(requirement_data, context)
    direction = _direction(record)
    direction_score, direction_source = _direction_score(direction, context)
    constraints = _hard_and_soft_constraints(record, context)
    missing = _missing_fields(record)
    info_risks = _information_risks(record, requirement_data)
    domain_match = _domain_project_match(record, context)

    title_and_text = _job_text(record)
    high_depth_gaps = {
        "大模型/LLM", "RAG", "向量数据库", "模型训练", "模型部署",
        "深度学习", "PyTorch", "TensorFlow",
    }
    if (
        re.search(r"研发|算法", _text(record.get("job_title")), re.IGNORECASE)
        and any(any(name in gap for name in high_depth_gaps) for gap in skills["skill_gaps"])
    ):
        constraints["soft_risks"].append("岗位研发深度高于当前直接项目证据")

    if (
        re.search(r"项目实习|资料整理|报告撰写|Office|PPT", title_and_text, re.IGNORECASE)
        and any(any(name in gap for name in ("报告撰写", "Excel", "跨团队协作")) for gap in skills["skill_gaps"])
    ):
        constraints["soft_risks"].append("材料与报告型岗位需要定制化能力证据")

    advanced_business_markers = sum(
        bool(re.search(pattern, title_and_text, re.IGNORECASE))
        for pattern in (
            r"精通\s*SQL", r"A/B\s*实验", r"经营分析|策略分析",
            r"相关实习经验.*优先", r"业务增长|决策支持",
        )
    )
    if advanced_business_markers >= 2:
        constraints["soft_risks"].append("高门槛业务分析岗位更适合作为冲刺目标")

    growth_preview, _, low_growth_preview = _growth_score(record)
    if growth_preview <= 35 and len(low_growth_preview) >= 2:
        constraints["soft_risks"].append("重复采集或基础维护工作占比高，成长价值较低")

    constraints["soft_risks"] = list(dict.fromkeys(constraints["soft_risks"]))

    feasibility = 100 - 18 * len(constraints["soft_risks"]) - 9 * len(missing)
    if constraints["hard_conflicts"]:
        feasibility = min(feasibility, 18)
    feasibility_score = _score(feasibility)

    effective_evidence_score = _score(
        max(skills["evidence_score"], 0.80 * domain_match["score"])
    )
    match_score = _score(
        0.45 * skills["skill_score"]
        + 0.20 * effective_evidence_score
        + 0.15 * direction_score
        + 0.20 * feasibility_score
        + (6 if domain_match["score"] >= 70 else 0)
    )

    salary_percentile = _salary_percentile(record, salary_stats)
    growth_score, growth_hits, low_growth_hits = _growth_score(record)
    clarity_score = _score(100 - 12 * len(missing) - 22 * len(info_risks))
    listing_status = _text(record.get("listing_status")) or "unknown"
    listing_confidence = {"active": 90, "unknown": 60, "suspected_inactive": 25, "closed": 0}.get(listing_status, 50)
    opportunity_score = _score(
        0.20 * salary_percentile
        + 0.30 * growth_score
        + 0.20 * clarity_score
        + 0.20 * direction_score
        + 0.10 * listing_confidence
    )

    urgency_score = _urgency_score(record)
    city_score = _city_preference_score(record, context)
    preference_score = _score(0.72 * direction_score + 0.18 * city_score + 0.10 * salary_percentile)

    gap_ratio = len(skills["skill_gaps"]) / max(1, len(requirement_data["requirements"]))
    partial_ratio = len(skills["partial_skills"]) / max(1, len(requirement_data["requirements"]))
    preparation_cost = _score(
        15
        + 58 * gap_ratio
        + 22 * partial_ratio
        + (18 if skills["evidence_score"] < 30 else 0)
    )
    uncertainty_score = _score(
        12 * len(missing)
        + 22 * len(info_risks)
        + (10 if listing_status == "unknown" else 0)
    )

    config = STRATEGY_CONFIG[strategy]
    weights = config["weights"]
    priority_score = _score(
        weights["match"] * match_score
        + weights["opportunity"] * opportunity_score
        + weights["urgency"] * urgency_score
        + weights["preference"] * preference_score
        - config["prep_penalty"] * preparation_cost
        - config["uncertainty_penalty"] * uncertainty_score
    )

    action_group, group_reason = _group_action(
        strategy=strategy,
        priority=priority_score,
        match_score=match_score,
        opportunity_score=opportunity_score,
        evidence_score=effective_evidence_score,
        skill_gaps=skills["skill_gaps"],
        hard_conflicts=constraints["hard_conflicts"],
        information_risks=info_risks,
        soft_risks=constraints["soft_risks"],
        listing_status=listing_status,
        growth_score=growth_score,
        domain_match_score=domain_match["score"],
    )

    user_status = _text(record.get("user_status")) or "to_review"
    queue_eligible = user_status in PENDING_USER_STATUSES and listing_status != "closed"
    queue_exclusion_reason = ""
    if user_status in IN_PROCESS_USER_STATUSES:
        queue_exclusion_reason = "岗位已进入投递、笔试、面试或Offer流程。"
    elif user_status not in PENDING_USER_STATUSES:
        queue_exclusion_reason = "岗位当前不属于待投递队列。"
    elif listing_status == "closed":
        queue_exclusion_reason = "岗位已关闭。"

    project_recommendations = _project_recommendations(requirement_data, context)
    reason_skill_assessment = dict(skills)
    reason_skill_assessment["evidence_score"] = effective_evidence_score
    reasons = _decision_reasons(
        direction=direction,
        direction_score=direction_score,
        skill_assessment=reason_skill_assessment,
        opportunity_score=opportunity_score,
        salary_percentile=salary_percentile,
        growth_score=growth_score,
        listing_status=listing_status,
        project_recommendations=project_recommendations,
    )

    risks = list(dict.fromkeys(
        constraints["hard_conflicts"]
        + constraints["soft_risks"]
        + info_risks
        + (["缺少关键信息：" + "、".join(missing)] if missing else [])
        + (["技能缺口：" + "、".join(skills["skill_gaps"][:4])] if skills["skill_gaps"] else [])
    ))

    salary_value, salary_unit = _salary_value(record.get("salary"))
    result = {
        "engine_version": ENGINE_VERSION,
        "strategy": strategy,
        "job_id": candidate.job_id,
        "job_title": _text(record.get("job_title")),
        "company_name": _text(
            record.get("company_name")
            or record.get("company_full_name")
            or record.get("company_short_name")
        ),
        "city": _text(record.get("city")),
        "salary": _text(record.get("salary")),
        "source_url": _text(record.get("source_url")),
        "user_status": user_status,
        "listing_status": listing_status,
        "queue_eligible": queue_eligible,
        "queue_exclusion_reason": queue_exclusion_reason,
        "action_group": action_group,
        "action_group_label": ACTION_GROUP_LABELS[action_group],
        "action_reason": group_reason,
        "match_score": match_score,
        "opportunity_score": opportunity_score,
        "priority_score": priority_score,
        "components": {
            "skill_fit": skills["skill_score"],
            "project_evidence": effective_evidence_score,
            "domain_project_match": domain_match["score"],
            "direction_fit": direction_score,
            "feasibility": feasibility_score,
            "salary_relative": salary_percentile,
            "growth_value": growth_score,
            "role_clarity": clarity_score,
            "listing_confidence": listing_confidence,
            "urgency": urgency_score,
            "preference": preference_score,
            "preparation_cost": preparation_cost,
            "uncertainty": uncertainty_score,
        },
        "direction": direction,
        "direction_source": direction_source,
        "requirements": requirement_data["requirements"],
        "bonus_skills": requirement_data["bonus_skills"],
        "matched_skills": skills["matched_skills"],
        "partial_skills": skills["partial_skills"],
        "skill_gaps": skills["skill_gaps"],
        "alternative_satisfied": skills["alternative_satisfied"],
        "requirement_details": skills["requirement_details"],
        "hard_conflicts": constraints["hard_conflicts"],
        "soft_risks": constraints["soft_risks"],
        "information_risks": info_risks,
        "missing_fields": missing,
        "reasons": reasons,
        "risks": risks,
        "resume_projects": project_recommendations,
        "suggested_action": _suggested_action(
            action_group,
            skills["skill_gaps"],
            project_recommendations,
            constraints["hard_conflicts"],
        ),
        "diagnostics": {
            "skill_coverage": skills["skill_coverage"],
            "relevant_evidence_count": skills["relevant_evidence_count"],
            "growth_positive_hits": len(growth_hits),
            "growth_low_value_hits": len(low_growth_hits),
            "salary_value": salary_value,
            "salary_unit": salary_unit,
            "required_days": constraints["required_days"],
            "required_months": constraints["required_months"],
            "job_type": constraints["job_type"],
            "domain_match": domain_match,
        },
    }
    return result


def _input_payload(candidates: list[DecisionCandidate], context: dict[str, Any]) -> dict[str, Any]:
    return {
        "engine_version": ENGINE_VERSION,
        "jobs": [
            {
                "job_id": item.job_id,
                "revision": item.payload.get("revision"),
                "content_hash": item.payload.get("content_hash"),
                "updated_at": item.payload.get("updated_at"),
                "user_status": item.payload.get("user_status"),
                "listing_status": item.payload.get("listing_status"),
                "quality_override": item.payload.get("quality_override"),
                "category_manual": item.payload.get("category_manual"),
                "management_updated_at": item.payload.get("management_updated_at"),
            }
            for item in candidates
        ],
        "profile": context["profile"],
        "skills": context["skills"],
        "projects": context["projects"],
        "locations": context["locations"],
        "preferences": context["preferences"],
    }


def _latest_run(strategy: str, *, db_path: Path) -> dict[str, Any] | None:
    initialize_decision_schema(db_path)
    with connect(db_path) as connection:
        row = connection.execute(
            """
            SELECT * FROM decision_runs
            WHERE strategy = ?
            ORDER BY run_id DESC
            LIMIT 1
            """,
            (strategy,),
        ).fetchone()
    return dict(row) if row else None


def _calibration_rows(*, db_path: Path) -> list[dict[str, Any]]:
    initialize_calibration_schema(db_path)
    with connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT
                s.sample_order,
                s.job_id,
                l.action_group,
                l.reason
            FROM decision_calibration_sample AS s
            JOIN decision_calibration_labels AS l
              ON l.job_id = s.job_id
            ORDER BY s.sample_order
            """
        ).fetchall()
    return [dict(row) for row in rows]


def _calibration_metrics(
    result_map: dict[str, dict[str, Any]],
    *,
    db_path: Path,
) -> dict[str, Any]:
    labels = _calibration_rows(db_path=db_path)
    compared: list[dict[str, Any]] = []
    exact = 0
    adjacent = 0
    hard_conflict_misses = 0

    for label in labels:
        result = result_map.get(str(label["job_id"]))
        if not result:
            continue
        manual = str(label["action_group"])
        predicted = str(result["action_group"])
        distance = abs(ACTION_ORDER[manual] - ACTION_ORDER[predicted])
        exact += int(distance == 0)
        adjacent += int(distance <= 1)
        if result["hard_conflicts"] and predicted != "defer":
            hard_conflict_misses += 1
        compared.append(
            {
                "sample_order": int(label["sample_order"]),
                "job_id": label["job_id"],
                "job_title": result["job_title"],
                "company_name": result["company_name"],
                "manual_group": manual,
                "manual_group_label": ACTION_GROUP_LABELS[manual],
                "manual_reason": label["reason"],
                "predicted_group": predicted,
                "predicted_group_label": ACTION_GROUP_LABELS[predicted],
                "priority_score": result["priority_score"],
                "distance": distance,
                "matched": distance == 0,
                "engine_reason": result["action_reason"],
            }
        )

    count = len(compared)
    manual_top = {
        item["job_id"]
        for item in sorted(
            compared,
            key=lambda item: (-ACTION_ORDER[item["manual_group"]], item["sample_order"]),
        )[:5]
    }
    predicted_top = {
        item["job_id"]
        for item in sorted(compared, key=lambda item: (-item["priority_score"], item["sample_order"]))[:5]
    }

    return {
        "label_count": count,
        "exact_match_count": exact,
        "exact_accuracy": round(exact / count, 4) if count else None,
        "adjacent_match_count": adjacent,
        "adjacent_accuracy": round(adjacent / count, 4) if count else None,
        "top5_overlap_count": len(manual_top & predicted_top) if count else 0,
        "top5_overlap_rate": round(len(manual_top & predicted_top) / max(1, min(5, count)), 4) if count else None,
        "hard_conflict_misses": hard_conflict_misses,
        "disagreements": [item for item in compared if not item["matched"]],
        "items": compared,
        "note": "人工标签只用于校验和解释差异，不会被直接写入岗位分数。",
    }


def recalculate_decisions(
    *,
    strategy: str = DEFAULT_STRATEGY,
    db_path: Path = DB_PATH,
) -> dict[str, Any]:
    strategy = _validate_strategy(strategy)
    initialize_decision_schema(db_path)
    candidates = _load_jobs(db_path=db_path)
    context = _profile_context(db_path=db_path)
    salary_stats = _percentile_stats(candidates)
    input_hash = _json_hash(_input_payload(candidates, context))

    results = [
        _calculate_one(
            candidate,
            context=context,
            salary_stats=salary_stats,
            strategy=strategy,
        )
        for candidate in candidates
    ]
    results.sort(key=lambda item: (-item["priority_score"], -item["match_score"], item["job_id"]))
    result_map = {item["job_id"]: item for item in results}
    calibration = _calibration_metrics(result_map, db_path=db_path)
    now = utc_now()

    with connect(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO decision_runs (
                strategy,
                engine_version,
                input_hash,
                created_at,
                job_count,
                queue_count,
                exact_accuracy,
                adjacent_accuracy,
                calibration_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                strategy,
                ENGINE_VERSION,
                input_hash,
                now,
                len(results),
                sum(1 for item in results if item["queue_eligible"]),
                calibration["exact_accuracy"],
                calibration["adjacent_accuracy"],
                calibration["label_count"],
            ),
        )
        run_id = int(cursor.lastrowid)
        connection.executemany(
            """
            INSERT INTO decision_results (
                run_id,
                job_id,
                action_group,
                match_score,
                opportunity_score,
                priority_score,
                queue_eligible,
                result_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    item["job_id"],
                    item["action_group"],
                    item["match_score"],
                    item["opportunity_score"],
                    item["priority_score"],
                    int(item["queue_eligible"]),
                    _json_dumps(item),
                )
                for item in results
            ],
        )

        old_rows = connection.execute(
            """
            SELECT run_id FROM decision_runs
            WHERE strategy = ?
            ORDER BY run_id DESC
            LIMIT -1 OFFSET 20
            """,
            (strategy,),
        ).fetchall()
        if old_rows:
            connection.executemany(
                "DELETE FROM decision_runs WHERE run_id = ?",
                [(int(row["run_id"]),) for row in old_rows],
            )

    return {
        "ok": True,
        "run_id": run_id,
        "strategy": strategy,
        "strategy_label": STRATEGY_LABELS[strategy],
        "engine_version": ENGINE_VERSION,
        "created_at": now,
        "job_count": len(results),
        "queue_count": sum(1 for item in results if item["queue_eligible"]),
        "input_hash": input_hash,
        "calibration": calibration,
        "by_action_group": {
            group: sum(1 for item in results if item["action_group"] == group)
            for group in ACTION_GROUPS
        },
    }


def _current_input_hash(*, db_path: Path) -> str:
    candidates = _load_jobs(db_path=db_path)
    context = _profile_context(db_path=db_path)
    return _json_hash(_input_payload(candidates, context))


def ensure_decision_run(
    *,
    strategy: str = DEFAULT_STRATEGY,
    refresh: bool = False,
    db_path: Path = DB_PATH,
) -> dict[str, Any]:
    strategy = _validate_strategy(strategy)
    latest = _latest_run(strategy, db_path=db_path)
    current_hash = _current_input_hash(db_path=db_path)
    if refresh or latest is None or latest.get("input_hash") != current_hash:
        recalculate_decisions(strategy=strategy, db_path=db_path)
        latest = _latest_run(strategy, db_path=db_path)
    if latest is None:
        raise RuntimeError("投递决策计算未生成有效运行记录。")
    latest["stale"] = latest.get("input_hash") != current_hash
    latest["strategy_label"] = STRATEGY_LABELS[strategy]
    return latest


def _load_run_results(run_id: int, *, db_path: Path) -> list[dict[str, Any]]:
    with connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT result_json
            FROM decision_results
            WHERE run_id = ?
            ORDER BY priority_score DESC, match_score DESC, job_id
            """,
            (run_id,),
        ).fetchall()
    return [json.loads(row["result_json"]) for row in rows]


def decision_summary(
    *,
    strategy: str = DEFAULT_STRATEGY,
    refresh: bool = False,
    db_path: Path = DB_PATH,
) -> dict[str, Any]:
    run = ensure_decision_run(strategy=strategy, refresh=refresh, db_path=db_path)
    results = _load_run_results(int(run["run_id"]), db_path=db_path)
    queue_results = [item for item in results if item["queue_eligible"]]
    counts = {
        group: sum(1 for item in queue_results if item["action_group"] == group)
        for group in ACTION_GROUPS
    }
    top_jobs = [
        {
            "job_id": item["job_id"],
            "job_title": item["job_title"],
            "company_name": item["company_name"],
            "action_group": item["action_group"],
            "action_group_label": item["action_group_label"],
            "priority_score": item["priority_score"],
            "match_score": item["match_score"],
            "opportunity_score": item["opportunity_score"],
            "suggested_action": item["suggested_action"],
        }
        for item in queue_results[:5]
    ]
    return {
        "run": run,
        "strategy": strategy,
        "strategy_label": STRATEGY_LABELS[strategy],
        "job_count": len(results),
        "queue_count": len(queue_results),
        "by_action_group": counts,
        "hard_conflict_count": sum(1 for item in queue_results if item["hard_conflicts"]),
        "information_risk_count": sum(1 for item in queue_results if item["information_risks"]),
        "top_jobs": top_jobs,
    }


def list_decisions(
    *,
    strategy: str = DEFAULT_STRATEGY,
    action_group: str | None = None,
    pending_only: bool = True,
    limit: int = 100,
    offset: int = 0,
    refresh: bool = False,
    db_path: Path = DB_PATH,
) -> dict[str, Any]:
    strategy = _validate_strategy(strategy)
    if action_group is not None and action_group not in ACTION_GROUPS:
        raise ValueError("action_group 不是有效行动分组。")
    safe_limit = max(1, min(int(limit), 500))
    safe_offset = max(0, int(offset))
    run = ensure_decision_run(strategy=strategy, refresh=refresh, db_path=db_path)
    results = _load_run_results(int(run["run_id"]), db_path=db_path)
    filtered = [
        item for item in results
        if (not pending_only or item["queue_eligible"])
        and (action_group is None or item["action_group"] == action_group)
    ]
    return {
        "run": run,
        "total": len(filtered),
        "limit": safe_limit,
        "offset": safe_offset,
        "items": filtered[safe_offset:safe_offset + safe_limit],
    }


def get_decision(
    job_id: str,
    *,
    strategy: str = DEFAULT_STRATEGY,
    refresh: bool = False,
    db_path: Path = DB_PATH,
) -> dict[str, Any]:
    strategy = _validate_strategy(strategy)
    run = ensure_decision_run(strategy=strategy, refresh=refresh, db_path=db_path)
    with connect(db_path) as connection:
        row = connection.execute(
            """
            SELECT result_json
            FROM decision_results
            WHERE run_id = ? AND job_id = ?
            """,
            (int(run["run_id"]), str(job_id)),
        ).fetchone()
    if row is None:
        raise KeyError(f"当前决策结果中不存在岗位：{job_id}")
    return {"run": run, "item": json.loads(row["result_json"])}


def decision_calibration_report(
    *,
    strategy: str = DEFAULT_STRATEGY,
    refresh: bool = False,
    db_path: Path = DB_PATH,
) -> dict[str, Any]:
    strategy = _validate_strategy(strategy)
    run = ensure_decision_run(strategy=strategy, refresh=refresh, db_path=db_path)
    results = _load_run_results(int(run["run_id"]), db_path=db_path)
    report = _calibration_metrics({item["job_id"]: item for item in results}, db_path=db_path)
    return {"run": run, "strategy": strategy, **report}


def decision_options() -> dict[str, Any]:
    return {
        "engine_version": ENGINE_VERSION,
        "default_strategy": DEFAULT_STRATEGY,
        "strategies": [
            {
                "value": strategy,
                "label": STRATEGY_LABELS[strategy],
                "weights": STRATEGY_CONFIG[strategy]["weights"],
            }
            for strategy in STRATEGIES
        ],
        "action_groups": [
            {"value": group, "label": ACTION_GROUP_LABELS[group]}
            for group in ACTION_GROUPS
        ],
        "principles": [
            "人工校准标签只用于评估，不直接写入分数。",
            "明确硬条件冲突可以覆盖普通高分。",
            "信息缺失与明确不满足分开处理。",
            "Python/R、PyTorch/TensorFlow等二选一要求按替代组判断。",
            "项目文本和结构化技能都可以形成能力证据。",
        ],
    }
