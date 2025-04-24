#include <Wire.h>

#define ARDUINO_ADDRESS 0x08

void setup() {
  Wire.begin(); // Khởi tạo I2C với ESP8266 làm master
  Serial.begin(9600);
  Serial.println("ESP8266 I2C Master Test");
}

void loop() {
  // Gửi dữ liệu qua I2C
  Wire.beginTransmission(ARDUINO_ADDRESS);
  Wire.write(1); // Gửi số 1 để bật LED
  Wire.endTransmission();
  Serial.println("Sent 1 to Arduino");
  delay(1000);
  
  Wire.beginTransmission(ARDUINO_ADDRESS);
  Wire.write(0); // Gửi số 0 để tắt LED
  Wire.endTransmission();
  Serial.println("Sent 0 to Arduino");
  delay(1000);
} 