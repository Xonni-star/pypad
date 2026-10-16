# Lektion 02 — Beispiel: Eingaben & Zahlen
# Online: die Antwort tippst du unten in die Zeile "> " (Enter zum Senden).

# 1) input() zeigt die Frage und liefert IMMER Text.
name = input("Wie heißt du? ")

# 2) Für Rechnen: int() macht aus "7" die Zahl 7.
alter = int(input("Wie alt bist du? "))

print(f"Hallo {name}!")
print(f"In 10 Jahren bist du {alter + 10}.")

# 3) Ohne Umwandlung hängt Python Text aneinander:
print("Als Text addiert:", "12" + "3")

# 4) Kommazahlen mit float() — mit Punkt schreiben!
preis = float(input("Preis in Euro (z. B. 2.5): "))
print(f"Zwei Stück kosten {preis * 2:.2f} Euro")
