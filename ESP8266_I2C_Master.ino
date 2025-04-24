#include <Wire.h>

// Địa chỉ I2C của Arduino
#define ARDUINO_ADDRESS 0x08

void setup() {
  Wire.begin(); // Khởi tạo I2C với ESP8266 làm master
  Serial.begin(9600);
}

void loop() {
  // Gửi dữ liệu qua I2C
  Wire.beginTransmission(ARDUINO_ADDRESS);
  Wire.write("TEST:1,2,3");
  Wire.endTransmission();
  
  Serial.println("Sent data to Arduino via I2C");
  delay(1000);
} 