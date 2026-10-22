#Requires -Version 5.1
# ============================================================
# 启动链编码校验
#
# 为什么需要它：
#   中文乱码在 Windows 上几乎全部来自「文件字节编码」和
#   「读取方假设的编码」不一致。这个脚本把约定固定成可校验的规则，
#   改完脚本跑一遍就知道有没有把乱码引回来。
#
# 约定：
#   scripts\*.ps1     → UTF-8 with BOM
#                       （PowerShell 5.1 只认 BOM，无 BOM 会按 GBK 解码）
#   启动.bat          → 纯 ASCII，无 BOM
#                       （cmd.exe 会执行 BOM 字节，且 GBK 解 UTF-8 中文必乱）
#
# 用法：  .\scripts\check-encoding.ps1
# ============================================================

[CmdletBinding()]
param()

try { & chcp.com 65001 > $null 2>&1 } catch { }
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    [Console]::InputEncoding  = [System.Text.Encoding]::UTF8
    $global:OutputEncoding    = [System.Text.Encoding]::UTF8
} catch { }

$Root = Split-Path -Parent $PSScriptRoot

$Targets = @(
    [pscustomobject]@{ Name = 'scripts\start.ps1';          Path = (Join-Path $PSScriptRoot 'start.ps1');          Rule = 'utf8-bom' },
    [pscustomobject]@{ Name = 'scripts\check-encoding.ps1'; Path = (Join-Path $PSScriptRoot 'check-encoding.ps1'); Rule = 'utf8-bom' },
    [pscustomobject]@{ Name = '启动.bat';                    Path = (Join-Path $Root '启动.bat');                   Rule = 'ascii'    }
)

$StrictUtf8 = New-Object System.Text.UTF8Encoding -ArgumentList @($false, $true)

$Failures = 0

Write-Host ''
Write-Host ('=' * 58) -ForegroundColor DarkCyan
Write-Host '  启动链编码校验' -ForegroundColor Cyan
Write-Host ('=' * 58) -ForegroundColor DarkCyan
Write-Host ''

foreach ($t in $Targets) {
    if (-not (Test-Path -LiteralPath $t.Path)) {
        Write-Host ('  [SKIP]  {0}  (文件不存在)' -f $t.Name) -ForegroundColor DarkGray
        continue
    }

    $bytes = [System.IO.File]::ReadAllBytes($t.Path)
    $hasBom = ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF)
    $nonAscii = 0
    foreach ($b in $bytes) { if ($b -gt 127) { $nonAscii++ } }

    $ok = $true
    $reasons = @()

    switch ($t.Rule) {
        'utf8-bom' {
            if (-not $hasBom) {
                $ok = $false
                $reasons += '缺少 UTF-8 BOM（PowerShell 5.1 会按 GBK 解码 → 中文乱码）'
            }
            $offset = if ($hasBom) { 3 } else { 0 }
            try {
                $null = $StrictUtf8.GetString($bytes, $offset, $bytes.Length - $offset)
            } catch {
                $ok = $false
                $reasons += 'BOM 之后不是合法 UTF-8 字节'
            }
        }
        'ascii' {
            if ($hasBom) {
                $ok = $false
                $reasons += '带 BOM（cmd.exe 会把 BOM 字节当成命令的一部分）'
            }
            if ($nonAscii -gt 0) {
                $ok = $false
                $reasons += "含 $nonAscii 个非 ASCII 字节（GBK 代码页下会乱码，中文请写到 start.ps1）"
            }
        }
    }

    # 追加一条前置检查：这里的脚本本来就是给 5.1 跑的，别被 pwsh 7 的成功蒙住
    if ($ok) {
        Write-Host ('  [ OK ]  {0}  ({1})' -f $t.Name, $t.Rule) -ForegroundColor Green
    } else {
        $Failures++
        Write-Host ('  [FAIL]  {0}  ({1})' -f $t.Name, $t.Rule) -ForegroundColor Red
        foreach ($r in $reasons) { Write-Host ('          - ' + $r) -ForegroundColor DarkRed }
    }
}

Write-Host ''
if ($Failures -eq 0) {
    Write-Host '  全部符合约定。' -ForegroundColor Green
} else {
    Write-Host "  有 $Failures 个文件不符合约定，请按上面的提示修正。" -ForegroundColor Yellow
}
Write-Host ''
Write-Host '  提示：本机 pwsh 7 能自动识别 UTF-8 无 BOM，' -ForegroundColor DarkGray
Write-Host '        但启动.bat 调用的是 Windows PowerShell 5.1，规则以 5.1 为准。' -ForegroundColor DarkGray
Write-Host ''

exit $(if ($Failures -eq 0) { 0 } else { 1 })