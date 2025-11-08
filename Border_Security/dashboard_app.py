import streamlit as st
from PIL import Image
import numpy as np
import time
import os
import sqlite3
import pandas as pd
import io 

# --- CONFIGURATION ---
ALERT_STATUS_FILE = 'alert_status.txt'      # Human Detection Status
FRAME_OUTPUT_FILE_LIVE = 'current_frame.jpg' # The single image for the live feed
RF_STATUS_FILE = 'rf_status.txt'            # RF Threat Status 
DB_NAME = 'surveillance_log.db'
ALERT_IMAGE_DIR = 'alert_images'
# --- END CONFIGURATION ---

# --- Status Check Helper Functions ---
def check_alert_status():
    """Reads the current Human Detection status."""
    try:
        with open(ALERT_STATUS_FILE, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return "INIT"
    except Exception:
        return "ERROR"

def check_rf_status():
    """Reads the current RF Inference status."""
    try:
        with open(RF_STATUS_FILE, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return "RF_INIT"
    except Exception:
        return "RF_ERROR"
        
def get_most_recent_alert_image():
    """Connects to the DB and fetches the file path for the latest captured threat log."""
    conn = sqlite3.connect(DB_NAME)
    query = "SELECT image_path, timestamp, type FROM threat_log ORDER BY id DESC LIMIT 1"
    
    try:
        df = pd.read_sql_query(query, conn)
        conn.close()
        if not df.empty:
            return df.iloc[0]['image_path'], df.iloc[0]['timestamp'], df.iloc[0]['type']
        return None, None, None
    except Exception:
        return None, None, None
# --- End Status Check Helper Functions ---


def display_dashboard():
    # --- UI Setup (Run only once) ---
    st.set_page_config(
        page_title="Border Security System", 
        layout="wide", 
        initial_sidebar_state="collapsed", 
        menu_items={'About': "Border Surveillance System - Minor Project"}
    )
    
    st.title("🛡️ Border Security Monitoring System")
    st.markdown("---")

    status_header = st.empty()
    
    # Define tabs
    tab1, tab2 = st.tabs(["🔴 THREAT MONITORING", "📸 VISUAL MONITORING"])
    
    # Define persistent placeholders outside the loop to prevent scrolling in Tab 1 & 2
    with tab1:
        st.subheader("Current Surveillance Status Metrics")
        col_h, col_r = st.columns(2)
        
        with col_h:
            st.markdown("### 🏃 Human Intrusion Status")
            human_status_placeholder = st.empty()
        
        with col_r:
            st.markdown("### 📱 Device Inference Status")
            rf_status_placeholder = st.empty()
            
    with tab2:
        live_col, log_col = st.columns(2)
        with live_col:
            st.markdown("### 📺 Live Surveillance Stream")
            live_placeholder = st.empty()
        with log_col:
            st.markdown("### 🚨 Most Recent Alert Image")
            log_placeholder = st.empty()

    # Start the main update loop
    while True:
        human_status = check_alert_status()
        rf_status = check_rf_status() 
        
        is_human_alert = (human_status == "ALERT")
        is_rf_alert = (rf_status == "RF_THREAT")
        is_major_alert = is_human_alert or is_rf_alert
        
        # 1. Update Overall Alert Banner (Global Header)
        if is_major_alert:
            status_header.error("🚨 CRITICAL THREAT DETECTED! Review Status Panels. 🚨")
        elif human_status == "NORMAL" and rf_status == "RF_CLEAR":
            status_header.success("✅ System Operational. ALL SYSTEMS NORMAL")
        else:
            status_header.info("⏳ Monitoring...")

        
        # --- TAB 1: THREAT MONITORING (Update the persistent placeholders with direct status text) ---
        with tab1:
            
            # Column H: Human Detection Status
            with col_h:
                if human_status == "ALERT":
                    # RED Status Box: THREAT DETECTED
                    html = ('<div style="background-color: #C11007; padding: 15px; border-radius: 30px; color: white; text-align: center;">'
                            '<h1>THREAT DETECTED</h1>'
                            '</div>')
                elif human_status == "NORMAL":
                    # GREEN Status Box: SAFE CONDITION
                    html = ('<div style="background-color: #008000; padding: 15px; border-radius: 30px; color: white; text-align: center;">'
                            '<h1>SAFE CONDITION</h1>'
                            '</div>')
                else:
                    html = f'<div style="padding: 15px; border-radius: 30px; color: #a9a9a9; text-align: center;">Human Detector: {human_status}</div>'
                
                human_status_placeholder.markdown(html, unsafe_allow_html=True)


            # Column R: RF Inference Status
            with col_r:
                if rf_status == "RF_THREAT":
                    # RED Status Box: THREAT DETECTED
                    html = ('<div style="background-color: #C11007; padding: 15px; border-radius: 30px; color: white; text-align: center;">'
                            '<h1>THREAT DETECTED</h1>'
                            '</div>')
                elif rf_status == "RF_CLEAR":
                    # GREEN Status Box: SAFE CONDITION
                    html = ('<div style="background-color: #008000; padding: 15px; border-radius: 30px; color: white; text-align: center;">'
                            '<h1>SAFE CONDITION</h1>'
                            '</div>')
                else:
                    html = f'<div style="padding: 15px; border-radius: 30px; color: #a9a9a9; text-align: center;">RF Detector: {rf_status}</div>'
                
                rf_status_placeholder.markdown(html, unsafe_allow_html=True)
            
        
        # --- TAB 2: VISUAL MONITORING (Update the persistent placeholders) ---
        with tab2:
            
            # Left Column Update: Live Feed
            with live_col:
                try:
                    if os.path.exists(FRAME_OUTPUT_FILE_LIVE):
                        img = Image.open(FRAME_OUTPUT_FILE_LIVE)
                        live_placeholder.image(img, caption=f"Real-time Stream | Last Updated: {time.strftime('%H:%M:%S')}", use_container_width=True)
                    else:
                        live_placeholder.image(np.zeros((480, 640, 3), dtype=np.uint8), caption="Waiting for Camera Feed...", use_container_width=True)
                except Exception:
                    live_placeholder.error("Could not load live camera image.")

            # Right Column Update: Most Recent Alert Image
            with log_col:
                path, timestamp, threat_type = get_most_recent_alert_image()
                
                if path and os.path.exists(path):
                    try:
                        alert_img = Image.open(path) 
                        log_placeholder.image(alert_img, use_container_width=True, caption=f"Captured: {timestamp} | Type: {threat_type}")
                    except Exception:
                        log_placeholder.warning("Image found but failed to load.")
                else:
                    log_placeholder.info("No threats have been logged yet.")

        # Control the refresh rate (0.5 second pause)
        time.sleep(0.5) 

if __name__ == "__main__":
    # Safety wrapper for execution
    
    display_dashboard()