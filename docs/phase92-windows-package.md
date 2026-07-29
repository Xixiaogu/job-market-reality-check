# Phase 9.2：Windows 可运行目录与 ZIP 发布包

## 目标

使用 PyInstaller `onedir` 模式生成可直接运行的 Windows 软件目录，并把浏览器扩展作为独立目录随软件发布。

## 主要产物

```text
release/
├─ JobMarketDecisionSystem-v1.0.7-desktop/
│  ├─ JobMarketDecisionSystem.exe
│  ├─ _internal/
│  ├─ browser-extension/
│  │  └─ chrome-mv3/
│  ├─ docs/
│  ├─ README_FIRST.txt
│  └─ version.json
├─ JobMarketDecisionSystem-v1.0.7-desktop-windows-x64.zip
└─ JobMarketDecisionSystem-v1.0.7-desktop-windows-x64.zip.sha256
```

## 打包兼容处理

打包模式下，分析流水线不能再使用 `python -m pipeline.<step>` 启动，因为 `sys.executable` 已经是桌面 EXE。启动器提供隐藏的 `--run-step` 模式，使内置分析模块继续在独立子进程中运行。

## 自动验收

构建完成后，`tests/release/test_portable_package_smoke.py` 会使用随机端口和隔离的临时用户目录启动打包后的 EXE，检查健康接口、桌面状态、浏览器扩展目录、SQLite 初始化、设置页和决策页。

当前基线构建命令：

```powershell
python -m pip install -e ".[desktop,build]"
.\scripts\build\build_desktop.ps1 -Version 1.0.7
```
