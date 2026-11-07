import accel
import mcu
import formulas

############################## photodiodes ####################################

# 3 PDs in series (Pmax, measured), mW
#pwr_PD = 0.635 # -3dBm per PD
pwr_PD = 1.27 # 0 dBm per PD

############################## laser ##########################################

# uplink
pwr_laser = 49.3 # mW, vdd = 3V, ILaser = 16.4 mA

############################## ADXL355 ########################################

V_ADXL355 = 2.5 # V
I_ADXL355 = 200 # µA
ODR = 0.125 # kHz, Table 10, p.27
pos_num = 96 # FIFO positions (p.31)
watermark = 90 # Table 45, p.41

################################ MCU ##########################################
# NOTE: if MCU_clk changes, check Range and update the values below:
# Table 41. Peripheral current consumption (µA/MHz):
# I_spi, I_USART_independent_clock_domain, I_USART_clock_domain
# I_GPIO, I_APB1

MCU_V_value = 2.5 # V
MCU_clk = 16 # MHz

# stop2
I_stop2 = 2.10 # µA

# run
I_run = 1.5 # mA, Table 29
I_MSI_range_run = 62 # µA, Table 50, p.126
I_LSE = 250 # LSE 250 nA Table 48, p.120

I_spi = 1.3
baud_rate_control_spi = 2 # (2, 4, 8, 16, 32, 64, 128, 256), p.1353

I_GPIO = 1.4 + 1.3 + 1.5 + 0.6 # GPIOA, B, C, H
I_APB1 = 0.7

I_USART_independent_clock_domain = 3.5
I_USART_clock_domain = 1.1
bytes_header_num = 0 # header
bytes_crc_num = 0 # CRC
bytes_per_fifo = watermark * 3
usartdiv = 16 # divider
uart_oversampling = 8
bits_per_frame = 10
f_clk = MCU_clk

# FIFO accumulation
n_fifo = 1
RAM_total = 160 * 1024 # bytes, STM32L451CC SRAM
n_fifo_max = RAM_total // bytes_per_fifo
print(f" n FIFO max : {n_fifo_max}")
if(n_fifo > n_fifo_max):
    raise ValueError("not enough RAM for n_fifo")

bytes_fifo_num = n_fifo * bytes_per_fifo

########################## Times (ms) #########################################

print("\n Times:")

t_cycle = accel.cycle_time(ODR, watermark)
print(f" MCU cycle time: {t_cycle:.2f} ms")

t_period = n_fifo * t_cycle
print(f" t_period (n_fifo = {n_fifo}, max {n_fifo_max}): {t_period:.2f} ms")

wakeuptime_typ = 11.37 #µs p.116
t_wakeup = formulas.conv_to_ms('us', wakeuptime_typ)
print(f" t_wakeup: {t_wakeup:.6} ms")

mcu_read_time = mcu.t_read_ms(MCU_clk, watermark, baud_rate_control_spi)
print(f" t_read: {mcu_read_time:.4f} ms")

send_data = True
mcu_send_time = mcu.t_send_ms(bytes_header_num, bytes_fifo_num, bytes_crc_num, uart_oversampling, usartdiv, f_clk, bits_per_frame)
print(f" t_send: {mcu_send_time:.2f} ms")

t_stop2 = mcu.t_stop2_ms(send_data, n_fifo * t_wakeup, n_fifo * mcu_read_time, mcu_send_time, t_period)
print(f" t_stop2: {t_stop2:.2f} ms")

# FIFO must be read before it overflows
if(t_wakeup + mcu_read_time > accel.timing_margin(ODR, pos_num, watermark)):
    raise ValueError("FIFO overflows before the read ends")

# send must end before the next INT1 (no read during send)
if(mcu_send_time > t_cycle - (t_wakeup + mcu_read_time)):
    raise ValueError("send overlaps the next FIFO read")

########################## Currents (mA) ######################################

print("\n Current consumption:")

I_stop2_mA = mcu.I_stop2_consumption_mA(I_stop2, I_LSE)
print(f" I_stop2_mA: {I_stop2_mA:.4f} mA")

I_wakeup_mA = mcu.I_wakeup_consumption_mA(I_LSE)
print(f" I_wakeup_mA: {I_wakeup_mA:.4f} mA")

I_base_mA = mcu.I_run_consumption_mA(I_run, I_MSI_range_run, MCU_clk, I_LSE, I_GPIO, I_APB1)
print(f" I_base_mA: {I_base_mA:.4f} mA")

I_read_mA = mcu.I_read_consumption_mA(I_base_mA, I_spi, MCU_clk)
print(f" I_read_mA: {I_read_mA:.4f} mA")

I_send_mA = mcu.I_send_consumption_mA(I_base_mA, I_USART_independent_clock_domain, I_USART_clock_domain, MCU_clk)
print(f" I_send_mA: {I_send_mA:.4f} mA")

########################## Phase Power (mW) ###################################

print("\n Power consumption during each phase:")

pwr_ADXL355 = accel.pwr_ADXL355_mW(V_ADXL355, I_ADXL355)
print(f" ADXL power: {pwr_ADXL355:.4f} mW")

pwr_stop2 = formulas.pwr_mW(I_stop2_mA, MCU_V_value)
pwr_wakeup = formulas.pwr_mW(I_wakeup_mA, MCU_V_value)
pwr_base = formulas.pwr_mW(I_base_mA, MCU_V_value)
pwr_read = formulas.pwr_mW(I_read_mA, MCU_V_value)
pwr_send = formulas.pwr_mW(I_send_mA, MCU_V_value)

print(f" stop2 power: {pwr_stop2:.4f} mW")
print(f" wakeup power: {pwr_wakeup:.4f} mW")
print(f" run base power: {pwr_base:.4f} mW")
print(f" run read power: {pwr_read:.4f} mW")
print(f" run send power: {pwr_send:.4f} mW")
print(f" laser power: {pwr_laser:.4f} mW")

######################### average power (mW) ##################################

print("\n Average power consumption:")

pwr_stop2_avg = pwr_stop2 * t_stop2 / t_period
print(f" stop2 average power: {pwr_stop2_avg:.4f} mW")

pwr_wakeup_avg = pwr_wakeup * n_fifo * t_wakeup / t_period
print(f" wakeup average power: {pwr_wakeup_avg:.4f} mW")

pwr_read_avg = pwr_read * n_fifo * mcu_read_time / t_period
print(f" read average power: {pwr_read_avg:.4f} mW")

pwr_send_avg = 0
pwr_laser_avg = 0
if(send_data):
    pwr_send_avg = pwr_send * mcu_send_time / t_period
    pwr_laser_avg = pwr_laser * mcu_send_time / t_period
print(f" send average power: {pwr_send_avg:.4f} mW")
print(f" laser average power: {pwr_laser_avg:.4f} mW")

pwr_MCU = pwr_stop2_avg + pwr_wakeup_avg + pwr_read_avg + pwr_send_avg
print(f"\n MCU average power: {pwr_MCU:.4f} mW")

pwr_total = pwr_MCU + pwr_ADXL355 + pwr_laser_avg
print(f"\n Total average power: {pwr_total:.4f} mW")

######################### energy balance (mW) #################################

pwr_balance = pwr_PD - pwr_total
print(f"\n Energy balance: {pwr_balance:.4f} mW")

