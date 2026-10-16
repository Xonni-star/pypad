#!/usr/bin/env python3
"""
PyPad Server - abgesicherte Online-Variante mit Benutzerverwaltung.

Laeuft auf dem Server, erreichbar ueber HTTPS. Jeder Nutzer hat seinen eigenen
Workspace; ausgefuehrter Code laeuft abgesichert (eigener User, kein Netz, Limits).
"""
import hashlib
import hmac
import json
import os
import re
import secrets
import shutil
import signal
import ssl
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    import pypad   # bewaehrte Bausteine (lint_code, explain_error, complete_words, RUNNER_SOURCE)
except Exception:
    pypad = None

DATA = Path(os.environ.get("PYPAD_DATA", "/srv/pypad"))
USERS_FILE = DATA / "users.json"
SESSIONS_FILE = DATA / "sessions.json"
RUN_DIR = DATA / "run"
WRAPPER = "/usr/local/bin/pypad-run"
HOST = os.environ.get("PYPAD_HOST", "0.0.0.0")
PORT = int(os.environ.get("PYPAD_PORT", "8443"))
CERT = os.environ.get("PYPAD_CERT", str(DATA / "elitebook.taila52ac2.ts.net.crt"))
KEY = os.environ.get("PYPAD_KEY", str(DATA / "elitebook.taila52ac2.ts.net.key"))
STATIC = Path(__file__).resolve().parent
TIMEOUT = int(os.environ.get("PYPAD_TIMEOUT", "20"))

USERS_LOCK = threading.Lock()
SESSIONS = {}
SESSIONS_LOCK = threading.Lock()
FAILED = {}
FAILED_LOCK = threading.Lock()
SESSION_TTL = 60 * 60 * 24 * 7   # 7 Tage


def log(msg):
    print(time.strftime("%Y-%m-%d %H:%M:%S  ") + msg, flush=True)


# ---------- Benutzer ----------
def users_load():
    try:
        d = json.loads(USERS_FILE.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def users_save(users):
    tmp = USERS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(users, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, USERS_FILE)
    os.chmod(USERS_FILE, 0o600)


def hash_pw(pw, salt=None):
    salt = salt or secrets.token_hex(16)
    h = hashlib.scrypt(pw.encode("utf-8"), salt=salt.encode("utf-8"), n=2 ** 14, r=8, p=1, dklen=64).hex()
    return salt, h


def verify_pw(pw, salt, h):
    try:
        return hmac.compare_digest(hash_pw(pw, salt)[1], h)
    except Exception:
        return False


def user_dir(name):
    return DATA / "users" / name


def workspace(name):
    d = user_dir(name) / "workspace"
    d.mkdir(parents=True, exist_ok=True)
    return d


def safe_path(name, pfad):
    """Pfad innerhalb des Workspace des Nutzers aufloesen - sonst None."""
    ws = workspace(name).resolve()
    roh = (pfad or "").strip() or "."
    p = (ws / roh).resolve()
    try:
        p.relative_to(ws)
        return p
    except ValueError:
        return None


# ---------- GitHub-Token (pro Benutzer) ----------
def token_datei(name):
    d = user_dir(name)
    d.mkdir(parents=True, exist_ok=True)
    return d / "github.json"


def token_status(name):
    try:
        d = json.loads(token_datei(name).read_text(encoding="utf-8"))
        return {"gesetzt": bool(d.get("token")), "login": d.get("login") or ""}
    except Exception:
        return {"gesetzt": False, "login": ""}


def token_lesen(name):
    try:
        return json.loads(token_datei(name).read_text(encoding="utf-8")).get("token") or ""
    except Exception:
        return ""


def token_speichern(name, token, login):
    p = token_datei(name)
    p.write_text(json.dumps({"token": token, "login": login}), encoding="utf-8")
    os.chmod(p, 0o600)


def token_pruefen(token):
    """Token bei GitHub pruefen -> Loginname, oder None wenn abgelehnt."""
    try:
        import urllib.request
        req = urllib.request.Request("https://api.github.com/user",
                                     headers={"Authorization": "token " + token,
                                              "User-Agent": "PyPad",
                                              "Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode()).get("login") or ""
    except Exception:
        return None


# ---------- Sitzungen ----------
def sessions_load():
    global SESSIONS
    try:
        SESSIONS = json.loads(SESSIONS_FILE.read_text(encoding="utf-8"))
    except Exception:
        SESSIONS = {}


def sessions_save():
    try:
        tmp = SESSIONS_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(SESSIONS), encoding="utf-8")
        os.replace(tmp, SESSIONS_FILE)
        os.chmod(SESSIONS_FILE, 0o600)
    except Exception:
        pass


def neue_sitzung(user):
    token = secrets.token_urlsafe(32)
    with SESSIONS_LOCK:
        SESSIONS[token] = {"user": user, "bis": time.time() + SESSION_TTL}
        sessions_save()
    return token


def sitzung_pruefen(token):
    with SESSIONS_LOCK:
        s = SESSIONS.get(token)
        if not s:
            return None
        if s.get("bis", 0) < time.time():
            SESSIONS.pop(token, None)
            sessions_save()
            return None
        return s["user"]


def sitzung_loeschen(token):
    with SESSIONS_LOCK:
        SESSIONS.pop(token, None)
        sessions_save()


def login_limit(ip):
    with FAILED_LOCK:
        jetzt = time.time()
        zaehler, erste = FAILED.get(ip, (0, jetzt))
        if jetzt - erste > 300:
            zaehler, erste = 0, jetzt
        FAILED[ip] = (zaehler, erste)
        return zaehler >= 10


def login_fehlschlag(ip):
    with FAILED_LOCK:
        zaehler, erste = FAILED.get(ip, (0, time.time()))
        if time.time() - erste > 300:
            zaehler, erste = 0, time.time()
        FAILED[ip] = (zaehler + 1, erste)


def login_erfolg(ip):
    with FAILED_LOCK:
        FAILED.pop(ip, None)


# ---------- Code ausfuehren (Sandbox) ----------
def run_code(user, code, stdin_text):
    lauf = RUN_DIR / (user + "-" + secrets.token_hex(4))
    lauf.mkdir(parents=True, exist_ok=True)
    os.chmod(lauf, 0o777)
    script = lauf / "main.py"
    script.write_text(code, encoding="utf-8")
    os.chmod(script, 0o644)
    vars_pfad = lauf / "vars.json"
    runner = lauf / "_runner.py"
    if pypad is not None:
        runner.write_text(pypad.RUNNER_SOURCE, encoding="utf-8")
        os.chmod(runner, 0o644)
        befehl = ["sudo", "-n", WRAPPER, str(runner), str(script), str(vars_pfad)]
    else:
        befehl = ["sudo", "-n", WRAPPER, str(script)]
    start = time.time()
    try:
        fertig = subprocess.run(befehl, input=(stdin_text or "").encode("utf-8"),
                                capture_output=True, timeout=TIMEOUT + 10)
        out = fertig.stdout.decode("utf-8", "replace")
        err = fertig.stderr.decode("utf-8", "replace")
        rc = fertig.returncode
    except subprocess.TimeoutExpired:
        out, err, rc = "", "\n[PyPad] Zeitlimit erreicht - Programm beendet.\n", -1
    except Exception as exc:
        out, err, rc = "", str(exc), -1

    variablen = None
    try:
        if vars_pfad.exists():
            variablen = json.loads(vars_pfad.read_text(encoding="utf-8"))
    except Exception:
        variablen = None

    erklaerung = None
    warnungen = None
    if pypad is not None:
        try:
            erklaerung = pypad.explain_error(err, code)
        except Exception:
            erklaerung = None
        try:
            warnungen = pypad.lint_code(code)
        except Exception:
            warnungen = None

    shutil.rmtree(lauf, ignore_errors=True)
    return {"stdout": out, "stderr": err, "returncode": rc, "ms": int((time.time() - start) * 1000),
            "vars": variablen, "explanation": erklaerung, "warnings": warnungen}


def complete_words(code, prefix):
    if pypad is not None:
        try:
            return pypad.complete_words(code, prefix)
        except Exception:
            pass
    import builtins
    import keyword
    low = (prefix or "").lower()
    basis = sorted(set(keyword.kwlist) | set(n for n in dir(builtins) if not n.startswith("_")))
    return [w for w in basis if w.lower().startswith(low)]


LAEUFE = {}
LAEUFE_LOCK = threading.Lock()
SANDBOX = ["sudo", "-n", WRAPPER]
WRAPPER_NET = os.environ.get("PYPAD_WRAPPER_NET", "/usr/local/bin/pypad-run-net")
SANDBOX_NET = ["sudo", "-n", WRAPPER_NET]


def netz_verfuegbar():
    """Gibt es den Sandkasten MIT Netz (Wrapper + Firewall eingerichtet)?"""
    try:
        return os.path.isfile(WRAPPER_NET) and os.access(WRAPPER_NET, os.X_OK)
    except OSError:
        return False


def neuer_lauf(code, stdin_text, netz=False):
    basis = SANDBOX_NET if (netz and netz_verfuegbar()) else SANDBOX
    lauf = pypad.Run(code, stdin_text, basis=basis, tmp_parent=RUN_DIR, cwd=RUN_DIR)
    with LAEUFE_LOCK:
        LAEUFE[lauf.id] = lauf
        if len(LAEUFE) > 40:
            for k in list(LAEUFE)[:-20]:
                alt = LAEUFE.pop(k, None)
                if alt is not None:
                    try:
                        alt.tmp.cleanup()
                    except Exception:
                        pass
    return lauf


def neuer_debug(code):
    lauf = pypad.DebugRun(code, basis=SANDBOX, tmp_parent=RUN_DIR, cwd=RUN_DIR)
    with LAEUFE_LOCK:
        LAEUFE[lauf.id] = lauf
    return lauf


class Handler(BaseHTTPRequestHandler):
    server_version = "PyPadServer/1.0"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        pass

    def _senden(self, status, body, ctype="application/json; charset=utf-8", cookie=None):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(status)
        if cookie is not None:
            self.send_header("Set-Cookie", cookie)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "close")
        self.close_connection = True
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, status=200, cookie=None):
        self._senden(status, json.dumps(obj, ensure_ascii=False), cookie=cookie)

    def _body(self):
        try:
            laenge = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            return {}
        if laenge <= 0:
            return {}
        try:
            return json.loads(self.rfile.read(laenge).decode("utf-8"))
        except Exception:
            return {}

    def _cookie(self):
        c = self.headers.get("Cookie") or ""
        for teil in c.split(";"):
            k, _, v = teil.strip().partition("=")
            if k == "session":
                return v
        return None

    def _user(self):
        token = self._cookie()
        return sitzung_pruefen(token) if token else None

    def _cookie_string(self, token):
        return "session=" + token + "; HttpOnly; Secure; SameSite=Strict; Path=/"

    def _ip(self):
        return self.client_address[0]

    def do_GET(self):
        url = urlparse(self.path)
        pfad = url.path

        if pfad in ("/", "/online.html"):
            datei = STATIC / "online.html"
            self._senden(200, datei.read_text(encoding="utf-8") if datei.exists() else "online.html fehlt",
                         "text/html; charset=utf-8")
            return
        if pfad.startswith("/vendor/"):
            name = pfad[len("/vendor/"):]
            if not re.match(r"^[A-Za-z0-9_.-]{1,64}$", name):
                self._senden(404, "nf", "text/plain")
                return
            datei = (STATIC / "vendor" / name)
            if not datei.is_file():
                self._senden(404, "nf", "text/plain")
                return
            ctype = "application/javascript; charset=utf-8" if name.endswith(".js") else "text/plain"
            self._senden(200, datei.read_bytes(), ctype)
            return

        user = self._user()
        if not user:
            self._json({"error": "nicht angemeldet"}, 401)
            return

        if pfad == "/api/whoami":
            nutzer = users_load().get(user, {})
            self._json({"user": user, "admin": bool(nutzer.get("admin"))})
            return
        if pfad == "/api/info":
            self._json({"user": user, "version": sys.version.split()[0], "workspace": str(workspace(user)),
                        "netz": netz_verfuegbar()})
            return
        if pfad == "/api/users":
            if not users_load().get(user, {}).get("admin"):
                self._json({"error": "kein Admin"}, 403)
                return
            self._json({"users": [{"name": n, "admin": bool(v.get("admin"))}
                                  for n, v in users_load().items()]})
            return
        if pfad == "/api/git-token":
            self._json(token_status(user))
            return
        if pfad == "/api/git":
            if pypad is None:
                self._json({"error": "Git nicht verfuegbar"}, 500)
                return
            ziel = safe_path(user, (parse_qs(url.query).get("pfad") or [""])[0])
            if ziel is None:
                self._json({"error": "Pfad nicht erlaubt"}, 400)
                return
            ws = str(ziel)
            self._json({"pfad": ws,
                        "branch": pypad.git_ausfuehren(ws, "rev-parse", "--abbrev-ref", "HEAD"),
                        "status": pypad.git_ausfuehren(ws, "status", "--short"),
                        "log": pypad.git_ausfuehren(ws, "log", "--oneline", "-6")})
            return
        if pfad == "/api/git-diff":
            if pypad is None:
                self._json({"error": "Git nicht verfuegbar"}, 500)
                return
            q = parse_qs(url.query)
            datei = (q.get("datei") or [""])[0]
            ziel = safe_path(user, (q.get("pfad") or [""])[0])
            if ziel is None:
                self._json({"error": "Pfad nicht erlaubt"}, 400)
                return
            ws = str(ziel)
            a = pypad.git_ausfuehren(ws, "diff", "--", datei)
            b = pypad.git_ausfuehren(ws, "diff", "--cached", "--", datei)
            diff = (a.get("ausgabe", "") + b.get("ausgabe", "")).strip()
            self._json({"diff": diff or "(keine Aenderungen an dieser Datei)"})
            return
        if pfad == "/api/files":
            q = parse_qs(url.query)
            ziel = safe_path(user, (q.get("pfad") or [""])[0])
            if ziel is None:
                self._json({"error": "Pfad nicht erlaubt"}, 400)
                return
            if not ziel.is_dir():
                self._json({"error": "kein Ordner"}, 400)
                return
            endungen = {".py", ".js", ".mjs", ".html", ".htm", ".css", ".json", ".md", ".markdown",
                        ".txt", ".sh", ".yml", ".yaml", ".toml", ".ini", ".cfg", ".conf"}
            dateien = sorted(p.name for p in ziel.iterdir() if p.is_file() and p.suffix.lower() in endungen)
            ordner = sorted(p.name for p in ziel.iterdir() if p.is_dir() and not p.name.startswith("."))
            self._json({"pfad": str(ziel), "dateien": dateien, "ordner": ordner})
            return
        if pfad == "/api/datei":
            q = parse_qs(url.query)
            ziel = safe_path(user, (q.get("pfad") or [""])[0])
            if ziel is None or not ziel.is_file():
                self._json({"error": "Datei nicht gefunden"}, 404)
                return
            self._json({"pfad": str(ziel), "code": ziel.read_text(encoding="utf-8", errors="replace")})
            return

        self._senden(404, "nf", "text/plain")

    def do_POST(self):
        url = urlparse(self.path)
        pfad = url.path
        daten = self._body()

        if pfad == "/api/login":
            ip = self._ip()
            if login_limit(ip):
                self._json({"error": "zu viele Fehlversuche - bitte kurz warten"}, 429)
                return
            name = (daten.get("user") or "").strip()
            pw = daten.get("pass") or ""
            nutzer = users_load().get(name)
            if not nutzer or not verify_pw(pw, nutzer.get("salt", ""), nutzer.get("hash", "")):
                login_fehlschlag(ip)
                self._json({"error": "Benutzer oder Passwort falsch"}, 401)
                return
            login_erfolg(ip)
            token = neue_sitzung(name)
            self._json({"ok": True, "user": name, "admin": bool(nutzer.get("admin"))},
                       cookie=self._cookie_string(token))
            return

        if pfad == "/api/logout":
            token = self._cookie()
            if token:
                sitzung_loeschen(token)
            self._json({"ok": True}, cookie=self._cookie_string(""))
            return

        user = self._user()
        if not user:
            self._json({"error": "nicht angemeldet"}, 401)
            return

        if pfad == "/api/user":
            if not users_load().get(user, {}).get("admin"):
                self._json({"error": "kein Admin"}, 403)
                return
            name = (daten.get("name") or "").strip()
            pw = daten.get("pass") or ""
            if not re.match(r"^[A-Za-z0-9_.-]{1,40}$", name):
                self._json({"error": "ungueltiger Benutzername"}, 400)
                return
            if len(pw) < 8:
                self._json({"error": "Passwort muss mindestens 8 Zeichen haben"}, 400)
                return
            with USERS_LOCK:
                users = users_load()
                ist_neu = name not in users
                salt, h = hash_pw(pw)
                users[name] = {"salt": salt, "hash": h,
                               "admin": bool(daten.get("admin")), "angelegt": time.strftime("%Y-%m-%d")}
                users_save(users)
                workspace(name)
            log("Benutzer angelegt/aktualisiert: " + name + (" (neu)" if ist_neu else ""))
            self._json({"ok": True, "name": name, "neu": ist_neu})
            return

        if pfad == "/api/user-delete":
            if not users_load().get(user, {}).get("admin"):
                self._json({"error": "kein Admin"}, 403)
                return
            name = (daten.get("name") or "").strip()
            if name == user:
                self._json({"error": "eigenen Account nicht loeschen"}, 400)
                return
            with USERS_LOCK:
                users = users_load()
                if name not in users:
                    self._json({"error": "unbekannt"}, 404)
                    return
                del users[name]
                users_save(users)
            self._json({"ok": True})
            return

        if pfad == "/api/datei":
            ziel = safe_path(user, daten.get("pfad"))
            if ziel is None:
                self._json({"error": "Pfad nicht erlaubt"}, 400)
                return
            code = daten.get("code")
            if code is None:
                self._json({"error": "kein Code"}, 400)
                return
            ziel.parent.mkdir(parents=True, exist_ok=True)
            ziel.write_text(code, encoding="utf-8")
            self._json({"gespeichert": str(ziel)})
            return

        if pfad in ("/api/run/start", "/api/debug/start"):
            code = daten.get("code") or ""
            if not code.strip():
                self._json({"error": "leerer Code"}, 400)
                return
            if pypad is None:
                self._json({"error": "Runner nicht verfuegbar"}, 500)
                return
            if pfad == "/api/run/start":
                if daten.get("netz") and not netz_verfuegbar():
                    self._json({"error": "Netzwerk-Modus ist auf diesem Server nicht eingerichtet."}, 400)
                    return
                lauf = neuer_lauf(code, daten.get("stdin") or "", netz=bool(daten.get("netz")))
            else:
                lauf = neuer_debug(code)
            self._json({"id": lauf.id})
            return

        if pfad in ("/api/run/poll", "/api/debug/poll"):
            lauf = LAEUFE.get((daten.get("id") or "").strip())
            if not lauf:
                self._json({"error": "unbekannte Lauf-ID"}, 404)
                return
            try:
                ab = int(daten.get("from") or 0)
            except (TypeError, ValueError):
                ab = 0
            if pfad == "/api/run/poll":
                self._json(lauf.snapshot(max(0, ab)))
            else:
                self._json(lauf.zustand(max(0, ab)))
            return

        if pfad in ("/api/run/input", "/api/debug/befehl"):
            lauf = LAEUFE.get((daten.get("id") or "").strip())
            if not lauf:
                self._json({"error": "unbekannte Lauf-ID"}, 404)
                return
            if pfad == "/api/run/input":
                self._json({"ok": lauf.write(str(daten.get("text") or "") + "\n")})
            else:
                befehl = str(daten.get("befehl") or "")
                if befehl == "stop":
                    lauf.kill()
                    self._json({"ok": True, "gestoppt": True})
                else:
                    self._json({"ok": lauf.befehl(befehl)})
            return

        if pfad == "/api/run/stop":
            lauf = LAEUFE.get((daten.get("id") or "").strip())
            if not lauf:
                self._json({"error": "unbekannte Lauf-ID"}, 404)
                return
            lauf.kill()
            self._json({"gestoppt": True})
            return

        if pfad == "/api/git-token":
            tok = str(daten.get("token") or "").strip()
            p = token_datei(user)
            if not tok:
                try:
                    p.unlink()
                except OSError:
                    pass
                self._json({"ok": True, "gesetzt": False, "login": ""})
                return
            login = token_pruefen(tok)
            if login is None:
                self._json({"error": "GitHub hat diesen Token nicht akzeptiert (abgelaufen oder falsch?)."})
                return
            token_speichern(user, tok, login)
            self._json({"ok": True, "gesetzt": True, "login": login})
            return

        if pfad == "/api/loeschen":
            ziel = safe_path(user, daten.get("pfad"))
            if ziel is None:
                self._json({"error": "Pfad nicht erlaubt"}, 400)
                return
            try:
                if ziel.resolve() == workspace(user).resolve():
                    self._json({"error": "Der Workspace selbst bleibt bestehen."}, 400)
                    return
                if not ziel.exists():
                    self._json({"error": "gibt es nicht mehr"}, 404)
                    return
                if ziel.is_dir():
                    shutil.rmtree(ziel)
                else:
                    ziel.unlink()
            except Exception as exc:
                self._json({"error": str(exc)}, 500)
                return
            self._json({"ok": True, "geloescht": str(ziel)})
            return

        if pfad == "/api/git-laden":
            if pypad is None:
                self._json({"error": "Git nicht verfuegbar"}, 500)
                return
            ws = str(workspace(user))
            self._json(pypad.github_laden(ws, daten.get("url"), daten.get("branch"),
                                          (daten.get("token") or "").strip() or token_lesen(user)))
            return

        if pfad in ("/api/git-commit", "/api/git-push", "/api/git-pull"):
            if pypad is None:
                self._json({"error": "Git nicht verfuegbar"}, 500)
                return
            ziel = safe_path(user, daten.get("pfad"))
            if ziel is None:
                self._json({"error": "Pfad nicht erlaubt"}, 400)
                return
            ws = str(ziel)
            tok = token_lesen(user)
            if pfad == "/api/git-commit":
                meldung = (daten.get("message") or "").strip() or "Update"
                pypad.git_ausfuehren(ws, "add", "-A")
                c = pypad.git_ausfuehren(ws, "-c", "user.name=" + user, "-c", "user.email=" + user + "@pypad.local",
                                         "commit", "-m", meldung)
                self._json({"ok": c.get("rc") == 0, "ausgabe": c.get("ausgabe", ""), "fehler": c.get("fehler", "")})
            elif pfad == "/api/git-push":
                self._json(pypad.git_ausfuehren(ws, "push", token=tok))
            else:
                self._json(pypad.git_ausfuehren(ws, "pull", token=tok))
            return

        if pfad == "/api/run":
            code = daten.get("code") or ""
            if not code.strip():
                self._json({"error": "leerer Code"}, 400)
                return
            self._json(run_code(user, code, daten.get("stdin") or ""))
            return

        if pfad == "/api/check":
            code = daten.get("code") or ""
            warnungen = []
            if pypad is not None:
                try:
                    warnungen = pypad.lint_code(code)
                except Exception:
                    warnungen = []
            self._json({"warnings": warnungen})
            return

        if pfad == "/api/complete":
            self._json({"words": complete_words(daten.get("code") or "", daten.get("prefix") or "")})
            return

        self._senden(404, "nf", "text/plain")


def main():
    DATA.mkdir(parents=True, exist_ok=True)
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    os.chmod(RUN_DIR, 0o777)
    if not USERS_FILE.exists():
        users_save({})
    sessions_load()

    # Erster Admin, falls noch keiner da ist
    users = users_load()
    if not users:
        admin_pw = os.environ.get("PYPAD_ADMIN_PW") or secrets.token_urlsafe(12)
        salt, h = hash_pw(admin_pw)
        users["admin"] = {"salt": salt, "hash": h, "admin": True, "angelegt": time.strftime("%Y-%m-%d")}
        users_save(users)
        log("Erster Admin angelegt: 'admin'  (Passwort gesetzt)")

    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(CERT, KEY)
    httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
    log("PyPad-Server lauscht auf https://" + HOST + ":" + str(PORT) + "/")
    log("Zertifikat: " + CERT)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        log("beendet")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
