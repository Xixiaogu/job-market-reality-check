from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
import tempfile
from contextlib import closing
from pathlib import Path

from tests.support.paths import PROJECT_ROOT

ROOT = PROJECT_ROOT


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    config_text = (ROOT / "local_api" / "config.py").read_text(encoding="utf-8")
    main_text = (ROOT / "local_api" / "main.py").read_text(encoding="utf-8")
    launcher_text = (ROOT / "desktop_launcher.py").read_text(encoding="utf-8")
    setup_text = (ROOT / "local_api" / "setup_ui.py").read_text(encoding="utf-8")

    require("PHASE_91_DESKTOP_PRODUCTIZATION" in config_text, "config marker missing")
    require("PHASE_91_DESKTOP_PRODUCTIZATION" in main_text, "main marker missing")
    require("PHASE_91_DESKTOP_PRODUCTIZATION" in launcher_text, "launcher marker missing")
    require('"/launch"' in main_text and '"/setup"' in main_text, "desktop routes missing")
    require("chrome://extensions" in setup_text, "extension guide missing")
    require("jobMarketApiTokenV1" in setup_text, "shared browser token key missing")

    with tempfile.TemporaryDirectory(prefix="phase91-") as directory:
        temp = Path(directory)
        legacy = temp / "legacy"
        user_data = temp / "user-data"
        (legacy / "data").mkdir(parents=True)
        (legacy / "local_api" / "runtime").mkdir(parents=True)

        legacy_db = legacy / "data" / "job_market.db"
        with closing(sqlite3.connect(legacy_db)) as connection:
            connection.execute("CREATE TABLE sample(value TEXT)")
            connection.execute("INSERT INTO sample(value) VALUES ('ok')")
            connection.commit()
        token = "t" * 48
        (legacy / "local_api" / "runtime" / "api_token.txt").write_text(token, encoding="utf-8")

        sys.path.insert(0, str(ROOT))
        import desktop_launcher

        result = desktop_launcher.migrate_legacy_data(legacy, user_data)
        require(result["database_migrated"], "database migration did not run")
        require(result["token_migrated"], "token migration did not run")
        with closing(sqlite3.connect(user_data / "data" / "job_market.db")) as connection:
            value = connection.execute("SELECT value FROM sample").fetchone()[0]
        require(value == "ok", "database backup content mismatch")
        require(
            (user_data / "runtime" / "api_token.txt").read_text(encoding="utf-8") == token,
            "token migration mismatch",
        )

        check_root = temp / "launcher-check"
        completed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "desktop_launcher.py"),
                "--check",
                "--no-migrate",
                "--user-data-dir",
                str(check_root),
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        require(completed.returncode == 0, completed.stdout)
        require(
            "Phase 9.1 desktop launcher check passed." in completed.stdout,
            "launcher check output missing",
        )

    print("Desktop productization contract tests passed.")


if __name__ == "__main__":
    main()
