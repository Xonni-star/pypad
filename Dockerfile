# PyPad Server als Container
# Bauen:  docker build -t pypad .
# Starten: docker run -d -p 8080:8080 -e PYPAD_ADMIN_PW=meinPasswort -v pypad-daten:/srv/pypad pypad
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYPAD_DATA=/srv/pypad \
    PYPAD_HOST=0.0.0.0 \
    PYPAD_PORT=8080 \
    PYPAD_HTTP=1 \
    PYPAD_RUNNER=direkt

# git fuer das Git-Panel (klonen, committen, push/pull), Zertifikate fuer HTTPS-Ziele
RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Eigener Benutzer: ausgefuehrter Code laeuft mit dessen Rechten - der Container selbst ist die Abschottung
RUN useradd --create-home --uid 10001 pypad

WORKDIR /app
COPY pypad.py pypad-server.py online.html index.html ./
COPY vendor ./vendor

RUN mkdir -p /srv/pypad && chown -R pypad:pypad /srv/pypad /app
USER pypad

EXPOSE 8080
VOLUME ["/srv/pypad"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/', timeout=3)" || exit 1

CMD ["python3", "pypad-server.py"]
