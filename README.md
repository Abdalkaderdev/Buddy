# Buddy

**An AI study companion and mental health support presence for university students — built on a Raspberry Pi 4 for about $31.**

Buddy is a voice-first, Iraqi-Arabic-by-default companion designed for university students in Erbil, Iraq. It listens, helps with hard coursework, and offers a warm, judgment-free presence when stress, loneliness, or anxiety hit at 2 AM — when no one else is awake and a therapist is out of reach.

> **Buddy is not a therapist.** It is a small, kind presence that listens, validates, suggests grounding techniques, and *always defers to a human* when a student is in crisis. Verified local crisis resources live in [`RESOURCES.md`](./RESOURCES.md).

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

## Why Buddy exists

Iraqi university students rarely get accessible mental health care. Even at the
local rate of around **$5 per therapy visit**, many students — especially women,
for whom stigma is sharper — never go. A culture that still treats anxiety and
burnout as weakness, combined with packed schedules and patchy WiFi, means most
students cope alone.

Buddy doesn't replace therapy, a friend, or a parent. It is a **warm presence
at 2 AM** that:

- Helps you understand a hard concept before tomorrow's exam, in the language you actually think in.
- Listens when you're spiraling, validates the feeling, and walks you through a 60-second grounding technique.
- Recognizes when a moment is bigger than itself, and gently hands you off to a human — a friend, a family member, or one of the verified hotlines in [`RESOURCES.md`](./RESOURCES.md).

## What Buddy does

- **Listens** — push-to-talk web mic, or USB mic on the Pi
- **Sees** — face *presence* detection (not recognition): Buddy knows someone is there, not who
- **Thinks** — Claude Haiku 4.5, with a system prompt tuned for warmth, humility, and safety
- **Talks back** — Edge TTS, Iraqi Arabic by default, switches to English mid-sentence when you do
- **Works from anything on your WiFi** — phone, laptop, tablet, no app install

### Three modes

| Mode | What it does |
|---|---|
| **Study** | Explains hard ideas simply, using analogies a student in Erbil would actually understand (the suq, traffic on 100m Road, exam season at SUE/SUH). |
| **Support** | When a student is overwhelmed: listens first, validates the feeling, offers a short grounding technique (5-4-3-2-1, box breathing). Never preachy. |
| **Safety hand-off** | If a conversation suggests crisis — self-harm, abuse, an unsafe situation — Buddy stops being clever and says, clearly, "I'm not the right helper for this. Please talk to a person." Then surfaces the right entry from [`RESOURCES.md`](./RESOURCES.md). |

## What makes Buddy different from ChatGPT

1. **Iraqi Arabic by default.** Not MSA, not Egyptian. The dialect students actually speak.
2. **Knows local crisis resources.** Verified Iraqi and Kurdistan-region hotlines and student counseling lines live in [`RESOURCES.md`](./RESOURCES.md), not buried in a generic global list.
3. **Runs on a $31 Raspberry Pi anyone in Erbil can build.** No subscription, no app store, no account.
4. **Voice-first.** A student curled up at 2 AM can talk to Buddy without typing.
5. **Private by design.** Buddy runs locally on the Pi over your WiFi. Only the text of your message goes to the LLM provider — no camera frames, no audio recordings, no identity. Face detection runs on-device and reports presence only ("someone is here" / "no one is here").

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

## Ethics & safety

Building a "mental health" tool on top of an LLM is a serious thing to do. Buddy's design assumes the LLM can be wrong and that students may turn to it in vulnerable moments. The rules:

- **Buddy is not a therapist** and never claims to be one. The system prompt makes this explicit, and Buddy will say it out loud when relevant.
- **Crisis = human, every time.** Any signal of self-harm, abuse, or acute danger triggers a hand-off script that points the student at a verified human resource from [`RESOURCES.md`](./RESOURCES.md).
- **Resources are verified, not scraped.** Every hotline and counseling number in `RESOURCES.md` is checked manually before it ships.
- **Privacy is the default.** Buddy runs on your Pi, on your WiFi. The camera does presence detection on-device — no face recognition, no images leave the Pi. Only the text of your spoken message goes to the LLM provider for a response; no audio, no video, no account, no log of who you are.
- **No data collection for training.** Buddy does not log conversations to disk by default and never sends them to a third party for model training.

## Project layout

```
.
├── README.md                              # this file
├── RESOURCES.md                           # verified Iraqi/Kurdistan crisis & support hotlines
├── DEMO_DAY.md                            # one-page demo day reference
├── DEMO_PLAN.md                           # full 5-minute demo script + Q&A
├── apps/buddy/                            # the Buddy app
│   ├── README.md                          # hardware build + dev guide
│   ├── pyproject.toml
│   ├── scripts/setup_pi.sh                # one-shot Pi installer
│   └── buddy/
│       ├── server.py                      # FastAPI + WebSocket web UI
│       ├── ai.py                          # Claude / Ollama provider
│       ├── audio.py                       # Whisper STT + Edge TTS
│       ├── vision.py                      # OpenCV face *presence*
│       ├── motion.py                      # (optional) physical motion
│       ├── config.py                      # personality + safety prompts
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
| `SYSTEM_PROMPT` | Buddy's personality, study + support + safety rules |
| `TTS_VOICE` | Iraqi Arabic by default; switches to English when the student does |
| `VOICES` | 12 voices, 4 dialects |

Env vars on the server:

| Var | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API key |
| `BUDDY_CAMERA` | `0` to disable camera presence detection |
| `BUDDY_CAMERA_INDEX` | which `/dev/videoN` to use (default 0) |

## License

MIT.
