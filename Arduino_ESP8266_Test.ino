#include <SoftwareSerial.h>

SoftwareSerial espSerial(2, 3); // RX, TX

void setup() {
  Serial.begin(9600);      // Debug Serial
  espSerial.begin(9600);   // ESP8266 communication
  
  Serial.println("Arduino ready to receive data from ESP8266");
}

void loop() {
  if (espSerial.available()) {
    String data = espSerial.readStringUntil('\n');
    Serial.println("Received from ESP8266: " + data);
  }
} 