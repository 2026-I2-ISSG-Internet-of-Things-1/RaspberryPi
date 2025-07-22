import smbus
import time

# I2C bus (1 on most Pi models) and slave addresses
bus = smbus.SMBus(1)
INPUT_ADDR = 0x08
OUTPUT_ADDR = 0x09
MAX_READ = 32  # max bytes Arduino will send


def read_input():
    # Read up to MAX_READ bytes from InputUnit, trim trailing zeros, parse CSV
    data = bus.read_i2c_block_data(INPUT_ADDR, 0, MAX_READ)
    try:
        end = data.index(0)
        data = data[:end]
    except ValueError:
        pass
    s = "".join(chr(b) for b in data)
    temp_str, lux_str, btn_str = s.split(",")
    return float(temp_str), int(lux_str), int(btn_str)


def read_color_index():
    # Read single byte from OutputUnit
    return bus.read_byte(OUTPUT_ADDR)


def main():
    try:
        while True:
            temp, lux, btn = read_input()
            color_idx = read_color_index()
            btn_state = "PRESSED" if btn else "Released"
            print(
                f"Temp: {temp:.2f}°C | Lux: {lux} | Button: {btn_state} | ColorIdx: {color_idx}"
            )
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nArrêt du programme.")


if __name__ == "__main__":
    main()
