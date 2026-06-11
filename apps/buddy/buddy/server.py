"""Web server for Buddy - chat via browser."""

import asyncio
import base64
import os
import re
import tempfile
import threading
import time

# Arabic Unicode ranges — used to detect when Claude replied in Arabic so we can
# pick the right TTS voice regardless of which voice the user selected in the UI.
_ARABIC_RE = re.compile(r"[؀-ۿݐ-ݿࢠ-ࣿﭐ-﷿ﹰ-﻿]")


def _detect_lang(text: str) -> str:
    """Return 'ar' if the text contains Arabic script, else 'en'."""
    return "ar" if _ARABIC_RE.search(text) else "en"


def _pick_voice_for_lang(detected: str, current_voice_key: str) -> tuple[str, str]:
    """If Claude's reply language differs from the current voice's language,
    fall back to a sane default voice for that language. Returns (key, edge_tts_code)."""
    current_lang = VOICES.get(current_voice_key, {}).get("lang", "en")
    if detected == current_lang:
        return current_voice_key, VOICES[current_voice_key]["code"]
    # Mismatch — pick a default for the detected language
    fallback = "ar-iq-female" if detected == "ar" else "en-us-female"
    return fallback, VOICES[fallback]["code"]
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

try:
    import edge_tts
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

# ElevenLabs is the preferred TTS when ELEVENLABS_API_KEY is set.
# Falls back to edge_tts (free, lower quality) otherwise.
try:
    from elevenlabs.client import ElevenLabs
    ELEVENLABS_SDK_AVAILABLE = True
except ImportError:
    ELEVENLABS_SDK_AVAILABLE = False

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "rFDdsCQRZCUL8cPOWtnP")
# turbo_v2_5 is ~3x faster than multilingual_v2 and still supports Arabic + English.
ELEVENLABS_MODEL = os.getenv("ELEVENLABS_MODEL", "eleven_turbo_v2_5")
_eleven_client = None

# ---- Caches ----
# TTS cache: same text → same audio. Saves ElevenLabs credits AND makes
# repeated greetings instant. Bounded LRU.
import hashlib
import collections
_TTS_CACHE: "collections.OrderedDict[str, str]" = collections.OrderedDict()
_TTS_CACHE_MAX = 80

def _tts_cache_key(text: str, voice_id: str) -> str:
    return hashlib.sha256(f"{voice_id}::{text}".encode("utf-8")).hexdigest()[:32]

def _tts_cache_get(text: str, voice_id: str) -> str | None:
    key = _tts_cache_key(text, voice_id)
    if key in _TTS_CACHE:
        _TTS_CACHE.move_to_end(key)
        return _TTS_CACHE[key]
    return None

def _tts_cache_put(text: str, voice_id: str, audio_b64: str) -> None:
    key = _tts_cache_key(text, voice_id)
    _TTS_CACHE[key] = audio_b64
    _TTS_CACHE.move_to_end(key)
    while len(_TTS_CACHE) > _TTS_CACHE_MAX:
        _TTS_CACHE.popitem(last=False)


def _get_eleven_client():
    global _eleven_client
    if _eleven_client is None and ELEVENLABS_API_KEY and ELEVENLABS_SDK_AVAILABLE:
        _eleven_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
    return _eleven_client


async def _tts_elevenlabs(text: str) -> str | None:
    """Synthesize via ElevenLabs Multilingual v2. Returns base64 mp3 or None.
    Cached by (voice_id, text) — repeated phrases are instant + free."""
    client = _get_eleven_client()
    if not client:
        return None

    cached = _tts_cache_get(text, ELEVENLABS_VOICE_ID)
    if cached is not None:
        print(f"[TTS][elevenlabs] cache hit ({len(text)} chars)")
        return cached

    def _gen():
        chunks = client.text_to_speech.convert(
            voice_id=ELEVENLABS_VOICE_ID,
            text=text,
            model_id=ELEVENLABS_MODEL,
            output_format="mp3_44100_128",
        )
        return b"".join(chunks)

    try:
        audio = await asyncio.to_thread(_gen)
        b64 = base64.b64encode(audio).decode("utf-8")
        _tts_cache_put(text, ELEVENLABS_VOICE_ID, b64)
        return b64
    except Exception as e:
        # Sanitize the key out of the error message
        msg = str(e)
        if ELEVENLABS_API_KEY:
            msg = msg.replace(ELEVENLABS_API_KEY, "***")
        print(f"[TTS][elevenlabs] error: {type(e).__name__}: {msg} — falling back to edge_tts")
        return None

try:
    from reachy_mini import ReachyMini
    from .motion import BuddyMotion
    ROBOT_AVAILABLE = True
except ImportError:
    ReachyMini = None
    BuddyMotion = None
    ROBOT_AVAILABLE = False

from .ai import get_ai
from .config import LLM_PROVIDER, OLLAMA_MODEL, TTS_VOICE, VOICES

app = FastAPI(title="Buddy - Companion Robot")

# Get the static files directory
STATIC_DIR = Path(__file__).parent / "static"

# AI instance
ai = None

# Robot instance
robot = None
motion = None

# Connected websocket clients
clients: set[WebSocket] = set()

# ---- Guardrails ----
# Per-WebSocket sliding-window rate limit for chat messages.
# Max RATE_LIMIT_MAX messages per RATE_LIMIT_WINDOW seconds.
RATE_LIMIT_MAX = 12
RATE_LIMIT_WINDOW = 60.0
_chat_timestamps: dict[WebSocket, "collections.deque[float]"] = {}

# Hard cap on inbound user message length (chars). Anything longer is rejected.
MAX_USER_MESSAGE_CHARS = 2000

# Safety-net cap on LLM output sent to TTS (chars). Prevents runaway replies
# from burning ElevenLabs credits or saturating the audio channel.
MAX_RESPONSE_CHARS = 1500

# Origin allowlist for WebSocket connections. A loose Tailscale 100.x.x.x match
# is also permitted so the user's own devices on the tailnet still work.
ALLOWED_ORIGINS = {
    "https://buddy.local:8080",
    "https://localhost:8080",
    "https://127.0.0.1:8080",
}
_TAILSCALE_ORIGIN_RE = re.compile(r"^https?://100\.\d+\.\d+\.\d+(:\d+)?$")


def _origin_allowed(origin: str | None) -> bool:
    """Return True if the WebSocket Origin header is on the allowlist."""
    if not origin:
        # No origin header (e.g. native client / curl) — allow, since the
        # browser cross-origin attack vector requires an origin header.
        return True
    if origin in ALLOWED_ORIGINS:
        return True
    if _TAILSCALE_ORIGIN_RE.match(origin):
        return True
    return False

# Camera face-detection state — written by the camera worker thread,
# read by the chat handler to inject context into Claude prompts.
ENABLE_CAMERA = os.getenv("BUDDY_CAMERA", "1") == "1"
CAMERA_INDEX = int(os.getenv("BUDDY_CAMERA_INDEX", "0"))
_camera_state = {"face": None, "last_seen": 0.0}
_camera_state_lock = threading.Lock()


def _camera_worker():
    """Background thread: grab frames from USB webcam and run face detection."""
    try:
        import cv2
        from .vision import get_detector
    except Exception as e:
        print(f"[CAMERA] disabled — opencv/vision unavailable: {e}")
        return

    detector = get_detector()
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print(f"[CAMERA] could not open device index {CAMERA_INDEX} — disabling")
        return
    print(f"[CAMERA] worker started on index {CAMERA_INDEX}")

    while True:
        ok, frame = cap.read()
        if not ok:
            time.sleep(0.5)
            continue
        try:
            faces = detector.detect_faces(frame)
        except Exception as e:
            print(f"[CAMERA] detect error: {e}")
            faces = []
        with _camera_state_lock:
            if faces:
                # Prefer a recognized face over "unknown"
                named = [f for f in faces if f.get("name") and f["name"] != "unknown"]
                pick = (named or faces)[0]
                _camera_state["face"] = pick["name"]
                _camera_state["last_seen"] = time.time()
            else:
                # Decay: forget face after 5s of empty frames
                if time.time() - _camera_state["last_seen"] > 5:
                    _camera_state["face"] = None
        time.sleep(2.0)  # ~0.5 Hz is plenty for companion-robot context


def _camera_context() -> dict:
    """Snapshot for AI context."""
    with _camera_state_lock:
        face = _camera_state["face"]
    if face is None:
        return {"no_face": True}
    if face == "unknown":
        return {"detected_face": "unknown"}
    return {"detected_face": face}


async def text_to_speech(text: str, voice: str = TTS_VOICE) -> str | None:
    """Convert text to speech and return base64-encoded MP3.

    Prefers ElevenLabs (Multilingual v2) when ELEVENLABS_API_KEY is set,
    falls back to edge-tts (free) otherwise. The `voice` argument is only
    used for edge-tts; ElevenLabs uses ELEVENLABS_VOICE_ID.
    """
    if ELEVENLABS_API_KEY and ELEVENLABS_SDK_AVAILABLE:
        print(f"[TTS][elevenlabs] voice={ELEVENLABS_VOICE_ID} chars={len(text)}")
        result = await _tts_elevenlabs(text)
        if result is not None:
            return result
        # fall through to edge_tts on failure

    print(f"[TTS][edge] Generating speech with voice: {voice}")
    if not TTS_AVAILABLE:
        return None

    try:
        # Create temp file for audio
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            temp_path = f.name

        # Generate speech
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(temp_path)

        # Read and encode as base64
        with open(temp_path, "rb") as f:
            audio_data = base64.b64encode(f.read()).decode("utf-8")

        # Clean up temp file
        Path(temp_path).unlink()

        return audio_data
    except Exception as e:
        print(f"TTS error: {e}")
        return None


# Store user settings per connection
user_settings: dict[WebSocket, dict] = {}


@app.on_event("startup")
async def startup():
    """Initialize AI and robot on startup."""
    global ai, robot, motion
    print("Initializing Buddy AI...")
    ai = get_ai(provider=LLM_PROVIDER, model=OLLAMA_MODEL)

    # Connect to robot
    if ROBOT_AVAILABLE:
        try:
            print("Connecting to Reachy Mini...")
            robot = ReachyMini(media_backend="no_media")
            robot.__enter__()  # Start the connection
            motion = BuddyMotion(robot)
            print("Robot connected!")
        except Exception as e:
            print(f"Could not connect to robot: {e}")
            print("Running in chat-only mode (no robot movements)")
            robot = None
            motion = None
    else:
        print("ReachyMini SDK not available - running in chat-only mode")

    # Start camera face-detection worker (USB webcam → context for Claude)
    if ENABLE_CAMERA:
        t = threading.Thread(target=_camera_worker, daemon=True, name="buddy-camera")
        t.start()
    else:
        print("[CAMERA] disabled via BUDDY_CAMERA=0")

    # Pre-warm Whisper model so the FIRST user STT call doesn't pay model-load latency
    threading.Thread(target=_prewarm_whisper, daemon=True, name="buddy-prewarm-stt").start()
    # Pre-warm TTS cache. Await it so the cache is hot BEFORE the first connection;
    # also avoids the OrderedDict thread-safety race between prewarm and live writes.
    try:
        await asyncio.wait_for(_prewarm_tts(), timeout=30)
    except (asyncio.TimeoutError, Exception) as e:
        print(f"[TTS] pre-warm timed out or errored: {e} — continuing")

    print("Buddy is ready!")


def _prewarm_whisper():
    """Load Whisper model into RAM on startup so first user call is instant."""
    try:
        from .audio import get_stt
        t0 = time.time()
        get_stt()  # forces model load
        print(f"[STT] Whisper pre-warmed in {time.time() - t0:.1f}s")
    except Exception as e:
        print(f"[STT] Pre-warm failed (will load lazily): {e}")


# Common short phrases Buddy is likely to say first.
# These get TTS-generated at boot and cached, so the very first reply of a
# demo is instant (no ElevenLabs round-trip needed).
PREWARM_PHRASES = [
    "هلا! أنا بَدي، شلونك اليوم؟",
    "هلا بيك",
    "اي والله",
    "زين، تره خوش سؤال",
    "هاي والله شكلها سهلة بس قوية",
    "خوش، خل نبدأ",
    "اوكي خل نشتغلها سوا",
    "Hey! I'm Buddy, how are you today?",
    "Sure, let's do it.",
    "Good question.",
]


async def _prewarm_tts():
    """Run a few common phrases through ElevenLabs in the background so the
    cache is hot before the user's first interaction. Failures are silent."""
    if not (ELEVENLABS_API_KEY and ELEVENLABS_SDK_AVAILABLE):
        return
    # Tiny delay so we don't block startup
    await asyncio.sleep(2)
    for phrase in PREWARM_PHRASES:
        try:
            t0 = time.time()
            audio = await _tts_elevenlabs(phrase)
            if audio:
                print(f"[TTS] pre-warmed ({len(phrase)} chars) in {time.time()-t0:.1f}s")
        except Exception as e:
            print(f"[TTS] pre-warm error for {phrase[:20]!r}: {e}")
        await asyncio.sleep(0.3)  # gentle pacing for ElevenLabs free tier
    print("[TTS] pre-warm complete — cache primed")


@app.on_event("shutdown")
async def shutdown():
    """Release robot connection on shutdown."""
    global robot
    if robot is not None:
        try:
            robot.__exit__(None, None, None)
        except Exception as e:
            print(f"[SHUTDOWN] Robot cleanup error: {e}")
        robot = None


@app.get("/")
async def root():
    """Serve the main page."""
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/voices")
async def get_voices():
    """Return available voices."""
    return VOICES


MAX_AUDIO_UPLOAD = 5 * 1024 * 1024  # 5 MB ≈ ~60s of opus/webm. Cap blocks DoS.


@app.post("/api/transcribe")
async def transcribe(audio: UploadFile = File(...), lang: str = "en"):
    """Whisper STT endpoint — Pi-friendly replacement for browser Web Speech.

    Streams the upload to a temp file with a hard size cap, runs faster-whisper,
    returns {"text": "..."} or {"error": "..."} on failure (never an opaque 500).
    """
    from .audio import get_stt

    ctype = (audio.content_type or "").lower()
    if not (ctype.startswith("audio/") or ctype.startswith("video/webm") or ctype.startswith("application/octet-stream")):
        return {"error": f"audio required, got content-type={ctype!r}"}

    stt = get_stt()
    if stt.model is None:
        return {"error": "Whisper not available (install faster-whisper)"}

    suffix = ".webm" if "webm" in ctype else ".wav"
    path = None
    try:
        # Stream upload to disk with size cap so a 10 GB POST can't OOM the Pi
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
            path = f.name
            total = 0
            while True:
                chunk = await audio.read(64 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_AUDIO_UPLOAD:
                    f.close()
                    Path(path).unlink(missing_ok=True)
                    return {"error": f"audio too large (cap {MAX_AUDIO_UPLOAD // 1024} KB)"}
                f.write(chunk)
        try:
            t0 = time.time()
            # Map UI lang code to Whisper language code (None = auto-detect)
            whisper_lang = None
            if lang and lang.startswith("ar"):
                whisper_lang = "ar"
            elif lang and lang.startswith("en"):
                whisper_lang = "en"
            text = stt.transcribe(path, language=whisper_lang)
            print(f"[TIMING] STT took {time.time()-t0:.2f}s  hint={whisper_lang}  -> {text[:60]!r}")
            return {"text": text, "language": whisper_lang}
        except Exception as e:
            import traceback
            print(f"[TRANSCRIBE] {type(e).__name__}: {e}\n{traceback.format_exc()}")
            return {"error": f"transcription failed: {type(e).__name__}: {e}"}
    finally:
        if path:
            try:
                Path(path).unlink()
            except FileNotFoundError:
                pass
            except Exception as e:
                print(f"[TRANSCRIBE] temp cleanup failed: {path}: {e}")


@app.get("/api/camera-state")
async def camera_state():
    """Debug: what does Buddy currently see?"""
    return {"enabled": ENABLE_CAMERA, **_camera_context()}


@app.get("/api/test-voice/{voice_key}")
async def test_voice(voice_key: str):
    """Test a specific voice."""
    from fastapi.responses import Response
    if voice_key not in VOICES:
        return {"error": "Voice not found"}

    voice_code = VOICES[voice_key]["code"]
    print(f"[TEST] Testing voice: {voice_key} -> {voice_code}")

    text = "مرحبا، أنا بادي" if "ar" in voice_key else "Hello, I am Buddy"
    audio = await text_to_speech(text, voice_code)

    if audio:
        import base64
        audio_bytes = base64.b64decode(audio)
        return Response(content=audio_bytes, media_type="audio/mpeg")
    return {"error": "TTS failed"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Handle WebSocket connections for real-time chat."""
    # Origin allowlist — reject cross-origin pages on the same Wi-Fi from
    # driving Buddy's chat. Tailscale 100.x.x.x origins are accepted.
    origin = websocket.headers.get("origin")
    if not _origin_allowed(origin):
        print(f"[WS] rejected connection — disallowed origin: {origin!r}")
        await websocket.close(code=1008)
        return

    await websocket.accept()
    clients.add(websocket)
    _chat_timestamps[websocket] = collections.deque()

    # Default: Iraqi Arabic. Switches language automatically as user speaks.
    default_voice = "ar-iq-female"
    user_settings[websocket] = {
        "voice": default_voice,
        "voice_code": VOICES[default_voice]["code"],
        "lang": VOICES[default_voice]["lang"],
    }

    # Welcome message in Arabic — wrapped so a TTS failure here doesn't
    # kill the whole connection before chat can start.
    try:
        welcome_text = "هلا! أنا بَدي، صديقك الروبوت. شلونك اليوم؟"
        welcome_audio = await text_to_speech(welcome_text, user_settings[websocket]["voice_code"])
        await websocket.send_json({
            "type": "message",
            "role": "assistant",
            "content": welcome_text,
            "actions": ["perk_antennas"],
            "audio": welcome_audio
        })
    except Exception as e:
        print(f"[WS] welcome send failed: {type(e).__name__}: {e} — continuing without greeting")

    # Send available voices
    await websocket.send_json({
        "type": "voices",
        "voices": VOICES
    })

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            if data.get("type") == "chat":
                user_message = data.get("message", "")

                # --- Guardrail: per-ws sliding-window rate limit ---
                now = time.time()
                dq = _chat_timestamps.setdefault(websocket, collections.deque())
                while dq and now - dq[0] > RATE_LIMIT_WINDOW:
                    dq.popleft()
                if len(dq) >= RATE_LIMIT_MAX:
                    is_ar = user_settings.get(websocket, {}).get("lang", "en") == "ar"
                    msg = "شوي مهلة" if is_ar else "Slow down a moment"
                    await websocket.send_json({"type": "system", "content": msg})
                    print(f"[WS] rate-limited ({len(dq)} msgs in {RATE_LIMIT_WINDOW}s)")
                    continue
                dq.append(now)

                # --- Guardrail: user message length cap ---
                if len(user_message) > MAX_USER_MESSAGE_CHARS:
                    is_ar = user_settings.get(websocket, {}).get("lang", "en") == "ar"
                    msg = ("رسالتك طويلة، اختصرها شوي"
                           if is_ar else "Message too long, please shorten")
                    await websocket.send_json({"type": "system", "content": msg})
                    print(f"[WS] rejected oversized message ({len(user_message)} chars)")
                    continue

                if user_message.strip():
                    # Get AI response with current language setting
                    lang = user_settings[websocket].get("lang", "en")
                    voice_key = user_settings[websocket].get("voice", "en-us-female")
                    voice_code = user_settings[websocket]["voice_code"]
                    print(f"[SERVER] Chat request - lang={lang}, voice={voice_key}, code={voice_code}")

                    # Inject what the camera sees right now
                    context = _camera_context() if ENABLE_CAMERA else None
                    t_ai = time.time()
                    response, actions = ai.chat(user_message, context=context, lang=lang)
                    print(f"[TIMING] ai.chat took {time.time()-t_ai:.2f}s; response={response[:50]!r}")

                    # --- Guardrail: clip overly long LLM output before TTS ---
                    if len(response) > MAX_RESPONSE_CHARS:
                        print(f"[WS] clipping response from {len(response)} -> {MAX_RESPONSE_CHARS} chars")
                        response = response[:MAX_RESPONSE_CHARS].rstrip() + "…"

                    # Execute robot actions
                    if motion and actions:
                        print(f"[SERVER] Executing robot actions: {actions}")
                        for action in actions:
                            try:
                                await motion.execute_action(action)
                            except Exception as e:
                                print(f"[SERVER] Action error: {e}")

                    # Auto-select voice based on Claude's response language so
                    # an Arabic reply doesn't get spoken by an English voice.
                    detected = _detect_lang(response)
                    tts_voice_key, tts_voice_code = _pick_voice_for_lang(detected, voice_key)
                    if tts_voice_key != voice_key:
                        print(f"[SERVER] Reply lang={detected} -> override voice to {tts_voice_key}")
                    t_tts = time.time()
                    audio_data = await text_to_speech(response, tts_voice_code)
                    print(f"[TIMING] TTS took {time.time()-t_tts:.2f}s  (audio={'yes' if audio_data else 'NONE'})")

                    # Send response back
                    await websocket.send_json({
                        "type": "message",
                        "role": "assistant",
                        "content": response,
                        "actions": actions,
                        "audio": audio_data
                    })

            elif data.get("type") == "set_voice":
                voice_key = data.get("voice", "en-us-female")
                if voice_key in VOICES:
                    user_settings[websocket]["voice"] = voice_key
                    user_settings[websocket]["voice_code"] = VOICES[voice_key]["code"]
                    user_settings[websocket]["lang"] = VOICES[voice_key]["lang"]
                    print(f"[SERVER] Voice changed to: {voice_key} -> {VOICES[voice_key]['code']}, lang={VOICES[voice_key]['lang']}")

                    # Set AI language and reset conversation
                    ai.set_language(VOICES[voice_key]["lang"])
                    ai.reset_conversation()

                    # Confirm voice change
                    voice_name = VOICES[voice_key]["name"]
                    if VOICES[voice_key]["lang"] == "ar":
                        confirm_text = "مرحبا! أنا بادي، صديقك الروبوت. شلونك اليوم؟"
                    else:
                        confirm_text = f"Voice changed to {voice_name}. Hello, I'm Buddy!"

                    audio_data = await text_to_speech(confirm_text, VOICES[voice_key]["code"])
                    await websocket.send_json({
                        "type": "system",
                        "content": f"Voice: {voice_name}" + (" 🇮🇶" if "IQ" in VOICES[voice_key]["code"] else ""),
                        "audio": audio_data
                    })

            elif data.get("type") == "reset":
                ai.reset_conversation()
                await websocket.send_json({
                    "type": "system",
                    "content": "Conversation reset! Let's start fresh."
                })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[WS] unexpected error: {type(e).__name__}: {e}")
    finally:
        clients.discard(websocket)
        user_settings.pop(websocket, None)
        _chat_timestamps.pop(websocket, None)


# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def main():
    """Run the web server. Uses HTTPS if BUDDY_SSL_CERT / BUDDY_SSL_KEY are set."""
    print("\n" + "=" * 50)
    print("  BUDDY - Web Interface")
    print("=" * 50)

    cert = os.getenv("BUDDY_SSL_CERT")
    key = os.getenv("BUDDY_SSL_KEY")
    use_https = bool(cert and key and os.path.exists(cert) and os.path.exists(key))
    scheme = "https" if use_https else "http"

    print(f"\nOpen your browser to: {scheme}://buddy.local:8080  or  {scheme}://localhost:8080")
    if use_https:
        print("(self-signed cert — accept the browser warning the first time)")
    else:
        print("(HTTP only — browser will block the microphone unless on localhost)")
    print("Press Ctrl+C to stop\n")

    if use_https:
        uvicorn.run(app, host="0.0.0.0", port=8080,
                    ssl_certfile=cert, ssl_keyfile=key)
    else:
        uvicorn.run(app, host="0.0.0.0", port=8080)


if __name__ == "__main__":
    main()
