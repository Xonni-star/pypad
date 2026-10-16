# Lektion - Beispiel fuer Uebung +
# Lektion 08 - Beispiel fuer Uebung +: sammeln bis zur leeren Eingabe
notizen = []
while True:
    zeile = input("Notiz (leer = Ende): ")
    if zeile == "":
        break
    notizen.append(zeile)

for i, n in enumerate(notizen, start=1):
    print(f"{i}. {n}")
