# Änderungen

## 1.0.0 — 2026-10-15

Erste veröffentlichte Fassung.

**Ausführen**
- Lokaler Server (nur Python-Standardbibliothek) + Browser-Oberfläche auf `127.0.0.1`
- Code ausführen per Klick oder **Cmd+Enter**, Ausgabe live, Exit-Code und Laufzeit
- **Echte Live-Eingabe** für `input()` wie im Terminal
- **■ Stopp** beendet auch Endlossschleifen und Kindprozesse, Zeitlimit 300 s

**Editor (Ace)**
- Python-Syntaxhervorhebung, Autovervollständigung aus der eigenen Python-Installation
- Attribut-Vervollständigung für importierte Module, Vorlagen für `for`/`def`/`try`/`with` …
- hell/dunkel, Schriftgröße, Auto-Speichern, `Cmd+S`, Snippet-Verwaltung

**Fehler verstehen**
- Fehlerzeile **punktgenau** markiert (Spalte bis Ende), Cursor auf der Stelle
- **Erklärungs-Kasten**: Fehlertyp, Klartext-Begründung, konkrete Tipps („Meintest du …?")
- **Hinweise** schon vor dem Lauf (unbenutzter Import, Tippfehler, Nutzung vor Zuweisung, None-Rückgabe …)
- **Variablen am Ende** des Laufs mit Wert und Typ
- **Verlauf** der letzten Läufe zum Zurückholen des Codes

**Lernen**
- Acht Lektionen mit **drei Stufen** (Übung, Übung +, Übung ++), Beispiel und Lösung
- **✓ Prüfen** testet den eigenen Code automatisch; bestandene Lektionen werden als erledigt markiert
- **Tipp**-Knopf mit schrittweisen Denkanstößen

**Qualität**
- Selbsttest mit 65 Prüfungen (`selbsttest.py`)
- MIT-Lizenz, Fremdcode-Nachweis in `THIRD-PARTY.md` (Ace 1.44.0, BSD-3-Clause)
