@echo off
rem -------------------------------------------------
rem Simple script to run the AlphaMed Voice AI backend
rem -------------------------------------------------

rem Change to project root (already there when double‑clicked)
cd "%~dp0"

rem Optional: create/activate a virtual environment
if not exist .venv (
    python -m venv .venv
)
call .venv\Scripts\activate

rem Install / upgrade dependencies (no‑op if already satisfied)
pip install -r backend\requirements.txt

rem Start the FastAPI server (auto‑reload enabled)
uvicorn backend.app.main:app --reload

pause
