@echo off
REM Double-click to start the 2027 Colorado Clutch 13U Training Hub locally.
cd /d "%~dp0"
echo Starting 2027 Colorado Clutch 13U Training Hub...  (leave this window open)
echo Open your browser to:  http://127.0.0.1:5055
echo Press Ctrl+C in this window to stop.
echo.
"C:\Users\travi\.claude\bookkeeping\.venv\Scripts\python.exe" app.py
pause
