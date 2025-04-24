#include <SoftwareSerial.h>

// Software serial for ESP8266 communication
SoftwareSerial espSerial(0, 1); // RX, TX

// Pins for traffic lights
int red1 = 2, yellow1 = 3, green1 = 4;
int red2 = 5, yellow2 = 6, green2 = 7;
int red3 = 8, yellow3 = 9, green3 = 10;
int red4 = 11, yellow4 = 12, green4 = 13;

// Accident indicator
int accidentLED = 13;

void setup() {
  // Initialize serial communications
  Serial.begin(9600);
  espSerial.begin(9600);
  
  // Configure all LED pins as OUTPUT
  int lights[] = {red1, yellow1, green1, red2, yellow2, green2, 
                  red3, yellow3, green3, red4, yellow4, green4, accidentLED};
  for (int i = 0; i < 13; i++) {
    pinMode(lights[i], OUTPUT);
    digitalWrite(lights[i], LOW); // Initially all LEDs are off
  }
  
  Serial.println("Traffic Light Controller Ready");
}

void loop() {
  // Check if data is available from ESP8266
  if (espSerial.available()) {
    String data = espSerial.readStringUntil('\n');
    Serial.println("Received: " + data);
    
    // Parse the data
    // Format: "S1:R,Y,G;S2:R,Y,G;S3:R,Y,G;S4:R,Y,G;A:0/1;D:value"
    // Example: "S1:1,0,0;S2:0,0,1;S3:1,0,0;S4:0,0,1;A:1;D:2"
    
    // Extract each section
    String s1Data = getSection(data, "S1:");
    String s2Data = getSection(data, "S2:");
    String s3Data = getSection(data, "S3:");
    String s4Data = getSection(data, "S4:");
    String accidentData = getSection(data, "A:");
    
    // Signal 1
    int s1r = s1Data.charAt(0) - '0';
    int s1y = s1Data.charAt(2) - '0';
    int s1g = s1Data.charAt(4) - '0';
    
    // Signal 2
    int s2r = s2Data.charAt(0) - '0';
    int s2y = s2Data.charAt(2) - '0';
    int s2g = s2Data.charAt(4) - '0';
    
    // Signal 3
    int s3r = s3Data.charAt(0) - '0';
    int s3y = s3Data.charAt(2) - '0';
    int s3g = s3Data.charAt(4) - '0';
    
    // Signal 4
    int s4r = s4Data.charAt(0) - '0';
    int s4y = s4Data.charAt(2) - '0';
    int s4g = s4Data.charAt(4) - '0';
    
    // Accident status
    int accident = accidentData.charAt(0) - '0';
    
    // Update traffic lights
    digitalWrite(red1, s1r);
    digitalWrite(yellow1, s1y);
    digitalWrite(green1, s1g);
    
    digitalWrite(red2, s2r);
    digitalWrite(yellow2, s2y);
    digitalWrite(green2, s2g);
    
    digitalWrite(red3, s3r);
    digitalWrite(yellow3, s3y);
    digitalWrite(green3, s3g);
    
    digitalWrite(red4, s4r);
    digitalWrite(yellow4, s4y);
    digitalWrite(green4, s4g);
    
    // Update accident LED
    digitalWrite(accidentLED, accident);
    
    // Debug output
    Serial.println("S1: " + String(s1r) + "," + String(s1y) + "," + String(s1g));
    Serial.println("S2: " + String(s2r) + "," + String(s2y) + "," + String(s2g));
    Serial.println("S3: " + String(s3r) + "," + String(s3y) + "," + String(s3g));
    Serial.println("S4: " + String(s4r) + "," + String(s4y) + "," + String(s4g));
    Serial.println("Accident: " + String(accident));
  }
}

// Helper function to extract a section from the data string
String getSection(String data, String sectionKey) {
  int startIndex = data.indexOf(sectionKey) + sectionKey.length();
  int endIndex = data.indexOf(";", startIndex);
  
  if (endIndex == -1) {
    // If no semicolon is found (might be the last section)
    return data.substring(startIndex);
  }
  
  return data.substring(startIndex, endIndex);
} 