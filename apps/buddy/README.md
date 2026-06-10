# Buddy — Interactive Companion Robot

A playful AI companion that recognizes faces, chats conversationally,
and (optionally) expresses emotions through movement on a Reachy Mini.
This README is for the **Raspberry Pi 4 build** sourced from ecity-iq.com.

---

## Features

- **Conversational AI** — Claude Haiku 4.5 (or Ollama as fallback)
- **Voice in** — browser Web Speech API (Chrome/Edge), or `/api/transcribe` with Whisper
- **Voice out** — Edge TTS (12 voices: English + Iraqi/Egyptian/Saudi Arabic)
- **Face detection** — OpenCV (USB webcam or Pi camera)
- **Optional face recognition** — `face_recognition` extra (`pip install buddy[recognition]`)
- **Optional motion** — works as a chat-only app if no Reachy Mini robot is connected

---

## Hardware bill of materials (ecity-iq.com, Erbil)

| Item | Price (IQD) | Notes |
|---|---|---|
| Raspberry Pi 4 Model B | (have it) | Pi 5 needs a 15→22-pin CSI adapter |
| Pi 4 USB-C 5V power supply | 5,500 | Pi 5 uses the 27W variant instead |
| Night Vision Fisheye Camera 5MP 160° (OV5647) | 25,000 | 15-pin CSI ribbon |
| USB Sound Card (USB→3.5mm) | 3,000 | Plugs into any Pi USB-A port |
| Mini 2-wire microphone | 500 | Solder to a 3.5mm plug (or use a pre-made mic) |
| Mono 5W audio amplifier board | 1,250 | Powered from Pi 5V GPIO |
| Harman Kardon 1.5" 40mm 4Ω 3W speaker | 5,000 | 2 wires to the amp output |
| **Subtotal** | **~40,250** | ~$31 USD |

You also need: a microSD card (≥16 GB), a USB SD-card reader, and your laptop with Wi-Fi.

---

## Hardware assembly

### 0. Safety

- **Always power OFF the Pi before plugging or unplugging the camera ribbon.** Hot-plugging the CSI ribbon can short the camera connector.
- The Pi 4 USB-C port is **power-only** — you cannot use it as a USB data port to a computer.
- Treat the Pi gently: the CSI ribbon clip is fragile.

### 1. Power supply (Pi 4 USB-C)

1. Plug the USB-C end of the ecity 5,500 IQD power supply (or any 5V/3A USB-C charger such as a 20W iPhone brick) into the **USB-C port** of the Pi.
2. Don't power it on yet — finish wiring first.

### 2. Camera (Night Vision Fisheye 5MP)

The Pi 4 has a **15-pin CSI ribbon connector** between the HDMI ports and the headphone jack. The fisheye camera kit usually ships with the ribbon already attached.

1. With the Pi powered off, gently lift the small **plastic clip** on the camera connector (pull up at the corners with a fingernail).
2. Slide the ribbon in with **silver/copper contacts facing the HDMI ports**, blue plastic backing facing the USB ports.
3. Push the plastic clip back down to lock it.
4. Repeat the same procedure on the camera board side.
5. (Optional) Connect the two infrared LEDs to the small 3-pin header on the camera if you bought them — for night-vision in dark rooms.

### 3. Microphone (via USB sound card)

The ecity USB sound card has two 3.5mm jacks (pink = mic in, green = headphone out).

1. Plug the **USB sound card** into any USB-A port on the Pi.
2. Plug the **mini microphone** into the **pink** 3.5mm jack of the sound card.
   - The 2-wire mini element from ecity needs a 3.5mm mono plug soldered on (tip = signal, sleeve = ground). If you'd rather skip soldering: any USB headset with a built-in mic plugged directly into the Pi works.

### 4. Speaker + amplifier

The mono 5W amplifier board has 4 input pads (VCC, GND, audio +, audio −) and 2 output pads (SPK+, SPK−).

1. **Power the amp from the Pi GPIO header** (top-left 40-pin block on the Pi):
   - **GPIO pin 2** (5V) → amp **VCC**
   - **GPIO pin 6** (GND) → amp **GND**
2. **Audio input from the sound card:**
   - Use a 3.5mm-jack-to-2-wire pigtail to take audio from the **green** jack of the sound card.
   - Connect the wire's signal (tip) to the amp's **IN+**
   - Connect the wire's ground (sleeve) to the amp's **IN−**
3. **Output to the speaker:**
   - Amp **SPK+** → red (or marked +) terminal of the Harman Kardon speaker
   - Amp **SPK−** → black (or marked −) terminal
4. Mount the speaker so the cone faces outward.

```
    Pi 4 USB-A ──── USB Sound Card ── pink jack ──── 2-wire MIC
                                  └── green jack ──── 5W amp IN ──── Speaker (4Ω 3W)
    Pi 4 GPIO 5V/GND ─────────────────── 5W amp VCC/GND
    Pi 4 CSI ──────── Camera Module 3 / Fisheye
    Pi 4 USB-C ────── 5V/3A power
```

### 5. Final check before first power-on

- [ ] Camera ribbon is locked into the CSI connector
- [ ] USB sound card is plugged in
- [ ] Mic is in the pink jack
- [ ] Amp VCC/GND are on GPIO pin 2 / pin 6 (not 1 or 14 — those are 3.3V / different)
- [ ] Speaker leads are not shorted to each other
- [ ] SD card with Raspberry Pi OS Bookworm is inserted (we'll prep that next)

---

## Software setup on the Pi

### 1. Flash the SD card

On your laptop:

1. Install [Raspberry Pi Imager](https://www.raspberrypi.com/software/).
2. CHOOSE DEVICE → Raspberry Pi 4. CHOOSE OS → Raspberry Pi OS 64-bit. CHOOSE STORAGE → your SD card.
3. Click NEXT → EDIT SETTINGS:
   - Hostname: `buddy`
   - Username: `pi`, password: pick something you'll remember
   - Wireless LAN: SSID + password of the network the Pi should join (same network your laptop is on, or your phone's hotspot)
   - Wireless LAN country: `IQ`
   - Time zone: `Asia/Baghdad`
   - Enable SSH (password auth)
4. SAVE → YES → wait for "Write Successful".

### 2. Boot the Pi

1. Slot the SD card back into the Pi.
2. Plug the USB-C power supply in.
3. Wait ~60 seconds for first boot (it expands the filesystem and joins Wi-Fi).
4. From your laptop on the **same Wi-Fi** as the Pi:

```bash
ping buddy.local
```

If that replies, SSH in:

```bash
ssh pi@buddy.local
```

### 3. Install Buddy (one-shot script)

On the Pi (over SSH), run:

```bash
curl -L https://raw.githubusercontent.com/Abdalkaderdev/Buddy/main/apps/buddy/scripts/setup_pi.sh | bash
```

or copy `apps/buddy/scripts/setup_pi.sh` to the Pi and run `bash setup_pi.sh`. The script:

- Installs Python, OpenCV deps, ffmpeg, ALSA, libcamera
- Creates a venv at `~/buddy-venv`
- Installs Buddy and all dependencies
- Creates a `buddy.service` systemd unit so Buddy starts at boot

### 4. Add your API key

```bash
echo "ANTHROPIC_API_KEY=sk-ant-..." > ~/.buddy.env
chmod 600 ~/.buddy.env
systemctl --user restart buddy.service
```

### 5. Open Buddy from any phone or laptop

On the same Wi-Fi: open `http://buddy.local:8080`.

Click the big purple mic and talk. Buddy listens, thinks, talks back, and (if the camera is wired) knows whether you're in the room.

---

## Quick start (laptop / simulator, no Pi needed)

If you want to develop on your laptop before the Pi parts arrive:

```bash
# From the repo root
.venv/Scripts/python -m buddy.server          # Windows
.venv/bin/python -m buddy.server              # macOS / Linux
```

Then open <http://localhost:8080>. The robot motion calls will fail gracefully — Buddy still chats, sees you on the webcam, and talks.

---

## Commands

| Command | Description |
|---|---|
| `/enroll <name>` | (CLI mode) teach Buddy a face |
| `/faces` | List enrolled faces |
| `quit` | Exit |

---

## Configuration

Edit `apps/buddy/buddy/config.py`:

| Variable | Purpose |
|---|---|
| `LLM_PROVIDER` | `"claude"` (API) or `"ollama"` (local) |
| `CLAUDE_MODEL` | default: `claude-haiku-4-5-20251001` |
| `OLLAMA_MODEL` | default: `qwen2.5:3b` |
| `SYSTEM_PROMPT` | Buddy's personality |
| `TTS_VOICE` | default voice code |
| `WHISPER_MODEL` | `tiny` / `base` / `small` / `medium` / `large` |
| `FACE_DETECTION_INTERVAL` | seconds between camera checks |

Server-side env vars:

| Var | Default | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | unset | Claude API key |
| `BUDDY_CAMERA` | `1` | set `0` to disable the camera worker |
| `BUDDY_CAMERA_INDEX` | `0` | which `/dev/videoN` to use |

---

## Project structure

```
apps/buddy/
├── README.md            # this file
├── pyproject.toml
├── scripts/
│   └── setup_pi.sh      # one-shot Raspberry Pi installer
└── buddy/
    ├── __init__.py
    ├── main.py          # CLI entry point
    ├── server.py        # FastAPI + WebSocket web UI
    ├── ai.py            # Claude / Ollama provider
    ├── audio.py         # Whisper STT + Edge TTS
    ├── vision.py        # OpenCV face detection + recognition
    ├── motion.py        # Optional Reachy Mini motion
    ├── config.py        # All settings
    ├── data/            # SQLite face DB (gitignored)
    └── static/          # index.html + main.js + style.css
```

---

## Actions

Buddy can include any of these in its reply (Claude emits `[ACTION:name]` tags
that the server parses and either sends to the robot or animates in the UI):

| Action | Effect |
|---|---|
| `nod`, `shake` | head yes / no |
| `look_up`, `look_down` | pitch |
| `spin` | big yaw swing |
| `dance` | rhythmic head + antennas |
| `curious` | head tilt |
| `giggle` | quick shaky head |
| `perk_antennas`, `droop_antennas` | antenna emotion |

---

## License

MIT for the Buddy app. The Reachy Mini SDK it builds on is Apache 2.0;
the hardware design files (3D prints) are CC BY-SA-NC by Pollen Robotics.
