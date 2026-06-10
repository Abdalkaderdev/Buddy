"""Web server for Buddy - chat via browser."""

import asyncio
import base64
import os
import tempfile
import threading
import time
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

try:
    from reachy_mini import ReachyMini
    ROBOT_AVAILABLE = True
except ImportError:
    ROBOT_AVAILABLE = False

from .ai import get_ai
from .motion import BuddyMotion
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
clients: list[WebSocket] = []

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
    """Convert text to speech and return base64 encoded audio."""
    print(f"[TTS] Generating speech with voice: {voice}")
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

    print("Buddy is ready!")


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


@app.post("/api/transcribe")
async def transcribe(audio: UploadFile = File(...), lang: str = "en"):
    """Whisper STT endpoint — alternative to browser Web Speech.

    Frontend POSTs a WAV/WebM blob recorded via MediaRecorder; we save it,
    run faster-whisper on it, return JSON {text: "..."}.

    Used on the Pi where browser Web Speech isn't reliable.
    """
    from .audio import get_stt
    stt = get_stt()
    if stt.model is None:
        return {"error": "Whisper not available (install faster-whisper)"}

    suffix = ".webm" if (audio.content_type or "").endswith("webm") else ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        f.write(await audio.read())
        path = f.name
    try:
        text = stt.transcribe(path)
        return {"text": text}
    finally:
        try:
            Path(path).unlink()
        except Exception:
            pass


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
    await websocket.accept()
    clients.append(websocket)

    # Default settings for this connection - use funny Irish voice
    user_settings[websocket] = {
        "voice": "en-funny",
        "voice_code": VOICES["en-funny"]["code"],
        "lang": "en"
    }

    # Send welcome message
    welcome_text = "Hey! I'm Buddy, your playful robot companion! How can I help you today?"
    welcome_audio = await text_to_speech(welcome_text, user_settings[websocket]["voice_code"])
    await websocket.send_json({
        "type": "message",
        "role": "assistant",
        "content": welcome_text,
        "actions": ["perk_antennas"],
        "audio": welcome_audio
    })

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

                if user_message.strip():
                    # Get AI response with current language setting
                    lang = user_settings[websocket].get("lang", "en")
                    voice_key = user_settings[websocket].get("voice", "en-us-female")
                    voice_code = user_settings[websocket]["voice_code"]
                    print(f"[SERVER] Chat request - lang={lang}, voice={voice_key}, code={voice_code}")

                    # Inject what the camera sees right now
                    context = _camera_context() if ENABLE_CAMERA else None
                    response, actions = ai.chat(user_message, context=context, lang=lang)
                    print(f"[SERVER] AI response: {response[:50]}...")

                    # Execute robot actions
                    if motion and actions:
                        print(f"[SERVER] Executing robot actions: {actions}")
                        for action in actions:
                            try:
                                await motion.execute_action(action)
                            except Exception as e:
                                print(f"[SERVER] Action error: {e}")

                    # Generate speech with selected voice
                    print(f"[SERVER] Generating TTS with voice: {voice_code}")
                    audio_data = await text_to_speech(response, voice_code)

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
        clients.remove(websocket)
        if websocket in user_settings:
            del user_settings[websocket]


# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def main():
    """Run the web server."""
    print("\n" + "=" * 50)
    print("  BUDDY - Web Interface")
    print("=" * 50)
    print("\nOpen your browser to: http://localhost:8080")
    print("Press Ctrl+C to stop\n")

    uvicorn.run(app, host="0.0.0.0", port=8080)


if __name__ == "__main__":
    main()
