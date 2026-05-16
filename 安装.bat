@echo off
chcp 65001 >nul
echo ========================================
echo   Reflection · 反观 安装程序
echo ========================================
echo.

set "INSTALL_DIR=%LOCALAPPDATA%\Reflection"
set "EXE_PATH=%INSTALL_DIR%\Reflection.exe"

echo [1/3] 安装到 %INSTALL_DIR% ...
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
copy /y "%~dp0Reflection.exe" "%EXE_PATH%" >nul

echo [2/3] 创建桌面快捷方式 ...
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\Reflection.lnk'); $s.TargetPath = '%EXE_PATH%'; $s.WorkingDirectory = '%INSTALL_DIR%'; $s.Description = 'Reflection · 反观'; $s.Save()"

echo [3/3] 创建开始菜单 ...
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $dir = [Environment]::GetFolderPath('StartMenu') + '\Programs\Reflection'; New-Item -ItemType Directory -Force -Path $dir | Out-Null; $s = $ws.CreateShortcut($dir + '\Reflection.lnk'); $s.TargetPath = '%EXE_PATH%'; $s.WorkingDirectory = '%INSTALL_DIR%'; $s.Description = 'Reflection · 反观'; $s.Save()"

echo.
echo 安装完成！双击桌面上的 [Reflection] 即可开始。
echo.
pause
