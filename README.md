# PyPad

Ein kleiner Python-Editor im Browser, der **komplett offline** auf dem eigenen Mac läuft.
Kein Internet, kein Konto, keine Cloud: die Oberfläche ist eine lokale Webseite auf `127.0.0.1`,
ausgeführt wird dein Code mit dem installierten Python.

*A tiny offline Python editor for macOS: local browser UI on 127.0.0.1, code runs with your own Python.*

## Was drin ist

- **Editor (Ace)** mit Python-Syntaxhervorhebung, Zeilennummern und **Autovervollständigung**
  (Python-Schlüsselwörter, Builtins, Modulnamen deiner Installation; bei `os.` / `math.` auch die
  echten Attribute — nur für Module, die der Code selbst importiert)
- **Ausführen** per Klick oder **Cmd+Enter**: Ausgabe und Fehler getrennt, Exit-Code und Laufzeit
- **Echte Live-Eingabe:** `input()` funktioniert wie im Terminal — unten tippen, Enter
- **■ Stopp** beendet laufende Programme (auch Endlosschleifen; Kindprozesse werden mitbeendet),
  Standard-Zeitlimit 300 s
- **Snippets** speichern / laden / löschen
- **Lernbereich:** Lektionen mit *Beispiel / Übung / Lösung*; Wechseln verliert keine Eingaben,
  Übungen werden automatisch gesichert
- **Selbsttest** mit 65 Prüfungen (`selbsttest.py`)

## Voraussetzungen

- macOS mit Python 3 (getestet mit 3.14) — Prüfen: `python3 --version`
- Sonst nichts: keine externen Bibliotheken, kein Build-Schritt, keine Installation

## Start

```bash
git clone https://github.com/Xonni-star/pypad.git
cd pypad
./PyPad.command          # oder: python3 pypad.py
```

Der Browser öffnet sich automatisch auf `http://127.0.0.1:8765/`.
Terminal-Fenster offen lassen; beenden mit Ctrl+C.

## Selbsttest

```bash
python3 selbsttest.py     # PyPad muss dabei laufen
```

## Optionen (Umgebungsvariablen)

| Variable | Standard | Bedeutung |
|---|---|---|
| `PYPAD_PORT` | 8765 | Port des lokalen Servers |
| `PYPAD_MAX_RUNTIME` | 300 | Zeitlimit pro Lauf in Sekunden |
| `PYPAD_TIMEOUT` | 20 | Zeitlimit nur für den einfachen `/run`-Endpunkt |
| `PYPAD_NO_BROWSER` | — | `1` = Browser nicht automatisch öffnen |

## Endpunkte (lokal)

| Methode | Pfad | Zweck |
|---|---|---|
| GET | `/` | Oberfläche |
| GET | `/info` | Python-Version, Pfade, Zeitlimit |
| GET | `/lektionen` | Liste der Lektionen |
| GET | `/files?dir=`, `/file?dir=&name=` | Datei listen / lesen |
| POST | `/file`, `/delete` | Datei speichern / löschen |
| POST | `/complete` | Vervollständigungsvorschläge |
| POST | `/run/start`, `/run/poll`, `/run/input`, `/run/stop` | Programm starten, Ausgabe streamen, Eingabe, Stopp |
| POST | `/run` | starten + auf Ende warten (einfach, für Skripte) |

## Sicherheit

- Der Server hört **nur auf 127.0.0.1** — von außen nicht erreichbar.
- Dateizugriff ausschließlich in `snippets/` und `lektionen/<lektion>/`;
  Pfad-Traversal, absolute Pfade und Punkt-Dateien werden abgewiesen.
- Programme laufen als dein Benutzer in einer eigenen Prozessgruppe.

## Eigene Lektionen

Als Beispiel liegt ein Lernpaket bei: §F§lektionen/lektion-01-ausgaben/§F§ (Beispiel, Übung, Lösung).
Eigene Lektionen einfach daneben anlegen und in §F§lektionen/lektionen.json§F§ eintragen:

```text
lektionen/lektionen.json           # [{"nr": "01", "titel": "...", "dir": "lektion-01-..."}]
lektionen/lektion-01-.../beispiel.py
lektionen/lektion-01-.../uebung.py
lektionen/lektion-01-.../LOESUNG.py
```

## Lizenz

PyPad steht unter der **MIT-Lizenz** — vollständiger Text in [LICENSE](LICENSE).
Kurz: benutzen, verändern und weitergeben erlaubt, solange Copyright-Hinweis und Lizenztext
mitgeliefert werden. **Keine Gewährleistung** („as is"), Benutzung auf eigene Gefahr;
Haftung für Schäden oder Datenverlust ist ausgeschlossen.

**Fremdcode:** Der mitgelieferte Editor **Ace 1.44.0** (`vendor/`) steht unter der
**BSD-3-Clause-Lizenz**, © 2010 Ajax.org B.V. Der vollständige Lizenztext, die Dateiliste und die
Prüfsummen stehen in [THIRD-PARTY.md](THIRD-PARTY.md). Darüber hinaus wird **kein** Fremdcode
verwendet — PyPad nutzt ausschließlich die Python-Standardbibliothek.

**Sicherheit & Haftung:** PyPad führt Python-Code lokal auf dem eigenen Rechner aus und lauscht
nur auf 127.0.0.1. Führe damit keinen Code aus, dem du nicht vertraust, und sichere eigene
Daten — für Datenverlust wird nicht gehaftet (siehe MIT-Lizenz).

**Datenschutz:** PyPad selbst baut **keine Verbindungen ins Internet** auf — keine Telemetrie,
keine Konten, keine externen Dienste, keine Cookies. Alle Dateien (Code, Einstellungen) bleiben
lokal. (Der Code, den *du* ausführst, kann natürlich selbst Netzwerk nutzen — das liegt in deiner Hand.)
