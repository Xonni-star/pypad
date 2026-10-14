# Lektion 03 — Lösung (erst nach eigenem Versuch!)

alter = int(input("Wie alt bist du? "))

if alter <= 11:
    kategorie = "Kind"
elif alter <= 17:
    kategorie = "Teenager"
elif alter <= 64:
    kategorie = "Erwachsener"
else:
    kategorie = "Senior"

print(f"Kategorie: {kategorie}")
