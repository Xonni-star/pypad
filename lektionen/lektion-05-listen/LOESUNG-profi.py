# Lektion - Loesung fuer Uebung ++
# Erst selbst versuchen!

woerter = ["apfel", "birne", "apfel", "a", "a", "a", "kiwi"]
zaehler = {}
for wort in woerter:
    zaehler[wort] = zaehler.get(wort, 0) + 1
for wort in zaehler:
    print(f"{wort}: {zaehler[wort]}")
