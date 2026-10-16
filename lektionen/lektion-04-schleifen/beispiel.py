# Lektion 04 — Beispiel: Schleifen

# 1) for mit range: 1 bis 5 (die 6 gehört nicht dazu)
for i in range(1, 6):
    print("Durchlauf", i)

print("-" * 20)

# 2) Das kleine Einmaleins der 3
for i in range(1, 11):
    print(f"3 mal {i} ist {i * 3}")

print("-" * 20)

# 3) Summe sammeln
summe = 0
for i in range(1, 101):
    summe = summe + i
print("Summe von 1 bis 100:", summe)

print("-" * 20)

# 4) while: läuft, solange die Bedingung stimmt
zahl = 3
while zahl > 0:
    print("Countdown", zahl)
    zahl = zahl - 1        # WICHTIG: sonst läuft die Schleife ewig
print("Start!")
