/**
  ******************************************************************************
  * @file    i2c.c
  * @brief   硬件 I²C1 初始化（选做）
  *
  * 为什么 400 kHz 而不是 100 kHz：
  *   OLED 一屏 1024 字节，100 kHz 下光传输就要约 92 ms，主循环会被卡住，
  *   按键响应明显变慢；400 kHz 下同样的量约 23 ms，肉眼看不出卡顿。
  ******************************************************************************
  */
#include "i2c.h"

I2C_HandleTypeDef hi2c1;

/**
  * @brief  初始化 I2C1：400 kHz、7 位地址、关闭双地址与通用呼叫
  */
void MX_I2C1_Init(void)
{
  hi2c1.Instance             = I2C1;
  hi2c1.Init.ClockSpeed      = 400000u;
  hi2c1.Init.DutyCycle       = I2C_DUTYCYCLE_2;
  hi2c1.Init.OwnAddress1     = 0u;
  hi2c1.Init.AddressingMode  = I2C_ADDRESSINGMODE_7BIT;
  hi2c1.Init.DualAddressMode = I2C_DUALADDRESS_DISABLE;
  hi2c1.Init.OwnAddress2     = 0u;
  hi2c1.Init.GeneralCallMode = I2C_GENERALCALL_DISABLE;
  hi2c1.Init.NoStretchMode   = I2C_NOSTRETCH_DISABLE;

  if (HAL_I2C_Init(&hi2c1) != HAL_OK)
  {
    Error_Handler();
  }
}

/**
  * @brief  I2C1 的底层引脚与时钟（HAL 在 HAL_I2C_Init 里自动调用）
  */
void HAL_I2C_MspInit(I2C_HandleTypeDef *hi2c)
{
  GPIO_InitTypeDef GPIO_InitStruct = {0};

  if (hi2c->Instance == I2C1)
  {
    __HAL_RCC_GPIOB_CLK_ENABLE();
    __HAL_RCC_I2C1_CLK_ENABLE();

    /* PB6 = SCL，PB7 = SDA；复用开漏，I²C 只能开漏 */
    GPIO_InitStruct.Pin   = GPIO_PIN_6 | GPIO_PIN_7;
    GPIO_InitStruct.Mode  = GPIO_MODE_AF_OD;
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);
  }
}

/**
  * @brief  关闭 I2C1（对称的收尾，本工程不会调用）
  */
void HAL_I2C_MspDeInit(I2C_HandleTypeDef *hi2c)
{
  if (hi2c->Instance == I2C1)
  {
    __HAL_RCC_I2C1_CLK_DISABLE();
    HAL_GPIO_DeInit(GPIOB, GPIO_PIN_6 | GPIO_PIN_7);
  }
}
