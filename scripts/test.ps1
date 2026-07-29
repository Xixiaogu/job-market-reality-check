param(
    [string]$Version = "1.0.7",
    [string]$PythonPath = "",
    [string]$SourceDatabasePath = "",
    [switch]$SkipPackaged,
    [switch]$SkipInstaller
)

$ErrorActionPreference = "Stop"
$script:ProjectRoot = Split-Path -Parent $PSScriptRoot
$script:Passed = 0
$script:Python = ""

function Resolve-ProjectPython {
    $candidates = @()
    if ($PythonPath) {
        $candidates += $PythonPath
    }
    if ($env:CONDA_PREFIX) {
        $candidates += (Join-Path $env:CONDA_PREFIX "python.exe")
    }

    $currentPython = Get-Command "python.exe" -ErrorAction SilentlyContinue
    if ($currentPython) {
        $candidates += $currentPython.Source
    }

    $conda = Get-Command "conda.exe" -ErrorAction SilentlyContinue
    if ($conda) {
        $condaRoot = Split-Path -Parent (Split-Path -Parent $conda.Source)
        $baseSciencePython = Join-Path $condaRoot "envs\base_science\python.exe"
        if (Test-Path -LiteralPath $baseSciencePython) {
            $candidates += $baseSciencePython
        }
    }

    foreach ($candidate in ($candidates | Select-Object -Unique)) {
        if (-not (Test-Path -LiteralPath $candidate)) {
            continue
        }
        $previousErrorAction = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        & $candidate -c "import fastapi, uvicorn" *> $null
        $importExitCode = $LASTEXITCODE
        $ErrorActionPreference = $previousErrorAction
        if ($importExitCode -eq 0) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }

    throw "No Python interpreter with FastAPI and Uvicorn was found. Activate base_science or pass -PythonPath."
}

function Invoke-PythonTest {
    param(
        [string]$Label,
        [string[]]$Arguments
    )

    Write-Host ""
    Write-Host "[$($script:Passed + 1)] $Label" -ForegroundColor Cyan
    & $script:Python @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Test failed: $Label (exit code $LASTEXITCODE)"
    }
    $script:Passed += 1
}

function Wait-Api {
    param(
        [System.Management.Automation.Job]$Job,
        [int]$Attempts = 80
    )

    for ($attempt = 0; $attempt -lt $Attempts; $attempt++) {
        if ($Job.State -in @("Failed", "Stopped", "Completed")) {
            $details = Receive-Job -Job $Job -ErrorAction SilentlyContinue | Out-String
            throw "Local API exited before becoming healthy.`n$details"
        }
        try {
            $health = Invoke-RestMethod `
                -Uri "http://127.0.0.1:8765/api/v1/health" `
                -TimeoutSec 1
            if ($health.ok) {
                return
            }
        }
        catch {
            Start-Sleep -Milliseconds 250
        }
    }

    $details = Receive-Job -Job $Job -ErrorAction SilentlyContinue | Out-String
    throw "Local API did not become healthy.`n$details"
}

function Start-IsolatedApi {
    param(
        [string]$DatabasePath,
        [string]$OutputPath,
        [string]$LogPath,
        [string]$AppMode = "development",
        [string]$UserDataPath = ""
    )

    return Start-Job -ScriptBlock {
        param($python, $projectRoot, $database, $output, $logs, $mode, $userData)
        Set-Location -LiteralPath $projectRoot
        $env:PYTHONUTF8 = "1"
        $env:JOB_MARKET_APP_MODE = $mode
        $env:JOB_MARKET_DB_PATH = $database
        $env:JOB_MARKET_LOCAL_OUTPUT_DIR = $output
        $env:JOB_MARKET_LOG_DIR = $logs
        if ($userData) {
            $env:JOB_MARKET_USER_DATA_DIR = $userData
        }
        & $python -m uvicorn local_api.main:app --host 127.0.0.1 --port 8765
    } -ArgumentList @(
        $script:Python,
        $script:ProjectRoot,
        $DatabasePath,
        $OutputPath,
        $LogPath,
        $AppMode,
        $UserDataPath
    )
}

function Stop-IsolatedApi {
    param([System.Management.Automation.Job]$Job)

    if ($Job) {
        Stop-Job -Job $Job -ErrorAction SilentlyContinue
        Remove-Job -Job $Job -Force -ErrorAction SilentlyContinue
    }
}

function Assert-TestPortAvailable {
    $client = [Net.Sockets.TcpClient]::new()
    try {
        $connection = $client.ConnectAsync("127.0.0.1", 8765)
        if ($connection.Wait(400) -and $client.Connected) {
            throw (
                "Port 8765 is already in use. Close the running desktop or " +
                "development service before starting the isolated baseline."
            )
        }
    }
    catch [AggregateException] {
        return
    }
    catch [Net.Sockets.SocketException] {
        return
    }
    finally {
        $client.Dispose()
    }
}

function Get-TestScripts {
    param([string]$RelativeDirectory)

    $directory = Join-Path $script:ProjectRoot $RelativeDirectory
    if (-not (Test-Path -LiteralPath $directory)) {
        throw "Test directory was not found: $directory"
    }

    return @(
        Get-ChildItem -LiteralPath $directory -Filter "test_*.py" -File |
            Sort-Object Name |
            ForEach-Object { $_.FullName }
    )
}

Set-Location -LiteralPath $script:ProjectRoot
$env:PYTHONUTF8 = "1"
$pathSeparator = [IO.Path]::PathSeparator
$env:PYTHONPATH = if ($env:PYTHONPATH) {
    "$script:ProjectRoot$pathSeparator$env:PYTHONPATH"
}
else {
    $script:ProjectRoot
}
$script:Python = Resolve-ProjectPython
Assert-TestPortAvailable

Write-Host "Job Market Reality Check baseline test suite" -ForegroundColor Green
Write-Host "Python: $script:Python"
Write-Host "Version: $Version"

$offlineTests = @(
    Get-TestScripts -RelativeDirectory "tests\contracts"
    Get-TestScripts -RelativeDirectory "tests\offline"
)

foreach ($test in $offlineTests) {
    Invoke-PythonTest -Label "offline: $test" -Arguments @($test)
}

Invoke-PythonTest `
    -Label "skill workflow" `
    -Arguments @("skills\job-market-reality-check\tests\test_skill_workflow.py")
Invoke-PythonTest `
    -Label "skill local API client" `
    -Arguments @("skills\job-market-reality-check\tests\test_local_api_client.py")

$sourceDatabase = if ($SourceDatabasePath) {
    [IO.Path]::GetFullPath(
        (Join-Path $script:ProjectRoot $SourceDatabasePath)
    )
}
else {
    Join-Path $script:ProjectRoot "data\job_market.db"
}
if (-not (Test-Path -LiteralPath $sourceDatabase)) {
    throw (
        "The integration-test source database is missing: $sourceDatabase. " +
        "Create a synthetic fixture with scripts\create_ci_fixture.py or " +
        "pass -SourceDatabasePath."
    )
}

$testRoot = Join-Path $script:ProjectRoot (
    ".build\baseline-tests\" + (Get-Date -Format "yyyyMMdd-HHmmss")
)
New-Item -ItemType Directory -Path $testRoot -Force | Out-Null
$databaseCopy = Join-Path $testRoot "job_market.db"
Copy-Item -LiteralPath $sourceDatabase -Destination $databaseCopy

$developmentJob = $null
try {
    $developmentJob = Start-IsolatedApi `
        -DatabasePath $databaseCopy `
        -OutputPath (Join-Path $testRoot "development-output") `
        -LogPath (Join-Path $testRoot "development-logs")
    Wait-Api -Job $developmentJob

    $apiTests = @(
        Get-TestScripts -RelativeDirectory "tests\api\development"
        Join-Path $script:ProjectRoot (
            "skills\job-market-reality-check\tests\test_local_api_integration.py"
        )
    )
    foreach ($test in $apiTests) {
        Invoke-PythonTest -Label "API: $test" -Arguments @($test)
    }
}
finally {
    Stop-IsolatedApi -Job $developmentJob
}

$desktopRoot = Join-Path $testRoot "desktop-user-data"
$desktopJob = $null
$previousUserData = $env:JOB_MARKET_USER_DATA_DIR
$previousAppMode = $env:JOB_MARKET_APP_MODE
try {
    $env:JOB_MARKET_USER_DATA_DIR = $desktopRoot
    $env:JOB_MARKET_APP_MODE = "desktop"
    $desktopJob = Start-IsolatedApi `
        -DatabasePath (Join-Path $desktopRoot "data\job_market.db") `
        -OutputPath (Join-Path $desktopRoot "output") `
        -LogPath (Join-Path $desktopRoot "logs") `
        -AppMode "desktop" `
        -UserDataPath $desktopRoot
    Wait-Api -Job $desktopJob
    Invoke-PythonTest `
        -Label "desktop API mode" `
        -Arguments @(
            Join-Path $script:ProjectRoot (
                "tests\api\desktop\test_desktop_mode_api.py"
            )
        )
}
finally {
    Stop-IsolatedApi -Job $desktopJob
    $env:JOB_MARKET_USER_DATA_DIR = $previousUserData
    $env:JOB_MARKET_APP_MODE = $previousAppMode
}

$releaseDir = Join-Path $script:ProjectRoot (
    "release\JobMarketDecisionSystem-v" + $Version + "-desktop"
)
if (-not $SkipPackaged) {
    Invoke-PythonTest `
        -Label "packaged desktop smoke" `
        -Arguments @(
            (Join-Path $script:ProjectRoot (
                "tests\release\test_portable_package_smoke.py"
            )),
            "--release-dir",
            $releaseDir
        )
}

if (-not $SkipInstaller) {
    $installer = Join-Path $script:ProjectRoot (
        "release\installer\JobMarketDecisionSystem-Setup-v" + $Version + ".exe"
    )
    Invoke-PythonTest `
        -Label "installer smoke" `
        -Arguments @(
            (Join-Path $script:ProjectRoot (
                "tests\release\test_installer_smoke.py"
            )),
            "--installer",
            $installer,
            "--expected-version",
            $Version
        )
}

Write-Host ""
Write-Host "Baseline test suite passed: $script:Passed test groups." -ForegroundColor Green
Write-Host "Isolated test artifacts: $testRoot"
