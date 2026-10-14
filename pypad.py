#!/usr/bin/env python3
"""
PyPad - ein kleiner Python-Editor im Browser, der komplett offline laeuft.

Start:  PyPad.command doppelklicken   (oder: python3 pypad.py)
Alles ist lokal: Server nur auf 127.0.0.1, Ausfuehrung mit dem installierten Python.
Optionen (Umgebungsvariablen): PYPAD_PORT, PYPAD_TIMEOUT, PYPAD_MAX_RUNTIME, PYPAD_NO_BROWSER=1
"""
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


class Run:
    """Ein laufendes Programm: Ausgabe wird gestreamt, Eingaben kommen live rein."""

    def __init__(self, code, prefill):
        self.id = uuid.uuid4().hex[:12]
        self.chunks = []
        self.lock = threading.Lock()
        self.done = False
        self.returncode = None
        self.started = time.time()
        self.killed_by_timeout = False
        self.tmp = tempfile.TemporaryDirectory(prefix="pypad-")
        script = Path(self.tmp.name) / "main.py"
        script.write_text(code, encoding="utf-8")
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["PYTHONUNBUFFERED"] = "1"
        env["MPLBACKEND"] = "Agg"
        self.proc = subprocess.Popen(
            [PYTHON, "-u", str(script)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(WORKDIR),
            env=env,
            start_new_session=True,
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
        try:
            os.killpg(os.getpgid(self.proc.pid), signal.SIGKILL)
        except Exception:
            try:
                self.proc.kill()
            except Exception:
                pass

    def snapshot(self, start):
        with self.lock:
            chunks = self.chunks[start:]
            total = len(self.chunks)
        return {
            "chunks": chunks,
            "next": total,
            "done": self.done,
            "returncode": self.returncode,
            "ms": int((time.time() - self.started) * 1000),
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
            self._json({"id": run.id})
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
