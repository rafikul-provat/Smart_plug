import tinytuya
import time
import csv
from datetime import datetime
import os

# ----------------------------
# CONFIGURATION (replace with your values)
# ----------------------------
DEVICE_ID = "a39435ab2fde8e8a80aony"  # Your Device ID
LOCAL_KEY = "G.B_x'(URqC~j0ix"       # Your Local Key
IP_ADDRESS = "192.168.0.102"         # Your Smart Plug IP
VERSION = 3.5                         # Device protocol version

CSV_FILE = "energy_log.csv"           # File to save data
POLL_INTERVAL = 5                     # seconds between readings
# ----------------------------

# Connect to the device
plug = tinytuya.OutletDevice(DEVICE_ID, IP_ADDRESS, LOCAL_KEY)
plug.set_version(VERSION)

# Initialize CSV file if it does not exist
file_exists = os.path.isfile(CSV_FILE)
with open(CSV_FILE, "a", newline="") as f:
    writer = csv.writer(f)
    if not file_exists:
        writer.writerow([
            "Timestamp", "Voltage (V)", "Current (A)", "Power (W)", "Energy (kWh)", "Status"
        ])

print("Logging started... Press Ctrl+C to stop.")

# Initialize cumulative energy
energy_kwh = 0.0  # kWh

try:
    while True:
        try:
            status = plug.status()
            data = status.get("dps", {})

            voltage = data.get("20", 0) / 10        # V
            current = data.get("18", 0) / 1000     # A
            power = data.get("19", 0) / 10         # W
            status_on = data.get("1", False)

            # Energy calculation in kWh
            energy_kwh += (power * POLL_INTERVAL) / 3600 / 1000  # kWh

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Print to console
            print(f"{timestamp} | Voltage: {voltage:.1f} V | Current: {current:.3f} A | "
                  f"Power: {power:.1f} W | Energy: {energy_kwh:.3f} kWh | "
                  f"Status: {'ON' if status_on else 'OFF'}")

            # Append to CSV
            with open(CSV_FILE, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    timestamp, voltage, current, power,
                    round(energy_kwh, 6), 'ON' if status_on else 'OFF'
                ])

        except Exception as e:
            print(f"Error reading plug: {e}")

        time.sleep(POLL_INTERVAL)

except KeyboardInterrupt:
    print("Logging stopped.")
