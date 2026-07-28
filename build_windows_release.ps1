param(
    [string]$ProjectRoot = (Get-Location).Path,
    [string]$Version = "1.0.0"
)

$ErrorActionPreference = "Stop"

function Fail([string]$Message) {
    Write-Host ""
    Write-Host "ERROR: $Message" -ForegroundColor Red
    exit 1
}

$root = (Resolve-Path -LiteralPath $ProjectRoot).Path

if ($env:CONDA_DEFAULT_ENV -ne "base_science") {
    Fail "Activate the base_science Conda environment before building. Current environment: $env:CONDA_DEFAULT_ENV"
}

$requiredFiles = @(
    "desktop_launcher.py",
    "local_api\main.py",
    "local_api\pipeline.py",
    "job_market_decision_system.spec",
    "packaging\windows_version_info.txt",
    "test_phase92_release.py",
    "packaging\README_FIRST.txt",
    "packaging\浏览器扩展安装说明.txt",
    "packaging\数据与隐私说明.txt",
    "clean_boss_jobs.py",
    "analyze_boss_jobs.py",
    "audit_boss_skills.py",
    "visualize_boss_jobs_v11.py"
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

Write-Host "Checking PyInstaller..." -ForegroundColor Cyan
& python -c "import PyInstaller; print('PyInstaller', PyInstaller.__version__)"
if ($LASTEXITCODE -ne 0) {
    Write-Host "PyInstaller is not installed. Installing it in base_science..." -ForegroundColor Yellow
    & python -m pip install pyinstaller
    if ($LASTEXITCODE -ne 0) {
        Fail "PyInstaller installation failed."
    }
}

Write-Host "Running source syntax checks..." -ForegroundColor Cyan
& python -m py_compile `
    (Join-Path $root "desktop_launcher.py") `
    (Join-Path $root "local_api\pipeline.py") `
    (Join-Path $root "test_phase92_release.py")
if ($LASTEXITCODE -ne 0) {
    Fail "Python syntax check failed."
}

Write-Host "Running Phase 9.1 offline regression test..." -ForegroundColor Cyan
Push-Location $root
try {
    & python .\test_phase91_offline.py
    if ($LASTEXITCODE -ne 0) {
        Fail "Phase 9.1 regression test failed."
    }
}
finally {
    Pop-Location
}

$buildRoot = Join-Path $root ".build\phase92"
$distRoot = Join-Path $buildRoot "dist"
$workRoot = Join-Path $buildRoot "work"
$releaseRoot = Join-Path $root "release"
$releaseName = "JobMarketDecisionSystem-v$Version"
$releaseDir = Join-Path $releaseRoot $releaseName
$zipPath = Join-Path $releaseRoot ($releaseName + "-windows-x64.zip")
$hashPath = $zipPath + ".sha256"

if (Test-Path -LiteralPath $releaseDir) {
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $backupDir = Join-Path $root ("local-backups\phase92-previous-release-" + $timestamp)
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
    Move-Item -LiteralPath $releaseDir -Destination $backupDir -Force
    Write-Host "Previous release moved to: $backupDir" -ForegroundColor Yellow
}

Remove-Item -LiteralPath $buildRoot -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $zipPath -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $hashPath -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $distRoot -Force | Out-Null
New-Item -ItemType Directory -Path $workRoot -Force | Out-Null
New-Item -ItemType Directory -Path $releaseRoot -Force | Out-Null

$env:JOB_MARKET_BUILD_ROOT = $root
$env:JOB_MARKET_BUILD_VERSION = $Version

Write-Host "Building Windows onedir release..." -ForegroundColor Cyan
Push-Location $root
try {
    & python -m PyInstaller `
        --noconfirm `
        --clean `
        --distpath $distRoot `
        --workpath $workRoot `
        (Join-Path $root "job_market_decision_system.spec")

    if ($LASTEXITCODE -ne 0) {
        Fail "PyInstaller build failed."
    }
}
finally {
    Pop-Location
    Remove-Item Env:\JOB_MARKET_BUILD_ROOT -ErrorAction SilentlyContinue
    Remove-Item Env:\JOB_MARKET_BUILD_VERSION -ErrorAction SilentlyContinue
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

$versionPayload = [ordered]@{
    product = "JobMarketDecisionSystem"
    display_name = "招聘市场分析与投递决策系统"
    version = $Version
    platform = "windows-x64"
    package_mode = "pyinstaller-onedir"
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

Write-Host "Running packaged release smoke test..." -ForegroundColor Cyan
Push-Location $root
try {
    & python .\test_phase92_release.py --release-dir $releaseDir
    if ($LASTEXITCODE -ne 0) {
        Fail "Packaged release smoke test failed."
    }
}
finally {
    Pop-Location
}

Write-Host "Creating ZIP release..." -ForegroundColor Cyan
Compress-Archive -LiteralPath $releaseDir -DestinationPath $zipPath -CompressionLevel Optimal -Force

if (-not (Test-Path -LiteralPath $zipPath)) {
    Fail "Release ZIP was not created."
}

$hash = Get-FileHash -LiteralPath $zipPath -Algorithm SHA256
($hash.Hash.ToLowerInvariant() + "  " + (Split-Path -Leaf $zipPath)) |
    Set-Content -LiteralPath $hashPath -Encoding ASCII

Write-Host ""
Write-Host "Phase 9.2 Windows release build passed." -ForegroundColor Green
Write-Host "Release directory: $releaseDir"
Write-Host "ZIP package: $zipPath"
Write-Host "SHA256: $hashPath"
