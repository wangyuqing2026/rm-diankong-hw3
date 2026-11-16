# 交叉编译工具链：arm-none-eabi-gcc
# 优先使用环境变量 ARM_TOOLCHAIN_DIR 指向的目录（例如 D:/apps/diankong-tools/gcc），
# 否则在 PATH 中查找 arm-none-eabi-gcc。
set(CMAKE_SYSTEM_NAME Generic)
set(CMAKE_SYSTEM_PROCESSOR arm)

if(DEFINED ENV{ARM_TOOLCHAIN_DIR})
    file(TO_CMAKE_PATH "$ENV{ARM_TOOLCHAIN_DIR}" _arm_dir)
    set(_arm_prefix "${_arm_dir}/bin/arm-none-eabi-")
else()
    set(_arm_prefix "arm-none-eabi-")
endif()

set(CMAKE_C_COMPILER   "${_arm_prefix}gcc")
set(CMAKE_CXX_COMPILER "${_arm_prefix}g++")
set(CMAKE_ASM_COMPILER "${_arm_prefix}gcc")
set(CMAKE_OBJCOPY      "${_arm_prefix}objcopy")
set(CMAKE_SIZE         "${_arm_prefix}size")
set(CMAKE_AR           "${_arm_prefix}ar")

set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)

set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
