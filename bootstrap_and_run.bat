@echo off
setlocal

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    py -3 -m venv .venv
    if errorlevel 1 goto :error
)

call .venv\Scripts\activate.bat
if errorlevel 1 goto :error

echo Installing/updating requirements...
python -m pip install --upgrade pip
if errorlevel 1 goto :error
python -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo Bootstrapping NLTK data...
python -m nltk.downloader punkt averaged_perceptron_tagger
if errorlevel 1 goto :error

echo Launching Conlang Studio interactive mode...
python -m src.main interactive --storage-dir src\languages
if errorlevel 1 goto :error

goto :eof

:error
echo.
echo Bootstrap failed. Please review the error output above.
exit /b 1
