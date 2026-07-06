@echo off
rem -------------------------------------------------
rem AlphaMed Voice AI - Server Launcher
rem Uses C:\Users\%USERNAME%\va_venv (avoids Windows long-path issues)
rem -------------------------------------------------

cd /d "%~dp0"

set VENV=%USERPROFILE%\va_venv

rem Check if our custom venv exists, otherwise create it
if not exist "%VENV%\Scripts\activate.bat" (
    echo Creating virtual environment at %VENV% ...
    python -m venv "%VENV%"
    call "%VENV%\Scripts\activate.bat"
    pip install -r backend\requirements.txt
) else (
    call "%VENV%\Scripts\activate.bat"
)

echo.
echo Starting AlphaMed Voice AI backend...
echo Open: http://127.0.0.1:8000
echo.

rem Start FastAPI with auto-reload
python -u -m uvicorn backend.app.main:app --reload

pause
