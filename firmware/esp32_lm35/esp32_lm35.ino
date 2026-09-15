#include <Arduino.h>
const int LM35_PIN = 34;
unsigned long seq = 0;
void setup(){ Serial.begin(115200); analogReadResolution(12); }
void loop(){
  int raw=analogRead(LM35_PIN); int mv=analogReadMilliVolts(LM35_PIN);
  Serial.printf("{\"version\":1,\"seq\":%lu,\"t_ms\":%lu,\"adc_raw\":%d,\"voltage_mv\":%d,\"status\":\"ok\"}\n",seq++,millis(),raw,mv);
  delay(500);
}
