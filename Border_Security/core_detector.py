import cv2
import numpy as np
import time
import os
import winsound
from ultralytics import YOLO
import sqlite3 # NEW: Database library

# --- CONFIGURATION ---
PERSON_CLASS_ID = 0
CONFIDENCE_THRESHOLD = 0.5
ALERT_COOLDOWN_SECONDS = 5

# --- Shared Files & DB ---
ALERT_STATUS_FILE = 'alert_status.txt'
FRAME_OUTPUT_FILE_LIVE = 'current_frame.jpg' # Only the latest frame is saved here
DB_NAME = 'surveillance_log.db'              # NEW: Database file
ALERT_IMAGE_DIR = 'alert_images'             # NEW: Directory to store alert screenshots
# --- END CONFIGURATION ---

last_alert_time = 0

def init_db():
    """Initializes the SQLite database and the alert image directory."""
    os.makedirs(ALERT_IMAGE_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Create the log table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS threat_log (
            id INTEGER PRIMARY KEY,
            timestamp TEXT NOT NULL,
            type TEXT NOT NULL,
            image_path TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def log_threat_to_db(frame, threat_type="Human"):
    """Saves the frame and logs the event to the database."""
    timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
    
    # Save the frame as a PNG to preserve quality for logging
    image_filename = f"{threat_type}_{timestamp}.png"
    image_path = os.path.join(ALERT_IMAGE_DIR, image_filename)
    cv2.imwrite(image_path, frame)
    
    # Log to database
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO threat_log (timestamp, type, image_path) VALUES (?, ?, ?)", 
                   (timestamp, threat_type, image_path))
    conn.commit()
    conn.close()
    print(f"Logged {threat_type} threat at {timestamp}")


def update_live_feed(frame, status):
    """Updates only the status file and the single live frame image."""
    try:
        # Update the status file
        with open(ALERT_STATUS_FILE, 'w') as f:
            f.write(status)
        
        # Save the frame for the live feed placeholder
        cv2.imwrite(FRAME_OUTPUT_FILE_LIVE, frame)
        
    except Exception as e:
        print(f"Error updating live files: {e}")

def trigger_local_alert():
    # (The function body remains the same as before)
    global last_alert_time
    
    current_time = time.time()
    if current_time - last_alert_time < ALERT_COOLDOWN_SECONDS:
        return
    
    print("--- ALERT: Intrusion detected. Triggering local sound alert. ---")
    
    try:
        # Play a simple system sound (500Hz frequency for 500ms duration)
        winsound.Beep(500, 500) 
        last_alert_time = current_time 
    except Exception as e:
        print(f"ERROR: Could not play sound. Error: {e}")


if __name__ == "__main__":
    init_db() # Initialize the database upon startup

    try:
        model = YOLO('yolov8n.pt') 
    except Exception as e:
        print(f"ERROR: Could not load YOLO model. {e}")
        exit()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: Could not open laptop camera (Index 0). Exiting.")
        update_live_feed(np.zeros((480, 640, 3), dtype=np.uint8), "ERROR")
        exit()

    print("--- Surveillance System Active ---")
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        current_detection_status = "NORMAL"
        human_detected = False
        
        results = model(frame, verbose=False, classes=[PERSON_CLASS_ID]) 
        
        for result in results:
            for box in result.boxes:
                if box.conf[0] > CONFIDENCE_THRESHOLD:
                    human_detected = True
                    
                    # Draw Bounding Box and Label
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
                    label = f"INTRUDER: {box.conf[0]*100:.1f}%"
                    cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                    
                    trigger_local_alert() 
                    current_detection_status = "ALERT" 
        
        # --- LOGGING THREAT FRAMES ---
        if human_detected:
            # We log the frame *only* if a human is detected
            log_threat_to_db(frame, threat_type="Human")

        # --- UPDATE LIVE FEED ---
        update_live_feed(frame, current_detection_status)

        cv2.imshow('Detector: Press Q to Quit', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    update_live_feed(frame, "SYSTEM_OFF") 
    print("--- Surveillance System Shut Down ---")