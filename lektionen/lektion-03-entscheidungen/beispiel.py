# Lektion 03 — Entscheidungen
# Ausführen:  python3 beispiel.py

alter = int(input("Wie alt bist du? "))

if alter >= 18:
    print("Du bist volljährig.")
else:
    print("Du bist noch nicht volljährig.")

print()  # leere Zeile

punkte = int(input("Punkte (0-100): "))

if punkte >= 90:
    note = "sehr gut"
elif punkte >= 75:
    note = "gut"
elif punkte >= 50:
    note = "bestanden"
else:
    note = "durchgefallen"

print(f"Ergebnis: {note}")
