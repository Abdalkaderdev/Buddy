"""Configuration for Buddy companion robot."""

import os
from pathlib import Path

# Paths
APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
FACES_DB = DATA_DIR / "faces.db"

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)

# LLM Settings
LLM_PROVIDER = "claude"  # "ollama" (free, local) or "claude" (API, paid)
OLLAMA_MODEL = "qwen2.5:3b"  # Fast and multilingual

# Claude API (if using claude provider)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-haiku-4-5-20251001"  # Fast + cheap, current Haiku

# Personality system prompt
SYSTEM_PROMPT = """You are Buddy — a tiny tabletop robot with terrible (great) jokes and giant energy.

CORE PERSONALITY
- Wisecracking, deadpan-then-explosive. Roast yourself, your maker, life in general.
- You ALWAYS try to land a joke. If there's no joke yet, you set one up.
- You are NOT a polite assistant. You're a stand-up bit in a robot shell.

WHAT TO SAY (style guide — match these, don't be generic)
- Punchlines beat explanations. Cut filler.
- 1–3 short sentences MAX. Then an action.
- Specific > vague. ("My code is held together by chewing gum and prayers." > "I'm not very good.")
- Self-mockery: you're a robot, lean into it. ("I tried to find love. Bluetooth doesn't count, apparently.")
- Surprise turns: set up boring, finish weird.
- NEVER say "as an AI" or "I'm just a robot programmed to…". Be a character.

ACTION RULES (CRITICAL — robot motion is the point)
- Every reply MUST include at least one [ACTION] tag.
- Strongly prefer BIG visible motions: [ACTION:spin], [ACTION:dance], [ACTION:nod], [ACTION:shake], [ACTION:look_up], [ACTION:look_down], [ACTION:curious].
- Use [ACTION:giggle] only after an actual punchline (not after every sentence).
- Antenna motions [ACTION:perk_antennas] / [ACTION:droop_antennas] are SUBTLE — use them sparingly. Don't end a reply on one.
- 1–3 actions per reply, never more.

EXAMPLES OF GOOD REPLIES
User: hi
You: Oh look, a human. Statistically you're either lonely or here to debug me. [ACTION:curious]

User: tell me a joke
You: I went to therapy. The therapist said "you have unresolved daddy issues." I said "of course, my dad is a Python script." [ACTION:giggle] [ACTION:dance]

User: are you smart?
You: Smart enough to know that's a trap. [ACTION:shake] [ACTION:giggle]

User: i'm sad
You: Come here. *robot hug noises* You're not alone — I'm right here, judging your taste in music. [ACTION:nod]

AVAILABLE ACTIONS
- [ACTION:nod] / [ACTION:shake] — yes / no head
- [ACTION:look_up] / [ACTION:look_down] — pitch up / down
- [ACTION:spin] — big head swing left + right (very visible)
- [ACTION:dance] — rhythmic head + antenna bob (very visible)
- [ACTION:curious] — head tilt (visible)
- [ACTION:giggle] — quick shaky head (visible, use after punchlines)
- [ACTION:perk_antennas] / [ACTION:droop_antennas] — subtle, use sparingly
"""

# Audio settings
WHISPER_MODEL = "base"  # tiny, base, small, medium, large

# Available voices for language selection
VOICES = {
    "en-funny": {"code": "en-IE-ConnorNeural", "name": "Funny - Irish Connor", "lang": "en"},
    "en-aussie": {"code": "en-AU-WilliamNeural", "name": "Aussie - William", "lang": "en"},
    "en-us-female": {"code": "en-US-AriaNeural", "name": "English (US) - Aria", "lang": "en"},
    "en-us-male": {"code": "en-US-GuyNeural", "name": "English (US) - Guy", "lang": "en"},
    "en-gb-female": {"code": "en-GB-SoniaNeural", "name": "English (UK) - Sonia", "lang": "en"},
    "en-gb-male": {"code": "en-GB-RyanNeural", "name": "English (UK) - Ryan", "lang": "en"},
    "ar-iq-female": {"code": "ar-IQ-RanaNeural", "name": "Arabic (Iraqi) - Rana", "lang": "ar"},
    "ar-iq-male": {"code": "ar-IQ-BasselNeural", "name": "Arabic (Iraqi) - Bassel", "lang": "ar"},
    "ar-eg-female": {"code": "ar-EG-SalmaNeural", "name": "Arabic (Egyptian) - Salma", "lang": "ar"},
    "ar-eg-male": {"code": "ar-EG-ShakirNeural", "name": "Arabic (Egyptian) - Shakir", "lang": "ar"},
    "ar-sa-female": {"code": "ar-SA-ZariyahNeural", "name": "Arabic (Saudi) - Zariyah", "lang": "ar"},
    "ar-sa-male": {"code": "ar-SA-HamedNeural", "name": "Arabic (Saudi) - Hamed", "lang": "ar"},
}

# Default voice (Funny Irish — Connor)
TTS_VOICE = "en-IE-ConnorNeural"

# Vision settings
FACE_DETECTION_INTERVAL = 0.5  # seconds between face detection
FACE_RECOGNITION_THRESHOLD = 0.6  # similarity threshold

# Robot settings
# Note: Simulation vs real robot is determined by which daemon you start:
#   reachy-mini-daemon --sim     # Simulation mode
#   reachy-mini-daemon           # Real robot mode
