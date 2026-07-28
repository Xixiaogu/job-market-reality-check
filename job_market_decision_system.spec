# -*- mode: python ; coding: utf-8 -*-

from __future__ import annotations

import os
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules


project_root = Path(
    os.environ.get("JOB_MARKET_BUILD_ROOT", Path.cwd())
).resolve()

pipeline_scripts = (
    "clean_boss_jobs.py",
    "analyze_boss_jobs.py",
    "audit_boss_skills.py",
    "visualize_boss_jobs_v11.py",
)

datas = []
for script_name in pipeline_scripts:
    script_path = project_root / script_name
    if not script_path.exists():
        raise FileNotFoundError(f"Required pipeline script not found: {script_path}")
    datas.append((str(script_path), "."))

hiddenimports = sorted(
    set(
        collect_submodules("local_api")
        + collect_submodules("uvicorn")
        + [
            "clean_boss_jobs",
            "analyze_boss_jobs",
            "audit_boss_skills",
            "visualize_boss_jobs_v11",
            "anyio._backends._asyncio",
        ]
    )
)

a = Analysis(
    [str(project_root / "desktop_launcher.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "IPython",
        "jupyter",
        "notebook",
        "pytest",
        "selenium",
        "playwright",
        "torch",
        "tensorflow",
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="JobMarketDecisionSystem",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version=str(project_root / "packaging" / "windows_version_info.txt"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="JobMarketDecisionSystem",
)
