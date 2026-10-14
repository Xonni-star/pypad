"""Selbsttest fuer PyPad - prueft den kleinen Server auf Herz und Nieren.

Aufruf (PyPad muss laufen):
    cd ~/Desktop/PyPad && python3 selbsttest.py
Optional anderer Port:
    PYPAD_BASE=http://127.0.0.1:8766 python3 selbsttest.py
"""
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

BASE = os.environ.get("PYPAD_BASE", "http://127.0.0.1:8765")
NL = chr(10)
results = []


def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))


def req(path, data=None, method=None, raw=None, timeout=30):
    body = None
    headers = {}
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
    elif raw is not None:
        body = raw.encode("utf-8")
        headers["Content-Type"] = "application/json"
    r = urllib.request.Request(BASE + path, data=body, headers=headers,
                               method=method or ("POST" if body is not None else "GET"))
    try:
        with urllib.request.urlopen(r, timeout=timeout) as res:
            return res.status, res.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def start(code, stdin=""):
    st, b = req("/run/start", {"code": code, "stdin": stdin})
    return json.loads(b).get("id")


def poll(rid, frm=0):
    st, b = req("/run/poll", {"id": rid, "from": frm})
    return json.loads(b)


def inp(rid, text):
    return json.loads(req("/run/input", {"id": rid, "text": text})[1])


def stop(rid):
    return json.loads(req("/run/stop", {"id": rid})[1])


def text_of(p, kind=None):
    return "".join(c["s"] for c in p.get("chunks", []) if kind is None or c["t"] == kind)


# ---------- Seite und Assets ----------
st, b = req("/")
page = b.decode("utf-8")
check("GET / liefert 200 HTML", st == 200 and "<!doctype html>" in page.lower())
check("Ace wird eingebunden", "vendor/ace.js" in page and "ace.edit" in page)
check("Live-Eingabezeile vorhanden", 'id="live"' in page)
check("Stopp-Knopf vorhanden", 'id="btnStop"' in page)
check("Completer im Client", "addCompleter" in page and "dottedChain" in page)

for f, minsize in [("ace.js", 300000), ("mode-python.js", 5000), ("theme-tomorrow_night.js", 2000),
                   ("ext-language_tools.js", 40000), ("ext-searchbox.js", 8000)]:
    st, b = req("/vendor/" + f)
    check("vendor/" + f, st == 200 and len(b) >= minsize, str(st) + " " + str(len(b)))

st, b = req("/vendor/gibtsnicht.js")
check("vendor unbekannt -> 404", st == 404, str(st))
st, b = req("/vendor/..%2fpypad.py")
check("vendor Traversal (encoded) -> 404", st == 404, str(st))
st, b = req("/vendor/PYPAD.PY")
check("vendor Gross/Klein -> 404", st == 404, str(st))
st, b = req("/gibtsnicht")
check("unbekannter Pfad -> 404", st == 404, str(st))
st, b = req("/run/start", method="GET")
check("GET auf /run/start -> 404", st == 404, str(st))

# ---------- /info ----------
st, b = req("/info")
d = json.loads(b)
check("/info liefert Felder", st == 200 and d.get("version") and d.get("snippets"), str(st))

# ---------- /complete ----------
def words(code, prefix):
    return json.loads(req("/complete", {"code": code, "prefix": prefix})[1]).get("words", [])

check("Vervollstaendigung: 'pri' -> print", "print" in words("", "pri"))
check("Vervollstaendigung: 'len' -> len", "len" in words("", "len"))
check("Vervollstaendigung: stdlib 'ima' -> imaplib", "imaplib" in words("", "ima"))
check("Vervollstaendigung: math.sq -> sqrt", words("import math", "math.sq") == ["sqrt"])
check("Attribut ohne import abgewiesen", words("x = 1", "math.sq") == [])
check("os. liefert Attribute", len(words("import os", "os.")) > 50)
check("leerer Prefix liefert Liste", len(words("", "")) > 100)
check("Gross/Klein egal", "print" in words("", "PRI"))

# ---------- Snippets ----------
tmpname = "zz_check_tmp"
st, b = req("/file", {"name": tmpname, "code": "print('hallo')"})
check("Snippet speichern", st == 200 and json.loads(b).get("saved") == tmpname + ".py", str(st))
check("Snippet wird gelistet", tmpname + ".py" in json.loads(req("/files")[1])["files"])
check("Snippet laden", json.loads(req("/file?name=" + tmpname + ".py")[1])["code"] == "print('hallo')")
st, b = req("/delete", {"name": tmpname})
check("Snippet loeschen", st == 200 and tmpname + ".py" not in json.loads(req("/files")[1])["files"], str(st))
st, b = req("/file", {"name": "../boese", "code": "x"})
check("Snippet Traversal abgewiesen", st == 400, str(st))
st, b = req("/file", {"name": "unter/ordner", "code": "x"})
check("Snippet mit Slash abgewiesen", st == 400, str(st))
st, b = req("/file", {"name": "x" * 90, "code": "x"})
check("zu langer Snippet-Name abgewiesen", st == 400, str(st))
st, b = req("/delete", {"name": "gibtsnicht"})
check("unbekanntes Snippet loeschen -> 404", st == 404, str(st))

# ---------- Laufzeit: interaktiv ----------
rid = start('a = input("A? ")' + NL + 'b = input("B? ")' + NL + 'print("sum", a, b)')
time.sleep(0.9)
p = poll(rid)
check("Prompt kommt vor Programmende", "A? " in text_of(p, "out") and p["done"] is False, repr(text_of(p)))
inp(rid, "eins")
time.sleep(0.5)
p2 = poll(rid, p["next"])
check("zweiter Prompt", "B? " in text_of(p2, "out"), repr(text_of(p2)))
inp(rid, "zwei")
time.sleep(0.7)
p3 = poll(rid, p2["next"])
check("Programm laeuft mit Live-Eingaben durch",
      "sum eins zwei" in text_of(p3, "out") and p3["done"] is True and p3["returncode"] == 0,
      repr(text_of(p3)) + " rc=" + str(p3["returncode"]))

# ---------- Fehlerfaelle ----------
rid = start('raise ValueError("kaputt")')
time.sleep(0.9)
p = poll(rid)
check("Fehler auf stderr getrennt", "ValueError" in text_of(p, "err") and p["returncode"] != 0,
      "err=" + repr(text_of(p, "err"))[:80])
rid = start('def (')
time.sleep(0.9)
p = poll(rid)
check("Syntaxfehler gemeldet", "SyntaxError" in text_of(p, "err"))
rid = start('x = input()' + NL + 'y = input()' + NL + 'print(x, y)', "eins" + NL + "zwei")
time.sleep(1.0)
p = poll(rid)
check("Vorab-Eingaben mehrzeilig", "eins zwei" in text_of(p, "out"), repr(text_of(p, "out")))
rid = start('x = input()' + NL + 'y = input()' + NL + 'print("zwei:", x, y)', "nur_eine")
time.sleep(1.0)
p = poll(rid)
check("zweites input() wartet auf Live-Eingabe", p["done"] is False and "zwei:" not in text_of(p, "out"),
      repr(text_of(p)))
inp(rid, "doch_noch")
time.sleep(0.8)
p2 = poll(rid, p["next"])
check("nachgetippte Eingabe wird angenommen",
      "zwei: nur_eine doch_noch" in text_of(p2, "out") and p2["done"] is True, repr(text_of(p2)))

# ---------- Stopp und Prozess-Hygiene ----------
rid = start('import time' + NL + 'print("start")' + NL + 'while True: time.sleep(0.2)')
time.sleep(1.0)
stop(rid)
time.sleep(0.9)
p = poll(rid)
check("Stopp beendet Endlosschleife", p["done"] is True and (p["returncode"] or 0) < 0, str(p["returncode"]))
rid = start('import subprocess, time' + NL + 'subprocess.Popen(["sleep", "120"])' + NL
            + 'print("kind gestartet", flush=True)' + NL + 'while True: time.sleep(0.2)')
time.sleep(1.4)
stop(rid)
time.sleep(1.0)
kids = subprocess.run(["pgrep", "-fl", "sleep 120"], capture_output=True, text=True).stdout.strip()
check("Kindprozesse werden mitbeendet", "sleep 120" not in kids, kids[:120])
st, b = req("/run/poll", {"id": "gibtsnicht"})
check("unbekannte Lauf-ID -> 404", st == 404, str(st))
st, b = req("/run/input", {"id": "gibtsnicht", "text": "x"})
check("input an unbekannte ID -> 404", st == 404, str(st))
st, b = req("/run/stop", {"id": "gibtsnicht"})
check("stop an unbekannte ID -> 404", st == 404, str(st))
st, b = req("/run/start", {"code": "   "})
check("leerer Code -> 400", st == 400, str(st))
st, b = req("/run/start", raw="{kaputt")
check("kaputtes JSON -> kein Absturz", st in (400, 404, 500), str(st))

# ---------- parallel ----------
r1 = start('import time' + NL + 'for i in range(6):' + NL + '    print("A", i, flush=True)' + NL + '    time.sleep(0.1)')
r2 = start('import time' + NL + 'for i in range(6):' + NL + '    print("B", i, flush=True)' + NL + '    time.sleep(0.1)')
time.sleep(2.0)
p1 = poll(r1)
p2 = poll(r2)
check("zwei Laeufe gleichzeitig", "A 5" in text_of(p1, "out") and "B 5" in text_of(p2, "out"))

# ---------- einfacher Modus /run ----------
st, b = req("/run", {"code": "print(6*7)"})
d = json.loads(b)
check("/run: stdout + exit 0", d["stdout"].strip() == "42" and d["returncode"] == 0, repr(d["stdout"]))
st, b = req("/run", {"code": "1/0"})
d = json.loads(b)
check("/run: stderr bei Fehler", "ZeroDivisionError" in d["stderr"])
st, b = req("/run", {"code": 'print("Grüße, 😀 üäö")'})
check("/run: Umlaute und Emoji", "Grüße" in json.loads(b)["stdout"] and "😀" in json.loads(b)["stdout"])
st, b = req("/run", {"code": "for i in range(5000):" + NL + "    print(i)"})
d = json.loads(b)
check("/run: 5000 Zeilen Ausgabe", d["stdout"].count(NL) >= 5000 and d["returncode"] == 0,
      "Zeilen=" + str(d["stdout"].count(NL)))
st, b = req("/run", {"code": "open('check_tmp.txt', 'w').write('ok')" + NL + "print(open('check_tmp.txt').read())"})
d = json.loads(b)
check("/run: Datei im playground", d["stdout"].strip() == "ok" and os.path.exists("playground/check_tmp.txt"), repr(d["stdout"]))

# ---------- Lektionen ----------
st, b = req("/lektionen")
lessons = json.loads(b).get("lektionen", [])
check("Lektionen werden gelistet", len(lessons) >= 1 and lessons[0].get("nr") == "01", repr(lessons)[:90])
first = lessons[0]["dir"] if lessons else "lektion-01-ausgaben"
st, b = req("/files?dir=lektionen/" + first)
files = json.loads(b).get("files", [])
check("Lektionsdateien gelistet", {"beispiel.py", "uebung.py", "LOESUNG.py"} <= set(files), repr(files))
missing = []
for lesson in lessons:
    st2, b2 = req("/files?dir=lektionen/" + lesson["dir"])
    namen = set(json.loads(b2).get("files", []))
    if not {"beispiel.py", "uebung.py", "LOESUNG.py"} <= namen:
        missing.append(lesson["dir"])
check("Jede Lektion hat Beispiel, Uebung und Loesung", bool(lessons) and not missing, repr(missing))
st, b = req("/file?dir=lektionen/" + first + "&name=uebung.py")
check("Uebung ladbar", st == 200 and bool(json.loads(b)["code"].strip()), str(st))
st, b = req("/file?dir=lektionen/" + first + "&name=LOESUNG.py")
check("Loesung ladbar", st == 200 and bool(json.loads(b)["code"].strip()), str(st))
st, b = req("/file?dir=lektionen/../..&name=pypad.py")
check("Lektions-Traversal abgewiesen", st in (400, 404), str(st))
st, b = req("/file?dir=/etc&name=passwd")
check("absoluter Pfad abgewiesen", st in (400, 404), str(st))
st, b = req("/file?dir=lektionen/gibtsnicht&name=uebung.py")
check("unbekannte Lektion abgewiesen", st in (400, 404), str(st))
st, b = req("/file", {"dir": "lektionen/" + first, "name": "_tmp_check", "code": "print('hi')"})
check("Speichern in Lektion", st == 200 and json.loads(b).get("saved") == "_tmp_check.py", str(st))
st, b = req("/file?dir=lektionen/" + first + "&name=_tmp_check.py")
check("Lektionsdatei wieder ladbar", st == 200 and "hi" in json.loads(b)["code"], str(st))
st, b = req("/delete", {"dir": "lektionen/" + first, "name": "_tmp_check"})
check("Lektionsdatei loeschbar", st == 200, str(st))
st, b = req("/file", {"dir": "lektionen/" + first, "name": ".versteckt", "code": "x"})
check("Punkt-Datei abgewiesen", st == 400, str(st))

# ---------- Testreste ----------
for leftover in ("playground/check_tmp.txt",):
    try:
        os.remove(leftover)
    except OSError:
        pass

# ---------- Ergebnis ----------
ok = sum(1 for _, c, _ in results if c)
bad = [r for r in results if not r[1]]
for name, cond, detail in results:
    print(("PASS  " if cond else "FAIL  ") + name + (("   [" + detail + "]") if detail and not cond else ""))
print("")
print("ERGEBNIS: " + str(ok) + "/" + str(len(results)) + " bestanden")
if bad:
    print("FEHLGESCHLAGEN:")
    for name, _, detail in bad:
        print(" - " + name + " " + detail)
sys.exit(1 if bad else 0)
