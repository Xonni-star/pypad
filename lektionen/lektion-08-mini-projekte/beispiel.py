# Lektion 08 — Beispiel: kleine Projekte zusammensetzen
# Variante A: Trinkgeld-Rechner

def trinkgeld_rechner():
    betrag = float(input("Rechnungsbetrag: "))
    prozent = float(input("Trinkgeld in Prozent: "))
    trinkgeld = betrag * prozent / 100
    gesamt = betrag + trinkgeld
    print(f"Trinkgeld: {trinkgeld:.2f} EUR")
    print(f"Gesamt:    {gesamt:.2f} EUR")

# Variante B: Einkaufsliste mit while, Liste und Datei
def einkaufsliste():
    artikel = []
    while True:
        eingabe = input("Artikel (leer = Ende): ")
        if eingabe == "":
            break                     # Schleife sauber verlassen
        artikel.append(eingabe)

    for i, a in enumerate(artikel, start=1):
        print(f"{i}. {a}")

    with open("einkauf.txt", "w") as datei:
        for a in artikel:
            datei.write(a + "\n")
    print("Gespeichert in einkauf.txt")

# Variante A starten (für B die Zeile unten austauschen)
trinkgeld_rechner()
# einkaufsliste()
