# Lektion 05 — Beispiel: Listen & Dictionaries

# 1) Liste: geordnet, Positionen ab 0
gerichte = ["Pizza", "Suppe", "Salat"]
print("Erstes:", gerichte[0], "| Letztes:", gerichte[-1])

# 2) Nummeriert ausgeben
for i, gericht in enumerate(gerichte, start=1):
    print(f"{i}. {gericht}")

# 3) Anhängen und zählen
gerichte.append("Nudeln")
print("Anzahl:", len(gerichte))

# 4) Dictionary: Schlüssel -> Wert
alter = {"Max": 45, "Mia": 30, "Tom": 12}
print("Max ist", alter["Max"], "Jahre alt")
alter["Anna"] = 27                     # neuen Eintrag ergänzen
for name, jahre in alter.items():
    print(f"{name}: {jahre} Jahre")

# 5) Summe und Durchschnitt aus einer Zahlenliste
zahlen = [4, 8, 15, 16]
print("Summe:", sum(zahlen), "| Durchschnitt:", sum(zahlen) / len(zahlen))
