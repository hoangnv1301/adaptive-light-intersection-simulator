#include <Wire.h>

#define ARDUINO_ADDRESS 0x08
#define LED_PIN 13

void setup() {
  Wire.begin(ARDUINO_ADDRESS); // Khởi tạo I2C với Arduino làm slave
  Wire.onReceive(receiveEvent); // Đăng ký hàm callback khi nhận dữ liệu
  
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  
  Serial.begin(9600);
  Serial.println("Arduino I2C Slave Test");
}

void loop() {
  // Không cần làm gì trong loop
  delay(100);
}

// Hàm được gọi khi nhận dữ liệu qua I2C
void receiveEvent(int howMany) {
  while (Wire.available()) {
    byte value = Wire.read();
    digitalWrite(LED_PIN, value ? HIGH : LOW);
    Serial.print("Received from ESP8266: ");
    Serial.println(value);
  }
} 