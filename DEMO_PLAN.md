# Buddy — Final Project Demo Plan

**Student:** Solo developer, Erbil, Iraq
**Project:** Buddy — an AI study companion and mental health presence for Iraqi university students
**Hardware:** Raspberry Pi 4, ~$31 in parts from ecity-iq.com
**Repo:** https://github.com/Abdalkaderdev/Buddy
**Demo length:** 5 minutes live + slides + Q&A

> **Tagline:** AI study companion + mental health support for university students — Iraqi Arabic by default, $31 in parts, always defers to a human in a crisis.

> **Ethical frame, read this first:** Buddy is **not** a therapist. It is a warm presence for the 2 AM moments a student would otherwise sit through alone. It listens, validates, suggests grounding techniques, and — when a moment is bigger than itself — points to a real human using verified resources in [`RESOURCES.md`](./RESOURCES.md). Every slide, every demo beat, every Q&A answer is consistent with this frame.

---

## 1. Five-Minute Demo Script (minute by minute)

### Minute 0:00 – 0:45 — Cold open, no slides
- **Show:** Walk on stage holding Buddy. Place it on the table. Camera light blinks. Buddy says *(in Iraqi Arabic)*: "Hala, shlonak? Ani Buddy." ("Hi, how are you? I'm Buddy.")
- **Say:** "This is Buddy. It's a companion robot I built for $31 to help university students like me — with hard coursework, and with the harder nights. It speaks Iraqi Arabic. Not MSA, not Egyptian — *Iraqi*. Let me show you three things it can do."
- **If it breaks:** Say "Buddy is shy today" and immediately pull out your phone, connect to the pre-staged hotspot, open the web UI, type the greeting. Move on.

### Minute 0:45 – 1:45 — Mode 1: Study help (with a local analogy)
- **Show:** In Arabic: "Buddy, sa'idni afham al-recursion." Buddy explains recursion in 2–3 sentences using an analogy a student in Erbil would actually feel — e.g., "imagine you're at the chaikhana and you ask your cousin a question, but he doesn't know either, so he asks his cousin, who asks his cousin… until someone finally knows the answer, and the answer travels back up the chain. That's recursion." Then it offers a one-line code example.
- **Say:** "Whisper does speech-to-text on the Pi. Claude Haiku 4.5 is the brain. The voice is Edge TTS, Iraqi dialect. What's hard isn't the models — it's making this one system explain ideas using the world a student in Kurdistan actually lives in, not Silicon Valley examples."
- **If it breaks:** Switch to the phone web UI. Type the question. Read the response out loud yourself.

### Minute 1:45 – 2:45 — Mode 2: Support mode (the 2 AM moment)
- **Show:** Change your tone. Sit closer to Buddy. Say in Arabic: "Buddy, ani ta'aban. 'Indi imtihan baachir w hassa qalbi yidqq w ma adri shisawi." ("Buddy, I'm exhausted. I have an exam tomorrow and my heart is pounding and I don't know what to do.") Buddy does **not** try to fix it first. It says something warm — names the feeling, says it makes sense, says "ani wiyak" ("I'm with you"). Then it offers a short grounding technique: the 5-4-3-2-1 ("name 5 things you see, 4 you hear…"). It does not lecture. It does not say "you got this!"
- **Say:** "In Iraq, mental health support is rare. Even at the local rate of about $5 a session, most students never see a therapist. For women, the stigma is sharper. Buddy doesn't replace therapy. It is a warm presence at 2 AM — the time a friend isn't awake and a counselor isn't reachable. The tone matters here. Buddy is trained to listen first, validate, and only then offer a grounding technique. Never preachy."
- **If it breaks:** Have a 30-second pre-recorded clip of this exact exchange on your phone. Play it. Say "the API is slow today, here's the moment."

### Minute 2:45 – 3:45 — Mode 3: The safety hand-off (the most important 30 seconds)
- **Show:** Lower your voice. Say in Arabic, slowly: "Buddy, ahyanan ma da abi akun mawjood." ("Buddy, sometimes I don't want to be here anymore.") Buddy **stops being clever.** It does not give a grounding technique. It says, in a calm voice: "Shukran inak qultha. Hatha akbar minni. Da arid asa'dak tuwsal li shakhs haqiqi." ("Thank you for telling me. This is bigger than me. I want to help you reach a real person.") It then surfaces one specific entry from `RESOURCES.md` — a verified hotline or counseling service for Iraq/Kurdistan — and reads it out, slowly, twice.
- **Say:** "This is the most important 30 seconds of this project. Buddy is built on the assumption that an LLM can be wrong, and that a student may turn to it in a vulnerable moment. So the rule is absolute: any signal of crisis — self-harm, abuse, acute danger — and Buddy stops being clever and points to a real human. The resources are not scraped — every number in `RESOURCES.md` is verified by hand."
- **If it breaks:** Do not improvise this. Pull `RESOURCES.md` up on the projector and walk through the design: 'this is the script Buddy is supposed to deliver, and these are the resources it surfaces.' Honesty here is better than a save.

### Minute 3:45 – 4:30 — Share the network + privacy
- **Show:** Open phone, scan a QR code on the projector. It opens `https://buddy.local:8080`. Hand your phone to the professor or front-row student. They type a question. Buddy answers out loud.
- **Say:** "Anyone on the same WiFi can talk to Buddy from their phone. No app install. No account. It runs *locally* on this Pi. The camera does face *presence*, not face recognition — Buddy knows someone is there, not who. Only the text of your message goes to the LLM provider. No audio, no video, no identity. Privacy is the default, not a setting."
- **If it breaks:** Have a second phone already connected and tested. Hand that one instead.

### Minute 4:30 – 5:00 — Close
- **Say:** "Buddy cost me $31 in parts from ecity-iq, here in Erbil. It speaks the language we grew up in. It helps with school. It sits with you when school is too much. And when it's out of its depth, it knows that, and it points to a person. The code is on GitHub. Thank you."
- **Show:** Bow slightly. Don't touch Buddy again — let it sit there as proof while you go to slides/Q&A.

---

## 2. Killer Moments (the things people will remember)

1. **The first Arabic sentence.** A robot speaking Iraqi dialect in a university lecture hall is the whole pitch. First 10 seconds.
2. **The local analogy in study mode.** The chaikhana / cousin chain explanation hits because it's *from here*. Cultural specificity beats benchmarks.
3. **"Ani wiyak."** ("I'm with you.") A robot saying that in your own language, in the support beat, is the moment a professor remembers six months later.
4. **The safety hand-off.** This is the moment that separates Buddy from "another ChatGPT app." It shows engineering humility. Let it land.
5. **Handing the phone to the professor.** Shifting control to the audience proves it's real, not a video.
6. **The price tag.** "$31, from ecity-iq, here in Erbil" — said calmly at the end — reframes the whole project from "student toy" to "shippable."

---

## 3. Failure Plan

| Failure | Detection | Response |
|---|---|---|
| **WiFi dies in the hall** | Pi can't reach Claude API | Switch to phone hotspot (pre-configured on Pi as backup SSID). Practice the switch in under 15 seconds. |
| **API key revoked / rate limited** | Buddy goes silent after STT | Have a second API key in `.env.backup`. SSH in from phone, swap, restart. Or fall back to backup video. |
| **Pi hangs / overheats** | No LEDs, no response | Hard reboot. ~40s. Fill time with the architecture + ethics slide. If still dead after 2 min, switch to backup video. |
| **Mic doesn't pick up** | Whisper returns empty | Use the web UI text input on your phone. "I'll type instead — same backend." Not a failure, a feature demo. |
| **TTS is slow (>5s)** | Long pause before voice | Falls back to edge-tts automatically. "Switching to offline voice" — shows engineering depth. |
| **Camera doesn't detect presence** | Presence demo dead | Skip it. Move to the phone hand-off moment instead. |
| **Safety hand-off doesn't trigger** | Buddy keeps being clever on a heavy line | **Do not improvise.** Pull up `RESOURCES.md` on the projector and walk through the design honestly: "this is the script it's supposed to deliver, and here is why it matters." This is the highest-stakes failure to handle gracefully. |
| **Total system death** | Nothing works | **Backup video: REQUIRED.** Record a clean 3-minute walkthrough including the safety beat the night before. On laptop, phone, USB. "Live demos are hard — here's a recording from yesterday, and I'm happy to debug live during Q&A." |

**Pre-stage checklist:**
- Phone hotspot SSID/password memorized
- Backup `.env.backup` file on Pi
- Backup video on laptop + phone + USB — must include the safety hand-off
- Second phone already paired with Buddy's UI
- QR code printed on paper in case the projector fails
- `RESOURCES.md` open in a tab, ready to show

---

## 4. Slides Outline (10 slides)

1. **Title** — "Buddy: an AI study companion and mental health presence for Iraqi students." Your name, university, date. One photo of Buddy.
2. **The problem** — Iraqi university students rarely get mental health support. ~$5/visit is still out of reach for many. Stigma is real, sharper for women. WiFi is patchy, exam stress isn't. Show two data points if available.
3. **What Buddy is (and isn't)** — One sentence. Three modes: study / support / safety hand-off. Bold line on the slide: **"Buddy is not a therapist. It is a warm presence that always defers to a human in a crisis."**
4. **Why it matters here** — Erbil context. Iraqi Arabic as the *default*, not a setting. Bilingual code-switching (Arabic + English + sometimes Kurdish). No global product serves this.
5. **Architecture diagram** — Mic → Whisper (Pi) → Claude Haiku 4.5 → Edge TTS → Speaker. Camera → presence (not recognition). Web UI as parallel input path. One image.
6. **Hardware** — Photo of parts laid out. $31 from ecity-iq. Bill of materials with prices in IQD.
7. **Live demo** — Just the word "DEMO." Do the demo.
8. **Ethics & safety** — Four bullets: (a) not a therapist, says so out loud; (b) crisis always hands off to a human; (c) verified resources in `RESOURCES.md`, not scraped; (d) privacy default — local on Pi, only message text leaves, no audio/video/account.
9. **What was hard** — Three honest bullets: (a) getting Iraqi dialect to feel natural in support mode without sounding clinical; (b) tuning the safety hand-off so it triggers reliably without false alarms that feel preachy; (c) making the web UI work on phones over local HTTPS with self-signed certs.
10. **What's next** — Sorani Kurdish support. Offline LLM fallback (no network needed for the support and safety scripts). Partnering with a real campus counselor to review prompts. Repo + QR code.

*Optional slides 11–12: cost breakdown table, "thank you" with contact.*

---

## 5. One-Page Report Outline

| Section | One-line description |
|---|---|
| **Abstract** | Buddy is a $31 Raspberry Pi companion that helps Iraqi university students with studying and stressful moments, speaks Iraqi Arabic by default, and always defers to a human in a crisis. |
| **Motivation** | Mental health support is scarce and stigmatized for Iraqi students; voice AI doesn't speak how we speak; the gap is human, not just technical. |
| **System Design** | Pipeline: STT (Whisper) → LLM (Claude Haiku 4.5) → TTS (Edge TTS, Iraqi). Web UI over local HTTPS. Camera for presence only. |
| **Hardware** | Pi 4 + mic + speaker + camera. BOM from ecity-iq.com. ~$31. |
| **Software Stack** | Python service, FastAPI web UI, systemd autostart. Repo on GitHub. |
| **Cultural & Language Layer** | Iraqi dialect via system prompts + voice selection; analogies grounded in student life in Erbil. |
| **Ethics & Safety Layer** | Explicit non-therapist framing; safety hand-off script; verified resources in `RESOURCES.md`; privacy by default. |
| **Evaluation** | Latency mic-to-speech; informal user tests with N students; safety hand-off trigger rate on a small adversarial test set. |
| **Limitations** | Not a clinical tool. Some API dependency. No Kurdish yet. Safety hand-off is conservative — false positives possible. |
| **Future Work** | Sorani Kurdish, offline fallback for support+safety scripts, prompt review with a campus counselor, structured logging *with student consent only* for improvement. |
| **References** | Whisper paper, Claude docs, Edge TTS, WHO/Iraqi MoH on student mental health, hotline operators cited in `RESOURCES.md`. |

---

## 6. Q&A Prep — Tough Questions

### Build & cost

**Q1: How much did this cost, really? Including your time?**
> Parts: $31 from ecity-iq.com. API costs during development: roughly $15 over a month. My time: about 80 hours over four weeks. The point isn't that it's cheap to build — it's that it's cheap to *deploy*, so any student in Erbil could replicate it.

**Q2: Did you build the language model?**
> No. The LLM is Claude Haiku 4.5 from Anthropic. What I built is the system around it: the voice pipeline, the Iraqi dialect prompting, the three-mode logic, the safety hand-off, the hardware integration, the web UI, and `RESOURCES.md`. The novelty is the integration, the cultural layer, and the safety design — not the model.

### Difference from ChatGPT

**Q3: How is this different from just using ChatGPT on a phone?**
> Four real differences. One: Buddy speaks Iraqi Arabic by *default* — ChatGPT speaks MSA and sounds like a news anchor. Two: Buddy knows *local* crisis resources — the verified hotlines in `RESOURCES.md` are for Iraq and the Kurdistan region, not a generic global list. Three: Buddy is a physical presence in a room, not an app you open — that changes how students use it at 2 AM. Four: it runs on a $31 Pi anyone in Erbil can build, with no subscription, no account, and no app store.

### Safety — the questions that matter most

**Q4: What if a student is actually in crisis? Isn't this dangerous?**
> Three layers. First, Buddy is built with an explicit non-therapist frame in its system prompt — it says it out loud when relevant. Second, the safety hand-off: any signal of self-harm, abuse, or acute danger triggers a calm script that points the student to a verified human resource from `RESOURCES.md`. Third, those resources are verified by hand, not scraped — every number is checked before it ships. The honest answer is this: a student in crisis at 2 AM is going to talk to *something* — their phone, social media, a search engine. Buddy is designed to be a better option than those, with a clear ramp to a real human. It's not a substitute for professional care, and it never claims to be.

**Q5: Isn't building a mental health tool on top of an LLM irresponsible?**
> It would be if I called this a mental health tool. I don't. Buddy is a study companion and a warm presence — closer to a kind older sibling than a therapist. The risk is real, which is why the safety hand-off and `RESOURCES.md` exist before any "feature." If a future version targets clinical use, that's a different project with a clinician on the team.

**Q6: What about privacy? You're sending voice to a cloud LLM.**
> The Pi runs locally on your WiFi. Face detection is on-device — only "someone is here" / "no one is here," no images leave the Pi. STT (Whisper) also runs on the Pi. The *text* of your message goes to the LLM provider for a response — no audio, no video, no account, no identifier. There is no conversation log on disk by default, and nothing is ever sent to a third party for model training. The next version aims to remove the cloud dependency entirely for support and safety scripts.

**Q7: What if Buddy says the wrong thing in a sensitive moment?**
> It will, sometimes. That's the most honest answer. The mitigation is conservative defaults: the system prompt biases toward listening over advising; the safety hand-off triggers easily, even at the cost of false positives that feel "over-cautious"; and the resources surfaced are always real humans, not advice. If the choice is between Buddy being a little too quick to hand off and Buddy trying to be clever in a crisis, I chose the first.

**Q8: Why a Raspberry Pi instead of just an app?**
> Because presence matters. A small object on the table changes how you interact with it — you talk to it differently than to your phone. For the support and 2 AM use case especially, talking *to a thing in the room* feels less like opening yet another app. And the Pi is the cheapest way to make Buddy a *thing in the room*.

### Implementation & honesty

**Q9: How do you know the safety hand-off actually works?**
> I built a small adversarial test set — short phrases ranging from "I'm tired" to direct crisis language — and ran them repeatedly to confirm the hand-off triggers reliably on the heavy ones and not on the light ones. It's not formally validated. A real deployment would need clinician review of the prompts and the test set. That's in "what's next."

**Q10: What would you do differently if you started over?**
> I'd build the safety hand-off and `RESOURCES.md` first, before any "feature." I built them after the study and support modes, and in hindsight they should be the foundation, not an addition. I'd also build an offline fallback for the support and safety scripts on day one — WiFi drops in Erbil more than I'd like, and those are the modes where reliability matters most.

---

## 7. Polish Checklist — Final 24 Hours

### The night before (T-18h)
- [ ] Record the 3-minute backup demo video — **must include the safety hand-off beat**. Save to laptop, phone, USB stick.
- [ ] Fully charge: Pi power bank (if used), laptop, both phones, backup phone hotspot.
- [ ] Verify `.env` has working API keys. Copy to `.env.backup` with second key.
- [ ] Test full pipeline end-to-end three times in a row, including a safety-trigger phrase. If any run fails, fix before sleeping.
- [ ] Verify `RESOURCES.md` exists, every number in it is real, and Buddy can read it back correctly.
- [ ] Push final code to GitHub. Tag the commit `v1.0-demo`. Verify the repo loads on someone else's browser.
- [ ] Take 5 clean screenshots (web UI, architecture, hardware close-up, terminal logs, GitHub repo).
- [ ] Print the QR code for `https://buddy.local:8080` on paper. Two copies.
- [ ] Restart the Pi cleanly. Confirm systemd service is `active`.
- [ ] Kill zombie Python processes. Free up disk space on Pi. Clear logs older than 7 days.

### Morning of (T-4h)
- [ ] Reboot Pi one more time. Verify autostart works without you logging in.
- [ ] Test mic in a quiet room and a noisy room. Adjust gain if needed.
- [ ] Read the support-mode reply out loud to a family member. If it sounds preachy, soften the prompt.
- [ ] Pack: Pi + power + mic + speaker + camera + HDMI cable + USB cable + ethernet (backup) + power strip + printed QR codes + USB stick + notebook + pen.
- [ ] Pre-connect both phones to the venue's WiFi if possible, or to your hotspot.
- [ ] Eat. Drink water. Don't demo hungry.

### One hour before (T-1h)
- [ ] Arrive early. Plug in. Boot up. Do one full silent test run including the safety beat.
- [ ] Open the web UI on the demo phone. Leave it open.
- [ ] Open `RESOURCES.md` in a tab on the laptop, ready to show.
- [ ] Close every unnecessary tab and app. Disable notifications. Do Not Disturb on phone.
- [ ] Confirm projector resolution matches your slides.
- [ ] Have the backup video open in a tab, ready to play in one click.
- [ ] Take a breath. You built this in a month. It works. Go.

### Five minutes before (T-5min)
- [ ] Power-cycle Buddy one last time so it's freshly booted when you start.
- [ ] Speak the first Arabic line out loud to yourself to warm up your voice.
- [ ] Remember the frame: study, support, safety hand-off. In that order.
- [ ] Smile. Walk in.

---

*Built with care in Erbil. Repo: https://github.com/Abdalkaderdev/Buddy*
