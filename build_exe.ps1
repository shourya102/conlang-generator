param(
    [ValidateSet('all', 'cli', 'desktop')]
    [string]$Target = 'all'
)

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

$buildCli = $Target -eq 'all' -or $Target -eq 'cli'
$buildDesktop = $Target -eq 'all' -or $Target -eq 'desktop'

if (-not (Test-Path '.venv\Scripts\python.exe')) {
    Write-Host 'Creating virtual environment...'
    py -3 -m venv .venv
}

$pythonExe = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'

Write-Host 'Installing/updating Python dependencies...'
& $pythonExe -m pip install --upgrade pip
& $pythonExe -m pip install -r requirements.txt

if ($buildCli) {
    Write-Host 'Installing CLI packaging toolchain...'
    & $pythonExe -m pip install pyinstaller

    Write-Host 'Bootstrapping NLTK data for CLI runtime...'
    & $pythonExe -m nltk.downloader punkt averaged_perceptron_tagger

    Write-Host 'Closing running CLI executable if present...'
    Stop-Process -Name 'conlang-studio' -Force -ErrorAction SilentlyContinue

    $pyiTmpRoot = Join-Path $env:TEMP 'conlang-studio-pyinstaller'
    New-Item -ItemType Directory -Force -Path $pyiTmpRoot | Out-Null
    $nonce = Get-Date -Format 'yyyyMMddHHmmssfff'
    $pyiWorkPath = Join-Path $pyiTmpRoot "work-$nonce"
    $pyiSpecPath = Join-Path $pyiTmpRoot "spec-$nonce"

    Write-Host 'Building CLI one-file executable...'
    Write-Host "PyInstaller work path: $pyiWorkPath"
    & $pythonExe -m PyInstaller --noconfirm --clean --onefile --name conlang-studio --distpath dist --workpath $pyiWorkPath --specpath $pyiSpecPath src\main.py
}

if ($buildDesktop) {
    Write-Host 'Closing running desktop executable if present...'
    Stop-Process -Name 'conlang-studio-desktop' -Force -ErrorAction SilentlyContinue

    Push-Location 'gui'
    try {
        Write-Host 'Installing/updating GUI dependencies...'
        & npm.cmd install

        Write-Host 'Building desktop EXE packages...'
        & npm.cmd run build:desktop
    }
    finally {
        Pop-Location
    }
}

Write-Host ''
Write-Host 'Build complete.'
if ($buildCli) {
    Write-Host "CLI EXE: $PSScriptRoot\dist\conlang-studio.exe"
}
if ($buildDesktop) {
    Write-Host "Desktop artifacts: $PSScriptRoot\dist\desktop"
}
