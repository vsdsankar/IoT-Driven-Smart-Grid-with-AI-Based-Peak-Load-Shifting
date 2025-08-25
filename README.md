# 🔋 IoT-Driven Smart Grid with AI-Based Peak Load Shifting

## 📋 Project Overview

This project implements an intelligent IoT-based smart grid system that uses artificial intelligence and machine learning to optimize energy consumption and reduce electricity costs through automated battery management and load shifting. The system demonstrates how modern IoT devices, cloud computing, and AI algorithms can work together to create more efficient and cost-effective energy systems.

## 🎯 What This Project Does

### Core Functionality:
- **Real-time Energy Monitoring**: Continuously monitors power consumption using IoT sensors
- **AI-Powered Load Optimization**: Uses machine learning to predict optimal charging/discharging times
- **Automated Battery Management**: Controls battery charging and discharging based on AI recommendations
- **Cost Optimization**: Reduces electricity bills by shifting loads from peak to off-peak hours
- **Live Dashboard**: Provides real-time visualization of energy consumption, battery status, and cost savings

### Key Benefits:
- 💰 **Cost Reduction**: Automatically shifts energy usage to cheaper off-peak hours
- 🔋 **Battery Optimization**: Maximizes battery efficiency through intelligent scheduling
- 📊 **Real-time Monitoring**: Live tracking of power consumption and system performance
- 🤖 **AI-Driven Decisions**: Machine learning algorithms continuously improve optimization
- 🌱 **Environmental Impact**: Reduces peak demand stress on the electrical grid

## 🏗️ System Architecture

The project consists of 6 main components:

### 1. **IoT Sensor Layer** 
- **Touch Sensor Data Acquisition** (`Touch Sensor Data Acquisition for IoT Grid.ino`)
  - Uses ACS712 current sensor to measure power consumption
  - ESP32 microcontroller for WiFi connectivity
  - Sends data every 30 seconds to the server
  - Monitors real-time power usage (Watts)

### 2. **Data Collection & Storage**
- **Real-Time Data Server** (`Real-Time Data Server for Smart Grid.py`)
  - TCP server that receives data from IoT sensors
  - Stores data in Firebase Realtime Database
  - Maintains local CSV backup files
  - Handles 24 hourly readings per day

### 3. **AI & Machine Learning Engine**
- **ML-Based Load Scheduling** (`ML-Based Load Scheduling for IoT Grid.py`)
  - Uses DBSCAN clustering algorithm to analyze consumption patterns
  - Identifies low-demand (charging) and high-demand (discharging) periods
  - Automatically calculates optimal 4-hour charging/discharging windows
  - Sends optimization commands to ESP32 controllers

### 4. **Battery Control System**
- **ESP32 Load Control** (`ESP32 Load Control Script.ino`)
  - Controls battery charging and discharging relays
  - Receives ML optimization commands via WiFi
  - Executes 72-hour automated cycles
  - Provides real-time status feedback

### 5. **Cost Optimization Engine**
- **Tariff & Load Optimizer** (`Tariff & Load Optimizer.py`)
  - Implements time-of-use pricing models
  - Calculates cost savings from load shifting
  - Compares optimized vs non-optimized consumption
  - Stores optimization results in Firebase

### 6. **User Interface & Monitoring**
- **Smart Grid Dashboard** (`Smart Grid Dashboard UI.py`)
  - Real-time web dashboard built with Streamlit
  - Live monitoring of power consumption graphs
  - Battery status visualization with charge levels
  - Cost savings calculations and display
  - 24-hour consumption pattern analysis

## 📊 Data Flow

```
IoT Sensors → Data Server → Firebase Database → ML Engine → Battery Controller
     ↓                                              ↓             ↓
  Power Data                                   Optimization    Battery Control
     ↓                                         Commands         Actions
Dashboard ← Cost Calculator ← Tariff Engine ← Optimized Data
```

## 🔧 Technical Specifications

### Hardware Requirements:
- **ESP32 Development Board** (2 units)
- **ACS712 Current Sensor** (5A version)
- **Relay Modules** (2-channel)
- **Battery System** (9Wh capacity)
- **WiFi Router** for connectivity
- **Computer/Server** for running Python scripts

### Software Stack:
- **IoT Programming**: Arduino IDE (C++)
- **Backend**: Python 3.7+
- **Database**: Firebase Realtime Database
- **Machine Learning**: scikit-learn (DBSCAN clustering)
- **Web Dashboard**: Streamlit
- **Data Visualization**: Matplotlib
- **Environment Management**: python-dotenv

### Key Technologies:
- **IoT Communication**: WiFi (TCP/IP)
- **Machine Learning**: DBSCAN clustering, K-Nearest Neighbors
- **Cloud Database**: Firebase Realtime Database
- **Real-time Dashboard**: Streamlit with auto-refresh
- **Data Processing**: NumPy, Pandas

## 🚀 How It Works

### Step-by-Step Process:

1. **Data Collection**:
   - ACS712 sensor measures current consumption every second
   - ESP32 calculates power (Watts) and sends data every 30 seconds
   - Data server collects 24 hourly readings to form one day's dataset

2. **AI Analysis**:
   - ML algorithm analyzes historical consumption patterns
   - DBSCAN clustering identifies high and low demand periods
   - System calculates optimal 4-hour charging and discharging windows

3. **Battery Optimization**:
   - ESP32 controller receives optimization commands
   - Battery charges during low-demand/low-cost periods
   - Battery discharges during high-demand/high-cost periods

4. **Cost Calculation**:
   - Tariff optimizer applies time-of-use pricing
   - Compares costs with and without battery optimization
   - Calculates actual monetary savings

5. **Real-time Monitoring**:
   - Dashboard displays live consumption graphs
   - Shows battery status and charge levels
   - Visualizes cost savings and optimization results

### Tariff Structure:
- **Peak Hours** (8 AM - 10 PM): ₹1.0 per unit
- **Off-Peak Hours** (10 PM - 8 AM): ₹0.2 per unit
- **Base Tariff**: ₹0.4 per unit

## 📈 Expected Results

### Performance Metrics:
- **Cost Savings**: 15-40% reduction in electricity bills
- **Peak Load Reduction**: 20-30% decrease during peak hours
- **Battery Efficiency**: 85-95% round-trip efficiency
- **System Response Time**: <10 seconds for optimization updates
- **Data Accuracy**: 99% accurate power measurements

### Environmental Impact:
- Reduced strain on electrical grid during peak hours
- More efficient use of renewable energy sources
- Lower carbon footprint through optimized consumption

## 🛠️ Installation & Setup

### Prerequisites:
```bash
# Install Python dependencies
pip install -r requirements.txt

# Set up Firebase account and download service account key
# Configure environment variables in .env file
```

### Configuration:
1. **Hardware Setup**:
   - Connect ACS712 sensor to ESP32 (Pin 34)
   - Connect relay modules to ESP32 (Pins 26, 27)
   - Wire battery system through relays

2. **Software Configuration**:
   - Update WiFi credentials in Arduino files
   - Configure Firebase credentials in .env file
   - Set server IP addresses and ports

3. **Running the System**:
   ```bash
   # Start data collection server
   python "Real-Time Data Server for Smart Grid.py"
   
   # Start ML optimization engine
   python "ML-Based Load Scheduling for IoT Grid.py"
   
   # Start cost optimizer
   python "Tariff & Load Optimizer.py"
   
   # Launch dashboard
   streamlit run "Smart Grid Dashboard UI.py"
   ```

## 📱 Dashboard Features

### Live Monitoring Page:
- Real-time power consumption graphs
- Original vs optimized consumption comparison
- 24-hour consumption patterns
- Color-coded efficiency indicators

### Battery Status Page:
- Real-time battery charge level (0-100%)
- Current operation mode (Charging/Discharging/Idle)
- Day progress indicator
- Optimization schedule display

### Savings Calculator Page:
- Cost comparison (with vs without battery)
- Daily savings calculations
- Monthly/yearly savings projections
- ROI analysis for battery investment

## 🔬 Research & Development

### Machine Learning Approach:
- **DBSCAN Clustering**: Identifies consumption patterns without predefined clusters
- **Automatic Parameter Selection**: Uses K-Nearest Neighbors for optimal epsilon value
- **Adaptive Learning**: System improves predictions over time
- **Real-time Processing**: Updates optimization every 12 minutes (720 seconds)

### Innovation Highlights:
- **Edge Computing**: AI processing on local devices
- **IoT Integration**: Seamless sensor-to-cloud data pipeline
- **Automated Optimization**: No manual intervention required
- **Scalable Architecture**: Can be extended to multiple buildings/devices

## 📊 Project Impact

### Technical Achievements:
- Successful integration of IoT, AI, and cloud technologies
- Real-time data processing and analysis
- Automated decision-making system
- User-friendly monitoring interface

### Practical Applications:
- **Residential**: Home energy management systems
- **Commercial**: Office building optimization
- **Industrial**: Factory load scheduling
- **Grid-Scale**: Utility company demand response

## 👥 Target Users

- **Homeowners**: Seeking to reduce electricity bills
- **Building Managers**: Managing commercial energy costs
- **Utility Companies**: Implementing demand response programs
- **Researchers**: Studying smart grid technologies
- **Students**: Learning IoT and AI applications

## 🔮 Future Enhancements

### Planned Features:
- **Mobile App**: iOS/Android applications
- **Weather Integration**: Solar/wind power predictions
- **Multi-device Support**: Control multiple batteries
- **Blockchain Integration**: Peer-to-peer energy trading
- **Advanced AI**: Deep learning for better predictions

### Scalability Options:
- **Cloud Deployment**: AWS/Azure hosting
- **Edge Computing**: Local processing capabilities
- **5G Integration**: Faster IoT communication
- **Grid Integration**: Utility company APIs

## 📚 Educational Value

This project demonstrates:
- **IoT System Design**: End-to-end sensor networks
- **Machine Learning Applications**: Real-world AI implementations
- **Cloud Computing**: Firebase and web technologies
- **Energy Management**: Smart grid concepts
- **Cost Optimization**: Economic analysis and modeling

## 🤝 Contributing

We welcome contributions to improve this smart grid system! Areas for contribution:
- Algorithm optimization
- User interface improvements
- Additional sensor integrations
- Cost model enhancements
- Documentation updates

## 📝 License

This project is developed for educational and research purposes. Please refer to individual component licenses for commercial use.

---

**Project Team**: Batch-13 (Students 62, 64, 65, 66)  
**Course**: Smart Grid & IoT, Semester 6, EEE Department, Amrita School of Engineering, Coimbatore.  
**Keywords**: IoT, Smart Grid, Machine Learning, Energy Optimization, Firebase, ESP32, Load Shifting, Cost Reduction 