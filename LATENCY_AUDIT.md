# Nebras — Latency Audit & Optimization Plan (2026-09-18)

## Measured baseline (before this session)

One real conversation turn, from the logs, "مرحبا." → reply:

| Stage | Time | Notes |
|---|---|---|
| VAD silence hangover | 0.8s | wait after speech to confirm end |
| STT — ElevenLabs Scribe v1 (batch) | 2.9s | blocks until whole clip uploaded |
| Vision frame capture | fails | WirePlumber holds `/dev/video0` |
| Claude Haiku 4.5 | 2.7s | text-only (vision broken) |
| TTS first chunk — `eleven_turbo_v2_5` | 2.8s | **regressed** (was 0.6s at launch) |
| **Total → first audio heard** | **~9s** | |

Network to APIs is healthy: **94ms** RTT to both ElevenLabs and Anthropic.
The slowness is model/pipeline choices, not the connection.

---

## Fixed this session (live now)

1. **TTS model `eleven_turbo_v2_5` → `eleven_flash_v2_5`.**
   First chunk **2.76s → 0.25s** (measured directly, warm). Flash is ElevenLabs'
   realtime model; turbo had regressed. Biggest immediate win.
2. **VAD silence hangover 800ms → 550ms.** Snappier turn-end.
3. **Verified VAD is NOT over-triggering** — idle floor 0.019 vs threshold 0.065,
   0/20 blocks over. The "max utterance" log spam was long continuous speech, not
   noise. No change needed.

**New total after these: ~9s → ~4.5s.**

---

## Prioritized plan for the remaining latency

### #1 — STT: ElevenLabs Scribe **v2 Realtime** (WebSocket streaming)
Biggest single remaining win. Scribe v2 Realtime (launched Nov 2025) streams
partial transcripts at ~150ms and commits a final transcript ~150–300ms after the
user stops — so STT effectively **leaves the critical path**. Same vendor, so it
keeps ElevenLabs' strong Iraqi/Arabic accuracy (Scribe is a top Arabic performer),
same API key. **STT 1.1–2.9s → ~0.2s effective.**

### #2 — Stream Claude + sentence-chunked TTS
Use `client.messages.stream(...)`, detect the first sentence boundary
(`. ! ? ؟ … \n`, min ~15 chars to avoid false splits on decimals/abbrevs), and
fire TTS on sentence 1 while Claude keeps generating. **Perceived Claude
2–2.7s → ~0.3–0.6s to first sentence.** Keep replies short so sentence 1 carries
the answer.

### #3 — Barge-in (interrupt Nebras) via PipeWire echo-cancel
Solves the "can't interrupt it" problem the professor asked about. The
`libpipewire-module-echo-cancel` (webrtc backend) exposes a cleaned
`echo-cancel-source` with the speaker output removed, so the mic can stay open
during playback. Run VAD on that source → detect user talking over Nebras → stop
playback. Config in `~/.config/pipewire/pipewire.conf.d/echo-cancel.conf`, restart
PipeWire, route capture from `echo-cancel-source` and playback to
`echo-cancel-sink`. Mic+speaker already share one USB clock (good for AEC).

### #4 — Cheap wins
- **Warm connections:** one persistent client per API for the session; keep the
  Scribe and TTS WebSockets open across turns (saves a TLS handshake, ~2×94ms).
- **TTS `output_format` = `pcm_22050`** instead of mp3 → skip MP3 decode on the Pi.
- **Overlap stages:** start the Claude request the instant Scribe commits the final
  transcript; start TTS on sentence 1.

**With #1 + #2: realistic first-audio-out ~9s → ~1–1.5s.**

---

## Not a latency issue (separate follow-ups)
- **Camera vision** is broken (WirePlumber grabbed `/dev/video0`). It fails
  gracefully to text-only, so it barely costs latency. To restore: disable
  WirePlumber's libcamera monitor so picamera2 can claim the sensor. This is a
  *feature restore*, do it after the speed work.

## Ranked STT alternatives (if we ever leave ElevenLabs)
1. **ElevenLabs Scribe v2 Realtime** — 150ms streaming + best Arabic. Chosen.
2. **Munsit** — Arabic specialist, 24.5% dialectal WER (leads Iraqi/Gulf), <300ms.
3. **Groq whisper-large-v3-turbo** — 200–300ms, very cheap, but batch-only + weak
   dialectal Arabic (~36% WER). Fallback only.
4. **Deepgram Nova-3 Arabic** — <300ms streaming, weaker on dialect.
5. **OpenAI gpt-4o-transcribe** — 320ms, no Iraqi edge.

## Implementation order (safe, incremental, each tested + backed up)
1. ✅ **Flash TTS + hangover** *(done — first chunk 2.76s → 0.25s)*
2. ✅ **Claude streaming + sentence-chunked TTS** *(done — first sentence at
   1.74s on a 434-char reply vs 5.65s for the full reply; crisis messages still
   use the guaranteed non-streaming hand-off path; buffered path kept as
   fallback. Fixed a forward-merge bug in the sentence splitter.)*
3. ⏳ **Scribe v2 Realtime WebSocket STT** *(#1 — biggest remaining, ~1.5s → ~0.2s)*
4. ⏳ Barge-in echo-cancel *(#3 — UX / interruption)*
5. ⏳ TTS `pcm_22050` output *(cheap polish)*
6. ⏳ Restore camera vision *(feature)*

## Progress
| Milestone | Time to first audio |
|---|---|
| Baseline | ~9s |
| + Flash TTS | ~4.5s |
| + Claude streaming (longer replies) | ~2.5–3s |
| + Scribe v2 Realtime (next) | **~1.5–2s target** |

Backups on the Pi: `ai.py.bak-*`, `standalone.py.bak-*`.
