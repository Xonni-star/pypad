# Lektion 08 — Lösung (erst nach eigenem Versuch!)
# Alle drei Varianten kurz gezeigt — bau deine Lieblingsvariante weiter aus.

print("=== A) Trinkgeld-Rechner ===")
betrag = float(input("Rechnungsbetrag: "))
prozent = float(input("Trinkgeld in %: "))
trinkgeld = betrag * prozent / 100
print(f"Trinkgeld:   {trinkgeld:.2f}")
print(f"Gesamtsumme: {betrag + trinkgeld:.2f}")

print()
print("=== B) Einkaufsliste ===")
liste = []
while True:
    artikel = input("Artikel (leer = Ende): ")
    if artikel == "":
        break
    liste.append(artikel)

for i, artikel in enumerate(liste, start=1):
    print(f"{i}. {artikel}")

with open("einkauf.txt", "w") as datei:
    for artikel in liste:
        datei.write(artikel + "\n")
print("Gespeichert in einkauf.txt")

print()
print("=== C) Noten-Durchschnitt ===")
noten = []
while True:
    eingabe = input("Note (ende = fertig): ")
    if eingabe == "ende":
        break
    noten.append(float(eingabe))

if noten:
    schnitt = sum(noten) / len(noten)
    print(f"Durchschnitt: {schnitt:.2f}")
    if schnitt <= 1.5:
        print("Sehr gut!")
    elif schnitt <= 2.5:
        print("Gut.")
    elif schnitt <= 3.5:
        print("Okay.")
    else:
        print("Da geht noch was.")
else:
    print("Keine Noten eingegeben.")
