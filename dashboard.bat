@echo off
cd /d C:\Users\mikem\soap-agent\soap-agent
call .venv\Scripts\activate.bat
echo Starting dashboard...
start http://localhost:5000
python dashboard.py
pause
