/* Q2 V2 pin PROPOSAL only. Not an initialized or board-tested BSP. */
#pragma once
/* Numbers ending GPIO are GPIO indices, not QFN physical pin numbers. */
/* QFN pin 5; FPC1.11 / U6.1，经3.3V隔离检测 */
#define Q2_KEY_POWER_SENSE_N_GPIO 0
/* QFN pin 6; FPC1.5 */
#define Q2_CTRL_INT_N_GPIO 1
/* QFN pin 7; U1.6 */
#define Q2_RTC_INT_N_GPIO 2
/* QFN pin 8; U15.4 */
#define Q2_IMU_INT1_GPIO 3
/* QFN pin 9; U14.1 */
#define Q2_BAT_ALERT_N_GPIO 4
/* QFN pin 10; U3.7 */
#define Q2_CHG_INT_N_GPIO 5
/* QFN pin 12; U3.5 U14.3 U1.2 U11.2 FPC1.4 */
#define Q2_SYS_I2C_SCL_GPIO 6
/* QFN pin 13; U3.6 U14.2 U1.3 U11.3 FPC1.3 */
#define Q2_SYS_I2C_SDA_GPIO 7
/* QFN pin 15; U6.3，经断电防反灌电路 */
#define Q2_POWER_OFF_REQ_GPIO 9
/* QFN pin 16; FPC1.6 */
#define Q2_CTRL_RESET_N_GPIO 10
/* QFN pin 17; U17.2 */
#define Q2_USB_PATH_SEL_GPIO 11
/* QFN pin 19; U11.5 */
#define Q2_MOTOR_EN_GPIO 12
/* QFN pin 20; U3.8 */
#define Q2_CHG_OTG_EN_GPIO 13
/* QFN pin 21; U7.6 U15.13 */
#define Q2_AUDIO_I2C_SCL_GPIO 14
/* QFN pin 22; U7.5 U15.14 */
#define Q2_AUDIO_I2C_SDA_GPIO 15
/* QFN pin 26; CARD2.CD */
#define Q2_SD_CARD_DETECT_N_GPIO 19
/* QFN pin 27; CARD2.7 */
#define Q2_SD_D0_GPIO 20
/* QFN pin 28; CARD2.8 */
#define Q2_SD_D1_GPIO 21
/* QFN pin 29; CARD2.1 */
#define Q2_SD_D2_GPIO 22
/* QFN pin 31; CARD2.2 */
#define Q2_SD_D3_GPIO 23
/* QFN pin 32; CARD2.5 */
#define Q2_SD_CLK_GPIO 24
/* QFN pin 33; CARD2.3 */
#define Q2_SD_CMD_GPIO 25
/* QFN pin 48; U8.2 */
#define Q2_DAC_I2S_DOUT_GPIO 35
/* QFN pin 51; U8.5 */
#define Q2_DAC_I2S_LRCK_GPIO 38
/* QFN pin 52; U8.12 */
#define Q2_DAC_RESET_N_GPIO 39
/* QFN pin 53; U8.9 */
#define Q2_DAC_I2S_BCLK_GPIO 40
/* QFN pin 55; JDISP1.20 */
#define Q2_TP_I2C_SCL_GPIO 42
/* QFN pin 56; JDISP1.19 */
#define Q2_TP_I2C_SDA_GPIO 43
/* QFN pin 57; JDISP1.1 */
#define Q2_LCD_RESET_N_GPIO 44
/* QFN pin 58; JDISP1.24 */
#define Q2_LCD_VCI_EN_GPIO 45
/* QFN pin 59; JDISP1.3 */
#define Q2_LCD_TE_GPIO 46
/* QFN pin 60; JDISP1.17 */
#define Q2_TP_INT_N_GPIO 47
/* QFN pin 61; JDISP1.18 */
#define Q2_TP_RESET_N_GPIO 48
/* QFN pin 67; JDISP1.4 */
#define Q2_LCD_CS_N_GPIO 52
/* QFN pin 68; JDISP1.5 */
#define Q2_LCD_CLK_GPIO 53
/* QFN pin 69; JDISP1.7 */
#define Q2_LCD_D0_GPIO 54
/* QFN pin 70; JDISP1.6 */
#define Q2_LCD_D1_GPIO 55
/* QFN pin 71; JDISP1.22 */
#define Q2_LCD_D3_GPIO 56
/* QFN pin 72; JDISP1.23 */
#define Q2_LCD_D2_GPIO 57
/* QFN pin 73; U12.5 RXD */
#define Q2_UART0_TX_GPIO 58
/* QFN pin 74; U12.4 TXD */
#define Q2_UART0_RX_GPIO 59
/* LP I2C is NOT a third HP I2C controller. Initialize through LP APIs. */
#define Q2_SYS_I2C_INITIAL_HZ 100000
#define Q2_AUDIO_I2C_HP_PORT 0
#define Q2_TP_I2C_HP_PORT 1
#define Q2_LCD_SPI_INITIAL_HZ 20000000
/* Native USB HS uses dedicated QFN pins 44/45, never GPIO44/45. */
