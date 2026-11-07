# Accelerometer consumption
# ADXL355

import formulas

def cutoff_freq(ODR):
    return ODR / 4 # kHz

def sampling_interval(ODR):
    return 1 / ODR      # 0.25 ms at 4000 Hz

def FIFO_fill_time(ODR, pos_num):
    samples = pos_num / 3
    return samples / ODR # 8 ms for 96 positions (32 samples) at 4000 Hz

def cycle_time(ODR, watermark):
    return watermark / (3 * ODR)   # 7.5 ms (INT1 period) at 4000 Hz

def timing_margin(ODR, pos_num, watermark):
    if (watermark < pos_num):
        return FIFO_fill_time(ODR, pos_num) - cycle_time(ODR, watermark)   # 0.5 ms if watermark = 90 at 4000 Hz
    raise ValueError("watermark must be less than pos_num")

def pwr_ADXL355_mW(Volt_supply_ADXL355, I_ADXL355):
    pwr_consumption = formulas.pwr_mW(formulas.conv_to_mA('uA', I_ADXL355), Volt_supply_ADXL355)
    return pwr_consumption