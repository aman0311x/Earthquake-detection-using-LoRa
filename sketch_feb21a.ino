#include <SPI.h>
#include <LoRa.h>
#include <Wire.h>
#include <math.h>

#define ss 5
#define rst 14
#define dio0 2


#define BUZZER_PIN 26  
#define PWM_CHANNEL 0  
#define MPU_ADDR 0x68

unsigned long buzzerTimer = 0;
bool isBuzzerOn = false;
unsigned long lastSendTime = 0;
unsigned long lastPrintTime = 0;

void readMPU(float &ax, float &ay, float &az) {
    Wire.beginTransmission(MPU_ADDR);
    Wire.write(0x3B); 
    Wire.endTransmission(false);
    Wire.requestFrom((uint16_t)MPU_ADDR, (uint8_t)6, true);
    
    int16_t x = (Wire.read() << 8 | Wire.read());
    int16_t y = (Wire.read() << 8 | Wire.read());
    int16_t z = (Wire.read() << 8 | Wire.read());
    
    ax = (float)x; 
    ay = (float)y; 
    az = (float)z;
}

void setup() {
    Serial.begin(115200);
    delay(1000);
    Serial.println("\n--- LoRa Two-Way Earthquake Node Started ---");

    ledcSetup(PWM_CHANNEL, 2000, 8); 
    ledcAttachPin(BUZZER_PIN, PWM_CHANNEL);
    ledcWrite(PWM_CHANNEL, 0); 

    
    Wire.begin(21, 22);
    Wire.beginTransmission(MPU_ADDR);
    Wire.write(0x6B);  
    Wire.write(0);     
    Wire.endTransmission(true);

    
    LoRa.setPins(ss, rst, dio0);
    if (!LoRa.begin(433E6)) { 
        Serial.println("Starting LoRa failed! Check wiring.");
        while (1);
    }
    
    
    LoRa.receive();
    Serial.println("System Ready. Monitoring Sensor and LoRa Network...");
}

void loop() {
    if (isBuzzerOn && (millis() - buzzerTimer > 1000)) {
        ledcWrite(PWM_CHANNEL, 0); 
        isBuzzerOn = false;
        Serial.println("Buzzer Timeout: OFF");
    }

    
    int packetSize = LoRa.parsePacket();
    if (packetSize) {
        String receivedData = "";
        while (LoRa.available()) {
            receivedData += (char)LoRa.read();
        }
        
        if (receivedData == "ALERT") {
            Serial.println("\n[ >>> RECEIVED ALERT FROM REMOTE NODE! <<< ]");
            Serial.println("-> Sounding Alarm locally!");
            
            ledcWrite(PWM_CHANNEL, 128); 
            isBuzzerOn = true;
            buzzerTimer = millis();      
        }
    }

    
    float ax, ay, az;
    readMPU(ax, ay, az);
    float magnitude = sqrt(ax*ax + ay*ay + az*az);

    
    if (millis() - lastPrintTime > 200) {
        Serial.print("Vibration Level: ");
        Serial.println(magnitude);
        lastPrintTime = millis();
    }

    
    if (magnitude > 25000 && (millis() - lastSendTime > 4000)) {
        Serial.println("\n[ !!! LOCAL EARTHQUAKE DETECTED !!! ]");
        Serial.println("-> Sounding Alarm & Broadcasting to other node...");
        
        
        ledcWrite(PWM_CHANNEL, 128);
        isBuzzerOn = true;
        buzzerTimer = millis();

        
        LoRa.beginPacket();
        LoRa.print("ALERT");
        LoRa.endPacket();
        
        
        LoRa.receive(); 
        
        lastSendTime = millis();
    }
    
    delay(10); 
}