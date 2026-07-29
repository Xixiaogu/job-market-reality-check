# Phase 9.3：Windows 正式安装程序

## 产物

```text
release/installer/
├─ JobMarketDecisionSystem-Setup-v1.0.7.exe
└─ JobMarketDecisionSystem-Setup-v1.0.7.exe.sha256
```

## 安装行为

- 按当前 Windows 用户安装，不要求管理员权限；
- 默认安装到 `%LOCALAPPDATA%\Programs\JobMarketDecisionSystem`；
- 创建开始菜单入口；
- 可选创建桌面快捷方式；
- 浏览器扩展随软件安装在 `browser-extension\chrome-mv3`；
- 安装完成后可直接启动桌面程序；
- 卸载时保留 `%LOCALAPPDATA%\JobMarketDecisionSystem` 中的岗位和个人数据。

## 自动验收

构建脚本会将安装程序静默安装到临时目录，验证：

1. EXE 与扩展文件存在；
2. 打包后的启动器自检通过；
3. 静默卸载成功；
4. 用户数据哨兵文件在卸载后仍保留。

安装器必须从同版本桌面目录构建：

```text
release\JobMarketDecisionSystem-v1.0.7-desktop
```

构建脚本会同时核对 `version.json`，避免把旧桌面目录封装进新版本安装器：

```powershell
python -m pip install -e ".[desktop,build]"
.\scripts\build\build_installer.ps1 -Version 1.0.7
```

smoke test 会执行真实的当前用户静默安装，因此需要写入开始菜单和
`HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall`。受限沙箱需要明确授权该操作。
