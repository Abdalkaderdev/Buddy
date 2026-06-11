# Buddy

A small AI study companion that also sits with you when you're stressed. Runs on a Raspberry Pi 4. The hardware costs about $31 from a shop in Erbil.

I built this because I got tired of opening ChatGPT alone at 2 AM during finals and getting a tab full of generic American self-help. Buddy speaks Iraqi Arabic by default, switches to English when I do, and doesn't pretend to be a therapist.

> Buddy is **not** a therapist. It listens, suggests a grounding technique if it helps, and points at a real human (number in [`RESOURCES.md`](./RESOURCES.md)) when something is bigger than a chatbot.

```
┌──────────────────────────────────────────────────────────────┐
│  STUDENT ─────────►  Buddy  ◄──────────── ANYONE ON WIFI     │
│   speaks               │                    chats via browser │
│   (mic)                │                                      │
│                        ▼                                      │
│              ┌──────────────────┐                            │
│              │  Raspberry Pi 4  │                            │
│              │  • USB mic       │                            │
│              │  • Fisheye cam   │                            │
│              │  • Mono speaker  │                            │
│              └──────────────────┘                            │
│                        │                                      │
│                        ▼                                      │
│              voice + face presence                            │
│                        │                                      │
│                        ▼                                      │
│                  Claude API                                   │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## Why I built this

A therapy visit in Erbil is around $5. That sounds cheap until you realize a lot of students can't spare it, and a lot more won't go anyway because the family doesn't take "anxiety" seriously. For women the stigma is worse. So most people I know just don't talk to anyone, ride it out, fail an exam, sleep badly for a month.

Buddy isn't a fix. It's just something that's awake at 3 AM when the rest of your phone is depressing and your friends are asleep. It can:

- Explain a hard concept in plain words (Iraqi Arabic if you want).
- Listen when you're spiraling and walk you through a 60-second breathing thing.
- Notice when the conversation got serious and tell you, clearly, "this is bigger than me, please call someone" — with a real verified number from [`RESOURCES.md`](./RESOURCES.md).

That's it. No "your mental health journey." No emojis.

## What Buddy does

> The robot's spoken persona is named **Sara (سارة)** — "Buddy" is the project name.

- **Standalone voice mode (new):** talk to the robot directly — USB mic in, speaker out, no browser, no phone. Runs at boot as `sara-standalone.service`. Sara also *sees*: a camera frame goes to Claude with each turn, so "what am I holding?" works.
- Listens (browser mic on your phone, or USB mic on the Pi).
- Sees that someone is in front of it, not who. The camera reports "person here" or "empty room" and that's all that leaves the Pi.
- Thinks using Claude Haiku 4.5 with a system prompt I rewrote a dozen times to stop it from sounding like an AI.
- Talks back using ElevenLabs (or Edge TTS as a free fallback). Iraqi Arabic default, switches to English mid-sentence if I do.
- Works from any device on the same WiFi. No app install. Phone, laptop, an iPad if you have one.

### The two modes (it picks by reading the room)

| Mode | What happens |
|---|---|
| Study | Explains the idea in one line, breaks it into 2–3 steps, gives an analogy from daily life here (chai cooling, the bakery line, traffic on 100m Road), then quizzes you back. |
| Support | Reflects what you said first, no fix-it reflex, asks one open question. Offers a grounding thing only if you keep talking. No jokes when you're hurting. |

There's also a hard safety hand-off: if you say something that suggests crisis, Buddy stops being clever, says it isn't the right helper, and gives you the ambulance number (122) plus Jiyan Foundation in Erbil (066 264 7979). Those numbers are verified by hand, not scraped.

## What makes Buddy different from "just use ChatGPT"

1. Iraqi Arabic by default. Not MSA, not Khaliji, not Egyptian. The way you actually talk.
2. Knows local resources. The numbers in [`RESOURCES.md`](./RESOURCES.md) are Erbil-specific and double-checked.
3. Runs on a $31 Raspberry Pi I bought from ecity-iq. No subscription, no account, no app store.
4. Voice-first. You don't have to type when you're already exhausted.
5. The camera does presence detection on the Pi. No images leave the device, ever. Only the text of what you said gets sent to Claude. No audio recording, no who-you-are, no log file.

## Hardware — about 40,000 IQD ($31)

I sourced everything locally at [ecity-iq.com](https://ecity-iq.com/). Full list with direct links and prices is in [`buddy_electronics_shopping_list.docx`](./buddy_electronics_shopping_list.docx).

| Part | Price |
|---|---|
| Raspberry Pi 4 B (already had it) | — |
| Pi 4 USB-C 5V power supply | 5,500 IQD |
| Night Vision Fisheye Camera 5MP 160° | 25,000 IQD |
| USB sound card + mini mic | 3,500 IQD |
| Mono 5W amp board | 1,250 IQD |
| Harman Kardon 1.5" 40mm 4Ω speaker | 5,000 IQD |
| Total | ~40,250 IQD |

Wiring instructions are in [`apps/buddy/README.md`](./apps/buddy/README.md). I broke a camera ribbon once doing this, so I added pinout warnings throughout.

## Run it on your laptop first (no Pi needed)

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

Open <http://localhost:8080> in Chrome or Edge. Tap the mic. Talk.

## Run it on the Pi

After flashing Raspberry Pi OS 64-bit with WiFi + SSH from the Imager:

```bash
ssh pi@buddy.local
curl -L https://raw.githubusercontent.com/Abdalkaderdev/Buddy/main/apps/buddy/scripts/setup_pi.sh | bash
echo "ANTHROPIC_API_KEY=sk-ant-..." > ~/.buddy.env
chmod 600 ~/.buddy.env
systemctl --user restart buddy.service
```

Open `http://buddy.local:8080` from any device on the same WiFi.

If you want remote access from anywhere (uni WiFi, phone hotspot, your friend's house), install Tailscale on the Pi and on your phone. The Pi gets a 100.x.x.x IP that works everywhere the Pi has internet.

Full hardware wiring is in [`apps/buddy/README.md`](./apps/buddy/README.md).

## Ethics + safety (I have to put this here)

I'm a student, not a clinician. Building anything that sits in front of someone at a bad moment is a real responsibility. The rules I gave myself:

- Buddy says "I'm not a therapist" out loud the moment it matters.
- Any signal of self-harm or acute danger triggers a hand-off with a real phone number and a strong push to call a human. No improvising.
- Every hotline in `RESOURCES.md` was checked by hand. If I couldn't verify it, I marked it `[VERIFY before using]` instead of inventing one.
- Privacy is the default. The Pi stays on your WiFi. Only the text of your sentence goes to Claude. No camera frames leave the box. No audio is stored. There's no account.
- I don't log conversations or send them anywhere for model training.

If any of this breaks, I'd rather hear about it on a GitHub issue than find out from a news article.

## Project layout

```
.
├── README.md                              # this file
├── RESOURCES.md                           # verified Iraq/Kurdistan crisis lines
├── KNOWLEDGE.md                           # grounding techniques + study methods (sourced)
├── USE_CASES.md                           # examples of what to ask Buddy
├── SAFETY_TESTS.md                        # adversarial phrases to run before demo
├── DEMO_DAY.md                            # one-page demo reference
├── DEMO_PLAN.md                           # 5-minute demo script + Q&A
├── SLIDES.md                              # 12-slide presentation, Marp-compatible
├── HANDOFF.md                             # context dump for the next dev session
├── apps/buddy/                            # the app
│   ├── README.md                          # hardware build + dev guide
│   ├── pyproject.toml
│   ├── scripts/setup_pi.sh                # one-shot Pi installer
│   └── buddy/
│       ├── server.py                      # FastAPI + WebSocket
│       ├── ai.py                          # Claude / Ollama
│       ├── audio.py                       # Whisper STT + Edge TTS
│       ├── vision.py                      # OpenCV face presence
│       ├── motion.py                      # optional Reachy Mini motors
│       ├── config.py                      # personality + safety prompts
│       └── static/                        # web UI
├── scripts/make_shopping_list.py
└── buddy_electronics_shopping_list.docx
```

## Configuration

Edit [`apps/buddy/buddy/config.py`](./apps/buddy/buddy/config.py):

| Setting | Default |
|---|---|
| `LLM_PROVIDER` | `"claude"` (or `"ollama"` for fully local) |
| `CLAUDE_MODEL` | `claude-haiku-4-5-20251001` |
| `SYSTEM_PROMPT` | the Buddy personality + safety + Iraqi vocab rules |
| `TTS_VOICE` | Iraqi Arabic default, switches to English when the student does |
| `VOICES` | 12 edge-tts voices, 4 dialects, used as fallback |

Server env vars:

| Var | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Claude key |
| `ELEVENLABS_API_KEY` | optional; if set, uses ElevenLabs Turbo v2.5 |
| `ELEVENLABS_VOICE_ID` | which ElevenLabs voice (default: Laura) |
| `BUDDY_CAMERA` | `0` to disable camera presence detection |
| `BUDDY_CAMERA_INDEX` | which `/dev/videoN` to use (default 0) |
| `BUDDY_SSL_CERT` / `BUDDY_SSL_KEY` | paths to a self-signed cert for HTTPS (needed for mic in browser) |

## License

MIT. Use it, fork it, write your own version for your own city.
