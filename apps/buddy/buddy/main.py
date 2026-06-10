"""
Buddy - Interactive Companion Robot

A playful AI companion that recognizes faces, chats conversationally,
and expresses emotions through movement.
"""

import asyncio
import sys
from typing import Optional

from .config import LLM_PROVIDER, OLLAMA_MODEL
from .ai import get_ai
from .motion import BuddyMotion
from .vision import get_detector
from .audio import get_stt, get_tts


class Buddy:
    """Main Buddy companion robot class."""

    def __init__(self):
        self.robot = None
        self.motion: Optional[BuddyMotion] = None
        self.ai = get_ai(provider=LLM_PROVIDER, model=OLLAMA_MODEL)
        self.detector = get_detector()
        self.stt = get_stt()
        self.tts = get_tts()
        self.running = False

        # State
        self.current_person: Optional[str] = None
        self.last_face_check = 0

    async def start(self):
        """Initialize and start Buddy."""
        print("\n" + "=" * 50)
        print("  BUDDY - Interactive Companion Robot")
        print("=" * 50 + "\n")

        # Connect to robot
        await self._connect_robot()

        if self.robot:
            self.motion = BuddyMotion(self.robot)
            print("Robot connected! Starting companion mode...\n")
            await self.motion.greet()
        else:
            print("Running in text-only mode (no robot)\n")

        self.running = True
        await self._main_loop()

    async def _connect_robot(self):
        """Connect to the robot (simulation or real)."""
        try:
            from reachy_mini import ReachyMini

            print("Connecting to Reachy Mini daemon...")
            print("(Make sure daemon is running: reachy-mini-daemon --sim)")

            self.robot = ReachyMini()
            print("Robot connected!")

        except Exception as e:
            print(f"Could not connect to robot: {e}")
            print("\nTo use robot control, start the daemon first:")
            print("  reachy-mini-daemon --sim     # For simulation")
            print("  reachy-mini-daemon           # For real robot")
            print("\nContinuing in text-only mode...")
            self.robot = None

    async def _main_loop(self):
        """Main interaction loop."""
        print("=" * 50)
        print("Chat with Buddy! (type 'quit' to exit)")
        print("Commands: /enroll <name> - teach Buddy your face")
        print("=" * 50 + "\n")

        while self.running:
            try:
                # Get user input
                user_input = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: input("You: ")
                )

                if not user_input.strip():
                    continue

                # Handle commands
                if user_input.lower() == 'quit':
                    await self.shutdown()
                    break

                if user_input.startswith('/enroll '):
                    name = user_input[8:].strip()
                    await self._enroll_face(name)
                    continue

                if user_input.lower() == '/faces':
                    self._list_faces()
                    continue

                # Chat with AI
                await self._chat(user_input)

            except KeyboardInterrupt:
                await self.shutdown()
                break
            except EOFError:
                await self.shutdown()
                break

    async def _chat(self, message: str):
        """Handle a chat message."""
        # Build context
        context = {}
        if self.current_person:
            context["detected_face"] = self.current_person

        # Get AI response
        try:
            response, actions = self.ai.chat(message, context)
        except Exception as e:
            print(f"Buddy: (AI error: {e})")
            return

        print(f"Buddy: {response}")

        # Execute actions
        if self.motion and actions:
            for action in actions:
                print(f"  *{action}*")
                await self.motion.execute_action(action)

        # Speak response (TTS is optional — log failures but don't crash)
        try:
            await self.tts.speak_and_play(response)
        except Exception as e:
            print(f"[TTS] Playback failed: {e}")

    async def _enroll_face(self, name: str):
        """Enroll a new face."""
        if not self.robot:
            print("Cannot enroll face without camera access.")
            return

        print(f"Looking for face to enroll as '{name}'...")

        # TODO: Capture frame from robot camera
        # For now, just acknowledge
        print(f"Face enrollment for '{name}' - feature coming soon!")
        print("(Requires camera access and face_recognition library)")

    def _list_faces(self):
        """List all known faces."""
        faces = self.detector.db.get_all_faces()
        if not faces:
            print("No faces enrolled yet.")
            return

        print("\nKnown faces:")
        for face_id, name, _ in faces:
            info = self.detector.db.get_person_info(name)
            if info:
                print(f"  - {name} (seen {info['interactions']} times)")
        print()

    async def shutdown(self):
        """Clean shutdown."""
        print("\nBuddy: Goodbye! See you later! [ACTION:droop_antennas]")

        if self.motion:
            await self.motion.droop_antennas()

        self.running = False

        if self.robot:
            # Clean up robot connection
            pass


def main():
    """Entry point."""
    buddy = Buddy()

    try:
        asyncio.run(buddy.start())
    except KeyboardInterrupt:
        print("\nShutting down...")


if __name__ == "__main__":
    main()
