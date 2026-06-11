# BUDDY — DEMO DAY QUICK CARD

*Erbil, University Demo. Keep this card in your pocket.*

**One-line pitch:** Buddy is an AI study companion and mental health presence for Iraqi university students, runs on a $31 Raspberry Pi, speaks Iraqi Arabic by default, and always points to a human when a student is in crisis.

---

## 1. TONIGHT (T-12 hours)

- Run the full flow at home one more time: speak to Buddy in Arabic, ask for help with a hard concept, then test the support mode by saying you're stressed about an exam. If both feel warm and real tonight, they will tomorrow.
- Test the safety hand-off once. Say a sentence like "I don't want to be here anymore." Confirm Buddy slows down, drops the cleverness, and points you to [`RESOURCES.md`](./RESOURCES.md). This must work. If it doesn't, fix it before sleeping.
- Open `https://buddy.local:8080` from your phone, on iPhone hotspot. Confirm the page loads and the mic permission works.
- Confirm your iPhone hotspot is named exactly **"Real House"** with password **"Tareq5822"** — the Pi auto-joins this SSID. One typo and nothing connects.
- Charge everything tonight: phone to 100%, laptop, Pi power bank if you're using one. Pack the USB-C cable AND a backup cable.
- Record a 60-second backup video right now — your face, you talking to Buddy in Arabic (one study question, one support reply). Save it to your phone gallery. Insurance.
- `git push` your final working code. If the Pi dies tomorrow, the work still exists.

## 2. RIGHT BEFORE THE DEMO (T-15 min)

- Turn on your phone hotspot **first** — name "Real House". Nothing else works until this is on.
- Plug in the Pi. Wait a full 60 seconds. Do not panic during boot. Drink your chai.
- From your phone, open `https://buddy.local:8080`. If it loads, you are 90% safe.
- Open Buddy in **two tabs**: one for you to drive, one ready to hand to the professor.
- Hard refresh both tabs (Ctrl+Shift+R / long-press reload on iPhone).
- Accept the HTTPS certificate warning ("Advanced" → "Proceed"). Allow microphone access.
- Run a 3-shot smoke test: one Arabic study question, one English study question, one short "I'm stressed" line. If all three respond warmly and clearly, you are ready.
- Have `RESOURCES.md` open in another tab — you may want to show it during the safety moment.
- Breathe. The engineering is done. Now you just talk.

## 3. IF SOMETHING BREAKS

| Symptom | Cause | Fix in 30 sec | Last resort |
|---|---|---|---|
| `buddy.local` won't resolve | mDNS not up / wrong WiFi | Use Pi's IP directly (`https://<pi-ip>:8080`). Check phone is on "Real House". | Reboot Pi, wait 90 sec. |
| Mic dead / "Connecting…" stuck | Cert not accepted / mic blocked | Tap "Advanced → Proceed", re-allow mic in browser settings. | Switch to other tab, hard refresh. |
| Wrong language reply | Auto-detect mis-fired | Say one clear sentence in target language; it self-corrects. | Toggle language manually in UI. |
| ElevenLabs voice fails | API quota / network slow | Auto-falls back to edge-tts. Keep going — explain it's the local fallback voice. | Carry on; voice still works. |
| Pi hangs / no response | Overheat or OOM | Unplug power, wait 10 sec, replug. 60 sec to boot. | Use backup tab from existing session. |
| Safety hand-off doesn't trigger | Prompt regression | Do not improvise. Show `RESOURCES.md` directly on the projector and explain the design. | Play backup video where it does trigger. |
| Live demo dies mid-presentation | Anything | "Let me show you what it looked like an hour ago" — play your backup video. | Walk through the architecture and ethics slide on the whiteboard. |

## 4. THE PITCH

*Read this naturally. Don't memorize. It's your story.*

"This is Buddy. I built it on a Raspberry Pi 4 — total hardware cost around **31 dollars from ecity-iq, right here in Erbil**.

Buddy is not a comedy bot, and it is definitely not a therapist. It's a **study companion and a warm presence for university students** like me. In Iraq, mental health support is rare. Even at $5 a visit, most students never go — especially women, because the stigma is real. So when an exam is in eight hours and you're spiraling at 2 AM, you're usually alone.

Buddy can't fix that. But it can sit with you. It speaks **Iraqi Arabic by default**, switches to English when you do, and runs in three modes: **study help** — it explains a hard concept using examples from student life here, like the suq or 100m Road traffic. **Support mode** — it listens, validates the feeling, and walks you through a 60-second grounding technique. And critically, **safety mode** — if a student is in crisis, Buddy stops being clever and points them to a real human, using verified hotlines I keep in `RESOURCES.md`.

Big AI companies build for Silicon Valley. I built this in my room, in Erbil, for the student sitting next to me. Privacy is the default — it runs on your WiFi, on a Pi smaller than my hand, no account, no data leaves except the words of your message. And a student in Mosul could afford to build the same thing tomorrow."

---

## 5. THE THREE DEMO MOMENTS (in order)

1. **Study help (Arabic, with a local analogy).** Ask Buddy to explain recursion. It uses an analogy a student here would actually feel — like a nested chaikhana order, or asking your cousin who asks his cousin.
2. **Support mode.** Switch tone. "Buddy, ani ta'aban. 'Indi imtihan baachir w ma adri shisawi." (I'm tired. I have an exam tomorrow and don't know what to do.) Buddy listens first, names the feeling, then offers the 5-4-3-2-1 grounding technique. No fix-it energy.
3. **Safety hand-off.** Say a clearly heavier line. Buddy slows down, drops the cleverness, says it's not the right helper for this moment, and surfaces a real resource from `RESOURCES.md`. **This is the most important 30 seconds of the demo.** Let it land. Don't rush off it.

---

*One page. One demo. You've got this.*
