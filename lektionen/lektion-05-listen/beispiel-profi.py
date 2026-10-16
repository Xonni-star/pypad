# Lektion - Beispiel fuer Uebung ++
# Lektion 05 - Beispiel fuer Uebung ++: zaehlen
stimmen = ["ja", "nein", "ja", "ja", "nein"]
zaehler = {}
for s in stimmen:
    zaehler[s] = zaehler.get(s, 0) + 1
for s in zaehler:
    print(s, ":", zaehler[s])
