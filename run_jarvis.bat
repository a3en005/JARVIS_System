@echo off
title J.A.R.V.I.S. Deployment System
color 0b

echo ---------------------------------------------------
echo    INITIALIZING J.A.R.V.I.S.
echo ---------------------------------------------------

:: 1. Move to the script's directory
cd /d "%~dp0"

:: 2. Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual Environment not found! 
    echo Please run: python -m venv venv
    pause
    exit
)

:: 3. Activate Virtual Environment and Launch
echo [SYSTEM] Activating Nervous System...
call venv\Scripts\activate.bat

echo [SYSTEM] Sparking Main Core...
python main.py

echo ---------------------------------------------------
echo    J.A.R.V.I.S. Session Terminated.
echo ---------------------------------------------------
pause