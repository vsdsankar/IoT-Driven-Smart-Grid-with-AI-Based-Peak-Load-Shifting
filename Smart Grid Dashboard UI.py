import streamlit as st
from streamlit_option_menu import option_menu
import time
import matplotlib.pyplot as plt
import numpy as np
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Initialize Firebase ---
firebase_creds_path = os.getenv('FIREBASE_CREDENTIALS_PATH_UNAIS')
firebase_db_url = os.getenv('FIREBASE_DATABASE_URL')

cred = credentials.Certificate(firebase_creds_path)
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred, {
        'databaseURL': firebase_db_url
    })

# --- Constants ---
DAY_DURATION = 720  # 720 seconds = 1 "day" in the simulation
HOUR_DURATION = DAY_DURATION / 24  # Each "hour" lasts 30 seconds

# --- Session State Initialization ---
if "previous_data" not in st.session_state:
    st.session_state.previous_data = None
if "simulation_start_time" not in st.session_state:
    st.session_state.simulation_start_time = time.time()
if "last_fetch_time" not in st.session_state:
    st.session_state.last_fetch_time = 0

# --- Firebase Fetch Logic ---
def parse_24_hour_data(data):
    if isinstance(data, dict):
        return [int(data.get(str(i), 0)) for i in range(24)]
    elif isinstance(data, list):
        return [int(data[i]) if i < len(data) else 0 for i in range(24)]
    return [0] * 24

def fetch_firebase_data():
    # Battery Timing
    battery_data = db.reference("Battery Data").get()
    best_charge_start = battery_data.get("best_charge_start", 0) if battery_data else 0
    best_charge_duration = battery_data.get("best_charge_duration", 0) if battery_data else 0
    best_discharge_start = battery_data.get("best_discharge_start", 0) if battery_data else 0
    best_discharge_duration = battery_data.get("best_discharge_duration", 0) if battery_data else 0

    # Tariff + Power Data
    optimized_data = db.reference("Optimized Data").get()
    cost_with_battery = optimized_data.get("cost_with_battery", 0) if optimized_data else 0
    cost_without_battery = optimized_data.get("cost_without_battery", 0) if optimized_data else 0
    optimized_consumption = optimized_data.get("optimized_consumption", {}) if optimized_data else {}
    power_consumption = optimized_data.get("power_consumption", {}) if optimized_data else {}

    original_power = parse_24_hour_data(power_consumption)
    optimized_power = parse_24_hour_data(optimized_consumption)

    return {
        "cost_with_battery": cost_with_battery,
        "cost_without_battery": cost_without_battery,
        "original_power": original_power,
        "optimized_power": optimized_power,
        "charging_start_time": best_charge_start,
        "charging_duration": best_charge_duration,
        "discharging_start_time": best_discharge_start,
        "discharging_duration": best_discharge_duration,
        "fetch_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

# --- Battery Simulation Functions ---
def calculate_battery_state(current_data):
    elapsed_time = time.time() - st.session_state.simulation_start_time
    if elapsed_time > DAY_DURATION:
        st.session_state.simulation_start_time = time.time()
        elapsed_time = 0
    
    current_hour = (elapsed_time / HOUR_DURATION) % 24
    
    # Get timing parameters
    charging_start = current_data["charging_start_time"]
    charging_end = charging_start + current_data["charging_duration"]
    discharging_start = current_data["discharging_start_time"]
    discharging_end = discharging_start + current_data["discharging_duration"]
    
    # 1. Start of day - battery is full (100%)
    if current_hour < discharging_start:
        battery_charge = 100
        status = "idle (full)"
    
    # 2. Discharging period
    elif discharging_start <= current_hour < discharging_end:
        progress = (current_hour - discharging_start) / current_data["discharging_duration"]
        battery_charge = max(0, 100 - (progress * 100))
        status = "discharging"
    
    # 3. After discharge, before charging - battery is empty (0%)
    elif discharging_end <= current_hour < charging_start:
        battery_charge = 0
        status = "idle (discharged)"
    
    # 4. Charging period
    elif charging_start <= current_hour < charging_end:
        progress = (current_hour - charging_start) / current_data["charging_duration"]
        battery_charge = min(100, progress * 100)
        status = "charging"
    
    # 5. After charging complete - battery stays full (100%) until next day
    else:
        battery_charge = 100
        status = "idle (charged)"
    
    return {
        "charge": battery_charge,
        "status": status,
        "current_hour": current_hour,
        "day_progress": (elapsed_time / DAY_DURATION) * 100
    }

def show_battery_display(battery_state):
    fig, ax = plt.subplots(figsize=(8, 2))
    charge = battery_state["charge"]
    
    color = 'green' if charge > 66 else 'orange' if charge > 33 else 'red'
    ax.add_patch(plt.Rectangle((0, 0), 100, 10, fill=False, edgecolor='black', linewidth=2))
    ax.add_patch(plt.Rectangle((0, 0), charge, 10, color=color))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 10)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(f"Battery: {int(charge)}% (Hour: {int(battery_state['current_hour'])})", fontsize=12)
    
    st.pyplot(fig)
    
    if "discharging" in battery_state["status"]:
        st.warning(f"⚡ {battery_state['status']} | Day Progress: {battery_state['day_progress']:.1f}%")
    elif "charging" in battery_state["status"]:
        st.success(f"🔌 {battery_state['status']} | Day Progress: {battery_state['day_progress']:.1f}%")
    else:
        st.info(f"⏸️ {battery_state['status']} | Day Progress: {battery_state['day_progress']:.1f}%")

# --- UI Sections ---
def show_live_monitoring(original_power, optimized_power):
    st.subheader("📊 Live Monitoring")
    hours = list(range(24))
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(hours, original_power, marker="o", linestyle="-", color="red", label="Original Power Consumption")
    ax.plot(hours, optimized_power, marker="s", linestyle="--", color="green", label="Optimized Power Consumption")
    ax.set_xlabel("Hour of the Day")
    ax.set_ylabel("Power Consumption (W)")
    ax.set_title("Power Consumption Comparison")
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.7)
    st.pyplot(fig)

def show_savings_calculation(cost_with_battery, cost_without_battery, cost_savings):
    st.subheader("💰 Savings (Tariff Calculation)")
    formatted_savings = abs(round(cost_savings, 2))
    savings_color = "#79c118" if cost_savings >= 0 else "#FF0000"
    
    col1, col2 = st.columns([1, 1])
    col3 = st.container()
    st.markdown(f"""
        <style>
        .big-box {{
            padding: 40px;
            text-align: center;
            font-size: 24px;
            font-weight: bold;
            border-radius: 10px;
            margin: 10px;
            border: 4px solid black;
            width: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }}
        .orange {{ background-color: #FF8C00; color: white; }}
        .blue {{ background-color: #1976D2; color: white; }}
        .savings {{ background-color: {savings_color}; color: white; }}
        .box-value {{ font-size: 35px; font-weight: bold; margin-bottom: 5px; }}
        .box-label {{ font-size: 18px; font-weight: normal; }}
        </style>
        """, unsafe_allow_html=True)

    with col1:
        st.markdown(f"""
            <div class="big-box orange">
                <div class="box-value">₹{cost_with_battery:.2f}</div>
                <div class="box-label">Cost With Battery</div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
            <div class="big-box blue">
                <div class="box-value">₹{cost_without_battery:.2f}</div>
                <div class="box-label">Cost Without Battery</div>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
            <div class="big-box savings" style="width: 50%; margin: auto;">
                <div class="box-value">₹{formatted_savings:.2f}</div>
                <div class="box-label">Savings</div>
            </div>
        """, unsafe_allow_html=True)

# --- Main UI ---
def main():
    st.title("IoT-driven Peak Load Shifting Dashboard")

    with st.sidebar:
        option = option_menu(
            "IoT-driven Peak Load Shifting",
            ["Live Monitoring", "Battery Status", "Savings (Tariff Calculation)"],
            icons=["bar-chart", "battery", "dollar-sign"],
            default_index=0
        )

    # Fetch new data only once per day (720 seconds)
    if (time.time() - st.session_state.last_fetch_time) > DAY_DURATION:
        current_data = fetch_firebase_data()
        st.session_state.previous_data = current_data
        st.session_state.last_fetch_time = time.time()
        st.session_state.simulation_start_time = time.time()
        print(f"✅ New data fetched at {current_data['fetch_time']}")
    else:
        current_data = st.session_state.previous_data

    if current_data is None:
        st.warning("Initializing... Please wait")
        time.sleep(2)
        st.rerun()

    # --- UI Display ---
    if option == "Live Monitoring":
        show_live_monitoring(current_data["original_power"], current_data["optimized_power"])
    elif option == "Battery Status":
        battery_state = calculate_battery_state(current_data)
        show_battery_display(battery_state)
    elif option == "Savings (Tariff Calculation)":
        cost_savings = current_data["cost_without_battery"] - current_data["cost_with_battery"]
        show_savings_calculation(
            current_data["cost_with_battery"],
            current_data["cost_without_battery"],
            cost_savings
        )

    # Refresh every 10 seconds (adjust as needed)
    time.sleep(10)
    st.rerun()

if __name__ == "__main__":
    main()