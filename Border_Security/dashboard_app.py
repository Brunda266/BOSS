import streamlit as st
from PIL import Image
import numpy as np
import time
import os
import sqlite3
import pandas as pd
import io 

# --- CONFIGURATION ---
ALERT_STATUS_FILE = 'alert_status.txt'
FRAME_OUTPUT_FILE_LIVE = 'current_frame.jpg'
RF_STATUS_FILE = 'rf_status.txt'
DB_NAME = 'surveillance_log.db'
ALERT_IMAGE_DIR = 'alert_images'
BACKGROUND_IMAGE_PATH = 'border.jpg' # <-- CHANGE THIS PATH/FILENAME
# --- END CONFIGURATION ---

# --- Custom CSS Function (NEW) ---
# dashboard_app.py (Replace the function definition)

# --- Custom CSS Function (UPDATED FOR ROBUSTNESS) ---
def add_bg_from_local(image_file):
    import base64
    if not os.path.exists(image_file):
        st.error(f"Background image file not found at: {image_file}")
        return

    with open(image_file, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    
    # Inject CSS to set the background image
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpeg;base64,{data}");
            background-size: cover;
            background-position: center center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
  /* 2. Target the main content blocks (headers, markdown, titles) 
              to give them a semi-transparent black background and white text. */
        .stApp, .css-1d3f9g6, .main, .block-container {{
            color: white; /* Ensures text is white */
            /* Add a semi-transparent black background to content areas */
            background-color: rgba(0, 0, 0, 0.7) !important; 
        }}
        
        /* 3. Ensure the markdown headers and text are white (if necessary) */
        h1, h2, h3, h4, .stText {{
            color: white !important;
        }}
        
        /* Remove extra Streamlit styling boxes if needed */
        .stTabs [data-baseweb="tab-list"] {{
            background-color: rgba(0, 0, 0, 0.8) !important;
        }}
        
        </style>
        """,
        unsafe_allow_html=True
    )
# --- End Custom CSS Function ---

# --- Status Check Helper Functions (Kept the same) ---
def check_alert_status():
    try:
        with open(ALERT_STATUS_FILE, 'r') as f:
            return f.read().strip()
    except FileNotFoundError: return "INIT"
    except Exception: return "ERROR"

def check_rf_status():
    try:
        with open(RF_STATUS_FILE, 'r') as f:
            return f.read().strip()
    except FileNotFoundError: return "RF_INIT"
    except Exception: return "RF_ERROR"
        
def get_most_recent_alert_image():
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
    # --- 1. Apply Background Image ---
    # Call the function directly here
    add_bg_from_local(BACKGROUND_IMAGE_PATH)

    # --- UI Setup (Run only once) ---
    st.set_page_config(
        page_title="Border Security System", 
        layout="wide", 
        initial_sidebar_state="collapsed", 
        menu_items={'About': "Border Surveillance System - Minor Project"}
    )
    
    st.title(" Border Security Monitoring System")
    st.markdown("---")

    status_header = st.empty()
    
    # Define tabs
    tab1, tab2 = st.tabs([" THREAT MONITORING", " VISUAL MONITORING"])
    
    # Define persistent placeholders outside the loop
    with tab1:
        st.subheader("Current Surveillance Status Metrics")
        col_h, col_r = st.columns(2)
        with col_h:
            st.markdown("###  Human Intrusion Status")
            human_status_placeholder = st.empty()
        with col_r:
            st.markdown("###  Device Inference Status")
            rf_status_placeholder = st.empty()
            
    with tab2:
        live_col, log_col = st.columns(2)
        with live_col:
            st.markdown("###  Live Surveillance Stream")
            live_placeholder = st.empty()
        with log_col:
            st.markdown("###  Most Recent Alert Image")
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
            status_header.error(" CRITICAL THREAT DETECTED! Review Status Panels. ")
        elif human_status == "NORMAL" and rf_status == "RF_CLEAR":
            status_header.success(" System Operational. ALL SYSTEMS NORMAL")
        else:
            status_header.info(" Monitoring...")

        
        # --- TAB 1: THREAT MONITORING (Update the persistent placeholders with direct status text) ---
        with tab1:
            # Column H: Human Detection Status
            with col_h:
                if human_status == "ALERT":
                    html = ('<div style="background-color: #ff4b4b; padding: 15px; border-radius: 8px; color: black; text-align: center;">'
                            '<h1>THREAT DETECTED</h1>'
                            '</div>')
                elif human_status == "NORMAL":
                    html = ('<div style="background-color: #008000; padding: 15px; border-radius: 8px; color: black; text-align: center;">'
                            '<h1>SAFE CONDITION</h1>'
                            '</div>')
                else:
                    html = f'<div style="padding: 15px; border-radius: 8px; color: #a9a9a9; text-align: center;">Human Detector: {human_status}</div>'
                
                human_status_placeholder.markdown(html, unsafe_allow_html=True)


            # Column R: RF Inference Status
            with col_r:
                if rf_status == "RF_THREAT":
                    html = ('<div style="background-color: #ff4b4b; padding: 15px; border-radius: 8px; color: black; text-align: center;">'
                            '<h1>THREAT DETECTED</h1>'
                            '</div>')
                elif rf_status == "RF_CLEAR":
                    html = ('<div style="background-color: #008000; padding: 15px; border-radius: 8px; color: black; text-align: center;">'
                            '<h1>SAFE CONDITION</h1>'
                            '</div>')
                else:
                    html = f'<div style="padding: 15px; border-radius: 8px; color: #a9a9a9; text-align: center;">RF Detector: {rf_status}</div>'
                
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
    # Ensure helper functions are correctly defined for execution (NO PLACEHOLDERS HERE)
    display_dashboard()