# -*- mode: python ; coding: utf-8 -*-

from __future__ import annotations

import os
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules


project_root = Path(
    os.environ.get("JOB_MARKET_BUILD_ROOT", Path.cwd())
).resolve()

datas = []
branding_dir = project_root / "packaging" / "branding"
for asset_name in ("app_icon.png", "app_icon.ico"):
    asset_path = branding_dir / asset_name
    if not asset_path.exists():
        raise FileNotFoundError(f"Required branding asset not found: {asset_path}")
    datas.append((str(asset_path), "packaging/branding"))

hiddenimports = sorted(
    set(
        collect_submodules("local_api")
        + collect_submodules("desktop")
        + collect_submodules("pipeline")
        + collect_submodules("uvicorn")
        + collect_submodules("webview")
        + collect_submodules("pystray")
        + [
            "anyio._backends._asyncio",
            "PIL.Image",
            "PIL.ImageDraw",
            "PIL.IcoImagePlugin",
            "PIL.PngImagePlugin",
            "clr",
            "pythonnet",
        ]
    )
)

a = Analysis(
    [str(project_root / "desktop" / "app.py")],
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
        "PyQt5",
        "PyQt6",
        "PySide2",
        "PySide6",
        "cefpython3",
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
    icon=str(branding_dir / "app_icon.ico"),
    version=str(project_root / "packaging" / "windows_version_info_shell.txt"),
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
