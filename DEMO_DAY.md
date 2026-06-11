# BUDDY — DEMO DAY QUICK CARD

*Erbil, University Demo. Keep this card in your pocket.*

---

## 1. TONIGHT (T-12 hours)

- Run the full flow at home one more time: speak to Buddy, hear a real response, in both Arabic and English. If it works tonight, it works tomorrow.
- Open `https://buddy.local:8080` from your phone, on iPhone hotspot. Confirm the page loads and the mic permission works.
- Confirm your iPhone hotspot is named exactly **"Real House"** with password **"Tareq5822"** — the Pi auto-joins this SSID. One typo and nothing connects.
- Charge everything tonight: phone to 100%, laptop, Pi power bank if you're using one. Pack the USB-C cable AND a backup cable.
- Record a 60-second backup video right now — your face, you talking to Buddy, Buddy answering out loud. Save it to your phone gallery. This is your insurance.
- `git push` your final working code. If the Pi dies tomorrow, the work still exists.

## 2. RIGHT BEFORE THE DEMO (T-15 min)

- Turn on your phone hotspot **first** — name "Real House". Nothing else works until this is on.
- Plug in the Pi. Wait a full 60 seconds. Do not panic during boot. Drink your chai.
- From your phone, open `https://buddy.local:8080`. If it loads, you are 90% safe.
- Open Buddy in **two tabs**: one for you to drive, one ready to hand to the professor.
- Hard refresh both tabs (Ctrl+Shift+R / long-press reload on iPhone).
- Accept the HTTPS certificate warning ("Advanced" → "Proceed"). Allow microphone access.
- Run a 3-shot smoke test: one Arabic sentence, one English sentence, one study question. If all three respond, you are ready.
- Breathe. The engineering is already done. Now you just talk.

## 3. IF SOMETHING BREAKS

| Symptom | Cause | Fix in 30 sec | Last resort |
|---|---|---|---|
| `buddy.local` won't resolve | mDNS not up / wrong WiFi | Use Pi's IP directly (`https://<pi-ip>:8080`). Check phone is on "Real House". | Reboot Pi, wait 90 sec. |
| Mic dead / "Connecting…" stuck | Cert not accepted / mic blocked | Tap "Advanced → Proceed", re-allow mic in browser settings. | Switch to other tab, hard refresh. |
| Wrong language reply | Auto-detect mis-fired | Say one clear sentence in target language; it self-corrects. | Toggle language manually in UI. |
| ElevenLabs voice fails | API quota / network slow | It auto-falls back to edge-tts. Just keep going — explain it's the local fallback voice. | Carry on; voice still works. |
| Pi hangs / no response | Overheat or OOM | Unplug power, wait 10 sec, replug. 60 sec to boot. | Use backup tab from existing session. |
| Live demo dies mid-presentation | Anything | "Let me show you what it looked like an hour ago" — play your backup video. | Walk through the architecture on the whiteboard. |

## 4. THE PITCH

*Read this naturally. Don't memorize. It's your story.*

"This is Buddy. I built it on a Raspberry Pi 4 — total hardware cost around **31 dollars from ecity-iq, right here in Erbil**. It's not a ChatGPT skin. It's an AI companion designed from the start for Iraqi students like me — it speaks **Arabic by default**, switches to English when you do, and runs in three modes: **companion** when you're lonely at 2 AM, **study mode** when you're stuck on a problem, and **support mode** when university is just too much. Big AI companies build for Silicon Valley. I built this in my room, for the student sitting next to me. Everything you see runs on a board smaller than my hand — and a kid in Mosul could afford to build the same thing tomorrow."

---

*One page. One demo. You've got this.*
