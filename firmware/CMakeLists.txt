cmake_minimum_required(VERSION 3.20)

# 电控组第三次培训作业 —— STM32F103C8T6 (72MHz, 64K Flash / 20K RAM)
# 交叉编译工具链在 cmake/gcc-arm-none-eabi.cmake 中指定
project(diankong3 C ASM)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

set(MCU_FLAGS -mcpu=cortex-m3 -mthumb)

# ---------- 源文件 ----------
file(GLOB HAL_SOURCES ${CMAKE_CURRENT_SOURCE_DIR}/Drivers/STM32F1xx_HAL_Driver/Src/*.c)
# 模板文件（msp_template / timebase_*_template）里有和本工程重复的弱符号，编译时排除
list(FILTER HAL_SOURCES EXCLUDE REGEX ".*_template\\.c$")

set(APP_SOURCES
    Core/Src/main.c
    Core/Src/gpio.c
    Core/Src/usart.c
    Core/Src/stm32f1xx_it.c
    Core/Src/stm32f1xx_hal_msp.c
    Core/Src/system_stm32f1xx.c
    Core/Src/OLED.c
)

set(STARTUP Core/Src/startup_stm32f103xb.s)

set(LINKER_SCRIPT ${CMAKE_CURRENT_SOURCE_DIR}/STM32F103C8Tx_FLASH.ld)

# ---------- 可执行文件 ----------
add_executable(${PROJECT_NAME}.elf ${APP_SOURCES} ${HAL_SOURCES} ${STARTUP})

target_include_directories(${PROJECT_NAME}.elf PRIVATE
    Core/Inc
    Drivers/STM32F1xx_HAL_Driver/Inc
    Drivers/STM32F1xx_HAL_Driver/Inc/Legacy
    Drivers/CMSIS/Device/ST/STM32F1xx/Include
    Drivers/CMSIS/Include
)

target_compile_definitions(${PROJECT_NAME}.elf PRIVATE
    USE_HAL_DRIVER
    STM32F103xB
)

target_compile_options(${PROJECT_NAME}.elf PRIVATE
    ${MCU_FLAGS}
    -Wall -Wextra
    -fdata-sections -ffunction-sections
    -O0 -g3
)

target_link_options(${PROJECT_NAME}.elf PRIVATE
    ${MCU_FLAGS}
    -T${LINKER_SCRIPT}
    -Wl,--gc-sections
    -Wl,-Map=${PROJECT_NAME}.map,--cref
    --specs=nano.specs
    --specs=nosys.specs
)

set_target_properties(${PROJECT_NAME}.elf PROPERTIES
    OUTPUT_NAME ${PROJECT_NAME}
    SUFFIX ".elf"
)

# ---------- 生成 hex / bin ----------
add_custom_command(TARGET ${PROJECT_NAME}.elf POST_BUILD
    COMMAND ${CMAKE_OBJCOPY} -O ihex   $<TARGET_FILE:${PROJECT_NAME}.elf> ${PROJECT_NAME}.hex
    COMMAND ${CMAKE_OBJCOPY} -O binary $<TARGET_FILE:${PROJECT_NAME}.elf> ${PROJECT_NAME}.bin
    COMMAND ${CMAKE_SIZE} $<TARGET_FILE:${PROJECT_NAME}.elf>
    COMMENT "生成 hex/bin 并打印尺寸"
)
