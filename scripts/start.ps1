# ============================================================
# 跳舞兰 H5 电商系统 · 启动脚本（Windows PowerShell）
#
# 【怎么用】
#   在项目根目录执行：
#     .\scripts\start.ps1
#
#   或者双击 scripts\start.bat
# ============================================================

$ErrorActionPreference = "Stop"

# 项目根目录（脚本在 scripts/ 下，往上一级就是根）
$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "backend"
$VenvPython = Join-Path $Backend ".venv\Scripts\python.exe"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  跳舞兰 H5 电商系统" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# ── 1. 检查虚拟环境 ──
if (-not (Test-Path $VenvPython)) {
    Write-Host "[错误] 找不到虚拟环境" -ForegroundColor Red
    Write-Host ""
    Write-Host "请先执行：" -ForegroundColor Yellow
    Write-Host "  cd backend"
    Write-Host "  python -m venv .venv"
    Write-Host "  .venv\Scripts\pip install -e ."
    Write-Host ""
    exit 1
}

# ── 2. 检查 .env ──
$EnvFile = Join-Path $Backend ".env"
if (-not (Test-Path $EnvFile)) {
    Write-Host "[提示] 没有 .env 文件，正在从模板创建..." -ForegroundColor Yellow
    Copy-Item (Join-Path $Backend ".env.example") $EnvFile
    Write-Host "[提示] 请编辑 backend\.env 填写数据库密码" -ForegroundColor Yellow
    Write-Host ""
}

# ── 3. 检查端口占用 ──
$Port = 8000
$Occupied = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($Occupied) {
    Write-Host "[提示] 端口 $Port 被占用，正在停止旧进程..." -ForegroundColor Yellow
    $Occupied | ForEach-Object {
        Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 2
}

# ── 4. 启动 ──
Write-Host "[启动] http://127.0.0.1:$Port" -ForegroundColor Green
Write-Host ""
Write-Host "  前台首页   http://127.0.0.1:$Port/" -ForegroundColor Gray
Write-Host "  管理后台   http://127.0.0.1:$Port/admin.html" -ForegroundColor Gray
Write-Host "  接口文档   http://127.0.0.1:$Port/docs" -ForegroundColor Gray
Write-Host ""
Write-Host "  按 Ctrl+C 停止" -ForegroundColor Gray
Write-Host ""

$env:PYTHONUTF8 = "1"
Set-Location $Backend
& $VenvPython -m uvicorn app.main:app --host 127.0.0.1 --port $Port
