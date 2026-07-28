# Windows Transparent Glass Experiment

Branch: `experiment/windows-transparent-glass`

This experiment keeps the verified v1.0.5 business behavior unchanged and tests only the
Windows window-composition layer.

## Implementation

- WebView2 starts with a fully transparent default background using
  `WEBVIEW2_DEFAULT_BACKGROUND_COLOR=00000000`.
- The WinForms host receives a Windows 11 system backdrop through
  `DwmSetWindowAttribute`.
- The default material is Desktop Acrylic (`DWMSBT_TRANSIENTWINDOW`).
- The FastAPI shared shell switches to a more transparent CSS surface when
  `JM_GLASS_MODE=system`.
- Failure to apply DWM glass is logged and the program continues with a standard window.

## Runtime modes

Default experiment:

```powershell
$env:JM_GLASS_MODE = "system"
$env:JM_GLASS_MATERIAL = "acrylic"
```

Mica comparison:

```powershell
$env:JM_GLASS_MODE = "system"
$env:JM_GLASS_MATERIAL = "mica"
```

Disable native glass without changing code:

```powershell
$env:JM_GLASS_MODE = "off"
```

## Manual acceptance

1. Desktop wallpaper or its color/material is visible through the main window.
2. Sidebar and cards remain readable.
3. No white flash remains after the page loads.
4. Window maximize, restore, resize, minimize and tray restore work.
5. Links, automatic refresh, dashboard navigation and decision recalculation still work.
6. No click-through or transparent holes appear.
7. Scrolling remains smooth.

This is an experimental branch. Do not merge it before manual acceptance.
