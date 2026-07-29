param(
    [Parameter(Mandatory = $true)]
    [string]$InputPath,

    [string]$PythonExecutable = "python",

    [switch]$Replace,

    [switch]$OpenDashboard
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot

if (-not $projectRoot) {
    $projectRoot = (Get-Location).Path
}

Set-Location $projectRoot

$requiredFiles = @(
    ".\local_api\extension_import.py",
    ".\pipeline\clean_jobs.py",
    ".\pipeline\analyze_jobs.py",
    ".\pipeline\audit_skills.py",
    ".\pipeline\build_dashboard.py"
)

$missingFiles = @(
    $requiredFiles |
        Where-Object {
            -not (Test-Path $_)
        }
)

if ($missingFiles.Count -gt 0) {
    throw (
        "缺少以下文件：`n" +
        ($missingFiles -join "`n")
    )
}

if (-not (Test-Path $InputPath)) {
    throw "找不到扩展 JSONL：$InputPath"
}

function Invoke-PipelineStep {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,

        [Parameter(Mandatory = $true)]
        [scriptblock]$Command
    )

    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host $Name -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan

    & $Command

    if ($LASTEXITCODE -ne 0) {
        throw "$Name 失败，退出码：$LASTEXITCODE"
    }
}

$resolvedInput = (
    Resolve-Path $InputPath
).Path

$importArguments = @(
    "-m",
    "local_api.extension_import",
    "--input",
    $resolvedInput
)

if ($Replace) {
    $importArguments += "--replace"
}

Invoke-PipelineStep `
    -Name "1/5 导入浏览器扩展岗位" `
    -Command {
        & $PythonExecutable @importArguments
    }

Invoke-PipelineStep `
    -Name "2/5 清洗岗位字段" `
    -Command {
        & $PythonExecutable -m pipeline.clean_jobs
    }

Invoke-PipelineStep `
    -Name "3/5 生成基础岗位分析" `
    -Command {
        & $PythonExecutable -m pipeline.analyze_jobs
    }

Invoke-PipelineStep `
    -Name "4/5 执行技能证据审计" `
    -Command {
        & $PythonExecutable -m pipeline.audit_skills
    }

Invoke-PipelineStep `
    -Name "5/5 生成可视化看板" `
    -Command {
        & $PythonExecutable -m pipeline.build_dashboard
    }

$dashboardPath = Join-Path `
    $projectRoot `
    "output\visualization_v1_1\visual_dashboard_v11.html"

if (-not (Test-Path $dashboardPath)) {
    throw "流程执行结束，但没有找到最终看板：$dashboardPath"
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "浏览器扩展 → Python 分析管线闭环完成" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host "扩展输入：$resolvedInput"
Write-Host "导入报告：$projectRoot\output\extension_import\import_report.json"
Write-Host "清洗结果：$projectRoot\output\boss_cleaned\jobs_cleaned.jsonl"
Write-Host "技能审计：$projectRoot\output\analysis_v1_1\jobs_skill_audited.jsonl"
Write-Host "最终看板：$dashboardPath"

if ($OpenDashboard) {
    Start-Process $dashboardPath
}
