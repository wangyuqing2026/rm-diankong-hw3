# 一键下载：ST-Link + OpenOCD 烧录 firmware/build/diankong3.elf
# 用法：工具\flash.ps1
# 前提：ST-Link 已插好、已装驱动（Zadig + WinUSB）；开发板 3.3V 供电

$OPENOCD = 'D:\apps\diankong-tools\openocd\bin\openocd.exe'

$proj = Resolve-Path (Join-Path $PSScriptRoot '..\firmware')
$elf  = Join-Path $proj 'build\diankong3.elf'

if (-not (Test-Path $elf)) {
    Write-Host '还没编译，先跑 工具\build.ps1' -ForegroundColor Yellow
    exit 1
}
if (-not (Test-Path $OPENOCD)) {
    Write-Host "找不到 OpenOCD：$OPENOCD" -ForegroundColor Red
    exit 1
}

# OpenOCD 的 -c 是 Tcl 字符串，Windows 路径里的 \ 会被当转义符吃掉（\f \b \t），
# 所以路径统一转成 / 再传进去。
$elfTcl = $elf -replace '\\', '/'

Write-Host "烧录 $elf" -ForegroundColor Cyan

# openocd 把日志写在 stderr，PowerShell 5.1 会把它当成错误。
# 这里临时放宽错误处理，改为自己根据输出判断成功与否。
$ErrorActionPreference = 'Continue'
$out = & $OPENOCD -f interface/stlink.cfg -f target/stm32f1x.cfg `
    -c "program $elfTcl verify reset exit" 2>&1
$text = ($out | ForEach-Object { $_.ToString() }) -join "`n"

# 只挑关键几行给用户看，别刷一屏
($text -split "`n") | Where-Object { $_ -match 'Programming|Verified|Error|Warn' } | ForEach-Object { $_.Trim() }

if ($text -match 'Programming Finished' -and $text -match 'Verified OK') {
    Write-Host '下载完成，板子已复位' -ForegroundColor Green
} elseif ($text -match 'Error') {
    Write-Host '下载失败：先看上面的 Error 行；常见是 ST-Link 线松了，或板子没供电' -ForegroundColor Red
} else {
    Write-Host '结果不确定，把上面的输出发我' -ForegroundColor Yellow
}
exit 0
