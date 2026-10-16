# Lektion 08 — Lösung (Variante A: Trinkgeld-Rechner)
# Erst fragen, dann rechnen, dann ausgeben — in kleinen Schritten.

betrag = float(input("Rechnungsbetrag: "))
prozent = float(input("Trinkgeld in Prozent: "))

trinkgeld = betrag * prozent / 100
gesamt = betrag + trinkgeld

print(f"Trinkgeld: {trinkgeld:.2f} EUR")
print(f"Gesamt:    {gesamt:.2f} EUR")

# :.2f heißt: Zahl mit zwei Nachkommastellen ausgeben.
