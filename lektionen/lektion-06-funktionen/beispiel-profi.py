# Lektion - Beispiel fuer Uebung ++
# Lektion 06 - Beispiel fuer Uebung ++: Funktion mit Schleife
def summe_bis(n):
    summe = 0
    for i in range(1, n + 1):
        summe = summe + i
    return summe

print("summe_bis(10) =", summe_bis(10))
print("summe_bis(100) =", summe_bis(100))
