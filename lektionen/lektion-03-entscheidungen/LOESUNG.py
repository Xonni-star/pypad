# Lektion 03 — Lösung
# elif wird von oben nach unten geprüft: der ERSTE passende Block läuft,
# alle weiteren werden übersprungen.

alter = int(input("Wie alt bist du? "))

if alter < 12:
    print("Kind")
elif alter < 18:
    print("Teenager")
elif alter < 65:
    print("Erwachsener")
else:
    print("Senior")
