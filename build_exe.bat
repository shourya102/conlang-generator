@echo off
setlocal
set DID_PUSHD=0

set TARGET=%~1
if "%TARGET%"=="" set TARGET=all

set BUILD_CLI=0
set BUILD_DESKTOP=0

if /I "%TARGET%"=="all" (
    set BUILD_CLI=1
    set BUILD_DESKTOP=1
) else if /I "%TARGET%"=="cli" (
    set BUILD_CLI=1
) else if /I "%TARGET%"=="desktop" (
    set BUILD_DESKTOP=1
) else (
    goto :usage
)

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    py -3 -m venv .venv
    if errorlevel 1 goto :error
)

call .venv\Scripts\activate.bat
if errorlevel 1 goto :error

echo Installing/updating Python dependencies...
python -m pip install --upgrade pip
if errorlevel 1 goto :error
python -m pip install -r requirements.txt
if errorlevel 1 goto :error

set "PYI_TMP_ROOT=%TEMP%\conlang-studio-pyinstaller"
set "PYI_NONCE=%RANDOM%%RANDOM%"
set "PYI_WORKPATH=%PYI_TMP_ROOT%\work-%PYI_NONCE%"
set "PYI_SPECPATH=%PYI_TMP_ROOT%\spec-%PYI_NONCE%"

if "%BUILD_CLI%"=="1" (
    echo Installing CLI packaging toolchain...
    python -m pip install pyinstaller
    if errorlevel 1 goto :error

    echo Downloading NLTK data for CLI runtime cache...
    python -m nltk.downloader punkt averaged_perceptron_tagger
    if errorlevel 1 goto :error

    echo Closing running CLI executable if present...
    taskkill /IM conlang-studio.exe /F >nul 2>&1

    if not exist "%PYI_TMP_ROOT%" mkdir "%PYI_TMP_ROOT%"

    echo Building CLI one-file executable...
    echo PyInstaller work path: %PYI_WORKPATH%
    python -m PyInstaller --noconfirm --clean --onefile --name conlang-studio --distpath dist --workpath "%PYI_WORKPATH%" --specpath "%PYI_SPECPATH%" src\main.py
    if errorlevel 1 goto :error
)

if "%BUILD_DESKTOP%"=="1" (
    echo Closing running desktop executable if present...
    taskkill /IM conlang-studio-desktop.exe /F >nul 2>&1

    echo Installing/updating GUI dependencies...
    pushd gui
    set DID_PUSHD=1
    call npm.cmd install
    if errorlevel 1 goto :error

    echo Building desktop EXE packages...
    call npm.cmd run build:desktop
    if errorlevel 1 (
        echo Standard desktop build failed.
        echo Retrying without EXE resource editing/signing to bypass winCodeSign symlink requirements...
        echo NOTE: Fallback mode may omit embedded EXE icon/version metadata.
        call npm.cmd run build:desktop:no-win-edit
        if errorlevel 1 goto :error
    )

    popd
    set DID_PUSHD=0
)

echo.
echo Build complete.
if "%BUILD_CLI%"=="1" (
    echo CLI EXE: %CD%\dist\conlang-studio.exe
)
if "%BUILD_DESKTOP%"=="1" (
    echo Desktop artifacts: %CD%\dist\desktop
)
goto :eof

:error
if "%DID_PUSHD%"=="1" popd
echo.
echo EXE build failed. Please review the errors above.
exit /b 1

:usage
echo Usage: build_exe.bat [all^|cli^|desktop]
exit /b 2
