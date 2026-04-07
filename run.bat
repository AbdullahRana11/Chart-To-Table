@echo off
echo ============================================
echo    Chart-to-Table Converter - Full Start
echo ============================================
echo.

:: Start Frontend in background
echo Starting Frontend...
cd /d "%~dp0frontend"
start "Frontend" cmd /c "npm run dev"

:: Wait a moment for frontend to initialize
timeout /t 3 /nobreak >nul

:: Start Backend (will load model)
echo Starting Backend (model loading takes 1-2 min)...
cd /d "%~dp0backend"
python app.py
