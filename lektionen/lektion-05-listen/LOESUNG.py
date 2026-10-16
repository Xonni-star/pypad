# Lektion 05 — Lösung

gerichte = ["Pizza", "Suppe", "Salat"]

for i, gericht in enumerate(gerichte, start=1):
    print(i, ".", gericht)

gerichte.append("Nudeln")
print("Anzahl:", len(gerichte))

alter = {"Max": 45, "Mia": 30, "Tom": 12}
for name in alter:
    print(name, "ist", alter[name], "Jahre alt")
