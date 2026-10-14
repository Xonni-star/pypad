# Lektion 06 — Funktionen
# Ausführen:  python3 beispiel.py

def begruessen(name):
    """Gibt eine Begrüßung aus."""
    print(f"Hallo {name}!")


def flaeche(breite, hoehe):
    """Gibt die Fläche zurück."""
    return breite * hoehe


begruessen("Max")
begruessen("Anna")

a = flaeche(4, 5)
print("Fläche:", a, "qm")
print("Doppelte Fläche:", flaeche(4, 5) * 2)
