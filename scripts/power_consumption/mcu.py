# MCU consumption
# STM32L451xx
# RAM + interrupts + GPIOs + SPI + UART

import formulas

# constants
I_WAKEUP_mA = 1.50                                   # Table 35, p.105 (MSI 4 MHz, Range 2)

# (1) STOP2 -> RTC disabled, wake-up by ADXL355 INT1 (EXTI)
# LSE always on: reference for MSI PLL-mode tSU(LSE) = 2 s, Table 48, p.120 (UART clock accuracy)
def I_stop2_consumption_mA(I_stop2, I_LSE):
    I_stop2_mA = formulas.conv_to_mA('uA', I_stop2)
    I_LSE_mA = formulas.conv_to_mA('nA', I_LSE)
    return I_stop2_mA + I_LSE_mA

# (2) wakeuptime -> time(Table 42) = [11.37 - 12.9] µs , p.116 (SRAM1, MSI 4 MHz, Range 2)
def I_wakeup_consumption_mA(I_LSE):
    return I_WAKEUP_mA + formulas.conv_to_mA('nA', I_LSE)

# (3) run -> I_run_T29 + I_MSI + I_LSE + I_GPIO(A,B,C,H) + I_APB
# Clock: wakes up from Stop 2 on MSI 4 MHz then switches to MCU_clk MHz for run
def I_run_consumption_mA(I_run, I_MSI_range_run, MCU_clk, I_LSE, GPIO_uA_per_MHz, APB1_uA_per_MHz):
    I_MSI_mA = formulas.conv_to_mA('uA', I_MSI_range_run)
    I_GPIO_mA = formulas.conv_to_mA('uA', GPIO_uA_per_MHz * MCU_clk)
    I_APB1_mA = formulas.conv_to_mA('uA', APB1_uA_per_MHz * MCU_clk)
    I_LSE_mA = formulas.conv_to_mA('nA', I_LSE)
    I_base = I_run + I_MSI_mA + I_GPIO_mA + I_APB1_mA + I_LSE_mA
    return I_base

# read: I_base + SPI3
def I_read_consumption_mA(I_base, I_spi, MCU_clk):
    I_spi_mA = I_base + formulas.conv_to_mA('uA', I_spi * MCU_clk)
    return I_spi_mA

# send: I_base + USART
def I_send_consumption_mA(I_base, I_USART_independent_clock_domain, I_USART_clock_domain, MCU_clk):
    I_USART_mA = I_base + formulas.conv_to_mA('uA', (I_USART_independent_clock_domain + I_USART_clock_domain) * MCU_clk)
    return I_USART_mA

# times
def t_read_ms(MCU_clk, watermark, baud_rate_control_spi):
    bytes_num = 1 + (watermark * 3)
    bits_num = bytes_num * 8
    f_sclk = MCU_clk / baud_rate_control_spi
    if f_sclk > 10:
        raise ValueError("SPI SCLK exceeds ADXL355 max (10 MHz), increase baud_rate_control_spi")
    read_time = bits_num / f_sclk
    return formulas.conv_to_ms('us', read_time)

def t_send_ms(bytes_header_num, bytes_fifo_num, bytes_crc_num, uart_oversampling, usartdiv, f_clk, bits_per_frame):
    bytes_num = bytes_header_num + bytes_fifo_num + bytes_crc_num + 1 # '1' is UART idle frame
    if(uart_oversampling == 16):
        baud = f_clk / usartdiv         # Mbaud
    elif(uart_oversampling == 8):
        baud = (2 * f_clk) / usartdiv   # Mbaud
    else:
        raise ValueError("uart_oversampling must be 8 or 16")
    print(f" UART baud : {baud:.3f} Mbaud")
    t_send = (bytes_num * bits_per_frame) / baud
    return formulas.conv_to_ms('us', t_send)

# all times in ms
def t_stop2_ms(send_data, t_wakeup, t_read, t_send, t_cycle):
    if send_data:
        t_stop2 = t_cycle - (t_wakeup + t_read + t_send)
    else:
        t_stop2 = t_cycle - (t_wakeup + t_read)
    if t_stop2 <= 0:
        raise ValueError("awake time does not fit in one cycle")
    return t_stop2

