"""Audio module - Speech-to-text and Text-to-speech."""

import asyncio
import tempfile
import wave
from pathlib import Path
from typing import Callable

from .config import WHISPER_MODEL, TTS_VOICE

# Try to import audio libraries
try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("Note: faster_whisper not available. Speech-to-text disabled.")

try:
    import edge_tts
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    print("Note: edge_tts not available. Text-to-speech disabled.")

try:
    import sounddevice as sd
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    print("Note: sounddevice not available. Audio I/O disabled.")


class SpeechToText:
    """Transcribes audio to text using Whisper."""

    def __init__(self):
        if WHISPER_AVAILABLE:
            print(f"Loading Whisper model: {WHISPER_MODEL}...")
            self.model = WhisperModel(WHISPER_MODEL, compute_type="int8")
            print("Whisper model loaded!")
        else:
            self.model = None

    def transcribe(self, audio_path: str, language: str | None = None) -> str:
        """Transcribe audio file to text.

        `language` can be 'ar', 'en', etc — passing it eliminates the
        auto-detection bug where short clips like 'marhaba' get classified
        as Thai/Indonesian/etc. None = auto-detect.
        """
        if not self.model:
            return ""

        segments, info = self.model.transcribe(
            audio_path,
            beam_size=5,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 400},
            language=language,  # None = auto
            initial_prompt="مرحبا" if language == "ar" else None,  # hint for Arabic
        )
        text = " ".join(seg.text for seg in segments).strip()
        print(f"[STT] lang={info.language} (p={info.language_probability:.2f}) text={text!r}")
        return text

    def transcribe_array(self, audio: "np.ndarray", sample_rate: int = 16000) -> str:
        """Transcribe numpy audio array to text."""
        if not self.model:
            return ""

        # Save to temp file (faster_whisper needs file path)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = f.name

        import numpy as np
        # Ensure audio is float32 and normalized
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)
        if audio.max() > 1.0:
            audio = audio / 32768.0

        # Save as WAV
        import scipy.io.wavfile as wav
        wav.write(temp_path, sample_rate, audio)

        text = self.transcribe(temp_path)

        # Clean up
        Path(temp_path).unlink()
        return text


class TextToSpeech:
    """Converts text to speech using Edge TTS."""

    def __init__(self, voice: str = TTS_VOICE):
        self.voice = voice

    async def speak(self, text: str) -> str | None:
        """
        Convert text to speech and return path to audio file.

        Returns:
            Path to MP3 file, or None if TTS unavailable
        """
        if not TTS_AVAILABLE:
            return None

        # Create temp file
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            output_path = f.name

        communicate = edge_tts.Communicate(text, self.voice)
        await communicate.save(output_path)
        return output_path

    async def speak_and_play(self, text: str):
        """Convert text to speech and play it."""
        audio_path = await self.speak(text)
        if audio_path and AUDIO_AVAILABLE:
            await self._play_audio(audio_path)
            Path(audio_path).unlink()

    async def _play_audio(self, path: str):
        """Play an audio file."""
        try:
            import subprocess
            # Use ffplay (comes with ffmpeg) for cross-platform playback
            process = await asyncio.create_subprocess_exec(
                "ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await process.wait()
        except FileNotFoundError:
            print("ffplay not found. Install ffmpeg for audio playback.")


class AudioRecorder:
    """Records audio from microphone."""

    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.recording = False
        self.audio_buffer = []

    def start_recording(self):
        """Start recording audio."""
        if not AUDIO_AVAILABLE:
            print("Audio recording not available")
            return

        self.recording = True
        self.audio_buffer = []

        def callback(indata, frames, time, status):
            if self.recording:
                self.audio_buffer.append(indata.copy())

        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            callback=callback
        )
        self.stream.start()

    def stop_recording(self) -> "np.ndarray":
        """Stop recording and return audio data."""
        import numpy as np

        self.recording = False
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()

        if self.audio_buffer:
            return np.concatenate(self.audio_buffer, axis=0).flatten()
        return np.array([])


# Singleton instances
_stt: SpeechToText | None = None
_tts: TextToSpeech | None = None


def get_stt() -> SpeechToText:
    """Get speech-to-text instance."""
    global _stt
    if _stt is None:
        _stt = SpeechToText()
    return _stt


def get_tts() -> TextToSpeech:
    """Get text-to-speech instance."""
    global _tts
    if _tts is None:
        _tts = TextToSpeech()
    return _tts
