# 编译并运行离线仿真（PC 上验证逻辑，不需要板子）
# 用法：右键"使用 PowerShell 运行"，或在命令行执行
#   powershell -ExecutionPolicy Bypass -File 工具\build_sim.ps1

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot      # diankong3 目录
$sim  = Join-Path $root 'sim'

# ---- 找一个 Windows 原生的 gcc（arm-none-eabi-gcc 不能用来编 PC 程序）----
$gcc = $null
$cmd = Get-Command gcc -ErrorAction SilentlyContinue
if ($cmd) { $gcc = $cmd.Source }

if (-not $gcc) {
    $cands = @(
        'C:\Users\Furina\RM\env\msys64\ucrt64\bin\gcc.exe',
        'C:\Users\Furina\RM\env\msys64\mingw64\bin\gcc.exe',
        'C:\msys64\ucrt64\bin\gcc.exe',
        'C:\msys64\mingw64\bin\gcc.exe',
        'C:\MinGW\bin\gcc.exe'
    )
    foreach ($c in $cands) {
        if (Test-Path $c) { $gcc = $c; break }
    }
}

if (-not $gcc) {
    Write-Host '没找到 PC 版 gcc。装一个再试，例如：winget install BrechtSanders.WinLibs.POSIX.UCRT' -ForegroundColor Yellow
    exit 1
}

# gcc 会去调 cc1.exe / as.exe / ld.exe，它们依赖同目录下的 DLL。
# 不把工具链的 bin 加进 PATH，就会出现"退出码 1、一行错都不报"的怪现象。
$env:PATH = "$(Split-Path -Parent $gcc);$env:PATH"

Write-Host "用 $gcc 编译仿真程序 ..."
Push-Location $sim
try {
    & $gcc -std=gnu11 -O1 -Wall -Wextra -I stub -I ../firmware/Core/Inc -o test_app.exe test_app.c
    if ($LASTEXITCODE -ne 0) {
        throw '编译失败'
    }
    Write-Host ''
    & .\test_app.exe
    if ($LASTEXITCODE -ne 0) {
        throw "有测试没通过（退出码 $LASTEXITCODE）"
    }
}
finally {
    Pop-Location
}
