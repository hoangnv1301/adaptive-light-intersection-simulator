#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>
#include <ArduinoJson.h>

// WiFi credentials
const char* ssid = "Samsung Galaxy A31";
const char* password = "thuuyenbui";

// Server address
String serverAddress = "http://172.20.10.3:8000/esp32-data";

// Accident indicator LED
const int accidentLED = 2;  // Built-in LED

// Variables to store previous state
int prevSignalStates[4][3] = {0};
bool prevAccidentState = false;
int prevAccidentDirection = 0;

unsigned long previousMillis = 0;
const long interval = 1000;  // Update interval in milliseconds

void setup() {
  // Initialize serial communication
  Serial.begin(9600);  // Giao tiếp với Arduino
  delay(2000);
  
  // Configure LED
  pinMode(accidentLED, OUTPUT);
  digitalWrite(accidentLED, HIGH); // Tắt LED (active LOW)
  
  // Connect to WiFi
  WiFi.begin(ssid, password);
  
  int timeout = 0;
  while (WiFi.status() != WL_CONNECTED && timeout < 20) {
    delay(500);
    timeout++;
    digitalWrite(accidentLED, !digitalRead(accidentLED)); // Blink LED while connecting
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    // Nhấp nháy LED để chỉ báo kết nối thành công
    for (int i = 0; i < 5; i++) {
      digitalWrite(accidentLED, LOW);  // LED bật
      delay(200);
      digitalWrite(accidentLED, HIGH); // LED tắt
      delay(200);
    }
  }
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
  
  // Send to Arduino via Serial
  Serial.println(message);
} 