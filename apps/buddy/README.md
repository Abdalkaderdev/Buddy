# Buddy — App + Hardware Build

This folder holds the Buddy app code and a step-by-step hardware build guide
for the Raspberry Pi 4 version. For the project overview, see the
[root README](../../README.md).

---

## Hardware bill of materials (ecity-iq.com, Erbil)

| Item | Price (IQD) | Notes |
|---|---|---|
| Raspberry Pi 4 Model B | — | Use what you have |
| Pi 4 USB-C 5V power supply | 5,500 | Or any 5V/3A USB-C charger (iPhone 20W brick works) |
| Night Vision Fisheye Camera 5MP 160° (OV5647) | 25,000 | 15-pin CSI ribbon |
| USB Sound Card (USB→3.5mm) | 3,000 | Plugs into any Pi USB-A port |
| Mini 2-wire microphone | 500 | Solder a 3.5mm plug onto it, or skip and use a USB headset mic |
| Mono 5W audio amplifier board | 1,250 | Powered from Pi 5V GPIO |
| Harman Kardon 1.5" 40mm 4Ω 3W speaker | 5,000 | 2 wires to the amp output |
| **Subtotal** | **~40,250** | ~$31 USD |

Plus: microSD card ≥16 GB, a USB SD-card reader, your laptop with Wi-Fi.

---

## Wiring

```
                 ┌─────────────────────────────┐
                 │        Raspberry Pi 4       │
                 │                             │
  USB-C ◄───── 5V/3A power supply              │
                 │                             │
  CSI  ◄───── Fisheye camera (15-pin ribbon)   │
                 │                             │
  USB-A ◄───── USB Sound Card                  │
                 │   │                         │
                 │   ├─pink jack ──── Mini mic │
                 │   │                         │
                 │   └─green jack ──┐          │
                 │                  │          │
  GPIO 5V (pin 2) ──────────────┐   │          │
  GPIO GND (pin 6) ─────────┐   │   │          │
                 │          │   │   │          │
                 └──────────┼───┼───┼──────────┘
                            ▼   ▼   ▼
                       ┌─────────────────┐
                       │  Mono 5W amp    │
                       │  VCC GND IN+ IN-│
                       │   SPK+    SPK-  │
                       └────┬───────┬────┘
                            │       │
                            ▼       ▼
                      Harman Kardon speaker
                          4Ω 3W
```

### Step-by-step

**Safety first**

- Always power **OFF** the Pi before plugging or unplugging the camera ribbon.
- The Pi 4 USB-C port is power-only — you cannot use it as a USB data port.
- The CSI ribbon clip is fragile — lift it gently.

**1. Camera**

The Pi 4's CSI connector is between the HDMI ports and the headphone jack.

1. With the Pi powered off, gently lift the small plastic clip on the camera connector by pulling up at the two corners with a fingernail.
2. Slide the ribbon in with **silver/copper contacts facing the HDMI ports**, blue plastic facing the USB ports.
3. Push the clip back down to lock it.
4. Repeat on the camera board side.

**2. Microphone via USB sound card**

The USB sound card has two 3.5 mm jacks: **pink = mic in**, **green = audio out**.

1. Plug the USB sound card into any Pi USB-A port.
2. Plug the microphone into the **pink** jack.
   - The 2-wire mini element from ecity needs a 3.5 mm mono plug soldered on (tip = signal, sleeve = ground). If you'd rather skip the soldering, any USB headset with a built-in mic plugged directly into the Pi works.

**3. Speaker + amplifier**

The mono 5 W amp board has 4 input pads (`VCC`, `GND`, `IN+`, `IN-`) and 2 output pads (`SPK+`, `SPK-`).

1. **Power the amp from the Pi GPIO header** (the 40-pin block in the top-left of the Pi):
   - **GPIO pin 2** (5 V) → amp **VCC**
   - **GPIO pin 6** (GND) → amp **GND**
2. **Audio input from the sound card**:
   - Use a 3.5 mm-jack-to-2-wire pigtail.
   - Wire signal (tip) → amp **IN+**
   - Wire ground (sleeve) → amp **IN-**
3. **Output to the speaker**:
   - Amp **SPK+** → speaker red (+)
   - Amp **SPK-** → speaker black (-)
4. Mount the speaker so the cone faces outward.

**4. Sanity check before first power-on**

- [ ] Camera ribbon is locked into the CSI connector
- [ ] USB sound card is plugged in
- [ ] Mic is in the **pink** jack
- [ ] Amp `VCC`/`GND` are on GPIO **pin 2** and **pin 6** (not 1 or 14 — those are 3.3V)
- [ ] Speaker leads are not shorted to each other
- [ ] microSD with Raspberry Pi OS is inserted

---

## Software setup

### 1. Flash the SD card

On your laptop:

1. Install [Raspberry Pi Imager](https://www.raspberrypi.com/software/).
2. **CHOOSE DEVICE** → Raspberry Pi 4
3. **CHOOSE OS** → Raspberry Pi OS (64-bit)
4. **CHOOSE STORAGE** → your microSD
5. Click **NEXT** → **EDIT SETTINGS**:
   - Hostname: `buddy`
   - Username: `pi`, password: pick something memorable
   - Wireless LAN: the SSID + password of the network your Pi will join
   - Wireless LAN country: `IQ`
   - Time zone: `Asia/Baghdad`
   - Services tab → enable **SSH** (password auth)
6. **SAVE** → **YES** → wait for "Write Successful"

### 2. First boot

1. Slot SD card into the Pi, plug USB-C power in.
2. Wait ~60 s for first boot.
3. From a device on the same Wi-Fi: `ping buddy.local` — should reply.
4. `ssh pi@buddy.local` and enter the password you set.

### 3. Install Buddy

```bash
curl -L https://raw.githubusercontent.com/Abdalkaderdev/Buddy/main/apps/buddy/scripts/setup_pi.sh | bash
```

The script installs system packages, creates a venv, installs Buddy, and sets up `buddy.service` as a systemd unit that starts at boot.

### 4. Add your API key

```bash
echo "ANTHROPIC_API_KEY=sk-ant-..." > ~/.buddy.env
chmod 600 ~/.buddy.env
systemctl --user restart buddy.service
```

### 5. Talk to Buddy

From any device on the same Wi-Fi, open <http://buddy.local:8080>, click the purple mic, and talk.

Use Chrome or Edge — Firefox's speech recognition is unreliable.

---

## Run on your laptop (no Pi needed)

For dev work before the Pi parts arrive:

```bash
# From the repo root
.venv/Scripts/python -m buddy.server          # Windows
.venv/bin/python -m buddy.server              # macOS / Linux
```

Buddy still chats, sees your laptop webcam, and talks. The motion calls (for a future Reachy Mini) just fail silently.

---

## Project structure

```
apps/buddy/
├── README.md            # this file
├── pyproject.toml
├── scripts/
│   └── setup_pi.sh      # one-shot Pi installer
└── buddy/
    ├── server.py        # FastAPI + WebSocket web UI
    ├── ai.py            # Claude / Ollama provider
    ├── audio.py         # Whisper STT + Edge TTS
    ├── vision.py        # OpenCV face detection
    ├── motion.py        # (optional) physical motion
    ├── config.py        # personality + settings
    ├── data/            # SQLite face DB (gitignored)
    └── static/          # web UI (HTML/CSS/JS)
```

---

## Configuration

Edit `buddy/config.py`:

| Setting | Default |
|---|---|
| `LLM_PROVIDER` | `"claude"` (or `"ollama"`) |
| `CLAUDE_MODEL` | `claude-haiku-4-5-20251001` |
| `SYSTEM_PROMPT` | Buddy's personality |
| `TTS_VOICE` | `en-IE-ConnorNeural` |
| `WHISPER_MODEL` | `base` |
| `FACE_DETECTION_INTERVAL` | seconds between camera checks |

Server env vars:

| Var | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API key |
| `BUDDY_CAMERA` | `0` disables the camera worker |
| `BUDDY_CAMERA_INDEX` | which `/dev/videoN` to use (default 0) |

---

## License

MIT.
