# Lektion 07 — Lösung
import random

with open("woerter.txt", "w") as datei:
    for _ in range(3):
        wort = input("Wort: ")
        datei.write(wort + "\n")     # Umbruch selbst schreiben

with open("woerter.txt") as datei:
    alle = [zeile.strip() for zeile in datei]   # strip() entfernt den Umbruch

for wort in alle:
    print(wort, "-", len(wort), "Buchstaben")

print("Zufallswort:", random.choice(alle))
