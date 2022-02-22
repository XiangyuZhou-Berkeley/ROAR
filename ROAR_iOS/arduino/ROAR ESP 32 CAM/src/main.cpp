#include <Arduino.h>

#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEServer.h>
#include <ESP32Servo.h>

#define SERVICE_UUID        "19B10010-E8F2-537E-4F6C-D104768A1214"
#define CONTROL_CHAR_UUID "19B10011-E8F2-537E-4F6C-D104768A1214"
#define VELOCITY_CHAR_UUID "19B10011-E8F2-537E-4F6C-D104768A1215"
#define PID_KValues_UUID "19B10011-E8F2-537E-4F6C-D104768A1216"



#define THROTTLE_PIN 14
#define STEERING_PIN 2
#define FLASH_LED_PIN 4
#define RED_LED_PIN 33

const char HANDSHAKE_START = '(';
const unsigned long redLEDToggleDuration = 500; // ms

volatile int32_t ws_throttle_read = 1500;
volatile int32_t ws_steering_read = 1500;
bool isForwardState = true; // car is currently in forward state.
unsigned int latest_throttle = 1500; // set to neutral by default
unsigned int latest_steering = 1500; // set to neutral by default

Servo throttleServo;
Servo steeringServo;


bool isFlashLightOn = false;
bool isRedLEDOn = false;
unsigned long lastREDLEDToggleTime = 0;  // will store last time LED was updated

bool deviceConnected = false;


void blinkRedLED();
void setupServo();
void setupBLE();
void ensureSmoothBackTransition();
void writeToSerial(unsigned int throttle, unsigned int steering);
void checkServo();
void writeToServo(unsigned int throttle, unsigned int steering);


class ControlCharCallback: public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic *pCharacteristic) {
      // let's not change this since it might break other people's workign code. 
      std::string value = pCharacteristic->getValue();
      if (value.length() > 0) {
        // turn buffer into a String object
        String argument = String(value.c_str());
        // terminate the string
        char buf[value.length()] = "\0";
        argument.toCharArray(buf, argument.length());

        // the input is going to be in the format of (1500, 1500)
        // so find the delimiter "," and then exclude the first "("
        // then extract the throttle and steering values
        char *token = strtok(buf, ",");
        if (token[0] == HANDSHAKE_START) {
            if (token != NULL) {
              unsigned int curr_throttle_read = atoi(token + 1);
              if (curr_throttle_read >= 1000 and curr_throttle_read <= 2000) {
                ws_throttle_read = curr_throttle_read;
              } 
            }
            token = strtok(NULL, ",");
            if (token != NULL) {
              unsigned int curr_steering_read = atoi(token);
              if (curr_steering_read >= 1000 and curr_steering_read <= 2000) {
                ws_steering_read = curr_steering_read;
              }
            }
        }
      }
    }
};


class ConfigCharCallback: public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic *pCharacteristic) {
      // We first get values from the buffer
      std::string value = pCharacteristic->getValue();
      if (value.length() == 12) {
        // the value is in little endian, 
        // Arduino is also in little endian
        // so 1.00 in hex should be 0x3f80000 in big endian
        // and we will have received 00 00 08 f3, so we simply map this to a float using the below struct
        float kp; float kd; float ki;

        union tmp {
            byte b[4];
            float fval;
        } t;
        t.b[0] = value[0]; t.b[1] = value[1]; t.b[2] = value[2]; t.b[3] = value[3]; kp = t.fval;
        t.b[0] = value[4]; t.b[1] = value[5]; t.b[2] = value[6]; t.b[3] = value[7]; kd = t.fval;
        t.b[0] = value[8]; t.b[1] = value[9]; t.b[2] = value[10]; t.b[3] = value[11]; ki = t.fval;
        // print it out for display
        Serial.print(kp); Serial.print(","); Serial.print(kd); Serial.print(","); Serial.print(ki); Serial.println();
      }
    }
};

class VelocityCharCallback: public BLECharacteristicCallbacks {
    void onRead(BLECharacteristic *pCharacteristic){
      float my_velocity_reading = 3.0; // TODO @ADAM, replace here with your actual reading
      pCharacteristic->setValue(my_velocity_reading);
    }
};


class MyServerCallbacks: public BLEServerCallbacks {
    void onConnect(BLEServer* pServer) {
      deviceConnected = true;
      Serial.println("Connected");
    };

    void onDisconnect(BLEServer* pServer) {
      deviceConnected = false;
      Serial.println("Disconnected");
      BLEDevice::startAdvertising();
    }
};

void setup() {
  Serial.begin(115200);
  pinMode(RED_LED_PIN, OUTPUT);
  pinMode(FLASH_LED_PIN, OUTPUT);


  setupServo();
  setupBLE();

}

void loop() {
  if (deviceConnected == false) {
    blinkRedLED();
  } else {
    digitalWrite(RED_LED_PIN, LOW);
  }

  ensureSmoothBackTransition();
  writeToServo(ws_throttle_read, ws_steering_read);
}


void setupBLE() {
    // setup ble name and server
    BLEDevice::init("IR Vehicle Control");
    BLEServer *pServer = BLEDevice::createServer();
    // initialize service
    BLEService *pService = pServer->createService(SERVICE_UUID);
    pServer->setCallbacks(new MyServerCallbacks());
    
    // add characteristics to our service
    BLECharacteristic *pCharacteristic = pService->createCharacteristic(
                                           CONTROL_CHAR_UUID,
                                           BLECharacteristic::PROPERTY_WRITE | 
                                           BLECharacteristic::PROPERTY_WRITE_NR);
    pCharacteristic->setCallbacks(new ControlCharCallback());

    BLECharacteristic *pidChar = pService->createCharacteristic(
                                           PID_KValues_UUID,
                                           BLECharacteristic::PROPERTY_WRITE |
                                           BLECharacteristic::PROPERTY_WRITE_NR);                     
    pidChar->setCallbacks(new ConfigCharCallback());

    BLECharacteristic *vCharacteristic = pService->createCharacteristic(
                                            VELOCITY_CHAR_UUID,
                                            BLECharacteristic::PROPERTY_READ);
    vCharacteristic->setCallbacks(new VelocityCharCallback());

    // start advertising
    pService->start();
    BLEDevice::startAdvertising();

    Serial.println("BLE Device Started");
}

void setupServo() {
  ESP32PWM::timerCount[0]=4;
  ESP32PWM::timerCount[1]=4;
  throttleServo.setPeriodHertz(50);
  throttleServo.attach(THROTTLE_PIN, 1000, 2000);
  steeringServo.setPeriodHertz(50);    // standard 50 hz servo
  steeringServo.attach(STEERING_PIN, 1000, 2000); // attaches the servo on pin (whatever you assign)
}

void writeToServo(unsigned int throttle, unsigned int steering) {
  checkServo(); // prevent servo from detaching
  latest_throttle = throttle;
  latest_steering = steering;

  throttleServo.writeMicroseconds(latest_throttle);
  steeringServo.writeMicroseconds(latest_steering);
  // writeToSerial(latest_throttle, latest_steering);
}

void writeToSerial(unsigned int throttle, unsigned int steering) {
  /*
   * Write to Serial
   */
  Serial.print(throttle);
  Serial.print(",");
  Serial.println(steering);
}
void checkServo() {
  if (throttleServo.attached() == false) {
    throttleServo.attach(THROTTLE_PIN);
  }
  if (steeringServo.attached() == false) {
    steeringServo.attach(STEERING_PIN);
  }
}

void ensureSmoothBackTransition() {
  if (isForwardState and latest_throttle < 1500) {
    writeToServo(1500, latest_steering);
    delay(100);
    writeToServo(1450, latest_steering);
    delay(100);
    writeToServo(1500,latest_steering);
    delay(100);
    isForwardState = false;
  } else if (latest_throttle >= 1500) {
    isForwardState = true;
  }
}


// Utility functions
void blinkFlashlight() {
  if (isFlashLightOn) {
    ledcWrite(FLASH_LED_PIN, 0);
    isFlashLightOn = false;
  } else {
    ledcWrite(FLASH_LED_PIN, 100);
    isFlashLightOn = true;
  }
}


void blinkRedLED() {
  unsigned long currentMillis = millis();
  if (isRedLEDOn && (currentMillis - lastREDLEDToggleTime >= redLEDToggleDuration)) {
    digitalWrite(RED_LED_PIN, HIGH);
    isRedLEDOn = false;
    lastREDLEDToggleTime = currentMillis;
  } else if (isRedLEDOn == false && (currentMillis -lastREDLEDToggleTime >= redLEDToggleDuration)) {
    digitalWrite(RED_LED_PIN, LOW);
    isRedLEDOn = true;
    lastREDLEDToggleTime = currentMillis;
  }
}
