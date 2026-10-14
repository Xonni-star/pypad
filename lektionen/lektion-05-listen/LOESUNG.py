# Lektion 05 — Lösung (erst nach eigenem Versuch!)

print("Meine Gerichte:")
gerichte = ["Pizza", "Pasta", "Salat"]
for i, gericht in enumerate(gerichte, start=1):
    print(f"{i}. {gericht}")

gerichte.append("Suppe")
print("Jetzt sind es", len(gerichte), "Gerichte")

print()

alter = {"Max": 45, "Anna": 32, "Ben": 12}
for name in alter:
    print(f"{name} ist {alter[name]} Jahre alt")
