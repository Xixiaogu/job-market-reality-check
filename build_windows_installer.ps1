param(
    [string]$ProjectRoot = (Get-Location).Path,
    [string]$Version = "1.0.7",
    [int]$InstallCompilerIfMissing = 1
)

$ErrorActionPreference = "Stop"

function Fail([string]$Message) {
    Write-Host ""
    Write-Host "ERROR: $Message" -ForegroundColor Red
    exit 1
}

function Find-Iscc {
    $command = Get-Command "ISCC.exe" -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    $candidates = @(
        (Join-Path $env:ProgramFiles "Inno Setup 7\ISCC.exe"),
        (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 7\ISCC.exe"),
        (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 7\ISCC.exe"),
        (Join-Path $env:ProgramFiles "Inno Setup 6\ISCC.exe"),
        (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe"),
        (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe")
    )

    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path -LiteralPath $candidate)) {
            return $candidate
        }
    }

    return $null
}

function Convert-VersionQuad([string]$SemanticVersion) {
    if ($SemanticVersion -notmatch '^\d+\.\d+\.\d+$') {
        throw "Version must use major.minor.patch format, for example 1.0.0."
    }
    return "$SemanticVersion.0"
}

$root = (Resolve-Path -LiteralPath $ProjectRoot).Path
$releaseDir = Join-Path $root ("release\JobMarketDecisionSystem-v" + $Version + "-desktop")
$releaseExe = Join-Path $releaseDir "JobMarketDecisionSystem.exe"
$releaseManifest = Join-Path $releaseDir "browser-extension\chrome-mv3\manifest.json"
$releaseVersion = Join-Path $releaseDir "version.json"
$templatePath = Join-Path $root "packaging\installer\JobMarketDecisionSystem.iss.template"
$testPath = Join-Path $root "tests\release\test_installer_smoke.py"
$outputDir = Join-Path $root "release\installer"
$buildDir = Join-Path $root ".build\phase93"
$generatedIss = Join-Path $buildDir "JobMarketDecisionSystem.iss"
$installerPath = Join-Path $outputDir ("JobMarketDecisionSystem-Setup-v" + $Version + ".exe")
$hashPath = $installerPath + ".sha256"

foreach ($requiredPath in @($releaseExe, $releaseManifest, $releaseVersion, $templatePath, $testPath)) {
    if (-not (Test-Path -LiteralPath $requiredPath)) {
        Fail "Required Phase 9.2/9.3 file was not found: $requiredPath"
    }
}

$versionPayload = Get-Content -LiteralPath $releaseVersion -Raw -Encoding UTF8 |
    ConvertFrom-Json
if ([string]$versionPayload.version -ne $Version) {
    Fail "Release version metadata does not match the requested installer version: $($versionPayload.version) != $Version"
}

$privateFiles = Get-ChildItem -LiteralPath $releaseDir -Recurse -File |
    Where-Object {
        $_.Extension -in @(".db", ".sqlite", ".sqlite3") -or
        $_.Name -match "^(api[_-]?token|desktop_state|migration)\." -or
        $_.Name -match "^\.env"
    }

if ($privateFiles) {
    $paths = ($privateFiles | ForEach-Object FullName) -join "`n"
    Fail "Private runtime files were found in the release directory:`n$paths"
}

$iscc = Find-Iscc
if (-not $iscc -and $InstallCompilerIfMissing -ne 0) {
    $winget = Get-Command "winget.exe" -ErrorAction SilentlyContinue
    if (-not $winget) {
        Fail "Inno Setup is missing and winget is unavailable. Install Inno Setup, then rerun this script."
    }

    Write-Host "Inno Setup was not found. Installing it with winget..." -ForegroundColor Yellow
    & winget install `
        --id JRSoftware.InnoSetup `
        --exact `
        --silent `
        --accept-package-agreements `
        --accept-source-agreements

    if ($LASTEXITCODE -ne 0) {
        Fail "winget could not install Inno Setup."
    }

    Start-Sleep -Seconds 2
    $iscc = Find-Iscc
}

if (-not $iscc) {
    Fail "ISCC.exe was not found. Install Inno Setup 6 or 7 and rerun the build."
}

Write-Host "Using Inno Setup compiler: $iscc" -ForegroundColor Cyan

New-Item -ItemType Directory -Path $buildDir -Force | Out-Null
New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
Remove-Item -LiteralPath $installerPath -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $hashPath -Force -ErrorAction SilentlyContinue

$template = Get-Content -LiteralPath $templatePath -Raw -Encoding UTF8
$generated = $template.
    Replace("@@VERSION@@", $Version).
    Replace("@@VERSION_QUAD@@", (Convert-VersionQuad $Version)).
    Replace("@@SOURCE_DIR@@", $releaseDir).
    Replace("@@OUTPUT_DIR@@", $outputDir)

[System.IO.File]::WriteAllText(
    $generatedIss,
    $generated,
    [System.Text.UTF8Encoding]::new($true)
)

Write-Host "Checking Python installer test syntax..." -ForegroundColor Cyan
& python -m py_compile $testPath
if ($LASTEXITCODE -ne 0) {
    Fail "Installer test syntax check failed."
}

Write-Host "Compiling Windows installer..." -ForegroundColor Cyan
& $iscc $generatedIss
if ($LASTEXITCODE -ne 0) {
    Fail "Inno Setup compilation failed."
}

if (-not (Test-Path -LiteralPath $installerPath)) {
    Fail "Installer was not created: $installerPath"
}

Write-Host "Running installer smoke test..." -ForegroundColor Cyan
& python $testPath --installer $installerPath --expected-version $Version
if ($LASTEXITCODE -ne 0) {
    Fail "Installer smoke test failed."
}

$hash = Get-FileHash -LiteralPath $installerPath -Algorithm SHA256
($hash.Hash.ToLowerInvariant() + "  " + (Split-Path -Leaf $installerPath)) |
    Set-Content -LiteralPath $hashPath -Encoding ASCII

Write-Host ""
Write-Host "Phase 9.3 Windows installer build passed." -ForegroundColor Green
Write-Host "Installer: $installerPath"
Write-Host "SHA256: $hashPath"
