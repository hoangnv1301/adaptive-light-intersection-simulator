#include <ESP8266WiFi.h>

// WiFi credentials - THAY ĐỔI THÔNG TIN THỰC TẾ Ở ĐÂY
const char* ssid = "TenWiFiThucTe";
const char* password = "MatKhauThucTe";

void setup() {
  // Khởi tạo Serial
  Serial.begin(9600);
  delay(1000);
  
  Serial.println("\nESP8266 WiFi Test");
  Serial.print("Connecting to: ");
  Serial.println(ssid);
  
  // Kết nối WiFi
  WiFi.begin(ssid, password);
  
  // Đợi kết nối với timeout
  int timeout = 0;
  while (WiFi.status() != WL_CONNECTED && timeout < 20) {
    delay(500);
    Serial.print(".");
    timeout++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("");
    Serial.println("WiFi connected");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
    
    // Nhấp nháy LED để chỉ báo kết nối thành công
    pinMode(LED_BUILTIN, OUTPUT);
    for (int i = 0; i < 5; i++) {
      digitalWrite(LED_BUILTIN, LOW);  // LED bật
      delay(200);
      digitalWrite(LED_BUILTIN, HIGH); // LED tắt
      delay(200);
    }
  } else {
    Serial.println("");
    Serial.println("Failed to connect to WiFi");
    Serial.println("Please check SSID and password");
  }
}

void loop() {
  // Hiển thị trạng thái WiFi mỗi 5 giây
  Serial.print("WiFi status: ");
  
  switch (WiFi.status()) {
    case WL_CONNECTED:
      Serial.println("Connected");
      break;
    case WL_NO_SSID_AVAIL:
      Serial.println("SSID not available");
      break;
    case WL_CONNECT_FAILED:
      Serial.println("Connection failed");
      break;
    case WL_IDLE_STATUS:
      Serial.println("Idle");
      break;
    case WL_DISCONNECTED:
      Serial.println("Disconnected");
      break;
    default:
      Serial.println("Unknown");
      break;
  }
  
  delay(5000);
} 