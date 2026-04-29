param(
    [string]$AppName = "TraceAI-Control",
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"

Write-Host "TraceAI Control — Windows build" -ForegroundColor Cyan

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $RepoRoot

if (-not $SkipTests) {
    Write-Host "Running tests..." -ForegroundColor Cyan
    python -m pytest -q
}

Write-Host "Checking PyInstaller..." -ForegroundColor Cyan
python -m PyInstaller --version | Out-Host

Write-Host "Cleaning previous build artifacts..." -ForegroundColor Cyan
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue ".\build", ".\dist\$AppName", ".\$AppName.spec"

Write-Host "Building executable..." -ForegroundColor Cyan
python -m PyInstaller `
    --name $AppName `
    --onedir `
    --windowed `
    --clean `
    --noconfirm `
    --collect-submodules src `
    -m src.ui.visual

$ExePath = Join-Path $RepoRoot "dist\$AppName\$AppName.exe"

if (-not (Test-Path $ExePath)) {
    throw "Build failed. Executable not found: $ExePath"
}

Write-Host "Build completed successfully." -ForegroundColor Green
Write-Host "Executable: $ExePath" -ForegroundColor Green
