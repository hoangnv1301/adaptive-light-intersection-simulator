#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>
#include <ArduinoJson.h>
#include <Wire.h>

// WiFi credentials
const char* ssid = "Samsung Galaxy A31";
const char* password = "thuuyenbui";

// Server address
String serverAddress = "http://172.20.10.3:8000/esp32-data";

// Arduino I2C address
#define ARDUINO_ADDRESS 0x08

// Accident indicator LED
const int accidentLED = 2;  // Built-in LED

// Variables to store previous state
int signalStates[4][3] = {0};
bool accidentState = false;
int accidentDirection = -1;

unsigned long previousMillis = 0;
const long interval = 1000;  // Update interval in milliseconds

void setup() {
  // Initialize serial communication
  Serial.begin(9600);
  delay(2000);
  
  Serial.println();
  Serial.println("ESP8266 Traffic Controller Starting");
  
  // Initialize I2C
  Wire.begin();
  
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
  if (accidentState) {
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
      signalStates[i][0] = signals[i]["red"];
      signalStates[i][1] = signals[i]["yellow"];
      signalStates[i][2] = signals[i]["green"];
    }
    
    // Check for accident
    accidentState = doc["accident"];
    accidentDirection = doc["accidentDirection"];
    
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

void sendToArduino() {
  // Prepare data to send
  byte data[13]; // 4 signals x 3 states + accident state
  
  // Signal states (12 bytes)
  for (int i = 0; i < 4; i++) {
    for (int j = 0; j < 3; j++) {
      data[i*3 + j] = signalStates[i][j];
    }
  }
  
  // Accident state (1 byte)
  data[12] = accidentState ? 1 : 0;
  
  // Send data via I2C
  Wire.beginTransmission(ARDUINO_ADDRESS);
  Wire.write(data, 13);
  Wire.endTransmission();
  
  Serial.println("Sent traffic data to Arduino via I2C");
  
  // Debug output
  Serial.println("Traffic light states:");
  for (int i = 0; i < 4; i++) {
    Serial.print("Signal ");
    Serial.print(i+1);
    Serial.print(": R=");
    Serial.print(signalStates[i][0]);
    Serial.print(", Y=");
    Serial.print(signalStates[i][1]);
    Serial.print(", G=");
    Serial.println(signalStates[i][2]);
  }
  
  Serial.print("Accident: ");
  Serial.println(accidentState ? "YES" : "NO");
  if (accidentState) {
    Serial.print("Accident Direction: ");
    Serial.println(accidentDirection);
  }
} 