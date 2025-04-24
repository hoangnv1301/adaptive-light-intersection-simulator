#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>
#include <ArduinoJson.h>

// WiFi credentials
const char* ssid = "Samsung Galaxy A31";
const char* password = "thuuyenbui";

// Server address
String serverAddress = "http://192.168.1.8:8000/esp32-data";

// Pins for traffic lights
// Signal 1
const int red1 = D0;
const int yellow1 = D1;
const int green1 = D2;
// Signal 2
const int red2 = D3;
const int yellow2 = D4;
const int green2 = D5;
// Signal 3
const int red3 = D6;
const int yellow3 = D7;
const int green3 = D8;
// Signal 4
const int red4 = 3;     // RX pin
const int yellow4 = 1;  // TX pin
const int green4 = 10;  // SD3

// Variables to store previous state
int prevSignalStates[4][3] = {0};
bool prevAccidentState = false;
int prevAccidentDirection = 0;

// Accident indicator LED
const int accidentLED = 2;  // Built-in LED

unsigned long previousMillis = 0;
const long interval = 1000;  // Update interval in milliseconds

void setup() {
  // Initialize serial communication
  Serial.begin(9600);
  delay(2000); // Đợi Serial khởi động
  
  Serial.println();
  Serial.println("ESP8266 Traffic Controller Starting");
  
  // Configure LED
  pinMode(accidentLED, OUTPUT);
  digitalWrite(accidentLED, HIGH); // Tắt LED (active LOW)
  
  // Configure all LED pins as OUTPUT
  pinMode(red1, OUTPUT);
  pinMode(yellow1, OUTPUT);
  pinMode(green1, OUTPUT);
  pinMode(red2, OUTPUT);
  pinMode(yellow2, OUTPUT);
  pinMode(green2, OUTPUT);
  pinMode(red3, OUTPUT);
  pinMode(yellow3, OUTPUT);
  pinMode(green3, OUTPUT);
  pinMode(red4, OUTPUT);
  pinMode(yellow4, OUTPUT);
  pinMode(green4, OUTPUT);
  
  // Turn off all LEDs initially
  digitalWrite(red1, LOW);
  digitalWrite(yellow1, LOW);
  digitalWrite(green1, LOW);
  digitalWrite(red2, LOW);
  digitalWrite(yellow2, LOW);
  digitalWrite(green2, LOW);
  digitalWrite(red3, LOW);
  digitalWrite(yellow3, LOW);
  digitalWrite(green3, LOW);
  digitalWrite(red4, LOW);
  digitalWrite(yellow4, LOW);
  digitalWrite(green4, LOW);
  
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
  
  // Send to Arduino
  Serial.println(message);
}

void updateSignal(int signalIndex, int red, int yellow, int green, int redPin, int yellowPin, int greenPin) {
  // Only update if state has changed
  if (prevSignalStates[signalIndex][0] != red || 
      prevSignalStates[signalIndex][1] != yellow || 
      prevSignalStates[signalIndex][2] != green) {
    
    // Update pins
    digitalWrite(redPin, red ? HIGH : LOW);
    digitalWrite(yellowPin, yellow ? HIGH : LOW);
    digitalWrite(greenPin, green ? HIGH : LOW);
    
    // Store new state
    prevSignalStates[signalIndex][0] = red;
    prevSignalStates[signalIndex][1] = yellow;
    prevSignalStates[signalIndex][2] = green;
    
    // Debug output
    Serial.print("Signal ");
    Serial.print(signalIndex + 1);
    Serial.print(" updated: R=");
    Serial.print(red);
    Serial.print(", Y=");
    Serial.print(yellow);
    Serial.print(", G=");
    Serial.println(green);
  }
} 