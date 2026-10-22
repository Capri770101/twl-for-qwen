@echo off
REM ============================================================
REM  Tiaowulan H5 E-commerce - One-click launcher
REM
REM  This file is intentionally ASCII-only.
REM  On a zh-CN Windows, cmd.exe runs code page 936 (GBK); any
REM  UTF-8 Chinese text inside a .bat is mangled before it is
REM  parsed. All Chinese messages live in scripts\start.ps1.
REM
REM  Do NOT save this file with a BOM: cmd.exe would try to
REM  execute the BOM bytes as part of the first command.
REM ============================================================

setlocal
chcp 65001 >nul 2>&1
cd /d "%~dp0"

set "PS1=%~dp0scripts\start.ps1"

if not exist "%PS1%" (
    echo.
    echo [ERROR] Launcher script not found:
    echo         "%PS1%"
    echo.
    pause
    exit /b 1
)

where powershell.exe >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] powershell.exe not found in PATH.
    echo         Windows PowerShell 5.1 or later is required.
    echo.
    pause
    exit /b 1
)

powershell.exe -NoProfile -NoLogo -ExecutionPolicy Bypass -File "%PS1%" %*
set "RC=%ERRORLEVEL%"

if not "%RC%"=="0" (
    echo.
    echo [Launcher] start.ps1 exited with code %RC%
)

if not defined TWL_NO_PAUSE (
    echo.
    echo Press any key to close this window . . .
    pause >nul
)

endlocal & exit /b %RC%