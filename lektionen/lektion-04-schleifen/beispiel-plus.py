# Lektion - Beispiel fuer Uebung +
# Lektion 04 - Beispiel fuer Uebung +: Sammeln in der Schleife
produkt = 1
for i in range(1, 6):
    produkt = produkt * i
print("1 * 2 * 3 * 4 * 5 =", produkt)

gerade_summe = 0
for i in range(2, 21, 2):
    gerade_summe = gerade_summe + i
print("Summe der geraden Zahlen bis 20:", gerade_summe)
