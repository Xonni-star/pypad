# Lektion 06 — Beispiel: Funktionen

# 1) Eine Funktion ohne Rückgabe
def begruessen(name):
    print(f"Hallo {name}!")

begruessen("Max")
begruessen("Mia")

# 2) Eine Funktion MIT Rückgabe
def ist_gerade(zahl):
    return zahl % 2 == 0        # Rest 0 -> gerade

print(ist_gerade(4))            # True
print(ist_gerade(7))            # False

# 3) Mehrere Parameter, einer mit Standardwert
def rechteck(breite, hoehe=1):
    return breite * hoehe

print("Fläche 5x3:", rechteck(5, 3))
print("Fläche 5x1:", rechteck(5))

# 4) Zwei Rückgabewerte auf einmal
def min_max(zahlen):
    return min(zahlen), max(zahlen)

klein, gross = min_max([4, 9, 2])
print("klein:", klein, "groß:", gross)
