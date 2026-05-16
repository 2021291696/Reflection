@echo off
cd /d "%~dp0"

set "INSTALL_DIR=%LOCALAPPDATA%\Reflection"

echo.
echo    Reflection Setup
echo    ----------------
echo.
echo [1/2] Installing...

if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
copy /y "Reflection.exe" "%INSTALL_DIR%\Reflection.exe" >nul 2>&1
if errorlevel 1 (
    echo Failed. Close other programs and try again.
    timeout /t 5 >nul
    exit
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0shortcut.ps1"

echo [2/2] Done
echo.
echo Double-click [Reflection] on your desktop to start.
timeout /t 3 >nul
exit
