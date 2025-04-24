#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>
#include <ArduinoJson.h>
#include <SoftwareSerial.h>

// WiFi credentials
const char* ssid = "Samsung Galaxy A31";
const char* password = "thuuyenbui";

// Server address
String serverAddress = "http://172.20.10.3:8000/esp32-data";

// Tạo đối tượng SoftwareSerial để giao tiếp với Arduino
SoftwareSerial arduinoSerial(3, 1); // RX, TX (GPIO3, GPIO1)

// Accident indicator LED
const int accidentLED = 2;  // Built-in LED

// Variables to store previous state
int prevSignalStates[4][3] = {0};
bool prevAccidentState = false;
int prevAccidentDirection = 0;

unsigned long previousMillis = 0;
const long interval = 1000;  // Update interval in milliseconds

void setup() {
  // Initialize serial communications
  Serial.begin(9600);      // Debug Serial
  arduinoSerial.begin(9600); // Arduino communication
  delay(2000); // Đợi Serial khởi động
  
  Serial.println();
  Serial.println("ESP8266 Traffic Controller Starting");
  
  // Configure LED
  pinMode(accidentLED, OUTPUT);
  digitalWrite(accidentLED, HIGH); // Tắt LED (active LOW)
  
  // Connect to WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  
  int timeout = 0;
  while (WiFi.status() != WL_CONNECTED && timeout < 20) {
    delay(500);
    Serial.print(".");
    timeout++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println();
    Serial.print("Connected to WiFi network with IP Address: ");
    Serial.println(WiFi.localIP());
    
    // Nhấp nháy LED để chỉ báo kết nối thành công
    for (int i = 0; i < 5; i++) {
      digitalWrite(accidentLED, LOW);  // LED bật
      delay(200);
      digitalWrite(accidentLED, HIGH); // LED tắt
      delay(200);
    }
  } else {
    Serial.println();
    Serial.println("Failed to connect to WiFi. Please check credentials.");
  }
}

void loop() {
  unsigned long currentMillis = millis();
  
  // Check if it's time to update
  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis;
    
    // Check WiFi connection status
    if (WiFi.status() == WL_CONNECTED) {
      updateTrafficLights();
    } else {
      Serial.println("WiFi Disconnected. Attempting to reconnect...");
      WiFi.begin(ssid, password);
    }
  }
  
  // Blink accident LED if there's an accident
  if (prevAccidentState) {
    digitalWrite(accidentLED, (currentMillis / 500) % 2);  // Blink every 500ms
  } else {
    digitalWrite(accidentLED, HIGH); // LED tắt khi không có tai nạn
  }
}

void updateTrafficLights() {
  WiFiClient client;
  HTTPClient http;
  
  Serial.println("Connecting to server...");
  http.begin(client, serverAddress);
  
  // Send HTTP GET request
  int httpResponseCode = http.GET();
  
  if (httpResponseCode > 0) {
    Serial.print("HTTP Response code: ");
    Serial.println(httpResponseCode);
    
    String payload = http.getString();
    Serial.println("Received payload:");
    Serial.println(payload);
    
    // Allocate the JSON document
    const size_t capacity = JSON_OBJECT_SIZE(3) + JSON_ARRAY_SIZE(4) + 4*JSON_OBJECT_SIZE(3) + 200;
    DynamicJsonDocument doc(capacity);
    
    // Parse JSON object
    DeserializationError error = deserializeJson(doc, payload);
    if (error) {
      Serial.print("deserializeJson() failed: ");
      Serial.println(error.c_str());
      return;
    }
    
    // Extract signal states
    JsonArray signals = doc["signals"];
    
    // Update signal states
    for (int i = 0; i < 4; i++) {
      prevSignalStates[i][0] = signals[i]["red"];
      prevSignalStates[i][1] = signals[i]["yellow"];
      prevSignalStates[i][2] = signals[i]["green"];
    }
    
    // Check for accident
    prevAccidentState = doc["accident"];
    if (prevAccidentState) {
      prevAccidentDirection = doc["accidentDirection"];
    }
    
    // Send data to Arduino
    sendToArduino();
  }
  else {
    Serial.print("Error code: ");
    Serial.println(httpResponseCode);
  }
  
  // Free resources
  http.end();
}

// Send data to Arduino
void sendToArduino() {
  // Format: "S1:R,Y,G;S2:R,Y,G;S3:R,Y,G;S4:R,Y,G;A:0/1;D:X"
  String message = "S1:";
  message += prevSignalStates[0][0];
  message += ",";
  message += prevSignalStates[0][1];
  message += ",";
  message += prevSignalStates[0][2];
  
  message += ";S2:";
  message += prevSignalStates[1][0];
  message += ",";
  message += prevSignalStates[1][1];
  message += ",";
  message += prevSignalStates[1][2];
  
  message += ";S3:";
  message += prevSignalStates[2][0];
  message += ",";
  message += prevSignalStates[2][1];
  message += ",";
  message += prevSignalStates[2][2];
  
  message += ";S4:";
  message += prevSignalStates[3][0];
  message += ",";
  message += prevSignalStates[3][1];
  message += ",";
  message += prevSignalStates[3][2];
  
  message += ";A:";
  message += prevAccidentState ? "1" : "0";
  
  message += ";D:";
  message += prevAccidentDirection;
  
  // Send to Arduino via SoftwareSerial
  arduinoSerial.println(message);
  
  // Also print to debug Serial
  Serial.println("Sent to Arduino: " + message);
} 