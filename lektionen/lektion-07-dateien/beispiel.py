# Lektion 07 — Beispiel: Dateien & Module
import random
import math

# 1) Schreiben ("w" überschreibt, "a" hängt an)
with open("beispiel-notizen.txt", "w") as datei:
    datei.write("Erste Zeile" + "\n")
    datei.write("Zweite Zeile" + "\n")

# 2) Lesen — jede Zeile hat den Umbruch am Ende
with open("beispiel-notizen.txt") as datei:
    for zeile in datei:
        sauber = zeile.strip()
        print("Gelesen:", sauber, f"({len(sauber)} Zeichen)")

# 3) Modul aus der Standardbibliothek
farben = ["rot", "grün", "blau"]
print("Zufallsfarbe:", random.choice(farben))
print("Zufallszahl 1-6:", random.randint(1, 6))

# 4) Mathe-Modul
print("Kreisfläche bei Radius 3:", round(math.pi * 3 ** 2, 2))
