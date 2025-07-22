import serial
import time

# USB-Serial connections to Arduinos
ser_in = serial.Serial("/dev/ttyACM0", 9600, timeout=1)
ser_out = serial.Serial("/dev/ttyACM1", 9600, timeout=1)

MAX_READ = 32  # max bytes Arduino will send


def read_input():
    # Read a line from InputUnit over Serial, parse CSV
    s = ser_in.readline().decode("ascii", errors="ignore").strip()
    if not s:
        return None, None, None
    temp_str, lux_str, btn_str = s.split(",")
    return float(temp_str), int(lux_str), int(btn_str)


def read_color_index():
    # Read a line from OutputUnit over Serial and parse color index
    s = ser_out.readline().decode("ascii", errors="ignore").strip()
    return int(s) if s else None


def main():
    try:
        while True:
            temp, lux, btn = read_input()
            color_idx = read_color_index()
            if temp is not None:
                btn_state = "PRESSED" if btn else "Released"
                print(
                    f"Temp: {temp:.2f}°C | Lux: {lux} | Button: {btn_state} | ColorIdx: {color_idx}"
                )
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nArrêt du programme.")


if __name__ == "__main__":
    main()
