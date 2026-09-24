# 第二版引脚分配完整表

候选方案：ESP32-S31NRV16；KiCad −90°。GPIO编号与QFN物理脚号分别列出。尚未写入原理图/PCB。

| 物理脚 | 芯片脚名 | GPIO | 功能分组 | 建议网络名 | 旧网络 | 目标 |
|---:|---|---:|---|---|---|---|
| 1 | ANT | — | 射频 | ANT |  | RF匹配/天线 |
| 2 | VDDA3 | — | 电源 | 3V3_VDDA3 |  | 3.3V域，局部滤波/去耦 |
| 3 | VDDA4 | — | 电源 | 3V3_VDDA4 |  | 3.3V域，局部滤波/去耦 |
| 4 | CHIP_PU | — | 复位 | CHIP_PU | ESP32S31_EN | RC及CH343下载控制电路 |
| 5 | XTAL_32K_N/GPIO0 | 0 | 唤醒/中断 | KEY_POWER_SENSE_N | ESP_IO42 | FPC1.11 / U6.1，经3.3V隔离检测 |
| 6 | XTAL_32K_P/GPIO1 | 1 | 唤醒/中断 | CTRL_INT_N | ESP_IO43 | FPC1.5 |
| 7 | GPIO2 | 2 | 唤醒/中断 | RTC_INT_N | ESP_IO34 | U1.6 |
| 8 | GPIO3 | 3 | 唤醒/中断 | IMU_INT1 | ESP_IO1 | U15.4 |
| 9 | GPIO4 | 4 | 唤醒/中断 | BAT_ALERT_N | ESP_IO35 | U14.1 |
| 10 | GPIO5 | 5 | 唤醒/中断 | CHG_INT_N | BQ25895_INT | U3.7 |
| 11 | VDDPST_1 | — | 电源 | 3V3_VDDPST_1 |  | 3.3V域，局部滤波/去耦 |
| 12 | GPIO6 | 6 | 系统LP I2C | SYS_I2C_SCL | BQ25895_I2C_CLK | U3.5 U14.3 U1.2 U11.2 FPC1.4 |
| 13 | GPIO7 | 7 | 系统LP I2C | SYS_I2C_SDA | BQ25895_I2C_SDA | U3.6 U14.2 U1.3 U11.3 FPC1.3 |
| 14 | GPIO8 | 8 | 空闲GPIO | SPARE_GPIO8 |  |  |
| 15 | GPIO9 | 9 | 系统控制 | POWER_OFF_REQ | GEK100_RST | U6.3，经断电防反灌电路 |
| 16 | GPIO10 | 10 | 系统控制 | CTRL_RESET_N | ESP_IO44 | FPC1.6 |
| 17 | GPIO11 | 11 | 系统控制 | USB_PATH_SEL | ESP_IO33 | U17.2 |
| 18 | VREF_TOUCH | — | 模拟预留 | NC_VREF_TOUCH |  | 本方案不用触摸/ADC则按手册处理 |
| 19 | GPIO12 | 12 | 系统控制 | MOTOR_EN | ESP_IO40 | U11.5 |
| 20 | GPIO13 | 13 | 系统控制 | CHG_OTG_EN | BQ25895_OTG_EN | U3.8 |
| 21 | GPIO14 | 14 | 音频HP I2C0 | AUDIO_I2C_SCL | DAC_I2C_SCL | U7.6 U15.13 |
| 22 | GPIO15 | 15 | 音频HP I2C0 | AUDIO_I2C_SDA | DAC_I2C_SDA | U7.5 U15.14 |
| 23 | GPIO16 | 16 | 空闲GPIO | SPARE_GPIO16 |  |  |
| 24 | GPIO17 | 17 | 空闲GPIO | SPARE_GPIO17 |  |  |
| 25 | GPIO18 | 18 | 空闲GPIO | SPARE_GPIO18 |  |  |
| 26 | GPIO19 | 19 | 系统控制 | SD_CARD_DETECT_N | ESP_IO19 | CARD2.CD |
| 27 | SDIO_DATA0 | 20 | SDMMC | SD_D0 | ESP_TF_DAT0 | CARD2.7 |
| 28 | SDIO_DATA1 | 21 | SDMMC | SD_D1 | ESP_TF_DAT1 | CARD2.8 |
| 29 | SDIO_DATA2 | 22 | SDMMC | SD_D2 | ESP_TF_DAT2 | CARD2.1 |
| 30 | VDD_PSRAM_1P8_1 | — | 电源 | VDD_PSRAM_1P8_1 |  | VDD_LDO_1P8，按参考电路 |
| 31 | SDIO_DATA3 | 23 | SDMMC | SD_D3 | ESP_TF_DAT3 | CARD2.2 |
| 32 | SDIO_CLK | 24 | SDMMC | SD_CLK | ESP_TF_CLK | CARD2.5 |
| 33 | SDIO_CMD | 25 | SDMMC | SD_CMD | ESP_TF_CMD | CARD2.3 |
| 34 | VDD_PSRAM_1P8_2 | — | 电源 | VDD_PSRAM_1P8_2 |  | VDD_LDO_1P8，按参考电路 |
| 35 | VDD_LDO_1P8 | — | 电源 | VDD_LDO_1P8 |  | PSRAM 1.8V供电和去耦 |
| 36 | SPICS | 26 | 启动Flash | FLASH_CS_N | ESP_FLASH_CS | U10.1 |
| 37 | SPIQ | 27 | 启动Flash | FLASH_D1 | ESP_FLASH_DO | U10.2 |
| 38 | SPIWP | 28 | 启动Flash | FLASH_D2 | ESP_FLASH_WP | U10.3 |
| 39 | VDD_SPI | — | 电源 | VDD_SPI |  | 外接Flash供电/去耦 |
| 40 | SPIHD | 30 | 启动Flash | FLASH_D3 | ESP_FLASH_HOLD | U10.7 |
| 41 | SPICLK | 31 | 启动Flash | FLASH_CLK | ESP_FLASH_CLK | U10.6 |
| 42 | SPID | 32 | 启动Flash | FLASH_D0 | ESP_FLASH_DI | U10.5 |
| 43 | VCCA/VDDPST_2 | — | 电源 | 3V3_VCCA/VDDPST_2 |  | 3.3V域，局部滤波/去耦 |
| 44 | USB_DP | — | USB HS | USB_HS_DP | ESP_USB_DP | U17.7 |
| 45 | USB_DM | — | USB HS | USB_HS_DM | ESP_USB_DN | U17.6 |
| 46 | GPIO33 | 33 | 调试预留 | USB_DEBUG_DM |  | 新增调试焊盘/连接器 |
| 47 | GPIO34 | 34 | 调试预留 | USB_DEBUG_DP |  | 新增调试焊盘/连接器 |
| 48 | GPIO35 | 35 | 音频I2S | DAC_I2S_DOUT | DAC_I2S_SDIN | U8.2 |
| 49 | GPIO36 | 36 | 启动配置 | STRAP_FLASH_3V3 |  | 启动上拉/下载电路 |
| 50 | GPIO37 | 37 | 启动配置 | STRAP_USB_JTAG |  | 启动上拉/下载电路 |
| 51 | GPIO38 | 38 | 音频I2S | DAC_I2S_LRCK | DAC_I2S_LRCK | U8.5 |
| 52 | GPIO39 | 39 | 音频I2S | DAC_RESET_N | DAC_RST# | U8.12 |
| 53 | GPIO40 | 40 | 音频I2S | DAC_I2S_BCLK | DAC_I2S_SCLK | U8.9 |
| 54 | VDDPST_3 | — | 电源 | 3V3_VDDPST_3 |  | 3.3V域，局部滤波/去耦 |
| 55 | GPIO42 | 42 | 触屏HP I2C1 | TP_I2C_SCL | ESP_I2C2_SCL | JDISP1.20 |
| 56 | GPIO43 | 43 | 触屏HP I2C1 | TP_I2C_SDA | ESP_I2C2_SDA | JDISP1.19 |
| 57 | GPIO44 | 44 | 屏幕控制 | LCD_RESET_N | ESP_IO47 | JDISP1.1 |
| 58 | GPIO45 | 45 | 屏幕控制 | LCD_VCI_EN | ESP_IO46 | JDISP1.24 |
| 59 | GPIO46 | 46 | 屏幕控制 | LCD_TE | AM213_TE_RESERVED | JDISP1.3 |
| 60 | GPIO47 | 47 | 屏幕控制 | TP_INT_N | ESP_IO54 | JDISP1.17 |
| 61 | GPIO48 | 48 | 屏幕控制 | TP_RESET_N | ESP_IO57 | JDISP1.18 |
| 62 | GPIO49 | 49 | 空闲GPIO | SPARE_GPIO49 |  |  |
| 63 | VREF_ADC | — | 模拟预留 | NC_VREF_ADC |  | 本方案不用触摸/ADC则按手册处理 |
| 64 | VDDPST_4 | — | 电源 | 3V3_VDDPST_4 |  | 3.3V域，局部滤波/去耦 |
| 65 | GPIO50 | 50 | 空闲GPIO | SPARE_GPIO50 |  |  |
| 66 | GPIO51 | 51 | 空闲GPIO | SPARE_GPIO51 |  |  |
| 67 | GPIO52 | 52 | 屏幕QSPI | LCD_CS_N | ESP_SPI2_CS | JDISP1.4 |
| 68 | GPIO53 | 53 | 屏幕QSPI | LCD_CLK | ESP_SPI2_CLK | JDISP1.5 |
| 69 | MTDO | 54 | 屏幕QSPI | LCD_D0 | ESP_SPI2_D0 | JDISP1.7 |
| 70 | MTCK | 55 | 屏幕QSPI | LCD_D1 | ESP_SPI2_D1 | JDISP1.6 |
| 71 | MTDI | 56 | 屏幕QSPI | LCD_D3 | ESP_SPI2_D3 | JDISP1.22 |
| 72 | MTMS | 57 | 屏幕QSPI | LCD_D2 | ESP_SPI2_D2 | JDISP1.23 |
| 73 | GPIO58 | 58 | 下载UART0 | UART0_TX | CH343P_UART_RX | U12.5 RXD |
| 74 | GPIO59 | 59 | 下载UART0 | UART0_RX | CH343P_UART_TX | U12.4 TXD |
| 75 | GPIO60 | 60 | 启动配置 | BOOT_MODE_H | ESP_BOOT2 | 启动上拉/下载电路 |
| 76 | GPIO61 | 61 | 启动配置 | BOOT_DOWNLOAD_N | ESP_BOOT1 | 启动上拉/下载电路 |
| 77 | VDDA1 | — | 电源 | 3V3_VDDA1 |  | 3.3V域，局部滤波/去耦 |
| 78 | XTAL_N | — | 晶振 | XTAL_N |  | 40MHz晶振/匹配 |
| 79 | XTAL_P | — | 晶振 | XTAL_P |  | 40MHz晶振/匹配 |
| 80 | VDDA2 | — | 电源 | 3V3_VDDA2 |  | 3.3V域，局部滤波/去耦 |
| 81 | GND | — | 地 | GND_EP |  | 连续GND/散热过孔 |
