#!/usr/bin/env python3
"""
PyPad - ein kleiner Python-Editor im Browser, der komplett offline laeuft.

Start:  PyPad.command doppelklicken   (oder: python3 pypad.py)
Alles ist lokal: Server nur auf 127.0.0.1, Ausfuehrung mit dem installierten Python.
Optionen (Umgebungsvariablen): PYPAD_PORT, PYPAD_TIMEOUT, PYPAD_MAX_RUNTIME, PYPAD_NO_BROWSER=1
"""
import ast
import builtins
import importlib
import json
import keyword
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
import uuid
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

APP_DIR = Path(__file__).resolve().parent
SNIPPET_DIR = APP_DIR / "snippets"
WORKDIR = APP_DIR / "playground"
INDEX = APP_DIR / "index.html"
VENDOR_DIR = APP_DIR / "vendor"

HOST = os.environ.get("PYPAD_HOST", "127.0.0.1")
PORT = int(os.environ.get("PYPAD_PORT", "8765"))
TIMEOUT = int(os.environ.get("PYPAD_TIMEOUT", "20"))
MAX_RUNTIME = int(os.environ.get("PYPAD_MAX_RUNTIME", "300"))
PYTHON = sys.executable or "/usr/bin/python3"
LOG_FILE = Path.home() / "Library" / "Logs" / "PyPad.log"
SNAKE = re.compile(r"^[A-Za-z0-9._ -]{1,64}$")

RUNS = {}
RUNS_LOCK = threading.Lock()
KEEP_RUNS = 20


def clean_stale_tempdirs(max_age_seconds=3600):
    """Alte Temp-Ordner wegraeumen - die bleiben liegen, wenn der Server hart beendet wird."""
    root = Path(tempfile.gettempdir())
    now = time.time()
    removed = 0
    for entry in root.glob("pypad-*"):
        try:
            if entry.is_dir() and (now - entry.stat().st_mtime) > max_age_seconds:
                shutil.rmtree(entry, ignore_errors=True)
                removed += 1
        except OSError:
            pass
    return removed


def log(msg):
    line = time.strftime("%Y-%m-%d %H:%M:%S  ") + msg
    print(line)
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except OSError:
        pass


LESSON_DIR = APP_DIR / "lektionen"
LESSON_SLUG = re.compile(r"^[a-z0-9][a-z0-9_-]{0,40}$")


def resolve_dir(rel):
    """Erlaubte Ordner: 'snippets' oder 'lektionen/<lektion>' - sonst None."""
    rel = (rel or "snippets").strip().strip("/")
    if rel in ("", "snippets"):
        return SNIPPET_DIR.resolve()
    parts = rel.split("/")
    if len(parts) == 2 and parts[0] == "lektionen" and LESSON_SLUG.match(parts[1]):
        candidate = (LESSON_DIR / parts[1]).resolve()
        base = LESSON_DIR.resolve()
        if candidate.parent == base and candidate.is_dir():
            return candidate
    return None


def file_path(directory, name):
    directory = resolve_dir(directory)
    if directory is None:
        return None
    name = (name or "").strip()
    if not name.endswith(".py"):
        name += ".py"
    if not SNAKE.match(name) or name.startswith("."):
        return None
    path = (directory / name).resolve()
    if path.parent != directory:
        return None
    return path


def port_free(port):
    # SO_REUSEADDR wie beim echten Server: TIME_WAIT-Reste blockieren dann nicht.
    s = socket.socket()
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, port))
        return True
    except OSError:
        return False
    finally:
        s.close()


def other_pypad(port):
    try:
        with urllib.request.urlopen("http://" + HOST + ":" + str(port) + "/info", timeout=1.5) as res:
            data = json.loads(res.read().decode("utf-8"))
        return "snippets" in data
    except Exception:
        return False


def open_browser(url):
    if os.environ.get("PYPAD_NO_BROWSER"):
        return
    try:
        webbrowser.open(url)
    except Exception:
        subprocess.run(["open", url], check=False)


def find_running_pypad():
    for candidate in range(PORT, PORT + 21):
        if other_pypad(candidate):
            return candidate
    return None


def pick_port(preferred):
    if port_free(preferred):
        return preferred
    for candidate in range(preferred + 1, preferred + 21):
        if port_free(candidate):
            return candidate
    return -1


KEYWORDS = sorted(set(keyword.kwlist) | set(getattr(keyword, "softkwlist", [])))
BUILTIN_NAMES = sorted(n for n in dir(builtins) if not n.startswith("_"))
STDLIB_NAMES = sorted(getattr(sys, "stdlib_module_names", ()))


def imported_roots(code):
    """Module, die der Code selbst importiert - nur fuer die werden Attribute vervollstaendigt."""
    roots = set()
    for match in re.finditer(r"^[ \t]*(?:import|from)[ \t]+([A-Za-z_][A-Za-z0-9_.]*)", code or "", re.M):
        roots.add(match.group(1).split(".")[0])
    return roots


def complete_words(code, prefix):
    prefix = (prefix or "").strip()
    if "." in prefix:
        parts = prefix.split(".")
        root = parts[0]
        if not root or root not in imported_roots(code):
            return []
        try:
            obj = importlib.import_module(root)
            for part in parts[1:-1]:
                if part:
                    obj = getattr(obj, part)
        except Exception:
            return []
        tail = parts[-1].lower()
        try:
            return sorted(n for n in dir(obj) if not n.startswith("_") and n.lower().startswith(tail))
        except Exception:
            return []
    low = prefix.lower()
    words = []
    seen = set()
    for name in KEYWORDS + BUILTIN_NAMES + STDLIB_NAMES:
        if name and name not in seen and name.lower().startswith(low):
            seen.add(name)
            words.append(name)
    return words


RUNNER_SOURCE = "\"\"\"PyPad-Runner: fuehrt den Code aus und schreibt danach die Variablen weg.\n\nWird von pypad.py automatisch erzeugt. Absichtlich so gebaut, dass Ausgabe und\nFehlermeldungen genau wie bei \"python3 main.py\" aussehen.\n\"\"\"\nimport json\nimport sys\nimport traceback\n\npfad = sys.argv[1]\nausgabe_pfad = sys.argv[2] if len(sys.argv) > 2 else None\n\nsys.argv = [pfad]\nns = {\"__name__\": \"__main__\", \"__file__\": pfad}\n\n\ndef _kurz(wert):\n    try:\n        text = repr(wert)\n    except Exception:\n        text = \"<nicht darstellbar>\"\n    text = \" \".join(text.split())\n    return text if len(text) <= 120 else text[:117] + \"...\"\n\n\ndef _sammeln():\n    wichtig = []\n    for name in sorted(ns):\n        if name.startswith(\"__\"):\n            continue\n        wert = ns[name]\n        art = type(wert).__name__\n        if art in (\"module\", \"function\", \"builtin_function_or_method\", \"type\", \"method\", \"classmethod\"):\n            continue\n        wichtig.append([name, art, _kurz(wert)])\n    return wichtig\n\n\ndef _wegschreiben():\n    if not ausgabe_pfad:\n        return\n    try:\n        with open(ausgabe_pfad, \"w\", encoding=\"utf-8\") as fh:\n            json.dump(_sammeln(), fh)\n    except Exception:\n        pass\n\n\ntry:\n    quelle = open(pfad, encoding=\"utf-8\").read()\n    code = compile(quelle, pfad, \"exec\")\nexcept SyntaxError as fehler:\n    traceback.print_exception(type(fehler), fehler, None)\n    status = 1\nelse:\n    status = 0\n    try:\n        exec(code, ns)\n    except SystemExit as fehler:\n        if isinstance(fehler.code, int):\n            status = fehler.code\n        else:\n            status = 0 if fehler.code is None else 1\n    except BaseException as fehler:   # noqa: BLE001 - genau wie Python selbst behandeln\n        tb = sys.exc_info()[2]\n        traceback.print_exception(type(fehler), fehler, tb.tb_next if tb else None)\n        status = 1\n    finally:\n        _wegschreiben()\n\nsys.exit(status)\n"


def _namen_im_code(code):
    """Alle Bezeichner aus dem Code (fuer "Meintest du ...?")"""
    return set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", code or ""))


def _vorschlag(name, kandidaten):
    import difflib
    treffer = difflib.get_close_matches(name, sorted(kandidaten), n=2, cutoff=0.75)
    return treffer


def explain_error(text, code):
    """Aus dem Traceback eine verstaendliche Erklaerung plus konkrete Tipps bauen."""
    if not text or not text.strip():
        return None
    zeilen = [z for z in text.strip().split("\n") if z.strip()]
    if not zeilen:
        return None
    letzte = zeilen[-1].strip()
    match = re.match(r"^([A-Za-z_][A-Za-z0-9_.]*)\s*:?\s*(.*)$", letzte)
    if not match:
        return None
    typ = match.group(1).split(".")[-1]
    meldung = match.group(2).strip()

    # Genaue Stelle aus dem Traceback lesen: Python zeigt die Quellzeile und darunter
    # eine Marker-Zeile wie "    ~~~^~~" - daraus kommen Start, Ende und Zeigerposition.
    zeile_nr = None
    code_stelle = ""
    span_start = None
    span_ende = None
    zeiger = None
    for i, z in enumerate(zeilen):
        mm = re.search(r'File "[^"]*main\.py", line (\d+)', z)
        if not mm:
            continue
        zeile_nr = int(mm.group(1))
        quelle = zeilen[i + 1] if i + 1 < len(zeilen) else ""
        marker = zeilen[i + 2] if i + 2 < len(zeilen) else ""
        if quelle.startswith("    ") and not quelle.lstrip().startswith("File \""):
            code_stelle = quelle[4:].rstrip()
        if "^" in marker:
            stellen = [j for j, ch in enumerate(marker) if ch in "~^"]
            if stellen:
                span_start = max(0, min(stellen) - 4)
                span_ende = max(0, max(stellen) - 4) + 1
                zeiger = max(0, marker.index("^") - 4)
    if span_start is None and zeile_nr is not None:
        span_start = 0
        span_ende = 1

    erklaerung = ""
    tipps = []

    if typ in ("SyntaxError", "IndentationError", "TabError"):
        erklaerung = "Python konnte den Text nicht als Programm lesen - irgendwo stimmt die Schreibweise nicht."
        if typ == "IndentationError" and "expected an indented block" in meldung:
            erklaerung = "Nach dem Doppelpunkt fehlt der eingerueckte Block."
            tipps.append("Direkt unter der Zeile mit ':' muss der Code eingerueckt stehen (4 Leerzeichen).")
        elif typ == "IndentationError":
            tipps.append("Diese Zeile ist anders eingerueckt als der Block darueber - pruefe die Leerzeichen.")
        tipps += [
            "Fehlt ein Doppelpunkt am Zeilenende? Beispiel: if x > 3:",
            "Fehlt eine Klammer, ein Anfuehrungszeichen oder ein Komma?",
            "Einrueckung: 4 Leerzeichen pro Ebene - Tabs und Leerzeichen nicht mischen.",
            "Der Fehler steckt oft in der Zeile DARUEBER.",
        ]

    elif typ == "NameError":
        m2 = re.search(r"name '([^']+)' is not defined", meldung)
        name = m2.group(1) if m2 else None
        erklaerung = "Python kennt diesen Namen nicht." if not name else "Python kennt den Namen '" + name + "' nicht."
        if name:
            kandidaten = _namen_im_code(code) | set(BUILTIN_NAMES)
            nah = [k for k in _vorschlag(name, kandidaten) if k != name]
            if nah:
                tipps.append("Meintest du " + " oder ".join("'" + k + "'" for k in nah) + "? (Tippfehler?)")
        tipps += [
            "Gross- und Kleinschreibung zaehlt: name und Name sind verschieden.",
            "Jeden Namen erst erzeugen, dann benutzen: name = \"Alex\"",
            "Bei input() daran denken: die Antwort muss in eine Variable gespeichert werden.",
        ]

    elif typ == "TypeError":
        m2 = re.search(r"unsupported operand type\(s\) for ([^:]+): '([^']+)' and '([^']+)'", meldung)
        m3 = re.search(r"'([^']+)' object is not (callable|subscriptable|iterable)", meldung)
        m4 = re.search(r"(?:can only concatenate|must be) (\w+)(?: \(not \"?(\w+)\"?\))?", meldung)
        if m4:
            erklaerung = "Du mischst Text und Zahl - das geht so nicht."
            tipps += [
                "Wandle um: str(zahl) fuer Text oder int(text) fuer eine Zahl.",
                "Am einfachsten mit f-string: f\"Du bist {alter} Jahre alt\"",
                "Pruefe mit print(type(x)), was wirklich in der Variablen steckt.",
            ]
        elif m2:
            art, a, b = m2.group(1).strip(), m2.group(2), m2.group(3)
            erklaerung = "Du mischst zwei verschiedene Datentypen (" + a + " und " + b + ") - das geht so nicht."
            tipps += [
                "Text und Zahl lassen sich nicht direkt verbinden. Wandle um: str(zahl) oder int(text).",
                "Am einfachsten mit f-string: f\"Du bist {alter} Jahre alt\"",
                "Pruefe mit print(type(x)), was wirklich in der Variablen steckt.",
            ]
        elif m3:
            erklaerung = "Der Wert vom Typ '" + m3.group(1) + "' kann das nicht (" + m3.group(2) + ")."
            tipps += [
                "Vielleicht hast du eine eingebaute Funktion mit einer eigenen Variable ueberschrieben (z. B. len oder sum)?",
                "Pruefe mit print(type(x)), welcher Typ wirklich drin steckt.",
            ]
        else:
            erklaerung = "Es wurden Bausteine mit den falschen Typen kombiniert."
            tipps.append("Pruefe die Typen mit print(type(x)).")

    elif typ == "ValueError":
        if "invalid literal for int()" in meldung:
            erklaerung = "int() konnte den Text nicht in eine Zahl umwandeln."
            tipps += [
                "int(\"abc\") geht nicht - nur Ziffern wie int(\"7\").",
                "Nach input() pruefe: hat der Benutzer wirklich eine Zahl getippt?",
                "Probiere es im PyPad aus: print(int(\"12\"))",
            ]
        elif "too many values to unpack" in meldung or "not enough values" in meldung:
            erklaerung = "Links und rechts vom = passen nicht zusammen."
            tipps.append("Bei a, b = ... muessen rechts genau zwei Werte stehen.")
        else:
            erklaerung = "Ein Wert passte nicht (ValueError)."
            tipps.append("Schau dir die markierte Zeile an: dort wird der Wert verarbeitet.")

    elif typ == "ZeroDivisionError":
        erklaerung = "Du teilst durch Null - das ist in Python verboten."
        tipps += [
            "Pruefe den Nenner, bevor du teilst: if nenner != 0:",
            "Haeufige Ursache: die Variable ist noch 0 oder leer.",
        ]

    elif typ == "IndexError":
        erklaerung = "Du greifst auf eine Stelle zu, die es in der Liste nicht gibt."
        tipps += [
            "Zaehlung beginnt bei 0: eine Liste mit 3 Elementen hat die Stellen 0, 1, 2.",
            "Laenge pruefen: len(liste) - die letzte Stelle ist len(liste) - 1.",
        ]

    elif typ == "KeyError":
        m2 = re.search(r"KeyError: (.+)", letzte)
        erklaerung = "Diesen Schluessel gibt es im Dictionary nicht."
        if m2:
            tipps.append("Vorher pruefen: if schluessel in daten:")
        tipps.append("Mit daten.get(\"schluessel\", \"Standard\") bekommst du keinen Fehler.")

    elif typ == "AttributeError":
        m2 = re.search(r"'([^']+)' object has no attribute '([^']+)'", meldung)
        erklaerung = "Diese Funktion/Eigenschaft gibt es fuer diesen Typ nicht."
        if m2:
            art, attr = m2.group(1), m2.group(2)
            basis = {"str": str, "int": int, "float": float, "list": list, "dict": dict, "set": set, "tuple": tuple}
            if art in basis:
                nah = [k for k in _vorschlag(attr, set(dir(basis[art]))) if k != attr]
                if nah:
                    tipps.append("Meintest du " + " oder ".join("." + k for k in nah) + "?")
            tipps.append("Der Wert ist ein " + art + " - nicht jeder Befehl passt zu jedem Typ.")
        tipps.append("Pruefe mit print(type(x)), was in der Variablen steckt.")

    elif typ in ("ModuleNotFoundError", "ImportError"):
        m2 = re.search(r"No module named '([^']+)'", meldung)
        erklaerung = "Dieses Modul gibt es nicht oder es ist nicht installiert."
        if m2:
            nah = [k for k in _vorschlag(m2.group(1), set(STDLIB_NAMES) | _namen_im_code(code)) if k != m2.group(1)]
            if nah:
                tipps.append("Meintest du " + " oder ".join("'" + k + "'" for k in nah) + "?")
        tipps += [
            "Schreibweise pruefen: math, random, os, sys sind schon dabei.",
            "Fuer Zusatz-Pakete im Terminal: pip3 install <name>",
        ]

    elif typ == "FileNotFoundError":
        erklaerung = "Die Datei wurde nicht gefunden."
        tipps += [
            "Dein Programm laeuft im Ordner playground/ - dort sucht Python die Datei.",
            "Dateinamen und Endung pruefen (z. B. notizen.txt).",
            "Beim Schreiben erst mit \"w\" anlegen: open(\"datei.txt\", \"w\")",
        ]

    elif typ == "EOFError":
        erklaerung = "Dein Programm wollte eine Eingabe (input()), es kam aber nichts an."
        tipps += [
            "Tippe die Antwort unten in die Zeile mit dem > und druecke Enter.",
            "Oder fuelle vorher das Feld \"Eingaben fuer den naechsten Start\".",
        ]

    elif typ == "UnboundLocalError":
        erklaerung = "In einer Funktion benutzt du einen Namen, bevor er dort gesetzt wurde."
        tipps.append("Setze die Variable in der Funktion oder uebergib sie als Parameter.")

    elif typ == "RecursionError":
        erklaerung = "Eine Funktion ruft sich immer wieder selbst auf und kommt nie zum Ende."
        tipps.append("Es fehlt eine Abbruch-Bedingung (if ...: return ...).")

    elif typ == "KeyboardInterrupt":
        erklaerung = "Das Programm wurde abgebrochen (Stopp oder Ctrl+C)."
        tipps.append("Das ist kein Fehler im Code.")

    else:
        erklaerung = "Fehler vom Typ " + typ + "."
        tipps += [
            "Schau dir die markierte Zeile an - dort ist es passiert.",
            "Bau kurz davor ein print(...) ein, um zu sehen, was in den Variablen steht.",
        ]

    if not tipps:
        tipps.append("Schau dir die markierte Zeile an.")

    return {
        "type": typ,
        "message": meldung,
        "line": zeile_nr,
        "col": span_start if span_start is not None else 0,
        "end": span_ende if span_ende is not None else 1,
        "zeiger": zeiger if zeiger is not None else (span_start or 0),
        "code": code_stelle,
        "erklaerung": erklaerung,
        "tipps": tipps,
    }


def _lauf_ergebnis(code, stdin_text, timeout=15):
    """Code einmal ausfuehren - fuer die Uebungs-Pruefung."""
    run = Run(code, stdin_text)
    try:
        run.proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        run.kill()
        run.proc.wait()
    time.sleep(0.15)
    with run.lock:
        chunks = list(run.chunks)
    out = "".join(c["s"] for c in chunks if c["t"] != "err")
    err = "".join(c["s"] for c in chunks if c["t"] == "err")
    rc = run.proc.returncode
    run.tmp.cleanup()
    return out, err, rc


def _als_liste(wert):
    """Einzelner Text oder Liste - immer als Liste behandeln."""
    if wert is None:
        return []
    if isinstance(wert, str):
        return [wert]
    if isinstance(wert, (list, tuple)):
        return list(wert)
    return [wert]


def _normal(text):
    return "\n".join(z.rstrip() for z in (text or "").strip().split("\n"))


def pruefen(folder, code, stufe="uebung"):
    """Den Code gegen die Faelle aus info.json pruefen."""
    try:
        info = json.loads((folder / "info.json").read_text(encoding="utf-8"))
    except Exception:
        return {"error": "fuer diese Lektion gibt es noch keine Pruefung"}
    pruefungen = info.get("pruefung") or {}
    faelle = pruefungen.get(stufe) or pruefungen.get("uebung") or []
    if not faelle:
        return {"error": "keine Pruefungsfaelle hinterlegt"}
    ergebnisse = []
    for fall in faelle:
        out, err, rc = _lauf_ergebnis(code, fall.get("stdin") or "")
        ok = rc == 0 and not err.strip()
        fehlt = []
        if ok:
            normal = _normal(out)
            klein = normal.lower()
            for muss in _als_liste(fall.get("muss_enthalten")):
                if str(muss).lower() not in klein:
                    ok = False
                    fehlt.append(str(muss))
            for darf_nicht in _als_liste(fall.get("darf_nicht_enthalten")):
                if str(darf_nicht).lower() in klein:
                    ok = False
                    fehlt.append("ohne " + str(darf_nicht))
            for muster in _als_liste(fall.get("muster")):
                if not re.search(muster, normal, re.M | re.I):
                    ok = False
                    fehlt.append("Zeile wie " + str(muster))
            if fall.get("min_zeilen") and len([z for z in normal.split("\n") if z.strip()]) < int(fall["min_zeilen"]):
                ok = False
                fehlt.append("mindestens " + str(fall["min_zeilen"]) + " Zeilen")
        eintrag = {"beschreibung": fall.get("beschreibung") or "Test", "ok": ok}
        if not ok:
            if err.strip():
                eintrag["fehler"] = err.strip().split("\n")[-1][:100]
            elif rc != 0:
                eintrag["fehler"] = "Programm lief nicht zu Ende (Zeitlimit oder Stopp)"
            if fehlt:
                eintrag["erwartet"] = "; ".join(fehlt)[:140]
            eintrag["bekommen"] = _normal(out)[:160].replace("\n", " / ")
        ergebnisse.append(eintrag)
    return {"faelle": ergebnisse}


def _fortschritt_lesen():
    try:
        daten = json.loads((LESSON_DIR / "fortschritt.json").read_text(encoding="utf-8"))
        return daten if isinstance(daten, dict) else {}
    except Exception:
        return {}


def scope_nodes(scope):
    """Alle Knoten eines Scopes, aber nicht in tiefere Scopes (Funktionen/Klassen) hinein."""
    result = []
    stack = list(ast.iter_child_nodes(scope))
    while stack:
        node = stack.pop()
        result.append(node)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            continue
        stack.extend(ast.iter_child_nodes(node))
    return result


def lint_code(code):
    """Einfache Hinweise auf typische Stolpersteine - ersetzt keinen echten Linter."""
    try:
        tree = ast.parse(code or "")
    except SyntaxError:
        return []

    def used(name):
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id == name and isinstance(node.ctx, ast.Load):
                return True
        return False

    hints = []

    # unbenutzte Importe
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                bound = alias.asname or alias.name.split(".")[0]
                if not used(bound):
                    hints.append({"line": node.lineno, "col": 0,
                                  "text": "Import '" + bound + "' wird nie benutzt"})
        elif isinstance(node, ast.ImportFrom):
            if node.module == "__future__":
                continue
            for alias in node.names:
                if alias.name == "*":
                    continue
                bound = alias.asname or alias.name
                if not used(bound):
                    hints.append({"line": node.lineno, "col": 0,
                                  "text": "'" + bound + "' importiert, aber nie benutzt"})

    # Zuweisungen, die nie gelesen werden (nur einfache Zuweisungen, keine Schleifenvariablen)
    scopes = [tree] + [n for n in ast.walk(tree)
                       if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    schon_gemeldet = set()
    for scope in scopes:
        stores = {}
        loads = set()
        for node in scope_nodes(scope):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        stores.setdefault(target.id, target)
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                stores.setdefault(node.target.id, node.target)
            elif isinstance(node, ast.Name):
                if isinstance(node.ctx, ast.Load):
                    loads.add(node.id)
                elif isinstance(node.ctx, ast.Store):
                    loads.discard(node.id)
        if scope is tree:
            loads |= {n.id for n in ast.walk(tree)
                      if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
        for name, node in stores.items():
            if name.startswith("_") or name in loads or node.lineno in schon_gemeldet:
                continue
            schon_gemeldet.add(node.lineno)
            start = getattr(node, "col_offset", 0)
            hints.append({"line": node.lineno, "col": start, "end": start + len(name),
                          "text": "'" + name + "' wird zugewiesen, aber nirgends benutzt"})

    # except ohne Typ
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            start = getattr(node, "col_offset", 0)
            hints.append({"line": node.lineno, "col": start, "end": start + len("except:"),
                          "text": "except: faengt ALLE Fehler - besser 'except Exception:'"})

    # Vergleich mit None
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for op, comp in zip(node.ops, node.comparators):
                if isinstance(comp, ast.Constant) and comp.value is None and isinstance(op, (ast.Eq, ast.NotEq)):
                    start = getattr(comp, "col_offset", 0)
                    hints.append({"line": getattr(comp, "lineno", node.lineno), "col": start, "end": start + 4,
                                  "text": "Vergleich mit None: 'is None' / 'is not None' benutzen"})

    # Namen sammeln, die irgendwo im Code gesetzt werden (Store, Parameter, Import, def/class)
    erste_stelle = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            erste_stelle.setdefault(node.id, node.lineno)
        elif isinstance(node, ast.arg):
            erste_stelle.setdefault(node.arg, node.lineno)
        elif isinstance(node, ast.alias):
            erste_stelle.setdefault((node.asname or node.name).split(".")[0], getattr(node, "lineno", 0))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            erste_stelle.setdefault(node.name, node.lineno)
        elif isinstance(node, ast.ExceptHandler) and node.name:
            erste_stelle.setdefault(node.name, node.lineno)
        elif isinstance(node, (ast.Global, ast.Nonlocal)):
            for name in node.names:
                erste_stelle.setdefault(name, node.lineno)
        elif isinstance(node, (ast.MatchAs, ast.MatchStar)) and getattr(node, "name", None):
            erste_stelle.setdefault(node.name, node.lineno)

    # nur die Stellen auf Modulebene (ohne Funktionen/Klassen) - fuer "benutzt vor dem Setzen"
    modul_stores = set()
    for node in scope_nodes(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            modul_stores.add(node.id)

    stern_import = any(isinstance(n, ast.ImportFrom) and any(a.name == "*" for a in n.names)
                       for n in ast.walk(tree))

    gemeldet = set()
    for node in scope_nodes(tree):   # nur Modulebene: Nutzung vor der Zuweisung
        if not (isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)):
            continue
        name = node.id
        if name in BUILTIN_NAMES or name in ("__file__", "__name__", "__doc__"):
            continue
        if name not in erste_stelle and not stern_import:
            key = (node.lineno, name)
            if key not in gemeldet:
                gemeldet.add(key)
                hints.append({"line": node.lineno, "col": node.col_offset, "end": node.col_offset + len(name),
                              "text": "'" + name + "' ist nirgends definiert (Tippfehler?)"})
        elif name in modul_stores and erste_stelle.get(name, 0) > node.lineno:
            key = (node.lineno, name)
            if key not in gemeldet:
                gemeldet.add(key)
                hints.append({"line": node.lineno, "col": node.col_offset, "end": node.col_offset + len(name),
                              "text": "'" + name + "' wird benutzt, bevor es gesetzt wird"})

    # Funktionen, die nie einen Wert zurueckgeben - aber deren Ergebnis benutzt wird
    eltern = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            eltern[id(child)] = parent

    def gibt_wert(tree_scope):
        if any(isinstance(n, (ast.Yield, ast.YieldFrom)) for n in ast.walk(tree_scope)):
            return True
        if any(isinstance(n, ast.Return) and n.value is not None for n in ast.walk(tree_scope)):
            return True
        body = getattr(tree_scope, "body", [])
        if body and isinstance(body[-1], ast.Raise):
            return True
        return False

    ohne_wert = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not gibt_wert(node):
            ohne_wert.setdefault(node.name, node.lineno)

    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)):
            continue
        name = node.func.id
        if name not in ohne_wert:
            continue
        parent = eltern.get(id(node))
        if isinstance(parent, ast.Expr):
            continue   # Ergebnis wird gar nicht benutzt - kein Problem
        hints.append({"line": node.lineno, "col": 0,
                      "text": "Funktion '" + name + "' gibt nichts zurueck (None) - das Ergebnis wird trotzdem benutzt"})

    hints.sort(key=lambda h: (h["line"], h["text"]))
    return hints


class Run:
    """Ein laufendes Programm: Ausgabe wird gestreamt, Eingaben kommen live rein."""

    def __init__(self, code, prefill):
        self.id = uuid.uuid4().hex[:12]
        self.chunks = []
        self.lock = threading.Lock()
        self.done = False
        self.returncode = None
        self.code = code
        self.explain = None
        self.started = time.time()
        self.killed_by_timeout = False
        self.tmp = tempfile.TemporaryDirectory(prefix="pypad-")
        script = Path(self.tmp.name) / "main.py"
        script.write_text(code, encoding="utf-8")
        runner = Path(self.tmp.name) / "_pypad_runner.py"
        runner.write_text(RUNNER_SOURCE, encoding="utf-8")
        self.vars_path = Path(self.tmp.name) / "_pypad_vars.json"
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["PYTHONUNBUFFERED"] = "1"
        env["MPLBACKEND"] = "Agg"
        start_kwargs = {}
        if os.name == "posix":
            start_kwargs["start_new_session"] = True   # eigene Prozessgruppe (killpg)
        else:
            start_kwargs["creationflags"] = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        self.proc = subprocess.Popen(
            [PYTHON, "-u", str(runner), str(script), str(self.vars_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(WORKDIR),
            env=env,
            **start_kwargs,
        )
        threading.Thread(target=self._reader, args=(self.proc.stdout, "out"), daemon=True).start()
        threading.Thread(target=self._reader, args=(self.proc.stderr, "err"), daemon=True).start()
        threading.Thread(target=self._watcher, daemon=True).start()
        if prefill:
            self.write(prefill if prefill.endswith("\n") else prefill + "\n")

    def _add(self, kind, text):
        with self.lock:
            self.chunks.append({"t": kind, "s": text})

    def _reader(self, pipe, kind):
        try:
            while True:
                data = os.read(pipe.fileno(), 4096)
                if not data:
                    break
                self._add(kind, data.decode("utf-8", "replace"))
        except (OSError, ValueError):
            pass
        finally:
            try:
                pipe.close()
            except Exception:
                pass

    def _watcher(self):
        try:
            self.proc.wait(timeout=MAX_RUNTIME)
        except subprocess.TimeoutExpired:
            self.killed_by_timeout = True
            self._add("sys", "\n[PyPad] Zeitlimit von " + str(MAX_RUNTIME) + " s erreicht - Programm beendet.\n")
            self.kill()
            self.proc.wait()
        self.returncode = self.proc.returncode
        self.done = True

    def write(self, text):
        with self.lock:
            if self.done or self.proc.stdin is None:
                return False
            try:
                self.proc.stdin.write(text.encode("utf-8"))
                self.proc.stdin.flush()
                return True
            except (BrokenPipeError, ValueError, OSError):
                return False

    def kill(self):
        if os.name == "posix":
            try:
                os.killpg(os.getpgid(self.proc.pid), getattr(signal, "SIGKILL", signal.SIGTERM))
                return
            except Exception:
                pass
        try:
            self.proc.kill()
        except Exception:
            pass

    def snapshot(self, start):
        with self.lock:
            chunks = self.chunks[start:]
            total = len(self.chunks)
        if self.done and self.explain is None:
            try:
                fehlertext = "".join(c["s"] for c in chunks if c["t"] == "err")
                if not fehlertext:
                    with self.lock:
                        fehlertext = "".join(c["s"] for c in self.chunks if c["t"] == "err")
                self.explain = explain_error(fehlertext, self.code) or {}
            except Exception:
                self.explain = {}
        variablen = None
        if self.done:
            try:
                if self.vars_path.exists():
                    variablen = json.loads(self.vars_path.read_text(encoding="utf-8"))
            except Exception:
                variablen = None
        return {
            "chunks": chunks,
            "next": total,
            "done": self.done,
            "returncode": self.returncode,
            "ms": int((time.time() - self.started) * 1000),
            "explanation": self.explain if self.done else None,
            "vars": variablen,
        }


def register(run):
    with RUNS_LOCK:
        RUNS[run.id] = run
        if len(RUNS) > KEEP_RUNS:
            for rid in sorted(RUNS, key=lambda k: RUNS[k].started):
                if rid != run.id and RUNS[rid].done:
                    old = RUNS.pop(rid)
                    try:
                        old.tmp.cleanup()
                    except Exception:
                        pass
                if len(RUNS) <= KEEP_RUNS:
                    break


class Handler(BaseHTTPRequestHandler):
    server_version = "PyPad/2.0"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        pass

    def _send(self, status, body, ctype="application/json; charset=utf-8"):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "close")
        self.close_connection = True
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, status=200):
        self._send(status, json.dumps(obj))

    def _body(self):
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            return {}
        if length <= 0:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception:
            return {}

    def _run_by_id(self, rid):
        return RUNS.get((rid or "").strip())

    def do_OPTIONS(self):
        self._send(204, "", "text/plain; charset=utf-8")

    def do_GET(self):
        url = urlparse(self.path)
        if url.path in ("/", "/index.html"):
            try:
                self._send(200, INDEX.read_text(encoding="utf-8"), "text/html; charset=utf-8")
            except FileNotFoundError:
                self._send(500, "index.html fehlt", "text/plain; charset=utf-8")
            return
        if url.path.startswith("/vendor/"):
            name = url.path[len("/vendor/"):]
            if not re.match(r"^[A-Za-z0-9_.-]{1,64}$", name):
                self._send(404, "not found", "text/plain; charset=utf-8")
                return
            path = (VENDOR_DIR / name).resolve()
            if path.parent != VENDOR_DIR.resolve() or not path.is_file():
                self._send(404, "not found", "text/plain; charset=utf-8")
                return
            ctype = "application/javascript; charset=utf-8" if name.endswith(".js") else "text/plain; charset=utf-8"
            self._send(200, path.read_bytes(), ctype)
            return
        if url.path == "/info":
            self._json({
                "python": PYTHON,
                "version": sys.version.split()[0],
                "timeout": MAX_RUNTIME,
                "snippets": str(SNIPPET_DIR),
                "playground": str(WORKDIR),
            })
            return
        if url.path == "/fortschritt":
            self._json({"fortschritt": _fortschritt_lesen()})
            return
        if url.path == "/lektion-info":
            query = parse_qs(url.query)
            folder = resolve_dir((query.get("dir") or [""])[0])
            if folder is None:
                self._json({"error": "ungueltiger Ordner"}, 400)
                return
            try:
                self._json(json.loads((folder / "info.json").read_text(encoding="utf-8")))
            except Exception:
                self._json({})
            return
        if url.path == "/lektionen":
            try:
                data = json.loads((LESSON_DIR / "lektionen.json").read_text(encoding="utf-8"))
            except Exception:
                data = []
            self._json({"lektionen": data})
            return
        if url.path == "/files":
            query = parse_qs(url.query)
            directory = resolve_dir((query.get("dir") or ["snippets"])[0])
            if directory is None:
                self._json({"error": "ungueltiger Ordner"}, 400)
                return
            self._json({"files": sorted(p.name for p in directory.glob("*.py"))})
            return
        if url.path == "/file":
            query = parse_qs(url.query)
            directory = (query.get("dir") or ["snippets"])[0]
            path = file_path(directory, (query.get("name") or [""])[0])
            if not path or not path.exists():
                self._json({"error": "nicht gefunden"}, 404)
                return
            self._json({"name": path.name, "dir": directory, "code": path.read_text(encoding="utf-8")})
            return
        self._send(404, "not found", "text/plain; charset=utf-8")

    def do_POST(self):
        url = urlparse(self.path)
        data = self._body()

        if url.path == "/pruefen":
            folder = resolve_dir(data.get("dir"))
            code = data.get("code") or ""
            if folder is None or not code.strip():
                self._json({"error": "ungueltiger Aufruf"}, 400)
                return
            self._json(pruefen(folder, code, data.get("stufe") or "uebung"))
            return

        if url.path == "/fortschritt":
            eintrag = {"erledigt": bool(data.get("erledigt")), "datum": time.strftime("%Y-%m-%d %H:%M")}
            daten = _fortschritt_lesen()
            daten[str(data.get("dir") or "").strip()] = eintrag
            try:
                (LESSON_DIR / "fortschritt.json").write_text(
                    json.dumps(daten, ensure_ascii=False, indent=2), encoding="utf-8")
                self._json({"gespeichert": True})
            except OSError as exc:
                self._json({"error": str(exc)}, 500)
            return

        if url.path == "/complete":
            self._json({"words": complete_words(data.get("code") or "", data.get("prefix") or "")})
            return

        if url.path == "/run/start":
            code = data.get("code") or ""
            if not code.strip():
                self._json({"error": "leerer Code"}, 400)
                return
            run = Run(code, data.get("stdin") or "")
            register(run)
            self._json({"id": run.id, "warnings": lint_code(code)})
            return

        if url.path == "/run/poll":
            run = self._run_by_id(data.get("id"))
            if not run:
                self._json({"error": "unbekannte Lauf-ID"}, 404)
                return
            try:
                start = int(data.get("from") or 0)
            except (TypeError, ValueError):
                start = 0
            self._json(run.snapshot(max(0, start)))
            return

        if url.path == "/run/input":
            run = self._run_by_id(data.get("id"))
            if not run:
                self._json({"error": "unbekannte Lauf-ID"}, 404)
                return
            text = data.get("text")
            text = "" if text is None else str(text)
            self._json({"ok": run.write(text + "\n"), "done": run.done})
            return

        if url.path == "/run/stop":
            run = self._run_by_id(data.get("id"))
            if not run:
                self._json({"error": "unbekannte Lauf-ID"}, 404)
                return
            run.kill()
            self._json({"stopped": True})
            return

        if url.path == "/run":
            code = data.get("code") or ""
            if not code.strip():
                self._json({"stdout": "", "stderr": "", "returncode": 0, "ms": 0})
                return
            started = time.time()
            run = Run(code, data.get("stdin") or "")
            register(run)
            timed_out = False
            try:
                run.proc.wait(timeout=TIMEOUT)
            except subprocess.TimeoutExpired:
                timed_out = True
                run.kill()
                run.proc.wait()
            time.sleep(0.15)
            with run.lock:
                chunks = list(run.chunks)
            out = "".join(c["s"] for c in chunks if c["t"] != "err")
            err = "".join(c["s"] for c in chunks if c["t"] == "err")
            if timed_out:
                err += "\n[PyPad] Zeitlimit von " + str(TIMEOUT) + " s erreicht - Programm beendet.\n"
            run.tmp.cleanup()
            with RUNS_LOCK:
                RUNS.pop(run.id, None)
            self._json({
                "stdout": out,
                "stderr": err,
                "returncode": run.proc.returncode,
                "ms": int((time.time() - started) * 1000),
            })
            return

        if url.path == "/file":
            path = file_path(data.get("dir"), data.get("name"))
            if not path:
                self._json({"error": "ungueltiger Name oder Ordner"}, 400)
                return
            path.write_text(data.get("code") or "", encoding="utf-8")
            self._json({"saved": path.name, "dir": data.get("dir") or "snippets"})
            return

        if url.path == "/delete":
            path = file_path(data.get("dir"), data.get("name"))
            if not path or not path.exists():
                self._json({"error": "nicht gefunden"}, 404)
                return
            path.unlink()
            self._json({"deleted": path.name})
            return

        self._send(404, "not found", "text/plain; charset=utf-8")


def main():
    SNIPPET_DIR.mkdir(exist_ok=True)
    WORKDIR.mkdir(exist_ok=True)
    LESSON_DIR.mkdir(exist_ok=True)
    stale = clean_stale_tempdirs()
    if stale:
        log("Aufgeraeumt: " + str(stale) + " alte Temp-Ordner")
    running = find_running_pypad()
    if running is not None:
        url = "http://" + HOST + ":" + str(running) + "/"
        log("PyPad laeuft bereits auf Port " + str(running) + " - oeffne " + url)
        open_browser(url)
        return
    port = pick_port(PORT)
    if port < 0:
        log("Kein freier Port zwischen " + str(PORT) + " und " + str(PORT + 20) + ". Beende.")
        sys.exit(1)
    if port != PORT:
        log("Port " + str(PORT) + " ist belegt - PyPad nutzt " + str(port) + ".")
    url = "http://" + HOST + ":" + str(port) + "/"
    try:
        httpd = ThreadingHTTPServer((HOST, port), Handler)
    except OSError as exc:
        log("Server konnte nicht starten: " + str(exc))
        sys.exit(1)
    log("PyPad laeuft: " + url)
    log("Ordner: " + str(APP_DIR))
    log("Python: " + PYTHON + " (" + sys.version.split()[0] + ")")
    log("Snippets: " + str(SNIPPET_DIR))
    log("Dieses Fenster offen lassen, solange du PyPad nutzt. Beenden mit Ctrl+C.")
    threading.Timer(0.7, lambda: open_browser(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        log("PyPad beendet.")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
