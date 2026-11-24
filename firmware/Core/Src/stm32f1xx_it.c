/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file    stm32f1xx_it.c
  * @brief   中断服务函数：SysTick、USART1、EXTI15_10
  ******************************************************************************
  */
/* USER CODE END Header */

#include "main.h"
#include "stm32f1xx_it.h"
#include "usart.h"          /* huart1 / hdma_usart1_tx 的声明在这里 */

extern UART_HandleTypeDef huart1;

/* ---- Cortex-M3 异常 ---- */
void NMI_Handler(void)
{
  while (1)
  {
  }
}

void HardFault_Handler(void)
{
  while (1)
  {
  }
}

void MemManage_Handler(void)
{
  while (1)
  {
  }
}

void BusFault_Handler(void)
{
  while (1)
  {
  }
}

void UsageFault_Handler(void)
{
  while (1)
  {
  }
}

void SVC_Handler(void)
{
}

void DebugMon_Handler(void)
{
}

void PendSV_Handler(void)
{
}

/**
  * @brief SysTick：HAL 用它产生 1ms 计时，HAL_GetTick() 依赖它
  */
void SysTick_Handler(void)
{
  HAL_IncTick();
}

/* ---- 外设中断 ---- */

/**
  * @brief 串口中断：HAL 内部会判断是接收完成、发送完成还是出错，
  *        再调用对应的回调（RxCpltCallback / TxCpltCallback）
  */
void USART1_IRQHandler(void)
{
  HAL_UART_IRQHandler(&huart1);
}

/**
  * @brief PA11/PA12 共用的中断入口：两个引脚都要检查并清标志
  */
void EXTI15_10_IRQHandler(void)
{
  HAL_GPIO_EXTI_IRQHandler(KEY1_Pin);
  HAL_GPIO_EXTI_IRQHandler(KEY2_Pin);
}

/**
  * @brief 选做：DMA1_Channel4 中断（USART1_TX 搬完一包时进来）
  * @note  HAL_DMA_IRQHandler 会清掉传输完成标志，并回调 HAL_UART_TxCpltCallback，
  *        我们的 s_tx_busy 就是在那里面清掉的——少了这个入口，标志永远不清，
  *        现象是"第一包发出去了，之后再也不发"。
  */
void DMA1_Channel4_IRQHandler(void)
{
  HAL_DMA_IRQHandler(&hdma_usart1_tx);
}
