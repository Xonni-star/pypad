# Lektion - Beispiel fuer Uebung ++
# Lektion 03 - Beispiel fuer Uebung ++: mehrere Bedingungen
alter = int(input("Alter: "))
hat_ticket = input("Ticket dabei? (j/n): ")
if alter >= 18 and hat_ticket == "j":
    print("Einlass gewaehrt")
else:
    print("kein Einlass")
