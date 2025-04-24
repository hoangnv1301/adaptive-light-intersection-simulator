#include <SoftwareSerial.h>

// Tạo đối tượng SoftwareSerial
SoftwareSerial espSerial(2, 3); // RX, TX

void setup() {
  // Khởi tạo Serial để debug
  Serial.begin(9600);
  
  // Khởi tạo SoftwareSerial để nhận dữ liệu từ ESP8266
  espSerial.begin(9600);
  
  // Đèn LED để chỉ báo
  pinMode(LED_BUILTIN, OUTPUT);
  
  Serial.println("Arduino ready to receive data from ESP8266");
}

void loop() {
  // Kiểm tra xem có dữ liệu từ ESP8266 không
  if (espSerial.available()) {
    // Đọc một byte
    char c = espSerial.read();
    
    // In ra Serial Monitor
    Serial.write(c);
    
    // Nhấp nháy LED để chỉ báo đã nhận dữ liệu
    digitalWrite(LED_BUILTIN, HIGH);
    delay(10);
    digitalWrite(LED_BUILTIN, LOW);
  }
} 