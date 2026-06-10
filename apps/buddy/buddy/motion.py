"""Motion control for Buddy - expressive movements."""

import asyncio
import numpy as np
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from reachy_mini import ReachyMini

from reachy_mini.utils import create_head_pose


class BuddyMotion:
    """Handles expressive robot movements."""

    def __init__(self, robot: "ReachyMini"):
        self.robot = robot

    async def execute_action(self, action: str):
        """Execute a named action."""
        actions = {
            "nod": self.nod,
            "shake": self.shake_head,
            "look_up": self.look_up,
            "look_down": self.look_down,
            "perk_antennas": self.perk_antennas,
            "droop_antennas": self.droop_antennas,
            "spin": self.happy_spin,
            "curious": self.curious_tilt,
            "giggle": self.giggle,
            "dance": self.dance,
        }

        if action in actions:
            print(f"[MOTION] Executing: {action}")
            await actions[action]()
            print(f"[MOTION] Completed: {action}")

    async def nod(self):
        """Nod yes."""
        # Nod down then up twice
        for _ in range(2):
            pose = create_head_pose(pitch=-15, degrees=True)
            self.robot.goto_target(pose, antennas=[0, 0], duration=0.2)
            await asyncio.sleep(0.25)
            pose = create_head_pose(pitch=10, degrees=True)
            self.robot.goto_target(pose, antennas=[0, 0], duration=0.2)
            await asyncio.sleep(0.25)
        # Return to neutral
        pose = create_head_pose()
        self.robot.goto_target(pose, antennas=[0, 0], duration=0.3)
        await asyncio.sleep(0.3)

    async def shake_head(self):
        """Shake head no."""
        for _ in range(2):
            pose = create_head_pose(yaw=-20, degrees=True)
            self.robot.goto_target(pose, antennas=[0, 0], duration=0.15)
            await asyncio.sleep(0.2)
            pose = create_head_pose(yaw=20, degrees=True)
            self.robot.goto_target(pose, antennas=[0, 0], duration=0.15)
            await asyncio.sleep(0.2)
        pose = create_head_pose()
        self.robot.goto_target(pose, antennas=[0, 0], duration=0.2)
        await asyncio.sleep(0.2)

    async def look_up(self):
        """Look up excitedly."""
        pose = create_head_pose(pitch=-25, degrees=True)
        self.robot.goto_target(pose, antennas=[0, 0], duration=0.3)
        await asyncio.sleep(0.5)
        pose = create_head_pose()
        self.robot.goto_target(pose, antennas=[0, 0], duration=0.4)
        await asyncio.sleep(0.4)

    async def look_down(self):
        """Look down sadly."""
        pose = create_head_pose(pitch=25, degrees=True)
        self.robot.goto_target(pose, antennas=[0, 0], duration=0.4)
        await asyncio.sleep(0.5)
        pose = create_head_pose()
        self.robot.goto_target(pose, antennas=[0, 0], duration=0.4)
        await asyncio.sleep(0.4)

    async def perk_antennas(self):
        """Perk up antennas - excited/alert."""
        # Antennas are in radians, positive is up
        pose = create_head_pose()
        antennas_up = [np.deg2rad(30), np.deg2rad(30)]
        self.robot.goto_target(pose, antennas=antennas_up, duration=0.2)
        await asyncio.sleep(0.3)
        self.robot.goto_target(pose, antennas=[0, 0], duration=0.3)
        await asyncio.sleep(0.3)

    async def droop_antennas(self):
        """Lower antennas - sad/tired."""
        pose = create_head_pose()
        antennas_down = [np.deg2rad(-20), np.deg2rad(-20)]
        self.robot.goto_target(pose, antennas=antennas_down, duration=0.4)
        await asyncio.sleep(0.5)
        self.robot.goto_target(pose, antennas=[0, 0], duration=0.4)
        await asyncio.sleep(0.4)

    async def happy_spin(self):
        """Do a happy spin - rotate body left then right."""
        pose = create_head_pose()
        # Note: Body yaw is controlled separately
        # For now, just do a head spin motion
        pose_left = create_head_pose(yaw=45, degrees=True)
        self.robot.goto_target(pose_left, antennas=[np.deg2rad(20), np.deg2rad(20)], duration=0.4)
        await asyncio.sleep(0.5)
        pose_right = create_head_pose(yaw=-45, degrees=True)
        self.robot.goto_target(pose_right, antennas=[np.deg2rad(20), np.deg2rad(20)], duration=0.4)
        await asyncio.sleep(0.5)
        self.robot.goto_target(pose, antennas=[0, 0], duration=0.3)
        await asyncio.sleep(0.3)

    async def curious_tilt(self):
        """Tilt head curiously."""
        pose = create_head_pose(roll=15, pitch=-5, degrees=True)
        self.robot.goto_target(pose, antennas=[0, 0], duration=0.3)
        await asyncio.sleep(0.8)
        pose = create_head_pose()
        self.robot.goto_target(pose, antennas=[0, 0], duration=0.3)
        await asyncio.sleep(0.3)

    async def giggle(self):
        """Giggle - quick shaky movement with perky antennas."""
        pose = create_head_pose()
        # Quick shaky movements
        for _ in range(4):
            pose_left = create_head_pose(roll=-8, pitch=-3, degrees=True)
            self.robot.goto_target(pose_left, antennas=[np.deg2rad(25), np.deg2rad(25)], duration=0.1)
            await asyncio.sleep(0.12)
            pose_right = create_head_pose(roll=8, pitch=-3, degrees=True)
            self.robot.goto_target(pose_right, antennas=[np.deg2rad(25), np.deg2rad(25)], duration=0.1)
            await asyncio.sleep(0.12)
        self.robot.goto_target(pose, antennas=[0, 0], duration=0.2)
        await asyncio.sleep(0.2)

    async def dance(self):
        """Dance - rhythmic head and antenna movements."""
        pose = create_head_pose()
        # Dance sequence
        for _ in range(3):
            # Bob left with left antenna up
            pose1 = create_head_pose(roll=-10, yaw=-15, degrees=True)
            self.robot.goto_target(pose1, antennas=[np.deg2rad(30), np.deg2rad(-10)], duration=0.25)
            await asyncio.sleep(0.3)
            # Bob right with right antenna up
            pose2 = create_head_pose(roll=10, yaw=15, degrees=True)
            self.robot.goto_target(pose2, antennas=[np.deg2rad(-10), np.deg2rad(30)], duration=0.25)
            await asyncio.sleep(0.3)
        # Finish with a flourish
        pose_up = create_head_pose(pitch=-15, degrees=True)
        self.robot.goto_target(pose_up, antennas=[np.deg2rad(35), np.deg2rad(35)], duration=0.2)
        await asyncio.sleep(0.3)
        self.robot.goto_target(pose, antennas=[0, 0], duration=0.3)
        await asyncio.sleep(0.3)

    async def greet(self):
        """Greeting gesture."""
        await self.perk_antennas()
        await self.nod()

    async def idle_movement(self):
        """Subtle idle movement to seem alive."""
        import random
        pitch = random.uniform(-5, 5)
        yaw = random.uniform(-10, 10)
        pose = create_head_pose(pitch=pitch, yaw=yaw, degrees=True)
        self.robot.goto_target(pose, antennas=[0, 0], duration=1.0)

    async def look_at(self, x: float, y: float):
        """
        Look at a position in camera frame.

        Args:
            x: Horizontal position (-1 to 1, left to right)
            y: Vertical position (-1 to 1, top to bottom)
        """
        yaw = -x * 30  # Negative because camera is mirrored
        pitch = y * 20
        pose = create_head_pose(yaw=yaw, pitch=pitch, degrees=True)
        self.robot.goto_target(pose, antennas=[0, 0], duration=0.3)
