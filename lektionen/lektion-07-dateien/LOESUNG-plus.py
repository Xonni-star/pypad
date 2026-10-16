# Lektion - Loesung fuer Uebung +
# Erst selbst versuchen!

with open("zeilen.txt", "w") as datei:
    datei.write("Zeile 1" + "\n")
    datei.write("Zeile 2" + "\n")
    datei.write("Zeile 3" + "\n")

with open("zeilen.txt", "a") as datei:
    datei.write("Zeile 4" + "\n")
    datei.write("Zeile 5" + "\n")

with open("zeilen.txt") as datei:
    anzahl = len([z for z in datei if z.strip()])
print("Zeilen in der Datei:", anzahl)
