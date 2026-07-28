from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

ACTIONS = {"defer": 0, "prepare_first": 1, "stretch": 2, "apply_now": 3}
ACTION_ZH = {
    "apply_now": "立即投递",
    "stretch": "值得冲刺",
    "prepare_first": "补材料后投递",
    "defer": "暂缓",
}
LEVEL = {
    "了解": 0.35,
    "基础": 0.55,
    "熟练": 0.80,
    "可独立完成项目": 1.00,
    "aware": 0.35,
    "basic": 0.55,
    "proficient": 0.80,
    "project": 1.00,
}
ALIASES = {
    "python3": "Python", "python": "Python", "pandas": "Pandas", "numpy": "NumPy",
    "sql": "SQL", "mysql": "MySQL", "postgresql": "PostgreSQL", "sqlite": "SQLite",
    "excel": "Excel", "power bi": "Power BI", "powerbi": "Power BI", "tableau": "Tableau",
    "fastapi": "FastAPI", "flask": "Flask", "django": "Django",
    "javascript": "JavaScript", "typescript": "TypeScript", "node.js": "Node.js", "nodejs": "Node.js",
    "machine learning": "机器学习", "机器学习": "机器学习", "深度学习": "深度学习",
    "数据分析": "数据分析", "商业分析": "商业分析", "数据清洗": "数据清洗",
    "数据可视化": "数据可视化", "浏览器扩展": "浏览器扩展", "chrome extension": "浏览器扩展",
    "git": "Git", "docker": "Docker", "linux": "Linux", "prompt": "Prompt",
    "agent": "AI Agent", "llm": "大语言模型", "大模型": "大语言模型",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_jobs(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    if path.suffix.lower() in {".jsonl", ".ndjson"}:
        return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    payload = read_json(path)
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("jobs"), list):
        return payload["jobs"]
    raise ValueError("Jobs must be CSV, JSON array, JSON object with jobs, or JSONL.")


def text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return " ".join(map(str, value))
    if isinstance(value, dict):
        return " ".join(f"{k} {v}" for k, v in value.items())
    return str(value)


def canonical(name: str) -> str:
    clean = re.sub(r"\s+", " ", name.strip())
    return ALIASES.get(clean.lower(), clean)


def extract_skills(job: dict[str, Any]) -> list[str]:
    found: list[str] = []
    explicit = job.get("skills")
    if isinstance(explicit, str):
        explicit = re.split(r"[,，/、;；|]", explicit)
    if isinstance(explicit, list):
        found.extend(canonical(str(item)) for item in explicit if str(item).strip())
    blob = " ".join(text(job.get(k)) for k in ("title", "description", "requirements", "responsibilities")).lower()
    for alias, value in ALIASES.items():
        if re.search(r"(?<![a-z0-9])" + re.escape(alias) + r"(?![a-z0-9])", blob):
            found.append(value)
    return list(dict.fromkeys(found))


def normalize(job: dict[str, Any], index: int) -> dict[str, Any]:
    result = dict(job)
    result["job_id"] = text(job.get("job_id") or job.get("id") or f"job-{index:03d}")
    result["title"] = text(job.get("title") or job.get("job_title") or job.get("name"))
    result["company"] = text(job.get("company") or job.get("company_name"))
    result["location"] = text(job.get("location") or job.get("city"))
    result["salary"] = text(job.get("salary") or job.get("salary_text"))
    result["employment_type"] = text(job.get("employment_type") or job.get("job_type") or job.get("type"))
    result["education"] = text(job.get("education") or job.get("degree"))
    result["experience"] = text(job.get("experience") or job.get("experience_required"))
    result["description"] = text(job.get("description") or job.get("job_description") or job.get("requirements"))
    result["hard_requirements"] = job.get("hard_requirements") or []
    result["skills"] = extract_skills(result)
    return result


def skill_map(profile: dict[str, Any]) -> dict[str, float]:
    result: dict[str, float] = {}
    for item in profile.get("skills", []):
        if isinstance(item, str):
            result[canonical(item)] = max(result.get(canonical(item), 0), 0.55)
        else:
            name = canonical(text(item.get("name")))
            if name:
                result[name] = max(result.get(name, 0), LEVEL.get(text(item.get("level") or "基础"), 0.55))
    for project in profile.get("projects", []):
        for name in project.get("skills", []):
            key = canonical(str(name))
            result[key] = max(result.get(key, 0), 0.80)
    return result


def similarity(title: str, targets: list[str]) -> float:
    if not title or not targets:
        return 0.5
    best = 0.0
    for target in targets:
        if target.lower() in title.lower() or title.lower() in target.lower():
            best = max(best, 0.9)
        title_tokens = set(re.findall(r"[\u4e00-\u9fff]+|[a-z0-9+#.]+", title.lower()))
        target_tokens = set(re.findall(r"[\u4e00-\u9fff]+|[a-z0-9+#.]+", target.lower()))
        if target_tokens:
            best = max(best, len(title_tokens & target_tokens) / len(target_tokens))
    return min(1.0, best)


def hard_check(job: dict[str, Any], profile: dict[str, Any]) -> tuple[str, list[str]]:
    reasons: list[str] = []
    education = text(profile.get("education", {}).get("level"))
    order = {"高中": 0, "大专": 1, "本科": 2, "硕士": 3, "博士": 4}
    required = next((x for x in ("博士", "硕士", "本科", "大专") if x in job["education"]), None)
    if required and education and order.get(education, -1) < order.get(required, -1):
        reasons.append(f"学历要求为{required}，个人档案为{education}")
    blob = " ".join([job["experience"], job["description"], text(job["hard_requirements"])])
    match = re.search(r"(\d+)\s*年(?:以上|及以上)", blob)
    if match and float(profile.get("years_experience") or 0) < float(match.group(1)):
        reasons.append(f"要求{match.group(1)}年以上经验")
    grad_year = profile.get("education", {}).get("graduation_year")
    years = [int(x) for x in re.findall(r"20\d{2}", blob)]
    if grad_year and "届" in blob and years and int(grad_year) not in years and any(k in blob for k in ("仅限", "限", "面向")):
        reasons.append(f"毕业年份可能不符合：岗位文本包含{years}")
    return ("conflict", reasons) if reasons else ("satisfied", [])


def project_evidence(profile: dict[str, Any], required: list[str]) -> tuple[int, list[str]]:
    if not required:
        return 50, []
    best, names = 0.0, []
    need = set(required)
    for project in profile.get("projects", []):
        have = {canonical(str(x)) for x in project.get("skills", [])}
        overlap = len(need & have)
        if overlap:
            score = min(1.0, overlap / len(need) + (0.15 if text(project.get("evidence")) else 0))
            if score > best:
                best, names = score, [text(project.get("name") or "未命名项目")]
    return round(best * 100), names


def daily_salary(value: str) -> float | None:
    if not value or ("天" not in value and "/d" not in value.lower()):
        return None
    nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", value)]
    return sum(nums[:2]) / min(2, len(nums)) if nums else None


def opportunity(job: dict[str, Any], profile: dict[str, Any]) -> int:
    parts = [similarity(job["title"], [str(x) for x in profile.get("targets", [])])]
    locations = [str(x) for x in profile.get("preferred_locations", [])]
    if locations and job["location"]:
        parts.append(1.0 if any(x.lower() in job["location"].lower() for x in locations) else 0.35)
    types = [str(x) for x in profile.get("constraints", {}).get("employment_types", [])]
    if types and job["employment_type"]:
        parts.append(1.0 if any(x.lower() in job["employment_type"].lower() for x in types) else 0.25)
    floor = profile.get("constraints", {}).get("minimum_daily_salary")
    actual = daily_salary(job["salary"])
    if floor is not None and actual is not None:
        parts.append(min(1.0, actual / float(floor)))
    return round(sum(parts) / len(parts) * 100)


def score(job: dict[str, Any], profile: dict[str, Any], inventory: dict[str, float]) -> dict[str, Any]:
    required = job["skills"]
    matched = [x for x in required if x in inventory]
    missing = [x for x in required if x not in inventory]
    skill_score = round(sum(inventory.get(x, 0) for x in required) / len(required) * 100) if required else 50
    evidence_score, projects = project_evidence(profile, required)
    opportunity_score = opportunity(job, profile)
    status, hard_reasons = hard_check(job, profile)
    priority = round(0.50 * skill_score + 0.20 * evidence_score + 0.30 * opportunity_score)
    if status == "conflict":
        priority = max(0, priority - 35)
    if status == "conflict":
        action = "defer"
    elif priority >= 75 and len(missing) <= 1:
        action = "apply_now"
    elif priority >= 60:
        action = "stretch"
    elif priority >= 45:
        action = "prepare_first"
    else:
        action = "defer"
    return {
        "job_id": job["job_id"], "title": job["title"], "company": job["company"],
        "location": job["location"], "salary": job["salary"], "priority": priority,
        "action": action, "action_zh": ACTION_ZH[action], "skill_match": skill_score,
        "project_evidence": evidence_score, "opportunity_value": opportunity_score,
        "hard_status": status, "hard_reasons": hard_reasons, "matched_skills": matched,
        "missing_skills": missing, "evidence_projects": projects,
    }


def calibrate(results: list[dict[str, Any]], path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    labels = {str(x["job_id"]): str(x["label"]) for x in read_json(path)}
    compared = [x for x in results if x["job_id"] in labels]
    if not compared:
        return {"count": 0, "exact_accuracy": None, "adjacent_accuracy": None, "disagreements": []}
    exact = adjacent = 0
    disagreements = []
    for item in compared:
        expected, predicted = labels[item["job_id"]], item["action"]
        distance = abs(ACTIONS[predicted] - ACTIONS[expected])
        exact += distance == 0
        adjacent += distance <= 1
        if distance:
            disagreements.append({"job_id": item["job_id"], "predicted": predicted, "expected": expected, "distance": distance})
    return {
        "count": len(compared),
        "exact_accuracy": round(exact / len(compared), 4),
        "adjacent_accuracy": round(adjacent / len(compared), 4),
        "disagreements": disagreements,
    }


def render_report(jobs: list[dict[str, Any]], results: list[dict[str, Any]], calibration: dict[str, Any] | None) -> str:
    counts = Counter(x["action"] for x in results)
    skills = Counter(skill for job in jobs for skill in job["skills"])
    lines = [
        "# 求职市场现实检查", "", "## 一、结论", "",
        f"- 可用岗位：{len(results)}", f"- 立即投递：{counts['apply_now']}",
        f"- 值得冲刺：{counts['stretch']}", f"- 补材料后投递：{counts['prepare_first']}",
        f"- 暂缓：{counts['defer']}", "- 说明：结果是透明规则排序，不是Offer概率。", "",
        "## 二、市场样本概览", "", "- 高频技能：" + ("、".join(x for x, _ in skills.most_common(10)) or "未提取到明确技能"), "",
    ]
    if calibration:
        lines += ["## 三、人工校准", "", f"- 比较样本：{calibration['count']}", f"- 完全一致率：{calibration['exact_accuracy']}", f"- 相邻一致率：{calibration['adjacent_accuracy']}", ""]
    lines += ["## 四、投递队列", ""]
    for action in ("apply_now", "stretch", "prepare_first", "defer"):
        lines += [f"### {ACTION_ZH[action]}", "", "| 岗位 | 公司 | 优先级 | 匹配技能 | 主要缺口 |", "|---|---|---:|---|---|"]
        group = [x for x in results if x["action"] == action]
        if not group:
            lines.append("| — | — | — | — | — |")
        for item in group[:15]:
            lines.append(f"| {item['title'] or '未命名岗位'} | {item['company'] or '未提供'} | {item['priority']} | {'、'.join(item['matched_skills'][:4]) or '未识别'} | {'、'.join(item['missing_skills'][:4]) or '无明确缺口'} |")
        lines.append("")
    lines += ["## 五、限制", "", "- 结论只代表输入样本，不代表整个招聘市场。", "- 缺失字段按未知处理。", "- 技能抽取需要人工复核。", "- 分数用于排序和解释，不表示Offer概率。", ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Portable job-market reality check")
    parser.add_argument("--jobs", required=True, type=Path)
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--labels", type=Path)
    args = parser.parse_args()

    raw_jobs = load_jobs(args.jobs)
    profile = read_json(args.profile)
    jobs = [normalize(job, index) for index, job in enumerate(raw_jobs, 1)]
    jobs = [job for job in jobs if job["title"] or job["description"]]
    inventory = skill_map(profile)
    results = [score(job, profile, inventory) for job in jobs]
    results.sort(key=lambda x: (-ACTIONS[x["action"]], -x["priority"]))
    calibration = calibrate(results, args.labels)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "normalized_jobs.json").write_text(json.dumps(jobs, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.output_dir / "decision_results.json").write_text(json.dumps({"summary": {"usable_jobs": len(results), "action_counts": dict(Counter(x["action"] for x in results))}, "calibration": calibration, "jobs": results}, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.output_dir / "report.md").write_text(render_report(jobs, results, calibration), encoding="utf-8")
    print("Job market reality check completed.")
    print(f"Usable jobs: {len(results)}")
    print(f"Output: {args.output_dir}")


if __name__ == "__main__":
    main()
