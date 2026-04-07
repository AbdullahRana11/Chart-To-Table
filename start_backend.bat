@echo off
echo ============================================
echo    Chart-to-Table Converter - Backend
echo ============================================
echo.

cd /d "%~dp0backend"

echo Installing Python dependencies...
pip install -r requirements.txt

echo.
echo Starting Flask server on port 5000...
echo (Model loading may take 1-2 minutes on first run)
echo.

python app.py

pause
