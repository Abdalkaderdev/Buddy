# Buddy — Final Project Demo Plan

**Student:** Solo developer, Erbil, Iraq
**Project:** Buddy — an AI companion robot that speaks Iraqi Arabic
**Hardware:** Raspberry Pi 4, ~$31 in parts from ecity-iq.com
**Repo:** https://github.com/Abdalkaderdev/Buddy
**Demo length:** 5 minutes live + slides + Q&A

---

## 1. Five-Minute Demo Script (minute by minute)

### Minute 0:00 – 0:45 — Cold open, no slides
- **Show:** Walk on stage holding Buddy. Place it on the table. Camera light blinks. Buddy says *(in Iraqi Arabic)*: "Hala, shlonak? Ani Buddy." ("Hi, how are you? I'm Buddy.")
- **Say:** "This is Buddy. It's a companion robot I built for $31. It speaks Iraqi Arabic — not Modern Standard, not Egyptian — *Iraqi*. Let me show you what it can do."
- **If it breaks:** Say "Buddy is shy today" and immediately pull out your phone, connect to the hotspot you pre-staged, and open the web UI. Type the same greeting. Move on.

### Minute 0:45 – 1:45 — Mode 1: Study helper (English switch)
- **Show:** Say to Buddy in Arabic: "Buddy, switch to English. Help me understand recursion." Buddy switches mid-sentence, explains recursion in 2 sentences using a simple example (e.g., Russian nesting dolls).
- **Say:** "It runs Whisper for speech-to-text on the Pi itself. The brain is Claude Haiku 4.5. Voice out is ElevenLabs — the Laura voice. The interesting part isn't the models — it's that this is one system that hears, thinks, and speaks in the language *I* grew up with."
- **If it breaks:** Switch to the phone web UI. Type the question. Read the response out loud yourself.

### Minute 1:45 – 2:45 — Mode 2: Comedy companion (cultural identity moment)
- **Show:** Switch back to Arabic. "Buddy, tell me a joke about Erbil traffic." Buddy delivers a local-flavored joke. Audience laughs (you've tested this joke 20 times — you know it lands).
- **Say:** "ChatGPT can do this in English. It cannot do it like *this* — with the rhythm of how we actually talk in Kurdistan. That's the gap I'm filling."
- **If it breaks:** Have one pre-recorded joke clip ready on your phone. Play it. Say "the API is slow today, here's what it sounds like."

### Minute 2:45 – 3:45 — Mode 3: Supportive friend + face presence
- **Show:** Walk away from Buddy. Camera detects no face — Buddy goes quiet. Walk back. Buddy notices you and says (Arabic): "Rja'et? Kunit mishtaqlak." ("You're back? I was missing you.")
- **Say:** "The camera isn't doing face *recognition*. It's doing face *presence*. Buddy doesn't know who you are — it just knows someone is there. That's a privacy choice."
- **If it breaks:** Manually trigger the "returned" event from the web UI. You'll have a button wired for exactly this.

### Minute 3:45 – 4:30 — Share the network
- **Show:** Open phone, scan a QR code on the projector. It opens `https://buddy.local:8080`. Hand your phone to the professor or front-row student. They type a question. Buddy answers out loud.
- **Say:** "Anyone on the same WiFi can talk to Buddy from their phone. No app install. No account. It's a local service."
- **If it breaks:** Have a second phone already connected and tested. Hand that one instead.

### Minute 4:30 – 5:00 — Close
- **Say:** "Buddy cost me $31 in parts. It runs in a city where most AI products don't speak our language. The code is on GitHub. Thank you."
- **Show:** Bow slightly. Don't touch Buddy again — let it sit there as proof while you go to slides/Q&A.

---

## 2. Killer Moments (the things people will remember)

1. **The first Arabic sentence.** The moment a robot speaks Iraqi dialect in a university lecture hall is the entire pitch. Make it the first 10 seconds.
2. **The local joke about Erbil.** Cultural specificity hits harder than any technical metric. If the room laughs, you've won.
3. **"Rja'et? Kunit mishtaqlak."** A robot noticing you came back and saying it missed you — in your own language — is emotionally disarming. This is the moment a professor remembers six months later.
4. **Handing the phone to the professor.** Shifting control to the audience proves it's real, not a video. It also makes them a participant, not a judge.
5. **The price tag.** Saying "$31" out loud after a 5-minute demo reframes the whole project from "student toy" to "actually shippable."

---

## 3. Failure Plan

| Failure | Detection | Response |
|---|---|---|
| **WiFi dies in the hall** | Pi can't reach Claude/ElevenLabs API | Switch to phone hotspot (pre-configured on Pi as backup SSID). Practice the switch in under 15 seconds. |
| **API key revoked / rate limited** | Buddy goes silent after STT | Have a second API key in a `.env.backup` file. SSH in from phone, `cp .env.backup .env`, restart service. Or fall back to backup video. |
| **Pi hangs / overheats** | No LEDs, no response | Hard reboot (pull power, replug). Takes ~40s to come back. Fill time by talking through the architecture slide. If still dead after 2 min, switch to backup video. |
| **Mic doesn't pick up** | Whisper returns empty | Use the web UI text input on your phone. Tell the audience: "I'll type instead — same backend." This is actually a *feature* demo, not a failure. |
| **ElevenLabs is slow (>5s)** | Long pause before TTS | Have local `espeak` fallback wired in. Say "switching to offline voice" — shows engineering depth. |
| **Camera doesn't detect face** | Presence demo dead | Skip it. Move to the phone hand-off moment instead. Don't draw attention to what's missing. |
| **Total system death** | Nothing works | **Backup video: REQUIRED.** Record a clean 3-minute walkthrough the night before. Have it on your laptop, your phone, and a USB stick. If everything fails: "Live demos are hard — here's a recording from yesterday, and I'm happy to debug live during Q&A." This is graceful, not embarrassing. |

**Pre-stage checklist:**
- Phone hotspot SSID/password memorized
- Backup `.env.backup` file on Pi
- Backup video on laptop + phone + USB
- Second phone already paired with Buddy's UI
- QR code printed on paper (not just on the slide) in case projector fails

---

## 4. Slides Outline (10 slides)

1. **Title** — "Buddy: an AI companion that speaks Iraqi Arabic." Your name, university, date. One photo of Buddy.
2. **The problem** — Voice AI exists. It doesn't speak how we speak. Show a screenshot of ChatGPT failing to do Iraqi dialect properly vs Buddy doing it right.
3. **What Buddy is** — One sentence. Three modes (comedy / study / supportive). Hardware photo with $31 price tag.
4. **Why it matters here** — Erbil context. Bilingual reality (Arabic + Kurdish + English code-switching). No corporate product serves this. One sentence on cultural identity.
5. **Architecture diagram** — Mic → Whisper (on Pi) → Claude Haiku 4.5 → ElevenLabs → Speaker. Camera → presence detection. Web UI as parallel input path. Keep it one image.
6. **Hardware** — Photo of parts laid out. Pi 4, mic, speaker, camera, case. Sourced from ecity-iq.com. Total: $31.
7. **Live demo** — Just the word "DEMO." Do the demo. Don't read slides.
8. **What was hard** — Three bullets: (a) getting Iraqi dialect to feel natural, not MSA; (b) latency budget on a Pi 4; (c) making the web UI work on phones over local HTTPS with self-signed certs.
9. **What I learned** — One paragraph. Honest. Pick something real (e.g., "Whisper's accuracy on Iraqi dialect drops 30% vs MSA — I had to tune prompts to compensate").
10. **What's next** — Kurdish (Sorani) support. Offline LLM fallback. Open-source the dialect prompts so other students can build for their languages. Repo link + QR code.

*Optional slides 11–12 if time permits: cost breakdown table, and a "thank you" with contact.*

---

## 5. One-Page Report Outline

| Section | One-line description |
|---|---|
| **Abstract** | What Buddy is, who it's for, why it's different — in 3 sentences. |
| **Motivation** | Voice AI doesn't serve Iraqi Arabic speakers. This project closes that gap on $31 of hardware. |
| **System Design** | Pipeline: STT (Whisper) → LLM (Claude Haiku 4.5) → TTS (ElevenLabs Laura). Web UI over local HTTPS. Camera for presence. |
| **Hardware** | Pi 4 + mic + speaker + camera + case. Bill of materials with prices from ecity-iq.com. |
| **Software Stack** | Python service, FastAPI web UI, systemd for autostart. Repo on GitHub. |
| **Cultural & Language Layer** | How Iraqi dialect is achieved via system prompts + voice selection. Why this matters locally. |
| **Evaluation** | Latency measurements (mic-to-speech end-to-end). Informal user tests with N friends/family. |
| **Limitations** | API dependency, no offline mode yet, dialect accuracy varies, no Kurdish yet. |
| **Future Work** | Sorani Kurdish, offline LLM, open dialect prompt library. |
| **References** | Whisper paper, Claude docs, ElevenLabs docs, Reachy Mini hardware references. |

---

## 6. Q&A Prep — Tough Questions

**Q1: How much did this cost, really? Including your time?**
> Parts: $31 from ecity-iq.com. API costs during development: roughly $15 over a month. My time: about 80 hours over four weeks. The point of the project isn't that it's cheap to build — it's that it's cheap to *deploy*, so anyone in Erbil could replicate it.

**Q2: Did you build the language model?**
> No. I'd be lying if I said I did. The LLM is Claude Haiku 4.5 from Anthropic. What I built is the system around it: the voice pipeline, the dialect prompting, the hardware integration, the web UI, the mode-switching logic, and the cultural layer. The novelty is the integration and the language target, not the model.

**Q3: How is this different from just using ChatGPT on a phone?**
> Three real differences. One: Buddy speaks Iraqi Arabic by default — ChatGPT speaks MSA and sounds like a news anchor. Two: Buddy is a physical presence in a room, not an app you open. Three: it's shared — anyone on the WiFi can talk to it without an account. ChatGPT is a personal tool; Buddy is a household one.

**Q4: What about privacy? You're sending voice to Anthropic and ElevenLabs.**
> Yes, audio leaves the device for STT-to-LLM-to-TTS. I'm honest about that. Two design choices reduce harm: the camera does presence detection only — no face recognition, no identity — and there's no account system, so there's nothing tying a conversation to a person. The next version targets fully on-device inference to remove the network dependency entirely.

**Q5: Does it scale? What if 100 people in a dorm use it?**
> Buddy is designed as a *single shared device*, not a service. The web UI handles concurrent users on the same WiFi, but they all share one voice output, so the natural cap is one conversation at a time. That's intentional — it behaves like a person, not a server.

**Q6: Why a Raspberry Pi instead of just an app?**
> Because presence matters. A robot on the table changes how you interact with it — you talk to it differently than you talk to your phone. The Pi is the cheapest way to make Buddy a *thing in the room* rather than another notification source.

**Q7: What's the most original part of this project?**
> The dialect layer and the assumption that the *default* language is Iraqi Arabic, not English with Arabic as an afterthought. Every off-the-shelf voice assistant treats non-English as a setting. Buddy treats Iraqi Arabic as the starting point. That's a small technical change with a big cultural consequence.

**Q8: What would you do differently if you started over?**
> I'd build the offline fallback path first instead of last. Cloud APIs work great until WiFi drops, and in Erbil that happens more than I'd like. Starting with a small local model and adding cloud as the *upgrade* would have been the more honest architecture.

**Q9 (bonus): Why ElevenLabs Laura specifically?**
> I tested seven voices with Arabic speakers in my family. Laura had the warmest tone and the least "robotic vowel" problem on Arabic phonemes. It was a listening choice, not a benchmark choice.

**Q10 (bonus): Could a child use this safely?**
> Not yet. There's no content filter beyond what Claude provides out of the box, and there's no parental control. I'd want to add a "kid mode" with stricter prompts and a logging option for parents before I'd hand it to a 7-year-old.

---

## 7. Polish Checklist — Final 24 Hours

### The night before (T-18h)
- [ ] Record the 3-minute backup demo video. Save to laptop, phone, USB stick.
- [ ] Fully charge: Pi power bank (if used), laptop, both phones, backup phone hotspot.
- [ ] Verify `.env` has working API keys. Copy to `.env.backup` with second key.
- [ ] Test full pipeline end-to-end three times in a row. If any run fails, fix before sleeping.
- [ ] Push final code to GitHub. Tag the commit `v1.0-demo`. Verify the repo loads on someone else's browser.
- [ ] Take 5 clean screenshots (web UI, architecture, hardware close-up, terminal logs, GitHub repo).
- [ ] Print the QR code for `https://buddy.local:8080` on paper. Two copies.
- [ ] Restart the Pi cleanly. Let it reach steady state. Confirm systemd service is `active`.
- [ ] Kill any zombie Python processes: `ps aux | grep python` then clean up.
- [ ] Free up disk space on Pi. Clear logs older than 7 days.

### Morning of (T-4h)
- [ ] Reboot Pi one more time. Verify autostart works without you logging in.
- [ ] Test mic in a quiet room and a noisy room. Adjust gain if needed.
- [ ] Test the joke about Erbil traffic on a family member. If they don't laugh, swap it.
- [ ] Pack: Pi + power + mic + speaker + camera + HDMI cable + USB cable + ethernet cable (backup) + power strip + the printed QR codes + USB stick + a notebook + a pen.
- [ ] Pre-connect both phones to the venue's WiFi if possible, or to your hotspot.
- [ ] Eat. Drink water. Don't demo hungry.

### One hour before (T-1h)
- [ ] Arrive early. Plug in. Boot up. Do one full silent test run.
- [ ] Open the web UI on the demo phone. Leave it open.
- [ ] Close every unnecessary tab and app on your laptop. Disable notifications.
- [ ] Put laptop on "Do Not Disturb." Silence phone notifications.
- [ ] Confirm projector resolution matches your slides.
- [ ] Have the backup video open in a tab, ready to play in one click.
- [ ] Take a breath. You built this in a month. It works. Go.

### Five minutes before (T-5min)
- [ ] Power-cycle Buddy one last time so it's freshly booted when you start.
- [ ] Speak the first Arabic line out loud to yourself to warm up your voice.
- [ ] Smile. Walk in.

---

*Built with care in Erbil. Repo: https://github.com/Abdalkaderdev/Buddy*
