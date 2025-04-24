#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>

// WiFi credentials
const char* ssid = "Samsung Galaxy A31";
const char* password = "thuuyenbui";

// Tạo đối tượng WebServer
ESP8266WebServer server(80);

// Biến lưu trạng thái đèn giao thông
String trafficData = "S1:1,0,0;S2:0,1,0;S3:0,0,1;S4:1,0,0;A:0;D:0";

void setup() {
  Serial.begin(9600);
  
  // Kết nối WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("");
  Serial.print("Connected to WiFi. IP address: ");
  Serial.println(WiFi.localIP());
  
  // Định nghĩa các endpoint
  server.on("/data", HTTP_GET, handleGetData);
  
  // Bắt đầu máy chủ
  server.begin();
  Serial.println("HTTP server started");
}

void loop() {
  server.handleClient();
  
  // Cập nhật dữ liệu từ máy chủ Python
  // (code cập nhật dữ liệu từ máy chủ Python)
  
  // In dữ liệu ra Serial để Arduino đọc
  Serial.println(trafficData);
  delay(1000);
}

void handleGetData() {
  server.send(200, "text/plain", trafficData);
}

// Add this function to the ESP8266 code to send data to Arduino
void sendToArduino() {
  // Format: "S1:R,Y,G;S2:R,Y,G;S3:R,Y,G;S4:R,Y,G;A:0/1"
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
  
  // Send to Arduino
  Serial.println(message);
}

// Call this function after updating the traffic lights in the updateTrafficLights() function 