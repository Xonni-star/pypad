# Änderungen

## 1.7.0 - 2026-10-16

**HTTPS aus dem ausgefuehrten Code heraus**
- Fehlt dem Python ein Zertifikatsbuendel, reicht PyPad dem Programm automatisch SSL_CERT_FILE / REQUESTS_CA_BUNDLE weiter (typisch macOS mit python.org-Installation: "CERTIFICATE_VERIFY_FAILED")
- Eine bereits gesetzte Einstellung wird nie ueberschrieben; gesucht werden certifi, /etc/ssl/cert.pem und die ueblichen Linux-Buendel
- Hintergrund: das betraf HTTPS auch ausserhalb von PyPad - jetzt laufen urllib und requests direkt

## 1.6.1 - 2026-10-16

**Bugfix: Knoepfe im Git-Panel**
- Online: "Laden" (GitHub) und "Commit" wurden von der Adresszeile zusammengedrueckt und waren kaum lesbar - das Eingabefeld darf jetzt schrumpfen, die Knoepfe behalten ihre Breite
- Online: der Aktualisieren-Knopf (Grafik) im Git-Kopf hatte dieselbe ID wie der neue Laden-Knopf - dadurch loeste er das Laden aus, und der sichtbare Laden-Knopf tat nichts
- Offline: gleiche Absicherung fuer die Knoepfe in Git- und Ordner-Zeile
- Klarere Meldung beim Laden: "Repo nicht gefunden oder privat" (GitHub meldet bei nicht vorhandenen Repos einen Anmeldefehler)

## 1.6.0 - 2026-10-16

**Code von GitHub laden (offline und online)**
- Git-Panel hat jetzt eine Lade-Zeile: GitHub-Adresse eintippen (https://github.com/user/repo oder kurz user/repo), "Laden" klont das Repo in den Ordner
- Es wird nur github.com angenommen, geklont wird flach (--depth 1); Fehler kommen in Klartext (Tippfehler, privat/nicht gefunden, kein Internet)
- Dateileiste zeigt jetzt auch Unterordner: Ordner anklicken = hineingehen, ".." = eine Ebene zurueck
- Git-Befehle (Status/Diff/Commit/Push/Pull) gelten fuer den gerade geoeffneten Ordner - nach dem Laden also fuer das Repo
- Doppeltes Laden in denselben Ordner wird abgefangen ("liegt hier schon")

## 1.5.0 - 2026-10-16

**Online-Variante: Debugger, Git und Live-Eingabe - plus Layout-Fix**
- Debugger: Programm im Einzelschritt (Schritt / Weiter / Ende), aktuelle Zeile hervorgehoben, Variablen sichtbar
- Git-Panel im Online-Editor: Branch, geaenderte Dateien, Diff per Klick, Commit, Push, Pull
- Live-Eingabe: input() kann waehrend des Laufs beantwortet werden (Eingabezeile unten)
- Bugfix: Oberflaeche fuellte das Fenster nicht - Editor und Ausgabe waren abgeschnitten
- Bugfix: an einigen Stellen stand der Quelltext der Hilfsfunktion statt eines Zeilenumbruchs in der Ausgabe

## 1.4.0 - 2026-10-16

**Online-Variante: gleiche Funktionen wie offline**
- Autovervollstaendigung aus dem echten Python (auch Attribute wie math.sqrt)
- Fehler-Erklaerung in Klartext mit Tipps
- Hinweise (Linter) vor dem Lauf, gelb markiert
- Variablen am Ende des Laufs
- Tabs, Code-Faltung, Zeile:Spalte, Ausgaben-Deckel, hell/dunkel + Schriftgroesse

## 1.3.2 - 2026-10-16

- Bugfix: Anmeldung und Oberflaeche waren gleichzeitig sichtbar (hidden-Regel ergaenzt)

## 1.3.1 - 2026-10-16

- Bugfix: Login-Skript der Online-Variante repariert

## 1.3.0 - 2026-10-16

**Online-Variante (PyPad Server)**
- Login + Benutzerverwaltung (Passwoerter scrypt-gehasht)
- Jeder Benutzer hat seinen eigenen Workspace
- Code laeuft abgesichert: eigener System-User, kein Netzwerk, Limits
- HTTPS mit echtem Zertifikat, Sitzungen, Login-Bremse
- Dateizugriff nur im eigenen Workspace (Traversal blockiert)

## 1.2.0 — 2026-10-16

**Server-Zugriff**
- Verbindungs-System: Server selbst anlegen (Name, Protokoll SSH/FTP/FTPS, Host, Port, Benutzer, Passwort)
- Dateien auf entfernten Rechnern auflisten, oeffnen und speichern (Cmd+S schreibt auf den Server)
- SSH (Key-Login oder Passwort via sshpass), FTP/FTPS nativ ueber ftplib
- Zugangsdaten lokal in verbindungen.json (chmod 600)

## 1.1.0 — 2026-10-16

**Editor & Bedienung**
- Datei-Browser: beliebigen Ordner öffnen, Text-Dateien auflisten, öffnen und direkt auf der Platte speichern
- Tabs für mehrere offene Dateien, dazu eine Liste zuletzt geöffneter Dateien
- Verschiebbare Fenstergrößen (Trenner ziehen), Code-Faltung, Zeile:Spalte-Anzeige, Ausgaben-Deckel bei sehr langen Läufen
- Einstellungen (⚙): Lernen-Leiste, Hinweise, Variablen, Erklärung, Auto-Speichern und Zeilennummern ein-/ausblenden, Schriftgröße

**Git**
- Status, Diff, Commit, Push und Pull direkt in der Seitenleiste (funktioniert mit jedem Git-Ordner)

**Sprachen & Werkzeuge**
- Syntax-Highlighting für JavaScript, HTML, CSS, JSON und Markdown (Ausführen bleibt Python)
- Markdown-Vorschau und Gehe-zu-Definition (F3)
- Schritt-für-Schritt-Debugger (🐞) mit Eingaben an input()
- Quiz-Karten in allen acht Lektionen

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
