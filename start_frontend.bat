@echo off
echo ============================================
echo    Chart-to-Table Converter - Frontend
echo ============================================
echo.

cd /d "%~dp0frontend"

echo Installing npm dependencies...
call npm install

echo.
echo Starting Vite dev server...
echo (Frontend will be available at http://localhost:5173)
echo.

:: Use local Vite from node_modules to avoid global conflicts
call .\node_modules\.bin\vite

pause
