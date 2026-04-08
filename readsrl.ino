#include <Wire.h>

const int MPU_addr = 0x68;

void setup() {
Wire.begin();
Serial.begin(115200);

// Wake up MPU6050
Wire.beginTransmission(MPU_addr);
Wire.write(0x6B);
Wire.write(0);
Wire.endTransmission(true);
}

void loop() {
Wire.beginTransmission(MPU_addr);
Wire.write(0x3B); // start with ACCEL_XOUT_H
Wire.endTransmission(false);
Wire.requestFrom(MPU_addr, 6, true);

int16_t ax = Wire.read() << 8 | Wire.read();
int16_t ay = Wire.read() << 8 | Wire.read();
int16_t az = Wire.read() << 8 | Wire.read();

// تحويل لـ g (تقريبًا)
float Ax = ax / 16384.0;
float Ay = ay / 16384.0;
float Az = az / 16384.0;

unsigned long t = millis();

// format: time,ax,ay,az
Serial.print(t); Serial.print(",");
Serial.print(Ax); Serial.print(",");
Serial.print(Ay); Serial.print(",");
Serial.println(Az);

delay(50); // ~20Hz
}