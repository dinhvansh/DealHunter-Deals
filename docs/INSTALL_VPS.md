# DealHunter VPS Installation

## 1. Host requirements

Recommended pilot host:

```text
Ubuntu 24.04 LTS
amd64/x86_64
2 vCPU / 4 GB RAM minimum
4 vCPU / 8 GB RAM recommended
40–80 GB SSD
```

The bundled Google Chrome Stable images are intended for amd64 Linux hosts.

## 2. Clone and bootstrap

```bash
git clone https://github.com/dinhvansh/DealHunter-Deals.git
cd DealHunter-Deals
sudo bash scripts/bootstrap-vps.sh
```

The script:

- installs Docker/Compose when needed
- creates `.env` from `.env.example`
- replaces the insecure example noVNC password
- builds the API image with Google Chrome Stable
- starts PostgreSQL, Redis and DealHunter
- runs `alembic upgrade head`
- performs `/health` smoke test

Then open:

```text
http://SERVER_IP:8000/setup
```

## 3. First-run setup

The setup wizard asks for:

- admin display name
- admin email/password
- public application URL
- timezone/language
- optional AI provider/base URL/API key/model
- optional browser-login URL

After completion:

- the setup route is locked
- the admin receives an authenticated HttpOnly session
- private dashboard/API routes require login

## 4. HTTPS

Before exposing DealHunter to other users, put it behind a reverse proxy with TLS (Nginx, Caddy, Traefik, Nginx Proxy Manager, etc.).

Then set:

```env
DEALHUNTER_SESSION_COOKIE_SECURE=true
```

and set the real public URL in Settings > General.

Do not expose PostgreSQL or Redis ports to the public Internet. In a hardened deployment, remove their host port mappings or firewall them.

## 5. Shopee login browser

Public Shopee search does not require an account session. Account login is only required for personalized voucher/freeship/checkout verification.

Start the optional human-login browser:

```bash
docker compose --profile browser-login up -d --build shopee-browser-login
```

Open:

```text
http://SERVER_IP:6080/vnc.html?autoconnect=true
```

Use the value of `DEALHUNTER_VNC_PASSWORD` when prompted.

The browser is branded Google Chrome Stable and uses the same persistent profile volume as DealHunter. The human logs in to Shopee directly. DealHunter does not receive the password, OTP or CAPTCHA response.

After login, stop the browser service:

```bash
docker compose stop shopee-browser-login
```

Then in DealHunter:

```text
Settings
→ Shopee Account
→ Kiểm tra session
```

Do not run the login browser and collector Chrome against the same profile at the same time.

## 6. AI provider

Go to:

```text
Settings → AI Provider
```

For OpenAI-compatible services configure:

```text
Provider: OpenAI Compatible
Base URL: https://provider.example/v1
API token: ******
Model: provider-model-name
```

For Ollama:

```text
Provider: Ollama
Base URL: http://ollama-host:11434
API token: blank
Model: local-model
```

Use `Test connection` before relying on the AI layer.

## 7. Telegram and affiliate

Configure in Settings. Tokens are encrypted before being written to PostgreSQL and only masked values are returned to the UI.

Affiliate commission must never influence Deal Score.

## 8. Update deployment

Before updating, inspect Git state and release notes. Then:

```bash
git fetch --all --prune
git status
git pull --ff-only
docker compose up -d --build
docker compose exec api alembic upgrade head
curl -fsS http://127.0.0.1:8000/health
```

If `git pull --ff-only` fails, stop and investigate divergence instead of force-resetting production.

## 9. Useful diagnostics

```bash
docker compose ps
docker compose logs --tail=200 api
docker compose logs --tail=100 postgres
docker compose logs --tail=100 redis
docker compose exec api google-chrome-stable --version
docker compose exec api alembic current
```

System status is also available after login at:

```text
Settings → System
```

## 10. Live collector validation

After the app is healthy:

```bash
docker compose exec api dealhunter live-sample "ssd 2tb" --listings 10 --transport chrome
```

Review the CSV and run:

```bash
docker compose exec api dealhunter live-report validation/<reviewed-file>.csv
```

Do not scale until at least 50 variants are manually validated with at least 95% accuracy.
