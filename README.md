# Buddy 🤖

An open-source AI companion robot you can build at home for around **$30**.

Buddy listens, sees, and talks back — powered by Claude, running on a Raspberry Pi 4.

```
┌──────────────────────────────────────────────────────────────┐
│  YOU ────────────►  Buddy  ◄──────────── ANYONE ON YOUR WIFI │
│   speak               │                    chats via browser │
│   (mic)               │                                      │
│                       ▼                                      │
│              ┌──────────────────┐                            │
│              │  Raspberry Pi 4  │                            │
│              │  • USB mic       │                            │
│              │  • Fisheye cam   │                            │
│              │  • Mono speaker  │                            │
│              └──────────────────┘                            │
│                       │                                      │
│                       ▼                                      │
│              voice + face context                            │
│                       │                                      │
│                       ▼                                      │
│                   Claude API                                 │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## What Buddy does

- 🎤 **Listens** — push-to-talk web mic, or USB mic on the Pi
- 👁️ **Sees** — face detection on the camera feed gives Buddy live context
  ("am I alone right now?" — Buddy actually knows)
- 🧠 **Thinks** — Claude Haiku 4.5 for responses with personality
- 🔊 **Talks back** — Edge TTS with 12 voices (English + Iraqi/Egyptian/Saudi Arabic)
- 🌐 **Works from anything** — phone, laptop, tablet, all on your WiFi

## Hardware — ~40,000 IQD ($31) total

All parts sourced from [ecity-iq.com](https://ecity-iq.com/) in Erbil. Full
build with prices and direct links is in
[`buddy_electronics_shopping_list.docx`](./buddy_electronics_shopping_list.docx).

| Part | Price |
|---|---|
| Raspberry Pi 4 B (your own) | — |
| Pi 4 USB-C 5V power supply | 5,500 IQD |
| Night Vision Fisheye Camera 5MP 160° | 25,000 IQD |
| USB Sound Card + mini microphone | 3,500 IQD |
| Mono 5W amplifier board | 1,250 IQD |
| Harman Kardon 1.5" 40mm 4Ω speaker | 5,000 IQD |
| **Total** | **~40,250 IQD** |

See [`apps/buddy/README.md`](./apps/buddy/README.md) for the wiring guide.

## Quick start — laptop simulator (no Pi needed)

You can try Buddy on your laptop before any hardware arrives:

```bash
git clone https://github.com/Abdalkaderdev/Buddy.git
cd Buddy
python -m venv .venv
.venv/Scripts/activate                              # Windows
# source .venv/bin/activate                         # macOS / Linux
pip install -e ./apps/buddy
pip install anthropic edge-tts fastapi uvicorn opencv-python \
    python-multipart faster-whisper websockets

set ANTHROPIC_API_KEY=sk-ant-...                    # Windows
# export ANTHROPIC_API_KEY=sk-ant-...               # macOS / Linux

python -m buddy.server
```

Open <http://localhost:8080> in Chrome or Edge, click the purple mic, and talk.

## Quick start — on the Raspberry Pi

After flashing Raspberry Pi OS 64-bit with Wi-Fi and SSH enabled:

```bash
ssh pi@buddy.local
curl -L https://raw.githubusercontent.com/Abdalkaderdev/Buddy/main/apps/buddy/scripts/setup_pi.sh | bash
echo "ANTHROPIC_API_KEY=sk-ant-..." > ~/.buddy.env
chmod 600 ~/.buddy.env
systemctl --user restart buddy.service
```

Open `http://buddy.local:8080` from any device on the same Wi-Fi.

Full setup including hardware wiring is in [`apps/buddy/README.md`](./apps/buddy/README.md).

## Project layout

```
.
├── README.md                              # this file
├── apps/buddy/                            # the Buddy app
│   ├── README.md                          # hardware build + dev guide
│   ├── pyproject.toml
│   ├── scripts/setup_pi.sh                # one-shot Pi installer
│   └── buddy/
│       ├── server.py                      # FastAPI + WebSocket web UI
│       ├── ai.py                          # Claude / Ollama provider
│       ├── audio.py                       # Whisper STT + Edge TTS
│       ├── vision.py                      # OpenCV face detection
│       ├── motion.py                      # (optional) physical motion
│       ├── config.py                      # personality + settings
│       └── static/                        # web UI (HTML/CSS/JS)
├── scripts/make_shopping_list.py          # regenerates the .docx parts list
├── plan.md                                # original project plan
└── buddy_electronics_shopping_list.docx   # printable shopping list
```

## Configuration

Edit [`apps/buddy/buddy/config.py`](./apps/buddy/buddy/config.py):

| Setting | Default |
|---|---|
| `LLM_PROVIDER` | `"claude"` (or `"ollama"` for fully local) |
| `CLAUDE_MODEL` | `claude-haiku-4-5-20251001` |
| `SYSTEM_PROMPT` | Buddy's personality — edit to taste |
| `TTS_VOICE` | `en-IE-ConnorNeural` (Irish) |
| `VOICES` | 12 voices, 4 dialects |

Env vars on the server:

| Var | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API key |
| `BUDDY_CAMERA` | `0` to disable camera face detection |
| `BUDDY_CAMERA_INDEX` | which `/dev/videoN` to use (default 0) |

## License

MIT.
