# Lektion - Beispiel fuer Uebung +
# Lektion 06 - Beispiel fuer Uebung +: zwei Funktionen
def sind_gerade(zahlen):
    return [z for z in zahlen if z % 2 == 0]

def groesste(zahlen):
    return max(zahlen)

werte = [4, 9, 12, 7]
print("Gerade Zahlen:", sind_gerade(werte))
print("Groesste:", groesste(werte))
