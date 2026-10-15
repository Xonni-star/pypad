#!/bin/sh
# PyPad starten - Linux und macOS
cd "$(dirname "$0")" || exit 1
PY=""
for c in python3 /usr/local/bin/python3 /opt/homebrew/bin/python3 "$HOME/.local/bin/python3"; do
  if command -v "$c" >/dev/null 2>&1; then PY="$c"; break; fi
done
if [ -z "$PY" ]; then
  echo "python3 nicht gefunden. Bitte Python 3 installieren."
  exit 1
fi
exec "$PY" -u pypad.py
