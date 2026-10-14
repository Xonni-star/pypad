#!/bin/zsh
# PyPad starten - einfach doppelklicken.
cd "$(dirname "$0")" || exit 1
LOG="$HOME/Library/Logs/PyPad.log"
PY=""
for c in /usr/local/bin/python3 /opt/homebrew/bin/python3 "$HOME/.local/bin/python3"; do
  if [ -x "$c" ]; then PY="$c"; break; fi
done
if [ -z "$PY" ]; then
  for c in /Library/Frameworks/Python.framework/Versions/*/bin/python3 /usr/bin/python3; do
    if [ -x "$c" ]; then PY="$c"; break; fi
  done
fi
echo "Starte PyPad ..."
if [ -z "$PY" ]; then
  echo "Kein python3 gefunden."
  if [ -t 0 ]; then read -r "?Enter zum Schliessen..."; fi
  exit 1
fi
"$PY" -u pypad.py
STATUS=$?
echo ""
if [ $STATUS -ne 0 ]; then
  echo "PyPad wurde mit Fehler beendet (Code $STATUS)."
  echo "Log: $LOG"
fi
if [ -t 0 ]; then read -r "?Fenster kann jetzt geschlossen werden (Enter)..."; fi
