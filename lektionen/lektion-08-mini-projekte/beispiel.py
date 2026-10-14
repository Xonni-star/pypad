# Lektion 08 — Mini-Projekt: Zahlen raten
# Ausführen:  python3 beispiel.py
# (Verbindet: input, int, if/elif/else, while, Funktionen, random)

import random


def spielen(bis=100):
    geheim = random.randint(1, bis)
    versuche = 0
    while True:
        tipp = int(input(f"Zahl zwischen 1 und {bis}: "))
        versuche += 1
        if tipp < geheim:
            print("Zu klein!")
        elif tipp > geheim:
            print("Zu gross!")
        else:
            print(f"Richtig! Gebraucht: {versuche} Versuche.")
            break


spielen()
