# 下载 CLion 便携版（免安装包，解压即用，不需要管理员权限）
$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'
$root = 'D:\apps\diankong-tools'
$dl = Join-Path $root '_dl'
New-Item -ItemType Directory -Force -Path $root, $dl | Out-Null

$zip = Join-Path $dl 'CLion.win.zip'
$out = Join-Path $root 'clion'

if (Test-Path (Join-Path $out '.ok')) { Write-Host '[skip] clion already extracted'; exit 0 }

if (-not (Test-Path $zip) -or (Get-Item $zip).Length -lt 100MB) {
    Write-Host '[get ] CLion portable zip (约 2.3 GB)'
    & curl.exe -L --ssl-no-revoke --retry 3 --retry-delay 3 -# -o $zip 'https://download.jetbrains.com/cpp/CLion-2026.3.0.1.win.zip'
    if ($LASTEXITCODE -ne 0) { Write-Host "[FAIL] clion download exit=$LASTEXITCODE"; exit 1 }
}
Write-Host "[ok  ] zip $([math]::Round((Get-Item $zip).Length/1MB,0)) MB"

if (Test-Path $out) { Remove-Item -Recurse -Force $out }
Expand-Archive -LiteralPath $zip -DestinationPath $out -Force
$inner = Get-ChildItem $out -Directory | Select-Object -First 1
if ($inner -and (Get-ChildItem $out).Count -eq 1) {
    $tmp = "$out._tmp"
    Move-Item $inner.FullName $tmp
    Remove-Item -Recurse -Force $out
    Move-Item $tmp $out
}
Set-Content (Join-Path $out '.ok') 'ok'
Get-ChildItem (Join-Path $out 'bin') -Filter 'clion64.exe' | Select-Object FullName
Write-Host 'CLION DONE'
exit 0
