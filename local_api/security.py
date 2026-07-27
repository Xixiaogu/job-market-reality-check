from __future__ import annotations

import secrets
from pathlib import Path

from .config import TOKEN_PATH, ensure_runtime_directories


MIN_TOKEN_LENGTH = 32


def get_or_create_token(path: Path = TOKEN_PATH) -> str:
    ensure_runtime_directories()

    if path.exists():
        token = path.read_text(encoding="utf-8").strip()
        if len(token) >= MIN_TOKEN_LENGTH:
            return token

    token = secrets.token_urlsafe(36)
    temporary_path = path.with_suffix(".tmp")
    temporary_path.write_text(token, encoding="utf-8")
    temporary_path.replace(path)

    try:
        path.chmod(0o600)
    except OSError:
        pass

    return token
