void setup() {
  // Khởi tạo Serial để debug
  Serial.begin(9600);
  
  // Khởi tạo Serial1 để nhận dữ liệu từ ESP8266
  Serial1.begin(9600);
  
  Serial.println("Arduino ready to receive data from ESP8266");
}

void loop() {
  // Kiểm tra xem có dữ liệu từ ESP8266 không
  if (Serial1.available()) {
    // Đọc một byte
    char c = Serial1.read();
    
    // In ra Serial Monitor
    Serial.write(c);
  }
} 