from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path


def run_checked(command: list[str], timeout: int) -> None:
    completed = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"Command failed with exit code {completed.returncode}:\n"
            f"{' '.join(command)}\n\n{completed.stdout}"
        )


def remove_tree(path: Path) -> None:
    for attempt in range(10):
        try:
            shutil.rmtree(path)
            return
        except FileNotFoundError:
            return
        except OSError:
            if attempt == 9:
                raise
            time.sleep(0.5)


def wait_missing(path: Path, timeout: float = 20.0) -> None:
    deadline = time.monotonic() + timeout
    while path.exists() and time.monotonic() < deadline:
        time.sleep(0.3)
    if path.exists():
        raise RuntimeError(f"Path still exists after uninstall: {path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--installer", required=True, type=Path)
    args = parser.parse_args()

    installer = args.installer.resolve()
    if not installer.exists():
        raise SystemExit(f"Installer not found: {installer}")

    temp_root = Path(tempfile.mkdtemp(prefix="phase93-installer-"))
    install_dir = temp_root / "installed app"
    user_data = temp_root / "user data"

    try:
        run_checked(
            [
                str(installer),
                "/VERYSILENT",
                "/SUPPRESSMSGBOXES",
                "/NORESTART",
                "/SP-",
                f"/DIR={install_dir}",
                "/MERGETASKS=!desktopicon",
            ],
            240,
        )

        executable = install_dir / "JobMarketDecisionSystem.exe"
        manifest = install_dir / "browser-extension" / "chrome-mv3" / "manifest.json"
        readme = install_dir / "README_FIRST.txt"
        uninstaller = install_dir / "unins000.exe"

        for required in (executable, manifest, readme, uninstaller):
            if not required.exists():
                raise RuntimeError(f"Installed file is missing: {required}")

        manifest_payload = json.loads(manifest.read_text(encoding="utf-8"))
        if int(manifest_payload.get("manifest_version", 0)) != 3:
            raise RuntimeError("Installed browser extension is not Manifest V3.")

        run_checked(
            [
                str(executable),
                "--check",
                "--no-migrate",
                "--user-data-dir",
                str(user_data),
            ],
            90,
        )

        sentinel = user_data / "keep-after-uninstall.txt"
        sentinel.parent.mkdir(parents=True, exist_ok=True)
        sentinel.write_text("preserve user data\n", encoding="utf-8")

        run_checked(
            [
                str(uninstaller),
                "/VERYSILENT",
                "/SUPPRESSMSGBOXES",
                "/NORESTART",
            ],
            180,
        )

        wait_missing(executable)
        if not sentinel.exists():
            raise RuntimeError("User data was removed by the uninstaller.")

        print("Phase 9.3 installer smoke test passed.")
        print(f"Installer: {installer}")
        print("Silent install: passed")
        print("Installed executable check: passed")
        print("Bundled browser extension: passed")
        print("Silent uninstall: passed")
        print("User data preservation: passed")
    finally:
        remove_tree(temp_root)


if __name__ == "__main__":
    main()
