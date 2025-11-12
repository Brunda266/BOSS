import time
import os
import subprocess
import numpy as np

# --- CONFIGURATION (UPDATED for refined threat inference) ---
RF_STATUS_FILE = 'rf_status.txt'

# THREAT CRITERIA FOR REFINED DETECTION:
# Simulate detection in an isolated area: if few networks are present, BUT a very strong signal is seen.
MAX_NETWORKS_COUNT = 5     # If more than 3 networks, it's considered civilian noise (not a specific threat).
MAX_RSSI_THRESHOLD = -50     # Signal strength stronger than -50 dBm (very close or very powerful device) is a threat.
# --- END CONFIGURATION ---

def run_wifi_scan():
    """Runs the Windows 'netsh' command to scan nearby Wi-Fi networks."""
    # Command to show Wi-Fi networks and their signal strength (RSSI)
    cmd = ['netsh', 'wlan', 'show', 'networks', 'mode=bssid']
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        return result.stdout
    except Exception as e:
        print(f"ERROR: Failed to run netsh command. {e}")
        return ""

def process_wifi_data(scan_output):
    """Analyzes the Wi-Fi scan output based on refined threat criteria."""
    lines = scan_output.split('\n')
    
    total_networks = 0
    strong_signals = 0
    
    for line in lines:
        line = line.strip()
        
        if line.startswith("SSID "):
            total_networks += 1
            
        if "Signal" in line and "%" in line:
            signal_percent = int(line.split(':')[1].strip().replace('%', ''))
            # Convert percentage to approximate RSSI
            rssi = (signal_percent / 2) - 100
            
            # Check for specific, very strong signals
            if rssi > MAX_RSSI_THRESHOLD:
                strong_signals += 1

    # REFINED INFERENCE LOGIC: 
    # Threat only if the overall network count is low (isolated area) AND a very strong, specific signal is detected.
    if total_networks <= MAX_NETWORKS_COUNT and strong_signals > 0:
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
    print("--- RF Inference Backend Active (Refined Threat Mode) ---")
    update_rf_status("RF_INIT")

    try:
        while True:
            scan_data = run_wifi_scan()
            
            if scan_data:
                rf_status = process_wifi_data(scan_data)
                update_rf_status(rf_status)
                
                print(f"[{time.strftime('%H:%M:%S')}] RF Status: {rf_status}. Networks detected: {scan_data.count('SSID ')}")
            
            time.sleep(5)

    except KeyboardInterrupt:
        print("\n--- RF Inference Backend Shut Down ---")
        update_rf_status("RF_OFF")