# Lektion 03 — Beispiel: Entscheidungen

alter = int(input("Wie alt bist du? "))

# Von oben nach unten prüfen — der erste passende Block läuft.
if alter < 12:
    print("Du bist ein Kind.")
elif alter < 18:
    print("Du bist ein Teenager.")
elif alter < 65:
    print("Du bist erwachsen.")
else:
    print("Du bist Senior.")

# Mehrere Bedingungen verbinden
wetter = "sonnig"
temperatur = 24

if wetter == "sonnig" and temperatur > 20:
    print("Perfektes Wetter für draußen!")

# not kehrt eine Bedingung um
if not wetter == "regen":
    print("Kein Regen in Sicht.")
