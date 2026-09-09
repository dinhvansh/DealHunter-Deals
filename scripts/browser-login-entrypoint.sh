#!/bin/sh
set -eu

VNC_PASSWORD="${VNC_PASSWORD:-change-me-now}"
PROFILE_DIR="${CHROME_PROFILE_DIR:-/data/chrome-profile}"
START_URL="${START_URL:-https://shopee.vn}"

mkdir -p "$PROFILE_DIR" /tmp/.X11-unix
chmod 700 "$PROFILE_DIR" || true

x11vnc -storepasswd "$VNC_PASSWORD" /tmp/vnc.pass >/dev/null
Xvfb :99 -screen 0 1440x900x24 -ac +extension GLX +render -noreset &
sleep 1
openbox >/tmp/openbox.log 2>&1 &

google-chrome-stable \
  --no-sandbox \
  --disable-dev-shm-usage \
  --disable-gpu \
  --user-data-dir="$PROFILE_DIR" \
  --window-size=1400,840 \
  --no-first-run \
  --no-default-browser-check \
  "$START_URL" >/tmp/chrome.log 2>&1 &

x11vnc \
  -display :99 \
  -rfbport 5900 \
  -rfbauth /tmp/vnc.pass \
  -forever \
  -shared \
  -noxdamage \
  >/tmp/x11vnc.log 2>&1 &

exec websockify --web=/usr/share/novnc/ 6080 localhost:5900
