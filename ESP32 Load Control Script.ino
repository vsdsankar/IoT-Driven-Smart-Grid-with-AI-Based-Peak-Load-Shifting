#include <WiFi.h>

// WiFi Credentials - Set these from environment variables or config file
// TODO: Replace with your actual WiFi credentials from .env file
const char* ssid = "YOUR_WIFI_SSID";        // From WIFI_SSID in .env
const char* password = "YOUR_WIFI_PASSWORD"; // From WIFI_PASSWORD in .env

// Server Settings
WiFiServer server(6000);  // Listening on port 6000

// Relay Pins
const int chargeRelay = 26;  // Relay for charging
const int dischargeRelay = 27; // Relay for discharging

// Actuation Variables
int chargeStart = -1, chargeDuration = 0;
int dischargeStart = -1, dischargeDuration = 0;
bool dataReceivedFlag = false;  // Flag to check if we have received initial data

void setup() {
    Serial.begin(115200);

    // Connect to WiFi
    WiFi.begin(ssid, password);
    Serial.print("Connecting to WiFi...");
    while (WiFi.status() != WL_CONNECTED) {
        delay(1000);
        Serial.print(".");
    }

    Serial.println("\nConnected!");
    Serial.print("ESP32 IP: ");
    Serial.println(WiFi.localIP());

    // Start Server
    server.begin();
    Serial.println("Server started, waiting for connection...");

    // Set Relay Pins as Output
    pinMode(chargeRelay, OUTPUT);
    pinMode(dischargeRelay, OUTPUT);
    digitalWrite(chargeRelay, LOW);
    digitalWrite(dischargeRelay, LOW);
}

void loop() {
    if (!dataReceivedFlag) {
        receiveData();  // Get data from Python if not received
    }

    if (dataReceivedFlag) {
        executeCycle(); // Run the 72-hour execution cycle
    }
}

// Function to receive data from Python
void receiveData() {
    WiFiClient client = server.available(); // Check for incoming client

    if (client) {
        Serial.println("Client Connected!");

        String receivedData = "";
        unsigned long startTime = millis();
        bool dataReceived = false;

        // Wait for complete message with timeout
        while (client.connected()) {
            while (client.available()) {
                char c = client.read();
                receivedData += c;
                if (c == '\n') {
                    dataReceived = true;
                    break; // Stop when newline is received
                }
            }

            // Timeout to prevent infinite loop
            if (millis() - startTime > 5000) {
                Serial.println("Timeout while receiving data!");
                break;
            }

            if (dataReceived) break;
        }

        receivedData.trim(); // Remove unwanted spaces or newlines
        Serial.println("Received Data: " + receivedData);

        // Parse received data
        int parsed = sscanf(receivedData.c_str(), "%d,%d,%d,%d", &chargeStart, &chargeDuration, &dischargeStart, &dischargeDuration);

        if (parsed == 4) {
            Serial.printf("Charging Start: %d, Duration: %d hours\n", chargeStart, chargeDuration);
            Serial.printf("Discharging Start: %d, Duration: %d hours\n", dischargeStart, dischargeDuration);

            client.print("ACK\n");  // Send acknowledgment
            Serial.println("Acknowledgment sent to Python.");

            dataReceivedFlag = true;  // Mark that valid data is received
        } else {
            Serial.println("Invalid data format received!");
            client.print("ERROR\n");
        }

        client.stop(); // Close connection
        Serial.println("Client Disconnected!");
    }
}

// Function to execute 72-hour cycle
void executeCycle() {
    Serial.println("🔄 Starting 72-hour execution...");

    for (int hour = 0; hour < 72; hour++) {
        Serial.print("⏳ Hour: "); Serial.println(hour % 24); // Show time in 24-hour format

        // Check Charging Period
        if ((hour % 24) >= chargeStart && (hour % 24) < chargeStart + chargeDuration) {
            digitalWrite(chargeRelay, HIGH);
            Serial.println("⚡ Battery is CHARGING...");
        } else {
            digitalWrite(chargeRelay, LOW);
        }

        // Check Discharging Period
        if ((hour % 24) >= dischargeStart && (hour % 24) < dischargeStart + dischargeDuration) {
            digitalWrite(dischargeRelay, HIGH);
            Serial.println("🔋 Battery is DISCHARGING...");
        } else {
            digitalWrite(dischargeRelay, LOW);
        }

        // If neither charging nor discharging, battery is idle
        if (!((hour % 24) >= chargeStart && (hour % 24) < chargeStart + chargeDuration) &&
            !((hour % 24) >= dischargeStart && (hour % 24) < dischargeStart + dischargeDuration)) {
            Serial.println("🛑 Battery is IDLE.");
        }

        delay(30000);  // Simulate each hour as 1 second (for testing)
    }

    Serial.println("✅ 72-hour cycle complete. Waiting for new data...");
    dataReceivedFlag = false;  // Reset to wait for new data
}
