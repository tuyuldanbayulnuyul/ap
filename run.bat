@echo off
echo ============================================
echo   INTERBANK SETTLEMENT TERMINAL - Launcher
echo ============================================
echo.
echo [1] Start Desktop App (GUI)
echo [2] Start Web Panel (Config)
echo [3] Start Both
echo.
set /p choice="Select option: "

if "%choice%"=="1" goto gui
if "%choice%"=="2" goto web
if "%choice%"=="3" goto both
goto end

:gui
echo Starting GUI App...
start python interbank_gui.py
goto end

:web
echo Starting Web Panel on http://127.0.0.1:5000
python web_panel.py
goto end

:both
echo Starting Web Panel...
start python web_panel.py
timeout /t 2
echo Starting GUI App...
start python interbank_gui.py
goto end

:end
