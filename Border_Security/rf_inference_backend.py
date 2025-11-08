import time
import os
import subprocess
import numpy as np

# --- CONFIGURATION ---
# New shared file for RF status
RF_STATUS_FILE = 'rf_status.txt'

# Thresholds for triggering a threat based on Wi-Fi scanning (Windows specific)
# This simulates detecting a "hotspot" or significant environmental change.
MIN_NETWORKS_FOR_THREAT = 5  # If more than 5 networks are visible, assume high electronic activity.
MAX_RSSI_THRESHOLD = -70     # Signal strength (RSSI) threshold. Stronger than -70 dBm (closer to 0) is a potential threat.
# --- END CONFIGURATION ---

def run_wifi_scan():
    """Runs the Windows 'netsh' command to scan nearby Wi-Fi networks."""
    # Command to show Wi-Fi networks and their signal strength (RSSI)
    cmd = ['netsh', 'wlan', 'show', 'networks', 'mode=bssid']
    
    try:
        # Execute the command and capture output
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to run netsh command. Ensure Wi-Fi adapter is enabled. {e}")
        return ""
    except FileNotFoundError:
        print("ERROR: 'netsh' command not found. This script requires Windows.")
        return ""

def process_wifi_data(scan_output):
    """Analyzes the Wi-Fi scan output to determine a threat level."""
    lines = scan_output.split('\n')
    
    total_networks = 0
    strong_signals = 0
    
    for line in lines:
        line = line.strip()
        
        # 1. Count the number of detected networks
        if line.startswith("SSID "):
            total_networks += 1
            
        # 2. Check for signal strength (RSSI)
        if "Signal" in line and "%" in line:
            # Simple parsing for signal strength (e.g., "Signal              : 90%")
            signal_percent = int(line.split(':')[1].strip().replace('%', ''))
            
            # Convert percentage to approximate RSSI for threshold check (Optional, but good practice)
            # A common approximation: RSSI = (signal_percent / 2) - 100
            rssi = (signal_percent / 2) - 100
            
            if rssi > MAX_RSSI_THRESHOLD:
                strong_signals += 1

    # Apply inference logic
    if total_networks >= MIN_NETWORKS_FOR_THREAT or strong_signals > 0:
        return "RF_THREAT"
    else:
        return "RF_CLEAR"

def update_rf_status(status):
    """Writes the current RF threat status to the shared file."""
    try:
        with open(RF_STATUS_FILE, 'w') as f:
            f.write(status)
    except Exception as e:
        print(f"Error writing to RF status file: {e}")

if __name__ == "__main__":
    print("--- RF Inference Backend Active ---")
    
    # Initialize the RF status file
    update_rf_status("RF_INIT")

    try:
        while True:
            # 1. Scan the environment
            scan_data = run_wifi_scan()
            
            if scan_data:
                # 2. Infer the threat level
                rf_status = process_wifi_data(scan_data)
                
                # 3. Write status to file
                update_rf_status(rf_status)
                
                # Console feedback
                print(f"[{time.strftime('%H:%M:%S')}] RF Status: {rf_status}. Networks: {scan_data.count('SSID ')}")
            
            # Scan frequency (e.g., every 5 seconds)
            time.sleep(5)

    except KeyboardInterrupt:
        print("\n--- RF Inference Backend Shut Down ---")
        update_rf_status("RF_OFF")