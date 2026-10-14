# Lektion 06 — Lösung (erst nach eigenem Versuch!)

def begruessen(name):
    print(f"Hallo {name}!")


def ist_gerade(zahl):
    return zahl % 2 == 0


for name in ["Max", "Anna", "Ben"]:
    begruessen(name)

print("-" * 20)

for zahl in range(1, 11):
    if ist_gerade(zahl):
        print(zahl, "ist gerade")
    else:
        print(zahl, "ist ungerade")
