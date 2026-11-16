# 一键复位：通过 ST-Link 让板子重新从头跑（不用去按板子上的按键）
# 用法：双击这个文件

$OPENOCD = 'D:\apps\diankong-tools\openocd\bin\openocd.exe'
if (-not (Test-Path $OPENOCD)) { Write-Host "找不到 OpenOCD：$OPENOCD" -ForegroundColor Red; Start-Sleep 2; exit 1 }

$cfg = Join-Path $env:TEMP 'diankong3_reset.cfg'
"init`nreset run`nshutdown" | Set-Content -Encoding ascii $cfg

$ErrorActionPreference = 'Continue'
& $OPENOCD -f interface/stlink.cfg -f target/stm32f1x.cfg -f $cfg 2>&1 | Out-Null

Write-Host '已复位，板子重新开始运行' -ForegroundColor Green
Start-Sleep -Milliseconds 600
exit 0
