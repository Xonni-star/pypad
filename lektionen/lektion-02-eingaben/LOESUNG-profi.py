# Lektion - Loesung fuer Uebung ++
# Erst selbst versuchen!

sekunden = int(input("Sekunden: "))
stunden = sekunden // 3600
minuten = (sekunden % 3600) // 60
rest = sekunden % 60
print(f"{sekunden} Sekunden sind {stunden} Stunde, {minuten} Minuten, {rest} Sekunden")
