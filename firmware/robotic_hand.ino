#include <Servo.h>

//==============================================================================
// IIOT ROBOTIC ARM 6-DOF TRASH SORTER FIRMWARE
// Supports:
// 1. Single-character waste category throw commands:
//    'P' -> Plastic Bin (Right)
//    'A' -> Paper Bin (Far Right)
//    'C' -> Cardboard Bin (Back)
//    'G' -> Glass Bin (Left)
//    'M' -> Metal Bin (Far Left)
//    'H' -> Home State
//    'E' -> Emergency Stop / Release
// 2. Streamed continuous joint angles: "S,q1,q2,q3,q4,q5,q6\n"
// 3. Handshake response: Emits "Done\n" after completing throw routine
//==============================================================================

// Current Servo Positions (Degrees [0..180])
int basePos     = 90;
int shoulderPos = 90;
int elbowPos    = 90;
int wrist1Pos   = 90;
int wrist2Pos   = 90;
int handPos     = 90;

// Servo Objects
Servo base;
Servo shoulder;
Servo elbow;
Servo wrist1;
Servo wrist2;
Servo hand;

// Forward Declarations
void homeState();
void pickUpObject();
void throwPlastic();
void throwPaper();
void throwCardboard();
void throwGlass();
void throwMetal();
void moveShoulderEased(int currentPos, int targetPos, int baseDelay);
void smoothMoveAllServos(int t1, int t2, int t3, int t4, int t5, int t6, int stepDelayMs);

void setup()
{
  Serial.begin(19200);
  pinMode(13, OUTPUT);

  // Attach Servo Pins
  base.attach(4);
  shoulder.attach(11);
  elbow.attach(12);
  wrist2.attach(6);
  wrist1.attach(10);
  hand.attach(5);

  homeState();
  Serial.println("Robotic Arm Ready");
}

void loop()
{
  if (Serial.available())
  {
    String inputStr = Serial.readStringUntil('\n');
    inputStr.trim();

    if (inputStr.length() == 0) return;

    // Continuous Joint Vector Command: S,q1,q2,q3,q4,q5,q6
    if (inputStr.startsWith("S,") || inputStr.startsWith("s,"))
    {
      int q1, q2, q3, q4, q5, q6;
      int count = sscanf(inputStr.c_str(), "%*c,%d,%d,%d,%d,%d,%d", &q1, &q2, &q3, &q4, &q5, &q6);
      if (count == 6)
      {
        smoothMoveAllServos(q1, q2, q3, q4, q5, q6, 15);
        Serial.println("Done");
      }
    }
    // Single-Character Category Triggers
    else if (inputStr.equalsIgnoreCase("P"))
    {
      Serial.println("Plastic Selected -> Throwing to Plastic Bin");
      pickUpObject();
      throwPlastic();
      delay(400);
      homeState();
      Serial.println("Done");
    }
    else if (inputStr.equalsIgnoreCase("A"))
    {
      Serial.println("Paper Selected -> Throwing to Paper Bin");
      pickUpObject();
      throwPaper();
      delay(400);
      homeState();
      Serial.println("Done");
    }
    else if (inputStr.equalsIgnoreCase("C"))
    {
      Serial.println("Cardboard Selected -> Throwing to Cardboard Bin");
      pickUpObject();
      throwCardboard();
      delay(400);
      homeState();
      Serial.println("Done");
    }
    else if (inputStr.equalsIgnoreCase("G"))
    {
      Serial.println("Glass Selected -> Throwing to Glass Bin");
      pickUpObject();
      throwGlass();
      delay(400);
      homeState();
      Serial.println("Done");
    }
    else if (inputStr.equalsIgnoreCase("M"))
    {
      Serial.println("Metal Selected -> Throwing to Metal Bin");
      pickUpObject();
      throwMetal();
      delay(400);
      homeState();
      Serial.println("Done");
    }
    else if (inputStr.equalsIgnoreCase("H") || inputStr.equalsIgnoreCase("RESET"))
    {
      homeState();
      Serial.println("Done");
    }
    else if (inputStr.equalsIgnoreCase("E") || inputStr.equalsIgnoreCase("STOP"))
    {
      hand.write(160); // Release gripper
      delay(200);
      Serial.println("Emergency Stopped");
    }
  }
}

// Shoulder easing movement to avoid torque spikes
void moveShoulderEased(int currentPos, int targetPos, int baseDelay)
{
  int totalSteps = abs(targetPos - currentPos);
  if (totalSteps == 0) return;

  int direction = (targetPos > currentPos) ? 1 : -1;

  for (int step = 0; step <= totalSteps; step++)
  {
    int pos = currentPos + (direction * step);
    shoulder.write(pos);

    int distFromStart = step;
    int distFromEnd = totalSteps - step;
    int distFromEdge = min(distFromStart, distFromEnd);
    int easeWindow = min(15, totalSteps / 3);

    int stepDelay = baseDelay;
    if (easeWindow > 0 && distFromEdge < easeWindow)
    {
      int extra = map(distFromEdge, 0, easeWindow, baseDelay * 2, 0);
      stepDelay = baseDelay + extra;
    }
    delay(stepDelay);
  }

  shoulderPos = targetPos;
}

// Smooth multi-joint interpolation
void smoothMoveAllServos(int t1, int t2, int t3, int t4, int t5, int t6, int stepDelayMs)
{
  t1 = constrain(t1, 0, 180);
  t2 = constrain(t2, 0, 180);
  t3 = constrain(t3, 0, 180);
  t4 = constrain(t4, 0, 180);
  t5 = constrain(t5, 0, 180);
  t6 = constrain(t6, 0, 180);

  int maxDiff = max(abs(t1 - basePos), abs(t2 - shoulderPos));
  maxDiff = max(maxDiff, abs(t3 - elbowPos));
  maxDiff = max(maxDiff, abs(t4 - wrist1Pos));
  maxDiff = max(maxDiff, abs(t5 - wrist2Pos));
  maxDiff = max(maxDiff, abs(t6 - handPos));

  if (maxDiff == 0) return;

  for (int step = 1; step <= maxDiff; step++)
  {
    float fraction = (float)step / (float)maxDiff;

    int cur1 = basePos     + (int)((t1 - basePos)     * fraction);
    int cur2 = shoulderPos + (int)((t2 - shoulderPos) * fraction);
    int cur3 = elbowPos    + (int)((t3 - elbowPos)    * fraction);
    int cur4 = wrist1Pos   + (int)((t4 - wrist1Pos)   * fraction);
    int cur5 = wrist2Pos   + (int)((t5 - wrist2Pos)   * fraction);
    int cur6 = handPos     + (int)((t6 - handPos)     * fraction);

    base.write(cur1);
    shoulder.write(cur2);
    elbow.write(cur3);
    wrist1.write(cur4);
    wrist2.write(cur5);
    hand.write(cur6);

    delay(stepDelayMs);
  }

  basePos     = t1;
  shoulderPos = t2;
  elbowPos    = t3;
  wrist1Pos   = t4;
  wrist2Pos   = t5;
  handPos     = t6;
}

// Pickup sequence from central target zone
void pickUpObject()
{
  // 1. Open gripper
  hand.write(160);
  handPos = 160;
  delay(400);

  // 2. Align wrist
  wrist2.write(110);
  wrist2Pos = 110;
  delay(300);

  // 3. Lower elbow
  elbow.write(140);
  elbowPos = 140;
  delay(400);

  // 4. Lower shoulder to reach item
  moveShoulderEased(shoulderPos, 32, 12);
  delay(400);

  // 5. Close gripper firmly on item
  hand.write(15);
  handPos = 15;
  delay(600);
}

// Throw routines for specific waste categories
void throwPlastic()
{
  moveShoulderEased(shoulderPos, 100, 15);
  elbow.write(130);
  elbowPos = 130;
  wrist2.write(110);
  wrist2Pos = 110;

  base.write(110);
  basePos = 110;
  delay(1900);
  base.write(90);

  delay(300);
  hand.write(160);
  handPos = 160;
  delay(400);

  base.write(75);
  basePos = 75;
  delay(1200);
  base.write(90);
}

void throwPaper()
{
  elbow.write(140);
  elbowPos = 140;
  delay(400);

  moveShoulderEased(shoulderPos, 95, 15);
  elbow.write(130);
  elbowPos = 130;
  delay(400);

  wrist2.write(110);
  wrist2Pos = 110;
  delay(400);

  base.write(120);
  basePos = 120;
  delay(9800);
  base.write(90);

  delay(300);
  hand.write(160);
  handPos = 160;
  delay(400);

  base.write(70);
  basePos = 70;
  delay(3500);
  base.write(90);
}

void throwGlass()
{
  moveShoulderEased(shoulderPos, 100, 15);
  delay(400);

  elbow.write(130);
  elbowPos = 130;
  delay(400);

  wrist2.write(140);
  wrist2Pos = 140;
  delay(400);

  base.write(70);
  basePos = 70;
  delay(2100);
  base.write(90);

  delay(300);
  hand.write(160);
  handPos = 160;
  delay(400);

  base.write(120);
  basePos = 120;
  delay(1500);
  base.write(90);
}

void throwMetal()
{
  hand.write(15);
  handPos = 15;

  moveShoulderEased(shoulderPos, 95, 15);
  delay(400);

  elbow.write(130);
  elbowPos = 130;
  delay(800);

  wrist2.write(140);
  wrist2Pos = 140;
  delay(400);

  base.write(75);
  basePos = 75;
  delay(1500);
  base.write(90);

  delay(300);
  hand.write(160);
  handPos = 160;
  delay(400);

  base.write(110);
  basePos = 110;
  delay(1600);
  base.write(90);
}

void throwCardboard()
{
  moveShoulderEased(shoulderPos, 105, 15);
  delay(400);

  elbow.write(130);
  elbowPos = 130;
  delay(800);

  base.write(125);
  basePos = 125;
  delay(2350);
  base.write(90);

  delay(300);
  moveShoulderEased(shoulderPos, 85, 15);
  delay(300);

  elbow.write(110);
  elbowPos = 110;
  delay(400);

  hand.write(160);
  handPos = 160;
  delay(400);

  base.write(60);
  basePos = 60;
  delay(1600);
  base.write(90);
}

// Reset Arm to Home Ready State
void homeState()
{
  wrist2.write(160);
  wrist2Pos = 160;
  delay(400);

  elbow.write(160);
  elbowPos = 160;
  delay(400);

  moveShoulderEased(shoulderPos, 85, 15);
  delay(400);

  hand.write(120);
  handPos = 120;
  delay(400);
}
