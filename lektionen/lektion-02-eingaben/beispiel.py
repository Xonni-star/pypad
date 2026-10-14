# Lektion 02 — Eingaben & Zahlen
# Ausführen:  python3 beispiel.py

name = input("Wie heißt du? ")
alter_text = input("Wie alt bist du? ")

# WICHTIG: input() liefert IMMER Text.
# Zum Rechnen umwandeln:  int(...) für ganze Zahlen
alter = int(alter_text)

geboren = 2026 - alter
print(f"Hallo {name}! Dann bist du ungefähr {geboren} geboren.")
print(f"In 10 Jahren bist du {alter + 10} Jahre alt.")
