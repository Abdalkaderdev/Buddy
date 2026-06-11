#!/usr/bin/env bash
# Buddy companion-robot — one-shot setup for Raspberry Pi (Raspberry Pi OS Bookworm).
#
# What it does:
#   1. Installs system packages (Python 3, OpenCV deps, ffmpeg, ALSA, libcamera tools).
#   2. Creates a Python venv inside ~/buddy-venv and installs Buddy + deps.
#   3. Writes a systemd user service so Buddy auto-starts at boot.
#
# Usage on the Pi:
#   curl -L https://your.host/setup_pi.sh | bash
# OR copy this file to the Pi and run:
#   bash setup_pi.sh
#
# Requires: Pi connected to internet, sudo access. Run as the regular user (NOT root).

set -euo pipefail

if [[ $EUID -eq 0 ]]; then
    echo "Run this script as the regular Pi user (not root). It will use sudo where needed."
    exit 1
fi

REPO_URL="${BUDDY_REPO_URL:-https://github.com/pollen-robotics/reachy_mini.git}"
INSTALL_DIR="${HOME}/reachy_mini"
VENV_DIR="${HOME}/buddy-venv"
SERVICE_NAME="buddy.service"

echo "==> Updating apt and installing system packages"
sudo apt-get update
sudo apt-get install -y --no-install-recommends \
    git python3 python3-venv python3-pip python3-dev \
    build-essential cmake pkg-config \
    libjpeg-dev libpng-dev \
    libopenblas-dev \
    libportaudio2 portaudio19-dev \
    ffmpeg alsa-utils \
    rpicam-apps v4l-utils \
    libgl1 libglib2.0-0
# Note: libatlas-base-dev was removed in Debian 13; libopenblas-dev replaces it.
# libcamera-apps was renamed to rpicam-apps in Bookworm 2023+.

echo "==> Cloning / updating the Buddy repo into ${INSTALL_DIR}"
if [[ -d "${INSTALL_DIR}/.git" ]]; then
    git -C "${INSTALL_DIR}" pull --ff-only
else
    git clone "${REPO_URL}" "${INSTALL_DIR}"
fi

echo "==> Creating Python venv at ${VENV_DIR}"
python3 -m venv "${VENV_DIR}"
source "${VENV_DIR}/bin/activate"
pip install --upgrade pip wheel

echo "==> Installing Buddy and its dependencies"
# Skip Buddy's declared deps (--no-deps) to avoid the reachy-mini → PyGObject →
# Cairo dependency chain. On the no-motor Pi build we don't need reachy-mini.
pip install --no-deps -e "${INSTALL_DIR}/apps/buddy"
pip install anthropic ollama faster-whisper edge-tts elevenlabs opencv-python \
    fastapi uvicorn websockets sounddevice scipy python-multipart numpy

echo "==> Writing systemd user service"
mkdir -p "${HOME}/.config/systemd/user"
cat > "${HOME}/.config/systemd/user/${SERVICE_NAME}" <<EOF
[Unit]
Description=Buddy Companion Robot
After=network-online.target

[Service]
Type=simple
WorkingDirectory=${INSTALL_DIR}
Environment=PYTHONUNBUFFERED=1
Environment=BUDDY_CAMERA=1
Environment=BUDDY_CAMERA_INDEX=0
# Put your real API key in ~/.buddy.env (chmod 600), it'll be loaded here.
EnvironmentFile=-${HOME}/.buddy.env
ExecStart=${VENV_DIR}/bin/python -m buddy.server
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF

echo "==> Enabling user systemd lingering (so Buddy runs at boot, no login needed)"
sudo loginctl enable-linger "${USER}"

echo "==> Enabling and starting the service"
systemctl --user daemon-reload
systemctl --user enable "${SERVICE_NAME}"
systemctl --user restart "${SERVICE_NAME}"

cat <<'NEXT'

============================================================
Buddy is installed.

NEXT STEPS:
  1. Create your secrets file:
       nano ~/.buddy.env
     Put inside (one line):
       ANTHROPIC_API_KEY=sk-ant-...

  2. Restart the service:
       systemctl --user restart buddy.service

  3. Open Buddy from any device on the same WiFi:
       http://<pi-ip-address>:8080

  4. Logs:
       journalctl --user -u buddy.service -f

  5. Test camera & mic:
       libcamera-hello       # check Pi camera
       arecord -l            # list mic devices
       speaker-test -t sine  # check speaker

ENV-VAR REFERENCE:
  BUDDY_CAMERA=0           disable face detection
  BUDDY_CAMERA_INDEX=N     pick a different /dev/video N
  ANTHROPIC_API_KEY=...    Claude (default provider per config.py)

============================================================
NEXT
