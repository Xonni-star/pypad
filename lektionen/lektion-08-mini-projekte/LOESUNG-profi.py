# Lektion - Loesung fuer Uebung ++
# Erst selbst versuchen!

noten = []
while True:
    eingabe = input("Note (oder 'ende'): ")
    if eingabe == "ende":
        break
    noten.append(int(eingabe))

schnitt = sum(noten) / len(noten)
print("Durchschnitt:", schnitt)
