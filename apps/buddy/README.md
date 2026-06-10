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
                  +-----------------------------+
                  |       Raspberry Pi 4        |
                  |                             |
   USB-C  <----- 5V / 3A power supply           |
                  |                             |
   CSI    <----- Fisheye camera (15-pin ribbon) |
                  |                             |
   USB-A  <----- USB Sound Card                 |
                  |   |                         |
                  |   +--pink jack ----- Mic    |
                  |   |                         |
                  |   +--green jack ---+        |
                  |                    |        |
   GPIO pin 2 (5V) ---------------+    |        |
   GPIO pin 6 (GND) ---------+    |    |        |
                  |          |    |    |        |
                  +----------|----|----|--------+
                             v    v    v
                        +--------------------+
                        |   Mono 5W amp      |
                        |  VCC GND IN+ IN-   |
                        |     OUT+  OUT-     |
                        +------+------+------+
                               |      |
                               v      v
                         Harman Kardon speaker
                              4 ohm 3W
```

### Pi 4 ports cheat-sheet

Hold the Pi with the USB ports on the right and the GPIO header at the top.

- **USB-C** (left edge): power **only** on the Pi 4. Do not try to use it for data.
- **HDMI micro** x2 (left edge): video out.
- **CSI camera** ribbon connector: sits **between the HDMI sockets and the 3.5 mm headphone jack**. (Note: the second slim connector between the USB ports and the SD-card edge is DSI for displays — do **not** plug the camera there.)
- **3.5 mm jack** (left edge): unused for Buddy. We route audio over USB instead because the Pi's onboard analog output is noisy.
- **USB-A** x4 (right edge): pick any one for the sound card.
- **40-pin GPIO header** (top edge): used only for **pin 2** (5 V) and **pin 6** (GND) to power the amp.

### Safety first — read before touching anything

- **Power the Pi off and unplug USB-C before** plugging or unplugging the camera ribbon, or moving any GPIO wire. CSI is **not** hot-swappable.
- **Never feed external 5 V into GPIO pin 2.** Pin 2 is an **output** sourced from the Pi's regulator. Picking power *from* it to drive the amp is fine; pushing power *into* it from a second supply can backfeed the Pi and kill it.
- **Use one power source.** Either USB-C powers the Pi (and the amp taps GPIO 5 V), **or** you power both Pi and amp from a beefier rail — do not run two separate supplies into the same 5 V net.
- **3.3 V vs 5 V.** GPIO pin 1 and pin 17 are **3.3 V** and will under-drive the amp. Pin 2 and pin 4 are the 5 V pins. Double-check before connecting VCC.
- **Don't short pin 2 to pin 6.** They sit right next to each other. A slip with a screwdriver = instant reboot or worse.
- **Camera ribbon polarity matters.** Plugging the CSI ribbon backwards puts 3.3 V on the wrong pins and **can permanently damage the camera sensor** the moment you power on. Verify orientation twice before locking the clip.
- **Keep speaker leads from shorting** to each other or to the GPIO header. The amp output is bridge-tied — a short can stress the chip.
- **Don't touch the 40-pin header while powered.** A loose washer or staple bridging pins can fry the SoC.

### 1. Camera

The Pi 4 CSI connector sits between the HDMI micro sockets and the 3.5 mm jack.

1. Pi is **powered off** and USB-C is **unplugged**.
2. Lift the dark plastic clip on the CSI socket by pulling up at the two short ends with a fingernail. It only travels about 2 mm — do not pry.
3. Insert the 15-pin ribbon with the **silver / exposed copper contacts facing the HDMI ports** and the **blue plastic stiffener facing the USB-A ports**. Push it in fully, straight, until the contacts disappear.
4. Press the clip back down evenly on both ends to lock it.
5. Repeat at the camera board end: contacts face the **back of the camera PCB** (the side without the lens), blue stiffener faces the lens side. Check the camera silkscreen if unsure.

**IR LEDs on the fisheye kit**

The OV5647 fisheye kit ships with **two infrared LEDs on short pigtails**. They plug into the **2-pin headers on the camera PCB itself** (one on each side of the lens, labelled IR LED or similar). They are **not** wired to the Pi GPIO. They draw their power from the camera's own 3.3 V rail and turn on automatically when the on-board light sensor decides it's dark enough. Just push each LED's connector onto its matching header — they are keyed/polarised, so they only fit one way. If a connector resists, flip it.

### 2. Microphone via USB sound card

The 7.1 USB sound card has two 3.5 mm jacks: **pink = mic input**, **green = headphone / line output**.

1. Plug the USB sound card into any Pi USB-A port.
2. Solder a 3.5 mm **mono** plug onto the 2-wire mini electret element:
   - **Tip** = signal (either wire — the element is non-polarised at audio level, but if you can read a `+` marking, that wire goes to tip)
   - **Sleeve** = ground
3. Plug the mic into the **pink** jack.
4. Plug a second 3.5 mm cable into the **green** jack. The other end goes to the amp input (see step 3).

Don't have / want to solder? Any USB headset with a built-in mic plugged directly into the Pi works as a drop-in replacement and you can skip the sound card entirely.

### 3. Speaker + amplifier

Ecity's mono 5 W amp is almost certainly a **PAM8403-class board** (or the very similar HXJ8002 / XPT8871). Pin labels vary slightly between batches, so trust the silkscreen on **your** board over this diagram if they disagree.

Typical pad layout:

```
   +-----------------------+
   |  VCC  GND  IN+  IN-   |   <- input side
   |                       |
   |     OUT+      OUT-    |   <- speaker side
   +-----------------------+
```

Some boards label the inputs `L`, `R`, `GND` (stereo) and the outputs `L+ L- R+ R-`. For mono use, tie `L` and `R` together at the input and use only the `L+ / L-` output pair. Confirm before soldering.

1. **Power the amp from the Pi GPIO header** (the 40-pin block along the top edge):
   - **GPIO pin 2** (5 V) -> amp **VCC**
   - **GPIO pin 6** (GND) -> amp **GND**

   Pin counting on the GPIO header: with the SD card facing you and the GPIO header on the far edge, **pin 1 is the corner closest to the SD card**. Odd pins (1, 3, 5, 7...) are the row nearest the edge of the board; even pins (2, 4, 6...) are the inner row. So pin 2 is the **second** pin from the SD-card corner, inner row. Pin 6 is three pairs further along, inner row.

2. **Audio input from the sound card** (green jack -> amp):
   - 3.5 mm **tip** -> amp **IN+** (or `L`)
   - 3.5 mm **sleeve** -> amp **IN-** (or `GND`-input — many PAM8403 boards share input GND with VCC GND; that's fine)
3. **Output to the speaker**:
   - Amp **OUT+** -> speaker red (+)
   - Amp **OUT-** -> speaker black (-)

   Do **not** ground either OUT pad. PAM8403 outputs are bridge-tied — grounding one side will short the bridge and may smoke the chip.
4. Mount the speaker so the cone faces outward through your enclosure. A 4 ohm 3 W speaker on a 5 W amp will run comfortably; expect roughly 1.5 W of clean output from a 5 V USB supply.

### 4. Sanity check before first power-on

- [ ] Camera ribbon is locked: silver contacts face the HDMI side at both ends
- [ ] IR LED pigtails are seated on the camera PCB headers (not floating)
- [ ] USB sound card is plugged into a USB-A port
- [ ] Mic is in the **pink** jack, audio cable to the amp is in the **green** jack
- [ ] Amp `VCC` is on GPIO **pin 2** and `GND` is on GPIO **pin 6** — not pin 1 (3.3 V) and not pin 14 (also GND but on the opposite row)
- [ ] No loose wire strands near the GPIO header
- [ ] Speaker leads not shorted to each other or to the chassis
- [ ] microSD with Raspberry Pi OS is fully inserted

### 5. First power-on test — exact commands

SSH in (`ssh pi@buddy.local`) and run these one at a time. Each one tests one subsystem.

**Power health** — confirms the USB-C supply is delivering enough current:

```bash
vcgencmd get_throttled
```

Expect `throttled=0x0`. Any other value means under-voltage / throttling has occurred (see troubleshooting).

**USB sound card detection**:

```bash
arecord -l        # list capture devices
aplay  -l         # list playback devices
```

The USB sound card should appear as something like `card 1: Device [USB PnP Sound Device]` in both lists. If only the Pi's built-in HDMI / headphone shows up, the sound card was not detected — re-seat the USB connector.

**Mic record + speaker playback round-trip** (5-second test):

```bash
arecord -D plughw:1,0 -d 5 -f cd -t wav /tmp/test.wav && \
aplay   -D plughw:1,0       /tmp/test.wav
```

Replace `1` with whatever card number `arecord -l` reported. Speak normally, you should hear yourself back. If recording is silent, check the pink jack and the soldered plug. If playback is silent, check the green jack -> amp wiring and that the amp has 5 V.

Optional — set the USB card as the system default so apps use it without `plughw:` hints:

```bash
sudo nano /etc/asound.conf
```
Paste:
```
defaults.pcm.card 1
defaults.ctl.card 1
```

**Camera preview** (3 seconds, then quits):

```bash
rpicam-hello -t 3000       # Bookworm / current Pi OS
# or, on older Pi OS:
libcamera-hello -t 3000
```

You need an HDMI display connected to see the preview. For a headless check that the sensor is at least visible to the kernel:

```bash
rpicam-still -o /tmp/test.jpg --immediate
ls -lh /tmp/test.jpg
```

A non-zero JPEG file means the camera is wired correctly. A `no cameras available` error almost always means the ribbon is in backwards or not fully seated.

**Pi temperature & voltage** (run after the camera test, while everything is live):

```bash
vcgencmd measure_temp
vcgencmd measure_volts core
vcgencmd get_throttled    # re-check
```

Temp under 70 C and `throttled=0x0` after a few minutes of activity means the build is healthy.

### 6. Troubleshooting

| Symptom | Most likely cause | Fix |
|---|---|---|
| `rpicam-hello` says **no cameras available** | Ribbon inserted backwards, or not fully seated, or clip not relocked | Power off, unplug USB-C, re-seat ribbon **silver contacts toward HDMI** on the Pi end, contacts toward the PCB back on the camera end |
| Camera worked once, now dead after a re-plug | Ribbon was inserted backwards even briefly while powered — sensor likely damaged | Try the ribbon on a known-good Pi to confirm; if dead there too, replace camera |
| `arecord -l` shows only the Pi's built-in audio, no USB card | Bad USB cable on the sound card, or marginal USB port | Try another USB-A port; try a different sound card; `dmesg \| tail` will show USB enumeration errors |
| `arecord` records pure silence | Mic in **green** jack instead of pink, or mono plug soldered wrong (tip and sleeve swapped) | Move mic to **pink** jack; re-check tip vs sleeve on the soldered plug; `alsamixer` -> F4 (capture) -> raise Mic and Capture levels, unmute |
| Recording works, playback is silent | Cable in wrong jack on sound card (must be **green** for output), or amp has no 5 V | Check `aplay` plays through the USB card; confirm GPIO pin 2 actually reads ~5 V with a meter; check the amp's power LED if it has one |
| Speaker plays but very quiet / distorted | Amp running on 3.3 V instead of 5 V (wrong GPIO pin), or speaker impedance mismatch, or input is line-level into a mic input | Move VCC from pin 1/17 to **pin 2**; confirm speaker is 4 ohm not 32 ohm; lower input gain in `alsamixer` for the **playback** side |
| Speaker hisses / buzzes constantly | Ground loop between USB and GPIO grounds, or amp input floating | Tie amp `IN-` to amp `GND` if not already; keep speaker wires short; move amp away from the Pi's USB-C cable |
| `vcgencmd get_throttled` returns anything other than `0x0` | Under-voltage from a weak USB-C supply, or the amp drawing too much from the GPIO 5 V rail | Use the ecity 5 V / 3 A supply (or better); avoid powering the amp from GPIO if you're already at the edge — a separate USB battery into the amp via its VCC/GND pads works |
| Pi reboots when audio gets loud | Amp pulling current spikes through GPIO 5 V, dragging the rail down | Same fix: power the amp from its own 5 V source, or use a bigger PSU |
| IR LEDs never light up in the dark | Pigtails not seated on the camera PCB headers, or the kit's light-sensor threshold is too low | Re-seat the 2-pin connectors on the camera board; cover the lens fully to trigger the sensor |

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
