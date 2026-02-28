"""
FERNANDA — Serial Bridge (FINAL)
Listens to ntfy.sh for tip events → sends T1/T2/T3 to Nano Every over serial.

SETUP:
1. Find your serial port:
      Mac/Linux:  run → ls /dev/tty.usb*
      Windows:    Device Manager → Ports → COMx

2. Paste your port into SERIAL_PORT below

3. Make sure NTFY_TOPIC matches the one in index.html

4. Install deps (run once):
      pip install pyserial requests

5. Close Arduino IDE Serial Monitor first (it blocks the port)

6. Run:
      python bridge.py
"""

import serial
import requests
import json
import time
import sys

# ── CONFIG — CHANGE THESE ─────────────────────────────
SERIAL_PORT = "/dev/tty.usbmodem101"   # ← YOUR PORT (run: ls /dev/tty.usb*)
BAUD_RATE   = 9600
NTFY_TOPIC  = "fernanda-twerks-2026"     # ← MUST MATCH index.html

# ─────────────────────────────────────────────────────
NTFY_URL = f"https://ntfy.sh/{NTFY_TOPIC}/sse"

TIP_LABELS = {
    "T1": "💸 $1  — shy wiggle",
    "T2": "💸 $5  — proper twerk",
    "T3": "🔥 $10 — FULL SEND",
}

def connect_serial():
    while True:
        try:
            ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
            time.sleep(2)
            print(f"✓ Serial connected: {SERIAL_PORT}")
            ser.write(b"PING\n")
            time.sleep(0.3)
            resp = ser.readline().decode("utf-8", errors="ignore").strip()
            if resp == "PONG":
                print("✓ Nano responding — FERNANDA IS ONLINE\n")
            else:
                print(f"  (Nano said: '{resp}' — continuing anyway)\n")
            return ser
        except serial.SerialException as e:
            print(f"✗ Cannot open {SERIAL_PORT}: {e}")
            print("  → Is the Nano plugged in?")
            print("  → Is Arduino IDE Serial Monitor closed?")
            print("  → Run: ls /dev/tty.usb* to find your port")
            print("  Retrying in 3s...\n")
            time.sleep(3)

def send(ser, cmd):
    try:
        ser.write(f"{cmd}\n".encode())
        time.sleep(0.15)
        ack = ser.readline().decode("utf-8", errors="ignore").strip()
        print(f"  → {TIP_LABELS.get(cmd, cmd)}  |  Nano: {ack}")
    except serial.SerialException as e:
        print(f"  ✗ Serial error: {e}")

def parse(lines):
    for line in lines:
        if line.startswith("data:"):
            try:
                data = json.loads(line[5:].strip())
                msg  = data.get("message", "").lower().strip()
                tags = [t.lower() for t in data.get("tags", [])]
                return msg, tags
            except json.JSONDecodeError:
                pass
    return None, []

def tip_to_cmd(msg, tags):
    mapping = {
        "tip1": "T1", "1": "T1",
        "tip2": "T2", "2": "T2",
        "tip3": "T3", "3": "T3",
    }
    for key, cmd in mapping.items():
        if key == msg or key in tags:
            return cmd
    return None

def main():
    print("=" * 45)
    print("  FERNANDA — Serial Bridge")
    print(f"  ntfy topic : {NTFY_TOPIC}")
    print(f"  serial port: {SERIAL_PORT}")
    print("=" * 45 + "\n")

    ser = connect_serial()
    print(f"Listening on ntfy.sh/{NTFY_TOPIC}...")
    print("Press a tip button on the website to test.\n")

    while True:
        try:
            with requests.get(NTFY_URL, stream=True, timeout=90) as resp:
                resp.raise_for_status()
                buf = []
                for raw in resp.iter_lines(decode_unicode=True):
                    if raw:
                        buf.append(raw)
                    elif buf:
                        msg, tags = parse(buf)
                        buf = []
                        if not msg or msg in ("open", "keepalive"):
                            continue
                        cmd = tip_to_cmd(msg, tags)
                        if cmd:
                            send(ser, cmd)
                        else:
                            print(f"  (ignored: msg='{msg}' tags={tags})")
        except requests.exceptions.Timeout:
            print("  Stream timeout — reconnecting...")
        except requests.exceptions.ConnectionError:
            print("  No connection — check wifi. Retrying in 5s...")
            time.sleep(5)
        except KeyboardInterrupt:
            print("\n\nStopping — centering servo...")
            send(ser, "STOP")
            ser.close()
            sys.exit(0)

if __name__ == "__main__":
    main()
