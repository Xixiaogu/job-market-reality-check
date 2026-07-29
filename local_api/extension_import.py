from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_TARGET = Path("output/boss_batch/jobs.jsonl")
DEFAULT_IMPORT_DIR = Path("output/extension_import")


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).replace("\xa0", " ").split()).strip()


def clean_multiline(value: Any) -> str:
    if value is None:
        return ""

    lines = []
    for raw_line in str(value).replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = " ".join(raw_line.replace("\xa0", " ").split()).strip()
        if line:
            lines.append(line)

    return "\n".join(lines)


def parse_iso_timestamp(value: Any) -> datetime:
    text = clean_text(value)
    if not text:
        return datetime.min

    normalized = text.replace("Z", "+00:00")

    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return datetime.min


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"找不到输入文件：{path.resolve()}")

    records: list[dict[str, Any]] = []

    with path.open("r", encoding="utf-8-sig") as file:
        for line_number, line in enumerate(file, start=1):
            stripped = line.strip()
            if not stripped:
                continue

            try:
                value = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise RuntimeError(
                    f"{path} 第 {line_number} 行不是有效 JSON：{exc}"
                ) from exc

            if not isinstance(value, dict):
                raise RuntimeError(
                    f"{path} 第 {line_number} 行必须是 JSON 对象。"
                )

            records.append(value)

    return records


def write_jsonl_atomic(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    temporary_path = path.with_name(f"{path.name}.tmp")

    with temporary_path.open("w", encoding="utf-8", newline="\n") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False))
            file.write("\n")

    temporary_path.replace(path)


def clean_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []

    result: list[str] = []
    seen: set[str] = set()

    for item in value:
        cleaned = clean_text(item)

        if not cleaned or cleaned in seen:
            continue

        seen.add(cleaned)
        result.append(cleaned)

    return result


def build_basic_info_raw(record: dict[str, Any]) -> str:
    parts = [
        clean_text(record.get("city")),
        clean_text(record.get("experience")),
        clean_text(record.get("internshipDays")),
        clean_text(record.get("internshipDuration")),
        clean_text(record.get("education")),
    ]

    return "·".join(part for part in parts if part)


def build_company_info_raw(record: dict[str, Any]) -> str:
    parts = [
        clean_text(record.get("financingStage")),
        clean_text(record.get("companySize")),
        clean_text(record.get("industry")),
    ]

    return "·".join(part for part in parts if part)


def build_core_text(record: dict[str, Any]) -> str:
    tags = clean_string_list(record.get("jobTags"))

    sections = [
        clean_text(record.get("jobTitle")),
        clean_text(record.get("salary")),
        build_basic_info_raw(record),
        clean_text(record.get("companyFullName"))
        or clean_text(record.get("companyShortName")),
        " ".join(tags),
        clean_multiline(record.get("jobDescription")),
    ]

    return "\n".join(section for section in sections if section)


def validate_extension_record(
    record: dict[str, Any],
    line_number: int,
) -> list[str]:
    issues: list[str] = []

    required_fields = {
        "jobId": record.get("jobId"),
        "jobTitle": record.get("jobTitle"),
        "salary": record.get("salary"),
        "city": record.get("city"),
        "education": record.get("education"),
        "jobDescription": record.get("jobDescription"),
        "sourceUrl": record.get("sourceUrl"),
    }

    for field_name, value in required_fields.items():
        if not clean_text(value):
            issues.append(f"第{line_number}行缺少字段:{field_name}")

    source_url = clean_text(record.get("sourceUrl"))
    if source_url and "zhipin.com" not in source_url:
        issues.append(f"第{line_number}行来源链接不是 zhipin.com")

    return issues


def convert_extension_record(record: dict[str, Any]) -> dict[str, Any]:
    job_id = clean_text(record.get("jobId"))
    job_title = clean_text(record.get("jobTitle"))
    salary = clean_text(record.get("salary"))
    city = clean_text(record.get("city"))
    education = clean_text(record.get("education"))
    job_description = clean_multiline(record.get("jobDescription"))
    source_url = clean_text(record.get("sourceUrl"))
    collected_at = clean_text(record.get("collectedAt"))
    saved_at = clean_text(record.get("savedAt"))
    internship_days = clean_text(record.get("internshipDays"))
    internship_duration = clean_text(record.get("internshipDuration"))
    experience = clean_text(record.get("experience"))
    company_short_name = clean_text(record.get("companyShortName"))
    company_full_name = clean_text(record.get("companyFullName"))
    extension_extraction = record.get("extraction", {})
    company_name_source = clean_text(
        extension_extraction.get("companyName")
        if isinstance(extension_extraction, dict)
        else ""
    )
    financing_stage = clean_text(record.get("financingStage"))
    company_size = clean_text(record.get("companySize"))
    industry = clean_text(record.get("industry"))
    job_tags = clean_string_list(record.get("jobTags"))

    missing_fields = [
        field
        for field, value in {
            "company_full_name": company_full_name,
        }.items()
        if not value
    ]

    return {
        "job_id": job_id,
        "recruiter_name": "",
        "influence": "",
        "recruiter_title": "",
        "recruiter_company": "",
        "job_title": job_title,
        "salary": salary,
        "city": city,
        "experience": experience,
        "education": education,
        "company_short_name": company_short_name or company_full_name,
        "company_full_name_source": company_name_source,
        "financing_stage": financing_stage,
        "job_description": job_description,
        "work_address": "",
        "company_full_name": company_full_name,
        "company_size": company_size,
        "industry": industry,
        "job_tags": job_tags,
        "recruiter_info_raw": "",
        "job_basic_info_raw": build_basic_info_raw(record),
        "company_info_raw": build_company_info_raw(record),
        "core_text": build_core_text(record),
        "source_url": source_url,
        "final_url": source_url,
        "source_sheet": "browser_extension",
        "source_cell": "",
        "collected_at": collected_at,
        "status": "partial" if missing_fields else "success",
        "missing_fields": missing_fields,
        "collector": "browser_extension",
        "extension_schema_version": clean_text(record.get("schemaVersion")),
        "extension_saved_at": saved_at,
        "extension_extraction": extension_extraction,
        "internship_days_per_week": internship_days,
        "internship_duration": internship_duration,
    }


def deduplicate_extension_records(
    records: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], int]:
    by_job_id: dict[str, dict[str, Any]] = {}
    duplicate_count = 0

    for record in records:
        job_id = clean_text(record.get("jobId"))
        if not job_id:
            continue

        previous = by_job_id.get(job_id)

        if previous is None:
            by_job_id[job_id] = record
            continue

        duplicate_count += 1

        previous_time = max(
            parse_iso_timestamp(previous.get("savedAt")),
            parse_iso_timestamp(previous.get("collectedAt")),
        )
        current_time = max(
            parse_iso_timestamp(record.get("savedAt")),
            parse_iso_timestamp(record.get("collectedAt")),
        )

        if current_time >= previous_time:
            by_job_id[job_id] = record

    return list(by_job_id.values()), duplicate_count


def merge_nonempty(
    existing: dict[str, Any],
    imported: dict[str, Any],
) -> tuple[dict[str, Any], bool]:
    result = dict(existing)
    changed = False

    fields_to_refresh = {
        "job_title",
        "salary",
        "city",
        "experience",
        "education",
        "company_short_name",
        "company_full_name",
        "company_full_name_source",
        "financing_stage",
        "company_size",
        "industry",
        "job_tags",
        "job_description",
        "job_basic_info_raw",
        "company_info_raw",
        "core_text",
        "source_url",
        "final_url",
        "collected_at",
        "collector",
        "extension_schema_version",
        "extension_saved_at",
        "extension_extraction",
        "internship_days_per_week",
        "internship_duration",
    }

    imported_full_name = clean_text(
        imported.get("company_full_name")
    )
    imported_short_name = clean_text(
        imported.get("company_short_name")
    )
    imported_name_source = clean_text(
        imported.get("company_full_name_source")
    )

    if (
        not imported_full_name
        and imported_short_name
        and imported_name_source
        in {"short-name-only", "title-fallback", "missing"}
        and clean_text(result.get("collector"))
        == "browser_extension"
        and clean_text(result.get("company_full_name"))
        == imported_short_name
    ):
        result["company_full_name"] = ""
        changed = True

    for field in fields_to_refresh:
        imported_value = imported.get(field)

        if imported_value in (None, "", [], {}):
            continue

        if result.get(field) != imported_value:
            result[field] = imported_value
            changed = True

    old_missing = {
        clean_text(value)
        for value in result.get("missing_fields", [])
        if clean_text(value)
    }

    # 招聘者信息不是当前插件导入的质量门槛。
    old_missing.discard("recruiter_name")

    if clean_text(result.get("company_full_name")):
        old_missing.discard("company_full_name")
    else:
        old_missing.add("company_full_name")

    result["missing_fields"] = sorted(old_missing)
    result["status"] = "success" if not result["missing_fields"] else "partial"

    return result, changed


def merge_records(
    existing_records: list[dict[str, Any]],
    imported_records: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    result = list(existing_records)
    index_by_job_id: dict[str, int] = {}

    for index, record in enumerate(result):
        job_id = clean_text(record.get("job_id"))
        if job_id:
            index_by_job_id[job_id] = index

    added = 0
    updated = 0
    unchanged = 0

    for imported in imported_records:
        job_id = clean_text(imported.get("job_id"))

        if job_id not in index_by_job_id:
            index_by_job_id[job_id] = len(result)
            result.append(imported)
            added += 1
            continue

        index = index_by_job_id[job_id]
        merged, changed = merge_nonempty(result[index], imported)
        result[index] = merged

        if changed:
            updated += 1
        else:
            unchanged += 1

    return result, {
        "added": added,
        "updated": updated,
        "unchanged": unchanged,
    }


def write_report(
    report_path: Path,
    report: dict[str, Any],
) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "将 Job Market Collector 导出的 JSONL 转换并合并到"
            "现有 BOSS Python 分析管线。"
        )
    )

    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="浏览器扩展导出的 boss-jobs-*.jsonl",
    )

    parser.add_argument(
        "--target",
        type=Path,
        default=DEFAULT_TARGET,
        help=(
            "现有原始岗位 JSONL。默认："
            f"{DEFAULT_TARGET.as_posix()}"
        ),
    )

    parser.add_argument(
        "--import-dir",
        type=Path,
        default=DEFAULT_IMPORT_DIR,
        help=(
            "转换结果、备份和报告目录。默认："
            f"{DEFAULT_IMPORT_DIR.as_posix()}"
        ),
    )

    parser.add_argument(
        "--replace",
        action="store_true",
        help="不合并现有 target，只用本次扩展记录覆盖 target。",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    extension_records = load_jsonl(args.input)

    validation_issues: list[str] = []

    for line_number, record in enumerate(extension_records, start=1):
        validation_issues.extend(
            validate_extension_record(record, line_number)
        )

    if validation_issues:
        print("扩展 JSONL 校验失败：", file=sys.stderr)
        for issue in validation_issues:
            print(f"- {issue}", file=sys.stderr)
        return 2

    unique_extension_records, duplicate_count = (
        deduplicate_extension_records(extension_records)
    )

    converted_records = [
        convert_extension_record(record)
        for record in unique_extension_records
    ]

    args.import_dir.mkdir(parents=True, exist_ok=True)

    imported_only_path = args.import_dir / "jobs_imported.jsonl"
    write_jsonl_atomic(imported_only_path, converted_records)

    existing_records: list[dict[str, Any]] = []

    if args.target.exists() and not args.replace:
        existing_records = load_jsonl(args.target)

        backup_dir = args.import_dir / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
        backup_path = backup_dir / f"jobs_before_{timestamp}.jsonl"
        shutil.copy2(args.target, backup_path)
    else:
        backup_path = None

    if args.replace:
        merged_records = converted_records
        merge_stats = {
            "added": len(converted_records),
            "updated": 0,
            "unchanged": 0,
        }
    else:
        merged_records, merge_stats = merge_records(
            existing_records,
            converted_records,
        )

    write_jsonl_atomic(args.target, merged_records)

    report = {
        "input_file": str(args.input.resolve()),
        "target_file": str(args.target.resolve()),
        "imported_only_file": str(imported_only_path.resolve()),
        "backup_file": (
            str(backup_path.resolve())
            if backup_path is not None
            else None
        ),
        "replace_mode": bool(args.replace),
        "extension_input_count": len(extension_records),
        "extension_duplicate_count": duplicate_count,
        "extension_unique_count": len(unique_extension_records),
        "existing_target_count": len(existing_records),
        "added_count": merge_stats["added"],
        "updated_count": merge_stats["updated"],
        "unchanged_count": merge_stats["unchanged"],
        "final_target_count": len(merged_records),
        "known_data_gaps": [
            "浏览器扩展当前未采集招聘者姓名与职位。",
            "若个别页面无法识别公司名称，该岗位会在清洗阶段进入 review。",
        ],
        "generated_at": datetime.now().astimezone().isoformat(),
    }

    report_path = args.import_dir / "import_report.json"
    write_report(report_path, report)

    print("=" * 72)
    print("浏览器扩展岗位导入完成")
    print("=" * 72)
    print(f"扩展输入：{len(extension_records)}")
    print(f"扩展去重后：{len(unique_extension_records)}")
    print(f"新增：{merge_stats['added']}")
    print(f"更新：{merge_stats['updated']}")
    print(f"未变化：{merge_stats['unchanged']}")
    print(f"最终 target：{len(merged_records)}")
    print(f"目标文件：{args.target.resolve()}")
    print(f"转换文件：{imported_only_path.resolve()}")
    print(f"导入报告：{report_path.resolve()}")

    if backup_path is not None:
        print(f"原目标备份：{backup_path.resolve()}")

    print()
    print("Phase 5B 已支持公司、经验、公司规模、行业与岗位标签。")
    print("个别页面若未识别公司名称，会进入 review；其他岗位可正常分析。")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

