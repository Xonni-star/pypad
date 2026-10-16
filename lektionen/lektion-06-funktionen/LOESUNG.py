# Lektion 06 — Lösung

def begruessen(name):
    print("Hallo", name + "!")

def ist_gerade(zahl):
    return zahl % 2 == 0      # % ist der Rest: 4 % 2 == 0 -> gerade

for n in ["Max", "Mia", "Tom"]:
    begruessen(n)

for i in range(1, 11):
    if ist_gerade(i):
        print(i, "ist gerade")
    else:
        print(i, "ist ungerade")
