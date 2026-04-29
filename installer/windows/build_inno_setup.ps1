param(
    [string]$AppName = 'TraceAI-Control',
    [string]$InnoSetupCompilerPath = ''
)

$ErrorActionPreference = 'Stop'

Write-Host 'TraceAI Control - Inno Setup installer build' -ForegroundColor Cyan

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..')
Set-Location $RepoRoot

$PyInstallerExe = Join-Path $RepoRoot "dist\$AppName\$AppName.exe"
if (-not (Test-Path $PyInstallerExe)) {
    throw "PyInstaller executable not found: $PyInstallerExe. Run installer\windows\build_windows.ps1 first."
}

if ([string]::IsNullOrWhiteSpace($InnoSetupCompilerPath)) {
    $CandidatePaths = @(
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
    )
    foreach ($CandidatePath in $CandidatePaths) {
        if ($CandidatePath -and (Test-Path $CandidatePath)) {
            $InnoSetupCompilerPath = $CandidatePath
            break
        }
    }
}

if ([string]::IsNullOrWhiteSpace($InnoSetupCompilerPath) -or -not (Test-Path $InnoSetupCompilerPath)) {
    throw 'Inno Setup compiler ISCC.exe not found. Install Inno Setup 6 or pass -InnoSetupCompilerPath.'
}

$InstallerScript = Join-Path $PSScriptRoot 'TraceAI-Control.iss'
if (-not (Test-Path $InstallerScript)) {
    throw "Inno Setup script not found: $InstallerScript"
}

Write-Host "Using Inno Setup compiler: $InnoSetupCompilerPath" -ForegroundColor Cyan
Write-Host "Using installer script: $InstallerScript" -ForegroundColor Cyan

& $InnoSetupCompilerPath $InstallerScript

$InstallerOutput = Join-Path $PSScriptRoot 'output\TraceAI-Control-Setup.exe'
if (-not (Test-Path $InstallerOutput)) {
    throw "Installer build failed. Output not found: $InstallerOutput"
}

Write-Host 'Installer build completed successfully.' -ForegroundColor Green
Write-Host "Installer: $InstallerOutput" -ForegroundColor Green
