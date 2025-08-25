#include <WiFi.h>

// Wi-Fi Credentials - Set these from environment variables or config file
// TODO: Replace with your actual WiFi credentials from .env file
const char* ssid = "YOUR_WIFI_SSID";        // From WIFI_SSID in .env
const char* password = "YOUR_WIFI_PASSWORD"; // From WIFI_PASSWORD in .env

// Server details - Set these from environment variables or config file
// TODO: Replace with your actual server details from .env file
const char* serverIP = "YOUR_SERVER_IP";     // From SERVER_IP in .env
const int serverPort = 5000;                // From SERVER_PORT in .env

// ACS712 Sensor Configuration
#define ACS712_PIN 34
#define SENSITIVITY 0.185          // Sensitivity for 5A version of ACS712
#define VCC 3.3
#define ADC_RESOLUTION 4095.0
#define ZERO_CURRENT_VOLTAGE 1.65  // Voltage at 0A (bias)

unsigned long lastSendTime = 0;           // For tracking 30-second intervals
const unsigned long sendInterval = 30000; // 30 seconds

void setup() {
    Serial.begin(115200);
    delay(1000);

    Serial.println("🔌 Starting ESP32...");
    WiFi.begin(ssid, password);

    Serial.print("🔗 Connecting to WiFi: ");
    Serial.println(ssid);

    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }

    Serial.println("\n✅ WiFi connected!");
    Serial.print("📶 ESP32 IP Address: ");
    Serial.println(WiFi.localIP());
}

void loop() {
    // Read current every second
    int adcValue = analogRead(ACS712_PIN);
    float voltage = (adcValue / ADC_RESOLUTION) * VCC;
    float current = (voltage - ZERO_CURRENT_VOLTAGE) / SENSITIVITY;
    float power = abs(current * 12.0); // Assuming 12V supply

    Serial.print("🔄 Power Reading: ");
    Serial.print(power, 3);
    Serial.println(" W");

    // Check if it's time to send data
    if (millis() - lastSendTime >= sendInterval) {
        Serial.println("📦 Attempting to send data to server...");

        WiFiClient client;

        if (client.connect(serverIP, serverPort)) {
            String data = String(power, 3); // Only send power value
            client.println(data);
            Serial.print("📤 Sent: ");
            Serial.println(data);
            client.stop(); // Close connection
        } else {
            Serial.println("⚠️ Failed to connect to server.");
        }

        lastSendTime = millis(); // Reset timer
    }

    delay(1000); // Wait 1 second before next reading
}
