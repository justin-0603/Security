@echo off
:: Control script to enable, disable, edit settings via GUI, or view security logs using dynamic paths

chcp 65001 > nul
cls

:: Get current directory where this bat file is located
set "CURRENT_DIR=%~dp0"
if "%CURRENT_DIR:~-1%"=="\" set "CURRENT_DIR=%CURRENT_DIR:~0,-1%"

:MENU
cls
echo ===================================================
echo              Security Control Center
echo ===================================================
echo.
echo  1. Disable Security Surveillance (Remove from Startup)
echo  2. Enable Security Surveillance (Add to Startup)
echo  3. Open Logs Folder
echo  4. Open Settings GUI App
echo  5. Exit
echo.
echo ===================================================
set /p choice="Select an option (1-5) and press Enter: "

if "%choice%"=="1" goto DISABLE
if "%choice%"=="2" goto ENABLE
if "%choice%"=="3" goto OPEN_LOGS
if "%choice%"=="4" goto OPEN_CONFIG_GUI
if "%choice%"=="5" goto END

:DISABLE
:: Kill running python background process and remove startup shortcut
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM pythonw.exe >nul 2>&1
schtasks /Delete /TN "SecuritySurveillanceTask" /F >nul 2>&1
schtasks /Delete /TN "SecuritySurveillanceTask_Unlock" /F >nul 2>&1

set "STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
if exist "%STARTUP_DIR%\run_security.vbs.lnk" (
    del "%STARTUP_DIR%\run_security.vbs.lnk"
)
if exist "%STARTUP_DIR%\run_security.vbs - Shortcut.lnk" (
    del "%STARTUP_DIR%\run_security.vbs - Shortcut.lnk"
)
echo.
echo [SUCCESS] Security Surveillance disabled and background process killed.
pause
goto MENU

:ENABLE
:: Kill existing instance and create startup shortcut
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM pythonw.exe >nul 2>&1

set "STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "TARGET_VBS=%CURRENT_DIR%\run_security.vbs"

powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%STARTUP_DIR%\run_security.vbs.lnk'); $s.TargetPath = '%TARGET_VBS%'; $s.WorkingDirectory = '%CURRENT_DIR%'; $s.Save()" >nul 2>&1

:: Start currently
start "" wscript.exe "%TARGET_VBS%"

echo.
echo [SUCCESS] Security Surveillance enabled and currently running in background.
echo Surveillance will automatically trigger on Boot, Logon, and Workstation Unlock.
echo Press Ctrl + Alt + K within 5 seconds after unlock to disable surveillance.
pause
goto MENU

:OPEN_LOGS
:: Open directory containing saved logs and captured images
set "LOG_DIR=%CURRENT_DIR%\Logs"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
explorer "%LOG_DIR%"
goto MENU

:OPEN_CONFIG_GUI
:: Launch GUI interface silently without spawning a black console window
start "" pythonw "%CURRENT_DIR%\config_ui.py"
goto MENU

:END
:: Exit batch execution
exit