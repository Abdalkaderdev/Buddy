# Buddy Project — Handoff for the Next AI Session

You (the next Claude session) are picking up where the previous one left off.
Read this file **first**, then `plan.md`, then `apps/buddy/README.md`.
This file is the only source of truth for what already happened and what's pending.

---

## 👤 User context

- **Name:** Abd / Abdalkader (GitHub: [@Abdalkaderdev](https://github.com/Abdalkaderdev))
- **Location:** Erbil, Iraq
- **Background:** University project — interactive AI companion robot
- **Timeline:** ~1 month deadline (as of the original `plan.md`)
- **Working environment:** Windows 11, PowerShell, uv for Python venvs
- **Speaks:** English + Arabic (Iraqi dialect specifically — voice picker has it)
- **Working style:** Likes concrete clickable links, hates over-explanation, wants me to **do things** not lecture. Move fast, fix bugs, only ask questions when truly blocked.

---

## 🎯 What Buddy is

An AI companion that listens (voice in), sees (face detection), thinks (Claude Haiku 4.5),
and talks back (Edge TTS). Originally planned as a full Reachy Mini build with 9
Dynamixel motors, **but the no-motor Pi-only build was chosen** because Dynamixels are
expensive and not available in Iraq.

The repo started as a fork of [pollen-robotics/reachy_mini](https://github.com/pollen-robotics/reachy_mini)
(the official Reachy Mini SDK). The user's app is in `apps/buddy/`. Everything else
in the repo is upstream Reachy Mini code we kept "just in case" — they may order the
Reachy Mini Wireless kit ($449) later, in which case the motion code activates.

---

## ✅ What's done

### Repo
- Root `README.md` rewritten to be Buddy-focused (was the upstream HuggingFace one)
- `apps/buddy/README.md` rewritten — hardware build + wiring guide
- `apps/buddy/scripts/setup_pi.sh` — one-shot Pi installer with systemd service
- `scripts/make_shopping_list.py` — generates the `.docx` parts list
- `buddy_electronics_shopping_list.docx` — single-page shopping list with ecity links
- `plan.md` updated to reflect Ollama-default decision (later overridden to Claude)
- Personal context lives in `agents.local.md` — **gitignored, won't be on new machine**

### Code (`apps/buddy/buddy/`)
- `server.py` — FastAPI + WebSocket web UI on port 8080
  - Voice-only mic UI (no chat input), Web Speech API in browser
  - `/api/transcribe` Whisper endpoint (alternative for the Pi)
  - `/api/camera-state` debug endpoint
  - Background thread polls USB webcam → OpenCV face detection → injects context into Claude prompts
  - Graceful fallback if no Reachy Mini robot is connected
- `ai.py` — Claude Haiku 4.5 default (`claude-haiku-4-5-20251001`), Ollama fallback
- `audio.py` — Whisper STT (lazy load) + Edge TTS
- `vision.py` — OpenCV face detector + SQLite face DB (`face_recognition` optional extra)
- `motion.py` — Reachy Mini motion (no-op without robot)
- `config.py` — punchy comedy SYSTEM_PROMPT, 12 voices (en + ar dialects), TTS defaults
- `static/index.html`, `main.js`, `style.css` — voice-only web UI with auto-listen-after-reply

### GitHub
- Repo pushed to **https://github.com/Abdalkaderdev/Buddy** (main branch)
- `.gitignore` excludes `.claude/`, `agents.local.md`, `apps/buddy/buddy/data/faces.db`
  (cached API keys, personal context, face embeddings)

### Hardware (ORDERED from ecity-iq.com on the date of the previous session)
- Total: ~40,250 IQD (~$31)
- All sourced locally in Erbil — see `buddy_electronics_shopping_list.docx`
- Items: Pi 4 USB-C power supply, Night Vision Fisheye 5MP 160°, USB sound card,
  mini mic, mono 5W amp board, Harman Kardon 1.5" 40mm 4Ω speaker
- **Status: ordered, awaiting delivery (~3-7 days)**

### Raspberry Pi
- User has Pi 4 Model B
- SD card flashed with **Raspberry Pi OS 64-bit Trixie (Debian 13)**
- Initial WiFi config was for `"Abd's Iphone"` hotspot — failed because iOS replaces
  straight apostrophes with curly ones. Reflashed for `Real House` (home/office WiFi).
- Pi boots, connects to "Real House", IP `192.168.10.157` on the previous session's
  network. **This IP will change at the user's home.** Use `ping buddy.local` to rediscover.
- SSH: `pi@buddy.local`, password `buddy1234`, **passwordless sudo enabled**
- Buddy install via `setup_pi.sh` was IN PROGRESS when the previous session ended —
  may have completed by the time you (next session) start. Check with:
  ```bash
  ssh pi@buddy.local 'systemctl --user status buddy.service'
  ```

---

## ⚠️ Critical things to know

### 1. The Anthropic API key was leaked
The previous session was given an API key (`sk-ant-api03-pd…AA` — full value was in chat
history, intentionally redacted here). The user said they would revoke it.

**On your first turn: confirm with the user whether they've revoked it.** If not,
remind them to revoke now at https://console.anthropic.com/settings/keys and create a
fresh one. Store the fresh key in a Windows env var:
```powershell
setx ANTHROPIC_API_KEY "sk-ant-..."
```
And on the Pi:
```bash
echo "ANTHROPIC_API_KEY=sk-ant-..." > ~/.buddy.env
chmod 600 ~/.buddy.env
systemctl --user restart buddy.service
```

The key was caught in `.claude/settings.local.json` as part of cached bash commands —
that's now gitignored and won't push, but it's still on the previous laptop's disk.

### 2. The Pi was configured for "Real House" WiFi
If the user takes the Pi home to a different WiFi, the Pi won't connect until either:
- Home WiFi is renamed to "Real House" with password "Tareq5822" (unlikely), OR
- The SD card is re-flashed with the home WiFi creds, OR
- A USB keyboard + HDMI monitor is plugged into the Pi to manually fix
  `/etc/NetworkManager/system-connections/preconfigured.nmconnection`

The user mentioned they wanted to keep the Pi on company WiFi. **Ask them which
network the Pi is on now** before assuming `buddy.local` will resolve.

### 3. SSH key auth is set up from the OFFICE laptop, NOT the home laptop
The previous session copied `~/.ssh/id_ed25519.pub` from the office machine to the Pi's
`authorized_keys`. On the home laptop the user will need to:
```bash
# Option A: copy the key from the office laptop (if accessible)
# Option B: regenerate and re-install:
ssh-keygen -t ed25519     # if no key exists yet
ssh-copy-id pi@buddy.local
# password is buddy1234
```

### 4. The repo is a 105 MB fork of pollen-robotics/reachy_mini
Cloning is slow on first try. Use `--depth 1` for a faster shallow clone:
```bash
git clone --depth 1 https://github.com/Abdalkaderdev/Buddy.git
```

### 5. Hardware hasn't arrived yet (as of the previous session)
The user can develop on the laptop with the laptop's built-in webcam and speakers.
The Pi works fine for chat without any sensors connected — the camera thread just
errors quietly and Buddy falls back to "no face detected" context.

---

## 📋 Pending tasks

In order of importance:

1. **Verify Buddy is installed on the Pi.**
   `ssh pi@buddy.local 'systemctl --user status buddy.service'`
   If not installed, run:
   `ssh pi@buddy.local 'bash /tmp/setup_pi.sh'` (or re-download)
2. **Add the new API key to the Pi** (`~/.buddy.env`)
3. **Test http://buddy.local:8080** from the user's phone/laptop. Mic + voice loop.
4. **When hardware arrives:** wire it up per `apps/buddy/README.md` § Wiring,
   reboot the Pi, test the camera (`libcamera-hello` or `/api/camera-state`) and
   the speaker (`speaker-test -t sine`).
5. **Polish for university demo:**
   - Personalize `SYSTEM_PROMPT` in `config.py` (the user wanted Iraqi-flavored humor)
   - Plan demo script (5-min presentation)
   - Record video backup in case the Pi acts up on demo day
6. **(Optional)** Order the Reachy Mini Wireless kit ($449) from Seeed Studio or
   Hugging Face if the user wants the real robot. ~90 day lead time.

---

## 🛠️ Useful runbook entries

### Reach the Pi
```bash
ping buddy.local                           # discovery
ssh pi@buddy.local                         # SSH in (key-based)
ssh pi@buddy.local 'systemctl --user status buddy.service'
ssh pi@buddy.local 'journalctl --user -u buddy.service -f'
```

### If `buddy.local` doesn't resolve
```bash
# Try IP scan on common subnets (adjust to user's network)
for i in $(seq 2 254); do ping -n 1 -w 200 192.168.1.$i > /dev/null && echo "192.168.1.$i UP" & done; wait
arp -a | grep 'd8-3a-dd'    # Raspberry Pi Foundation OUI prefix
```

### Update Buddy code on the Pi after pushing to GitHub
```bash
ssh pi@buddy.local 'cd ~/reachy_mini && git pull && systemctl --user restart buddy.service'
```

### Develop locally on the user's laptop
```bash
cd ~/reachy_mini                            # wherever they cloned it
.venv/Scripts/python -m buddy.server        # Windows
.venv/bin/python -m buddy.server            # macOS / Linux
# then open http://localhost:8080
```

The laptop venv at `C:/Users/max/reachy_mini/.venv` already had everything installed
on the previous session's machine. On a fresh laptop clone, recreate with:
```bash
python -m venv .venv
.venv/Scripts/activate
pip install -e ./apps/buddy
pip install anthropic edge-tts fastapi uvicorn opencv-python python-multipart \
            faster-whisper websockets paramiko
```

---

## 🎙️ Architecture summary

```
                                  ┌────────────────────────────┐
   ┌─────────┐    HTTP/WS         │  Pi 4 B running buddy.svc  │
   │ Browser ├────────────────────┤  port 8080 (FastAPI)       │
   │ (phone) │                    │                            │
   └─────────┘                    │  ┌────────┐  ┌─────────┐   │
                                  │  │ ai.py  │  │vision.py│   │
                                  │  │Claude  │  │OpenCV   │   │
                                  │  │Haiku4.5│  │face det.│   │
                                  │  └────────┘  └─────────┘   │
                                  │  ┌────────────────────┐    │
                                  │  │ audio.py edge-tts  │    │
                                  │  └────────────────────┘    │
                                  └────────────────────────────┘
                                          │            │
                                       USB mic       USB speaker
                                       + Pi cam      (via amp)
```

The frontend uses **browser Web Speech API** (Chrome/Edge only) for STT in the dev
flow. `/api/transcribe` exists as a fallback using on-device Whisper for when the
user wants offline operation. The frontend doesn't use Whisper by default.

---

## 🔄 Decision log (so you don't reopen settled questions)

| Decision | What we picked | Why |
|---|---|---|
| LLM provider | **Claude Haiku 4.5** | Cheap, fast, good at personality. Ollama kept as fallback (config.py `LLM_PROVIDER`) |
| Voice in | **Browser Web Speech API** | Free, instant, no model loading. Whisper available server-side for Pi |
| Voice out | **Edge TTS** | 12 voices, free, Arabic dialects supported. Connor (Irish) is default |
| Robot platform | **Pi 4 B (no motors)** | Dynamixels not available in Iraq, too expensive. User may add the $449 Reachy Wireless kit later |
| Repo strategy | **Single fork of pollen-robotics/reachy_mini** | Keep upstream SDK for the future Reachy purchase. App in `apps/buddy/` |
| Hardware source | **ecity-iq.com (Erbil)** | Local, fast delivery, prices in IQD |
| Speaker pick | **Harman Kardon 1.5" 40mm 4Ω 3W (5,000 IQD)** | Best driver in stock at ecity |
| Power supply | **Pi 4 USB-C 5V 5,500 IQD** (NOT the 17,000 IQD Pi 5 supply) | Pi 4 only draws ~3A |
| Pi WiFi | **"Real House" / Tareq5822** | iPhone hotspot path failed (curly apostrophe) |
| Pi SSH | **password `buddy1234` + my ed25519 key + NOPASSWD sudo** | Set up on first boot |
| Pi OS | **Debian 13 (Trixie) 64-bit** | What Imager defaulted to |

---

## 🚨 Open issues / known gotchas

1. **`raw.githubusercontent.com` caches files for ~5 min.** When the user pushes a
   commit and tries to curl the raw file on the Pi, they may get a stale version.
   Workaround: use the GitHub API (`https://api.github.com/repos/.../contents/...`)
   or SCP from the laptop directly.
2. **The user's iPhone hotspot rewrites straight apostrophes to curly.** Avoid SSIDs
   with apostrophes in any Pi config.
3. **`libatlas-base-dev` doesn't exist on Trixie.** Replaced with `libopenblas-dev`.
   Already fixed in `setup_pi.sh`.
4. **`libcamera-apps` renamed to `rpicam-apps`** in Bookworm 2023+. Already fixed.
5. **`face_recognition` requires dlib which needs cmake** — install fails on Pi
   without it. It's an optional `[recognition]` extra, not a hard dep.
6. **The browser mic UI requires Chrome or Edge.** Firefox's Web Speech API is broken.
7. **The dev setup on the previous laptop is gone** (the user is moving to a different
   machine). They need to clone the repo + recreate the venv on the home laptop.

---

## 📞 First message template you can send the user

When the new session starts, lead with something like this (adapt to context):

> Welcome back. I've read HANDOFF.md. Quick checklist before we continue:
>
> 1. Did you revoke the old Anthropic API key and create a new one?
> 2. Where is the Pi physically right now — same network as before, or moved?
> 3. Has the ecity hardware order arrived?
>
> Once I know those, I'll either: verify Buddy is running on the Pi, help you wire
> the new parts, or work on the demo personality / script — your call.

---

Last updated: end of the previous session on the office laptop, before moving to home.
