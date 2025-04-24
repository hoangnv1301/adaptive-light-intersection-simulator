#include <SoftwareSerial.h>

// Tạo đối tượng SoftwareSerial để giao tiếp với ESP8266
SoftwareSerial espSerial(2, 3); // RX, TX

// Đèn LED để hiển thị trạng thái
const int ledPin = 13;
unsigned long lastReceiveTime = 0;
int receivedCount = 0;

void setup() {
  // Khởi tạo cả hai cổng Serial
  Serial.begin(9600);      // Serial Monitor
  espSerial.begin(9600);   // Giao tiếp với ESP8266
  
  // Cấu hình chân LED
  pinMode(ledPin, OUTPUT);
  digitalWrite(ledPin, LOW);
  
  Serial.println("Arduino Communication Test");
}

void loop() {
  // Kiểm tra xem có dữ liệu từ ESP8266 không
  if (espSerial.available()) {
    String data = espSerial.readStringUntil('\n');
    lastReceiveTime = millis();
    
    // Hiển thị dữ liệu nhận được trên Serial Monitor
    Serial.print("Received from ESP8266: ");
    Serial.println(data);
    
    // Phân tích dữ liệu
    if (data.startsWith("ESP8266_TEST:")) {
      // Trích xuất số từ thông điệp
      int value = data.substring(13).toInt();
      receivedCount++;
      
      // Nhấp nháy LED để hiển thị đã nhận dữ liệu
      digitalWrite(ledPin, HIGH);
      delay(100);
      digitalWrite(ledPin, LOW);
      
      // Gửi phản hồi lại ESP8266
      espSerial.print("ARDUINO_RECEIVED:");
      espSerial.println(value);
      
      // Hiển thị thông tin trên Serial Monitor
      Serial.print("Parsed value: ");
      Serial.println(value);
      Serial.print("Total messages received: ");
      Serial.println(receivedCount);
    }
  }
  
  // Kiểm tra xem có mất kết nối không
  if (millis() - lastReceiveTime > 5000 && lastReceiveTime > 0) {
    Serial.println("WARNING: No data received from ESP8266 for 5 seconds!");
    
    // Nhấp nháy LED nhanh để hiển thị lỗi kết nối
    for (int i = 0; i < 5; i++) {
      digitalWrite(ledPin, HIGH);
      delay(50);
      digitalWrite(ledPin, LOW);
      delay(50);
    }
    
    lastReceiveTime = millis(); // Cập nhật để không hiển thị cảnh báo liên tục
  }
} 