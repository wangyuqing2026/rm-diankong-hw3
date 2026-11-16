/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file    main.h
  * @brief   引脚定义与全局声明
  ******************************************************************************
  */
/* USER CODE END Header */

#ifndef __MAIN_H
#define __MAIN_H

#ifdef __cplusplus
extern "C" {
#endif

#include "stm32f1xx_hal.h"

void Error_Handler(void);

/* ---------------- 引脚定义（与作业接线表一致） ---------------- */
/* 4 颗 LED，接 PA0~PA3，高电平点亮 */
#define LED1_Pin            GPIO_PIN_0
#define LED1_GPIO_Port      GPIOA
#define LED2_Pin            GPIO_PIN_1
#define LED2_GPIO_Port      GPIOA
#define LED3_Pin            GPIO_PIN_2
#define LED3_GPIO_Port      GPIOA
#define LED4_Pin            GPIO_PIN_3
#define LED4_GPIO_Port      GPIOA

/* 2 个按键，接 PA11 / PA12，内部上拉，按下为低电平，下降沿触发中断 */
#define KEY1_Pin            GPIO_PIN_11
#define KEY1_GPIO_Port      GPIOA
#define KEY2_Pin            GPIO_PIN_12
#define KEY2_GPIO_Port      GPIOA

#ifdef __cplusplus
}
#endif

#endif /* __MAIN_H */
