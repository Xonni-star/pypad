# Lektion - Loesung fuer Uebung ++
# Erst selbst versuchen!

jahr = int(input("Jahr: "))
if jahr % 4 == 0 and (jahr % 100 != 0 or jahr % 400 == 0):
    print(f"{jahr} ist ein Schaltjahr")
else:
    print(f"{jahr} ist kein Schaltjahr")
