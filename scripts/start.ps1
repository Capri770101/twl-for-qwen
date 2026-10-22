#Requires -Version 5.1
# ============================================================
# 跳舞兰 H5 电商系统 · 一键启动
#
# 用法：
#   双击项目根目录的「启动.bat」（推荐）
#   或在项目根目录执行：  .\scripts\start.ps1
#
# 参数：
#   -Port 8000    指定端口
#   -Check        只做环境自检，不启动服务
#   -NoBrowser    启动后不自动打开浏览器
#   -Reload       开启热重载（开发用）
#
# 【编码约定 · 千万不要改】
#   本文件必须保存为 UTF-8 with BOM。
#   Windows PowerShell 5.1 遇到「UTF-8 无 BOM」的 .ps1 会按系统
#   代码页（简体中文 = GBK/936）解码，中文会变成
#   「璺宠垶鍏?H5」这类乱码。BOM 是 5.1 可靠的 UTF-8 识别信号。
#   改完文件请执行 scripts\check-encoding.ps1 校验。
# ============================================================

[CmdletBinding()]
param(
    [int]$Port = 8000,
    [switch]$Check,
    [switch]$NoBrowser,
    [switch]$Reload
)

$ErrorActionPreference = 'Stop'

# ------------------------------------------------------------
# 0. 控制台编码对齐
#    cmd.exe / PowerShell / Python 三方统一到 UTF-8，
#    这是「不乱码」的真正前提，不是装饰。
# ------------------------------------------------------------
try { & chcp.com 65001 > $null 2>&1 } catch { }

try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    [Console]::InputEncoding  = [System.Text.Encoding]::UTF8
    $global:OutputEncoding    = [System.Text.Encoding]::UTF8
} catch { }

$env:PYTHONUTF8       = '1'     # Python UTF-8 模式（源码 / 文件 IO / stdio）
$env:PYTHONIOENCODING = 'utf-8' # 标准流显式 UTF-8
$env:PYTHONUNBUFFERED = '1'     # 日志实时刷出，不憋在缓冲区

# ------------------------------------------------------------
# 路径
# ------------------------------------------------------------
$Root       = Split-Path -Parent $PSScriptRoot
$Backend    = Join-Path $Root 'backend'
$VenvDir    = Join-Path $Backend '.venv'
$VenvPython = Join-Path $VenvDir 'Scripts\python.exe'
$EnvFile    = Join-Path $Backend '.env'
$EnvTpl     = Join-Path $Backend '.env.example'

$Line = '=' * 58

# ------------------------------------------------------------
# 输出辅助
# ------------------------------------------------------------
function Show-Title {
    param([string]$Text)
    Write-Host ''
    Write-Host $Line -ForegroundColor DarkCyan
    Write-Host "  $Text" -ForegroundColor Cyan
    Write-Host $Line -ForegroundColor DarkCyan
    Write-Host ''
}
function Show-Ok   { param([string]$t) Write-Host "  [ OK ]  $t" -ForegroundColor Green }
function Show-Warn { param([string]$t) Write-Host "  [WARN]  $t" -ForegroundColor Yellow }
function Show-Fail { param([string]$t) Write-Host "  [FAIL]  $t" -ForegroundColor Red }
function Show-Note { param([string]$t) Write-Host "  [ .. ]  $t" -ForegroundColor DarkGray }

# 读 KEY=VALUE 形式的 .env（不打印任何值，只用来判空/判默认值）
function Read-EnvMap {
    param([string]$Path)
    $map = @{}
    if (-not (Test-Path -LiteralPath $Path)) { return $map }
    foreach ($raw in Get-Content -LiteralPath $Path -Encoding UTF8) {
        $line = $raw.Trim()
        if (-not $line) { continue }
        if ($line.StartsWith('#')) { continue }
        $idx = $line.IndexOf('=')
        if ($idx -lt 1) { continue }
        $key = $line.Substring(0, $idx).Trim()
        $val = $line.Substring($idx + 1).Trim()
        if ($val.Length -ge 2) {
            if (($val.StartsWith('"') -and $val.EndsWith('"')) -or
                ($val.StartsWith("'") -and $val.EndsWith("'"))) {
                $val = $val.Substring(1, $val.Length - 2)
            }
        }
        $map[$key] = $val
    }
    return $map
}

# 查占用端口的 PID，Get-NetTCPConnection 不可用时回退 netstat
function Get-PortOwners {
    param([int]$PortNumber)
    $pids = @()
    try {
        $conns = Get-NetTCPConnection -LocalPort $PortNumber -State Listen -ErrorAction Stop
        $pids = @($conns | ForEach-Object { [int]$_.OwningProcess })
    } catch {
        try {
            $lines = & netstat.exe -ano -p TCP 2>$null |
                Select-String -Pattern ":$PortNumber\s" |
                Select-String -Pattern 'LISTENING'
            foreach ($l in $lines) {
                $parts = ($l.ToString().Trim() -split '\s+')
                if ($parts.Count -ge 5) {
                    $candidate = 0
                    if ([int]::TryParse($parts[$parts.Count - 1], [ref]$candidate)) {
                        $pids += $candidate
                    }
                }
            }
        } catch { }
    }
    return @($pids | Where-Object { $_ -gt 0 } | Sort-Object -Unique)
}

function Format-ProcessLabel {
    param([int]$ProcessId)
    $p = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if ($p) { return ('{0} (PID {1})' -f $p.ProcessName, $ProcessId) }
    return ('PID {0}' -f $ProcessId)
}

# ------------------------------------------------------------
# 1. 自检
# ------------------------------------------------------------
Show-Title '跳舞兰 H5 电商系统 · 启动'

$Problems = New-Object System.Collections.Generic.List[string]
$Warnings = New-Object System.Collections.Generic.List[string]

# 1.1 虚拟环境
$HasVenv = Test-Path -LiteralPath $VenvPython
if ($HasVenv) {
    $pyVer = ''
    try { $pyVer = (& $VenvPython -c "import sys;print(sys.version.split()[0])" 2>&1 | Out-String).Trim() } catch { }
    Show-Ok "Python 虚拟环境就绪（Python $pyVer）"
} else {
    Show-Fail "找不到虚拟环境：$VenvDir"
    $Problems.Add('先在 backend 目录创建虚拟环境：')
    $Problems.Add("    cd `"$Backend`"")
    $Problems.Add('    python -m venv .venv')
    $Problems.Add('    .venv\Scripts\pip install -e .')
}

# 1.2 依赖完整性
if ($HasVenv) {
    $probe = @'
import importlib.util as u
mods = ["fastapi", "uvicorn", "sqlalchemy", "pydantic"]
missing = [m for m in mods if u.find_spec(m) is None]
print(",".join(missing))
'@
    $probeFile = Join-Path $env:TEMP 'twl-dep-probe.py'
    try {
        Set-Content -LiteralPath $probeFile -Value $probe -Encoding UTF8
        $missing = (& $VenvPython $probeFile 2>&1 | Out-String).Trim()
    } catch {
        $missing = ''
    } finally {
        Remove-Item -LiteralPath $probeFile -Force -ErrorAction SilentlyContinue
    }
    if ([string]::IsNullOrWhiteSpace($missing)) {
        Show-Ok '依赖包完整（fastapi / uvicorn / sqlalchemy / pydantic）'
    } else {
        Show-Fail "缺少依赖包：$missing"
        $Problems.Add('在 backend 目录执行：.venv\Scripts\pip install -e .')
    }
}

# 1.3 .env
$HasEnv = Test-Path -LiteralPath $EnvFile
if ($HasEnv) {
    Show-Ok '.env 配置文件存在'
} elseif (Test-Path -LiteralPath $EnvTpl) {
    Show-Warn '.env 不存在，正在从 .env.example 复制'
    Copy-Item -LiteralPath $EnvTpl -Destination $EnvFile -Force
    $HasEnv = $true
    $Warnings.Add('backend\.env 是刚复制的模板，数据库密码等仍是示例值，请按实际情况填写后重启。')
} else {
    Show-Fail '.env 与 .env.example 都不存在'
    $Problems.Add('缺少 backend\.env.example，无法生成配置文件。')
}

# 1.4 关键配置项（只看是否为空 / 是否仍是模板默认值，绝不打印值）
if ($HasEnv) {
    $envMap = Read-EnvMap -Path $EnvFile
    $tplMap = Read-EnvMap -Path $EnvTpl

    $required = @('POSTGRES_HOST', 'POSTGRES_PORT', 'POSTGRES_USER', 'POSTGRES_PASSWORD', 'POSTGRES_DB', 'SECRET_KEY')
    $emptyKeys = @()
    foreach ($k in $required) {
        if (-not $envMap.ContainsKey($k) -or [string]::IsNullOrWhiteSpace($envMap[$k])) {
            $emptyKeys += $k
        }
    }
    if ($emptyKeys.Count -eq 0) {
        Show-Ok '数据库与密钥配置项已填写'
    } else {
        Show-Fail "以下配置项为空：$($emptyKeys -join ', ')"
        $Problems.Add('打开 backend\.env 填写上面这些项，然后重新运行本脚本。')
    }

    $stillTemplate = @()
    foreach ($k in @('POSTGRES_PASSWORD', 'SECRET_KEY')) {
        if ($envMap.ContainsKey($k) -and $tplMap.ContainsKey($k) -and
            $envMap[$k] -eq $tplMap[$k] -and -not [string]::IsNullOrWhiteSpace($envMap[$k])) {
            $stillTemplate += $k
        }
    }
    if ($stillTemplate.Count -gt 0) {
        $Warnings.Add("backend\.env 里的 $($stillTemplate -join '、') 仍是 .env.example 的模板值，正式环境务必更换。")
    }

    # 存储/缓存类后端启用时检查配套地址
    if ($envMap.ContainsKey('CACHE_PROVIDER') -and $envMap['CACHE_PROVIDER'] -eq 'redis') {
        if (-not $envMap.ContainsKey('REDIS_URL') -or [string]::IsNullOrWhiteSpace($envMap['REDIS_URL'])) {
            $Warnings.Add('CACHE_PROVIDER=redis 但 REDIS_URL 为空，服务可能启动失败。')
        }
    }
}

# 1.5 数据库连通性
if ($HasVenv -and $HasEnv -and $Problems.Count -eq 0) {
    Show-Note '检查数据库连通性...'
    $dbProbe = @'
import asyncio, re, sys

async def main():
    from sqlalchemy import text
    from app.core.database import engine
    try:
        async with engine.connect() as conn:
            await conn.execute(text("select 1"))
    finally:
        await engine.dispose()

try:
    asyncio.run(main())
    print("OK")
except Exception as exc:
    msg = "%s: %s" % (type(exc).__name__, exc)
    msg = re.sub(r"(?i)(password|passwd|pwd)\s*[=:]\s*\S+", r"\1=***", msg)
    msg = re.sub(r"(?i)(://[^:/@\s]+:)[^@\s]+@", r"\1***@", msg)
    print("ERR " + msg[:300])
    sys.exit(1)
'@
    $dbFile = Join-Path $env:TEMP 'twl-db-probe.py'
    $dbOut = ''
    try {
        Set-Content -LiteralPath $dbFile -Value $dbProbe -Encoding UTF8
        Push-Location -LiteralPath $Backend
        try {
            $dbOut = (& $VenvPython $dbFile 2>&1 | Out-String).Trim()
        } finally {
            Pop-Location
        }
    } catch {
        $dbOut = 'ERR launch-failed'
    } finally {
        Remove-Item -LiteralPath $dbFile -Force -ErrorAction SilentlyContinue
    }

    if ($dbOut -eq 'OK') {
        Show-Ok '数据库连接正常'
    } else {
        Show-Fail '数据库连不上'
        if ($dbOut) { Write-Host "          $dbOut" -ForegroundColor DarkRed }
        $Problems.Add('检查 backend\.env 里的 POSTGRES_* 配置，以及 PostgreSQL 服务是否已启动。')
    }
}

# 1.6 端口
$PortPids = Get-PortOwners -PortNumber $Port
if ($PortPids.Count -eq 0) {
    Show-Ok "端口 $Port 空闲"
} else {
    $labels = $PortPids | ForEach-Object { Format-ProcessLabel -ProcessId $_ }
    Show-Warn "端口 $Port 已被占用：$($labels -join '、')"
    Show-Note '启动时会先结束这些进程再接管端口'
}

# 1.7 汇总
if ($Problems.Count -gt 0) {
    Show-Title '自检未通过'
    if ($Warnings.Count -gt 0) {
        foreach ($w in $Warnings) { Write-Host "  ! $w" -ForegroundColor Yellow }
        Write-Host ''
    }
    foreach ($p in $Problems) { Write-Host "  $p" -ForegroundColor Red }
    Write-Host ''
    exit 1
}

if ($Warnings.Count -gt 0) {
    Write-Host ''
    foreach ($w in $Warnings) { Write-Host "  ! $w" -ForegroundColor Yellow }
    Write-Host ''
}

if ($Check) {
    Show-Title '自检通过，未启动服务'
    Write-Host "  如需启动，去掉 -Check 重新运行即可。" -ForegroundColor DarkGray
    Write-Host ''
    exit 0
}

# ------------------------------------------------------------
# 2. 接管端口
# ------------------------------------------------------------
if ($PortPids.Count -gt 0) {
    foreach ($procId in $PortPids) {
        try {
            Stop-Process -Id $procId -Force -ErrorAction Stop
            Show-Note "已结束 $(Format-ProcessLabel -ProcessId $procId)"
        } catch {
            Show-Fail "结束 PID $procId 失败：$($_.Exception.Message)"
        }
    }
    Start-Sleep -Seconds 2

    $stillBusy = Get-PortOwners -PortNumber $Port
    if ($stillBusy.Count -gt 0) {
        Show-Fail "端口 $Port 仍被占用，无法启动"
        exit 1
    }
}

# ------------------------------------------------------------
# 3. 启动
# ------------------------------------------------------------
Show-Title '启动服务'
Write-Host "  前台首页    http://127.0.0.1:$Port/"          -ForegroundColor Gray
Write-Host "  商城        http://127.0.0.1:$Port/shop.html"  -ForegroundColor Gray
Write-Host "  管理后台    http://127.0.0.1:$Port/admin.html" -ForegroundColor Gray
Write-Host "  接口文档    http://127.0.0.1:$Port/docs"      -ForegroundColor Gray
Write-Host ''
Write-Host '  按 Ctrl+C 停止服务' -ForegroundColor DarkYellow
Write-Host ''

# 后台等端口真的起来再开浏览器（最多等 60 秒，不打扰前台进程）
if (-not $NoBrowser) {
    $url = "http://127.0.0.1:$Port/"
    $opener = @"
`$deadline = (Get-Date).AddSeconds(60)
while ((Get-Date) -lt `$deadline) {
    try {
        `$client = New-Object System.Net.Sockets.TcpClient
        `$client.Connect('127.0.0.1', $Port)
        `$client.Close()
        Start-Process '$url'
        break
    } catch {
        Start-Sleep -Milliseconds 400
    }
}
"@
    try {
        $encoded = [Convert]::ToBase64String([System.Text.Encoding]::Unicode.GetBytes($opener))
        Start-Process -FilePath 'powershell.exe' `
            -WindowStyle Hidden `
            -ArgumentList @('-NoProfile', '-EncodedCommand', $encoded) | Out-Null
    } catch { }
}

Set-Location -LiteralPath $Backend

$uvArgs = @('-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', "$Port")
if ($Reload) {
    $uvArgs += @('--reload', '--reload-dir', 'app')
}

& $VenvPython @uvArgs
$exitCode = $LASTEXITCODE

Write-Host ''
if ($exitCode -ne 0) {
    Show-Fail "服务异常退出（退出码 $exitCode）"
    Write-Host '  常见原因：数据库中途断开、端口被其他程序抢占、配置项写错' -ForegroundColor DarkGray
} else {
    Show-Note '服务已停止'
}
Write-Host ''

exit $exitCode