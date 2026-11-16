# 一键编译：不依赖 CLion，直接用本机的 arm-none-eabi-gcc + CMake + Ninja
# 用法：右键“使用 PowerShell 运行”，或在终端执行  工具\build.ps1

$ErrorActionPreference = 'Stop'

# ---- 工具链路径（换电脑时只改这两行）----
$GCC_BIN    = 'D:\apps\diankong-tools\gcc\bin'
$CMAKE_BIN  = 'D:\apps\diankong-tools\cmake\bin'
$NINJA_BIN  = 'D:\apps\diankong-tools\ninja'

$proj = Resolve-Path (Join-Path $PSScriptRoot '..\firmware')
$env:PATH = "$GCC_BIN;$NINJA_BIN;$CMAKE_BIN;$env:PATH"

Push-Location $proj
try {
    cmake -S . -B build -G Ninja -DCMAKE_TOOLCHAIN_FILE="$proj\cmake\gcc-arm-none-eabi.cmake"
    if ($LASTEXITCODE -ne 0) { throw 'CMake 配置失败' }

    cmake --build build
    if ($LASTEXITCODE -ne 0) { throw '编译失败' }

    Write-Host ''
    Write-Host '=== 产物 ===' -ForegroundColor Green
    Get-ChildItem build -Filter 'diankong3.*' | Where-Object Extension -in '.hex','.bin','.elf' |
        Select-Object Name, @{n='大小(KB)';e={[math]::Round($_.Length/1KB,1)}} | Format-Table -AutoSize
    Write-Host '烧录：工具\flash.ps1' -ForegroundColor Cyan
}
finally {
    Pop-Location
}
exit 0
