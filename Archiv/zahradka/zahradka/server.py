"""Záhradka – webový server (len štandardná knižnica Pythonu)."""
import argparse
import datetime as dt
import json
import mimetypes
import os
import ssl
import sys
import threading
import time
import traceback
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import core
import navody as N
import plodiny as P

STATIC = os.path.join(core.BASE, "static")
DB = None
CFG = {"token": None, "vyzaduj_token": False}
HTTPD = None


class Chyba(Exception):
    pass


def json_body(h):
    n = int(h.headers.get("Content-Length") or 0)
    if not n:
        return {}
    return json.loads(h.rfile.read(n).decode("utf-8"))


def qs(h):
    return {k: v[0] for k, v in urllib.parse.parse_qs(urllib.parse.urlparse(h.path).query).items()}


# ---------------------------------------------------------------- API
def api_init(h, q):
    return dict(verzia=core.VERZIA, nastavenia=DB.settings_public(), plodiny=P.zoznam(), zahony=DB.zahony(),
                sposoby=P.SPOSOBY, stavy=P.STAVY, naroky=P.NAROKY, pody=core.PODY,
                typy_dennik=core.TYPY_DENNIK, typy_zahonov=core.TYPY_ZAHONOV,
                navody=[dict(id=n["id"], nazov=n["nazov"]) for n in N.NAVODY], dnes=core.d2s(core.today()))


def api_nastenka(h, q):
    return DB.nastenka(core.s2d(q.get("datum")) or core.today())


def api_pocasie(h, q):
    return DB.pocasie(force=q.get("refresh") == "1")


def api_plan(h, q):
    rok = int(q.get("rok") or core.today().year)
    vys = DB.vysadby_rok(rok)
    return dict(zahony=DB.zahony_planu(rok), vsetky=DB.zahony(), vysadby=vys, rok=rok,
                zamknute=DB.je_zamknuty(rok), uzamknute=DB.uzamknute())


def api_zahon_detail(h, q):
    zid = int(q["id"])
    rok = int(q.get("rok") or core.today().year)
    return dict(historia=DB.historia_zahona(zid), navrh=DB.navrh_striedania(zid, rok + 1),
                fotky=DB.fotky(zahon_id=zid), dennik=DB.dennik(zahon_id=zid, limit=30))


def api_vysadby(h, q):
    rok = int(q.get("rok") or core.today().year)
    return dict(rok=rok, vysadby=DB.vysadby_rok(rok),
                roky=sorted({r["rok"] for r in DB.q("SELECT DISTINCT rok FROM vysadby")} | {core.today().year}))


def api_striedanie(h, q):
    return DB.kontrola_striedania(q.get("zahon_id"), q.get("plodina"), int(q.get("rok") or core.today().year),
                                  q.get("id"))


def api_dennik(h, q):
    rok = q.get("rok") or None
    return dict(dennik=DB.dennik(rok=rok, zahon_id=q.get("zahon_id"), plodina=q.get("plodina")),
                zber=DB.zber_suhrn(rok or core.today().year),
                roky=sorted({r["r"] for r in DB.q("SELECT DISTINCT substr(datum,1,4) r FROM dennik")} | {str(core.today().year)}, reverse=True))


def api_fotky(h, q):
    return DB.fotky(zahon_id=q.get("zahon_id"), plodina=q.get("plodina"))


def api_plodina(h, q):
    d = P.detail(q.get("id"))
    if not d:
        raise Chyba("Neznáma plodina")
    return d


def api_navod(h, q):
    for n in N.NAVODY:
        if n["id"] == q.get("id"):
            return n
    raise Chyba("Návod neexistuje")


def api_geokod(h, q):
    try:
        return core.geokod(q.get("q", ""))
    except Exception as e:
        raise Chyba(f"Vyhľadávanie miesta zlyhalo: {e}")


def api_prompt(h, q):
    return dict(prompt=DB.prompt_diagnostiky(q["id"], q.get("poznamka", "")))


GET = {
    "/api/verzia": lambda h, q: dict(verzia=core.VERZIA, app="zahradka"),
    "/api/init": api_init,
    "/api/nastenka": api_nastenka,
    "/api/pocasie": api_pocasie,
    "/api/plan": api_plan,
    "/api/zahon": api_zahon_detail,
    "/api/vysadby": api_vysadby,
    "/api/striedanie": api_striedanie,
    "/api/dennik": api_dennik,
    "/api/fotky": api_fotky,
    "/api/plodina": api_plodina,
    "/api/navod": api_navod,
    "/api/geokod": api_geokod,
    "/api/prompt": api_prompt,
    "/api/striedanie_plan": lambda h, q: DB.striedanie_plan(q.get("od"), q.get("do")),
}


def p_nastavenia(h, b):
    if "api_key" in b and ("…" in b["api_key"]):
        b.pop("api_key")  # zamaskovaný kľúč sa neprepisuje
    DB.set_settings(b)
    return DB.settings_public()


def p_zahon(h, b):
    return dict(id=DB.save_zahon(b))



def p_zahon_zmazat(h, b):
    DB.del_zahon(b["id"], b.get("rok"))
    return {}


def p_vysadba(h, b):
    vid = DB.save_vysadba(b)
    return dict(id=vid, varovania=DB.kontrola_striedania(b.get("zahon_id"), b.get("plodina"),
                                                          int(b.get("rok") or core.today().year), vid))


def p_vysadba_zmazat(h, b):
    DB.del_vysadba(b["id"])
    return {}


def p_hotovo(h, b):
    DB.oznac(b["key"], bool(b.get("hotovo")), text=b.get("text", ""), typ=b.get("typ", ""),
             pid=b.get("pid"), nastav=b.get("nastav"), zapisat=b.get("zapisat", True),
             zahon_nazov=b.get("zahon", ""))
    return {}


def p_dennik(h, b):
    return dict(id=DB.save_dennik(b))


def p_dennik_zmazat(h, b):
    DB.del_dennik(b["id"])
    return {}


def p_fotka(h, b):
    return dict(id=DB.uloz_fotku(b))


def p_fotka_upravit(h, b):
    DB.uprav_fotku(b)
    return {}


def p_fotka_zmazat(h, b):
    DB.del_fotku(b["id"])
    return {}


def p_diagnostika(h, b):
    return DB.diagnostika_api(b["id"], b.get("poznamka", ""))


def p_vypnut(h, b):
    threading.Thread(target=lambda: (time.sleep(0.3), HTTPD.shutdown()), daemon=True).start()
    return dict(ok=True)


POST = {
    "/api/nastavenia": p_nastavenia,
    "/api/zahon": p_zahon,
    "/api/zahon/zmazat": p_zahon_zmazat,
    "/api/vysadba": p_vysadba,
    "/api/vysadba/zmazat": p_vysadba_zmazat,
    "/api/hotovo": p_hotovo,
    "/api/dennik": p_dennik,
    "/api/dennik/zmazat": p_dennik_zmazat,
    "/api/fotka": p_fotka,
    "/api/fotka/upravit": p_fotka_upravit,
    "/api/fotka/zmazat": p_fotka_zmazat,
    "/api/diagnostika": p_diagnostika,
    "/api/vypnut": p_vypnut,
    "/api/zamknut": lambda h, b: (DB.zamkni(b["rok"], bool(b.get("zamknut", True))), {})[1],
    "/api/striedanie": lambda h, b: DB.uloz_striedanie(b),
}


# ---------------------------------------------------------------- HTTP
class H(BaseHTTPRequestHandler):
    server_version = "Zahradka/" + core.VERZIA

    def log_message(self, fmt, *args):
        if args and str(args[1]).startswith(("4", "5")) and str(args[1]) != "404":
            sys.stderr.write("%s %s\n" % (dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), fmt % args))

    def _send(self, code, body, ctype="application/json; charset=utf-8", extra=None):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False, default=str).encode("utf-8")
        elif isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _auth(self):
        if not CFG["vyzaduj_token"] or self.client_address[0] in ("127.0.0.1", "::1"):
            return True
        tok = CFG["token"]
        cookie = self.headers.get("Cookie", "")
        if f"zahradka_token={tok}" in cookie:
            return True
        q = qs(self)
        if q.get("token") == tok:
            path = urllib.parse.urlparse(self.path).path
            self._send(302, b"", "text/plain", {
                "Location": path,
                "Set-Cookie": f"zahradka_token={tok}; Max-Age=31536000; Path=/; HttpOnly; SameSite=Strict"
                              + ("; Secure" if CFG.get("https") else "")})
            return False
        self._send(403, "Prístup zamietnutý – otvor adresu raz s ?token=…", "text/plain; charset=utf-8")
        return False

    def do_GET(self):
        if not self._auth():
            return
        path = urllib.parse.urlparse(self.path).path
        try:
            if path in GET:
                return self._send(200, GET[path](self, qs(self)))
            if path == "/api/export/dennik.csv":
                _, content = DB.export_dennik()
                return self._send(200, "\ufeff" + content, "text/csv; charset=utf-8",
                                  {"Content-Disposition": f'attachment; filename="dennik-{core.d2s(core.today())}.csv"'})
            if path.startswith("/fotky/"):
                f = DB.fotka_cesta(urllib.parse.unquote(path[len("/fotky/"):]))
                if not f:
                    return self._send(404, "nenájdené", "text/plain")
                with open(f, "rb") as fh:
                    return self._send(200, fh.read(), mimetypes.guess_type(f)[0] or "image/jpeg",
                                      {"Cache-Control": "max-age=86400"})
            rel = "index.html" if path in ("/", "") else path.lstrip("/")
            if rel.startswith("static/"):
                rel = rel[len("static/"):]
            f = os.path.normpath(os.path.join(STATIC, rel))
            if f.startswith(STATIC) and os.path.isfile(f):
                with open(f, "rb") as fh:
                    ctype = mimetypes.guess_type(f)[0] or "application/octet-stream"
                    if ctype.startswith("text/") or ctype.endswith("javascript"):
                        ctype += "; charset=utf-8"
                    return self._send(200, fh.read(), ctype)
            return self._send(404, dict(chyba="Neznáma adresa"))
        except Chyba as e:
            return self._send(400, dict(chyba=str(e)))
        except Exception as e:
            traceback.print_exc()
            return self._send(500, dict(chyba=f"{type(e).__name__}: {e}"))

    def do_POST(self):
        if not self._auth():
            return
        path = urllib.parse.urlparse(self.path).path
        try:
            if path not in POST:
                return self._send(404, dict(chyba="Neznáma adresa"))
            return self._send(200, POST[path](self, json_body(self)))
        except (Chyba, ValueError, KeyError) as e:
            return self._send(400, dict(chyba=str(e)))
        except Exception as e:
            traceback.print_exc()
            return self._send(500, dict(chyba=f"{type(e).__name__}: {e}"))


def zalohovac():
    while True:
        try:
            DB.zaloha()
        except Exception:
            traceback.print_exc()
        time.sleep(3600)


def main():
    global DB, HTTPD
    ap = argparse.ArgumentParser(description="Záhradka")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8768)
    ap.add_argument("--cert")
    ap.add_argument("--key")
    ap.add_argument("--token", help="prístupový token pre iné počítače (inak sa vygeneruje)")
    ap.add_argument("--no-browser", action="store_true")
    ap.add_argument("--db", help="cesta k databáze (test)")
    a = ap.parse_args()

    DB = core.DB(a.db)
    if a.token:
        DB.set_settings({"remote_token": a.token})
    CFG["vyzaduj_token"] = a.host not in ("127.0.0.1", "localhost")
    CFG["token"] = DB.token() if CFG["vyzaduj_token"] else None

    HTTPD = ThreadingHTTPServer((a.host, a.port), H)
    HTTPD.daemon_threads = True
    scheme = "http"
    if a.cert:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(a.cert, a.key)
        HTTPD.socket = ctx.wrap_socket(HTTPD.socket, server_side=True)
        scheme = "https"
        CFG["https"] = True

    threading.Thread(target=zalohovac, daemon=True).start()
    url = f"{scheme}://127.0.0.1:{a.port}/"
    print(f"Záhradka {core.VERZIA} beží: {url}", flush=True)
    if CFG["vyzaduj_token"]:
        print(f"Z iného počítača: {scheme}://<IP>:{a.port}/?token={CFG['token']}", flush=True)
    if not a.no_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        HTTPD.serve_forever()
    except KeyboardInterrupt:
        pass
    print("Záhradka vypnutá.", flush=True)


if __name__ == "__main__":
    main()
