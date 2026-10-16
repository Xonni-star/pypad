# Lektion - Loesung fuer Uebung ++
# Erst selbst versuchen!

def fakultaet(n):
    ergebnis = 1
    for i in range(1, n + 1):
        ergebnis = ergebnis * i
    return ergebnis

print("fakultaet(5) =", fakultaet(5))
