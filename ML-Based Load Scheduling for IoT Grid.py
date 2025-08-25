import pandas as pd
import numpy as np
import socket
import time
import firebase_admin
from firebase_admin import credentials, db
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.neighbors import NearestNeighbors
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# 🔥 Firebase Configuration
FIREBASE_CREDENTIALS_PATH = os.getenv('FIREBASE_CREDENTIALS_PATH_PRANA')
DATABASE_URL = os.getenv('FIREBASE_DATABASE_URL')

# Initialize Firebase (if not already initialized)
if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred, {"databaseURL": DATABASE_URL})

# 🔌 ESP32 Configuration
ESP32_IP = os.getenv('ESP32_IP')  # Update with actual ESP32 IP
ESP32_PORT = int(os.getenv('ESP32_SERVER_PORT', 6000))
file_path = os.getenv('CSV_FILE_PATH')

def process_ml_model():
    print("\n===== Running ML Model =====", flush=True)

    # --- Load Dataset ---
    dataset = pd.read_csv(file_path)

    # Convert all non-numeric values to NaN and fill them with mean
    dataset.iloc[:, 1:] = dataset.iloc[:, 1:].apply(pd.to_numeric, errors='coerce')

    # Handle Missing Values
    imputer = SimpleImputer(strategy="mean")
    X = dataset.iloc[:, 1:].values
    X = imputer.fit_transform(X)

    # Normalize Data (Standardization)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # --- Automatic eps Selection Using Nearest Neighbors ---
    neighbors = NearestNeighbors(n_neighbors=5)
    neighbors_fit = neighbors.fit(X_scaled)
    distances, indices = neighbors_fit.kneighbors(X_scaled)

    # Find eps from the knee-point of sorted distances
    sorted_distances = np.sort(distances[:, -1])
    eps_value = sorted_distances[int(0.9 * len(sorted_distances))]

    print(f"Calculated eps value for DBSCAN: {eps_value}", flush=True)

    # Apply DBSCAN with found eps
    dbscan = DBSCAN(eps=eps_value, min_samples=3)
    cluster_labels = dbscan.fit_predict(X_scaled)

    # Extract unique clusters (excluding noise)
    unique_labels = np.unique(cluster_labels)
    unique_labels = unique_labels[unique_labels != -1]

    if len(unique_labels) > 0:
        # Compute cluster-wise average power consumption
        cluster_means = np.array([X[cluster_labels == i].mean(axis=0) for i in unique_labels])

        # Identify Low-Demand (Charging) & High-Demand (Discharging) clusters
        low_demand_cluster = np.argmin(cluster_means.sum(axis=1))
        high_demand_cluster = np.argmax(cluster_means.sum(axis=1))

        # Get hourly trends
        low_demand_hours = cluster_means[low_demand_cluster]
        high_demand_hours = cluster_means[high_demand_cluster]

        # --- Find Best Charging & Discharging Hours using a 4-hour window ---
        best_charge_start = np.argmin([sum(low_demand_hours[i:i+4]) for i in range(21)])
        best_charge_duration = 4

        best_discharge_start = np.argmax([sum(high_demand_hours[i:i+4]) for i in range(21)])
        best_discharge_duration = 4

        # Output required values
        print(f"Best Charge Start: {best_charge_start}", flush=True)
        print(f"Best Charge Duration: {best_charge_duration} hours", flush=True)
        print(f"Best Discharge Start: {best_discharge_start}", flush=True)
        print(f"Best Discharge Duration: {best_discharge_duration} hours", flush=True)

        # --- Sending Data to ESP32 ---
        data_to_send = f"{int(best_charge_start)},{int(best_charge_duration)},{int(best_discharge_start)},{int(best_discharge_duration)}\n"
        print(f"Sending Data to ESP32: {data_to_send.strip()}", flush=True)

        response = send_to_esp32(data_to_send)

        # Print received response
        print(f"📥 Received from ESP32: {response}", flush=True)

        # --- Update Firebase (Inside "Battery Data") ---
        update_firebase(best_charge_start, best_charge_duration, best_discharge_start, best_discharge_duration)

    else:
        print("No valid clusters found! Check dataset and retry.", flush=True)

    print("✅ Acknowledgment: Data processing & transmission completed. Waiting for next cycle...\n", flush=True)

def send_to_esp32(data):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5)
            s.connect((ESP32_IP, ESP32_PORT))
            s.sendall(data.encode())
            print("Data Sent Successfully!", flush=True)

            # Wait for ESP32 Response
            response = s.recv(1024).decode().strip()
            print(f"✅ ESP32 Response Received: {response}", flush=True)
            return response
    except Exception as e:
        print(f"⚠️ Error: {e}", flush=True)
        return "Error"

def update_firebase(charge_start, charge_duration, discharge_start, discharge_duration):
    try:
        ref = db.reference("/Battery Data")
        ref.set({
            "best_charge_start": int(charge_start),
            "best_charge_duration": int(charge_duration),
            "best_discharge_start": int(discharge_start),
            "best_discharge_duration": int(discharge_duration),
            "last_updated": time.strftime("%Y-%m-%d %H:%M:%S")
        })
        print("🔥 Firebase Updated Successfully Inside 'Battery Data'!", flush=True)
    except Exception as e:
        print(f"⚠️ Firebase Error: {e}", flush=True)

# --- Run the model every 72 seconds ---
if __name__ == "__main__":
    while True:
        process_ml_model()
        print("⏳ Waiting for 72 seconds before the next update...\n", flush=True)
        time.sleep(720)