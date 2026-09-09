#!/usr/bin/env bash
set -euo pipefail

if [[ ${EUID:-$(id -u)} -ne 0 ]]; then
  echo "Run as root: sudo bash scripts/bootstrap-vps.sh" >&2
  exit 1
fi

ARCH="$(uname -m)"
if [[ "$ARCH" != "x86_64" && "$ARCH" != "amd64" ]]; then
  echo "Unsupported architecture for bundled Google Chrome Stable: $ARCH" >&2
  echo "Use an amd64/x86_64 VPS or deploy a different browser runtime explicitly." >&2
  exit 2
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y ca-certificates curl git openssl docker.io
if ! docker compose version >/dev/null 2>&1; then
  if apt-cache show docker-compose-v2 >/dev/null 2>&1; then
    apt-get install -y docker-compose-v2
  elif apt-cache show docker-compose-plugin >/dev/null 2>&1; then
    apt-get install -y docker-compose-plugin
  else
    apt-get install -y docker-compose
  fi
fi
systemctl enable --now docker

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
SERVER_IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
SERVER_IP="${SERVER_IP:-SERVER_IP}"

if [[ ! -f .env ]]; then
  cp .env.example .env
  VNC_PASS="$(openssl rand -base64 24 | tr -d '=+/\n' | cut -c1-24)"
  sed -i "s/^DEALHUNTER_VNC_PASSWORD=.*/DEALHUNTER_VNC_PASSWORD=${VNC_PASS}/" .env
  echo "Created .env with a random noVNC password. Keep .env private."
else
  echo ".env already exists; preserving it."
fi

if grep -q '^DEALHUNTER_VNC_PASSWORD=change-me-now$' .env; then
  VNC_PASS="$(openssl rand -base64 24 | tr -d '=+/\n' | cut -c1-24)"
  sed -i "s/^DEALHUNTER_VNC_PASSWORD=.*/DEALHUNTER_VNC_PASSWORD=${VNC_PASS}/" .env
fi

if grep -q '^DEALHUNTER_BROWSER_LOGIN_PUBLIC_URL=http://localhost:' .env; then
  sed -i "s|^DEALHUNTER_BROWSER_LOGIN_PUBLIC_URL=.*|DEALHUNTER_BROWSER_LOGIN_PUBLIC_URL=http://${SERVER_IP}:6080/vnc.html?autoconnect=true|" .env
fi

mkdir -p validation

docker compose up -d --build postgres redis api
docker compose exec -T api alembic upgrade head

for _ in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:8000/health >/dev/null; then
    break
  fi
  sleep 2
done
curl -fsS http://127.0.0.1:8000/health >/dev/null

echo
echo "DealHunter is healthy."
echo "First-run setup: http://${SERVER_IP}:8000/setup"
echo
echo "Optional Shopee human login browser:"
echo "  docker compose --profile browser-login up -d --build shopee-browser-login"
echo "  http://${SERVER_IP}:6080/vnc.html?autoconnect=true"
echo "  Password is stored in .env as DEALHUNTER_VNC_PASSWORD"
echo
echo "Before Internet exposure, configure HTTPS/reverse proxy and set:"
echo "  DEALHUNTER_SESSION_COOKIE_SECURE=true"
