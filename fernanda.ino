/*
 * FERNANDA — THE TWERKING PLANT
 * ITP/IMA Stupid Hackathon 2026
 *
 * Board:  Arduino Nano Every
 * Servo:  MG90D on D6
 * Power:  Nano 5V pin → servo red
 *         Nano GND    → servo brown (SHARED GROUND — critical)
 *         2x 1000µF 25V caps in parallel across power rails
 *
 * WIRING:
 *   Servo ORANGE (signal) → D6
 *   Servo RED    (power)  → Nano 5V pin
 *   Servo BROWN  (gnd)    → Nano GND pin
 *   Demo button one leg   → D7
 *   Demo button other leg → GND
 *
 * SERIAL COMMANDS (sent by bridge.py):
 *   T1   → polite wiggle   ($1 tip)
 *   T2   → proper twerk    ($5 tip)
 *   T3   → FULL SEND       ($10 tip)
 *   STOP → stop demo mode, return to center
 *   PING → replies PONG (connection check)
 */

#include <Servo.h>

// ── PINS ──────────────────────────────────────────────
const int SERVO_PIN  = 6;
const int BUTTON_PIN = 7;   // demo mode button

// ── SERVO ─────────────────────────────────────────────
Servo hip;

// ── CENTER POSITION ───────────────────────────────────
// If servo isn't centered, tweak this value (try 85 or 95)
const int CENTER = 90;

// ── STATE ─────────────────────────────────────────────
bool demoMode        = false;
bool lastButtonState = HIGH;
unsigned long lastDemoBeat = 0;
const int DEMO_BPM   = 120;

// ── SETUP ─────────────────────────────────────────────
void setup() {
  Serial.begin(9600);
  pinMode(BUTTON_PIN, INPUT_PULLUP);

  hip.attach(SERVO_PIN);
  hip.write(CENTER);
  delay(800);   // let servo settle on boot

  Serial.println("FERNANDA ONLINE");
  Serial.println("Commands: T1 T2 T3 STOP PING");
}

// ── LOOP ──────────────────────────────────────────────
void loop() {

  // ── BUTTON: toggle demo mode ──
  bool buttonState = digitalRead(BUTTON_PIN);
  if (buttonState == LOW && lastButtonState == HIGH) {
    demoMode = !demoMode;
    Serial.println(demoMode ? "DEMO ON" : "DEMO OFF");
    if (!demoMode) hip.write(CENTER);
    delay(50);  // debounce
  }
  lastButtonState = buttonState;

  // ── DEMO MODE: auto twerk at 120 BPM ──
  if (demoMode) {
    unsigned long interval = 60000UL / DEMO_BPM;
    if (millis() - lastDemoBeat >= interval) {
      lastDemoBeat = millis();
      twerk(2);   // T3 in demo mode — full send
    }
    return;
  }

  // ── SERIAL COMMANDS ──
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    cmd.toUpperCase();

    if      (cmd == "T1")   { twerk(0); Serial.println("ACK T1"); }
    else if (cmd == "T2")   { twerk(1); Serial.println("ACK T2"); }
    else if (cmd == "T3")   { twerk(2); Serial.println("ACK T3"); }
    else if (cmd == "STOP") { demoMode = false; hip.write(CENTER); Serial.println("ACK STOP"); }
    else if (cmd == "PING") { Serial.println("PONG"); }
    else                    { Serial.print("UNKNOWN: "); Serial.println(cmd); }
  }
}

// ── TWERK ─────────────────────────────────────────────
// level 0 = T1 shy wiggle
// level 1 = T2 proper twerk  
// level 2 = T3 full unhinged send
void twerk(int level) {

  // angle, thrustMs, returnMs, reps
  int params[3][4] = {
    { 35, 35, 70,  3  },   // T1 — embarrassed wiggle
    { 55, 25, 50,  7  },   // T2 — committed twerk
    { 80, 18, 35, 12  },   // T3 — unhinged, no regrets
  };

  int angle    = params[level][0];
  int thrustMs = params[level][1];
  int returnMs = params[level][2];
  int reps     = params[level][3];

  for (int i = 0; i < reps; i++) {
    // Alternate direction each rep for realistic hip motion
    hip.write(i % 2 == 0 ? CENTER + angle : CENTER - angle);
    delay(thrustMs);
    hip.write(CENTER);
    delay(returnMs);
  }

  hip.write(CENTER);
  delay(100);
}
