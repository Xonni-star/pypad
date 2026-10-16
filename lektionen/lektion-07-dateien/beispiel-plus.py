# Lektion - Beispiel fuer Uebung +
# Lektion 07 - Beispiel fuer Uebung +: schreiben und anhaengen
with open("protokoll.txt", "w") as datei:
    datei.write("Start" + "\n")

with open("protokoll.txt", "a") as datei:
    datei.write("Schritt 1" + "\n")
    datei.write("Ende" + "\n")

with open("protokoll.txt") as datei:
    zeilen = [z.strip() for z in datei]
print("Eintraege:", len(zeilen), "->", zeilen)
