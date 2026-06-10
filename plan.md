# Interactive Companion Robot - Project Plan

## Overview
Build an interactive companion robot that:
- Chats conversationally using an LLM
- Recognizes people using computer vision
- Reacts emotionally with expressive motions

**Hardware:** DIY Reachy Mini (3D printed body + purchased electronics)
**Compute Strategy:** Heavy processing on laptop, commands sent to robot via WiFi

---

## Phase 0: Hardware Build (DIY)

### 3D Printing
- [ ] Print all parts from `3d_print_files/` folder
- [ ] Post-process (sand, paint if desired)
- [ ] Test-fit parts before electronics

### Electronics Assembly
- [ ] Order components (see `3d_print_files/BOM.md`)
- [ ] Flash motor firmware
- [ ] Wire Dynamixel chain (TTL bus)
- [ ] Set up CM4 with Reachy Mini OS
- [ ] Test each motor individually
- [ ] Assemble Stewart platform
- [ ] Final assembly

### Verification
- [ ] Connect to robot via WiFi
- [ ] Run basic movement test
- [ ] Verify camera/mic work

---

## Core Features

### 1. Conversational AI
- **Speech-to-Text:** Local Whisper model (faster-whisper or OpenAI whisper)
- **LLM:** Anthropic Claude API (claude-3.5-sonnet or claude-3-haiku)
- **Text-to-Speech:** edge-tts or pyttsx3 for voice output
- Conversation flow: Listen → Transcribe → Claude → Speak

### 2. Face Recognition
- Detect faces in camera stream (OpenCV)
- Recognize known people (face_recognition library or similar)
- Remember names and past interactions
- Greet returning users by name

### 3. Emotional Reactions
- Map conversation context to emotions
- Play emotion animations from reachy-mini-emotions-library
- React to face detection (look at person, perk up when someone approaches)
- Idle behaviors when alone

---

## Technical Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      LAPTOP                                 │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Camera     │    │     LLM      │    │   Motion     │  │
│  │  Processor   │───→│   (OpenAI)   │───→│   Queue      │  │
│  │              │    │              │    │              │  │
│  │ - Face det.  │    │ - Realtime   │    │ - goto cmds  │  │
│  │ - Face recog │    │ - Tools      │    │ - emotions   │  │
│  │ - Tracking   │    │ - Context    │    │ - tracking   │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         ↑                   ↑                   │          │
└─────────│───────────────────│───────────────────│──────────┘
          │                   │                   │
          │            WiFi Connection            │
          │                   │                   │
          ↓                   ↓                   ↓
┌─────────────────────────────────────────────────────────────┐
│                  REACHY MINI (Wireless)                     │
│                                                             │
│     Camera ──────────────────────────→ Motors               │
│     (stream)                           (receive commands)   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: Foundation
- [ ] Create app using conversation template
- [ ] Verify basic conversation works
- [ ] Test camera streaming from robot to laptop

### Phase 2: Face Detection
- [ ] Add OpenCV face detection to camera pipeline
- [ ] Implement head tracking (look at detected face)
- [ ] Test detection reliability

### Phase 3: Face Recognition
- [ ] Integrate face_recognition library
- [ ] Create known_faces database (store embeddings + names)
- [ ] Add enrollment flow ("What's your name?")
- [ ] Test recognition accuracy

### Phase 4: Emotional Integration
- [ ] Create emotion mapping (context → emotion)
- [ ] Add LLM tools for emotions and reactions
- [ ] Implement idle behaviors
- [ ] Add greeting behavior for recognized faces

### Phase 5: Polish
- [ ] Create landing page for HuggingFace
- [ ] Test full interaction loop
- [ ] Document setup instructions
- [ ] Record demo video

---

## Questions to Clarify

Please answer these before we start coding:

### Q1: LLM Provider
**Answer: Ollama (default, free/local) with Anthropic Claude as fallback**

Code defaults to Ollama (`qwen2.5:3b`) for zero-cost local inference.
Set `LLM_PROVIDER = "claude"` in `apps/buddy/buddy/config.py` to use the API.

Stack:
- Local speech-to-text (faster-whisper)
- Ollama or Claude for conversation
- Local text-to-speech (edge-tts)

### Q2: Face Recognition Scope
**Answer: Many people (classroom/event scale)**

Using SQLite database for:
- Face embeddings
- Names and metadata
- Interaction history

### Q3: Personality
**Answer: Playful companion**

System prompt will emphasize:
- Jokes and humor
- Casual language
- Fun interactions
- Expressive emotions

### Q4: Privacy Considerations
**Answer: TBD** - Local storage recommended for classroom use

### Q5: Deadline
**Answer: 1+ month**

Plenty of time for full features and polish.

---

## Dependencies

```
# Core
reachy-mini

# LLM (pick one or both)
ollama              # Local LLM (default)
anthropic           # Claude API (optional)

# Speech
faster-whisper      # Local speech-to-text
edge-tts            # Text-to-speech (Microsoft voices, free)
sounddevice         # Audio capture/playback
scipy               # WAV writing for Whisper input

# Face detection / recognition
opencv-python
numpy
face-recognition    # OPTIONAL extra: needs dlib + cmake on Windows

# Web UI
fastapi
uvicorn
websockets

# Database
sqlite3             # Built into Python, no install needed
```

---

## Risk Factors

| Risk | Mitigation |
|------|------------|
| face_recognition install issues (dlib) | Fall back to OpenCV haar cascades |
| WiFi latency affects responsiveness | Tune control loop timing, buffer commands |
| CM4 compute limits | Keep all ML on laptop |
| LLM costs | Set usage limits, consider local model for testing |

---

## Next Steps

Once questions are answered:
1. Create the app with `reachy-mini-app-assistant`
2. Start with Phase 1 (basic conversation)
3. Iterate through phases

---

*This plan will be updated as we progress.*
