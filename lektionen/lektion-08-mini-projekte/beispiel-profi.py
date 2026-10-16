# Lektion - Beispiel fuer Uebung ++
# Lektion 08 - Beispiel fuer Uebung ++: Durchschnitt berechnen
werte = []
while True:
    e = input("Messwert (oder 'ende'): ")
    if e == "ende":
        break
    werte.append(float(e))

print("Anzahl:", len(werte))
print("Mittelwert:", sum(werte) / len(werte))
