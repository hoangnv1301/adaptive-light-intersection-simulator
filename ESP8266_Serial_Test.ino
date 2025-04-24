void setup() {
  // Khởi tạo Serial với tốc độ 9600 baud
  Serial.begin(9600);
  delay(3000); // Đợi Serial khởi động
  
  // Gửi thông điệp ban đầu
  Serial.println();
  Serial.println("ESP8266 Serial Test");
  Serial.println("If you can see this, Serial is working!");
}

void loop() {
  // Gửi thông điệp mỗi 2 giây
  Serial.println("Hello from ESP8266!");
  delay(2000);
} 