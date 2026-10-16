# Lektion 04 — Lösung
# range(1, 11) zählt 1 bis 10 — die obere Grenze gehört nicht dazu.
# Bei while muss sich die Bedingung IN der Schleife ändern.

for i in range(1, 11):
    print(i)

for i in range(1, 11):
    print(i * 7)

zahl = int(input("Startzahl: "))
while zahl > 0:
    print(zahl)
    zahl = zahl - 1
print("Start!")
