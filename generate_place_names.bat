@echo off
setlocal

cd /d "%~dp0"

set "COUNT=%~1"
if "%COUNT%"=="" set "COUNT=30"

set "LANGUAGE=%~2"
if "%LANGUAGE%"=="" set "LANGUAGE=imperial"

if exist ".venv\Scripts\python.exe" (
    set "PYTHON_CMD=.venv\Scripts\python.exe"
) else (
    set "PYTHON_CMD=py -3"
)

echo Generating %COUNT% place names for language "%LANGUAGE%"...
call %PYTHON_CMD% src\main.py generate --language "%LANGUAGE%" --kind name --category place --count %COUNT%
if errorlevel 1 (
    echo.
    echo Place-name generation failed.
    exit /b 1
)

echo.
echo Done.
