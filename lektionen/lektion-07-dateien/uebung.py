# Lektion 07 — Übung
# Ziel: Dateien schreiben und lesen, ein Modul benutzen.
#
# Aufgaben:
#  1. Frage mit input() nach drei Wörtern und schreibe sie (je eine Zeile)
#     in die Datei woerter.txt.
#  2. Lies die Datei wieder ein und gib jedes Wort mit seiner Länge aus.
#  3. import random — und gib ein zufälliges Wort aus der Liste aus.
#
# Tipps:
#  - Schreiben:  with open("woerter.txt", "w") as datei:  datei.write(wort + "\n")
#  - Lesen:      with open("woerter.txt") as datei:  for zeile in datei:
#  - Zeile ohne Umbruch:  zeile.strip()
#  - Länge:      len(wort)          Zufall:  random.choice(liste)
#
# Ausführen: python3 uebung.py

# --- Dein Code ab hier ---

