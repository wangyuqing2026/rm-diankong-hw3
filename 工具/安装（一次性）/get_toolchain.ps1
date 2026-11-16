# 下载并解压 STM32 开发所需的便携工具链（无需管理员权限）
$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'
$root = 'D:\apps\diankong-tools'
$dl = Join-Path $root '_dl'
New-Item -ItemType Directory -Force -Path $root, $dl | Out-Null

$items = @(
    @{ name = 'gcc';   url = 'https://github.com/xpack-dev-tools/arm-none-eabi-gcc-xpack/releases/download/v13.3.1-1.1/xpack-arm-none-eabi-gcc-13.3.1-1.1-win32-x64.zip'; dir = 'gcc' },
    @{ name = 'openocd'; url = 'https://github.com/xpack-dev-tools/openocd-xpack/releases/download/v0.12.0-7/xpack-openocd-0.12.0-7-win32-x64.zip'; dir = 'openocd' },
    @{ name = 'cmake'; url = 'https://github.com/Kitware/CMake/releases/download/v4.5.0/cmake-4.5.0-windows-x86_64.zip'; dir = 'cmake' },
    @{ name = 'ninja'; url = 'https://github.com/ninja-build/ninja/releases/download/v1.13.2/ninja-win.zip'; dir = 'ninja' }
)

foreach ($it in $items) {
    $zip = Join-Path $dl ($it.name + '.zip')
    $target = Join-Path $root $it.dir
    if (Test-Path (Join-Path $target '.ok')) { Write-Host "[skip] $($it.name) already installed"; continue }
    Write-Host "[get ] $($it.name) <- $($it.url)"
    & curl.exe -L --ssl-no-revoke --retry 3 --retry-delay 2 -sS -o $zip $it.url
    if ($LASTEXITCODE -ne 0) { Write-Host "[FAIL] download $($it.name) exit=$LASTEXITCODE"; continue }
    $size = (Get-Item $zip).Length
    Write-Host "[ok  ] $($it.name) $([math]::Round($size/1MB,1)) MB"
    if (Test-Path $target) { Remove-Item -Recurse -Force $target }
    Expand-Archive -LiteralPath $zip -DestinationPath $target -Force
    # 解压后通常有一层同名目录，压平
    $inner = Get-ChildItem $target | Select-Object -First 1
    if ($inner -and $inner.PSIsContainer -and (Get-ChildItem $target).Count -eq 1) {
        $tmp = "$target._tmp"
        Move-Item $inner.FullName $tmp
        Remove-Item -Recurse -Force $target
        Move-Item $tmp $target
    }
    Set-Content -Path (Join-Path $target '.ok') -Value 'ok'
    Write-Host "[done] $($it.name)"
}

Write-Host '=== verify ==='
$gccExe = Get-ChildItem (Join-Path $root 'gcc\bin') -Filter 'arm-none-eabi-gcc.exe' -ErrorAction SilentlyContinue | Select-Object -First 1
if ($gccExe) { & $gccExe.FullName --version | Select-Object -First 1 }
$cmakeExe = Get-ChildItem (Join-Path $root 'cmake\bin') -Filter 'cmake.exe' -ErrorAction SilentlyContinue | Select-Object -First 1
if ($cmakeExe) { & $cmakeExe.FullName --version | Select-Object -First 1 }
$ninjaExe = Get-ChildItem (Join-Path $root 'ninja') -Filter 'ninja.exe' -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
if ($ninjaExe) { & $ninjaExe.FullName --version }
$ocdExe = Get-ChildItem (Join-Path $root 'openocd\bin') -Filter 'openocd.exe' -ErrorAction SilentlyContinue | Select-Object -First 1
if ($ocdExe) { & $ocdExe.FullName --version 2>&1 | Select-Object -First 1 }
Write-Host 'ALL DONE'
exit 0
