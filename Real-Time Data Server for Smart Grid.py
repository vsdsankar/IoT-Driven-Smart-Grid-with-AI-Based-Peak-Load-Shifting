import socket
import csv
import os
import firebase_admin
from firebase_admin import credentials, db
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ----------------- Firebase Initialization -----------------
FIREBASE_CREDENTIALS_PATH = os.getenv('FIREBASE_CREDENTIALS_PATH_PRANA')
FIREBASE_DATABASE_URL = os.getenv('FIREBASE_DATABASE_URL')

try:
    cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred, {
        'databaseURL': FIREBASE_DATABASE_URL
    })
    print("✅ Firebase initialized successfully.")
except Exception as e:
    print("❌ Firebase initialization failed:", e)
    exit()

# Firebase database reference
ref = db.reference('sensor_data')
READINGS_PER_DAY = 24  # 24 readings make one full dataset

# ----------------- Server Configuration -----------------
HOST = os.getenv('SERVER_HOST', '')           # Listen on all available interfaces
PORT = int(os.getenv('SERVER_PORT', 5000))    # Must match the ESP32 port
CSV_FILE = os.getenv('CSV_FILE_PATH')
MAX_LOCAL_ROWS = int(os.getenv('MAX_LOCAL_ROWS', 300))  # Keep only the latest 10 days locally

def print_server_ips():
    """Prints all available IPs for the server."""
    hostname = socket.gethostname()
    host_ips = socket.gethostbyname_ex(hostname)
    print("📡 Server host details:")
    print(f"   🔹 Hostname: {hostname}")
    print(f"   🔹 IP Addresses: {host_ips[2]}")

# ----------------- CSV File Setup -----------------
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        header = ['Day'] + [f'Hour_{i}' for i in range(READINGS_PER_DAY)]
        writer.writerow(header)
    print(f"✅ Created CSV file: {CSV_FILE}")

def load_rows():
    """Load existing rows from CSV (skip header)."""
    rows = []
    with open(CSV_FILE, 'r') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        for row in reader:
            rows.append(row)
    return rows

def save_rows(rows):
    """Save only the latest MAX_LOCAL_ROWS to the CSV file."""
    with open(CSV_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        header = ['Day'] + [f'Hour_{i}' for i in range(READINGS_PER_DAY)]
        writer.writerow(header)
        writer.writerows(rows[-MAX_LOCAL_ROWS:])  # Keep only the latest 10 rows
    print(f"✅ CSV file updated. Keeping only the last {MAX_LOCAL_ROWS} days.")

# ----------------- Main Server Code -----------------
def main():
    print_server_ips()
    rows = load_rows()  # Load existing rows from file
    current_row = []    # Buffer for the current row of readings

    current_day = len(rows) + 1  # Determine next day count from existing data
    readings = {}

    # Set up the TCP server socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((HOST, PORT))
            s.listen()
            print(f"🚀 Server listening on port {PORT}...")
        except Exception as e:
            print("❌ Error binding the socket:", e)
            return
        
        while True:
            try:
                conn, addr = s.accept()
                with conn:
                    print(f"🔗 Connected by {addr}")
                    data = conn.recv(1024).decode().strip()
                    if not data:
                        print("⚠️ No data received.")
                        continue
                    print(f"📩 Received data: {data}")

                    # Append reading to batch
                    readings[len(readings)] = data  # Store readings as index-value pairs

                    # If we have 24 readings, push to Firebase correctly
                    if len(readings) == READINGS_PER_DAY:
                        day_key = f'Day_{current_day}'
                        try:
                            ref.child(day_key).set(readings)  # Store readings under `Day_1`, `Day_2`, etc.
                            print(f"✅ Uploaded {day_key} to Firebase correctly.")
                        except Exception as e:
                            print("❌ Firebase upload error:", e)

                        # Append new row to CSV
                        new_row = [f'Day_{current_day}'] + list(readings.values())
                        rows.append(new_row)

                        # Keep only the latest MAX_LOCAL_ROWS rows
                        if len(rows) > MAX_LOCAL_ROWS:
                            rows = rows[-MAX_LOCAL_ROWS:]

                        save_rows(rows)
                        print(f"✅ Saved {day_key} to CSV. Total rows locally: {len(rows)}")

                        readings = {}  # Reset for the next day
                        current_day += 1  # Move to the next day
                    
                    # Append received reading to the current row
                    current_row.append(data)
                    print(f"📝 Current row length: {len(current_row)} / {READINGS_PER_DAY}")

            except Exception as e:
                print("❌ Error during connection handling:", e)

if __name__ == '__main__':
    main()