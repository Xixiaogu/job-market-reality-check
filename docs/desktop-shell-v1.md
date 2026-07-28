# Desktop Shell V1

This phase converts the existing FastAPI browser launcher into a native Windows desktop shell without changing the dashboard or analysis logic.

## Added

- Native pywebview window using Edge WebView2
- Windows taskbar and Alt+Tab presence
- Product icon for source and packaged EXE
- System tray menu
- Close-to-tray behavior
- Single-instance show signal
- Graceful FastAPI shutdown when the shell owns the service
- Existing `--no-browser` headless mode retained for automated tests
- Existing browser launcher retained as a fallback

## Manual acceptance

1. Run `release\JobMarketDecisionSystem-v1.0.1-desktop\JobMarketDecisionSystem.exe`.
2. A native application window should appear; the default browser should not open.
3. The taskbar should display the application icon and Chinese product title.
4. Close the window. The service should remain available in the system tray.
5. Double-click the EXE again. The existing window should return instead of starting another instance.
6. Use the tray menu to open the data directory and log directory.
7. Choose `退出`; the tray icon and FastAPI process should stop.
8. Verify the browser extension can still synchronize jobs while the desktop app is running.

The installer is intentionally not rebuilt in this phase. Rebuild it only after the native shell passes manual acceptance.
