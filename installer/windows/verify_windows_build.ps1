param(
    [string]$AppName = "TraceAI-Control"
)

$ErrorActionPreference = "Stop"

Write-Host "TraceAI Control — Windows build verification" -ForegroundColor Cyan

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $RepoRoot

$ExePath = Join-Path $RepoRoot "dist\$AppName\$AppName.exe"
$BuildFolder = Join-Path $RepoRoot "dist\$AppName"

if (-not (Test-Path $BuildFolder)) {
    throw "Build folder not found: $BuildFolder. Run installer\windows\build_windows.ps1 first."
}

if (-not (Test-Path $ExePath)) {
    throw "Executable not found: $ExePath. Run installer\windows\build_windows.ps1 first."
}

$ExecutableInfo = Get-Item $ExePath
if ($ExecutableInfo.Length -le 0) {
    throw "Executable is empty: $ExePath"
}

Write-Host "Build artifact found." -ForegroundColor Green
Write-Host "Executable: $ExePath" -ForegroundColor Green
Write-Host "Size bytes: $($ExecutableInfo.Length)" -ForegroundColor Green

Write-Host "Manual smoke test:" -ForegroundColor Cyan
Write-Host "1. Start the executable:" -ForegroundColor Cyan
Write-Host "   .\dist\$AppName\$AppName.exe"
Write-Host "2. Confirm the visual form opens."
Write-Host "3. Select the official source folder."
Write-Host "4. Enter code and lot."
Write-Host "5. Select output DOCX path."
Write-Host "6. Generate the report."
Write-Host "7. Confirm the DOCX file is created."

Write-Host "Verification completed." -ForegroundColor Green
