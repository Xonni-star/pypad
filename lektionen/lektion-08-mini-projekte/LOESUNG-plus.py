# Lektion - Loesung fuer Uebung +
# Erst selbst versuchen!

artikel = []
while True:
    eingabe = input("Artikel (leer = Ende): ")
    if eingabe == "":
        break
    artikel.append(eingabe)

for i, a in enumerate(artikel, start=1):
    print(f"{i}. {a}")
print("Insgesamt", len(artikel), "Artikel")
