@echo off
REM ============================================================
REM 跳舞兰 H5 电商系统 · 一键启动
REM 双击这个文件即可
REM ============================================================

cd /d "%~dp0.."
powershell -ExecutionPolicy Bypass -File "scripts\start.ps1"

pause
