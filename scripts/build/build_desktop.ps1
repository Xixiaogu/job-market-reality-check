param(
    [string]$ProjectRoot = "",
    [string]$Version = "1.0.7",
    [string]$PythonPath = ""
)

$ErrorActionPreference = "Stop"

function Fail([string]$Message) {
    Write-Host ""
    Write-Host "ERROR: $Message" -ForegroundColor Red
    exit 1
}

if (-not $ProjectRoot) {
    $ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
}
$root = (Resolve-Path -LiteralPath $ProjectRoot).Path
if (-not $PythonPath) {
    $pythonCommand = Get-Command "python.exe" -ErrorAction SilentlyContinue
    if (-not $pythonCommand) {
        Fail "Python was not found. Pass -PythonPath with an explicit interpreter."
    }
    $PythonPath = $pythonCommand.Source
}
if (-not (Test-Path -LiteralPath $PythonPath)) {
    Fail "Python interpreter was not found: $PythonPath"
}

if ($Version -notmatch '^\d+\.\d+\.\d+$') {
    Fail "Version must use semantic format such as 1.0.1."
}

$requiredFiles = @(
    "desktop\app.py",
    "desktop\runtime.py",
    "local_api\main.py",
    "local_api\pipeline.py",
    "packaging\pyinstaller\desktop.spec",
    "packaging\generate_branding.py",
    "packaging\branding\app_icon.ico",
    "packaging\branding\app_icon.png",
    "tests\contracts\test_desktop_shell.py",
    "tests\contracts\test_desktop_productization.py",
    "tests\release\test_portable_package_smoke.py",
    "packaging\README_FIRST.txt",
    "packaging\浏览器扩展安装说明.txt",
    "packaging\数据与隐私说明.txt",
    "pipeline\clean_jobs.py",
    "pipeline\analyze_jobs.py",
    "pipeline\audit_skills.py",
    "pipeline\build_dashboard.py"
)

foreach ($relativePath in $requiredFiles) {
    $fullPath = Join-Path $root $relativePath
    if (-not (Test-Path -LiteralPath $fullPath)) {
        Fail "Required build file was not found: $fullPath"
    }
}

$extensionCandidates = @(
    (Join-Path $root "extension\.output\chrome-mv3"),
    (Join-Path $root "extension\.output\chrome-mv3-dev"),
    (Join-Path $root "browser-extension\chrome-mv3")
)
$extensionDir = $extensionCandidates |
    Where-Object { Test-Path -LiteralPath (Join-Path $_ "manifest.json") } |
    Select-Object -First 1

if (-not $extensionDir) {
    Fail "No built Chrome Manifest V3 extension was found."
}

Write-Host "Checking desktop-shell dependencies..." -ForegroundColor Cyan
& $PythonPath -c "import webview, pystray, PIL, PyInstaller; print('pywebview', webview.__version__ if hasattr(webview, '__version__') else 'installed'); print('pystray installed'); print('Pillow', PIL.__version__); print('PyInstaller', PyInstaller.__version__)"
if ($LASTEXITCODE -ne 0) {
    Fail "Desktop-shell Python dependencies are missing."
}

Write-Host "Regenerating product icon..." -ForegroundColor Cyan
& $PythonPath (Join-Path $root "packaging\generate_branding.py")
if ($LASTEXITCODE -ne 0) {
    Fail "Branding generation failed."
}

Write-Host "Running source syntax checks..." -ForegroundColor Cyan
& $PythonPath -m py_compile `
    (Join-Path $root "desktop\app.py") `
    (Join-Path $root "desktop\runtime.py") `
    (Join-Path $root "tests\contracts\test_desktop_shell.py")
if ($LASTEXITCODE -ne 0) {
    Fail "Python syntax check failed."
}

Write-Host "Running desktop-shell source tests..." -ForegroundColor Cyan
Push-Location $root
try {
    & $PythonPath -m tests.contracts.test_desktop_shell
    if ($LASTEXITCODE -ne 0) {
        Fail "Desktop-shell source tests failed."
    }

    & $PythonPath -m tests.contracts.test_desktop_productization
    if ($LASTEXITCODE -ne 0) {
        Fail "Desktop productization contract tests failed."
    }
}
finally {
    Pop-Location
}

$parts = $Version.Split(".")
$quad = "$($parts[0]), $($parts[1]), $($parts[2]), 0"
$versionInfo = @"
# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=($quad),
    prodvers=($quad),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          u'080404B0',
          [
            StringStruct(u'CompanyName', u'Job Market Reality Check'),
            StringStruct(u'FileDescription', u'招聘市场分析与投递决策系统'),
            StringStruct(u'FileVersion', u'$Version'),
            StringStruct(u'InternalName', u'JobMarketDecisionSystem'),
            StringStruct(u'LegalCopyright', u'Copyright (c) 2026'),
            StringStruct(u'OriginalFilename', u'JobMarketDecisionSystem.exe'),
            StringStruct(u'ProductName', u'招聘市场分析与投递决策系统'),
            StringStruct(u'ProductVersion', u'$Version')
          ]
        )
      ]
    ),
    VarFileInfo([VarStruct(u'Translation', [2052, 1200])])
  ]
)
"@
$versionInfoPath = Join-Path $root "packaging\windows_version_info_shell.txt"
[System.IO.File]::WriteAllText(
    $versionInfoPath,
    $versionInfo,
    [System.Text.UTF8Encoding]::new($true)
)

$buildRoot = Join-Path $root ".build\desktop-shell"
$distRoot = Join-Path $buildRoot "dist"
$workRoot = Join-Path $buildRoot "work"
$releaseRoot = Join-Path $root "release"
$releaseName = "JobMarketDecisionSystem-v$Version-desktop"
$releaseDir = Join-Path $releaseRoot $releaseName
$zipPath = Join-Path $releaseRoot ($releaseName + "-windows-x64.zip")
$hashPath = $zipPath + ".sha256"

if (Test-Path -LiteralPath $releaseDir) {
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $backupDir = Join-Path $root ("local-backups\desktop-shell-previous-release-" + $timestamp)
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
    Move-Item -LiteralPath $releaseDir -Destination $backupDir -Force
    Write-Host "Previous desktop-shell release moved to: $backupDir" -ForegroundColor Yellow
}

Remove-Item -LiteralPath $buildRoot -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $zipPath -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $hashPath -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $distRoot -Force | Out-Null
New-Item -ItemType Directory -Path $workRoot -Force | Out-Null
New-Item -ItemType Directory -Path $releaseRoot -Force | Out-Null

$env:JOB_MARKET_BUILD_ROOT = $root

Write-Host "Building native desktop-shell release..." -ForegroundColor Cyan
Push-Location $root
try {
    & $PythonPath -m PyInstaller `
        --noconfirm `
        --clean `
        --distpath $distRoot `
        --workpath $workRoot `
        (Join-Path $root "packaging\pyinstaller\desktop.spec")

    if ($LASTEXITCODE -ne 0) {
        Fail "PyInstaller desktop-shell build failed."
    }
}
finally {
    Pop-Location
    Remove-Item Env:\JOB_MARKET_BUILD_ROOT -ErrorAction SilentlyContinue
}

$builtDir = Join-Path $distRoot "JobMarketDecisionSystem"
$builtExe = Join-Path $builtDir "JobMarketDecisionSystem.exe"
if (-not (Test-Path -LiteralPath $builtExe)) {
    Fail "Built executable was not found: $builtExe"
}

New-Item -ItemType Directory -Path $releaseDir -Force | Out-Null
Copy-Item -Path (Join-Path $builtDir "*") -Destination $releaseDir -Recurse -Force

$releaseExtensionDir = Join-Path $releaseDir "browser-extension\chrome-mv3"
New-Item -ItemType Directory -Path $releaseExtensionDir -Force | Out-Null
Copy-Item -Path (Join-Path $extensionDir "*") -Destination $releaseExtensionDir -Recurse -Force

$releaseDocs = Join-Path $releaseDir "docs"
New-Item -ItemType Directory -Path $releaseDocs -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $root "packaging\README_FIRST.txt") -Destination (Join-Path $releaseDir "README_FIRST.txt") -Force
Copy-Item -LiteralPath (Join-Path $root "packaging\浏览器扩展安装说明.txt") -Destination $releaseDocs -Force
Copy-Item -LiteralPath (Join-Path $root "packaging\数据与隐私说明.txt") -Destination $releaseDocs -Force
Copy-Item -LiteralPath (Join-Path $root "packaging\branding\app_icon.png") -Destination $releaseDocs -Force

$versionPayload = [ordered]@{
    product = "JobMarketDecisionSystem"
    display_name = "招聘市场分析与投递决策系统"
    version = $Version
    platform = "windows-x64"
    package_mode = "pyinstaller-onedir-pywebview"
    desktop_shell = "pywebview-edgechromium"
    system_tray = $true
    built_at = (Get-Date).ToString("o")
    extension_manifest_version = 3
}
$versionPayload |
    ConvertTo-Json -Depth 4 |
    Set-Content -LiteralPath (Join-Path $releaseDir "version.json") -Encoding UTF8

$forbidden = Get-ChildItem -LiteralPath $releaseDir -Recurse -File |
    Where-Object {
        $_.Extension -in @(".db", ".sqlite", ".sqlite3") -or
        $_.Name -match "^(api[_-]?token|desktop_state|migration)\." -or
        $_.Name -match "^\.env"
    }

if ($forbidden) {
    $paths = ($forbidden | ForEach-Object FullName) -join "`n"
    Fail "Private runtime files were found in the release:`n$paths"
}

Write-Host "Running packaged headless smoke test..." -ForegroundColor Cyan
Push-Location $root
try {
    & $PythonPath -m tests.release.test_portable_package_smoke `
        --release-dir $releaseDir
    if ($LASTEXITCODE -ne 0) {
        Fail "Packaged release smoke test failed."
    }
}
finally {
    Pop-Location
}

Write-Host "Creating desktop-shell ZIP release..." -ForegroundColor Cyan
Compress-Archive -LiteralPath $releaseDir -DestinationPath $zipPath -CompressionLevel Optimal -Force

if (-not (Test-Path -LiteralPath $zipPath)) {
    Fail "Desktop-shell ZIP was not created."
}

$hash = Get-FileHash -LiteralPath $zipPath -Algorithm SHA256
($hash.Hash.ToLowerInvariant() + "  " + (Split-Path -Leaf $zipPath)) |
    Set-Content -LiteralPath $hashPath -Encoding ASCII

Write-Host ""
Write-Host "Desktop shell release build passed." -ForegroundColor Green
Write-Host "Release directory: $releaseDir"
Write-Host "Executable: $releaseDir\JobMarketDecisionSystem.exe"
Write-Host "ZIP package: $zipPath"
Write-Host "SHA256: $hashPath"
