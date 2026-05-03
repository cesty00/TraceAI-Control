param(
    [string]$AppName = 'TraceAI-Control',
    [string]$AppVersion = '0.5.0',
    [string]$BuildChannel = 'github-actions-installer',
    [string]$BuildCommit = '',
    [switch]$SkipTests
)

$ErrorActionPreference = 'Stop'

Write-Host 'TraceAI Control - Windows build' -ForegroundColor Cyan

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..')
Set-Location $RepoRoot

$EntryPoint = Join-Path $RepoRoot 'src\ui\visual.py'
if (-not (Test-Path $EntryPoint)) {
    throw "Entry point not found: $EntryPoint"
}

if ([string]::IsNullOrWhiteSpace($BuildCommit)) {
    try {
        $BuildCommit = (git rev-parse HEAD).Trim()
    }
    catch {
        $BuildCommit = 'UNKNOWN'
    }
}

if (-not $SkipTests) {
    Write-Host 'Running tests...' -ForegroundColor Cyan
    python -m pytest -q
}

Write-Host 'Checking PyInstaller...' -ForegroundColor Cyan
python -m PyInstaller --version | Out-Host

Write-Host 'Cleaning previous build artifacts...' -ForegroundColor Cyan
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue '.\build', ".\dist\$AppName", ".\$AppName.spec"

$MetadataDir = Join-Path $RepoRoot 'build\metadata'
New-Item -ItemType Directory -Force -Path $MetadataDir | Out-Null
$MetadataPath = Join-Path $MetadataDir 'traceai_build_info.json'
$BuildDate = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
$Metadata = [ordered]@{
    app_version = $AppVersion
    build_commit = $BuildCommit
    build_date = $BuildDate
    build_channel = $BuildChannel
}
$Metadata | ConvertTo-Json -Depth 3 | Set-Content -Path $MetadataPath -Encoding UTF8
Write-Host "Build metadata written: $MetadataPath" -ForegroundColor Cyan
Get-Content $MetadataPath | Out-Host

$AddDataSeparator = if ($IsWindows -or $env:OS -eq 'Windows_NT') { ';' } else { ':' }
$AddDataArg = "$MetadataPath$AddDataSeparator."

Write-Host 'Building executable...' -ForegroundColor Cyan
$PyInstallerArgs = @(
    '--name', $AppName,
    '--onedir',
    '--windowed',
    '--clean',
    '--noconfirm',
    '--collect-submodules', 'src',
    '--add-data', $AddDataArg,
    $EntryPoint
)

python -m PyInstaller @PyInstallerArgs

$BuildFolder = Join-Path $RepoRoot "dist\$AppName"
$ExePath = Join-Path $BuildFolder "$AppName.exe"

if (-not (Test-Path $ExePath)) {
    throw "Build failed. Executable not found: $ExePath"
}

$PackagedMetadata = Join-Path $BuildFolder 'traceai_build_info.json'
Copy-Item -Force $MetadataPath $PackagedMetadata
if (-not (Test-Path $PackagedMetadata)) {
    throw "Build failed. Metadata not found next to executable: $PackagedMetadata"
}

Write-Host 'Build completed successfully.' -ForegroundColor Green
Write-Host "Executable: $ExePath" -ForegroundColor Green
Write-Host "Metadata: $PackagedMetadata" -ForegroundColor Green
