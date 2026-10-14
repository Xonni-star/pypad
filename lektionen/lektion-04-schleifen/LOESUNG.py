# Lektion 04 — Lösung (erst nach eigenem Versuch!)

print("1 bis 10:")
for i in range(1, 11):
    print(i)

print("-" * 20)

print("Einmaleins der 7:")
for i in range(1, 11):
    print(f"7 x {i} = {i * 7}")

print("-" * 20)

start = int(input("Startzahl: "))
zahl = start
while zahl >= 1:
    print(zahl)
    zahl -= 1
print("Start!")
