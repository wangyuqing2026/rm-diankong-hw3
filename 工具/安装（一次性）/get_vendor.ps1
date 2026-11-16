# 下载 STM32CubeF1 的 HAL 驱动与 CMSIS（拆分包，体积小）
$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'
$root = 'C:\Users\Furina\Documents\deepseek-harness\default-workspace\diankong3\vendor'
$dl = Join-Path $root '_dl'
New-Item -ItemType Directory -Force -Path $root, $dl | Out-Null

$repos = @(
    @{ name = 'stm32f1xx-hal-driver'; url = 'https://codeload.github.com/STMicroelectronics/stm32f1xx-hal-driver/zip/refs/heads/master' },
    @{ name = 'cmsis-device-f1';      url = 'https://codeload.github.com/STMicroelectronics/cmsis-device-f1/zip/refs/heads/master' },
    @{ name = 'cmsis-core';           url = 'https://codeload.github.com/STMicroelectronics/cmsis-core/zip/refs/heads/master' }
)

foreach ($r in $repos) {
    $zip = Join-Path $dl ($r.name + '.zip')
    $out = Join-Path $root $r.name
    if (Test-Path (Join-Path $out '.ok')) { Write-Host "[skip] $($r.name)"; continue }
    Write-Host "[get ] $($r.name)"
    & curl.exe -L --retry 3 -sS -o $zip $r.url
    if ($LASTEXITCODE -ne 0) { Write-Host "[FAIL] $($r.name)"; continue }
    Write-Host "[ok  ] $($r.name) $([math]::Round((Get-Item $zip).Length/1MB,1)) MB"
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
}
Write-Host '=== tree check ==='
Get-ChildItem $root -Directory | ForEach-Object { "$($_.Name): $((Get-ChildItem $_.FullName -Recurse -File).Count) files" }
Get-ChildItem (Join-Path $root 'cmsis-device-f1') -Recurse -Filter 'startup_stm32f103xb.s' | Select-Object -First 2 FullName
Get-ChildItem (Join-Path $root 'stm32f1xx-hal-driver') -Recurse -Filter 'stm32f1xx_hal_conf_template.h' | Select-Object -First 2 FullName
Write-Host 'VENDOR DONE'
exit 0
