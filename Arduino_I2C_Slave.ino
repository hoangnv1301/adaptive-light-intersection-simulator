#include <Wire.h>

// Địa chỉ I2C của Arduino
#define ARDUINO_ADDRESS 0x08

// Buffer để lưu dữ liệu nhận được
char buffer[32];
int bufferIndex = 0;

void setup() {
  Wire.begin(ARDUINO_ADDRESS); // Khởi tạo I2C với Arduino làm slave
  Wire.onReceive(receiveEvent); // Đăng ký hàm callback khi nhận dữ liệu
  
  Serial.begin(9600);
  Serial.println("Arduino I2C Slave ready");
}

void loop() {
  // Không cần làm gì trong loop
  delay(100);
}

// Hàm được gọi khi nhận dữ liệu qua I2C
void receiveEvent(int howMany) {
  bufferIndex = 0;
  
  while (Wire.available()) {
    char c = Wire.read();
    buffer[bufferIndex++] = c;
    
    // Đảm bảo không vượt quá kích thước buffer
    if (bufferIndex >= 31) {
      break;
    }
  }
  
  // Thêm ký tự kết thúc chuỗi
  buffer[bufferIndex] = '\0';
  
  // In dữ liệu nhận được
  Serial.print("Received from ESP8266: ");
  Serial.println(buffer);
} 