import firebase_admin
from firebase_admin import credentials, db
import numpy as np
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ---- Initialize Firebase ----
firebase_creds_path = os.getenv('FIREBASE_CREDENTIALS_PATH_UNAIS')
firebase_db_url = os.getenv('FIREBASE_DATABASE_URL')

cred = credentials.Certificate(firebase_creds_path)
firebase_admin.initialize_app(cred, {
    'databaseURL': firebase_db_url
})

# ---- Firebase References ----
sensor_ref = db.reference('sensor_data')
battery_ref = db.reference('Battery Data')
optimized_ref = db.reference('Optimized Data')
history_ref = db.reference('Optimized History')

# ---- Tariff Structure ----
base_tariff = 0.4
peak_tariff = 1
offpeak_tariff = 0.2
peak_hours = list(range(8, 22))
offpeak_hours = list(range(22, 24)) + list(range(0, 8))

# ---- Function to Compute Tariff ----
def compute_tariff(consumption):
    total_cost = 0
    for hour, usage in enumerate(consumption):
        if hour in peak_hours:
            total_cost += usage * peak_tariff
        elif hour in offpeak_hours:
            total_cost += usage * offpeak_tariff
        else:
            total_cost += usage * base_tariff
    return total_cost

# ---- Tracking Last Fetched Data ----
last_day = None

while True:
    # ---- Fetch Sensor Data ----
    sensor_data = sensor_ref.get()
    if sensor_data:
        latest_day = sorted(sensor_data.keys(), key=lambda x: int(x.split('_')[-1]))[-1]

        if latest_day != last_day:
            latest_values = sensor_data[latest_day]

            # ---- DEBUG: Print raw Firebase data ----
            print(f"\n[DEBUG] Data for {latest_day}:", latest_values)

            # ---- Parse power data safely (list or dict) ----
            try:
                if isinstance(latest_values, list):
                    power_consumption = np.array([
                        int(float(x)) if str(x).replace('.', '', 1).isdigit() else 0 for x in latest_values
                    ])
                elif isinstance(latest_values, dict):
                    power_consumption = np.array([
                        int(float(latest_values.get(str(i), 0))) for i in range(24)
                    ])
                else:
                    print(f"[ERROR] Unexpected data format for {latest_day}")
                    time.sleep(720)
                    continue
            except Exception as e:
                print(f"[ERROR] Failed to parse power data: {e}")
                time.sleep(720)
                continue

            print("[DEBUG] Parsed power_consumption:", power_consumption.tolist())
            print("[DEBUG] Data Length:", len(power_consumption))

            if len(power_consumption) < 24:
                print(f"⚠️ Skipping {latest_day}: Not enough hourly data.")
                time.sleep(720)
                continue

            # ---- Fetch Battery Data ----
            battery_data = battery_ref.get()
            battery_schedule = [
                int(battery_data.get("best_charge_start", 0)),
                int(battery_data.get("best_charge_duration", 0)),
                int(battery_data.get("best_discharge_start", 0)),
                int(battery_data.get("best_discharge_duration", 0))
            ] if battery_data else [0, 0, 0, 0]

            print("[DEBUG] Battery Schedule:", battery_schedule)

            # ---- Optimization ----
            optimized_consumption = power_consumption.copy()
            battery_capacity = 9
            charge_start, charge_duration, discharge_start, discharge_duration = battery_schedule
            charging_hours = list(range(charge_start, min(charge_start + charge_duration, 24)))
            discharging_hours = list(range(discharge_start, min(discharge_start + discharge_duration, 24)))
            charge_profile = [battery_capacity] * len(charging_hours)
            discharge_profile = [battery_capacity] * len(discharging_hours)

            print("[DEBUG] Charging Hours:", charging_hours)
            print("[DEBUG] Discharging Hours:", discharging_hours)

            try:
                for i, hour in enumerate(discharging_hours):
                    optimized_consumption[hour] -= discharge_profile[i]

                for i, hour in enumerate(charging_hours):
                    optimized_consumption[hour] += charge_profile[i]
            except IndexError as e:
                print(f"[ERROR] Index error during optimization: {e}")
                time.sleep(720)
                continue

            # ---- Clamp values and smooth ----
            optimized_consumption = np.clip(optimized_consumption, 10, 30)
            for i in range(1, len(optimized_consumption) - 1):
                optimized_consumption[i] = (
                    optimized_consumption[i - 1] + optimized_consumption[i] + optimized_consumption[i + 1]
                ) / 3
            optimized_consumption = np.round(optimized_consumption).astype(int)

            # ---- Tariff Calculation ----
            cost_without_battery = compute_tariff(power_consumption)
            cost_with_battery = compute_tariff(optimized_consumption)
            savings = cost_without_battery - cost_with_battery

            # ---- Print Results ----
            print(f"\n✅ Processed {latest_day}")
            print("Original Power Consumption:", power_consumption.tolist())
            print("Optimized Power Consumption:", optimized_consumption.tolist())
            print(f"Tariff without Battery: ₹{cost_without_battery}")
            print(f"Tariff with Battery: ₹{cost_with_battery}")
            print(f"💰 Savings: ₹{savings}")

            # ---- Push to Firebase ----
            result_data = {
                "power_consumption": power_consumption.tolist(),
                "optimized_consumption": optimized_consumption.tolist(),
                "cost_without_battery": cost_without_battery,
                "cost_with_battery": cost_with_battery,
                "savings": savings
            }

            optimized_ref.set(result_data)
            history_ref.child(latest_day).set(result_data)

            # ---- Mark Day as Processed ----
            last_day = latest_day

    time.sleep(720)
