@echo off
setlocal
set DID_PUSHD=0

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Creating Python virtual environment...
    py -3 -m venv .venv
    if errorlevel 1 goto :error
)

call .venv\Scripts\activate.bat
if errorlevel 1 goto :error

echo Installing/updating Python requirements...
python -m pip install --upgrade pip
if errorlevel 1 goto :error
python -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo Bootstrapping NLTK data...
python -m nltk.downloader punkt averaged_perceptron_tagger
if errorlevel 1 goto :error

echo Installing/updating GUI dependencies...
pushd gui
set DID_PUSHD=1
call npm.cmd install
if errorlevel 1 goto :error

echo Launching Electron GUI...
call npm.cmd run dev
if errorlevel 1 goto :error
if "%DID_PUSHD%"=="1" popd

goto :eof

:error
if "%DID_PUSHD%"=="1" popd
echo.
echo GUI bootstrap failed. Please review the errors above.
exit /b 1
