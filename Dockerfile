FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

RUN set -eux; \
    arch="$(dpkg --print-architecture)"; \
    if [ "$arch" != "amd64" ]; then \
      echo "Google Chrome Stable Linux container is supported here only on amd64/x86_64; got $arch" >&2; \
      exit 1; \
    fi; \
    apt-get update; \
    apt-get install -y --no-install-recommends ca-certificates wget; \
    wget -q -O /tmp/google-chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb; \
    apt-get install -y --no-install-recommends /tmp/google-chrome.deb; \
    rm -f /tmp/google-chrome.deb; \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir .

RUN mkdir -p /data/chrome-profile

CMD ["uvicorn", "dealhunter.main:app", "--host", "0.0.0.0", "--port", "8000"]
