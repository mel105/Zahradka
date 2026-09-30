"""Spúšťač Záhradky: spustí server na pozadí (bez terminálu) a otvorí prehliadač.
Ak už beží rovnaká verzia, len otvorí prehliadač. Ak beží stará verzia, vypne ju a spustí novú.
Voliteľne port ako prvý parameter: zahradka.pyw 8770
"""
import json
import os
import subprocess
import sys
import time
import urllib.request
import webbrowser

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
from core import VERZIA  # noqa: E402

PORT = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 8768
URL = f"http://127.0.0.1:{PORT}/"
LOG = os.path.join(BASE, "data", "server.log")


def bezi():
    try:
        with urllib.request.urlopen(URL + "api/verzia", timeout=1.5) as r:
            return json.loads(r.read().decode())
    except Exception:
        return None


def vypni():
    try:
        req = urllib.request.Request(URL + "api/vypnut", data=b"{}", headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=3).read()
    except Exception:
        pass
    for _ in range(30):
        if not bezi():
            return
        time.sleep(0.2)


def spusti():
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    if os.path.exists(LOG) and os.path.getsize(LOG) > 1_000_000:
        os.replace(LOG, LOG + ".old")
    log = open(LOG, "a", encoding="utf-8")
    log.write(f"\n==== {time.strftime('%Y-%m-%d %H:%M:%S')} štart verzie {VERZIA} ====\n")
    log.flush()
    cmd = [sys.executable, os.path.join(BASE, "server.py"), "--no-browser", "--port", str(PORT)]
    kw = dict(cwd=BASE, stdout=log, stderr=log, stdin=subprocess.DEVNULL)
    if os.name == "nt":
        kw["creationflags"] = 0x08000000 | 0x00000200  # CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP
    else:
        kw["start_new_session"] = True
    subprocess.Popen(cmd, **kw)


def koniec_logu(n=25):
    try:
        with open(LOG, encoding="utf-8", errors="replace") as f:
            return "".join(f.readlines()[-n:])
    except OSError:
        return "(log neexistuje)"


def chyba(text):
    try:
        import tkinter
        from tkinter import messagebox
        r = tkinter.Tk()
        r.withdraw()
        messagebox.showerror("Záhradka", text)
        r.destroy()
    except Exception:
        print(text)


def main():
    v = bezi()
    if v and v.get("app") == "zahradka" and v.get("verzia") == VERZIA:
        webbrowser.open(URL)
        return
    if v and v.get("app") == "zahradka":
        vypni()
    spusti()
    for _ in range(75):
        time.sleep(0.2)
        if bezi():
            webbrowser.open(URL)
            return
    chyba(f"Server sa nespustil.\n\nKoniec súboru {LOG}:\n\n{koniec_logu()}")


if __name__ == "__main__":
    main()
