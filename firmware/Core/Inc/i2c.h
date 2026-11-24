/**
  ******************************************************************************
  * @file    i2c.h
  * @brief   硬件 I²C1 初始化（选做：OLED 由软件位翻转改为硬件 I²C）
  *
  * 接线：PB6 = SCL，PB7 = SDA，两脚都是复用开漏，模块自带 4.7k 上拉即可通信。
  ******************************************************************************
  */
#ifndef __I2C_H__
#define __I2C_H__

#ifdef __cplusplus
extern "C" {
#endif

#include "stm32f1xx_hal.h"

extern I2C_HandleTypeDef hi2c1;

void MX_I2C1_Init(void);

#ifdef __cplusplus
}
#endif

#endif /* __I2C_H__ */
