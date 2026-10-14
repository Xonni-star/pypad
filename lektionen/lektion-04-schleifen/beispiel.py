# Lektion 04 — Schleifen
# Ausführen:  python3 beispiel.py

# for-Schleife: eine feste Anzahl Wiederholungen
for i in range(1, 6):
    print("Durchlauf", i)

print("-" * 20)

# range(start, stopp, schritt) — die stopp-Zahl gehört NICHT dazu
for zahl in range(0, 11, 2):
    print("gerade Zahl:", zahl)

print("-" * 20)

# while-Schleife: läuft, solange die Bedingung stimmt
zaehler = 3
while zaehler > 0:
    print("Countdown", zaehler)
    zaehler -= 1          # dasselbe wie:  zaehler = zaehler - 1
print("Start!")
