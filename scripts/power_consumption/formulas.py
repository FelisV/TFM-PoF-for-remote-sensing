# unit conversions
types_of_ampere_values = {
    'nA': 1e-9,
    'uA': 1e-6,
    'mA': 1e-3,
    'A': 1,
}

def conv_to_mA(value_type, value):
    base = value * types_of_ampere_values[value_type]
    value_ma = base / types_of_ampere_values['mA']
    return value_ma

types_of_time_values = {
    'ns': 1e-9,
    'us': 1e-6,
    'ms': 1e-3,
    's': 1,
}

def conv_to_ms(value_type, value):
    base = value * types_of_time_values[value_type]
    value_ms = base / types_of_time_values['ms']
    return value_ms

def pwr_mW(value_mA, value_V):
    return value_mA * value_V
