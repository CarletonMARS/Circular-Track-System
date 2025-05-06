int Index;

void setup()
{
  Serial.begin(115200);
pinMode(4, OUTPUT); //Enable
pinMode(2, OUTPUT); //Step
pinMode(3, OUTPUT); //Direction

digitalWrite(4,LOW);
}

void loop()
{
  // put your main code here, to run repeatedly:
  if (Serial.available() > 0) {
    // read the incoming byte:
    // say what you got:
    String DiffAngleSTR = Serial.readString();
    int NumberofSteps = DiffAngleSTR.toInt();
    if(NumberofSteps > 0 ){
      //Serial.println("Moving Positive");
      PositiveDirection(NumberofSteps);
      Serial.println(NumberofSteps);
    }
    if(NumberofSteps < 0 ){
     //Serial.println("Moving Negative");
      NegativeDirection(abs(NumberofSteps));
     
     Serial.println(NumberofSteps);
    }
  }
}

void PositiveDirection(int NumSteps) {
digitalWrite(3,LOW);

for(Index = 0; Index < NumSteps; Index++)
{
  digitalWrite(2,HIGH);
  delayMicroseconds(1000);
  digitalWrite(2,LOW);
  delayMicroseconds(1000);
}

}

void NegativeDirection(int NumSteps) {
digitalWrite(3,HIGH);

for(Index = 0; Index < NumSteps; Index++)
{
  digitalWrite(2,HIGH);
  delayMicroseconds(1000);
  digitalWrite(2,LOW);
  delayMicroseconds(1000);
}
}
