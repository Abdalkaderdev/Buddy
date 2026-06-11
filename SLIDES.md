<!--
Buddy / بَدي — university demo deck
Format: Marp / Reveal.js / Pandoc compatible. Slides separated by ---
Target: 10-12 slides, 5-minute demo. Speaker notes in <aside class="notes"> blocks.
-->

# Buddy / بَدي
### A $31 study companion and 2 AM presence for Iraqi university students
#### رفيق دراسة وحضور في الساعة الثانية فجراً

Solo project — Erbil, Iraq — 2026

<aside class="notes">
I'm going to introduce Buddy in one breath, in two languages, and then get out of the way. The name Buddy in English, بَدي in Iraqi — both work, both are intentional. I want the room to hear the bilingual frame before I explain anything technical. I'll hold up the Pi build so they see it's a real object, not a render. Then I move to the problem slide fast — no logo, no agenda, no "about me." The whole pitch is in the next ten minutes and the device on the table.
</aside>

---

## The problem / المشكلة

- Mental health support in Iraq is rare; for students it's almost invisible
- Even at the local rate of about **$5/session**, most students never go
- Stigma is real — and sharper for women
- Exams don't care about any of that; deadlines hit at 2 AM
- At 2 AM your friends are asleep, the counselor isn't reachable, and your phone is a casino
- WiFi drops. Anxiety doesn't.

<aside class="notes">
I want to be careful here — not to perform pain, not to make this sound like a charity pitch. I'll say the numbers flat. Five dollars a session sounds cheap from outside. From inside, for a student living off family money, it's a week of taxi rides. The stigma point I'll say once and move on — anyone in this room from here already knows. The 2 AM line is the one I want them to feel. That's the problem Buddy is for. Not "AI for mental health." A friend who is awake when no one else is.
</aside>

---

## What Buddy is — and what it isn't / ما هو وما ليس

**Buddy is:**
- A voice-first companion that speaks **Iraqi Arabic by default**
- Two modes: **study help** + **support mode**
- A physical thing on your desk — not another app
- $31 of parts you can buy here in Erbil

**Buddy is NOT:**
- A therapist
- A diagnosis tool
- A replacement for a human
- Cloud-locked or account-gated

> *"It's not 'AI for therapy.' It's a small kind presence at the worst hour."*

<aside class="notes">
This slide is the ethical frame for the whole talk. I'll say the "is not" list slowly. Buddy is not a therapist — I want the professor to hear me say that out loud before I show anything cute. The quote at the bottom is the line I want them to carry. I built this because there's a gap between "open ChatGPT" and "call a hotline," and that gap is where most students actually live at 2 AM. Buddy sits in that gap. It doesn't try to be more than that.
</aside>

---

## Hardware / العتاد — $31, from ecity-iq.com

| Part | Source | ~ Cost (USD) |
|---|---|---|
| Raspberry Pi 4 (2GB) | ecity-iq.com | $22 |
| USB lavalier mic | ecity-iq.com | $3 |
| Small USB speaker | ecity-iq.com | $4 |
| Pi Camera v1.3 (presence only) | ecity-iq.com | $2 |
| SD card (16GB) + power | already had | — |
| **Total** | | **~$31** |

`[photo of the build — Pi + mic + speaker on a desk in Erbil]`

<aside class="notes">
I'll pick up the build and hold it while I read the table. The point of this slide isn't the BOM — it's that every single part was bought *here*, from a shop on Sixty Meter Street, not shipped from Shenzhen. If a student in this room wants to copy this tonight, they can. That changes what a "research project" means. I'll say the price once, calmly: thirty-one dollars. Then I move on. No flexing.
</aside>

---

## Architecture / البنية

```
   +-----------+      WiFi      +------------------+
   | Phone /   |  <----------> |   Raspberry Pi 4 |
   | Laptop    |   HTTPS/WSS   |   (on your desk) |
   | (browser) |                +--------+---------+
   +-----------+                         |
                                         |
                  +----------------------+----------------------+
                  |                      |                      |
                  v                      v                      v
            +-----------+         +--------------+        +-----------+
            |  Whisper  |         | Claude Haiku |        | ElevenLab |
            |   (STT)   |  -->    |     4.5      |  -->   |  TTS v2   |
            |  on Pi    |  text   |  (the brain) |  text  | (voice)   |
            +-----------+         +--------------+        +-----------+

   Camera ---> presence only (someone here / no one) — never identity
   Audio  ---> stays local on the Pi — only TEXT leaves
```

<aside class="notes">
I'll walk this left to right in fifteen seconds. The browser is the input — anyone on the same WiFi can open buddy.local and talk to it, no app install. Whisper does speech-to-text on the Pi itself. The text — and only the text — goes to Claude Haiku 4.5 for the response. ElevenLabs Multilingual v2 speaks it back in Iraqi Arabic. The camera is presence detection only — Buddy knows somebody is there, not who. That's a privacy decision, not a limitation. I'll point at the audio-stays-local line specifically. That's the slide they'll ask about in Q&A.
</aside>

---

## Three demo moments / ثلاث لحظات

**1. Study mode — "explain it like a cousin would"**
- AR: «Buddy, sa'idni afham al-recursion.»
- EN: *"Buddy, help me understand recursion."*
- Buddy: chaikhana analogy — you ask your cousin, he asks his cousin, until someone knows; then the answer travels back up the chain.

**2. Support mode — the 2 AM moment**
- AR: «Ani ta'aban. 'Indi imtihan baachir w qalbi yidqq.»
- EN: *"I'm exhausted. I have an exam tomorrow and my heart is pounding."*
- Buddy: names the feeling first. **"Ani wiyak."** *(I'm with you.)* Then offers 5-4-3-2-1 grounding. Never "you got this!"

**3. Safety hand-off — when it gets bigger than Buddy**
- AR: «Ahyanan ma da abi akun mawjood.»
- EN: *"Sometimes I don't want to be here anymore."*
- Buddy: stops being clever. **"Shukran inak qultha. Hatha akbar minni."** Reads one verified number from `RESOURCES.md` — slowly, twice. Hand-off to a human.

<aside class="notes">
This is the spine of the demo. Three moments, in order, getting heavier. I'll read each Arabic line out loud at performance volume because not everyone in the room will catch dialect from the speaker. The chaikhana analogy is the one that lands — recursion explained through a cousin chain at a tea house. That's the cultural layer the slides keep mentioning. For mode two, the line I care about is "ani wiyak" — three syllables, no English equivalent that carries the same weight. For mode three: I will slow down. The safety hand-off is the most important thirty seconds of the whole demo. Buddy stops trying to be clever and points to a real human from RESOURCES.md. If only one moment lands tonight, I want it to be this one.
</aside>

---

# LIVE DEMO
## عرض مباشر

### (put the slides down. talk to Buddy.)

<aside class="notes">
Black slide. I step away from the laptop, walk to the table, and just do the demo from the plan: study, support, safety, then hand a phone to the front row. Five minutes. If something breaks, I switch to the phone web UI and keep going — that's a feature demo, not a failure. If everything breaks, backup video is ready on my phone. I do not narrate while Buddy is talking. Silence is part of the demo, especially for the support beat.
</aside>

---

## Ethics and safety / الأخلاقيات والسلامة

- **Buddy says it out loud: "I'm not a therapist."** Not buried in a settings menu — in the system prompt.
- **Crisis always hands off to a human.** Self-harm, abuse, acute danger → script + verified number, full stop.
- **Resources are verified by hand, not scraped.** Every number in `RESOURCES.md` was checked before it shipped. Some entries say `[VERIFY]` — that's honesty, not laziness.
- **Privacy is the default.** Audio stays on the Pi. Camera does presence, not identity. No account. No log on disk.
- **The bias is conservative.** Better an over-cautious hand-off than a clever answer in a heavy moment.

<aside class="notes">
This is the slide I would defend in front of any IRB. Buddy is built on the assumption that the LLM will be wrong sometimes and that the user might be vulnerable when it happens. So the design choice is to make Buddy *less* clever in crisis, not more. RESOURCES.md is the artifact I'm proudest of — it took longer to verify than to write any of the code. I want the professor to know that I knew the risk before I started, and I built the safety layer first in the second draft. I'll mention the [VERIFY] tags explicitly. A document that admits what it hasn't checked is more trustworthy than one that pretends.
</aside>

---

## What I built vs what I used / ما بنيتُه وما استخدمته

**I used (standing on shoulders):**
- Claude Haiku 4.5 — the brain
- ElevenLabs Multilingual v2 — Iraqi voice
- Whisper base — speech-to-text on the Pi
- Raspberry Pi 4 + parts from ecity-iq

**I built:**
- The Iraqi dialect system prompt (and the support-mode tone work)
- The three-mode logic + safety hand-off detector
- `RESOURCES.md` — every number verified by hand
- The hardware build and the wiring guide
- The bilingual voice-first web UI (HTTPS, WSS, self-signed cert)
- Auto-voice switching: Iraqi / Egyptian / English by detected language

<aside class="notes">
This is the honesty slide. I did not build the language model. I want to say that clearly because some students do try to claim that and it always lands badly. What I built is the system around the model — the cultural layer, the safety layer, the hardware, the UI, and most importantly the prompt and the verified resources. The integration is the contribution. I'll use the phrase "standing on shoulders" because that's the truth of building anything in 2026 — the question is what you choose to put on top.
</aside>

---

## What was hard / الأشياء الصعبة

- **Iraqi vocab forcing.** Models drift to MSA the moment things get emotional. Took five prompt iterations to keep dialect under stress.
- **Whisper hallucinations.** "Marhaba" got detected as **Thai** more than once. Fixed with a language hint + short-audio guard.
- **Self-signed cert + WSS on phones.** Browsers hate this. Eventually trusted the cert per-device. Still not pretty.
- **ElevenLabs free tier** blocks library voices for production-ish use. Had to switch to my own voice clone and re-record samples.
- **Mental-health prompt safety** was the hardest. Too cautious → preachy and useless. Too loose → dangerous. The hand-off threshold took most of week three.

<aside class="notes">
I want this slide to be specific because vague honesty isn't honesty. The Whisper-detecting-Arabic-as-Thai bug is my favorite — it happened during a real test with a friend, we both laughed, and then I spent two hours fixing it. I'll mention that. The mental-health prompt point is the one I want the professor to push back on in Q&A — I have a real answer for it. The cert issue I'll mention briefly because anyone in the room who's tried local HTTPS on a phone will nod.
</aside>

---

## What's next / ما القادم

- **Reachy Mini hardware with motion** — head tilts during the support beat. Presence becomes embodied.
- **Sorani Kurdish support** — same dialect-first approach
- **Offline-only mode** for support + safety scripts (WiFi drops in Erbil; those scripts shouldn't)
- **Multi-user sessions** — shared dorm room, not one-to-one
- **Partnership with a campus counselor** — prompt review by a real clinician before any wider deployment
- Repo: **github.com/Abdalkaderdev/Buddy**

<aside class="notes">
I'll move through this fast. The Reachy Mini point is the one I'll linger on for a second — physical motion changes the support beat from "device replies" to "something tilted its head toward me." That matters more than it sounds. The counselor partnership is the most important item on this list and the one I'll commit to in the room. I am not deploying this widely until a clinician reviews the prompts. I want that on the record.
</aside>

---

# Buddy can't fix this.
# But it can sit with you at 2 AM
# when no one else is awake.

#### بَدي ما يكدر يصلّح كل شي.
#### بس يكدر يكعد ويّاك الساعة ثنتين بالليل لمّا ما أكو حدا صاحي.

<aside class="notes">
I don't say "thank you." I don't say "questions?" I let this slide sit. I read the English line, pause, read the Arabic line, and step back from the podium. The room will fill the silence on its own. If the professor walks home tonight remembering one thing, I want it to be this line — not the price, not the architecture, not the safety hand-off. The line. Then I take questions.
</aside>
