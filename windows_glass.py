from __future__ import annotations

# WINDOWS_GLASS_EXPERIMENT_V1

import ctypes
import logging
import os
import sys
from ctypes import wintypes
from typing import Any, MutableMapping


GLASS_MODE_ENV = "JM_GLASS_MODE"
GLASS_MATERIAL_ENV = "JM_GLASS_MATERIAL"
WEBVIEW_BACKGROUND_ENV = "WEBVIEW2_DEFAULT_BACKGROUND_COLOR"

MODE_OFF = "off"
MODE_SYSTEM = "system"

MATERIAL_ACRYLIC = "acrylic"
MATERIAL_MICA = "mica"
MATERIAL_TABBED = "tabbed"

# Windows 11 DWM attributes.
DWMWA_USE_IMMERSIVE_DARK_MODE = 20
DWMWA_WINDOW_CORNER_PREFERENCE = 33
DWMWA_SYSTEMBACKDROP_TYPE = 38

DWMWCP_ROUND = 2

DWMSBT_AUTO = 0
DWMSBT_NONE = 1
DWMSBT_MAINWINDOW = 2       # Mica
DWMSBT_TRANSIENTWINDOW = 3  # Desktop Acrylic
DWMSBT_TABBEDWINDOW = 4     # Mica Alt


class MARGINS(ctypes.Structure):
    _fields_ = [
        ("cxLeftWidth", ctypes.c_int),
        ("cxRightWidth", ctypes.c_int),
        ("cyTopHeight", ctypes.c_int),
        ("cyBottomHeight", ctypes.c_int),
    ]


def normalize_glass_mode(value: str | None) -> str:
    normalized = (value or "").strip().lower()
    if normalized in {"", "1", "true", "yes", "on", "system", "glass"}:
        return MODE_SYSTEM
    if normalized in {"0", "false", "no", "off", "standard", "none"}:
        return MODE_OFF
    return MODE_SYSTEM


def normalize_material(value: str | None) -> str:
    normalized = (value or "").strip().lower()
    if normalized in {"mica", "main", "mainwindow"}:
        return MATERIAL_MICA
    if normalized in {"tabbed", "mica-alt", "mica_alt"}:
        return MATERIAL_TABBED
    return MATERIAL_ACRYLIC


def requested_mode(environ: MutableMapping[str, str] | None = None) -> str:
    target = os.environ if environ is None else environ
    return normalize_glass_mode(target.get(GLASS_MODE_ENV, MODE_SYSTEM))


def requested_material(environ: MutableMapping[str, str] | None = None) -> str:
    target = os.environ if environ is None else environ
    return normalize_material(target.get(GLASS_MATERIAL_ENV, MATERIAL_ACRYLIC))


def configure_webview_environment(
    mode: str,
    environ: MutableMapping[str, str] | None = None,
) -> dict[str, str]:
    target = os.environ if environ is None else environ
    normalized = normalize_glass_mode(mode)
    target[GLASS_MODE_ENV] = normalized

    if normalized == MODE_SYSTEM:
        # AARRGGBB. Fully transparent is supported; partial alpha is not.
        target[WEBVIEW_BACKGROUND_ENV] = "00000000"
    else:
        target.pop(WEBVIEW_BACKGROUND_ENV, None)

    return {
        "mode": normalized,
        "material": requested_material(target),
        "webview_background": target.get(WEBVIEW_BACKGROUND_ENV, ""),
    }


def windows_build_number() -> int:
    if os.name != "nt":
        return 0
    try:
        return int(sys.getwindowsversion().build)
    except Exception:
        return 0


def _hwnd_from_native(native_window: Any) -> int:
    handle = getattr(native_window, "Handle", None)
    if handle is None:
        raise RuntimeError("The native WinForms window does not expose Handle.")

    to_int64 = getattr(handle, "ToInt64", None)
    if callable(to_int64):
        return int(to_int64())

    return int(handle)


def _set_dwm_int(hwnd: int, attribute: int, value: int) -> int:
    dwmapi = ctypes.windll.dwmapi
    data = ctypes.c_int(int(value))
    return int(
        dwmapi.DwmSetWindowAttribute(
            wintypes.HWND(hwnd),
            ctypes.c_uint(attribute),
            ctypes.byref(data),
            ctypes.sizeof(data),
        )
    )


def _extend_frame(hwnd: int) -> int:
    margins = MARGINS(-1, -1, -1, -1)
    return int(
        ctypes.windll.dwmapi.DwmExtendFrameIntoClientArea(
            wintypes.HWND(hwnd),
            ctypes.byref(margins),
        )
    )


def _material_value(material: str) -> int:
    if material == MATERIAL_MICA:
        return DWMSBT_MAINWINDOW
    if material == MATERIAL_TABBED:
        return DWMSBT_TABBEDWINDOW
    return DWMSBT_TRANSIENTWINDOW


def _set_winforms_background(native_window: Any) -> list[str]:
    notes: list[str] = []
    try:
        import clr

        clr.AddReference("System.Drawing")
        from System.Drawing import Color

        native_window.BackColor = Color.Black
        notes.append("form-background=black")

        def visit(controls: Any) -> None:
            for control in controls:
                if hasattr(control, "DefaultBackgroundColor"):
                    try:
                        control.DefaultBackgroundColor = Color.Transparent
                        notes.append(
                            f"webview-background=transparent:{control.GetType().Name}"
                        )
                    except Exception:
                        logging.debug(
                            "Could not set WebView2 DefaultBackgroundColor",
                            exc_info=True,
                        )
                nested = getattr(control, "Controls", None)
                if nested is not None:
                    visit(nested)

        controls = getattr(native_window, "Controls", None)
        if controls is not None:
            visit(controls)
    except Exception:
        logging.debug(
            "Could not configure WinForms/WebView2 transparent background",
            exc_info=True,
        )
        notes.append("winforms-background=unavailable")

    return notes


def apply_windows_glass(
    native_window: Any,
    *,
    mode: str | None = None,
    material: str | None = None,
) -> dict[str, Any]:
    normalized_mode = normalize_glass_mode(
        mode if mode is not None else requested_mode()
    )
    normalized_material = normalize_material(
        material if material is not None else requested_material()
    )

    result: dict[str, Any] = {
        "requested": normalized_mode == MODE_SYSTEM,
        "applied": False,
        "mode": normalized_mode,
        "material": normalized_material,
        "build": windows_build_number(),
        "notes": [],
    }

    if normalized_mode != MODE_SYSTEM:
        result["notes"].append("glass-disabled")
        return result

    if os.name != "nt":
        result["notes"].append("not-windows")
        return result

    hwnd = _hwnd_from_native(native_window)
    result["hwnd"] = hwnd

    result["notes"].extend(_set_winforms_background(native_window))

    build = int(result["build"])
    corner_hr = _set_dwm_int(hwnd, DWMWA_WINDOW_CORNER_PREFERENCE, DWMWCP_ROUND)
    result["corner_hr"] = corner_hr

    # Extend the DWM material through the full client area.
    frame_hr = _extend_frame(hwnd)
    result["frame_hr"] = frame_hr

    if build >= 22621:
        backdrop_hr = _set_dwm_int(
            hwnd,
            DWMWA_SYSTEMBACKDROP_TYPE,
            _material_value(normalized_material),
        )
        result["backdrop_hr"] = backdrop_hr
        result["applied"] = backdrop_hr == 0
    else:
        # Official system backdrop types are available from Windows 11 build 22621.
        result["notes"].append("windows-build-does-not-support-system-backdrop")
        result["applied"] = False

    # Keep the light application appearance.
    result["dark_mode_hr"] = _set_dwm_int(
        hwnd,
        DWMWA_USE_IMMERSIVE_DARK_MODE,
        0,
    )
    return result
