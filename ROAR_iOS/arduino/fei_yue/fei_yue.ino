int motorPinA = 2; // should be whatever you need them to be
int motorPinB = 3;

int potPin = A0;

int dbWindow = 32; // deadband of 32 units on either side of "setPoint"

void setup() {
  Serial.begin(9600);

  pinMode(motorPinA, OUTPUT);
  pinMode(motorPinB, OUTPUT);
}

void loop() {

  Serial.print("Start: ");
  Serial.println(analogRead(potPin));

  digitalWrite(motorPinA, LOW);
  digitalWrite(motorPinB, HIGH);
  Serial.print("A Low, B High: ");
  Serial.println(analogRead(potPin));
  delay(100);

  


  digitalWrite(motorPinA, HIGH);
  digitalWrite(motorPinB, LOW);
  Serial.print("A High B Low: ");
  Serial.println(analogRead(potPin));
  delay(100);

  Serial.println("");


}
