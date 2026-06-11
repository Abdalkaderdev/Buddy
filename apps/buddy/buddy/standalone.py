"""Sara standalone always-on listening loop.

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

RMS_THRESHOLD = 0.08         # tweak for ambient noise (USB mic on Pi runs hot)
MIN_SPEECH_MS = 600           # must have this much speech before we accept utterance
SILENCE_HANGOVER_MS = 800    # silence after speech => end of utterance
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
async def main() -> None:
    print("=" * 60)
    print("  Sara standalone mode listening — speak Arabic or English")
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
        stt = ElevenLabsSTT(); print("[STT] using ElevenLabs Scribe (cloud)")
    except Exception as _e:
        print(f"[STT] elevenlabs init failed: {_e}; falling back to local Whisper")
        stt = SpeechToText()
    ai = get_ai(provider=LLM_PROVIDER, model=OLLAMA_MODEL)
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

        # STT — let Whisper auto-detect language
        t0 = time.time()
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
            streamed = await _speak_streaming(tts_text)
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
