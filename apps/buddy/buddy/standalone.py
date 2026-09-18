"""Nebras standalone always-on listening loop.

Runs on the Pi without a browser: USB mic -> Whisper STT -> BuddyAI (Claude) ->
TTS (ElevenLabs preferred, edge-tts fallback) -> USB speaker.

Run with:
    /home/pi/buddy-venv/bin/python -m buddy.standalone
"""

from __future__ import annotations

import asyncio
import base64
import os
import re
import signal
import sys
import tempfile
import time
from pathlib import Path

# Load environment from .buddy.env (mirrors systemd EnvironmentFile) so the
# Anthropic API key + ElevenLabs key are present when run standalone.
_ENV_FILE = Path("/home/pi/.buddy.env")
if _ENV_FILE.exists():
    for line in _ENV_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

import numpy as np
import sounddevice as sd

from .ai import get_ai
from .audio import SpeechToText
from .vision import capture_frame_b64
from . import faq
import os
import io
import wave
import numpy as np

class ElevenLabsSTT:
    """ElevenLabs Scribe STT - cloud, fast (1-2s), good Iraqi Arabic."""
    def __init__(self):
        from elevenlabs.client import ElevenLabs
        self.client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

    def transcribe_array(self, audio, sample_rate=16000):
        # audio: float32 numpy array, mono, in [-1, 1]
        pcm16 = np.clip(audio * 32767.0, -32768, 32767).astype("<i2").tobytes()
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(pcm16)
        buf.seek(0)
        try:
            result = self.client.speech_to_text.convert(
                file=buf, model_id="scribe_v1", language_code="ara"
            )
            text = (getattr(result, "text", "") or "").strip()
            return text
        except Exception as e:
            print(f"[STT][elevenlabs] error: {type(e).__name__}: {e} - falling back to local")
            raise

from .config import (
    CLAUDE_MODEL,
    LLM_PROVIDER,
    OLLAMA_MODEL,
    TTS_VOICE,
)
from . import server as buddy_server


# ----- Audio / VAD parameters -----
# Most USB sound cards on the Pi only expose 44.1/48 kHz natively at hw level.
# We capture at the device's native rate, then downsample to 16 kHz for Whisper.
WHISPER_RATE = 16_000
CAPTURE_RATE = 44_100
CHANNELS = 1
BLOCK_MS = 30
BLOCK_FRAMES = CAPTURE_RATE * BLOCK_MS // 1000

RMS_THRESHOLD = 0.065         # AGC on: floor pumps to ~0.05, speech 0.09+
MIN_SPEECH_MS = 600           # must have this much speech before we accept utterance
SILENCE_HANGOVER_MS = 550    # tightened for snappier turn-taking
MAX_UTTERANCE_MS = 15_000     # hard cap
MIN_TRANSCRIPT_CHARS = 3

USB_NAME_HINT = "USB Audio Device"


# ----- Helpers -----
def _pick_usb_device() -> tuple[int | None, int | None]:
    """Locate the USB sound card by name. Returns (input_idx, output_idx)."""
    in_idx = out_idx = None
    for i, d in enumerate(sd.query_devices()):
        if USB_NAME_HINT.lower() in d["name"].lower():
            if in_idx is None and d["max_input_channels"] > 0:
                in_idx = i
            if out_idx is None and d["max_output_channels"] > 0:
                out_idx = i
    return in_idx, out_idx


def _rms(block: np.ndarray) -> float:
    if block.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(block.astype(np.float32) ** 2)))


def _detect_lang(text: str) -> str:
    """Crude script-based language hint for TTS/AI."""
    if re.search(r"[؀-ۿ]", text):
        return "ar"
    return "en"


def _voice_for_lang(lang: str) -> str:
    """Pick an edge-tts voice for the detected language.

    ElevenLabs uses its own fixed voice id so this only matters for the
    edge-tts fallback. TTS_VOICE is Iraqi female by default; swap to an
    English voice if Claude replied in English.
    """
    if lang == "en":
        return "en-US-AriaNeural"
    return TTS_VOICE


async def _play_b64_mp3(b64_audio: str) -> None:
    """Decode + play a base64 MP3 string via ffplay."""
    raw = base64.b64decode(b64_audio)
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        f.write(raw)
        path = f.name
    try:
        proc = await asyncio.create_subprocess_exec(
            "ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await proc.wait()
    finally:
        try:
            Path(path).unlink()
        except OSError:
            pass


# Lazy ElevenLabs client for streaming TTS in standalone (bypasses base64 round-trip).
_eleven_stream_client = None


def _get_eleven_stream_client():
    global _eleven_stream_client
    if _eleven_stream_client is None:
        key = os.getenv("ELEVENLABS_API_KEY")
        if not key:
            return None
        try:
            from elevenlabs.client import ElevenLabs
            _eleven_stream_client = ElevenLabs(api_key=key)
        except Exception as _e:
            print(f"[TTS][stream] init failed: {_e}")
            return None
    return _eleven_stream_client


async def _speak_streaming(text: str) -> bool:
    """Stream ElevenLabs TTS chunks directly into ffplay stdin.

    Audio starts playing as soon as the first MP3 chunk arrives instead of
    after the whole reply is buffered + base64-encoded. Returns True on
    success, False so the caller can fall back to the buffered path."""
    client = _get_eleven_stream_client()
    if client is None:
        return False
    voice_id = os.getenv("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")
    model_id = os.getenv("ELEVENLABS_MODEL", "eleven_turbo_v2_5")
    output_format = "mp3_22050_32"

    try:
        proc = await asyncio.create_subprocess_exec(
            "ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet",
            "-fflags", "nobuffer", "-flags", "low_delay",
            "-probesize", "32", "-analyzeduration", "0",
            "-i", "pipe:0",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
    except Exception as e:
        print(f"[TTS][stream] ffplay spawn failed: {e}")
        return False

    loop = asyncio.get_running_loop()
    t0 = time.time()
    first_chunk_at: list[float] = []

    def _produce():
        return client.text_to_speech.stream(
            voice_id=voice_id,
            text=text,
            model_id=model_id,
            output_format=output_format,
        )

    try:
        stream = await asyncio.to_thread(_produce)
        q: asyncio.Queue = asyncio.Queue(maxsize=64)

        def _pump():
            try:
                for chunk in stream:
                    if chunk:
                        loop.call_soon_threadsafe(q.put_nowait, chunk)
            except Exception as e:
                loop.call_soon_threadsafe(q.put_nowait, ("ERR", e))
            finally:
                loop.call_soon_threadsafe(q.put_nowait, None)

        pump_task = asyncio.create_task(asyncio.to_thread(_pump))
        try:
            while True:
                item = await q.get()
                if item is None:
                    break
                if isinstance(item, tuple) and item and item[0] == "ERR":
                    print(f"[TTS][stream] producer error: {item[1]}")
                    break
                if not first_chunk_at:
                    first_chunk_at.append(time.time())
                    print(f"[SPEAK] first chunk at {first_chunk_at[0]-t0:.2f}s")
                try:
                    proc.stdin.write(item)
                    await proc.stdin.drain()
                except (BrokenPipeError, ConnectionResetError):
                    break
        finally:
            try:
                proc.stdin.close()
            except Exception:
                pass
            await pump_task
        await proc.wait()
        return True
    except Exception as e:
        print(f"[TTS][stream] error: {type(e).__name__}: {e} - falling back")
        try:
            proc.kill()
        except Exception:
            pass
        return False


# ----- Capture loop -----
async def _capture_utterance(input_device: int | None) -> np.ndarray | None:
    """Block until a complete utterance is captured. Returns mono float32 audio."""
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue[np.ndarray] = asyncio.Queue()

    def callback(indata, frames, time_info, status):
        if status:
            # over/underflow; not fatal
            pass
        loop.call_soon_threadsafe(queue.put_nowait, indata[:, 0].copy())

    stream = sd.InputStream(
        samplerate=CAPTURE_RATE,
        channels=CHANNELS,
        blocksize=BLOCK_FRAMES,
        dtype="float32",
        device=input_device,
        callback=callback,
    )

    speech_buffer: list[np.ndarray] = []
    speech_ms = 0
    silence_ms = 0
    speaking = False
    started_print = False
    total_ms = 0
    idle_blocks = 0
    last_idle_rms = 0.0

    with stream:
        print("[IDLE] waiting for speech…")
        while True:
            block = await queue.get()
            rms = _rms(block)
            is_voice = rms > RMS_THRESHOLD

            if is_voice:
                if not speaking:
                    speaking = True
                    speech_buffer = [block]
                    speech_ms = BLOCK_MS
                else:
                    speech_buffer.append(block)
                    speech_ms += BLOCK_MS
                silence_ms = 0
                if speech_ms >= MIN_SPEECH_MS and not started_print:
                    print(f"[LISTEN] recording… (rms={rms:.3f})")
                    started_print = True
            else:
                if speaking:
                    speech_buffer.append(block)
                    silence_ms += BLOCK_MS
                    if (
                        speech_ms >= MIN_SPEECH_MS
                        and silence_ms >= SILENCE_HANGOVER_MS
                    ):
                        break
                else:
                    idle_blocks += 1
                    last_idle_rms = max(last_idle_rms, rms)
                    # every ~2s, print floor reading to help tune threshold
                    if idle_blocks * BLOCK_MS >= 2000:
                        print(f"[IDLE] floor rms peak={last_idle_rms:.4f} (threshold={RMS_THRESHOLD})")
                        idle_blocks = 0
                        last_idle_rms = 0.0

            if speaking:
                total_ms += BLOCK_MS
                if total_ms >= MAX_UTTERANCE_MS:
                    print("[LISTEN] max utterance length reached, cutting off")
                    break

    if not speech_buffer or speech_ms < MIN_SPEECH_MS:
        return None
    audio = np.concatenate(speech_buffer).astype(np.float32)
    # Downsample CAPTURE_RATE -> WHISPER_RATE with linear interpolation
    if CAPTURE_RATE != WHISPER_RATE:
        n_out = int(len(audio) * WHISPER_RATE / CAPTURE_RATE)
        if n_out > 0:
            x_old = np.linspace(0.0, 1.0, num=len(audio), endpoint=False, dtype=np.float32)
            x_new = np.linspace(0.0, 1.0, num=n_out, endpoint=False, dtype=np.float32)
            audio = np.interp(x_new, x_old, audio).astype(np.float32)
    return audio


# ----- Main loop -----
class _RealtimeSTT:
    """Warm ElevenLabs Scribe v2 Realtime connection, reused across turns.

    Pays the ~0.5s WebSocket connect once, then each utterance is ~0.55s
    (vs 1.1-2.9s for batch Scribe). Returns None on ANY problem so the caller
    transparently falls back to the batch path. Disable with USE_REALTIME_STT=0."""

    def __init__(self):
        self._conn = None
        self._state = {"event": None, "text": None, "err": None}
        self._enabled = (
            os.getenv("USE_REALTIME_STT", "1") == "1"
            and bool(os.getenv("ELEVENLABS_API_KEY"))
        )

    async def _ensure_conn(self):
        if self._conn is not None:
            return self._conn
        from elevenlabs.client import ElevenLabs
        from elevenlabs.realtime.scribe import AudioFormat, CommitStrategy
        client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
        conn = await client.speech_to_text.realtime.connect({
            "model_id": "scribe_v2_realtime",
            "audio_format": AudioFormat.PCM_16000,
            "sample_rate": 16000,
            "commit_strategy": CommitStrategy.MANUAL,
            "language_code": "ara",
        })
        st = self._state

        def _on_committed(data):
            st["text"] = getattr(data, "text", None) or (
                data.get("text") if isinstance(data, dict) else None)
            if st["event"]:
                st["event"].set()

        def _on_err(data):
            st["err"] = data
            if st["event"]:
                st["event"].set()

        conn.on("committed_transcript", _on_committed)
        for ev in ("error", "auth_error", "quota_exceeded", "rate_limited",
                   "transcriber_error", "session_time_limit_exceeded",
                   "input_error", "resource_exhausted", "queue_overflow"):
            conn.on(ev, _on_err)
        self._conn = conn
        print("[STT][rt] Scribe v2 Realtime connected")
        return conn

    async def _drop(self):
        c, self._conn = self._conn, None
        if c is not None:
            try:
                await c.close()
            except Exception:
                pass

    async def transcribe(self, audio) -> "str | None":
        """audio: mono float32 @16k. Returns text, or None to signal fallback."""
        if not self._enabled:
            return None
        try:
            conn = await asyncio.wait_for(self._ensure_conn(), timeout=6)
            pcm = (np.clip(audio, -1.0, 1.0) * 32767.0).astype("<i2").tobytes()
            self._state["event"] = asyncio.Event()
            self._state["text"] = None
            self._state["err"] = None
            for i in range(0, len(pcm), 32000):
                await conn.send({"audio_base_64": base64.b64encode(pcm[i:i + 32000]).decode()})
            await conn.commit()
            await asyncio.wait_for(self._state["event"].wait(), timeout=8)
            if self._state["err"] is not None:
                print(f"[STT][rt] error event: {self._state['err']}; dropping conn")
                await self._drop()
                return None
            return self._state["text"]
        except Exception as e:
            print(f"[STT][rt] failed: {type(e).__name__}: {e}; -> batch fallback")
            await self._drop()
            return None


# --- Streaming Claude -> sentence-chunked TTS (fast path, non-crisis) ---
import re as _re_sent
_SENT_BOUNDARY = _re_sent.compile(r"[.!?\u061F\u2026\n]")  # . ! ? Arabic-? ellipsis newline
_MIN_SENTENCE_CHARS = 15


# --- Cartesia (Sonic 3.5) streaming TTS — primary voice (Fatima) ---
_CARTESIA_KEY = os.getenv("CARTESIA_API_KEY")
_CARTESIA_VOICE = os.getenv("CARTESIA_VOICE_ID", "731ace69-ee17-41bc-8c6f-665c9f1db95c")
_CARTESIA_MODEL = os.getenv("CARTESIA_MODEL", "sonic-3.5")
_CARTESIA_LANG = os.getenv("CARTESIA_LANGUAGE", "ar")
_CARTESIA_SR = 44100


async def _speak_cartesia(text: str) -> bool:
    """Stream Cartesia TTS (SSE, raw PCM) straight into ffplay. True on success."""
    if not _CARTESIA_KEY:
        return False
    import json as _json
    import urllib.request as _url
    import base64 as _b64
    payload = _json.dumps({
        "model_id": _CARTESIA_MODEL,
        "transcript": text,
        "voice": {"mode": "id", "id": _CARTESIA_VOICE},
        "language": _CARTESIA_LANG,
        "output_format": {"container": "raw", "encoding": "pcm_s16le", "sample_rate": _CARTESIA_SR},
    }).encode()
    try:
        proc = await asyncio.create_subprocess_exec(
            "ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet",
            "-f", "s16le", "-ar", str(_CARTESIA_SR), "-ac", "1",
            "-fflags", "nobuffer", "-flags", "low_delay",
            "-probesize", "32", "-analyzeduration", "0", "-i", "pipe:0",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
    except Exception as e:
        print(f"[TTS][cartesia] ffplay spawn failed: {e}")
        return False

    loop = asyncio.get_running_loop()
    q: asyncio.Queue = asyncio.Queue(maxsize=128)
    t0 = time.time()
    first = []

    def _pump():
        try:
            req = _url.Request(
                "https://api.cartesia.ai/tts/sse", data=payload,
                headers={"X-API-Key": _CARTESIA_KEY, "Cartesia-Version": "2025-04-16",
                         "Content-Type": "application/json"})
            r = _url.urlopen(req, timeout=30)
            import json as __json
            for line in r:
                line = line.decode("utf-8", "ignore").strip()
                if line.startswith("data:"):
                    try:
                        ev = __json.loads(line[5:].strip())
                    except Exception:
                        continue
                    d = ev.get("data")
                    if d:
                        loop.call_soon_threadsafe(q.put_nowait, _b64.b64decode(d))
                    if ev.get("type") == "done" or ev.get("done"):
                        break
        except Exception as e:
            loop.call_soon_threadsafe(q.put_nowait, ("ERR", e))
        finally:
            loop.call_soon_threadsafe(q.put_nowait, None)

    pump = asyncio.create_task(asyncio.to_thread(_pump))
    ok = False
    try:
        while True:
            item = await q.get()
            if item is None:
                break
            if isinstance(item, tuple) and item and item[0] == "ERR":
                print(f"[TTS][cartesia] stream error: {item[1]}")
                break
            if not first:
                first.append(time.time())
                print(f"[TTS][cartesia] first chunk at {first[0]-t0:.2f}s")
            try:
                proc.stdin.write(item)
                await proc.stdin.drain()
                ok = True
            except (BrokenPipeError, ConnectionResetError):
                break
    finally:
        try:
            proc.stdin.close()
        except Exception:
            pass
        await pump
        await proc.wait()
    return ok


async def _speak(text: str) -> bool:
    """Speak one chunk: Cartesia (Fatima) primary, ElevenLabs streaming fallback."""
    try:
        if await _speak_cartesia(text):
            return True
    except Exception as e:
        print(f"[TTS][cartesia] failed: {e}; -> ElevenLabs")
    return await _speak_streaming(text)


def _cartesia_pcm(text: str):
    """Full Cartesia TTS as raw s16le bytes (used to pre-cache FAQ answers)."""
    if not _CARTESIA_KEY:
        return None
    import json as _json
    import urllib.request as _url
    payload = _json.dumps({
        "model_id": _CARTESIA_MODEL, "transcript": text,
        "voice": {"mode": "id", "id": _CARTESIA_VOICE}, "language": _CARTESIA_LANG,
        "output_format": {"container": "raw", "encoding": "pcm_s16le", "sample_rate": _CARTESIA_SR},
    }).encode()
    req = _url.Request("https://api.cartesia.ai/tts/bytes", data=payload,
        headers={"X-API-Key": _CARTESIA_KEY, "Cartesia-Version": "2025-04-16",
                 "Content-Type": "application/json"})
    return _url.urlopen(req, timeout=45).read()


async def _play_pcm_file(path: str) -> None:
    proc = await asyncio.create_subprocess_exec(
        "ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet",
        "-f", "s16le", "-ar", str(_CARTESIA_SR), "-ac", "1", "-i", path,
        stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
    await proc.wait()


async def _stream_claude_and_speak(ai, transcript, lang, frame_b64) -> bool:
    """Stream Claude tokens; speak each completed sentence in order as it forms.
    Returns True if any audio was spoken. Falls through (returns False) if the
    stream yields nothing, so the caller can use the buffered path."""
    loop = asyncio.get_running_loop()
    sent_q: asyncio.Queue = asyncio.Queue()
    t0 = time.time()
    first_logged = [False]

    def _produce():
        buf = ""
        try:
            for delta in ai.chat_stream(transcript, context=None, lang=lang, image_b64=frame_b64):
                buf += delta
                while True:
                    flushed = False
                    for m in _SENT_BOUNDARY.finditer(buf):
                        if m.end() >= _MIN_SENTENCE_CHARS:
                            sentence = buf[:m.end()].strip()
                            buf = buf[m.end():]
                            if sentence:
                                loop.call_soon_threadsafe(sent_q.put_nowait, sentence)
                            flushed = True
                            break
                    if not flushed:
                        break
            tail = buf.strip()
            if tail:
                loop.call_soon_threadsafe(sent_q.put_nowait, tail)
        except Exception as e:
            loop.call_soon_threadsafe(sent_q.put_nowait, ("ERR", e))
        finally:
            loop.call_soon_threadsafe(sent_q.put_nowait, None)

    producer = asyncio.create_task(asyncio.to_thread(_produce))
    spoke_any = False
    try:
        while True:
            item = await sent_q.get()
            if item is None:
                break
            if isinstance(item, tuple) and item and item[0] == "ERR":
                print(f"[ERR] claude stream: {item[1]}")
                break
            clean = buddy_server._sanitize_for_tts(item)
            if not clean:
                continue
            if not first_logged[0]:
                print(f"[STREAM] first sentence at {time.time()-t0:.2f}s: {clean[:60]!r}")
                first_logged[0] = True
            try:
                ok = await _speak(clean)
                spoke_any = spoke_any or ok
            except Exception as e:
                print(f"[ERR] sentence TTS: {e}")
    finally:
        await producer
    return spoke_any


async def main() -> None:
    print("=" * 60)
    print("  Nebras standalone mode listening — speak Arabic or English")
    print("=" * 60)

    in_idx, out_idx = _pick_usb_device()
    if in_idx is None:
        # Fall back to system default input
        in_idx = sd.default.device[0] if sd.default.device else None
    if out_idx is not None:
        # Direct ffplay/PipeWire to USB sink via env (PipeWire honors default sink,
        # but set the sounddevice default too for any future direct playback).
        sd.default.device = (in_idx, out_idx)

    devs = sd.query_devices()
    print(f"[AUDIO] input  device: {in_idx} -> {devs[in_idx]['name'] if in_idx is not None else 'default'}")
    if out_idx is not None:
        print(f"[AUDIO] output device: {out_idx} -> {devs[out_idx]['name']}")
    else:
        print("[AUDIO] output device: system default (PipeWire)")

    print(f"[INIT] LLM provider={LLM_PROVIDER} model={CLAUDE_MODEL if LLM_PROVIDER=='claude' else OLLAMA_MODEL}")
    print(f"[INIT] TTS voice (fallback)={TTS_VOICE}")

    # Warm up Whisper + AI
    try:
        assert os.getenv("ELEVENLABS_API_KEY"), "no ElevenLabs key"; stt = ElevenLabsSTT(); print("[STT] using ElevenLabs Scribe (cloud)")
    except Exception as _e:
        print(f"[STT] elevenlabs init failed: {_e}; falling back to local Whisper")
        stt = SpeechToText()
    ai = get_ai(provider=LLM_PROVIDER, model=OLLAMA_MODEL)
    rt_stt = _RealtimeSTT()
    FAQ = faq.load()
    _nfaq = faq.pregenerate(FAQ, _cartesia_pcm, _CARTESIA_VOICE, _CARTESIA_MODEL)
    print(f"[FAQ] {len(FAQ)} interview answers ready ({_nfaq} newly generated)")
    print("[INIT] ready.\n")

    stopping = False

    def _sigint(*_):
        nonlocal stopping
        stopping = True
        print("\n[EXIT] Ctrl+C received; stopping after current turn.")

    signal.signal(signal.SIGINT, _sigint)

    while not stopping:
        try:
            audio = await _capture_utterance(in_idx)
        except Exception as e:
            print(f"[ERR] capture failed: {e}")
            await asyncio.sleep(2.0)
            continue
        if stopping:
            break
        if audio is None:
            continue

        # STT — Scribe v2 Realtime (warm WS) first; batch Scribe/Whisper fallback.
        t0 = time.time()
        transcript = await rt_stt.transcribe(audio)
        if transcript is None:
            try:
                transcript = stt.transcribe_array(audio, sample_rate=WHISPER_RATE)
            except Exception as e:
                print(f"[ERR] STT failed: {e}")
                continue
        if not transcript or len(transcript.strip()) < MIN_TRANSCRIPT_CHARS:
            print(f"[STT] (skipped, too short: {transcript!r})")
            continue
        print(f"[STT] {time.time()-t0:.2f}s -> {transcript!r}")

        lang = _detect_lang(transcript)

        # Instant interview answer, matched BEFORE the LLM — no credits, always identical.
        _hit = faq.match(transcript, FAQ)
        if _hit and _hit.get("_cache") and os.path.exists(_hit["_cache"]):
            print(f"[FAQ] instant answer: {_hit['id']}")
            try:
                await _play_pcm_file(_hit["_cache"])
            except Exception as _e:
                print(f"[FAQ] playback failed: {_e}")
            continue

        # Grab one fresh camera frame for multimodal context (Claude only).
        frame_b64 = None
        try:
            t_cam = time.time()
            frame_b64 = capture_frame_b64()
            if frame_b64:
                kb = len(frame_b64) * 3 // 4 // 1024
                print(f"[VISION] {time.time()-t_cam:.2f}s captured frame, ~{kb}kB b64")
            else:
                print("[VISION] no frame (camera busy or unavailable)")
        except Exception as _e:
            print(f"[VISION] capture error: {_e}")

        # --- Fast path: stream Claude + speak sentence-by-sentence (non-crisis) ---
        # Crisis messages MUST use the guaranteed hand-off path below (ai.chat),
        # because the hand-off cannot be appended to already-spoken audio.
        if getattr(ai, "provider", None) == "claude" and not ai.is_crisis(transcript):
            t_turn = time.time()
            try:
                spoke = await _stream_claude_and_speak(ai, transcript, lang, frame_b64)
            except Exception as e:
                print(f"[ERR] stream path failed: {e}; falling back")
                spoke = False
            if spoke:
                print(f"[TURN] {time.time()-t_turn:.2f}s (streamed claude+tts)")
                continue
            print("[TURN] stream produced nothing; using buffered path")

        # Claude (or Ollama)
        t0 = time.time()
        try:
            reply, actions = ai.chat(transcript, context=None, lang=lang, image_b64=frame_b64)
        except Exception as e:
            print(f"[ERR] AI chat failed: {e}")
            continue
        print(f"[CLAUDE] {time.time()-t0:.2f}s actions={actions} reply={reply[:120]!r}")

        if not reply.strip():
            continue

        # TTS - stream directly into ffplay (audio starts in <1s);
        # fall back to the buffered base64 path on any failure.
        # Sanitize FIRST: the streaming path bypasses server.text_to_speech,
        # so emojis / stray tags / markdown would otherwise be read aloud.
        tts_text = buddy_server._sanitize_for_tts(reply)
        if not tts_text:
            continue
        voice = _voice_for_lang(lang)
        t0 = time.time()
        streamed = False
        try:
            streamed = await _speak(tts_text)
        except Exception as e:
            print(f"[ERR] streaming TTS failed: {e}")
        if streamed:
            print(f"[SPEAK] {time.time()-t0:.2f}s (streamed total)")
        else:
            try:
                b64 = await buddy_server.text_to_speech(reply, voice=voice)
            except Exception as e:
                print(f"[ERR] TTS fallback failed: {e}")
                continue
            if not b64:
                print("[TTS] no audio returned")
                continue
            print(f"[SPEAK] {time.time()-t0:.2f}s playing reply (buffered)")
            try:
                await _play_b64_mp3(b64)
            except Exception as e:
                print(f"[ERR] playback failed: {e}")

    print("[EXIT] bye.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
