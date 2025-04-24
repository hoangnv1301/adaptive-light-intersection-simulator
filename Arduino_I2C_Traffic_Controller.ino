#include <Wire.h>

// Arduino I2C address
#define ARDUINO_ADDRESS 0x08

// Pins for traffic lights
int red1 = 2, yellow1 = 3, green1 = 4;
int red2 = 5, yellow2 = 6, green2 = 7;
int red3 = 8, yellow3 = 9, green3 = 10;
int red4 = 11, yellow4 = 12, green4 = 13;

// Accident indicator
int accidentLED = A0;

// Buffer to store received data
byte signalStates[4][3] = {0};
bool accidentState = false;

void setup() {
  // Initialize serial communication
  Serial.begin(9600);
  Serial.println("Arduino Traffic Light Controller Starting");
  
  // Initialize I2C
  Wire.begin(ARDUINO_ADDRESS);
  Wire.onReceive(receiveEvent);
  
  // Configure all LED pins as OUTPUT
  pinMode(red1, OUTPUT);
  pinMode(yellow1, OUTPUT);
  pinMode(green1, OUTPUT);
  pinMode(red2, OUTPUT);
  pinMode(yellow2, OUTPUT);
  pinMode(green2, OUTPUT);
  pinMode(red3, OUTPUT);
  pinMode(yellow3, OUTPUT);
  pinMode(green3, OUTPUT);
  pinMode(red4, OUTPUT);
  pinMode(yellow4, OUTPUT);
  pinMode(green4, OUTPUT);
  pinMode(accidentLED, OUTPUT);
  
  // Turn off all LEDs initially
  digitalWrite(red1, LOW);
  digitalWrite(yellow1, LOW);
  digitalWrite(green1, LOW);
  digitalWrite(red2, LOW);
  digitalWrite(yellow2, LOW);
  digitalWrite(green2, LOW);
  digitalWrite(red3, LOW);
  digitalWrite(yellow3, LOW);
  digitalWrite(green3, LOW);
  digitalWrite(red4, LOW);
  digitalWrite(yellow4, LOW);
  digitalWrite(green4, LOW);
  digitalWrite(accidentLED, LOW);
  
  Serial.println("All LEDs initialized");
}

void loop() {
  // Nothing to do here, everything is handled in the receiveEvent callback
  delay(100);
  
  // Blink accident LED if there's an accident
  if (accidentState) {
    digitalWrite(accidentLED, (millis() / 500) % 2);  // Blink every 500ms
  } else {
    digitalWrite(accidentLED, LOW); // LED tắt khi không có tai nạn
  }
}

// Function called when data is received from ESP8266
void receiveEvent(int howMany) {
  if (howMany >= 13) {  // 4 signals x 3 states + accident state
    // Read signal states (12 bytes)
    for (int i = 0; i < 4; i++) {
      for (int j = 0; j < 3; j++) {
        signalStates[i][j] = Wire.read();
      }
    }
    
    // Read accident state (1 byte)
    accidentState = Wire.read() == 1;
    
    // Update traffic lights
    updateTrafficLights();
    
    // Debug output
    Serial.println("Received traffic data from ESP8266");
    Serial.println("Traffic light states:");
    for (int i = 0; i < 4; i++) {
      Serial.print("Signal ");
      Serial.print(i+1);
      Serial.print(": R=");
      Serial.print(signalStates[i][0]);
      Serial.print(", Y=");
      Serial.print(signalStates[i][1]);
      Serial.print(", G=");
      Serial.println(signalStates[i][2]);
    }
    
    Serial.print("Accident: ");
    Serial.println(accidentState ? "YES" : "NO");
  }
  
  // Clear any remaining bytes
  while (Wire.available()) {
    Wire.read();
  }
}

// Update traffic lights based on received data
void updateTrafficLights() {
  // Signal 1
  digitalWrite(red1, signalStates[0][0] ? HIGH : LOW);
  digitalWrite(yellow1, signalStates[0][1] ? HIGH : LOW);
  digitalWrite(green1, signalStates[0][2] ? HIGH : LOW);
  
  // Signal 2
  digitalWrite(red2, signalStates[1][0] ? HIGH : LOW);
  digitalWrite(yellow2, signalStates[1][1] ? HIGH : LOW);
  digitalWrite(green2, signalStates[1][2] ? HIGH : LOW);
  
  // Signal 3
  digitalWrite(red3, signalStates[2][0] ? HIGH : LOW);
  digitalWrite(yellow3, signalStates[2][1] ? HIGH : LOW);
  digitalWrite(green3, signalStates[2][2] ? HIGH : LOW);
  
  // Signal 4
  digitalWrite(red4, signalStates[3][0] ? HIGH : LOW);
  digitalWrite(yellow4, signalStates[3][1] ? HIGH : LOW);
  digitalWrite(green4, signalStates[3][2] ? HIGH : LOW);
} 