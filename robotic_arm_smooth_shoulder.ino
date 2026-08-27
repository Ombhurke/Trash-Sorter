#include <Servo.h>

//==================================================
// Servo Position Variables
//==================================================

int shoulderPos = 90;
int elbowPos = 90;
int wrist1Pos = 90;
int wrist2Pos = 90;
int handPos = 90;
int basePos = 90;


//==================================================
// Servo Objects
//==================================================

Servo shoulder;
Servo elbow;
Servo wrist1;
Servo wrist2;
Servo hand;
Servo base;


//==================================================
// SETUP
//==================================================

void setup()
{
  Serial.begin(19200);

  pinMode(13, OUTPUT);

  // Servo Connections

  base.attach(4);
  shoulder.attach(11);
  elbow.attach(12);
  wrist2.attach(6);
  wrist1.attach(10);
  hand.attach(5);

  Serial.println("Robotic Arm Ready");

  // Move to Home Position
  homeState();
}


//==================================================
// LOOP
//==================================================

void loop()
{
  // Wait for command from Serial Monitor

  if (Serial.available())
  {
    char command = Serial.read();

    // Plastic
    if (command == 'P' || command == 'p')
    {
      Serial.println("Plastic Selected");

      pickUpObject();

      throwPlastic();

      delay(500);

      homeState();

      Serial.println("Done");
    }

    // Paper
    else if (command == 'A' || command == 'a')
    {
      Serial.println("Paper Selected");

      pickUpObject();

      throwPaper();

      delay(500);

      homeState();

      Serial.println("Done");
    }

    // Cardboard
    else if (command == 'C' || command == 'c')
    {
      Serial.println("Cardboard Selected");

      pickUpObject();

      throwCardboard();

      delay(500);

      homeState();

      Serial.println("Done");
    }

    // Glass
    else if (command == 'G' || command == 'g')
    {
      Serial.println("Glass Selected");

      pickUpObject();

      throwGlass();

      delay(500);

      homeState();

      Serial.println("Done");
    }

    // Metal
    else if (command == 'M' || command == 'm')
    {
      Serial.println("Metal Selected");

      pickUpObject();

      throwMetal();

      delay(500);

      homeState();

      Serial.println("Done");
    }

    // Home / Reset Position
    else if (command == 'H' || command == 'h' || command == 'R' || command == 'r')
    {
      Serial.println("Home Selected");

      homeState();

      delay(200);

      Serial.println("Done");
    }
  }
}


//==================================================
// SLOW SERVO MOVEMENT FUNCTION (generic, used for non-shoulder joints)
//==================================================

void moveServoSlow(Servo &servo, int currentPos, int targetPos, int speedDelay)
{
  if (currentPos < targetPos)
  {
    for (int i = currentPos; i <= targetPos; i++)
    {
      servo.write(i);
      delay(speedDelay);
    }
  }
  else
  {
    for (int i = currentPos; i >= targetPos; i--)
    {
      servo.write(i);
      delay(speedDelay);
    }
  }
}


//==================================================
// EASED SHOULDER MOVEMENT FUNCTION
// Starts slow, speeds up in the middle, slows down again
// near the target -> feels gentle/"easy" instead of a sudden snap.
//==================================================

void moveShoulderEased(int currentPos, int targetPos, int baseDelay)
{
  int totalSteps = abs(targetPos - currentPos);
  if (totalSteps == 0) return;

  int direction = (targetPos > currentPos) ? 1 : -1;

  for (int step = 0; step <= totalSteps; step++)
  {
    int pos = currentPos + (direction * step);
    shoulder.write(pos);

    // Distance from nearest end of the motion (0 = at an endpoint)
    int distFromStart = step;
    int distFromEnd = totalSteps - step;
    int distFromEdge = min(distFromStart, distFromEnd);

    // Ease window: how many steps at each end get the slow treatment
    int easeWindow = min(15, totalSteps / 3);

    int stepDelay;
    if (easeWindow > 0 && distFromEdge < easeWindow)
    {
      // Slower near start/end: extra delay tapers off linearly
      int extra = map(distFromEdge, 0, easeWindow, baseDelay * 2, 0);
      stepDelay = baseDelay + extra;
    }
    else
    {
      stepDelay = baseDelay;
    }

    delay(stepDelay);
  }

  shoulderPos = targetPos;
}


//==================================================
// PICK UP OBJECT
//==================================================

void pickUpObject()
{
  // Rotate to Pick Position


  // Open Gripper

  hand.write(160);
  handPos = 160;
  delay(500);

  // Move Down

  wrist2.write(110);
  wrist2Pos = 110;
  delay(500);

  elbow.write(140);
  elbowPos = 140;
  delay(500);

  // Shoulder moves slowly + gently (eased)

  moveShoulderEased(shoulderPos, 32, 12);

  delay(500);

  // Close Gripper

  hand.write(15);
  handPos = 15;
  delay(200);

    hand.write(15);
  handPos = 15;
  delay(1000);
}


//==================================================
// THROW PAPER (RIGHT)
//==================================================

void throwPlastic()
{
  // Shoulder moves slowly + gently upwards

  moveShoulderEased(shoulderPos, 100, 15);


  elbow.write(130);
  elbowPos = 130;

  wrist2.write(110);
  wrist2Pos = 110;

  // RIGHT BIN

  base.write(110);   // Move to the right
  basePos = 110;
  delay(1900);       // Move for 300 milliseconds
  base.write(90);   // STOP the motor

  delay(400);

  // Release Object
  hand.write(160);
  handPos = 160;
  delay(500);

  base.write(75);   
  basePos = 75;
  delay(1200);      
  base.write(90); 
}



//==================================================
// THROW paper (RIGHT)
//==================================================

void throwPaper()
{
    elbow.write(140);
  elbowPos = 140;
  delay(500);
  // Shoulder moves slowly + gently upwards

  moveShoulderEased(shoulderPos, 95, 15);

  elbow.write(130);
  elbowPos = 130;
  delay(500);

  wrist2.write(110);
  wrist2Pos = 110;
  delay(500);

  // RIGHT BIN

  base.write(120);   // Move to the right
  basePos = 120;
  delay(9800);       // Move for 300 milliseconds
  base.write(90);   // STOP the motor

  delay(400);

  // Release Object
  hand.write(160);
  handPos = 160;
  delay(500);

  base.write(70); 
  basePos = 70;
  delay(3500);     
  base.write(90); 
}



//==================================================
// THROW GLASS (LEFT) -- calibrate values below
//==================================================

void throwGlass()
{
  // Shoulder moves slowly + gently upwards

  moveShoulderEased(shoulderPos, 100, 15);

  delay(500);

  elbow.write(130);
  elbowPos = 130;
  delay(500);

  wrist2.write(140);
  wrist2Pos = 140;
  delay(500);

  // LEFT BIN

  base.write(70);  
  basePos = 70;
  delay(2100);      
  base.write(90);  

  delay(400);
  
  // Release Object
  hand.write(160);
  handPos = 160;
  delay(500);

  base.write(120);  
  basePos = 120;
  delay(1500);      
  base.write(90); 
}




//==================================================
// THROW CARDBOARD (LEFT) -- calibrate values below
//==================================================

void throwMetal()
{
  // Shoulder moves slowly + gently upwards
    hand.write(15);
  handPos = 15;

  moveShoulderEased(shoulderPos, 95, 15);

  delay(500);

  elbow.write(130);
  elbowPos = 130;
  delay(1000);

  wrist2.write(140);
  wrist2Pos = 140;
  delay(500);

  // LEFT BIN

  base.write(75);   
  basePos = 75;
  delay(1500);     
  base.write(90);  

  delay(400);

  // Release Object
  hand.write(160);
  handPos = 160;
  delay(500);

  base.write(110);   
  basePos = 110;
  delay(1600);       
  base.write(90); 
}




//==================================================
// THROW METAL (BACK) -- calibrate values below
//==================================================

void throwCardboard()
{
  // Shoulder moves slowly + gently upwards
  moveShoulderEased(shoulderPos, 105, 15);

  delay(500);

  elbow.write(130);
  elbowPos = 130;
  delay(1000);
  
  // RIGHT BIN
  base.write(125);   // Move to the right
  basePos = 125;
  delay(2350);       // Move for 300 milliseconds
  base.write(90);   // STOP the motor

  delay(400);

  moveShoulderEased(shoulderPos, 85, 15);

  delay(300);

  elbow.write(110);
  elbowPos = 110;
  delay(500);

  // Release Object

  hand.write(160);
  handPos = 160;
  delay(500);

  base.write(60);   
  basePos = 60;
  delay(1600);      
  base.write(90); 
}


//==================================================
// HOME POSITION
//==================================================

void homeState()
{


  wrist2.write(160);
  wrist2Pos = 160;
  delay(500);

  elbow.write(160);
  elbowPos = 160;
  delay(500);

  // Shoulder moves slowly + gently back home

  moveShoulderEased(shoulderPos, 85, 15);

  delay(500);

  // Half Open Waiting Position

  hand.write(120);
  handPos = 120;
  delay(500);
}
