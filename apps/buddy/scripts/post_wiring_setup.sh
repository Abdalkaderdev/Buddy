#!/usr/bin/env bash
# Run this on the Pi AFTER you've physically wired up the ecity hardware
# (camera ribbon, USB sound card + mic, speaker through the amp).
#
#   curl -L https://raw.githubusercontent.com/Abdalkaderdev/Buddy/main/apps/buddy/scripts/post_wiring_setup.sh | bash
#
# What it does:
#   1. Enables the Pi camera interface
#   2. Makes the USB sound card the default audio device
#   3. Flips BUDDY_CAMERA=1 so Buddy starts seeing
#   4. Restarts the service
#   5. Tests all three: camera preview, mic record + playback round-trip

set -e

if [[ $EUID -eq 0 ]]; then
    echo "Run this as the pi user (not root). It will use sudo where needed."
    exit 1
fi

echo "=== 1. Enable the Pi camera interface ==="
# raspi-config knobs are idempotent
sudo raspi-config nonint do_camera 0 2>/dev/null || echo "(camera knob may not exist on Trixie — that's OK, libcamera handles it)"

# Make sure the v4l2 bridge module is loaded so cv2.VideoCapture(0) sees the camera
if ! grep -q "^bcm2835-v4l2" /etc/modules-load.d/buddy-camera.conf 2>/dev/null; then
    echo "bcm2835-v4l2" | sudo tee /etc/modules-load.d/buddy-camera.conf >/dev/null
    sudo modprobe bcm2835-v4l2 || true
fi

echo "=== 2. Find the USB sound card ==="
CARD_NUM=$(arecord -l 2>/dev/null | grep -i 'usb' | head -1 | sed -E 's/card ([0-9]+):.*/\1/' || echo "")
if [[ -z "$CARD_NUM" ]]; then
    echo "No USB sound card detected via arecord -l."
    echo "Plug in the ecity USB sound card and re-run this script."
    exit 1
fi
echo "USB sound card is card $CARD_NUM"

# Set ALSA default — both for capture and playback
cat > "$HOME/.asoundrc" <<EOF
pcm.!default {
    type asym
    playback.pcm "plughw:$CARD_NUM,0"
    capture.pcm  "plughw:$CARD_NUM,0"
}
ctl.!default {
    type hw
    card $CARD_NUM
}
EOF
echo "ALSA default → USB sound card (card $CARD_NUM)"

echo "=== 3. Enable camera worker in Buddy ==="
sed -i 's/^BUDDY_CAMERA=.*/BUDDY_CAMERA=1/' ~/.buddy.env 2>/dev/null || echo "BUDDY_CAMERA=1" >> ~/.buddy.env
grep -q '^BUDDY_CAMERA_INDEX=' ~/.buddy.env || echo "BUDDY_CAMERA_INDEX=0" >> ~/.buddy.env
chmod 600 ~/.buddy.env
echo "~/.buddy.env updated"

echo "=== 4. Restart the buddy service ==="
systemctl --user daemon-reload
systemctl --user restart buddy.service
sleep 3
systemctl --user is-active buddy.service && echo "buddy.service is active"

echo
echo "============================================================"
echo "TESTS — verify each one works before you call it done"
echo "============================================================"

echo
echo "--- Test 1: camera preview (5 seconds) ---"
echo "Run: rpicam-hello -t 5000"
echo "Expected: a window/log shows the camera is streaming."
echo
echo "--- Test 2: mic + speaker round-trip ---"
echo "Run: arecord -d 5 -f cd /tmp/test.wav && aplay /tmp/test.wav"
echo "Expected: 5 sec recording, then you hear yourself through the speaker."
echo
echo "--- Test 3: open Buddy in browser ---"
echo "Open https://buddy.local:8080 — tap mic, say 'هلا بادي شفت روحي'"
echo "Buddy should know whether your face is in front of the camera."
echo
echo "--- Test 4: check what Buddy sees right now ---"
echo "curl -sk https://buddy.local:8080/api/camera-state"
echo "Expected: {\"enabled\":true,\"detected_face\":\"unknown\"} when you're in frame,"
echo "          {\"enabled\":true,\"no_face\":true} when you step out."
echo "============================================================"
