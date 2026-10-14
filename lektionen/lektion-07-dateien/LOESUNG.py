# Lektion 07 — Lösung (erst nach eigenem Versuch!)

import random

woerter = []
for i in range(3):
    woerter.append(input(f"Wort {i + 1}: "))

with open("woerter.txt", "w") as datei:
    for wort in woerter:
        datei.write(wort + "\n")

print("In der Datei steht:")
with open("woerter.txt") as datei:
    for zeile in datei:
        wort = zeile.strip()
        print(f"{wort} hat {len(wort)} Buchstaben")

print("Zufallswort:", random.choice(woerter))
