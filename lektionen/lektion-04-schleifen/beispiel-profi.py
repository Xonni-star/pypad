# Lektion - Beispiel fuer Uebung ++
# Lektion 04 - Beispiel fuer Uebung ++: Schleife in der Schleife
for reihe in range(1, 4):
    for spalte in range(1, 4):
        print(f"{reihe}" + "x" + f"{spalte}={reihe * spalte}", end="  ")
    print()      # Zeilenumbruch nach jeder Reihe
