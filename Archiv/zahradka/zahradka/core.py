"""Záhradka – databáza a logika (úlohy, počasie, striedanie, fotky, diagnostika)."""
import base64
import calendar
import datetime as dt
import glob
import json
import os
import secrets
import sqlite3
import ssl
import threading
import urllib.parse
import urllib.request

import plodiny as P

VERZIA = "1.1.0"
BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
FOTKY = os.path.join(DATA, "fotky")
BACKUPS = os.path.join(DATA, "backups")
EXPORT = os.path.join(DATA, "export")

DEFAULTS = {
    "nazov": "Moja záhradka",
    "miesto": "Lysá nad Labem",
    "lat": "50.2015",
    "lon": "14.8330",
    "poda": "piesocnata",
    "sirka": "10",
    "dlzka": "20",
    "juh": "dole",
    "api_key": "",
    "model": "claude-sonnet-5-5",
    "dennik_auto": "1",
    "uzamknute": "[]",      # zoznam uzamknutých rokov (JSON)
    "striedanie": "",       # nastavenie striedania (JSON)
}

PODY = {"piesocnata": "piesočnatá (ľahká)", "hlinita": "hlinitá (stredná)", "ilovita": "ílovitá (ťažká)"}
TYPY_DENNIK = {
    "sejba": "sejba", "vysadba": "výsadba", "hnojenie": "hnojenie", "ochrana": "ochrana / postrek",
    "polievanie": "polievanie", "rez": "rez", "zber": "zber", "praca": "práca",
    "pozorovanie": "pozorovanie", "nakup": "nákup",
}
TYP_ULOHY_DO_DENNIKA = {
    "sejba": "sejba", "vysadba": "vysadba", "hnojenie": "hnojenie", "ochrana": "ochrana",
    "zber": "zber", "rez": "rez", "starostlivost": "praca", "priprava": "praca", "nakup": "nakup",
    "info": "praca",
}
TYPY_ZAHONOV = {"zahon": "záhon", "ker": "ker / strom", "chodnik": "chodník", "kompost": "kompost",
                "chatka": "chatka / kôlňa", "voda": "voda / sud", "trava": "tráva", "ine": "iné"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS zahony(
  id INTEGER PRIMARY KEY, nazov TEXT NOT NULL, typ TEXT DEFAULT 'zahon',
  x REAL DEFAULT 0, y REAL DEFAULT 0, w REAL DEFAULT 1, h REAL DEFAULT 1,
  poznamka TEXT DEFAULT '', aktivny INTEGER DEFAULT 1, od_roku INTEGER, do_roku INTEGER);
CREATE TABLE IF NOT EXISTS vysadby(
  id INTEGER PRIMARY KEY, plodina TEXT NOT NULL, odroda TEXT DEFAULT '', zahon_id INTEGER,
  rok INTEGER NOT NULL, datum TEXT, sposob TEXT DEFAULT 'sadenice', stav TEXT DEFAULT 'plan',
  mnozstvo TEXT DEFAULT '', poznamka TEXT DEFAULT '', koniec TEXT);
CREATE TABLE IF NOT EXISTS dennik(
  id INTEGER PRIMARY KEY, datum TEXT NOT NULL, typ TEXT, zahon_id INTEGER, plodina TEXT,
  text TEXT, mnozstvo REAL, jednotka TEXT, uloha_key TEXT, created TEXT);
CREATE TABLE IF NOT EXISTS fotky(
  id INTEGER PRIMARY KEY, datum TEXT, zahon_id INTEGER, plodina TEXT, subor TEXT,
  popis TEXT DEFAULT '', hodnotenie TEXT DEFAULT '', hodnotenie_zdroj TEXT DEFAULT '',
  hodnotenie_datum TEXT, created TEXT);
CREATE TABLE IF NOT EXISTS hotovo(key TEXT PRIMARY KEY, datum TEXT);
CREATE TABLE IF NOT EXISTS cache(key TEXT PRIMARY KEY, ts TEXT, data TEXT);
CREATE TABLE IF NOT EXISTS plan_snapshot(rok INTEGER PRIMARY KEY, data TEXT, ts TEXT);
CREATE INDEX IF NOT EXISTS ix_vys_rok ON vysadby(rok);
CREATE INDEX IF NOT EXISTS ix_den_datum ON dennik(datum);
"""


def today():
    return dt.date.today()


def d2s(d):
    return d.isoformat() if d else None


def s2d(s):
    try:
        return dt.date.fromisoformat(str(s)[:10])
    except (TypeError, ValueError):
        return None


def mmdd(year, s):
    m, d = (int(x) for x in s.split("-"))
    return dt.date(year, m, min(d, calendar.monthrange(year, m)[1]))


def fmt(d):
    return f"{d.day}. {d.month}."


class DB:
    def __init__(self, path=None):
        os.makedirs(DATA, exist_ok=True)
        os.makedirs(FOTKY, exist_ok=True)
        self.path = path or os.path.join(DATA, "zahradka.db")
        self.lock = threading.RLock()
        self.con = sqlite3.connect(self.path, check_same_thread=False)
        self.con.row_factory = sqlite3.Row
        self.con.execute("PRAGMA journal_mode=WAL")
        self.con.execute("PRAGMA foreign_keys=ON")
        self.con.executescript(SCHEMA)
        stlpce = {r[1] for r in self.con.execute("PRAGMA table_info(zahony)")}
        for s in ("od_roku", "do_roku"):
            if s not in stlpce:  # databáza z verzie 1.0.x
                self.con.execute(f"ALTER TABLE zahony ADD COLUMN {s} INTEGER")
        self.con.commit()

    # ------------------------------------------------------------ základ
    def q(self, sql, args=()):
        with self.lock:
            return [dict(r) for r in self.con.execute(sql, args).fetchall()]

    def x(self, sql, args=()):
        with self.lock:
            cur = self.con.execute(sql, args)
            self.con.commit()
            return cur.lastrowid

    # ------------------------------------------------------------ nastavenia
    def settings(self):
        s = dict(DEFAULTS)
        for r in self.q("SELECT key, value FROM settings"):
            s[r["key"]] = r["value"]
        return s

    def set_settings(self, d):
        for k, v in d.items():
            if k in DEFAULTS or k == "remote_token":
                self.x("INSERT OR REPLACE INTO settings(key, value) VALUES (?, ?)", (k, str(v)))

    def token(self):
        s = self.settings()
        t = s.get("remote_token")
        if not t:
            t = secrets.token_urlsafe(12)
            self.set_settings({"remote_token": t})
        return t

    def settings_public(self):
        s = self.settings()
        s.pop("remote_token", None)
        key = s.get("api_key", "")
        s["api_key_nastaveny"] = bool(key)
        s["api_key"] = (key[:10] + "…" + key[-4:]) if key else ""
        return s

    # ------------------------------------------------------------ uzamknuté roky
    def uzamknute(self):
        try:
            return sorted(int(x) for x in json.loads(self.settings().get("uzamknute") or "[]"))
        except (ValueError, TypeError):
            return []

    def je_zamknuty(self, rok):
        return rok is not None and int(rok) in self.uzamknute()

    def zamkni(self, rok, zamknut=True):
        """Uzamknutie roka: uloží sa snímka plánu (poloha a rozmery objektov) a výsadby roka sa nedajú meniť."""
        rok = int(rok)
        roky = set(self.uzamknute())
        if zamknut:
            self.x("INSERT OR REPLACE INTO plan_snapshot(rok, data, ts) VALUES (?,?,?)",
                   (rok, json.dumps(self.zahony(rok)), dt.datetime.now().isoformat(timespec="seconds")))
            roky.add(rok)
        else:
            self.x("DELETE FROM plan_snapshot WHERE rok=?", (rok,))
            roky.discard(rok)
        self.set_settings({"uzamknute": json.dumps(sorted(roky))})

    def zahony_planu(self, rok):
        """Objekty plánu pre daný rok – pri uzamknutom roku zo snímky."""
        if self.je_zamknuty(rok):
            r = self.q("SELECT data FROM plan_snapshot WHERE rok=?", (int(rok),))
            if r:
                return json.loads(r[0]["data"])
        return self.zahony(rok)

    # ------------------------------------------------------------ záhony
    def zahony(self, rok=None):
        """Aktívne objekty plánu; s rokom len tie, ktoré v danom roku existujú (od_roku / do_roku)."""
        sql, args = "SELECT * FROM zahony WHERE aktivny=1", []
        if rok:
            sql += " AND (od_roku IS NULL OR od_roku<=?) AND (do_roku IS NULL OR do_roku>=?)"
            args += [int(rok), int(rok)]
        rows = self.q(sql + " ORDER BY typ != 'zahon', nazov", args)
        for r in rows:
            for k in ("x", "y", "w", "h"):
                r[k] = round(r[k], 2)
        return rows

    def zahon_mena(self):
        return {r["id"]: r["nazov"] for r in self.q("SELECT id, nazov FROM zahony")}

    def save_zahon(self, d):
        vals = (d.get("nazov") or "Záhon", d.get("typ") or "zahon", round(float(d.get("x") or 0), 2),
                round(float(d.get("y") or 0), 2), max(0.1, round(float(d.get("w") or 1), 2)),
                max(0.1, round(float(d.get("h") or 1), 2)), d.get("poznamka") or "")
        rok = lambda k: int(d[k]) if str(d.get(k) or "").strip() else None
        if d.get("id"):
            self.x("UPDATE zahony SET nazov=?, typ=?, x=?, y=?, w=?, h=?, poznamka=? WHERE id=?", vals + (int(d["id"]),))
            if "od_roku" in d or "do_roku" in d:
                self.x("UPDATE zahony SET od_roku=?, do_roku=? WHERE id=?", (rok("od_roku"), rok("do_roku"), int(d["id"])))
            return int(d["id"])
        return self.x("INSERT INTO zahony(nazov, typ, x, y, w, h, poznamka, od_roku, do_roku) VALUES (?,?,?,?,?,?,?,?,?)",
                      vals + (rok("od_roku"), rok("do_roku")))

    def del_zahon(self, zid, rok=None):
        """Odstránenie z plánu od roku `rok`: v starších rokoch objekt ostane (do_roku = rok-1).
        Ak v starších rokoch neexistoval, skryje sa úplne. História (výsadby, denník, fotky) ostáva vždy."""
        z = self.q("SELECT od_roku FROM zahony WHERE id=?", (int(zid),))
        if rok and z and (z[0]["od_roku"] is None or z[0]["od_roku"] < int(rok)):
            self.x("UPDATE zahony SET do_roku=? WHERE id=?", (int(rok) - 1, int(zid)))
        else:
            self.x("UPDATE zahony SET aktivny=0 WHERE id=?", (int(zid),))

    # ------------------------------------------------------------ výsadby
    def vysadby_rok(self, rok):
        """Výsadby roka + trvalky a prezimujúce z minulých rokov, ktoré ešte nie sú ukončené."""
        rows = self.q("SELECT * FROM vysadby WHERE rok<=? ORDER BY rok, plodina", (rok,))
        out = []
        for v in rows:
            p = P.PLODINY.get(v["plodina"])
            if v["rok"] == rok:
                v["z_minula"] = False
                out.append(v)
            elif v["stav"] != "ukoncene" and p and (p["trvalka"] or (p["prezimuje"] and v["rok"] == rok - 1)):
                v["z_minula"] = True
                out.append(v)
        return out

    def aktivne(self, rok):
        return [v for v in self.vysadby_rok(rok) if v["stav"] != "ukoncene"]

    def save_vysadba(self, d):
        pid = d.get("plodina")
        if pid not in P.PLODINY:
            raise ValueError("Neznáma plodina")
        rok = int(d.get("rok") or today().year)
        zid = int(d["zahon_id"]) if d.get("zahon_id") else None
        stav = d.get("stav") or "plan"
        if d.get("id"):
            st = self.q("SELECT * FROM vysadby WHERE id=?", (int(d["id"]),))
            if st and self.je_zamknuty(st[0]["rok"]):
                st = st[0]
                zmena = (st["plodina"] != pid or st["zahon_id"] != zid or st["rok"] != rok
                         or (st["sposob"] or "") != (d.get("sposob") or st["sposob"] or "")
                         or (st["odroda"] or "") != (d.get("odroda") or ""))
                if zmena:
                    raise ValueError(f"Rok {st['rok']} je uzamknutý – meniť sa dá len stav, množstvo a poznámka.")
        elif self.je_zamknuty(rok):
            raise ValueError(f"Rok {rok} je uzamknutý – odomkni ho v Pláne.")
        koniec = d.get("koniec") or (d2s(today()) if stav == "ukoncene" else None)
        vals = (pid, d.get("odroda") or "", zid, rok, d.get("datum") or None,
                d.get("sposob") or P.PLODINY[pid]["sposoby"][0], stav,
                d.get("mnozstvo") or "", d.get("poznamka") or "", koniec)
        if d.get("id"):
            self.x("""UPDATE vysadby SET plodina=?, odroda=?, zahon_id=?, rok=?, datum=?, sposob=?, stav=?,
                      mnozstvo=?, poznamka=?, koniec=? WHERE id=?""", vals + (int(d["id"]),))
            return int(d["id"])
        return self.x("""INSERT INTO vysadby(plodina, odroda, zahon_id, rok, datum, sposob, stav, mnozstvo, poznamka, koniec)
                         VALUES (?,?,?,?,?,?,?,?,?,?)""", vals)

    def del_vysadba(self, vid):
        r = self.q("SELECT rok FROM vysadby WHERE id=?", (int(vid),))
        if r and self.je_zamknuty(r[0]["rok"]):
            raise ValueError(f"Rok {r[0]['rok']} je uzamknutý.")
        self.x("DELETE FROM vysadby WHERE id=?", (int(vid),))

    # ------------------------------------------------------------ striedanie (4 skupiny)
    def striedanie_cfg(self):
        try:
            c = json.loads(self.settings().get("striedanie") or "{}")
        except ValueError:
            c = {}
        c.setdefault("rok", today().year + 1)
        c.setdefault("zahony", [])   # [{"id": zahon_id, "skupina": 1..4 v roku c["rok"]}]
        return c

    @staticmethod
    def skupina_v_roku(start, rok0, rok):
        return (int(start) - 1 + (int(rok) - int(rok0))) % 4 + 1

    def navrh_skupin(self, rok0):
        """Návrh skupín pre rok0 podľa toho, čo v záhonoch rástlo v roku rok0-1 (posun o krok)."""
        out, obsadene = {}, set()
        zz = [z for z in self.zahony(rok0) if z["typ"] == "zahon"]
        for z in zz:
            sk = [P.skupina_plodiny(v["plodina"]) for v in self.q(
                "SELECT plodina FROM vysadby WHERE zahon_id=? AND rok=?", (z["id"], rok0 - 1))]
            sk = [s for s in sk if s]
            if sk:
                pref = max(set(sk), key=sk.count) % 4 + 1
                out[z["id"]] = pref
        for zid, s in list(out.items()):   # konflikty: každá skupina raz, kým sa dá
            while s in obsadene and len(obsadene) < 4:
                s = s % 4 + 1
            out[zid] = s
            obsadene.add(s)
        for z in zz:
            if z["id"] not in out:
                volne = [s for s in (1, 2, 3, 4) if s not in obsadene] or [1]
                out[z["id"]] = volne[0]
                obsadene.add(volne[0])
        return [dict(id=z["id"], skupina=out[z["id"]]) for z in zz]

    def uloz_striedanie(self, d):
        cfg = dict(rok=int(d.get("rok") or today().year + 1),
                   zahony=[dict(id=int(x["id"]), skupina=int(x["skupina"])) for x in d.get("zahony", [])])
        self.set_settings({"striedanie": json.dumps(cfg)})
        return cfg

    def skupina_skutocna(self, zid, rok):
        """Skupina podľa toho, čo v záhone v danom roku naozaj rástlo (bez trvaliek a zeleného hnojenia)."""
        sk = [P.skupina_plodiny(v["plodina"]) for v in self.q("SELECT plodina FROM vysadby WHERE zahon_id=? AND rok=?", (zid, rok))
              if P.PLODINY.get(v["plodina"], {}).get("typ") != "zelene_hnojenie"]
        sk = [s for s in sk if s]
        return max(set(sk), key=sk.count) if sk else None

    def striedanie_plan(self, od=None, do=None):
        cfg = self.striedanie_cfg()
        od = int(od or cfg["rok"] - 1)
        do = int(do or cfg["rok"] + 3)
        mena = self.zahon_mena()
        sk = {s["id"]: s for s in P.SKUPINY}
        riadky = []
        vsetky = {z["id"]: z for z in self.q("SELECT * FROM zahony")}
        for z in cfg["zahony"]:
            bunky = []
            zz = vsetky.get(z["id"], {})
            for rok in range(od, do + 1):
                if (zz.get("od_roku") and rok < zz["od_roku"]) or (zz.get("do_roku") and rok > zz["do_roku"]):
                    bunky.append(dict(rok=rok, skupina=None, neexistuje=True, vysadby=[], mimo=[], varovania=[]))
                    continue
                minulost = rok < cfg["rok"]
                g = self.skupina_skutocna(z["id"], rok) if minulost else self.skupina_v_roku(z["skupina"], cfg["rok"], rok)
                vys = [v for v in self.vysadby_rok(rok) if v["zahon_id"] == z["id"] and not v.get("z_minula")]
                mimo = [] if minulost else [P.PLODINY[v["plodina"]]["nazov"] for v in vys if v["plodina"] in P.PLODINY
                        and P.skupina_plodiny(v["plodina"]) not in (None, g)
                        and P.PLODINY[v["plodina"]]["typ"] != "zelene_hnojenie"]
                varovania = [x["text"] for v in vys for x in self.kontrola_striedania(z["id"], v["plodina"], rok, v["id"])
                             if x["uroven"] == "varovanie"]
                bunky.append(dict(rok=rok, skupina=g, minulost=minulost, vysadby=[dict(id=v["id"], plodina=v["plodina"], stav=v["stav"]) for v in vys],
                                  mimo=mimo, varovania=varovania))
            riadky.append(dict(id=z["id"], nazov=mena.get(z["id"], "?"), bunky=bunky))
        return dict(cfg=cfg, od=od, do=do, skupiny=P.SKUPINY, riadky=riadky,
                    zahony=[z for z in self.zahony() if z["typ"] == "zahon"],
                    navrh=self.navrh_skupin(cfg["rok"]), uzamknute=self.uzamknute())

    def _ulohy_striedania(self, rok):
        cfg = self.striedanie_cfg()
        if not cfg["zahony"]:
            return []
        mena = self.zahon_mena()
        sk = {s["id"]: s for s in P.SKUPINY}
        out = []
        if rok < cfg["rok"] - 1:
            return []   # história – úlohy sa netvoria
        for z in cfg["zahony"]:
            meno = mena.get(z["id"], "")
            if rok >= cfg["rok"]:
                teraz = sk[self.skupina_v_roku(z["skupina"], cfg["rok"], rok)]
            else:
                s0 = self.skupina_skutocna(z["id"], rok)
                teraz = sk[s0] if s0 else None
            buduci = sk[self.skupina_v_roku(z["skupina"], cfg["rok"], rok + 1)]
            base = dict(zdroj="striedanie", pid=None, rok=rok, opak="raz", potrebujes=[], nastav=None,
                        plodina="", zahony=[meno])
            if rok >= cfg["rok"]:
                out.append(dict(base, uid="jar", typ="priprava", od=mmdd(rok, "03-10"), do=mmdd(rok, "04-20"),
                                text=f"{meno}: tento rok {teraz['kratko'].lower()} – {teraz['jar']}",
                                key=f"s:{z['id']}:{rok}:jar"))
            po = f"po zbere {teraz['po']}. " if teraz else ""
            out.append(dict(base, uid="jesen", typ="priprava", od=mmdd(rok, "09-20"), do=mmdd(rok, "11-15"),
                            text=f"{meno}: {po}Budúci rok tu bude {buduci['kratko'].lower()} – {buduci['jesen']}",
                            key=f"s:{z['id']}:{rok}:jesen"))
        return out

    # ------------------------------------------------------------ striedanie
    def kontrola_striedania(self, zahon_id, pid, rok, vysadba_id=None):
        if not zahon_id or pid not in P.PLODINY:
            return []
        p = P.PLODINY[pid]
        pauza = 4 if p["rodina"] == "Kapustovité" else 3
        msgs = []
        rows = self.q("SELECT * FROM vysadby WHERE zahon_id=? AND rok>=? AND rok<? AND id!=?",
                      (int(zahon_id), rok - pauza, rok, int(vysadba_id or 0)))
        for v in rows:
            q = P.PLODINY.get(v["plodina"])
            if not q:
                continue
            if v["plodina"] == pid and p["trvalka"]:
                continue
            if q["rodina"] == p["rodina"]:
                msgs.append(dict(uroven="varovanie", text=(
                    f"V roku {v['rok']} tu rástla plodina {q['nazov']} – rovnaká čeľaď ({p['rodina']}). "
                    f"Odporúčaná pauza je {pauza} roky, inak sa hromadia choroby a škodcovia.")))
        if p["naroky"] == "silne":
            minule = [P.PLODINY[v["plodina"]] for v in rows
                      if v["rok"] == rok - 1 and v["plodina"] in P.PLODINY]
            if any(q["naroky"] == "silne" for q in minule):
                msgs.append(dict(uroven="info", text=(
                    "Minulý rok tu bola silne náročná plodina. Ak tu chceš znova silne náročnú, "
                    "daj poriadne kompostu.")))
        return msgs

    def navrh_striedania(self, zahon_id, rok):
        trvalky = [P.PLODINY[v["plodina"]]["nazov"] for v in self.aktivne(rok - 1)
                   if v["zahon_id"] == int(zahon_id) and P.PLODINY.get(v["plodina"], {}).get("trvalka")]
        if trvalky:
            return dict(naroky=None, naroky_text="", obsadene=True, vyhnut=[], kandidati=[],
                        preco=f"Záhon je obsadený trvalkou ({', '.join(trvalky)}). Keď ju po rokoch zrušíš "
                              f"(stav „ukončené“), na jej miesto daj inú čeľaď.")
        rows = self.q("SELECT * FROM vysadby WHERE zahon_id=? AND rok>=? AND rok<?", (int(zahon_id), rok - 4, rok))
        minule = [P.PLODINY[v["plodina"]] for v in rows if v["rok"] == rok - 1 and v["plodina"] in P.PLODINY
                  and P.PLODINY[v["plodina"]]["typ"] != "zelene_hnojenie"]
        naroky = {q["naroky"] for q in minule}
        if "silne" in naroky:
            dalsie, preco = "stredne", "minulý rok tu boli silne náročné plodiny"
        elif "stredne" in naroky:
            dalsie, preco = "slabo", "minulý rok tu boli stredne náročné plodiny"
        elif "slabo" in naroky:
            dalsie, preco = "silne", "minulý rok tu boli slabo náročné plodiny – teraz s kompostom silne náročné"
        else:
            dalsie, preco = None, "z minulého roka nemám záznam"
        zakazane = set()
        for v in rows:
            q = P.PLODINY.get(v["plodina"])
            if not q:
                continue
            pauza = 4 if q["rodina"] == "Kapustovité" else 3
            if v["rok"] >= rok - pauza:
                zakazane.add(q["rodina"])
        kandidati = [q["nazov"] for q in P.PLODINY.values()
                     if q["typ"] in ("zelenina",) and q["rodina"] not in zakazane
                     and (dalsie is None or q["naroky"] == dalsie)]
        return dict(naroky=dalsie, naroky_text=P.NAROKY.get(dalsie, "podľa chuti"), preco=preco,
                    vyhnut=sorted(zakazane), kandidati=kandidati)

    def historia_zahona(self, zahon_id):
        rows = self.q("SELECT * FROM vysadby WHERE zahon_id=? ORDER BY rok DESC, plodina", (int(zahon_id),))
        roky = {}
        for v in rows:
            p = P.PLODINY.get(v["plodina"], {})
            roky.setdefault(v["rok"], []).append(dict(v, nazov=p.get("nazov", v["plodina"]), rodina=p.get("rodina", "")))
        return [dict(rok=r, vysadby=roky[r]) for r in sorted(roky, reverse=True)]

    # ------------------------------------------------------------ úlohy
    def _hotovo(self):
        return {r["key"] for r in self.q("SELECT key FROM hotovo")}

    def _instancie(self, rok, poda, mena):
        """Všetky úlohy roka (bez rozhodnutia o týždni)."""
        akt = self.aktivne(rok)
        out = []
        podla_plodiny = {}
        for v in akt:
            podla_plodiny.setdefault(v["plodina"], []).append(v)
        vsetky_sposoby = {v["sposob"] for v in akt}
        pestujem = set(podla_plodiny)

        for pid, vys in podla_plodiny.items():
            p = P.PLODINY.get(pid)
            if not p:
                continue
            sposoby = {v["sposob"] for v in vys}
            stavy = {v["stav"] for v in vys}
            zahony = sorted({mena.get(v["zahon_id"], "") for v in vys if v["zahon_id"]})
            # prezimujúce (cesnak, raž): v roku výsadby len jesenné úlohy, v ďalšom roku len jarné/letné
            fazy = {"jesen" if v["rok"] == rok else "jar" for v in vys}
            for u in p["ulohy"]:
                if p["prezimuje"]:
                    jesenna = u["od"] >= "08-01"
                    if (jesenna and "jesen" not in fazy) or (not jesenna and "jar" not in fazy):
                        continue
                if u["sposob"] and not (sposoby & set(u["sposob"])):
                    continue
                if u["stav"] and not (stavy & set(u["stav"])):
                    continue
                # trvalky a prezimujúce: výsadbové úlohy len pre plánované výsadby
                out.append(dict(zdroj="plodina", pid=pid, uid=u["id"], rok=rok, text=u["text"], typ=u["typ"],
                                opak=u["opak"], od=mmdd(rok, u["od"]), do=mmdd(rok, u["do"]),
                                potrebujes=u["potrebujes"], nastav=u["nastav"], stav_filter=u["stav"],
                                sposob_filter=u["sposob"], plodina=p["nazov"], zahony=zahony,
                                key=f"p:{pid}:{u['id']}:{rok}"))

        out += self._ulohy_striedania(rok)
        for g in P.VSEOBECNE:
            if g["poda"] and poda not in g["poda"]:
                continue
            if g["ak_plodiny"] and not (pestujem & set(g["ak_plodiny"])):
                continue
            if g["ak_sposob"] and not (vsetky_sposoby & set(g["ak_sposob"])):
                continue
            out.append(dict(zdroj="vseobecne", pid=None, uid=g["id"], rok=rok, text=g["text"], typ=g["typ"],
                            opak=g["opak"], od=mmdd(rok, g["od"]), do=mmdd(rok, g["do"]),
                            potrebujes=g["potrebujes"], nastav=None, plodina="", zahony=[],
                            key=f"g:{g['id']}:{rok}"))
        return out

    def _relativne(self, mena):
        out = []
        for v in self.q("SELECT * FROM vysadby WHERE stav NOT IN ('plan','ukoncene') AND datum IS NOT NULL"):
            p = P.PLODINY.get(v["plodina"])
            d0 = s2d(v["datum"])
            if not p or not d0:
                continue
            for i, r in enumerate(p["rel"]):
                if r["sposob"] and v["sposob"] not in r["sposob"]:
                    continue
                out.append(dict(zdroj="vysadba", pid=v["plodina"], uid=f"rel{i}", rok=d0.year, text=r["text"],
                                typ="starostlivost", opak=r["opak"], od=d0 + dt.timedelta(days=r["od"]),
                                do=d0 + dt.timedelta(days=r["do"]), potrebujes=[], nastav=None,
                                plodina=p["nazov"], zahony=[mena.get(v["zahon_id"], "")] if v["zahon_id"] else [],
                                key=f"r:{v['id']}:{i}"))
        return out

    @staticmethod
    def _kluc(u, ws):
        if u["opak"] == "tyzden":
            y, w, _ = ws.isocalendar()
            return f"{u['key']}:w{y}-{w}"
        if u["opak"] == "14dni":
            return f"{u['key']}:d{ws.toordinal() // 14}"
        return u["key"]

    def nastenka(self, datum=None):
        d = datum or today()
        s = self.settings()
        ws = d - dt.timedelta(days=d.weekday())
        we = ws + dt.timedelta(days=6)
        ms = d.replace(day=1)
        me = d.replace(day=calendar.monthrange(d.year, d.month)[1])
        horizont = me + dt.timedelta(days=35)
        mena = self.zahon_mena()
        hotovo = self._hotovo()

        roky = range((ws - dt.timedelta(days=14)).year, horizont.year + 1)
        inst = []
        for r in roky:
            inst += self._instancie(r, s["poda"], mena)
        inst += self._relativne(mena)

        tyzden, mesiac, buduce, nakup = [], [], [], {}
        for u in inst:
            if u["do"] < ws - dt.timedelta(days=14) or u["od"] > horizont:
                continue
            key = self._kluc(u, ws)
            done = key in hotovo
            item = dict(key=key, text=u["text"], typ=u["typ"], opak=u["opak"], zdroj=u["zdroj"],
                        plodina=u["plodina"], pid=u["pid"], zahony=u["zahony"], potrebujes=u["potrebujes"],
                        od=d2s(u["od"]), do=d2s(u["do"]), od_txt=fmt(u["od"]), do_txt=fmt(u["do"]),
                        hotovo=done, nastav=u["nastav"], meskanie=False)
            dlzka = (u["do"] - u["od"]).days
            if u["do"] < ws:
                if u["opak"] == "raz" and not done and u["zdroj"] != "vseobecne":
                    item["meskanie"] = True
                    tyzden.append(item)
            elif u["od"] <= we:
                if u["opak"] != "raz" or dlzka <= 21 or (u["do"] - we).days <= 7:
                    tyzden.append(item)
                else:
                    item["priebezne"] = True
                    mesiac.append(item)
            elif u["od"] <= me:
                mesiac.append(item)
            elif not done:
                item["hotovo"] = False
                item["checkable"] = False
                buduce.append(item)
            if not done and u["potrebujes"] and u["do"] >= d and u["od"] <= d + dt.timedelta(days=28):
                for n in u["potrebujes"]:
                    nakup.setdefault(n, set()).add(u["plodina"] or "záhrada")

        poradie = {"info": 0, "sejba": 1, "vysadba": 2, "nakup": 3, "priprava": 4, "hnojenie": 5,
                   "ochrana": 6, "rez": 7, "starostlivost": 8, "zber": 9}
        klucik = lambda i: (not i["meskanie"], i["hotovo"], poradie.get(i["typ"], 9), i["do"])
        tyzden.sort(key=klucik)
        mesiac.sort(key=lambda i: (i["hotovo"], i["od"], poradie.get(i["typ"], 9)))
        buduce.sort(key=lambda i: i["od"])

        wx = self.pocasie()
        upoz = upozornenia(wx, d, s["poda"], {v["plodina"] for v in self.aktivne(d.year)
                                              if v["stav"] in ("zasiate", "vysadene")})
        y, w, _ = d.isocalendar()
        return dict(
            datum=d2s(d), tyzden_od=d2s(ws), tyzden_do=d2s(we), iso_tyzden=w, rok=d.year,
            mesiac=d.month, nazov=s["nazov"], pocasie=wx, upozornenia=upoz,
            ulohy_tyzden=tyzden, ulohy_mesiac=mesiac, ulohy_buduce=buduce[:25],
            nakup=[dict(vec=k, pre=sorted(v)) for k, v in sorted(nakup.items())],
            dennik=self.dennik(limit=6),
            pestujem=len(self.aktivne(d.year)),
        )

    def oznac(self, key, done, text="", typ="", plodina_nazov="", pid=None, nastav=None, zapisat=True, zahon_nazov=""):
        if not done:
            self.x("DELETE FROM hotovo WHERE key=?", (key,))
            self.x("DELETE FROM dennik WHERE uloha_key=?", (key,))
            return
        self.x("INSERT OR REPLACE INTO hotovo(key, datum) VALUES (?, ?)", (key, d2s(today())))
        zid = None
        if zahon_nazov:
            r = self.q("SELECT id FROM zahony WHERE nazov=? AND aktivny=1", (zahon_nazov,))
            zid = r[0]["id"] if r else None
        if nastav and pid:
            # plánované výsadby tejto plodiny sa prepnú (napr. plan -> vysadene) a dostanú dátum
            for v in self.aktivne(today().year):
                if v["plodina"] != pid:
                    continue
                if nastav == "zasiate" and v["stav"] == "plan":
                    self.x("UPDATE vysadby SET stav='zasiate', datum=COALESCE(datum, ?) WHERE id=?", (d2s(today()), v["id"]))
                elif nastav == "vysadene" and v["stav"] in ("plan", "zasiate"):
                    self.x("UPDATE vysadby SET stav='vysadene', datum=? WHERE id=?", (d2s(today()), v["id"]))
                if zid is None and v["zahon_id"]:
                    zid = v["zahon_id"]
        if zapisat and self.settings().get("dennik_auto") == "1":
            self.x("""INSERT INTO dennik(datum, typ, zahon_id, plodina, text, uloha_key, created)
                      VALUES (?,?,?,?,?,?,?)""",
                   (d2s(today()), TYP_ULOHY_DO_DENNIKA.get(typ, "praca"), zid, pid or "", text, key,
                    dt.datetime.now().isoformat(timespec="seconds")))

    # ------------------------------------------------------------ denník
    def dennik(self, rok=None, zahon_id=None, plodina=None, limit=None):
        sql, args = "SELECT * FROM dennik WHERE 1=1", []
        if rok:
            sql += " AND substr(datum,1,4)=?"
            args.append(str(rok))
        if zahon_id:
            sql += " AND zahon_id=?"
            args.append(int(zahon_id))
        if plodina:
            sql += " AND plodina=?"
            args.append(plodina)
        sql += " ORDER BY datum DESC, id DESC"
        if limit:
            sql += f" LIMIT {int(limit)}"
        mena = self.zahon_mena()
        out = self.q(sql, args)
        for r in out:
            r["zahon"] = mena.get(r["zahon_id"], "")
            r["plodina_nazov"] = P.PLODINY.get(r["plodina"], {}).get("nazov", r["plodina"] or "")
        return out

    def save_dennik(self, d):
        mn = d.get("mnozstvo")
        mn = float(str(mn).replace(",", ".")) if mn not in (None, "") else None
        vals = (d.get("datum") or d2s(today()), d.get("typ") or "praca",
                int(d["zahon_id"]) if d.get("zahon_id") else None, d.get("plodina") or "",
                d.get("text") or "", mn, d.get("jednotka") or "")
        if d.get("id"):
            self.x("UPDATE dennik SET datum=?, typ=?, zahon_id=?, plodina=?, text=?, mnozstvo=?, jednotka=? WHERE id=?",
                   vals + (int(d["id"]),))
            return int(d["id"])
        return self.x("""INSERT INTO dennik(datum, typ, zahon_id, plodina, text, mnozstvo, jednotka, created)
                         VALUES (?,?,?,?,?,?,?,?)""", vals + (dt.datetime.now().isoformat(timespec="seconds"),))

    def del_dennik(self, did):
        r = self.q("SELECT uloha_key FROM dennik WHERE id=?", (int(did),))
        self.x("DELETE FROM dennik WHERE id=?", (int(did),))
        if r and r[0]["uloha_key"]:
            self.x("DELETE FROM hotovo WHERE key=?", (r[0]["uloha_key"],))

    def zber_suhrn(self, rok):
        rows = self.q("""SELECT plodina, jednotka, SUM(mnozstvo) s, COUNT(*) n FROM dennik
                         WHERE typ='zber' AND substr(datum,1,4)=? GROUP BY plodina, jednotka""", (str(rok),))
        for r in rows:
            r["plodina_nazov"] = P.PLODINY.get(r["plodina"], {}).get("nazov", r["plodina"] or "(bez plodiny)")
        return rows

    def export_dennik(self):
        os.makedirs(EXPORT, exist_ok=True)
        rows = self.dennik()
        lines = ["datum;typ;zahon;plodina;text;mnozstvo;jednotka"]
        for r in reversed(rows):
            txt = (r["text"] or "").replace(";", ",").replace("\n", " ")
            mn = "" if r["mnozstvo"] is None else str(r["mnozstvo"]).replace(".", ",")
            lines.append(f"{r['datum']};{TYPY_DENNIK.get(r['typ'], r['typ'])};{r['zahon']};{r['plodina_nazov']};{txt};{mn};{r['jednotka'] or ''}")
        content = "\r\n".join(lines) + "\r\n"
        path = os.path.join(EXPORT, f"dennik-{d2s(today())}.csv")
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            f.write(content)
        return path, content

    # ------------------------------------------------------------ fotky
    def fotky(self, zahon_id=None, plodina=None):
        sql, args = "SELECT * FROM fotky WHERE 1=1", []
        if zahon_id:
            sql += " AND zahon_id=?"
            args.append(int(zahon_id))
        if plodina:
            sql += " AND plodina=?"
            args.append(plodina)
        sql += " ORDER BY datum DESC, id DESC"
        mena = self.zahon_mena()
        out = self.q(sql, args)
        for r in out:
            r["zahon"] = mena.get(r["zahon_id"], "")
            r["plodina_nazov"] = P.PLODINY.get(r["plodina"], {}).get("nazov", r["plodina"] or "")
        return out

    def uloz_fotku(self, d):
        data = d.get("data") or ""
        if "," in data[:100]:
            hlavicka, data = data.split(",", 1)
        else:
            hlavicka = ""
        raw = base64.b64decode(data)
        ext = ".png" if "png" in hlavicka else ".webp" if "webp" in hlavicka else ".jpg"
        datum = d.get("datum") or d2s(today())
        rok = datum[:4]
        os.makedirs(os.path.join(FOTKY, rok), exist_ok=True)
        meno = f"{datum.replace('-', '')}_{dt.datetime.now().strftime('%H%M%S')}_{secrets.token_hex(3)}{ext}"
        with open(os.path.join(FOTKY, rok, meno), "wb") as f:
            f.write(raw)
        return self.x("""INSERT INTO fotky(datum, zahon_id, plodina, subor, popis, created) VALUES (?,?,?,?,?,?)""",
                      (datum, int(d["zahon_id"]) if d.get("zahon_id") else None, d.get("plodina") or "",
                       f"{rok}/{meno}", d.get("popis") or "", dt.datetime.now().isoformat(timespec="seconds")))

    def uprav_fotku(self, d):
        fid = int(d["id"])
        polia = {"datum": d.get("datum"), "zahon_id": int(d["zahon_id"]) if d.get("zahon_id") else None,
                 "plodina": d.get("plodina") or "", "popis": d.get("popis") or ""}
        self.x("UPDATE fotky SET datum=?, zahon_id=?, plodina=?, popis=? WHERE id=?",
               (polia["datum"], polia["zahon_id"], polia["plodina"], polia["popis"], fid))
        if "hodnotenie" in d:
            self.x("UPDATE fotky SET hodnotenie=?, hodnotenie_zdroj=?, hodnotenie_datum=? WHERE id=?",
                   (d["hodnotenie"] or "", d.get("hodnotenie_zdroj") or "vložené ručne",
                    d2s(today()) if d["hodnotenie"] else None, fid))

    def del_fotku(self, fid):
        r = self.q("SELECT subor FROM fotky WHERE id=?", (int(fid),))
        self.x("DELETE FROM fotky WHERE id=?", (int(fid),))
        if r:
            p = os.path.join(FOTKY, r[0]["subor"])
            if os.path.isfile(p):
                os.remove(p)

    def fotka_cesta(self, rel):
        p = os.path.normpath(os.path.join(FOTKY, rel))
        return p if p.startswith(os.path.normpath(FOTKY)) and os.path.isfile(p) else None

    # ------------------------------------------------------------ diagnostika
    def prompt_diagnostiky(self, fid, poznamka=""):
        f = self.q("SELECT * FROM fotky WHERE id=?", (int(fid),))
        if not f:
            raise ValueError("Fotka neexistuje")
        f = f[0]
        s = self.settings()
        p = P.PLODINY.get(f["plodina"])
        vys = None
        if f["plodina"] and f["zahon_id"]:
            r = self.q("SELECT * FROM vysadby WHERE plodina=? AND zahon_id=? ORDER BY rok DESC LIMIT 1",
                       (f["plodina"], f["zahon_id"]))
            vys = r[0] if r else None
        riadky = [
            "Si skúsený záhradkár v strednej Európe. Na fotke je rastlina z mojej záhradky. Zhodnoť jej stav.",
            "",
            f"Záhradka: záhradkárska kolónia ({s['miesto']}), bez skleníka, pôda {PODY.get(s['poda'], s['poda'])}.",
            f"Rastlina: {p['nazov'] if p else (f['plodina'] or 'neuvedená – urči ju, ak vieš')}"
            + (f", odroda {vys['odroda']}" if vys and vys['odroda'] else "")
            + (f", vysadená/zasiata {vys['datum']}" if vys and vys['datum'] else ""),
            f"Dátum fotky: {f['datum']}.",
        ]
        poc = self.pocasie_minulych_dni(s2d(f["datum"]))
        if poc:
            riadky.append(f"Počasie 7 dní pred fotkou: {poc}.")
        popis = " ".join(x for x in (f["popis"], poznamka) if x)
        if popis:
            riadky.append(f"Môj popis: {popis}")
        riadky += [
            "",
            "Odpovedz po slovensky, stručne, v tejto štruktúre:",
            "1. Stav: zdravá / mierny problém / vážny problém",
            "2. Čo vidíš: choroba, škodca, nedostatok živín, sucho / prelievanie, iné – a ako si istý",
            "3. Čo urobiť teraz (konkrétne kroky, prípravky len bežne dostupné pre záhradkára)",
            "4. Prevencia do budúcna",
            "Ak sa z fotky nedá rozhodnúť, napíš to a povedz, akú fotku potrebuješ (napr. spodná strana listu, detail plodu).",
        ]
        return "\n".join(riadky)

    def diagnostika_api(self, fid, poznamka=""):
        s = self.settings()
        if not s.get("api_key"):
            raise ValueError("Nie je nastavený API kľúč (Nastavenia → Diagnostika).")
        f = self.q("SELECT * FROM fotky WHERE id=?", (int(fid),))[0]
        path = self.fotka_cesta(f["subor"])
        if not path:
            raise ValueError("Súbor fotky chýba.")
        with open(path, "rb") as fh:
            b64 = base64.b64encode(fh.read()).decode()
        mt = "image/png" if path.endswith(".png") else "image/webp" if path.endswith(".webp") else "image/jpeg"
        body = {
            "model": s.get("model") or DEFAULTS["model"],
            "max_tokens": 1500,
            "messages": [{"role": "user", "content": [
                {"type": "image", "source": {"type": "base64", "media_type": mt, "data": b64}},
                {"type": "text", "text": self.prompt_diagnostiky(fid, poznamka)},
            ]}],
        }
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages", data=json.dumps(body).encode(),
            headers={"x-api-key": s["api_key"], "anthropic-version": "2023-06-01", "content-type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120, context=ssl.create_default_context()) as r:
                res = json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")[:500]
            raise ValueError(f"API vrátilo chybu {e.code}: {detail}")
        except urllib.error.URLError as e:
            raise ValueError(f"Nedá sa pripojiť na api.anthropic.com: {e.reason}")
        text = "".join(c.get("text", "") for c in res.get("content", []) if c.get("type") == "text").strip()
        usage = res.get("usage", {})
        zdroj = f"Claude API ({res.get('model', body['model'])}, tokeny: vstup {usage.get('input_tokens', '?')}, výstup {usage.get('output_tokens', '?')})"
        self.x("UPDATE fotky SET hodnotenie=?, hodnotenie_zdroj=?, hodnotenie_datum=? WHERE id=?",
               (text, zdroj, d2s(today()), int(fid)))
        return dict(hodnotenie=text, zdroj=zdroj)

    # ------------------------------------------------------------ počasie
    def _cache_get(self, key):
        r = self.q("SELECT ts, data FROM cache WHERE key=?", (key,))
        return (r[0]["ts"], json.loads(r[0]["data"])) if r else (None, None)

    def _cache_set(self, key, data):
        self.x("INSERT OR REPLACE INTO cache(key, ts, data) VALUES (?,?,?)",
               (key, dt.datetime.now().isoformat(timespec="seconds"), json.dumps(data)))

    def pocasie(self, force=False):
        s = self.settings()
        key = f"wx:{s['lat']}:{s['lon']}"
        ts, data = self._cache_get(key)
        fresh = ts and (dt.datetime.now() - dt.datetime.fromisoformat(ts)).total_seconds() < 3600
        if data and fresh and not force:
            return dict(data, ts=ts, stare=False, chyba=None)
        try:
            data = stiahni_pocasie(s["lat"], s["lon"])
            self._cache_set(key, data)
            ts2, _ = self._cache_get(key)
            return dict(data, ts=ts2, stare=False, chyba=None)
        except Exception as e:  # sieť nedostupná – použi starú predpoveď
            if data:
                return dict(data, ts=ts, stare=True, chyba=f"Predpoveď sa nepodarilo obnoviť ({e}). Zobrazujem uloženú.")
            return dict(dni=[], ts=None, stare=True, chyba=f"Počasie nedostupné: {e}")

    def pocasie_minulych_dni(self, datum):
        if not datum:
            return ""
        s = self.settings()
        _, data = self._cache_get(f"wx:{s['lat']}:{s['lon']}")
        if not data:
            return ""
        dni = [x for x in data.get("dni", []) if datum - dt.timedelta(days=7) <= s2d(x["datum"]) <= datum]
        if not dni:
            return ""
        zr = sum(x["zrazky"] or 0 for x in dni)
        tmin = min(x["tmin"] for x in dni if x["tmin"] is not None)
        tmax = max(x["tmax"] for x in dni if x["tmax"] is not None)
        return f"teploty {tmin:.0f} až {tmax:.0f} °C, zrážky spolu {zr:.0f} mm"

    # ------------------------------------------------------------ zálohy
    def zaloha(self):
        os.makedirs(BACKUPS, exist_ok=True)
        cesta = os.path.join(BACKUPS, f"zahradka-{d2s(today())}.db")
        if not os.path.exists(cesta):
            with self.lock:
                dst = sqlite3.connect(cesta)
                self.con.backup(dst)
                dst.close()
        subory = sorted(glob.glob(os.path.join(BACKUPS, "zahradka-*.db")))
        for f in subory[:-30]:
            os.remove(f)
        return cesta


# ---------------------------------------------------------------- počasie (Open-Meteo, bez kľúča)
def _get_json(url, timeout=12):
    req = urllib.request.Request(url, headers={"User-Agent": f"Zahradka/{VERZIA}"})
    with urllib.request.urlopen(req, timeout=timeout, context=ssl.create_default_context()) as r:
        return json.loads(r.read().decode())


def stiahni_pocasie(lat, lon):
    q = urllib.parse.urlencode({
        "latitude": lat, "longitude": lon, "timezone": "Europe/Prague", "past_days": 7, "forecast_days": 7,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,"
                 "wind_speed_10m_max,weather_code",
    })
    j = _get_json("https://api.open-meteo.com/v1/forecast?" + q)
    dd = j["daily"]
    dni = []
    for i, t in enumerate(dd["time"]):
        dni.append(dict(datum=t, tmax=dd["temperature_2m_max"][i], tmin=dd["temperature_2m_min"][i],
                        zrazky=dd["precipitation_sum"][i], pravd=dd["precipitation_probability_max"][i],
                        vietor=dd["wind_speed_10m_max"][i], kod=dd["weather_code"][i]))
    return dict(dni=dni)


def geokod(nazov):
    q = urllib.parse.urlencode({"name": nazov, "count": 8, "language": "sk", "format": "json"})
    j = _get_json("https://geocoding-api.open-meteo.com/v1/search?" + q)
    return [dict(nazov=r.get("name"), kraj=r.get("admin1", ""), stat=r.get("country", ""),
                 lat=r["latitude"], lon=r["longitude"]) for r in j.get("results", [])]


DNI = ["po", "ut", "st", "št", "pi", "so", "ne"]


def _den(d, dnes):
    if d == dnes:
        return "dnes"
    if d == dnes + dt.timedelta(days=1):
        return "zajtra"
    return f"{DNI[d.weekday()]} {fmt(d)}"


def upozornenia(wx, dnes, poda, rastuce):
    """Úlohy podľa počasia. rastuce = id plodín, ktoré sú vonku."""
    dni = {s2d(x["datum"]): x for x in wx.get("dni", [])}
    if dnes not in dni:
        return []
    out = []
    m = dnes.month
    nazvy = lambda ids: ", ".join(P.PLODINY[i]["nazov"].split(" (")[0].lower() for i in ids)

    # mráz v najbližších 3 nociach
    for i in range(3):
        d = dnes + dt.timedelta(days=i)
        x = dni.get(d)
        if not x or x["tmin"] is None:
            continue
        if x["tmin"] <= 2 and 3 <= m <= 11:
            silny = x["tmin"] <= -1
            if 4 <= m <= 6:
                citl = [p for p in P.CITLIVE_JAR if p in rastuce]
                co = nazvy(citl) if citl else "citlivé výsadby a skoré sejby"
                text = f"zakry {co} bielou textíliou (večer)"
            elif 9 <= m <= 11:
                citl = [p for p in P.CITLIVE if p in rastuce]
                if not citl and not silny:
                    continue  # na jeseň bez citlivých rastlín mrazík netreba hlásiť
                co = nazvy(citl) if citl else "zeleninu, ktorá ešte ostala vonku"
                text = f"pozbieraj alebo zakry {co}"
            else:
                text = "skoré sejby a výsadby zakry textíliou"
            druh = "Mráz" if silny else "Prízemný mrazík"
            out.append(dict(uroven="alarm" if silny else "varovanie", ikona="❄️",
                            text=f"{druh} v noci na {_den(d, dnes)} (min. {x['tmin']:.0f} °C) – {text}."))
            break

    # dážď dnes / zajtra
    for i in range(2):
        d = dnes + dt.timedelta(days=i)
        x = dni.get(d)
        if x and ((x["zrazky"] or 0) >= 3 or (x["pravd"] or 0) >= 70):
            out.append(dict(uroven="info", ikona="🌧️",
                            text=f"{_den(d, dnes).capitalize()} prší ({(x['zrazky'] or 0):.0f} mm, {x['pravd'] or 0} %) – "
                                 f"nestriekaj, nehnoj na list, polievanie vynechaj."))
            break

    # sucho
    if 4 <= m <= 9:
        sucho = 0
        d = dnes - dt.timedelta(days=1)
        while d in dni and (dni[d]["zrazky"] or 0) < 1:
            sucho += 1
            d -= dt.timedelta(days=1)
        buduce = sum((dni.get(dnes + dt.timedelta(days=i)) or {}).get("zrazky") or 0 for i in range(3))
        tmax = dni[dnes]["tmax"] or 0
        if sucho >= 3 and buduce < 2 and tmax >= 18:
            piesok = " Piesočnatá pôda vysychá rýchlo." if poda == "piesocnata" else ""
            out.append(dict(uroven="varovanie", ikona="💧",
                            text=f"{sucho} dní bez dažďa a ďalšie dni tiež sucho – polievaj ráno, ku koreňom, výdatne.{piesok}"))

    # horúčava
    for i in range(3):
        d = dnes + dt.timedelta(days=i)
        x = dni.get(d)
        if x and (x["tmax"] or 0) >= 30:
            out.append(dict(uroven="varovanie", ikona="🔥",
                            text=f"Horúco {_den(d, dnes)} ({x['tmax']:.0f} °C) – polievaj skoro ráno, mulčuj, mladé výsadby pritieň."))
            break

    # vietor
    for i in range(2):
        d = dnes + dt.timedelta(days=i)
        x = dni.get(d)
        if x and (x["vietor"] or 0) >= 50:
            out.append(dict(uroven="varovanie", ikona="💨",
                            text=f"Silný vietor {_den(d, dnes)} ({x['vietor']:.0f} km/h) – skontroluj kolíky, zaťaž textíliu."))
            break

    # vhodné okno na postrek
    x0, x1 = dni.get(dnes), dni.get(dnes + dt.timedelta(days=1))
    if x0 and x1 and 4 <= m <= 9 and (x0["zrazky"] or 0) < 1 and (x1["zrazky"] or 0) < 1 \
            and (x0["vietor"] or 0) < 20 and (x0["tmax"] or 0) < 28:
        out.append(dict(uroven="ok", ikona="✅", text="Dnes a zajtra bez dažďa a vetra – vhodné na postrek alebo hnojenie na list."))
    return out
