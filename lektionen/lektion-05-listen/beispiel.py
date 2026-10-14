# Lektion 05 — Listen & Dictionaries
# Ausführen:  python3 beispiel.py

einkauf = ["Brot", "Milch", "Kaffee"]
print(einkauf)
print("erstes Element:", einkauf[0])
print("Anzahl:", len(einkauf))

einkauf.append("Butter")        # hinten anhängen
for ding in einkauf:
    print("-", ding)

print()

nummeriert = ["Brot", "Milch"]
for i, ding in enumerate(nummeriert, start=1):
    print(f"{i}. {ding}")

print()

# Dictionary: Schlüssel -> Wert
alter = {"Max": 45, "Anna": 32, "Ben": 12}
print("Max ist", alter["Max"], "Jahre alt")
alter["Carla"] = 27             # neuer Eintrag
for name in alter:
    print(f"{name} ist {alter[name]} Jahre alt")
