from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from .config import PROJECT_ROOT


if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from import_extension_jobs import (  # type: ignore
        clean_text,
        convert_extension_record,
        merge_nonempty,
        validate_extension_record,
    )
except ImportError as exc:
    raise RuntimeError(
        "无法导入项目根目录下的 import_extension_jobs.py。"
    ) from exc


EMPTY_VALUES = (None, "", [], {})


def validate_payload(payload: dict[str, Any]) -> list[str]:
    return validate_extension_record(payload, 1)


def convert_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return convert_extension_record(payload)


def merge_extension_into_canonical(
    existing: dict[str, Any],
    incoming: dict[str, Any],
) -> tuple[dict[str, Any], bool]:
    return merge_nonempty(existing, incoming)


def merge_canonical_nonempty(
    existing: dict[str, Any],
    incoming: dict[str, Any],
) -> tuple[dict[str, Any], bool]:
    result = dict(existing)
    changed = False

    for key, value in incoming.items():
        if value in EMPTY_VALUES:
            continue
        if result.get(key) != value:
            result[key] = value
            changed = True

    return result, changed


def canonical_job_id(record: dict[str, Any]) -> str:
    return clean_text(record.get("job_id"))
