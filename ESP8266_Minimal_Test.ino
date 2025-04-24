void setup() {
  Serial.begin(9600);
  pinMode(LED_BUILTIN, OUTPUT);
}

void loop() {
  digitalWrite(LED_BUILTIN, HIGH);
  Serial.println("TEST:1,2,3");
  delay(500);
  digitalWrite(LED_BUILTIN, LOW);
  delay(500);
} 