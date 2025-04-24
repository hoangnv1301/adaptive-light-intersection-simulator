#include <ESP8266WiFi.h>

// Biến để theo dõi thời gian
unsigned long previousMillis = 0;
const long interval = 1000;  // Gửi dữ liệu mỗi 1 giây
int counter = 0;

void setup() {
  // Khởi tạo giao tiếp Serial với tốc độ 9600 baud
  Serial.begin(9600);
  Serial.println();
  Serial.println("ESP8266 Communication Test");
  
  // Đèn LED tích hợp để hiển thị trạng thái
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH); // Tắt LED (LED_BUILTIN thường là active LOW)
  
  // Chờ 2 giây để Arduino khởi động
  delay(2000);
}

void loop() {
  unsigned long currentMillis = millis();
  
  // Kiểm tra xem đã đến lúc gửi dữ liệu chưa
  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis;
    
    // Tạo thông điệp kiểm tra
    String message = "ESP8266_TEST:";
    message += counter;
    
    // Gửi thông điệp qua Serial
    Serial.println(message);
    
    // Nhấp nháy LED để hiển thị đã gửi dữ liệu
    digitalWrite(LED_BUILTIN, LOW);  // Bật LED
    delay(100);
    digitalWrite(LED_BUILTIN, HIGH); // Tắt LED
    
    // Tăng bộ đếm
    counter++;
  }
  
  // Kiểm tra xem có dữ liệu từ Arduino không
  if (Serial.available()) {
    String response = Serial.readStringUntil('\n');
    
    // Nếu nhận được phản hồi từ Arduino, nhấp nháy LED nhanh
    if (response.startsWith("ARDUINO_RECEIVED:")) {
      for (int i = 0; i < 3; i++) {
        digitalWrite(LED_BUILTIN, LOW);  // Bật LED
        delay(50);
        digitalWrite(LED_BUILTIN, HIGH); // Tắt LED
        delay(50);
      }
    }
  }
} 