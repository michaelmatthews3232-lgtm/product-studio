@echo off
cd /d C:\Users\mikem\soap-agent\soap-agent
call .venv\Scripts\activate.bat

if "%~1"=="" (
    echo ERROR: Drop a candle photo onto this file to run the pipeline.
    pause
    exit /b 1
)

echo.
echo === Running candle pipeline for: %~nx1 ===
echo.

copy "%~1" "inputs\%~nx1" >nul
python run.py "inputs\%~nx1" --product candle

echo.
echo === Done! Upload the .zip file from the output folder to Fiverr ===
echo.
explorer output
pause
