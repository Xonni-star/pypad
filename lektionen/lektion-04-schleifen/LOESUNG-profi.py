# Lektion - Loesung fuer Uebung ++
# Erst selbst versuchen!

for zahl in range(2, 31):
    prim = True
    for teiler in range(2, zahl):
        if zahl % teiler == 0:
            prim = False
            break
    if prim:
        print(zahl)
