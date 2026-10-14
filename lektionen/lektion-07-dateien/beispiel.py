# Lektion 07 — Dateien & Module
# Ausführen:  python3 beispiel.py

# Schreiben (überschreibt die Datei)
with open("notizen.txt", "w") as datei:
    datei.write("Zeile 1\n")
    datei.write("Zeile 2\n")

# Lesen (alles auf einmal)
with open("notizen.txt") as datei:
    inhalt = datei.read()
print(inhalt)

# Anhängen (hängt hinten an)
with open("notizen.txt", "a") as datei:
    datei.write("Zeile 3\n")

# Zeile für Zeile lesen
with open("notizen.txt") as datei:
    for zeile in datei:
        print("gelesen:", zeile.strip())

# Module: fertige Bibliotheken benutzen
import math
print("Wurzel aus 16:", math.sqrt(16))

import random
print("Würfel:", random.randint(1, 6))
